import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export default function BlogPosts() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const res = await fetch(`${API_BASE}/api/v1/blog_posts/`);
        if (!res.ok) {
          throw new Error(`Request failed: ${res.status}`);
        }
        const data = await res.json();
        console.log('Blog posts API response:', data);
        console.log('Number of posts:', data?.length);
        if (!cancelled) {
          setPosts(data || []);
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
  }, []);

  const formatDate = (dateString) => {
    if (!dateString) return "";
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
      });
    } catch {
      return dateString;
    }
  };

  return (
    <section className="bg-white rounded-xl p-6 shadow-lg border border-slate-200">
      <div className="flex items-center gap-2 mb-6">
        <h2 className="text-2xl font-semibold text-slate-900">Blog Posts</h2>
        {loading && (
          <span className="inline-block px-2.5 py-1 rounded-full bg-sky-100 text-sky-600 text-xs">
            Loading
          </span>
        )}
        {error && (
          <span className="inline-block px-2.5 py-1 rounded-full bg-red-100 text-red-600 text-xs">
            Error
          </span>
        )}
      </div>

      {error ? (
        <p className="text-red-600 m-0">Failed to load posts: {error}</p>
      ) : posts.length === 0 && !loading ? (
        <p className="text-slate-400 m-0">No blog posts found.</p>
      ) : (
        <div className="flex flex-col gap-6">
          {posts.map((post, index) => (
            <article
              key={index}
              className="border-b border-slate-200 pb-6 last:border-b-0 last:pb-0"
            >
              <div className="flex flex-col md:flex-row gap-4">
                {post.thumbnail && (
                  <div className="md:w-48 md:flex-shrink-0">
                    <img
                      src={post.thumbnail}
                      alt={post.title}
                      className="w-full h-32 object-cover rounded-lg"
                    />
                  </div>
                )}
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-slate-900 mb-2">
                    <a
                      href={post.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-sky-600 transition-colors"
                    >
                      {post.title}
                    </a>
                  </h3>
                  <div className="flex items-center gap-3 text-sm text-slate-500 mb-3">
                    <span>{post.author}</span>
                    {post.published && (
                      <>
                        <span>•</span>
                        <time dateTime={post.published}>
                          {formatDate(post.published)}
                        </time>
                      </>
                    )}
                  </div>
                  {post.excerpt && (
                    <p className="text-slate-600 mb-3 line-clamp-3">
                      {post.excerpt}
                    </p>
                  )}
                  <a
                    href={post.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center text-sky-600 hover:text-sky-700 font-medium text-sm"
                  >
                    Read on Medium
                    <svg
                      className="ml-1 w-4 h-4"
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
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
