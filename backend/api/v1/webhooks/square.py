"""Square webhook handler for processing payment events."""
import os
import hmac
import hashlib
import base64
import json
import logging
from typing import Optional

from api.v1.books.purchases import create_purchase_with_key, has_user_purchased_book

logger = logging.getLogger(__name__)


def get_webhook_secret() -> str:
    """Get Square webhook signature secret from environment."""
    return os.getenv("SQUARE_WEBHOOK_SIGNATURE_SECRET", "")


def get_webhook_url() -> str:
    """Get the webhook URL configured in Square Dashboard."""
    # This should match exactly what's configured in Square Dashboard
    return os.getenv("SQUARE_WEBHOOK_URL", "")


def verify_square_signature(signature: str, payload: bytes, notification_url: str = None) -> bool:
    """
    Verify Square webhook signature.
    
    Square uses HMAC-SHA256 with the webhook signature secret.
    The signature is base64-encoded and sent in the x-square-hmacsha256-signature header.
    
    Note: Square's signature includes both the request body AND the notification URL.
    """
    secret = get_webhook_secret()
    if not secret:
        logger.warning("SQUARE_WEBHOOK_SIGNATURE_SECRET not set, skipping signature verification")
        # Allow requests when secret is not configured (development/testing only)
        return True
    
    # If secret is set but signature is missing, reject
    if not signature:
        logger.warning("Square webhook signature header missing but secret is configured")
        return False
    
    try:
        # Get the webhook URL configured in Square (should match Dashboard exactly)
        webhook_url = notification_url or get_webhook_url()
        
        # Try using Square SDK's helper function if available (most reliable)
        try:
            from square.utilities.webhooks_helper import is_valid_webhook_event_signature
            # Square SDK expects: body (string), signature, secret, notification_url
            payload_str = payload.decode('utf-8') if isinstance(payload, bytes) else payload
            is_valid = is_valid_webhook_event_signature(
                payload_str,
                signature,
                secret,
                webhook_url  # The exact URL configured in Square Dashboard
            )
            if is_valid:
                logger.info("Signature verified using Square SDK helper")
                return True
            else:
                logger.warning("Square SDK helper rejected signature, trying manual verification...")
        except ImportError:
            logger.debug("Square SDK webhook helper not available, using manual verification")
        except Exception as e:
            logger.debug(f"Square SDK helper failed: {e}, trying manual verification...")
        
        # Manual verification: Square signs: notification_url + payload
        key_bytes = bytes(secret, 'utf-8')
        payload_str = payload.decode('utf-8') if isinstance(payload, bytes) else payload
        
        # Method 1: Try notification_url + payload (Square's current method)
        if webhook_url:
            message = webhook_url + payload_str
            hmac_hash = hmac.new(key_bytes, message.encode('utf-8'), hashlib.sha256)
            expected_signature = base64.b64encode(hmac_hash.digest()).decode('utf-8')
            
            if hmac.compare_digest(expected_signature, signature):
                logger.info("Signature verified using notification_url + payload method")
                return True
            logger.debug(f"URL method failed. Received: {signature[:20]}..., Expected: {expected_signature[:20]}...")
        
        # Method 2: Try payload only (fallback for older Square implementations)
        hmac_hash = hmac.new(key_bytes, payload, hashlib.sha256)
        expected_signature = base64.b64encode(hmac_hash.digest()).decode('utf-8')
        
        if hmac.compare_digest(expected_signature, signature):
            logger.info("Signature verified using payload-only method")
            return True
        
        # Log for debugging
        logger.warning(f"Signature verification failed. Received: {signature}, Expected: {expected_signature}")
        logger.debug(f"Payload length: {len(payload)} bytes, Webhook URL: {webhook_url}")
        
        return False
    except Exception as e:
        logger.error(f"Error verifying Square signature: {e}", exc_info=True)
        return False


def get_user_by_email(email: str) -> Optional[int]:
    """Get user ID by email address."""
    import os
    import psycopg
    from contextlib import contextmanager
    
    @contextmanager
    def get_connection():
        dsn = os.getenv(
            "DATABASE_URL",
            "postgres://postgres:postgres@localhost:55432/bikepacking",
        )
        conn = psycopg.connect(dsn)
        try:
            yield conn
        finally:
            conn.close()
    
    query = """
        SELECT id FROM users
        WHERE email = %s
        LIMIT 1;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (email.lower(),))
            result = cur.fetchone()
            return result[0] if result else None


def extract_book_id_from_metadata(payment_data: dict) -> Optional[int]:
    """
    Extract book_id from payment metadata.
    
    Square allows custom metadata to be included in payments.
    When creating a Square checkout, include metadata like: {"book_id": "123"}
    """
    metadata = payment_data.get("metadata", {})
    
    # Try to get book_id from metadata (can be string or int)
    book_id = metadata.get("book_id")
    if book_id:
        try:
            return int(book_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid book_id in metadata: {book_id}")
    
    # Alternative: Try to extract from order line items or note
    # This depends on how you structure your Square checkout
    order_id = payment_data.get("order_id")
    if order_id:
        # You could also store book_id in the order reference or note field
        # and parse it here if needed
        pass
    
    return None


def extract_email_from_metadata(payment_data: dict) -> Optional[str]:
    """
    Extract user email from payment metadata as a fallback.
    
    We store user_email in metadata as a backup if buyer_email_address is missing.
    """
    # Try payment.metadata first
    metadata = payment_data.get("metadata", {})
    if isinstance(metadata, dict):
        user_email = metadata.get("user_email")
        if user_email:
            return str(user_email)
    
    # Try payment.order.metadata
    order = payment_data.get("order", {})
    if isinstance(order, dict):
        order_metadata = order.get("metadata", {})
        if isinstance(order_metadata, dict):
            user_email = order_metadata.get("user_email")
            if user_email:
                return str(user_email)
    
    return None


def fetch_order_from_square(order_id: str, timeout: int = 5) -> Optional[dict]:
    """
    Fetch an order from Square API using the order_id.
    
    This is needed because the payment webhook doesn't include the order metadata.
    
    Args:
        order_id: Square order ID
        timeout: Timeout in seconds (not currently enforced, but reserved for future use)
    """
    try:
        logger.info(f"Starting to fetch order {order_id} from Square (timeout: {timeout}s)")
        print(f"[DEBUG] Starting to fetch order {order_id} from Square")
        # Import Square SDK directly to avoid circular imports
        import os
        
        # Get client directly to avoid HTTPException in webhook handler
        access_token = os.getenv("SQUARE_ACCESS_TOKEN")
        environment = os.getenv("SQUARE_ENVIRONMENT", "sandbox")
        
        if not access_token:
            logger.error("SQUARE_ACCESS_TOKEN not configured, cannot fetch order")
            return None
        
        # Try to determine SDK version and import (same logic as payment_links.py)
        try:
            # Try new SDK first (v42+)
            from square import Square
            from square.environment import SquareEnvironment
            SDK_NEW = True
        except ImportError:
            try:
                # Fall back to old SDK (v41 and earlier)
                from square.client import Client
                SDK_NEW = False
            except ImportError:
                logger.error("Square SDK not installed - neither new nor old SDK found")
                return None
        
        # Create client
        if SDK_NEW:
            env = SquareEnvironment.SANDBOX if environment == "sandbox" else SquareEnvironment.PRODUCTION
            client = Square(token=access_token, environment=env)
        else:
            client = Client(access_token=access_token, environment=environment)
        
        # Fetch order
        if SDK_NEW:
            # New SDK: use orders.get() method
            try:
                # The new SDK uses orders.get() method
                result = client.orders.get(order_id=order_id)
                
                # Check if result has errors attribute (new SDK)
                if hasattr(result, 'errors') and result.errors:
                    logger.error(f"Error fetching order {order_id}: {result.errors}")
                    return None
                
                # Try to get order from result (new SDK structure)
                # The get() method typically returns result.body.order or result.body
                if hasattr(result, 'body'):
                    body = result.body
                    if isinstance(body, dict):
                        # Try 'order' key first
                        if 'order' in body:
                            return body['order']
                        # If no 'order' key, body might be the order itself
                        return body
                    return body
                elif hasattr(result, 'order'):
                    return result.order
                else:
                    # Result might be the order directly
                    logger.warning(f"Unexpected result structure when fetching order {order_id}: {type(result)}. Trying result as order directly.")
                    return result if isinstance(result, dict) else None
            except Exception as e:
                logger.error(f"Exception fetching order {order_id}: {e}", exc_info=True)
                return None
        else:
            # Old SDK
            result = client.orders.retrieve_order(order_id)
            if hasattr(result, 'is_success') and result.is_success():
                return result.body.get('order')
            else:
                errors = result.errors if hasattr(result, 'errors') else 'Unknown error'
                logger.error(f"Error fetching order {order_id}: {errors}")
                return None
    except Exception as e:
        logger.error(f"Failed to fetch order {order_id} from Square: {e}", exc_info=True)
        return None


def process_payment_succeeded(payment_data: dict, event_id: str) -> dict:
    """
    Process a successful payment and create purchase record.
    
    Args:
        payment_data: Payment object from Square webhook
        event_id: Unique event ID for idempotency
        
    Returns:
        dict with status and details
    """
    payment_id = payment_data.get("id")
    status = payment_data.get("status")
    
    if status != "COMPLETED":
        return {
            "processed": False,
            "reason": f"Payment status is {status}, not COMPLETED"
        }
    
    # Extract user email from payment
    # Square might use different field names - check multiple possibilities
    buyer_email = (
        payment_data.get("buyer_email_address") or
        payment_data.get("buyer_email") or
        payment_data.get("email_address") or
        payment_data.get("email")
    )
    
    # Also check in nested structures
    if not buyer_email:
        # Check billing_address
        billing_address = payment_data.get("billing_address", {})
        if isinstance(billing_address, dict):
            buyer_email = billing_address.get("email_address")
    
    # Fallback: try to get email from payment metadata if buyer_email_address is missing
    if not buyer_email:
        buyer_email = extract_email_from_metadata(payment_data)
        if buyer_email:
            logger.info(f"Using email from payment metadata for payment {payment_id}: {buyer_email}")
    
    # Extract book_id from metadata
    # First try payment metadata
    book_id = extract_book_id_from_metadata(payment_data)
    
    # If email or book_id is missing, try to fetch the order and get metadata from there
    order = None
    if not buyer_email or not book_id:
        order_id = payment_data.get("order_id")
        if order_id:
            logger.info(f"Fetching order {order_id} to extract metadata (email: {bool(buyer_email)}, book_id: {bool(book_id)})")
            print(f"[DEBUG] Attempting to fetch order {order_id} from Square API")
            order = fetch_order_from_square(order_id)
            if order:
                print(f"[DEBUG] Successfully fetched order {order_id}")
                logger.info(f"Successfully fetched order {order_id}")
                
                # Convert Pydantic model to dict if needed
                if hasattr(order, 'model_dump'):
                    # Pydantic v2
                    order_dict = order.model_dump()
                elif hasattr(order, 'dict'):
                    # Pydantic v1
                    order_dict = order.dict()
                elif isinstance(order, dict):
                    order_dict = order
                else:
                    # Try to convert using __dict__ or access attributes directly
                    try:
                        order_dict = dict(order) if hasattr(order, '__iter__') else vars(order)
                    except (TypeError, ValueError):
                        # Last resort: access attributes directly
                        order_dict = order
                
                print(f"[DEBUG] Order type: {type(order)}, Order keys: {list(order_dict.keys()) if isinstance(order_dict, dict) else 'N/A'}")
                logger.info(f"Order type: {type(order)}, Order keys: {list(order_dict.keys()) if isinstance(order_dict, dict) else 'N/A'}")
                
                # Also check order.note field (backup storage method)
                order_note = order_dict.get("note", "") if isinstance(order_dict, dict) else (getattr(order, 'note', None) or "")
                print(f"[DEBUG] Order note field: {order_note}")
                logger.info(f"Order note field: {order_note}")
                
                # Try to parse book_id and email from note field (format: "book_id:123|email:user@example.com")
                if order_note and isinstance(order_note, str):
                    for part in order_note.split("|"):
                        if ":" in part:
                            key, value = part.split(":", 1)
                            if key == "book_id" and not book_id:
                                try:
                                    book_id = int(value)
                                    logger.info(f"Extracted book_id {book_id} from order.note")
                                    print(f"[DEBUG] Extracted book_id from note: {book_id}")
                                except (ValueError, TypeError):
                                    pass
                            elif key == "email" and not buyer_email:
                                buyer_email = value
                                logger.info(f"Extracted email from order.note: {buyer_email}")
                                print(f"[DEBUG] Extracted email from note: {buyer_email}")
                
                # Try to extract from order metadata
                order_metadata = order_dict.get("metadata", {}) if isinstance(order_dict, dict) else (getattr(order, 'metadata', None) or {})
                
                # If metadata is a Pydantic model, convert it
                if hasattr(order_metadata, 'model_dump'):
                    order_metadata = order_metadata.model_dump()
                elif hasattr(order_metadata, 'dict'):
                    order_metadata = order_metadata.dict()
                elif not isinstance(order_metadata, dict):
                    order_metadata = {}
                
                print(f"[DEBUG] Order metadata: {order_metadata}")
                logger.info(f"Order metadata: {order_metadata}")
                
                # Extract book_id from order if not already found
                if not book_id and isinstance(order_metadata, dict):
                    book_id_str = order_metadata.get("book_id")
                    if book_id_str:
                        try:
                            book_id = int(book_id_str)
                            logger.info(f"Found book_id {book_id} in order metadata")
                            print(f"[DEBUG] Extracted book_id: {book_id}")
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Failed to convert book_id {book_id_str} to int: {e}")
                    else:
                        logger.warning(f"No book_id in order metadata. Available keys: {list(order_metadata.keys())}")
                        print(f"[DEBUG] No book_id in order metadata. Keys: {list(order_metadata.keys())}")
                
                # Also try to get email from order if we don't have it yet
                if not buyer_email:
                    if isinstance(order_dict, dict):
                        order_email = order_dict.get("buyer_email") or order_metadata.get("user_email")
                    else:
                        order_email = getattr(order, 'buyer_email', None) or order_metadata.get("user_email")
                    
                    if order_email:
                        buyer_email = str(order_email)
                        logger.info(f"Found email from order metadata: {buyer_email}")
                        print(f"[DEBUG] Extracted email from order: {buyer_email}")
            else:
                print(f"[DEBUG] Failed to fetch order {order_id} - order is None")
                logger.warning(f"Failed to fetch order {order_id}")
    
    # Now check if we have email - if not, log and return error
    if not buyer_email:
        logger.warning(f"No buyer email in payment {payment_id}")
        payment_structure = json.dumps(payment_data, indent=2, default=str)
        logger.info(f"Payment data keys: {list(payment_data.keys())}")
        logger.info(f"Payment data structure: {payment_structure[:1000]}")
        
        # Also print for visibility
        print("=" * 80)
        print(f"Payment {payment_id} - No buyer email found in payment or order")
        print(f"Payment data keys: {list(payment_data.keys())}")
        print("Payment data structure:")
        print(payment_structure[:2000])  # First 2000 chars
        print("=" * 80)
        
        return {
            "processed": False,
            "reason": "No buyer email address in payment or order metadata"
        }
    
    # Get user by email
    user_id = get_user_by_email(buyer_email)
    if not user_id:
        logger.warning(f"User not found for email: {buyer_email}")
        return {
            "processed": False,
            "reason": f"User not found for email: {buyer_email}"
        }
    
    if not book_id:
        logger.warning(f"No book_id found in payment or order metadata for payment {payment_id}")
        return {
            "processed": False,
            "reason": "No book_id in payment or order metadata"
        }
    
    # Extract payment details
    amount_money = payment_data.get("amount_money", {})
    payment_amount = amount_money.get("amount")  # Amount in cents
    payment_currency = amount_money.get("currency", "GBP")
    
    # Create purchase record with access key and payment details
    # The create_purchase_with_key function handles idempotency via payment_id
    try:
        access_key = create_purchase_with_key(
            user_id=user_id,
            book_id=book_id,
            payment_id=payment_id,
            payment_provider="square",
            payment_amount=payment_amount,
            payment_currency=payment_currency
        )
        logger.info(f"Created purchase for user {user_id}, book {book_id}, payment {payment_id}")
        return {
            "processed": True,
            "user_id": user_id,
            "book_id": book_id,
            "payment_id": payment_id,
            "access_key": access_key
        }
    except Exception as e:
        logger.error(f"Error creating purchase: {e}")
        return {
            "processed": False,
            "reason": str(e)
        }


def handle_square_webhook(event: dict) -> dict:
    """
    Handle a Square webhook event.
    
    Square sends events like:
    {
        "merchant_id": "...",
        "type": "payment.updated",
        "event_id": "...",
        "created_at": "...",
        "data": {
            "type": "payment",
            "id": "...",
            "object": {
                "payment": {...}
            }
        }
    }
    """
    event_type = event.get("type")
    event_id = event.get("event_id")
    event_data = event.get("data", {})
    
    if event_type == "payment.updated":
        payment_obj = event_data.get("object", {})
        payment = payment_obj.get("payment", {})
        
        if not payment:
            logger.warning(f"No payment object in event data. Event data keys: {list(event_data.keys())}")
            logger.info(f"Event data structure: {json.dumps(event_data, indent=2, default=str)[:500]}")
            return {
                "processed": False,
                "reason": "No payment object in event data"
            }
        
        # Log payment structure for debugging
        logger.info(f"Processing payment {payment.get('id')}. Payment keys: {list(payment.keys())}")
        
        return process_payment_succeeded(payment, event_id)
    
    elif event_type == "test.notification":
        # Square sends this for webhook testing
        return {
            "processed": True,
            "test": True,
            "message": "Test notification received"
        }
    
    else:
        return {
            "processed": False,
            "reason": f"Unhandled event type: {event_type}"
        }


