#!/usr/bin/env python3
"""
Automated Tax Rulings Scraper - Main Application
Scrapes yesterday's tax rulings (or weekend rulings if today is Monday) and uploads to Google Sheets
"""

import os
import sys
import json
import logging
from datetime import datetime, date
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import config, logger
from src.scraper import ITRulingsScraper, ITExpertCornerScraper, ITLitigationTrackerScraper
from src.sheets_uploader import SheetsUploader

def save_json_backup(rulings_data):
    """Save rulings data to JSON file as backup"""
    try:
        # Ensure downloads directory exists
        downloads_dir = Path(config.DOWNLOAD_DIR)
        downloads_dir.mkdir(exist_ok=True)
        
        # Save to fixed filename
        json_filename = downloads_dir / "rulings.json"
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(rulings_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 JSON backup saved: {json_filename}")
        return str(json_filename)
        
    except Exception as e:
        logger.error(f"❌ Failed to save JSON backup: {e}")
        return None

def main():
    """Main application function"""
    start_time = datetime.now()
    logger.info("🚀 Starting Automated Tax Rulings Scraper")
    logger.info(f"⏰ Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialize scraper
        logger.info("📡 Initializing scraper...")
        scraper = ITRulingsScraper()
        expert_corner_scraper = ITExpertCornerScraper()
        litigation_tracker_scraper = ITLitigationTrackerScraper()
        # Determine if today is Monday
        today = date.today()
        is_monday = today.weekday() == 0
        
        # Always scrape yesterday's rulings (or weekend rulings if today is Monday)
        if is_monday:
            logger.info("🔍 Today is Monday - starting scraping process for weekend rulings...")
            time_period = "weekend"
        else:
            logger.info("🔍 Starting scraping process for yesterday's rulings...")
            time_period = "yesterday"
            
        rulings_data = []
        expert_corner_data = []
        litigation_tracker_data = []
        
        # Use the yesterday rulings scraper method
        rulings_data = scraper.scrape_yesterday_rulings()
        expert_corner_data = expert_corner_scraper.scrape_yesterday_expert_corner()
        litigation_tracker_data = litigation_tracker_scraper.scrape_yesterday_litigation_tracker()
        # Save JSON backup
        json_file = save_json_backup(rulings_data)
        
        # Upload to Google Sheets
        logger.info("📊 Uploading to Google Sheets...")
        uploader = SheetsUploader()
        any_uploaded = False
        
        if rulings_data:
            logger.info(f"✅ Successfully {rulings_data} rulings")
            logger.info(f"✅ Successfully scraped {len(rulings_data)} rulings")
            if uploader.upload_data(rulings_data):
                logger.info("✅ Successfully uploaded to Google Sheets")
                logger.info(f"🔗 View at: {uploader.get_sheet_url()}")
                any_uploaded = True
            else:
                logger.error("❌ Failed to upload to Google Sheets")
                logger.info(f"💾 Data saved locally: {json_file}")
        
        else:
            logger.warning(f"⚠️ No rulings found for {time_period}")
            # return 1 
        
        if expert_corner_data:
            logger.info(f"Expert Corner Data: {expert_corner_data}")
            if uploader.upload_expert_corner_data(expert_corner_data):
                logger.info("✅ Successfully uploaded expert corner data to Google Sheets")
                any_uploaded = True
            else:
                logger.error("❌ Failed to upload expert corner data to Google Sheets")
        else:
            logger.warning(f"⚠️ No export articles found for {time_period}")
            # return 1
        
        if litigation_tracker_data:
            logger.info(f"Expert Corner Data: {litigation_tracker_data}")
            if uploader.upload_litigation_tracker_data(litigation_tracker_data):
                logger.info("✅ Successfully uploaded expert corner data to Google Sheets")
                any_uploaded = True
            else:
                logger.error("❌ Failed to upload expert corner data to Google Sheets")
        else:
            logger.warning(f"⚠️ No export articles found for {time_period}")
            # return 1
        
        if not any_uploaded:
            logger.warning("⚠️ No data to upload to Google Sheets.")
            # return 1
        
        # Success summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("🎉 SCRAPING COMPLETED SUCCESSFULLY!")
        logger.info(f"📋 Rulings processed: {len(rulings_data)}")
        logger.info(f"📋 Expert Corner processed: {len(expert_corner_data)}")
        logger.info(f"⏱️ Total time: {duration}")
        logger.info(f"📊 Google Sheets updated: {uploader.get_sheet_url()}")
        logger.info(f"💾 JSON backup: {json_file}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("⏹️ Process interrupted by user")
        return 130
        
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        return 1

def print_banner():
    """Print application banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                🤖 AUTOMATED TAX RULINGS SCRAPER             ║
    ║                                                              ║
    ║  🎯 Extracts yesterday's tax rulings from Taxsutra.com     ║
    ║  📊 Uploads data to Google Sheets automatically            ║
    ║  ⚡ Optimized for server deployment & automation            ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

if __name__ == "__main__":
    # Print banner
    print_banner()
    
    # Set up logging for main execution
    try:
        # Ensure logs directory exists
        config.LOGS_DIR.mkdir(exist_ok=True)
        
        # Run main function
        exit_code = main()
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"💥 Critical error: {e}")
        sys.exit(1) 