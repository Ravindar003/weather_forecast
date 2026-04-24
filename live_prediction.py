"""
Live Weather Prediction from OpenWeatherMap API
Fetches current weather data and generates predictions.
"""

import requests
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import joblib
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
import json

sys.path.insert(0, str(Path(__file__).parent))
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VanillaRNNPyTorch(nn.Module):
    """PyTorch RNN for weather forecasting."""
    
    def __init__(self, input_size=25):
        super().__init__()
        self.rnn = nn.RNN(input_size, 128, batch_first=True, num_layers=2, dropout=0.2)
        self.fc = nn.Sequential(
            nn.Linear(128, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 1)
        )
    
    def forward(self, x):
        out, _ = self.rnn(x)
        out = out[:, -1, :]
        out = self.fc(out)
        return out


def fetch_current_weather(api_key=None, lat=None, lon=None):
    """
    Fetch current weather from OpenWeatherMap API.
    
    Args:
        api_key: OpenWeatherMap API key
        lat: Latitude
        lon: Longitude
    
    Returns:
        Dictionary with current weather data
    """
    if api_key is None:
        api_key = config.OPENWEATHERMAP_API_KEY
    if lat is None:
        lat = config.LAT
    if lon is None:
        lon = config.LON
    
    if api_key == "your_api_key_here":
        logger.error("❌ OpenWeatherMap API key not configured")
        logger.info("Please set OPENWEATHERMAP_API_KEY in config.py")
        logger.info("Get a free API key from: https://openweathermap.org/api")
        return None
    
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        'lat': lat,
        'lon': lon,
        'appid': api_key,
        'units': 'metric'  # Get temperatures in Celsius
    }
    
    try:
        logger.info(f"Fetching weather data for ({lat}, {lon})...")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logger.info("✓ Weather data fetched successfully")
        return data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ API request failed: {e}")
        return None


def extract_weather_features(weather_data):
    """
    Extract features from OpenWeatherMap API response.
    
    Args:
        weather_data: Response from OpenWeatherMap API
    
    Returns:
        Dictionary with extracted features
    """
    if weather_data is None:
        return None
    
    try:
        # Main weather info
        main = weather_data.get('main', {})
        clouds = weather_data.get('clouds', {})
        wind = weather_data.get('wind', {})
        rain = weather_data.get('rain', {})
        weather = weather_data.get('weather', [{}])[0]
        
        # Extract features
        features = {
            'tempm': float(main.get('temp', 0)),
            'hum': int(main.get('humidity', 0)),
            'pressurem': float(main.get('pressure', 0)) / 10,  # Convert to match dataset format
            'dewptm': float(main.get('dew_point', main.get('temp', 0))),
            'heatindexm': float(main.get('feels_like', main.get('temp', 0))),
            'windchillm': float(main.get('feels_like', main.get('temp', 0))),
            'wspdm': float(wind.get('speed', 0)) * 3.6,  # Convert m/s to km/h
            'wgustm': float(wind.get('gust', wind.get('speed', 0))) * 3.6,
            'wdird': int(wind.get('deg', 0)),
            'vism': float(weather_data.get('visibility', 10000)) / 1000,  # Convert to km
            'precipm': float(rain.get('1h', 0)) if rain else 0,  # Rainfall in last hour
            
            # Weather conditions (binary)
            'fog': 1 if 'mist' in weather.get('main', '').lower() else 0,
            'rain': 1 if weather.get('main', '').lower() == 'rain' else 0,
            'snow': 1 if weather.get('main', '').lower() == 'snow' else 0,
            'thunder': 1 if 'thunder' in weather.get('main', '').lower() else 0,
            'tornado': 0,  # Not available from API
            'hail': 0,     # Not available from API
        }
        
        return features
        
    except Exception as e:
        logger.error(f"Error extracting features: {e}")
        return None


def create_feature_sequence(current_features, historical_data=None):
    """
    Create feature sequence for model input.
    Uses current data and generates time-based features.
    
    Args:
        current_features: Current weather features
        historical_data: DataFrame with historical data (optional)
    
    Returns:
        Tuple of (X_scaled, feature_names, current_features_dict)
    """
    now = datetime.now()
    hour = now.hour
    day_of_year = now.timetuple().tm_yday
    
    # Add time features (circular encoding)
    current_features['hour_sin'] = float(np.sin(2 * np.pi * hour / 24))
    current_features['hour_cos'] = float(np.cos(2 * np.pi * hour / 24))
    current_features['day_sin'] = float(np.sin(2 * np.pi * day_of_year / 365))
    current_features['day_cos'] = float(np.cos(2 * np.pi * day_of_year / 365))
    
    # Calculate delta features
    current_features['heat_delta'] = current_features['heatindexm'] - current_features['tempm']
    current_features['chill_delta'] = current_features['windchillm'] - current_features['tempm']
    
    # If no historical data, use current temp for lags
    if historical_data is None or len(historical_data) == 0:
        current_features['tempm_lag1'] = current_features['tempm']
        current_features['tempm_lag3'] = current_features['tempm']
        current_features['tempm_lag6'] = current_features['tempm']
        current_features['tempm_lag12'] = current_features['tempm']
        current_features['tempm_lag24'] = current_features['tempm']
    else:
        # Use historical data for lags
        temps = historical_data['tempm'].values if 'tempm' in historical_data.columns else []
        current_features['tempm_lag1'] = float(temps[-1]) if len(temps) > 0 else current_features['tempm']
        current_features['tempm_lag3'] = float(temps[-3]) if len(temps) > 2 else current_features['tempm']
        current_features['tempm_lag6'] = float(temps[-6]) if len(temps) > 5 else current_features['tempm']
        current_features['tempm_lag12'] = float(temps[-12]) if len(temps) > 11 else current_features['tempm']
        current_features['tempm_lag24'] = float(temps[-24]) if len(temps) > 23 else current_features['tempm']
    
    # Get features in correct order
    feature_cols = ['dewptm', 'fog', 'hail', 'heatindexm', 'hum', 'precipm', 'pressurem', 'rain',
                    'snow', 'tempm', 'thunder', 'tornado', 'vism', 'wdird', 'wgustm', 'windchillm',
                    'wspdm', 'hour_sin', 'hour_cos', 'day_sin', 'day_cos', 'heat_delta', 'chill_delta',
                    'tempm_lag1', 'tempm_lag3']
    
    # Create feature array
    X = np.array([current_features.get(col, 0) for col in feature_cols]).reshape(1, -1)
    
    # Load scaler and scale
    scaler_X = joblib.load('models/scaler_X.pkl')
    X_scaled = scaler_X.transform(X)
    
    # Expand for sequence (1, 1, 25) -> repeat for sequence length
    X_scaled = np.repeat(X_scaled, 48, axis=0)  # 48 hours of sequence
    X_scaled = np.expand_dims(X_scaled, axis=0)  # Add batch dimension
    
    return X_scaled, feature_cols, current_features


def predict_with_live_data(api_key=None):
    """
    Fetch live weather data and make predictions.
    
    Args:
        api_key: OpenWeatherMap API key (optional)
    
    Returns:
        Dictionary with current data and predictions
    """
    logger.info("=" * 70)
    logger.info("🌤️ LIVE WEATHER PREDICTION FROM OpenWeatherMap API")
    logger.info("=" * 70)
    
    # Fetch current weather
    logger.info("\n1️⃣  Fetching live weather data...")
    weather_data = fetch_current_weather(api_key)
    
    if weather_data is None:
        logger.error("Cannot proceed without weather data")
        return None
    
    # Extract features
    logger.info("\n2️⃣  Extracting features...")
    current_features = extract_weather_features(weather_data)
    
    if current_features is None:
        logger.error("Cannot extract features")
        return None
    
    # Load historical data for context
    logger.info("\n3️⃣  Loading historical data for context...")
    try:
        historical_df = pd.read_csv('data/weather_data.csv')
        historical_df['datetime_utc'] = pd.to_datetime(historical_df['datetime_utc'])
        historical_df = historical_df.tail(72)
    except:
        logger.warning("   Historical data not available, using current data only")
        historical_df = None
    
    # Create feature sequence
    logger.info("\n4️⃣  Preparing prediction input...")
    X_scaled, feature_cols, features_dict = create_feature_sequence(current_features, historical_df)
    logger.info(f"   ✓ Input shape: {X_scaled.shape}")
    
    # Load model
    logger.info("\n5️⃣  Loading prediction model...")
    device = torch.device('cpu')
    model = VanillaRNNPyTorch(input_size=len(feature_cols))
    model.load_state_dict(torch.load('models/best_vanilla_rnn.pt', map_location=device))
    model.to(device)
    model.eval()
    logger.info("   ✓ Model loaded")
    
    # Make prediction
    logger.info("\n6️⃣  Generating prediction...")
    with torch.no_grad():
        X_tensor = torch.FloatTensor(X_scaled).to(device)
        y_pred_scaled = model(X_tensor).cpu().numpy()
    
    # Inverse scale
    scaler_y = joblib.load('models/scaler_y.pkl')
    y_pred = scaler_y.inverse_transform(y_pred_scaled)
    predicted_temp = float(y_pred[0, 0])
    
    logger.info(f"   ✓ Prediction: {predicted_temp:.2f}°C")
    
    # Compile results
    result = {
        'timestamp': datetime.now(),
        'location': {
            'name': weather_data.get('name', 'Unknown'),
            'lat': weather_data.get('coord', {}).get('lat'),
            'lon': weather_data.get('coord', {}).get('lon'),
        },
        'current': {
            'temperature': current_features['tempm'],
            'humidity': current_features['hum'],
            'pressure': current_features['pressurem'],
            'wind_speed': current_features['wspdm'],
            'wind_gust': current_features['wgustm'],
            'wind_direction': current_features['wdird'],
            'visibility': current_features['vism'],
            'feels_like': current_features['heatindexm'],
            'conditions': weather_data.get('weather', [{}])[0].get('main', 'N/A'),
            'description': weather_data.get('weather', [{}])[0].get('description', 'N/A'),
        },
        'prediction': {
            'temperature': predicted_temp,
            'timestamp': datetime.now(),
        },
        'raw_features': features_dict,
        'api_response': weather_data
    }
    
    return result


def display_results(result):
    """Display prediction results in formatted output."""
    if result is None:
        logger.error("No results to display")
        return
    
    print("\n" + "=" * 70)
    print("📍 LOCATION INFORMATION")
    print("=" * 70)
    location = result['location']
    print(f"City: {location['name']}")
    print(f"Latitude: {location['lat']}")
    print(f"Longitude: {location['lon']}")
    
    print("\n" + "=" * 70)
    print("🌡️  CURRENT WEATHER CONDITIONS")
    print("=" * 70)
    current = result['current']
    print(f"Temperature:       {current['temperature']:>8.1f}°C")
    print(f"Feels Like:        {current['feels_like']:>8.1f}°C")
    print(f"Humidity:          {current['humidity']:>8}%")
    print(f"Pressure:          {current['pressure']:>8.1f} hPa")
    print(f"Wind Speed:        {current['wind_speed']:>8.1f} km/h")
    print(f"Wind Gust:         {current['wind_gust']:>8.1f} km/h")
    print(f"Wind Direction:    {current['wind_direction']:>8}°")
    print(f"Visibility:        {current['visibility']:>8.1f} km")
    print(f"Conditions:        {current['conditions']:>8}")
    print(f"Description:       {current['description']:>8}")
    
    print("\n" + "=" * 70)
    print("🔮 TEMPERATURE PREDICTION")
    print("=" * 70)
    pred = result['prediction']
    current_temp = result['current']['temperature']
    pred_temp = pred['temperature']
    diff = pred_temp - current_temp
    diff_pct = (diff / abs(current_temp) * 100) if current_temp != 0 else 0
    
    print(f"Current Temperature:    {current_temp:>8.2f}°C")
    print(f"Predicted Temperature:  {pred_temp:>8.2f}°C")
    print(f"Temperature Change:     {diff:+8.2f}°C ({diff_pct:+.1f}%)")
    print(f"Prediction Time:        {pred['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("=" * 70 + "\n")


def save_live_prediction(result):
    """Save live prediction to predictions_log.csv."""
    if result is None:
        return
    
    pred_log = pd.DataFrame([{
        'timestamp': result['timestamp'],
        'observation_time': result['timestamp'],
        'temperature': result['prediction']['temperature'],
        'source': 'live_api',
        'location': result['location']['name']
    }])
    
    log_file = 'predictions_log.csv'
    try:
        existing = pd.read_csv(log_file)
        pred_log = pd.concat([existing, pred_log], ignore_index=True)
    except:
        pass
    
    pred_log.to_csv(log_file, index=False)
    logger.info(f"✓ Prediction saved to {log_file}")


if __name__ == "__main__":
    import sys
    
    # Check for API key argument
    api_key = None
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    
    try:
        result = predict_with_live_data(api_key)
        
        if result:
            display_results(result)
            save_live_prediction(result)
            
            # Also save to JSON for dashboard integration
            with open('latest_live_prediction.json', 'w') as f:
                result_copy = result.copy()
                result_copy['timestamp'] = result_copy['timestamp'].isoformat()
                result_copy['prediction']['timestamp'] = result_copy['prediction']['timestamp'].isoformat()
                json.dump(result_copy, f, indent=2)
            logger.info("✓ Prediction saved to latest_live_prediction.json")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)
