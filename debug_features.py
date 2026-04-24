#!/usr/bin/env python
"""Debug script to identify correct feature columns."""

import joblib
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
import config
from src.preprocess import (
    load_and_clean_data, 
    engineer_time_features, 
    engineer_delta_features,
    engineer_lag_features
)

# Load scaler
scaler = joblib.load('models/scaler_X.pkl')
print(f'Scaler expects {scaler.n_features_in_} features')
print(f'Scaler feature means: {scaler.mean_}')
print()

# Load and prepare data
df = load_and_clean_data('data/weather_data.csv')
df = engineer_time_features(df)
df = engineer_delta_features(df)
df = engineer_lag_features(df)

print(f'DataFrame shape: {df.shape}')
print(f'DataFrame columns: {df.columns.tolist()}')
print()

# List of numeric columns
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
print(f'Numeric columns ({len(numeric_cols)}):', numeric_cols)
print()

# Show which FEATURE_COLS are available
print(f'config.FEATURE_COLS ({len(config.FEATURE_COLS)}):')
available = []
for i, col in enumerate(config.FEATURE_COLS):
    if col in df.columns:
        dtype = df[col].dtype
        is_numeric = dtype != 'object'
        print(f'  {i+1:2d}. {col:20s} - {dtype} - {"✓" if is_numeric else "✗"}')
        if is_numeric:
            available.append(col)
    else:
        print(f'  {i+1:2d}. {col:20s} - NOT IN DATAFRAME')

print()
print(f'Available numeric FEATURE_COLS: {len(available)}')
print(available)

# Try to match scaler
if len(available) == scaler.n_features_in_:
    print(f'\n✓ Perfect match! Using these {len(available)} features')
    X = df[available].values
    print(f'X shape: {X.shape}')
    print(f'X values sample:\n{X[-1:]}')
    
    # Try transform
    try:
        X_scaled = scaler.transform(X[-1:])
        print(f'\n✓ Scaler transform successful!')
        print(f'X_scaled:\n{X_scaled}')
    except Exception as e:
        print(f'✗ Error during transform: {e}')
else:
    print(f'\n✗ Mismatch: need {scaler.n_features_in_}, have {len(available)}')
    print(f'Difference: {scaler.n_features_in_ - len(available)} features missing or excluded')
