# 🚀 Email Services Quick Start

## Option 1: Automated Setup (Recommended)

### Windows
```bash
setup.bat
```

### Linux/Mac
```bash
chmod +x setup.sh
./setup.sh
```

This will:
1. ✅ Install all dependencies
2. ✅ Run interactive email configuration
3. ✅ Test Gmail connection
4. ✅ Launch the application

## Option 2: Manual Setup

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Email
```bash
python setup_email.py
```

### Step 3: Run Application
```bash
streamlit run 1.py
```

---

## 🎯 What You Can Do Now

### 1. **Send Predictions to Single Email**
- Get real-time weather predictions from OpenWeatherMap API
- Compare with model predictions
- Send detailed report to any email address

### 2. **Manage Subscribers**
- Add email addresses with frequency preference
- View all subscribers
- Remove subscribers
- Database persisted in SQLite

### 3. **Broadcast to All**
- Send predictions to all active subscribers
- Tracks last sent timestamp
- HTML formatted emails with styling

### 4. **Live Weather API**
- Real-time data from OpenWeatherMap
- TNN + RNN ensemble predictions
- Side-by-side comparison

---

## 📋 Verification Checklist

Before running, make sure you have:

- [ ] Python 3.8+ installed
- [ ] Google account with 2-Factor Authentication enabled
- [ ] Gmail app password (16 characters)
- [ ] OpenWeatherMap API key (free account)
- [ ] Internet connection

---

## 🐛 Troubleshooting

### "Module not found: dotenv"
```bash
pip install python-dotenv
```

### "Email Error: Invalid login credentials"
- Verify you're using **app password**, not regular password
- App password must be exactly 16 characters
- No spaces or special characters

### "SMTP Connection refused"
- Check internet connection
- Verify SMTP settings in .env
- Try disabling VPN/firewall temporarily

### Database errors
- Delete `email_subscribers.db` to reset
- Application will recreate on next run

---

## 📊 Database

**Location:** `email_subscribers.db`

**Manage directly:**
```bash
# View all subscribers
sqlite3 email_subscribers.db "SELECT * FROM email_subscribers;"

# Delete subscriber
sqlite3 email_subscribers.db "DELETE FROM email_subscribers WHERE email='test@example.com';"

# Reset database
rm email_subscribers.db
```

---

## 🔐 Security Tips

1. ✅ **Never commit .env** - It's in .gitignore
2. ✅ **Use app passwords** - Not your actual Gmail password
3. ✅ **Enable 2FA** - Required for Gmail app passwords
4. ✅ **Rotate credentials regularly** - Change app passwords monthly
5. ✅ **Audit subscribers** - Review who has access to predictions

---

## 📞 Support

If you encounter issues:

1. Check [EMAIL_SETUP_GUIDE.md](EMAIL_SETUP_GUIDE.md) for detailed instructions
2. Review logs in Streamlit interface
3. Test configuration: `python setup_email.py test`

---

**Version:** 1.0  
**Last Updated:** April 27, 2026
