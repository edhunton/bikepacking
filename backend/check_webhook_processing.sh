#!/bin/bash
# Check if webhook is processing and what database changes are happening

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🔍 Checking Webhook Processing & Database Changes"
echo "=================================================="
echo ""

# Check server logs suggestion
echo "1️⃣ Check your backend server logs:"
echo -e "   ${BLUE}Look for lines like:${NC}"
echo "   • 'Processed Square webhook event...'"
echo "   • 'Created purchase for user X, book Y, payment Z'"
echo "   • Any error messages"
echo ""

# Check database
echo "2️⃣ Checking database for recent purchases..."
echo ""
echo "   Recent purchases (last 10):"
echo "   ----------------------------"
psql $DATABASE_URL -c "
SELECT 
    bp.id,
    bp.user_id,
    u.email,
    bp.book_id,
    b.title,
    bp.payment_id,
    bp.payment_provider,
    bp.payment_amount,
    bp.payment_currency,
    bp.purchased_at,
    bp.access_key IS NOT NULL as has_access_key
FROM book_purchases bp
LEFT JOIN users u ON bp.user_id = u.id
LEFT JOIN books b ON bp.book_id = b.id
ORDER BY bp.purchased_at DESC
LIMIT 10;
" 2>/dev/null || echo -e "   ${YELLOW}⚠️  Could not connect to database${NC}"
echo ""

# Check for Square payments specifically
echo "3️⃣ Square payments specifically:"
echo "   ----------------------------"
psql $DATABASE_URL -c "
SELECT 
    bp.payment_id,
    bp.user_id,
    u.email,
    bp.book_id,
    b.title,
    bp.payment_amount,
    bp.payment_currency,
    bp.purchased_at
FROM book_purchases bp
LEFT JOIN users u ON bp.user_id = u.id
LEFT JOIN books b ON bp.book_id = b.id
WHERE bp.payment_provider = 'square'
ORDER BY bp.purchased_at DESC
LIMIT 10;
" 2>/dev/null || echo -e "   ${YELLOW}⚠️  Could not connect to database${NC}"
echo ""

echo "=================================================="
echo ""
echo "💡 What happens when payment.updated is received:"
echo ""
echo "   1. Webhook received → /api/v1/webhooks/square"
echo "   2. Signature verified (if SQUARE_WEBHOOK_SECRET is set)"
echo "   3. Event type checked → 'payment.updated'"
echo "   4. Payment status checked → must be 'COMPLETED'"
echo "   5. User lookup by email → buyer_email_address"
echo "   6. Book ID extracted → from metadata.book_id"
echo "   7. Database INSERT → book_purchases table with:"
echo "      • user_id (from email lookup)"
echo "      • book_id (from metadata)"
echo "      • payment_id (Square payment ID - for idempotency)"
echo "      • payment_provider = 'square'"
echo "      • payment_amount (in cents)"
echo "      • payment_currency (e.g., 'GBP')"
echo "      • access_key (generated securely)"
echo "      • purchased_at (timestamp)"
echo ""
echo "   8. User now has access to locked content!"
echo ""


