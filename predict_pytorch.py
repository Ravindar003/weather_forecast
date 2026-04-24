"""
Prediction script using PyTorch RNN model.
Makes weather predictions using the trained vanilla RNN model.
"""

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import joblib
import sys
from pathlib import Path
from datetime import datetime, timedelta
import logging

sys.path.insert(0, str(Path(__file__).parent))
import config
from src.preprocess import (
    load_and_clean_data, 
    engineer_time_features, 
    engineer_delta_features,
    engineer_lag_features
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VanillaRNNPyTorch(nn.Module):
    """PyTorch implementation of Vanilla RNN for weather forecasting."""
    
    def __init__(self, input_size=25, hidden_units=[128, 64], output_size=6, dropout=0.2):
        super(VanillaRNNPyTorch, self).__init__()
        self.rnn = nn.RNN(input_size, hidden_units[0], batch_first=True, dropout=dropout)
        self.rnn2 = nn.RNN(hidden_units[0], hidden_units[1], batch_first=True)
        self.fc = nn.Sequential(
            nn.Linear(hidden_units[1], 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Linear(32, output_size)
        )
    
    def forward(self, x):
        # x shape: (batch, seq_len, input_size)
        out, _ = self.rnn(x)
        out, _ = self.rnn2(out)
        # Take last output
        out = out[:, -1, :]
        out = self.fc(out)
        return out


def prepare_prediction_data(csv_path: str, lookback: int = 72) -> tuple:
    """
    Load and prepare data for prediction.
    
    Args:
        csv_path: Path to weather CSV data
        lookback: Number of hours to look back
    
    Returns:
        Tuple of (sequence, df, scaler_X, scaler_y)
    """
    logger.info("Loading and preparing data for prediction...")
    
    # Load and clean data
    df = load_and_clean_data(csv_path)
    
    # Engineer features
    df = engineer_time_features(df)
    df = engineer_delta_features(df)
    df = engineer_lag_features(df, target_col='tempm', lags=[1, 3, 6, 12, 24])
    
    logger.info(f"Data shape after feature engineering: {df.shape}")
    logger.info(f"Available columns: {df.columns.tolist()}")
    
    # Get last 72 hours
    if len(df) < lookback:
        logger.warning(f"Only {len(df)} rows available, need {lookback}")
        lookback = len(df)
    
    df_recent = df.iloc[-lookback:].copy()
    logger.info(f"Using last {len(df_recent)} hours for prediction")
    
    # Select features in correct order
    # Filter out non-numeric columns that can't be scaled
    available_features = [col for col in config.FEATURE_COLS if col in df_recent.columns and df_recent[col].dtype != 'object']
    
    logger.info(f"Using features: {available_features}")
    logger.info(f"Feature count: {len(available_features)}")
    
    X = df_recent[available_features].values
    
    # Load scaler
    scaler_X = joblib.load('models/scaler_X.pkl')
    scaler_y = joblib.load('models/scaler_y.pkl')
    
    # Scale features
    X_scaled = scaler_X.transform(X)
    
    # Reshape to (1, seq_len, n_features) for batch prediction
    X_scaled = np.expand_dims(X_scaled, axis=0)
    
    logger.info(f"Scaled input shape: {X_scaled.shape}")
    
    return X_scaled, df_recent, scaler_X, scaler_y


def make_predictions(model_path: str = 'models/best_vanilla_rnn.pt', 
                     csv_path: str = 'data/weather_data.csv') -> dict:
    """
    Load model and make predictions.
    
    Args:
        model_path: Path to PyTorch model
        csv_path: Path to weather data
    
    Returns:
        Dictionary with predictions and metadata
    """
    logger.info("=" * 60)
    logger.info("WEATHER FORECASTING - PYTORCH RNN PREDICTION")
    logger.info("=" * 60)
    
    # Prepare data
    X_scaled, df_recent, scaler_X, scaler_y = prepare_prediction_data(csv_path)
    
    # Load model
    logger.info(f"Loading model from {model_path}")
    device = torch.device('cpu')
    
    model = VanillaRNNPyTorch(
        input_size=25,
        hidden_units=[128, 64],
        output_size=6,
        dropout=0.2
    )
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    logger.info("✓ Model loaded successfully")
    
    # Make prediction
    with torch.no_grad():
        X_tensor = torch.FloatTensor(X_scaled).to(device)
        y_pred_scaled = model(X_tensor).cpu().numpy()
    
    logger.info(f"Prediction shape: {y_pred_scaled.shape}")
    
    # Inverse scale predictions
    y_pred = scaler_y.inverse_transform(y_pred_scaled)
    logger.info("✓ Predictions generated and inverse-scaled")
    
    # Format results
    prediction_dict = {
        'timestamp': datetime.now(),
        'lookback_hours': len(df_recent),
        'latest_observation_time': df_recent.index[-1],
        'predictions': {}
    }
    
    for i, target_col in enumerate(config.TARGET_COLS):
        pred_value = y_pred[0, i]
        prediction_dict['predictions'][target_col] = float(pred_value)
    
    # Get current values for comparison
    latest_row = df_recent.iloc[-1]
    prediction_dict['current_values'] = {col: float(latest_row[col]) for col in config.TARGET_COLS}
    
    return prediction_dict


def print_predictions(predictions: dict) -> None:
    """Pretty print predictions."""
    print("\n" + "=" * 70)
    print("🌤️  WEATHER PREDICTION RESULTS")
    print("=" * 70)
    print(f"Prediction Time: {predictions['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Based on: {predictions['lookback_hours']} hours of data")
    print(f"Latest observation: {predictions['latest_observation_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 70)
    
    print(f"\n{'Metric':<20} {'Current':<15} {'Predicted':<15} {'Change':<15}")
    print("-" * 70)
    
    for target in config.TARGET_COLS:
        current = predictions['current_values'].get(target, 0)
        predicted = predictions['predictions'].get(target, 0)
        change = predicted - current
        change_pct = (change / abs(current) * 100) if current != 0 else 0
        
        change_str = f"{change:+.2f} ({change_pct:+.1f}%)" if abs(current) > 0 else f"{change:+.2f}"
        
        print(f"{target:<20} {current:>14.2f} {predicted:>14.2f} {change_str:>14}")
    
    print("=" * 70 + "\n")


def check_alerts(predictions: dict) -> list:
    """Check if predictions exceed alert thresholds."""
    alerts = []
    
    for target, pred_value in predictions['predictions'].items():
        if target not in config.ALERT_THRESHOLDS:
            continue
        
        thresholds = config.ALERT_THRESHOLDS[target]
        
        # Check if reversed (lower is worse, like visibility)
        is_reversed = thresholds.get('reversed', False)
        
        # Check danger threshold
        if 'danger' in thresholds:
            danger_val = thresholds['danger']
            if (not is_reversed and pred_value >= danger_val) or (is_reversed and pred_value <= danger_val):
                alerts.append(f"🚨 DANGER: {target} predicted to be {pred_value:.2f}")
        
        # Check warning threshold
        if 'warning' in thresholds:
            warning_val = thresholds['warning']
            if (not is_reversed and pred_value >= warning_val) or (is_reversed and pred_value <= warning_val):
                if 'danger' not in thresholds or pred_value < thresholds['danger']:
                    alerts.append(f"⚠️  WARNING: {target} predicted to be {pred_value:.2f}")
    
    return alerts


if __name__ == "__main__":
    try:
        # Make predictions
        predictions = make_predictions()
        
        # Display results
        print_predictions(predictions)
        
        # Check for alerts
        alerts = check_alerts(predictions)
        if alerts:
            print("\n⚠️  ALERTS:")
            for alert in alerts:
                print(f"  {alert}")
        else:
            print("✓ No weather alerts")
        
        # Save predictions log
        pred_log = pd.DataFrame([{
            'timestamp': predictions['timestamp'],
            'latest_observation': predictions['latest_observation_time'],
            **predictions['predictions']
        }])
        
        # Append to predictions log if exists
        log_file = 'predictions_log.csv'
        try:
            existing = pd.read_csv(log_file)
            pred_log = pd.concat([existing, pred_log], ignore_index=True)
        except FileNotFoundError:
            pass
        
        pred_log.to_csv(log_file, index=False)
        logger.info(f"✓ Predictions saved to {log_file}")
        
    except Exception as e:
        logger.error(f"Error during prediction: {str(e)}", exc_info=True)
        sys.exit(1)
