# Payment Link Strategy: Static vs Dynamic

## Recommendation: **Dynamic Links** ✅

For proper webhook integration with user identification, you should create payment links **dynamically** when a user wants to purchase.

## Static Links (One-Time Creation) ❌

**How it works:**
- Create payment link once per book
- Store URL in `books.purchase_url` database field
- Share the same link with all users

**Problems:**
- ❌ Can't include `buyer_email` (would need to know all users upfront)
- ❌ Webhook can't identify which user made the payment
- ❌ No user-specific tracking
- ❌ Less secure (anyone with link can pay, no user verification)

## Dynamic Links (On-Demand Creation) ✅

**How it works:**
- Create payment link when user clicks "Purchase"
- Include logged-in user's email
- Link expires after use or time limit

**Benefits:**
- ✅ `buyer_email` pre-filled with logged-in user's email
- ✅ Webhook can identify user automatically
- ✅ User must be logged in to get link
- ✅ Better security and tracking
- ✅ Can include user-specific metadata if needed

## Implementation

### Option A: API Endpoint (Recommended)

Create an endpoint that generates payment links on-demand:

```python
@router.get("/{book_id}/payment-link")
def get_payment_link(
    book_id: int,
    current_user: UserInDB = Depends(get_current_user)
) -> dict:
    """Generate a Square payment link for the logged-in user."""
    # Get book details
    book = get_book_by_id(book_id)
    
    # Create dynamic payment link with user's email
    payment_link_url = create_payment_link_for_user(
        user_email=current_user.email,
        book_id=book_id,
        book_title=book.title,
        price_cents=book.price_cents or 999,  # From book model
        currency="GBP"
    )
    
    return {
        "payment_link": payment_link_url,
        "book_id": book_id
    }
```

**Frontend usage:**
```javascript
// When user clicks "Purchase" button
const response = await fetch(`/api/v1/books/${bookId}/payment-link`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { payment_link } = await response.json();
window.open(payment_link, '_blank');
```

### Option B: Keep Static Links + Manual Association

If you prefer static links, you'd need to:
1. Create links without `buyer_email`
2. Have users enter email during Square checkout
3. Manually match payments to users (less reliable)

**Not recommended** - dynamic is cleaner.

## Flow Comparison

### Static Link Flow:
```
1. Admin creates link → Store in DB
2. User visits page → Sees static link
3. User clicks → Goes to Square
4. User enters email → Completes payment
5. Webhook receives payment → ❌ Can't match to user easily
```

### Dynamic Link Flow:
```
1. User logs in → Views books
2. User clicks "Purchase" → API creates link with user's email
3. User redirected → Pre-filled email in Square
4. User completes payment → Webhook receives payment
5. Webhook finds user by email → ✅ Creates purchase automatically
```

## Code Example

See `backend/api/v1/books/payment_links.py` for the dynamic link creation function.

Add to `backend/api/v1/books/router.py`:

```python
from .payment_links import create_payment_link_for_user
from .controller import get_book_by_id  # You'll need this function

@router.get("/{book_id}/payment-link")
def get_payment_link(
    book_id: int,
    current_user: UserInDB = Depends(get_current_user)
) -> dict:
    """Get a Square payment link for purchasing this book."""
    # Check if already purchased
    if has_user_purchased_book(current_user.id, book_id):
        raise HTTPException(
            status_code=400,
            detail="You have already purchased this book"
        )
    
    # Get book details (you may need to add get_book_by_id function)
    books = get_all_books()
    book = next((b for b in books if b.id == book_id), None)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Create dynamic payment link
    try:
        payment_link = create_payment_link_for_user(
            user_email=current_user.email,
            book_id=book_id,
            book_title=book.title,
            price_cents=getattr(book, 'price_cents', 999),  # Adjust based on your model
            currency="GBP"
        )
        return {"payment_link": payment_link}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Recommendation

**Use dynamic links** - They're more secure, provide better user experience, and enable automatic webhook processing.

The script (`create_square_payment_link.py`) is still useful for:
- Testing
- Creating one-off payment links
- Admin operations

But for production user purchases, use the API endpoint approach.


