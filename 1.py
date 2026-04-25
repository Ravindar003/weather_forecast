import streamlit as st
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import joblib
import json
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path

# ==========================================
# 1. MODEL ARCHITECTURES
# ==========================================

class AttentionReadout(nn.Module):
    def __init__(self, hidden_size):
        super().__init__()
        self.w = nn.Linear(hidden_size, 1, bias=False)
    def forward(self, hidden_states):
        scores = self.w(hidden_states).squeeze(-1)
        weights = F.softmax(scores, dim=1).unsqueeze(-1)
        return (hidden_states * weights).sum(dim=1)

class DualBranchGRU(nn.Module):
    def __init__(self, input_size):
        super().__init__()
        hs = 256 // 2  # HIDDEN_SIZE = 256
        self.gru_long = nn.GRU(input_size, hs, num_layers=3, batch_first=True, dropout=0.2)
        self.gru_short = nn.GRU(input_size, hs, num_layers=3, batch_first=True, dropout=0.2)
        self.attn_long = AttentionReadout(hs)
        self.attn_short = AttentionReadout(hs)
        self.head = nn.Sequential(
            nn.Linear(hs * 2, 256), nn.LayerNorm(256), nn.GELU(), nn.Dropout(0.2),
            nn.Linear(256, 64), nn.GELU(), nn.Linear(64, 1)
        )
    def forward(self, long_x, short_x):
        out_l, _ = self.gru_long(long_x)
        out_s, _ = self.gru_short(short_x)
        fused = torch.cat([self.attn_long(out_l), self.attn_short(out_s)], dim=1)
        return self.head(fused).squeeze(-1)

class TNNModel(nn.Module):
    def __init__(self, input_size, n_heads=8, n_layers=4, d_model=128):
        super().__init__()
        self.encoder = nn.Linear(input_size, d_model)
        layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=n_heads, dim_feedforward=512, batch_first=True)
        self.transformer = nn.TransformerEncoder(layer, num_layers=n_layers)
        self.head = nn.Sequential(nn.Linear(d_model, 64), nn.ReLU(), nn.Linear(64, 1))
    def forward(self, x):
        x = self.encoder(x)
        x = self.transformer(x)
        return self.head(x[:, -1, :]).squeeze(-1)

# ==========================================
# 2. FEATURE ENGINEERING ENGINE
# ==========================================
def engineer_features(live_df, hist_df, feature_names, seq_len=72):
    """
    Creates a 72-hour context and calculates all 74+ required features.
    """
    # 1. Merge History and Live
    combined = pd.concat([hist_df.tail(seq_len + 24), live_df], ignore_index=True)
    
    # 2. Cyclic Time
    now = datetime.now()
    combined['hour'], combined['month'], combined['dayofyear'] = now.hour, now.month, now.timetuple().tm_yday
    for p, c in [(24, "hour"), (12, "month"), (365, "dayofyear")]:
        combined[f"{c}_sin"] = np.sin(2 * np.pi * combined[c] / p)
        combined[f"{c}_cos"] = np.cos(2 * np.pi * combined[c] / p)
    combined["week_sin"] = np.sin(2 * np.pi * now.isocalendar()[1] / 52)
    combined["week_cos"] = np.cos(2 * np.pi * now.isocalendar()[1] / 52)

    # 3. Rolling Stats & Missing Min/Max Calculation
    target = "tempm"
    for w in [3, 6, 12, 24, 48]:
        combined[f"tempm_rmean_{w}"] = combined[target].rolling(w, min_periods=1).mean()
        combined[f"tempm_rstd_{w}"] = combined[target].rolling(w, min_periods=1).std().fillna(0)
    
    combined["tempm_rmin_24"] = combined[target].rolling(24, min_periods=1).min()
    combined["tempm_rmax_24"] = combined[target].rolling(24, min_periods=1).max()
    combined["tempm_range_24"] = combined["tempm_rmax_24"] - combined["tempm_rmin_24"]
    
    # 4. Lags
    for lag in [1, 2, 3, 6, 12, 24, 48, 72]:
        combined[f"tempm_lag{lag}"] = combined[target].shift(lag)

    wx_cols = ["dewptm", "hum", "pressurem", "wspdm", "heatindexm", "windchillm", "vism", "wgustm"]
    for col in wx_cols:
        if col in combined.columns:
            for lag in [1, 3, 6, 12]: combined[f"{col}_lag{lag}"] = combined[col].shift(lag)
    
    if "dewptm" in combined.columns: combined["dew_depression"] = combined[target] - combined["dewptm"]

    # 5. Safety Net for Binary Flags
    for bc in ["fog", "rain", "thunder", "hail", "tornado"]:
        if bc not in combined.columns: combined[bc] = 0

    # Modern Pandas Fill (No method='bfill')
    combined = combined.bfill().ffill().fillna(0)
    
    # FINAL SAFETY CHECK: Fill missing features with 0
    for name in feature_names:
        if name not in combined.columns: combined[name] = 0
            
    return combined[feature_names].values[-seq_len:]

# ==========================================
# 3. RESOURCE LOADER
# ==========================================
@st.cache_resource
def load_all_assets():
    path = Path("models/v2")
    with open(path / "rnn_v2_metadata.json", "r") as f: meta = json.load(f)
    
    # Load RNN
    rnn = DualBranchGRU(input_size=meta['num_features'])
    rnn.load_state_dict(torch.load(path / "best_rnn_v2.pt", map_location="cpu"))
    rnn.eval()
    rsx, rsy = joblib.load(path / "rnn_v2_scaler_X.pkl"), joblib.load(path / "rnn_v2_scaler_y.pkl")
    
    # Load TNN
    tnn = TNNModel(input_size=meta['num_features'])
    tnn_path = path / "best_tnn.pt"
    if tnn_path.exists():
        try:
            tnn.load_state_dict(torch.load(tnn_path, map_location="cpu"))
        except Exception as e:
            st.warning(f"TNN Architecture Mismatch: {e}")
    tnn.eval()
    tsx, tsy = joblib.load(path / "tnn_V2_scaler_X.pkl"), joblib.load(path / "tnn_V2_scaler_y.pkl")

    # Load History
    hist_df = pd.read_csv("weather_data.csv")
    hist_df['datetime_utc'] = pd.to_datetime(hist_df['datetime_utc'])
    
    return rnn, tnn, rsx, rsy, tsx, tsy, meta, hist_df

# ==========================================
# 4. APP UI
# ==========================================
def main():
    st.set_page_config(page_title="AtmoSense Weather AI", layout="wide")
    
    st.markdown("""<style>
    .main { background: #0f172a; color: #f8fafc; }
    .card { background: #1e293b; padding: 20px; border-radius: 15px; border: 1px solid #334155; height: 100%;}
    .metric-val { font-size: 32px; font-weight: bold; color: #60a5fa; }
    .ensemble-box { 
        background: linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%); 
        padding: 40px; border-radius: 20px; text-align: center; margin: 20px 0;
    }
    </style>""", unsafe_allow_html=True)

    try:
        rnn, tnn, rsx, rsy, tsx, tsy, meta, hist_df = load_all_assets()
        feature_names = meta['feature_names']
    except Exception as e:
        st.error(f"Initialization Error: {e}")
        return

    st.title("🌡️ Delhi Weather AI: Dual-Model Comparison")
    
    # Sidebar
    st.sidebar.header("📡 Live Simulation")
    live_t = st.sidebar.number_input("Temp (°C)", value=40.1, step=0.1)
    live_h = st.sidebar.slider("Humidity (%)", 0, 100, 35)
    live_p = st.sidebar.number_input("Pressure (hPa)", value=1005, step=1)
    
    live_entry = pd.DataFrame([{'tempm': live_t, 'hum': live_h, 'dewptm': live_t-15, 'pressurem': live_p, 
                                'wspdm': 12, 'vism': 4, 'heatindexm': live_t+2, 'windchillm': live_t, 'wgustm': 0}])

    # Logic
    with st.spinner("AI Generating Predictions..."):
        seq_data = engineer_features(live_entry, hist_df, feature_names, seq_len=72)
        
        # RNN Pred (48h)
        rnn_in = rsx.transform(seq_data[-48:])
        l_x = torch.FloatTensor(rnn_in).unsqueeze(0)
        s_x = torch.FloatTensor(rnn_in[-24:]).unsqueeze(0)
        with torch.no_grad():
            r_raw = rnn(l_x, s_x).numpy().reshape(-1, 1)
            p_rnn = float(rsy.inverse_transform(r_raw)[0][0])
        
        # TNN Pred (72h)
        tnn_in = tsx.transform(seq_data)
        t_x = torch.FloatTensor(tnn_in).unsqueeze(0)
        with torch.no_grad():
            t_raw = tnn(t_x).numpy().reshape(-1, 1)
            p_tnn = float(tsy.inverse_transform(t_raw)[0][0])
            
        # Ensemble (Weighted 65/35)
        p_ens = (p_tnn * 0.65) + (p_rnn * 0.35)

    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    results = [
        ("🌍 Live", live_t, "0.00", "#f8fafc"),
        ("🧠 TNN", p_tnn, f"{p_tnn - live_t:+.2f}", "#60a5fa"),
        ("📊 RNN", p_rnn, f"{p_rnn - live_t:+.2f}", "#a78bfa"),
        ("⚖️ Ensemble", p_ens, f"{p_ens - live_t:+.2f}", "#10b981")
    ]
    
    for i, (label, val, err, color) in enumerate(results):
        with [c1, c2, c3, c4][i]:
            st.markdown(f"""<div class="card">
                <div style="color: {color}; font-weight: bold;">{label}</div>
                <div class="metric-val">{val:.2f}°C</div>
                <div style="color: #94a3b8; font-size: 13px;">Error: {err}°C</div>
            </div>""", unsafe_allow_html=True)

    st.markdown(f"""<div class="ensemble-box">
        <p style="margin:0; letter-spacing: 2px; color: #bfdbfe;">INTEGRATED FORECAST</p>
        <div style="font-size: 72px; font-weight: 900; color: #ffffff;">{p_ens:.1f}°C</div>
    </div>""", unsafe_allow_html=True)

    # Graph
    fig = go.Figure()
    fig.add_trace(go.Bar(x=['Live', 'TNN', 'RNN', 'Ensemble'], y=[live_t, p_tnn, p_rnn, p_ens],
                         marker_color=['#475569', '#3b82f6', '#8b5cf6', '#10b981']))
    fig.update_layout(title="Model Comparison", template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()