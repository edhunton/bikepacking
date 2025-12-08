import Book from "./Book";

export default function Books({ books, loading, error }) {
  return (
    <section className="bg-white rounded-xl p-6 shadow-lg border border-slate-200">
      <div className="flex items-center gap-2 mb-4">
        <h2 className="text-2xl font-semibold text-slate-900">Books</h2>
        {loading && (
          <span className="inline-block px-2.5 py-1 rounded-full bg-sky-100 text-sky-600 text-xs">
            Loading
          </span>
        )}
        {error && (
          <span className="inline-block px-2.5 py-1 rounded-full bg-red-100 text-red-600 text-xs">
            Error
          </span>
        )}
      </div>

      {error ? (
        <p className="text-red-600 m-0">Failed to load: {error}</p>
      ) : books.length === 0 && !loading ? (
        <p className="text-slate-400 m-0">No books found.</p>
      ) : (
        <div className="flex flex-col gap-4">
          {books.map((book) => (
            <Book key={book.id} book={book} />
          ))}
        </div>
      )}
    </section>
  );
}
