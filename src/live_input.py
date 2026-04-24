"""
Live weather data fetching module.
Retrieves real-time weather data from OpenWeatherMap API and prepares it for inference.
"""

import requests
import numpy as np
import pandas as pd
from datetime import datetime
import logging
from typing import Dict, Tuple, Optional
from pathlib import Path
import sys
import joblib

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def compute_dew_point(temp_c: float, humidity: float) -> float:
    """
    Compute dew point from temperature and humidity.
    Using Magnus formula approximation.
    
    Args:
        temp_c: Temperature in Celsius
        humidity: Relative humidity (0-100)
    
    Returns:
        Dew point in Celsius
    """
    a = 17.27
    b = 237.7
    
    alpha = ((a * temp_c) / (b + temp_c)) + np.log(humidity / 100.0)
    dew_point = (b * alpha) / (a - alpha)
    
    return dew_point


def get_compass_direction(degrees: float) -> str:
    """
    Convert wind direction degrees to compass direction.
    
    Args:
        degrees: Wind direction in degrees (0-360)
    
    Returns:
        Compass direction string (N, NE, E, SE, S, SW, W, NW)
    """
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    index = int((degrees + 11.25) / 22.5) % 16
    return directions[index]


def fetch_live_weather() -> Dict:
    """
    Fetch live weather data from OpenWeatherMap API.
    
    Returns:
        Dictionary with mapped weather data
    
    Raises:
        Exception if API call fails
    """
    try:
        logger.info(f"Fetching live weather for {config.CITY}")
        
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            'lat': config.LAT,
            'lon': config.LON,
            'appid': config.OPENWEATHERMAP_API_KEY,
            'units': 'metric'  # Get temperatures in Celsius
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logger.info("Weather data fetched successfully")
        
        # Extract and map API response to dataset columns
        weather_data = {
            'tempm': data['main']['temp'],
            'hum': data['main']['humidity'],
            'pressurem': data['main']['pressure'],
            'wspdm': data['wind']['speed'] * 3.6,  # Convert m/s to km/h
            'wdird': data['wind']['deg'],
            'wgustm': data['wind'].get('gust', 0) * 3.6,  # Convert m/s to km/h
            'vism': data['visibility'] / 1000,  # Convert m to km
            'heatindexm': data['main']['feels_like'],
            'windchillm': data['main']['feels_like'],
            'precipm': data.get('rain', {}).get('1h', 0.0),
            'dewptm': compute_dew_point(data['main']['temp'], data['main']['humidity']),
            '_conds': data['weather'][0]['description'],
            'datetime_utc': datetime.utcnow(),
        }
        
        # Binary weather conditions
        weather_id = data['weather'][0]['id']
        weather_main = data['weather'][0]['main']
        
        weather_data['fog'] = 1 if 700 <= weather_id < 710 else 0
        weather_data['rain'] = 1 if weather_main == "Rain" else 0
        weather_data['snow'] = 1 if weather_main == "Snow" else 0
        weather_data['thunder'] = 1 if weather_main == "Thunderstorm" else 0
        weather_data['tornado'] = 1 if weather_id == 781 else 0
        weather_data['hail'] = 1 if weather_main == "Hail" else 0
        weather_data['wdire'] = get_compass_direction(data['wind']['deg'])
        
        logger.info("Weather data mapped successfully")
        return weather_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching weather data: {str(e)}")
        raise
    except KeyError as e:
        logger.error(f"Missing key in API response: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in fetch_live_weather: {str(e)}")
        raise


def add_time_features(weather_data: Dict) -> Dict:
    """
    Add engineered time-based features to weather data.
    
    Args:
        weather_data: Dictionary with base weather data
    
    Returns:
        Updated dictionary with time features
    """
    dt = weather_data['datetime_utc']
    hour = dt.hour
    day_of_year = dt.timetuple().tm_yday
    
    weather_data['hour_sin'] = np.sin(2 * np.pi * hour / 24)
    weather_data['hour_cos'] = np.cos(2 * np.pi * hour / 24)
    weather_data['day_sin'] = np.sin(2 * np.pi * day_of_year / 365)
    weather_data['day_cos'] = np.cos(2 * np.pi * day_of_year / 365)
    
    return weather_data


def add_delta_features(weather_data: Dict) -> Dict:
    """
    Add delta features (differences from base temperature).
    
    Args:
        weather_data: Dictionary with weather data
    
    Returns:
        Updated dictionary with delta features
    """
    weather_data['heat_delta'] = weather_data['heatindexm'] - weather_data['tempm']
    weather_data['chill_delta'] = weather_data['windchillm'] - weather_data['tempm']
    
    return weather_data


def create_feature_vector(weather_data: Dict, scaler_path: str = "models/scaler.pkl",
                         historical_data: Optional[np.ndarray] = None) -> np.ndarray:
    """
    Create feature vector ready for model input.
    Handles scaling and sequence padding with lags.
    
    Args:
        weather_data: Dictionary with current weather data
        scaler_path: Path to fitted StandardScaler
        historical_data: Previous sequence data for lags (if available)
    
    Returns:
        Scaled feature array ready for model: (1, 72, n_features)
    """
    try:
        logger.info("Creating feature vector for inference")
        
        # Add time and delta features
        weather_data = add_time_features(weather_data)
        weather_data = add_delta_features(weather_data)
        
        # Create dataframe with current observation
        current_df = pd.DataFrame([weather_data])
        
        # If historical data is available, use it; otherwise pad with current values
        if historical_data is not None and len(historical_data) > 0:
            # Create sequence from historical data + current observation
            sequence_data = np.vstack([historical_data[-(config.LOOK_BACK-1):], 
                                       current_df[config.FEATURE_COLS].values])
        else:
            # Pad with current values if no history available
            current_values = current_df[config.FEATURE_COLS].values
            sequence_data = np.repeat(current_values, config.LOOK_BACK, axis=0)
        
        # Convert to DataFrame for scaling
        sequence_df = pd.DataFrame(sequence_data, columns=config.FEATURE_COLS)
        
        # Load scaler and apply to continuous features only
        scaler = joblib.load(scaler_path)
        continuous_cols = [col for col in config.FEATURE_COLS 
                          if col not in config.BINARY_COLS]
        
        sequence_df[continuous_cols] = scaler.transform(sequence_df[continuous_cols])
        
        # Reshape to (1, lookback, features) for model input
        X = sequence_df[config.FEATURE_COLS].values.reshape(1, config.LOOK_BACK, -1)
        
        logger.info(f"Feature vector created with shape {X.shape}")
        return X
        
    except Exception as e:
        logger.error(f"Error creating feature vector: {str(e)}")
        raise


def prepare_live_input(scaler_path: str = "models/scaler.pkl",
                      historical_data: Optional[np.ndarray] = None) -> Tuple[np.ndarray, Dict]:
    """
    Complete pipeline for preparing live input for inference.
    
    Args:
        scaler_path: Path to fitted StandardScaler
        historical_data: Previous sequence data for context
    
    Returns:
        Tuple of (scaled feature array, raw weather data)
    """
    try:
        logger.info("Starting live input preparation")
        
        # Fetch live weather
        weather_data = fetch_live_weather()
        
        # Create and scale feature vector
        X = create_feature_vector(weather_data, scaler_path, historical_data)
        
        logger.info("Live input prepared successfully")
        return X, weather_data
        
    except Exception as e:
        logger.error(f"Error in live input preparation: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        # Example usage
        X, weather_data = prepare_live_input()
        print(f"Feature shape: {X.shape}")
        print(f"Temperature: {weather_data['tempm']:.1f}°C")
        print(f"Humidity: {weather_data['hum']:.1f}%")
        print(f"Wind Speed: {weather_data['wspdm']:.1f} km/h")
    except Exception as e:
        print(f"Error: {str(e)}")
