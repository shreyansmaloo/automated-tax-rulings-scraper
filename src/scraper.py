"""
Core scraping functionality for automated tax rulings
Optimized for performance with headless Chrome support
"""

import logging
import time
import re
from datetime import date
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from config.settings import config

logger = logging.getLogger(__name__)

class ITRulingsScraper:
    """Main scraper class for automated tax rulings"""
    
    def __init__(self):
        self.driver = None
        self.config = config
        
    def setup_driver(self):
        """Setup Chrome WebDriver with performance optimizations"""
        logger.info("Setting up Chrome WebDriver...")
        
        chrome_options = Options()
        
        # Performance optimizations
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        
        # Major performance boost - disable images and media
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        
        # Memory optimizations
        chrome_options.add_argument("--memory-pressure-off")
        chrome_options.add_argument("--max_old_space_size=2048")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--disable-sync")
        chrome_options.add_argument("--disable-default-apps")
        
        # Headless mode for server deployment
        if self.config.HEADLESS_MODE:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--single-process")  # Important for server resources
            
        # Set Chrome binary path if specified
        if self.config.CHROME_BINARY_PATH and self.config.CHROME_BINARY_PATH != "/usr/bin/google-chrome":
            chrome_options.binary_location = self.config.CHROME_BINARY_PATH
        
        # Optimized preferences
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.geolocation": 2,
            "profile.default_content_settings.popups": 0
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            # Try to use system ChromeDriver first, then webdriver-manager
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                logger.info("✅ Chrome WebDriver initialized with system driver")
            except:
                # Fallback to webdriver-manager
                chromedriver_path = ChromeDriverManager().install()
                service = Service(chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("✅ Chrome WebDriver initialized with webdriver-manager")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Chrome WebDriver: {e}")
            return False
    
    def login_to_taxsutra(self):
        """Login to Taxsutra website"""
        try:
            logger.info("Navigating to Taxsutra login page...")
            self.driver.get("https://www.taxsutra.com/dt/rulings")
            
            # Click Sign in button
            signin_button = WebDriverWait(self.driver, self.config.WEBDRIVER_TIMEOUT).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/user/login']"))
            )
            signin_button.click()
            logger.info("Clicked Sign in button")
            
            # Wait for login form
            WebDriverWait(self.driver, self.config.WEBDRIVER_TIMEOUT).until(
                EC.visibility_of_element_located((By.ID, "edit-name"))
            )
            
            # Enter credentials
            username_field = self.driver.find_element(By.ID, "edit-name")
            password_field = self.driver.find_element(By.ID, "edit-pass")
            login_button = self.driver.find_element(By.ID, "edit-submit")
            
            username_field.send_keys(self.config.TAXSUTRA_USERNAME)
            password_field.send_keys(self.config.TAXSUTRA_PASSWORD)
            login_button.click()
            logger.info("Submitted login credentials")
            
            # Handle force login if needed
            try:
                force_login_button = WebDriverWait(self.driver, 8).until(
                    EC.element_to_be_clickable((By.ID, "edit-reset"))
                )
                force_login_button.click()
                logger.info("Handled force login")
            except:
                logger.debug("No force login required")
            
            # Navigate back to rulings page
            self.driver.get("https://www.taxsutra.com/dt/rulings")
            time.sleep(self.config.PAGE_LOAD_WAIT)
            
            logger.info("✅ Successfully logged in to Taxsutra")
            return True
            
        except Exception as e:
            logger.error(f"❌ Login failed: {e}")
            return False
    
    def get_today_string(self):
        """Get today's date in Taxsutra format"""
        today = date.today()
        return today.strftime("%b %d, %Y")
    
    def is_today_date(self, date_string):
        """Check if the given date string is today's date"""
        if not date_string or date_string == "N/A":
            return False
        
        today_str = self.get_today_string()
        normalized_date = " ".join(date_string.strip().split())
        normalized_today = " ".join(today_str.split())
        
        return normalized_date == normalized_today
    
    def handle_paywall_login(self):
        """Handle paywall login if it appears"""
        try:
            paywall_form = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".payWallWrap #user-login-form"))
            )
            logger.info("Paywall detected, attempting re-login...")
            
            username_field = paywall_form.find_element(By.ID, "edit-name")
            password_field = paywall_form.find_element(By.ID, "edit-pass")
            login_button = paywall_form.find_element(By.ID, "edit-submit--2")
            
            username_field.send_keys(self.config.TAXSUTRA_USERNAME)
            password_field.send_keys(self.config.TAXSUTRA_PASSWORD)
            login_button.click()
            
            WebDriverWait(self.driver, self.config.WEBDRIVER_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".payWallWrap"))
            )
            logger.info("✅ Paywall login successful")
            time.sleep(self.config.PAGE_LOAD_WAIT)
            
        except Exception as e:
            logger.debug(f"No paywall or paywall handling failed: {e}")
    
    def extract_ruling_data(self):
        """Extract data from a single ruling page"""
        data = {}
        
        # Wait for page to load
        time.sleep(self.config.PAGE_LOAD_WAIT)
        
        # Handle paywall if present
        self.handle_paywall_login()
        
        # Extract Title
        try:
            title_element = WebDriverWait(self.driver, self.config.WEBDRIVER_TIMEOUT).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "h3 .field--name-title"))
            )
            data["Title"] = title_element.text.strip()
            logger.debug(f"Extracted title: {data['Title'][:50]}...")
        except:
            try:
                title_text = self.driver.title
                if " | IT-rulings" in title_text:
                    data["Title"] = title_text.replace(" | IT-rulings", "").strip()
                else:
                    data["Title"] = title_text.strip()
                logger.debug("Extracted title from page title")
            except:
                data["Title"] = "N/A"
                logger.warning("Could not extract title")
        
        # Extract Published Date
        try:
            published_date_element = WebDriverWait(self.driver, self.config.WEBDRIVER_TIMEOUT).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".podcastTimeDate"))
            )
            data["Published Date"] = published_date_element.text.strip()
            logger.debug(f"Extracted published date: {data['Published Date']}")
        except:
            data["Published Date"] = "N/A"
            logger.warning("Could not extract published date")
        
        # Extract Ruling Date
        try:
            date_element = WebDriverWait(self.driver, self.config.WEBDRIVER_TIMEOUT).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".field--name-field-date-of-judgement .field__item"))
            )
            date_text = date_element.text.strip()
            
            # Extract date using regex
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_text)
            if date_match:
                data["Ruling Date"] = date_match.group(1)
            else:
                data["Ruling Date"] = date_text
            logger.debug(f"Extracted ruling date: {data['Ruling Date']}")
        except:
            data["Ruling Date"] = "N/A"
            logger.warning("Could not extract ruling date")
        
        # Extract Conclusion
        try:
            conclusion_element = WebDriverWait(self.driver, self.config.WEBDRIVER_TIMEOUT).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#conclusion > div > div.field__item > p"))
            )
            data["Conclusion"] = conclusion_element.text
            logger.debug(f"Extracted conclusion: {len(data['Conclusion'])} characters")
        except:
            data["Conclusion"] = "N/A"
            logger.warning("Could not extract conclusion")
        
        # Extract Decision Summary
        try:
            decision_summary_element = WebDriverWait(self.driver, self.config.WEBDRIVER_TIMEOUT).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#block-taxsutra-digital-content > div > div > div.offset-md-1.col-md-10.rulingsDetailsWrap > div.centerLayoutWrap > div.centerContentWrap > div.clearfix.text-formatted.field.field--name-body.field--type-text-with-summary.field--label-above"))
            )
            raw_text = decision_summary_element.text
            cleaned_text = raw_text
            
            # Clean up the text
            if raw_text.startswith("Decision Summary"):
                cleaned_text = raw_text.replace("Decision Summary", "", 1).strip()
            
            data["Decision Summary"] = cleaned_text
            logger.debug(f"Extracted decision summary: {len(cleaned_text)} characters")
        except:
            data["Decision Summary"] = "N/A"
            logger.warning("Could not extract decision summary")
        
        # Extract Case Law Information
        try:
            case_law_element = WebDriverWait(self.driver, self.config.WEBDRIVER_TIMEOUT).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#block-taxsutra-digital-content > div > div > div.offset-md-1.col-md-10.rulingsDetailsWrap > div.centerLayoutWrap > div.centerContentWrap > div:nth-child(11)"))
            )
            raw_text = case_law_element.text
            cleaned_text = raw_text
            
            # Clean up the text
            prefixes_to_remove = ["Case Law Information", "Case Name :", "Case Name"]
            for prefix in prefixes_to_remove:
                if cleaned_text.startswith(prefix):
                    cleaned_text = cleaned_text.replace(prefix, "", 1).strip()
                    break
            
            data["Case Law Information"] = cleaned_text
            logger.debug(f"Extracted case law info: {len(cleaned_text)} characters")
        except:
            data["Case Law Information"] = "N/A"
            logger.warning("Could not extract case law information")
        
        return data
    
    def scrape_all_todays_rulings(self):
        """Main function to scrape all today's rulings"""
        if not self.setup_driver():
            return []
        
        try:
            if not self.login_to_taxsutra():
                logger.error("Failed to login, aborting scraping")
                return []
            
            today_str = self.get_today_string()
            logger.info(f"Looking for rulings published on: {today_str}")
            
            all_rulings = []
            page_count = 0
            
            while True:
                page_count += 1
                logger.info(f"Processing page {page_count}")
                
                # Find all ruling links on current page
                ruling_links = self.driver.find_elements(By.CSS_SELECTOR, "div.view-content.row div.views-row h3 > a")
                
                if not ruling_links:
                    logger.info("No more ruling links found")
                    break
                
                logger.info(f"Found {len(ruling_links)} ruling links on page {page_count}")
                
                # Extract URLs and titles to avoid stale element issues
                ruling_urls_and_titles = []
                for link in ruling_links:
                    try:
                        url = link.get_attribute("href")
                        title = link.text.strip()
                        ruling_urls_and_titles.append((url, title))
                    except Exception as e:
                        logger.warning(f"Error getting link data: {e}")
                        continue
                
                # Process each ruling
                for url, title in ruling_urls_and_titles:
                    try:
                        logger.info(f"Processing: {title[:60]}...")
                        
                        # Navigate to ruling page
                        self.driver.get(url)
                        time.sleep(self.config.PAGE_LOAD_WAIT)
                        
                        # Extract data
                        ruling_data = self.extract_ruling_data()
                        ruling_data["URL"] = url
                        
                        # Check if this ruling is from today
                        published_date = ruling_data.get("Published Date", "")
                        
                        if self.is_today_date(published_date):
                            logger.info(f"✅ Found today's ruling: {title[:50]}...")
                            all_rulings.append(ruling_data)
                        else:
                            logger.info(f"⏹️ Reached older ruling ({published_date}), stopping")
                            return all_rulings
                        
                        # Go back to main page
                        self.driver.get("https://www.taxsutra.com/dt/rulings")
                        time.sleep(self.config.PAGE_LOAD_WAIT)
                        
                    except Exception as e:
                        logger.error(f"Error processing ruling: {e}")
                        # Try to go back to main page
                        try:
                            self.driver.get("https://www.taxsutra.com/dt/rulings")
                            time.sleep(self.config.PAGE_LOAD_WAIT)
                        except:
                            logger.error("Failed to return to main page")
                        continue
                
                # Check for next page
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, ".pager__item--next a")
                    if next_button:
                        logger.info(f"Moving to page {page_count + 1}")
                        self.driver.execute_script("arguments[0].click();", next_button)
                        time.sleep(self.config.PAGE_LOAD_WAIT * 2)
                    else:
                        logger.info("No more pages to process")
                        break
                except:
                    logger.info("No next page found")
                    break
            
            logger.info(f"✅ Scraping completed. Found {len(all_rulings)} rulings from today")
            return all_rulings
            
        except Exception as e:
            logger.error(f"❌ Scraping failed with error: {e}")
            return []
            
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Chrome driver closed") 