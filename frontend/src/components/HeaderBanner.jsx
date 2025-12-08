export default function HeaderBanner() {
  return (
    <header className="bg-gradient-to-r from-sky-600 to-blue-700 text-white">
      <div className="max-w-7xl mx-auto px-6 py-12">
        <p className="tracking-wider uppercase text-xs text-sky-100 mb-2">
          Bikepacking API
        </p>
        <h1 className="text-4xl font-bold mb-2">Bikepacking Books</h1>
        <p className="text-sky-100 text-lg">
          Discover guidebooks for your next adventure
        </p>
      </div>
    </header>
  );
}
