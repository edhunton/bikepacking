# Square Sandbox Testing Guide

## Payment Links in Sandbox

Square Payment Links work in sandbox mode, but there are some differences from production:

### Understanding the Sandbox Testing Panel

When you create a payment link in sandbox, you might see a "Sandbox Testing Panel" that displays:
- The API response details
- The `order_id` 
- The payment link `url`
- The order state (usually `DRAFT`)

**This panel is just informational** - it's showing you what Square returned. The actual checkout page is at the URL shown (`https://sandbox.square.link/u/XXXXX`).

### How to Complete a Test Purchase

1. **Copy the URL** from the testing panel (e.g., `https://sandbox.square.link/u/KwrEUTXo`)
2. **Open it in a new browser tab/window** (or click directly if it's a link)
3. **You should see the actual Square checkout page** with payment form
4. **Use test card**: `4111 1111 1111 1111` with any CVV, expiration, and ZIP
5. **Complete the purchase** - this will trigger your webhook

### Test Card Numbers

To complete a test purchase in Square sandbox, use these test card numbers:

**Successful Payment:**
- Card Number: `4111 1111 1111 1111`
- CVV: Any 3 digits (e.g., `123`)
- Expiration: Any future date (e.g., `12/25`)
- ZIP Code: Any 5 digits (e.g., `12345`)

**Declined Payment (for testing errors):**
- Card Number: `4000 0000 0000 0002`

### Sandbox Testing Panel

When you open a payment link in sandbox mode, you might see a "Checkout API Sandbox Testing Panel" that appears display-only. Here's what to check:

1. **Verify the Link Type**: Make sure you're using Payment Links (not just Checkout API preview)
   - Payment Links should have URLs like: `https://sandbox.square.link/u/XXXXX`
   - These should allow actual checkout, not just display

2. **If the panel is display-only**, try:
   - Checking your Square Dashboard to ensure the payment link is active
   - Verifying your sandbox account has the necessary permissions
   - Using the test card numbers above
   - Clearing browser cache and trying again

3. **Check Payment Link Settings**:
   - Go to Square Dashboard > Payment Links
   - Make sure the link is not set to "Draft" or "Paused"
   - Verify checkout is enabled for the link

### Testing the Complete Flow

1. **Create Payment Link**: Click "Buy Now" button - should create a link with your email
2. **Open Link**: Payment link opens in new window/tab
3. **Complete Checkout**: Use test card `4111 1111 1111 1111`
4. **Verify Webhook**: Check that webhook receives `payment.updated` event
5. **Check Purchase Record**: Verify purchase is created in your database

### Troubleshooting

If the sandbox panel shows "display only":

1. **Check Square Dashboard**:
   - Log into [Square Sandbox Dashboard](https://squareup.com/dashboard/sandbox)
   - Go to Payment Links section
   - Verify the link was created and is active

2. **Verify API Response**:
   - Check server logs for the actual payment link URL
   - The URL should be a full Square payment link, not a preview URL

3. **Try Direct Link**:
   - Copy the payment link URL from the API response
   - Open it directly in a browser (not via `window.open`)
   - This can help identify if it's a browser/popup issue

4. **Check Sandbox Account**:
   - Ensure your sandbox application has Payment Links API enabled
   - Verify your access token has the correct permissions

### Alternative: Use Square Checkout API

If Payment Links don't work for testing, you can switch to Square Checkout API temporarily:

```python
# This creates a checkout session instead of a payment link
# It redirects to Square's hosted checkout page
result = client.checkout.create_checkout(location_id, {
    "idempotency_key": str(uuid.uuid4()),
    "order": {...},
    "redirect_url": "https://yourdomain.com/payment-success"
})
```

Payment Links are generally better for production use, but Checkout API might work better for sandbox testing.

## Webhook Testing

To test webhooks in sandbox:

1. Set up webhook URL in Square Dashboard
2. Use Square's webhook testing tool
3. Or complete a test payment and verify the webhook is received

The webhook should receive a `payment.updated` event when payment is completed.

