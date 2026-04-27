@echo off
REM Quick setup script for AtmoSense Email Services (Windows)

echo.
echo ===================================================
echo.  AtmoSense Weather AI - Quick Setup
echo ===================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python first.
    pause
    exit /b 1
)

echo ✅ Python found

REM Install dependencies
echo.
echo 📦 Installing dependencies...
echo.

pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed

REM Run email setup
echo.
echo 📧 Running email setup...
echo.

python setup_email.py

if errorlevel 1 (
    echo ❌ Setup failed
    pause
    exit /b 1
)

echo.
echo ✅ Setup complete!
echo.
echo 🚀 Starting application...
echo.

REM Run Streamlit app
streamlit run 1.py

pause
