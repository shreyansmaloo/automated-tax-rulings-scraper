FROM python:3.11-alpine

# Install system dependencies and Chromium for Alpine
RUN apk update && \
    apk add --no-cache \
    chromium \
    chromium-chromedriver \
    wget \
    gnupg

# Set environment variables for headless Chrome
ENV DISPLAY=:99
ENV CHROME_BINARY_PATH=/usr/bin/chromium-browser
ENV CHROME_OPTIONS="--headless --no-sandbox --disable-dev-shm-usage --disable-gpu"

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Create necessary directories including chrome_profile
RUN mkdir -p /app/logs /app/downloads /app/chrome_profile

# Set proper permissions for chrome_profile
RUN chmod 755 /app/chrome_profile

# Tell Selenium to use Chromium
ENV CHROME_BINARY_PATH=/usr/bin/chromium-browser

CMD ["python", "src/main.py"]