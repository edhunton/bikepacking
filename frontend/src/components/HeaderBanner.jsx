import { useState, useEffect } from "react";

// List of image filenames in the public/images folder
// Add your image files to frontend/public/images/ and update this list
const BANNER_IMAGES = [
  "banner1.jpg",
  "banner2.jpg",
  "banner3.jpg",
  "banner4.jpg",
  "banner5.jpg",
];

export default function HeaderBanner() {
  const [randomImage, setRandomImage] = useState("");

  useEffect(() => {
    // Select a random image on component mount
    if (BANNER_IMAGES.length > 0) {
      const randomIndex = Math.floor(Math.random() * BANNER_IMAGES.length);
      setRandomImage(BANNER_IMAGES[randomIndex]);
    }
  }, []);

  const imagePath = randomImage ? `/images/${randomImage}` : null;

  return (
    <header className="relative bg-gradient-to-r from-sky-600 to-blue-700 text-white overflow-hidden">
      {imagePath && (
        <div className="absolute inset-0 opacity-30">
          <img
            src={imagePath}
            alt="Bikepacking banner"
            className="w-full h-full object-cover"
          />
        </div>
      )}
      <div className="relative max-w-7xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold">Bikepacking Books</h1>
      </div>
    </header>
  );
}
