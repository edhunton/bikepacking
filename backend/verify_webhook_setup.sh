#!/bin/bash
# Comprehensive verification script for webhook setup

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🔍 Verifying Webhook Setup"
echo "=========================="
echo ""

# Check 1: Python import
echo "1️⃣ Checking Python imports..."
if python3 backend/check_routes.py > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ Python imports successful${NC}"
    python3 backend/check_routes.py | grep -A 10 "Webhook routes"
else
    echo -e "   ${RED}❌ Python import failed${NC}"
    python3 backend/check_routes.py 2>&1 | head -20
    exit 1
fi
echo ""

# Check 2: Server running
echo "2️⃣ Checking if server is running..."
if curl -s http://localhost:8000/api/v1/books/health > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ Server is running${NC}"
else
    echo -e "   ${RED}❌ Server is NOT running${NC}"
    echo "   Start it with: cd backend && python server.py"
    exit 1
fi
echo ""

# Check 3: Local webhook endpoint
echo "3️⃣ Testing local webhook endpoint..."
LOCAL_RESPONSE=$(curl -s -w "\nHTTP:%{http_code}" \
    http://localhost:8000/api/v1/webhooks/square \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"test": true}' 2>&1)

LOCAL_HTTP=$(echo "$LOCAL_RESPONSE" | grep "HTTP:" | cut -d: -f2)

if [ "$LOCAL_HTTP" = "401" ]; then
    echo -e "   ${GREEN}✅ Endpoint exists and signature verification works (401 expected)${NC}"
elif [ "$LOCAL_HTTP" = "422" ] || [ "$LOCAL_HTTP" = "400" ]; then
    echo -e "   ${GREEN}✅ Endpoint exists (HTTP $LOCAL_HTTP - validation error expected)${NC}"
elif [ "$LOCAL_HTTP" = "404" ]; then
    echo -e "   ${RED}❌ Endpoint returns 404 - route not registered!${NC}"
    echo "   Response: $(echo "$LOCAL_RESPONSE" | grep -v "HTTP:")"
    echo ""
    echo "   ${YELLOW}💡 Solution: Restart your backend server${NC}"
    echo "   1. Stop the server (Ctrl+C)"
    echo "   2. Start it again: cd backend && python server.py"
    exit 1
else
    echo -e "   ${YELLOW}⚠️  Got HTTP $LOCAL_HTTP${NC}"
    echo "   Response: $(echo "$LOCAL_RESPONSE" | grep -v "HTTP:" | head -5)"
fi
echo ""

# Check 4: ngrok
echo "4️⃣ Checking ngrok..."
if curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ ngrok is running${NC}"
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | \
        python3 -c "
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
    if [ -n "$NGROK_URL" ]; then
        echo "   Public URL: $NGROK_URL"
        echo "   Webhook URL: $NGROK_URL/api/v1/webhooks/square"
    fi
else
    echo -e "   ${RED}❌ ngrok is NOT running${NC}"
    echo "   Start it with: ngrok http 8000"
fi
echo ""

echo "=========================="
echo -e "${GREEN}✅ Setup verification complete!${NC}"


