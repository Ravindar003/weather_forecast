"""
Test script to verify the weather forecasting system setup.
Run this to check if all components are working correctly.
"""

import sys
from pathlib import Path
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test if all required packages are installed."""
    print("="*70)
    print("Testing Package Imports")
    print("="*70)
    
    packages = {
        'tensorflow': 'TensorFlow',
        'keras': 'Keras',
        'numpy': 'NumPy',
        'pandas': 'Pandas',
        'sklearn': 'Scikit-learn',
        'joblib': 'Joblib',
        'requests': 'Requests',
        'schedule': 'Schedule',
        'matplotlib': 'Matplotlib',
        'seaborn': 'Seaborn',
    }
    
    failed = []
    for package, name in packages.items():
        try:
            __import__(package)
            print(f"✓ {name:20} - OK")
        except ImportError:
            print(f"✗ {name:20} - MISSING")
            failed.append(name)
    
    if failed:
        print(f"\n⚠️  Missing packages: {', '.join(failed)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    print("\n✓ All imports successful!")
    return True


def test_config():
    """Test configuration file."""
    print("\n" + "="*70)
    print("Testing Configuration")
    print("="*70)
    
    try:
        import config
        
        # Check critical config values
        checks = {
            'OPENWEATHERMAP_API_KEY': config.OPENWEATHERMAP_API_KEY,
            'CITY': config.CITY,
            'LAT': config.LAT,
            'LON': config.LON,
            'LOOK_BACK': config.LOOK_BACK,
            'FEATURE_COLS': config.FEATURE_COLS,
            'TARGET_COLS': config.TARGET_COLS,
            'ALERT_THRESHOLDS': config.ALERT_THRESHOLDS,
        }
        
        for name, value in checks.items():
            if value:
                print(f"✓ {name:25} - Configured")
            else:
                print(f"⚠️  {name:25} - Empty or None")
        
        print(f"\n✓ Config loaded successfully!")
        print(f"  Location: {config.CITY} ({config.LAT}, {config.LON})")
        print(f"  Features: {len(config.FEATURE_COLS)} input features")
        print(f"  Targets: {len(config.TARGET_COLS)} output targets")
        print(f"  Lookback: {config.LOOK_BACK} hours")
        
        return True
    except Exception as e:
        print(f"✗ Config error: {str(e)}")
        return False


def test_preprocessing():
    """Test preprocessing pipeline."""
    print("\n" + "="*70)
    print("Testing Data Preprocessing")
    print("="*70)
    
    try:
        from src.preprocess import (
            load_and_clean_data,
            engineer_time_features,
            engineer_delta_features,
            engineer_lag_features,
            create_sequences,
            train_test_split_time_series
        )
        import config
        
        csv_path = "data/weather_data.csv"
        
        if not Path(csv_path).exists():
            print(f"⚠️  Data file not found: {csv_path}")
            return False
        
        print(f"Loading data from {csv_path}")
        df = load_and_clean_data(csv_path)
        print(f"✓ Data loaded: {df.shape[0]} rows, {df.shape[1]} columns")
        
        print("✓ Adding time features...")
        df = engineer_time_features(df)
        
        print("✓ Adding delta features...")
        df = engineer_delta_features(df)
        
        print("✓ Adding lag features...")
        df = engineer_lag_features(df)
        
        print("✓ Creating sequences...")
        X, y = create_sequences(df, config.TARGET_COLS, config.LOOK_BACK)
        print(f"✓ Sequences created: X shape {X.shape}, y shape {y.shape}")
        
        print("✓ Splitting train/test...")
        X_train, X_test, y_train, y_test = train_test_split_time_series(X, y, 0.8)
        print(f"✓ Train: {X_train.shape}, Test: {X_test.shape}")
        
        return True
    except Exception as e:
        print(f"✗ Preprocessing error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_models():
    """Test model loading."""
    print("\n" + "="*70)
    print("Testing Model Files")
    print("="*70)
    
    models_dir = Path("models")
    files = {
        'TNN Model': models_dir / "tnn_model.h5",
        'RNN Model': models_dir / "rnn_model.h5",
        'Scaler': models_dir / "scaler.pkl",
    }
    
    missing = []
    for name, path in files.items():
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            print(f"✓ {name:20} - Found ({size_mb:.1f} MB)")
        else:
            print(f"⚠️  {name:20} - Not found")
            missing.append(name)
    
    if missing:
        print(f"\n⚠️  Missing model files: {', '.join(missing)}")
        print("Run: python src/train_tnn.py && python src/train_rnn.py")
        return False
    
    return True


def test_live_input():
    """Test live input module."""
    print("\n" + "="*70)
    print("Testing Live Input Module")
    print("="*70)
    
    try:
        from src.live_input import (
            compute_dew_point,
            get_compass_direction,
            add_time_features,
            create_feature_vector
        )
        
        print("✓ Testing dew point computation...")
        dp = compute_dew_point(25, 65)
        print(f"  Dew point at 25°C, 65% humidity: {dp:.1f}°C")
        
        print("✓ Testing compass direction...")
        direction = get_compass_direction(135)
        print(f"  Direction at 135°: {direction}")
        
        print("✓ Testing time features...")
        from datetime import datetime
        test_data = {
            'datetime_utc': datetime.now(),
            'tempm': 25.0,
            'hum': 65.0
        }
        test_data = add_time_features(test_data)
        print(f"  Hour sin/cos added: {test_data.get('hour_sin', 'N/A'):.2f}")
        
        print("\n✓ Live input module working!")
        return True
    except Exception as e:
        print(f"✗ Live input error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_alerts():
    """Test alert threshold checking."""
    print("\n" + "="*70)
    print("Testing Alert System")
    print("="*70)
    
    try:
        from src.alert import check_thresholds, get_unit_for_variable
        
        # Test predictions that trigger alerts
        test_predictions = {
            'tempm': 42.0,  # Danger: > 40
            'hum': 87.0,    # Warning: > 85
            'wspdm': 50.0,  # Normal
            'vism': 0.5,    # Danger: < 1 (reversed)
        }
        
        print("Testing threshold checks with:")
        for var, val in test_predictions.items():
            unit = get_unit_for_variable(var)
            print(f"  {var}: {val} {unit}")
        
        alerts = check_thresholds(test_predictions)
        
        print(f"\n✓ Danger alerts: {len(alerts['danger'])}")
        for alert in alerts['danger']:
            print(f"  - {alert['variable']}: {alert['value']} {alert['unit']} (threshold: {alert['threshold']})")
        
        print(f"\n✓ Warning alerts: {len(alerts['warning'])}")
        for alert in alerts['warning']:
            print(f"  - {alert['variable']}: {alert['value']} {alert['unit']} (threshold: {alert['threshold']})")
        
        return True
    except Exception as e:
        print(f"✗ Alert system error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_directory_structure():
    """Test if all required directories exist."""
    print("\n" + "="*70)
    print("Testing Directory Structure")
    print("="*70)
    
    directories = {
        'data': Path("data"),
        'models': Path("models"),
        'src': Path("src"),
    }
    
    files = {
        'config.py': Path("config.py"),
        'main.py': Path("main.py"),
        'requirements.txt': Path("requirements.txt"),
        'README.md': Path("README.md"),
    }
    
    all_ok = True
    
    for name, path in directories.items():
        if path.exists() and path.is_dir():
            print(f"✓ Directory: {name}")
        else:
            print(f"✗ Directory missing: {name}")
            all_ok = False
    
    for name, path in files.items():
        if path.exists():
            print(f"✓ File: {name}")
        else:
            print(f"✗ File missing: {name}")
            all_ok = False
    
    return all_ok


def main():
    """Run all tests."""
    print("\n")
    print("█" * 70)
    print("AtmoSense - System Verification Test".center(70))
    print("█" * 70)
    
    results = {}
    
    # Run tests
    results['Imports'] = test_imports()
    results['Directory Structure'] = test_directory_structure()
    results['Configuration'] = test_config()
    results['Data Preprocessing'] = test_preprocessing()
    results['Model Files'] = test_models()
    results['Live Input'] = test_live_input()
    results['Alert System'] = test_alerts()
    
    # Summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:30} {status}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print("="*70)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All systems operational! Ready to run forecasts.")
        print("\n  To train models:")
        print("    python src/train_tnn.py")
        print("    python src/train_rnn.py")
        print("\n  To run forecasts:")
        print("    python main.py")
        return 0
    else:
        print("\n⚠️  Some tests failed. See above for details.")
        print("\n  Common fixes:")
        print("    1. pip install -r requirements.txt")
        print("    2. Check config.py has valid API keys")
        print("    3. Run: python src/train_tnn.py && python src/train_rnn.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())
