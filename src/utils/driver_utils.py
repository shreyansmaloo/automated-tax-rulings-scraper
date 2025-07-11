#!/usr/bin/env python3
"""
Utility functions for WebDriver setup and login operations
"""

import time
import logging
import platform
import os
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Get logger
logger = logging.getLogger(__name__)

def setup_driver(config):
    """
    Set up and configure Chrome WebDriver with performance optimizations
    
    Args:
        config: Configuration object with settings
        
    Returns:
        WebDriver instance or None if setup fails
    """
    try:
        logger.info("Setting up Chrome WebDriver...")
        
        # Configure Chrome options for performance and headless mode
        chrome_options = Options()
        
        # Add essential options only - removing problematic ones
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Set headless mode based on configuration
        if config.HEADLESS_MODE:
            chrome_options.add_argument("--headless=new")
            logger.info("Running in headless mode")
        
        # Set Chrome binary path from config
        if os.path.exists(config.CHROME_BINARY_PATH):
            chrome_options.binary_location = config.CHROME_BINARY_PATH
            logger.info(f"Using Chrome binary from config: {config.CHROME_BINARY_PATH}")
        
        # Detect system architecture and OS
        system = platform.system()
        machine = platform.machine()
        logger.info(f"Detected system: {system} {machine}")
        
        # Special handling for Mac ARM (Apple Silicon)
        if system == "Darwin" and machine == "arm64":
            logger.info("Using special handling for Mac ARM architecture")
            
            # Use our downloaded ChromeDriver
            local_chromedriver_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                                "drivers/chromedriver-mac-arm64/chromedriver")
            
            if os.path.exists(local_chromedriver_path):
                logger.info(f"Using local ChromeDriver found at: {local_chromedriver_path}")
                # Make sure it's executable
                try:
                    os.chmod(local_chromedriver_path, 0o755)
                    service = Service(executable_path=local_chromedriver_path)
                    
                    # Add debugging information
                    logger.info("Creating Chrome WebDriver with local chromedriver")
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    logger.info("Chrome WebDriver created successfully")
                    
                except Exception as e:
                    logger.error(f"Error using local ChromeDriver: {e}")
                    logger.info("Falling back to direct instantiation")
                    try:
                        driver = webdriver.Chrome(options=chrome_options)
                    except Exception as inner_e:
                        logger.error(f"Direct instantiation also failed: {inner_e}")
                        return None
            else:
                logger.warning(f"Local ChromeDriver not found at {local_chromedriver_path}, trying direct instantiation")
                try:
                    driver = webdriver.Chrome(options=chrome_options)
                except Exception as e:
                    logger.error(f"Direct instantiation failed: {e}")
                    return None
                
        else:
            # Standard approach for other platforms
            try:
                driver = webdriver.Chrome(options=chrome_options)
                logger.info("Using system ChromeDriver")
            except Exception as e:
                logger.info(f"System ChromeDriver not available: {e}. Using webdriver-manager...")
                try:
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    logger.info("Using webdriver-manager ChromeDriver")
                except Exception as inner_e:
                    logger.error(f"WebDriver manager installation failed: {inner_e}")
                    return None
        
        # Set page load timeout
        driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
        
        # Verify driver is working by loading a simple page
        try:
            logger.info("Testing WebDriver with a simple page load...")
            driver.get("about:blank")
            logger.info("WebDriver test successful")
        except Exception as e:
            logger.error(f"WebDriver test failed: {e}")
            if driver:
                driver.quit()
            return None
        
        logger.info("✅ Chrome WebDriver setup complete")
        return driver
        
    except Exception as e:
        logger.error(f"❌ Failed to set up Chrome WebDriver: {e}")
        return None

def login_to_taxsutra(driver, config, target_url=None):
    """
    Login to Taxsutra.com with retry mechanism
    
    Args:
        driver: WebDriver instance
        config: Configuration object with settings
        target_url: Optional URL to navigate to after login
        
    Returns:
        bool: True if login successful, False otherwise
    """
    try:
        logger.info("Logging in to Taxsutra.com...")
        
        # Navigate to login page
        driver.get("https://www.taxsutra.com/user/login")
        time.sleep(config.PAGE_LOAD_WAIT)
        
        # Check if already logged in
        if "My Account" in driver.page_source:
            logger.info("Already logged in to Taxsutra.com")
            
            # Navigate to target URL if provided
            if target_url:
                logger.info(f"Navigating to {target_url}")
                driver.get(target_url)
                time.sleep(config.PAGE_LOAD_WAIT)
                
            return True
        
        # Fill login form
        try:
            # Wait for username field
            username_field = WebDriverWait(driver, config.WEBDRIVER_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "edit-name"))
            )
            username_field.clear()
            username_field.send_keys(config.TAXSUTRA_USERNAME)
            
            # Wait for password field
            password_field = WebDriverWait(driver, config.WEBDRIVER_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "edit-pass"))
            )
            password_field.clear()
            password_field.send_keys(config.TAXSUTRA_PASSWORD)
            
            # Click login button
            login_button = WebDriverWait(driver, config.WEBDRIVER_TIMEOUT).until(
                EC.element_to_be_clickable((By.ID, "edit-submit"))
            )
            login_button.click()

            try:
                force_login_button = WebDriverWait(driver, 8).until(
                    EC.element_to_be_clickable((By.ID, "edit-reset"))
                )
                force_login_button.click()
                logger.info("Handled force login")
            except:
                logger.debug("No force login required")

            # Wait for login to complete
            time.sleep(config.PAGE_LOAD_WAIT)

        except Exception as e:
            logger.error(f"❌ Error during login form submission: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Login to Taxsutra.com failed: {e}")
        return False

def login_to_taxmann(driver, config):
    """
    Login to Taxmann.com with retry mechanism
    
    Args:
        driver: WebDriver instance
        config: Configuration object with settings
        
    Returns:
        bool: True if login successful, False otherwise
    """
    try:
        logger.info("Logging in to Taxmann.com...")
        
        # Navigate to login page
        driver.get("https://www.taxmann.com/login")
        time.sleep(config.PAGE_LOAD_WAIT)
        
        # Check if already logged in
        if "My Account" in driver.page_source or "Log out" in driver.page_source:
            logger.info("Already logged in to Taxmann.com")
            return True
        
        # Fill login form
        try:
            # Wait for email field
            email_field = WebDriverWait(driver, config.WEBDRIVER_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            email_field.clear()
            email_field.send_keys(config.TAXMANN_EMAIL)
            
            # Wait for password field
            password_field = WebDriverWait(driver, config.WEBDRIVER_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            password_field.clear()
            password_field.send_keys(config.TAXMANN_PASSWORD)
            
            # Click login button
            login_button = WebDriverWait(driver, config.WEBDRIVER_TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
            )
            login_button.click()
            
            # Wait for login to complete
            time.sleep(config.PAGE_LOAD_WAIT)
            
            # Check if login successful
            if "My Account" in driver.page_source or "Log out" in driver.page_source:
                logger.info("✅ Successfully logged in to Taxmann.com")
                return True
            else:
                logger.warning("❌ Login to Taxmann.com failed - incorrect credentials or site issue")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error during login form submission: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Login to Taxmann.com failed: {e}")
        return False

def handle_paywall_login(driver, config):
    """
    Handle paywall login if encountered
    
    Args:
        driver: WebDriver instance
        config: Configuration object with settings
        
    Returns:
        bool: True if handled successfully, False otherwise
    """
    try:
        # Check if paywall is present
        paywall_indicators = [
            "Please login to continue", 
            "Login to continue", 
            "Subscribe to continue",
            "Login to read full article",
            "Login to view"
        ]
        
        page_source = driver.page_source.lower()
        if any(indicator.lower() in page_source for indicator in paywall_indicators):
            logger.info("Paywall detected, attempting login...")
            
            # Look for login button
            try:
                login_button = WebDriverWait(driver, config.WEBDRIVER_TIMEOUT).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Login') or contains(@href, 'login')]")
                    )
                )
                login_button.click()
                time.sleep(config.PAGE_LOAD_WAIT)
                
                # Now on login page, perform login
                if "taxsutra.com" in driver.current_url:
                    return login_to_taxsutra(driver, config)
                elif "taxmann.com" in driver.current_url:
                    return login_to_taxmann(driver, config)
                else:
                    logger.warning("Unknown login page, cannot proceed")
                    return False
                    
            except Exception as e:
                logger.warning(f"Could not find or click login button: {e}")
                return False
        else:
            # No paywall detected
            return True
            
    except Exception as e:
        logger.error(f"❌ Error handling paywall: {e}")
        return False