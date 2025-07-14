# ⚙️ Configuration Guide

This guide explains how to configure the Taxsutra Scraper for your environment.

## 📋 Configuration Overview

The application uses environment variables for configuration, managed through:
- `.env` file for local/server configuration
- `config/settings.py` for advanced configuration
- Command-line arguments (for specific use cases)

---

## 🔧 Environment Variables (.env)

### Required Configuration

#### Google Sheets Configuration
```bash
# Your Google Spreadsheet ID (found in the URL)
SPREADSHEET_ID=1eknhrQZT8hwH58DJeeFZGOsqh7m7f7kJlS_EZAlZ6HM

# Path to your service account JSON file
SERVICE_ACCOUNT_DETAILS=config/credentials/service-account.json
```

#### Taxsutra Credentials
```bash
# Your Taxsutra login credentials
TAXSUTRA_USERNAME=your_email@example.com
TAXSUTRA_PASSWORD=your_password_here
```

### Optional Configuration

#### Logging Settings
```bash
# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Log file paths
LOG_FILE=logs/scraper.log
ERROR_LOG_FILE=logs/error.log
```

#### Server Configuration
```bash
# Run Chrome in headless mode (true for servers)
HEADLESS_MODE=true

# Path to Chrome binary (auto-detected if not specified)
CHROME_BINARY_PATH=/usr/bin/google-chrome

# Directory for downloaded files
DOWNLOAD_DIR=downloads
```

#### Performance Tuning
```bash
# WebDriver timeout in seconds (default: 8)
WEBDRIVER_TIMEOUT=8

# Page load wait time in seconds (default: 1.5)
PAGE_LOAD_WAIT=1.5

# Number of retry attempts (default: 3)
RETRY_ATTEMPTS=3
```

#### Timezone & Scheduling
```bash
# Timezone for cron jobs and timestamps
TIMEZONE=Asia/Kolkata
```

---

## 🔑 Google Sheets Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Note your project ID

### Step 2: Enable Google Sheets API

1. In the Cloud Console, go to **APIs & Services > Dashboard**
2. Click **+ ENABLE APIS AND SERVICES**
3. Search for "Google Sheets API"
4. Click on it and press **ENABLE**

### Step 3: Create Service Account

1. Go to **APIs & Services > Credentials**
2. Click **+ CREATE CREDENTIALS > Service account**
3. Fill in the details:
   - **Service account name**: `taxsutra-scraper`
   - **Service account ID**: Will be auto-generated
   - **Description**: `Service account for Taxsutra scraper`

### Step 4: Generate Service Account Key

1. After creating the service account, click on it
2. Go to the **Keys** tab
3. Click **ADD KEY > Create new key**
4. Choose **JSON** format
5. Download the file and save it as `config/credentials/service-account.json`

### Step 5: Share Google Sheet

1. Open your Google Sheet
2. Click **Share** button
3. Add the service account email (found in the JSON file)
4. Give it **Editor** permission
5. Copy the spreadsheet ID from the URL

**Example URL**: `https://docs.google.com/spreadsheets/d/1eknhrQZT8hwH58DJeeFZGOsqh7m7f7kJlS_EZAlZ6HM/edit`  
**Spreadsheet ID**: `1eknhrQZT8hwH58DJeeFZGOsqh7m7f7kJlS_EZAlZ6HM`

---

## 🏗️ Advanced Configuration

### Custom Settings (config/settings.py)

For advanced users, you can modify `config/settings.py`:

```python
# Custom Chrome options
CHROME_OPTIONS = [
    "--disable-images",
    "--disable-plugins", 
    "--disable-extensions",
    "--no-sandbox",
    "--disable-dev-shm-usage"
]

# Custom field mappings
FIELD_MAPPINGS = {
    "title": "h3 .field--name-title",
    "published_date": ".podcastTimeDate",
    "ruling_date": ".field--name-field-date-of-judgement .field__item"
}

# Custom retry configuration
RETRY_CONFIG = {
    "max_attempts": 3,
    "backoff_factor": 2,
    "retry_on_errors": ["TimeoutException", "NoSuchElementException"]
}
```

### Environment-Specific Configurations

#### Development Environment
```bash
# .env.development
LOG_LEVEL=DEBUG
HEADLESS_MODE=false
WEBDRIVER_TIMEOUT=20
PAGE_LOAD_WAIT=3
```

#### Production Environment
```bash
# .env.production
LOG_LEVEL=INFO
HEADLESS_MODE=true
WEBDRIVER_TIMEOUT=8
PAGE_LOAD_WAIT=1.5
```

#### Testing Environment
```bash
# .env.testing
LOG_LEVEL=WARNING
HEADLESS_MODE=true
WEBDRIVER_TIMEOUT=5
PAGE_LOAD_WAIT=1
```

---

## 🌐 Server-Specific Configuration

### Hostinger VPS
```bash
HEADLESS_MODE=true
CHROME_BINARY_PATH=/usr/bin/google-chrome
LOG_LEVEL=INFO
WEBDRIVER_TIMEOUT=8
```

### DigitalOcean Droplet
```bash
HEADLESS_MODE=true
CHROME_BINARY_PATH=/usr/bin/google-chrome-stable
LOG_LEVEL=INFO
WEBDRIVER_TIMEOUT=10
```

### AWS EC2
```bash
HEADLESS_MODE=true
CHROME_BINARY_PATH=/usr/bin/google-chrome
LOG_LEVEL=INFO
WEBDRIVER_TIMEOUT=8
PAGE_LOAD_WAIT=2
```

### Google Cloud VM
```bash
HEADLESS_MODE=true
CHROME_BINARY_PATH=/usr/bin/google-chrome
LOG_LEVEL=INFO
WEBDRIVER_TIMEOUT=8
```

---

## 📊 Performance Configuration

### Low-Resource Servers (1GB RAM)
```bash
WEBDRIVER_TIMEOUT=5
PAGE_LOAD_WAIT=1
RETRY_ATTEMPTS=2
LOG_LEVEL=WARNING
```

### High-Performance Servers (4GB+ RAM)
```bash
WEBDRIVER_TIMEOUT=15
PAGE_LOAD_WAIT=2
RETRY_ATTEMPTS=5
LOG_LEVEL=DEBUG
```

### Network-Optimized
```bash
WEBDRIVER_TIMEOUT=12
PAGE_LOAD_WAIT=2
RETRY_ATTEMPTS=3
```

---

## 🕐 Scheduling Configuration

### Cron Job Configuration

#### Daily at 10:30 AM (Recommended)
```bash
30 10 * * * cd /path/to/taxsutra-scraper && source venv/bin/activate && python3 src/main.py >> logs/cron.log 2>&1
```

#### Twice Daily (Morning and Evening)
```bash
30 10 * * * cd /path/to/taxsutra-scraper && source venv/bin/activate && python3 src/main.py >> logs/cron.log 2>&1
30 18 * * * cd /path/to/taxsutra-scraper && source venv/bin/activate && python3 src/main.py >> logs/cron.log 2>&1
```

#### Every 6 Hours
```bash
0 */6 * * * cd /path/to/taxsutra-scraper && source venv/bin/activate && python3 src/main.py >> logs/cron.log 2>&1
```

### Systemd Timer Configuration

#### Daily Execution
```ini
[Timer]
OnCalendar=*-*-* 10:30:00
Persistent=true
```

#### Weekly Execution (Mondays)
```ini
[Timer]
OnCalendar=Mon *-*-* 10:30:00
Persistent=true
```

---

## 🔍 Debugging Configuration

### Verbose Debugging
```bash
LOG_LEVEL=DEBUG
WEBDRIVER_TIMEOUT=30
PAGE_LOAD_WAIT=5
RETRY_ATTEMPTS=1
```

### Screenshot Debugging (for development)
```python
# Add to config/settings.py
SAVE_SCREENSHOTS = True
SCREENSHOT_DIR = "debug/screenshots"
SAVE_PAGE_SOURCE = True
```

---

## 🛡️ Security Configuration

### File Permissions
```bash
# Set appropriate permissions
chmod 600 .env
chmod 600 config/credentials/service-account.json
chmod 755 src/main.py
chmod 644 requirements.txt
```

### Environment Variable Security
```bash
# Don't store sensitive data in version control
echo ".env" >> .gitignore
echo "config/credentials/" >> .gitignore
```

### Network Security
```bash
# Firewall configuration (Ubuntu/Debian)
sudo ufw allow ssh
sudo ufw allow out 80,443
sudo ufw enable
```

---

## 📝 Configuration Validation

### Automatic Validation

The application automatically validates configuration on startup:

```bash
python3 src/main.py
```

If there are configuration errors, you'll see:
```
Configuration errors:
- SPREADSHEET_ID is required
- Service account file not found: config/credentials/service-account.json
```

### Manual Validation

#### Test Google Sheets Connection
```bash
source venv/bin/activate
python3 -c "
from config.settings import config
from src.sheets_uploader import SheetsUploader
uploader = SheetsUploader()
print('✅ Google Sheets OK' if uploader.authenticate() else '❌ Google Sheets Failed')
"
```

#### Test Chrome Installation
```bash
google-chrome --version
google-chrome --headless --disable-gpu --no-sandbox --dump-dom https://www.google.com > /dev/null 2>&1 && echo "✅ Chrome OK" || echo "❌ Chrome Failed"
```

#### Test Taxsutra Access
```bash
curl -I https://www.taxsutra.com/dt/rulings && echo "✅ Taxsutra Accessible" || echo "❌ Taxsutra Not Accessible"
```

---

## 🚨 Common Configuration Issues

### Issue 1: Service Account Authentication
**Error**: `Service account file not found`
**Solution**: Ensure the file exists and path is correct
```bash
ls -la config/credentials/service-account.json
```

### Issue 2: Google Sheets Permission
**Error**: `The caller does not have permission`
**Solution**: Share the sheet with service account email
```bash
# Find service account email in JSON file
grep "client_email" config/credentials/service-account.json
```

### Issue 3: Chrome Binary Not Found
**Error**: `chrome not reachable`
**Solution**: Install Chrome or set correct path
```bash
which google-chrome
which google-chrome-stable
```

### Issue 4: Network Connectivity
**Error**: `Failed to establish a new connection`
**Solution**: Check firewall and network settings
```bash
curl -I https://www.taxsutra.com
ping google.com
```

---

## 📦 Configuration Templates

### Minimal Configuration (.env.minimal)
```bash
SPREADSHEET_ID=your_sheet_id_here
TAXSUTRA_USERNAME=your_username
TAXSUTRA_PASSWORD=your_password
SERVICE_ACCOUNT_DETAILS=config/credentials/service-account.json
```

### Complete Configuration (.env.complete)
```bash
# Required
SPREADSHEET_ID=your_sheet_id_here
TAXSUTRA_USERNAME=your_username
TAXSUTRA_PASSWORD=your_password
SERVICE_ACCOUNT_DETAILS=config/credentials/service-account.json

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/scraper.log
ERROR_LOG_FILE=logs/error.log

# Server
HEADLESS_MODE=true
CHROME_BINARY_PATH=/usr/bin/google-chrome
DOWNLOAD_DIR=downloads

# Performance
WEBDRIVER_TIMEOUT=8
PAGE_LOAD_WAIT=1.5
RETRY_ATTEMPTS=3

# Other
TIMEZONE=Asia/Kolkata
```

---

## 🔄 Configuration Updates

### Updating Configuration
1. Stop any running scrapers
2. Update `.env` file
3. Restart the application
4. Verify changes with test run

### Configuration Backup
```bash
# Backup current configuration
cp .env .env.backup.$(date +%Y%m%d)
tar -czf config-backup-$(date +%Y%m%d).tar.gz .env config/
```

### Configuration Migration
```bash
# When updating from older versions
python3 scripts/migrate_config.py --old-config .env.old --new-config .env
```

---

**📝 Note**: Always test configuration changes in a development environment before deploying to production. Keep backups of working configurations. 