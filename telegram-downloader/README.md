# Telegram Media Downloader

A production-ready Python application that automatically downloads images and videos from all your Telegram chats using user account authentication. Fully containerized with Docker for easy deployment.

## Features

✅ **User Account Authentication** - Phone number-based login with 2FA support  
✅ **Comprehensive Monitoring** - Scans all chats, including historical messages  
✅ **Smart Organization** - Files organized by chat name with sender username in filename  
✅ **Duplicate Prevention** - SQLite database tracks downloads to avoid duplicates  
✅ **Docker Ready** - Fully containerized with Docker Compose for easy deployment  
✅ **Production Ready** - Robust error handling, logging, and automatic retry logic  
✅ **Bug Fixed** - All photo size attribute errors and permission issues resolved  

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Telegram account with phone number
- API credentials from https://my.telegram.org

### Installation

1. Create project directory and extract files:
   ```bash
   mkdir telegram-downloader
   cd telegram-downloader
   # Copy all files from this artifact
   ```

2. Set up environment:
   ```bash
   cp .env.example .env
   nano .env  # Add your TELEGRAM_API_ID and TELEGRAM_API_HASH
   ```

3. Create required directories with proper permissions:
   ```bash
   mkdir -p data downloads
   chmod 777 data downloads
   ```

4. Build the Docker image:
   ```bash
   docker compose build
   ```

5. First-time authentication:
   ```bash
   docker compose run --rm telegram-downloader
   # Enter phone number, verification code, and 2FA password if enabled
   ```

6. Run in background:
   ```bash
   docker compose up -d
   ```

7. Monitor logs:
   ```bash
   docker compose logs -f
   ```

## File Organization

