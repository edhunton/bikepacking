import { useEffect, useState } from "react";
import Book from "./Book";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export default function Books({ books, loading, error }) {
  const [localBooks, setLocalBooks] = useState(books);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [formSuccess, setFormSuccess] = useState("");
  const [formData, setFormData] = useState({
    title: "",
    author: "",
    published_at: "",
    isbn: "",
    cover_url: "",
    purchase_url: "",
  });
  const [photoForm, setPhotoForm] = useState({
    book_id: "",
    caption: "",
    files: [],
  });
  const [photoStatus, setPhotoStatus] = useState({ loading: false, error: "", success: "" });

  useEffect(() => {
    setLocalBooks(books);
  }, [books]);

  const handleEdit = (book) => {
    setEditingId(book.id);
    setShowForm(true);
    setFormError("");
    setFormSuccess("");
    setFormData({
      title: book.title || "",
      author: book.author || "",
      published_at: book.published_at ? book.published_at.slice(0, 10) : "",
      isbn: book.isbn || "",
      cover_url: book.cover_url || "",
      purchase_url: book.purchase_url || "",
    });
    setTimeout(() => {
      const el = document.getElementById("book-edit-form");
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 0);
  };

  const handlePhotoChange = (e) => {
    const { name, value, files } = e.target;
    if (name === "file") {
      setPhotoForm((prev) => ({
        ...prev,
        files: files ? Array.from(files) : [],
      }));
    } else {
      setPhotoForm((prev) => ({ ...prev, [name]: value }));
    }
  };

  const handlePhotoSubmit = async (e) => {
    e.preventDefault();
    setPhotoStatus({ loading: true, error: "", success: "" });
    try {
      if (!photoForm.book_id) throw new Error("Select a book");
      if (!photoForm.files?.length) throw new Error("Choose one or more image files");

      // Upload each file sequentially so errors are clear
      for (const f of photoForm.files) {
        const fd = new FormData();
        fd.append("book_id", photoForm.book_id);
        fd.append("caption", photoForm.caption || "");
        fd.append("file", f);

        const res = await fetch(`${API_BASE}/api/v1/books/photos`, {
          method: "POST",
          body: fd,
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Upload failed: ${res.status}`);
        }
      }

      setPhotoStatus({ loading: false, error: "", success: "Photos uploaded" });
      setPhotoForm((prev) => ({ ...prev, files: [], caption: "" }));
      const fileInput = document.getElementById("book_photo_file");
      if (fileInput) fileInput.value = "";
    } catch (err) {
      setPhotoStatus({ loading: false, error: err.message, success: "" });
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!editingId) return;
    setSaving(true);
    setFormError("");
    setFormSuccess("");

    const payload = {
      title: formData.title || null,
      author: formData.author || null,
      published_at: formData.published_at || null,
      isbn: formData.isbn || null,
      cover_url: formData.cover_url || null,
      purchase_url: formData.purchase_url || null,
    };

    try {
      const res = await fetch(`${API_BASE}/api/v1/books/${editingId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Update failed: ${res.status}`);
      }
      const updated = await res.json();
      setLocalBooks((prev) =>
        prev.map((b) => (b.id === editingId ? updated : b))
      );
      setFormSuccess(`Updated "${updated.title}"`);
      setTimeout(() => {
        setShowForm(false);
        setEditingId(null);
        setFormSuccess("");
      }, 1500);
    } catch (err) {
      setFormError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="bg-white rounded-xl p-4 sm:p-6 shadow-lg border border-slate-200 space-y-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
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
        {editingId && (
          <button
            onClick={() => {
              setShowForm(false);
              setEditingId(null);
              setFormError("");
              setFormSuccess("");
            }}
            className="w-full sm:w-auto px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors"
          >
            Cancel Edit
          </button>
        )}
      </div>

      {showForm && (
        <div
          id="book-edit-form"
          className="border border-slate-200 rounded-lg p-4 bg-slate-50 space-y-3"
        >
          <h3 className="text-lg font-semibold text-slate-900">
            Edit Book Details
          </h3>
          {formError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {formError}
            </div>
          )}
          {formSuccess && (
            <div className="p-3 bg-green-50 border border-green-200 rounded text-green-700 text-sm">
              {formSuccess}
            </div>
          )}
          <form onSubmit={handleSubmit} className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Title *
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleInputChange}
                required
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Author
              </label>
              <input
                type="text"
                name="author"
                value={formData.author}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Published Date
              </label>
              <input
                type="date"
                name="published_at"
                value={formData.published_at}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                ISBN
              </label>
              <input
                type="text"
                name="isbn"
                value={formData.isbn}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Cover URL
              </label>
              <input
                type="text"
                name="cover_url"
                value={formData.cover_url}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:outline-none"
                placeholder="https://example.com/cover.jpg"
              />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Purchase URL
              </label>
              <input
                type="text"
                name="purchase_url"
                value={formData.purchase_url}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:outline-none"
                placeholder="https://square.link/..."
              />
            </div>
            <div className="sm:col-span-2 flex gap-2">
              <button
                type="submit"
                disabled={saving}
                className="px-4 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save Changes"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowForm(false);
                  setEditingId(null);
                  setFormError("");
                  setFormSuccess("");
                }}
                className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Photo upload */}
      <div className="border border-slate-200 rounded-lg p-4 bg-white space-y-3">
        <h3 className="text-lg font-semibold text-slate-900">Add Photo to a Book</h3>
        {photoStatus.error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            {photoStatus.error}
          </div>
        )}
        {photoStatus.success && (
          <div className="p-3 bg-green-50 border border-green-200 rounded text-green-700 text-sm">
            {photoStatus.success}
          </div>
        )}
        <form onSubmit={handlePhotoSubmit} className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-slate-700 mb-1">Book *</label>
            <select
              name="book_id"
              value={photoForm.book_id}
              onChange={handlePhotoChange}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:outline-none"
              required
            >
              <option value="">Select a book</option>
              {localBooks.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.title}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Caption</label>
            <input
              type="text"
              name="caption"
              value={photoForm.caption}
              onChange={handlePhotoChange}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:outline-none"
              placeholder="Optional caption"
            />
          </div>
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-slate-700 mb-1">Photos *</label>
            <input
              type="file"
              id="book_photo_file"
              name="file"
              accept=".jpg,.jpeg,.png,.webp"
              multiple
              onChange={handlePhotoChange}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:outline-none file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-sky-50 file:text-sky-700 hover:file:bg-sky-100"
              required
            />
            {photoForm.files?.length > 0 && (
              <p className="mt-1 text-xs text-slate-600">
                Selected {photoForm.files.length} file{photoForm.files.length > 1 ? "s" : ""}
              </p>
            )}
          </div>
          <div className="sm:col-span-2 flex gap-2">
            <button
              type="submit"
              disabled={photoStatus.loading}
              className="px-4 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors disabled:opacity-50"
            >
              {photoStatus.loading ? "Uploading..." : "Upload Photo"}
            </button>
          </div>
        </form>
      </div>

      {error ? (
        <p className="text-red-600 m-0">Failed to load: {error}</p>
      ) : localBooks.length === 0 && !loading ? (
        <p className="text-slate-400 m-0">No books found.</p>
      ) : (
        <div className="flex flex-col gap-4">
          {localBooks.map((book) => (
            <Book key={book.id} book={book} onEdit={handleEdit} />
          ))}
        </div>
      )}
    </section>
  );
}
