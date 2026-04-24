"""
Demo: Live Weather API Integration
Shows example output without requiring an actual API key.
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
import config


def create_mock_api_response():
    """Create a mock OpenWeatherMap API response for demonstration."""
    return {
        'name': config.CITY,
        'coord': {
            'lat': config.LAT,
            'lon': config.LON
        },
        'main': {
            'temp': 32.5,
            'feels_like': 35.2,
            'humidity': 65,
            'pressure': 1013,
            'dew_point': 22.1,
        },
        'wind': {
            'speed': 3.5,  # m/s
            'gust': 5.1,
            'deg': 120
        },
        'clouds': {
            'all': 40
        },
        'visibility': 10000,
        'rain': {
            '1h': 0.0
        },
        'weather': [{
            'main': 'Clouds',
            'description': 'partly cloudy'
        }]
    }


def display_api_response_demo():
    """Display example API response."""
    print("\n" + "=" * 70)
    print("📡 EXAMPLE OpenWeatherMap API Response")
    print("=" * 70)
    
    api_response = create_mock_api_response()
    print("\nRaw JSON Response:")
    print(json.dumps(api_response, indent=2))


def display_extracted_features_demo():
    """Display example extracted features."""
    print("\n" + "=" * 70)
    print("🔧 EXTRACTED FEATURES")
    print("=" * 70)
    
    api_response = create_mock_api_response()
    main = api_response.get('main', {})
    wind = api_response.get('wind', {})
    
    features = {
        'tempm': main.get('temp', 0),
        'hum': main.get('humidity', 0),
        'pressurem': main.get('pressure', 0) / 10,
        'dewptm': main.get('dew_point', 0),
        'heatindexm': main.get('feels_like', 0),
        'windchillm': main.get('feels_like', 0),
        'wspdm': wind.get('speed', 0) * 3.6,  # m/s to km/h
        'wgustm': wind.get('gust', 0) * 3.6,
        'wdird': wind.get('deg', 0),
        'vism': api_response.get('visibility', 10000) / 1000,
        'precipm': api_response.get('rain', {}).get('1h', 0),
        'fog': 0,
        'rain': 0,
        'snow': 0,
        'thunder': 0,
        'tornado': 0,
        'hail': 0,
    }
    
    print("\nExtracted Feature Values:")
    print(f"{'Feature':<20} {'Value':<15} {'Unit'}")
    print("-" * 50)
    for key, value in features.items():
        if 'h' in key and 'm' in key:  # Time-based
            print(f"{key:<20} {value:>14.2f} {'':<15}")
        elif key in ['hum', 'fog', 'rain', 'snow', 'thunder', 'tornado', 'hail']:
            print(f"{key:<20} {int(value):>14d} {'':<15}")
        elif key == 'wdird':
            print(f"{key:<20} {int(value):>14d} {'degrees':<15}")
        else:
            print(f"{key:<20} {value:>14.2f} {'':<15}")


def display_prediction_process():
    """Display the prediction process."""
    print("\n" + "=" * 70)
    print("🔮 PREDICTION PROCESS")
    print("=" * 70)
    
    steps = [
        "1️⃣  Fetch current weather from API",
        "   └─ Temperature: 32.5°C",
        "   └─ Humidity: 65%",
        "   └─ Wind: 12.6 km/h",
        "",
        "2️⃣  Extract 25 features",
        "   └─ Numeric values (temp, humidity, pressure, etc.)",
        "   └─ Binary indicators (fog, rain, snow, etc.)",
        "   └─ Time-based features (hour_sin, day_cos, etc.)",
        "",
        "3️⃣  Scale features using StandardScaler",
        "   └─ Normalize to mean=0, std=1",
        "   └─ Uses saved scaler from training",
        "",
        "4️⃣  Create sequence (48 timesteps)",
        "   └─ Input shape: [1, 48, 25]",
        "   └─ 1 sample, 48-hour history, 25 features",
        "",
        "5️⃣  Pass through RNN model",
        "   └─ 2-layer RNN (128 units each)",
        "   └─ Fully connected output layer",
        "",
        "6️⃣  Inverse-scale prediction",
        "   └─ Convert from scaled to actual temperature",
        "",
        "7️⃣  Display results & save to log",
        "   └─ Save to predictions_log.csv",
        "   └─ Save to latest_live_prediction.json",
    ]
    
    for step in steps:
        print(step)


def display_sample_output():
    """Display sample prediction output."""
    print("\n" + "=" * 70)
    print("📊 SAMPLE PREDICTION OUTPUT")
    print("=" * 70)
    
    print("""
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
Pressure:              101.3 kPa
Wind Speed:             12.6 km/h
Wind Gust:              18.4 km/h
Wind Direction:         120°
Visibility:             10.0 km
Conditions:            Clouds
Description:           partly cloudy

======================================================================
🔮 TEMPERATURE PREDICTION
======================================================================
Current Temperature:     32.50°C
Predicted Temperature:   30.75°C
Temperature Change:      -1.75°C (-5.4%)
Prediction Time:        2026-04-24 15:45:30
======================================================================
""")


def display_integration_info():
    """Display integration with dashboard."""
    print("\n" + "=" * 70)
    print("🌐 DASHBOARD INTEGRATION")
    print("=" * 70)
    
    print("""
After running live predictions, the data automatically integrates with
your Streamlit dashboard!

📊 What you'll see in the dashboard:
  ✓ Real-time temperature metrics (current, predicted, change)
  ✓ Weather alerts if conditions worsen
  ✓ Updated prediction history table
  ✓ Charts comparing live predictions with observations
  ✓ Statistics on prediction accuracy
  ✓ Prediction distribution analysis

🚀 To view in dashboard:
  1. Run: python live_prediction.py
  2. Open: http://localhost:8501 in your browser
  3. Click "Generate New Prediction" to see live data
  4. Charts update automatically!
""")


def display_files_created():
    """Display files that will be created."""
    print("\n" + "=" * 70)
    print("💾 FILES CREATED/UPDATED")
    print("=" * 70)
    
    print("""
After running live predictions:

1. predictions_log.csv
   ├─ Cumulative log of all predictions
   ├─ Used by dashboard for charts
   └─ Example rows:
      timestamp, observation_time, temperature, source, location
      2026-04-24 15:45:30, 2026-04-24 15:45:30, 30.75, live_api, Tiruchirappalli

2. latest_live_prediction.json
   ├─ Latest prediction with full data
   ├─ Includes entire API response
   └─ Useful for debugging and integration

3. config.py (if saving API key)
   └─ OPENWEATHERMAP_API_KEY updated
""")


def main():
    """Main demo display."""
    print("\n" + "=" * 80)
    print(" " * 15 + "🌤️  LIVE WEATHER PREDICTION - API INTEGRATION DEMO")
    print("=" * 80)
    
    print("""
This demo shows how the live weather prediction system works with the
OpenWeatherMap API. No API key needed to see this demonstration!
""")
    
    display_api_response_demo()
    display_extracted_features_demo()
    display_prediction_process()
    display_sample_output()
    display_integration_info()
    display_files_created()
    
    print("\n" + "=" * 80)
    print(" " * 25 + "🚀 QUICK START INSTRUCTIONS")
    print("=" * 80)
    
    print("""
1️⃣  GET API KEY (FREE - 5 minutes):
    • Visit: https://openweathermap.org/api
    • Sign up (free tier available)
    • Get your API key from account dashboard

2️⃣  CONFIGURE THE SYSTEM (1 minute):
    Option A - Interactive:
      python setup_live_api.py
      Select option 1, paste your API key
    
    Option B - Command line:
      python live_prediction.py YOUR_API_KEY_HERE
    
    Option C - Edit config.py:
      Open config.py and replace "your_api_key_here"

3️⃣  RUN LIVE PREDICTION (1 minute):
    python live_prediction.py
    
    View in dashboard:
    http://localhost:8501

4️⃣  AUTOMATE (Optional):
    python setup_live_api.py
    Select option 3 for regular updates

📚 Documentation:
    • Full guide: LIVE_API_GUIDE.md
    • Source code: live_prediction.py
    • Setup wizard: setup_live_api.py
    • Config file: config.py

✨ Features:
   ✓ Real-time weather from OpenWeatherMap
   ✓ Automatic feature extraction
   ✓ PyTorch neural network prediction
   ✓ Dashboard integration
   ✓ Historical logging
   ✓ Multiple locations supported

Total time to first prediction: ~10 minutes!
""")
    
    print("=" * 80)
    print("Ready to start? Get your free API key and run: python setup_live_api.py\n")


if __name__ == "__main__":
    main()
