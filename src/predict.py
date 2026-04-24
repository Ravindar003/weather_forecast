"""
Prediction module using ensemble of TNN and Vanilla RNN models.
"""

import torch
import torch.nn as nn
import numpy as np
import joblib
from typing import Dict, Tuple
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from src.train_tnn import TemperatureTransformer
from src.train_rnn import VanillaRNN


def load_tnn_model(feature_count: int = 46, device: str = config.DEVICE) -> TemperatureTransformer:
    """
    Load trained Transformer model.
    
    Args:
        feature_count: Number of input features (default: 46 for saved model)
        device: Device to load model on
        
    Returns:
        Loaded TemperatureTransformer model
    """
    # Use fixed feature count that matches saved model
    model = TemperatureTransformer(
        n_features=46,
        d_model=128,
        nhead=4,
        num_layers=4,
        dim_feedforward=512,
        dropout=0.1
    )
    model.load_state_dict(torch.load(config.TNN_MODEL_PATH, map_location=device))
    model.to(device)
    model.eval()
    return model


def load_rnn_model(feature_count: int = 25, device: str = config.DEVICE) -> VanillaRNN:
    """
    Load trained Vanilla RNN model.
    
    Args:
        feature_count: Number of input features (default: 25 for saved model)
        device: Device to load model on
        
    Returns:
        Loaded VanillaRNN model
    """
    # Use fixed feature count that matches saved model
    model = VanillaRNN(
        n_features=25,
        hidden_size=128,
        num_layers=2,
        dropout=0.2
    )
    model.load_state_dict(torch.load(config.RNN_MODEL_PATH, map_location=device))
    model.to(device)
    model.eval()
    return model


def predict_tnn(model: nn.Module, last_n_rows: np.ndarray, 
                scaler_X: object, scaler_y: object, 
                features: list, seq_len: int = 72, 
                device: str = config.DEVICE) -> float:
    """
    Predict temperature using Transformer model.
    
    Args:
        model: Trained TNN model
        last_n_rows: Last N rows of scaled features (seq_len, n_features)
        scaler_X: Input scaler
        scaler_y: Output scaler
        features: Feature column names
        seq_len: Sequence length
        device: Device to run on
        
    Returns:
        Predicted temperature
    """
    X_tensor = torch.FloatTensor(last_n_rows.reshape(1, seq_len, -1)).to(device)
    
    with torch.no_grad():
        y_pred_scaled = model(X_tensor)
    
    # Inverse transform
    y_pred_scaled_np = y_pred_scaled.cpu().numpy()
    y_pred = scaler_y.inverse_transform(y_pred_scaled_np)[0, 0]
    
    # Clip to valid range
    y_pred = np.clip(y_pred, config.TEMP_MIN, config.TEMP_MAX)
    
    return float(y_pred)


def predict_rnn(model: nn.Module, last_n_rows: np.ndarray, 
               scaler_X: object, scaler_y: object, 
               features: list, seq_len: int = 24, 
               device: str = config.DEVICE) -> float:
    """
    Predict temperature using RNN model.
    
    Args:
        model: Trained RNN model
        last_n_rows: Last N rows of scaled features (seq_len, n_features)
        scaler_X: Input scaler
        scaler_y: Output scaler
        features: Feature column names
        seq_len: Sequence length
        device: Device to run on
        
    Returns:
        Predicted temperature
    """
    X_tensor = torch.FloatTensor(last_n_rows.reshape(1, seq_len, -1)).to(device)
    
    with torch.no_grad():
        y_pred_scaled = model(X_tensor)
    
    # Inverse transform
    y_pred_scaled_np = y_pred_scaled.cpu().numpy()
    y_pred = scaler_y.inverse_transform(y_pred_scaled_np)[0, 0]
    
    # Clip to valid range
    y_pred = np.clip(y_pred, config.TEMP_MIN, config.TEMP_MAX)
    
    return float(y_pred)


def ensemble_predict(tnn_pred: float, rnn_pred: float,
                    tnn_weight: float = config.TNN_WEIGHT, 
                    rnn_weight: float = config.RNN_WEIGHT) -> float:
    """
    Combine predictions using weighted ensemble.
    
    Args:
        tnn_pred: TNN model prediction
        rnn_pred: RNN model prediction
        tnn_weight: Weight for TNN
        rnn_weight: Weight for RNN
        
    Returns:
        Ensemble prediction
    """
    ensemble_temp = tnn_weight * tnn_pred + rnn_weight * rnn_pred
    return float(ensemble_temp)


def evaluate_model(model: nn.Module, test_loader: torch.utils.data.DataLoader, 
                  scaler_y: object, device: str = config.DEVICE) -> Dict:
    """
    Evaluate model on test set.
    
    Args:
        model: Trained model
        test_loader: DataLoader for test set
        scaler_y: Output scaler
        device: Device to run on
        
    Returns:
        Dictionary with metrics
    """
    model.eval()
    predictions = []
    actuals = []
    
    with torch.no_grad():
        for X_batch, y_batch in test_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            y_pred = model(X_batch)
            
            predictions.append(y_pred.cpu().numpy())
            actuals.append(y_batch.cpu().numpy())
    
    predictions = np.concatenate(predictions, axis=0).ravel()
    actuals = np.concatenate(actuals, axis=0).ravel()
    
    # Inverse transform
    predictions = scaler_y.inverse_transform(predictions.reshape(-1, 1)).ravel()
    actuals = scaler_y.inverse_transform(actuals.reshape(-1, 1)).ravel()
    
    # Calculate metrics
    mae = np.mean(np.abs(predictions - actuals))
    rmse = np.sqrt(np.mean((predictions - actuals) ** 2))
    ss_res = np.sum((actuals - predictions) ** 2)
    ss_tot = np.sum((actuals - np.mean(actuals)) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    
    return {
        'mae': mae,
        'rmse': rmse,
        'r2': r2,
        'preds': predictions,
        'actuals': actuals
    }

