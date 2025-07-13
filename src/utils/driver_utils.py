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
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
        
        # Add user data directory to use your Chrome profile
        chrome_profile_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chrome_profile")
        chrome_options.add_argument(f"--user-data-dir={chrome_profile_path}")
        
        # Set Chrome binary path from config
        if os.path.exists(config.CHROME_BINARY_PATH):
            chrome_options.binary_location = config.CHROME_BINARY_PATH
            logger.info(f"Using Chrome binary from config: {config.CHROME_BINARY_PATH}")
        
        # Create Chrome driver directly
        try:
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome WebDriver created successfully with user profile")
        except Exception as e:
            logger.error(f"Failed to create Chrome WebDriver with user profile: {e}")
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
    
def login_to_taxsutra(driver, config):
    """
    Login to Taxsutra.com with retry mechanism
    
    Args:
        driver: WebDriver instance
        config: Configuration object with settings
        target_url: Optional URL to navigate to after login
        
    Returns:
        bool: True if login successful, False otherwise
    """
    
    # Check if already logged in by looking for a known element only visible when logged in
    try:
        driver.get("https://www.taxsutra.com/user/login")
        time.sleep(config.PAGE_LOAD_WAIT)
        # Check for a logout link or user profile element that only appears when logged in
        if "logout" in driver.page_source.lower() or "my account" in driver.page_source.lower():
            logger.info("Already logged in to Taxsutra.com, skipping login form.")
            return True
    except Exception as e:
        logger.warning(f"Could not verify login status before login attempt: {e}")
        
    try:
        logger.info("Logging in to Taxsutra.com...")
        
        if "logout" in driver.page_source.lower() or "my account" in driver.page_source.lower():
            logger.info("Already logged in to Taxsutra.com, skipping login form.")
            return True
    
        else:
            # Navigate to login page
            driver.get("https://www.taxsutra.com/user/login")
            time.sleep(config.PAGE_LOAD_WAIT)
            
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
        driver.get("https://www.taxmann.com/gp/auth/login")
        
        # Check if already logged in by looking for a user/account element or absence of login form
        try:
            # Wait briefly for page to load
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            # If a user/account/profile icon is present, assume already logged in
            # (Taxmann shows a user icon with class 'user-profile' or similar when logged in)
            user_icon = driver.find_elements(By.CSS_SELECTOR, ".user-profile, .profile-dropdown, .dropdown-user, .fa-user")
            if user_icon:
                logger.info("✅ Already logged in to Taxmann.com, skipping login form.")
                return True
            # Alternatively, if the login form is not present, assume logged in
            login_form = driver.find_elements(By.NAME, "email")
            if not login_form:
                logger.info("✅ Login form not found, possibly already logged in to Taxmann.com.")
                return True
        except Exception as e:
            logger.debug(f"Could not determine login state: {e}")

        # Fill login form
        try:
            try:
                login_with_email_btn = WebDriverWait(driver, config.WEBDRIVER_TIMEOUT).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Login with Email')]"))
                )
                login_with_email_btn.click()
            except Exception as e:
                logger.warning(f"'Login with Email' button not found or not clickable: {e}")
                pass
            
            # Now wait for email field and enter email
            email_field = WebDriverWait(driver, config.WEBDRIVER_TIMEOUT).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            email_field.clear()
            email_field.send_keys(config.TAXMANN_EMAIL)

            # Wait for password field
            password_field = WebDriverWait(driver, config.WEBDRIVER_TIMEOUT).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_field.clear()
            password_field.send_keys(config.TAXMANN_PASSWORD)
            
            time.sleep(5)

            # Click login button
            login_button = WebDriverWait(driver, config.WEBDRIVER_TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
            )
            login_button.click()
            
            # Wait for login to complete
            # time.sleep(config.PAGE_LOAD_WAIT)
            
            # Check if login successful
            time.sleep(10)

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