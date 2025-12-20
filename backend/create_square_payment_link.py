#!/usr/bin/env python3
"""
Create a Square Payment Link with metadata for book purchases.

This script creates a Square Payment Link that includes:
- buyer_email (for user identification)
- metadata.book_id (for book identification)

Usage:
    python create_square_payment_link.py --book-id 1 --email user@example.com --price 999

Or use environment variables for configuration.
"""
import os
import sys
import argparse
import uuid
from pathlib import Path

try:
    from square.client import Client
except ImportError:
    print("ERROR: squareup package not installed.")
    print("Install it with: pip install squareup")
    sys.exit(1)


def get_square_client(access_token: str = None, environment: str = None):
    """Create and return a Square API client."""
    access_token = access_token or os.getenv("SQUARE_ACCESS_TOKEN")
    environment = environment or os.getenv("SQUARE_ENVIRONMENT", "sandbox")
    
    if not access_token:
        print("ERROR: SQUARE_ACCESS_TOKEN not set.")
        print("Set it as environment variable or pass --access-token")
        print("Get your access token from: https://developer.squareup.com/apps")
        sys.exit(1)
    
    if environment not in ["sandbox", "production"]:
        print(f"ERROR: Invalid environment '{environment}'. Use 'sandbox' or 'production'")
        sys.exit(1)
    
    return Client(
        access_token=access_token,
        environment=environment
    )


def create_payment_link(
    client: Client,
    book_id: int,
    book_title: str,
    price_cents: int,
    currency: str,
    buyer_email: str,
    location_id: str = None
):
    """
    Create a Square Payment Link with metadata.
    
    Args:
        client: Square API client
        book_id: Book ID from your database
        book_title: Book title for display
        price_cents: Price in smallest currency unit (e.g., cents)
        currency: Currency code (e.g., 'GBP', 'USD')
        buyer_email: Buyer's email address
        location_id: Square location ID (optional, uses first location if not provided)
    
    Returns:
        Payment link URL or None if failed
    """
    # Get location ID if not provided
    if not location_id:
        locations_result = client.locations.list_locations()
        if not locations_result.is_success():
            print(f"ERROR: Failed to get locations: {locations_result.errors}")
            return None
        
        locations = locations_result.body.get("locations", [])
        if not locations:
            print("ERROR: No Square locations found. Create a location in Square Dashboard.")
            return None
        
        location_id = locations[0]["id"]
        print(f"Using location: {locations[0].get('name', location_id)}")
    
    # Create payment link request
    payment_link_request = {
        "idempotency_key": str(uuid.uuid4()),
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
            "buyer_email": buyer_email,  # ← Important: Links payment to user
        },
        "metadata": {
            "book_id": str(book_id)  # ← Important: Links payment to book
        }
    }
    
    # Create the payment link
    result = client.checkout.create_payment_link(body=payment_link_request)
    
    if not result.is_success():
        print(f"ERROR: Failed to create payment link:")
        for error in result.errors:
            print(f"  - {error.get('category', 'ERROR')}: {error.get('detail', 'Unknown error')}")
        return None
    
    payment_link = result.body.get("payment_link", {})
    payment_link_url = payment_link.get("url")
    payment_link_id = payment_link.get("id")
    
    print(f"\n✅ Payment link created successfully!")
    print(f"   Payment Link ID: {payment_link_id}")
    print(f"   URL: {payment_link_url}")
    print(f"\n📋 Metadata included:")
    print(f"   - book_id: {book_id}")
    print(f"   - buyer_email: {buyer_email}")
    
    return payment_link_url


def main():
    parser = argparse.ArgumentParser(
        description="Create a Square Payment Link with book purchase metadata",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python create_square_payment_link.py --book-id 1 --email user@example.com --price 999
  
  # With all options
  python create_square_payment_link.py \\
    --book-id 1 \\
    --book-title "Bikepacking Guide" \\
    --email user@example.com \\
    --price 1999 \\
    --currency GBP \\
    --location-id LOCATION_ID \\
    --environment production

Environment Variables:
  SQUARE_ACCESS_TOKEN    - Your Square access token (required)
  SQUARE_ENVIRONMENT     - 'sandbox' or 'production' (default: sandbox)
        """
    )
    
    parser.add_argument(
        "--book-id",
        type=int,
        required=True,
        help="Book ID from your database"
    )
    
    parser.add_argument(
        "--book-title",
        type=str,
        help="Book title (default: 'Book #{book_id}')"
    )
    
    parser.add_argument(
        "--email",
        "--buyer-email",
        dest="buyer_email",
        required=True,
        help="Buyer's email address (must match a user in your database)"
    )
    
    parser.add_argument(
        "--price",
        type=int,
        required=True,
        help="Price in smallest currency unit (e.g., 999 = £9.99 for GBP, $9.99 for USD)"
    )
    
    parser.add_argument(
        "--currency",
        type=str,
        default="GBP",
        help="Currency code (default: GBP)"
    )
    
    parser.add_argument(
        "--location-id",
        type=str,
        help="Square location ID (optional, uses first location if not provided)"
    )
    
    parser.add_argument(
        "--access-token",
        type=str,
        help="Square access token (or use SQUARE_ACCESS_TOKEN env var)"
    )
    
    parser.add_argument(
        "--environment",
        type=str,
        choices=["sandbox", "production"],
        help="Square environment (or use SQUARE_ENVIRONMENT env var, default: sandbox)"
    )
    
    args = parser.parse_args()
    
    # Set default book title if not provided
    book_title = args.book_title or f"Book #{args.book_id}"
    
    # Create Square client
    client = get_square_client(args.access_token, args.environment)
    
    # Create payment link
    url = create_payment_link(
        client=client,
        book_id=args.book_id,
        book_title=book_title,
        price_cents=args.price,
        currency=args.currency,
        buyer_email=args.buyer_email,
        location_id=args.location_id
    )
    
    if url:
        print(f"\n🔗 Share this link with the customer:")
        print(f"   {url}")
        print(f"\n💡 After payment, the webhook will automatically create a purchase record.")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())


