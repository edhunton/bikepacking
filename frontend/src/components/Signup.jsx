import { useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export default function Signup({ onSignupSuccess, onCancel }) {
  const [formData, setFormData] = useState({
    name: "",
    age: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");

    // Validation
    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match");
      setLoading(false);
      return;
    }

    if (formData.password.length < 6) {
      setError("Password must be at least 6 characters");
      setLoading(false);
      return;
    }

    try {
      const payload = {
        first_name: formData.firstName,
        last_name: formData.lastName,
        email: formData.email,
        password: formData.password,
        role: "user", // Default role
      };

      // Age is optional
      if (formData.age) {
        const ageNum = parseInt(formData.age, 10);
        if (!isNaN(ageNum) && ageNum > 0) {
          payload.age = ageNum;
        }
      }

      const res = await fetch(`${API_BASE}/api/v1/users/signup`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Signup failed");
      }

      const user = await res.json();
      setSuccess(`Account created successfully! Welcome, ${user.name}.`);
      
      // Auto-login after signup
      const loginRes = await fetch(`${API_BASE}/api/v1/users/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
        }),
      });

      if (loginRes.ok) {
        const tokenData = await loginRes.json();
        localStorage.setItem("authToken", tokenData.access_token);

        // Fetch user info
        const meRes = await fetch(`${API_BASE}/api/v1/users/me`, {
          headers: {
            Authorization: `Bearer ${tokenData.access_token}`,
          },
        });
        let userInfo = null;
        if (meRes.ok) {
          userInfo = await meRes.json();
        }

        if (onSignupSuccess) {
          onSignupSuccess({ token: tokenData.access_token, user: userInfo });
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto p-6 bg-slate-800 rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold text-slate-100 mb-6">Create Account</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="firstName" className="block text-sm font-medium text-slate-200 mb-1">
            First Name *
          </label>
          <input
            type="text"
            id="firstName"
            name="firstName"
            value={formData.firstName}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-slate-600 bg-slate-700 text-slate-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
        </div>

        <div>
          <label htmlFor="lastName" className="block text-sm font-medium text-slate-200 mb-1">
            Last Name *
          </label>
          <input
            type="text"
            id="lastName"
            name="lastName"
            value={formData.lastName}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-slate-600 bg-slate-700 text-slate-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
        </div>

        <div>
          <label htmlFor="email" className="block text-sm font-medium text-slate-200 mb-1">
            Email *
          </label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-slate-600 bg-slate-700 text-slate-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
        </div>

        <div>
          <label htmlFor="age" className="block text-sm font-medium text-slate-200 mb-1">
            Age (optional)
          </label>
          <select
            id="age"
            name="age"
            value={formData.age}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-slate-600 bg-slate-700 text-slate-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="">Select age</option>
            {Array.from({ length: 83 }, (_, i) => i + 18).map((age) => (
              <option key={age} value={age}>
                {age}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium text-slate-200 mb-1">
            Password *
          </label>
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            required
            minLength="6"
            className="w-full px-3 py-2 border border-slate-600 bg-slate-700 text-slate-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
          <p className="text-xs text-slate-400 mt-1">At least 6 characters</p>
        </div>

        <div>
          <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate-200 mb-1">
            Confirm Password *
          </label>
          <input
            type="password"
            id="confirmPassword"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-slate-600 bg-slate-700 text-slate-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {success && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
            {success}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full px-4 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 disabled:opacity-60 disabled:cursor-not-allowed font-medium"
        >
          {loading ? "Creating Account..." : "Sign Up"}
        </button>
      </form>

      <p className="mt-4 text-sm text-center text-slate-300">
        Already have an account?{" "}
        <button
          type="button"
          onClick={onCancel}
          className="text-sky-400 hover:text-sky-300 font-medium"
        >
          Log in
        </button>
      </p>
    </div>
  );
}
