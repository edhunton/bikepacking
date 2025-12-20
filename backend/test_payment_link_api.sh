#!/bin/bash
# Test script for the payment link API endpoint

API_BASE="${API_BASE:-http://localhost:8000}"
BOOK_ID="${1:-1}"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🧪 Testing Payment Link API Endpoint"
echo "====================================="
echo ""

# Check if token is provided
if [ -z "$AUTH_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  AUTH_TOKEN not set${NC}"
    echo ""
    echo "To test with authentication:"
    echo "  1. Log in to get a token:"
    echo "     curl -X POST $API_BASE/api/v1/users/login \\"
    echo "       -H 'Content-Type: application/json' \\"
    echo "       -d '{\"email\":\"user@example.com\",\"password\":\"yourpassword\"}'"
    echo ""
    echo "  2. Set the token:"
    echo "     export AUTH_TOKEN=your_token_here"
    echo ""
    echo "  3. Run this script again:"
    echo "     ./test_payment_link_api.sh $BOOK_ID"
    echo ""
    exit 1
fi

echo "1️⃣ Testing payment link endpoint..."
echo "   Book ID: $BOOK_ID"
echo "   Endpoint: GET $API_BASE/api/v1/books/$BOOK_ID/payment-link"
echo ""

RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
    "$API_BASE/api/v1/books/$BOOK_ID/payment-link" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json")

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')

echo "   HTTP Code: $HTTP_CODE"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "   ${GREEN}✅ Success!${NC}"
    echo ""
    PAYMENT_LINK=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('payment_link', ''))" 2>/dev/null)
    BOOK_TITLE=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('book_title', ''))" 2>/dev/null)
    
    echo "   Response:"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
    echo ""
    
    if [ -n "$PAYMENT_LINK" ]; then
        echo -e "   ${GREEN}🔗 Payment Link:${NC}"
        echo "   $PAYMENT_LINK"
        echo ""
        echo "   You can:"
        echo "   • Open this link in a browser to test Square checkout"
        echo "   • Complete a test payment in Square sandbox"
        echo "   • Check webhook processing after payment"
    fi
elif [ "$HTTP_CODE" = "400" ]; then
    echo -e "   ${YELLOW}⚠️  User already purchased this book${NC}"
    echo "   Response: $BODY"
elif [ "$HTTP_CODE" = "401" ]; then
    echo -e "   ${RED}❌ Unauthorized - invalid token${NC}"
    echo "   Response: $BODY"
elif [ "$HTTP_CODE" = "404" ]; then
    echo -e "   ${RED}❌ Book not found${NC}"
    echo "   Response: $BODY"
elif [ "$HTTP_CODE" = "500" ]; then
    echo -e "   ${RED}❌ Server error${NC}"
    echo "   Response: $BODY"
    echo ""
    echo "   Common issues:"
    echo "   • SQUARE_ACCESS_TOKEN not set"
    echo "   • Square SDK not installed (pip install squareup)"
    echo "   • Square API error"
else
    echo -e "   ${RED}❌ Unexpected response${NC}"
    echo "   Response: $BODY"
fi

echo ""
echo "====================================="


