import { useState, useEffect } from "react";
import bannerManifest from "../banner-manifest.js";

// Automatically loaded from the banners folder via build script
// Run 'npm run generate-banners' to update this list when adding new images
const BANNER_IMAGES = bannerManifest.banners || [];

export default function HeaderBanner() {
  const [randomImage, setRandomImage] = useState("");

  useEffect(() => {
    // Select a random image on component mount
    if (BANNER_IMAGES.length > 0) {
      const randomIndex = Math.floor(Math.random() * BANNER_IMAGES.length);
      setRandomImage(BANNER_IMAGES[randomIndex]);
    }
  }, []);

  const imagePath = randomImage ? `/images/banners/${randomImage}` : null;

  return (
    <header className="hidden md:block relative bg-gradient-to-r from-sky-600 to-blue-700 text-white overflow-hidden h-[640px]">
      {imagePath && (
        <div className="absolute inset-0 opacity-30">
          <img
            src={imagePath}
            alt="Bikepacking banner"
            className="w-full h-full object-cover"
          />
        </div>
      )}
    </header>
  );
}
