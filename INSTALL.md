# Installation and Setup Guide

## System Requirements

- **Python**: 3.8 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Disk Space**: 2GB for models and data
- **OS**: Windows, macOS, or Linux
- **Internet**: Required for live weather data

## Step-by-Step Installation

### 1. Clone or Download the Project

```bash
cd /path/to/your/projects
git clone <repository-url> weather_forecast
cd weather_forecast
```

### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

**Verify Installation:**
```bash
python test_system.py
```

### 4. Configure API Credentials

Edit `config.py` and add your API keys:

#### A. OpenWeatherMap (Required for Live Data)

1. Go to: https://openweathermap.org/api
2. Sign up for free (free tier available)
3. Copy your API key from dashboard
4. Paste in `config.py`:

```python
OPENWEATHERMAP_API_KEY = "your_api_key_here"
```

Test: `python -c "from src.live_input import fetch_live_weather; print(fetch_live_weather())"`

#### B. Gmail SMTP (Optional - for Email Alerts)

If using Gmail:

1. Enable 2-Factor Authentication: https://myaccount.google.com/security
2. Create App Password: https://myaccount.google.com/apppasswords
3. Select "Mail" and "Windows" for app and device
4. Copy the 16-character password
5. Update `config.py`:

```python
EMAIL_SENDER = "your_email@gmail.com"
EMAIL_PASSWORD = "xxxx xxxx xxxx xxxx"  # 16-char password from step 4
EMAIL_RECIPIENT = "recipient@example.com"
ENABLE_EMAIL = True
```

For non-Gmail SMTP servers, adjust accordingly.

#### C. Twilio (Optional - for SMS Alerts)

1. Sign up: https://www.twilio.com (free trial $15 credit)
2. Get credentials from: https://www.twilio.com/console
3. Update `config.py`:

```python
TWILIO_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_TOKEN = "your_auth_token"
TWILIO_FROM = "+1XXXXXXXXXX"      # Your Twilio phone
TWILIO_TO = "+91XXXXXXXXXX"       # Recipient phone
ENABLE_SMS = True
```

#### D. ntfy.sh (Optional - for Push Notifications)

Already configured! Just ensure enabled:

```python
ENABLE_PUSH = True
NTFY_TOPIC = "atmosense-alerts"
```

View alerts at: https://ntfy.sh/atmosense-alerts

### 5. Customize Configuration (Optional)

Edit `config.py` to adjust:

**Location:**
```python
CITY = "Tiruchirappalli"
LAT = 10.7905
LON = 78.7047
```

**Alert Thresholds:**
```python
ALERT_THRESHOLDS = {
    "tempm": {"danger": 40, "warning": 35},
    # ... customize as needed
}
```

**Scheduling:**
```python
SCHEDULE_INTERVAL = 1
SCHEDULE_UNIT = "hours"  # or "minutes", "seconds"
```

### 6. Train Models

```bash
# Train TNN Model (takes ~5-10 minutes)
python src/train_tnn.py

# Train Vanilla RNN Model (takes ~5-10 minutes)
python src/train_rnn.py
```

**What gets created:**
- `models/tnn_model.h5` - TNN model
- `models/rnn_model.h5` - RNN model
- `models/scaler.pkl` - Feature scaler
- `models/tnn_training.png` - Loss curves
- `models/rnn_training.png` - Loss curves

**Monitor Training:**
```bash
tail -f atmosense.log
```

### 7. Verify Installation

```bash
python test_system.py
```

Expected output:
```
✓ All systems operational! Ready to run forecasts.
```

If any test fails, see the troubleshooting section below.

---

## Running the System

### Option 1: Single Forecast

```bash
python -c "
from main import WeatherForecastingSystem
system = WeatherForecastingSystem()
system.run_pipeline()
"
```

### Option 2: Continuous Scheduling (Recommended)

```bash
python main.py
```

Runs indefinitely with hourly forecasts. Press Ctrl+C to stop.

### Option 3: Docker

```bash
# Build image
docker build -t atmosense .

# Run container
docker run -d \
  --name atmosense-forecaster \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/data:/app/data \
  --restart unless-stopped \
  atmosense

# View logs
docker logs -f atmosense-forecaster
```

### Option 4: Docker Compose

```bash
docker-compose up -d

# View logs
docker-compose logs -f atmosense
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError"

**Solution:** Ensure virtual environment is activated and requirements installed

```bash
# Windows
venv\Scripts\activate
pip install -r requirements.txt

# macOS/Linux
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "API key not found" or "Invalid API key"

**Solution:** Check OpenWeatherMap API configuration

```bash
# Verify key is correct
python -c "
import config
print(f'API Key: {config.OPENWEATHERMAP_API_KEY[:10]}...')
"

# Test with curl
curl "https://api.openweathermap.org/data/2.5/weather?lat=10.7905&lon=78.7047&appid=YOUR_KEY"
```

### Issue: "Model file not found"

**Solution:** Train models first

```bash
python src/train_tnn.py
python src/train_rnn.py

# Verify files exist
ls models/
```

### Issue: "Email failed" or "Cannot send SMS"

**Solutions:**
- Email: Verify Gmail App Password (not regular password)
- SMS: Check Twilio account has credits
- Push: Test at https://ntfy.sh/atmosense-alerts

### Issue: "Out of memory" or "CUDA out of memory"

**Solutions:**
```python
# In config.py, reduce:
BATCH_SIZE = 16  # Lower from 32
EPOCHS = 50      # Lower from 100

# Or use CPU only:
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
```

### Issue: "Slow training" or "Slow predictions"

**Solutions:**
- Use GPU: Install `tensorflow-gpu` for faster training
- Reduce lookback: `LOOK_BACK = 24` instead of 72
- Reduce features: Remove less important columns
- Increase batch size: `BATCH_SIZE = 64` (if RAM allows)

### Issue: Low prediction accuracy

**Solutions:**
- **Add more data:** Use larger, more diverse weather dataset
- **Longer training:** Increase EPOCHS
- **Better features:** Manually add domain-specific features
- **Hyperparameter tuning:** Adjust learning rates and layer sizes
- **Ensemble weights:** Adjust TNN (0.65) vs RNN (0.35) in predict.py

### Issue: Docker container won't start

**Solution:** Check logs and ensure config is valid

```bash
docker logs atmosense-forecaster

# Rebuild if needed
docker build --no-cache -t atmosense .
```

---

## Production Deployment

### Linux Systemd Service

```bash
# Copy service file
sudo cp atmosense.service /etc/systemd/system/

# Create user
sudo useradd -r -s /bin/bash atmosense

# Install application
sudo mkdir -p /opt/atmosense
sudo cp -r . /opt/atmosense/
sudo chown -R atmosense:atmosense /opt/atmosense

# Create virtual environment
cd /opt/atmosense
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
sudo nano /opt/atmosense/config.py  # Add API keys

# Train models
python src/train_tnn.py
python src/train_rnn.py

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable atmosense
sudo systemctl start atmosense

# Check status
sudo systemctl status atmosense

# View logs
sudo journalctl -u atmosense -f
```

### AWS EC2 Deployment

```bash
# SSH into instance
ssh -i key.pem ubuntu@your-instance.compute.amazonaws.com

# Install Python
sudo apt update && sudo apt install -y python3.9 python3-pip

# Clone repository
git clone <repo> /home/ubuntu/atmosense
cd /home/ubuntu/atmosense

# Setup and run
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Edit config with your API keys
nano config.py

# Train models
python3 src/train_tnn.py
python3 src/train_rnn.py

# Run with nohup to keep running after logout
nohup python3 main.py > atmosense.log 2>&1 &
```

### Heroku Deployment

Create `Procfile`:
```
web: python main.py
```

Create `runtime.txt`:
```
python-3.9.0
```

Deploy:
```bash
heroku create atmosense-app
git push heroku main
heroku logs --tail
```

---

## Performance Optimization

### Faster Inference

```python
# Use TensorFlow Lite
import tensorflow as tf

converter = tf.lite.TFLiteConverter.from_saved_model("models/tnn_model.h5")
tflite_model = converter.convert()

# Saves ~30% file size, ~5% speed improvement
with open("models/tnn_model.tflite", "wb") as f:
    f.write(tflite_model)
```

### Batch Processing

```python
# Process multiple locations
locations = [
    (10.7905, 78.7047),  # Tiruchirappalli
    (13.0827, 80.2707),  # Chennai
    (12.2381, 76.6550),  # Bangalore
]

for lat, lon in locations:
    config.LAT = lat
    config.LON = lon
    system.run_pipeline()
```

### Model Caching

```python
# Load models once
from src.predict import EnsemblePredictor

predictor = EnsemblePredictor()
predictor.load_models()

# Reuse for multiple predictions
for i in range(100):
    ensemble_pred, _ = predictor.ensemble_predict(X[i])
```

---

## Updating and Maintenance

### Update Dependencies

```bash
pip install --upgrade -r requirements.txt
```

### Retrain Models Periodically

```bash
# Monthly or quarterly retraining recommended
python src/train_tnn.py
python src/train_rnn.py
```

### Backup

```bash
# Backup models and config
tar -czf atmosense-backup-$(date +%Y%m%d).tar.gz \
    models/ \
    data/ \
    config.py \
    predictions_log.csv
```

### Monitor

```bash
# Check system status
python test_system.py

# View prediction log
tail -50 predictions_log.csv

# Check disk space
du -sh .

# Check memory usage (Linux)
ps aux | grep python
```

---

## Security Best Practices

1. **Never commit credentials**
   ```bash
   git add -A
   git rm --cached config.py
   echo "config.py" >> .gitignore
   git commit -m "Remove config from tracking"
   ```

2. **Use environment variables**
   ```bash
   export OPENWEATHERMAP_API_KEY="your_key"
   export EMAIL_PASSWORD="your_password"
   ```

3. **Restrict file permissions**
   ```bash
   chmod 600 config.py
   chmod 700 models/
   ```

4. **Use secrets manager**
   ```python
   # AWS Secrets Manager
   import boto3
   
   client = boto3.client('secretsmanager')
   secret = client.get_secret_value(SecretId='atmosense/config')
   ```

---

## Next Steps

1. **Run initial forecast:** `python -c "from main import WeatherForecastingSystem; WeatherForecastingSystem().run_pipeline()"`
2. **Check predictions:** Look at console output
3. **Schedule continuous runs:** `python main.py`
4. **Monitor performance:** Check `atmosense.log`
5. **Add to production:** Use systemd, Docker, or cloud platform

---

## Support

- **Documentation:** See README.md
- **API Reference:** See API.md
- **Quick Start:** See QUICKSTART.md
- **Issues:** Check troubleshooting section above
- **Logs:** Check `atmosense.log` for detailed error messages

---

**Installation Complete!** 🎉

You now have a fully functional weather forecasting system. Start with:

```bash
python main.py
```

Happy forecasting! 🌡️
