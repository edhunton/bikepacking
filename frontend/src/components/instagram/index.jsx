import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

// Lightbox component for viewing full-size images
function Lightbox({ media, isOpen, onClose, onNext, onPrevious, hasNext, hasPrevious }) {
  if (!isOpen || !media) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-90 p-4"
      onClick={onClose}
    >
      <div className="relative max-w-7xl max-h-full w-full h-full flex items-center justify-center">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-white hover:text-gray-300 z-10 bg-black bg-opacity-50 rounded-full p-2 transition-colors"
          aria-label="Close"
        >
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>

        {/* Navigation buttons */}
        {hasPrevious && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onPrevious();
            }}
            className="absolute left-4 text-white hover:text-gray-300 z-10 bg-black bg-opacity-50 rounded-full p-3 transition-colors"
            aria-label="Previous"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
          </button>
        )}

        {hasNext && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onNext();
            }}
            className="absolute right-4 text-white hover:text-gray-300 z-10 bg-black bg-opacity-50 rounded-full p-3 transition-colors"
            aria-label="Next"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5l7 7-7 7"
              />
            </svg>
          </button>
        )}

        {/* Media content */}
        <div
          className="max-w-full max-h-full flex items-center justify-center"
          onClick={(e) => e.stopPropagation()}
        >
          {media.media_type === "VIDEO" ? (
            <video
              src={media.media_url}
              controls
              className="max-w-full max-h-[90vh] rounded-lg"
              autoPlay
            />
          ) : (
            <img
              src={media.media_url}
              alt={media.caption || "Instagram post"}
              className="max-w-full max-h-[90vh] object-contain rounded-lg"
            />
          )}
        </div>

        {/* Caption */}
        {media.caption && (
          <div
            className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-75 text-white p-4 rounded-b-lg"
            onClick={(e) => e.stopPropagation()}
          >
            <p className="text-sm line-clamp-3">{media.caption}</p>
            {media.permalink && (
              <a
                href={media.permalink}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sky-400 hover:text-sky-300 text-xs mt-2 inline-block"
              >
                View on Instagram →
              </a>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Thumbnail component
function MediaThumbnail({ media, onClick }) {
  const [imageError, setImageError] = useState(false);

  if (imageError || !media.media_url) {
    return (
      <div
        onClick={onClick}
        className="aspect-square bg-slate-100 border border-slate-200 rounded-lg flex items-center justify-center hover:bg-slate-200 transition-colors cursor-pointer"
      >
        <svg
          className="w-8 h-8 text-slate-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
      </div>
    );
  }

  return (
    <div
      onClick={onClick}
      className="aspect-square relative rounded-lg overflow-hidden border border-slate-200 hover:shadow-lg transition-shadow cursor-pointer group"
    >
      <img
        src={media.media_url}
        alt={media.caption || "Instagram post"}
        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
        onError={() => setImageError(true)}
      />
      
      {/* Media type indicator */}
      {media.media_type === "VIDEO" && (
        <div className="absolute top-2 right-2 bg-black bg-opacity-60 rounded-full p-1.5">
          <svg
            className="w-4 h-4 text-white"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
          </svg>
        </div>
      )}

      {media.media_type === "CAROUSEL_ALBUM" && (
        <div className="absolute top-2 right-2 bg-black bg-opacity-60 rounded-full p-1.5">
          <svg
            className="w-4 h-4 text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
        </div>
      )}

      {/* Caption preview on hover */}
      {media.caption && (
        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-all duration-300 flex items-end p-3">
          <p className="text-white text-xs line-clamp-2 opacity-0 group-hover:opacity-100 transition-opacity">
            {media.caption}
          </p>
        </div>
      )}
    </div>
  );
}

export default function Instagram() {
  const [media, setMedia] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [selectedMediaIndex, setSelectedMediaIndex] = useState(0);
  const [limit, setLimit] = useState(12);

  // Load Instagram media
  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const params = new URLSearchParams({
          limit: limit.toString(),
          use_cache: "true",
        });

        const res = await fetch(`${API_BASE}/api/v1/instagram/media?${params.toString()}`);
        if (!res.ok) {
          throw new Error(`Request failed: ${res.status}`);
        }
        const data = await res.json();

        if (!cancelled) {
          setMedia(data);
          console.log("Instagram media API response:", data);
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
  }, [limit]);

  // Handle keyboard navigation in lightbox
  useEffect(() => {
    if (!lightboxOpen) return;

    function handleKeyDown(e) {
      if (e.key === "Escape") {
        setLightboxOpen(false);
      } else if (e.key === "ArrowLeft" && selectedMediaIndex > 0) {
        setSelectedMediaIndex(selectedMediaIndex - 1);
      } else if (e.key === "ArrowRight" && selectedMediaIndex < media.length - 1) {
        setSelectedMediaIndex(selectedMediaIndex + 1);
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [lightboxOpen, selectedMediaIndex, media.length]);

  const openLightbox = (index) => {
    setSelectedMediaIndex(index);
    setLightboxOpen(true);
  };

  const closeLightbox = () => {
    setLightboxOpen(false);
  };

  const nextMedia = () => {
    if (selectedMediaIndex < media.length - 1) {
      setSelectedMediaIndex(selectedMediaIndex + 1);
    }
  };

  const previousMedia = () => {
    if (selectedMediaIndex > 0) {
      setSelectedMediaIndex(selectedMediaIndex - 1);
    }
  };

  // Flatten carousel albums to show all children
  const flattenedMedia = media.flatMap((item) => {
    if (item.media_type === "CAROUSEL_ALBUM" && item.children && item.children.length > 0) {
      return item.children.map((child) => ({
        ...child,
        parentCaption: item.caption,
        parentPermalink: item.permalink,
      }));
    }
    return [item];
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-slate-600">Loading Instagram posts...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading Instagram posts: {error}</p>
      </div>
    );
  }

  if (media.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-600">No Instagram posts found.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-800 mb-2">Instagram Posts</h2>
        <p className="text-slate-600">
          Showing {flattenedMedia.length} post{flattenedMedia.length !== 1 ? "s" : ""}
        </p>
      </div>

      {/* Media grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {flattenedMedia.map((item, index) => (
          <MediaThumbnail
            key={item.id || index}
            media={item}
            onClick={() => openLightbox(index)}
          />
        ))}
      </div>

      {/* Load more button */}
      {media.length >= limit && (
        <div className="mt-8 text-center">
          <button
            onClick={() => setLimit(limit + 12)}
            className="px-6 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors"
          >
            Load More
          </button>
        </div>
      )}

      {/* Lightbox */}
      <Lightbox
        media={flattenedMedia[selectedMediaIndex]}
        isOpen={lightboxOpen}
        onClose={closeLightbox}
        onNext={nextMedia}
        onPrevious={previousMedia}
        hasNext={selectedMediaIndex < flattenedMedia.length - 1}
        hasPrevious={selectedMediaIndex > 0}
      />
    </div>
  );
}


