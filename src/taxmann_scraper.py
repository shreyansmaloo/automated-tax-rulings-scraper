"""Taxmann.com scraper module for automated tax rulings

Scrapes GST updates, Company & SEBI Laws, and FEMA & Banking updates from Taxmann.com
"""

import logging
import time
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyperclip

from config.settings import config
from src.utils.base_scraper import TaxSutraBaseScraper

logger = logging.getLogger(__name__)

class TaxmannArchivesScraper(TaxSutraBaseScraper):
    """Scraper for Taxmann Archives updates (https://www.taxmann.com/research/all/archives)"""

    def __init__(self, driver):
        super().__init__(driver)
        self.target_url = "https://www.taxmann.com/research/all/archives"

    def navigate_to_archives(self):
        logger.info("Navigating to Taxmann.com Archives page...")
        logger.info(f"Target URL: {self.target_url}")
        self.driver.get(self.target_url)
        time.sleep(self.config.PAGE_LOAD_WAIT * 2)
        logger.info("✅ Successfully navigated to Archives page")
        return True

    def scrape_yesterday_archives_updates(self, taxmann_gst_data, taxmann_direct_tax_data, taxmann_fema_banking_data):
        try:
            if not self.navigate_to_archives():
                logger.error("Failed to navigate to Archives page, aborting scraping")
                return []

            # Compute yesterday's date in 'DD MMM YYYY' format
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%d %b %Y")
            logger.info(f"Looking for updates with date: {yesterday}")

            # Increase items per page to 100 by selecting from the dropdown
            try:
                # Wait for the items-per-page dropdown to be present
                per_page_dropdown = WebDriverWait(self.driver, self.config.WEBDRIVER_TIMEOUT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "select[aria-label*='items per page'], select[name*='perPage'], select"))
                )
                # Check if dropdown is already set to 100
                current_value = per_page_dropdown.get_attribute("value")
                if current_value != "100":
                    # Try to select 100
                    for option in per_page_dropdown.find_elements(By.TAG_NAME, "option"):
                        if option.text.strip() == "100" or option.get_attribute("value") == "100":
                            option.click()
                            logger.info("Set items per page to 100")
                            break
                    else:
                        logger.warning("Could not find '100' option in items per page dropdown")
                    # Wait for the page to reload after changing the dropdown
                    time.sleep(self.config.PAGE_LOAD_WAIT)
                else:
                    logger.info("Items per page already set to 100")
            except Exception as e:
                logger.warning(f"Could not set items per page to 100: {e}")


            # Find all article containers and filter by date
            article_containers = self.driver.find_elements(By.CSS_SELECTOR, ".media, .article-item, .news-item")
            
            combined_updates = []
            for container in article_containers:
                try:
                    # Find the date element within this article container
                    date_elem = container.find_element(By.CSS_SELECTOR, ".news-date-1, .date, .published-date")
                    date_text = date_elem.text.strip()
                    
                    # Only if the date matches yesterday, get the article link
                    if date_text == yesterday:
                        # Find the main article link (usually the title link)
                        article_link = container.find_element(By.CSS_SELECTOR, "a[href*='/research/'], .title a, .headline a, h3 a, h4 a")
                        href = article_link.get_attribute("href")
                        
                        # GST articles
                        if "/research/gst-new" in href:
                            combined_updates.append({
                                "URL": href,
                                "Category": "GST",
                                "Date": yesterday
                            })

                        # Income Tax / Direct Tax Laws articles
                        elif "/research/direct-tax-laws" in href:
                            combined_updates.append({
                                "URL": href,
                                "Category": "Direct Tax",
                                "Date": yesterday
                            })

                        # FEMA & Banking articles
                        elif "/research/fema-banking-insurance" in href:
                            combined_updates.append({
                                "URL": href,
                                "Category": "FEMA & Banking",
                                "Date": yesterday
                            })

                except Exception as e:
                    logger.debug(f"Skipping container due to error: {e}")
                    continue

            logger.info(f"Found { len(combined_updates)} article links matching date {yesterday}")

            for item in combined_updates[0:1]:
                url = item.get("URL")
                category = item.get("Category")
                date_val = item.get("Date", yesterday)
                try:
                    self.driver.get(url)
                    time.sleep(self.config.PAGE_LOAD_WAIT)

                    # 1. Title (generally h2)
                    try:
                        title_elem = self.driver.find_element(By.CSS_SELECTOR, "h2")
                        title = title_elem.text.strip()
                    except Exception:
                        title = "No Title"

                    # 2. Category (already available as 'category' from the array)
                    # 3. Sub-category: try to extract from the text below the title
                    try:
                        # Look for the element immediately following the h2
                        subcat_elem = None
                        try:
                            subcat_elem = title_elem.find_element(By.XPATH, "following-sibling::*[1]")
                        except Exception:
                            # fallback: look for a .meta, .news-details, or similar
                            try:
                                subcat_elem = self.driver.find_element(By.CSS_SELECTOR, ".content-m-info-div1")
                            except Exception:
                                subcat_elem = None
                        subcat_text = subcat_elem.text.strip() if subcat_elem else ""
                        # Try to extract sub-category from the pipe-separated text 
                        # e.g. "11 Jul 2025 | [2025] 175 taxmann.com 959 (Madras)[16-06-2025] | GST | Case Laws |  237 Views"
                        if subcat_text:
                            parts = [p.strip() for p in subcat_text.split("|") if p.strip()]
                            sub_category = parts[-2]
                            if sub_category.strip().lower() == "opinion":
                                continue
                            sub_category = parts[-2]
                    except Exception:
                        logger.info(f"No sub-category found for {title}")
                        sub_category = "General"

                    # 4. Summary: fetch from class dbs_summary and div id as body, concatenate both
                    if sub_category.strip().lower() == "case laws":
                        summary_parts = []
                        try:
                            # Try to get summary from class dbs_summary
                            try:
                                    # Remove leading "INCOME TAX :", "GST :", "FEMA, BANKING & INSURANCE :", etc. from summary lines
                                    dbs_summary_elem = self.driver.find_element(By.CSS_SELECTOR, "div#dbs_summary")
                                    dbs_summary_text = dbs_summary_elem.text.strip()
                                    if dbs_summary_text:
                                        # Remove leading "CATEGORY :" from each line if present
                                        lines = dbs_summary_text.splitlines()
                                        cleaned_lines = []
                                        for line in lines:
                                            # Remove leading category and colon (case-insensitive, allow spaces)
                                            cleaned_line = line
                                            for prefix in [
                                                "INCOME TAX :","INCOME TAX:", "GST :", "GST:", "FEMA, BANKING & INSURANCE :","FEMA, BANKING & INSURANCE:", "FEMA & BANKING :", "FEMA & BANKING:", "FEMA :", "FEMA:", "BANKING & INSURANCE :", "BANKING & INSURANCE:"
                                            ]:
                                                if cleaned_line.upper().startswith(prefix):
                                                    cleaned_line = cleaned_line[len(prefix):].lstrip()
                                                    break
                                            cleaned_lines.append(cleaned_line)
                                        dbs_summary_text = "\n".join(cleaned_lines)
                                        # Remove trailing '■■■' or similar box characters from the summary text
                                        import re
                                        # Remove any trailing '■' (one or more, possibly with whitespace before/after)
                                        dbs_summary_text = re.sub(r'[\s■]+$', '', dbs_summary_text)
                                        summary_parts.append(dbs_summary_text)
                            except Exception:
                                pass

                            # Try to get summary from div#body
                            try:
                                headnotes = self.driver.find_element(By.CSS_SELECTOR, "div#headnotes")
                                body_text = headnotes.text.strip()
                                if body_text:
                                    summary_parts.append(body_text)
                            except Exception:
                                pass
                        except Exception:
                            pass

                        # Instead of joining with newlines, concatenate as a single paragraph with a space
                        summary = ""
                        if summary_parts:
                            # Remove empty strings and strip each part
                            summary_parts_clean = [part.strip() for part in summary_parts if part.strip()]
                            summary = " ".join(summary_parts_clean)
                    else:
                        # For non-case law sub-categories, try to fetch summary from div inside app-pdf-viewer
                        summary = ""
                        try:
                            # Find the app-pdf-viewer element
                            app_pdf_viewer = self.driver.find_element(By.CSS_SELECTOR, "app-pdf-viewer")
                            # Find the first div inside app-pdf-viewer
                            pdf_div = app_pdf_viewer.find_element(By.CSS_SELECTOR, "div")
                            pdf_text = pdf_div.text.strip()
                            if pdf_text:
                                summary = pdf_text
                        except Exception:
                            summary = ""
                   

                    citation_text = None
                    if sub_category.strip().lower() == "case laws":
                        try:
                            # Only for case laws: look for the citation button and get its value
                            citation_btn = self.driver.find_element(By.CSS_SELECTOR, ".copy-citation-action")
                            # The citation text is usually in a data-clipboard-text attribute or as a value
                            # Click the citation button to copy citation to clipboard, then read from clipboard

                            citation_btn.click()
                            citation_text = pyperclip.paste()
                            logger.info(f"Citation text: {citation_text}")
                        except Exception:
                            citation_text = None

                    # Instead of updating a generic update_date, update the specific GST, FEMA, or Direct Tax data lists
                    if category.strip().upper() == "GST":
                        taxmann_gst_data.append({
                            "Title": title,
                            "Category": category,
                            "Sub-Category": sub_category,
                            "Summary": summary,
                            "Citation": citation_text,
                            "Date": date_val,
                            "Source": "Taxmann.com",
                            "URL": url
                        })
                        
                    elif category.strip().upper() in ["FEMA & BANKING", "FEMA"]:
                        taxmann_fema_banking_data.append({
                            "Title": title,
                            "Category": category,
                            "Sub-Category": sub_category,
                            "Summary": summary,
                            "Citation": citation_text,
                            "Date": date_val,
                            "Source": "Taxmann.com",
                            "URL": url
                        })

                    elif category.strip().upper() in ["DIRECT TAX", "INCOME TAX"]:
                        taxmann_direct_tax_data.append({
                            "Title": title,
                            "Category": category,
                            "Sub-Category": sub_category,
                            "Summary": summary,
                            "Citation": citation_text,
                            "Date": date_val,
                            "Source": "Taxmann.com",
                            "URL": url
                        })

                except Exception as e:
                    logger.warning(f"Failed to process update at {url}: {e}")
                    continue

        finally:
            logger.info(f"✅ Scraping completed. Found {len(combined_updates)} updates for {yesterday}")
            self.cleanup()