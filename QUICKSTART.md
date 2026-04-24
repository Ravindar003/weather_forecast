# Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get API Keys (Free)
- **OpenWeatherMap**: https://openweathermap.org/api (free tier available)
- **Twilio** (optional): https://www.twilio.com (free trial $15 credit)
- **Gmail** (optional): Use your Gmail + generate App Password
- **ntfy.sh** (optional): Free, no signup needed

### 3. Configure APIs
Edit `config.py`:
```python
OPENWEATHERMAP_API_KEY = "your_key_here"
LAT = 10.7905  # Your latitude
LON = 78.7047  # Your longitude
CITY = "Tiruchirappalli"
```

### 4. Train Models
```bash
# This trains both TNN and RNN models on the sample data
python src/train_tnn.py
python src/train_rnn.py

# Or run both in sequence:
python -c "
from src.train_tnn import train_tnn_pipeline
from src.train_rnn import train_rnn_pipeline
train_tnn_pipeline('data/weather_data.csv')
train_rnn_pipeline('data/weather_data.csv')
print('Training complete!')
"
```

### 5. Run Single Forecast
```bash
python -c "
from main import WeatherForecastingSystem
system = WeatherForecastingSystem()
system.run_pipeline()
"
```

### 6. Run 24/7 Scheduler
```bash
python main.py
```

This will:
- Fetch live weather every hour
- Make predictions with TNN + RNN ensemble
- Check thresholds and send alerts if needed
- Log everything to `predictions_log.csv`

## Common Commands

### Train Models Only
```bash
python src/train_tnn.py
python src/train_rnn.py
```

### Run Single Forecast
```bash
python main.py  # Press Ctrl+C after first run
```

### Check Logs
```bash
tail -f atmosense.log          # Live logs
cat predictions_log.csv        # View predictions history
```

### View Current Predictions
```python
from src.live_input import prepare_live_input
from src.predict import predict_pipeline

X, weather = prepare_live_input()
pred = predict_pipeline(X)
print(f"Temperature: {pred['ensemble']['tempm']:.1f}°C")
print(f"Humidity: {pred['ensemble']['hum']:.1f}%")
```

## Enable Notifications

### Email Alerts (Gmail)
```python
# In config.py
ENABLE_EMAIL = True
EMAIL_SENDER = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"  # Not regular password!
EMAIL_RECIPIENT = "recipient@example.com"
```

**Getting Gmail App Password:**
1. Enable 2-Factor Authentication on Gmail
2. Go to https://myaccount.google.com/apppasswords
3. Create app password for "Mail" and "Windows"
4. Use that 16-character password in config.py

### SMS Alerts (Twilio)
```python
# In config.py
ENABLE_SMS = True
TWILIO_SID = "AC..."
TWILIO_TOKEN = "..."
TWILIO_FROM = "+1XXXXXXXXXX"
TWILIO_TO = "+91XXXXXXXXXX"
```

### Push Notifications (ntfy.sh)
```python
# In config.py - Already configured!
ENABLE_PUSH = True
NTFY_TOPIC = "atmosense-alerts"

# View alerts at: https://ntfy.sh/atmosense-alerts
```

## Troubleshooting

### "API key invalid"
- Check OpenWeatherMap key is correct in config.py
- Test at: https://api.openweathermap.org/data/2.5/weather?lat=10.7905&lon=78.7047&appid=YOUR_KEY

### "Model not found"
- Ensure models/tnn_model.h5 and models/rnn_model.h5 exist
- Run training: `python src/train_tnn.py && python src/train_rnn.py`

### "Email failed"
- If using Gmail: Enable App Password (see above)
- If not Gmail: Enable "Less secure apps"

### "SMS/Push not sent"
- Check if ENABLE_SMS or ENABLE_PUSH is True in config.py
- For Twilio: verify account has credits
- For ntfy.sh: test with curl:
```bash
curl -d "Test message" https://ntfy.sh/atmosense-alerts
```

## Next Steps

1. **Customize Thresholds**: Edit ALERT_THRESHOLDS in config.py
2. **Deploy**: Use Docker or systemd service
3. **Integrate**: Connect to dashboard/web app
4. **Monitor**: Check atmosense.log for issues
5. **Improve**: Retrain models with more historical data

## Performance Metrics

After training, check these in the console:
- **TNN Test Loss**: Lower is better (target < 0.5)
- **RNN Test Loss**: Lower is better (target < 1.0)
- **MAE**: Mean Absolute Error in °C/% units

If performance is poor:
- Add more training data
- Increase EPOCHS in config.py
- Adjust hyperparameters in TNN_CONFIG and RNN_CONFIG
- Try longer LOOK_BACK window (72 → 96 hours)

## File Structure After Setup

```
weather_forecast/
├── data/
│   └── weather_data.csv
├── models/
│   ├── tnn_model.h5          ← Created after training
│   ├── rnn_model.h5          ← Created after training
│   └── scaler.pkl            ← Created after preprocessing
├── src/
│   ├── preprocess.py
│   ├── train_tnn.py
│   ├── train_rnn.py
│   ├── predict.py
│   ├── live_input.py
│   └── alert.py
├── main.py
├── config.py                 ← EDIT THIS!
├── requirements.txt
├── README.md
├── .gitignore
├── atmosense.log             ← Auto-created
└── predictions_log.csv       ← Auto-created
```

## That's It!

You now have a production-ready weather forecasting system. 🚀

For questions, see README.md for detailed documentation.
