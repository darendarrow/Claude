# Reddit Media Downloader — Dockerfile
# Lightweight Python container with ffmpeg for video+audio merging

FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Runtime Stage ───────────────────────────────────────────
FROM python:3.11-slim

# Install ffmpeg for Reddit video+audio merging
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY reddit_media_downloader.py .

# Create default directories
RUN mkdir -p /app/downloads /app/data

CMD ["python", "reddit_media_downloader.py"]
