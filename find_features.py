#!/usr/bin/env python
"""Find which 25 features the scaler was trained on."""

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
print(f'Scaler expects {scaler.n_features_in_} features\n')

# Load and prepare data
df = load_and_clean_data('data/weather_data.csv')
df = engineer_time_features(df)
df = engineer_delta_features(df)
df = engineer_lag_features(df)

# Get numeric columns
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
print(f'Total numeric columns available: {len(numeric_cols)}')
print(f'Numeric columns: {numeric_cols}\n')

# Filter config.FEATURE_COLS to only numeric ones
feature_cols_numeric = [col for col in config.FEATURE_COLS if col in numeric_cols]
print(f'config.FEATURE_COLS numeric subset ({len(feature_cols_numeric)}):')
print(feature_cols_numeric)
print()

# Scaler was probably trained without '_conds' since it's a string
# Try removing one feature at a time to find which ones aren't in the scaler
print(f'Trying to find the 25 features the scaler expects...\n')

# Start with all numeric feature_cols and try removing them one by one
removed_candidates = []
for col in feature_cols_numeric:
    test_cols = [c for c in feature_cols_numeric if c != col]
    if len(test_cols) == 25:
        try:
            X_test = df[test_cols].values[-1:]
            scaler.transform(X_test)
            print(f'✓ SUCCESS: Removing {col} gives 25 features that work!')
            print(f'  Features: {test_cols}')
            break
        except Exception as e:
            print(f'  Tried removing {col}: {type(e).__name__}')
            removed_candidates.append(col)

# If we have more than 25, try all combinations to find the right set
if len(feature_cols_numeric) > 25:
    print(f'\nTrying to find the correct 25-feature subset...')
    from itertools import combinations
    
    # Try removing features systematically
    to_remove = len(feature_cols_numeric) - 25
    print(f'Need to remove {to_remove} features')
    
    # The most likely candidates to remove are wdire (text), and maybe some lags
    # Let's try a few strategic removals
    candidates_to_try = ['wdire']  # Text column
    
    for col_to_remove in candidates_to_try:
        if col_to_remove in feature_cols_numeric:
            test_cols = [c for c in feature_cols_numeric if c != col_to_remove]
            print(f'\nRemoving {col_to_remove}: {len(test_cols)} features left')
            if len(test_cols) == 25:
                try:
                    X_test = df[test_cols].values[-1:]
                    scaler.transform(X_test)
                    print(f'✓ SUCCESS with just removing {col_to_remove}!')
                    print(f'Correct features: {test_cols}')
                    break
                except Exception as e:
                    print(f'✗ Failed: {e}')
