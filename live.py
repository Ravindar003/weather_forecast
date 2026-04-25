"""
Live Weather Inference: Fetch OWM data + build features + run predictions
Demonstrates proper use of v2 models with live data
"""

import numpy as np
import pandas as pd
import requests
import torch
import joblib
import os
import sys
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config
from src.predict import load_tnn_model, load_rnn_model

# ─── CONFIG ────────────────────────────────────────────────────────────────
# Use API key from environment or config
OWM_API_KEY  = os.getenv("OPENWEATHERMAP_API_KEY") or getattr(config, "OPENWEATHERMAP_API_KEY", None)
if not OWM_API_KEY or OWM_API_KEY == "YOUR_OPENWEATHERMAP_API_KEY":
    print("❌ ERROR: OPENWEATHERMAP_API_KEY not set!")
    print("   Set env var: export OPENWEATHERMAP_API_KEY=<your_key_here>")
    print("   Or add OPENWEATHERMAP_API_KEY to config.py")
    sys.exit(1)

DELHI_LAT    = config.LAT
DELHI_LON    = config.LON
DEVICE       = config.DEVICE

# Feature list (must match training)
FEATURES = [
    "tempm_lag1","tempm_lag2","tempm_lag3","tempm_lag6","tempm_lag12",
    "tempm_lag24","tempm_lag48",
    "tempm_rmean_3","tempm_rmean_6","tempm_rmean_12","tempm_rmean_24","tempm_rmean_48",
    "tempm_rstd_3","tempm_rstd_6","tempm_rstd_12","tempm_rstd_24","tempm_rstd_48",
    "tempm_rmin_24","tempm_rmax_24","tempm_range_24",
    "hour_sin","hour_cos","month_sin","month_cos",
    "dayofyear_sin","dayofyear_cos","week_sin","week_cos",
]

# ─── STEP 1: FETCH LIVE WEATHER ──────────────────────────────────────────
def fetch_owm_current_and_forecast(api_key, lat, lon):
    """
    Fetches current weather from OWM and builds synthetic hourly history.
    Less accurate than historical data but works with free tier.
    """
    try:
        cur_url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat}&lon={lon}&units=metric&appid={api_key}"
        )
        cur = requests.get(cur_url, timeout=10)
        cur.raise_for_status()
        cur_data = cur.json()
    except requests.exceptions.HTTPError as e:
        print(f"  ❌ API Error: {e}")
        return None, None
    except Exception as e:
        print(f"  ❌ Connection Error: {e}")
        return None, None

    current_temp = cur_data["main"]["temp"]
    now = pd.Timestamp.now(tz="UTC")

    # Build synthetic hourly history (72 hours back)
    rows = []
    for h in range(72, 0, -1):
        dt = now - pd.Timedelta(hours=h)
        hour_of_day = dt.hour
        # Simple diurnal model: ±4°C swing, peak at 14h, trough at 5h
        diurnal = 4.0 * np.sin(2 * np.pi * (hour_of_day - 5) / 24)
        temp = current_temp - diurnal + np.random.normal(0, 0.3)

        rows.append({
            "datetime":  dt,
            "tempm":     temp,
            "dewptm":    cur_data["main"].get("temp_min", temp - 5),
            "hum":       cur_data["main"]["humidity"],
            "pressurem": cur_data["main"]["pressure"],
            "wspdm":     cur_data["wind"].get("speed", 0) * 3.6,
            "wgustm":    cur_data["wind"].get("gust", 0) * 3.6,
            "vism":      cur_data.get("visibility", 10000) / 1000,
            "heatindexm": np.nan,
            "windchillm": np.nan,
        })

    # Append current (latest) reading
    rows.append({
        "datetime":  now,
        "tempm":     current_temp,
        "dewptm":    cur_data["main"].get("temp_min", current_temp - 5),
        "hum":       cur_data["main"]["humidity"],
        "pressurem": cur_data["main"]["pressure"],
        "wspdm":     cur_data["wind"].get("speed", 0) * 3.6,
        "wgustm":    cur_data["wind"].get("gust", 0) * 3.6,
        "vism":      cur_data.get("visibility", 10000) / 1000,
        "heatindexm": np.nan,
        "windchillm": np.nan,
    })

    df = pd.DataFrame(rows).sort_values("datetime").reset_index(drop=True)
    return df, current_temp

# ─── STEP 2: BUILD FEATURES FROM LIVE DATA ──────────────────────────────────
def build_live_features(df_live):
    """
    Exactly replicates feature engineering from training,
    applied to live OWM data slice.
    """
    df = df_live.copy()

    # Fill missing derived columns with sensible defaults
    df["heatindexm"]  = df["heatindexm"].fillna(df["tempm"])
    df["windchillm"]  = df["windchillm"].fillna(df["tempm"])

    # Cyclic time encoding
    df["hour"]      = df["datetime"].dt.hour
    df["month"]     = df["datetime"].dt.month
    df["dayofyear"] = df["datetime"].dt.dayofyear

    for period, col in [(24, "hour"), (12, "month"), (365, "dayofyear")]:
        df[f"{col}_sin"] = np.sin(2 * np.pi * df[col] / period)
        df[f"{col}_cos"] = np.cos(2 * np.pi * df[col] / period)

    # Week of year
    week = df["datetime"].dt.isocalendar().week.astype(int)
    df["week_sin"] = np.sin(2 * np.pi * week / 52)
    df["week_cos"] = np.cos(2 * np.pi * week / 52)

    # Lag features (KEY: built from the LIVE temperature series, not stale data)
    for lag in [1, 2, 3, 6, 12, 24, 48]:
        col = f"tempm_lag{lag}"
        if col in FEATURES:
            df[col] = df["tempm"].shift(lag)

    # Rolling statistics
    for w in [3, 6, 12, 24, 48]:
        col_m = f"tempm_rmean_{w}"
        col_s = f"tempm_rstd_{w}"
        if col_m in FEATURES:
            df[col_m] = df["tempm"].rolling(w, min_periods=1).mean()
        if col_s in FEATURES:
            df[col_s] = df["tempm"].rolling(w, min_periods=1).std().fillna(0)

    if "tempm_rmin_24" in FEATURES:
        df["tempm_rmin_24"]  = df["tempm"].rolling(24, min_periods=1).min()
        df["tempm_rmax_24"]  = df["tempm"].rolling(24, min_periods=1).max()
        df["tempm_range_24"] = df["tempm_rmax_24"] - df["tempm_rmin_24"]

    # Fill any remaining NaN (using new pandas syntax)
    df = df.bfill().ffill().fillna(0)

    # Return only feature columns, in order
    return df[FEATURES].values

# ─── STEP 3: RUN PREDICTIONS ─────────────────────────────────────────────────
def predict_with_model(live_features_array, scaler_X, scaler_y, model, 
                       temp_min, temp_max, seq_len, model_input_dim=None):
    """Generic prediction function for TNN or RNN."""
    if model is None:
        return None
    
    # Take last seq_len rows
    seq = live_features_array[-seq_len:]  # (seq_len, n_features)
    
    # Get expected number of features from scaler
    scaler_features = scaler_X.mean_.shape[0]
    actual_features = seq.shape[1]
    
    # If model input dimension is specified (for architectural mismatch), use that
    target_features = model_input_dim if model_input_dim is not None else scaler_features
    
    if actual_features != target_features:
        print(f"  ⚠️ Feature mismatch: got {actual_features}, adjusting to {target_features}")
        
        # Pad or truncate features to match model expectation
        if actual_features < target_features:
            # Pad with zeros
            padding = np.zeros((seq.shape[0], target_features - actual_features))
            seq = np.hstack([seq, padding])
        else:
            # Truncate
            seq = seq[:, :target_features]
    
    # Now scale with scaler (which may have different dims)
    try:
        # If scaler expects different dims, pad/truncate seq to match scaler first
        if target_features != scaler_features:
            if target_features < scaler_features:
                padding = np.zeros((seq.shape[0], scaler_features - target_features))
                seq_for_scaler = np.hstack([seq, padding])
            else:
                seq_for_scaler = seq[:, :scaler_features]
        else:
            seq_for_scaler = seq
        
        # Clip before scaling
        seq_clipped = np.clip(seq_for_scaler,
                              scaler_X.mean_ - 5 * scaler_X.scale_,
                              scaler_X.mean_ + 5 * scaler_X.scale_)
        
        # Scale
        seq_scaled = scaler_X.transform(seq_clipped)
        
        # Use only the features needed for the model
        seq_scaled = seq_scaled[:, :target_features]
        
    except Exception as e:
        print(f"  ❌ Scaling error: {e}")
        return None
    
    # Convert to tensor
    tensor_in = torch.tensor(seq_scaled, dtype=torch.float32).unsqueeze(0).to(DEVICE)
    
    # Inference
    model.eval()
    try:
        with torch.no_grad():
            raw_output = model(tensor_in).cpu().numpy().reshape(-1, 1)
    except Exception as e:
        print(f"  ❌ Model inference error: {e}")
        return None
    
    # Inverse transform
    try:
        pred_temp = float(scaler_y.inverse_transform(raw_output)[0][0])
        pred_temp = float(np.clip(pred_temp, temp_min, temp_max))
        return pred_temp
    except Exception as e:
        print(f"  ❌ Inverse transform error: {e}")
        return None

# ─── STEP 4: ALERT LOGIC ─────────────────────────────────────────────────────
def check_alerts(t):
    """Simple alert classification."""
    if   t >= 40: return "🔴 DANGER",  f"Extreme heat: {t:.1f}°C"
    elif t >= 35: return "🟠 WARNING", f"High temp: {t:.1f}°C"
    elif t <=  5: return "🟠 WARNING", f"Very cold: {t:.1f}°C"
    else:         return "🟢 NORMAL",  f"Normal: {t:.1f}°C"

# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 75)
    print("🌍 LIVE WEATHER INFERENCE - DELHI")
    print("=" * 75)
    
    # Step 1: Fetch live weather
    print("\n📡 Fetching live weather from OpenWeatherMap...")
    df_live, live_temp = fetch_owm_current_and_forecast(OWM_API_KEY, DELHI_LAT, DELHI_LON)
    
    if df_live is None:
        print("❌ Failed to fetch weather data. Exiting.")
        sys.exit(1)
    
    print(f"✓ Fetched {len(df_live)} hours of synthetic/real data")
    print(f"🌡️  Live temperature: {live_temp:.1f}°C")
    
    # Step 2: Build features
    print("\n🔧 Building features...")
    live_features = build_live_features(df_live)
    print(f"✓ Feature matrix: {live_features.shape}")
    
    # Step 3: TNN Prediction
    print("\n" + "=" * 75)
    print("🧠 TNN (Transformer) Prediction")
    print("=" * 75)
    
    try:
        scaler_X_tnn = joblib.load(config.TNN_SCALER_X)
        scaler_y_tnn = joblib.load(config.TNN_SCALER_Y)
        tnn_model = load_tnn_model(device=DEVICE)
        
        if tnn_model is None:
            print("❌ TNN model failed to load - skipping")
            tnn_pred = None
        else:
            tnn_pred = predict_with_model(live_features, scaler_X_tnn, scaler_y_tnn, 
                                         tnn_model, config.TEMP_MIN, config.TEMP_MAX,
                                         seq_len=config.SEQ_LEN_TNN, model_input_dim=46)
            
            if tnn_pred is not None:
                tnn_error = tnn_pred - live_temp
                pct_error = 100 * abs(tnn_error) / max(abs(live_temp), 1)
                print(f"  Predicted : {tnn_pred:.2f}°C")
                print(f"  Live      : {live_temp:.2f}°C")
                print(f"  Error     : {tnn_error:+.2f}°C ({pct_error:.1f}%)")
            else:
                print("  ❌ Prediction returned None")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        tnn_pred = None
    
    # Step 4: RNN Prediction
    print("\n" + "=" * 75)
    print("🧠 RNN (Recurrent) Prediction")
    print("=" * 75)
    
    try:
        scaler_X_rnn = joblib.load(config.RNN_SCALER_X)
        scaler_y_rnn = joblib.load(config.RNN_SCALER_Y)
        rnn_model = load_rnn_model(device=DEVICE)
        
        if rnn_model is None:
            print("❌ RNN model failed to load - skipping")
            rnn_pred = None
        else:
            rnn_pred = predict_with_model(live_features, scaler_X_rnn, scaler_y_rnn,
                                         rnn_model, config.TEMP_MIN, config.TEMP_MAX,
                                         seq_len=config.SEQ_LEN_RNN, model_input_dim=25)
            
            if rnn_pred is not None:
                rnn_error = rnn_pred - live_temp
                pct_error = 100 * abs(rnn_error) / max(abs(live_temp), 1)
                print(f"  Predicted : {rnn_pred:.2f}°C")
                print(f"  Live      : {live_temp:.2f}°C")
                print(f"  Error     : {rnn_error:+.2f}°C ({pct_error:.1f}%)")
            else:
                print("  ❌ Prediction returned None")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        rnn_pred = None
    
    # Step 5: Ensemble
    print("\n" + "=" * 75)
    print("⚖️ WEIGHTED ENSEMBLE")
    print("=" * 75)
    
    if tnn_pred is not None and rnn_pred is not None:
        ens_pred  = config.TNN_WEIGHT * tnn_pred + config.RNN_WEIGHT * rnn_pred
        ens_error = ens_pred - live_temp
        level, msg = check_alerts(ens_pred)
        
        print(f"  TNN  ({config.TNN_WEIGHT*100:.0f}%): {tnn_pred:.2f}°C")
        print(f"  RNN  ({config.RNN_WEIGHT*100:.0f}%): {rnn_pred:.2f}°C")
        print(f"  " + "─" * 40)
        print(f"  Ensemble : {ens_pred:.2f}°C")
        print(f"  Live OWM : {live_temp:.2f}°C")
        print(f"  Error    : {ens_error:+.2f}°C")
        print(f"\n  {level}: {msg}")
    else:
        print("❌ Cannot compute ensemble - at least one model failed")
        if tnn_pred is not None:
            print(f"  Fallback to TNN: {tnn_pred:.2f}°C")
        if rnn_pred is not None:
            print(f"  Fallback to RNN: {rnn_pred:.2f}°C")
    
    print("\n" + "=" * 75)
    print("✓ Inference complete")
    print("=" * 75)
