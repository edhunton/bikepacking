#!/bin/bash
# Debug script to check payment link endpoint issues

API_BASE="${API_BASE:-http://localhost:8000}"
BOOK_ID="${1:-1}"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔍 Debugging Payment Link Endpoint"
echo "==================================="
echo ""

# Check 1: Server health
echo "1️⃣ Checking server health..."
if curl -s http://localhost:8000/api/v1/books/health > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ Server is running${NC}"
else
    echo -e "   ${RED}❌ Server is NOT running${NC}"
    exit 1
fi
echo ""

# Check 2: Python imports
echo "2️⃣ Checking Python imports..."
cd backend
if python3 -c "from api.v1.books.payment_links import create_payment_link_for_user; print('✅ Payment links module imports OK')" 2>&1; then
    echo -e "   ${GREEN}✅ Payment links module imports successfully${NC}"
else
    ERROR=$(python3 -c "from api.v1.books.payment_links import create_payment_link_for_user" 2>&1)
    echo -e "   ${RED}❌ Import failed${NC}"
    echo "   Error: $ERROR"
    echo ""
    if echo "$ERROR" | grep -q "squareup\|square.client"; then
        echo "   ${YELLOW}💡 Solution: Install squareup${NC}"
        echo "   pip install squareup"
    fi
fi
echo ""

# Check 3: Square SDK installation
echo "3️⃣ Checking Square SDK..."
if python3 -c "from square.client import Client; print('✅ Square SDK installed')" 2>&1; then
    echo -e "   ${GREEN}✅ Square SDK is installed${NC}"
else
    echo -e "   ${RED}❌ Square SDK NOT installed${NC}"
    echo "   Install with: pip install squareup"
fi
echo ""

# Check 4: Environment variables
echo "4️⃣ Checking environment variables..."
cd ..
if grep -q "SQUARE_ACCESS_TOKEN" backend/.env 2>/dev/null; then
    echo -e "   ${GREEN}✅ SQUARE_ACCESS_TOKEN found in .env${NC}"
else
    echo -e "   ${YELLOW}⚠️  SQUARE_ACCESS_TOKEN not found in .env${NC}"
    echo "   Add it: SQUARE_ACCESS_TOKEN=your_token_here"
fi

if grep -q "SQUARE_ENVIRONMENT" backend/.env 2>/dev/null; then
    ENV_VAL=$(grep "SQUARE_ENVIRONMENT" backend/.env | cut -d= -f2)
    echo -e "   ${GREEN}✅ SQUARE_ENVIRONMENT found: $ENV_VAL${NC}"
else
    echo -e "   ${YELLOW}⚠️  SQUARE_ENVIRONMENT not found (will default to 'sandbox')${NC}"
fi
echo ""

# Check 5: Test endpoint with token (if provided)
if [ -n "$AUTH_TOKEN" ]; then
    echo "5️⃣ Testing endpoint..."
    RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
        "$API_BASE/api/v1/books/$BOOK_ID/payment-link" \
        -H "Authorization: Bearer $AUTH_TOKEN" \
        -H "Content-Type: application/json")
    
    HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')
    
    echo "   HTTP Code: $HTTP_CODE"
    if [ "$HTTP_CODE" = "500" ]; then
        echo -e "   ${RED}❌ 500 Internal Server Error${NC}"
        echo "   Response:"
        echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
        echo ""
        echo "   Common causes:"
        echo "   • SQUARE_ACCESS_TOKEN not set or invalid"
        echo "   • Square SDK not installed"
        echo "   • No Square locations configured"
        echo "   • Square API error"
    fi
fi

echo ""
echo "==================================="
echo "💡 Next steps:"
echo "   1. Check backend server logs for detailed error"
echo "   2. Ensure SQUARE_ACCESS_TOKEN is set in .env"
echo "   3. Install Square SDK: pip install squareup"
echo "   4. Verify Square location is configured in Square Dashboard"


