# 🚀 Deployment Guide

This guide covers deploying the IT-rulings Scraper to various server environments.

## 🎯 Quick Deployment Options

### Option 1: Hostinger VPS (Recommended)
```bash
chmod +x deploy/hostinger_deploy.sh
./deploy/hostinger_deploy.sh
```

### Option 2: Ubuntu/Debian Server
```bash
chmod +x deploy/ubuntu_setup.sh
./deploy/ubuntu_setup.sh
```

### Option 3: Manual Setup
Follow the manual steps below for custom environments.

---

## 📋 Pre-requisites

### System Requirements
- **OS**: Ubuntu 18.04+, Debian 10+, CentOS 7+, or similar
- **RAM**: Minimum 1GB, Recommended 2GB+
- **Storage**: 1GB+ free space
- **Network**: Stable internet connection

### Required Accounts
- **Taxsutra Account**: Valid login credentials
- **Google Cloud Account**: For Sheets API access
- **VPS/Server**: With sudo access

Before deploying, ensure you have:

- **Server Access**: SSH access to your target server
- **Python 3.8+**: Installed on the server
- **Chrome Browser**: Installed on the server
- **Google Cloud Service Account**: With Sheets API access
- **Taxsutra Account**: Valid login credentials

---

## 🔧 Manual Deployment Steps

### Step 1: Server Setup

#### Update System
```bash
sudo apt update && sudo apt upgrade -y
```

#### Install Python 3.8+
```bash
sudo apt install -y python3 python3-pip python3-venv python3-dev
```

#### Install Google Chrome
```bash
# Add Google's signing key
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -

# Add repository
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list

# Install Chrome
sudo apt update
sudo apt install -y google-chrome-stable
```

#### Install Dependencies
```bash
sudo apt install -y xvfb unzip curl wget
```

### Step 2: Project Setup

#### Create Project Directory
```bash
sudo mkdir -p /opt/it-rulings-scraper
sudo chown $USER:$USER /opt/it-rulings-scraper
cd /opt/it-rulings-scraper
```

#### Upload Project Files
```bash
# Clone repository (or upload files)
git clone https://github.com/yourusername/it-rulings-scraper.git .

# Alternative: Upload via SCP
scp -r it-rulings-scraper/ user@server:/opt/

# Alternative: Upload via rsync
rsync -av it-rulings-scraper/ user@server:/opt/it-rulings-scraper/
```

#### Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configuration

#### Environment Setup
```bash
cp .env.example .env
nano .env  # Edit with your credentials
```

#### Service Account Setup
```bash
mkdir -p config/credentials
# Upload your service-account.json file here
chmod 600 config/credentials/service-account.json
```

#### Directory Permissions
```bash
chmod +x src/main.py
chmod +x deploy/*.sh
mkdir -p logs downloads
```

### Step 4: Testing

#### Test Chrome Installation
```bash
google-chrome --version
google-chrome --headless --disable-gpu --no-sandbox --dump-dom https://www.google.com
```

#### Test Python Dependencies
```bash
source venv/bin/activate
python3 -c "import selenium, google.oauth2.service_account; print('✅ Dependencies OK')"
```

#### Test Scraper
```bash
python3 src/main.py
```

### Step 5: Automation Setup

#### Option A: Systemd (Recommended)
```bash
# Create service file
sudo tee /etc/systemd/system/it-rulings-scraper.service > /dev/null <<EOF
[Unit]
Description=IT-rulings Automated Scraper
After=network.target

[Service]
Type=oneshot
User=$USER
Group=$USER
WorkingDirectory=/opt/it-rulings-scraper
Environment=PATH=/opt/it-rulings-scraper/venv/bin
ExecStart=/opt/it-rulings-scraper/venv/bin/python3 /opt/it-rulings-scraper/src/main.py
StandardOutput=append:/opt/it-rulings-scraper/logs/systemd.log
StandardError=append:/opt/it-rulings-scraper/logs/systemd-error.log
EOF

# Create timer for daily execution
sudo tee /etc/systemd/system/it-rulings-scraper.timer > /dev/null <<EOF
[Unit]
Description=Run IT-rulings Scraper daily at 10:30 AM
Requires=it-rulings-scraper.service

[Timer]
OnCalendar=*-*-* 10:30:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable it-rulings-scraper.timer
sudo systemctl start it-rulings-scraper.timer

# Check status
sudo systemctl status it-rulings-scraper.timer
```

#### Option B: Cron Job
```bash
# Add to crontab
(crontab -l 2>/dev/null; echo "30 10 * * * cd /opt/it-rulings-scraper && source venv/bin/activate && python3 src/main.py >> logs/cron.log 2>&1") | crontab -
```

---

## 🔍 Monitoring & Maintenance

### Check Service Status

```bash
# Systemd timer status
sudo systemctl status it-rulings-scraper.timer
sudo systemctl list-timers | grep it-rulings

# Cron job status
crontab -l | grep it-rulings

# View logs
tail -f /opt/it-rulings-scraper/logs/scraper.log

# View systemd logs
journalctl -u it-rulings-scraper.service -f

# View cron logs
tail -f /opt/it-rulings-scraper/logs/cron.log
```

### Manual Execution

```bash
cd /opt/it-rulings-scraper
source venv/bin/activate
python3 src/main.py
```

---

## 🌐 Specific Provider Instructions

### Hostinger VPS

1. **Login**: SSH to your VPS
2. **Run Script**: `./deploy/hostinger_deploy.sh`
3. **Configure**: Edit `.env` and add service account
4. **Test**: Run the scraper manually

### DigitalOcean Droplet

1. **Create Droplet**: Ubuntu 20.04 LTS, 1GB RAM+
2. **SSH Access**: Use SSH key authentication
3. **Run Setup**: `./deploy/ubuntu_setup.sh`
4. **Configure**: Follow on-screen instructions

### AWS EC2

1. **Launch Instance**: Ubuntu Server 20.04 LTS
2. **Security Group**: Allow SSH (port 22)
3. **Connect**: Use SSH with key pair
4. **Deploy**: Run deployment script

### Google Cloud VM

1. **Create VM**: Ubuntu 20.04, e2-micro or larger
2. **Firewall**: Enable SSH access
3. **Connect**: Use browser SSH or gcloud CLI
4. **Deploy**: Run deployment script

---

## 🛡️ Security Considerations

### User Security

```bash
# Create dedicated user (optional)
sudo useradd -m -s /bin/bash it-rulings
sudo usermod -aG sudo it-rulings

# Set up SSH key authentication
# Disable password authentication
```

### File Permissions

```bash
# Secure configuration files
chmod 600 .env
chmod 600 config/credentials/service-account.json
chmod 700 config/credentials/

# Set ownership
sudo chown -R $USER:$USER /opt/it-rulings-scraper
```

### Firewall Setup
```bash
# Basic UFW setup
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow out 80,443
```

### Log Rotation

```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/it-rulings-scraper > /dev/null <<EOF
/opt/it-rulings-scraper/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF
```

---

## 🔧 Troubleshooting

### Common Issues

#### Chrome/ChromeDriver Problems
```bash
# Install missing dependencies
sudo apt install -y libxss1 libappindicator1 libindicator7

# Test Chrome
google-chrome --headless --disable-gpu --no-sandbox --version
```

#### Permission Errors
```bash
# Fix permissions
sudo chown -R $USER:$USER /opt/it-rulings-scraper
chmod +x src/main.py
```

#### Network Issues
```bash
# Test connectivity
curl -I https://www.taxsutra.com
ping google.com
```

#### Memory Issues
```bash
# Monitor memory usage
free -h
htop

# Optimize Chrome options (already included in code)
```

### Log Analysis
```bash
# Check for errors
grep -i error logs/scraper.log
grep -i failed logs/scraper.log

# Monitor resource usage
dmesg | grep -i "killed process"
```

---

## 📊 Performance Optimization

### Server Resources
- **2GB RAM**: Recommended minimum
- **2 CPU cores**: For better performance
- **SSD storage**: Faster I/O operations

### Chrome Optimizations
Already included in the code:
- Disabled images and plugins
- Reduced timeouts
- Memory optimizations
- Headless mode

### Network Optimizations
- Use servers close to India for better latency
- Ensure stable internet connection
- Consider using CDN for better performance

---

## 🔄 Updates & Maintenance

### Update Application

```bash
cd /opt/it-rulings-scraper

# Stop services
sudo systemctl stop it-rulings-scraper.timer

# Backup current version
cp -r . ../it-rulings-scraper-backup-$(date +%Y%m%d)

# Pull updates
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Test update
python3 src/main.py

# Restart services
sudo systemctl start it-rulings-scraper.timer
```

### System Maintenance
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Clean up logs
find logs/ -name "*.log" -mtime +30 -delete

# Monitor disk space
df -h
```

### Backup Configuration
```bash
# Backup important files
tar -czf backup-$(date +%Y%m%d).tar.gz .env config/credentials/ logs/
```

---

## 📞 Support

### Getting Help

1. **Check Logs**: Always check application and system logs first
2. **Test Manually**: Try running the scraper manually
3. **Verify Configuration**: Ensure all credentials are correct
4. **Check Dependencies**: Verify all packages are installed

### Useful Commands
```bash
# System info
uname -a
lsb_release -a
python3 --version
google-chrome --version

# Process monitoring
ps aux | grep python
ps aux | grep chrome

# Network testing
netstat -tuln
ss -tuln
```

---

**📝 Note**: This deployment guide assumes basic Linux system administration knowledge. For production environments, consider additional security measures like SSL certificates, monitoring systems, and backup strategies. 