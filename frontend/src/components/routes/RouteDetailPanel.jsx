import { useState, useEffect } from "react";
import RouteMap from "./RouteMap";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export default function RouteDetailPanel({ route, onClose, isAdmin, onEdit, inline = false, currentUser }) {
  const [photos, setPhotos] = useState([]);
  const [photosLoading, setPhotosLoading] = useState(false);
  const [photosError, setPhotosError] = useState("");
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [lightboxIndex, setLightboxIndex] = useState(0);
  const [showPhotoUpload, setShowPhotoUpload] = useState(false);
  const [photoFiles, setPhotoFiles] = useState([]);
  const [photoUploading, setPhotoUploading] = useState(false);
  const [photoUploadError, setPhotoUploadError] = useState("");
  const [showStravaInput, setShowStravaInput] = useState(false);
  const [stravaActivityUrl, setStravaActivityUrl] = useState("");
  const [stravaUpdating, setStravaUpdating] = useState(false);
  const [localStravaActivities, setLocalStravaActivities] = useState(null);
  const [reprocessingGPS, setReprocessingGPS] = useState(false);
  const [hasPurchasedGuidebook, setHasPurchasedGuidebook] = useState(null);
  const [checkingPurchase, setCheckingPurchase] = useState(false);

  useEffect(() => {
    if (route?.id) {
      loadPhotos();
    }
  }, [route?.id]);

  // Check if user has purchased the guidebook
  useEffect(() => {
    const checkPurchaseStatus = async () => {
      // If no guidebook associated, always allow access
      if (!route?.guidebook_id) {
        setHasPurchasedGuidebook(true);
        return;
      }

      // Admins always have access
      if (isAdmin) {
        setHasPurchasedGuidebook(true);
        return;
      }

      // If no user, lock it
      if (!currentUser?.id) {
        setHasPurchasedGuidebook(false);
        return;
      }

      setCheckingPurchase(true);
      try {
        const token = localStorage.getItem('authToken');
        if (!token) {
          setHasPurchasedGuidebook(false);
          return;
        }
        const res = await fetch(`${API_BASE}/api/v1/books/${route.guidebook_id}/purchased`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (res.ok) {
          const data = await res.json();
          setHasPurchasedGuidebook(data.purchased === true);
        } else {
          setHasPurchasedGuidebook(false);
        }
      } catch (err) {
        console.error('Error checking purchase status:', err);
        setHasPurchasedGuidebook(false);
      } finally {
        setCheckingPurchase(false);
      }
    };

    checkPurchaseStatus();
  }, [route?.guidebook_id, currentUser?.id, isAdmin]);

  const loadPhotos = async () => {
    setPhotosLoading(true);
    setPhotosError("");
    try {
      const res = await fetch(`${API_BASE}/api/v1/routes/${route.id}/photos`);
      if (!res.ok) {
        throw new Error(`Failed to load photos: ${res.status}`);
      }
      const data = await res.json();
      setPhotos(data || []);
    } catch (err) {
      setPhotosError(err.message);
    } finally {
      setPhotosLoading(false);
    }
  };

  const handlePhotoUpload = async (e) => {
    e.preventDefault();
    if (!photoFiles || photoFiles.length === 0) return;

    setPhotoUploading(true);
    setPhotoUploadError("");
    try {
      // Upload each file sequentially
      for (const file of photoFiles) {
        const formData = new FormData();
        formData.append("route_id", route.id);
        formData.append("file", file);

        const res = await fetch(`${API_BASE}/api/v1/routes/photos`, {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Upload failed for ${file.name}: ${res.status}`);
        }
      }

      // Reload photos
      await loadPhotos();
      setPhotoFiles([]);
      setShowPhotoUpload(false);
      const fileInput = document.getElementById("route_photo_file");
      if (fileInput) fileInput.value = "";
    } catch (err) {
      setPhotoUploadError(err.message);
    } finally {
      setPhotoUploading(false);
    }
  };

  const handleReprocessGPS = async () => {
    if (!route?.id) return;
    
    setReprocessingGPS(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/routes/${route.id}/photos/reprocess-gps`, {
        method: "POST",
      });
      
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Failed to reprocess GPS: ${res.status}`);
      }
      
      const data = await res.json();
      // Reload photos to show updated GPS data
      await loadPhotos();
      alert(`Successfully processed ${data.updated_count} photos with GPS data`);
    } catch (err) {
      alert(`Error: ${err.message}`);
    } finally {
      setReprocessingGPS(false);
    }
  };

  const handleAddStravaActivity = async (e) => {
    e.preventDefault();
    if (!stravaActivityUrl.trim()) return;

    setStravaUpdating(true);
    try {
      const currentActivities = localStravaActivities !== null 
        ? (localStravaActivities ? localStravaActivities.split(',').map(s => s.trim()).filter(Boolean) : [])
        : (route.strava_activities ? route.strava_activities.split(',').map(s => s.trim()).filter(Boolean) : []);
      
      const newActivities = [...currentActivities, stravaActivityUrl.trim()];
      const newActivitiesString = newActivities.join(', ');
      
      const res = await fetch(`${API_BASE}/api/v1/routes/${route.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          strava_activities: newActivitiesString,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Update failed: ${res.status}`);
      }

      // Update local state to reflect the change
      setLocalStravaActivities(newActivitiesString);
      setStravaActivityUrl("");
      setShowStravaInput(false);
    } catch (err) {
      alert(`Error: ${err.message}`);
    } finally {
      setStravaUpdating(false);
    }
  };

  const openLightbox = (index) => {
    setLightboxIndex(index);
    setLightboxOpen(true);
  };

  const closeLightbox = () => {
    setLightboxOpen(false);
  };

  const nextPhoto = () => {
    setLightboxIndex((prev) => (prev + 1) % photos.length);
  };

  const prevPhoto = () => {
    setLightboxIndex((prev) => (prev - 1 + photos.length) % photos.length);
  };

  // Parse comma-separated Strava activities
  const parseStravaActivities = () => {
    const activitiesString = localStravaActivities !== null ? localStravaActivities : route.strava_activities;
    if (!activitiesString) return [];
    return activitiesString.split(',').map(url => url.trim()).filter(Boolean);
  };

  // Parse comma-separated Komoot collections
  const parseKomootCollections = () => {
    if (!route.komoot_collections) return [];
    return route.komoot_collections.split(',').map(url => url.trim()).filter(Boolean);
  };

  const stravaActivities = parseStravaActivities();
  const komootCollections = parseKomootCollections();

  // Format time range
  const formatTimeRange = () => {
    if (route.min_time && route.max_time) {
      return `${route.min_time} - ${route.max_time} days`;
    } else if (route.min_time) {
      return `${route.min_time}+ days`;
    } else if (route.max_time) {
      return `up to ${route.max_time} days`;
    }
    return null;
  };

  // Grade indicator with glyphs
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

  // If inline mode, render as expandable card section
  if (inline) {
    return (
      <div>
        <div className="border-t border-slate-200 bg-slate-50">
          <div className="p-4 space-y-4">
            {/* Route Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              {route.distance && (
                <div>
                  <span className="text-slate-500">Distance</span>
                  <p className="font-semibold text-slate-900">
                    {route.distance > 1000 ? `${(route.distance / 1000).toFixed(1)} km` : `${Math.round(route.distance)} m`}
                  </p>
                </div>
              )}
              {formatTimeRange() && (
                <div>
                  <span className="text-slate-500">Time</span>
                  <p className="font-semibold text-slate-900">{formatTimeRange()}</p>
                </div>
              )}
              {route.grade && (
                <div>
                  <span className="text-slate-500">Grade</span>
                  <div className="flex items-center gap-1.5">
                    {getGradeIndicator(route.grade)}
                    <span className="font-semibold text-slate-900 capitalize">{route.grade}</span>
                  </div>
                </div>
              )}
              {route.country && (
                <div>
                  <span className="text-slate-500">Country</span>
                  <p className="font-semibold text-slate-900">{route.country}</p>
                </div>
              )}
            </div>

            {/* Interactive Map */}
            {route.gpx_url && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-base font-semibold text-slate-900">Route Map</h3>
                  {(hasPurchasedGuidebook === true || !route.guidebook_id) ? (
                    <a
                      href={route.gpx_url.startsWith('http') ? route.gpx_url : `${API_BASE}${route.gpx_url}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      download
                      className="inline-flex items-center px-3 py-1.5 text-xs bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors"
                    >
                      Download GPX
                      <svg className="ml-1.5 w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                    </a>
                  ) : (
                    <div className="inline-flex items-center px-3 py-1.5 text-xs bg-slate-300 text-slate-600 rounded-lg cursor-not-allowed">
                      <svg className="mr-1.5 w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                      </svg>
                      GPX Locked
                    </div>
                  )}
                </div>
                <div className="border border-slate-200 rounded-lg overflow-hidden">
                  <RouteMap 
                    gpxUrl={route.gpx_url} 
                    routeTitle={route.title} 
                    interactive={true}
                    height="300px"
                    photos={photos}
                  />
                </div>
              </div>
            )}

            {/* Description */}
            {route.description && (
              <div>
                <h3 className="text-base font-semibold text-slate-900 mb-2">Description</h3>
                <p className="text-slate-700 whitespace-pre-wrap text-sm">{route.description}</p>
              </div>
            )}

            {/* Photos */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-base font-semibold text-slate-900">Photos</h3>
                <div className="flex items-center gap-2">
                  {isAdmin && photos.length > 0 && (
                    <button
                      type="button"
                      onClick={handleReprocessGPS}
                      disabled={reprocessingGPS}
                      className="text-xs text-sky-600 hover:text-sky-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Re-process photos to extract GPS coordinates from EXIF data"
                    >
                      {reprocessingGPS ? "Processing..." : "Extract GPS"}
                    </button>
                  )}
                  {isAdmin && (
                    <button
                      onClick={() => setShowPhotoUpload(!showPhotoUpload)}
                      className="px-3 py-1.5 text-sm bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors"
                    >
                    {showPhotoUpload ? "Cancel" : "Add Photo"}
                  </button>
                )}
              </div>

              {isAdmin && showPhotoUpload && (
                <div className="mb-3 p-3 bg-white rounded-lg border border-slate-200">
                  <form onSubmit={handlePhotoUpload}>
                    <div className="space-y-2">
                      <div>
                        <label htmlFor="route_photo_file_inline" className="block text-sm font-medium text-slate-700 mb-1">
                          Photos (multiple allowed)
                        </label>
                        <input
                          type="file"
                          id="route_photo_file_inline"
                          accept="image/*"
                          multiple
                          onChange={(e) => setPhotoFiles(Array.from(e.target.files || []))}
                          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 text-sm"
                          required
                        />
                        {photoFiles.length > 0 && (
                          <p className="mt-1 text-xs text-slate-500">
                            {photoFiles.length} file{photoFiles.length !== 1 ? 's' : ''} selected
                          </p>
                        )}
                      </div>
                      {photoUploadError && (
                        <div className="text-red-600 text-xs">{photoUploadError}</div>
                      )}
                      <button
                        type="submit"
                        disabled={photoUploading || photoFiles.length === 0}
                        className="px-3 py-1.5 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                      >
                        {photoUploading ? "Uploading..." : `Upload ${photoFiles.length > 0 ? photoFiles.length : ''} Photo${photoFiles.length !== 1 ? 's' : ''}`}
                      </button>
                    </div>
                  </form>
                </div>
              )}

              {photosLoading ? (
                <div className="text-slate-600 text-sm">Loading photos...</div>
              ) : photosError ? (
                <div className="text-red-600 text-sm">Error loading photos: {photosError}</div>
              ) : photos.length === 0 ? (
                <div className="text-slate-500 text-sm">No photos yet.</div>
              ) : (
                <div className="grid grid-cols-3 md:grid-cols-5 gap-2">
                  {photos.map((photo, index) => (
                    <button
                      key={photo.id}
                      type="button"
                      onClick={() => openLightbox(index)}
                      className="relative aspect-square overflow-hidden rounded-lg border border-slate-200 hover:shadow-md transition-shadow"
                    >
                      <img
                        src={photo.thumbnail_url || photo.photo_url}
                        alt={photo.caption || `Photo ${photo.id}`}
                        className="w-full h-full object-cover"
                        onError={(e) => (e.target.src = photo.photo_url)}
                      />
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Links Section */}
            <div className="space-y-3">
              {/* Strava Activities */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-base font-semibold text-slate-900">Strava Activities</h3>
                  {isAdmin && (
                    <button
                      onClick={() => setShowStravaInput(!showStravaInput)}
                      className="px-3 py-1.5 text-sm bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
                    >
                      {showStravaInput ? "Cancel" : "Add Activity"}
                    </button>
                  )}
                </div>

                {isAdmin && showStravaInput && (
                  <div className="mb-2 p-3 bg-white rounded-lg border border-slate-200">
                    <form onSubmit={handleAddStravaActivity}>
                      <div className="space-y-2">
                        <div>
                          <label htmlFor="strava_activity_url_inline" className="block text-sm font-medium text-slate-700 mb-1">
                            Strava Activity URL or ID
                          </label>
                          <input
                            type="text"
                            id="strava_activity_url_inline"
                            value={stravaActivityUrl}
                            onChange={(e) => setStravaActivityUrl(e.target.value)}
                            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 text-sm"
                            placeholder="https://www.strava.com/activities/123456789 or 123456789"
                            required
                          />
                        </div>
                        <button
                          type="submit"
                          disabled={stravaUpdating || !stravaActivityUrl.trim()}
                          className="px-3 py-1.5 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                        >
                          {stravaUpdating ? "Adding..." : "Add Activity"}
                        </button>
                      </div>
                    </form>
                  </div>
                )}

                {stravaActivities.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {stravaActivities.map((activity, index) => {
                      const activityId = activity.match(/activities\/(\d+)/)?.[1] || activity;
                      const activityUrl = activity.startsWith('http') 
                        ? activity 
                        : `https://www.strava.com/activities/${activityId}`;
                      
                      return (
                        <a
                          key={index}
                          href={activityUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center px-3 py-1.5 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors text-xs font-medium"
                        >
                          Strava {index + 1}
                          <svg className="ml-1.5 w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                        </a>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-slate-500 text-sm">No Strava activities added yet.</div>
                )}
              </div>

              {/* Google MyMap */}
              {route.google_mymap_url && (
                <div>
                  <h3 className="text-base font-semibold text-slate-900 mb-2">Google MyMap</h3>
                  {(hasPurchasedGuidebook === true || !route.guidebook_id) ? (
                    <div className="space-y-2">
                      <a
                        href={route.google_mymap_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-xs font-medium"
                      >
                        View & Copy Map
                        <svg className="ml-1.5 w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </a>
                      <p className="text-xs text-slate-500">
                        Click to open the map, then use the menu (⋮) to "Copy map" to your own My Maps
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="inline-flex items-center px-3 py-1.5 bg-slate-300 text-slate-600 rounded-lg text-xs font-medium cursor-not-allowed">
                        <svg className="mr-1.5 w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                        Locked
                      </div>
                      <p className="text-xs text-slate-500">
                        This map is only available to users who have purchased the guidebook
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Komoot Collections */}
              {komootCollections.length > 0 && (
                <div>
                  <h3 className="text-base font-semibold text-slate-900 mb-2">Komoot Collections</h3>
                  {(hasPurchasedGuidebook === true || !route.guidebook_id) ? (
                    <div className="flex flex-wrap gap-2">
                      {komootCollections.map((collection, index) => {
                        const collectionUrl = collection.startsWith('http')
                          ? collection
                          : `https://www.komoot.com/collection/${collection}`;
                        
                        return (
                          <a
                            key={index}
                            href={collectionUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-xs font-medium"
                          >
                            Komoot {index + 1}
                            <svg className="ml-1.5 w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                          </a>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="inline-flex items-center px-3 py-1.5 bg-slate-300 text-slate-600 rounded-lg text-xs font-medium cursor-not-allowed">
                        <svg className="mr-1.5 w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                        Locked
                      </div>
                      <p className="text-xs text-slate-500">
                        These collections are only available to users who have purchased the guidebook
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Lightbox (shared for both modes) */}
        {lightboxOpen && photos.length > 0 && (
          <div className="fixed inset-0 z-60 bg-black/90 flex items-center justify-center" onClick={closeLightbox}>
            <div className="relative max-w-5xl w-full mx-4" onClick={(e) => e.stopPropagation()}>
              <button onClick={closeLightbox} className="absolute top-4 right-4 z-10 px-3 py-1 rounded bg-black/70 text-white text-sm hover:bg-black">Close</button>
              <button onClick={prevPhoto} className="absolute left-4 top-1/2 -translate-y-1/2 z-10 px-3 py-1 rounded bg-black/70 text-white text-2xl hover:bg-black">‹</button>
              <button onClick={nextPhoto} className="absolute right-4 top-1/2 -translate-y-1/2 z-10 px-3 py-1 rounded bg-black/70 text-white text-2xl hover:bg-black">›</button>
              <img src={photos[lightboxIndex].photo_url} alt={photos[lightboxIndex].caption || `Photo ${lightboxIndex + 1}`} className="w-full max-h-[90vh] object-contain" />
              {photos[lightboxIndex].caption && <div className="absolute bottom-0 left-0 right-0 px-4 py-2 bg-black/70 text-white text-sm">{photos[lightboxIndex].caption}</div>}
              <div className="absolute bottom-4 right-4 px-3 py-1 rounded bg-black/70 text-white text-xs">{lightboxIndex + 1} / {photos.length}</div>
            </div>
          </div>
        )}
      </div>
      </div>
    );
  }

  // Modal mode (legacy, kept for backward compatibility)
  return (
    <div>
      <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4 overflow-y-auto">
        <div className="bg-white rounded-xl shadow-xl max-w-6xl w-full max-h-[95vh] overflow-y-auto my-8">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between z-10">
            <div>
              <h2 className="text-2xl font-semibold text-slate-900">{route.title}</h2>
              {route.county && (
                <p className="text-slate-600 text-sm mt-1">{route.county}</p>
              )}
            </div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onClose();
            }}
            className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors text-sm font-medium"
          >
            Close
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Route Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            {route.distance && (
              <div>
                <span className="text-slate-500">Distance</span>
                <p className="font-semibold text-slate-900">
                  {route.distance > 1000 ? `${(route.distance / 1000).toFixed(1)} km` : `${Math.round(route.distance)} m`}
                </p>
              </div>
            )}
            {formatTimeRange() && (
              <div>
                <span className="text-slate-500">Time</span>
                <p className="font-semibold text-slate-900">{formatTimeRange()}</p>
              </div>
            )}
            {route.grade && (
              <div>
                <span className="text-slate-500">Grade</span>
                <p className="font-semibold text-slate-900 capitalize">{route.grade}</p>
              </div>
            )}
            {route.country && (
              <div>
                <span className="text-slate-500">Country</span>
                <p className="font-semibold text-slate-900">{route.country}</p>
              </div>
            )}
          </div>

          {/* Interactive Map */}
          {route.gpx_url && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-base font-semibold text-slate-900">Route Map</h3>
                {(hasPurchasedGuidebook === true || !route.guidebook_id) ? (
                  <a
                    href={route.gpx_url.startsWith('http') ? route.gpx_url : `${API_BASE}${route.gpx_url}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    download
                    className="inline-flex items-center px-4 py-2 text-sm bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors"
                  >
                    Download GPX
                    <svg className="ml-1.5 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                  </a>
                ) : (
                  <div className="inline-flex items-center px-4 py-2 text-sm bg-slate-300 text-slate-600 rounded-lg cursor-not-allowed">
                    <svg className="mr-1.5 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                    GPX Locked
                  </div>
                )}
              </div>
              <div className="border border-slate-200 rounded-lg overflow-hidden">
                <RouteMap 
                  gpxUrl={route.gpx_url} 
                  routeTitle={route.title} 
                  interactive={true}
                  height="300px"
                  photos={photos}
                />
              </div>
            </div>
          )}

          {/* Description */}
          {route.description && (
            <div>
              <h3 className="text-base font-semibold text-slate-900 mb-2">Description</h3>
              <div className="prose prose-slate max-w-none">
                <p className="text-slate-700 whitespace-pre-wrap">{route.description}</p>
              </div>
            </div>
          )}

          {/* Photos */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-base font-semibold text-slate-900">Photos</h3>
              <div className="flex items-center gap-2">
                {isAdmin && photos.length > 0 && (
                  <button
                    type="button"
                    onClick={handleReprocessGPS}
                    disabled={reprocessingGPS}
                    className="text-xs text-sky-600 hover:text-sky-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Re-process photos to extract GPS coordinates from EXIF data"
                  >
                    {reprocessingGPS ? "Processing..." : "Extract GPS from Photos"}
                  </button>
                )}
                {isAdmin && (
                  <button
                    onClick={() => setShowPhotoUpload(!showPhotoUpload)}
                    className="px-3 py-1.5 text-sm bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors"
                  >
                    {showPhotoUpload ? "Cancel" : "Add Photo"}
                  </button>
                )}
              </div>
            </div>

            {isAdmin && showPhotoUpload && (
              <div className="mb-4 p-4 bg-slate-50 rounded-lg border border-slate-200">
                <form onSubmit={handlePhotoUpload}>
                  <div className="space-y-3">
                    <div>
                      <label htmlFor="route_photo_file" className="block text-sm font-medium text-slate-700 mb-1">
                        Photos (multiple allowed)
                      </label>
                      <input
                        type="file"
                        id="route_photo_file"
                        accept="image/*"
                        multiple
                        onChange={(e) => setPhotoFiles(Array.from(e.target.files || []))}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                        required
                      />
                      {photoFiles.length > 0 && (
                        <p className="mt-1 text-xs text-slate-500">
                          {photoFiles.length} file{photoFiles.length !== 1 ? 's' : ''} selected
                        </p>
                      )}
                    </div>
                    {photoUploadError && (
                      <div className="text-red-600 text-sm">{photoUploadError}</div>
                    )}
                    <button
                      type="submit"
                      disabled={photoUploading || photoFiles.length === 0}
                      className="px-4 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {photoUploading ? "Uploading..." : `Upload ${photoFiles.length > 0 ? photoFiles.length : ''} Photo${photoFiles.length !== 1 ? 's' : ''}`}
                    </button>
                  </div>
                </form>
              </div>
            )}

            {photosLoading ? (
              <div className="text-slate-600">Loading photos...</div>
            ) : photosError ? (
              <div className="text-red-600">Error loading photos: {photosError}</div>
            ) : photos.length === 0 ? (
              <div className="text-slate-500 text-sm">No photos yet.</div>
            ) : (
              <div className="grid grid-cols-3 md:grid-cols-5 gap-2">
                {photos.map((photo, index) => (
                  <button
                    key={photo.id}
                    type="button"
                    onClick={() => openLightbox(index)}
                    className="relative aspect-square overflow-hidden rounded-lg border border-slate-200 hover:shadow-md transition-shadow"
                  >
                    <img
                      src={photo.thumbnail_url || photo.photo_url}
                      alt={photo.caption || `Photo ${photo.id}`}
                      className="w-full h-full object-cover"
                      onError={(e) => (e.target.src = photo.photo_url)}
                    />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Links Section */}
          <div className="space-y-4">
            {/* Strava Activities */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-base font-semibold text-slate-900">Strava Activities</h3>
                {isAdmin && (
                  <button
                    onClick={() => setShowStravaInput(!showStravaInput)}
                    className="px-3 py-1.5 text-sm bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
                  >
                    {showStravaInput ? "Cancel" : "Add Activity"}
                  </button>
                )}
              </div>

              {isAdmin && showStravaInput && (
                <div className="mb-3 p-4 bg-slate-50 rounded-lg border border-slate-200">
                  <form onSubmit={handleAddStravaActivity}>
                    <div className="space-y-3">
                      <div>
                        <label htmlFor="strava_activity_url" className="block text-sm font-medium text-slate-700 mb-1">
                          Strava Activity URL or ID
                        </label>
                        <input
                          type="text"
                          id="strava_activity_url"
                          value={stravaActivityUrl}
                          onChange={(e) => setStravaActivityUrl(e.target.value)}
                          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                          placeholder="https://www.strava.com/activities/123456789 or 123456789"
                          required
                        />
                      </div>
                      <button
                        type="submit"
                        disabled={stravaUpdating || !stravaActivityUrl.trim()}
                        className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {stravaUpdating ? "Adding..." : "Add Activity"}
                      </button>
                    </div>
                  </form>
                </div>
              )}

              {stravaActivities.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {stravaActivities.map((activity, index) => {
                    const activityId = activity.match(/activities\/(\d+)/)?.[1] || activity;
                    const activityUrl = activity.startsWith('http') 
                      ? activity 
                      : `https://www.strava.com/activities/${activityId}`;
                    
                    return (
                      <a
                        key={index}
                        href={activityUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors text-sm font-medium"
                      >
                        Strava Activity {index + 1}
                        <svg
                          className="ml-1.5 w-4 h-4"
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
                    );
                  })}
                </div>
              ) : (
                <div className="text-slate-500">No Strava activities added yet.</div>
              )}
            </div>

            {/* Google MyMap */}
            {route.google_mymap_url && (
              <div>
                <h3 className="text-base font-semibold text-slate-900 mb-2">Google MyMap</h3>
                {(hasPurchasedGuidebook === true || !route.guidebook_id) ? (
                  <div className="space-y-2">
                    <a
                      href={route.google_mymap_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                    >
                      View & Copy Map
                      <svg
                        className="ml-1.5 w-4 h-4"
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
                    <p className="text-sm text-slate-500">
                      Click to open the map, then use the menu (⋮) next to the map title to "Copy map" to your own My Maps
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="inline-flex items-center px-4 py-2 bg-slate-300 text-slate-600 rounded-lg text-sm font-medium cursor-not-allowed">
                      <svg className="mr-1.5 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                      </svg>
                      Locked - Purchase Guidebook to Unlock
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Komoot Collections */}
            {komootCollections.length > 0 && (
              <div>
                <h3 className="text-base font-semibold text-slate-900 mb-2">Komoot Collections</h3>
                {(hasPurchasedGuidebook === true || !route.guidebook_id) ? (
                  <div className="flex flex-wrap gap-2">
                    {komootCollections.map((collection, index) => {
                      const collectionUrl = collection.startsWith('http')
                        ? collection
                        : `https://www.komoot.com/collection/${collection}`;
                      
                      return (
                        <a
                          key={index}
                          href={collectionUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
                        >
                          Komoot Collection {index + 1}
                          <svg
                            className="ml-1.5 w-4 h-4"
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
                      );
                    })}
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="inline-flex items-center px-4 py-2 bg-slate-300 text-slate-600 rounded-lg text-sm font-medium cursor-not-allowed">
                      <svg className="mr-1.5 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                      </svg>
                      Locked - Purchase Guidebook to Unlock
                    </div>
                    <p className="text-sm text-slate-500">
                      These collections are only available to users who have purchased the guidebook
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Lightbox */}
      {lightboxOpen && photos.length > 0 && (
        <div
          className="fixed inset-0 z-60 bg-black/90 flex items-center justify-center"
          onClick={closeLightbox}
        >
          <div
            className="relative max-w-5xl w-full mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={closeLightbox}
              className="absolute top-4 right-4 z-10 px-3 py-1 rounded bg-black/70 text-white text-sm hover:bg-black"
            >
              Close
            </button>
            <button
              onClick={prevPhoto}
              className="absolute left-4 top-1/2 -translate-y-1/2 z-10 px-3 py-1 rounded bg-black/70 text-white text-2xl hover:bg-black"
            >
              ‹
            </button>
            <button
              onClick={nextPhoto}
              className="absolute right-4 top-1/2 -translate-y-1/2 z-10 px-3 py-1 rounded bg-black/70 text-white text-2xl hover:bg-black"
            >
              ›
            </button>
            <img
              src={photos[lightboxIndex].photo_url}
              alt={photos[lightboxIndex].caption || `Photo ${lightboxIndex + 1}`}
              className="w-full max-h-[90vh] object-contain"
            />
            {photos[lightboxIndex].caption && (
              <div className="absolute bottom-0 left-0 right-0 px-4 py-2 bg-black/70 text-white text-sm">
                {photos[lightboxIndex].caption}
              </div>
            )}
            <div className="absolute bottom-4 right-4 px-3 py-1 rounded bg-black/70 text-white text-xs">
              {lightboxIndex + 1} / {photos.length}
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  );
}
