"""Taxmann.com scraper module for automated tax rulings

Scrapes GST updates, Direct Tax updates, Company & SEBI Laws, and FEMA & Banking updates from Taxmann.com
"""

import logging
import time
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import glob
from pathlib import Path    
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
        try:
            self.driver.get(self.target_url)
            time.sleep(5)
        except Exception as e:
            logger.error(f"Failed to navigate to Taxmann.com Archives page: {e}")
            return False
        try:
            close_buttons = self.driver.find_elements(By.CLASS_NAME, "close")
            if close_buttons:
                for btn in close_buttons:
                    try:
                        if btn.is_displayed() and btn.is_enabled():
                            btn.click()
                            logger.info("Closed pop-up by clicking 'close' button.")
                            time.sleep(1)
                            break
                    except Exception as e:
                        logger.debug(f"Error clicking close button: {e}")
        except Exception as e:
            logger.debug(f"Error clicking close button: {e}")
        time.sleep(5)
        logger.info("✅ Successfully navigated to Archives page")
        return True

    def scrape_yesterday_archives_updates(self, taxmann_gst_data, taxmann_direct_tax_data, taxmann_company_sebi_data, taxmann_fema_banking_data):
        # Initialize variables that might be referenced in finally block
        combined_updates = []
        yesterday = ""
        
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

                        # Company & SEBI articles
                        elif "/research/company-and-sebi" in href:
                            combined_updates.append({
                                "URL": href,
                                "Category": "Company & SEBI",
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

            for item in combined_updates:
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
                        sub_category = "General"
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
                            court = self.driver.find_element(By.XPATH, "/html/body/app-root/div[1]/div/div/div[3]/div/app-top-story/div/div/div/div[1]/div/div/section/div/div/div[2]/app-preview-document/div[1]/div/div[2]/app-html-viewer/div[3]/div/div/div[2]/div[1]/div[1]").text.strip()
                            party1 = self.driver.find_element(By.XPATH, "/html/body/app-root/div[1]/div/div/div[3]/div/app-top-story/div/div/div/div[1]/div/div/section/div/div/div[2]/app-preview-document/div[1]/div/div[2]/app-html-viewer/div[3]/div/div/div[2]/div[1]/div[2]").text.strip()
                            party2 = self.driver.find_element(By.XPATH, "/html/body/app-root/div[1]/div/div/div[3]/div/app-top-story/div/div/div/div[1]/div/div/section/div/div/div[2]/app-preview-document/div[1]/div/div[2]/app-html-viewer/div[3]/div/div/div[2]/div[1]/div[4]").text.strip()
                            case_reference = self.driver.find_element(By.ID, "db_citation").text.strip()
                            citation_text = f"{party1} vs. {party2}, {court}, {case_reference}"
                            logger.info(f"Citation text: {citation_text}")
                        except Exception:
                            citation_text = None

                        # Extract and download PDF if available
                        try:
                            self.driver.find_element(By.XPATH, "//img[contains(@src, 'download.svg')]").click()
                            download_element = WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, "//a[@class='btn btn-default justify-content-start' and contains(text(), 'PDF')]"))
                            )
                            download_element.click()
                            time.sleep(5)
                            
                            # Rename the downloaded file  
                            downloads_dir = Path("downloads")
                            
                            # Find the most recently downloaded PDF file
                            pdf_files = list(downloads_dir.glob("*.pdf"))
                            if pdf_files:
                                # Sort by modification time to get the most recent
                                latest_pdf = max(pdf_files, key=lambda x: x.stat().st_mtime)
                                
                                # Generate new filename with timestamp
                                timestamp = time.strftime("%Y%m%d_%H%M%S")
                                new_filename = f"taxmann_rulings_{timestamp}.pdf"
                                new_filepath = downloads_dir / new_filename
                                
                                # Rename the file
                                try:
                                    latest_pdf.rename(new_filepath)
                                    logger.info(f"✅ Renamed downloaded PDF to: {new_filename}")
                                    # Save the filename for the Excel link
                                    pdf_filename = new_filename
                                except Exception as rename_error:
                                    logger.warning(f"Failed to rename PDF file: {rename_error}")
                                    pdf_filename = None
                            else:
                                logger.warning("No PDF files found in downloads directory")
                                pdf_filename = None
                                
                        except Exception as e:
                            logger.warning(f"Error while looking for PDF: {e}")
                            pdf_filename = None

                    if category.strip().upper() == "GST":
                        taxmann_gst_data.append({
                            "Title": title,
                            "Category": category,
                            "Sub-Category": sub_category,
                            "Summary": summary,
                            "Citation": citation_text,
                            "Date": date_val,
                            "Source": "Taxmann.com",
                            "URL": url,
                            "PDF Path": pdf_filename
                        })

                    elif category.strip().upper() == "DIRECT TAX":
                        taxmann_direct_tax_data.append({
                            "Title": title,
                            "Category": category,
                            "Sub-Category": sub_category,
                            "Summary": summary,
                            "Citation": citation_text,
                            "Date": date_val,
                            "Source": "Taxmann.com",
                            "URL": url,
                            "PDF Path": pdf_filename
                        })
                    
                    elif category.strip().upper() in ["COMPANY & SEBI"]:
                        taxmann_company_sebi_data.append({
                            "Title": title,
                            "Category": category,
                            "Sub-Category": sub_category,
                            "Summary": summary,
                            "Citation": citation_text,
                            "Date": date_val,
                            "Source": "Taxmann.com",
                            "URL": url,
                            "PDF Path": pdf_filename
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
                            "URL": url,
                            "PDF Path": pdf_filename
                        })

                except Exception as e:
                    logger.warning(f"Failed to process update at {url}: {e}")
                    continue

        finally:
            if yesterday:
                logger.info(f"✅ Scraping completed. Found {len(combined_updates)} updates for {yesterday}")
            else:
                logger.info(f"✅ Scraping completed. Found {len(combined_updates)} updates")
            self.cleanup()