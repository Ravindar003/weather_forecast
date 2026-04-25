# AI Agent Instructions for AtmoSense Weather Forecast

## 📋 Quick Context

**AtmoSense** is a production-ready weather forecasting system that:
- Predicts 6 weather variables (temperature, humidity, wind speed, pressure, visibility, precipitation)
- Uses PyTorch ensemble: **Transformer NN (65%)** + **Vanilla RNN (35%)**
- Fetches live data from OpenWeatherMap API
- Sends threshold-based alerts via email, SMS (Twilio), push (ntfy.sh)
- Logs predictions to [predictions_log.csv](predictions_log.csv)

**Tech Stack:** PyTorch, Streamlit, OpenWeatherMap API, Twilio, ntfy.sh, systemd

---

## 🏗️ Architecture & Key Components

| File | Purpose | Key Responsibility |
|------|---------|-------------------|
| [config.py](config.py) | **Central hub** | All constants, thresholds, paths, API keys, model weights |
| [main.py](main.py) | **Orchestrator** | Scheduling, pipeline execution, 24/7 loop, single-run modes |
| [app.py](app.py) | **Streamlit UI** | 5-page dashboard: predictions, comparison, alerts, history, settings |
| [src/predict.py](src/predict.py) | **Inference** | Load ensemble (TNN + RNN), weighted inference |
| [src/live_input.py](src/live_input.py) | **API Integration** | Fetch OpenWeatherMap data, error handling, retry logic |
| [src/preprocess.py](src/preprocess.py) | **Data Pipeline** | Load, clean, feature engineering (lag, circular time, delta), scale |
| [src/alert.py](src/alert.py) | **Alert System** | Threshold checking, multi-channel notification dispatch |
| [src/train_tnn.py](src/train_tnn.py) | **TNN Training** | Transformer model: Conv1D+Attention, Huber loss, 72h lookback |
| [src/train_rnn.py](src/train_rnn.py) | **RNN Training** | Vanilla RNN: Stacked layers, MSE loss, 24h lookback |

**Pipeline Flow:** Fetch (live_input) → Preprocess → TNN/RNN inference → Weighted ensemble → Threshold check → Notify → Log

---

## ⏱️ "Rate" Features (API Limits, Scheduling, Restart Limits)

### 1. **API Rate Limiting** (OpenWeatherMap)
- **Limit:** 60 requests/minute (free tier)
- **Configured in:** [LIVE_API_GUIDE.md](LIVE_API_GUIDE.md) & [config.py](config.py)
- **Location in code:** [src/live_input.py](src/live_input.py) → fetch logic
- **Implementation:** Single-call per cycle (scheduled, not burst)
- **Workaround if hitting limit:** Increase `schedule_interval` in [main.py](main.py)'s `schedule_pipeline()`

### 2. **Forecast Frequency / Scheduling**
- **Default interval:** Every **1 hour** (via `schedule.every(1).hours.do()`)
- **Configured in:** [main.py](main.py) → `schedule_pipeline()` function
- **Minimum safe interval:** 5–10 minutes (depends on API key limits)
- **How to change:**
  ```python
  # main.py, line ~60-70
  schedule.every(1).hours.do(...)  # Change 1 to 2 for 2-hour intervals
  ```

### 3. **System Service Rate Limits** (systemd)
- **File:** [atmosense.service](atmosense.service)
- **Burst limit:** `StartLimitBurst=5` (max 5 restarts)
- **Window:** `StartLimitInterval=300` (within 5 minutes)
- **Restart delay:** `RestartSec=60` (60-second wait between restarts)
- **Memory cap:** `MemoryLimit=2G` (resource safety)
- **Use case:** If service crashes repeatedly, systemd enforces rate limiting to prevent restart loops

---

## 🚀 Common Commands & Tasks

### Setup & Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Configure API key (interactive)
python setup_live_api.py

# Verify system is ready
python test_system.py
```

### Train Models
```bash
# Train Transformer (72h lookback, 65% weight)
python src/train_tnn.py

# Train Vanilla RNN (24h lookback, 35% weight)
python src/train_rnn.py
```

### Run Predictions
```bash
# Single forecast (one-time)
python -c "from main import WeatherForecastingSystem; WeatherForecastingSystem().run_pipeline()"

# Scheduled loop (hourly, 24/7)
python main.py

# With logging
python main.py > atmosense.log 2>&1 &
```

### Dashboard
```bash
# Start Streamlit (5-page UI)
streamlit run app.py
# → http://localhost:8501
```

### Monitoring
```bash
# View live logs
tail -f atmosense.log

# Check predictions history
cat predictions_log.csv

# Test API connectivity
python test_api_connection.py
```

---

## 🔧 Key Configuration Points

All settings in [config.py](config.py). Most important:

| Setting | Default | Purpose |
|---------|---------|---------|
| `OPENWEATHER_API_KEY` | (env var) | API access |
| `SEQ_LEN_TNN` | 72 | Transformer lookback (hours) |
| `SEQ_LEN_RNN` | 24 | RNN lookback (hours) |
| `TNN_WEIGHT` | 0.65 | Transformer contribution to ensemble |
| `RNN_WEIGHT` | 0.35 | RNN contribution to ensemble |
| `ALERT_THRESHOLDS` | dict | Danger/warning levels for 6 variables |
| `BATCH_SIZE` | 256 | Training batch size |
| `PATIENCE` | 15 | Early stopping patience |

**To modify:** Edit [config.py](config.py) directly or set env vars before running.

---

## ⚠️ Important Patterns & Gotchas

### 1. **Ensemble Weights Must Sum to 1.0**
```python
# ✅ Correct
TNN_WEIGHT = 0.65
RNN_WEIGHT = 0.35  # 0.65 + 0.35 = 1.0

# ❌ Wrong
TNN_WEIGHT = 0.70
RNN_WEIGHT = 0.30  # Will still work but violates design intent
```

### 2. **Sequence Lengths Are Fixed**
- TNN expects exactly 72 hours of history
- RNN expects exactly 24 hours of history
- Changing these requires **retraining** both models
- See [src/preprocess.py](src/preprocess.py) for padding/trimming logic

### 3. **Scalers Must Match Training Data**
- Each model has its own scalers (TNN: `tnn_scaler_X.pkl`, RNN: `scaler_X.pkl`)
- **Never mix scalers** between models
- If you retrain, scalers are automatically saved

### 4. **Alert Thresholds Are Bidirectional**
```python
# Example: Temperature alerts
"temperature": {
    "danger": (5, 45),      # < 5°C or > 45°C
    "warning": (10, 40),    # < 10°C or > 40°C
}
# Triggered if predicted value falls outside upper bound OR below lower bound
```

### 5. **API Key Must Be Set**
- Before first run, set `OPENWEATHER_API_KEY` env var OR edit [config.py](config.py)
- Run `python setup_live_api.py` for guided setup
- System will fail silently if key is missing

### 6. **Predictions Are Logged After Notification Attempt**
- [predictions_log.csv](predictions_log.csv) captures: timestamp, predictions, alerts, notification status
- Useful for auditing which alerts were sent and why

---

## 🛠️ Development Workflow

### Making Changes to Models
1. Edit [src/train_tnn.py](src/train_tnn.py) or [src/train_rnn.py](src/train_rnn.py)
2. Retrain: `python src/train_tnn.py` or `python src/train_rnn.py`
3. New weights automatically saved to [models/](models/)
4. No code changes needed; prediction code auto-loads new models

### Making Changes to Alert Logic
1. Edit thresholds in [config.py](config.py)
2. Edit conditions in [src/alert.py](src/alert.py)
3. No retraining needed; takes effect next prediction cycle

### Adding New Notification Channel
1. Edit [src/alert.py](src/alert.py) → add notify function
2. Call it from `send_alert()` dispatcher
3. Add configuration/credentials to [config.py](config.py)

### Debugging a Failed Prediction
1. Check [atmosense.log](atmosense.log) for stack trace
2. Check [predictions_log.csv](predictions_log.csv) for which step failed
3. Common issues:
   - API key invalid or rate limited
   - Missing model files in [models/](models/)
   - Live data has missing columns
   - Threshold config is malformed

---

## 📊 Data & Model References

**Dataset:** [data/weather_data.csv](data/weather_data.csv)
- 6 variables: temperature, humidity, wind_speed, pressure, visibility, precipitation
- 70/15/15 train/val/test split
- Standardized via MinMaxScaler (0-1 range)

**Feature Engineering** (in [src/preprocess.py](src/preprocess.py)):
- **Lag features:** 1h, 3h, 6h, 12h, 24h lookback
- **Circular time encoding:** hour_sin, hour_cos, day_sin, day_cos
- **Delta features:** heat_delta (THI), chill_delta (WCI)

**Training Hyperparameters:**
- TNN: 100 epochs, Huber loss, Conv1D+Attention, lr=1e-3
- RNN: 50 epochs, MSE loss, Stacked SimpleRNN, lr=1e-3
- Both: early stopping (patience=15), batch size=256

---

## 📚 Additional Resources

- [README.md](README.md) — Full documentation
- [QUICKSTART.md](QUICKSTART.md) — Fast setup guide
- [LIVE_API_GUIDE.md](LIVE_API_GUIDE.md) — API integration details
- [API.md](API.md) — API endpoint reference
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) — High-level summary

---

## 💡 For AI Agents: Quick Troubleshooting Paths

| Issue | Check | Fix |
|-------|-------|-----|
| "API rate limit exceeded" | [LIVE_API_GUIDE.md](LIVE_API_GUIDE.md), [main.py](main.py) scheduling | Increase `schedule_interval` |
| "Model file not found" | [config.py](config.py) paths, [models/](models/) directory | Retrain with `python src/train_*.py` |
| "Alert not sent" | [src/alert.py](src/alert.py), [config.py](config.py) credentials | Verify API keys (email, Twilio, ntfy.sh) |
| "Predictions look wrong" | [src/preprocess.py](src/preprocess.py), scaler files | Check input data format, retrain if changed |
| "Service keeps restarting" | [atmosense.service](atmosense.service) rate limits | Increase `StartLimitInterval` or check logs |
| "Out of memory" | [config.py](config.py) batch size, [atmosense.service](atmosense.service) limit | Reduce `BATCH_SIZE` or increase `MemoryLimit` |

---

**Last Updated:** April 2026  
**Maintained By:** AI Agent Instructions
