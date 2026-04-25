"""
Prediction module using ensemble of TNN and Vanilla RNN models.
"""

import torch
import torch.nn as nn
import numpy as np
import joblib
import json
from typing import Dict, Tuple
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from src.train_tnn import TemperatureTransformer
from src.train_rnn import VanillaRNN


def detect_model_version(model_path: str) -> str:
    """
    Detect if model is v2 (TAGate-based) or original architecture.
    Returns 'v2' or 'original'
    """
    try:
        checkpoint = torch.load(model_path, map_location='cpu')
        state_dict = checkpoint if isinstance(checkpoint, dict) else checkpoint
        
        # Check for v2-specific keys
        if any(key.startswith('tag.') for key in state_dict.keys()):
            return 'v2'
        if 'encoder.layers' in str(state_dict.keys()):
            return 'v2'
        if 'transformer.layers' in str(state_dict.keys()):
            return 'original'
        
        # Default detection based on keys
        if 'proj' in str(state_dict.keys()) or 'pos_enc.pe' in state_dict:
            return 'v2'
        
        return 'original'
    except Exception as e:
        print(f"⚠️ Error detecting model version: {e}")
        return 'original'


def load_tnn_model(feature_count: int = 46, device: str = config.DEVICE) -> TemperatureTransformer:
    """
    Load trained Transformer model.
    
    Args:
        feature_count: Number of input features (default: 46 for saved model)
        device: Device to load model on
        
    Returns:
        Loaded TemperatureTransformer model or None if failed
    """
    try:
        # Detect model version
        version = detect_model_version(config.TNN_MODEL_PATH)
        print(f"📊 Detected TNN model version: {version}")
        
        # For v2 models, we need a different approach
        if version == 'v2':
            print("⚠️ TNN v2 model detected - attempting compatibility load...")
            # For v2, we can try loading with relaxed constraints
            model = TemperatureTransformer(n_features=46)
            checkpoint = torch.load(config.TNN_MODEL_PATH, map_location=device)
            
            # Load only compatible keys
            model_state = model.state_dict()
            checkpoint_state = checkpoint if isinstance(checkpoint, dict) else checkpoint
            
            compatible_keys = {k: v for k, v in checkpoint_state.items() 
                             if k in model_state and v.shape == model_state[k].shape}
            
            if compatible_keys:
                model.load_state_dict(compatible_keys, strict=False)
                print(f"✓ Loaded {len(compatible_keys)} compatible TNN weights")
            else:
                print("❌ No compatible weights found in v2 checkpoint")
        else:
            # Original model
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
        
    except Exception as e:
        print(f"❌ Error loading TNN model: {str(e)}")
        return None


def load_rnn_model(feature_count: int = 25, device: str = config.DEVICE) -> VanillaRNN:
    """
    Load trained Vanilla RNN model.
    
    Args:
        feature_count: Number of input features (default: 25 for saved model)
        device: Device to load model on
        
    Returns:
        Loaded VanillaRNN model or None if failed
    """
    try:
        # Detect model version
        version = detect_model_version(config.RNN_MODEL_PATH)
        print(f"📊 Detected RNN model version: {version}")
        
        if version == 'v2':
            print("⚠️ RNN v2 model detected - attempting compatibility load...")
            model = VanillaRNN(n_features=25, hidden_size=128, num_layers=2, dropout=0.2)
            checkpoint = torch.load(config.RNN_MODEL_PATH, map_location=device)
            
            # Load only compatible keys
            model_state = model.state_dict()
            checkpoint_state = checkpoint if isinstance(checkpoint, dict) else checkpoint
            
            compatible_keys = {k: v for k, v in checkpoint_state.items() 
                             if k in model_state and v.shape == model_state[k].shape}
            
            if compatible_keys:
                model.load_state_dict(compatible_keys, strict=False)
                print(f"✓ Loaded {len(compatible_keys)} compatible RNN weights")
            else:
                print("❌ No compatible weights found in v2 checkpoint")
        else:
            # Original model
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
        
    except Exception as e:
        print(f"❌ Error loading RNN model: {str(e)}")
        return None


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
    try:
        # Check if model is None
        if model is None:
            print("⚠️ TNN model is not loaded. Returning fallback: 20°C")
            return 20.0
        
        # Check for NaN in input
        if np.isnan(last_n_rows).any():
            print(f"⚠️ Warning: Input data contains NaN values. Replacing with 0.")
            last_n_rows = np.nan_to_num(last_n_rows, nan=0.0)
        
        X_tensor = torch.FloatTensor(last_n_rows.reshape(1, seq_len, -1)).to(device)
        
        with torch.no_grad():
            y_pred_scaled = model(X_tensor)
        
        # Inverse transform
        y_pred_scaled_np = y_pred_scaled.cpu().numpy()
        
        # Handle 2D reshape for scaler
        if y_pred_scaled_np.ndim == 1:
            y_pred_scaled_np = y_pred_scaled_np.reshape(-1, 1)
        
        y_pred = scaler_y.inverse_transform(y_pred_scaled_np)[0, 0]
        
        # Check for NaN result
        if np.isnan(y_pred):
            print(f"⚠️ Warning: TNN prediction is NaN. Returning safe default: 20°C")
            y_pred = 20.0
        
        # Clip to valid range
        y_pred = np.clip(y_pred, config.TEMP_MIN, config.TEMP_MAX)
        
        return float(y_pred)
    except Exception as e:
        print(f"❌ Error in predict_tnn: {str(e)}")
        return 20.0  # Safe fallback


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
    try:
        # Check if model is None
        if model is None:
            print("⚠️ RNN model is not loaded. Returning fallback: 20°C")
            return 20.0
        
        # Check for NaN in input
        if np.isnan(last_n_rows).any():
            print(f"⚠️ Warning: Input data contains NaN values. Replacing with 0.")
            last_n_rows = np.nan_to_num(last_n_rows, nan=0.0)
        
        X_tensor = torch.FloatTensor(last_n_rows.reshape(1, seq_len, -1)).to(device)
        
        with torch.no_grad():
            y_pred_scaled = model(X_tensor)
        
        # Inverse transform
        y_pred_scaled_np = y_pred_scaled.cpu().numpy()
        
        # Handle 2D reshape for scaler
        if y_pred_scaled_np.ndim == 1:
            y_pred_scaled_np = y_pred_scaled_np.reshape(-1, 1)
        
        y_pred = scaler_y.inverse_transform(y_pred_scaled_np)[0, 0]
        
        # Check for NaN result
        if np.isnan(y_pred):
            print(f"⚠️ Warning: RNN prediction is NaN. Returning safe default: 20°C")
            y_pred = 20.0
        
        # Clip to valid range
        y_pred = np.clip(y_pred, config.TEMP_MIN, config.TEMP_MAX)
        
        return float(y_pred)
    except Exception as e:
        print(f"❌ Error in predict_rnn: {str(e)}")
        return 20.0  # Safe fallback


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
    # Handle NaN values
    if np.isnan(tnn_pred):
        tnn_pred = rnn_pred if not np.isnan(rnn_pred) else 20.0
    if np.isnan(rnn_pred):
        rnn_pred = tnn_pred if not np.isnan(tnn_pred) else 20.0
    
    ensemble_temp = tnn_weight * tnn_pred + rnn_weight * rnn_pred
    
    # Final NaN check
    if np.isnan(ensemble_temp):
        print(f"⚠️ Warning: Ensemble still NaN. TNN={tnn_pred}, RNN={rnn_pred}. Returning 20°C")
        ensemble_temp = 20.0
    
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

