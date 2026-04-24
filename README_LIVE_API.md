# 🌤️ Live Weather Prediction - OpenWeatherMap API Integration

## 📌 Overview

This system integrates with the **OpenWeatherMap API** to fetch real-time weather data and generate predictions using your trained PyTorch RNN neural network.

**Key Features:**
- ✅ Real-time weather data from OpenWeatherMap
- ✅ Automatic feature extraction (25+ features)
- ✅ Seamless neural network prediction
- ✅ Automatic Streamlit dashboard integration
- ✅ Historical prediction logging
- ✅ Support for any location worldwide

---

## 🚀 Quick Start (10 minutes)

### 1. Get Free API Key
1. Visit: https://openweathermap.org/api
2. Sign up (free tier available)
3. Get your API key from account dashboard

### 2. Configure System
```bash
python setup_live_api.py
# Select option 1 and paste your API key
```

### 3. Run Live Prediction
```bash
python live_prediction.py
```

### 4. View in Dashboard
- Open: http://localhost:8501
- Click "Generate New Prediction"
- See live data in charts!

---

## 📁 New Files Created

### Core System
| File | Purpose |
|------|---------|
| **live_prediction.py** | Main prediction engine using live API data |
| **setup_live_api.py** | Interactive setup wizard for API configuration |
| **demo_live_api.py** | Demo showing how the system works (no API key needed) |

### Documentation
| File | Purpose |
|------|---------|
| **LIVE_API_GUIDE.md** | Complete guide with examples and troubleshooting |
| **README_LIVE_API.md** | This file - Quick reference |

---

## 🔧 How It Works

### Data Flow
```
OpenWeatherMap API
         ↓
Fetch current weather
         ↓
Extract 25 features
   (temperature, humidity, wind, conditions, etc.)
         ↓
Scale with StandardScaler
         ↓
Create 48-timestep sequence
         ↓
PyTorch RNN Model (2-layer, 128 units)
         ↓
Temperature Prediction
         ↓
Save to predictions_log.csv
Save to latest_live_prediction.json
         ↓
Streamlit Dashboard
```

### Extracted Features

**Numeric Features (13):**
- Temperature, Humidity, Pressure
- Wind Speed, Wind Gust, Wind Direction
- Visibility, Dew Point
- Heat Index, Wind Chill
- Rainfall, Feels Like Temperature

**Categorical Features (6):**
- Fog, Rain, Snow, Thunder, Tornado, Hail (binary 1/0)

**Time-Based Features (6):**
- Hour sine/cosine, Day sine/cosine
- Heat delta, Chill delta

**Total: 25 features** ✓

---

## 💻 Usage Examples

### Example 1: Run with Saved API Key
```bash
python setup_live_api.py
# Select option 3: Run live prediction (with saved API key)
```

### Example 2: Command Line with API Key
```bash
python live_prediction.py YOUR_API_KEY_HERE
```

### Example 3: Interactive Setup
```bash
python setup_live_api.py
# Menu:
#  1. Configure API key
#  2. Run live prediction (with API key prompt)
#  3. Run live prediction (with saved API key)
#  4. Show current API key status
#  5. Exit
```

### Example 4: See Demo (No API Key Needed)
```bash
python demo_live_api.py
# Shows example data and prediction process
```

---

## 📊 Prediction Output Example

```
======================================================================
🌡️  CURRENT WEATHER CONDITIONS
======================================================================
Temperature:            32.5°C
Feels Like:             35.2°C
Humidity:                 65%
Pressure:              101.3 kPa
Wind Speed:             12.6 km/h
Wind Gust:              18.4 km/h
Wind Direction:         120°
Visibility:             10.0 km
Conditions:            Clouds

======================================================================
🔮 TEMPERATURE PREDICTION
======================================================================
Current Temperature:     32.50°C
Predicted Temperature:   30.75°C
Temperature Change:      -1.75°C (-5.4%)
Prediction Time:        2026-04-24 15:45:30
======================================================================
```

---

## 🌐 Dashboard Integration

**Automatic:** Predictions automatically appear in your dashboard!

**What updates:**
- ✅ Current temperature metric
- ✅ Prediction charts
- ✅ Prediction history table
- ✅ Weather alerts
- ✅ Statistics and distributions

**How to view:**
1. Keep Streamlit running: `streamlit run dashboard.py`
2. Run predictions: `python live_prediction.py`
3. Open dashboard at: http://localhost:8501
4. Charts auto-update!

---

## 🔍 Configuration

### Default Location: Tiruchirappalli, India
```python
# In config.py:
CITY = "Tiruchirappalli"
LAT = 10.7905
LON = 78.7047
```

### Change to Different Location
```python
# Examples:
# London
CITY = "London"
LAT = 51.5074
LON = -0.1278

# New York
CITY = "New York"
LAT = 40.7128
LON = -74.0060

# Tokyo
CITY = "Tokyo"
LAT = 35.6762
LON = 139.6503
```

---

## 📁 Data Files

### predictions_log.csv
Cumulative log of all predictions (appended on each run)
```csv
timestamp,observation_time,temperature,source,location
2026-04-24 15:45:30,2026-04-24 15:45:30,30.75,live_api,Tiruchirappalli
```

### latest_live_prediction.json
Latest prediction with full details (useful for debugging)
```json
{
  "timestamp": "2026-04-24T15:45:30",
  "location": {
    "name": "Tiruchirappalli",
    "lat": 10.7905,
    "lon": 78.7047
  },
  "current": {
    "temperature": 32.5,
    "humidity": 65,
    "conditions": "Clouds"
  },
  "prediction": {
    "temperature": 30.75,
    "timestamp": "2026-04-24T15:45:30"
  }
}
```

---

## ⚠️ Troubleshooting

### "API key not configured"
```bash
python setup_live_api.py
# Select option 1 to configure
```

### "API request failed"
- Check internet connection
- Verify API key is correct
- Check if rate limit exceeded (wait a minute)
- Verify latitude/longitude are correct

### "Cannot extract features"
```bash
pip install --upgrade requests pandas numpy
python demo_live_api.py  # Test without API
```

### Dashboard not updating
- Make sure Streamlit is still running
- Refresh browser (F5)
- Check terminal for errors
- Run `streamlit cache clear` if needed

---

## 🎯 Next Steps

✅ **Phase 1: Setup** (5 minutes)
- [ ] Get API key from https://openweathermap.org/api
- [ ] Run `python setup_live_api.py`
- [ ] Save API key to config.py

✅ **Phase 2: Test** (2 minutes)
- [ ] Run `python demo_live_api.py` (see example)
- [ ] Run `python live_prediction.py` (use actual data)

✅ **Phase 3: Dashboard** (1 minute)
- [ ] Make sure `streamlit run dashboard.py` is running
- [ ] Generate new predictions from dashboard button
- [ ] See live data in charts!

✅ **Phase 4: Automation** (Optional)
- [ ] Set up scheduled predictions
- [ ] Monitor weather alerts
- [ ] Export predictions for analysis

---

## 📚 Documentation Files

| File | Content |
|------|---------|
| **LIVE_API_GUIDE.md** | Complete guide with examples, locations, API info |
| **live_prediction.py** | Source code - Main prediction engine |
| **setup_live_api.py** | Source code - Interactive setup wizard |
| **demo_live_api.py** | Source code - Demo showing how it works |
| **config.py** | Configuration file - API keys, locations, parameters |

---

## 🔗 Useful Links

- **OpenWeatherMap API**: https://openweathermap.org/api
- **Get Free API Key**: https://openweathermap.org/api/free
- **API Documentation**: https://openweathermap.org/current
- **Weather Conditions**: https://openweathermap.org/weather-conditions

---

## ✨ What's Included

### Scripts (3)
- ✅ `live_prediction.py` - Fetch weather & predict
- ✅ `setup_live_api.py` - Interactive setup
- ✅ `demo_live_api.py` - Demo with examples

### Documentation (2)
- ✅ `LIVE_API_GUIDE.md` - Full guide
- ✅ `README_LIVE_API.md` - This file

### Integration
- ✅ Automatic Streamlit dashboard updates
- ✅ CSV logging (predictions_log.csv)
- ✅ JSON export (latest_live_prediction.json)
- ✅ Configuration management (config.py)

---

## 🚀 Ready to Start?

```bash
# 1. See demo (no API needed)
python demo_live_api.py

# 2. Get API key from https://openweathermap.org/api

# 3. Configure system
python setup_live_api.py

# 4. Run live prediction
python live_prediction.py

# 5. View in dashboard at http://localhost:8501
```

**Total time: 10 minutes! ⚡**

---

**Happy Weather Forecasting! 🌤️**
