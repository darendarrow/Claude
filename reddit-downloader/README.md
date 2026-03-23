# Reddit Media Downloader

A Python script that automatically downloads images and videos from specified Reddit subreddits, organizing files into folders named after each post's title. Built to mirror the architecture of the Telegram Media Downloader — with SQLite tracking, Docker support, `.env` configuration, and continuous monitoring.

## Features

- **Subreddit-based downloading** — configure one or more subreddits to monitor
- **Post title organization** — each post's media is stored in a folder named after its title
- **Gallery support** — downloads all images from Reddit gallery posts
- **Reddit video handling** — downloads v.redd.it video and merges audio with ffmpeg
- **Imgur support** — handles direct Imgur links and gifv→mp4 conversion
- **Duplicate prevention** — SQLite database tracks every download to skip duplicates
- **History scan** — process existing posts (hot/new/top/rising sort modes)
- **Continuous monitoring** — stream new posts in real-time after the history scan
- **Docker-ready** — includes Dockerfile and docker-compose.yml
- **Configurable** — media type filters, file size limits, poll intervals, and more

## Prerequisites

- Python 3.9+
- A Reddit account
- Reddit API credentials (free)
- ffmpeg (optional, for merging Reddit video + audio)

## Quick Start

### 1. Get Reddit API Credentials

1. Go to [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Click **"create another app..."** at the bottom
3. Fill in the form:
   - **name**: `MediaDownloader` (or anything you like)
   - **type**: select **script**
   - **redirect uri**: `http://localhost:8080`
4. Click **Create app**
5. Note down the **client ID** (string under the app name) and **client secret**

### 2. Install Dependencies

```bash
# Clone or copy the project
cd reddit_downloader

# (Optional) create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

# Install Python packages
pip install -r requirements.txt

# (Optional) install ffmpeg for Reddit video audio merging
# Ubuntu/Debian:
sudo apt install ffmpeg
# macOS:
brew install ffmpeg
```

### 3. Configure

```bash
cp .env.example .env
nano .env   # or use any text editor
```

At minimum, set these values:

```
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
SUBREDDITS=earthporn,itookapicture,wallpapers
```

### 4. Run

```bash
python reddit_media_downloader.py
```

The script will scan each subreddit's history, then (if `CONTINUOUS_MODE=true`) monitor for new posts indefinitely.

## Docker Deployment

```bash
# Build the image
docker compose build

# Run in the background
docker compose up -d

# Follow logs
docker compose logs -f

# Stop
docker compose down
```

Downloaded files and the SQLite database persist on the host via volume mounts (`./downloads` and `./data`).

## CLI Options

```
python reddit_media_downloader.py [OPTIONS]

--no-history    Skip historical scan, go straight to monitoring
--no-monitor    Scan history only, then exit
```

## Configuration Reference

All settings are defined in `.env`. See `.env.example` for the full list with descriptions.

| Variable | Default | Description |
|---|---|---|
| `REDDIT_CLIENT_ID` | *(required)* | OAuth client ID from reddit.com/prefs/apps |
| `REDDIT_CLIENT_SECRET` | *(required)* | OAuth client secret |
| `REDDIT_USERNAME` | *(optional)* | For script-type auth (higher rate limits) |
| `REDDIT_PASSWORD` | *(optional)* | For script-type auth |
| `SUBREDDITS` | *(required)* | Comma-separated subreddit names |
| `MAX_HISTORY_POSTS` | `500` | Posts to scan per subreddit (0 = skip) |
| `HISTORY_SORT` | `new` | Sort mode: hot, new, top, rising |
| `TOP_TIME_FILTER` | `all` | Time filter when sort=top |
| `POLL_INTERVAL` | `300` | Seconds between new-post polls |
| `CONTINUOUS_MODE` | `true` | Monitor after history scan |
| `DOWNLOAD_IMAGES` | `true` | Download image files |
| `DOWNLOAD_VIDEOS` | `true` | Download video files |
| `DOWNLOAD_GIFS` | `true` | Download GIF/animated files |
| `MAX_FILE_SIZE_MB` | `0` | Max file size (0 = unlimited) |

## Directory Structure

```
downloads/
├── earthporn/
│   ├── Sunset_over_the_Grand_Canyon/
│   │   └── Sunset_over_the_Grand_Canyon.jpg
│   └── Misty_morning_in_the_Alps_gallery/
│       ├── Misty_morning_in_the_Alps_gallery_001.jpg
│       ├── Misty_morning_in_the_Alps_gallery_002.jpg
│       └── Misty_morning_in_the_Alps_gallery_003.jpg
├── itookapicture/
│   └── ITAP_of_a_hummingbird/
│       └── ITAP_of_a_hummingbird.jpg
data/
├── downloads.db
└── reddit_downloader.log
```

## License

MIT License
