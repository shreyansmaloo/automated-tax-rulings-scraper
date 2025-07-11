#!/usr/bin/env python3
"""
Base Scraper class that provides common functionality for all scrapers
"""

import logging
from datetime import date

from config.settings import config
from src.utils.driver_utils import setup_driver, login_to_taxsutra, login_to_taxmann, handle_paywall_login
from src.utils.date_utils import (
    get_today_string, get_yesterday_string, get_weekend_dates,
    is_today_date, is_target_date, normalize_date_for_compare,
    extract_date, is_date_in_range
)

logger = logging.getLogger(__name__)

class BaseScraper:
    """
    Base Scraper class that provides common functionality for all scrapers
    
    This class handles common operations like:
    - Driver setup
    - Login to Taxsutra and Taxmann
    - Date utilities
    - Paywall handling
    
    All scraper classes should inherit from this base class.
    """
    
    def __init__(self, driver):
        """
        Initialize the base scraper with configuration and driver
        
        Args:
            driver: WebDriver instance to use for scraping. Should be provided by the caller.
        """
        if driver is None:
            raise ValueError("Driver must be provided to BaseScraper")
            
        self.driver = driver
        self.config = config
        self.target_url = None  # Subclasses should set this
    
    def setup_driver(self):
        """
        Setup Chrome WebDriver with performance optimizations
        Only used when a driver isn't already provided
        
        Returns:
            bool: True if driver setup was successful, False otherwise
        """
        logger.info("Setting up Chrome WebDriver...")
        if self.driver is None:
            self.driver = setup_driver(self.config)
        return self.driver is not None
    
    def login_to_taxsutra(self, target_url="https://www.taxsutra.com/"):
        """
        Login to Taxsutra website with retry mechanism
        
        Args:
            target_url: Optional URL to navigate to after login
            
        Returns:
            bool: True if login successful, False otherwise
        """
        logger.info("Checking if login to Taxsutra is needed...")
        return login_to_taxsutra(self.driver, self.config, target_url=target_url)
    
    def login_and_navigate(self, target_url="https://www.taxsutra.com/"):
        """
        Login and navigate to the specified target URL.
        If target_url is None, uses self.target_url instead.
        
        Args:
            target_url: Optional URL to navigate to after login
            
        Returns:
            bool: True if login and navigation successful, False otherwise
        """
        url_to_use = target_url if target_url else self.target_url
        if not self.login_to_taxsutra(url_to_use):
            logger.error("Failed to login, aborting scraping")
            return False
        return True

    def login_to_taxmann(self):
        """
        Login to Taxmann website with retry mechanism
        
        Returns:
            bool: True if login successful, False otherwise
        """
        logger.info("Checking if login to Taxmann is needed...")
        return login_to_taxmann(self.driver, self.config)
    
    def handle_paywall_login(self):
        """
        Handle paywall login if encountered
        
        Returns:
            bool: True if handled successfully, False otherwise
        """
        logger.info("Checking for paywall...")
        return handle_paywall_login(self.driver, self.config)
    
    def get_today_string(self):
        """
        Get today's date in Taxsutra format
        
        Returns:
            str: Today's date in format 'Mon DD, YYYY'
        """
        return get_today_string()
    
    def get_yesterday_string(self):
        """
        Get yesterday's date in Taxsutra format
        
        Returns:
            str: Yesterday's date in format 'Mon DD, YYYY'
        """
        return get_yesterday_string()
    
    def get_weekend_dates(self):
        """
        Get weekend dates (Saturday and Sunday) if today is Monday
        
        Returns:
            list: List of weekend dates in format 'Mon DD, YYYY'
        """
        return get_weekend_dates()
    
    def is_today_date(self, date_string):
        """
        Check if the given date string is today's date
        
        Args:
            date_string: Date string to check
            
        Returns:
            bool: True if date_string is today's date, False otherwise
        """
        return is_today_date(date_string)
    
    def is_target_date(self, date_string, target_dates):
        """
        Check if the given date string matches any of the target dates
        
        Args:
            date_string: Date string to check
            target_dates: List of target date strings
            
        Returns:
            bool: True if date_string matches any target date, False otherwise
        """
        return is_target_date(date_string, target_dates)
    
    def normalize_date_for_compare(self, date_str):
        """
        Normalize date string to 'Mon D, YYYY' (no leading zero on day)
        
        Args:
            date_str: Date string to normalize
            
        Returns:
            str: Normalized date string
        """
        return normalize_date_for_compare(date_str)
    
    def extract_date(self, text):
        """
        Extract date from text using multiple formats and regex patterns
        
        Args:
            text: Text to extract date from
            
        Returns:
            str: Extracted date in format 'Mon DD, YYYY' or None if no date found
        """
        return extract_date(text)
    
    def is_date_in_range(self, date_str, start_date, end_date):
        """
        Check if date is within a specified range
        
        Args:
            date_str: Date string to check
            start_date: Start date of range
            end_date: End date of range
            
        Returns:
            bool: True if date is in range, False otherwise
        """
        return is_date_in_range(date_str, start_date, end_date)
    
    def get_target_dates(self):
        """
        Get target dates based on current day of week
        
        Returns:
            list: List of target date strings
        """
        today = date.today()
        
        # If today is Saturday or Sunday, return empty list
        if today.weekday() in [5, 6]:  # 5=Saturday, 6=Sunday
            logger.info("Today is Saturday or Sunday, not generating any data.")
            return []
        
        # If today is Monday, return weekend dates
        if today.weekday() == 0:  # Monday
            target_dates = self.get_weekend_dates()
            logger.info(f"Today is Monday, looking for weekend data published on: {', '.join(target_dates)}")
        else:
            # Otherwise return yesterday's date
            target_dates = [self.get_yesterday_string()]
            logger.info(f"Looking for data published on: {target_dates[0]}")
        
        return target_dates
    
    def cleanup(self):
        """
        Clean up resources (close driver)
        """
        if self.driver:
            self.driver.quit()
            logger.info("Chrome driver closed")