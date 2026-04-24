"""
Alert system for weather forecasting.
Handles threshold checks and sends notifications.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from typing import List, Dict
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
import config


def check_alerts(predicted: Dict) -> List[Dict]:
    """
    Check predicted values against alert thresholds.
    
    Args:
        predicted: Dict with predicted weather variables
        
    Returns:
        List of alert dicts with level, variable, value, message, emoji
    """
    alerts = []
    
    # Check numeric thresholds
    for variable, thresholds in config.ALERT_THRESHOLDS.items():
        if variable not in predicted:
            continue
        
        value = predicted[variable]
        
        # Check if reverse threshold (lower is worse)
        reverse = thresholds.get('reverse', False)
        
        # Check danger level
        if 'danger' in thresholds:
            danger_threshold = thresholds['danger']
            is_danger = (value >= danger_threshold) if not reverse else (value <= danger_threshold)
            
            if is_danger:
                alerts.append({
                    'level': 'DANGER',
                    'variable': variable,
                    'value': value,
                    'message': f"🔴 DANGER: {variable} = {value:.1f}",
                    'emoji': '🔴'
                })
                continue
        
        # Check warning level
        if 'warning' in thresholds:
            warning_threshold = thresholds['warning']
            is_warning = (value >= warning_threshold) if not reverse else (value <= warning_threshold)
            
            if is_warning:
                alerts.append({
                    'level': 'WARNING',
                    'variable': variable,
                    'value': value,
                    'message': f"🟠 WARNING: {variable} = {value:.1f}",
                    'emoji': '🟠'
                })
                continue
        
        # Check cold alert for temperature
        if variable == 'tempm' and 'cold' in thresholds:
            if value <= thresholds['cold']:
                alerts.append({
                    'level': 'WARNING',
                    'variable': variable,
                    'value': value,
                    'message': f"🟠 COLD: {variable} = {value:.1f}°C",
                    'emoji': '🟠'
                })
    
    # Check binary alerts
    for binary_var, message in config.BINARY_ALERTS.items():
        if binary_var in predicted and predicted[binary_var]:
            alerts.append({
                'level': 'WARNING' if 'Tornado' not in message else 'DANGER',
                'variable': binary_var,
                'value': 1,
                'message': message,
                'emoji': '🟠' if 'Tornado' not in message else '🔴'
            })
    
    return alerts


def send_email_alert(alerts: List[Dict], recipient: str, sender_email: str = None, 
                    sender_password: str = None) -> bool:
    """
    Send email alert with all detected alerts.
    
    Args:
        alerts: List of alert dicts
        recipient: Email recipient
        sender_email: Gmail address (from settings)
        sender_password: Gmail app password (from settings)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not sender_email or not sender_password:
            print("⚠️ Email credentials not configured. Skipping email alert.")
            return False
        
        # Count danger and warnings
        danger_count = sum(1 for a in alerts if a['level'] == 'DANGER')
        warning_count = sum(1 for a in alerts if a['level'] == 'WARNING')
        
        # Build email
        subject = f"⚠️ AtmoSense Alert — {danger_count} danger, {warning_count} warning"
        
        body = f"""
AtmoSense Weather Alert
{"="*50}

Alert Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

CRITICAL ALERTS: {danger_count}
WARNING ALERTS: {warning_count}

{"="*50}

ALERT DETAILS:
"""
        
        for alert in alerts:
            body += f"\n{alert['emoji']} [{alert['level']}] {alert['variable']}: {alert['value']:.2f}"
            body += f"\n   {alert['message']}\n"
        
        body += f"""
{"="*50}

This is an automated alert from AtmoSense.
Predicted by TNN+RNN Ensemble | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        # Send email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        print(f"✉️ Email alert sent to {recipient}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        return False


def send_push_notification(alerts: List[Dict], topic: str = config.DEFAULT_NTFY_TOPIC) -> bool:
    """
    Send push notification via ntfy.sh.
    
    Args:
        alerts: List of alert dicts
        topic: ntfy.sh topic name
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not alerts:
            return True
        
        # Determine priority
        danger_alerts = [a for a in alerts if a['level'] == 'DANGER']
        priority = "urgent" if danger_alerts else "default"
        
        # Build message
        message = f"⚠️ {len(alerts)} weather alerts detected!"
        tags = "warning,thermometer"
        
        if danger_alerts:
            message = f"🔴 {len(danger_alerts)} CRITICAL weather alerts!"
            tags = "warning,thermometer,red"
        
        # Send notification
        response = requests.post(
            f"{config.NTFY_ENDPOINT}",
            data=message.encode(utf_8),
            headers={
                "Priority": priority,
                "Tags": tags,
                "Title": "AtmoSense Alert"
            },
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"🔔 Push notification sent to {topic}")
            return True
        else:
            print(f"❌ Push notification failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending push notification: {str(e)}")
        return False
