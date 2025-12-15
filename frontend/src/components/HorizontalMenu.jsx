export default function HorizontalMenu({ activeSection, onSectionChange }) {
  const menuItems = [
    { id: "books", label: "Books" },
    { id: "routes", label: "Routes" },
    { id: "tours", label: "Tours" },
    { id: "blog-posts", label: "Blog Posts" },
    { id: "strava", label: "Strava" },
    { id: "komoot", label: "Komoot" },
    { id: "instagram", label: "Instagram" },
    { id: "recipes", label: "Recipes" },
  ];

  return (
    <nav className="bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <ul className="flex items-center gap-4 sm:gap-8 whitespace-nowrap overflow-x-auto py-2">
          {menuItems.map((item) => (
            <li key={item.id} className="flex-shrink-0">
              <button
                onClick={() => onSectionChange(item.id)}
                className={`block py-3 px-2 text-sm sm:text-base font-medium transition-colors ${
                  activeSection === item.id
                    ? "text-slate-700 border-b-2 border-sky-600"
                    : "text-slate-600 hover:text-sky-600"
                }`}
              >
                {item.label}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}
