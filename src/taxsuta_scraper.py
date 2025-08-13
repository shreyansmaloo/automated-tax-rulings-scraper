import logging
import time
import re
import os
import requests
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from config.settings import config
from src.utils.base_scraper import TaxSutraBaseScraper

logger = logging.getLogger(__name__)

class RulingsScraper(TaxSutraBaseScraper):
    """Main scraper class for automated tax rulings"""
    
    def __init__(self, driver):
        """
        Initialize the ITRulingsScraper
        
        Args:
            driver: WebDriver instance to use for scraping
        """
        if driver is None:
            raise ValueError("Driver must be provided to ITRulingsScraper")
            
        super().__init__(driver)
        self.target_url = "https://www.taxsutra.com/dt/rulings"
    
    def extract_judicial_info_from_html(self, case_law_element):
        """
        Extract judicial information from case law information text.
        """
        try:
            # Get the full case law information text
            case_law_text = case_law_element.text.strip()
            
            # Look for "Judicial Level & Location" field in the text
            lines = case_law_text.split('\n')
            judicial_found = False
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Check if this line contains judicial level information
                if "Judicial Level & Location" in line and ":" in line:
                    # If the judicial info is on the same line after ":"
                    if line.count(":") == 1:
                        judicial_info = line.split(":", 1)[1].strip()
                        if judicial_info and judicial_info != "Judicial Level & Location":
                            return judicial_info
                    judicial_found = True
                elif judicial_found and line and not any(field in line for field in ["Appeal Number", "Date of Ruling", "Ruling in favour", "Section Reference"]):
                    # This might be the judicial info on the next line
                    if any(court_word in line.lower() for court_word in ["court", "tribunal", "itat", "commissioner"]):
                        return line
                    elif len(line) > 5 and not line.endswith(":"):  # Reasonable judicial info length
                        return line
                        
            # Alternative search for just "Judicial Level"
            for line in lines:
                line = line.strip()
                if "Judicial Level" in line and ":" in line:
                    judicial_info = line.split(":", 1)[1].strip()
                    if judicial_info:
                        return judicial_info
                        
            return "N/A"
            
        except Exception as e:
            logger.warning(f"Error extracting judicial info from HTML: {e}")
            return "N/A"

    def extract_case_name_from_html(self, case_law_element):
        """
        Extract case name from case law information text.
        """
        try:
            # Get the full case law information text
            case_law_text = case_law_element.text.strip()
            
            # Look for "Case Name" field in the text
            lines = case_law_text.split('\n')
            case_name_found = False
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Check if this line contains "Case Name"
                if "Case Name" in line and ":" in line:
                    # If the case name is on the same line after ":"
                    if line.count(":") == 1:
                        case_name = line.split(":", 1)[1].strip()
                        if case_name and case_name != "Case Name":
                            return case_name
                    case_name_found = True
                elif case_name_found and line and not any(field in line for field in ["Taxpayer Name", "Judicial Level", "Appeal Number", "Date of Ruling"]):
                    # This might be the case name on the next line
                    if " Vs " in line or " V. " in line or " v. " in line:
                        return line
                    elif len(line) > 10 and not line.endswith(":"):  # Reasonable case name length
                        return line
            
            # Fallback: Look for taxpayer name
            for line in lines:
                line = line.strip()
                if "Taxpayer Name" in line and ":" in line:
                    taxpayer_name = line.split(":", 1)[1].strip()
                    if taxpayer_name:
                        return taxpayer_name
                        
            return "N/A"
            
        except Exception as e:
            logger.warning(f"Error extracting case name from HTML: {e}")
            return "N/A"

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
        
        # Extract Citation Number
        try:
            citation_element = WebDriverWait(self.driver, self.config.WEBDRIVER_TIMEOUT).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".citationNumber"))
            )
            data["Citation"] = citation_element.text.strip()
            logger.debug(f"Extracted citation: {data['Citation']}")
        except:
            data["Citation"] = "N/A"
            logger.warning("Could not extract citation number")
        
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
        
        # # Extract Ruling Date
        # try:
        #     date_element = WebDriverWait(self.driver, self.config.WEBDRIVER_TIMEOUT).until(
        #         EC.visibility_of_element_located((By.CSS_SELECTOR, ".field--name-field-date-of-judgement .field__item"))
        #     )
        #     date_text = date_element.text.strip()
            
        #     # Extract date using regex
        #     date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_text)
        #     if date_match:
        #         data["Ruling Date"] = date_match.group(1)
        #     else:
        #         data["Ruling Date"] = date_text
        #     logger.debug(f"Extracted ruling date: {data['Ruling Date']}")
        # except:
        #     data["Ruling Date"] = "N/A"
        #     logger.warning("Could not extract ruling date")
        
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
        
        # Extract Case Law Information using improved HTML-based approach
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
            
            # Extract Case Name using HTML structure instead of regex
            data["Case Name"] = self.extract_case_name_from_html(case_law_element)
            logger.debug(f"Extracted case name: {data['Case Name']}")
            
            # Extract Judicial Level & Location using HTML structure instead of regex
            data["Judicial Level & Location"] = self.extract_judicial_info_from_html(case_law_element)
            logger.debug(f"Extracted judicial level & location: {data['Judicial Level & Location']}")
                
        except:
            data["Case Law Information"] = "N/A"
            data["Case Name"] = "N/A"
            data["Judicial Level & Location"] = "N/A"
            logger.warning("Could not extract case law information")
        
        # Extract Taxpayer Name from case law information
        try:
            # Try to extract from the case law information we already have
            case_law_text = data.get("Case Law Information", "")
            if case_law_text and case_law_text != "N/A":
                lines = case_law_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if "Taxpayer Name" in line and ":" in line:
                        taxpayer_name = line.split(":", 1)[1].strip()
                        if taxpayer_name:
                            data["Taxpayer Name"] = taxpayer_name
                            logger.debug(f"Extracted taxpayer name: {data['Taxpayer Name']}")
                            break
            
            # If still not found, try DOM-based extraction
            if "Taxpayer Name" not in data or data["Taxpayer Name"] == "N/A":
                try:
                    taxpayer_element = WebDriverWait(self.driver, self.config.WEBDRIVER_TIMEOUT).until(
                        EC.visibility_of_element_located((By.XPATH, "//div[contains(text(), 'Taxpayer Name')]/following-sibling::div"))
                    )
                    data["Taxpayer Name"] = taxpayer_element.text.strip()
                    logger.debug(f"Extracted taxpayer name from DOM: {data['Taxpayer Name']}")
                except:
                    data["Taxpayer Name"] = "N/A"
                    logger.debug("Could not extract taxpayer name")
            
        except:
            data["Taxpayer Name"] = "N/A"
            logger.debug("Could not extract taxpayer name")
        
        # Extract and download PDF if available
        data["PDF Path"] = None
        try:
            download_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/download/attachment-conclusion/')]"))
            )
            
            download_url = download_element.get_attribute('href')
            print(f"Download URL: {download_url}")
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"taxsutra_rulings_{timestamp}.pdf"

            selenium_cookies = self.driver.get_cookies()
            requests_cookies = {}
            for cookie in selenium_cookies:
                requests_cookies[cookie['name']] = cookie['value']
            
            # Download using requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(download_url, cookies=requests_cookies, headers=headers)
            downloads_dir = Path(config.DOWNLOAD_DIR)

            if response.status_code == 200:
                file_path = os.path.join(downloads_dir, filename)              
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"File downloaded successfully: {file_path}")
                data["PDF Path"] = filename  # Save the filename for the Excel link
            else:
                print(f"Failed to download. Status code: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"Error while looking for PDF: {e}")
        
        return data
    
    def extract_ruling_info_from_main_page(self, ruling_row):
        """Extract basic ruling information from main page listing"""
        try:
            # Extract URL and title
            link = ruling_row.find_element(By.CSS_SELECTOR, "h3 > a")
            url = link.get_attribute("href")
            title = link.text.strip()
            
            # Extract published date from the main page
            # Look for date elements in the ruling row
            date_elements = ruling_row.find_elements(By.CSS_SELECTOR, ".podcastTimeDate, .field--name-field-published-date .field__item, .views-field-field-published-date .field__item")
            published_date = "N/A"
            
            for date_element in date_elements:
                date_text = date_element.text.strip()
                if date_text and date_text != "N/A":
                    published_date = date_text
                    break
            
            # If no specific date element found, try to find any date-like text in the row
            if published_date == "N/A":
                row_text = ruling_row.text
                # Look for date patterns like "Jun 09, 2025" or "2025-06-09"
                date_patterns = [
                    r'[A-Za-z]{3}\s+\d{2},\s+\d{4}',  # Jun 09, 2025
                    r'\d{4}-\d{2}-\d{2}',              # 2025-06-09
                    r'\d{2}/\d{2}/\d{4}',              # 09/06/2025
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, row_text)
                    if match:
                        published_date = match.group(0)
                        break
            
            return {
                'url': url,
                'title': title,
                'published_date': published_date
            }
            
        except Exception as e:
            logger.warning(f"Error extracting ruling info from main page: {e}")
            return None

    def scrape_yesterday_rulings(self, target_url):
        """Scrape rulings from yesterday or weekend if today is Monday - with early date filtering"""
        self.target_url = target_url
        self.driver.get(self.target_url)
        time.sleep(self.config.PAGE_LOAD_WAIT)
        try:
            target_dates = self.get_target_dates()
            
            all_rulings = []
            page_count = 0
            found_target_date = False
            
            while True:
                page_count += 1
                logger.info(f"Processing page {page_count}")
                
                # Find all ruling rows on current page
                ruling_rows = self.driver.find_elements(By.CSS_SELECTOR, "div.view-content.row div.views-row")
                
                if not ruling_rows:
                    logger.info("No more ruling rows found")
                    break
                
                logger.info(f"Found {len(ruling_rows)} ruling rows on page {page_count}")
                
                # Extract basic info from each ruling row to filter by date early
                ruling_infos = []
                for ruling_row in ruling_rows:
                    ruling_info = self.extract_ruling_info_from_main_page(ruling_row)
                    if ruling_info:
                        ruling_infos.append(ruling_info)
                
                # Filter by date before visiting detail pages
                for ruling_info in ruling_infos:
                    url = ruling_info['url']
                    title = ruling_info['title']
                    published_date = ruling_info['published_date']
                    
                    logger.info(f"Checking: {title[:60]}... (Published: {published_date})")
                    
                    # Check if this ruling matches target dates
                    if self.is_target_date(published_date, target_dates):
                        logger.info(f"✅ Found target date ruling - visiting detail page: {title[:50]}... ({published_date})")
                        
                        try:
                            # Navigate to ruling page to extract full details
                            self.driver.get(url)
                            time.sleep(self.config.PAGE_LOAD_WAIT)
                            
                            # Extract full data
                            ruling_data = self.extract_ruling_data()
                            ruling_data["URL"] = url
                            
                            all_rulings.append(ruling_data)
                            found_target_date = True
                            
                            # Go back to main page
                            self.driver.get("https://www.taxsutra.com/dt/rulings")
                            time.sleep(self.config.PAGE_LOAD_WAIT)
                            
                        except Exception as e:
                            logger.error(f"Error processing ruling detail page: {e}")
                            # Try to go back to main page
                            try:
                                self.driver.get("https://www.taxsutra.com/dt/rulings")
                                time.sleep(self.config.PAGE_LOAD_WAIT)
                            except:
                                logger.error("Failed to return to main page")
                            continue
                    
                    elif self.is_today_date(published_date):
                        # Skip today's rulings, continue looking
                        logger.info(f"⏭️ Skipping today's ruling: {title[:50]}... ({published_date})")
                        
                    elif found_target_date:
                        # If we already found a target date ruling and now we're seeing older ones,
                        # we can stop as we've passed the target date(s)
                        logger.info(f"⏹️ Reached older ruling ({published_date}), stopping")
                        return all_rulings
                    
                    else:
                        # Check if this is an older ruling that we should skip
                        logger.info(f"⏭️ Skipping ruling with different date: {title[:50]}... ({published_date})")
                
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
            
            if len(all_rulings) == 0:
                if len(target_dates) > 1:  # Weekend dates
                    logger.warning("⚠️ No rulings found for the weekend")
                else:
                    logger.warning("⚠️ No rulings found for yesterday")
            else:
                if len(target_dates) > 1:  # Weekend dates
                    logger.info(f"✅ Scraping completed. Found {len(all_rulings)} rulings from the weekend")
                else:
                    logger.info(f"✅ Scraping completed. Found {len(all_rulings)} rulings from yesterday")
            
            return all_rulings
            
        except Exception as e:
            logger.error(f"❌ Scraping failed with error: {e}")
            return []
            
        finally:
            logger.info("Completed Rulings")
            # self.cleanup()             
class ExpertCornerScraper(TaxSutraBaseScraper):
    """Scraper for Taxsutra Expert Corner"""
    def __init__(self, driver):
        super().__init__(driver)
        self.target_url = "https://www.taxsutra.com/dt/experts-corner"

    def get_article_elements(self):
        """Wait for and return all <li> article elements inside the content wrapper."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time
        try:
            time.sleep(10)  # Wait for articles to load after filter submit
            wrapper = WebDriverWait(self.driver, self.config.WEBDRIVER_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".views-infinite-scroll-content-wrapper.clearfix"))
            )
            li_elements = wrapper.find_elements(By.TAG_NAME, "li")
            return li_elements
        except Exception as e:
            logger.error(f"Could not find article list wrapper: {e}")
            return []

    def extract_article_info(self, li):
        """Extract and return the date and title from a single <li> element."""
        from selenium.webdriver.common.by import By
        try:
            date_div = li.find_element(By.CSS_SELECTOR, "div.articleDate")
            date_text = date_div.text.strip()
            h3 = li.find_element(By.TAG_NAME, "h3")
            title_text = h3.text.strip()
            url = li.find_element(By.TAG_NAME, "a").get_attribute("href")
            return date_text, title_text, url
        except Exception:
            return None, None, None

    def extract_article_tag(self, li):
        """Extract and return the text under class 'articleTag articlePurpleTag' from a single <li> element."""
        from selenium.webdriver.common.by import By
        try:
            tag_div = li.find_element(By.CSS_SELECTOR, ".articleTag.articlePurpleTag")
            return tag_div.text.strip()
        except Exception:
            return ""

    def scrape_yesterday_expert_corner(self, target_url):
        """Scrape all expert articles and return a JSON list of dicts with 'title' and 'date' for yesterday (or weekend if Monday)."""
        self.target_url = target_url
        self.driver.get(self.target_url)
        time.sleep(self.config.PAGE_LOAD_WAIT)
        import json
        try:    
            # Get target dates based on current day
            target_dates = self.get_target_dates()
            if not target_dates:
                logger.info("Today is a weekend, not generating any data.")
                return []
                
            # Normalize target dates for comparison
            normalized_targets = [self.normalize_date_for_compare(d) for d in target_dates]
            
            results = []
            li_elements = self.get_article_elements()
            for li in li_elements:
                date_text, title_text, url = self.extract_article_info(li)
                tag_text = self.extract_article_tag(li)
                normalized_date = self.normalize_date_for_compare(date_text)
                if date_text and title_text and tag_text == "Expert Articles" and normalized_date in normalized_targets:
                    results.append({"title": title_text, "date": date_text, "URL": url})
                    
            logger.info(f"Returned all expert articles for yesterday or weekend (filtered for 'Expert Articles').")
            return results
        finally:
            logger.info("Completed Expert")
            # self.cleanup()
class LitigationTrackerScraper(TaxSutraBaseScraper):
    """Scraper for Taxsutra Litigation Tracker"""
    def __init__(self, driver):
        super().__init__(driver)
        self.target_url = "https://www.taxsutra.com/dt/litigation-tracker"
    
    def scrape_yesterday_litigation_tracker(self, target_url):
        """Scrape litigation tracker articles for yesterday (or weekend if Monday) and return JSON with date, title, summary."""
        self.target_url = target_url
        self.driver.get(self.target_url)
        time.sleep(self.config.PAGE_LOAD_WAIT)

        
        if not self.setup_driver():
            return []
        try:                
            # Wait for articles to load
            time.sleep(10)
            wrapper = self.driver.find_element(By.XPATH, '//*[@class="views-infinite-scroll-content-wrapper clearfix"]')
            article_divs = wrapper.find_elements(By.XPATH, './div')
            logger.info(f"Found {len(article_divs)} litigation tracker articles")
            
            # Get target dates based on current day
            target_dates = self.get_target_dates()
            if not target_dates:
                logger.info("Today is a weekend, not generating any data.")
                return []
                
            # Normalize target dates for comparison
            normalized_targets = [self.normalize_date_for_compare(d) for d in target_dates]
            
            results = []
            for div in article_divs:
                try:
                    date_span = div.find_element(By.TAG_NAME, 'span')
                    date_text = date_span.text.strip()
                    normalized_litigation_date = self.normalize_date_for_compare(date_text)
                    
                    if normalized_litigation_date in normalized_targets:
                        link_elem = div.find_element(By.TAG_NAME, 'h3').find_element(By.TAG_NAME, 'a')
                        url = link_elem.get_attribute("href")
                        
                        # Navigate to the article page
                        self.driver.execute_script("window.open(arguments[0]);", url)
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        time.sleep(3)
                        
                        # Extract title
                        try:
                            title_elem = WebDriverWait(self.driver, self.config.WEBDRIVER_TIMEOUT).until(
                                EC.visibility_of_element_located((By.XPATH, '//*[@class="field field--name-title field--type-string field--label-hidden"]'))
                            )
                            title = title_elem.text.strip()
                        except Exception:
                            title = ""
                            
                        # Extract summary
                        try:
                            summary_elem = WebDriverWait(self.driver, self.config.WEBDRIVER_TIMEOUT).until(
                                EC.visibility_of_element_located((By.XPATH, '//*[@class="clearfix text-formatted field field--name-field-conclusion field--type-text-long field--label-hidden field__item"]'))
                            )
                            summary = summary_elem.text.strip()
                        except Exception:
                            summary = ""
                            
                        results.append({"date": date_text, "title": title, "summary": summary})
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])
                except Exception as e:
                    logger.error(f"Error processing div: {e}")
            
            return results
        finally:
            logger.info("Completed Litigation")
            # self.cleanup()
            