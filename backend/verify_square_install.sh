#!/bin/bash
# Verify Square SDK installation

echo "🔍 Checking Square SDK Installation"
echo "===================================="
echo ""

cd backend

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo "✅ Virtual environment found: .venv"
    echo "   Testing in virtual environment..."
    .venv/bin/python3 -c "from square.client import Client; print('✅ Square SDK installed in .venv')" 2>&1 || echo "❌ Square SDK NOT in .venv"
elif [ -d "venv" ]; then
    echo "✅ Virtual environment found: venv"
    echo "   Testing in virtual environment..."
    venv/bin/python3 -c "from square.client import Client; print('✅ Square SDK installed in venv')" 2>&1 || echo "❌ Square SDK NOT in venv"
else
    echo "⚠️  No virtual environment found"
fi

echo ""

# Check system Python
echo "Checking system Python..."
python3 -c "from square.client import Client; print('✅ Square SDK installed in system Python')" 2>&1 || echo "❌ Square SDK NOT in system Python"

echo ""
echo "💡 If SDK is missing, install it:"
echo "   • With venv: source .venv/bin/activate && pip install squareup"
echo "   • Or: cd backend && pip install squareup"
echo ""
echo "⚠️  Make sure you restart your backend server after installing!"


