import os
import ssl
from datetime import datetime
from typing import List, Optional

# Set up SSL context before importing feedparser
# This allows feedparser to use the unverified SSL context
ssl._create_default_https_context = ssl._create_unverified_context

import feedparser
import logging

from .models import BlogPost

logger = logging.getLogger("uvicorn.error")

# Default Medium usernames - can be overridden via query parameter or MEDIUM_USERNAMES env var
# Comma-separated list of Medium usernames
DEFAULT_MEDIUM_USERNAMES = os.getenv("MEDIUM_USERNAMES", "midlifecycles,bivvytobothy,nicky-eds-adventures").split(",")


def extract_thumbnail_from_content(content: str) -> Optional[str]:
    """Extract thumbnail image URL from HTML content."""
    if not content:
        return None
    
    # Look for img tags in the content
    import re
    img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
    if img_match:
        return img_match.group(1)
    return None


def clean_html_excerpt(html_content: str, max_length: int = 200) -> str:
    """Extract plain text excerpt from HTML content."""
    if not html_content:
        return ""
    
    import re
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html_content)
    # Clean up whitespace
    text = ' '.join(text.split())
    # Truncate to max_length
    if len(text) > max_length:
        text = text[:max_length].rsplit(' ', 1)[0] + '...'
    return text


def get_blog_posts(
    usernames: Optional[str] = None,
    include_content: bool = False
) -> List[BlogPost]:
    """
    Fetch blog posts from Medium RSS feed(s).
    
    Args:
        usernames: Comma-separated list of Medium usernames (without @). If not provided, uses defaults.
        include_content: Include full post content (default: False, only excerpt)
    
    Returns:
        List of BlogPost objects sorted by published date (newest first)
    """
    # Parse usernames from parameter or use defaults
    if usernames:
        medium_usernames = [u.strip() for u in usernames.split(",") if u.strip()]
    else:
        medium_usernames = [u.strip() for u in DEFAULT_MEDIUM_USERNAMES if u.strip()]
    
    if not medium_usernames:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="No Medium usernames provided"
        )
    
    all_posts = []
    
    # Fetch posts from each username
    for medium_username in medium_usernames:
        # Construct RSS feed URL (format: https://medium.com/feed/username)
        rss_url = f"https://medium.com/feed/{medium_username}"
        
        try:
            # Parse RSS feed
            logger.info(f"Fetching Medium RSS feed: {rss_url}")
            # SSL context is already set globally at module level
            feed = feedparser.parse(rss_url)
            
            logger.info(f"Feed status: {getattr(feed, 'status', 'N/A')}")
            logger.info(f"Feed bozo: {feed.bozo}")
            logger.info(f"Feed entries type: {type(feed.entries)}")
            logger.info(f"Number of entries: {len(feed.entries) if feed.entries else 0}")
            
            # Check if entries exist and is not empty
            if not feed.entries or len(feed.entries) == 0:
                logger.warning(f"No entries found in feed for {medium_username}. Bozo exception: {feed.bozo_exception if feed.bozo else 'None'}")
                if feed.bozo and feed.bozo_exception:
                    logger.warning(f"Bozo exception details: {feed.bozo_exception}")
                continue  # Skip this username and continue with next

            # If the parser flagged an issue and we have no entries, skip this feed
            if feed.bozo and feed.bozo_exception and not feed.entries:
                logger.warning(f"Error parsing RSS feed for {medium_username}: {feed.bozo_exception}")
                continue  # Skip this username and continue with next
            
            logger.info(f"Found {len(feed.entries)} entries in Medium feed for {medium_username}")
            
            # Process entries for this feed
            for idx, entry in enumerate(feed.entries):
                try:
                    # Extract thumbnail from content
                    thumbnail = None
                    if hasattr(entry, 'content') and entry.content:
                        thumbnail = extract_thumbnail_from_content(entry.content[0].value)
                    elif hasattr(entry, 'summary'):
                        thumbnail = extract_thumbnail_from_content(entry.summary)
                    
                    # Get excerpt
                    excerpt = ""
                    if hasattr(entry, 'summary'):
                        excerpt = clean_html_excerpt(entry.summary)
                    elif hasattr(entry, 'content') and entry.content:
                        excerpt = clean_html_excerpt(entry.content[0].value)
                    
                    # Get full content if requested
                    content = None
                    if include_content and hasattr(entry, 'content') and entry.content:
                        content = entry.content[0].value
                    
                    # Parse published date
                    published_str = ""
                    if hasattr(entry, 'published'):
                        try:
                            # Parse the date and format it
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                pub_date = datetime(*entry.published_parsed[:6])
                                published_str = pub_date.isoformat()
                            else:
                                published_str = entry.get('published', '')
                        except (AttributeError, ValueError, TypeError) as e:
                            published_str = entry.get('published', '')
                    
                    # Ensure we have required fields
                    title = entry.get('title', 'Untitled')
                    link = entry.get('link', '')
                    author = entry.get('author', 'Unknown')
                    
                    # Skip if we don't have essential fields
                    if not title or not link:
                        logger.warning(f"Skipping entry {idx} from {medium_username}: missing title or link")
                        continue
                    
                    # Create post object
                    post = BlogPost(
                        title=title,
                        link=link,
                        published=published_str,
                        author=author,
                        excerpt=excerpt,
                        content=content,
                        thumbnail=thumbnail
                    )
                    all_posts.append(post)
                    logger.info(f"Successfully created post from {medium_username}: {title[:50]}...")
                    
                except Exception as e:
                    logger.error(f"Error processing entry {idx} from {medium_username}: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    continue
        
        except Exception as exc:
            logger.error(f"Error fetching Medium posts for {medium_username}: {str(exc)}")
            # Continue with next username instead of failing completely
            continue
    
    # Sort posts by published date (newest first)
    try:
        all_posts.sort(key=lambda x: x.published if x.published else "", reverse=True)
    except Exception:
        pass  # If sorting fails, just return unsorted
    
    logger.info(f"Returning {len(all_posts)} blog posts from {len(medium_usernames)} Medium account(s)")
    
    return all_posts
