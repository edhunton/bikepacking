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
      <div className="max-w-7xl mx-auto px-6">
        <ul className="flex gap-8">
          {menuItems.map((item) => (
            <li key={item.id}>
              <button
                onClick={() => onSectionChange(item.id)}
                className={`block py-4 px-2 font-medium transition-colors ${
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
