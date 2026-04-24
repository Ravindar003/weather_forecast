# AtmoSense - Weather Forecasting & Alert System

A production-ready weather forecasting system using **PyTorch-based deep learning models** with Streamlit web UI for real-time predictions, alerts, and historical analysis.

## 🌦️ Project Overview

**AtmoSense** predicts temperature and weather conditions using an ensemble of:
- **Transformer Neural Network (TNN)**: 3-day (72h) lookback, 65% weight
- **Vanilla RNN**: 1-day (24h) lookback, 35% weight

### Key Features

✅ **PyTorch Deep Learning**: Transformer + RNN models with proper time-series handling
✅ **Ensemble Predictions**: Weighted (65% TNN + 35% RNN) for robust forecasting
✅ **Streamlit Dashboard**: 5-page UI with live predictions, model comparison, alerts
✅ **Intelligent Alerts**: Configurable thresholds with email & ntfy.sh notifications
✅ **Historical Analysis**: Charts, statistics, and pattern visualization
✅ **Production-Ready**: Type hints, error handling, comprehensive logging

## 📁 Project Structure

```
weather_forecast/
├── data/
│   └── weather_data.csv              # Delhi weather dataset (historical)
├── models/
│   ├── best_tnn_model.pth            # Trained Transformer model (PyTorch)
│   ├── best_vanilla_rnn.pt           # Trained Vanilla RNN model (PyTorch)
│   ├── tnn_scaler_X.pkl              # TNN input scaler (joblib)
│   ├── tnn_scaler_y.pkl              # TNN target scaler (joblib)
│   ├── scaler_X.pkl                  # RNN input scaler (joblib)
│   └── scaler_y.pkl                  # RNN target scaler (joblib)
├── src/
│   ├── __init__.py
│   ├── preprocess.py                 # Data pipeline: load→clean→engineer→scale
│   ├── train_tnn.py                  # Transformer model training
│   ├── train_rnn.py                  # Vanilla RNN model training
│   ├── predict.py                    # Ensemble inference
│   ├── live_input.py                 # [Optional] Live data collection
│   └── alerts.py                     # Alert checking & notifications
├── app.py                            # Streamlit dashboard (5 pages)
├── config.py                         # Centralized configuration
├── requirements.txt                  # Python dependencies (PyTorch 2.0+)
└── README.md                         # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip

### Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure settings (optional)
# Edit config.py for alert thresholds, paths, etc.

# 3. Train models
python src/train_tnn.py
python src/train_rnn.py

# 4. Run dashboard
streamlit run app.py
```

Open browser → http://localhost:8501

## 🎛️ Configuration (config.py)

### Core Settings
```python
# Paths
DATA_PATH = "data/weather_data.csv"
MODEL_DIR = "models/"
TNN_MODEL_PATH = "models/best_tnn_model.pth"
RNN_MODEL_PATH = "models/best_vanilla_rnn.pt"

# Model Architecture
SEQ_LEN_TNN = 72      # 3 days for Transformer
SEQ_LEN_RNN = 24      # 1 day for Vanilla RNN
BATCH_SIZE = 256

# Training
EPOCHS_TNN = 100
EPOCHS_RNN = 50
PATIENCE = 15  # Early stopping
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Ensemble Weights
TNN_WEIGHT = 0.65     # Transformer contribution
RNN_WEIGHT = 0.35     # RNN contribution
```

### Alert Thresholds
```python
ALERT_THRESHOLDS = {
    "tempm": {"danger": 40, "warning": 35, "cold": 5},
    "hum": {"danger": 90, "warning": 85},
    "wspdm": {"danger": 60, "warning": 40},
    "wgustm": {"danger": 80, "warning": 60},
    "vism": {"danger": 1, "warning": 2, "reverse": True},
    "pressurem": {"danger": 980, "warning": 990, "reverse": True},
    "precipm": {"danger": 50, "warning": 30},
}

BINARY_ALERTS = {
    "tornado": "🌪️ TORNADO DETECTED",
    "thunder": "⚡ THUNDERSTORM",
    "hail": "🧊 HAIL",
    "fog": "🌫️ FOG",
}
```

### Notifications
```python
# Email (Gmail SMTP)
EMAIL_SENDER = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"
EMAIL_RECIPIENT = "alert@example.com"

# Push (ntfy.sh - free, no signup)
NTFY_ENDPOINT = "https://ntfy.sh/atmosense-weather"
DEFAULT_NTFY_TOPIC = "atmosense-weather"
```
## 🏗️ Model Architecture

### Transformer Neural Network (TNN)
- Input: 72-hour sequences with cyclic time features
- Embeddings: 128-dimensional
- Positional Encoding: Sinusoidal
- Encoder: 4 Transformer layers (8 heads, 512 feedforward)
- Output: Temperature prediction
- **Loss**: HuberLoss (δ=1.5, robust to outliers)
- **Optimizer**: AdamW (lr=1e-3, weight_decay=1e-4)

### Vanilla RNN
- Input: 24-hour sequences
- Stacked: 2-layer RNN (128 units, tanh activation)
- Head: Dense → BatchNorm → ReLU → Output
- **Loss**: HuberLoss (δ=1.5)
- **Optimizer**: Adam (lr=1e-3)

### Ensemble Prediction
```python
final_temp = 0.65 × tnn_pred + 0.35 × rnn_pred
```

## 🔔 Alert System

### Alert Channels
✉️ **Email (Gmail SMTP)**
- Triggered when alerts detected
- HTML-formatted message with all conditions
- Requires Gmail App Password

📱 **Push Notifications (ntfy.sh)**
- Free, no signup required
- Priority: "urgent" for DANGER alerts
- Tags: weather, thermometer, warning

## 🎯 Features Implemented

✅ **Data Pipeline**
- Load CSV with pd.read_datetime  
- Clean sentinels (-9999 → NaN)
- Engineer cyclic time features (sin/cos hour, day, month)
- Create lag features (1-24h temperature)
- Rolling statistics (6h/24h mean, std, min, max)
- StandardScaler fitting on train data only

✅ **PyTorch Models**
- Transformer with positional encoding
- Vanilla RNN with batch normalization
- HuberLoss for robustness
- Gradient clipping (norm=1.0)
- Early stopping with patience
- Learning rate scheduling

✅ **Ensemble Inference**
- Load both models from .pth files
- Inverse transform predictions
- Clip to valid temperature range [-5°C, 50°C]
- Weighted averaging (65% TNN + 35% RNN)

✅ **Alert System**
- Check thresholds: DANGER and WARNING levels
- Binary alerts: tornado, thunder, hail, fog
- Email notifications (Gmail SMTP SSL)
- Push notifications (ntfy.sh endpoint)
- Configurable all thresholds in config.py

✅ **Streamlit Dashboard**
- 5-page web UI with dark theme
- Dashboard: 5 metrics + 48h forecast + alerts
- Live Prediction: Form inputs + ensemble results
- Model Comparison: Metrics, curves, error distribution
- Historical Analysis: Time series + statistics
- Alert Settings: Threshold editor + test alerts

## 🐛 Troubleshooting

### Models not training
```bash
# Ensure data file exists and has correct path
python -c "import pandas as pd; print(pd.read_csv('data/weather_data.csv').shape)"

# Check config.py paths
python -c "import config; print(config.DATA_PATH, config.TNN_MODEL_PATH)"
```

### Out of memory during training
- Reduce BATCH_SIZE in config.py (default: 256)
- Use CPU: Set `DEVICE = "cpu"` in config.py

### Streamlit app crashes
- Check all models are trained: `ls models/*.pth`
- Check scalers exist: `ls models/*scaler*.pkl`
- Restart kernel: `streamlit run app.py`

### Prediction error: "Scalers not found"
- Train models first: `python src/train_tnn.py && python src/train_rnn.py`
- Verify joblib pickle files exist in models/ folder

## 📈 Performance Tuning

**Faster Training**
- Reduce EPOCHS_TNN (default: 100) or EPOCHS_RNN (default: 50)
- Increase BATCH_SIZE (trades memory for speed)
- Use GPU: Ensure torch sees your GPU via `torch.cuda.is_available()`

**Better Accuracy**
- Provide more training data (longer historical period)
- Increase EPOCHS for both models
- Tune learning rates in train_tnn.py and train_rnn.py

**Lower Latency**
- Reduce SEQ_LEN_TNN (default: 72) → 48 or 24
- Reduce model complexity (fewer layers, smaller d_model)

## 🐳 Production Deployment

### Docker Container

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:
```bash
docker build -t atmosense .
docker run -p 8501:8501 atmosense
```

### Linux Systemd Service

Create `/etc/systemd/system/atmosense.service`:

```ini
[Unit]
Description=AtmoSense Streamlit Dashboard
After=network.target

[Service]
Type=simple
User=atmosense
WorkingDirectory=/opt/atmosense
ExecStart=/usr/bin/streamlit run /opt/atmosense/app.py --server.port=8501
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable atmosense
sudo systemctl start atmosense
```

## 📚 API Reference

### Preprocessing

```python
from src.preprocess import load_and_clean, engineer_features, create_sequences, split_and_scale

# Load and clean data
df = load_and_clean('data/weather_data.csv')

# Engineer features
df = engineer_features(df)

# Create sequences for modeling
X, y, seq_dates = create_sequences(df, seq_len=72)

# Split and scale (returns 6 numpy arrays + 2 scalers)
X_train, X_val, X_test, y_train, y_val, y_test, scaler_X, scaler_y = split_and_scale(X, y)
```

### Training

```python
from src.train_tnn import train_tnn
from src.train_rnn import train_rnn

# Train Transformer
train_tnn()  # Saves to config.TNN_MODEL_PATH

# Train RNN
train_rnn()  # Saves to config.RNN_MODEL_PATH
```

### Inference

```python
from src.predict import load_tnn_model, load_rnn_model, predict_tnn, predict_rnn, ensemble_predict

# Load models
tnn_model = load_tnn_model(feature_count=34)
rnn_model = load_rnn_model(feature_count=34)

# Make predictions
tnn_pred = predict_tnn(tnn_model, X_recent, scaler_X, scaler_y, features, seq_len=72)
rnn_pred = predict_rnn(rnn_model, X_recent, scaler_X, scaler_y, features, seq_len=24)

# Ensemble
final_pred = ensemble_predict(tnn_pred, rnn_pred)  # Returns float (°C)
```

### Alerts

```python
from src.alerts import check_alerts, send_email_alert, send_push_notification

# Check thresholds
predicted_values = {'tempm': 42.5, 'hum': 88, 'wspdm': 65}
alerts = check_alerts(predicted_values)
# Returns: [{'level': 'DANGER', 'variable': 'tempm', 'value': 42.5, 'message': '...', 'emoji': '🔴'}, ...]

# Send notifications
send_email_alert(alerts, recipient='user@example.com', sender_email='...',sender_password='...')
send_push_notification(alerts, topic='atmosense-weather')
```

## 🔐 Security & Privacy

⚠️ **Before Production Deployment:**

1. **Protect Credentials**
   - Never commit config.py with real credentials to git
   - Use environment variables or .env files
   - Store API keys in OS keyring

2. **Email Setup**
   - Use Gmail App Password (not your main password)
   - Enable 2-factor authentication on Gmail
   - Create app-specific password

3. **HTTPS Only**
   - Run Streamlit behind nginx/Apache with SSL
   - Use self-signed certificates for local testing
   - Never expose dashboard on public IP without authentication

4. **Data Handling**
   - Encrypt predictions_log.csv if storing sensitive data
   - Implement access controls
   - Comply with GDPR/local regulations

## 📊 Dependencies

**Core ML Stack**
- `torch>=2.0.0` - Deep learning framework
- `numpy>=1.24.0` - Numerical computing
- `pandas>=2.0.0` - Data manipulation
- `scikit-learn>=1.3.0` - Preprocessing & metrics

**UI & Visualization**
- `streamlit>=1.28.0` - Web dashboard
- `plotly>=5.15.0` - Interactive charts

**Utilities**
- `joblib>=1.3.0` - Model serialization
- `requests>=2.31.0` - HTTP requests for ntfy.sh
- `schedule>=1.2.0` - Task scheduling (optional)

## 📝 Data Format

### Input: weather_data.csv

Required columns with example data:
```
datetime_utc,tempm,hum,pressurem,wspdm,wgustm,vism,dewptm,heatindexm,windchillm,fog,rain,thunder,tornado,hail,snow
20240101-00:00,15.2,65,1013.5,12.3,25.6,10.0,8.5,15.2,12.1,0,0,0,0,0,0
20240101-01:00,14.8,68,1013.4,13.1,27.2,9.8,8.1,14.8,11.5,0,0,0,0,0,0
```

**Data Quality Issues Handled:**
- Sentinel values: -9999, -9999.0, -999.9, -999 → converted to NaN
- Temperature clipping: [-5°C, 50°C] range
- NaN filling: forward fill + linear interpolation
- Duplicate timestamps: removed
- Missing sequences: dropped

## 🚢 Version History

**v1.0.0** (Current)
- PyTorch 2.0 models (Transformer TNN + Vanilla RNN)
- Streamlit 5-page dashboard
- Email + ntfy.sh alerts
- Time-series preprocessing with feature engineering
- Ensemble inference (65% TNN, 35% RNN)
