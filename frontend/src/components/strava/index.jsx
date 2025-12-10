import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

// Component for map thumbnail with proper error handling
function MapThumbnail({ mapUrl, activityUrl, mapId, hasPolyline }) {
  const [imageError, setImageError] = useState(false);
  
  if (imageError) {
    return (
      <div className="flex-shrink-0">
        <a
          href={activityUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="block rounded-lg w-48 h-32 bg-slate-100 border border-slate-200 flex items-center justify-center hover:bg-slate-200 transition-colors"
        >
          <div className="text-center">
            <svg
              className="w-8 h-8 mx-auto mb-1 text-slate-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
              />
            </svg>
            <span className="text-xs text-slate-600">View Map</span>
          </div>
        </a>
      </div>
    );
  }
  
  return (
    <div className="flex-shrink-0">
      <a
        href={activityUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="block relative rounded-lg w-48 h-32 border border-slate-200 overflow-hidden hover:shadow-md transition-shadow bg-slate-100"
      >
        <img
          src={mapUrl}
          alt="Activity map"
          className="w-full h-full object-cover"
          onError={() => {
            console.error('Map image failed to load:', mapUrl);
            console.error('Map data:', { mapId, hasPolyline });
            setImageError(true);
          }}
        />
      </a>
    </div>
  );
}

export default function StravaActivities() {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState({
    activityType: "Ride",
    minDistance: 30000, // 30km in meters
    maxDistance: null,
    minDuration: null,
    maxDuration: null,
  });

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError("");
      try {
        // Build query parameters
        const params = new URLSearchParams({
          per_page: "30", // Reduced to avoid rate limits
          use_cache: "true", // Set to "true" to enable caching (disabled for testing)
        });
        
        if (filters.activityType) {
          params.append("activity_type", filters.activityType);
        }
        if (filters.minDistance !== null && filters.minDistance !== undefined) {
          params.append("min_distance", filters.minDistance.toString());
        }
        if (filters.maxDistance !== null && filters.maxDistance !== undefined) {
          params.append("max_distance", filters.maxDistance.toString());
        }
        if (filters.minDuration !== null && filters.minDuration !== undefined) {
          params.append("min_duration", filters.minDuration.toString());
        }
        if (filters.maxDuration !== null && filters.maxDuration !== undefined) {
          params.append("max_duration", filters.maxDuration.toString());
        }
        
        const res = await fetch(`${API_BASE}/api/v1/strava/activities?${params.toString()}`);
        if (!res.ok) {
          throw new Error(`Request failed: ${res.status}`);
        }
        const data = await res.json();
        console.log('Strava activities API response:', data);
        console.log('Number of activities:', data?.length);
        // Debug first activity to see structure
        if (data && data.length > 0) {
          const first = data[0];
          console.log('First activity structure:', {
            id: first.id,
            name: first.name,
            hasMap: !!first.map,
            mapData: first.map,
            mapPolyline: first.map?.summary_polyline?.substring(0, 50),
            mapId: first.map?.id,
            hasPhotos: !!first.photos,
            photos: first.photos,
            photosType: typeof first.photos,
            photosKeys: first.photos ? Object.keys(first.photos) : null
          });
        }
        if (!cancelled) {
          setActivities(data || []);
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
  }, [filters]);

  const formatDistance = (meters) => {
    if (meters >= 1000) {
      return `${(meters / 1000).toFixed(2)} km`;
    }
    return `${Math.round(meters)} m`;
  };

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const formatSpeed = (mps) => {
    if (!mps) return null;
    // Convert m/s to km/h
    const kmh = (mps * 3.6).toFixed(1);
    return `${kmh} km/h`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return "";
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateString;
    }
  };

  const getActivityTypeIcon = (type) => {
    const icons = {
      Ride: "🚴",
      Run: "🏃",
      Walk: "🚶",
      Hike: "🥾",
      Swim: "🏊",
      Workout: "💪",
      VirtualRide: "🚴‍♂️",
      VirtualRun: "🏃‍♂️",
    };
    return icons[type] || "🏃";
  };

  const getActivityUrl = (activityId) => {
    return `https://www.strava.com/activities/${activityId}`;
  };

  const activityTypes = ["Ride", "Run", "Walk", "Hike", "Swim", "Workout", "VirtualRide", "VirtualRun"];

  return (
    <section className="bg-white rounded-xl p-6 shadow-lg border border-slate-200">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <h2 className="text-2xl font-semibold text-slate-900">Strava Activities</h2>
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
      </div>

      {/* Filters */}
      <div className="mb-6 p-4 bg-slate-50 rounded-lg border border-slate-200">
        <h3 className="text-sm font-semibold text-slate-700 mb-3">Filters</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Activity Type
            </label>
            <select
              value={filters.activityType || ""}
              onChange={(e) => setFilters({ ...filters, activityType: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              <option value="">All Types</option>
              {activityTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Min Distance (km)
            </label>
            <input
              type="number"
              value={filters.minDistance ? (filters.minDistance / 1000).toFixed(1) : ""}
              onChange={(e) => {
                const value = e.target.value;
                setFilters({
                  ...filters,
                  minDistance: value ? parseFloat(value) * 1000 : null,
                });
              }}
              placeholder="e.g. 30"
              className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Max Distance (km)
            </label>
            <input
              type="number"
              value={filters.maxDistance ? (filters.maxDistance / 1000).toFixed(1) : ""}
              onChange={(e) => {
                const value = e.target.value;
                setFilters({
                  ...filters,
                  maxDistance: value ? parseFloat(value) * 1000 : null,
                });
              }}
              placeholder="No limit"
              className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Min Duration (hours)
            </label>
            <input
              type="number"
              step="0.5"
              value={filters.minDuration ? (filters.minDuration / 3600).toFixed(1) : ""}
              onChange={(e) => {
                const value = e.target.value;
                setFilters({
                  ...filters,
                  minDuration: value ? parseFloat(value) * 3600 : null,
                });
              }}
              placeholder="e.g. 1.5"
              className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>
        </div>
      </div>

      {error ? (
        <p className="text-red-600 m-0">Failed to load activities: {error}</p>
      ) : activities.length === 0 && !loading ? (
        <p className="text-slate-400 m-0">No activities found.</p>
      ) : (
        <div className="flex flex-col gap-4">
          {activities.map((activity) => (
            <article
              key={activity.id}
              className="border border-slate-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl">{getActivityTypeIcon(activity.type)}</span>
                    <h3 className="text-lg font-semibold text-slate-900">
                      <a
                        href={getActivityUrl(activity.id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-sky-600 transition-colors"
                      >
                        {activity.name}
                      </a>
                    </h3>
                  </div>
                  
                  <div className="flex flex-wrap gap-4 text-sm text-slate-600 mb-2">
                    <span className="font-medium">{activity.type}</span>
                    <span>•</span>
                    <time dateTime={activity.start_date_local}>
                      {formatDate(activity.start_date_local)}
                    </time>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                    <div>
                      <span className="text-slate-500">Distance</span>
                      <p className="font-semibold text-slate-900">{formatDistance(activity.distance)}</p>
                    </div>
                    <div>
                      <span className="text-slate-500">Time</span>
                      <p className="font-semibold text-slate-900">{formatTime(activity.moving_time)}</p>
                    </div>
                    {activity.average_speed && (
                      <div>
                        <span className="text-slate-500">Avg Speed</span>
                        <p className="font-semibold text-slate-900">{formatSpeed(activity.average_speed)}</p>
                      </div>
                    )}
                    {activity.total_elevation_gain && (
                      <div>
                        <span className="text-slate-500">Elevation</span>
                        <p className="font-semibold text-slate-900">
                          {Math.round(activity.total_elevation_gain)} m
                        </p>
                      </div>
                    )}
                  </div>

                  {activity.description && (
                    <p className="text-slate-600 text-sm mt-2 line-clamp-2">
                      {activity.description}
                    </p>
                  )}

                  <a
                    href={getActivityUrl(activity.id)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center text-sky-600 hover:text-sky-700 font-medium text-sm mt-3"
                  >
                    View on Strava
                    <svg
                      className="ml-1 w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                      />
                    </svg>
                  </a>
                </div>

                {/* Show photo thumbnail if available, otherwise show map */}
                {(() => {
                  // Check for photos - simplified logic
                  const photos = activity.photos;
                  let photoUrl = null;
                  
                  if (photos) {
                    // Check for direct thumbnail_url
                    if (photos.thumbnail_url) {
                      photoUrl = photos.thumbnail_url;
                    }
                    // Check for nested structure
                    else if (photos.primary && typeof photos.primary === 'object') {
                      if (photos.primary.thumbnail_url) {
                        photoUrl = photos.primary.thumbnail_url;
                      } else if (photos.primary.urls) {
                        photoUrl = photos.primary.urls['100'] || photos.primary.urls['600'];
                      }
                    }
                    // Check for data array
                    else if (Array.isArray(photos.data) && photos.data.length > 0) {
                      photoUrl = photos.data[0].thumbnail_url || photos.data[0].url;
                    }
                  }
                  
                  // Show photo if available
                  if (photoUrl) {
                    return (
                      <div className="flex-shrink-0">
                        <img
                          src={photoUrl}
                          alt="Activity photo"
                          className="rounded-lg w-48 h-32 object-cover border border-slate-200"
                          onError={(e) => {
                            console.error('Photo failed to load:', photoUrl);
                            e.target.style.display = 'none';
                          }}
                        />
                      </div>
                    );
                  }
                  
                  // Fallback to map if no photo
                  const mapData = activity.map;
                  if (mapData) {
                    const polyline = mapData.summary_polyline || mapData.polyline;
                    
                    if (polyline) {
                      // Use Mapbox with the polyline to generate map thumbnail
                      // Strava's CDN map URLs are unreliable, so we use polyline-based maps
                      const encodedPolyline = encodeURIComponent(polyline);
                      // Get Mapbox token from environment variable
                      // Set VITE_MAPBOX_ACCESS_TOKEN in your .env file
                      // Get a free token at https://account.mapbox.com/
                      const mapboxToken = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN;
                      if (!mapboxToken) {
                        console.warn('VITE_MAPBOX_ACCESS_TOKEN not set - map thumbnails will not work');
                        // Return placeholder instead of broken image
                        return (
                          <div className="flex-shrink-0">
                            <a
                              href={getActivityUrl(activity.id)}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="block rounded-lg w-48 h-32 bg-slate-100 border border-slate-200 flex items-center justify-center hover:bg-slate-200 transition-colors"
                            >
                              <div className="text-center">
                                <svg
                                  className="w-8 h-8 mx-auto mb-1 text-slate-400"
                                  fill="none"
                                  stroke="currentColor"
                                  viewBox="0 0 24 24"
                                >
                                  <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
                                  />
                                </svg>
                                <span className="text-xs text-slate-600">View Map</span>
                              </div>
                            </a>
                          </div>
                        );
                      }
                      const mapUrl = `https://api.mapbox.com/styles/v1/mapbox/outdoors-v11/static/path-3+ff0000-0.6(${encodedPolyline})/auto/200x150?access_token=${mapboxToken}`;
                      
                      return (
                        <MapThumbnail 
                          mapUrl={mapUrl}
                          activityUrl={getActivityUrl(activity.id)}
                          mapId={mapData.id}
                          hasPolyline={!!polyline}
                        />
                      );
                    }
                  }
                  
                  // Show placeholder if no map or photo
                  return (
                    <div className="flex-shrink-0">
                      <a
                        href={getActivityUrl(activity.id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block rounded-lg w-48 h-32 bg-slate-100 border border-slate-200 flex items-center justify-center hover:bg-slate-200 transition-colors"
                      >
                        <div className="text-center">
                          <svg
                            className="w-8 h-8 mx-auto mb-1 text-slate-400"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
                            />
                          </svg>
                          <span className="text-xs text-slate-600">View Map</span>
                        </div>
                      </a>
                    </div>
                  );
                  
                  return null;
                })()}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
