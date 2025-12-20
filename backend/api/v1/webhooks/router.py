"""Webhook router for payment provider integrations."""
import json
import logging
from fastapi import APIRouter, Request, HTTPException, Header

from .square import verify_square_signature, handle_square_webhook

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def webhook_health():
    """Health check endpoint for webhooks."""
    return {"status": "ok", "service": "webhooks"}


@router.post("/square")
async def square_webhook(
    request: Request,
    x_square_signature: str | None = Header(None, alias="x-square-hmacsha256-signature"),
    x_square_hmacsha256_signature: str | None = Header(None, alias="x-square-hmacsha256-signature")  # Try both header name formats
):
    """
    Handle Square webhook events for payment processing.
    
    Square sends payment.updated events when payment status changes.
    When a payment is COMPLETED, this endpoint automatically creates
    a purchase record for the user and book.
    
    Expected Square event structure:
    {
        "merchant_id": "...",
        "type": "payment.updated",
        "event_id": "...",
        "data": {
            "type": "payment",
            "object": {
                "payment": {
                    "id": "...",
                    "status": "COMPLETED",
                    "buyer_email_address": "user@example.com",
                    "metadata": {"book_id": "123"},
                    ...
                }
            }
        }
    }
    
    To set up in Square:
    1. Go to Square Developer Dashboard
    2. Navigate to your application's webhooks settings
    3. Subscribe to "payment.updated" events
    4. Set webhook URL to: https://yourdomain.com/api/v1/webhooks/square
    5. Copy the webhook signature secret and set SQUARE_WEBHOOK_SIGNATURE_SECRET env var
    6. When creating Square checkout links, include metadata: {"book_id": "123"}
    """
    # Immediate logging to verify endpoint is being called - do this FIRST
    # Use flush=True to ensure output is written immediately
    import sys
    sys.stdout.flush()
    sys.stderr.flush()
    
    try:
        logger.info("=" * 80)
        logger.info("WEBHOOK ENDPOINT CALLED - Square webhook received")
        print("=" * 80, flush=True)
        print("WEBHOOK ENDPOINT CALLED - Square webhook received", flush=True)
        print(f"Request URL: {request.url}", flush=True)
        print(f"Request method: {request.method}", flush=True)
        sys.stdout.flush()
    except Exception as log_err:
        print(f"ERROR IN INITIAL LOGGING: {log_err}", flush=True)
        sys.stderr.flush()
    
    # Wrap entire handler in try-except to prevent server crashes
    try:
        # Get raw body for signature verification
        body = await request.body()
        logger.info(f"Body read successfully: {len(body)} bytes")
        
        # Try both possible header names (Square might use either format)
        signature = x_square_signature or x_square_hmacsha256_signature
        
        # Also check headers directly in case FastAPI header parsing fails
        if not signature:
            all_headers = {k.lower(): v for k, v in request.headers.items()}
            signature = (
                all_headers.get("x-square-hmacsha256-signature") or
                all_headers.get("x-square-signature") or
                None
            )
        
        # Log headers for debugging
        logger.info(f"Square webhook received. Signature header: {signature}")
        square_headers = {k: v for k, v in request.headers.items() if 'square' in k.lower() or 'signature' in k.lower()}
        logger.info(f"All headers with 'square' or 'signature': {square_headers}")
        logger.info(f"Body length: {len(body)} bytes")
        logger.info(f"Body preview (first 200 chars): {body[:200]}")
        
        # Verify signature - Square signs: notification_url + payload
        # Use the request URL, or SQUARE_WEBHOOK_URL env var if set (should match Square Dashboard)
        notification_url = str(request.url)  # Full URL including scheme, host, path
        if not verify_square_signature(signature, body, notification_url):
            logger.warning("Invalid Square webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse event
        try:
            event = json.loads(body)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON")
        
        # Log the full payload from Square - use both logger and print for visibility
        payload_str = json.dumps(event, indent=2, default=str)
        separator = "=" * 80
        
        # Use logger (may be filtered by log level)
        logger.info(separator)
        logger.info("Square webhook payload received:")
        logger.info(payload_str)
        logger.info(separator)
        
        # Also print to stdout for visibility (won't be filtered)
        print(separator)
        print("Square webhook payload received:")
        print(payload_str)
        print(separator)
        
        # Extract and log payment data structure specifically
        data_obj = event.get("data", {})
        if isinstance(data_obj, dict):
            obj = data_obj.get("object", {})
            if isinstance(obj, dict) and obj.get("type") == "payment":
                payment_obj = obj.get("payment", {})
                if payment_obj:
                    print("\n" + "=" * 80)
                    print("PAYMENT OBJECT STRUCTURE:")
                    print(f"Payment ID: {payment_obj.get('id')}")
                    print(f"Payment keys: {list(payment_obj.keys())}")
                    print(f"Order ID: {payment_obj.get('order_id')}")
                    print(f"Buyer email address: {payment_obj.get('buyer_email_address')}")
                    print(f"Metadata: {payment_obj.get('metadata')}")
                    
                    # Check if order is nested in payment
                    nested_order = payment_obj.get("order")
                    if nested_order:
                        print(f"Nested order keys: {list(nested_order.keys()) if isinstance(nested_order, dict) else 'Not a dict'}")
                        if isinstance(nested_order, dict):
                            print(f"Nested order metadata: {nested_order.get('metadata')}")
                    
                    # Print full payment object structure
                    payment_str = json.dumps(payment_obj, indent=2, default=str)
                    print("\nFull payment object:")
                    print(payment_str[:3000])  # First 3000 chars
                    print("=" * 80 + "\n")
        
        # Process event
        try:
            result = handle_square_webhook(event)
            logger.info(f"Processed Square webhook event {event.get('event_id')}: {result}")
            return result
        except Exception as e:
            logger.error(f"Error processing Square webhook: {e}", exc_info=True)
            # Return 200 to prevent Square from retrying on our errors
            # But log the error for investigation
            return {
                "processed": False,
                "error": str(e)
            }
    except HTTPException:
        # Re-raise HTTP exceptions (401, 400, etc.) as-is
        raise
    except Exception as e:
        # Catch ANY other exception that occurs to prevent 502
        logger.error(f"Fatal error in webhook handler: {e}", exc_info=True)
        print(f"FATAL WEBHOOK ERROR: {e}")
        import traceback
        traceback.print_exc()
        # Always return 200 to Square so they don't retry
        return {
            "processed": False,
            "error": "Internal server error",
            "detail": str(e)
        }


