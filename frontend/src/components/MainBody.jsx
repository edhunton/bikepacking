import Books from "./Books";
import Routes from "./Routes";
import Tours from "./Tours";
import BlogPosts from "./BlogPosts";
import Recipes from "./Recipes";

export default function MainBody({ activeSection, books, loading, error }) {
  const renderSection = () => {
    switch (activeSection) {
      case "books":
        return <Books books={books} loading={loading} error={error} />;
      case "routes":
        return <Routes />;
      case "tours":
        return <Tours />;
      case "blog-posts":
        return <BlogPosts />;
      case "recipes":
        return <Recipes />;
      default:
        return <Books books={books} loading={loading} error={error} />;
    }
  };

  return (
    <main className="max-w-7xl mx-auto px-6 py-8">{renderSection()}</main>
  );
}
