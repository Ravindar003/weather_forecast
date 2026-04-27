#!/usr/bin/env python
"""
Setup script for AtmoSense Email Services
Helps configure Gmail credentials and environment variables
"""

import os
import sys
from pathlib import Path

def setup_email_config():
    """Interactive setup for email configuration"""
    
    print("=" * 60)
    print("🌡️  AtmoSense Email Service Setup")
    print("=" * 60)
    print()
    
    # Check if .env exists
    env_path = Path(".env")
    if env_path.exists():
        print("✅ .env file found")
        response = input("Overwrite existing .env? (y/n): ").strip().lower()
        if response != 'y':
            print("Setup cancelled")
            return
    
    print("\n📧 Gmail Configuration Instructions:")
    print("-" * 60)
    print("1. Go to: https://myaccount.google.com/security")
    print("2. Enable 2-Step Verification (if needed)")
    print("3. Go to 'App passwords'")
    print("4. Select App: Mail, Device: Windows Computer")
    print("5. Copy the 16-character password")
    print("-" * 60)
    print()
    
    # Get Gmail credentials
    sender_email = input("📧 Gmail Address: ").strip()
    sender_password = input("🔑 App Password (16 chars): ").strip()
    sender_name = input("👤 Sender Name [AtmoSense Weather AI]: ").strip() or "AtmoSense Weather AI"
    
    # Get OpenWeatherMap API key
    print("\n🌍 OpenWeatherMap Configuration:")
    print("-" * 60)
    print("1. Go to: https://openweathermap.org/api")
    print("2. Sign up for free")
    print("3. Copy your API key from dashboard")
    print("-" * 60)
    print()
    
    api_key = input("🔑 OpenWeatherMap API Key: ").strip()
    
    # Validate inputs
    if not sender_email or '@' not in sender_email:
        print("❌ Invalid email address")
        return False
    
    if len(sender_password) < 16:
        print("❌ App password must be 16 characters")
        return False
    
    if not api_key:
        print("❌ API key required")
        return False
    
    # Write to .env
    env_content = f"""# ==========================================
# DATABASE CONFIG
# ==========================================
DATABASE_URL='postgresql://postgres.nujhrwxhvprfugbdsrdr:[YOUR-PASSWORD]@aws-1-ap-south-1.pooler.supabase.com:6543/postgres'
NEXT_PUBLIC_SUPABASE_URL='https://nujhrwxhvprfugbdsrdr.supabase.co'
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY='sb_publishable_2UcIl4b5mfgAgoAW60U6Pg_HxDtZzQI'

# ==========================================
# EMAIL CONFIGURATION (Gmail SMTP)
# ==========================================
SENDER_EMAIL={sender_email}
SENDER_PASSWORD={sender_password}
SENDER_NAME={sender_name}

SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465

# ==========================================
# OPENWEATHERMAP API
# ==========================================
OPENWEATHER_API_KEY={api_key}
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("\n✅ Configuration saved to .env")
    print()
    
    # Add to .gitignore
    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        content = gitignore_path.read_text()
        if ".env" not in content:
            with open(".gitignore", "a") as f:
                f.write("\n.env\n")
            print("✅ Added .env to .gitignore")
    else:
        with open(".gitignore", "w") as f:
            f.write(".env\n")
        print("✅ Created .gitignore with .env")
    
    print()
    print("=" * 60)
    print("🎉 Setup Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Run the app: streamlit run 1.py")
    print()
    
    return True

def test_email_config():
    """Test email configuration"""
    from dotenv import load_dotenv
    import smtplib
    
    load_dotenv()
    
    sender_email = os.getenv("SENDER_EMAIL", "").strip()
    sender_password = os.getenv("SENDER_PASSWORD", "").strip()
    
    print("\n🧪 Testing Email Configuration...")
    print("-" * 60)
    
    if not sender_email or sender_email == "your_email@gmail.com":
        print("❌ Email not configured")
        return False
    
    print(f"📧 Email: {sender_email}")
    print(f"🔑 Password: {'*' * len(sender_password)}")
    
    try:
        print("\n🔐 Connecting to Gmail SMTP...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
        print("✅ Gmail authentication successful!")
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Main setup function"""
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_email_config()
    else:
        setup_email_config()

if __name__ == "__main__":
    main()
