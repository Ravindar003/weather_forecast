# 📧 Email Services API Reference

## EmailDatabase Class

Complete API documentation for the EmailDatabase class used to manage email subscribers.

### Constructor

```python
db = EmailDatabase(db_path='email_subscribers.db')
```

**Parameters:**
- `db_path` (str): Path to SQLite database file. Default: `email_subscribers.db`

**Attributes:**
- `db_path`: Full path to database file
- `db_path` normalized to workspace root

---

## Methods

### `init_db()`

Initialize the email subscribers database table.

**Syntax:**
```python
db.init_db()
```

**Description:**
Creates SQLite table with schema if it doesn't exist:
```sql
CREATE TABLE email_subscribers (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    subscribed BOOLEAN DEFAULT 1,
    frequency TEXT DEFAULT 'daily',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_sent TIMESTAMP
)
```

**Returns:** None

**Example:**
```python
db = EmailDatabase()
db.init_db()  # Table created if not exists
```

---

### `add_subscriber(email, frequency='daily')`

Add a new subscriber or update existing subscription.

**Syntax:**
```python
db.add_subscriber(email, frequency='daily')
```

**Parameters:**
- `email` (str): Email address (converted to lowercase)
- `frequency` (str): Notification frequency
  - `'hourly'`: Every hour
  - `'daily'`: Once per day (default)
  - `'weekly'`: Once per week

**Returns:** None

**Raises:**
- `sqlite3.Error`: Database error

**Example:**
```python
# Add subscriber
db.add_subscriber('user@example.com', 'daily')

# Update frequency
db.add_subscriber('user@example.com', 'hourly')
```

**Notes:**
- Email addresses are automatically lowercased
- Duplicate emails are updated (not rejected)
- New subscribers marked as `subscribed=1` by default

---

### `remove_subscriber(email)`

Unsubscribe an email address (soft delete).

**Syntax:**
```python
db.remove_subscriber(email)
```

**Parameters:**
- `email` (str): Email address to unsubscribe

**Returns:** None

**Raises:**
- `sqlite3.Error`: Database error

**Example:**
```python
db.remove_subscriber('user@example.com')
```

**Notes:**
- Sets `subscribed=0` (soft delete)
- Does not physically remove record
- Allows reactivation if needed

---

### `get_all_subscribers()`

Retrieve all active subscribers.

**Syntax:**
```python
subscribers = db.get_all_subscribers()
```

**Returns:**
- List of tuples: `(email, frequency, created_at, last_sent)`
- Empty list if no active subscribers

**Example:**
```python
subscribers = db.get_all_subscribers()
for email, freq, created, last_sent in subscribers:
    print(f"{email} ({freq}): last sent {last_sent}")
```

**Output:**
```
[
    ('user1@example.com', 'daily', '2024-04-27 10:00:00', '2024-04-27 12:00:00'),
    ('user2@example.com', 'hourly', '2024-04-27 11:00:00', None),
    ('user3@example.com', 'weekly', '2024-04-27 09:00:00', '2024-04-26 14:00:00')
]
```

---

### `get_subscriber_count()`

Get count of active subscribers.

**Syntax:**
```python
count = db.get_subscriber_count()
```

**Returns:**
- Integer: Number of active subscribers

**Example:**
```python
count = db.get_subscriber_count()
print(f"Active subscribers: {count}")  # Output: Active subscribers: 42
```

---

### `update_last_sent(email)`

Update the `last_sent` timestamp for a subscriber.

**Syntax:**
```python
db.update_last_sent(email)
```

**Parameters:**
- `email` (str): Email address to update

**Returns:** None

**Raises:**
- `sqlite3.Error`: Database error

**Example:**
```python
# After sending email
db.update_last_sent('user@example.com')
```

**Notes:**
- Sets `last_sent` to current timestamp
- Used for scheduling logic
- Only updates if subscriber exists and is active

---

## Email Functions

### `send_prediction_email(recipient_email, live_data, predictions, api_data)`

Send weather prediction to a single recipient.

**Syntax:**
```python
send_prediction_email(recipient_email, live_data, predictions, api_data)
```

**Parameters:**
- `recipient_email` (str): Target email address
- `live_data` (dict): Live weather data from API
  - Keys: `temp`, `humidity`, `wind_speed`, `pressure`, `visibility`, `precipitation`
- `predictions` (dict): Model predictions
  - Keys: Same as `live_data`
- `api_data` (dict): OpenWeatherMap API response (for details)

**Returns:** Dict with status
```python
{
    'success': True/False,
    'message': 'Status message',
    'recipient': 'user@example.com'
}
```

**Example:**
```python
live_data = {
    'temp': 25.5,
    'humidity': 65,
    'wind_speed': 12,
    'pressure': 1013,
    'visibility': 10,
    'precipitation': 0
}

predictions = {
    'temp': 26.2,
    'humidity': 60,
    'wind_speed': 14,
    'pressure': 1012,
    'visibility': 9,
    'precipitation': 0.5
}

api_data = {'main': {'feels_like': 25.0}, 'weather': [{'description': 'Sunny'}]}

result = send_prediction_email('user@example.com', live_data, predictions, api_data)
print(result['message'])
```

**Output:**
```python
{
    'success': True,
    'message': '✅ Email sent successfully to user@example.com',
    'recipient': 'user@example.com'
}
```

**Notes:**
- Requires `.env` configuration (SENDER_EMAIL, SENDER_PASSWORD)
- HTML formatted email
- Includes current timestamp
- Includes weather description
- Automatic error handling with user-friendly messages

---

### `send_batch_emails(predictions, api_data)`

Send predictions to all active subscribers.

**Syntax:**
```python
results = send_batch_emails(predictions, api_data)
```

**Parameters:**
- `predictions` (dict): Model predictions (same as above)
- `api_data` (dict): OpenWeatherMap API response

**Returns:** Dict with summary
```python
{
    'total': 42,
    'sent': 40,
    'failed': 2,
    'details': [
        {'email': 'user1@example.com', 'success': True},
        {'email': 'user2@example.com', 'success': False, 'error': 'Invalid email'}
    ]
}
```

**Example:**
```python
predictions = {...}  # Model output
api_data = {...}     # Weather API response

results = send_batch_emails(predictions, api_data)

print(f"Sent: {results['sent']}/{results['total']}")
if results['failed'] > 0:
    for detail in results['details']:
        if not detail['success']:
            print(f"Failed: {detail['email']} - {detail.get('error', 'Unknown')}")
```

**Notes:**
- Fetches all active subscribers from database
- Updates `last_sent` timestamp for each recipient
- Continues on error (doesn't stop on failure)
- Returns detailed results for each recipient
- Ideal for batch processing during scheduled runs

---

## Configuration (.env)

Required environment variables for email services:

```bash
# Gmail SMTP Configuration
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=abcd_efgh_ijkl_mnop    # 16-char app password
SENDER_NAME=AtmoSense Weather AI
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465

# OpenWeatherMap API
OPENWEATHER_API_KEY=your_api_key_here
```

---

## Email Template

HTML email sent to subscribers:

```
Subject: AtmoSense Weather Forecast - [TIMESTAMP]

Body:
┌─────────────────────────────────────────────────────┐
│  🌡️ AtmoSense Weather Forecast                      │
│                                                     │
│  Timestamp: [TIMESTAMP]                            │
│  Weather: [DESCRIPTION]                            │
│                                                     │
│  ✨ Live API Data (OpenWeatherMap)                 │
│  ├─ Temp: [X]°C (feels like [Y]°C)               │
│  ├─ Humidity: [X]%                                │
│  ├─ Wind Speed: [X] km/h                          │
│  ├─ Pressure: [X] hPa                             │
│  ├─ Visibility: [X] km                            │
│  └─ Precipitation: [X] mm                         │
│                                                     │
│  🤖 Model Predictions (Ensemble)                  │
│  ├─ Temperature: [X]°C                            │
│  ├─ Humidity: [X]%                                │
│  ├─ Wind Speed: [X] km/h                          │
│  ├─ Pressure: [X] hPa                             │
│  ├─ Visibility: [X] km                            │
│  └─ Precipitation: [X] mm                         │
│                                                     │
│  📊 Comparison                                      │
│  ├─ Temp Diff: [±X]°C                             │
│  ├─ Humidity Diff: [±X]%                          │
│  └─ (Other metrics...)                            │
│                                                     │
│  To manage your subscription, reply to this email. │
└─────────────────────────────────────────────────────┘
```

---

## Error Handling

### Common Errors & Solutions

**Error:** `sqlite3.IntegrityError: UNIQUE constraint failed`
- **Cause:** Email already exists with same uniqueness constraint
- **Solution:** Use `add_subscriber()` for updates (uses INSERT OR REPLACE)

**Error:** `SMTPAuthenticationError: Invalid login credentials`
- **Cause:** Wrong email or app password
- **Solution:** Verify 16-char app password from Google Account

**Error:** `SMTPNotSupportedError: SMTP AUTH extension not supported`
- **Cause:** SMTP server configuration mismatch
- **Solution:** Verify SMTP_PORT is 465 (TLS) not 587 (STARTTLS)

**Error:** `ConnectionRefusedError: No connection could be made`
- **Cause:** Network or firewall blocking SMTP
- **Solution:** Check internet connection, disable VPN, check firewall

---

## Best Practices

### 1. Always Initialize Database
```python
db = EmailDatabase()
db.init_db()  # Create table on first run
```

### 2. Validate Email Format
```python
import re
if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
    db.add_subscriber(email)
```

### 3. Handle Errors Gracefully
```python
try:
    db.add_subscriber(email)
except sqlite3.Error as e:
    print(f"Database error: {e}")
```

### 4. Use Batch Operations
```python
# Good: Send to all at once
send_batch_emails(predictions, api_data)

# Avoid: Loop sending individual emails
for email in email_list:
    send_prediction_email(email, ...)  # Slower
```

### 5. Track Sent Emails
```python
# Always update timestamp after sending
db.update_last_sent(email)
```

---

## Performance Notes

- **Database:** SQLite (fast for < 10,000 subscribers)
- **Batch Sending:** ~2-3 seconds per 100 emails (network dependent)
- **Query Time:** `get_all_subscribers()` < 100ms for 10,000 rows

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-27 | Initial implementation |

---

**Last Updated:** April 27, 2026  
**Maintained By:** AtmoSense Development Team
