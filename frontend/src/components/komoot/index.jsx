import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

function formatDistance(meters) {
  if (!meters) return "N/A";
  if (meters >= 1000) {
    return `${(meters / 1000).toFixed(1)} km`;
  }
  return `${Math.round(meters)} m`;
}

function formatDuration(seconds) {
  if (!seconds) return "N/A";
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
}

function formatElevation(meters) {
  if (!meters) return "N/A";
  return `${Math.round(meters)} m`;
}

export default function Komoot() {
  const [activeTab, setActiveTab] = useState("tours"); // "tours" or "collections"
  const [tours, setTours] = useState([]);
  const [collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState({
    tourType: "",
    useCache: true,
  });

  // Load tours
  useEffect(() => {
    if (activeTab !== "tours") return;
    
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const params = new URLSearchParams({
          per_page: "30",
          use_cache: filters.useCache ? "true" : "false",
        });
        
        if (filters.tourType) {
          params.append("tour_type", filters.tourType);
        }
        
        const res = await fetch(`${API_BASE}/api/v1/komoot/tours?${params.toString()}`);
        if (!res.ok) {
          throw new Error(`Request failed: ${res.status}`);
        }
        const data = await res.json();
        
        if (!cancelled) {
          setTours(data);
          console.log('Komoot tours API response:', data);
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
  }, [filters, activeTab]);

  // Load collections
  useEffect(() => {
    if (activeTab !== "collections") return;
    
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const params = new URLSearchParams({
          use_cache: filters.useCache ? "true" : "false",
        });
        
        const res = await fetch(`${API_BASE}/api/v1/komoot/collections?${params.toString()}`);
        if (!res.ok) {
          throw new Error(`Request failed: ${res.status}`);
        }
        const data = await res.json();
        
        if (!cancelled) {
          setCollections(data);
          console.log('Komoot collections API response:', data);
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
  }, [filters.useCache, activeTab]);

  const tourTypes = ["bike", "hike", "run", "mtb", "roadbike", "touringbike"];

  if (loading) {
    return (
      <section className="bg-white rounded-xl p-6 shadow-lg border border-slate-200">
        <div className="flex items-center gap-2 mb-4">
          <h2 className="text-2xl font-semibold text-slate-900">Komoot</h2>
        </div>
        <p className="text-slate-600">Loading {activeTab}...</p>
      </section>
    );
  }

  if (error && activeTab === "tours") {
    return (
      <section className="bg-white rounded-xl p-6 shadow-lg border border-slate-200">
        <div className="flex items-center gap-2 mb-4">
          <h2 className="text-2xl font-semibold text-slate-900">Komoot</h2>
        </div>
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          <p className="font-semibold">Error loading tours</p>
          <p className="text-sm">{error}</p>
          <p className="text-sm mt-2">
            Note: Komoot integration requires configuration. Please set KOMOOT_USER_ID 
            (and optionally KOMOOT_EMAIL and KOMOOT_PASSWORD) in your backend environment variables.
          </p>
        </div>
      </section>
    );
  }

  if (error && activeTab === "collections") {
    return (
      <section className="bg-white rounded-xl p-6 shadow-lg border border-slate-200">
        <div className="flex items-center gap-2 mb-4">
          <h2 className="text-2xl font-semibold text-slate-900">Komoot</h2>
        </div>
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          <p className="font-semibold">Error loading collections</p>
          <p className="text-sm">{error}</p>
          <p className="text-sm mt-2">
            Note: Collections require authentication. Please set KOMOOT_EMAIL and KOMOOT_PASSWORD 
            in your backend environment variables.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="bg-white rounded-xl p-6 shadow-lg border border-slate-200">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold text-slate-900">Komoot</h2>
        
        {/* Tabs */}
        <div className="flex gap-2 border-b border-slate-200">
          <button
            onClick={() => setActiveTab("tours")}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === "tours"
                ? "text-sky-600 border-b-2 border-sky-600"
                : "text-slate-600 hover:text-sky-600"
            }`}
          >
            Tours
          </button>
          <button
            onClick={() => setActiveTab("collections")}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === "collections"
                ? "text-sky-600 border-b-2 border-sky-600"
                : "text-slate-600 hover:text-sky-600"
            }`}
          >
            Collections
          </button>
        </div>
      </div>

      {/* Filters - only show for tours */}
      {activeTab === "tours" && (
        <div className="mb-6 p-4 bg-slate-50 rounded-lg border border-slate-200">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Filters</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Tour Type
              </label>
              <select
                value={filters.tourType || ""}
                onChange={(e) => setFilters({ ...filters, tourType: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
              >
                <option value="">All Types</option>
                {tourTypes.map((type) => (
                  <option key={type} value={type}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="flex items-end">
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={filters.useCache}
                  onChange={(e) => setFilters({ ...filters, useCache: e.target.checked })}
                  className="rounded border-slate-300 text-sky-600 focus:ring-sky-500"
                />
                Use cache
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Collections View */}
      {activeTab === "collections" && (
        <>
          {collections.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-slate-600 mb-2">No collections found.</p>
              <p className="text-sm text-slate-500">
                {error ? (
                  "Please check your Komoot configuration in the backend environment variables."
                ) : (
                  "Collections may require authentication. Make sure KOMOOT_EMAIL and KOMOOT_PASSWORD are set."
                )}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {collections.map((collection) => (
                <div
                  key={collection.id || collection.name}
                  className="border border-slate-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex flex-col md:flex-row gap-4">
                    {/* Collection Thumbnail */}
                    {collection.thumbnail_url && (
                      <div className="flex-shrink-0">
                        <a
                          href={collection.komoot_url || `https://www.komoot.com/collection/${collection.id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block"
                        >
                          <img
                            src={collection.thumbnail_url}
                            alt={collection.name}
                            className="rounded-lg w-full md:w-48 h-32 object-cover border border-slate-200"
                            onError={(e) => {
                              e.target.style.display = 'none';
                            }}
                          />
                        </a>
                      </div>
                    )}

                    {/* Collection Details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <h3 className="text-lg font-semibold text-slate-900">
                          <a
                            href={collection.komoot_url || `https://www.komoot.com/collection/${collection.id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hover:text-sky-600 transition-colors"
                          >
                            {collection.name}
                          </a>
                        </h3>
                        {collection.item_count !== null && collection.item_count !== undefined && (
                          <span className="px-2 py-1 text-xs font-medium bg-sky-100 text-sky-700 rounded-full flex-shrink-0">
                            {collection.item_count} item{collection.item_count !== 1 ? 's' : ''}
                          </span>
                        )}
                      </div>

                      {collection.description && (
                        <p className="text-sm text-slate-600 mb-3 line-clamp-2">
                          {collection.description}
                        </p>
                      )}

                      {/* Collection Items Preview */}
                      {collection.items && collection.items.length > 0 && (
                        <div className="mt-3">
                          <p className="text-xs text-slate-500 mb-2">Items in this collection:</p>
                          <div className="flex flex-wrap gap-2">
                            {collection.items.slice(0, 5).map((item, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-1 text-xs bg-slate-100 text-slate-700 rounded"
                              >
                                {item.name || item.title || `Item ${idx + 1}`}
                              </span>
                            ))}
                            {collection.items.length > 5 && (
                              <span className="px-2 py-1 text-xs text-slate-500">
                                +{collection.items.length - 5} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Tours View */}
      {activeTab === "tours" && (
        <>
          {tours.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-slate-600 mb-2">No tours found.</p>
              <p className="text-sm text-slate-500">
                {error ? (
                  "Please check your Komoot configuration in the backend environment variables."
                ) : (
                  "Try adjusting your filters or check your Komoot account settings."
                )}
              </p>
            </div>
          ) : (
        <div className="space-y-4">
          {tours.map((tour) => (
            <div
              key={tour.id}
              className="border border-slate-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex flex-col md:flex-row gap-4">
                {/* Tour Image/Map */}
                {tour.thumbnail_url || tour.map_image_url ? (
                  <div className="flex-shrink-0">
                    <a
                      href={tour.komoot_url || `https://www.komoot.com/tour/${tour.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block"
                    >
                      <img
                        src={tour.thumbnail_url || tour.map_image_url}
                        alt={tour.name}
                        className="rounded-lg w-full md:w-48 h-32 object-cover border border-slate-200"
                        onError={(e) => {
                          e.target.style.display = 'none';
                        }}
                      />
                    </a>
                  </div>
                ) : null}

                {/* Tour Details */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h3 className="text-lg font-semibold text-slate-900">
                      <a
                        href={tour.komoot_url || `https://www.komoot.com/tour/${tour.id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-sky-600 transition-colors"
                      >
                        {tour.name}
                      </a>
                    </h3>
                    {tour.type && (
                      <span className="px-2 py-1 text-xs font-medium bg-sky-100 text-sky-700 rounded-full flex-shrink-0">
                        {tour.type}
                      </span>
                    )}
                  </div>

                  {tour.description && (
                    <p className="text-sm text-slate-600 mb-3 line-clamp-2">
                      {tour.description}
                    </p>
                  )}

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                    <div>
                      <span className="text-slate-500">Distance</span>
                      <p className="font-semibold text-slate-900">
                        {formatDistance(tour.distance)}
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-500">Duration</span>
                      <p className="font-semibold text-slate-900">
                        {formatDuration(tour.duration)}
                      </p>
                    </div>
                    {tour.elevation_gain && (
                      <div>
                        <span className="text-slate-500">Elevation</span>
                        <p className="font-semibold text-slate-900">
                          {formatElevation(tour.elevation_gain)}
                        </p>
                      </div>
                    )}
                    {tour.difficulty && (
                      <div>
                        <span className="text-slate-500">Difficulty</span>
                        <p className="font-semibold text-slate-900">
                          {tour.difficulty}
                        </p>
                      </div>
                    )}
                  </div>

                  {tour.highlights && tour.highlights.length > 0 && (
                    <div className="mt-3">
                      <span className="text-xs text-slate-500">
                        {tour.highlights.length} highlight{tour.highlights.length !== 1 ? 's' : ''}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
          )}
        </>
      )}
    </section>
  );
}
