# Telegram Media Downloader

A production-ready Python application that automatically downloads images and videos from all your Telegram chats using user account authentication. Fully containerized with Docker for easy deployment.

## Features

✅ **User Account Authentication** - Phone number-based login with 2FA support  
✅ **Comprehensive Monitoring** - Scans all chats, including historical messages  
✅ **Smart Organization** - Files organized by chat name with sender username in filename  
✅ **Duplicate Prevention** - SQLite database tracks downloads to avoid duplicates  
✅ **Docker Ready** - Fully containerized with Docker Compose for easy deployment  
✅ **Production Ready** - Robust error handling, logging, and automatic retry logic  

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Telegram account with phone number
- API credentials from https://my.telegram.org

### Installation

1. Clone or download this project
2. Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your TELEGRAM_API_ID and TELEGRAM_API_HASH
   ```

3. Build the Docker image:
   ```bash
   docker compose build
   ```

4. First-time authentication (interactive):
   ```bash
   docker compose run --rm telegram-downloader
   ```
   - Enter your phone number
   - Enter the verification code
   - Enter 2FA password if enabled

5. Run in background:
   ```bash
   docker compose up -d
   ```

6. View logs:
   ```bash
   docker compose logs -f
   ```

## File Organization

Downloaded files are organized as:
