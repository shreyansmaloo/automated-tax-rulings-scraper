#!/bin/bash

# Automated Tax Rulings Scraper - Hostinger VPS Deployment Script
# This script sets up the entire environment on a fresh Hostinger VPS

set -e  # Exit on error

echo "🚀 Starting Hostinger VPS Deployment for Automated Tax Rulings Scraper"
echo "============================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root. Consider creating a dedicated user for security."
fi

# Step 1: Update system
print_step "1. Updating system packages"
sudo apt update && sudo apt upgrade -y

# Step 2: Install Python and pip
print_step "2. Installing Python 3.8+ and pip"
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Step 3: Install Chrome and ChromeDriver
print_step "3. Installing Google Chrome"
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install -y google-chrome-stable

# Step 4: Install additional dependencies
print_step "4. Installing system dependencies"
sudo apt install -y curl wget unzip xvfb

# Step 5: Create project directory
print_step "5. Setting up project directory"
PROJECT_DIR="/opt/automated-tax-rulings-scraper"
sudo mkdir -p $PROJECT_DIR
sudo chown $USER:$USER $PROJECT_DIR
cd $PROJECT_DIR

# Step 6: Copy project files (assuming they're in current directory)
print_step "6. Copying project files"
if [ -d "../automated-tax-rulings-scraper" ]; then
    cp -r ../automated-tax-rulings-scraper/* .
else
    print_error "Project files not found. Please ensure automated-tax-rulings-scraper directory exists."
    exit 1
fi

# Step 7: Set up Python virtual environment
print_step "7. Creating Python virtual environment"
python3 -m venv venv
source venv/bin/activate

# Step 8: Install Python dependencies
print_step "8. Installing Python dependencies"
pip install --upgrade pip
pip install -r requirements.txt

# Step 9: Create necessary directories
print_step "9. Creating necessary directories"
mkdir -p logs downloads config/credentials

# Step 10: Set up environment file
print_step "10. Setting up environment configuration"
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_warning "Please edit .env file with your actual credentials:"
    print_warning "  - SPREADSHEET_ID"
    print_warning "  - TAXSUTRA_USERNAME" 
    print_warning "  - TAXSUTRA_PASSWORD"
    print_warning "  - Place service-account.json in config/credentials/"
fi

# Step 11: Set file permissions
print_step "11. Setting file permissions"
chmod +x src/main.py
chmod +x deploy/*.sh
chmod 600 .env 2>/dev/null || true

# Step 12: Create systemd service (optional)
print_step "12. Creating systemd service"
sudo tee /etc/systemd/system/automated-tax-rulings-scraper.service > /dev/null <<EOF
[Unit]
Description=Taxsutra Automated Scraper
After=network.target

[Service]
Type=oneshot
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python3 $PROJECT_DIR/src/main.py
StandardOutput=append:$PROJECT_DIR/logs/systemd.log
StandardError=append:$PROJECT_DIR/logs/systemd-error.log

[Install]
WantedBy=multi-user.target
EOF

# Step 13: Create systemd timer for daily execution
print_step "13. Creating systemd timer for daily execution"
sudo tee /etc/systemd/system/automated-tax-rulings-scraper.timer > /dev/null <<EOF
[Unit]
Description=Run Taxsutra Scraper daily at 10:30 AM
Requires=automated-tax-rulings-scraper.service

[Timer]
OnCalendar=*-*-* 10:30:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Step 14: Enable and start systemd timer
print_step "14. Enabling systemd timer"
sudo systemctl daemon-reload
sudo systemctl enable automated-tax-rulings-scraper.timer
sudo systemctl start automated-tax-rulings-scraper.timer

# Step 15: Test installation
print_step "15. Testing installation"
if source venv/bin/activate && python3 -c "import selenium, google.oauth2.service_account; print('✅ Dependencies OK')"; then
    print_status "✅ All dependencies installed successfully"
else
    print_error "❌ Dependency check failed"
    exit 1
fi

# Final instructions
echo ""
echo "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "======================================"
echo ""
print_status "Project deployed to: $PROJECT_DIR"
print_status "Virtual environment: $PROJECT_DIR/venv"
print_status "Logs directory: $PROJECT_DIR/logs"
print_status "Daily execution: 10:30 AM (systemd timer)"
echo ""
print_warning "IMPORTANT: Before running, please:"
echo "1. Edit .env file with your actual credentials"
echo "2. Place your service-account.json in config/credentials/"
echo "3. Share your Google Sheet with the service account email"
echo ""
print_status "Manual test run:"
echo "  cd $PROJECT_DIR"
echo "  source venv/bin/activate"
echo "  python3 src/main.py"
echo ""
print_status "Check systemd timer status:"
echo "  sudo systemctl status automated-tax-rulings-scraper.timer"
echo ""
print_status "View logs:"
echo "  tail -f $PROJECT_DIR/logs/scraper.log"
echo ""
print_status "Deployment completed at: $(date)" 