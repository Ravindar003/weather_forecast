#!/bin/bash
# Quick setup script for AtmoSense Email Services (Linux/Mac)

echo ""
echo "==================================================="
echo ""
echo "  AtmoSense Weather AI - Quick Setup"
echo ""
echo "==================================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python not found. Please install Python first."
    exit 1
fi

echo "✅ Python found"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
echo ""

pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed"

# Run email setup
echo ""
echo "📧 Running email setup..."
echo ""

python3 setup_email.py

if [ $? -ne 0 ]; then
    echo "❌ Setup failed"
    exit 1
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Starting application..."
echo ""

# Run Streamlit app
streamlit run 1.py
