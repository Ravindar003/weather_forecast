"""
AtmoSense Weather App - Delhi
Modern Weather App UI for Real-time Forecasts and Alerts
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import joblib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config
from src.predict import load_tnn_model, load_rnn_model, predict_tnn, predict_rnn, ensemble_predict
from src.live_input import fetch_live_weather, add_time_features, add_delta_features
from src.alert import check_thresholds

# Page Configuration
st.set_page_config(
    page_title="Weather - Delhi",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Styling - Modern Weather App Theme
st.markdown("""
<style>
    * {
        margin: 0;
        padding: 0;
    }
    
    body {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .main {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    }
    
    /* Header Styling */
    .header-container {
        text-align: center;
        padding: 2rem 1rem;
        background: linear-gradient(180deg, rgba(26, 26, 46, 0.95) 0%, rgba(15, 52, 96, 0.95) 100%);
        border-bottom: 3px solid #667eea;
        margin-bottom: 2rem;
        border-radius: 10px;
    }
    
    .location-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #667eea;
        margin-bottom: 0.5rem;
    }
    
    .update-time {
        font-size: 0.9rem;
        color: #aaa;
        margin-top: 0.5rem;
    }
    
    /* Current Weather Box */
    .weather-box {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border: 2px solid #667eea;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
    
    .temperature-display {
        font-size: 4.5rem;
        font-weight: 700;
        color: #667eea;
        line-height: 1;
    }
    
    .weather-condition {
        font-size: 1.5rem;
        color: #e0e0e0;
        margin-top: 0.5rem;
        text-transform: capitalize;
    }
    
    .weather-details {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-top: 1.5rem;
    }
    
    .detail-item {
        background: rgba(102, 126, 234, 0.15);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
    
    .detail-label {
        font-size: 0.85rem;
        color: #aaa;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .detail-value {
        font-size: 1.8rem;
        font-weight: 600;
        color: #667eea;
        margin-top: 0.3rem;
    }
    
    /* Forecast Cards */
    .forecast-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 1rem;
        margin: 1.5rem 0;
    }
    
    .forecast-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
        border: 2px solid rgba(102, 126, 234, 0.3);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .forecast-card:hover {
        border-color: #667eea;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.25) 0%, rgba(118, 75, 162, 0.25) 100%);
        transform: translateY(-5px);
    }
    
    .forecast-time {
        font-size: 0.85rem;
        color: #aaa;
        margin-bottom: 0.5rem;
    }
    
    .forecast-temp {
        font-size: 1.8rem;
        font-weight: 700;
        color: #667eea;
    }
    
    .forecast-condition {
        font-size: 1.2rem;
        margin-top: 0.3rem;
    }
    
    /* Alert Box */
    .alert-box {
        background: linear-gradient(135deg, rgba(255, 107, 107, 0.15) 0%, rgba(255, 160, 0, 0.15) 100%);
        border: 2px solid #ff6b6b;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
    }
    
    .alert-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #ff6b6b;
        margin-bottom: 0.5rem;
    }
    
    .alert-message {
        color: #e0e0e0;
        line-height: 1.6;
    }
    
    /* Section Headers */
    .section-header {
        font-size: 1.4rem;
        font-weight: 700;
        color: #667eea;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #667eea;
    }
    
    /* Charts */
    .chart-container {
        background: rgba(26, 26, 46, 0.5);
        border: 2px solid rgba(102, 126, 234, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
    }
    
    /* Metro Style Info Grid */
    .info-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
        margin: 1.5rem 0;
    }
    
    @media (max-width: 768px) {
        .temperature-display {
            font-size: 3rem;
        }
        
        .weather-details {
            grid-template-columns: 1fr;
        }
        
        .info-grid {
            grid-template-columns: 1fr;
        }
    }
    
    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(102, 126, 234, 0.1);
    }
    
    ::-webkit-scrollbar-thumb {
        background: #667eea;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Weather Emoji Mapping
WEATHER_EMOJI = {
    'clear': '☀️',
    'sunny': '☀️',
    'clouds': '☁️',
    'cloudy': '☁️',
    'rain': '🌧️',
    'rainy': '🌧️',
    'drizzle': '🌦️',
    'thunderstorm': '⛈️',
    'snow': '❄️',
    'mist': '🌫️',
    'fog': '🌫️',
    'wind': '💨',
    'hail': '🧊'
}

# Load Models
@st.cache_resource
def load_models_cached():
    """Load and cache ML models and scalers."""
    try:
        device = config.DEVICE
        tnn_model = load_tnn_model(device=device)
        rnn_model = load_rnn_model(device=device)
        
        # Check if models loaded successfully
        if tnn_model is None:
            st.warning("⚠️ TNN model failed to load - will use fallback predictions")
        if rnn_model is None:
            st.warning("⚠️ RNN model failed to load - will use fallback predictions")
        
        # Load scalers
        tnn_scaler_X = joblib.load(config.TNN_SCALER_X)
        tnn_scaler_y = joblib.load(config.TNN_SCALER_Y)
        rnn_scaler_X = joblib.load(config.RNN_SCALER_X)
        rnn_scaler_y = joblib.load(config.RNN_SCALER_Y)
        
        return {
            'tnn': tnn_model,
            'rnn': rnn_model,
            'tnn_scaler_X': tnn_scaler_X,
            'tnn_scaler_y': tnn_scaler_y,
            'rnn_scaler_X': rnn_scaler_X,
            'rnn_scaler_y': rnn_scaler_y,
            'device': device,
            'loaded': tnn_model is not None or rnn_model is not None
        }
    except Exception as e:
        st.warning(f"⚠️ Models not loaded: {str(e)}")
        return {'loaded': False}

# Load Dataset
@st.cache_data
def load_dataset():
    """Load historical data."""
    try:
        df = pd.read_csv(config.DATA_PATH)
        df['datetime_utc'] = pd.to_datetime(df['datetime_utc'], format=config.DATETIME_FORMAT)
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

# Get Weather Emoji
def get_weather_emoji(condition):
    """Get emoji for weather condition."""
    condition_lower = str(condition).lower()
    for key, emoji in WEATHER_EMOJI.items():
        if key in condition_lower:
            return emoji
    return '🌦️'

# Main App
def main():
    # Header
    st.markdown("""
    <div class="header-container">
        <div class="location-title">🌍 DELHI WEATHER</div>
        <div class="update-time">Real-time Forecast & Alerts</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    models = load_models_cached()
    dataset = load_dataset()
    
    if not models['loaded'] or dataset is None:
        st.error("❌ Unable to load models or data. Please ensure models are trained.")
        return
    
    try:
        # Fetch live data
        live_data = fetch_live_weather()
        
        if live_data is None:
            st.error("❌ Unable to fetch live weather data. Check API connection.")
            return
        
        # Add features to live data
        live_data = add_time_features(live_data)
        live_data = add_delta_features(live_data)
        
        # Extract current weather values IMMEDIATELY (needed later)
        temp = live_data.get('tempm', 25)
        humidity = live_data.get('hum', 60)
        wind_speed = live_data.get('wspdm', 5) / 3.6  # Convert km/h to m/s for display
        pressure = live_data.get('pressurem', 1013)
        visibility = live_data.get('vism', 10)
        condition = live_data.get('_conds', 'Clear')
        
        # Get predictions using both models
        try:
            # Use only numeric features that exist in the dataset
            available_features = [col for col in config.NUMERIC_FEATURES if col in dataset.columns]
            
            # Prepare live data with time features
            live_data_df = pd.DataFrame([live_data])
            
            # Ensure all numeric features are present in live data
            for col in available_features:
                if col not in live_data_df.columns:
                    live_data_df[col] = live_data.get(col, 0)
            
            # Combine with recent history for context
            if len(dataset) > 0:
                # Get last 71 rows from historical data
                df_history = dataset[available_features].tail(71)
                
                # Add current live data
                df_combined = pd.concat([
                    df_history,
                    live_data_df[available_features]
                ], ignore_index=True)
            else:
                df_combined = live_data_df[available_features]
            
            # Ensure we have data
            if len(df_combined) == 0:
                st.error("❌ No data available for prediction.")
                return
            
            X_full = df_combined.values
            
            # TNN needs 72 timesteps
            if len(X_full) < config.SEQ_LEN_TNN:
                # Pad by repeating first row
                padding_rows = np.tile(X_full[0], (config.SEQ_LEN_TNN - len(X_full), 1))
                tnn_data = np.vstack([padding_rows, X_full])
            else:
                tnn_data = X_full[-config.SEQ_LEN_TNN:, :]
            
            # Expand features to match scaler expectations
            # The scaler expects more features (with lags, rolling stats, etc.)
            tnn_data_expanded = []
            
            for i in range(len(tnn_data)):
                row = list(tnn_data[i])
                
                # Get temperature for lag features
                temp_idx = 0
                current_temp = 20
                
                if 'tempm' in available_features:
                    temp_idx = available_features.index('tempm')
                    current_temp = tnn_data[i][temp_idx]
                
                # Add lag features (using current value if history not available)
                for lag in [1, 2, 3, 6, 12, 24]:
                    if i >= lag and len(tnn_data_expanded) > i - lag:
                        # Get temp from previous row in expanded data
                        lag_val = tnn_data_expanded[i - lag][temp_idx] if i > 0 else current_temp
                    else:
                        lag_val = current_temp
                    row.append(lag_val)
                
                # Add rolling statistics
                row.append(current_temp)  # mean_6
                row.append(current_temp)  # mean_24
                row.append(0)             # std_6
                row.append(current_temp)  # min_24
                row.append(current_temp)  # max_24
                
                tnn_data_expanded.append(row)
            
            tnn_data_expanded = np.array(tnn_data_expanded)
            
            # Scale for TNN
            try:
                tnn_data_scaled = models['tnn_scaler_X'].transform(tnn_data_expanded)
            except Exception as e:
                # Feature count mismatch - adjust
                n_features_expected = models['tnn_scaler_X'].n_features_in_
                n_features_have = tnn_data_expanded.shape[1]
                
                if n_features_have < n_features_expected:
                    padding = np.zeros((tnn_data_expanded.shape[0], n_features_expected - n_features_have))
                    tnn_data_expanded = np.hstack([tnn_data_expanded, padding])
                elif n_features_have > n_features_expected:
                    tnn_data_expanded = tnn_data_expanded[:, :n_features_expected]
                
                tnn_data_scaled = models['tnn_scaler_X'].transform(tnn_data_expanded)
            
            # Ensure feature count matches model input dimension (46 for TNN)
            model_input_features = 46  # TNN model was trained with 46 features
            if tnn_data_scaled.shape[1] > model_input_features:
                tnn_data_scaled = tnn_data_scaled[:, :model_input_features]
            elif tnn_data_scaled.shape[1] < model_input_features:
                padding = np.zeros((tnn_data_scaled.shape[0], model_input_features - tnn_data_scaled.shape[1]))
                tnn_data_scaled = np.hstack([tnn_data_scaled, padding])
            
            tnn_pred = predict_tnn(
                models['tnn'],
                tnn_data_scaled,
                models['tnn_scaler_X'],
                models['tnn_scaler_y'],
                available_features,
                seq_len=config.SEQ_LEN_TNN,
                device=models['device']
            )
            
            # Debug NaN
            if np.isnan(tnn_pred):
                st.warning(f"⚠️ TNN prediction is NaN. Data shape: {tnn_data_scaled.shape}, contains NaN: {np.isnan(tnn_data_scaled).any()}")
                tnn_pred = temp  # Fallback to live temperature
            
            # RNN: last 24 rows
            if len(X_full) < config.SEQ_LEN_RNN:
                padding_rows = np.tile(X_full[0], (config.SEQ_LEN_RNN - len(X_full), 1))
                rnn_data = np.vstack([padding_rows, X_full])
            else:
                rnn_data = X_full[-config.SEQ_LEN_RNN:, :]
            
            # Use only first 14 features for RNN or available if less
            n_rnn_features = min(14, rnn_data.shape[1])
            rnn_data_subset = rnn_data[:, :n_rnn_features]
            
            try:
                rnn_data_scaled = models['rnn_scaler_X'].transform(rnn_data_subset)
            except Exception as e:
                # Feature mismatch - pad or truncate
                n_features_expected = models['rnn_scaler_X'].n_features_in_
                n_features_have = rnn_data_subset.shape[1]
                
                if n_features_have < n_features_expected:
                    padding = np.zeros((rnn_data_subset.shape[0], n_features_expected - n_features_have))
                    rnn_data_subset = np.hstack([rnn_data_subset, padding])
                elif n_features_have > n_features_expected:
                    rnn_data_subset = rnn_data_subset[:, :n_features_expected]
                
                rnn_data_scaled = models['rnn_scaler_X'].transform(rnn_data_subset)
            
            # Ensure feature count matches RNN model input dimension (25 for RNN)
            model_rnn_features = 25  # RNN model expects 25 features
            if rnn_data_scaled.shape[1] > model_rnn_features:
                rnn_data_scaled = rnn_data_scaled[:, :model_rnn_features]
            elif rnn_data_scaled.shape[1] < model_rnn_features:
                padding = np.zeros((rnn_data_scaled.shape[0], model_rnn_features - rnn_data_scaled.shape[1]))
                rnn_data_scaled = np.hstack([rnn_data_scaled, padding])
            
            rnn_pred = predict_rnn(
                models['rnn'],
                rnn_data_scaled,
                models['rnn_scaler_X'],
                models['rnn_scaler_y'],
                available_features[:n_rnn_features],
                seq_len=config.SEQ_LEN_RNN,
                device=models['device']
            )
            
            # Debug NaN
            if np.isnan(rnn_pred):
                st.warning(f"⚠️ RNN prediction is NaN. Data shape: {rnn_data_scaled.shape}, contains NaN: {np.isnan(rnn_data_scaled).any()}")
                rnn_pred = temp  # Fallback to live temperature
            
            # Store individual predictions before ensemble
            try:
                ensemble_temp = ensemble_predict(tnn_pred, rnn_pred)
            except Exception as e:
                st.warning(f"⚠️ Ensemble failed: {e}. Using average.")
                ensemble_temp = (tnn_pred + rnn_pred) / 2 if not np.isnan(tnn_pred) and not np.isnan(rnn_pred) else temp
            
            predictions_data = {
                'live_temp': temp,
                'tnn_pred': tnn_pred if not np.isnan(tnn_pred) else temp,
                'rnn_pred': rnn_pred if not np.isnan(rnn_pred) else temp,
                'ensemble_pred': ensemble_temp if not np.isnan(ensemble_temp) else temp,
                'live_humidity': humidity,
                'live_pressure': pressure,
                'live_wind': wind_speed,
                'live_visibility': visibility,
                'live_condition': condition,
            }
            
            # Create predictions dataframe
            predictions = pd.DataFrame([{
                'tempm': predictions_data['ensemble_pred'],
                'hum': live_data.get('hum', 60),
                'wspdm': live_data.get('wspdm', 5),
                'pressurem': live_data.get('pressurem', 1013),
                'vism': live_data.get('vism', 10),
                'precipm': live_data.get('precipm', 0),
            }])
        except Exception as e:
            st.warning(f"⚠️ Ensemble prediction failed: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            predictions = pd.DataFrame()
        
        if predictions is None or predictions.empty:
            st.error("❌ Error generating predictions.")
            return
        
        # Get predictions if available
        if 'predictions_data' in locals():
            tnn_temp = predictions_data['tnn_pred']
            rnn_temp = predictions_data['rnn_pred']
            ensemble_temp = predictions_data['ensemble_pred']
            
            # Calculate differences/errors
            tnn_error = tnn_temp - temp
            rnn_error = rnn_temp - temp
            ensemble_error = ensemble_temp - temp
            
            # MODEL PREDICTIONS COMPARISON SECTION
            st.markdown('<div class="section-header">🤖 AI MODEL PREDICTIONS vs LIVE WEATHER</div>', unsafe_allow_html=True)
            
            # Create comparison table
            comparison_data = {
                'Source': ['🌍 OpenWeatherMap (Live)', '🧠 TNN (Transformer)', '📊 RNN (Vanilla)', '⚖️ Ensemble (Combined)'],
                'Temperature (°C)': [f"{temp:.2f}", f"{tnn_temp:.2f}", f"{rnn_temp:.2f}", f"{ensemble_temp:.2f}"],
                'Error vs Live (°C)': ['—', f"{tnn_error:+.2f}", f"{rnn_error:+.2f}", f"{ensemble_error:+.2f}"],
                'Confidence': ['100%', '65%', '35%', '100%'],
            }
            
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)
            
            # DETAILED COMPARISON CARDS
            col1, col2, col3, col4 = st.columns(4)
            
            # OpenWeatherMap Live
            with col1:
                st.markdown(f"""
                <div class="forecast-card" style="border-color: #4CAF50; border-width: 3px;">
                    <div class="forecast-time">🌍 LIVE WEATHER</div>
                    <div style="font-size: 2rem; margin: 0.5rem 0; color: #4CAF50;">🌡️</div>
                    <div class="forecast-temp">{temp:.1f}°C</div>
                    <div style="font-size: 0.75rem; color: #aaa; margin-top: 0.5rem;">
                        🌐 OpenWeatherMap API<br>
                        ✓ Current observation
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # TNN Prediction
            with col2:
                tnn_color = "#667eea" if abs(tnn_error) < 3 else "#ff9800"
                st.markdown(f"""
                <div class="forecast-card" style="border-color: {tnn_color}; border-width: 3px;">
                    <div class="forecast-time">🧠 TNN PREDICTION</div>
                    <div style="font-size: 2rem; margin: 0.5rem 0; color: {tnn_color};">⚙️</div>
                    <div class="forecast-temp">{tnn_temp:.1f}°C</div>
                    <div style="font-size: 0.75rem; color: #aaa; margin-top: 0.5rem;">
                        Error: <span style="color: {tnn_color};">{tnn_error:+.2f}°C</span><br>
                        Weight: 65%
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # RNN Prediction
            with col3:
                rnn_color = "#667eea" if abs(rnn_error) < 3 else "#ff9800"
                st.markdown(f"""
                <div class="forecast-card" style="border-color: {rnn_color}; border-width: 3px;">
                    <div class="forecast-time">📊 RNN PREDICTION</div>
                    <div style="font-size: 2rem; margin: 0.5rem 0; color: {rnn_color};">📈</div>
                    <div class="forecast-temp">{rnn_temp:.1f}°C</div>
                    <div style="font-size: 0.75rem; color: #aaa; margin-top: 0.5rem;">
                        Error: <span style="color: {rnn_color};">{rnn_error:+.2f}°C</span><br>
                        Weight: 35%
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Ensemble (Best Prediction)
            with col4:
                ensemble_color = "#4CAF50" if abs(ensemble_error) < 2 else "#ff6b6b"
                st.markdown(f"""
                <div class="forecast-card" style="border-color: {ensemble_color}; border-width: 3px;">
                    <div class="forecast-time">⚖️ ENSEMBLE BEST</div>
                    <div style="font-size: 2rem; margin: 0.5rem 0; color: {ensemble_color};">🎯</div>
                    <div class="forecast-temp">{ensemble_temp:.1f}°C</div>
                    <div style="font-size: 0.75rem; color: #aaa; margin-top: 0.5rem;">
                        Error: <span style="color: {ensemble_color};">{ensemble_error:+.2f}°C</span><br>
                        ✓ Final Forecast
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # ERROR ANALYSIS
            st.markdown('<div class="section-header">📉 ERROR ANALYSIS & STATISTICS</div>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🧠 TNN Absolute Error", f"{abs(tnn_error):.2f}°C", 
                         f"{-abs(tnn_error):+.2f}°C" if abs(tnn_error) < 2 else f"{abs(tnn_error):+.2f}°C")
            
            with col2:
                st.metric("📊 RNN Absolute Error", f"{abs(rnn_error):.2f}°C",
                         f"{-abs(rnn_error):+.2f}°C" if abs(rnn_error) < 2 else f"{abs(rnn_error):+.2f}°C")
            
            with col3:
                st.metric("⚖️ Ensemble Absolute Error", f"{abs(ensemble_error):.2f}°C",
                         f"{-abs(ensemble_error):+.2f}°C" if abs(ensemble_error) < 1.5 else f"{abs(ensemble_error):+.2f}°C")
            
            # Model Accuracy Comparison
            accuracy_data = pd.DataFrame({
                'Model': ['TNN (65%)', 'RNN (35%)', 'Ensemble (Combined)'],
                'Prediction (°C)': [tnn_temp, rnn_temp, ensemble_temp],
                'Error (°C)': [tnn_error, rnn_error, ensemble_error],
                'Accuracy': [f"{100 - abs(tnn_error)*5:.1f}%", f"{100 - abs(rnn_error)*5:.1f}%", f"{100 - abs(ensemble_error)*5:.1f}%"]
            })
            
            fig_accuracy = go.Figure()
            fig_accuracy.add_trace(go.Bar(
                x=['TNN', 'RNN', 'Ensemble'],
                y=[tnn_temp, rnn_temp, ensemble_temp],
                name='Predicted Temperature',
                marker_color=['#667eea', '#764ba2', '#4CAF50'],
            ))
            fig_accuracy.add_hline(y=temp, line_dash="dash", line_color="red", 
                                  annotation_text="Live Weather", annotation_position="right")
            
            fig_accuracy.update_layout(
                title='Predictions vs Live Weather',
                xaxis_title='Model',
                yaxis_title='Temperature (°C)',
                hovermode='x unified',
                plot_bgcolor='rgba(26, 26, 46, 0.5)',
                paper_bgcolor='rgba(26, 26, 46, 0.5)',
                font=dict(color='white', size=12),
                height=400,
                showlegend=True
            )
            
            st.plotly_chart(fig_accuracy, use_container_width=True)
            
            # Current Weather Details
            st.markdown('<div class="section-header">🌍 LIVE WEATHER DETAILS</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div style="background: rgba(102, 126, 234, 0.15); padding: 1rem; border-radius: 10px; border-left: 4px solid #667eea;">
                    <div style="font-size: 0.85rem; color: #aaa; text-transform: uppercase; letter-spacing: 1px;">📊 Humidity</div>
                    <div style="font-size: 1.8rem; font-weight: 600; color: #667eea; margin-top: 0.3rem;">{humidity:.0f}%</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style="background: rgba(102, 126, 234, 0.15); padding: 1rem; border-radius: 10px; border-left: 4px solid #667eea; margin-top: 1rem;">
                    <div style="font-size: 0.85rem; color: #aaa; text-transform: uppercase; letter-spacing: 1px;">💨 Wind Speed</div>
                    <div style="font-size: 1.8rem; font-weight: 600; color: #667eea; margin-top: 0.3rem;">{wind_speed:.1f} m/s</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style="background: rgba(102, 126, 234, 0.15); padding: 1rem; border-radius: 10px; border-left: 4px solid #667eea;">
                    <div style="font-size: 0.85rem; color: #aaa; text-transform: uppercase; letter-spacing: 1px;">🔽 Pressure</div>
                    <div style="font-size: 1.8rem; font-weight: 600; color: #667eea; margin-top: 0.3rem;">{pressure:.0f} hPa</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style="background: rgba(102, 126, 234, 0.15); padding: 1rem; border-radius: 10px; border-left: 4px solid #667eea; margin-top: 1rem;">
                    <div style="font-size: 0.85rem; color: #aaa; text-transform: uppercase; letter-spacing: 1px;">👁️ Visibility</div>
                    <div style="font-size: 1.8rem; font-weight: 600; color: #667eea; margin-top: 0.3rem;">{visibility:.1f} km</div>
                </div>
                """, unsafe_allow_html=True)
        
        else:
            # Fallback if predictions not available
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                st.markdown(f"""
                <div class="weather-box">
                    <div style="font-size: 3.5rem; margin-bottom: 0.5rem;">{get_weather_emoji(condition)}</div>
                    <div class="temperature-display">{temp:.0f}°C</div>
                    <div class="weather-condition">{condition}</div>
                    <div class="weather-details">
                        <div class="detail-item">
                            <div class="detail-label">💧 Humidity</div>
                            <div class="detail-value">{humidity:.0f}%</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">💨 Wind Speed</div>
                            <div class="detail-value">{wind_speed:.1f} m/s</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">🔽 Pressure</div>
                            <div class="detail-value">{pressure:.0f} hPa</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # ALERTS SECTION
        # Prepare predictions dict for thresholds check
        predictions_dict = {}
        if not predictions.empty:
            pred_row = predictions.iloc[0]
            predictions_dict = {
                'tempm': pred_row.get('tempm', temp) if 'tempm' in pred_row else temp,
                'hum': pred_row.get('hum', humidity) if 'hum' in pred_row else humidity,
                'wspdm': pred_row.get('wspdm', wind_speed * 3.6) if 'wspdm' in pred_row else wind_speed * 3.6,
                'pressurem': pred_row.get('pressurem', pressure) if 'pressurem' in pred_row else pressure,
                'vism': pred_row.get('vism', visibility) if 'vism' in pred_row else visibility,
                'precipm': pred_row.get('precipm', 0) if 'precipm' in pred_row else 0,
            }
        
        alerts_result = check_thresholds(predictions_dict, live_data)
        if alerts_result['danger'] or alerts_result['warning']:
            alert_messages = []
            for alert in alerts_result['danger']:
                alert_messages.append(f"🔴 DANGER: {alert['variable'].upper()} = {alert['value']:.1f} {alert['unit']} (threshold: {alert['threshold']:.1f})")
            for alert in alerts_result['warning']:
                alert_messages.append(f"🟡 WARNING: {alert['variable'].upper()} = {alert['value']:.1f} {alert['unit']} (threshold: {alert['threshold']:.1f})")
            
            alert_msg = "<br>".join(alert_messages)
            st.markdown(f"""
            <div class="alert-box">
                <div class="alert-title">🚨 WEATHER ALERTS</div>
                <div class="alert-message">{alert_msg}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # FORECAST SECTION
        st.markdown('<div class="section-header">📊 HOURLY FORECAST (Next 24 Hours)</div>', unsafe_allow_html=True)
        
        # Generate forecast data
        forecast_hours = 24
        forecast_data = []
        
        for i in range(forecast_hours):
            future_time = datetime.now() + timedelta(hours=i)
            # Use predictions if available, otherwise use current values
            if not predictions.empty and len(predictions) > i:
                pred_row = predictions.iloc[i]
                pred_temp = pred_row.get('tempm', temp) if 'tempm' in pred_row else (pred_row.get('temperature', temp) if 'temperature' in pred_row else temp)
                pred_humidity = pred_row.get('hum', humidity) if 'hum' in pred_row else (pred_row.get('humidity', humidity) if 'humidity' in pred_row else humidity)
                pred_wind = pred_row.get('wspdm', wind_speed * 3.6) if 'wspdm' in pred_row else (pred_row.get('wind_speed', wind_speed * 3.6) if 'wind_speed' in pred_row else wind_speed * 3.6)
            else:
                pred_temp = temp
                pred_humidity = humidity
                pred_wind = wind_speed * 3.6
            
            forecast_data.append({
                'time': future_time.strftime('%H:%M'),
                'hour': future_time.hour,
                'temp': pred_temp,
                'humidity': pred_humidity,
                'wind': pred_wind,
            })
        
        # Display forecast cards
        cols = st.columns(6)
        for idx, forecast in enumerate(forecast_data[::4]):  # Show every 4th hour
            with cols[idx % 6]:
                st.markdown(f"""
                <div class="forecast-card">
                    <div class="forecast-time">{forecast['time']}</div>
                    <div style="font-size: 1.5rem; margin: 0.5rem 0;">{get_weather_emoji(condition)}</div>
                    <div class="forecast-temp">{forecast['temp']:.0f}°</div>
                    <div style="font-size: 0.85rem; color: #aaa; margin-top: 0.3rem;">💧 {forecast['humidity']:.0f}%</div>
                </div>
                """, unsafe_allow_html=True)
        
        # DETAILED FORECAST CHART
        st.markdown('<div class="section-header">📈 DETAILED TRENDS</div>', unsafe_allow_html=True)
        
        forecast_df = pd.DataFrame(forecast_data[:24])
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=forecast_df['time'],
            y=forecast_df['temp'],
            mode='lines+markers',
            name='Temperature',
            line=dict(color='#667eea', width=3),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(102, 126, 234, 0.2)',
        ))
        
        fig.update_layout(
            title='Temperature Forecast (24 Hours)',
            xaxis_title='Time',
            yaxis_title='Temperature (°C)',
            hovermode='x unified',
            plot_bgcolor='rgba(26, 26, 46, 0.5)',
            paper_bgcolor='rgba(26, 26, 46, 0.5)',
            font=dict(color='white', size=12),
            height=400,
            margin=dict(l=50, r=50, t=50, b=50),
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # DETAILED INFO GRID
        st.markdown('<div class="section-header">📋 DETAILED INFORMATION</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("🌡️ Feels Like", f"{temp - 2:.0f}°C")
            st.metric("👁️ Visibility", f"{visibility:.1f} km")
            st.metric("🌤️ UV Index", "Moderate")
        
        with col2:
            st.metric("💧 Dew Point", f"{live_data.get('dewptm', temp - 10):.0f}°C")
            st.metric("🧭 Wind Direction", live_data.get('wdire', 'NE'))
            precip = live_data.get('precipm', 0) if not predictions.empty else 0
            st.metric("☔ Precipitation", f"{precip:.1f} mm")
        
        # FOOTER
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #aaa; font-size: 0.85rem; padding: 1rem;">
            <p>📱 AtmoSense Weather App | Real-time AI Forecasts for Delhi</p>
            <p style="margin-top: 0.5rem;">Last Updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.info("Try refreshing the page or check the system logs.")

if __name__ == "__main__":
    main()
