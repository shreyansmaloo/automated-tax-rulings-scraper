#!/usr/bin/env python3
"""
Automated Tax Rulings Scraper - Main Application
Scrapes yesterday's tax rulings (or weekend rulings if today is Monday) from Taxsutra.com and Taxmann.com
and uploads to Google Sheets
"""

import sys
import json
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import config, logger
from src.scraper import ITRulingsScraper, ITExpertCornerScraper, ITLitigationTrackerScraper
from src.taxmann_scraper import TaxmannGSTScraper, TaxmannCompanySEBIScraper, TaxmannFEMABankingScraper
from src.sheets_uploader import SheetsUploader
from src.utils.driver_utils import setup_driver

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
    logger.info("🚀 Application started")
    logger.info(f"⏰ Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialize driver once to be shared across all scrapers
        logger.info("📡 Setting up shared WebDriver...")
        driver = setup_driver(config)
        if not driver:
            logger.error("❌ Failed to set up WebDriver, aborting.")
            return 1

        rulings_data = []
        taxmann_gst_data = []
        expert_corner_data = []
        litigation_tracker_data = []
        taxmann_fema_banking_data = []
        taxmann_company_sebi_data = []
        
        # Define time period for logging
        time_period = "yesterday" if datetime.now().weekday() != 0 else "the weekend"
        
        # Initialize all Taxsutra scrapers with the same driver
        logger.info("📡 Starting Taxsutra.com scraping...")
        
        # Initialize the first scraper and login
        taxsutra_rulings_scraper = ITRulingsScraper(driver)
        taxsutra_rulings_scraper.login_to_taxsutra()
        
        # Scrape rulings data
        rulings_data = taxsutra_rulings_scraper.scrape_yesterday_rulings(taxsutra_rulings_scraper.target_url)
        
        # Initialize other Taxsutra scrapers with the same driver (no need to login again)
        taxsutra_expert_corner_scraper = ITExpertCornerScraper(driver)
        expert_corner_data = taxsutra_expert_corner_scraper.scrape_yesterday_expert_corner()
        
        taxsutra_litigation_tracker_scraper = ITLitigationTrackerScraper(driver)
        litigation_tracker_data = taxsutra_litigation_tracker_scraper.scrape_yesterday_litigation_tracker()
        
        # logger.info("📡 Starting Taxmann.com scraping...")
        # # Initialize Taxmann scrapers with the same driver
        # taxmann_gst_scraper = TaxmannGSTScraper(driver)
        # # Only login once for all Taxmann scrapers
        # taxmann_gst_scraper.login_to_taxmann()
        # taxmann_gst_data = taxmann_gst_scraper.scrape_yesterday_gst_updates()
        
        # # Reuse the same driver for other Taxmann scrapers (no need to login again)
        # taxmann_company_sebi_scraper = TaxmannCompanySEBIScraper(driver)
        # taxmann_company_sebi_data = taxmann_company_sebi_scraper.scrape_yesterday_company_sebi_updates()
        
        # taxmann_fema_banking_scraper = TaxmannFEMABankingScraper(driver)
        # taxmann_fema_banking_data = taxmann_fema_banking_scraper.scrape_yesterday_fema_banking_updates()
        
        # Clean up the driver after all scrapers are done
        if driver:
            driver.quit()
            logger.info("🧹 WebDriver cleaned up")
        
        # Combine all data for backup
        all_data = {
            "taxsutra": {
                "rulings": rulings_data,
                "expert_corner": expert_corner_data,
                "litigation_tracker": litigation_tracker_data
            },
            "taxmann": {
                "gst": taxmann_gst_data,
                "company_sebi": taxmann_company_sebi_data,
                "fema_banking": taxmann_fema_banking_data
            }
        }
        
        # Save JSON backup
        json_file = save_json_backup(all_data)
        
        # Upload to Google Sheets
        logger.info("📊 Uploading to Google Sheets...")
        uploader = SheetsUploader()
        any_uploaded = False
        
        if rulings_data:
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
        
        # Upload Taxmann data to Google Sheets
        if taxmann_gst_data:
            logger.info(f"✅ Successfully scraped {len(taxmann_gst_data)} Taxmann GST updates")
            if uploader.upload_taxmann_data(taxmann_gst_data):
                logger.info("✅ Successfully uploaded Taxmann GST data to Google Sheets")
                any_uploaded = True
            else:
                logger.error("❌ Failed to upload Taxmann GST data to Google Sheets")
        else:
            logger.warning(f"⚠️ No Taxmann GST updates found for {time_period}")
        
        if taxmann_company_sebi_data:
            logger.info(f"✅ Successfully scraped {len(taxmann_company_sebi_data)} Taxmann Company & SEBI updates")
            if uploader.upload_taxmann_data(taxmann_company_sebi_data):
                logger.info("✅ Successfully uploaded Taxmann Company & SEBI data to Google Sheets")
                any_uploaded = True
            else:
                logger.error("❌ Failed to upload Taxmann Company & SEBI data to Google Sheets")
        else:
            logger.warning(f"⚠️ No Taxmann Company & SEBI updates found for {time_period}")
        
        if taxmann_fema_banking_data:
            logger.info(f"✅ Successfully scraped {len(taxmann_fema_banking_data)} Taxmann FEMA & Banking updates")
            if uploader.upload_taxmann_data(taxmann_fema_banking_data):
                logger.info("✅ Successfully uploaded Taxmann FEMA & Banking data to Google Sheets")
                any_uploaded = True
            else:
                logger.error("❌ Failed to upload Taxmann FEMA & Banking data to Google Sheets")
        else:
            logger.warning(f"⚠️ No Taxmann FEMA & Banking updates found for {time_period}")
            
        if not any_uploaded:
            logger.warning("⚠️ No data to upload to Google Sheets.")
            # return 1
        
        # Success summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("🎉 SCRAPING COMPLETED SUCCESSFULLY!")
        logger.info(f"📋 Taxsutra Rulings processed: {len(rulings_data)}")
        logger.info(f"📋 Taxsutra Expert Corner processed: {len(expert_corner_data)}")
        logger.info(f"📋 Taxsutra Litigation Tracker processed: {len(litigation_tracker_data)}")
        logger.info(f"📋 Taxmann GST updates processed: {len(taxmann_gst_data)}")
        logger.info(f"📋 Taxmann Company & SEBI updates processed: {len(taxmann_company_sebi_data)}")
        logger.info(f"📋 Taxmann FEMA & Banking updates processed: {len(taxmann_fema_banking_data)}")
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
    ║  🎯 Extracts yesterday's tax rulings from:                 ║
    ║     - Taxsutra.com                                        ║
    ║     - Taxmann.com                                         ║
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