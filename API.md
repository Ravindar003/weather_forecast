# AtmoSense API Documentation

## Overview

AtmoSense provides a modular API for weather forecasting, prediction, and alerting. All modules support type hints and comprehensive error handling.

## Modules

### 1. src.preprocess

Data preprocessing and feature engineering.

#### `load_and_clean_data(csv_path: str) -> pd.DataFrame`
Load and clean weather data from CSV.

```python
from src.preprocess import load_and_clean_data

df = load_and_clean_data("data/weather_data.csv")
# Returns: DataFrame with datetime_utc as index, duplicates removed, NaN filled
```

**Parameters:**
- `csv_path` (str): Path to CSV file

**Returns:**
- pd.DataFrame: Cleaned data with datetime index

**Raises:**
- FileNotFoundError: If CSV file doesn't exist
- ValueError: If datetime column is invalid

---

#### `engineer_time_features(df: pd.DataFrame) -> pd.DataFrame`
Add circular encoded time features.

```python
df = engineer_time_features(df)
# Adds: hour_sin, hour_cos, day_sin, day_cos
```

**Added Features:**
- `hour_sin`: sin(2π * hour / 24)
- `hour_cos`: cos(2π * hour / 24)
- `day_sin`: sin(2π * day_of_year / 365)
- `day_cos`: cos(2π * day_of_year / 365)

---

#### `engineer_delta_features(df: pd.DataFrame) -> pd.DataFrame`
Add temperature delta features.

```python
df = engineer_delta_features(df)
# Adds: heat_delta, chill_delta
```

**Added Features:**
- `heat_delta`: heatindexm - tempm
- `chill_delta`: windchillm - tempm

---

#### `engineer_lag_features(df: pd.DataFrame, target_col: str = 'tempm', lags: List[int] = [1, 3, 6, 12, 24]) -> pd.DataFrame`
Add lagged features for temporal context.

```python
df = engineer_lag_features(df, target_col='tempm', lags=[1, 3, 6, 12, 24])
# Adds: tempm_lag1, tempm_lag3, tempm_lag6, tempm_lag12, tempm_lag24
```

**Parameters:**
- `df` (pd.DataFrame): Input data
- `target_col` (str): Column to lag (default: 'tempm')
- `lags` (List[int]): Lag periods in hours (default: [1, 3, 6, 12, 24])

**Returns:**
- pd.DataFrame: With lag features

---

#### `scale_features(df: pd.DataFrame, scaler: StandardScaler = None, fit: bool = True) -> Tuple[pd.DataFrame, StandardScaler]`
Scale continuous features using StandardScaler.

```python
df_scaled, scaler = scale_features(df, fit=True)
# Binary columns not scaled; scaler saved for later use

# Use existing scaler
df_new_scaled, _ = scale_features(df_new, scaler=scaler, fit=False)
```

**Parameters:**
- `df` (pd.DataFrame): Input data
- `scaler` (StandardScaler): Pre-fitted scaler (optional)
- `fit` (bool): Whether to fit new scaler (default: True)

**Returns:**
- Tuple[pd.DataFrame, StandardScaler]: Scaled data and scaler object

---

#### `create_sequences(df: pd.DataFrame, target_cols: List[str], lookback: int) -> Tuple[np.ndarray, np.ndarray]`
Create sequences for model training.

```python
X, y = create_sequences(df, ['tempm', 'hum', 'pressurem', 'wspdm', 'vism', 'precipm'], lookback=72)
# X shape: (n_samples, 72, n_features)
# y shape: (n_samples, 6)
```

**Parameters:**
- `df` (pd.DataFrame): Input data with all features
- `target_cols` (List[str]): Columns to predict
- `lookback` (int): Sequence length in hours

**Returns:**
- Tuple[np.ndarray, np.ndarray]: (X, y) sequences

---

#### `preprocess_pipeline(csv_path: str, output_dir: str = "models") -> Dict`
Complete preprocessing pipeline.

```python
result = preprocess_pipeline("data/weather_data.csv", output_dir="models")
# result keys: X_train, X_test, y_train, y_test, scaler, feature_cols, target_cols
```

---

### 2. src.live_input

Live weather data fetching and preparation.

#### `fetch_live_weather() -> Dict`
Fetch live weather from OpenWeatherMap API.

```python
from src.live_input import fetch_live_weather

weather_data = fetch_live_weather()
# Returns dict with all weather parameters mapped from API
```

**Returns:**
```python
{
    'tempm': 28.5,           # Temperature in Celsius
    'hum': 65,               # Humidity %
    'pressurem': 1013.2,     # Pressure hPa
    'wspdm': 12.0,           # Wind speed km/h
    'wdird': 180,            # Wind direction degrees
    'wgustm': 15.5,          # Wind gust km/h
    'vism': 10.0,            # Visibility km
    'heatindexm': 24.8,      # Heat index/feels like
    'windchillm': 26.2,      # Wind chill
    'precipm': 0.0,          # Precipitation mm
    'dewptm': 12.5,          # Dew point
    '_conds': 'Clear',       # Conditions text
    'fog': 0,                # Binary conditions
    'rain': 0,
    'snow': 0,
    'thunder': 0,
    'tornado': 0,
    'hail': 0,
    'wdire': 'S',            # Wind direction compass
    'datetime_utc': datetime.datetime(...),
}
```

**Requires:** `config.OPENWEATHERMAP_API_KEY`

**Raises:**
- requests.exceptions.RequestException: Network error
- KeyError: Missing data in API response

---

#### `prepare_live_input(scaler_path: str = "models/scaler.pkl", historical_data: Optional[np.ndarray] = None) -> Tuple[np.ndarray, Dict]`
Complete live input preparation pipeline.

```python
X, weather_data = prepare_live_input(scaler_path="models/scaler.pkl")
# X ready for model inference: shape (1, 72, n_features)
```

**Parameters:**
- `scaler_path` (str): Path to fitted StandardScaler
- `historical_data` (Optional[np.ndarray]): Previous sequence for context

**Returns:**
- Tuple[np.ndarray, Dict]: (scaled_input, raw_weather)

---

### 3. src.predict

Model inference and ensemble predictions.

#### `class EnsemblePredictor`

```python
from src.predict import EnsemblePredictor

# Initialize
predictor = EnsemblePredictor(
    tnn_path="models/tnn_model.h5",
    rnn_path="models/rnn_model.h5",
    scaler_path="models/scaler.pkl"
)

# Load models
predictor.load_models()

# Generate predictions
ensemble_pred, individual_preds = predictor.ensemble_predict(X)

# Inverse transform
predictions_original_scale = predictor.inverse_transform(ensemble_pred)
```

**Methods:**

##### `load_models() -> None`
Load all models and scaler.

##### `predict_tnn(X: np.ndarray) -> np.ndarray`
Run TNN inference on input sequences.

##### `predict_rnn(X: np.ndarray) -> np.ndarray`
Run RNN inference on input sequences.

##### `ensemble_predict(X: np.ndarray, tnn_weight: float = 0.65, rnn_weight: float = 0.35) -> Tuple[np.ndarray, Dict]`
Generate weighted ensemble predictions.

**Returns:**
```python
(
    ensemble_predictions,  # (n_samples, n_targets)
    {
        'tnn': tnn_predictions,
        'rnn': rnn_predictions,
        'ensemble': ensemble_predictions
    }
)
```

##### `inverse_transform(predictions: np.ndarray) -> np.ndarray`
Convert scaled predictions back to original scale.

---

#### `predict_pipeline(X: np.ndarray, ...) -> Dict`
Complete prediction pipeline.

```python
from src.predict import predict_pipeline

result = predict_pipeline(X, tnn_path="...", rnn_path="...", scaler_path="...")
# Returns:
# {
#     'ensemble': {'tempm': 31.2, 'hum': 68.5, ...},
#     'tnn': {'tempm': 31.5, ...},
#     'rnn': {'tempm': 30.8, ...}
# }
```

---

### 4. src.alert

Alert checking and notifications.

#### `check_thresholds(predictions: Dict, weather_data: Optional[Dict] = None) -> Dict[str, List]`
Check predictions against alert thresholds.

```python
from src.alert import check_thresholds

alerts = check_thresholds(
    predictions={'tempm': 42.0, 'hum': 87.0},
    weather_data=weather_data
)
# Returns:
# {
#     'danger': [
#         {'variable': 'tempm', 'value': 42.0, 'threshold': 40, 'unit': '°C'}
#     ],
#     'warning': [
#         {'variable': 'hum', 'value': 87.0, 'threshold': 85, 'unit': '%'}
#     ]
# }
```

---

#### `send_alerts(alerts: Dict[str, List], predictions: Dict) -> Dict[str, bool]`
Send all enabled alert notifications.

```python
from src.alert import send_alerts

status = send_alerts(alerts, predictions)
# Returns: {'email': True, 'sms': False, 'push': True}
```

**Channels:**
- Email (requires Gmail SMTP config)
- SMS (requires Twilio config)
- Push (uses free ntfy.sh)

---

### 5. src.train_tnn

TNN model training.

#### `class TemporalNeuralNetwork`

```python
from src.train_tnn import TemporalNeuralNetwork

# Initialize
tnn = TemporalNeuralNetwork(
    input_shape=(72, n_features),  # lookback × features
    output_dim=6                    # number of targets
)

# Build model
tnn.build_model()

# Train
history = tnn.train(
    X_train, y_train,
    X_val, y_val,
    epochs=100,
    batch_size=32,
    model_path="models/tnn_model.h5"
)
```

---

#### `train_tnn_pipeline(csv_path: str, model_dir: str = "models") -> None`
End-to-end TNN training.

```python
from src.train_tnn import train_tnn_pipeline

train_tnn_pipeline("data/weather_data.csv", model_dir="models")
# Creates: models/tnn_model.h5, models/tnn_training.png
```

---

### 6. src.train_rnn

Vanilla RNN model training.

#### `class VanillaRNNModel`

```python
from src.train_rnn import VanillaRNNModel

# Initialize and build
rnn = VanillaRNNModel(input_shape=(72, n_features), output_dim=6)
rnn.build_model()

# Train
history = rnn.train(
    X_train, y_train,
    X_val, y_val,
    epochs=100,
    batch_size=32
)
```

---

#### `train_rnn_pipeline(csv_path: str, model_dir: str = "models") -> None`
End-to-end RNN training.

```python
from src.train_rnn import train_rnn_pipeline

train_rnn_pipeline("data/weather_data.csv")
# Creates: models/rnn_model.h5, models/rnn_training.png
```

---

## Usage Examples

### Complete Forecast Workflow

```python
from src.live_input import prepare_live_input
from src.predict import predict_pipeline
from src.alert import check_thresholds, send_alerts
from datetime import datetime

# Step 1: Get live data
X, weather_data = prepare_live_input()

# Step 2: Run predictions
predictions = predict_pipeline(X)

# Step 3: Check thresholds
alerts = check_thresholds(predictions['ensemble'], weather_data)

# Step 4: Send notifications
if alerts['danger'] or alerts['warning']:
    status = send_alerts(alerts, predictions['ensemble'])
    print(f"Notifications sent: {status}")

# Step 5: Log results
print(f"Forecast at {datetime.now()}")
print(f"Temperature: {predictions['ensemble']['tempm']:.1f}°C")
print(f"Humidity: {predictions['ensemble']['hum']:.1f}%")
```

### Training New Models

```python
from src.train_tnn import train_tnn_pipeline
from src.train_rnn import train_rnn_pipeline

# Train both models
train_tnn_pipeline("data/weather_data.csv")
train_rnn_pipeline("data/weather_data.csv")

print("Models trained and saved!")
```

### Custom Feature Engineering

```python
from src.preprocess import (
    load_and_clean_data,
    engineer_time_features,
    engineer_delta_features,
    scale_features,
    create_sequences
)
import config

# Load data
df = load_and_clean_data("data/weather_data.csv")

# Custom features
df['custom_feature'] = df['tempm'] * df['hum'] / 100  # Example

# Engineer defaults
df = engineer_time_features(df)
df = engineer_delta_features(df)

# Scale
df_scaled, scaler = scale_features(df)

# Create sequences
X, y = create_sequences(df_scaled, config.TARGET_COLS, config.LOOK_BACK)
```

---

## Error Handling

All functions include comprehensive error handling:

```python
from src.live_input import fetch_live_weather
import logging

logger = logging.getLogger(__name__)

try:
    weather = fetch_live_weather()
except requests.exceptions.RequestException as e:
    logger.error(f"Network error: {e}")
except KeyError as e:
    logger.error(f"Missing API field: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

---

## Type Hints

All functions include type hints for IDE support:

```python
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd

def my_function(
    predictions: Dict[str, float],
    alerts: Dict[str, List],
    threshold: Optional[float] = None
) -> Dict[str, bool]:
    ...
```

---

## Configuration Reference

See `config.py` for all configurable parameters:

- API keys and credentials
- Model hyperparameters
- Alert thresholds
- Feature columns and targets
- Scheduling options

---

## Performance Considerations

- **Memory**: Models require ~500MB VRAM
- **Speed**: Single inference ~100ms
- **Throughput**: ~1000 predictions/minute
- **Latency**: API calls ~2-3 seconds

---

## Testing

Run system verification:

```bash
python test_system.py
```

---

## License & Support

See README.md for support information.
