import { useState, useEffect, useRef } from "react";
import RouteMap from "./RouteMap";
import RouteDetailPanel from "./RouteDetailPanel";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export default function Routes({ books: booksProp = [], onNavigateToBook, currentUser }) {
  const isAdmin = currentUser?.role === "admin";
  const [showForm, setShowForm] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [importSource, setImportSource] = useState("strava"); // "strava" or "komoot"
  const [importLoading, setImportLoading] = useState(false);
  const [importError, setImportError] = useState("");
  const [stravaActivities, setStravaActivities] = useState([]);
  const [komootTours, setKomootTours] = useState([]);
  const [editingRouteId, setEditingRouteId] = useState(null);
  const [routes, setRoutes] = useState([]);
  const [books, setBooks] = useState(booksProp);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const generatingThumbnails = useRef(new Set()); // Track routes currently generating thumbnails
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [purchasedBookIds, setPurchasedBookIds] = useState(new Set());
  const [formData, setFormData] = useState({
    title: "",
    gpx_url: "",
    gpx_file: null,
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
    min_time: "",
    max_time: "",
    off_road_distance: "",
    off_road_percentage: "",
    grade: "",
  });

  // Load books for guidebook dropdown (if not provided as prop)
  useEffect(() => {
    if (booksProp.length > 0) {
      setBooks(booksProp);
      return;
    }
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
  }, [booksProp]);

  // Fetch purchased books to populate purchasedBookIds
  useEffect(() => {
    const fetchPurchasedBooks = async () => {
      if (!currentUser?.id) {
        setPurchasedBookIds(new Set());
        return;
      }

      try {
        const token = localStorage.getItem('authToken');
        if (!token) {
          setPurchasedBookIds(new Set());
          return;
        }

        // Get all unique guidebook_ids from routes
        const guidebookIds = [...new Set(routes.map(r => r.guidebook_id).filter(Boolean))];
        if (guidebookIds.length === 0) {
          return;
        }

        // Check purchase status for each guidebook
        const purchasedSet = new Set();
        await Promise.all(
          guidebookIds.map(async (bookId) => {
            try {
              const res = await fetch(`${API_BASE}/api/v1/books/${bookId}/purchased`, {
                headers: {
                  'Authorization': `Bearer ${token}`
                }
              });
              if (res.ok) {
                const data = await res.json();
                if (data.purchased === true) {
                  purchasedSet.add(bookId);
                }
              }
            } catch (err) {
              console.error(`Error checking purchase for book ${bookId}:`, err);
            }
          })
        );

        setPurchasedBookIds(purchasedSet);
      } catch (error) {
        console.error('Error fetching purchased books:', error);
        setPurchasedBookIds(new Set());
      }
    };

    fetchPurchasedBooks();
  }, [currentUser?.id, routes]);

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
        
        // Automatically generate thumbnails for routes that don't have them
        data.forEach(route => {
          if (route.gpx_url && !route.thumbnail_url && !generatingThumbnails.current.has(route.id)) {
            generatingThumbnails.current.add(route.id);
            // Generate thumbnail silently in the background
            fetch(`${API_BASE}/api/v1/routes/${route.id}/generate-thumbnail`, {
              method: 'POST'
            })
              .then(() => {
                // Reload routes to get updated thumbnail
                return fetch(`${API_BASE}/api/v1/routes/`);
              })
              .then(res => res.ok ? res.json() : null)
              .then(data => {
                if (data) {
                  setRoutes(data);
                }
                generatingThumbnails.current.delete(route.id);
              })
              .catch(err => {
                console.error("Error generating thumbnail:", err);
                generatingThumbnails.current.delete(route.id);
                // Silently fail - user still sees the map
              });
          }
        });
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
      min_time: route.min_time ? route.min_time.toString() : "",
      max_time: route.max_time ? route.max_time.toString() : "",
      off_road_distance: route.off_road_distance ? route.off_road_distance.toString() : "",
      off_road_percentage: route.off_road_percentage ? route.off_road_percentage.toString() : "",
      grade: route.grade || "",
      description: route.description || "",
      strava_activities: route.strava_activities || "",
      google_mymap_url: route.google_mymap_url || "",
      komoot_collections: route.komoot_collections || "",
    });
    setShowForm(true);
    setError("");
    setSuccess("");
    
    // Scroll to the form at the top
    setTimeout(() => {
      const formElement = document.getElementById('route-edit-form');
      if (formElement) {
        formElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
      } else {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    }, 0);
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
      min_time: "",
      max_time: "",
      off_road_distance: "",
      off_road_percentage: "",
      grade: "",
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
        min_time: formData.min_time ? parseFloat(formData.min_time) : null,
        max_time: formData.max_time ? parseFloat(formData.max_time) : null,
        off_road_distance: formData.off_road_distance ? parseFloat(formData.off_road_distance) : null,
        off_road_percentage: formData.off_road_percentage ? parseFloat(formData.off_road_percentage) : null,
        grade: formData.grade || null,
        description: formData.description || null,
        strava_activities: formData.strava_activities || null,
        google_mymap_url: formData.google_mymap_url || null,
        komoot_collections: formData.komoot_collections || null,
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
      
      // If route has a GPX file, generate thumbnail in the background
      if (gpxUrl && updatedRoute.id) {
        // Generate thumbnail asynchronously (don't wait for it)
        fetch(`${API_BASE}/api/v1/routes/${updatedRoute.id}/generate-thumbnail`, {
          method: 'POST'
        }).then(() => {
          // Reload routes after thumbnail is generated
          fetch(`${API_BASE}/api/v1/routes/`)
            .then(res => res.ok ? res.json() : null)
            .then(data => data && setRoutes(data))
            .catch(err => console.error("Error reloading routes:", err));
        }).catch(err => {
          console.error("Error generating thumbnail:", err);
          // Don't show error to user, thumbnail generation is optional
        });
      }
      
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
      min_time: "",
      max_time: "",
      off_road_distance: "",
        off_road_percentage: "",
        grade: "",
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

  const formatDistance = (distance) => {
    if (!distance) return "N/A";
    // If distance is > 1000, assume it's in meters, otherwise assume km
    const km = distance > 1000 ? distance / 1000 : distance;
    return `${km.toFixed(1)} km`;
  };

  const getGradeIndicator = (grade) => {
    if (!grade) return null;
    const gradeLower = grade.toLowerCase();
    
    switch (gradeLower) {
      case 'easy':
        return <span className="inline-block w-3 h-3 rounded-full bg-green-500" title="Easy" />;
      case 'moderate':
        return <span className="inline-block w-0 h-0 border-l-[6px] border-r-[6px] border-t-[10px] border-l-transparent border-r-transparent border-t-blue-500" title="Moderate" />;
      case 'difficult':
        return <span className="inline-block w-3 h-3 rounded-full bg-red-500" title="Difficult" />;
      case 'hard':
        return <span className="inline-block w-3 h-3 rotate-45 bg-black" title="Hard" />;
      case 'very hard':
        return <span className="inline-flex items-center gap-0.5" title="Very Hard"><span className="inline-block w-3 h-3 rotate-45 bg-black" /><span className="inline-block w-3 h-3 rotate-45 bg-black" /></span>;
      default:
        return null;
    }
  };

  const formatElevation = (meters) => {
    if (!meters) return "N/A";
    return `${meters.toLocaleString()} m`;
  };

  // Load Strava activities for import
  const loadStravaActivities = async () => {
    setImportLoading(true);
    setImportError("");
    try {
      const res = await fetch(`${API_BASE}/api/v1/strava/activities?per_page=50&activity_type=Ride`);
      if (!res.ok) {
        throw new Error(`Failed to load Strava activities: ${res.status}`);
      }
      const data = await res.json();
      setStravaActivities(data);
    } catch (err) {
      setImportError(err.message);
    } finally {
      setImportLoading(false);
    }
  };

  // Load Komoot tours for import
  const loadKomootTours = async () => {
    setImportLoading(true);
    setImportError("");
    try {
      const res = await fetch(`${API_BASE}/api/v1/komoot/tours?per_page=50`);
      if (!res.ok) {
        throw new Error(`Failed to load Komoot tours: ${res.status}`);
      }
      const data = await res.json();
      setKomootTours(data);
    } catch (err) {
      setImportError(err.message);
    } finally {
      setImportLoading(false);
    }
  };

  // Handle import source change
  const handleImportSourceChange = (source) => {
    setImportSource(source);
    setImportError("");
    if (source === "strava") {
      loadStravaActivities();
    } else {
      loadKomootTours();
    }
  };

  // Import a route from Strava activity
  const handleImportFromStrava = async (activity) => {
    setImportLoading(true);
    setImportError("");
    try {
      // Construct Strava GPX export URL
      const stravaGpxUrl = `https://www.strava.com/activities/${activity.id}/export_gpx`;
      
      // Try to download the GPX file via backend (avoids CORS issues)
      let gpxUrl = "";
      
      try {
        // Use backend endpoint to download GPX file
        const downloadRes = await fetch(`${API_BASE}/api/v1/routes/download-gpx?gpx_url=${encodeURIComponent(stravaGpxUrl)}`, {
          method: "POST",
        });
        
        if (downloadRes.ok) {
          const downloadData = await downloadRes.json();
          gpxUrl = downloadData.url;
        } else {
          // If download fails, fall back to using the URL directly
          const errorData = await downloadRes.json().catch(() => ({}));
          console.warn("Could not download GPX file via backend:", errorData);
          gpxUrl = stravaGpxUrl;
        }
      } catch (downloadErr) {
        // If download fails, use URL directly
        console.warn("Could not download GPX file, using URL directly:", downloadErr);
        gpxUrl = stravaGpxUrl;
      }
      
      // Pre-fill the form with activity data
      setFormData({
        title: activity.name || "",
        gpx_url: gpxUrl,
        gpx_file: null,
        country: "",
        county: "",
        distance: activity.distance ? (activity.distance / 1000).toFixed(2) : "",
        ascent: activity.total_elevation_gain ? activity.total_elevation_gain.toString() : "",
        descent: "",
        starting_station: "",
        ending_station: "",
        getting_there: "",
        bike_choice: activity.type === "Ride" ? "Gravel" : "",
        guidebook_id: "",
        min_time: "",
        max_time: "",
        off_road_distance: "",
        off_road_percentage: "",
        grade: "",
        description: "",
        strava_activities: "",
        google_mymap_url: "",
        komoot_collections: "",
      });

      // Close import modal and open form
      setShowImportModal(false);
      setShowForm(true);
      setEditingRouteId(null);
      if (gpxUrl && !gpxUrl.includes("strava.com")) {
        setSuccess(`Imported "${activity.name}" from Strava. GPX file has been downloaded and saved locally.`);
      } else {
        setSuccess(`Imported "${activity.name}" from Strava. GPX URL has been added. If it requires authentication, you may need to download the GPX file manually and upload it.`);
      }
    } catch (err) {
      setImportError(err.message);
    } finally {
      setImportLoading(false);
    }
  };

  // Import a route from Komoot tour
  const handleImportFromKomoot = async (tour) => {
    setImportLoading(true);
    setImportError("");
    try {
      // Pre-fill the form with tour data
      setFormData({
        title: tour.name || "",
        gpx_url: "",
        gpx_file: null,
        country: "",
        county: "",
        distance: tour.distance ? (tour.distance / 1000).toFixed(2) : "",
        ascent: tour.elevation_gain ? tour.elevation_gain.toString() : "",
        descent: "",
        starting_station: "",
        ending_station: "",
        getting_there: "",
        bike_choice: "",
        guidebook_id: "",
        min_time: "",
        max_time: "",
        off_road_distance: "",
        off_road_percentage: "",
        grade: "",
        description: "",
        strava_activities: "",
        google_mymap_url: "",
        komoot_collections: "",
      });

      // Close import modal and open form
      setShowImportModal(false);
      setShowForm(true);
      setEditingRouteId(null);
      setSuccess(`Pre-filled form with data from "${tour.name}". Please add GPX file or URL.`);
    } catch (err) {
      setImportError(err.message);
    } finally {
      setImportLoading(false);
    }
  };

  // Load activities/tours when import modal opens
  useEffect(() => {
    if (showImportModal && isAdmin) {
      if (importSource === "strava") {
        loadStravaActivities();
      } else {
        loadKomootTours();
      }
    }
  }, [showImportModal, importSource, isAdmin]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-2xl font-semibold text-slate-900">Routes</h2>
        {isAdmin && (
          <div className="flex gap-2">
            <button
              onClick={() => setShowImportModal(true)}
              className="w-full sm:w-auto px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              Import Route
            </button>
            <button
              onClick={() => {
                if (showForm) {
                  handleCancel();
                } else {
                  setShowForm(true);
                  setEditingRouteId(null);
                }
              }}
              className="w-full sm:w-auto px-4 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors"
            >
              {showForm ? "Cancel" : "Add New Route"}
            </button>
          </div>
        )}
      </div>

      {isAdmin && showForm && (
        <div id="route-edit-form" className="bg-white rounded-xl p-4 sm:p-6 shadow-lg border border-slate-200">
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
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
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


              {/* Grade */}
              <div>
                <label htmlFor="grade" className="block text-sm font-medium text-slate-700 mb-1">
                  Grade
                </label>
                <select
                  id="grade"
                  name="grade"
                  value={formData.grade}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                >
                  <option value="">Select grade</option>
                  <option value="easy">Easy</option>
                  <option value="moderate">Moderate</option>
                  <option value="difficult">Difficult</option>
                  <option value="hard">Hard</option>
                  <option value="very hard">Very Hard</option>
                </select>
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
                  <option value="mountain">Mountain Bike</option>
                  <option value="gravel">Gravel Bike</option>
                  <option value="road">Road Bike</option>
                  <option value="hybrid">Hybrid Bike</option>
                  <option value="ebike">E-Bike</option>
                  <option value="any">Any</option>
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

              {/* Time Range */}
              <div className="space-y-2 p-3 bg-slate-50 rounded-lg border border-slate-200">
                <h4 className="text-sm font-semibold text-slate-700 mb-2">Time (days)</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label htmlFor="min_time" className="block text-sm font-medium text-slate-700 mb-1">
                      Min
                    </label>
                    <input
                      type="number"
                      id="min_time"
                      name="min_time"
                      step="0.1"
                      min="0"
                      value={formData.min_time}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                      placeholder="e.g., 2"
                    />
                  </div>
                  <div>
                    <label htmlFor="max_time" className="block text-sm font-medium text-slate-700 mb-1">
                      Max
                    </label>
                    <input
                      type="number"
                      id="max_time"
                      name="max_time"
                      step="0.1"
                      min="0"
                      value={formData.max_time}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                      placeholder="e.g., 3"
                    />
                  </div>
                </div>
              </div>

              {/* Ascent and Descent - Grouped */}
              <div className="space-y-2 p-3 bg-slate-50 rounded-lg border border-slate-200">
                <h4 className="text-sm font-semibold text-slate-700 mb-2">Elevation</h4>
                <div className="grid grid-cols-2 gap-3">
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
                </div>
              </div>

              {/* Off-road distance and percentage */}
              <div className="space-y-2 p-3 bg-slate-50 rounded-lg border border-slate-200">
                <h4 className="text-sm font-semibold text-slate-700 mb-2">Off-Road</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label htmlFor="off_road_distance" className="block text-sm font-medium text-slate-700 mb-1">
                      Distance (km)
                    </label>
                    <input
                      type="number"
                      id="off_road_distance"
                      name="off_road_distance"
                      step="0.1"
                      min="0"
                      value={formData.off_road_distance}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                      placeholder="e.g., 120.5"
                    />
                  </div>
                  <div>
                    <label htmlFor="off_road_percentage" className="block text-sm font-medium text-slate-700 mb-1">
                      Percentage (%)
                    </label>
                    <input
                      type="number"
                      id="off_road_percentage"
                      name="off_road_percentage"
                      step="0.1"
                      min="0"
                      max="100"
                      value={formData.off_road_percentage}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                      placeholder="e.g., 34.4"
                    />
                  </div>
                </div>
              </div>

              {/* Starting and Ending Stations - Grouped */}
              <div className="space-y-2 p-3 bg-slate-50 rounded-lg border border-slate-200">
                <h4 className="text-sm font-semibold text-slate-700 mb-2">Train Stations</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label htmlFor="starting_station" className="block text-sm font-medium text-slate-700 mb-1">
                      Start
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
                  <div>
                    <label htmlFor="ending_station" className="block text-sm font-medium text-slate-700 mb-1">
                      Finish
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

            {/* Description */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-slate-700 mb-1">
                Description
              </label>
              <textarea
                id="description"
                name="description"
                rows="4"
                value={formData.description}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                placeholder="Detailed description of the route..."
              />
            </div>

            {/* Route Links - GPX, My Maps, Strava, Komoot */}
            <div className="space-y-2 p-3 bg-slate-50 rounded-lg border border-slate-200">
              <h4 className="text-sm font-semibold text-slate-700 mb-3">Route Links</h4>
              <div className="space-y-4">
                {/* GPX File Upload */}
                <div>
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
                <div>
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

                {/* Google MyMap */}
                <div>
                  <label htmlFor="google_mymap_url" className="block text-sm font-medium text-slate-700 mb-1">
                    Google MyMap URL
                  </label>
                  <input
                    type="text"
                    id="google_mymap_url"
                    name="google_mymap_url"
                    value={formData.google_mymap_url}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                    placeholder="https://www.google.com/maps/d/viewer?mid=..."
                  />
                  <p className="mt-1 text-xs text-slate-500">
                    Tip: Share your map with "Anyone with the link" in Google MyMaps so users can copy it to their own maps
                  </p>
                </div>

                {/* Strava Activities */}
                <div>
                  <label htmlFor="strava_activities" className="block text-sm font-medium text-slate-700 mb-1">
                    Strava Activities
                  </label>
                  <textarea
                    id="strava_activities"
                    name="strava_activities"
                    rows="2"
                    value={formData.strava_activities}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                    placeholder="Comma-separated Strava activity URLs or IDs..."
                  />
                  <p className="mt-1 text-xs text-slate-500">
                    Enter URLs or IDs separated by commas (e.g., https://www.strava.com/activities/123456789, https://www.strava.com/activities/987654321)
                  </p>
                </div>

                {/* Komoot Collections */}
                <div>
                  <label htmlFor="komoot_collections" className="block text-sm font-medium text-slate-700 mb-1">
                    Komoot Collections
                  </label>
                  <textarea
                    id="komoot_collections"
                    name="komoot_collections"
                    rows="2"
                    value={formData.komoot_collections}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                    placeholder="Comma-separated Komoot collection URLs or IDs..."
                  />
                  <p className="mt-1 text-xs text-slate-500">
                    Enter URLs or IDs separated by commas for different route schedules
                  </p>
                </div>
              </div>
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

      {/* Import Route Modal */}
      {isAdmin && showImportModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-slate-200">
              <h2 className="text-2xl font-semibold text-slate-900">Import Route</h2>
              <button
                onClick={() => {
                  setShowImportModal(false);
                  setImportError("");
                }}
                className="text-slate-400 hover:text-slate-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Source Selection */}
            <div className="p-6 border-b border-slate-200 space-y-4">
              <div className="flex gap-2">
                <button
                  onClick={() => handleImportSourceChange("strava")}
                  className={`px-4 py-2 rounded-lg transition-colors ${
                    importSource === "strava"
                      ? "bg-orange-600 text-white"
                      : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                  }`}
                >
                  Strava
                </button>
                <button
                  onClick={() => handleImportSourceChange("komoot")}
                  className={`px-4 py-2 rounded-lg transition-colors ${
                    importSource === "komoot"
                      ? "bg-green-600 text-white"
                      : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                  }`}
                >
                  Komoot
                </button>
              </div>
              
              {/* Direct URL Import for Strava */}
              {importSource === "strava" && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Or import directly from a Strava activity URL:
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      id="strava_url"
                      placeholder="https://www.strava.com/activities/123456789"
                      className="flex-1 px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                      onKeyDown={async (e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          const url = e.target.value.trim();
                          if (url) {
                            // Extract activity ID from URL
                            const match = url.match(/activities\/(\d+)/);
                            if (match) {
                              const activityId = match[1];
                              // Create a mock activity object
                              const mockActivity = {
                                id: activityId,
                                name: `Strava Activity ${activityId}`,
                                distance: null,
                                total_elevation_gain: null,
                                type: "Ride",
                              };
                              await handleImportFromStrava(mockActivity);
                            } else {
                              setImportError("Invalid Strava activity URL. Please use format: https://www.strava.com/activities/123456789");
                            }
                          }
                        }
                      }}
                    />
                    <button
                      onClick={async (e) => {
                        const input = document.getElementById("strava_url");
                        const url = input.value.trim();
                        if (url) {
                          const match = url.match(/activities\/(\d+)/);
                          if (match) {
                            const activityId = match[1];
                            const mockActivity = {
                              id: activityId,
                              name: `Strava Activity ${activityId}`,
                              distance: null,
                              total_elevation_gain: null,
                              type: "Ride",
                            };
                            await handleImportFromStrava(mockActivity);
                          } else {
                            setImportError("Invalid Strava activity URL. Please use format: https://www.strava.com/activities/123456789");
                          }
                        }
                      }}
                      className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
                    >
                      Import
                    </button>
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    Paste a Strava activity URL (e.g., from a friend's shared route)
                  </p>
                </div>
              )}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {importError && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-800">
                  {importError}
                </div>
              )}

              {importLoading ? (
                <div className="text-center py-8 text-slate-600">Loading...</div>
              ) : importSource === "strava" ? (
                stravaActivities.length === 0 ? (
                  <div className="text-center py-8 text-slate-600">No Strava activities found.</div>
                ) : (
                  <div className="space-y-3">
                    {stravaActivities.map((activity) => (
                      <div
                        key={activity.id}
                        className="border border-slate-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <h3 className="font-semibold text-slate-900 mb-2">{activity.name}</h3>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm text-slate-600">
                              <div>
                                <span className="font-medium">Distance:</span>{" "}
                                {activity.distance ? `${(activity.distance / 1000).toFixed(1)} km` : "N/A"}
                              </div>
                              {activity.total_elevation_gain && (
                                <div>
                                  <span className="font-medium">Elevation:</span> {activity.total_elevation_gain} m
                                </div>
                              )}
                              <div>
                                <span className="font-medium">Type:</span> {activity.type}
                              </div>
                              <div>
                                <span className="font-medium">Date:</span>{" "}
                                {new Date(activity.start_date_local).toLocaleDateString()}
                              </div>
                            </div>
                          </div>
                          <button
                            onClick={() => handleImportFromStrava(activity)}
                            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                          >
                            Import
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )
              ) : (
                komootTours.length === 0 ? (
                  <div className="text-center py-8 text-slate-600">No Komoot tours found.</div>
                ) : (
                  <div className="space-y-3">
                    {komootTours.map((tour) => (
                      <div
                        key={tour.id}
                        className="border border-slate-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <h3 className="font-semibold text-slate-900 mb-2">{tour.name}</h3>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm text-slate-600">
                              {tour.distance && (
                                <div>
                                  <span className="font-medium">Distance:</span> {formatDistance(tour.distance)}
                                </div>
                              )}
                              {tour.elevation_gain && (
                                <div>
                                  <span className="font-medium">Elevation:</span> {formatElevation(tour.elevation_gain)}
                                </div>
                              )}
                              {tour.type && (
                                <div>
                                  <span className="font-medium">Type:</span> {tour.type}
                                </div>
                              )}
                            </div>
                            {tour.description && (
                              <p className="text-sm text-slate-600 mt-2 line-clamp-2">{tour.description}</p>
                            )}
                          </div>
                          <button
                            onClick={() => handleImportFromKomoot(tour)}
                            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                          >
                            Import
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )
              )}
            </div>
          </div>
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
                className="border border-slate-200 rounded-lg overflow-hidden"
              >
                <div
                  onClick={() => setSelectedRoute(selectedRoute?.id === route.id ? null : route)}
                  className="p-4 hover:shadow-md transition-shadow cursor-pointer"
                >
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between mb-2">
                  <h4 className="text-lg font-semibold text-slate-900">
                    {route.title}
                  </h4>
                  {isAdmin && (
                    <div className="flex gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEdit(route);
                        }}
                        className="px-3 py-1.5 text-sm bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors"
                      >
                        Edit
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(route.id, route.title);
                        }}
                        disabled={loading}
                        className="px-3 py-1.5 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Delete
                      </button>
                    </div>
                  )}
                </div>
                
                <div className="flex flex-col md:flex-row gap-4 items-start">
                  <div className="flex-1">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm text-slate-600">
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
                      {route.off_road_distance && (
                        <div>
                          <span className="font-medium">Off-road:</span> {formatDistance(route.off_road_distance)}
                        </div>
                      )}
                      {route.off_road_percentage !== null && route.off_road_percentage !== undefined && (
                        <div>
                          <span className="font-medium">% Off-road:</span> {route.off_road_percentage.toFixed(1)}%
                        </div>
                      )}
                      {route.grade && (
                        <div className="flex items-center gap-2">
                          <span className="font-medium">Grade:</span>
                          <div className="flex items-center gap-1.5">
                            {getGradeIndicator(route.grade)}
                            <span className="capitalize">{route.grade}</span>
                          </div>
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
                    {route.guidebook_id && (
                      <div className="mt-2 text-sm text-slate-600">
                        <span className="font-medium">Guidebook:</span>{" "}
                        {(() => {
                          const book = books.find((b) => b.id === route.guidebook_id);
                          if (!book) return "Unknown";
                          return (
                            <button
                              type="button"
                              onClick={() => {
                                if (onNavigateToBook) {
                                  onNavigateToBook("books");
                                  // Scroll to book after a brief delay to allow render
                                  setTimeout(() => {
                                    const bookEl = document.getElementById(`book-${book.id}`);
                                    if (bookEl) {
                                      bookEl.scrollIntoView({ behavior: "smooth", block: "center" });
                                      // Highlight briefly
                                      bookEl.classList.add("ring-2", "ring-sky-500");
                                      setTimeout(() => {
                                        bookEl.classList.remove("ring-2", "ring-sky-500");
                                      }, 2000);
                                    }
                                  }, 100);
                                }
                              }}
                              className="text-sky-600 hover:text-sky-700 hover:underline"
                            >
                              {book.title}
                            </button>
                          );
                        })()}
                      </div>
                    )}
                  </div>
                  
                  {/* Route Thumbnail/Map - Inline */}
                  {route.gpx_url && (
                    <div className="flex-shrink-0 w-full md:w-48 relative">
                      {route.thumbnail_url ? (
                        <img
                          src={route.thumbnail_url.startsWith('http') ? route.thumbnail_url : `${API_BASE}${route.thumbnail_url}`}
                          alt={`Route map for ${route.title}`}
                          className="w-full h-40 md:h-32 object-cover rounded-lg border border-slate-200"
                          onError={async (e) => {
                            // If thumbnail fails to load, try to regenerate it silently
                            try {
                              await fetch(`${API_BASE}/api/v1/routes/${route.id}/generate-thumbnail?force=true`, {
                                method: 'POST'
                              });
                              // Reload routes to get updated thumbnail
                              const routesRes = await fetch(`${API_BASE}/api/v1/routes/`);
                              if (routesRes.ok) {
                                const routesData = await routesRes.json();
                                setRoutes(routesData);
                              }
                            } catch (err) {
                              console.error("Error generating thumbnail:", err);
                              // Show fallback map
                              e.target.style.display = 'none';
                              const fallback = e.target.nextSibling;
                              if (fallback) fallback.style.display = 'block';
                            }
                          }}
                        />
                      ) : (
                        <RouteMap gpxUrl={route.gpx_url} routeTitle={route.title} />
                      )}
                    </div>
                  )}
                </div>
                </div>
                
                {/* Expanded Route Details */}
                {selectedRoute?.id === route.id && (
                  <RouteDetailPanel
                    route={selectedRoute}
                    onClose={() => setSelectedRoute(null)}
                    isAdmin={isAdmin}
                    onEdit={handleEdit}
                    inline={true}
                    currentUser={currentUser}
                  />
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
