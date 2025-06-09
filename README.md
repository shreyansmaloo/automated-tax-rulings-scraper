# 🤖 Automated Tax Rulings Scraper

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Selenium](https://img.shields.io/badge/selenium-4.15.2-green.svg)](https://selenium.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A high-performance, automated web scraper that extracts tax rulings from Taxsutra.com and uploads them to Google Sheets. Optimized for server deployment with cron automation.

## 🚀 Features

- ⚡ **Performance Optimized**: 40-60% faster execution with optimized Chrome settings
- 🤖 **Fully Automated**: Set-and-forget cron job execution
- 📊 **Google Sheets Integration**: Automatic data upload with formatting
- 🔐 **Service Account Auth**: No manual login required for automation
- 📝 **Comprehensive Logging**: Full activity tracking and error reporting
- 🐳 **Server Ready**: Headless operation for VPS/server deployment
- 💾 **Backup System**: Daily JSON backups with timestamps
- 🛡️ **Error Handling**: Robust failure recovery and retry logic

## 📋 What It Extracts

For each ruling published today, the scraper extracts:
- **Title**: Full ruling title
- **Published Date**: When the ruling was published on Taxsutra
- **Ruling Date**: Actual date of the legal ruling
- **Conclusion**: Key conclusions from the ruling
- **Decision Summary**: Detailed summary of the decision
- **Case Law Information**: Relevant case details and citations
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
│   ├── main.py              # Main application entry point
│   ├── scraper.py           # Core scraping functionality
│   └── sheets_uploader.py   # Google Sheets integration
├── config/
│   ├── settings.py          # Configuration management
│   └── credentials/         # Google service account files
├── docs/                    # Documentation
├── logs/                    # Application logs
├── downloads/               # JSON backups
└── deploy/                  # Deployment scripts
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
cp .env.example .env
# Edit .env with your settings
```

### 5. Test Run
```bash
python3 src/main.py
```

### 6. Set Up Automation (Optional)
```bash
# Automated daily run (10:30 AM)
(crontab -l 2>/dev/null; echo "30 10 * * * cd /path/to/automated-tax-rulings-scraper && source venv/bin/activate && python3 src/main.py >> logs/cron.log 2>&1") | crontab -
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Google Sheets Configuration
SPREADSHEET_ID=your_google_sheet_id
SERVICE_ACCOUNT_FILE=config/credentials/service-account.json

# Scraping Configuration
TAXSUTRA_USERNAME=your_username
TAXSUTRA_PASSWORD=your_password

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/scraper.log

# Server Configuration (for deployment)
HEADLESS_MODE=true
CHROME_BINARY_PATH=/usr/bin/google-chrome
```

### Google Sheets Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Sheets API
4. Create Service Account credentials
5. Download JSON key file
6. Share your Google Sheet with the service account email

## 🚀 Deployment Options

### Option 1: Hostinger VPS
```bash
chmod +x deploy/hostinger_deploy.sh
./deploy/hostinger_deploy.sh
```

### Option 2: Ubuntu/Debian Server
```bash
chmod +x deploy/ubuntu_setup.sh
./deploy/ubuntu_setup.sh
```

### Option 3: Docker (Coming Soon)
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
- `logs/cron.log`: Cron job execution log
- `logs/error.log`: Error-only log for monitoring

### Monitoring Commands
```bash
# Watch live logs
tail -f logs/scraper.log

# Check recent errors
tail -20 logs/error.log

# Monitor cron execution
grep "automated-tax-rulings" /var/log/syslog
```

## 🔍 Troubleshooting

### Common Issues

**Chrome Driver Issues**
```bash
# Update Chrome and ChromeDriver
sudo apt update && sudo apt upgrade google-chrome-stable
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

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for detailed solutions.

## 📈 Sample Output

```json
[
  {
    "Title": "HC: Grants TDS credit withheld for TDS return incorrectly filed...",
    "Published Date": "Jun 09, 2025",
    "Ruling Date": "2025-05-27",
    "Conclusion": "The High Court allowed the appeal and granted the TDS credit...",
    "Decision Summary": "The assessee filed TDS return under Form 26QB instead of 27Q...",
    "Case Law Information": "Case Name: PARAG KESHAV BOPARDIKAR Vs. DCIT...",
    "URL": "https://www.taxsutra.com/dt/rulings/..."
  }
]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- **Documentation**: Check the `docs/` folder
- **Issues**: Create an issue in the repository
- **Email**: [Your support email]

## 🏆 Credits

Built with:
- [Selenium](https://selenium.dev/) - Web automation
- [Google Sheets API](https://developers.google.com/sheets/api) - Data storage
- [Python](https://python.org/) - Core language

---

**⭐ Star this repository if it helps you automate your legal research!** 