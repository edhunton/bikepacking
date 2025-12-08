import { useEffect, useState } from "react";
import HeaderBanner from "./components/HeaderBanner";
import HorizontalMenu from "./components/HorizontalMenu";
import MainBody from "./components/MainBody";

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
  const [activeSection, setActiveSection] = useState("books");
  const { books, loading, error } = useBooks();

  return (
    <div className="min-h-screen bg-slate-50">
      <HeaderBanner />
      <HorizontalMenu
        activeSection={activeSection}
        onSectionChange={setActiveSection}
      />
      <MainBody
        activeSection={activeSection}
        books={books}
        loading={loading}
        error={error}
      />
    </div>
  );
}
