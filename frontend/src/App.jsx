import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

function useBooks() {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const res = await fetch(`${API_BASE}/api/v1/books/`);
        if (!res.ok) {
          throw new Error(`Request failed: ${res.status}`);
        }
        const data = await res.json();
        if (!cancelled) {
          setBooks(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return { books, loading, error };
}

export default function App() {
  const { books, loading, error } = useBooks();

  return (
    <main className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">Bikepacking API</p>
          <h1>Books</h1>
          <p className="subhead">
            Data served from the FastAPI backend via /api/v1/books.
          </p>
        </div>
      </header>

      <section className="card">
        <div className="card-header">
          <h2>Books</h2>
          {loading && <span className="pill">Loading</span>}
          {error && <span className="pill pill-error">Error</span>}
        </div>

        {error ? (
          <p className="error">Failed to load: {error}</p>
        ) : books.length === 0 && !loading ? (
          <p className="muted">No books found.</p>
        ) : (
          <ul className="list">
            {books.map((book) => (
              <li key={book.id} className="list-item">
                <div>
                  <div className="title">{book.title}</div>
                  <div className="meta">
                    <span>{book.author}</span>
                    {book.published_at && (
                      <>
                        <span className="dot" aria-hidden="true">
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
    </main>
  );
}
