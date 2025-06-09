#!/bin/bash

# Automated Tax Rulings Scraper - Shared Hosting Deployment Script
# This script sets up the project on shared hosting (like Hostinger) without root access

set -e  # Exit on error

echo "🚀 Starting Shared Hosting Deployment for Automated Tax Rulings Scraper"
echo "=================================================================="

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

# Check current user and environment
print_status "Current user: $(whoami)"
print_status "Home directory: $HOME"

# Step 1: Check Python availability
print_step "1. Checking Python availability"
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version)
    print_status "✅ Python3 found: $PYTHON_VERSION"
elif command -v python >/dev/null 2>&1; then
    PYTHON_VERSION=$(python --version)
    print_status "✅ Python found: $PYTHON_VERSION"
    alias python3=python
else
    print_error "❌ Python not found. Please contact your hosting provider."
    exit 1
fi

# Step 2: Check pip availability
print_step "2. Checking pip availability"
if command -v pip3 >/dev/null 2>&1; then
    print_status "✅ pip3 found"
elif command -v pip >/dev/null 2>&1; then
    print_status "✅ pip found"
    alias pip3=pip
else
    print_error "❌ pip not found. Please contact your hosting provider."
    exit 1
fi

# Step 3: Set up project directory in home
print_step "3. Setting up project directory"
PROJECT_DIR="$HOME/automated-tax-rulings-scraper"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Step 4: Copy project files
print_step "4. Copying project files"
# Copy all files from the current directory to project directory
cp -r ../automated-tax-rulings-scraper/* . 2>/dev/null || {
    # If that fails, assume we're already in the right directory
    print_status "Files already in place or copying from current directory"
}

# Step 5: Set up Python virtual environment
print_step "5. Creating Python virtual environment"
python3 -m venv venv || {
    print_warning "Virtual environment creation failed. Trying without venv..."
    mkdir -p venv/bin
    ln -sf $(which python3) venv/bin/python3
    ln -sf $(which pip3) venv/bin/pip3
}

# Try to activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    print_status "✅ Virtual environment activated"
else
    print_warning "⚠️  Virtual environment not available, using system Python"
fi

# Step 6: Install Python dependencies
print_step "6. Installing Python dependencies"
pip3 install --user --upgrade pip
pip3 install --user -r requirements.txt

# Step 7: Create necessary directories
print_step "7. Creating necessary directories"
mkdir -p logs downloads config/credentials

# Step 8: Set up environment file
print_step "8. Setting up environment configuration"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
    else
        # Create a basic .env file
        cat > .env << 'EOF'
# Google Sheets Configuration
SPREADSHEET_ID=your_spreadsheet_id_here

# Taxsutra Login Credentials
TAXSUTRA_USERNAME=your_username_here
TAXSUTRA_PASSWORD=your_password_here

# Browser Configuration (for shared hosting)
HEADLESS=true
DISABLE_GPU=true
NO_SANDBOX=true
EOF
    fi
    print_warning "Please edit .env file with your actual credentials:"
    print_warning "  - SPREADSHEET_ID"
    print_warning "  - TAXSUTRA_USERNAME" 
    print_warning "  - TAXSUTRA_PASSWORD"
    print_warning "  - Place service-account.json in config/credentials/"
fi

# Step 9: Set file permissions
print_step "9. Setting file permissions"
chmod +x src/main.py 2>/dev/null || true
chmod +x deploy/*.sh 2>/dev/null || true
chmod 600 .env 2>/dev/null || true

# Step 10: Create a simple cron job script
print_step "10. Creating cron job script"
cat > run_scraper.sh << EOF
#!/bin/bash
cd $PROJECT_DIR
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi
python3 src/main.py >> logs/cron.log 2>&1
EOF
chmod +x run_scraper.sh

# Step 11: Test basic Python imports
print_step "11. Testing Python dependencies"
python3 -c "
try:
    import requests
    print('✅ requests OK')
except ImportError:
    print('❌ requests missing')

try:
    import google.oauth2.service_account
    print('✅ google-auth OK')
except ImportError:
    print('❌ google-auth missing')

try:
    from selenium import webdriver
    print('✅ selenium OK (Note: Chrome may not be available)')
except ImportError:
    print('❌ selenium missing')
" || print_warning "Some dependencies may be missing"

# Final instructions
echo ""
echo "🎉 SHARED HOSTING DEPLOYMENT COMPLETED!"
echo "====================================="
echo ""
print_status "Project deployed to: $PROJECT_DIR"
print_status "Logs directory: $PROJECT_DIR/logs"
echo ""
print_warning "IMPORTANT NOTES FOR SHARED HOSTING:"
echo "1. Chrome/ChromeDriver may not be available - you may need to use Firefox or alternative methods"
echo "2. Some Python packages may require compilation - contact support if installation fails"
echo "3. Memory and CPU limits may apply"
echo ""
print_warning "SETUP STEPS:"
echo "1. Edit .env file with your actual credentials"
echo "2. Place your service-account.json in config/credentials/"
echo "3. Share your Google Sheet with the service account email"
echo ""
print_status "Manual test run:"
echo "  cd $PROJECT_DIR"
echo "  python3 src/main.py"
echo ""
print_status "Set up cron job (through hosting control panel):"
echo "  Command: $PROJECT_DIR/run_scraper.sh"
echo "  Schedule: Daily at your preferred time"
echo ""
print_status "View logs:"
echo "  tail -f $PROJECT_DIR/logs/scraper.log"
echo "  tail -f $PROJECT_DIR/logs/cron.log"
echo ""
print_status "Deployment completed at: $(date)" 