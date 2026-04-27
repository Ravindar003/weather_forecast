#!/usr/bin/env python
"""
Quick test for Gmail SMTP authentication
Helps diagnose email configuration issues
"""

import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("📧 Gmail SMTP Authentication Test")
print("=" * 60)

sender_email = os.getenv("SENDER_EMAIL", "").strip()
sender_password = os.getenv("SENDER_PASSWORD", "").strip()
sender_password = sender_password.replace(" ", "")  # Remove spaces

print(f"\n✓ Email: {sender_email}")
print(f"✓ Password length: {len(sender_password)} chars")
print(f"✓ SMTP: smtp.gmail.com:465")

if not sender_email or sender_email == "your_email@gmail.com":
    print("\n❌ Email not configured in .env")
    exit(1)

if len(sender_password) < 10:
    print("\n❌ Password too short (need 16 chars)")
    exit(1)

print("\n🔐 Testing Gmail SMTP connection...")

try:
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    print("✓ Connected to smtp.gmail.com:465")
    
    server.login(sender_email, sender_password)
    print("✓ Authentication successful!")
    
    server.quit()
    print("\n✅ All checks passed! Email should work now.")
    print("\nIf you're still getting errors:")
    print("1. Make sure 2-Step Verification is enabled on Gmail")
    print("2. Re-generate a new app password")
    print("3. Copy WITHOUT spaces (remove 'abcd efgh ijkl mnop' → 'abcdefghijklmnop')")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"\n❌ Authentication Failed: {e}")
    print("\nFix: Get a new app password:")
    print("1. Go to https://myaccount.google.com/security")
    print("2. Enable 2-Step Verification (if needed)")
    print("3. Generate 'App passwords' → Mail + Windows")
    print("4. Copy 16-char password (remove spaces)")
    print("5. Update .env SENDER_PASSWORD")
    
except smtplib.SMTPException as e:
    print(f"\n❌ SMTP Error: {e}")
    print("\nCheck:")
    print("- Internet connection active")
    print("- SMTP_SERVER=smtp.gmail.com")
    print("- SMTP_PORT=465")
    
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 60)
