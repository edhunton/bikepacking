export default function Book({ book }) {
  const { id, title, author, published_at, isbn, cover_url, thumbnail } = book;

  // Use cover_url, thumbnail, or a placeholder
  const imageUrl = cover_url || thumbnail || "/images/book-placeholder.jpg";

  // Handle buy button click
  const handleBuyClick = () => {
    // You can customize this URL based on your needs
    if (isbn) {
      // Search on Amazon or other bookstores using ISBN
      window.open(`https://www.amazon.com/s?k=${isbn}`, "_blank");
    } else {
      // Fallback search by title
      window.open(`https://www.amazon.com/s?k=${encodeURIComponent(title)}`, "_blank");
    }
  };

  return (
    <div className="flex gap-4 p-4 border border-slate-200 rounded-lg bg-white hover:shadow-md transition-shadow">
      {/* Thumbnail - 640x432 aspect ratio (1.48:1) */}
      <div className="flex-shrink-0">
        <img
          src={`/images/books/${imageUrl}`}
          alt={`Cover of ${title}`}
          className="w-40 aspect-[432/640] object-cover rounded border border-slate-200"
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

        {/* Buy Button */}
        <button
          onClick={handleBuyClick}
          className="self-start mt-4 px-4 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors text-sm font-medium"
        >
          Buy Now
        </button>
      </div>
    </div>
  );
}
