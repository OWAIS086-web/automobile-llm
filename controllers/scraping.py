import os
import time
import json
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
from tqdm import tqdm
from flask import current_app
from models.database import get_db_connection
from utils.logger import scraping_logger, warning_logger, log_error

# Configuration
BASE = "https://www.pakwheels.com/forums/"
DATA_DIR = "data"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9"
}
DEFAULT_DELAY = 0.6
DEFAULT_MAX_TOPICS = 500
DEFAULT_MAX_POSTS = 10000

def get_soup(url, timeout=15):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        scraping_logger.warning(f"Failed to GET {url}: {e}")
        return None


def get_json(url, timeout=15, max_retries=3):
    """
    Fetch JSON data from URL with retry mechanism and better error handling
    """
    for attempt in range(max_retries):
        try:
            scraping_logger.info(f"🔍 Fetching JSON (attempt {attempt + 1}/{max_retries}): {url}")
            resp = requests.get(url, headers=HEADERS, timeout=timeout)
            
            # Log response details for debugging
            scraping_logger.info(f"📊 Response status: {resp.status_code}")
            scraping_logger.info(f"📊 Response headers: {dict(resp.headers)}")
            scraping_logger.info(f"📊 Response content preview: {resp.text[:200]}...")
            
            resp.raise_for_status()
            
            # Check if response is actually JSON
            content_type = resp.headers.get('content-type', '').lower()
            if 'application/json' not in content_type and 'text/json' not in content_type:
                scraping_logger.warning(f"⚠️ Response is not JSON (content-type: {content_type})")
                # Check if it's an HTML error page
                if 'text/html' in content_type:
                    if 'page not found' in resp.text.lower() or '404' in resp.text:
                        scraping_logger.warning(f"📄 Page not found (404): {url}")
                        return None
                    elif 'access denied' in resp.text.lower() or 'forbidden' in resp.text.lower():
                        scraping_logger.warning(f"🚫 Access denied: {url}")
                        return None
                    else:
                        scraping_logger.warning(f"🌐 HTML response instead of JSON: {url}")
                        scraping_logger.warning(f"Response preview: {resp.text[:500]}...")
                        return None
            
            # Try to parse JSON
            try:
                json_data = resp.json()
                scraping_logger.info(f"✅ Successfully parsed JSON response")
                return json_data
            except json.JSONDecodeError as json_err:
                scraping_logger.warning(f"❌ JSON decode error: {json_err}")
                scraping_logger.warning(f"Response preview: {resp.text[:500]}...")
                if 'page not found' in resp.text.lower():
                    scraping_logger.warning(f"📄 Page not found response received")
                    return None
                # Continue to retry logic
                
        except requests.exceptions.Timeout:
            scraping_logger.warning(f"⏰ Timeout fetching JSON from {url} (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
        except requests.exceptions.ConnectionError:
            scraping_logger.warning(f"🔗 Connection error fetching JSON from {url} (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                scraping_logger.warning(f"📄 Post not found (404): {url}")
                return None  # Don't retry for 404s
            elif e.response.status_code == 429:
                scraping_logger.warning(f"🚫 Rate limited (429): {url} (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))  # Longer wait for rate limiting
            else:
                scraping_logger.warning(f"🌐 HTTP error {e.response.status_code} fetching JSON from {url} (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        except Exception as e:
            scraping_logger.warning(f"❌ Failed to GET JSON {url} (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    
    scraping_logger.error(f"💥 Failed to fetch JSON after {max_retries} attempts: {url}")
    return None


def fetch_categories():
    """Scrape forum main page and return category links (unique)."""
    soup = get_soup(BASE)
    if not soup:
        return []

    cats = []
    seen = set()
    for a in soup.select("a[href*='/forums/c/']"):
        name = a.get_text(strip=True)
        href = a.get("href")
        if not href or not name:
            continue
        full = urljoin(BASE, href)
        if full not in seen:
            cats.append({"name": name, "href": full})
            seen.add(full)
    # sort by name
    cats.sort(key=lambda x: x["name"].lower())
    return cats


def collect_all_topics_from_category(category_url, delay=DEFAULT_DELAY, max_topics=DEFAULT_MAX_TOPICS):
    """
    Walk pagination for a category and collect topic titles + urls until end or max_topics reached.
    Returns list of {title, href}
    """
    topics = []
    seen = set()
    page = 1
    while True:
        if page == 1:
            url = category_url
        else:
            # Discourse uses ?page=N for forum category pagination
            url = f"{category_url}?page={page}"
        scraping_logger.info(f"Fetching topic list: {url}")
        soup = get_soup(url)
        if not soup:
            break

        found_on_page = 0
        for a in soup.select("a[href*='/t/']"):
            href = a.get("href")
            if not href:
                continue
            full = urljoin(category_url, href)
            title = a.get_text(strip=True)
            if not title or full in seen:
                continue
            topics.append({"title": title, "href": full})
            seen.add(full)
            found_on_page += 1
            if len(topics) >= max_topics:
                return topics

        if found_on_page == 0:
            break
        page += 1
        time.sleep(delay)
    return topics


def fetch_posts_for_topic_via_json(topic_url, max_posts=DEFAULT_MAX_POSTS, delay=DEFAULT_DELAY, descending=False):
    """
    Fetch posts from a Discourse topic using JSON API.
    Gets LATEST posts when descending=True, OLDEST posts when descending=False.
    
    Args:
        topic_url: URL of the topic
        max_posts: Maximum number of posts to fetch
        delay: Delay between requests (not used in simplified version)
        descending: If True, fetch latest posts first (newest to oldest)
    """
    # Clean URL and validate format
    base_url = topic_url.rstrip("/").split("?")[0].split("#")[0]
    
    # Log the original and cleaned URLs for debugging
    scraping_logger.info(f"🔗 Original URL: {topic_url}")
    scraping_logger.info(f"🔗 Cleaned base URL: {base_url}")
    
    # Ensure the URL is in the correct format for PakWheels
    if not base_url.startswith("https://www.pakwheels.com/forums/t/"):
        scraping_logger.error(f"❌ Invalid PakWheels URL format: {base_url}")
        scraping_logger.error("Expected format: https://www.pakwheels.com/forums/t/topic-name/topic-id")
        return []
    
    json_url = base_url + ".json"
    scraping_logger.info(f"🔍 JSON URL: {json_url}")
    
    # Test basic connectivity first
    try:
        test_resp = requests.head(base_url, headers=HEADERS, timeout=10)
        scraping_logger.info(f"🌐 Base URL connectivity test: {test_resp.status_code}")
    except Exception as e:
        scraping_logger.warning(f"⚠️ Base URL connectivity test failed: {e}")
    
    scraping_logger.info(f"🔍 Fetching topic: {json_url}")
    
    # Try to get more posts if we want latest posts
    if descending:
        # For latest posts, try different approaches
        # First try the regular endpoint to see what we get
        data = get_json(json_url)
        
        if data:
            # Get topic metadata to check post numbers
            highest_post_number = data.get("highest_post_number", 0)
            
            # Check if we got recent posts
            post_stream = data.get("post_stream", {})
            posts_data = post_stream.get("posts", [])
            if posts_data:
                post_numbers = [p.get("post_number", 0) for p in posts_data if isinstance(p, dict)]
                if post_numbers:
                    max_found = max(post_numbers)
                    # If we're missing recent posts (more than 100 posts behind), try print version
                    if max_found < highest_post_number - 100:
                        scraping_logger.info(f"📡 Default response has posts up to #{max_found}, trying print version for more recent posts")
                        print_data = get_json(f"{json_url}?print=true")
                        if print_data:
                            print_post_stream = print_data.get("post_stream", {})
                            print_posts = print_post_stream.get("posts", [])
                            if len(print_posts) > len(posts_data):
                                scraping_logger.info(f"📡 Print version has {len(print_posts)} posts vs {len(posts_data)} in regular version")
                                data = print_data
    else:
        # Use regular endpoint for oldest posts
        data = get_json(json_url)
    
    if not data:
        scraping_logger.error(f"❌ Failed to fetch topic data from: {json_url}")
        scraping_logger.error("🔧 Possible causes:")
        scraping_logger.error("   • Topic may have been deleted or moved")
        scraping_logger.error("   • Network connectivity issues")
        scraping_logger.error("   • PakWheels server is down or blocking requests")
        scraping_logger.error("   • Rate limiting or firewall restrictions")
        scraping_logger.error("   • Invalid topic URL format")
        scraping_logger.error("💡 Try again later or check if the topic still exists")
        return []

    # Validate response structure
    if not isinstance(data, dict):
        scraping_logger.error(f"❌ Invalid response format - expected dict, got {type(data)}")
        return []

    # Get topic metadata
    topic_title = data.get("title", "")
    posts_count = data.get("posts_count", 0)
    highest_post_number = data.get("highest_post_number", posts_count)
    
    if posts_count == 0:
        scraping_logger.warning(f"⚠️ Topic has no posts: {topic_title}")
        return []
    
    scraping_logger.info(f"📊 Topic: '{topic_title[:50]}...'")
    scraping_logger.info(f"📊 Total posts: {posts_count} | Highest post #: {highest_post_number}")
    
    # Get posts from the response
    post_stream = data.get("post_stream", {})
    if not isinstance(post_stream, dict):
        scraping_logger.error("❌ Invalid post_stream format in topic data")
        return []
    
    # Get the posts from the response
    posts_data = post_stream.get("posts", [])
    scraping_logger.info(f"📊 Found {len(posts_data)} posts in response")
    
    # Process posts
    all_posts = []
    seen_post_ids = set()
    
    for p in posts_data:
        if not isinstance(p, dict):
            continue
            
        post_id = p.get("id")
        post_number = p.get("post_number", 0)
        
        # Skip duplicates
        if post_id in seen_post_ids:
            continue
        
        seen_post_ids.add(post_id)
        post_data = {
            "post_number": post_number,
            "username": p.get("username") or p.get("name") or "Unknown",
            "created_at": p.get("created_at"),
            "updated_at": p.get("updated_at"),
            "cooked": p.get("cooked", ""),
            "reply_count": p.get("reply_count", 0),
            "reply_to_post_number": p.get("reply_to_post_number"),
            "quote_count": p.get("quote_count", 0),
            "reads": p.get("reads", 0),
            "topic_title": topic_title
        }
        all_posts.append(post_data)
    
    # Log what post numbers we found
    if all_posts:
        post_numbers = [p.get("post_number", 0) for p in all_posts]
        post_numbers.sort()
        scraping_logger.info(f"📊 Found posts: #{post_numbers[0]} to #{post_numbers[-1]} (total: {len(post_numbers)})")
    
    # Sort posts based on desired order
    if descending:
        # Sort by post_number descending (newest first)
        all_posts.sort(key=lambda x: x.get("post_number", 0), reverse=True)
        scraping_logger.info(f"📥 Sorted posts in descending order (newest first)")
    else:
        # Sort by post_number ascending (oldest first)
        all_posts.sort(key=lambda x: x.get("post_number", 0))
        scraping_logger.info(f"📤 Sorted posts in ascending order (oldest first)")
    
    # Limit to max_posts
    all_posts = all_posts[:max_posts]
    
    scraping_logger.info(f"✅ Returning {len(all_posts)} posts (order: {'NEWEST→OLDEST' if descending else 'OLDEST→NEWEST'})")
    
    # Log date range
    if all_posts:
        first_date = all_posts[0].get("created_at", "")[:10]
        last_date = all_posts[-1].get("created_at", "")[:10]
        scraping_logger.info(f"📅 Date range: {first_date} to {last_date}")
    
    return all_posts


def save_posts_to_db(category_name, topic_title, topic_url, posts, user_id, company_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    saved_count = 0
    skipped_count = 0

    print(f"💾 Saving {len(posts)} posts to database...")
    for p in tqdm(posts, desc="💾 Saving posts", unit="post", ncols=100):
        post_number = p.get("post_number")

        # Check if post already exists for this user and company
        cur.execute("""
            SELECT COUNT(*) FROM posts 
            WHERE post_number = ? AND topic_url = ? AND user_id = ? AND company_id = ?
        """, (post_number, topic_url, user_id, company_id))
        
        exists = cur.fetchone()[0] > 0
        
        if exists:
            skipped_count += 1
            continue
        
        text = p.get("cooked") or ""
        # store raw cooked HTML and also store plain text trimmed
        plain = BeautifulSoup(text, "lxml").get_text(" ", strip=True) if text else ""
        
        cur.execute("""
            INSERT INTO posts (user_id, company_id, category, topic_title, topic_url, post_number, author, created_at, cooked_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, company_id, category_name, topic_title, topic_url, post_number, p.get("username"), p.get("created_at"), plain))
        saved_count += 1
    
    conn.commit()
    conn.close()
    
    scraping_logger.info(f"Saved {saved_count} new posts, skipped {skipped_count} duplicates")
    return saved_count, skipped_count


def export_topic_posts_to_files(category_slug, topic_title, topic_url, posts):
    """Save per-topic JSON and CSV in data/"""
    safe_slug = category_slug.replace("/", "_")
    topic_safe = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in topic_title)[:100]
    base = os.path.join(DATA_DIR, f"{safe_slug}__{topic_safe}")
    json_path = base + ".json"
    csv_path = base + ".csv"

    # JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"topic": topic_title, "url": topic_url, "posts": posts}, f, ensure_ascii=False, indent=2)

    # CSV (flatten)
    rows = []
    for p in posts:
        text = p.get("cooked") or ""
        plain = BeautifulSoup(text, "lxml").get_text(" ", strip=True) if text else ""
        rows.append({
            "post_number": p.get("post_number"),
            "author": p.get("username"),
            "created_at": p.get("created_at"),
            "content": plain
        })
    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False, encoding="utf-8")

    return json_path, csv_path