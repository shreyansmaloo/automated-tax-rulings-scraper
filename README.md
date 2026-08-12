# 🤖 Automated Tax Rulings Scraper

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Selenium](https://img.shields.io/badge/selenium-4.15.2-green.svg)](https://selenium.dev/)

A high-performance, automated web scraper that extracts tax rulings from Taxsutra.com and Taxmann.com, and uploads them to Google Sheets. Optimized for server deployment with cron automation.

> **Deploying or operating this in production?** Read **[DEPLOYMENT.md](DEPLOYMENT.md)** first — it's the
> single source of truth for the actual Coolify/Docker deployment, environment variables, credentials
> setup, and the scheduled task. This README covers local development and the general shape of the app.

## 🚀 Features

- ⚡ **Performance Optimized**: 40-60% faster execution with optimized Chrome settings
- 🤖 **Fully Automated**: Set-and-forget cron job execution
- 📊 **Google Sheets Integration**: Automatic data upload with formatting
- 📧 **Email Notifications**: Daily update emails with categorized sections
- 🔐 **Service Account Auth**: No manual login required for automation
- 📝 **Comprehensive Logging**: Full activity tracking and error reporting
- 🐳 **Server Ready**: Headless operation for VPS/server deployment
- 💾 **Backup System**: Daily JSON backups with timestamps
- 🛡️ **Error Handling**: Robust failure recovery and retry logic

## 📋 What It Extracts

For each ruling published today, the scraper extracts:
- **Title**: Full ruling title
- **Published Date**: When the ruling was published
- **Category**: Type of tax ruling (GST, Company & SEBI, FEMA & Banking)
- **Content**: Detailed content of the ruling or update
- **URL**: Direct link to the ruling

## 🎯 Use Cases

- **Law Firms**: Daily monitoring of new tax rulings
- **Tax Consultants**: Automated research updates
- **Corporate Legal Teams**: Compliance monitoring
- **Researchers**: Data collection for analysis
- **News Outlets**: Legal news automation

## 📁 Project Structure

```
automated-tax-rulings-scraper/
├── src/
│   ├── main.py                    # Main application entry point
│   ├── taxsuta_scraper.py         # Taxsutra.com scrapers (Rulings, Expert Corner, Litigation Tracker)
│   ├── taxmann_scraper.py         # Taxmann.com Archives scraper
│   ├── sheets_uploader.py         # Google Sheets integration
│   ├── email_sender.py            # Daily summary email
│   ├── file_upload.py             # FTP upload + local cleanup of downloaded PDFs
│   └── utils/
│       ├── driver_utils.py        # Selenium/Chrome setup + Taxsutra/Taxmann logins
│       ├── base_scraper.py        # Shared scraper base class
│       └── date_utils.py          # Target-date calculation (yesterday / weekend-on-Monday)
├── config/
│   ├── settings.py                # Configuration management (env vars + service-account file)
│   └── credentials/                # Google service account file goes here (gitignored)
├── logs/                          # Application logs (scraper.log, error.log)
├── downloads/                     # Downloaded PDFs (uploaded to FTP, then cleaned up)
├── Dockerfile                     # Active build definition used by the Coolify deployment
├── nixpacks.toml                  # Legacy/inactive — see DEPLOYMENT.md Part E for why it's not used
├── DEPLOYMENT.md                  # Full deployment & operations runbook — read this for production
└── env.example                    # Example environment variables
```

## ⚡ Quick Start

### 1. Clone/Download Project
```bash
# If using git
git clone <repository-url>
cd automated-tax-rulings-scraper

# Or download and extract the project files
```

### 2. Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Google Sheets
1. Create a Google Service Account
2. Download the JSON credentials file
3. Place it in `config/credentials/service-account.json`
4. Share your Google Sheet with the service account email

### 4. Update Configuration
```bash
cp env.example .env
# Edit .env with your settings
```

### 5. Test Run
```bash
python3 src/main.py
```

### 6. Set Up Automation (Optional)

For local/VPS use outside of Coolify, a plain crontab entry works (this uses the machine's own
local timezone directly, unlike Coolify below):
```bash
# Automated daily run (10:30 AM local time)
(crontab -l 2>/dev/null; echo "30 10 * * * cd /path/to/automated-tax-rulings-scraper && source venv/bin/activate && python3 src/main.py >> logs/cron.log 2>&1") | crontab -
```

**In production this repo is deployed to Coolify**, which runs the scraper via its own
**Scheduled Tasks** feature (a cron-like scheduler that execs `python3 src/main.py` into the
running container) rather than a system crontab — see
[DEPLOYMENT.md Part L](DEPLOYMENT.md#part-l--set-up-the-daily-scheduled-task) for the exact setup.
**Important**: Coolify's Scheduled Task frequency runs in the server's own clock (UTC on the
current deployment), not IST — see Part L for the conversion. Writing `0 8 * * *` there does
**not** mean 8 AM IST.

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Google Sheets Configuration
SPREADSHEET_ID=your_google_sheet_id
SERVICE_ACCOUNT_FILE=config/credentials/service-account.json

# Taxsutra Login Credentials
TAXSUTRA_USERNAME=your_taxsutra_username
TAXSUTRA_PASSWORD=your_taxsutra_password

# Taxmann Login Credentials
TAXMANN_EMAIL=your_taxmann_email
TAXMANN_PASSWORD=your_taxmann_password

# Email Configuration (Optional - for daily update emails)
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=465
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here
EMAIL_RECIPIENT=admin@m2k.co.in

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/scraper.log

# Server Configuration (for deployment)
CHROME_BINARY_PATH=/usr/bin/chromium  # must match whatever the Dockerfile installs — see DEPLOYMENT.md Part E
# Note: Chrome always runs headless in a container, unconditionally - there's no HEADLESS_MODE
# toggle anymore. A configurable version of this once caused a broken deploy to silently email
# everyone an empty "no updates" report, so it's intentionally not configurable.
```

### Google Sheets Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Sheets API
4. Create Service Account credentials
5. Download JSON key file
6. Share your Google Sheet with the service account email

### Email Setup (Optional)
The scraper can send daily update emails with M2K branding and comprehensive data from `rulings.json`:

**Email Features:**
- **M2K Brand Colors**: Orange (`#ea580c`) and Dark Blue (`#1e293b`)
- **Three Sections**: Articles, Taxsutra Updates, Taxmann Updates
- **Rich Content**: Titles, summaries, citations, dates, categories
- **Statistics Dashboard**: Summary counts for each section
- **Professional Design**: Modern layout with hover effects

**Data Sources:**
- Uses `rulings.json` for comprehensive data
- Automatically categorizes content based on URLs and metadata
- Includes all available information: summaries, citations, case names, judicial levels

To enable email notifications:
1. For Gmail: Use an App Password (not your regular password)
2. Enable 2-factor authentication on your Gmail account
3. Generate an App Password: Google Account → Security → App Passwords
4. Set the environment variables in your `.env` file

## 🚀 Deployment

Production deployment is via **Coolify**, building the included `Dockerfile` (Debian-based, with a
real `chromium`/`chromium-driver` install) and running the scraper as a Coolify **Scheduled Task**
against the deployed container. Full step-by-step instructions — including why Dockerfile is used
instead of Nixpacks, environment variable setup, the Google service-account credentials file, and
the scheduled task configuration — are in **[DEPLOYMENT.md](DEPLOYMENT.md)**.

For a quick local Docker Compose run (development only, not how production is deployed):
```bash
docker-compose up -d
```

## 📊 Performance Optimizations

- **Chrome Browser**: Images disabled, plugins disabled, extensions disabled
- **WebDriver Timeouts**: Reduced from 20s to 8s for faster response
- **Sleep Timers**: Minimized wait times between operations
- **Memory Management**: Optimized for server environments
- **Network**: Background networking disabled, sync disabled
- **Headless Mode**: No GUI for server deployment

**Expected Performance**: 40-60% faster execution compared to standard Selenium scripts

## 📝 Logging & Monitoring

### Log Levels
- **INFO**: Normal operation status
- **ERROR**: Errors that stop execution
- **WARNING**: Issues that don't stop execution
- **DEBUG**: Detailed debugging information

### Log Files
- `logs/scraper.log`: Main application log
- `logs/error.log`: Error-only log for monitoring
- `logs/cron.log`: Only produced if you're running via a plain system crontab (see above); not
  applicable when running under Coolify's Scheduled Tasks — for those, use Coolify's
  **Scheduled Tasks → (task) → Recent executions → Download Logs** instead.

### Monitoring Commands
```bash
# Watch live logs
tail -f logs/scraper.log

# Check recent errors
tail -20 logs/error.log

# Monitor cron execution (plain crontab deployments only)
grep "automated-tax-rulings" /var/log/syslog
```

Note: `src/file_upload.py`'s FTP upload step uses `print()` rather than the logger, so its
per-file status only appears live in the terminal/execution output, not in `logs/scraper.log`.

## 🔍 Troubleshooting

### Common Issues

**Chrome Driver Issues**

On the Coolify/Docker deployment, Chrome and its driver come from the Dockerfile's
`apt-get install chromium chromium-driver` (Debian packages — see
[DEPLOYMENT.md Part E](DEPLOYMENT.md#part-e--set-the-build-method-to-dockerfile) for why
Debian specifically, not Ubuntu/Nixpacks). To update, bump the base image or rebuild without cache:
```bash
# In Coolify: Actions → Force deploy (without cache)
```
For a local (non-Docker) install:
```bash
sudo apt update && sudo apt install --reinstall chromium chromium-driver
```

**Google Sheets Authentication**
```bash
# Verify service account file
python3 -c "from google.oauth2 import service_account; print('OK')"
```

**Permission Issues**
```bash
chmod +x src/main.py
chmod 600 config/credentials/service-account.json
```

**Taxmann Login Issues**
```bash
# Check if your Taxmann credentials are correct in .env file
# Ensure you have an active subscription to Taxmann.com
```

**Google Sheets upload fails with a 403 "PERMISSION_DENIED" error**

The service-account credentials file being valid is not enough — the target Google Sheet must
also be explicitly shared with the service account's email as **Editor**. See
[DEPLOYMENT.md Part H](DEPLOYMENT.md#part-h--set-up-the-google-sheet-and-google-service-account).

See [DEPLOYMENT.md](DEPLOYMENT.md) for the full deployment runbook (written for non-technical
readers too) and more detailed solutions.

## 📈 Sample Output

```json
[
  {
    "Title": "HC: Grants TDS credit withheld for TDS return incorrectly filed...",
    "Published Date": "Jun 09, 2025",
    "Category": "GST",
    "Content": "The High Court allowed the appeal and granted the TDS credit...",
    "URL": "https://www.taxmann.com/research/gst/..."
  }
]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

- **Deployment/operations**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Issues**: Create an issue in the repository, or contact the repo owner

## 🏆 Credits

Built with:
- [Selenium](https://selenium.dev/) - Web automation
- [Google Sheets API](https://developers.google.com/sheets/api) - Data storage
- [Python](https://python.org/) - Core language

---

**⭐ Star this repository if it helps you automate your legal research!** 