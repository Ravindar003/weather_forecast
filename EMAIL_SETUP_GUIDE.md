# 📧 Email Service Setup Guide

## Step 1: Install Required Package

```bash
pip install python-dotenv
```

## Step 2: Get Google App Password

### For Gmail Users (Recommended):

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** (if not already enabled)
3. Go to **App passwords**
4. Select:
   - **App:** Mail
   - **Device:** Windows Computer (or your OS)
5. Google will generate a **16-character app password**
6. Copy this password

### Example:
```
Original Email: your_email@gmail.com
App Password:   abcd efgh ijkl mnop
```

## Step 3: Configure .env File

Edit `.env` file in the project root:

```bash
# ==========================================
# EMAIL CONFIGURATION (Gmail SMTP)
# ==========================================
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=abcdefghijklmnop
SENDER_NAME=AtmoSense Weather AI

SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465

# ==========================================
# OPENWEATHERMAP API
# ==========================================
OPENWEATHER_API_KEY=your_api_key_here
```

**⚠️ Security Note:** Never commit `.env` to version control. Add it to `.gitignore`:

```bash
echo ".env" >> .gitignore
```

## Step 4: Test Email Service

Run this test script:

```bash
python -c "
import os
from dotenv import load_dotenv

load_dotenv()

sender_email = os.getenv('SENDER_EMAIL')
sender_password = os.getenv('SENDER_PASSWORD')

if sender_email and sender_email != 'your_email@gmail.com':
    print('✅ Email configured:', sender_email)
else:
    print('❌ Email not configured')
"
```

## Step 5: Run the App

```bash
streamlit run 1.py
```

## Features

### Single Email Send
- Type recipient email in sidebar
- Click "Send Now" button
- Report sent immediately

### Subscriber Management
- **Add Subscriber:** Add email with frequency preference (hourly, daily, weekly)
- **View All:** See all active subscribers
- **Unsubscribe:** Remove subscribers from list

### Broadcast
- Click "🔄 Broadcast to All" to send current predictions to all subscribers
- Stores sent timestamp in database

## Database Location

Email subscribers stored in: `email_subscribers.db` (SQLite)

### Database Schema

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

## Troubleshooting

### "Email Error: Invalid login credentials"
- ✅ Check SENDER_PASSWORD is 16 characters (app password, not regular password)
- ✅ Verify SENDER_EMAIL is correct
- ✅ 2-Step Verification is enabled on Gmail account

### "Email Error: [Errno 11001] getaddrinfo failed"
- ✅ Check internet connection
- ✅ Verify SMTP_SERVER: `smtp.gmail.com`
- ✅ Verify SMTP_PORT: `465`

### Emails not received
- ✅ Check spam folder
- ✅ Verify recipient email is valid
- ✅ Check subscriber is marked as `subscribed = 1`

## Advanced: Alternative Email Providers

### Outlook/Hotmail
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
```

### Yahoo Mail
```bash
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=465
SENDER_PASSWORD=generated_app_password
```

### Custom SMTP
Update SMTP_SERVER and SMTP_PORT in `.env`

---

**Last Updated:** April 27, 2026
