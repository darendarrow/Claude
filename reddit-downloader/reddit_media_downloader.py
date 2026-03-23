"""
Reddit Media Downloader - Main Script
=======================================

This script automatically downloads images and videos from specified subreddits
using the Reddit API (via PRAW). It processes both historical posts and can
continuously monitor for new submissions.

Features:
    - Downloads images (jpg, png, gif, webp) and videos from Reddit posts
    - Supports gallery posts (multiple images per post)
    - Handles Reddit-hosted video (v.redd.it) with audio merging via ffmpeg
    - Organizes files into folders named after the post title
    - Tracks downloads in SQLite to avoid duplicates
    - Configurable subreddit list, sort mode, and history depth
    - Rate-limit aware with automatic backoff
    - Docker-ready with persistent storage

Usage:
    1. Configure .env with your Reddit API credentials
    2. Run: python reddit_media_downloader.py

Author: Auto-generated (matching Telegram downloader architecture)
"""

import os
import re
import sys
import time
import json
import sqlite3
import hashlib
import logging
import asyncio
import argparse
import subprocess
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import praw
import requests
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

load_dotenv()

# Reddit API credentials (REQUIRED)
CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
USER_AGENT = os.getenv("REDDIT_USER_AGENT", "RedditMediaDownloader/1.0")
USERNAME = os.getenv("REDDIT_USERNAME", "")
PASSWORD = os.getenv("REDDIT_PASSWORD", "")

# Subreddits to monitor (comma-separated in .env)
SUBREDDITS = [
    s.strip()
    for s in os.getenv("SUBREDDITS", "").split(",")
    if s.strip()
]

# Download configuration
DOWNLOAD_PATH = Path(os.getenv("DOWNLOAD_PATH", "./downloads"))
DATA_PATH = Path(os.getenv("DATA_PATH", "./data"))
DB_PATH = DATA_PATH / "downloads.db"

# How many historical posts to scan per subreddit (0 = skip history)
MAX_HISTORY_POSTS = int(os.getenv("MAX_HISTORY_POSTS", "500"))

# Sort mode for historical scan: hot, new, top, rising
HISTORY_SORT = os.getenv("HISTORY_SORT", "new")

# Time filter for 'top' sort: hour, day, week, month, year, all
TOP_TIME_FILTER = os.getenv("TOP_TIME_FILTER", "all")

# Polling interval in seconds for monitoring new posts
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "300"))

# Whether to run in continuous monitoring mode after history scan
CONTINUOUS_MODE = os.getenv("CONTINUOUS_MODE", "true").lower() == "true"

# Media type filters
DOWNLOAD_IMAGES = os.getenv("DOWNLOAD_IMAGES", "true").lower() == "true"
DOWNLOAD_VIDEOS = os.getenv("DOWNLOAD_VIDEOS", "true").lower() == "true"
DOWNLOAD_GIFS = os.getenv("DOWNLOAD_GIFS", "true").lower() == "true"

# Maximum file size in MB (0 = no limit)
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "0"))

# ─────────────────────────────────────────────────────────────
# Logging Setup
# ─────────────────────────────────────────────────────────────

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="[%(levelname)s/%(asctime)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(DATA_PATH / "reddit_downloader.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────────────────────

def sanitize_filename(name: str, max_length: int = 180) -> str:
    """
    Convert a Reddit post title into a safe, readable directory/file name.

    Removes or replaces characters that are problematic on Windows, macOS,
    and Linux file systems. Truncates to *max_length* characters to avoid
    path-length issues.
    """
    # Replace path separators and other problematic characters
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name)
    # Collapse whitespace / underscores
    name = re.sub(r"[\s_]+", "_", name).strip("_. ")
    # Truncate
    if len(name) > max_length:
        name = name[:max_length].rstrip("_. ")
    return name or "untitled"


def get_file_extension(url: str, default: str = ".jpg") -> str:
    """Extract file extension from a URL, falling back to *default*."""
    parsed = urllib.parse.urlparse(url)
    path = parsed.path
    _, ext = os.path.splitext(path)
    ext = ext.lower().split("?")[0]
    if ext in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".webm", ".mov"):
        return ext
    return default


def human_size(num_bytes: int) -> str:
    """Return a human-readable file size string."""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(num_bytes) < 1024:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.2f} TB"


# ─────────────────────────────────────────────────────────────
# Database Layer
# ─────────────────────────────────────────────────────────────

class DownloadDatabase:
    """
    SQLite-backed tracker for downloaded media.

    Stores post IDs and individual file paths so the script never
    re-downloads content it has already saved.
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path))
        self._init_tables()

    def _init_tables(self):
        """Create tables on first run."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id     TEXT NOT NULL,
                subreddit   TEXT NOT NULL,
                post_title  TEXT,
                file_url    TEXT,
                file_path   TEXT,
                file_size   INTEGER DEFAULT 0,
                media_type  TEXT,
                created_utc REAL,
                downloaded_at TEXT DEFAULT (datetime('now'))
            )
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_post_id ON downloads(post_id)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_file_url ON downloads(file_url)
        """)
        self.conn.commit()

    def is_downloaded(self, post_id: str, file_url: str = "") -> bool:
        """Check whether a specific file from a post was already downloaded."""
        if file_url:
            row = self.conn.execute(
                "SELECT 1 FROM downloads WHERE post_id = ? AND file_url = ?",
                (post_id, file_url),
            ).fetchone()
        else:
            row = self.conn.execute(
                "SELECT 1 FROM downloads WHERE post_id = ?",
                (post_id,),
            ).fetchone()
        return row is not None

    def record(self, *, post_id, subreddit, post_title, file_url,
               file_path, file_size, media_type, created_utc):
        """Record a completed download."""
        self.conn.execute(
            """INSERT INTO downloads
               (post_id, subreddit, post_title, file_url, file_path,
                file_size, media_type, created_utc)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (post_id, subreddit, post_title, file_url,
             file_path, file_size, media_type, created_utc),
        )
        self.conn.commit()

    def total_downloads(self) -> int:
        """Return the total number of files downloaded."""
        row = self.conn.execute("SELECT COUNT(*) FROM downloads").fetchone()
        return row[0] if row else 0

    def close(self):
        self.conn.close()


# ─────────────────────────────────────────────────────────────
# Media Extraction Helpers
# ─────────────────────────────────────────────────────────────

def extract_media_urls(submission) -> list[dict]:
    """
    Inspect a PRAW submission and return a list of media dicts:
        [{"url": "...", "type": "image"|"video"|"gif", "index": 0}, ...]

    Handles:
        - Direct image links (i.redd.it, i.imgur.com, etc.)
        - Reddit-hosted video (v.redd.it)
        - Reddit gallery posts (multiple images)
        - Imgur gifv links
    """
    media_items = []
    url = submission.url

    # ── Reddit Gallery ──────────────────────────────────────
    if hasattr(submission, "is_gallery") and submission.is_gallery:
        if hasattr(submission, "media_metadata") and submission.media_metadata:
            for idx, (media_id, meta) in enumerate(submission.media_metadata.items()):
                if meta.get("status") != "valid":
                    continue
                # Highest resolution source
                source = meta.get("s", {})
                media_url = source.get("u") or source.get("gif") or source.get("mp4")
                if media_url:
                    # Reddit HTML-encodes the URL twice in metadata
                    media_url = media_url.replace("&amp;", "&")
                    mtype = "gif" if source.get("gif") or source.get("mp4") else "image"
                    media_items.append({"url": media_url, "type": mtype, "index": idx})
        return media_items

    # ── Reddit-hosted Video (v.redd.it) ─────────────────────
    if hasattr(submission, "is_video") and submission.is_video:
        video_data = getattr(submission, "media", None)
        if video_data and "reddit_video" in video_data:
            rv = video_data["reddit_video"]
            video_url = rv.get("fallback_url") or rv.get("dash_url")
            if video_url:
                media_items.append({"url": video_url, "type": "video", "index": 0})
        return media_items

    # ── Direct Image Links ──────────────────────────────────
    image_extensions = (".jpg", ".jpeg", ".png", ".gif", ".webp")
    if any(url.lower().endswith(ext) for ext in image_extensions):
        mtype = "gif" if url.lower().endswith(".gif") else "image"
        media_items.append({"url": url, "type": mtype, "index": 0})
        return media_items

    # ── Imgur gifv → mp4 ────────────────────────────────────
    if "imgur.com" in url and url.lower().endswith(".gifv"):
        mp4_url = url[:-5] + ".mp4"
        media_items.append({"url": mp4_url, "type": "video", "index": 0})
        return media_items

    # ── Imgur single image (no extension) ───────────────────
    if re.match(r"https?://(i\.)?imgur\.com/\w+$", url):
        media_items.append({"url": url + ".jpg", "type": "image", "index": 0})
        return media_items

    return media_items


def should_download(media_type: str) -> bool:
    """Check whether the user has enabled this media type."""
    if media_type == "image" and not DOWNLOAD_IMAGES:
        return False
    if media_type == "video" and not DOWNLOAD_VIDEOS:
        return False
    if media_type == "gif" and not DOWNLOAD_GIFS:
        return False
    return True


# ─────────────────────────────────────────────────────────────
# Download Engine
# ─────────────────────────────────────────────────────────────

class RedditMediaDownloader:
    """
    Core downloader that authenticates with Reddit, scans subreddits,
    extracts media, and saves files organized by post title.
    """

    def __init__(self):
        self.db = DownloadDatabase(DB_PATH)
        self.reddit: Optional[praw.Reddit] = None
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self._stats = {"downloaded": 0, "skipped": 0, "errors": 0}

    # ── Authentication ──────────────────────────────────────

    def authenticate(self):
        """Create an authenticated PRAW Reddit instance."""
        if not CLIENT_ID or not CLIENT_SECRET:
            raise ValueError(
                "Missing Reddit API credentials. "
                "Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env. "
                "Create an app at https://www.reddit.com/prefs/apps"
            )

        kwargs = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "user_agent": USER_AGENT,
        }

        # If username/password provided, use script-type auth (higher rate limits)
        if USERNAME and PASSWORD:
            kwargs["username"] = USERNAME
            kwargs["password"] = PASSWORD
            logger.info("Authenticating as user: %s", USERNAME)
        else:
            logger.info("Authenticating in read-only mode (no username/password)")

        self.reddit = praw.Reddit(**kwargs)

        # Verify authentication
        if USERNAME and PASSWORD:
            logger.info("Logged in as: %s", self.reddit.user.me())
        else:
            logger.info("Read-only mode active")

    # ── Single File Download ────────────────────────────────

    def _download_file(self, url: str, dest: Path, max_retries: int = 3) -> Optional[Path]:
        """
        Download a single file from *url* to *dest* with retry logic.
        Returns the final Path on success or None on failure.
        """
        for attempt in range(1, max_retries + 1):
            try:
                resp = self.session.get(url, stream=True, timeout=60)
                resp.raise_for_status()

                # Check file size before downloading fully
                content_length = int(resp.headers.get("content-length", 0))
                if MAX_FILE_SIZE_MB and content_length > MAX_FILE_SIZE_MB * 1024 * 1024:
                    logger.warning(
                        "Skipping %s — file too large (%s, limit %d MB)",
                        url, human_size(content_length), MAX_FILE_SIZE_MB,
                    )
                    return None

                dest.parent.mkdir(parents=True, exist_ok=True)
                total = 0
                with open(dest, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=1024 * 64):
                        f.write(chunk)
                        total += len(chunk)

                logger.info("  Saved %s (%s)", dest.name, human_size(total))
                return dest

            except requests.exceptions.HTTPError as e:
                if e.response is not None and e.response.status_code == 429:
                    wait = 2 ** attempt * 5
                    logger.warning("Rate limited — retrying in %ds", wait)
                    time.sleep(wait)
                else:
                    logger.error("HTTP error downloading %s: %s", url, e)
                    return None

            except Exception as e:
                logger.error("Error downloading %s (attempt %d/%d): %s",
                             url, attempt, max_retries, e)
                if attempt < max_retries:
                    time.sleep(2 ** attempt)

        return None

    # ── Reddit Video with Audio Merge ───────────────────────

    def _download_reddit_video(self, video_url: str, dest: Path) -> Optional[Path]:
        """
        Download a Reddit-hosted video. Reddit stores video and audio in
        separate DASH streams. This method downloads both and merges them
        with ffmpeg when available.
        """
        video_path = dest.with_suffix(".video.mp4")
        audio_url = re.sub(r"DASH_\d+", "DASH_AUDIO_128", video_url)
        # Also try the older audio path
        audio_url_alt = video_url.rsplit("/", 1)[0] + "/DASH_audio.mp4"
        audio_path = dest.with_suffix(".audio.mp4")

        # Download video stream
        result = self._download_file(video_url, video_path)
        if not result:
            return None

        # Attempt to download audio stream
        audio_downloaded = self._download_file(audio_url, audio_path)
        if not audio_downloaded:
            audio_downloaded = self._download_file(audio_url_alt, audio_path)

        final_path = dest.with_suffix(".mp4")

        if audio_downloaded:
            # Merge video + audio with ffmpeg
            try:
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(video_path),
                    "-i", str(audio_path),
                    "-c:v", "copy", "-c:a", "aac",
                    "-strict", "experimental",
                    str(final_path),
                ]
                subprocess.run(cmd, capture_output=True, timeout=120, check=True)
                video_path.unlink(missing_ok=True)
                audio_path.unlink(missing_ok=True)
                logger.info("  Merged video + audio → %s", final_path.name)
                return final_path
            except FileNotFoundError:
                logger.warning("  ffmpeg not found — saving video without audio")
                video_path.rename(final_path)
                audio_path.unlink(missing_ok=True)
                return final_path
            except subprocess.SubprocessError as e:
                logger.warning("  ffmpeg merge failed: %s — saving video only", e)
                video_path.rename(final_path)
                audio_path.unlink(missing_ok=True)
                return final_path
        else:
            # No audio available — just rename video
            video_path.rename(final_path)
            return final_path

    # ── Process a Single Submission ─────────────────────────

    def process_submission(self, submission) -> int:
        """
        Extract and download all media from a single Reddit submission.
        Returns the number of files downloaded.
        """
        post_id = submission.id
        subreddit = str(submission.subreddit)
        title = submission.title
        created_utc = submission.created_utc

        media_items = extract_media_urls(submission)
        if not media_items:
            return 0

        downloaded_count = 0
        safe_title = sanitize_filename(title)
        post_dir = DOWNLOAD_PATH / sanitize_filename(subreddit) / safe_title

        for item in media_items:
            media_url = item["url"]
            media_type = item["type"]
            index = item["index"]

            # Check type filter
            if not should_download(media_type):
                continue

            # Check if already downloaded
            if self.db.is_downloaded(post_id, media_url):
                self._stats["skipped"] += 1
                continue

            # Build filename
            ext = get_file_extension(media_url, ".jpg" if media_type == "image" else ".mp4")
            if len(media_items) > 1:
                filename = f"{safe_title}_{index + 1:03d}{ext}"
            else:
                filename = f"{safe_title}{ext}"

            dest = post_dir / filename

            # Avoid name collisions
            counter = 1
            while dest.exists():
                stem = dest.stem.rsplit("_dup", 1)[0]
                dest = dest.with_name(f"{stem}_dup{counter}{ext}")
                counter += 1

            logger.info(
                "Downloading %s from r/%s: \"%s\"",
                media_type, subreddit, title[:80],
            )

            # Download
            if media_type == "video" and "v.redd.it" in media_url:
                result = self._download_reddit_video(media_url, dest)
            else:
                result = self._download_file(media_url, dest)

            if result:
                file_size = result.stat().st_size
                self.db.record(
                    post_id=post_id,
                    subreddit=subreddit,
                    post_title=title,
                    file_url=media_url,
                    file_path=str(result),
                    file_size=file_size,
                    media_type=media_type,
                    created_utc=created_utc,
                )
                downloaded_count += 1
                self._stats["downloaded"] += 1
            else:
                self._stats["errors"] += 1

        return downloaded_count

    # ── History Scan ────────────────────────────────────────

    def scan_history(self):
        """
        Scan historical posts from each configured subreddit.
        Uses the sort mode and post limit from configuration.
        """
        if MAX_HISTORY_POSTS <= 0:
            logger.info("History scan disabled (MAX_HISTORY_POSTS=0)")
            return

        logger.info(
            "Starting history scan: %d posts per subreddit, sort=%s",
            MAX_HISTORY_POSTS, HISTORY_SORT,
        )

        for sub_name in SUBREDDITS:
            logger.info("=" * 60)
            logger.info("Scanning r/%s ...", sub_name)

            try:
                subreddit = self.reddit.subreddit(sub_name)

                # Select sort mode
                if HISTORY_SORT == "top":
                    posts = subreddit.top(
                        time_filter=TOP_TIME_FILTER, limit=MAX_HISTORY_POSTS
                    )
                elif HISTORY_SORT == "hot":
                    posts = subreddit.hot(limit=MAX_HISTORY_POSTS)
                elif HISTORY_SORT == "rising":
                    posts = subreddit.rising(limit=MAX_HISTORY_POSTS)
                else:  # default: new
                    posts = subreddit.new(limit=MAX_HISTORY_POSTS)

                scanned = 0
                sub_downloads = 0
                for submission in posts:
                    scanned += 1
                    sub_downloads += self.process_submission(submission)
                    if scanned % 50 == 0:
                        logger.info(
                            "  Progress: %d/%d posts scanned, %d files downloaded",
                            scanned, MAX_HISTORY_POSTS, sub_downloads,
                        )

                logger.info(
                    "Completed r/%s: %d posts scanned, %d files downloaded",
                    sub_name, scanned, sub_downloads,
                )

            except Exception as e:
                logger.error("Error scanning r/%s: %s", sub_name, e)

    # ── Continuous Monitoring ───────────────────────────────

    def monitor_new_posts(self):
        """
        Continuously poll subreddits for new submissions using PRAW's
        stream functionality. Runs indefinitely until interrupted.
        """
        logger.info("=" * 60)
        logger.info("Starting continuous monitoring (Ctrl+C to stop)")
        logger.info("Watching: %s", ", ".join(f"r/{s}" for s in SUBREDDITS))
        logger.info("Poll interval: %ds", POLL_INTERVAL)

        # Combine subreddits into a single multi-reddit for streaming
        multi = "+".join(SUBREDDITS)
        subreddit = self.reddit.subreddit(multi)

        try:
            # stream.submissions() yields new posts in near-real-time
            for submission in subreddit.stream.submissions(
                skip_existing=True, pause_after=-1
            ):
                if submission is None:
                    # No new posts — pause_after=-1 returns None when idle
                    time.sleep(POLL_INTERVAL)
                    continue

                count = self.process_submission(submission)
                if count:
                    logger.info(
                        "  [NEW] Downloaded %d file(s) from r/%s",
                        count, submission.subreddit,
                    )

        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error("Stream error: %s", e)
            raise

    # ── Main Entry Point ────────────────────────────────────

    def run(self):
        """Full pipeline: authenticate → scan history → monitor."""
        print("=" * 60)
        print("  Reddit Media Downloader")
        print("=" * 60)

        # Validate configuration
        if not SUBREDDITS:
            logger.error(
                "No subreddits configured. Set SUBREDDITS in .env "
                "(comma-separated, e.g. SUBREDDITS=earthporn,itookapicture)"
            )
            sys.exit(1)

        logger.info("Subreddits: %s", ", ".join(f"r/{s}" for s in SUBREDDITS))
        logger.info("Download path: %s", DOWNLOAD_PATH.resolve())
        logger.info("Database: %s", DB_PATH.resolve())
        logger.info("Previously downloaded: %d files", self.db.total_downloads())

        # Ensure directories exist
        DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)
        DATA_PATH.mkdir(parents=True, exist_ok=True)

        # Authenticate
        self.authenticate()

        # Phase 1: Historical scan
        self.scan_history()

        logger.info("-" * 60)
        logger.info(
            "Session stats — Downloaded: %d | Skipped: %d | Errors: %d",
            self._stats["downloaded"], self._stats["skipped"], self._stats["errors"],
        )
        logger.info("Total files in database: %d", self.db.total_downloads())

        # Phase 2: Continuous monitoring
        if CONTINUOUS_MODE:
            self.monitor_new_posts()
        else:
            logger.info("Continuous mode disabled — exiting after history scan")

        self.db.close()


# ─────────────────────────────────────────────────────────────
# CLI Entry Point
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download media from Reddit subreddits"
    )
    parser.add_argument(
        "--no-history",
        action="store_true",
        help="Skip the historical post scan and go straight to monitoring",
    )
    parser.add_argument(
        "--no-monitor",
        action="store_true",
        help="Only scan history, then exit (no continuous monitoring)",
    )
    args = parser.parse_args()

    if args.no_history:
        MAX_HISTORY_POSTS = 0
    if args.no_monitor:
        CONTINUOUS_MODE = False

    downloader = RedditMediaDownloader()

    try:
        downloader.run()
    except KeyboardInterrupt:
        logger.info("\nShutdown requested — goodbye!")
    except Exception as exc:
        logger.critical("Fatal error: %s", exc, exc_info=True)
        sys.exit(1)
