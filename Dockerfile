FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    curl \
    xz-utils && \
    rm -rf /var/lib/apt/lists/*

# Install Chromium for web scraping
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables for headless Chromium
ENV DISPLAY=:99
ENV CHROME_BINARY_PATH=/usr/bin/chromium
ENV CHROME_OPTIONS="--headless --no-sandbox --disable-dev-shm-usage --disable-gpu"

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/logs /app/downloads /app/chrome_profile

# Set proper permissions for chrome_profile
RUN chmod 755 /app/chrome_profile

# Default command runs the scraper directly
CMD ["/usr/local/bin/python3", "/app/src/main.py"]
