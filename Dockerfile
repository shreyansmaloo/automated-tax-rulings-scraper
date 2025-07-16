FROM python:3.11-slim

# Install system dependencies and Chromium
RUN apt-get update && \
    apt-get install -y chromium chromium-driver && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV DISPLAY=:99

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Tell Selenium to use Chromium
ENV CHROME_BINARY_PATH=/usr/bin/chromium

CMD ["python", "src/main.py"]
