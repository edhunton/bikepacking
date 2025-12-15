export default function Book({ book, onEdit }) {
  const { title, author, published_at, isbn, cover_url, thumbnail, purchase_url } = book;

  // Use cover_url, thumbnail, or a placeholder
  const imageUrl = cover_url || thumbnail || "/images/book-placeholder.jpg";

  // Handle buy button click
  const handleBuyClick = () => {
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
        <div className="flex gap-2 mt-4">
          <button
            onClick={handleBuyClick}
            className="px-4 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors text-sm font-medium"
          >
            {purchase_url ? "Buy Now" : "Find Book"}
          </button>
          {onEdit && (
            <button
              onClick={() => onEdit(book)}
              className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors text-sm font-medium"
            >
              Edit
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
