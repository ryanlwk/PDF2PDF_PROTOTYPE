#!/bin/bash
# Quick start script for PDF2PDF prototype

echo "🚀 Starting PDF2PDF Prototype..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "✅ Virtual environment found"
fi

# Activate virtual environment and run
source venv/bin/activate
echo "✅ Dependencies ready"
echo ""
echo "📄 Launching Streamlit app..."
echo "   Access at: http://localhost:8501"
echo ""

streamlit run app.py


