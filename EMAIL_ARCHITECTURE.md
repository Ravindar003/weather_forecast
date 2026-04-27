# 🏗️ Email Services Architecture & Developer Guide

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  Streamlit Dashboard (1.py)                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Prediction Tab │ API Tab │ Alerts │ Email Manager   │  │
│  └──────────────────────────────────────────────────────┘  │
│              │                    │                         │
│              ▼                    ▼                         │
│  ┌─────────────────────┐  ┌──────────────────────┐        │
│  │  Model Predictions  │  │  Email Manager UI    │        │
│  │  (TNN + RNN)        │  │  - Add Subscriber    │        │
│  └─────────────────────┘  │  - Manage List       │        │
│                           │  - Broadcast         │        │
│                           └──────────────────────┘        │
│                                  │                         │
│                                  ▼                         │
│                           ┌──────────────┐               │
│                           │ EmailDatabase│               │
│                           └──────┬───────┘               │
│                                  │                         │
│                                  ▼                         │
│                      ┌──────────────────────┐             │
│                      │ email_subscribers.db │             │
│                      │ (SQLite)             │             │
│                      └──────────────────────┘             │
│                                  │                         │
│                                  ▼                         │
│  ┌─────────────────────────────────────┐                 │
│  │ Gmail SMTP (smtp.gmail.com:465)     │                 │
│  │ SSL/TLS Encrypted                   │                 │
│  └─────────────────────────────────────┘                 │
│                                  │                         │
│                                  ▼                         │
│  ┌─────────────────────────────────────┐                 │
│  │ Recipient Email Inboxes             │                 │
│  │ (Subscribers & Ad-hoc Recipients)   │                 │
│  └─────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. **Streamlit UI Layer** (1.py main())
- Renders 5+ tabs
- Handles user interactions
- Calls backend functions
- Displays email management interface

### 2. **Email Manager Layer** (1.py functions)
- `send_prediction_email()`: Single recipient
- `send_batch_emails()`: All subscribers
- HTML template generation
- Error handling & user feedback

### 3. **Database Layer** (EmailDatabase class)
- `init_db()`: Initialize schema
- `add_subscriber()`: Create/update
- `remove_subscriber()`: Deactivate
- `get_all_subscribers()`: Query
- `update_last_sent()`: Track

### 4. **SMTP Layer** (External)
- Gmail SMTP server
- TLS encryption (port 465)
- Authentication via app password
- Email delivery

### 5. **Configuration Layer** (.env)
- Credentials (email, password)
- SMTP settings (host, port)
- API keys (OpenWeatherMap)

---

## Data Flow

### **Scenario 1: Add Subscriber**

```
User fills form in Streamlit
        │
        ▼
["Add Subscriber" button clicked]
        │
        ▼
[Streamlit calls: db.add_subscriber(email, frequency)]
        │
        ▼
[EmailDatabase.add_subscriber() executes]
        │
        ▼
[SQL: INSERT OR REPLACE INTO email_subscribers ...]
        │
        ▼
[SQLite writes to email_subscribers.db]
        │
        ▼
[Success message displayed in UI]
```

### **Scenario 2: Send Single Email**

```
User enters recipient email & clicks "Send Now"
        │
        ▼
[Streamlit calls: send_prediction_email(email, ...)]
        │
        ▼
[Function retrieves .env credentials]
        │
        ▼
[Generates HTML email from template]
        │
        ▼
[Connects to Gmail SMTP (smtp.gmail.com:465)]
        │
        ▼
[Authenticates with SENDER_EMAIL & SENDER_PASSWORD]
        │
        ▼
[Sends MIME email to recipient]
        │
        ▼
[Returns status dict with success/error]
        │
        ▼
[Streamlit displays result]
```

### **Scenario 3: Broadcast to All**

```
User clicks "🔄 Broadcast to All"
        │
        ▼
[Streamlit calls: send_batch_emails(predictions, api_data)]
        │
        ▼
[Function calls: db.get_all_subscribers()]
        │
        ▼
[Queries SQLite for all subscribed=1 emails]
        │
        ▼
[Returns list: [(email1, freq1, ...), (email2, freq2, ...), ...]]
        │
        ▼
[Loop through each subscriber]
        │  
        ├─▶ [send_prediction_email(email1, ...)]
        │   │
        │   └─▶ [Update db: last_sent = NOW]
        │
        ├─▶ [send_prediction_email(email2, ...)]
        │   │
        │   └─▶ [Update db: last_sent = NOW]
        │
        └─▶ [... repeat for all ...]
        │
        ▼
[Collect results: {total, sent, failed, details}]
        │
        ▼
[Display summary in Streamlit]
```

---

## File Structure

```
weather_forecast/
├── 1.py                          # Main Streamlit app
├── .env                          # Config (SECRETS!)
├── email_subscribers.db          # SQLite database (auto-created)
│
├── SETUP FILES:
├── setup_email.py                # Interactive config wizard
├── setup.bat                     # Windows setup
├── setup.sh                      # Linux/Mac setup
│
├── DOCUMENTATION:
├── EMAIL_SETUP_GUIDE.md          # Step-by-step setup
├── EMAIL_QUICKSTART.md           # Quick reference
├── EMAIL_SERVICES_README.md      # Complete summary
├── EMAIL_API_REFERENCE.md        # Function documentation
└── EMAIL_ARCHITECTURE.md         # This file
```

---

## Code Walkthrough

### EmailDatabase Initialization

```python
# In 1.py, line ~26
class EmailDatabase:
    def __init__(self, db_path='email_subscribers.db'):
        self.db_path = Path(db_path)
        self.init_db()  # Auto-create table
    
    def init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        # Create table if not exists
        c.execute('''CREATE TABLE IF NOT EXISTS email_subscribers (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            subscribed BOOLEAN DEFAULT 1,
            frequency TEXT DEFAULT 'daily',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_sent TIMESTAMP
        )''')
        conn.commit()
        conn.close()
```

### Email Sending Logic

```python
# In 1.py, line ~108
def send_prediction_email(recipient_email, live_data, predictions, api_data):
    try:
        # 1. Load credentials from .env
        sender_email = os.getenv('SENDER_EMAIL')
        sender_password = os.getenv('SENDER_PASSWORD')
        sender_name = os.getenv('SENDER_NAME', 'AtmoSense')
        
        # 2. Create MIME message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"AtmoSense Weather Forecast - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        msg["From"] = f"{sender_name} <{sender_email}>"
        msg["To"] = recipient_email
        
        # 3. Generate HTML body (with predictions, comparison, etc.)
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>🌡️ AtmoSense Weather Forecast</h2>
                <p>Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <h3>✨ Live API Data</h3>
                <table border="1">
                    <tr><td>Temperature</td><td>{live_data['temp']:.1f}°C</td></tr>
                    <tr><td>Humidity</td><td>{live_data['humidity']}%</td></tr>
                    ...
                </table>
                
                <h3>🤖 Model Predictions</h3>
                <table border="1">
                    <tr><td>Temperature</td><td>{predictions['temp']:.1f}°C</td></tr>
                    ...
                </table>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, "html"))
        
        # 4. Connect to Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return {'success': True, 'message': f'✅ Email sent to {recipient_email}'}
        
    except Exception as e:
        return {'success': False, 'message': f'❌ Error: {str(e)}'}
```

---

## Extension Points

### 1. **Add New Notification Channel**

```python
# In 1.py, add new function:
def send_prediction_sms(phone_number, predictions):
    """Send predictions via SMS using Twilio"""
    from twilio.rest import Client
    
    account_sid = os.getenv('TWILIO_SID')
    auth_token = os.getenv('TWILIO_TOKEN')
    client = Client(account_sid, auth_token)
    
    message_text = f"🌡️ Weather: Temp {predictions['temp']}°C, Humidity {predictions['humidity']}%"
    
    client.messages.create(
        from_=os.getenv('TWILIO_PHONE'),
        to=phone_number,
        body=message_text
    )
```

### 2. **Add Email Scheduling**

```python
# Install: pip install APScheduler
import schedule

def scheduled_broadcast():
    """Send predictions every hour"""
    predictions = get_latest_predictions()
    api_data = fetch_live_weather()
    send_batch_emails(predictions, api_data)

schedule.every(1).hours.do(scheduled_broadcast)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 3. **Add Subscriber Frequency Filtering**

```python
def send_batch_emails(predictions, api_data):
    db = EmailDatabase()
    subscribers = db.get_all_subscribers()
    
    current_hour = datetime.now().hour
    
    for email, frequency, created, last_sent in subscribers:
        # Only send if frequency matches current time
        if frequency == 'hourly':
            # Send every hour
            send_prediction_email(email, ...)
        elif frequency == 'daily' and current_hour == 9:
            # Send daily at 9 AM
            send_prediction_email(email, ...)
        elif frequency == 'weekly' and datetime.now().weekday() == 0:
            # Send Mondays
            send_prediction_email(email, ...)
```

### 4. **Add Email Unsubscribe Link**

```python
# In HTML template:
html_body += f"""
<hr>
<p style="font-size: 10px; color: #666;">
    <a href="https://yourdomain.com/unsubscribe?email={email}&token=HASH">
        Unsubscribe from emails
    </a>
</p>
"""
```

---

## Configuration Options

### Email Provider Support

**Gmail (Default)**
```python
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465
```

**Outlook/Hotmail**
```python
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
```

**Yahoo Mail**
```python
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=465
```

**Custom SMTP**
```python
SMTP_SERVER=mail.yourdomain.com
SMTP_PORT=587  # or 465 for TLS
```

---

## Testing & Debugging

### Test Email Function
```python
from dotenv import load_dotenv
load_dotenv()

# Test data
test_live = {'temp': 25, 'humidity': 60, ...}
test_pred = {'temp': 26, 'humidity': 58, ...}
test_api = {'main': {}, 'weather': []}

# Send test email
result = send_prediction_email('your_email@example.com', test_live, test_pred, test_api)
print(result)
```

### Test Database
```python
db = EmailDatabase()
db.add_subscriber('test@example.com', 'daily')
print(db.get_all_subscribers())
print(db.get_subscriber_count())
```

### Debug SMTP Connection
```python
import smtplib

try:
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login('your_email@gmail.com', 'app_password_16_chars')
    print('✅ Connected to Gmail')
    server.quit()
except Exception as e:
    print(f'❌ Error: {e}')
```

---

## Performance Optimization

### 1. **Batch Email Sending**
- Uses single loop instead of nested queries
- Updates `last_sent` in batch after success
- ~2-3 sec per 100 emails

### 2. **Database Connection Pooling**
- Could use `sqlite3.connection` context manager
- Currently: Open/close per function (simple, acceptable)

### 3. **Caching Subscriber List**
```python
# Cache for 1 minute to avoid repeated queries
@lru_cache(maxsize=1)
def get_subscribers_cached():
    return db.get_all_subscribers()
```

---

## Security Best Practices

✅ **Never Hardcode Credentials**
- Always use `.env` file
- Load via `os.getenv()` or `python-dotenv`

✅ **Use App Passwords**
- Not actual Gmail password
- Can be revoked independently
- 16-character length enforced

✅ **SSL/TLS Encryption**
- Port 465 for implicit TLS
- Port 587 for STARTTLS (if needed)

✅ **Validate Email Format**
```python
import re
email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
if not re.match(email_pattern, email):
    raise ValueError("Invalid email format")
```

✅ **Sanitize Inputs**
```python
# Convert to lowercase
email = email.lower().strip()

# Remove whitespace
email = email.replace(' ', '')
```

---

## Troubleshooting Matrix

| Problem | Root Cause | Solution |
|---------|-----------|----------|
| Database locked | Multiple connections | Use context managers |
| Memory leak | Unclosed connections | Always call `conn.close()` |
| Slow queries | No indexes | Add PRIMARY KEY + UNIQUE |
| SMTP timeout | Network issue | Check firewall/VPN |
| Email rejected | Invalid domain | Verify recipient email |
| Credentials failed | Wrong app password | Get new 16-char password |

---

## Monitoring & Logging

### Add Logging

```python
import logging

logging.basicConfig(filename='email_service.log', level=logging.INFO)
logger = logging.getLogger(__name__)

def send_prediction_email(...):
    try:
        logger.info(f"Sending email to {recipient_email}")
        # ... send logic ...
        logger.info(f"Email sent successfully to {recipient_email}")
    except Exception as e:
        logger.error(f"Email failed for {recipient_email}: {e}")
```

### Monitor Subscriber Growth

```python
# Add to dashboard
subscriber_count = db.get_subscriber_count()
st.metric("Active Subscribers", subscriber_count)

# Track over time
subscribers_today = len([s for s in db.get_all_subscribers() 
                        if s[2] == datetime.now().date()])
```

---

## Version Roadmap

### v1.0 (Current) ✅
- ✅ Email database (SQLite)
- ✅ Subscriber management
- ✅ Single & batch sending
- ✅ Gmail SMTP integration
- ✅ Streamlit UI

### v1.1 (Planned)
- 🔄 Email scheduling
- 🔄 Unsubscribe links
- 🔄 Email templates customization
- 🔄 Open rate tracking

### v2.0 (Future)
- 🔄 Multi-channel (SMS, Push)
- 🔄 Email queue & retry
- 🔄 Analytics dashboard
- 🔄 Advanced filtering

---

**Last Updated:** April 27, 2026  
**Documentation Version:** 1.0  
**Maintained By:** AtmoSense Development
