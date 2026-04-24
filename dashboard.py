"""
Weather Forecasting Dashboard
Web-based visualization for weather predictions using Streamlit.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

sys.path.insert(0, str(Path(__file__).parent))
import config

# Page config
st.set_page_config(
    page_title="🌤️ Weather Forecast Dashboard",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .alert-danger {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 15px;
        border-radius: 4px;
        margin: 10px 0;
    }
    .alert-warning {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 15px;
        border-radius: 4px;
        margin: 10px 0;
    }
    .alert-success {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 15px;
        border-radius: 4px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=60)
def load_predictions():
    """Load predictions from CSV log."""
    log_file = 'predictions_log.csv'
    if Path(log_file).exists():
        df = pd.read_csv(log_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['observation_time'] = pd.to_datetime(df['observation_time'])
        return df.sort_values('timestamp')
    return pd.DataFrame()


@st.cache_data(ttl=60)
def load_weather_data():
    """Load historical weather data."""
    csv_path = 'data/weather_data.csv'
    if Path(csv_path).exists():
        df = pd.read_csv(csv_path)
        df['datetime_utc'] = pd.to_datetime(df['datetime_utc'])
        return df.sort_values('datetime_utc')
    return pd.DataFrame()


def get_latest_prediction():
    """Get the most recent prediction."""
    predictions = load_predictions()
    if not predictions.empty:
        return predictions.iloc[-1]
    return None


def run_new_prediction():
    """Run a new prediction using the model."""
    from run_prediction import main as predict_main
    try:
        predict_main()
        st.success("✅ New prediction generated successfully!")
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"❌ Error generating prediction: {e}")
        return False


def create_temperature_chart(df):
    """Create interactive temperature time series chart."""
    fig = go.Figure()
    
    # Add historical data
    fig.add_trace(go.Scatter(
        x=df['datetime_utc'],
        y=df['tempm'],
        name='Observed Temperature',
        line=dict(color='#2196F3', width=2),
        hovertemplate='<b>Observed</b><br>Time: %{x}<br>Temp: %{y:.1f}°C<extra></extra>'
    ))
    
    fig.update_layout(
        title='📊 Temperature Time Series',
        xaxis_title='Date & Time',
        yaxis_title='Temperature (°C)',
        hovermode='x unified',
        height=400,
        template='plotly_white',
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig


def create_prediction_vs_actual_chart(predictions_df, weather_df):
    """Create chart comparing predictions with actuals."""
    if predictions_df.empty or weather_df.empty:
        return None
    
    # Get recent data
    recent_weather = weather_df.tail(50).copy()
    
    fig = go.Figure()
    
    # Add observed temperatures
    fig.add_trace(go.Scatter(
        x=recent_weather['datetime_utc'],
        y=recent_weather['tempm'],
        name='Observed',
        line=dict(color='#2196F3', width=2),
        hovertemplate='<b>Observed</b><br>%{x}<br>%{y:.1f}°C<extra></extra>'
    ))
    
    # Add predictions
    fig.add_trace(go.Scatter(
        x=predictions_df['observation_time'],
        y=predictions_df['temperature'],
        name='Predicted',
        mode='markers+lines',
        marker=dict(size=8, color='#FF9800'),
        line=dict(color='#FF9800', width=2, dash='dash'),
        hovertemplate='<b>Predicted</b><br>%{x}<br>%{y:.1f}°C<extra></extra>'
    ))
    
    fig.update_layout(
        title='📈 Predictions vs Observed Temperature',
        xaxis_title='Date & Time',
        yaxis_title='Temperature (°C)',
        hovermode='x unified',
        height=400,
        template='plotly_white',
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig


def create_alerts_display(latest_pred):
    """Display weather alerts."""
    if latest_pred is None:
        st.warning("⚠️ No predictions available yet.")
        return
    
    alerts = []
    
    temp = latest_pred.get('temperature', 0)
    thresholds = config.ALERT_THRESHOLDS.get('tempm', {})
    
    # Check for danger
    if 'danger' in thresholds and temp >= thresholds['danger']:
        alerts.append(('danger', f"🚨 DANGER: Temperature reached {temp:.1f}°C (Danger: ≥{thresholds['danger']}°C)"))
    
    # Check for warning
    if 'warning' in thresholds and temp >= thresholds['warning'] and (
        'danger' not in thresholds or temp < thresholds['danger']
    ):
        alerts.append(('warning', f"⚠️ WARNING: Temperature at {temp:.1f}°C (Warning: ≥{thresholds['warning']}°C)"))
    
    if not alerts:
        st.markdown('<div class="alert-success"><strong>✓ All systems normal</strong> - No weather alerts</div>', unsafe_allow_html=True)
    else:
        for alert_type, message in alerts:
            css_class = 'alert-danger' if alert_type == 'danger' else 'alert-warning'
            st.markdown(f'<div class="{css_class}">{message}</div>', unsafe_allow_html=True)


def main():
    # Header
    st.title("🌤️ Weather Forecasting Dashboard")
    st.markdown("Real-time weather predictions using PyTorch RNN neural network")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Control Panel")
        
        if st.button("🔄 Generate New Prediction", use_container_width=True, type="primary"):
            with st.spinner("Generating prediction..."):
                if run_new_prediction():
                    st.rerun()
        
        st.divider()
        
        st.subheader("📊 Dashboard Settings")
        show_raw_data = st.checkbox("Show Raw Data", value=False)
        show_statistics = st.checkbox("Show Statistics", value=True)
        prediction_range = st.slider("Display last N days", 1, 30, 7)
    
    # Load data
    predictions_df = load_predictions()
    weather_df = load_weather_data()
    latest_pred = get_latest_prediction()
    
    # Main metrics row
    if latest_pred is not None:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "🌡️ Current Prediction",
                f"{latest_pred.get('temperature', 0):.1f}°C",
                delta=None
            )
        
        with col2:
            pred_time = latest_pred.get('observation_time', 'N/A')
            st.metric(
                "⏰ Based on Data",
                f"{pd.Timestamp(pred_time).strftime('%H:%M')}" if pred_time != 'N/A' else 'N/A',
                delta=None
            )
        
        with col3:
            if not weather_df.empty:
                current_temp = weather_df.iloc[-1]['tempm']
                diff = latest_pred.get('temperature', 0) - current_temp
                st.metric(
                    "📈 Temperature Change",
                    f"{diff:+.1f}°C",
                    delta=f"{(diff/abs(current_temp)*100):+.1f}%" if current_temp != 0 else "N/A"
                )
        
        with col4:
            forecast_time = pd.Timestamp(latest_pred.get('timestamp', datetime.now()))
            now = datetime.now()
            time_since = (now - forecast_time).total_seconds() / 60
            st.metric(
                "🕐 Forecast Age",
                f"{int(time_since)} min ago" if time_since < 60 else f"{int(time_since/60)}h ago",
                delta=None
            )
    
    st.divider()
    
    # Alerts Section
    with st.container():
        st.subheader("⚠️ Weather Alerts")
        create_alerts_display(latest_pred)
    
    st.divider()
    
    # Charts section
    col1, col2 = st.columns(2)
    
    with col1:
        if not weather_df.empty:
            st.plotly_chart(
                create_temperature_chart(weather_df.tail(100)),
                use_container_width=True
            )
    
    with col2:
        if not predictions_df.empty and not weather_df.empty:
            chart = create_prediction_vs_actual_chart(predictions_df, weather_df)
            if chart:
                st.plotly_chart(chart, use_container_width=True)
            else:
                st.info("📊 Not enough data for comparison chart")
        else:
            st.info("📊 Waiting for prediction data...")
    
    st.divider()
    
    # Statistics section
    if show_statistics and not predictions_df.empty:
        st.subheader("📈 Prediction Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_temp = predictions_df['temperature'].mean()
            st.metric("Average Predicted Temperature", f"{avg_temp:.1f}°C")
        
        with col2:
            max_temp = predictions_df['temperature'].max()
            st.metric("Highest Prediction", f"{max_temp:.1f}°C")
        
        with col3:
            min_temp = predictions_df['temperature'].min()
            st.metric("Lowest Prediction", f"{min_temp:.1f}°C")
        
        # Prediction distribution chart
        fig = px.histogram(
            predictions_df,
            x='temperature',
            nbins=20,
            title='📊 Temperature Prediction Distribution',
            labels={'temperature': 'Temperature (°C)', 'count': 'Frequency'},
            color_discrete_sequence=['#2196F3']
        )
        fig.update_layout(height=350, template='plotly_white')
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Prediction History
    st.subheader("📋 Prediction History")
    
    if not predictions_df.empty:
        # Filter by date range
        if len(predictions_df) > 0:
            cutoff_date = datetime.now() - timedelta(days=prediction_range)
            display_df = predictions_df[predictions_df['timestamp'] >= cutoff_date].copy()
        else:
            display_df = predictions_df.copy()
        
        # Format for display
        display_df = display_df[['timestamp', 'observation_time', 'temperature']].copy()
        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        display_df['observation_time'] = display_df['observation_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
        display_df['temperature'] = display_df['temperature'].apply(lambda x: f'{x:.2f}°C')
        display_df = display_df.rename(columns={
            'timestamp': 'Prediction Time',
            'observation_time': 'Observation Time',
            'temperature': 'Temperature'
        })
        
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("📊 No predictions yet. Click 'Generate New Prediction' to start.")
    
    # Raw Data Section
    if show_raw_data:
        st.divider()
        st.subheader("🔍 Raw Data")
        
        tab1, tab2 = st.tabs(["Predictions", "Weather Data"])
        
        with tab1:
            if not predictions_df.empty:
                st.dataframe(predictions_df, use_container_width=True)
            else:
                st.info("No prediction data available")
        
        with tab2:
            if not weather_df.empty:
                st.dataframe(weather_df.tail(50), use_container_width=True)
            else:
                st.info("No weather data available")
    
    # Footer
    st.divider()
    st.markdown("""
        <div style='text-align: center; color: #666; font-size: 0.9em; margin-top: 2rem;'>
            <p>🌤️ Weather Forecasting System | Powered by PyTorch RNN Neural Network</p>
            <p>Last updated: {}</p>
        </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
