import { useEffect } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export default function Book({
  book,
  onEdit,
  onToggle,
  isExpanded,
  photos = [],
  photosLoading,
  photosError,
  onPhotoClick,
  currentUser,
  paymentLink = null,  // Pre-generated payment link
  paymentLinksLoading = false,  // Whether links are being loaded
  hasPurchased = false,  // Whether user has already purchased this book
}) {
  // Log payment link payload when it's set for this book
  useEffect(() => {
    if (paymentLink) {
      console.log(`[Book Component] Book ${book.id} (${book.title}) payment link payload:`, {
        bookId: book.id,
        bookTitle: book.title,
        paymentLink: paymentLink,
        userEmail: currentUser?.email
      });
    }
  }, [paymentLink, book.id, book.title, currentUser?.email]);
  const { title, subtitle, author, published_at, isbn, cover_url, thumbnail, purchase_url, amazon_link } = book;

  // Use cover_url, thumbnail, or a placeholder
  const imageUrl = cover_url || thumbnail || "/images/book-placeholder.jpg";

  // Handle buy button click - use pre-generated payment link if available
  const handleBuyClick = async (e) => {
    e.stopPropagation();
    
    // If user is logged in, try pre-generated payment link first
    if (currentUser) {
      // Use pre-generated link if available
      if (paymentLink) {
        console.log("[Buy Button Click] Using pre-generated payment link:", {
          bookId: book.id,
          bookTitle: book.title,
          paymentLink: paymentLink,
          userEmail: currentUser?.email
        });
        window.open(paymentLink, "_blank");
        return;
      }
      
      // If links are still loading, wait and try on-demand generation
      if (paymentLinksLoading) {
        // Wait a bit for links to load, then try on-demand
        setTimeout(() => {
          if (paymentLink) {
            window.open(paymentLink, "_blank");
          } else {
            generatePaymentLinkOnDemand();
          }
        }, 500);
        return;
      }
      
      // Fallback: generate payment link on-demand if pre-generation failed
      generatePaymentLinkOnDemand();
      return;
    }
    
    // Generate payment link on-demand (fallback function)
    async function generatePaymentLinkOnDemand() {
      try {
        const token = localStorage.getItem("authToken");
        const response = await fetch(`${API_BASE}/api/v1/books/${book.id}/payment-link`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();
          const paymentUrl = data.payment_link;
          console.log("Opening payment link (on-demand):", paymentUrl);
          window.open(paymentUrl, "_blank");
        } else {
          throw new Error(`Failed to create payment link: ${response.status}`);
        }
      } catch (error) {
        console.error("Error creating payment link:", error);
        alert("Failed to create payment link. Please try again.");
        // Fall through to static URL or Amazon fallback
      }
    }
    
    // Fallback to static purchase_url or Amazon (if user not logged in or payment link failed)
    if (purchase_url) {
      window.open(purchase_url, "_blank");
      return;
    }
    if (isbn) {
      window.open(`https://www.amazon.co.uk/s?k=${isbn}`, "_blank");
      return;
    }
    window.open(`https://www.amazon.co.uk/s?k=${encodeURIComponent(title)}`, "_blank");
  };

  // Handle review button click - link to Amazon reviews
  const handleReviewClick = () => {
    // If we have the full Amazon link, use it and append #customerReviews to go to reviews section
    if (amazon_link) {
      // Ensure the link ends with the ASIN, then append #customerReviews
      const reviewUrl = amazon_link.split('#')[0] + '#customerReviews';
      window.open(reviewUrl, "_blank");
      return;
    }
    // Fallback: Use Amazon search
    if (isbn) {
      window.open(`https://www.amazon.co.uk/s?k=${encodeURIComponent(isbn)}&i=stripbooks`, "_blank");
      return;
    }
    const searchQuery = author ? `${title} ${author}` : title;
    window.open(`https://www.amazon.co.uk/s?k=${encodeURIComponent(searchQuery)}&i=stripbooks`, "_blank");
  };

  return (
    <div
      id={`book-${book.id}`}
      className="p-4 border border-slate-200 rounded-lg bg-white hover:shadow-md transition-shadow cursor-pointer"
      onClick={onToggle}
    >
      <div className="flex gap-4">
        {/* Thumbnail - 640x432 aspect ratio (1.48:1) */}
        <div className="flex-shrink-0">
          <img
            src={`/images/books/${imageUrl}`}
            alt={`Cover of ${title}`}
            className="w-32 md:w-40 aspect-[432/640] object-cover rounded border border-slate-200"
            onError={(e) => {
              // Fallback to placeholder if image fails to load
              e.target.src = "/images/book-placeholder.jpg";
            }}
          />
        </div>

        {/* Content */}
        <div className="flex-1 flex flex-col justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-900 mb-1">
              {title}
            </h3>
            {subtitle && (
              <p className="text-slate-500 text-sm mb-2 italic">{subtitle}</p>
            )}
            {author && (
              <p className="text-slate-600 text-sm mb-2">By {author}</p>
            )}
            {published_at && (
              <p className="text-slate-500 text-xs mb-2">
                Published: {published_at}
              </p>
            )}
            {isbn && (
              <p className="text-slate-500 text-xs font-mono">ISBN: {isbn}</p>
            )}
          </div>

          {/* Buy / Edit Buttons */}
          <div className="flex gap-2 mt-4">
            <button
              onClick={handleBuyClick}
              className="px-4 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors text-sm font-medium"
            >
              {hasPurchased ? "Buy Again" : (purchase_url || currentUser ? "Buy Now" : "Find Book")}
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleReviewClick();
              }}
              className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors text-sm font-medium"
              title="Write a review on Amazon"
            >
              Write Review
            </button>
            {onEdit && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit(book);
                }}
                className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors text-sm font-medium"
              >
                Edit
              </button>
            )}
          </div>
        </div>
      </div>

      {isExpanded && (
        <div className="mt-4 space-y-2">
          {photosLoading && (
            <div className="text-sm text-slate-500">Loading photos...</div>
          )}
          {photosError && (
            <div className="text-sm text-red-600">Error: {photosError}</div>
          )}
          {!photosLoading && !photosError && photos.length === 0 && (
            <div className="text-sm text-slate-500">No photos yet.</div>
          )}
          {!photosLoading && photos.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {photos.map((p, index) => (
                <button
                  key={p.id}
                  type="button"
                  className="relative w-10 h-10 sm:w-12 sm:h-12"
                  onClick={(e) => {
                    e.stopPropagation();
                    onPhotoClick && onPhotoClick(index);
                  }}
                >
                  <img
                    src={p.thumbnail_url || p.photo_url}
                    alt={p.caption || `Photo ${p.id}`}
                    className="w-full h-full object-cover rounded border border-slate-200"
                    onError={(e) => (e.target.src = p.photo_url)}
                  />
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
