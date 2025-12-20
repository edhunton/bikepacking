# Square Webhook Setup Guide

This guide explains how to set up Square webhooks for automatic purchase tracking.

**For local testing:** See `WEBHOOK_LOCAL_TESTING.md` for how to expose your localhost server.

## Overview

When a customer completes a payment through Square, Square sends a webhook event to our server. The webhook handler automatically creates a purchase record, granting the customer access to the purchased book.

## Setup Steps

### 1. Configure Square Checkout with Metadata

When creating Square checkout links (stored in `books.purchase_url`), you need to include the `book_id` in the payment metadata.

**Important:** When creating a Square Payment Link or Checkout, include metadata:
```json
{
  "book_id": "123"  // The book's database ID
}
```

This can be done via:
- Square Payment Links: Add metadata in the API call
- Square Checkout: Include `metadata` field with `book_id`

### 2. Set Up Webhook in Square Developer Dashboard

1. Go to [Square Developer Dashboard](https://developer.squareup.com/apps)
2. Select your application
3. Navigate to **Webhooks** in the left sidebar
4. Click **Add Webhook** or **Subscribe to Events**
5. Enter your webhook URL: `https://yourdomain.com/api/v1/webhooks/square`
   - **For local testing:** Use ngrok or similar (see `WEBHOOK_LOCAL_TESTING.md`)
6. Subscribe to the event: **payment.updated**
7. Copy the **Webhook Signature Secret** (you'll need this next)

### 3. Configure Environment Variable

Add the webhook signature secret to your `.env` file:

```bash
SQUARE_WEBHOOK_SIGNATURE_SECRET=your_webhook_signature_secret_here
```

**Security:** Keep this secret secure. It's used to verify that webhooks are actually from Square.

### 4. Test the Webhook

Square provides a test notification feature. The webhook handler will respond to `test.notification` events.

You can also test by:
1. Making a test payment in Square's sandbox
2. Checking the server logs for webhook processing
3. Verifying the purchase was created in the database

## How It Works

1. **Customer completes payment** via Square checkout link
2. **Square sends webhook** to `/api/v1/webhooks/square` with payment details
3. **Server verifies signature** to ensure the webhook is from Square
4. **Extract details:**
   - User email from `buyer_email_address`
   - Book ID from `metadata.book_id`
   - Payment ID for idempotency
5. **Create purchase record** with access key
6. **User gains access** to the book's locked content

## Payment Flow

```
Customer → Square Checkout (with metadata: {"book_id": "123"})
    ↓
Payment Completed
    ↓
Square Webhook → /api/v1/webhooks/square
    ↓
Verify Signature
    ↓
Extract: user_email, book_id, payment_id
    ↓
Find User by Email
    ↓
Create Purchase Record (idempotent via payment_id)
    ↓
User Can Now Access Book Content
```

## Idempotency

The system prevents duplicate purchases by:
- Checking `payment_id` first (if webhook is sent twice)
- Using `UNIQUE(user_id, book_id)` constraint as backup

## Manual Purchases

For testing or special cases, you can manually create purchases:
- **API Endpoint:** `POST /api/v1/books/{book_id}/purchase`
- **Auth:** Requires user authentication
- **Use Cases:** Testing, admin grants, external purchases (Amazon, etc.)

## Troubleshooting

### Webhook not being called
- Check Square webhook configuration
- Verify webhook URL is publicly accessible (HTTPS required in production)
- Check Square dashboard for webhook delivery logs

### Purchase not created
- Check server logs for errors
- Verify `book_id` is in payment metadata
- Verify user email matches an existing user account
- Check database for any constraint violations

### Signature verification failing
- Verify `SQUARE_WEBHOOK_SIGNATURE_SECRET` is set correctly
- Ensure webhook secret matches Square dashboard
- Check that request body is not being modified before verification

## Security Notes

- Webhooks should only be accessible over HTTPS in production
- Always verify webhook signatures
- Log all webhook events for auditing
- Consider rate limiting the webhook endpoint
- Never expose the webhook signature secret in code or logs


