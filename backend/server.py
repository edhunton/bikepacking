import logging
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file BEFORE importing routers
# This ensures env vars are available when routers are imported
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

import uvicorn
from fastapi import FastAPI

from api.v1.books.router import router as books_router
from api.v1.blog_posts.router import router as blog_posts_router
from api.v1.strava.router import router as strava_router
from api.v1.komoot.router import router as komoot_router
from api.v1.instagram.router import router as instagram_router

# Use uvicorn's logger so messages appear with the server output.
logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Visible console confirmation when the server boots.
    logger.info("Bikepacking API server started")
    yield
    # Add any shutdown logging/cleanup here if needed.


app = FastAPI(lifespan=lifespan)


# Mount versioned routers
app.include_router(books_router, prefix="/api/v1/books")
app.include_router(blog_posts_router, prefix="/api/v1/blog_posts")
app.include_router(strava_router, prefix="/api/v1/strava")
app.include_router(komoot_router, prefix="/api/v1/komoot")
app.include_router(instagram_router, prefix="/api/v1/instagram")


if __name__ == "__main__":
    # Running directly: python backend/server.py
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)