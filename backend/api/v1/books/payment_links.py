"""API endpoint for creating dynamic Square payment links."""
import os
import uuid
import logging
from typing import Optional

from fastapi import HTTPException

try:
    # Try new SDK (v42+) first
    from square import Square
    from square.environment import SquareEnvironment
    SDK_NEW = True
except ImportError:
    try:
        # Fall back to old SDK (v41 and earlier)
        from square.client import Client
        SDK_NEW = False
    except ImportError:
        Square = None
        Client = None
        SDK_NEW = None

logger = logging.getLogger(__name__)


def get_square_client():
    """Get Square API client from environment variables."""
    if SDK_NEW is None:
        raise HTTPException(
            status_code=500,
            detail="Square SDK not installed. Install with: pip install squareup"
        )
    
    access_token = os.getenv("SQUARE_ACCESS_TOKEN")
    environment = os.getenv("SQUARE_ENVIRONMENT", "sandbox")
    
    if not access_token:
        raise HTTPException(
            status_code=500,
            detail="SQUARE_ACCESS_TOKEN not configured. Set it in environment variables."
        )
    
    # Use new SDK (v42+)
    if SDK_NEW:
        env = SquareEnvironment.SANDBOX if environment == "sandbox" else SquareEnvironment.PRODUCTION
        return Square(
            token=access_token,
            environment=env
        )
    # Use old SDK (v41 and earlier)
    else:
        return Client(
            access_token=access_token,
            environment=environment
        )


def create_payment_link_for_user(
    user_email: str,
    book_id: int,
    book_title: str,
    price_cents: int,
    currency: str = "GBP",
    location_id: Optional[str] = None
) -> str:
    """
    Create a Square Payment Link dynamically for a specific user.
    
    This should be called when a user wants to purchase a book.
    The link includes:
    - buyer_email: The user's email (for webhook user identification)
    - metadata.book_id: The book ID (for webhook book identification)
    
    Args:
        user_email: The logged-in user's email address
        book_id: Book ID from database
        book_title: Book title for display
        price_cents: Price in smallest currency unit
        currency: Currency code (default: GBP)
        location_id: Square location ID (optional)
    
    Returns:
        Payment link URL
    
    Raises:
        HTTPException: If Square API call fails
    """
    client = get_square_client()
    is_new_sdk = SDK_NEW  # Store locally to avoid issues
    
    # Get location ID if not provided
    if not location_id:
        try:
            if is_new_sdk:
                # New SDK (v42+) uses list() method and may raise exceptions or return data directly
                try:
                    locations_result = client.locations.list()
                    # New SDK returns the response directly or raises exceptions on error
                    # Check if response has errors attribute
                    if hasattr(locations_result, 'errors') and locations_result.errors:
                        errors = locations_result.errors
                        logger.error(f"Failed to get Square locations: {errors}")
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to get Square locations: {errors}"
                        )
                    # Extract locations - new SDK might have different structure
                    if hasattr(locations_result, 'locations'):
                        locations = locations_result.locations
                    elif hasattr(locations_result, 'data') and hasattr(locations_result.data, 'locations'):
                        locations = locations_result.data.locations
                    elif hasattr(locations_result, 'body'):
                        locations = locations_result.body.get("locations", []) if isinstance(locations_result.body, dict) else []
                    else:
                        locations = []
                except Exception as api_error:
                    # New SDK may raise exceptions on API errors
                    logger.error(f"Square API error getting locations: {api_error}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to get Square locations: {str(api_error)}"
                    )
            else:
                # Old SDK (v41 and earlier) uses list_locations() method
                locations_result = client.locations.list_locations()
                
                if not locations_result.is_success():
                    errors = locations_result.errors if hasattr(locations_result, 'errors') else str(locations_result)
                    logger.error(f"Failed to get Square locations: {errors}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to get Square locations: {errors}"
                    )
                
                # Extract locations from response
                if hasattr(locations_result, 'body'):
                    locations = locations_result.body.get("locations", [])
                elif hasattr(locations_result, 'data'):
                    locations = locations_result.data.get("locations", [])
                else:
                    locations = []
                
            if not locations:
                raise HTTPException(
                    status_code=500,
                    detail="No Square locations found. Create a location in Square Dashboard."
                )
            
            # Get location ID - handle both dict and object formats
            if isinstance(locations[0], dict):
                location_id = locations[0].get("id")
            else:
                location_id = getattr(locations[0], 'id', None)
                
            if not location_id:
                raise HTTPException(
                    status_code=500,
                    detail="Could not extract location ID from Square response"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting locations: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving Square locations: {str(e)}. Please provide location_id parameter."
            )
    
    # Create payment link request with user-specific data
    # Ensure idempotency_key is a plain string (not UUID object)
    idempotency_key = str(uuid.uuid4())
    # Double-check it's actually a string type
    if not isinstance(idempotency_key, str):
        idempotency_key = str(idempotency_key)
    
    # For new SDK, check if idempotency_key is a separate parameter before building request
    idempotency_key_separate = False
    if is_new_sdk:
        try:
            import inspect
            if hasattr(client, 'checkout') and hasattr(client.checkout, 'payment_links'):
                sig = inspect.signature(client.checkout.payment_links.create)
                param_names = [p for p in sig.parameters.keys() if p != 'self']
                idempotency_key_separate = 'idempotency_key' in param_names
        except Exception:
            # If inspection fails, assume it's not separate (safer default)
            pass
    
    # Prepare request data - format may differ between SDK versions
    if is_new_sdk:
        # For new SDK, all fields are separate parameters, not wrapped in a dict
        # Build the order object - metadata goes inside the order (not top-level)
        order_object = {
            "location_id": str(location_id),
            "line_items": [
                {
                    "name": str(book_title),
                    "quantity": "1",
                    "item_type": "ITEM",
                    "base_price_money": {
                        "amount": int(price_cents),
                        "currency": str(currency)
                    }
                }
            ]
            # NOTE: metadata should be at payment link level, not inside order
        }
        
        pre_populated_data = {
            "buyer_email": str(user_email)
        }
        
        # Add checkout_options to enable proper checkout flow (not just display)
        checkout_options = {
            "allow_tipping": False,
            "collect_shipping_address": False,
            "ask_for_shipping_address": False
        }
        
        # Store individual parameters for passing as kwargs
        # NOTE: New SDK doesn't support top-level metadata - put it in the order object
        # Store book_id and email in order metadata
        order_object["metadata"] = {
            "book_id": str(book_id),  # Store book_id in order metadata
            "user_email": str(user_email)  # Also store email in metadata as backup
        }
        
        # ALSO store in order.note field as backup (more reliably preserved by Square)
        # Format: "book_id:123|email:user@example.com"
        order_object["note"] = f"book_id:{book_id}|email:{user_email}"
        
        payment_link_params = {
            "description": str(f"Purchase: {book_title}"),
            "order": order_object,
            "pre_populated_data": pre_populated_data,
            "checkout_options": checkout_options
        }
        
        # For compatibility, also create a dict version (but idempotency_key is always separate)
        payment_link_request = payment_link_params
    else:
        # Old SDK uses dict format
        payment_link_request = {
            "idempotency_key": idempotency_key,
            "description": f"Purchase: {book_title}",
            "order": {
                "location_id": location_id,
                "line_items": [
                    {
                        "name": book_title,
                        "quantity": "1",
                        "item_type": "ITEM",
                        "base_price_money": {
                            "amount": price_cents,
                            "currency": currency
                        }
                    }
                ]
            },
            "pre_populated_data": {
                "buyer_email": user_email,  # ← User-specific: Links payment to logged-in user
            },
            "metadata": {
                "book_id": str(book_id)  # ← Links payment to book
            }
        }
    
    # Create the payment link
    try:
        if is_new_sdk:
            # New SDK (v42+) - use checkout.payment_links.create()
            # The method only accepts keyword arguments, not positional or 'body='
            try:
                if hasattr(client, 'checkout') and hasattr(client.checkout, 'payment_links'):
                    # Inspect the method signature to find the correct parameter name
                    import inspect
                    sig = inspect.signature(client.checkout.payment_links.create)
                    param_names = list(sig.parameters.keys())
                    # Remove 'self' if present
                    param_names = [p for p in param_names if p != 'self']
                    
                    if param_names:
                        # Use the first parameter name (excluding self)
                        param_name = param_names[0]
                        
                        # Log what we're about to send (for debugging)
                        # All fields are separate parameters in new SDK - pass them directly as kwargs
                        # NOTE: metadata should be at top level, not inside order
                        call_kwargs = {
                            'idempotency_key': idempotency_key,
                            'description': payment_link_params['description'],
                            'order': payment_link_params['order'],
                            'pre_populated_data': payment_link_params['pre_populated_data']
                        }
                        # Add checkout_options if present (helps enable checkout flow)
                        if 'checkout_options' in payment_link_params:
                            call_kwargs['checkout_options'] = payment_link_params['checkout_options']
                        # NOTE: metadata is already in the order object, not top-level
                        
                        result = client.checkout.payment_links.create(**call_kwargs)
                    else:
                        # If no parameters found, try common names
                        # Common parameter names in Square SDK v42+
                        for param_name in ['payment_link', 'request', 'payload', 'data']:
                            try:
                                result = client.checkout.payment_links.create(**{param_name: payment_link_request})
                                logger.debug(f"Successfully used parameter name: {param_name}")
                                break
                            except TypeError:
                                continue
                        else:
                            # If all attempts failed, try importing request model
                            try:
                                from square.models.checkout import CreatePaymentLinkRequest
                                request_obj = CreatePaymentLinkRequest(**payment_link_request)
                                # Try again with the model object
                                for param_name in ['payment_link', 'request', 'payload', 'data']:
                                    try:
                                        result = client.checkout.payment_links.create(**{param_name: request_obj})
                                        break
                                    except TypeError:
                                        continue
                                else:
                                    raise HTTPException(
                                        status_code=500,
                                        detail=f"Could not determine correct parameter name for create(). Tried: {param_names if param_names else ['payment_link', 'request', 'payload', 'data']}"
                                    )
                            except (ImportError, TypeError, AttributeError) as e:
                                raise HTTPException(
                                    status_code=500,
                                    detail=f"Square SDK API argument error: Could not determine parameter name. Tried inspecting signature and common names. Error: {str(e)}"
                                )
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="Square SDK structure: checkout.payment_links not available"
                    )
            except HTTPException:
                raise
            except AttributeError as e:
                logger.error(f"Square SDK structure issue: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Square SDK API structure issue: {str(e)}"
                )
            except Exception as e:
                logger.error(f"Square SDK error creating payment link: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create payment link: {str(e)}"
                )
            
            # New SDK (v42+) - check for errors or exceptions
            # Check if result has status_code (HTTP response) or errors attribute
            if hasattr(result, 'status_code') and result.status_code and result.status_code >= 400:
                # This is likely an HTTP response with errors
                error_body = getattr(result, 'body', {})
                if isinstance(error_body, dict) and 'errors' in error_body:
                    errors = error_body['errors']
                    error_details = []
                    for error in errors:
                        if isinstance(error, dict):
                            detail = error.get('detail', str(error))
                            field = error.get('field', '')
                            code = error.get('code', '')
                            error_details.append(f"{field}: {detail}" if field else detail)
                        else:
                            error_details.append(str(error))
                    
                    logger.error(f"Square API error creating payment link: {error_details}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to create payment link: {', '.join(error_details[:3])}"
                    )
                else:
                    logger.error(f"Square API error (status {result.status_code}): {error_body}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to create payment link: Square API returned status {result.status_code}"
                    )
            elif hasattr(result, 'errors') and result.errors:
                errors = result.errors
                error_details = [str(error.get('detail', error)) if isinstance(error, dict) else str(error) for error in (errors if isinstance(errors, list) else [errors])]
                logger.error(f"Failed to create Square payment link: {error_details}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create payment link: {', '.join(error_details[:3])}"
                )
            # Extract payment link from new SDK response
            # Response structure can vary - try multiple approaches
            payment_link = None
            
            # Try direct attribute access
            if hasattr(result, 'payment_link'):
                payment_link = result.payment_link
            # Try body attribute (common in SDK responses)
            elif hasattr(result, 'body'):
                if isinstance(result.body, dict):
                    payment_link = result.body.get("payment_link")
                # If body is the payment_link directly
                elif hasattr(result.body, 'url'):
                    payment_link = result.body
            # Try data attribute
            elif hasattr(result, 'data'):
                if hasattr(result.data, 'payment_link'):
                    payment_link = result.data.payment_link
                elif hasattr(result.data, 'url'):
                    payment_link = result.data
            # Try as dict
            elif isinstance(result, dict):
                payment_link = result.get("payment_link")
            
            # Log what we found for debugging
            if payment_link:
                logger.debug(f"Found payment_link object: {type(payment_link)}")
            else:
                # Log full result structure for debugging
                logger.warning(f"Could not find payment_link in response. Result type: {type(result)}")
                if hasattr(result, '__dict__'):
                    logger.warning(f"Result attributes: {list(result.__dict__.keys())}")
                if hasattr(result, 'body'):
                    logger.warning(f"Result body type: {type(result.body)}, content: {result.body}")
            
            if not payment_link:
                payment_link = {}
        else:
            # Old SDK (v41 and earlier) - use checkout.create_payment_link()
            result = client.checkout.create_payment_link(body=payment_link_request)
            
            if not result.is_success():
                errors = result.errors if hasattr(result, 'errors') else str(result)
                error_details = [str(error.get('detail', error)) if isinstance(error, dict) else str(error) for error in (errors if isinstance(errors, list) else [errors])]
                logger.error(f"Failed to create Square payment link: {error_details}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create payment link: {', '.join(error_details[:3])}"
                )
            payment_link = result.body.get("payment_link", {}) if hasattr(result, 'body') else {}
        
        # Extract URL - handle both dict and object formats
        if isinstance(payment_link, dict):
            payment_link_url = payment_link.get("url")
        else:
            payment_link_url = getattr(payment_link, 'url', None)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Square API error creating payment link: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create payment link: {str(e)}"
        )
    
    if not payment_link_url:
        result_str = str(result) if result else "None"
        if hasattr(result, 'body'):
            result_str = str(result.body)
        logger.error(f"Payment link created but no URL in response: {result_str}")
        raise HTTPException(
            status_code=500,
            detail="Payment link created but no URL returned from Square API"
        )
    
    logger.info(f"Created payment link for user {user_email}, book {book_id}: {payment_link_url}")
    
    # Log the full URL for debugging (helps verify it's a proper payment link, not preview)
    logger.debug(f"Payment link URL format: {payment_link_url}")
    if "square.link" in payment_link_url:
        logger.info("✓ Valid Square payment link URL format")
    else:
        logger.warning(f"⚠ Payment link URL doesn't match expected format: {payment_link_url}")
    
    return payment_link_url


