import { useState, useEffect } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export default function Routes() {
  const [showForm, setShowForm] = useState(false);
  const [editingRouteId, setEditingRouteId] = useState(null);
  const [routes, setRoutes] = useState([]);
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [formData, setFormData] = useState({
    title: "",
    gpx_url: "",
    gpx_file: null,
    difficulty: "",
    country: "",
    county: "",
    distance: "",
    ascent: "",
    descent: "",
    starting_station: "",
    ending_station: "",
    getting_there: "",
    bike_choice: "",
    guidebook_id: "",
  });

  // Load books for guidebook dropdown
  useEffect(() => {
    async function loadBooks() {
      try {
        const res = await fetch(`${API_BASE}/api/v1/books/`);
        if (res.ok) {
          const data = await res.json();
          setBooks(data);
        }
      } catch (err) {
        console.error("Error loading books:", err);
      }
    }
    loadBooks();
  }, []);

  // Load routes
  useEffect(() => {
    async function loadRoutes() {
      setLoading(true);
      try {
        const res = await fetch(`${API_BASE}/api/v1/routes/`);
        if (!res.ok) {
          throw new Error(`Request failed: ${res.status}`);
        }
        const data = await res.json();
        setRoutes(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadRoutes();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setFormData((prev) => ({
        ...prev,
        gpx_file: file,
        gpx_url: "", // Clear URL if file is selected
      }));
    }
  };

  const handleEdit = (route) => {
    setEditingRouteId(route.id);
    // Convert path to full URL if it's a relative path
    let gpxUrl = route.gpx_url || "";
    if (gpxUrl && !gpxUrl.startsWith('http')) {
      // If it's a relative path starting with /static, convert to full URL
      if (gpxUrl.startsWith('/static')) {
        gpxUrl = `http://localhost:5173${gpxUrl}`;
      } else {
        // Otherwise, assume it needs the prefix
        gpxUrl = `http://localhost:5173${gpxUrl.startsWith('/') ? '' : '/'}${gpxUrl}`;
      }
    }
    setFormData({
      title: route.title || "",
      gpx_url: gpxUrl,
      gpx_file: null,
      difficulty: route.difficulty || "",
      country: route.country || "",
      county: route.county || "",
      distance: route.distance ? route.distance.toString() : "",
      ascent: route.ascent ? route.ascent.toString() : "",
      descent: route.descent ? route.descent.toString() : "",
      starting_station: route.starting_station || "",
      ending_station: route.ending_station || "",
      getting_there: route.getting_there || "",
      bike_choice: route.bike_choice || "",
      guidebook_id: route.guidebook_id ? route.guidebook_id.toString() : "",
    });
    setShowForm(true);
    setError("");
    setSuccess("");
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingRouteId(null);
    setError("");
    setSuccess("");
    setFormData({
      title: "",
      gpx_url: "",
      gpx_file: null,
      difficulty: "",
      country: "",
      county: "",
      distance: "",
      ascent: "",
      descent: "",
      starting_station: "",
      ending_station: "",
      getting_there: "",
      bike_choice: "",
      guidebook_id: "",
    });
    const fileInput = document.getElementById("gpx_file");
    if (fileInput) fileInput.value = "";
  };

  const handleDelete = async (routeId, routeTitle) => {
    if (!confirm(`Are you sure you want to delete "${routeTitle}"? This action cannot be undone.`)) {
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const res = await fetch(`${API_BASE}/api/v1/routes/${routeId}`, {
        method: "DELETE",
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || `Request failed: ${res.status}`);
      }

      const result = await res.json();
      
      // Remove the route from the list
      setRoutes((prev) => prev.filter((route) => route.id !== routeId));
      setSuccess(result.message || `Route "${routeTitle}" deleted successfully!`);
      
      // Clear success message after a delay
      setTimeout(() => {
        setSuccess("");
      }, 3000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      let gpxUrl = formData.gpx_url;

      // If a file was uploaded, upload it first
      if (formData.gpx_file) {
        const formDataUpload = new FormData();
        formDataUpload.append("file", formData.gpx_file);

        const uploadRes = await fetch(`${API_BASE}/api/v1/routes/upload-gpx`, {
          method: "POST",
          body: formDataUpload,
        });

        if (!uploadRes.ok) {
          const errorData = await uploadRes.json();
          throw new Error(errorData.detail || `File upload failed: ${uploadRes.status}`);
        }

        const uploadData = await uploadRes.json();
        gpxUrl = uploadData.url;
      }

      // Prepare data - convert empty strings to null for optional fields
      const submitData = {
        title: formData.title,
        gpx_url: gpxUrl || null,
        difficulty: formData.difficulty || null,
        country: formData.country || null,
        county: formData.county || null,
        distance: formData.distance ? parseFloat(formData.distance) : null,
        ascent: formData.ascent ? parseInt(formData.ascent, 10) : null,
        descent: formData.descent ? parseInt(formData.descent, 10) : null,
        starting_station: formData.starting_station || null,
        ending_station: formData.ending_station || null,
        getting_there: formData.getting_there || null,
        bike_choice: formData.bike_choice || null,
        guidebook_id: formData.guidebook_id ? parseInt(formData.guidebook_id, 10) : null,
      };

      let res;
      if (editingRouteId) {
        // Update existing route
        res = await fetch(`${API_BASE}/api/v1/routes/${editingRouteId}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(submitData),
        });
      } else {
        // Create new route
        res = await fetch(`${API_BASE}/api/v1/routes/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(submitData),
        });
      }

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || `Request failed: ${res.status}`);
      }

      const updatedRoute = await res.json();
      
      if (editingRouteId) {
        // Update the route in the list
        setRoutes((prev) =>
          prev.map((route) => (route.id === editingRouteId ? updatedRoute : route))
        );
        setSuccess(`Route "${updatedRoute.title}" updated successfully!`);
      } else {
        // Add new route to the list
        setRoutes((prev) => [...prev, updatedRoute]);
        setSuccess(`Route "${updatedRoute.title}" created successfully!`);
      }
      
      // Reset form
      setFormData({
        title: "",
        gpx_url: "",
        gpx_file: null,
        difficulty: "",
        country: "",
        county: "",
        distance: "",
        ascent: "",
        descent: "",
        starting_station: "",
        ending_station: "",
        getting_there: "",
        bike_choice: "",
        guidebook_id: "",
      });
      
      // Reset file input
      const fileInput = document.getElementById("gpx_file");
      if (fileInput) fileInput.value = "";
      
      // Hide form after a delay
      setTimeout(() => {
        setShowForm(false);
        setEditingRouteId(null);
        setSuccess("");
      }, 2000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatDistance = (km) => {
    if (!km) return "N/A";
    return `${km.toFixed(1)} km`;
  };

  const formatElevation = (meters) => {
    if (!meters) return "N/A";
    return `${meters.toLocaleString()} m`;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-slate-900">Routes</h2>
        <button
          onClick={() => {
            if (showForm) {
              handleCancel();
            } else {
              setShowForm(true);
              setEditingRouteId(null);
            }
          }}
          className="px-4 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors"
        >
          {showForm ? "Cancel" : "Add New Route"}
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl p-6 shadow-lg border border-slate-200">
          <h3 className="text-xl font-semibold text-slate-900 mb-4">
            {editingRouteId ? "Edit Route" : "Add New Route"}
          </h3>
          
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-800">
              {error}
            </div>
          )}
          
          {success && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-800">
              {success}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Title - Required */}
              <div className="md:col-span-2">
                <label htmlFor="title" className="block text-sm font-medium text-slate-700 mb-1">
                  Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="title"
                  name="title"
                  required
                  value={formData.title}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                  placeholder="e.g., King Alfred's Way"
                />
              </div>

              {/* GPX File Upload */}
              <div className="md:col-span-2">
                <label htmlFor="gpx_file" className="block text-sm font-medium text-slate-700 mb-1">
                  GPX File
                </label>
                <input
                  type="file"
                  id="gpx_file"
                  name="gpx_file"
                  accept=".gpx"
                  onChange={handleFileChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-sky-50 file:text-sky-700 hover:file:bg-sky-100"
                />
                {formData.gpx_file && (
                  <p className="mt-1 text-sm text-slate-600">
                    Selected: {formData.gpx_file.name}
                  </p>
                )}
              </div>

              {/* GPX URL (alternative) */}
              <div className="md:col-span-2">
                <label htmlFor="gpx_url" className="block text-sm font-medium text-slate-700 mb-1">
                  Or GPX File URL (if not uploading)
                </label>
                <input
                  type="text"
                  id="gpx_url"
                  name="gpx_url"
                  value={formData.gpx_url}
                  onChange={handleInputChange}
                  disabled={!!formData.gpx_file}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 disabled:bg-slate-100 disabled:cursor-not-allowed"
                  placeholder="http://localhost:5173/static/gpx/route.gpx or https://example.com/route.gpx"
                />
              </div>

              {/* Difficulty */}
              <div>
                <label htmlFor="difficulty" className="block text-sm font-medium text-slate-700 mb-1">
                  Difficulty
                </label>
                <select
                  id="difficulty"
                  name="difficulty"
                  value={formData.difficulty}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                >
                  <option value="">Select difficulty</option>
                  <option value="Easy">Easy</option>
                  <option value="Moderate">Moderate</option>
                  <option value="Hard">Hard</option>
                  <option value="Very Hard">Very Hard</option>
                </select>
              </div>

              {/* Guidebook */}
              <div>
                <label htmlFor="guidebook_id" className="block text-sm font-medium text-slate-700 mb-1">
                  Guidebook
                </label>
                <select
                  id="guidebook_id"
                  name="guidebook_id"
                  value={formData.guidebook_id}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                >
                  <option value="">None (standalone route)</option>
                  {books.map((book) => (
                    <option key={book.id} value={book.id}>
                      {book.title}
                    </option>
                  ))}
                </select>
              </div>

              {/* Country */}
              <div>
                <label htmlFor="country" className="block text-sm font-medium text-slate-700 mb-1">
                  Country
                </label>
                <input
                  type="text"
                  id="country"
                  name="country"
                  value={formData.country}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                  placeholder="e.g., UK"
                />
              </div>

              {/* County */}
              <div>
                <label htmlFor="county" className="block text-sm font-medium text-slate-700 mb-1">
                  County/Region
                </label>
                <input
                  type="text"
                  id="county"
                  name="county"
                  value={formData.county}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                  placeholder="e.g., Hampshire"
                />
              </div>

              {/* Distance */}
              <div>
                <label htmlFor="distance" className="block text-sm font-medium text-slate-700 mb-1">
                  Distance (km)
                </label>
                <input
                  type="number"
                  id="distance"
                  name="distance"
                  step="0.1"
                  min="0"
                  value={formData.distance}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                  placeholder="e.g., 350.5"
                />
              </div>

              {/* Ascent */}
              <div>
                <label htmlFor="ascent" className="block text-sm font-medium text-slate-700 mb-1">
                  Ascent (meters)
                </label>
                <input
                  type="number"
                  id="ascent"
                  name="ascent"
                  min="0"
                  value={formData.ascent}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                  placeholder="e.g., 4500"
                />
              </div>

              {/* Descent */}
              <div>
                <label htmlFor="descent" className="block text-sm font-medium text-slate-700 mb-1">
                  Descent (meters)
                </label>
                <input
                  type="number"
                  id="descent"
                  name="descent"
                  min="0"
                  value={formData.descent}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                  placeholder="e.g., 4500"
                />
              </div>

              {/* Starting Station */}
              <div>
                <label htmlFor="starting_station" className="block text-sm font-medium text-slate-700 mb-1">
                  Starting Station
                </label>
                <input
                  type="text"
                  id="starting_station"
                  name="starting_station"
                  value={formData.starting_station}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                  placeholder="e.g., Winchester Station"
                />
              </div>

              {/* Ending Station */}
              <div>
                <label htmlFor="ending_station" className="block text-sm font-medium text-slate-700 mb-1">
                  Ending Station
                </label>
                <input
                  type="text"
                  id="ending_station"
                  name="ending_station"
                  value={formData.ending_station}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                  placeholder="e.g., Winchester Station"
                />
              </div>
            </div>

            {/* Getting There */}
            <div>
              <label htmlFor="getting_there" className="block text-sm font-medium text-slate-700 mb-1">
                Getting There
              </label>
              <textarea
                id="getting_there"
                name="getting_there"
                rows="3"
                value={formData.getting_there}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                placeholder="Instructions on how to get to the starting point..."
              />
            </div>

            {/* Bike Choice */}
            <div>
              <label htmlFor="bike_choice" className="block text-sm font-medium text-slate-700 mb-1">
                Bike Choice
              </label>
              <select
                id="bike_choice"
                name="bike_choice"
                value={formData.bike_choice}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
              >
                <option value="">Select bike type</option>
                <option value="MTB">MTB</option>
                <option value="Gravel">Gravel</option>
                <option value="Endurance">Endurance</option>
                <option value="Road">Road</option>
              </select>
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading
                  ? editingRouteId
                    ? "Updating..."
                    : "Creating..."
                  : editingRouteId
                  ? "Update Route"
                  : "Create Route"}
              </button>
              <button
                type="button"
                onClick={handleCancel}
                className="px-6 py-2 bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Routes List */}
      <div className="bg-white rounded-xl p-6 shadow-lg border border-slate-200">
        <h3 className="text-xl font-semibold text-slate-900 mb-4">
          All Routes ({routes.length})
        </h3>

        {loading && !showForm && (
          <div className="text-center py-8 text-slate-600">Loading routes...</div>
        )}

        {!loading && routes.length === 0 && (
          <div className="text-center py-8 text-slate-600">
            No routes yet. Click "Add New Route" to get started!
          </div>
        )}

        {routes.length > 0 && (
          <div className="space-y-4">
            {routes.map((route) => (
              <div
                key={route.id}
                className="border border-slate-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-lg font-semibold text-slate-900">
                        {route.title}
                      </h4>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEdit(route)}
                          className="px-3 py-1.5 text-sm bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(route.id, route.title)}
                          disabled={loading}
                          className="px-3 py-1.5 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-slate-600">
                      {route.difficulty && (
                        <div>
                          <span className="font-medium">Difficulty:</span> {route.difficulty}
                        </div>
                      )}
                      {route.distance && (
                        <div>
                          <span className="font-medium">Distance:</span> {formatDistance(route.distance)}
                        </div>
                      )}
                      {route.ascent && (
                        <div>
                          <span className="font-medium">Ascent:</span> {formatElevation(route.ascent)}
                        </div>
                      )}
                      {route.country && (
                        <div>
                          <span className="font-medium">Country:</span> {route.country}
                        </div>
                      )}
                      {route.county && (
                        <div>
                          <span className="font-medium">County:</span> {route.county}
                        </div>
                      )}
                      {route.starting_station && (
                        <div>
                          <span className="font-medium">Start:</span> {route.starting_station}
                        </div>
                      )}
                      {route.ending_station && (
                        <div>
                          <span className="font-medium">End:</span> {route.ending_station}
                        </div>
                      )}
                      {route.gpx_url && (
                        <div>
                          <a
                            href={route.gpx_url.startsWith('http') ? route.gpx_url : `${API_BASE}${route.gpx_url}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sky-600 hover:text-sky-700"
                            download
                          >
                            Download GPX →
                          </a>
                        </div>
                      )}
                    </div>
                    {route.getting_there && (
                      <div className="mt-3 text-sm text-slate-600">
                        <span className="font-medium">Getting There:</span> {route.getting_there}
                      </div>
                    )}
                    {route.bike_choice && (
                      <div className="mt-2 text-sm text-slate-600">
                        <span className="font-medium">Bike Choice:</span> {route.bike_choice}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
