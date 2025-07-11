#!/usr/bin/env python3
"""
Utility modules for the tax rulings scraper
"""

# Import utility modules for easy access
from src.utils.driver_utils import (
    setup_driver,
    login_to_taxsutra,
    login_to_taxmann,
    handle_paywall_login
)

from src.utils.date_utils import (
    get_today_string,
    get_yesterday_string,
    get_yesterday_date,
    get_weekend_dates,
    is_today_date,
    is_target_date,
    normalize_date_for_compare,
    extract_date,
    is_date_in_range
)