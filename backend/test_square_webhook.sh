#!/bin/bash
# Test script for Square webhook endpoint
# This simulates Square webhook requests for local testing

NGROK_URL="${NGROK_URL:-https://farah-legislatorial-turgidly.ngrok-free.dev}"
WEBHOOK_URL="$NGROK_URL/api/v1/webhooks/square"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🧪 Testing Square Webhook Endpoint"
echo "=================================="
echo ""

# Check if ngrok URL is set
if [ -z "$NGROK_URL" ] || [ "$NGROK_URL" = "https://farah-legislatorial-turgidly.ngrok-free.de" ]; then
    echo -e "${YELLOW}⚠️  Using default ngrok URL. Set NGROK_URL env var to use different URL${NC}"
    echo "   Example: NGROK_URL=https://your-url.ngrok-free.de ./test_square_webhook.sh"
    echo ""
fi

# Test 1: Check local server
echo "1️⃣ Checking local backend server..."
if curl -s http://localhost:8000/api/v1/books/health > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ Backend server is running${NC}"
else
    echo -e "   ${RED}❌ Backend server is NOT running on port 8000${NC}"
    echo "   Start it with: cd backend && python server.py"
    exit 1
fi
echo ""

# Test 2: Test webhook endpoint without signature (should fail with 401)
echo "2️⃣ Testing webhook endpoint without signature (should fail)..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
    "$WEBHOOK_URL" \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"type":"test.notification","event_id":"test123"}')

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')

if [ "$HTTP_CODE" = "401" ]; then
    echo -e "   ${GREEN}✅ Signature verification is working (401 as expected)${NC}"
elif [ "$HTTP_CODE" = "422" ] || [ "$HTTP_CODE" = "400" ]; then
    echo -e "   ${YELLOW}⚠️  Got HTTP $HTTP_CODE (endpoint reachable, but validation error)${NC}"
else
    echo -e "   ${RED}❌ Unexpected HTTP $HTTP_CODE${NC}"
fi
echo "   Response: $BODY"
echo ""

# Test 3: Test with signature (requires SECRET)
if [ -z "$SQUARE_WEBHOOK_SECRET" ]; then
    echo "3️⃣ Testing with signature..."
    echo -e "   ${YELLOW}⚠️  SQUARE_WEBHOOK_SECRET not set, skipping signature test${NC}"
    echo "   Set it with: export SQUARE_WEBHOOK_SECRET=your_secret"
    echo ""
else
    echo "3️⃣ Testing webhook endpoint with signature..."
    
    # Create test payload
    PAYLOAD='{"type":"payment.updated","event_id":"test_event_123","merchant_id":"test_merchant","data":{"type":"payment","object":{"payment":{"id":"test_payment_123","status":"COMPLETED","buyer_email_address":"test@example.com","metadata":{"book_id":"1"}}}}}'
    
    # Generate signature (HMAC-SHA256, base64 encoded)
    SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SQUARE_WEBHOOK_SECRET" -binary | base64)
    
    RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
        "$WEBHOOK_URL" \
        -X POST \
        -H "Content-Type: application/json" \
        -H "x-square-hmacsha256-signature: $SIGNATURE" \
        -d "$PAYLOAD")
    
    HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "   ${GREEN}✅ Webhook accepted with valid signature!${NC}"
        echo "   Response: $BODY"
    else
        echo -e "   ${RED}❌ Got HTTP $HTTP_CODE${NC}"
        echo "   Response: $BODY"
    fi
    echo ""
fi

# Test 4: Test notification event (doesn't require signature verification in test mode)
echo "4️⃣ Testing test.notification event..."
TEST_PAYLOAD='{"type":"test.notification","event_id":"test_notification_123","merchant_id":"test_merchant"}'

RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
    "$WEBHOOK_URL" \
    -X POST \
    -H "Content-Type: application/json" \
    -d "$TEST_PAYLOAD")

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')

if echo "$BODY" | grep -q "test" || [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ]; then
    echo -e "   ${GREEN}✅ Endpoint is reachable${NC}"
    echo "   HTTP Code: $HTTP_CODE"
    echo "   Response: $BODY"
else
    echo -e "   ${RED}❌ Unexpected response${NC}"
    echo "   HTTP Code: $HTTP_CODE"
    echo "   Response: $BODY"
fi
echo ""

# Summary
echo "=================================="
echo "📋 Summary:"
echo "   Webhook URL: $WEBHOOK_URL"
echo "   Local server: http://localhost:8000"
echo ""
echo "💡 Tips:"
echo "   • Monitor requests at: http://localhost:4040 (ngrok web interface)"
echo "   • Check backend logs for webhook processing details"
echo "   • Use Square Dashboard to send actual test events"
echo "   • Visit the URL in browser first to bypass ngrok warning page"


