#!/bin/bash
# Test if the webhook endpoint is reachable

NGROK_URL="https://farah-legislatorial-turgidly.ngrok-free.dev"

echo "🧪 Testing webhook endpoint..."
echo ""
echo "Testing: $NGROK_URL/api/v1/webhooks/square"
echo ""

# Test 1: Check if ngrok tunnel is up
echo "1️⃣ Checking ngrok tunnel..."
if curl -s "$NGROK_URL" > /dev/null 2>&1; then
    echo "   ✅ ngrok tunnel is accessible"
else
    echo "   ❌ ngrok tunnel is NOT accessible"
    echo "      Make sure ngrok is running: ngrok http 8000"
    exit 1
fi

# Test 2: Check if backend server is responding
echo ""
echo "2️⃣ Checking local backend server..."
if curl -s http://localhost:8000/api/v1/books/health > /dev/null 2>&1; then
    echo "   ✅ Backend server is running on port 8000"
else
    echo "   ❌ Backend server is NOT running on port 8000"
    echo "      Start it with: cd backend && python server.py"
    exit 1
fi

# Test 3: Try to reach the webhook endpoint through ngrok
echo ""
echo "3️⃣ Testing webhook endpoint through ngrok..."
echo "   (Note: ngrok free tier may show a warning page on first visit)"
echo ""

RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$NGROK_URL/api/v1/webhooks/square" -X POST -H "Content-Type: application/json" -d '{"test": true}' 2>&1)
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')

if [ "$HTTP_CODE" = "422" ] || [ "$HTTP_CODE" = "400" ] || [ "$HTTP_CODE" = "401" ]; then
    echo "   ✅ Webhook endpoint is reachable! (Got HTTP $HTTP_CODE - expected for invalid request)"
    echo "   📝 Response: $BODY"
elif [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Webhook endpoint is reachable and responding!"
    echo "   📝 Response: $BODY"
else
    echo "   ⚠️  Got HTTP $HTTP_CODE"
    echo "   📝 Response: $BODY"
    echo ""
    echo "   ℹ️  If you see HTML about 'ngrok browser warning', visit the URL in a browser first"
fi

echo ""
echo "✨ Next steps:"
echo "   1. Copy this URL to Square Dashboard:"
echo "      $NGROK_URL/api/v1/webhooks/square"
echo "   2. If you see the ngrok warning page, visit the URL in a browser once"
echo "   3. Send a test notification from Square Dashboard"
echo "   4. Check your server logs and ngrok web interface (http://localhost:4040)"


