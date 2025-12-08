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
        <ul className="list-none p-0 m-0 flex flex-col gap-3">
          {books.map((book) => (
            <li
              key={book.id}
              className="p-4 border border-slate-200 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors"
            >
              <div>
                <div className="font-semibold mb-1 text-slate-900">
                  {book.title}
                </div>
                <div className="flex items-center gap-2 text-slate-600 text-sm">
                  <span>{book.author}</span>
                  {book.published_at && (
                    <>
                      <span className="text-slate-300" aria-hidden="true">
                        •
                      </span>
                      <span>{book.published_at}</span>
                    </>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
