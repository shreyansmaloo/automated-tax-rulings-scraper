#!/usr/bin/env python3
"""
Utility functions for date handling operations
"""

import re
import logging
from datetime import datetime, date, timedelta

# Get logger
logger = logging.getLogger(__name__)

def get_today_string():
    """
    Get today's date as a formatted string
    
    Returns:
        str: Today's date in format 'DD Month YYYY'
    """
    return date.today().strftime("%d %B %Y")

def get_yesterday_string():
    """Get yesterday's date in Taxsutra format"""
    yesterday = date.today() - timedelta(days=1)
    return yesterday.strftime("%b %d, %Y")
    
def get_weekend_dates():
    """Get weekend dates (Saturday and Sunday) if today is Monday"""
    today = date.today()
    
    # If today is Monday (weekday 0), get Saturday and Sunday dates
    if today.weekday() == 0:  # Monday
        saturday = today - timedelta(days=2)  # Saturday
        sunday = today - timedelta(days=1)    # Sunday
        return [saturday.strftime("%b %d, %Y"), sunday.strftime("%b %d, %Y")]
    else:
        # Just return yesterday for non-Monday
        yesterday = today - timedelta(days=1)
        return [yesterday.strftime("%b %d, %Y")]

def get_yesterday_date():
    """
    Get yesterday's date as a date object
    
    Returns:
        date: Yesterday's date
    """
    return date.today() - timedelta(days=1)

def is_today_date(date_str):
    """
    Check if the given date string represents today's date
    
    Args:
        date_str (str): Date string to check
        
    Returns:
        bool: True if date_str represents today's date, False otherwise
    """
    try:
        today = date.today().strftime("%d %B %Y")
        return normalize_date_for_compare(date_str) == normalize_date_for_compare(today)
    except Exception as e:
        logger.warning(f"Error checking if date is today: {e}")
        return False

# def is_today_date(self, date_string):
#     """Check if the given date string is today's date"""
#     if not date_string or date_string == "N/A":
#         return False
#     today_str = self.get_today_string()
#     normalized_date = " ".join(date_string.strip().split())
#     normalized_today = " ".join(today_str.split())
#     return normalized_date == normalized_today

def is_target_date(date_string, target_dates):
    """Check if the given date string matches any of the target dates"""
    if not date_string or date_string == "N/A":
        return False
    
    normalized_date = " ".join(date_string.strip().split())
    
    for target_date in target_dates:
        normalized_target = " ".join(target_date.split())
        if normalized_date == normalized_target:
            return True
            
    return False
    
def normalize_date_for_compare(date_str):
    """
    Normalize date string for comparison by removing ordinal suffixes and standardizing format
    
    Args:
        date_str (str): Date string to normalize
        
    Returns:
        str: Normalized date string
    """
    try:
        # Remove ordinal suffixes (1st, 2nd, 3rd, 4th, etc.)
        date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
        
        # Try to parse the date string into a datetime object
        date_formats = [
            "%d %B %Y",       # 01 January 2023
            "%d %b %Y",        # 01 Jan 2023
            "%B %d, %Y",       # January 01, 2023
            "%b %d, %Y",        # Jan 01, 2023
            "%d-%m-%Y",        # 01-01-2023
            "%d/%m/%Y",        # 01/01/2023
            "%Y-%m-%d"         # 2023-01-01
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                # Return in a standard format for comparison
                return dt.strftime("%d %B %Y")
            except ValueError:
                continue
                
        # If no format matches, try to extract using regex
        # Look for patterns like DD-MM-YYYY, DD/MM/YYYY, etc.
        date_patterns = [
            r'(\d{1,2})[-./](\d{1,2})[-./](\d{4})',  # DD-MM-YYYY or DD/MM/YYYY
            r'(\d{4})[-./](\d{1,2})[-./](\d{1,2})'   # YYYY-MM-DD
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                groups = match.groups()
                if len(groups[0]) == 4:  # YYYY-MM-DD format
                    year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                else:  # DD-MM-YYYY format
                    day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                    
                dt = datetime(year, month, day)
                return dt.strftime("%d %B %Y")
                
        # If all else fails, return the original string
        return date_str
        
    except Exception as e:
        logger.warning(f"Error normalizing date: {e}")
        return date_str

def extract_date(date_text):
    """
    Extract date from text in various formats
    
    Args:
        date_text (str): Text containing a date
        
    Returns:
        datetime or None: Extracted date as datetime object, or None if extraction fails
    """
    try:
        # Try different date formats
        date_formats = [
            "%d-%m-%Y",  # 01-01-2023
            "%d/%m/%Y",  # 01/01/2023
            "%d.%m.%Y",  # 01.01.2023
            "%d %b %Y",  # 01 Jan 2023
            "%d %B %Y",  # 01 January 2023
            "%b %d, %Y",  # Jan 01, 2023
            "%B %d, %Y",  # January 01, 2023
            "%Y-%m-%d"   # 2023-01-01
        ]
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_text.strip(), date_format)
            except:
                continue
                
        # If no format matches, try to extract using regex
        # Look for patterns like DD-MM-YYYY, DD/MM/YYYY, etc.
        date_patterns = [
            r'(\d{1,2})[-./](\d{1,2})[-./](\d{4})',  # DD-MM-YYYY or DD/MM/YYYY
            r'(\d{4})[-./](\d{1,2})[-./](\d{1,2})'   # YYYY-MM-DD
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_text)
            if match:
                groups = match.groups()
                if len(groups[0]) == 4:  # YYYY-MM-DD format
                    year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                else:  # DD-MM-YYYY format
                    day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                    
                return datetime(year, month, day)
                
        return None
        
    except Exception as e:
        logger.warning(f"Error extracting date from '{date_text}': {e}")
        return None

def is_date_in_range(check_date, target_dates):
    """
    Check if a date is in the range of target dates
    
    Args:
        check_date (datetime): Date to check
        target_dates (list): List of date objects to compare against
        
    Returns:
        bool: True if check_date is in target_dates, False otherwise
    """
    if not check_date:
        return False
        
    # Convert datetime to date if needed
    if isinstance(check_date, datetime):
        check_date = check_date.date()
        
    # Check if the date matches any target date
    return any(check_date == target_date for target_date in target_dates)