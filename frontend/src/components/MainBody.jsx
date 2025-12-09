import Books from "./books";
import Routes from "./routes";
import Tours from "./tours";
import BlogPosts from "./blog-posts";
import StravaActivities from "./strava";
import Recipes from "./recipes";

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
      case "strava":
        return <StravaActivities />;
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
