#!/bin/bash

# Taxsutra Scraper - Ubuntu/Debian Setup Script
# Works on Ubuntu 18.04+, Debian 10+, and most VPS providers

set -e  # Exit on error

echo "🐧 Starting Ubuntu/Debian Setup for Taxsutra Scraper"
echo "====================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VERSION=$VERSION_ID
    print_status "Detected OS: $OS $VERSION"
else
    print_error "Cannot detect OS. This script requires Ubuntu or Debian."
    exit 1
fi

# Step 1: Update package lists
print_step "1. Updating package lists"
sudo apt update

# Step 2: Install essential packages
print_step "2. Installing essential packages"
sudo apt install -y curl wget gnupg lsb-release software-properties-common

# Step 3: Install Python 3.8+
print_step "3. Installing Python 3.8+"
sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential

# Verify Python version
PYTHON_VERSION=$(python3 --version | cut -d " " -f 2 | cut -d "." -f 1,2)
print_status "Python version: $PYTHON_VERSION"

# Step 4: Install Google Chrome
print_step "4. Installing Google Chrome"
if ! command -v google-chrome &> /dev/null; then
    # Add Google's signing key
    curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | sudo gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg
    
    # Add repository
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
    
    # Update and install
    sudo apt update
    sudo apt install -y google-chrome-stable
    
    print_status "Google Chrome installed successfully"
else
    print_status "Google Chrome already installed"
fi

# Step 5: Install additional dependencies for headless operation
print_step "5. Installing additional dependencies"
sudo apt install -y xvfb unzip fontconfig fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 libgtk-3-0 libnspr4 libnss3 libx11-xcb1 libxcomposite1 libxcursor1 libxdamage1 libxfixes3 libxi6 libxrandr2 libxss1 libxtst6 lsb-release xdg-utils

# Step 6: Set up project
print_step "6. Setting up project directory"
PROJECT_DIR="$HOME/taxsutra-scraper"

if [ -d "$PROJECT_DIR" ]; then
    print_warning "Project directory already exists. Backing up..."
    mv "$PROJECT_DIR" "$PROJECT_DIR.backup.$(date +%s)"
fi

mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Step 7: Create directory structure
print_step "7. Creating directory structure"
mkdir -p src config/credentials deploy docs logs downloads

# Step 8: Set up Python virtual environment
print_step "8. Creating Python virtual environment"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Step 9: Install Python packages
print_step "9. Installing Python packages"
pip install selenium==4.15.2 webdriver-manager==4.0.1 google-api-python-client==2.108.0 google-auth==2.23.4 google-auth-oauthlib==1.1.0 google-auth-httplib2==0.1.1 requests==2.31.0 python-dotenv==1.0.0

# Step 10: Test Chrome installation
print_step "10. Testing Chrome installation"
if google-chrome --version; then
    print_status "✅ Chrome test successful"
else
    print_error "❌ Chrome test failed"
    exit 1
fi

# Step 11: Test headless Chrome
print_step "11. Testing headless Chrome"
timeout 10 google-chrome --headless --disable-gpu --no-sandbox --dump-dom https://www.google.com > /dev/null 2>&1
if [ $? -eq 0 ]; then
    print_status "✅ Headless Chrome test successful"
else
    print_warning "⚠️ Headless Chrome test failed (might work anyway)"
fi

# Step 12: Create basic configuration files
print_step "12. Creating configuration files"

# Create .env.example
cat > .env.example << 'EOF'
# Google Sheets Configuration
SPREADSHEET_ID=your_google_sheet_id_here
SERVICE_ACCOUNT_FILE=config/credentials/service-account.json

# Taxsutra Login Credentials
TAXSUTRA_USERNAME=your_username@example.com
TAXSUTRA_PASSWORD=your_password_here

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/scraper.log
ERROR_LOG_FILE=logs/error.log

# Server Configuration
HEADLESS_MODE=true
CHROME_BINARY_PATH=/usr/bin/google-chrome
DOWNLOAD_DIR=downloads

# Timing Configuration (in seconds)
WEBDRIVER_TIMEOUT=8
PAGE_LOAD_WAIT=1.5
RETRY_ATTEMPTS=3

# Timezone (for cron scheduling)
TIMEZONE=Asia/Kolkata
EOF

# Create requirements.txt
cat > requirements.txt << 'EOF'
selenium==4.15.2
webdriver-manager==4.0.1
google-api-python-client==2.108.0
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
requests==2.31.0
python-dotenv==1.0.0
EOF

# Step 13: Create cron job setup script
print_step "13. Creating cron job setup script"
cat > setup_cron.sh << 'EOF'
#!/bin/bash
# Add cron job for daily execution at 10:30 AM

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_COMMAND="30 10 * * * cd $SCRIPT_DIR && source venv/bin/activate && python3 src/main.py >> logs/cron.log 2>&1"

# Add to crontab
(crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -

echo "✅ Cron job added for daily execution at 10:30 AM"
echo "📋 View cron jobs: crontab -l"
echo "📝 View cron logs: tail -f $SCRIPT_DIR/logs/cron.log"
EOF

chmod +x setup_cron.sh

# Step 14: Create monitoring script
print_step "14. Creating monitoring script"
cat > monitor.sh << 'EOF'
#!/bin/bash
# Monitoring script for Taxsutra Scraper

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔍 Taxsutra Scraper Status Monitor"
echo "=================================="
echo ""

# Check if virtual environment exists
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo "✅ Virtual environment: EXISTS"
else
    echo "❌ Virtual environment: MISSING"
fi

# Check if Chrome is installed
if command -v google-chrome &> /dev/null; then
    echo "✅ Google Chrome: $(google-chrome --version)"
else
    echo "❌ Google Chrome: NOT INSTALLED"
fi

# Check if .env file exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    echo "✅ Configuration file: EXISTS"
else
    echo "⚠️ Configuration file: MISSING (.env file)"
fi

# Check if service account exists
if [ -f "$SCRIPT_DIR/config/credentials/service-account.json" ]; then
    echo "✅ Service account: EXISTS"
else
    echo "⚠️ Service account: MISSING"
fi

# Check recent logs
echo ""
echo "📝 Recent log entries:"
if [ -f "$SCRIPT_DIR/logs/scraper.log" ]; then
    tail -5 "$SCRIPT_DIR/logs/scraper.log" | sed 's/^/    /'
else
    echo "    No log file found"
fi

# Check cron job
echo ""
echo "⏰ Cron job status:"
if crontab -l 2>/dev/null | grep -q "taxsutra"; then
    echo "✅ Cron job: CONFIGURED"
    crontab -l | grep "taxsutra" | sed 's/^/    /'
else
    echo "⚠️ Cron job: NOT CONFIGURED"
fi

echo ""
echo "🔗 Useful commands:"
echo "    Test run: cd $SCRIPT_DIR && source venv/bin/activate && python3 src/main.py"
echo "    Setup cron: ./setup_cron.sh"
echo "    View logs: tail -f logs/scraper.log"
EOF

chmod +x monitor.sh

# Step 15: Create README for this installation
print_step "15. Creating installation README"
cat > INSTALLATION_README.md << EOF
# Taxsutra Scraper - Ubuntu/Debian Installation

## ✅ Installation Completed Successfully

Your Taxsutra scraper has been set up in: \`$PROJECT_DIR\`

## 📋 What's Installed

- ✅ Python 3.8+ with virtual environment
- ✅ Google Chrome (stable)
- ✅ All Python dependencies
- ✅ Project structure and configuration files
- ✅ Monitoring and cron setup scripts

## 🔧 Next Steps

### 1. Configure Environment
\`\`\`bash
cd $PROJECT_DIR
cp .env.example .env
nano .env  # Edit with your actual credentials
\`\`\`

### 2. Add Service Account
Place your Google Service Account JSON file at:
\`config/credentials/service-account.json\`

### 3. Test Installation
\`\`\`bash
source venv/bin/activate
python3 src/main.py
\`\`\`

### 4. Set up Daily Automation
\`\`\`bash
./setup_cron.sh
\`\`\`

### 5. Monitor Status
\`\`\`bash
./monitor.sh
\`\`\`

## 📚 Documentation

- Project structure is ready for the main application files
- Logs will be saved in \`logs/\` directory
- Downloaded files will be saved in \`downloads/\` directory
- Configuration is managed through \`.env\` file

## 🆘 Support

If you encounter issues:
1. Check \`./monitor.sh\` for system status
2. Review logs in \`logs/scraper.log\`
3. Ensure all credentials are properly configured
4. Test Chrome: \`google-chrome --headless --disable-gpu --no-sandbox --dump-dom https://www.google.com\`

Installation completed on: $(date)
EOF

# Final status
echo ""
echo "🎉 UBUNTU/DEBIAN SETUP COMPLETED!"
echo "================================="
echo ""
print_status "Project directory: $PROJECT_DIR"
print_status "Virtual environment: $PROJECT_DIR/venv"
print_status "Chrome version: $(google-chrome --version 2>/dev/null || echo 'Error getting version')"
print_status "Python version: $(python3 --version)"
echo ""
print_warning "⚠️ IMPORTANT NEXT STEPS:"
echo "1. Copy your project files to: $PROJECT_DIR"
echo "2. Configure .env file with your credentials"
echo "3. Add your service-account.json file"
echo "4. Run: ./monitor.sh to check status"
echo "5. Run: ./setup_cron.sh to enable daily automation"
echo ""
print_status "Installation completed successfully!"
echo "📖 See INSTALLATION_README.md for detailed instructions" 