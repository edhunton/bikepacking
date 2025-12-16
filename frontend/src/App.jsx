import { useEffect, useState } from "react";
import HeaderBanner from "./components/HeaderBanner";
import HorizontalMenu from "./components/HorizontalMenu";
import MainBody from "./components/MainBody";
import Login from "./components/Login";

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
  const [auth, setAuth] = useState(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("authToken") : null;
    return { token, user: null };
  });

  useEffect(() => {
    async function loadUser() {
      if (!auth.token) return;
      try {
        const res = await fetch(`${API_BASE}/api/v1/users/me`, {
          headers: {
            Authorization: `Bearer ${auth.token}`,
          },
        });
        if (res.ok) {
          const user = await res.json();
          setAuth((prev) => ({ ...prev, user }));
        }
      } catch {
        // ignore
      }
    }
    loadUser();
  }, [auth.token]);

  return (
    <div className="min-h-screen bg-slate-50">
      <HeaderBanner />
      <Login
        currentUser={auth.user}
        onLogin={(next) => {
          if (!next) {
            setAuth({ token: null, user: null });
          } else {
            setAuth(next);
          }
        }}
      />
      <HorizontalMenu
        activeSection={activeSection}
        onSectionChange={setActiveSection}
      />
      <MainBody
        activeSection={activeSection}
        setActiveSection={setActiveSection}
        books={books}
        loading={loading}
        error={error}
      />
    </div>
  );
}
