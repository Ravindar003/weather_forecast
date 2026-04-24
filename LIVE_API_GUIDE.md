# 🌤️ Live Weather Prediction Guide

## Getting Started with Live Weather Data

This guide shows you how to fetch live weather data from OpenWeatherMap API and make predictions.

---

## 📋 Quick Start

### 1. Get an OpenWeatherMap API Key (FREE)

**Step-by-step:**
1. Visit: https://openweathermap.org/api
2. Scroll to "Current weather data" section
3. Click "Subscribe" (Free tier available)
4. Create a free account
5. Go to your API Keys page in Account settings
6. Copy your API key

**Free tier includes:**
- Current weather data
- 5-day forecasts
- Up to 60 requests/minute
- Perfect for our use case!

### 2. Configure the API Key

**Option A: Using Interactive Setup**
```bash
python setup_live_api.py
```
Then select option 1 and paste your API key. It will be saved to `config.py`.

**Option B: Direct Command Line**
```bash
python live_prediction.py YOUR_API_KEY_HERE
```

**Option C: Edit config.py Directly**
```python
# In config.py, find this line:
OPENWEATHERMAP_API_KEY = "your_api_key_here"

# Replace with your actual key:
OPENWEATHERMAP_API_KEY = "abc123def456..."
```

---

## 🚀 Usage

### Run Live Prediction (Simple)
```bash
python live_prediction.py
```

**Output will show:**
- ✓ Current weather data fetched from API
- ✓ All extracted features (temperature, humidity, wind, etc.)
- ✓ Neural network prediction
- ✓ Comparison: current vs. predicted temperature

### Run with Interactive Setup
```bash
python setup_live_api.py
```

**Menu Options:**
- 1️⃣ **Configure API Key** - Set up or update your API key
- 2️⃣ **Run Live Prediction** - Prompts for API key if needed
- 3️⃣ **Run Live Prediction** - Uses saved API key from config.py
- 4️⃣ **Show API Key Status** - Check if API key is configured
- 5️⃣ **Exit** - Close the program

---

## 📊 What Data is Fetched?

The system fetches these features from OpenWeatherMap API:

| Feature | Source | Description |
|---------|--------|-------------|
| **tempm** | `main.temp` | Current temperature (°C) |
| **hum** | `main.humidity` | Humidity (%) |
| **pressurem** | `main.pressure` | Air pressure (hPa) |
| **windchillm** | `main.feels_like` | Wind chill (°C) |
| **heatindexm** | `main.feels_like` | Heat index (°C) |
| **dewptm** | `main.dew_point` | Dew point (°C) |
| **wspdm** | `wind.speed` | Wind speed (km/h) |
| **wgustm** | `wind.gust` | Wind gust (km/h) |
| **wdird** | `wind.deg` | Wind direction (°) |
| **vism** | `visibility` | Visibility (km) |
| **precipm** | `rain.1h` | Rainfall (mm/hour) |
| **fog** | `weather.main` | Fog indicator (1/0) |
| **rain** | `weather.main` | Rain indicator (1/0) |
| **snow** | `weather.main` | Snow indicator (1/0) |
| **thunder** | `weather.main` | Thunderstorm indicator (1/0) |

---

## 🔮 Prediction Output

**Example Output:**

```
======================================================================
📍 LOCATION INFORMATION
======================================================================
City: Tiruchirappalli
Latitude: 10.7905
Longitude: 78.7047

======================================================================
🌡️  CURRENT WEATHER CONDITIONS
======================================================================
Temperature:            32.5°C
Feels Like:             35.2°C
Humidity:                 65%
Pressure:              1013.2 hPa
Wind Speed:             12.5 km/h
Wind Gust:              18.3 km/h
Wind Direction:          120°
Visibility:              10.0 km
Conditions:              Partly cloudy
Description:             partly cloudy

======================================================================
🔮 TEMPERATURE PREDICTION
======================================================================
Current Temperature:     32.50°C
Predicted Temperature:   30.75°C
Temperature Change:       -1.75°C (-5.4%)
Prediction Time:        2026-04-24 14:30:45
======================================================================
```

---

## 📈 Integration with Dashboard

The live predictions automatically integrate with your Streamlit dashboard!

**How it works:**
1. Run: `python live_prediction.py`
2. Predictions are saved to `predictions_log.csv`
3. Open the dashboard: `streamlit run dashboard.py`
4. See live predictions in the charts and tables!

---

## 🔧 Advanced: Using Different Locations

**In config.py:**
```python
# Change location by modifying:
CITY = "London"
LAT = 51.5074
LON = -0.1278
```

**Popular Coordinates:**
- **New York**: LAT=40.7128, LON=-74.0060
- **London**: LAT=51.5074, LON=-0.1278
- **Tokyo**: LAT=35.6762, LON=139.6503
- **Sydney**: LAT=-33.8688, LON=151.2093
- **Mumbai**: LAT=19.0760, LON=72.8777

---

## ⚠️ Troubleshooting

### "API key not configured"
```
❌ OpenWeatherMap API key not configured
Please set OPENWEATHERMAP_API_KEY in config.py
```
**Solution:** Run `python setup_live_api.py` and select option 1

### "API request failed"
```
❌ API request failed: [error message]
```
**Possible causes:**
- Invalid API key
- API rate limit exceeded (wait a minute)
- No internet connection
- Wrong latitude/longitude

**Solution:**
1. Verify API key is correct
2. Check internet connection
3. Wait a few minutes if rate limited

### "Cannot extract features"
```
Error extracting features: [error]
```
**Solution:**
- Make sure you have latest version of required packages
- Try running: `pip install --upgrade requests`

---

## 📊 Data Saved

**Predictions are saved to:**

1. **predictions_log.csv** - Cumulative log of all predictions
   - Added to existing data
   - Used by dashboard for historical charts

2. **latest_live_prediction.json** - Latest prediction in JSON format
   - Full API response included
   - Useful for debugging
   - Can be used by other applications

---

## 🎯 Next Steps

1. ✅ Get your free API key (5 minutes)
2. ✅ Configure the system (1 minute)
3. ✅ Run your first live prediction (1 minute)
4. ✅ View in dashboard (open browser)

**Total time: ~10 minutes!**

---

## 📞 API Documentation

For more information on the OpenWeatherMap API:
- **Main API Docs**: https://openweathermap.org/api
- **Current Weather**: https://openweathermap.org/current
- **API Response Format**: https://openweathermap.org/weather-conditions

---

## ✨ Features

✅ **Real-time Weather Data** - Live data from OpenWeatherMap
✅ **Neural Network Predictions** - PyTorch RNN model
✅ **Automatic Feature Extraction** - All preprocessing handled
✅ **Dashboard Integration** - Automatic Streamlit updates
✅ **Historical Logging** - Cumulative prediction records
✅ **Error Handling** - Graceful failure with clear messages
✅ **Multiple Locations** - Can predict for any location

---

**Happy Forecasting! 🌤️**
