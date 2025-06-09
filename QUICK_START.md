# 🚀 Quick Start Guide

Get your automated tax rulings scraper running in minutes!

## 📋 Prerequisites

### For Hostinger VPS:
```bash
chmod +x deploy/hostinger_deploy.sh
./deploy/hostinger_deploy.sh
```

### For Any Ubuntu/Debian Server:
```bash
chmod +x deploy/ubuntu_setup.sh
./deploy/ubuntu_setup.sh
```

## 📝 Required Information

Before starting, have these ready:

1. **Google Spreadsheet ID** (from URL)
2. **Taxsutra credentials** (username/password)
3. **Service account JSON file** (from Google Cloud)

## 🔧 Manual Quick Setup

### 1. Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
nano .env  # Edit with your credentials
```

### 3. Add Service Account
```bash
# Place your service-account.json file here:
mkdir -p config/credentials
# Copy your file to config/credentials/service-account.json
```

### 4. Test Run
```bash
python3 src/main.py
```

### 5. Set Up Daily Automation
```bash
# For cron (all systems)
(crontab -l 2>/dev/null; echo "30 10 * * * cd $(pwd) && source venv/bin/activate && python3 src/main.py >> logs/cron.log 2>&1") | crontab -

# For systemd (Ubuntu/Debian)
sudo cp deploy/automated-tax-rulings-scraper.service /etc/systemd/system/
sudo cp deploy/automated-tax-rulings-scraper.timer /etc/systemd/system/
sudo systemctl enable automated-tax-rulings-scraper.timer
sudo systemctl start automated-tax-rulings-scraper.timer
```

## 📊 Verification

Check everything is working:

```bash
# Test Google Sheets connection
python3 -c "from src.sheets_uploader import SheetsUploader; print('✅ OK' if SheetsUploader().authenticate() else '❌ Failed')"

# Test Chrome
google-chrome --version

# View logs
tail -f logs/scraper.log
```

## 🆘 Need Help?

- **Configuration Issues**: See `docs/CONFIGURATION.md`
- **Deployment Issues**: See `docs/DEPLOYMENT.md`
- **Common Problems**: Check the logs in `logs/` directory

## ✅ Success Indicators

You'll know it's working when you see:
- ✅ Chrome WebDriver initialized
- ✅ Successfully logged in to Taxsutra
- ✅ Google Sheets authentication successful
- 📊 X cells updated in Google Sheets

**Ready to deploy!** 🎉 