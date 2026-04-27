import streamlit as st
import pandas as pd
import numpy as np
import torch
import joblib
from datetime import datetime
import requests

# ============================
# LOAD MODELS
# ============================
@st.cache_resource
def load_models():
    rnn = torch.load("models/rnn.pt", map_location="cpu")
    tnn = torch.load("models/tnn.pt", map_location="cpu")
    rnn.eval()
    tnn.eval()

    scaler_X = joblib.load("models/scaler_X.pkl")
    scaler_y = joblib.load("models/scaler_y.pkl")

    hist_df = pd.read_csv("weather_data.csv")
    return rnn, tnn, scaler_X, scaler_y, hist_df

# ============================
# FETCH LIVE DATA
# ============================
def fetch_weather(api_key):
    url = f"https://api.openweathermap.org/data/2.5/weather?q=Delhi&appid={api_key}&units=metric"
    res = requests.get(url).json()

    return {
        "temp": res["main"]["temp"],
        "humidity": res["main"]["humidity"],
        "pressure": res["main"]["pressure"],
        "wind": res["wind"]["speed"]
    }

# ============================
# FEATURE ENGINEERING (SIMPLE)
# ============================
def create_sequence(hist_df, current_temp):
    hist = hist_df.copy()

    # add latest temp
    new_row = hist.iloc[-1].copy()
    new_row["tempm"] = current_temp
    hist = pd.concat([hist, pd.DataFrame([new_row])])

    # take last 72 rows
    seq = hist.tail(72)

    return seq[["tempm"]].values

# ============================
# MAIN APP
# ============================
def main():
    st.title("🌡️ Weather AI Prediction System")

    rnn, tnn, scaler_X, scaler_y, hist_df = load_models()

    api_key = st.sidebar.text_input("API Key")

    if api_key:
        data = fetch_weather(api_key)
        temp = data["temp"]
    else:
        temp = st.sidebar.number_input("Temperature", value=40.0)

    st.write("### 🌍 Live Temperature:", temp)

    # ============================
    # FIXED PREDICTION PIPELINE
    # ============================
    seq = create_sequence(hist_df, temp)

    seq_scaled = scaler_X.transform(seq)

    x = torch.tensor(seq_scaled, dtype=torch.float32).unsqueeze(0)

    with torch.no_grad():
        rnn_pred = rnn(x).numpy().reshape(-1, 1)
        tnn_pred = tnn(x).numpy().reshape(-1, 1)

    p_rnn = scaler_y.inverse_transform(rnn_pred)[0][0]
    p_tnn = scaler_y.inverse_transform(tnn_pred)[0][0]

    # ============================
    # SMART ADJUSTMENT (FIX)
    # ============================
    last_temp = hist_df["tempm"].iloc[-1]
    adjustment = temp - last_temp

    p_rnn += 0.5 * adjustment
    p_tnn += 0.5 * adjustment

    # Clamp
    p_rnn = np.clip(p_rnn, temp - 5, temp + 5)
    p_tnn = np.clip(p_tnn, temp - 5, temp + 5)

    # Ensemble
    p_ens = (p_tnn * 0.65) + (p_rnn * 0.35)

    # ============================
    # DISPLAY
    # ============================
    col1, col2, col3 = st.columns(3)

    col1.metric("🧠 TNN", f"{p_tnn:.2f}°C")
    col2.metric("📊 RNN", f"{p_rnn:.2f}°C")
    col3.metric("⚖️ Ensemble", f"{p_ens:.2f}°C")

    st.write("### Error vs Live")
    st.write("TNN Error:", round(p_tnn - temp, 2))
    st.write("RNN Error:", round(p_rnn - temp, 2))
    st.write("Ensemble Error:", round(p_ens - temp, 2))


if __name__ == "__main__":
    main()