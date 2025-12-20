#!/bin/bash
# Debug script to check webhook endpoint setup

NGROK_URL="${NGROK_URL:-https://farah-legislatorial-turgidly.ngrok-free.dev}"
WEBHOOK_URL="$NGROK_URL/api/v1/webhooks/square"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🔍 Debugging Webhook Endpoint"
echo "=============================="
echo ""

# Test 1: Local server health check
echo "1️⃣ Testing local server health endpoint..."
LOCAL_HEALTH=$(curl -s http://localhost:8000/api/v1/books/health 2>&1)
if [ $? -eq 0 ] && [ -n "$LOCAL_HEALTH" ]; then
    echo -e "   ${GREEN}✅ Local server is running${NC}"
    echo "   Response: $LOCAL_HEALTH"
else
    echo -e "   ${RED}❌ Local server is NOT responding${NC}"
    echo "   Make sure: cd backend && python server.py"
    exit 1
fi
echo ""

# Test 2: Check if webhook endpoint exists locally
echo "2️⃣ Testing webhook endpoint locally..."
LOCAL_WEBHOOK=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
    http://localhost:8000/api/v1/webhooks/square \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"test": true}' 2>&1)

LOCAL_HTTP=$(echo "$LOCAL_WEBHOOK" | grep "HTTP_CODE" | cut -d: -f2)
LOCAL_BODY=$(echo "$LOCAL_WEBHOOK" | sed '/HTTP_CODE/d')

if [ "$LOCAL_HTTP" = "401" ] || [ "$LOCAL_HTTP" = "422" ] || [ "$LOCAL_HTTP" = "400" ]; then
    echo -e "   ${GREEN}✅ Local webhook endpoint exists (HTTP $LOCAL_HTTP - expected)${NC}"
elif [ "$LOCAL_HTTP" = "404" ]; then
    echo -e "   ${RED}❌ Local webhook endpoint returns 404${NC}"
    echo "   The route might not be registered correctly"
    echo "   Response: $LOCAL_BODY"
    echo ""
    echo "   Check:"
    echo "   • Is the webhook router included in server.py?"
    echo "   • Is the route defined correctly?"
else
    echo -e "   ${YELLOW}⚠️  Got HTTP $LOCAL_HTTP${NC}"
    echo "   Response: $LOCAL_BODY"
fi
echo ""

# Test 3: Test ngrok tunnel
echo "3️⃣ Testing ngrok tunnel..."
NGROK_TEST=$(curl -s -o /dev/null -w "%{http_code}" "$NGROK_URL" 2>&1)
if [ "$NGROK_TEST" = "200" ] || [ "$NGROK_TEST" = "403" ] || [ "$NGROK_TEST" = "302" ]; then
    echo -e "   ${GREEN}✅ ngrok tunnel is accessible (HTTP $NGROK_TEST)${NC}"
else
    echo -e "   ${RED}❌ ngrok tunnel not accessible (HTTP $NGROK_TEST)${NC}"
    echo "   Make sure ngrok is running: ngrok http 8000"
    exit 1
fi
echo ""

# Test 4: Test webhook through ngrok
echo "4️⃣ Testing webhook endpoint through ngrok..."
echo "   URL: $WEBHOOK_URL"
echo ""

NGROK_WEBHOOK=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
    "$WEBHOOK_URL" \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"test": true}' 2>&1)

NGROK_HTTP=$(echo "$NGROK_WEBHOOK" | grep "HTTP_CODE" | cut -d: -f2)
NGROK_BODY=$(echo "$NGROK_WEBHOOK" | sed '/HTTP_CODE/d' | head -20)

echo "   HTTP Code: $NGROK_HTTP"
echo "   Response preview: ${NGROK_BODY:0:200}..."
echo ""

if [ "$NGROK_HTTP" = "404" ]; then
    echo -e "   ${RED}❌ 404 Not Found${NC}"
    echo ""
    echo "   Possible issues:"
    echo "   1. Route not registered - check server.py includes webhook router"
    echo "   2. ngrok not forwarding to correct port"
    echo "   3. URL path mismatch"
    echo ""
    echo "   Try these checks:"
    echo "   • Visit http://localhost:4040 to see ngrok request inspector"
    echo "   • Check backend logs for incoming requests"
    echo "   • Verify server.py has: app.include_router(webhooks_router, prefix='/api/v1/webhooks')"
elif [ "$NGROK_HTTP" = "401" ] || [ "$NGROK_HTTP" = "422" ] || [ "$NGROK_HTTP" = "400" ]; then
    echo -e "   ${GREEN}✅ Endpoint is reachable! (HTTP $NGROK_HTTP is expected)${NC}"
elif echo "$NGROK_BODY" | grep -q "ngrok"; then
    echo -e "   ${YELLOW}⚠️  ngrok warning page detected${NC}"
    echo "   Visit the URL in a browser first to bypass"
else
    echo -e "   ${YELLOW}⚠️  Unexpected response${NC}"
fi

echo ""
echo "=============================="
echo "💡 Tips:"
echo "   • Monitor ngrok requests: http://localhost:4040"
echo "   • Check backend server logs for errors"
echo "   • Verify both server and ngrok are running"


