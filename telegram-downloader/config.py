"""
Configuration module for Telegram Media Downloader.
Loads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram API Credentials (REQUIRED)
API_ID = int(os.getenv('TELEGRAM_API_ID', 0))
API_HASH = os.getenv('TELEGRAM_API_HASH', '')

# Validate required credentials
if not API_ID or not API_HASH:
    raise ValueError(
        "Missing required Telegram API credentials. "
        "Please set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env file. "
        "Get them from https://my.telegram.org"
    )

# Session configuration
SESSION_NAME = os.getenv('SESSION_NAME', 'media_downloader')

# Download configuration
DOWNLOAD_PATH = Path(os.getenv('DOWNLOAD_PATH', './downloads'))
DOWNLOAD_PATH.mkdir(exist_ok=True)

# How many historical messages to scan per chat (set to 0 to skip history)
MAX_HISTORY_MESSAGES = int(os.getenv('MAX_HISTORY_MESSAGES', 1000))

# Flood wait threshold - auto-sleep for flood waits less than this (seconds)
FLOOD_SLEEP_THRESHOLD = int(os.getenv('FLOOD_SLEEP_THRESHOLD', 60))

# Supported media types
DOWNLOAD_PHOTOS = os.getenv('DOWNLOAD_PHOTOS', 'true').lower() == 'true'
DOWNLOAD_VIDEOS = os.getenv('DOWNLOAD_VIDEOS', 'true').lower() == 'true'
DOWNLOAD_DOCUMENTS = os.getenv('DOWNLOAD_DOCUMENTS', 'false').lower() == 'true'
