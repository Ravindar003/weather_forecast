"""
Simplified PyTorch prediction without strict feature alignment.
Uses all available numeric features that can be scaled.
"""

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import joblib
import sys
from pathlib import Path
from datetime import datetime
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
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VanillaRNNPyTorch(nn.Module):
    """PyTorch RNN for weather forecasting - matches trained model."""
    
    def __init__(self, input_size=25):
        super().__init__()
        # Two stacked RNN layers with 128 units each
        self.rnn = nn.RNN(input_size, 128, batch_first=True, num_layers=2, dropout=0.2)
        
        # FC layers matching checkpoint: 128 -> 128 -> 64 -> 1
        self.fc = nn.Sequential(
            nn.Linear(128, 128),     # fc.0
            nn.BatchNorm1d(128),      # fc.1
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),       # fc.4
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 1)          # fc.7
        )
    
    def forward(self, x):
        # x shape: (batch, seq_len, input_size)
        out, _ = self.rnn(x)
        # Take last output from last RNN layer
        out = out[:, -1, :]  # Shape: (batch, 128)
        out = self.fc(out)   # Shape: (batch, 1)
        return out


def main():
    logger.info("=" * 70)
    logger.info("🌤️  WEATHER FORECASTING SYSTEM - PyTorch RNN Predictions")
    logger.info("=" * 70)
    
    try:
        # Load and prepare data
        logger.info("\n1️⃣  Loading and preparing data...")
        df = load_and_clean_data('data/weather_data.csv')
        logger.info(f"   ✓ Loaded {len(df)} records")
        
        df = engineer_time_features(df)
        logger.info(f"   ✓ Added time features")
        
        df = engineer_delta_features(df)
        logger.info(f"   ✓ Added delta features")
        
        df = engineer_lag_features(df)
        logger.info(f"   ✓ Added lag features ({len(df)} rows after lag cutoff)")
        
        # Get all numeric features available
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        logger.info(f"   ✓ Found {len(numeric_cols)} numeric features")
        
        # Get last 72 hours (or all if less)
        lookback = min(72, len(df))
        df_recent = df.iloc[-lookback:].copy()
        logger.info(f"   ✓ Using last {len(df_recent)} hours")
        
        # Load scaler
        logger.info("\n2️⃣  Loading scalers...")
        scaler_X = joblib.load('models/scaler_X.pkl')
        scaler_y = joblib.load('models/scaler_y.pkl')
        logger.info(f"   ✓ Scaler_X: {scaler_X.n_features_in_} features")
        logger.info(f"   ✓ Scaler_y: {scaler_y.n_features_in_} output(s)")
        
        # Get features in order - match what scaler expects
        # The scaler was trained on specific features - try to use the right ones
        feature_subset = numeric_cols[:scaler_X.n_features_in_]  # Take first N features that match scaler
        logger.info(f"   Using features: {feature_subset}")
        
        X = df_recent[feature_subset].values
        logger.info(f"   ✓ Feature matrix shape: {X.shape}")
        
        # Scale
        X_scaled = scaler_X.transform(X)
        X_tensor = torch.FloatTensor(np.expand_dims(X_scaled, axis=0))
        logger.info(f"   ✓ Scaled shape: {X_tensor.shape}")
        
        # Load model
        logger.info("\n3️⃣  Loading PyTorch model...")
        device = torch.device('cpu')
        model = VanillaRNNPyTorch(input_size=scaler_X.n_features_in_)
        model.load_state_dict(torch.load('models/best_vanilla_rnn.pt', map_location=device))
        model.to(device)
        model.eval()
        logger.info("   ✓ Model loaded successfully")
        
        # Make prediction
        logger.info("\n4️⃣  Running inference...")
        with torch.no_grad():
            y_pred_scaled = model(X_tensor.to(device)).cpu().numpy()
        logger.info(f"   ✓ Prediction (scaled): {y_pred_scaled}")
        
        # Inverse scale
        y_pred = scaler_y.inverse_transform(y_pred_scaled)
        logger.info(f"   ✓ Prediction (real values): {y_pred}")
        
        # Display results - Note: This model predicts only 1 target (temperature)
        logger.info("\n" + "=" * 70)
        logger.info("📊 PREDICTION RESULTS")
        logger.info("=" * 70)
        logger.info(f"Latest observation: {df_recent.index[-1]}")
        logger.info(f"Forecast time: {datetime.now()}\n")
        
        # Get current temperature
        if 'tempm' in df_recent.columns:
            current_temp = float(df_recent['tempm'].iloc[-1])
            predicted_temp = float(y_pred[0, 0])
            change = predicted_temp - current_temp
            change_pct = (change / abs(current_temp) * 100) if abs(current_temp) > 0 else 0
            change_str = f"{change:+.2f}°C ({change_pct:+.1f}%)"
            
            print(f"{'Temperature (tempm)':<30} {'Current':<15} {'Predicted':<15}")
            print("-" * 60)
            print(f"{'':30} {current_temp:>14.2f}°C {predicted_temp:>14.2f}°C")
            print(f"{'Change':30} {change_str:>44}")
        
        print("=" * 70 + "\n")
        
        pred_dict = {'temperature': float(y_pred[0, 0])}
        
        # Check alerts
        logger.info("\n⚠️  Checking alert thresholds...")
        alerts = []
        
        # Check temperature alert
        if 'tempm' in config.ALERT_THRESHOLDS:
            pred_temp = pred_dict['temperature']
            thresholds = config.ALERT_THRESHOLDS['tempm']
            
            if 'danger' in thresholds and pred_temp >= thresholds['danger']:
                alerts.append(f"🚨 DANGER: Temperature = {pred_temp:.2f}°C (threshold: {thresholds['danger']}°C)")
            elif 'warning' in thresholds and pred_temp >= thresholds['warning']:
                alerts.append(f"⚠️  WARNING: Temperature = {pred_temp:.2f}°C (threshold: {thresholds['warning']}°C)")
        
        if alerts:
            for alert in alerts:
                logger.warning(alert)
        else:
            logger.info("   ✓ No temperature alerts")
        
        # Save predictions
        pred_log = pd.DataFrame([{
            'timestamp': datetime.now(),
            'observation_time': df_recent.index[-1],
            **pred_dict
        }])
        
        log_file = 'predictions_log.csv'
        try:
            existing = pd.read_csv(log_file)
            pred_log = pd.concat([existing, pred_log], ignore_index=True)
        except:
            pass
        
        pred_log.to_csv(log_file, index=False)
        logger.info(f"\n✓ Predictions saved to {log_file}")
        
    except Exception as e:
        logger.error(f"\n✗ Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
