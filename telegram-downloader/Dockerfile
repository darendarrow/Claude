# Telegram Media Downloader - Dockerfile
# This creates a containerized environment for the media downloader
# using a multi-stage build for optimal image size

# Build stage - compiles optional C extensions
FROM python:3.11-slim as builder

# Install build dependencies needed for compiling cryptg and other packages
# gcc, g++, and make are needed for C/C++ compilation
# libssl-dev provides encryption libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment to isolate dependencies
RUN python -m venv /opt/venv

# Activate the virtual environment for subsequent commands
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements file first (Docker layer caching optimization)
# This way, dependencies are only rebuilt when requirements change
COPY requirements.txt .

# Install all Python dependencies including optional performance packages
# --no-cache-dir reduces image size by not storing pip cache
# cryptg provides 10-100x faster encryption/decryption
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir cryptg

# Runtime stage - final lean image
FROM python:3.11-slim

# Create a non-root user for security best practices
# Running as root in containers is a security risk
RUN useradd --create-home --shell /bin/bash telegramuser

# Install runtime dependencies only (no build tools needed)
# libssl is needed at runtime for cryptographic operations
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Set up the Python path to use our virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory where the application will run
WORKDIR /app

# Copy application files
# These are copied after dependencies so changes don't invalidate cached layers
COPY config.py .
COPY media_downloader.py .

# Create directories for persistent data
# These will be mounted as volumes to persist data outside the container
RUN mkdir -p /app/downloads /app/data && \
    chown -R telegramuser:telegramuser /app

# Switch to non-root user for security
USER telegramuser

# Set environment variables for Python
# PYTHONUNBUFFERED ensures logs are immediately visible (no buffering)
# PYTHONDONTWRITEBYTECODE prevents .pyc file creation (cleaner container)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Health check to monitor if the script is still running
# This allows Docker/orchestrators to detect and restart failed containers
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD pgrep -f media_downloader.py || exit 1

# Default command to run the application
CMD ["python", "-u", "media_downloader.py"]
