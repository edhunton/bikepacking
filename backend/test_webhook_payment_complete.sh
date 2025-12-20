#!/bin/bash
# Test script specifically for payment.updated webhook with COMPLETED status
# This simulates a real Square payment completion

NGROK_URL="${NGROK_URL:-https://farah-legislatorial-turgidly.ngrok-free.dev}"
WEBHOOK_URL="$NGROK_URL/api/v1/webhooks/square"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "💳 Testing Payment Completed Webhook"
echo "===================================="
echo ""

# Check required parameters
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: $0 <user_email> [book_id] [payment_id]${NC}"
    echo ""
    echo "Example:"
    echo "  $0 test@example.com 1 payment_abc123"
    echo ""
    echo "This will simulate a Square payment completion for:"
    echo "  • User email: test@example.com (must exist in database)"
    echo "  • Book ID: 1"
    echo "  • Payment ID: payment_abc123 (optional, defaults to random)"
    exit 1
fi

USER_EMAIL="$1"
BOOK_ID="${2:-1}"
PAYMENT_ID="${3:-test_payment_$(date +%s)}"

echo "📝 Test Parameters:"
echo "   User Email: $USER_EMAIL"
echo "   Book ID: $BOOK_ID"
echo "   Payment ID: $PAYMENT_ID"
echo ""

# Check if user exists
echo "1️⃣ Checking if user exists..."
USER_CHECK=$(curl -s "http://localhost:8000/api/v1/users?email=$USER_EMAIL" 2>/dev/null)
if echo "$USER_CHECK" | grep -q "id"; then
    echo -e "   ${GREEN}✅ User found${NC}"
else
    echo -e "   ${RED}❌ User not found: $USER_EMAIL${NC}"
    echo "   Make sure the user exists in the database"
    exit 1
fi
echo ""

# Check if secret is set
if [ -z "$SQUARE_WEBHOOK_SECRET" ]; then
    echo -e "${YELLOW}⚠️  SQUARE_WEBHOOK_SECRET not set${NC}"
    echo "   Webhook will fail signature verification"
    echo "   Set it with: export SQUARE_WEBHOOK_SECRET=your_secret"
    echo ""
fi

# Create payment.updated payload
PAYLOAD=$(cat <<EOF
{
  "type": "payment.updated",
  "event_id": "evt_${PAYMENT_ID}",
  "merchant_id": "test_merchant_123",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "data": {
    "type": "payment",
    "id": "evt_${PAYMENT_ID}",
    "object": {
      "payment": {
        "id": "${PAYMENT_ID}",
        "status": "COMPLETED",
        "buyer_email_address": "${USER_EMAIL}",
        "amount_money": {
          "amount": 999,
          "currency": "GBP"
        },
        "metadata": {
          "book_id": "${BOOK_ID}"
        },
        "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
      }
    }
  }
}
EOF
)

echo "2️⃣ Sending payment.updated webhook..."

# Generate signature if secret is set
if [ -n "$SQUARE_WEBHOOK_SECRET" ]; then
    SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SQUARE_WEBHOOK_SECRET" -binary | base64)
    echo "   Signature: ${SIGNATURE:0:20}..."
    
    RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
        "$WEBHOOK_URL" \
        -X POST \
        -H "Content-Type: application/json" \
        -H "x-square-hmacsha256-signature: $SIGNATURE" \
        -d "$PAYLOAD")
else
    RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
        "$WEBHOOK_URL" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$PAYLOAD")
fi

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')

echo ""
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "   ${GREEN}✅ Webhook processed successfully!${NC}"
    echo "   HTTP Code: $HTTP_CODE"
    echo "   Response: $BODY"
    echo ""
    echo -e "${BLUE}📊 Check the database:${NC}"
    echo "   SELECT * FROM book_purchases WHERE user_id = (SELECT id FROM users WHERE email = '$USER_EMAIL');"
else
    echo -e "   ${RED}❌ Webhook failed${NC}"
    echo "   HTTP Code: $HTTP_CODE"
    echo "   Response: $BODY"
fi

echo ""
echo "===================================="


