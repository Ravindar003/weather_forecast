"""
Main orchestration module for weather forecasting and alert system.
Runs the complete pipeline end-to-end with scheduling.
"""

import schedule
import time
import logging
from datetime import datetime
from pathlib import Path
import csv
import sys
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
import config
from src.live_input import prepare_live_input
from src.predict import predict_pipeline
from src.alert import check_thresholds, send_alerts

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('atmosense.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class WeatherForecastingSystem:
    """
    Main orchestrator for weather forecasting and alert system.
    """
    
    def __init__(self, models_dir: str = "models", log_file: str = "predictions_log.csv"):
        """
        Initialize forecasting system.
        
        Args:
            models_dir: Directory containing trained models
            log_file: Path to CSV log file for predictions
        """
        self.models_dir = models_dir
        self.log_file = log_file
        self.historical_sequences = []
        
        logger.info("WeatherForecastingSystem initialized")
    
    def initialize_log(self) -> None:
        """
        Initialize predictions log CSV file with headers.
        """
        try:
            log_path = Path(self.log_file)
            
            if not log_path.exists():
                logger.info(f"Creating log file: {self.log_file}")
                
                headers = [
                    'timestamp',
                    'current_temp',
                    'current_humidity',
                    'current_pressure',
                    'predicted_temp',
                    'predicted_humidity',
                    'predicted_pressure',
                    'predicted_wind_speed',
                    'predicted_visibility',
                    'predicted_precipitation',
                    'tnn_temp',
                    'rnn_temp',
                    'danger_alerts',
                    'warning_alerts',
                    'email_sent',
                    'sms_sent',
                    'push_sent'
                ]
                
                with open(log_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                
                logger.info(f"Log file initialized with headers")
        
        except Exception as e:
            logger.error(f"Error initializing log file: {str(e)}")
    
    def log_prediction(self, predictions: dict, alerts: dict,
                      notification_status: dict, weather_data: dict) -> None:
        """
        Log prediction and alert information to CSV.
        
        Args:
            predictions: Dictionary with ensemble, tnn, and rnn predictions
            alerts: Dictionary with triggered alerts
            notification_status: Dictionary with notification sending status
            weather_data: Current weather observations
        """
        try:
            danger_alerts_str = "; ".join([
                f"{a['variable']}={a['value']:.2f}" for a in alerts['danger']
            ]) if alerts['danger'] else "None"
            
            warning_alerts_str = "; ".join([
                f"{a['variable']}={a['value']:.2f}" for a in alerts['warning']
            ]) if alerts['warning'] else "None"
            
            log_row = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'current_temp': round(weather_data.get('tempm', 0), 2),
                'current_humidity': round(weather_data.get('hum', 0), 2),
                'current_pressure': round(weather_data.get('pressurem', 0), 2),
                'predicted_temp': round(predictions['ensemble'].get('tempm', 0), 2),
                'predicted_humidity': round(predictions['ensemble'].get('hum', 0), 2),
                'predicted_pressure': round(predictions['ensemble'].get('pressurem', 0), 2),
                'predicted_wind_speed': round(predictions['ensemble'].get('wspdm', 0), 2),
                'predicted_visibility': round(predictions['ensemble'].get('vism', 0), 2),
                'predicted_precipitation': round(predictions['ensemble'].get('precipm', 0), 2),
                'tnn_temp': round(predictions['tnn'].get('tempm', 0), 2),
                'rnn_temp': round(predictions['rnn'].get('tempm', 0), 2),
                'danger_alerts': danger_alerts_str,
                'warning_alerts': warning_alerts_str,
                'email_sent': notification_status.get('email', False),
                'sms_sent': notification_status.get('sms', False),
                'push_sent': notification_status.get('push', False)
            }
            
            with open(self.log_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=log_row.keys())
                writer.writerow(log_row)
            
            logger.info(f"Prediction logged to {self.log_file}")
        
        except Exception as e:
            logger.error(f"Error logging prediction: {str(e)}")
    
    def run_pipeline(self) -> None:
        """
        Execute the complete forecasting pipeline once.
        """
        try:
            logger.info("="*70)
            logger.info("STARTING FORECASTING PIPELINE")
            logger.info("="*70)
            
            # Step 1: Fetch live weather
            logger.info("Step 1/5: Fetching live weather data")
            try:
                X, weather_data = prepare_live_input(
                    scaler_path=f"{self.models_dir}/scaler.pkl",
                    historical_data=None
                )
                logger.info(f"✓ Current conditions: {weather_data['tempm']:.1f}°C, "
                           f"{weather_data['hum']:.0f}% humidity")
            except Exception as e:
                logger.error(f"✗ Failed to fetch live weather: {str(e)}")
                return
            
            # Step 2: Run predictions
            logger.info("Step 2/5: Running ensemble predictions (TNN + RNN)")
            try:
                predictions = predict_pipeline(
                    X,
                    tnn_path=f"{self.models_dir}/tnn_model.h5",
                    rnn_path=f"{self.models_dir}/rnn_model.h5",
                    scaler_path=f"{self.models_dir}/scaler.pkl"
                )
                logger.info(f"✓ Ensemble forecast:")
                logger.info(f"  Temperature: {predictions['ensemble']['tempm']:.1f}°C "
                           f"(TNN: {predictions['tnn']['tempm']:.1f}°C, "
                           f"RNN: {predictions['rnn']['tempm']:.1f}°C)")
                logger.info(f"  Humidity: {predictions['ensemble']['hum']:.1f}%")
                logger.info(f"  Pressure: {predictions['ensemble']['pressurem']:.1f} hPa")
                logger.info(f"  Wind Speed: {predictions['ensemble']['wspdm']:.1f} km/h")
                logger.info(f"  Visibility: {predictions['ensemble']['vism']:.1f} km")
                logger.info(f"  Precipitation: {predictions['ensemble']['precipm']:.1f} mm")
            except Exception as e:
                logger.error(f"✗ Prediction failed: {str(e)}")
                return
            
            # Step 3: Check thresholds
            logger.info("Step 3/5: Checking alert thresholds")
            try:
                alerts = check_thresholds(predictions['ensemble'], weather_data)
                
                if alerts['danger']:
                    logger.warning(f"✓ DANGER ALERTS: {len(alerts['danger'])} triggered")
                    for alert in alerts['danger']:
                        logger.warning(f"  - {alert['variable']}: {alert['value']:.2f} "
                                     f"{alert['unit']} (threshold: {alert['threshold']})")
                else:
                    logger.info("✓ No danger alerts")
                
                if alerts['warning']:
                    logger.warning(f"✓ WARNING ALERTS: {len(alerts['warning'])} triggered")
                    for alert in alerts['warning']:
                        logger.warning(f"  - {alert['variable']}: {alert['value']:.2f} "
                                     f"{alert['unit']} (threshold: {alert['threshold']})")
                else:
                    logger.info("✓ No warning alerts")
            
            except Exception as e:
                logger.error(f"✗ Threshold check failed: {str(e)}")
                return
            
            # Step 4: Send notifications
            logger.info("Step 4/5: Sending notifications")
            try:
                notification_status = send_alerts(alerts, predictions['ensemble'])
                
                logger.info(f"✓ Email: {'✓ Sent' if notification_status['email'] else '✗ Skipped'}")
                logger.info(f"✓ SMS: {'✓ Sent' if notification_status['sms'] else '✗ Skipped'}")
                logger.info(f"✓ Push: {'✓ Sent' if notification_status['push'] else '✗ Skipped'}")
            
            except Exception as e:
                logger.error(f"✗ Notification sending failed: {str(e)}")
                notification_status = {'email': False, 'sms': False, 'push': False}
            
            # Step 5: Log results
            logger.info("Step 5/5: Logging predictions and alerts")
            try:
                self.log_prediction(predictions, alerts, notification_status, weather_data)
                logger.info("✓ Prediction and alerts logged")
            except Exception as e:
                logger.error(f"✗ Logging failed: {str(e)}")
            
            logger.info("="*70)
            logger.info(f"PIPELINE COMPLETED AT {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
            logger.info("="*70)
            print()  # Blank line for readability
        
        except Exception as e:
            logger.critical(f"Unexpected error in pipeline: {str(e)}")
    
    def schedule_pipeline(self, interval: int = 1, unit: str = "hours") -> None:
        """
        Schedule pipeline to run at regular intervals.
        
        Args:
            interval: Number of time units between runs
            unit: Time unit ('hours', 'minutes', 'seconds')
        """
        logger.info(f"Scheduling pipeline to run every {interval} {unit}")
        
        if unit == "hours":
            schedule.every(interval).hours.do(self.run_pipeline)
        elif unit == "minutes":
            schedule.every(interval).minutes.do(self.run_pipeline)
        elif unit == "seconds":
            schedule.every(interval).seconds.do(self.run_pipeline)
        else:
            raise ValueError(f"Unknown time unit: {unit}")
        
        # Run initial forecast
        logger.info("Running initial forecast...")
        self.run_pipeline()
        
        # Keep scheduler running
        logger.info("Scheduler started. Press Ctrl+C to stop.")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute if a task needs to run
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")


def main() -> None:
    """
    Main entry point for the weather forecasting system.
    """
    logger.info("="*70)
    logger.info("AtmoSense - Weather Forecasting and Alert System")
    logger.info("="*70)
    logger.info(f"Configuration: {config.CITY} ({config.LAT}, {config.LON})")
    logger.info(f"Models: TNN (65%) + Vanilla RNN (35%)")
    logger.info(f"Lookback window: {config.LOOK_BACK} hours")
    logger.info("="*70)
    
    # Initialize system
    system = WeatherForecastingSystem(
        models_dir="models",
        log_file="predictions_log.csv"
    )
    
    # Initialize log file
    system.initialize_log()
    
    # Schedule and run pipeline
    try:
        system.schedule_pipeline(
            interval=config.SCHEDULE_INTERVAL,
            unit=config.SCHEDULE_UNIT
        )
    except KeyboardInterrupt:
        logger.info("\nForecast system shutting down...")
    except Exception as e:
        logger.critical(f"Critical error: {str(e)}")


if __name__ == "__main__":
    main()
