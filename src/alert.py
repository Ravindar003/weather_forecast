"""
Alert and notification module for weather forecasting system.
Checks thresholds and sends email, SMS, and push notifications.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from datetime import datetime
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

try:
    from twilio.rest import Client
except ImportError:
    Client = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_thresholds(predictions: Dict, weather_data: Optional[Dict] = None) -> Dict[str, List]:
    """
    Check predictions and current weather against alert thresholds.
    
    Args:
        predictions: Dictionary with predicted values {variable: value}
        weather_data: Optional dictionary with current weather observations
    
    Returns:
        Dictionary with alerts: {'danger': [...], 'warning': [...]}
    """
    logger.info("Checking thresholds")
    
    alerts = {'danger': [], 'warning': []}
    
    # Use predicted values primarily, fall back to current if available
    values_to_check = predictions.copy()
    if weather_data:
        values_to_check.update(weather_data)
    
    # Check each threshold
    for variable, threshold_config in config.ALERT_THRESHOLDS.items():
        if variable not in values_to_check:
            continue
        
        value = values_to_check[variable]
        reversed_check = threshold_config.get('reversed', False)
        
        # Check danger threshold
        if 'danger' in threshold_config:
            danger_level = threshold_config['danger']
            
            if reversed_check:
                triggered = value < danger_level
            else:
                triggered = value > danger_level
            
            if triggered:
                alerts['danger'].append({
                    'variable': variable,
                    'value': value,
                    'threshold': danger_level,
                    'unit': get_unit_for_variable(variable)
                })
        
        # Check warning threshold (if danger not triggered)
        if 'warning' in threshold_config:
            warning_level = threshold_config['warning']
            
            # Skip if already in danger
            if alerts['danger'] and any(a['variable'] == variable for a in alerts['danger']):
                continue
            
            if reversed_check:
                triggered = value < warning_level
            else:
                triggered = value > warning_level
            
            if triggered:
                alerts['warning'].append({
                    'variable': variable,
                    'value': value,
                    'threshold': warning_level,
                    'unit': get_unit_for_variable(variable)
                })
    
    logger.info(f"Thresholds checked: {len(alerts['danger'])} danger, {len(alerts['warning'])} warning")
    return alerts


def get_unit_for_variable(variable: str) -> str:
    """
    Get measurement unit for a weather variable.
    
    Args:
        variable: Variable name
    
    Returns:
        Unit string
    """
    units = {
        'tempm': '°C',
        'hum': '%',
        'pressurem': 'hPa',
        'wspdm': 'km/h',
        'wgustm': 'km/h',
        'vism': 'km',
        'precipm': 'mm',
        'heatindexm': '°C',
        'windchillm': '°C',
        'dewptm': '°C',
    }
    return units.get(variable, '')


def send_email_alert(alerts: Dict[str, List], predictions: Dict) -> bool:
    """
    Send email notification for triggered alerts.
    
    Args:
        alerts: Dictionary with danger and warning alerts
        predictions: Dictionary with predicted values
    
    Returns:
        True if email sent successfully, False otherwise
    """
    if not config.ENABLE_EMAIL:
        logger.info("Email notifications disabled")
        return False
    
    try:
        logger.info("Preparing email alert")
        
        # Check if there are any alerts
        if not alerts['danger'] and not alerts['warning']:
            logger.info("No alerts to send")
            return False
        
        # Compose email
        sender = config.EMAIL_SENDER
        recipient = config.EMAIL_RECIPIENT
        
        # Determine alert level
        if alerts['danger']:
            subject = f"AtmoSense Alert: DANGER - Multiple Weather Threats"
            alert_level = "DANGER"
        else:
            subject = f"AtmoSense Alert: WARNING - Weather Conditions"
            alert_level = "WARNING"
        
        # Build email body
        body = f"""
AtmoSense Weather Alert System
{'='*60}

Alert Level: {alert_level}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
Location: {config.CITY} ({config.LAT}, {config.LON})

{'='*60}
DANGER ALERTS:
{'='*60}
"""
        
        if alerts['danger']:
            for alert in alerts['danger']:
                body += f"\n⚠️  {alert['variable'].upper()}: {alert['value']:.2f} {alert['unit']}"
                body += f"\n   Threshold: {alert['threshold']} {alert['unit']}"
        else:
            body += "\nNone"
        
        body += f"""

{'='*60}
WARNING ALERTS:
{'='*60}
"""
        
        if alerts['warning']:
            for alert in alerts['warning']:
                body += f"\n⚠️  {alert['variable'].upper()}: {alert['value']:.2f} {alert['unit']}"
                body += f"\n   Threshold: {alert['threshold']} {alert['unit']}"
        else:
            body += "\nNone"
        
        body += f"""

{'='*60}
PREDICTED VALUES (Next Hour):
{'='*60}
"""
        
        for var, value in predictions.items():
            unit = get_unit_for_variable(var)
            body += f"\n{var}: {value:.2f} {unit}"
        
        body += f"""

{'='*60}
This alert was generated by the TNN+RNN ensemble model.
Predicted by: Temporal Neural Network (65%) + Vanilla RNN (35%)

For support, contact: admin@atmosense.local
{'='*60}
"""
        
        # Create MIME message
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        logger.info(f"Connecting to Gmail SMTP server")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10) as server:
            server.login(sender, config.EMAIL_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Email alert sent to {recipient}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        logger.error("Email authentication failed. Check credentials.")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending email: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False


def send_sms_alert(alerts: Dict[str, List]) -> bool:
    """
    Send SMS notification using Twilio.
    
    Args:
        alerts: Dictionary with danger and warning alerts
    
    Returns:
        True if SMS sent successfully, False otherwise
    """
    if not config.ENABLE_SMS:
        logger.info("SMS notifications disabled")
        return False
    
    if Client is None:
        logger.warning("Twilio client not available. Install twilio package.")
        return False
    
    try:
        logger.info("Preparing SMS alert")
        
        # Check if there are any alerts
        if not alerts['danger'] and not alerts['warning']:
            logger.info("No alerts to send")
            return False
        
        # Build compact message (under 160 characters)
        if alerts['danger']:
            alert_vars = [a['variable'][:4].upper() for a in alerts['danger'][:3]]
            message = f"🚨 DANGER: {', '.join(alert_vars)}. Check AtmoSense for details."
        else:
            alert_vars = [a['variable'][:4].upper() for a in alerts['warning'][:3]]
            message = f"⚠️ WARNING: {', '.join(alert_vars)}. Check AtmoSense for details."
        
        # Truncate to 160 characters
        message = message[:160]
        
        logger.info(f"SMS message: {message}")
        
        # Send via Twilio
        client = Client(config.TWILIO_SID, config.TWILIO_TOKEN)
        sms = client.messages.create(
            body=message,
            from_=config.TWILIO_FROM,
            to=config.TWILIO_TO
        )
        
        logger.info(f"SMS sent successfully (SID: {sms.sid})")
        return True
        
    except Exception as e:
        logger.error(f"Error sending SMS: {str(e)}")
        return False


def send_push_notification(alerts: Dict[str, List]) -> bool:
    """
    Send push notification via ntfy.sh.
    
    Args:
        alerts: Dictionary with danger and warning alerts
    
    Returns:
        True if notification sent successfully, False otherwise
    """
    if not config.ENABLE_PUSH:
        logger.info("Push notifications disabled")
        return False
    
    try:
        logger.info("Preparing push notification")
        
        # Check if there are any alerts
        if not alerts['danger'] and not alerts['warning']:
            logger.info("No alerts to send")
            return False
        
        # Determine priority and alert summary
        if alerts['danger']:
            priority = "urgent"
            alert_count = len(alerts['danger'])
            summary = f"{alert_count} DANGER alert{'s' if alert_count > 1 else ''}"
        else:
            priority = "default"
            alert_count = len(alerts['warning'])
            summary = f"{alert_count} WARNING alert{'s' if alert_count > 1 else ''}"
        
        # Prepare notification payload
        headers = {
            'Title': f'AtmoSense: {summary}',
            'Priority': priority,
            'Tags': 'warning,weather,atmosense'
        }
        
        # Build message body
        message_lines = [f"Location: {config.CITY}"]
        message_lines.append(f"Timestamp: {datetime.now().strftime('%H:%M UTC')}")
        
        if alerts['danger']:
            message_lines.append("\nDANGER:")
            for alert in alerts['danger'][:5]:
                message_lines.append(f"  • {alert['variable']}: {alert['value']:.1f} {alert['unit']}")
        
        if alerts['warning']:
            message_lines.append("\nWARNING:")
            for alert in alerts['warning'][:5]:
                message_lines.append(f"  • {alert['variable']}: {alert['value']:.1f} {alert['unit']}")
        
        message = "\n".join(message_lines)
        
        # Send via ntfy.sh
        response = requests.post(
            config.NTFY_URL,
            data=message.encode('utf-8'),
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("Push notification sent successfully")
            return True
        else:
            logger.error(f"Push notification failed: HTTP {response.status_code}")
            return False
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending push notification: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in push notification: {str(e)}")
        return False


def send_alerts(alerts: Dict[str, List], predictions: Dict) -> Dict[str, bool]:
    """
    Send all enabled alert notifications.
    
    Args:
        alerts: Dictionary with danger and warning alerts
        predictions: Dictionary with predicted values
    
    Returns:
        Dictionary with notification status for each channel
    """
    logger.info("Sending alerts through all channels")
    
    status = {
        'email': False,
        'sms': False,
        'push': False
    }
    
    if alerts['danger'] or alerts['warning']:
        status['email'] = send_email_alert(alerts, predictions)
        status['sms'] = send_sms_alert(alerts)
        status['push'] = send_push_notification(alerts)
    else:
        logger.info("No alerts triggered, skipping notifications")
    
    return status


if __name__ == "__main__":
    # Example usage
    test_alerts = {
        'danger': [
            {'variable': 'tempm', 'value': 42, 'threshold': 40, 'unit': '°C'}
        ],
        'warning': [
            {'variable': 'hum', 'value': 87, 'threshold': 85, 'unit': '%'}
        ]
    }
    
    test_predictions = {
        'tempm': 42.5,
        'hum': 87.0,
        'pressurem': 1010.0,
        'wspdm': 35.0,
        'vism': 8.5,
        'precipm': 2.0
    }
    
    print("Testing alert system...")
    status = send_alerts(test_alerts, test_predictions)
    print(f"Notification status: {status}")
