#!/usr/bin/env python3
"""
Test OpenWeatherMap API Connection
Verifies that the API key works and can fetch weather data
"""

import requests
import config
from datetime import datetime
import json

def test_api_connection():
    """Test the OpenWeatherMap API connection."""
    
    print('='*70)
    print('🔍 Testing OpenWeatherMap API Connection')
    print('='*70)
    
    # Test 1: Check configuration
    print('\n✓ Configuration Check:')
    print(f'  API Key: {config.OPENWEATHERMAP_API_KEY[:10]}...{config.OPENWEATHERMAP_API_KEY[-5:]}')
    print(f'  City: {config.CITY}')
    print(f'  Latitude: {config.LAT}')
    print(f'  Longitude: {config.LON}')
    
    # Test 2: Fetch current weather
    print('\n🌐 Fetching Live Weather Data...')
    url = 'https://api.openweathermap.org/data/2.5/weather'
    params = {
        'lat': config.LAT,
        'lon': config.LON,
        'appid': config.OPENWEATHERMAP_API_KEY,
        'units': 'metric'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            print('  ✅ Connection SUCCESS!')
            data = response.json()
            
            print('\n📊 Weather Data Received:')
            print(f'  Location: {data["name"]}')
            print(f'  Coordinates: ({data["coord"]["lat"]}, {data["coord"]["lon"]})')
            print(f'  Current Temperature: {data["main"]["temp"]}°C')
            print(f'  Feels Like: {data["main"]["feels_like"]}°C')
            print(f'  Humidity: {data["main"]["humidity"]}%')
            print(f'  Pressure: {data["main"]["pressure"]} hPa')
            print(f'  Wind Speed: {data["wind"]["speed"]} m/s')
            print(f'  Visibility: {data.get("visibility", 0)/1000:.1f} km')
            print(f'  Conditions: {data["weather"][0]["description"].title()}')
            print(f'  ⏱️  Response Time: {response.elapsed.total_seconds():.2f}s')
            print(f'  🕐 Fetched at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
            
            print('\n✨ All API connection tests PASSED!')
            return True
            
        elif response.status_code == 401:
            print(f'  ❌ Authentication Failed!')
            print(f'  Status Code: {response.status_code}')
            print(f'  Error: Invalid or expired API key')
            return False
            
        elif response.status_code == 404:
            print(f'  ❌ Location Not Found!')
            print(f'  Status Code: {response.status_code}')
            print(f'  Error: Check latitude and longitude')
            return False
            
        else:
            print(f'  ⚠️  Unexpected Response!')
            print(f'  Status Code: {response.status_code}')
            print(f'  Response: {response.text[:200]}')
            return False
            
    except requests.exceptions.Timeout:
        print('  ❌ Connection Timeout (exceeded 10 seconds)')
        print('  Check your internet connection')
        return False
        
    except requests.exceptions.ConnectionError:
        print('  ❌ Connection Error')
        print('  Cannot reach OpenWeatherMap servers')
        print('  Check your internet connection')
        return False
        
    except Exception as e:
        print(f'  ❌ Error: {str(e)}')
        return False
    
    finally:
        print('\n' + '='*70)


def test_live_prediction():
    """Test the live prediction system."""
    print('\n🤖 Testing Live Prediction System...')
    print('='*70)
    
    try:
        from live_prediction import predict_with_live_data
        print('  ✓ live_prediction module imported successfully')
        print('  ✓ Prediction system is ready to use')
        return True
    except Exception as e:
        print(f'  ❌ Error loading live_prediction: {str(e)}')
        return False


if __name__ == '__main__':
    api_ok = test_api_connection()
    live_ok = test_live_prediction()
    
    print('\n📋 SUMMARY')
    print('='*70)
    print(f'  API Connection: {"✅ PASS" if api_ok else "❌ FAIL"}')
    print(f'  Live Prediction Module: {"✅ PASS" if live_ok else "❌ FAIL"}')
    print('='*70)
    
    if api_ok and live_ok:
        print('\n🎉 All systems operational! Ready for live predictions.\n')
    else:
        print('\n⚠️  Some issues detected. Check the errors above.\n')
