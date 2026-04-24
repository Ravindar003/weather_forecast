"""
AtmoSense Configuration
Central configuration file for all constants, paths, and thresholds.
"""

import os
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# BASE PATHS
# ═══════════════════════════════════════════════════════════
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
SRC_DIR = BASE_DIR / "src"
OUTPUT_DIR = BASE_DIR / "outputs"

# Ensure directories exist
OUTPUT_DIR.mkdir(exist_ok=True)

# ═══════════════════════════════════════════════════════════
# DATA PATHS
# ═══════════════════════════════════════════════════════════
DATA_PATH = str(DATA_DIR / "weather_data.csv")
SETTINGS_PATH = str(BASE_DIR / "settings.json")

# ═══════════════════════════════════════════════════════════
# MODEL PATHS
# ═══════════════════════════════════════════════════════════
TNN_MODEL_PATH = str(MODEL_DIR / "best_tnn_model.pth")
RNN_MODEL_PATH = str(MODEL_DIR / "best_vanilla_rnn.pt")

TNN_SCALER_X = str(MODEL_DIR / "tnn_scaler_X.pkl")
TNN_SCALER_Y = str(MODEL_DIR / "tnn_scaler_y.pkl")
RNN_SCALER_X = str(MODEL_DIR / "scaler_X.pkl")
RNN_SCALER_Y = str(MODEL_DIR / "scaler_y.pkl")

# ═══════════════════════════════════════════════════════════
# MODEL HYPERPARAMETERS
# ═══════════════════════════════════════════════════════════
SEQ_LEN_TNN = 72        # 3 days look-back (72 hours)
SEQ_LEN_RNN = 24        # 1 day look-back (24 hours)
BATCH_SIZE = 256
EPOCHS_TNN = 100
EPOCHS_RNN = 50
PATIENCE = 15

# Train/Val/Test split ratios
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# ═══════════════════════════════════════════════════════════
# FEATURE ENGINEERING
# ═══════════════════════════════════════════════════════════
NUMERIC_FEATURES = [
    "dewptm", "fog", "hail", "heatindexm", "hum",
    "pressurem", "rain", "thunder", "tornado",
    "vism", "wdird", "wgustm", "windchillm", "wspdm"
]

TARGET = "tempm"

# Temperature clipping range
TEMP_MIN = -5      # °C
TEMP_MAX = 50      # °C

# Sentinel values to replace with NaN
SENTINEL_VALUES = [-9999, -9999.0, -999.9, -999]

# ═══════════════════════════════════════════════════════════
# ALERT THRESHOLDS
# ═══════════════════════════════════════════════════════════
ALERT_THRESHOLDS = {
    "tempm": {
        "danger": 40,
        "warning": 35,
        "cold": 5,
    },
    "hum": {
        "danger": 90,
        "warning": 85,
    },
    "wspdm": {
        "danger": 60,
        "warning": 40,
    },
    "wgustm": {
        "danger": 80,
        "warning": 60,
    },
    "vism": {
        "danger": 1,
        "warning": 2,
        "reverse": True,  # Lower is worse
    },
    "pressurem": {
        "danger": 980,
        "warning": 990,
        "reverse": True,  # Lower is worse
    },
    "precipm": {
        "danger": 50,
        "warning": 30,
    },
}

# Binary alerts
BINARY_ALERTS = {
    "tornado": "🌪️ TORNADO DETECTED",
    "thunder": "⚡ Thunderstorm Alert",
    "hail": "❄️ Hail Warning",
    "fog": "🌫️ Fog Advisory",
    "rain": "🌧️ Heavy Rain Alert",
    "snow": "❄️ Snowfall Alert",
}

# ═══════════════════════════════════════════════════════════
# STREAMLIT UI COLORS
# ═══════════════════════════════════════════════════════════
DARK_BG = "#0e1117"
CARD_BG = "#1c2333"
PRIMARY_ACCENT = "#4fa3e0"  # Blue
DANGER_COLOR = "#e05c5c"     # Red
WARNING_COLOR = "#e0a85c"    # Orange
SUCCESS_COLOR = "#5ce08a"    # Green

# ═══════════════════════════════════════════════════════════
# ENSEMBLE PREDICTION WEIGHTS
# ═══════════════════════════════════════════════════════════
TNN_WEIGHT = 0.65
RNN_WEIGHT = 0.35

# ═══════════════════════════════════════════════════════════
# NOTIFICATION SETTINGS (Defaults)
# ═══════════════════════════════════════════════════════════
NTFY_ENDPOINT = "https://ntfy.sh/atmosense-weather"
DEFAULT_NTFY_TOPIC = "atmosense-weather"

# ═══════════════════════════════════════════════════════════
# DATETIME FORMAT
# ═══════════════════════════════════════════════════════════
DATETIME_FORMAT = "%Y%m%d-%H:%M"

# ═══════════════════════════════════════════════════════════
# DEVICE (GPU if available, else CPU)
# ═══════════════════════════════════════════════════════════
DEVICE = "cuda" if __import__("torch").cuda.is_available() else "cpu"
