#!/bin/bash
# Check ngrok configuration and forwarding

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🔍 Checking ngrok Setup"
echo "======================"
echo ""

# Check if ngrok is running
echo "1️⃣ Checking if ngrok is running..."
if curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ ngrok web interface is accessible${NC}"
else
    echo -e "   ${RED}❌ ngrok is NOT running${NC}"
    echo "   Start it with: ngrok http 8000"
    exit 1
fi
echo ""

# Get ngrok tunnel info
echo "2️⃣ Checking ngrok tunnel configuration..."
TUNNEL_INFO=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null)

if [ -z "$TUNNEL_INFO" ]; then
    echo -e "   ${RED}❌ Could not get tunnel info${NC}"
    exit 1
fi

# Extract tunnel details
PUBLIC_URL=$(echo "$TUNNEL_INFO" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    tunnels = data.get('tunnels', [])
    if not tunnels:
        print('NO_TUNNELS')
    else:
        for tunnel in tunnels:
            if tunnel.get('proto') == 'https':
                config = tunnel.get('config', {})
                addr = config.get('addr', 'unknown')
                print(f\"{tunnel.get('public_url', 'unknown')}|{addr}\")
                break
except Exception as e:
    print(f'ERROR|{e}')
" 2>/dev/null)

if [ -z "$PUBLIC_URL" ] || [ "$PUBLIC_URL" = "NO_TUNNELS" ]; then
    echo -e "   ${RED}❌ No HTTPS tunnels found${NC}"
    echo "   Make sure you started ngrok with: ngrok http 8000"
    exit 1
fi

PUBLIC_URL_ONLY=$(echo "$PUBLIC_URL" | cut -d'|' -f1)
FORWARD_ADDR=$(echo "$PUBLIC_URL" | cut -d'|' -f2)

echo "   Public URL: $PUBLIC_URL_ONLY"
echo "   Forwarding to: $FORWARD_ADDR"
echo ""

# Check if forwarding address matches expected
if [[ "$FORWARD_ADDR" == *"localhost:8000"* ]] || [[ "$FORWARD_ADDR" == *"127.0.0.1:8000"* ]]; then
    echo -e "   ${GREEN}✅ ngrok is forwarding to port 8000${NC}"
else
    echo -e "   ${YELLOW}⚠️  ngrok is forwarding to: $FORWARD_ADDR (expected localhost:8000)${NC}"
    echo "   Make sure your backend is running on port 8000"
fi
echo ""

# Test local server
echo "3️⃣ Testing local server on port 8000..."
if curl -s http://localhost:8000/api/v1/books/health > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ Local server is responding${NC}"
else
    echo -e "   ${RED}❌ Local server is NOT responding on port 8000${NC}"
    echo "   Start it with: cd backend && python server.py"
    exit 1
fi
echo ""

# Test through ngrok
echo "4️⃣ Testing through ngrok..."
if [ -n "$PUBLIC_URL_ONLY" ]; then
    WEBHOOK_URL="$PUBLIC_URL_ONLY/api/v1/webhooks/square"
    echo "   Testing: $WEBHOOK_URL"
    
    NGROK_RESPONSE=$(curl -s -w "\nHTTP:%{http_code}" \
        "$WEBHOOK_URL" \
        -X POST \
        -H "Content-Type: application/json" \
        -d '{"test": true}' 2>&1)
    
    HTTP_CODE=$(echo "$NGROK_RESPONSE" | grep "HTTP:" | cut -d: -f2)
    BODY=$(echo "$NGROK_RESPONSE" | sed '/HTTP:/d' | head -10)
    
    echo ""
    echo "   HTTP Code: $HTTP_CODE"
    
    if echo "$BODY" | grep -q "Invalid signature"; then
        echo -e "   ${GREEN}✅ Webhook endpoint is working! (Invalid signature is expected)${NC}"
    elif echo "$BODY" | grep -q "<!DOCTYPE HTML" || echo "$BODY" | grep -q "<html>"; then
        echo -e "   ${RED}❌ Got HTML response (404) - ngrok not forwarding correctly${NC}"
        echo ""
        echo "   ${YELLOW}Possible issues:${NC}"
        echo "   1. ngrok is forwarding to wrong port/service"
        echo "   2. Backend server not running on port 8000"
        echo "   3. Need to restart ngrok after starting server"
        echo ""
        echo "   ${BLUE}Solution:${NC}"
        echo "   1. Make sure backend is running: cd backend && python server.py"
        echo "   2. Restart ngrok: Stop it (Ctrl+C) then: ngrok http 8000"
        echo "   3. Wait a few seconds for ngrok to establish connection"
    elif [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "422" ]; then
        echo -e "   ${GREEN}✅ Webhook endpoint is working! (HTTP $HTTP_CODE is expected)${NC}"
    else
        echo -e "   ${YELLOW}⚠️  Unexpected response${NC}"
        echo "   Response preview: ${BODY:0:100}"
    fi
fi

echo ""
echo "======================"
echo ""
echo "💡 Tip: Visit http://localhost:4040 to see ngrok's request inspector"
echo "   This shows all requests passing through ngrok in real-time"


