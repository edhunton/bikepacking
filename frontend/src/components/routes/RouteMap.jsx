import { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";
const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN ?? "";

// GPX parser to extract coordinates from various GPX formats
function parseGPX(gpxText) {
  const parser = new DOMParser();
  const xmlDoc = parser.parseFromString(gpxText, "text/xml");
  const coordinates = [];

  // Check for parse errors
  const parseError = xmlDoc.querySelector("parsererror");
  if (parseError) {
    throw new Error("Invalid GPX file format");
  }

  // Try to get track points (trkpt) - most common format
  const trackPoints = xmlDoc.querySelectorAll("trkpt");
  if (trackPoints.length > 0) {
    trackPoints.forEach((point) => {
      const lat = parseFloat(point.getAttribute("lat"));
      const lon = parseFloat(point.getAttribute("lon"));
      if (!isNaN(lat) && !isNaN(lon)) {
        coordinates.push([lon, lat]); // Mapbox uses [lng, lat]
      }
    });
  }

  // If no track points, try waypoints (wpt)
  if (coordinates.length === 0) {
    const waypoints = xmlDoc.querySelectorAll("wpt");
    waypoints.forEach((point) => {
      const lat = parseFloat(point.getAttribute("lat"));
      const lon = parseFloat(point.getAttribute("lon"));
      if (!isNaN(lat) && !isNaN(lon)) {
        coordinates.push([lon, lat]);
      }
    });
  }

  // If still no coordinates, try route points (rtept)
  if (coordinates.length === 0) {
    const routePoints = xmlDoc.querySelectorAll("rtept");
    routePoints.forEach((point) => {
      const lat = parseFloat(point.getAttribute("lat"));
      const lon = parseFloat(point.getAttribute("lon"));
      if (!isNaN(lat) && !isNaN(lon)) {
        coordinates.push([lon, lat]);
      }
    });
  }

  return coordinates;
}

export default function RouteMap({ gpxUrl, routeTitle }) {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const markersRef = useRef([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Initialize map once
  useEffect(() => {
    if (!mapContainer.current || !MAPBOX_TOKEN) {
      if (!MAPBOX_TOKEN) {
        setError("Mapbox token not configured");
      }
      setLoading(false);
      return;
    }

    if (!map.current) {
      mapboxgl.accessToken = MAPBOX_TOKEN;
      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: "mapbox://styles/mapbox/outdoors-v12",
        center: [0, 0],
        zoom: 2,
      });
    }

    // Cleanup on unmount
    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  // Load GPX when URL changes
  useEffect(() => {
    if (!gpxUrl || !map.current) {
      setLoading(false);
      return;
    }

    // Fetch and parse GPX file
    const fetchGPX = async () => {
      try {
        setLoading(true);
        setError("");

        // Handle both full URLs and relative paths
        const url = gpxUrl.startsWith("http") 
          ? gpxUrl 
          : `${API_BASE}${gpxUrl.startsWith("/") ? "" : "/"}${gpxUrl}`;

        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`Failed to fetch GPX: ${response.status}`);
        }

        const gpxText = await response.text();
        const coordinates = parseGPX(gpxText);

        if (coordinates.length === 0) {
          throw new Error("No coordinates found in GPX file");
        }

        // Calculate bounds
        const lngs = coordinates.map((coord) => coord[0]);
        const lats = coordinates.map((coord) => coord[1]);
        const bounds = [
          [Math.min(...lngs), Math.min(...lats)],
          [Math.max(...lngs), Math.max(...lats)],
        ];

        // Function to add route to map
        const addRouteToMap = () => {
          // Remove existing source and layer if they exist
          if (map.current.getSource("route")) {
            map.current.removeLayer("route");
            map.current.removeSource("route");
          }

          // Remove existing markers
          markersRef.current.forEach((marker) => marker.remove());
          markersRef.current = [];

          // Add route as a line
          map.current.addSource("route", {
            type: "geojson",
            data: {
              type: "Feature",
              properties: {},
              geometry: {
                type: "LineString",
                coordinates: coordinates,
              },
            },
          });

          map.current.addLayer({
            id: "route",
            type: "line",
            source: "route",
            layout: {
              "line-join": "round",
              "line-cap": "round",
            },
            paint: {
              "line-color": "#3b82f6",
              "line-width": 4,
            },
          });

          // Add start marker
          if (coordinates.length > 0) {
            new mapboxgl.Marker({ color: "#10b981" })
              .setLngLat(coordinates[0])
              .setPopup(new mapboxgl.Popup().setText("Start"))
              .addTo(map.current);
          }

          // Add end marker
          if (coordinates.length > 1) {
            new mapboxgl.Marker({ color: "#ef4444" })
              .setLngLat(coordinates[coordinates.length - 1])
              .setPopup(new mapboxgl.Popup().setText("End"))
              .addTo(map.current);
          }

          // Fit map to route bounds
          map.current.fitBounds(bounds, {
            padding: 50,
            maxZoom: 14,
          });

          setLoading(false);
        };

        // Wait for map to load, then add route
        if (map.current.loaded()) {
          addRouteToMap();
        } else {
          map.current.once("load", addRouteToMap);
        }
      } catch (err) {
        console.error("Error loading GPX:", err);
        setError(err.message);
        setLoading(false);
      }
    };

    fetchGPX();

    // Cleanup function
    return () => {
      // Remove route layer
      if (map.current && map.current.getSource("route")) {
        if (map.current.getLayer("route")) {
          map.current.removeLayer("route");
        }
        map.current.removeSource("route");
      }
      // Remove markers
      markersRef.current.forEach((marker) => marker.remove());
      markersRef.current = [];
    };
  }, [gpxUrl, routeTitle]);

  if (!MAPBOX_TOKEN) {
    return (
      <div className="h-64 bg-slate-100 rounded-lg flex items-center justify-center text-slate-600 text-sm p-4 text-center">
        Mapbox token not configured. Set VITE_MAPBOX_ACCESS_TOKEN in your .env file.
        <br />
        <a 
          href="https://account.mapbox.com/" 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-sky-600 hover:text-sky-700 underline mt-2 inline-block"
        >
          Get a free token →
        </a>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-64 bg-red-50 border border-red-200 rounded-lg flex items-center justify-center text-red-600">
        Error loading map: {error}
      </div>
    );
  }

  return (
    <div className="relative">
      {loading && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10 rounded-lg">
          <div className="text-slate-600 text-xs">Loading...</div>
        </div>
      )}
      <div
        ref={mapContainer}
        className="w-full h-32 rounded-lg overflow-hidden"
        style={{ minHeight: "128px", height: "128px" }}
      />
    </div>
  );
}
