# Creating Square Payment Links

This guide explains how to create Square Payment Links with the proper metadata for automatic purchase tracking.

## Setup

### 1. Install Square SDK

```bash
cd backend
pip install squareup
```

Or add to `requirements.txt` (already included):
```bash
pip install -r requirements.txt
```

### 2. Get Square Access Token

1. Go to [Square Developer Dashboard](https://developer.squareup.com/apps)
2. Select your application
3. Go to **Credentials** → **Sandbox** (for testing) or **Production**
4. Copy your **Access Token**

### 3. Set Environment Variables

Add to your `.env` file:

```bash
# Square API credentials
SQUARE_ACCESS_TOKEN=your_access_token_here
SQUARE_ENVIRONMENT=sandbox  # or 'production' for live payments
```

Or export in your shell:

```bash
export SQUARE_ACCESS_TOKEN=your_access_token_here
export SQUARE_ENVIRONMENT=sandbox
```

## Usage

### Basic Usage

```bash
cd backend
python create_square_payment_link.py \
  --book-id 1 \
  --email user@example.com \
  --price 999
```

This creates a payment link for:
- Book ID: 1
- Buyer email: user@example.com (must exist in your database)
- Price: £9.99 (999 cents for GBP)

### With All Options

```bash
python create_square_payment_link.py \
  --book-id 1 \
  --book-title "Bikepacking King Alfred's Way" \
  --email user@example.com \
  --price 1999 \
  --currency GBP \
  --location-id YOUR_LOCATION_ID \
  --environment sandbox
```

### Parameters

- `--book-id` (required): Book ID from your database
- `--email` / `--buyer-email` (required): Buyer's email (must match a user in your database)
- `--price` (required): Price in smallest currency unit (e.g., 999 = £9.99)
- `--book-title` (optional): Book title for display (default: "Book #{book_id}")
- `--currency` (optional): Currency code (default: GBP)
- `--location-id` (optional): Square location ID (uses first location if not provided)
- `--access-token` (optional): Square access token (or use env var)
- `--environment` (optional): 'sandbox' or 'production' (default: sandbox)

## What Gets Created

The script creates a Square Payment Link that includes:

1. **Buyer Email** (`pre_populated_data.buyer_email`)
   - Pre-fills the email field
   - Ensures webhook can find the user by email

2. **Book ID Metadata** (`metadata.book_id`)
   - Stores the book ID for webhook processing
   - Links the payment to the correct book

3. **Order Details**
   - Book title as line item name
   - Price and currency
   - Location ID

## Example Output

```
Using location: Main Store
✅ Payment link created successfully!
   Payment Link ID: ABC123XYZ
   URL: https://square.link/u/ABC123XYZ

📋 Metadata included:
   - book_id: 1
   - buyer_email: user@example.com

🔗 Share this link with the customer:
   https://square.link/u/ABC123XYZ

💡 After payment, the webhook will automatically create a purchase record.
```

## Webhook Flow

1. Customer clicks payment link → Square checkout
2. Customer completes payment → Square processes payment
3. Square sends `payment.updated` webhook → Your API receives it
4. Webhook handler extracts:
   - `buyer_email_address` → finds user_id
   - `metadata.book_id` → gets book_id
5. Purchase record created in `book_purchases` table
6. User gains access to locked content

## Troubleshooting

### "SQUARE_ACCESS_TOKEN not set"
- Set the environment variable or pass `--access-token`
- Get token from Square Developer Dashboard

### "No Square locations found"
- Create a location in Square Dashboard
- Or pass `--location-id` explicitly

### "Failed to create payment link"
- Check your access token is valid
- Verify you're using the correct environment (sandbox/production)
- Ensure location_id is valid

### Webhook doesn't create purchase
- Verify buyer email matches a user in your database
- Check that metadata.book_id is included (it should be automatically)
- Check server logs for webhook processing errors

## Integration with Your App

You could integrate this into your application:

1. **Backend API Endpoint**: Create an endpoint that calls this script
2. **Frontend**: Show payment link when user wants to purchase
3. **Database**: Store payment_link_id for tracking

Example API endpoint:

```python
@router.post("/books/{book_id}/payment-link")
def create_book_payment_link(
    book_id: int,
    current_user: UserInDB = Depends(get_current_user)
):
    # Get book details
    book = get_book_by_id(book_id)
    
    # Create payment link using Square API
    payment_link_url = create_payment_link(...)
    
    return {"payment_link": payment_link_url}
```

## Security Notes

- **Never expose access tokens** in frontend code
- Use environment variables for credentials
- Use sandbox for testing, production for live payments
- Payment links are public URLs - anyone with the link can pay
- Use idempotency keys (already handled by script)


