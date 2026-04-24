"""
Data preprocessing module for weather forecasting.
Handles cleaning, feature engineering, and sequence creation.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
from typing import Tuple, List
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
import config


def load_and_clean(path: str) -> pd.DataFrame:
    """
    Load and clean the weather dataset.
    
    Args:
        path: Path to the CSV file
        
    Returns:
        Cleaned pandas DataFrame
    """
    print("📊 Loading dataset...")
    df = pd.read_csv(path)
    
    print(f"Original shape: {df.shape}")
    
    # Parse datetime
    print("🕐 Parsing datetime column...")
    df['datetime_utc'] = pd.to_datetime(df['datetime_utc'], format=config.DATETIME_FORMAT)
    df = df.sort_values('datetime_utc').reset_index(drop=True)
    
    # Replace sentinel values with NaN
    print("🔧 Replacing sentinel values...")
    for col in df.columns:
        if col != 'datetime_utc':
            df[col] = df[col].replace(config.SENTINEL_VALUES, np.nan)
    
    # Clip temperature to valid range
    print(f"📍 Clipping temperature to [{config.TEMP_MIN}, {config.TEMP_MAX}]°C...")
    df[config.TARGET] = df[config.TARGET].clip(config.TEMP_MIN, config.TEMP_MAX)
    
    # Fill NaN values: forward fill + linear interpolation (numeric columns only)
    print("🔨 Filling NaN values...")
    numeric_cols = df.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        df[col] = df[col].ffill().interpolate(method='linear')
    
    # Drop remaining NaN
    df = df.dropna()
    
    print(f"Cleaned shape: {df.shape}")
    print("✅ Data cleaning complete!\n")
    
    return df


def engineer_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Engineer features for the model.
    
    Args:
        df: Cleaned DataFrame with datetime_utc index
        
    Returns:
        DataFrame with engineered features and list of feature names
    """
    print("🔨 Engineering features...")
    df = df.copy()
    
    # Extract time components
    df['hour'] = df['datetime_utc'].dt.hour
    df['month'] = df['datetime_utc'].dt.month
    df['day'] = df['datetime_utc'].dt.day
    
    # Cyclic encoding
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    df['day_sin'] = np.sin(2 * np.pi * df['day'] / 31)
    df['day_cos'] = np.cos(2 * np.pi * df['day'] / 31)
    
    # Lags for temperature
    for lag in [1, 2, 3, 6, 12, 24]:
        df[f'tempm_lag{lag}'] = df[config.TARGET].shift(lag)
    
    # Rolling statistics
    df['tempm_mean_6'] = df[config.TARGET].rolling(window=6, min_periods=1).mean()
    df['tempm_mean_24'] = df[config.TARGET].rolling(window=24, min_periods=1).mean()
    df['tempm_std_6'] = df[config.TARGET].rolling(window=6, min_periods=1).std().fillna(0)
    df['tempm_min_24'] = df[config.TARGET].rolling(window=24, min_periods=1).min()
    df['tempm_max_24'] = df[config.TARGET].rolling(window=24, min_periods=1).max()
    
    # Lags for other features
    lag_features = ['dewptm', 'hum', 'pressurem', 'wspdm', 'heatindexm', 
                   'windchillm', 'vism', 'wgustm']
    for feat in lag_features:
        if feat in df.columns:
            df[f'{feat}_lag1'] = df[feat].shift(1)
            df[f'{feat}_lag6'] = df[feat].shift(6)
    
    # Ensure binary flags exist (0 or 1)
    for col in ['fog', 'rain', 'thunder', 'hail', 'tornado']:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)
    
    # Derived features
    if 'heatindexm' in df.columns and config.TARGET in df.columns:
        df['heat_delta'] = df['heatindexm'] - df[config.TARGET]
    if 'windchillm' in df.columns and config.TARGET in df.columns:
        df['chill_delta'] = df['windchillm'] - df[config.TARGET]
    
    # Drop time component columns (not needed for model)
    df = df.drop(['hour', 'month', 'day', 'datetime_utc'], axis=1, errors='ignore')
    
    # Drop non-numeric columns (strings like _conds, wdire)
    df = df.select_dtypes(include=['number', 'int64', 'float64'])
    
    # Fill any remaining NaN from lags and rolling
    df = df.bfill().ffill().dropna()
    
    # Build feature list
    feature_cols = [col for col in df.columns if col != config.TARGET]
    
    print(f"✅ Engineered {len(feature_cols)} features\n")
    
    return df, feature_cols


def create_sequences(X: np.ndarray, y: np.ndarray, 
                    seq_len: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create sliding window sequences.
    
    Args:
        X: Feature array (n_samples, n_features)
        y: Target array (n_samples,)
        seq_len: Sequence length
        
    Returns:
        X_seq (n_sequences, seq_len, n_features) and y_seq (n_sequences,)
    """
    X_seq = []
    y_seq = []
    
    for i in range(len(X) - seq_len):
        X_seq.append(X[i:i+seq_len])
        y_seq.append(y[i+seq_len])
    
    return np.array(X_seq), np.array(y_seq)


def split_and_scale(X_seq: np.ndarray, y_seq: np.ndarray,
                   scaler_x_path: str, scaler_y_path: str) -> Tuple:
    """
    Split data into train/val/test and scale.
    
    Args:
        X_seq: Sequence features (n_sequences, seq_len, n_features)
        y_seq: Sequence targets (n_sequences,)
        scaler_x_path: Path to save X scaler
        scaler_y_path: Path to save y scaler
        
    Returns:
        X_train, X_val, X_test, y_train, y_val, y_test, scaler_X, scaler_y
    """
    print("📋 Splitting data (time-ordered)...")
    
    # Time-ordered split
    n = len(X_seq)
    train_idx = int(n * config.TRAIN_RATIO)
    val_idx = train_idx + int(n * config.VAL_RATIO)
    
    X_train, X_val, X_test = X_seq[:train_idx], X_seq[train_idx:val_idx], X_seq[val_idx:]
    y_train, y_val, y_test = y_seq[:train_idx], y_seq[train_idx:val_idx], y_seq[val_idx:]
    
    print(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    
    # Reshape for scaling (flatten time dimension)
    print("🔨 Scaling features...")
    X_train_2d = X_train.reshape(-1, X_train.shape[-1])
    X_val_2d = X_val.reshape(-1, X_val.shape[-1])
    X_test_2d = X_test.reshape(-1, X_test.shape[-1])
    
    # Fit scaler on train only
    scaler_X = StandardScaler()
    scaler_X.fit(X_train_2d)
    
    X_train_scaled = scaler_X.transform(X_train_2d).reshape(X_train.shape)
    X_val_scaled = scaler_X.transform(X_val_2d).reshape(X_val.shape)
    X_test_scaled = scaler_X.transform(X_test_2d).reshape(X_test.shape)
    
    scaler_y = StandardScaler()
    scaler_y.fit(y_train.reshape(-1, 1))
    
    y_train_scaled = scaler_y.transform(y_train.reshape(-1, 1)).ravel()
    y_val_scaled = scaler_y.transform(y_val.reshape(-1, 1)).ravel()
    y_test_scaled = scaler_y.transform(y_test.reshape(-1, 1)).ravel()
    
    # Save scalers
    joblib.dump(scaler_X, scaler_x_path)
    joblib.dump(scaler_y, scaler_y_path)
    print(f"💾 Scalers saved to {scaler_x_path} and {scaler_y_path}")
    
    print("✅ Data preprocessing complete!\n")
    
    return (X_train_scaled, X_val_scaled, X_test_scaled, 
            y_train_scaled, y_val_scaled, y_test_scaled,
            scaler_X, scaler_y)


if __name__ == "__main__":
    # Load and clean
    df = load_and_clean(config.DATA_PATH)
    
    # Engineer features
    df, feature_cols = engineer_features(df)
    
    # Prepare data
    X = df[feature_cols].values
    y = df[config.TARGET].values
    
    print(f"Data shape: X={X.shape}, y={y.shape}")
    print(f"Features: {feature_cols}\n")
