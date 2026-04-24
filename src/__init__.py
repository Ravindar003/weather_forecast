"""
AtmoSense Weather Forecasting System
Package for multi-variable weather prediction and alerting.
"""

__version__ = "1.0.0"
__author__ = "AtmoSense Team"
__description__ = "Temporal Neural Network + Vanilla RNN Ensemble Weather Forecasting"

from . import preprocess

# Optional imports (require TensorFlow)
try:
    from . import train_tnn
    from . import train_rnn
    from . import predict
except ImportError:
    pass

try:
    from . import live_input
except ImportError:
    pass

from . import alert

__all__ = [
    'preprocess',
    'train_tnn',
    'train_rnn',
    'live_input',
    'predict',
    'alert'
]
