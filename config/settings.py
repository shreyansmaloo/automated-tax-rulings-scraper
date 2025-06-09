"""
Configuration management for Automated Tax Rulings Scraper
Loads settings from environment variables and provides defaults
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for Automated Tax Rulings Scraper"""
    
    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent
    LOGS_DIR = PROJECT_ROOT / "logs"
    CONFIG_DIR = PROJECT_ROOT / "config"
    CREDENTIALS_DIR = CONFIG_DIR / "credentials"
    
    # Google Sheets Configuration
    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "")
    SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", "config/credentials/service-account.json")
    
    # Taxsutra Login Credentials
    TAXSUTRA_USERNAME = os.getenv("TAXSUTRA_USERNAME", "")
    TAXSUTRA_PASSWORD = os.getenv("TAXSUTRA_PASSWORD", "")
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FILE = os.getenv("LOG_FILE", "logs/scraper.log")
    ERROR_LOG_FILE = os.getenv("ERROR_LOG_FILE", "logs/error.log")
    
    # Server Configuration
    HEADLESS_MODE = os.getenv("HEADLESS_MODE", "false").lower() == "true"
    CHROME_BINARY_PATH = os.getenv("CHROME_BINARY_PATH", "/usr/bin/google-chrome")
    DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")
    
    # Timing Configuration (in seconds)
    WEBDRIVER_TIMEOUT = int(os.getenv("WEBDRIVER_TIMEOUT", "8"))
    PAGE_LOAD_WAIT = float(os.getenv("PAGE_LOAD_WAIT", "1.5"))
    RETRY_ATTEMPTS = int(os.getenv("RETRY_ATTEMPTS", "3"))
    
    # Timezone
    TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
    
    # Validation
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []
        
        if not cls.SPREADSHEET_ID:
            errors.append("SPREADSHEET_ID is required")
            
        if not cls.TAXSUTRA_USERNAME:
            errors.append("TAXSUTRA_USERNAME is required")
            
        if not cls.TAXSUTRA_PASSWORD:
            errors.append("TAXSUTRA_PASSWORD is required")
            
        if not Path(cls.SERVICE_ACCOUNT_FILE).exists():
            errors.append(f"Service account file not found: {cls.SERVICE_ACCOUNT_FILE}")
            
        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(f"- {error}" for error in errors))
    
    @classmethod
    def setup_logging(cls):
        """Setup logging configuration"""
        # Ensure logs directory exists
        cls.LOGS_DIR.mkdir(exist_ok=True)
        
        # Configure logging
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Main logger
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL),
            format=log_format,
            handlers=[
                logging.FileHandler(cls.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        
        # Error logger
        error_logger = logging.getLogger('error')
        error_handler = logging.FileHandler(cls.ERROR_LOG_FILE)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(log_format))
        error_logger.addHandler(error_handler)
        
        return logging.getLogger(__name__)

# Initialize configuration
config = Config()

# Validate and setup logging when imported
try:
    config.validate()
    logger = config.setup_logging()
    logger.info("Configuration loaded successfully")
except Exception as e:
    print(f"Configuration error: {e}")
    print("Please check your .env file and ensure all required settings are provided.")
    exit(1) 