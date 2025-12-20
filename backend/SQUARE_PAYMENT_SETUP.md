# Setting Up Square Payments with Metadata

To properly associate payments with users and books, you need to include metadata and buyer email when creating Square payments.

## Required Fields

Your Square payment webhook needs:
1. **`buyer_email_address`** - To find the user in your database
2. **`metadata.book_id`** - To identify which book was purchased

## Option 1: Square Payment Links (Recommended)

When creating a Square Payment Link via API, include metadata:

```python
# Example using Square API
from square.client import Client

square_client = Client(
    access_token='YOUR_SQUARE_ACCESS_TOKEN',
    environment='sandbox'  # or 'production'
)

payment_link_request = {
    "idempotency_key": str(uuid.uuid4()),
    "description": f"Purchase: {book_title}",
    "order": {
        "location_id": "YOUR_LOCATION_ID",
        "line_items": [
            {
                "name": book_title,
                "quantity": "1",
                "item_type": "ITEM",
                "base_price_money": {
                    "amount": price_in_cents,
                    "currency": "GBP"
                }
            }
        ]
    },
    "pre_populated_data": {
        "buyer_email": user_email,  # ← Important: Include buyer email
    },
    "metadata": {
        "book_id": str(book_id)  # ← Important: Include book_id
    }
}

result = square_client.checkout.create_payment_link(body=payment_link_request)
payment_link_url = result.body['payment_link']['url']
```

## Option 2: Square Checkout API

When using Square Checkout API:

```python
checkout_request = {
    "idempotency_key": str(uuid.uuid4()),
    "order": {
        "location_id": "YOUR_LOCATION_ID",
        "line_items": [...],
        "metadata": {
            "book_id": str(book_id)  # ← Include in order metadata
        }
    },
    "pre_populate_buyer_email": user_email,  # ← Include buyer email
    "redirect_url": "https://yourdomain.com/thanks"
}

result = square_client.checkout.create_checkout(location_id, checkout_request)
```

## Option 3: Square Online Store / Invoicing

If using Square's online store or invoicing:
- **Metadata**: Add custom fields during order creation
- **Email**: Ensure customer email is collected during checkout

## Current Webhook Handler Requirements

Your webhook handler (`backend/api/v1/webhooks/square.py`) expects:

```json
{
  "data": {
    "object": {
      "payment": {
        "buyer_email_address": "user@example.com",  // ← Required
        "metadata": {
          "book_id": "123"  // ← Required
        },
        "status": "COMPLETED"
      }
    }
  }
}
```

## Troubleshooting

### If buyer_email_address is missing:

The webhook will return:
```json
{
  "processed": false,
  "reason": "No buyer email address in payment"
}
```

**Solution**: Ensure your Square checkout collects and includes the buyer's email.

### If metadata.book_id is missing:

The webhook will return:
```json
{
  "processed": false,
  "reason": "No book_id in payment metadata"
}
```

**Solution**: Include `metadata: {"book_id": "123"}` when creating the payment.

## Alternative: Using Order ID Lookup

If you cannot include metadata in Square payments, you could:
1. Store a mapping of `order_id → book_id` in your database
2. Modify the webhook handler to lookup book_id from order_id

This would require additional database infrastructure and code changes.

## Testing

Use the test script to simulate a payment with proper structure:

```bash
cd backend
export SQUARE_WEBHOOK_SECRET=your_secret
./test_webhook_payment_complete.sh user@example.com 1 payment_test_123
```

This creates a properly formatted webhook payload with buyer_email and metadata.


