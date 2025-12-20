#!/bin/bash
# Quick script to help test Square webhook setup

echo "🔍 Checking webhook setup..."
echo ""

# Check if backend server is running
if curl -s http://localhost:8000/api/v1/books/health > /dev/null 2>&1; then
    echo "✅ Backend server is running on port 8000"
else
    echo "❌ Backend server is NOT running on port 8000"
    echo "   Start it with: cd backend && python server.py"
    exit 1
fi

# Check if ngrok is running
if curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
    echo "✅ ngrok is running"
    
    # Get the public URL
    PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for tunnel in data.get('tunnels', []):
        if tunnel.get('proto') == 'https':
            print(tunnel.get('public_url', ''))
            break
except:
    pass
" 2>/dev/null)
    
    if [ -n "$PUBLIC_URL" ]; then
        echo "✅ Public URL: $PUBLIC_URL"
        echo ""
        echo "📋 Webhook URL for Square Dashboard:"
        echo "   $PUBLIC_URL/api/v1/webhooks/square"
        echo ""
    fi
else
    echo "❌ ngrok is NOT running"
    echo "   Start it with: ngrok http 8000"
    exit 1
fi

# Check for webhook secret
if grep -q "SQUARE_WEBHOOK_SIGNATURE_SECRET" backend/.env 2>/dev/null; then
    echo "✅ SQUARE_WEBHOOK_SIGNATURE_SECRET is set in backend/.env"
else
    echo "⚠️  SQUARE_WEBHOOK_SIGNATURE_SECRET not found in backend/.env"
    echo "   Add it after setting up webhook in Square Dashboard"
fi

echo ""
echo "✨ Setup looks good! Next steps:"
echo "   1. Copy the webhook URL above to Square Dashboard"
echo "   2. Get the Webhook Signature Secret from Square"
echo "   3. Add it to backend/.env as SQUARE_WEBHOOK_SIGNATURE_SECRET=..."
echo "   4. Restart your backend server"
echo "   5. Send a test notification from Square Dashboard"


