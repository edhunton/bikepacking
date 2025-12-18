import { useState } from "react";
import Signup from "./Signup";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export default function Login({ onLogin, currentUser }) {
  const [showSignup, setShowSignup] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/api/v1/users/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Login failed");
      }
      const data = await res.json();
      const token = data.access_token;
      localStorage.setItem("authToken", token);

      // Optionally load current user
      const meRes = await fetch(`${API_BASE}/api/v1/users/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      let user = null;
      if (meRes.ok) {
        user = await meRes.json();
      }

      onLogin && onLogin({ token, user });
      setPassword("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("authToken");
    onLogin && onLogin(null);
  };

  if (showSignup) {
    return (
      <div className="bg-slate-900 text-slate-100 py-4">
        <div className="max-w-md mx-auto">
          <Signup
            onSignupSuccess={(authData) => {
              onLogin && onLogin(authData);
              setShowSignup(false);
            }}
            onCancel={() => setShowSignup(false)}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-end gap-4 px-6 py-2 bg-slate-900 text-slate-100">
      {currentUser ? (
        <>
          <span className="text-sm">
            Signed in as <span className="font-semibold">{currentUser.email}</span> (
            <span className="uppercase text-xs">{currentUser.role}</span>)
          </span>
          <button
            type="button"
            onClick={handleLogout}
            className="px-3 py-1 text-xs font-medium rounded bg-slate-700 hover:bg-slate-600"
          >
            Log out
          </button>
        </>
      ) : (
        <form onSubmit={handleSubmit} className="flex items-center gap-2 text-xs">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            className="px-2 py-1 rounded border border-slate-600 bg-slate-800 text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-sky-500"
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            className="px-2 py-1 rounded border border-slate-600 bg-slate-800 text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-sky-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-3 py-1 rounded bg-sky-600 hover:bg-sky-500 disabled:opacity-60"
          >
            {loading ? "…" : "Log in"}
          </button>
          {error && <span className="text-red-400 ml-2">{error}</span>}
          <button
            type="button"
            onClick={() => setShowSignup(true)}
            className="px-3 py-1 text-xs rounded border border-slate-600 hover:bg-slate-800"
          >
            Sign up
          </button>
        </form>
      )}
    </div>
  );
}



