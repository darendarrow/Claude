"""
Telegram Media Downloader - Main Script
========================================

This script automatically downloads images and videos from all Telegram chats
using user account authentication. It processes both historical messages and
monitors for new incoming media in real-time.

Features:
- User account authentication (phone number based)
- Monitors ALL chats automatically
- Downloads from message history and new messages
- Organizes files by chat name
- Includes sender username in filenames
- Comprehensive error handling and logging
- Automatic retry with exponential backoff
- Duplicate detection to avoid re-downloading

Author: Created for Telegram Media Management
License: MIT
"""

import asyncio
import logging
import os
import re
import signal
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Set

from telethon import TelegramClient, events
from telethon.errors import (
    FloodWaitError,
    SessionPasswordNeededError,
    BadRequestError,
    UnauthorizedError,
    ChatAdminRequiredError
)
from telethon.tl.types import (
    MessageMediaPhoto,
    MessageMediaDocument,
    User,
    Chat,
    Channel
)

import config

# Configure logging
logging.basicConfig(
    format='[%(levelname)s/%(asctime)s] %(name)s: %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('media_downloader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Reduce Telethon's verbose logging
logging.getLogger('telethon').setLevel(logging.WARNING)


class MediaDownloader:
    """
    Main class for downloading media from Telegram chats.
    
    This class handles:
    - User authentication
    - Message history scanning
    - Real-time message monitoring
    - Media downloading with proper organization
    - Duplicate detection and tracking
    """
    
    def __init__(self):
        """Initialize the MediaDownloader with configuration settings."""
        self.client = TelegramClient(
            config.SESSION_NAME,
            config.API_ID,
            config.API_HASH
        )
        
        # Set flood wait threshold for automatic sleep
        self.client.flood_sleep_threshold = config.FLOOD_SLEEP_THRESHOLD
        
        # Track downloaded messages to avoid duplicates
        self.downloaded_messages: Set[int] = set()
        
        # Initialize database for tracking downloads
        # Store in data directory which is mounted as a volume
        self.db_path = 'data/media_tracker.db'
        self._init_database()
        
        # Load previously downloaded message IDs
        self._load_downloaded_messages()
        
        # Flag for graceful shutdown
        self.running = True
        
    def _init_database(self):
        """Initialize SQLite database for tracking downloads."""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS downloads (
                message_id INTEGER PRIMARY KEY,
                chat_id INTEGER,
                chat_name TEXT,
                sender_username TEXT,
                file_path TEXT,
                download_date TIMESTAMP,
                file_size INTEGER,
                media_type TEXT
            )
        ''')
        
        # Index for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_message_id 
            ON downloads(message_id)
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def _load_downloaded_messages(self):
        """Load previously downloaded message IDs from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT message_id FROM downloads')
        self.downloaded_messages = {row[0] for row in cursor.fetchall()}
        
        conn.close()
        logger.info(f"Loaded {len(self.downloaded_messages)} previously downloaded messages")
    
    def _track_download(
        self,
        message_id: int,
        chat_id: int,
        chat_name: str,
        sender_username: str,
        file_path: str,
        file_size: int,
        media_type: str
    ):
        """
        Track a downloaded file in the database.
        
        Args:
            message_id: Telegram message ID
            chat_id: Chat/channel ID
            chat_name: Name of the chat
            sender_username: Username of the sender
            file_path: Local file path where media was saved
            file_size: Size of the file in bytes
            media_type: Type of media (photo/video/document)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO downloads 
                (message_id, chat_id, chat_name, sender_username, 
                 file_path, download_date, file_size, media_type)
                VALUES (?, ?, ?, ?, ?, datetime('now'), ?, ?)
            ''', (
                message_id,
                chat_id,
                chat_name,
                sender_username,
                file_path,
                file_size,
                media_type
            ))
            
            conn.commit()
            self.downloaded_messages.add(message_id)
            
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
        finally:
            conn.close()
    
    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """
        Sanitize filename by removing invalid characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename safe for filesystem
        """
        # Remove invalid characters for filenames
        invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
        sanitized = re.sub(invalid_chars, '_', filename)
        
        # Limit length to avoid filesystem issues
        if len(sanitized) > 200:
            sanitized = sanitized[:200]
        
        return sanitized
    
    async def _get_chat_name(self, chat) -> str:
        """
        Get readable name for a chat/channel.
        
        Args:
            chat: Telethon chat entity
            
        Returns:
            Readable chat name
        """
        if isinstance(chat, User):
            if chat.username:
                return f"@{chat.username}"
            return f"{chat.first_name or ''} {chat.last_name or ''}".strip() or f"user_{chat.id}"
        
        elif isinstance(chat, (Chat, Channel)):
            return chat.title or f"chat_{chat.id}"
        
        return f"unknown_{chat.id if hasattr(chat, 'id') else 'chat'}"
    
    async def _get_sender_username(self, message) -> str:
        """
        Get username or name of message sender.
        
        Args:
            message: Telethon message object
            
        Returns:
            Sender's username or name
        """
        try:
            sender = await message.get_sender()
            
            if sender is None:
                return "unknown"
            
            if isinstance(sender, User):
                if sender.username:
                    return sender.username
                return f"{sender.first_name or ''} {sender.last_name or ''}".strip() or f"user_{sender.id}"
            
            elif isinstance(sender, (Chat, Channel)):
                return sender.title or f"chat_{sender.id}"
            
            return "unknown"
            
        except Exception as e:
            logger.warning(f"Could not get sender info: {e}")
            return "unknown"
    
    async def _download_media(
        self,
        message,
        chat_name: str,
        sender_username: str
    ) -> Optional[str]:
        """
        Download media from a message with proper organization.
        
        Args:
            message: Telethon message object containing media
            chat_name: Name of the chat
            sender_username: Username of the sender
            
        Returns:
            Path to downloaded file, or None if download failed
        """
        # Check if already downloaded
        if message.id in self.downloaded_messages:
            logger.debug(f"Message {message.id} already downloaded, skipping")
            return None
        
        # Determine media type and extension
        media_type = None
        extension = None
        file_size = 0
        
        if message.photo and config.DOWNLOAD_PHOTOS:
            media_type = "photo"
            extension = ".jpg"
            # Handle different photo size types safely
            try:
                if hasattr(message.photo, 'sizes') and message.photo.sizes:
                    last_size = message.photo.sizes[-1]
                    file_size = getattr(last_size, 'size', 0)
                else:
                    file_size = 0
            except (AttributeError, IndexError):
                file_size = 0
            
        elif message.video and config.DOWNLOAD_VIDEOS:
            media_type = "video"
            extension = ".mp4"
            file_size = message.video.size
            
        elif message.document and config.DOWNLOAD_DOCUMENTS:
            mime_type = message.document.mime_type
            
            if mime_type.startswith('image/'):
                media_type = "photo"
                extension = os.path.splitext(message.file.name)[1] or ".jpg"
            elif mime_type.startswith('video/'):
                media_type = "video"
                extension = os.path.splitext(message.file.name)[1] or ".mp4"
            else:
                media_type = "document"
                extension = os.path.splitext(message.file.name)[1] or ".file"
            
            file_size = message.document.size
        
        if not media_type:
            return None
        
        # Create chat-specific directory
        sanitized_chat_name = self._sanitize_filename(chat_name)
        chat_dir = config.DOWNLOAD_PATH / sanitized_chat_name / media_type
        chat_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename with timestamp, sender, and message ID
        timestamp = message.date.strftime('%Y%m%d_%H%M%S')
        sanitized_sender = self._sanitize_filename(sender_username)
        filename = f"{timestamp}_{sanitized_sender}_msg{message.id}{extension}"
        filepath = chat_dir / filename
        
        # Handle duplicate filenames
        counter = 1
        while filepath.exists():
            filename = f"{timestamp}_{sanitized_sender}_msg{message.id}_{counter}{extension}"
            filepath = chat_dir / filename
            counter += 1
        
        # Download with retry logic
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(
                    f"Downloading {media_type} from {chat_name} "
                    f"by {sender_username} ({file_size / 1024 / 1024:.2f}MB)"
                )
                
                # Download the media
                await message.download_media(file=str(filepath))
                
                # Track the download
                self._track_download(
                    message_id=message.id,
                    chat_id=message.chat_id,
                    chat_name=chat_name,
                    sender_username=sender_username,
                    file_path=str(filepath),
                    file_size=file_size,
                    media_type=media_type
                )
                
                logger.info(f"Successfully downloaded to: {filepath}")
                return str(filepath)
                
            except FloodWaitError as e:
                logger.warning(f"Flood wait: must wait {e.seconds} seconds")
                await asyncio.sleep(e.seconds)
                retry_count += 1
                
            except Exception as e:
                logger.error(f"Error downloading media from message {message.id}: {e}")
                retry_count += 1
                
                if retry_count < max_retries:
                    wait_time = 2 ** retry_count  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to download after {max_retries} attempts")
        
        return None
    
    async def _process_message(self, message):
        """
        Process a single message and download media if present.
        
        Args:
            message: Telethon message object
        """
        # Check if message has media
        if not (message.photo or message.video or message.document):
            return
        
        try:
            # Get chat and sender information
            chat = await message.get_chat()
            chat_name = await self._get_chat_name(chat)
            sender_username = await self._get_sender_username(message)
            
            # Download the media
            await self._download_media(message, chat_name, sender_username)
            
        except Exception as e:
            logger.error(f"Error processing message {message.id}: {e}")
    
    async def scan_chat_history(self, chat_id, chat_name: str, limit: int):
        """
        Scan historical messages in a chat and download media.
        
        Args:
            chat_id: Chat ID or username
            chat_name: Readable name of the chat
            limit: Maximum number of messages to scan
        """
        logger.info(f"Scanning {limit} messages from {chat_name}")
        
        try:
            downloaded_count = 0
            processed_count = 0
            
            # Iterate through messages in reverse chronological order
            async for message in self.client.iter_messages(chat_id, limit=limit):
                if not self.running:
                    break
                
                processed_count += 1
                
                # Process messages with media
                if message.photo or message.video or message.document:
                    sender_username = await self._get_sender_username(message)
                    result = await self._download_media(message, chat_name, sender_username)
                    
                    if result:
                        downloaded_count += 1
                
                # Progress logging
                if processed_count % 100 == 0:
                    logger.info(
                        f"Progress: {processed_count}/{limit} messages processed, "
                        f"{downloaded_count} media files downloaded"
                    )
            
            logger.info(
                f"Completed scanning {chat_name}: {downloaded_count} new files downloaded "
                f"from {processed_count} messages"
            )
            
        except ChatAdminRequiredError:
            logger.warning(f"Admin permissions required for {chat_name}")
        except FloodWaitError as e:
            logger.warning(f"Flood wait for {chat_name}: must wait {e.seconds} seconds")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f"Error scanning {chat_name}: {e}")
    
    async def scan_all_chats(self):
        """Scan message history from all chats the user is part of."""
        logger.info("Starting to scan all chats for historical media...")
        
        try:
            # Get all dialogs (chats/channels the user is part of)
            dialogs = await self.client.get_dialogs()
            logger.info(f"Found {len(dialogs)} chats/channels to scan")
            
            for dialog in dialogs:
                if not self.running:
                    break
                
                chat_name = await self._get_chat_name(dialog.entity)
                
                # Skip if no messages to scan
                if config.MAX_HISTORY_MESSAGES <= 0:
                    continue
                
                await self.scan_chat_history(
                    dialog.id,
                    chat_name,
                    config.MAX_HISTORY_MESSAGES
                )
                
                # Small delay between chats to avoid rate limiting
                await asyncio.sleep(1)
            
            logger.info("Completed scanning all chats")
            
        except Exception as e:
            logger.error(f"Error scanning chats: {e}")
    
    async def start_monitoring(self):
        """Start monitoring for new messages with media in real-time."""
        logger.info("Starting real-time message monitoring...")
        
        @self.client.on(events.NewMessage())
        async def handle_new_message(event):
            """Event handler for new incoming messages."""
            if not self.running:
                return
            
            message = event.message
            
            # Only process messages with media
            if message.photo or message.video or message.document:
                try:
                    chat = await message.get_chat()
                    chat_name = await self._get_chat_name(chat)
                    
                    logger.info(f"New media received in {chat_name}")
                    await self._process_message(message)
                    
                except Exception as e:
                    logger.error(f"Error handling new message: {e}")
        
        logger.info("Real-time monitoring active - press Ctrl+C to stop")
    
    async def authenticate(self):
        """
        Authenticate the user account with phone number.
        Handles first-time login and 2FA if enabled.
        """
        await self.client.connect()
        
        if await self.client.is_user_authorized():
            logger.info("Already authenticated")
            return
        
        logger.info("First time setup - authentication required")
        
        # Request phone number
        phone = input('Enter your phone number (with country code, e.g., +1234567890): ')
        
        try:
            # Send code request
            await self.client.send_code_request(phone)
            
            # Get verification code from user
            code = input('Enter the verification code you received: ')
            
            try:
                # Attempt to sign in
                await self.client.sign_in(phone, code)
                logger.info("Successfully authenticated!")
                
            except SessionPasswordNeededError:
                # 2FA is enabled, request password
                logger.info("Two-factor authentication is enabled")
                password = input('Enter your 2FA password: ')
                await self.client.sign_in(password=password)
                logger.info("Successfully authenticated with 2FA!")
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(sig, frame):
            logger.info("Shutdown signal received - stopping gracefully...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self):
        """
        Main execution method.
        Authenticates, scans history, and monitors for new messages.
        """
        try:
            # Setup signal handlers for graceful shutdown
            self.setup_signal_handlers()
            
            # Authenticate user
            await self.authenticate()
            
            # Get user info
            me = await self.client.get_me()
            logger.info(f"Logged in as: {me.username or me.first_name} (ID: {me.id})")
            
            # Scan historical messages from all chats
            if config.MAX_HISTORY_MESSAGES > 0:
                await self.scan_all_chats()
            else:
                logger.info("Skipping history scan (MAX_HISTORY_MESSAGES=0)")
            
            # Start monitoring for new messages
            await self.start_monitoring()
            
            # Keep running until interrupted
            await self.client.run_until_disconnected()
            
        except UnauthorizedError:
            logger.error("Authentication failed - please delete the session file and try again")
        except BadRequestError as e:
            logger.error(f"Bad request error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
        finally:
            # Cleanup
            logger.info("Disconnecting...")
            await self.client.disconnect()
            logger.info("Shutdown complete")


async def main():
    """Entry point for the application."""
    print("=" * 60)
    print("Telegram Media Downloader")
    print("=" * 60)
    print()
    
    downloader = MediaDownloader()
    await downloader.run()


if __name__ == '__main__':
    # Run the async main function
    asyncio.run(main())
