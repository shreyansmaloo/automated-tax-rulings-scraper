"""Taxmann.com scraper module for automated tax rulings

Scrapes GST updates, Company & SEBI Laws, and FEMA & Banking updates from Taxmann.com
"""

import logging
import time
import re
from datetime import date, datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config.settings import config
from src.utils.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class TaxmannBaseScraper(BaseScraper):
    """Base scraper class for Taxmann.com"""
    
    def __init__(self, driver):
        super().__init__(driver)
        self.is_logged_in = False
    
    def _check_if_already_logged_in(self):
        """Check if already logged in to Taxmann.com"""
        try:
            # Look for elements that indicate logged-in state
            indicators = [
                "My Account",
                "Logout",
                "My Profile",
                "My Subscription",
                self.config.TAXMANN_EMAIL  # User's email might be displayed
            ]
            
            page_source = self.driver.page_source
            
            for indicator in indicators:
                if indicator in page_source:
                    logger.info(f"Found login indicator: '{indicator}'")
                    return True
                    
            # Try to find logout link or account menu
            try:
                self.driver.find_element(By.XPATH, "//a[contains(text(), 'Logout')] | //a[contains(@href, 'logout')] | //div[contains(text(), 'My Account')]")
                logger.info("Found logout link or account menu")
                return True
            except:
                pass
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return False
            
    def save_page_source(self, prefix="debug"):
        """Save the current page source for debugging"""
        try:
            # Create a filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Use category if available, otherwise use 'base'
            category = getattr(self, 'category', 'base')
            filename = f"{prefix}_{category.replace(' & ', '_').lower()}_{timestamp}.html"
            
            # Get the page source
            page_source = self.driver.page_source
            
            # Save to file
            with open(filename, "w", encoding="utf-8") as f:
                f.write(page_source)
                
            logger.info(f"Saved page source to {filename}")
            return filename
        except Exception as e:
            logger.warning(f"Failed to save page source: {e}")
            return None
            
    def find_update_elements_with_multiple_selectors(self):
        """Try multiple CSS selectors to find update elements with retry mechanism"""
        logger.info("Attempting to find update elements using multiple approaches")
        
        # List of selectors to try, from most specific to most generic
        selectors = [
            # Specific selectors that might be used on the site
            ".latest-stories-item", ".news-item", ".article-item", ".update-item", ".case-law-item",
            ".story-card", ".news-card", ".article-card", ".update-card", ".case-law-card",
            ".story-box", ".news-box", ".article-box", ".update-box", ".case-law-box",
            ".story-container", ".news-container", ".article-container", ".update-container", ".case-law-container",
            ".story-wrapper", ".news-wrapper", ".article-wrapper", ".update-wrapper", ".case-law-wrapper",
            ".story-list-item", ".news-list-item", ".article-list-item", ".update-list-item", ".case-law-list-item",
            ".story-grid-item", ".news-grid-item", ".article-grid-item", ".update-grid-item", ".case-law-grid-item",
            ".story-tile", ".news-tile", ".article-tile", ".update-tile", ".case-law-tile",
            ".story-panel", ".news-panel", ".article-panel", ".update-panel", ".case-law-panel",
            ".story-block", ".news-block", ".article-block", ".update-block", ".case-law-block",
            
            # More generic attribute selectors
            "div[class*='story']", "div[class*='news']", "div[class*='article']", "div[class*='update']", "div[class*='case']",
            "li[class*='story']", "li[class*='news']", "li[class*='article']", "li[class*='update']", "li[class*='case']",
            
            # Very generic selectors
            ".card", ".item", ".list-item", ".grid-item", ".tile", ".panel", ".block", ".box", ".container", ".wrapper"
        ]
        
        # Add retry mechanism for finding elements
        max_retries = self.config.RETRY_ATTEMPTS
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Try each selector with explicit wait
                for selector in selectors:
                    try:
                        # First check if elements exist with a short wait
                        WebDriverWait(self.driver, 2).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        # If we get here, at least one element exists, now get all of them
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            logger.info(f"Found {len(elements)} elements with selector: {selector}")
                            return elements
                    except Exception:
                        # Selector not found, continue to next one
                        continue
                
                # If no elements found with CSS selectors, try XPath
                xpath_expressions = [
                    # Find elements that might contain updates based on text content
                    "//div[contains(., 'Latest') or contains(., 'Case Laws') or contains(., 'Updates')]//a[contains(@href, '/post/') or contains(@href, '/caselaws/')]/..",
                    "//div[contains(., 'News') or contains(., 'Articles')]//a[contains(@href, '/post/') or contains(@href, '/caselaws/')]/..",
                    
                    # Find elements with links that might be updates
                    "//a[contains(@href, '/post/') or contains(@href, '/caselaws/')]/..",
                    "//a[contains(@href, '/research/') or contains(@href, '/news/')]/..",
                    
                    # Find elements with date-like text
                    "//div[contains(text(), '202') or contains(., '/202') or contains(., '-202')]/..",
                    
                    # Last resort: find any div with substantial text and a link
                    "//div[string-length(normalize-space(text())) > 30]//a/.."
                ]
                
                for xpath in xpath_expressions:
                    try:
                        # First check if elements exist with a short wait
                        WebDriverWait(self.driver, 2).until(
                            EC.presence_of_element_located((By.XPATH, xpath))
                        )
                        # If we get here, at least one element exists, now get all of them
                        elements = self.driver.find_elements(By.XPATH, xpath)
                        if elements:
                            logger.info(f"Found {len(elements)} elements with XPath: {xpath}")
                            return elements
                    except Exception:
                        # XPath not found, continue to next one
                        continue
                
                # Try advanced approaches
                logger.info("Standard selectors failed, trying advanced approaches")
                
                # Try direct link query first (most targeted approach)
                elements = self.find_elements_by_direct_link_query()
                if elements:
                    return elements
                
                # Try DOM structure analysis next (more reliable than text analysis)
                elements = self.find_elements_by_dom_structure()
                if elements:
                    return elements
                    
                # Try text content analysis as last resort
                elements = self.find_elements_by_text_content()
                if elements:
                    return elements
                    
                # If no elements found, refresh the page and retry
                if retry_count < max_retries - 1:
                    logger.warning(f"No elements found, refreshing page and retrying (attempt {retry_count + 1}/{max_retries})")
                    self.driver.refresh()
                    time.sleep(self.config.PAGE_LOAD_WAIT * 2)  # Wait longer after refresh
                
                retry_count += 1
                
            except Exception as e:
                logger.warning(f"Error finding elements (attempt {retry_count + 1}/{max_retries}): {e}")
                retry_count += 1
                time.sleep(1)  # Short pause before retry
        
        # If still no elements found after all retries, return empty list
        logger.warning("No update elements found with any approach after all retries")
        return []
        
    def find_elements_by_text_content(self):
        """Find elements by looking for text content that suggests they are updates"""
        try:
            # Get all elements with text
            all_elements = self.driver.find_elements(By.XPATH, "//div[string-length(normalize-space(text())) > 10]")
            
            # Keywords that might indicate an update
            update_keywords = [
                "update", "news", "article", "story", "case", "law", "ruling", "judgment", 
                "notification", "circular", "amendment", "regulation", "act", "section", 
                "rule", "provision", "order", "gst", "tax", "company", "sebi", "fema", "banking"
            ]
            
            # Date patterns that might indicate an update
            date_patterns = [
                r'\d{1,2}[-./]\d{1,2}[-./]\d{4}',  # DD-MM-YYYY or DD/MM/YYYY
                r'\d{4}[-./]\d{1,2}[-./]\d{1,2}',   # YYYY-MM-DD
                r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4}',  # DD Mon YYYY
                r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}'   # Mon DD, YYYY
            ]
            
            potential_updates = []
            
            for element in all_elements:
                try:
                    text = element.text.lower()
                    
                    # Check if element contains update keywords
                    if any(keyword in text for keyword in update_keywords):
                        potential_updates.append(element)
                        continue
                    
                    # Check if element contains a date pattern
                    if any(re.search(pattern, element.text) for pattern in date_patterns):
                        potential_updates.append(element)
                        continue
                    
                    # Check if element has a link that might be an update
                    links = element.find_elements(By.TAG_NAME, "a")
                    if links and any("/post/" in link.get_attribute("href") or 
                                   "/caselaws/" in link.get_attribute("href") or
                                   "/research/" in link.get_attribute("href") or
                                   "/news/" in link.get_attribute("href")
                                   for link in links):
                        potential_updates.append(element)
                        continue
                        
                except Exception as e:
                    continue
            
            if potential_updates:
                logger.info(f"Found {len(potential_updates)} potential update elements by text content analysis")
                return potential_updates
                
            # If no elements found, try DOM structure analysis
            dom_elements = self.find_elements_by_dom_structure()
            if dom_elements:
                return dom_elements
                
            return []
            
        except Exception as e:
            logger.warning(f"Error finding elements by text content: {e}")
            return []
            
    def find_elements_by_dom_structure(self):
        """Find update elements by analyzing the DOM structure"""
        try:
            # Execute JavaScript to find potential update elements
            js_script = """
            function findPotentialUpdates() {
                // Look for common update patterns in DOM structure
                let potentialUpdates = [];
                
                // Pattern 1: Lists of items with similar structure
                const lists = document.querySelectorAll('ul, ol, div[class*="list"]');
                for (const list of lists) {
                    const children = list.children;
                    if (children.length >= 2) {
                        // Check if children have similar structure (potential update list)
                        const firstChildHTML = children[0].innerHTML.length;
                        const secondChildHTML = children[1].innerHTML.length;
                        
                        // If similar size and contains links, likely an update list
                        if (Math.abs(firstChildHTML - secondChildHTML) / Math.max(firstChildHTML, secondChildHTML) < 0.5 &&
                            children[0].querySelector('a') && children[1].querySelector('a')) {
                            for (const child of children) {
                                potentialUpdates.push(child);
                            }
                        }
                    }
                }
                
                // Pattern 2: Grid or card layouts
                const grids = document.querySelectorAll('div[class*="grid"], div[class*="card"], div[class*="container"]');
                for (const grid of grids) {
                    const children = grid.children;
                    if (children.length >= 2) {
                        // Similar check as above
                        const firstChildHTML = children[0].innerHTML.length;
                        const secondChildHTML = children[1].innerHTML.length;
                        
                        if (Math.abs(firstChildHTML - secondChildHTML) / Math.max(firstChildHTML, secondChildHTML) < 0.5 &&
                            children[0].querySelector('a') && children[1].querySelector('a')) {
                            for (const child of children) {
                                potentialUpdates.push(child);
                            }
                        }
                    }
                }
                
                // Pattern 3: Find sections with headings like "Latest Updates", "Case Laws", etc.
                const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6, div[class*="heading"], div[class*="title"]');
                for (const heading of headings) {
                    const text = heading.textContent.toLowerCase();
                    if (text.includes('latest') || text.includes('update') || text.includes('case') || 
                        text.includes('law') || text.includes('news') || text.includes('article')) {
                        // Get the next sibling or parent's children after this heading
                        let container = heading.nextElementSibling;
                        if (!container) {
                            container = heading.parentElement.nextElementSibling;
                        }
                        
                        if (container) {
                            const items = container.querySelectorAll('div, li');
                            for (const item of items) {
                                if (item.querySelector('a')) {
                                    potentialUpdates.push(item);
                                }
                            }
                        }
                    }
                }
                
                // Return element IDs for retrieval
                return Array.from(new Set(potentialUpdates)).map((el, index) => {
                    // Add a temporary ID if none exists
                    if (!el.id) {
                        el.id = 'temp-update-' + index;
                    }
                    return el.id;
                });
            }
            return findPotentialUpdates();
            """
            
            # Execute the JavaScript and get element IDs
            element_ids = self.driver.execute_script(js_script)
            
            if not element_ids:
                return []
                
            # Retrieve the elements by their IDs
            elements = []
            for element_id in element_ids:
                try:
                    element = self.driver.find_element(By.ID, element_id)
                    elements.append(element)
                except:
                    continue
                    
            logger.info(f"Found {len(elements)} potential update elements by DOM structure analysis")
            return elements
            
        except Exception as e:
            logger.warning(f"Error finding elements by DOM structure: {e}")
            return []
            
    def find_elements_by_direct_link_query(self):
        """Find update elements by directly querying for links with specific patterns"""
        try:
            # Try to find all links that might be updates
            link_patterns = [
                "//a[contains(@href, '/post/')]",
                "//a[contains(@href, '/caselaws/')]",
                "//a[contains(@href, '/research/')]",
                "//a[contains(@href, '/news/')]",
                "//a[contains(@href, '/updates/')]",
                "//a[contains(@href, '/articles/')]",
                "//a[contains(@href, '/stories/')]",
                "//a[contains(@href, '/case-laws/')]"
            ]
            
            all_links = []
            for pattern in link_patterns:
                links = self.driver.find_elements(By.XPATH, pattern)
                if links:
                    logger.info(f"Found {len(links)} links with pattern: {pattern}")
                    all_links.extend(links)
            
            if not all_links:
                return []
                
            # Get parent elements of links (these are likely the update elements)
            parent_elements = []
            for link in all_links:
                try:
                    # Get the parent element that likely contains the whole update
                    parent = link
                    for _ in range(3):  # Go up to 3 levels up to find a suitable container
                        try:
                            parent = parent.find_element(By.XPATH, "./..")  # Get parent
                            # Check if this parent has enough content to be an update
                            if len(parent.text.strip()) > 30:
                                parent_elements.append(parent)
                                break
                        except:
                            break
                except:
                    continue
            
            # Remove duplicates (same element might be found multiple times)
            unique_parents = []
            parent_ids = set()
            for parent in parent_elements:
                try:
                    parent_id = parent.id
                    if not parent_id:  # If no ID, use the element's text as identifier
                        parent_id = parent.text[:50]  # Use first 50 chars as identifier
                    
                    if parent_id not in parent_ids:
                        parent_ids.add(parent_id)
                        unique_parents.append(parent)
                except:
                    continue
            
            logger.info(f"Found {len(unique_parents)} potential update elements by direct link query")
            return unique_parents
            
        except Exception as e:
            logger.warning(f"Error finding elements by direct link query: {e}")
            return []

class TaxmannGSTScraper(TaxmannBaseScraper):
    """Scraper for GST updates from Taxmann.com"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.taxmann.com/"
        self.category = "GST"
        self.target_url = "https://www.taxmann.com/research/gst/caselaws"
    
    def navigate_to_gst_updates(self):
        """Navigate to GST updates section with retry mechanism"""
        from selenium.common.exceptions import StaleElementReferenceException
        
        max_retries = self.config.RETRY_ATTEMPTS
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info("Navigating to Taxmann.com GST updates section...")
                
                # First login to Taxmann
                if not self.login_to_taxmann():
                    logger.error("Failed to login to Taxmann.com")
                    return False
                
                # Navigate directly to GST updates page
                self.driver.get(self.target_url)
                time.sleep(self.config.PAGE_LOAD_WAIT * 2)  # Wait longer for direct URL
                
                # Wait for updates to load and verify page has content
                try:
                    # Check if page has loaded with content
                    WebDriverWait(self.driver, self.config.WEBDRIVER_TIMEOUT).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".article, .post, .update, .case-law, [class*='article'], [class*='post'], [class*='update'], [class*='case']"))
                    )
                except Exception as e:
                    logger.warning(f"Page may not have loaded properly, but continuing: {e}")
                
                logger.info("✅ Successfully navigated to GST updates section")
                return True
                
            except StaleElementReferenceException:
                logger.warning(f"Stale element reference when navigating to GST updates, retrying ({retry_count+1}/{max_retries})")
                retry_count += 1
                time.sleep(1)  # Pause before retry
            except Exception as e:
                logger.warning(f"Error navigating to GST updates: {e}, retrying ({retry_count+1}/{max_retries})")
                retry_count += 1
                time.sleep(1)  # Pause before retry
        
        logger.error(f"❌ Failed to navigate to GST updates after {max_retries} retries")
        return False
    
    def safe_get_text(self, element, default=""):
        """Safely get text from an element, handling stale element references"""
        max_retries = self.config.RETRY_ATTEMPTS
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                return element.text.strip()
            except Exception as e:
                logger.warning(f"Error getting text from element: {e}, retrying ({retry_count+1}/{max_retries})")
                retry_count += 1
                time.sleep(0.5)  # Short pause before retry
        
        logger.warning(f"Failed to get text after {max_retries} retries")
        return default
    
    def extract_update_info(self, update_element):
        """Extract basic information from an update element with retry mechanism for stale elements"""
        from selenium.common.exceptions import StaleElementReferenceException
        
        max_retries = self.config.RETRY_ATTEMPTS
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Try multiple approaches to extract title and URL
                try:
                    # First approach - look for heading elements with explicit wait
                    try:
                        title_element = WebDriverWait(self.driver, 2).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "h3, h2, h4, .title, .heading"))
                        )
                        title = self.safe_get_text(title_element, "Unknown Title")
                        
                        # Try to get URL from the title element or its child
                        try:
                            url = WebDriverWait(title_element, 1).until(
                                EC.presence_of_element_located((By.TAG_NAME, "a"))
                            ).get_attribute("href")
                        except:
                            # If no direct link in title, look for any link in the update element
                            url = WebDriverWait(update_element, 1).until(
                                EC.presence_of_element_located((By.TAG_NAME, "a"))
                            ).get_attribute("href")
                    except:
                        # Fallback to direct find_element if WebDriverWait fails
                        title_element = update_element.find_element(By.CSS_SELECTOR, "h3, h2, h4, .title, .heading")
                        title = self.safe_get_text(title_element, "Unknown Title")
                        
                        # Try to get URL from the title element or its child
                        try:
                            url = title_element.find_element(By.TAG_NAME, "a").get_attribute("href")
                        except:
                            # If no direct link in title, look for any link in the update element
                            url = update_element.find_element(By.TAG_NAME, "a").get_attribute("href")
                except Exception as e:
                    # Second approach - the element itself might be a link or contain a primary link
                    try:
                        # Try to find the main link with explicit wait
                        try:
                            link_element = WebDriverWait(update_element, 1).until(
                                EC.presence_of_element_located((By.TAG_NAME, "a"))
                            )
                            url = link_element.get_attribute("href")
                            title = self.safe_get_text(link_element, "Unknown Title")
                        except:
                            # Fallback to direct find_element
                            link_element = update_element.find_element(By.TAG_NAME, "a")
                            url = link_element.get_attribute("href")
                            title = self.safe_get_text(link_element, "Unknown Title")
                    except Exception as e2:
                        # Last resort - use the element's text as title and try to find any URL
                        try:
                            element_text = self.safe_get_text(update_element)
                            title = element_text.split('\n')[0] if element_text else "Unknown Title"  # First line as title
                        except:
                            title = "Unknown Title"  # Fallback if text extraction fails
                            
                        url = "#"  # Placeholder if no URL found
                        
                        # Try to find any link
                        try:
                            links = update_element.find_elements(By.TAG_NAME, "a")
                            if links:
                                url = links[0].get_attribute("href")
                        except:
                            pass  # Keep the placeholder URL
                
                # Extract date using multiple approaches
                try:
                    # Try common date selectors with explicit wait
                    try:
                        date_element = WebDriverWait(update_element, 1).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".date, .time, .published-date, [class*='date'], [class*='time']"))
                        )
                        date_text = self.safe_get_text(date_element)
                    except:
                        # Fallback to direct find_element
                        date_element = update_element.find_element(By.CSS_SELECTOR, ".date, .time, .published-date, [class*='date'], [class*='time']")
                        date_text = self.safe_get_text(date_element)
                except:
                    # Try to find date in the text content
                    try:
                        element_text = self.safe_get_text(update_element)
                        # Look for date patterns in the text
                        date_matches = re.findall(r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}', element_text)
                        if date_matches:
                            date_text = date_matches[0]
                        else:
                            # Default to today's date if no date found
                            date_text = date.today().strftime("%d %b %Y")
                    except:
                        # Default to today's date if all attempts fail
                        date_text = date.today().strftime("%d %b %Y")
                
                article_date = self.extract_date(date_text)
                
                # Extract category/topic if available
                try:
                    # Try with explicit wait
                    try:
                        topic_element = WebDriverWait(update_element, 1).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".category, .topic, .tag, [class*='category'], [class*='topic'], [class*='tag']"))
                        )
                        topic = self.safe_get_text(topic_element)
                    except:
                        # Fallback to direct find_element
                        topic_element = update_element.find_element(By.CSS_SELECTOR, ".category, .topic, .tag, [class*='category'], [class*='topic'], [class*='tag']")
                        topic = self.safe_get_text(topic_element)
                except:
                    # Try to determine topic from URL or title
                    if "gst" in url.lower() or "gst" in title.lower():
                        topic = "GST"
                    elif "company" in url.lower() or "sebi" in url.lower() or "company" in title.lower() or "sebi" in title.lower():
                        topic = "Company & SEBI"
                    elif "fema" in url.lower() or "banking" in url.lower() or "fema" in title.lower() or "banking" in title.lower():
                        topic = "FEMA & Banking"
                    else:
                        topic = "General"
                
                return {
                    "title": title,
                    "url": url,
                    "date": article_date,
                    "topic": topic
                }
                
            except StaleElementReferenceException:
                logger.warning(f"Stale element reference when extracting update info, retrying ({retry_count+1}/{max_retries})")
                retry_count += 1
                time.sleep(1)  # Pause before retry
            except Exception as e:
                logger.warning(f"Error extracting update info: {e}, retrying ({retry_count+1}/{max_retries})")
                retry_count += 1
                time.sleep(1)  # Pause before retry
        
        # If all retries fail, try to extract minimal information
        try:
            # Last resort - try to get any text and URL
            try:
                element_text = update_element.text.strip()
                title = element_text.split('\n')[0] if element_text else "Unknown Title"
            except:
                title = "Unknown Title"
                
            try:
                links = update_element.find_elements(By.TAG_NAME, "a")
                url = links[0].get_attribute("href") if links else "#"
            except:
                url = "#"
                
            return {
                "title": title,
                "url": url,
                "date": date.today(),  # Default to today's date
                "topic": "General"  # Default topic
            }
        except Exception as e:
            logger.warning(f"Failed to extract update info after all retries: {e}")
            return None
    
    def extract_article_content(self, url):
        """Extract content from an article page with retry mechanism for stale elements"""
        from selenium.common.exceptions import StaleElementReferenceException
        
        max_retries = self.config.RETRY_ATTEMPTS
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"Navigating to article: {url}")
                self.driver.get(url)
                time.sleep(self.config.PAGE_LOAD_WAIT)
                
                # Try multiple selectors to find article content
                selectors = [
                    ".article-content p, .content p, .body p",
                    "#content p, .post-content p, .entry-content p",
                    ".case-law-content p, .update-content p",
                    "[class*='article'] p, [class*='content'] p, [class*='body'] p",
                    "[id*='article'] p, [id*='content'] p, [id*='body'] p"
                ]
                
                paragraphs = []
                for selector in selectors:
                    try:
                        # Use explicit wait for better reliability
                        WebDriverWait(self.driver, 2).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        paragraphs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if paragraphs:
                            logger.info(f"Found content using selector: {selector}")
                            break
                    except:
                        continue
                
                # If still no paragraphs found, try a more generic approach
                if not paragraphs:
                    # Try to find any div that might contain the article content
                    main_content_divs = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'content') or contains(@class, 'article') or contains(@id, 'content')]")
                    if main_content_divs:
                        # Get paragraphs from the first content div
                        paragraphs = main_content_divs[0].find_elements(By.TAG_NAME, "p")
                
                # If still no paragraphs, try to get any text content
                if not paragraphs:
                    logger.warning(f"No paragraphs found using standard selectors, trying fallback methods")
                    # Try to find any text blocks
                    text_blocks = self.driver.find_elements(By.XPATH, "//div[string-length(normalize-space(text())) > 100]")
                    if text_blocks:
                        # Create synthetic paragraphs from text blocks
                        paragraphs = [text_blocks[0]]  # First paragraph
                        if len(text_blocks) > 2:
                            paragraphs.append(text_blocks[2])  # Third paragraph if available
                        elif len(text_blocks) > 1:
                            paragraphs.append(text_blocks[1])  # Second paragraph if third not available
                
                # Process the paragraphs we found
                if len(paragraphs) >= 3:
                    # Extract 1st and 3rd paragraphs as required
                    first_paragraph = self.safe_get_text(paragraphs[0])
                    third_paragraph = self.safe_get_text(paragraphs[2])
                    content = f"{first_paragraph}\n\n{third_paragraph}"
                elif len(paragraphs) >= 1:
                    # If fewer than 3 paragraphs, just use what's available
                    content = self.safe_get_text(paragraphs[0])
                    if len(paragraphs) >= 2:
                        content += "\n\n" + self.safe_get_text(paragraphs[1])
                else:
                    # Last resort fallback - get any text from the page
                    try:
                        # Try to get the main content area with explicit wait
                        try:
                            content_area = WebDriverWait(self.driver, 2).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, ".article-content, .content, .body, #content, [class*='content']"))
                            )
                            content = self.safe_get_text(content_area)
                        except:
                            # Fallback to direct find_element
                            content_area = self.driver.find_element(By.CSS_SELECTOR, ".article-content, .content, .body, #content, [class*='content']")
                            content = self.safe_get_text(content_area)
                    except:
                        # If all else fails, just get the page body text
                        body_element = self.driver.find_element(By.TAG_NAME, "body")
                        content = self.safe_get_text(body_element)
                        # Try to clean up the content by removing navigation, headers, etc.
                        content_lines = content.split('\n')
                        # Keep only lines with substantial text (more than 30 characters)
                        content_lines = [line for line in content_lines if len(line.strip()) > 30]
                        # Take the first and third substantial lines if available
                        if len(content_lines) >= 3:
                            content = f"{content_lines[0]}\n\n{content_lines[2]}"
                        elif len(content_lines) > 0:
                            content = content_lines[0]
                            if len(content_lines) > 1:
                                content += "\n\n" + content_lines[1]
                
                # Add source attribution
                content += "\n\nSource: Taxmann.com"
                
                return content
                
            except StaleElementReferenceException:
                logger.warning(f"Stale element reference when extracting article content, retrying ({retry_count+1}/{max_retries})")
                retry_count += 1
                time.sleep(1)  # Pause before retry
            except Exception as e:
                logger.warning(f"Error extracting article content: {e}, retrying ({retry_count+1}/{max_retries})")
                retry_count += 1
                time.sleep(1)  # Pause before retry
        
        # If all retries fail, return a fallback message
        logger.error(f"Failed to extract article content after {max_retries} retries")
        return f"Content extraction failed. Please visit {url} for details."
    
    def scrape_yesterday_gst_updates(self):
        """Scrape GST updates from yesterday or weekend if today is Monday"""
        if not self.setup_driver():
            return []
        
        try:
            # Navigate to GST updates section
            if not self.navigate_to_gst_updates():
                logger.error("Failed to navigate to GST updates, aborting scraping")
                return []
            
            # Get target dates (yesterday or weekend dates if Monday)
            target_dates = self.get_target_dates()
            
            all_updates = []
            
            # Log the current URL for debugging
            current_url = self.driver.current_url
            logger.info(f"Current page URL: {current_url}")
            
            # Log page title for debugging
            page_title = self.driver.title
            logger.info(f"Page title: {page_title}")
            
            # Take screenshot for debugging
            try:
                screenshot_path = f"taxmann_debug_{self.category.replace(' & ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Saved screenshot to {screenshot_path}")
            except Exception as e:
                logger.warning(f"Could not save screenshot: {e}")
                
            # Save page source for debugging
            self.save_page_source()
            
            # Find all update elements on the page using multiple selectors
            update_elements = self.find_update_elements_with_multiple_selectors()
            
            if not update_elements:
                logger.warning("No update elements found on the page")
                return []
            
            logger.info(f"Found {len(update_elements)} update elements")
            
            # Process each update
            for update_element in update_elements:
                update_info = self.extract_update_info(update_element)
                
                if not update_info:
                    continue
                
                # Skip updates categorized as "Opinion"
                if update_info["topic"].lower() == "opinion":
                    logger.info(f"Skipping 'Opinion' update: {update_info['title']}")
                    continue
                
                # Check if this update matches target dates
                if update_info["date"] and self.is_date_in_range(update_info["date"], target_dates):
                    logger.info(f"✅ Found target date update: {update_info['title']}")
                    
                    # Extract full content
                    content = self.extract_article_content(update_info["url"])
                    
                    # Create final data structure
                    update_data = {
                        "Title": update_info["title"],
                        "Content": content,
                        "Category": self.category,
                        "Sub-Category": update_info["topic"],
                        "Date": update_info["date"].strftime("%Y-%m-%d") if update_info["date"] else "N/A",
                        "Source": "Taxmann.com",
                        "URL": update_info["url"]
                    }
                    
                    all_updates.append(update_data)
            
            if len(all_updates) == 0:
                logger.warning(f"⚠️ No GST updates found for the target dates")
            else:
                logger.info(f"✅ Scraping completed. Found {len(all_updates)} GST updates")
            
            return all_updates
            
        except Exception as e:
            logger.error(f"❌ GST scraping failed with error: {e}")
            return []
            
        finally:
            self.cleanup()

class TaxmannCompanySEBIScraper(TaxmannGSTScraper):
    """Scraper for Company & SEBI Laws updates from Taxmann.com"""
    
    def __init__(self):
        super().__init__()
        self.category = "Company & SEBI"
        self.target_url = "http://taxmann.com/research/company-and-sebi"
    
    def navigate_to_company_sebi_updates(self):
        """Navigate to Company & SEBI section"""
        logger.info("Navigating to Taxmann.com Company & SEBI section...")
        
        # Set target URL for Company & SEBI updates
        self.target_url = "https://www.taxmann.com/research/company-sebi"
        
        # Use the inherited login_to_taxmann method which handles navigation to target_url
        if not self.login_to_taxmann():
            logger.error("Failed to login to Taxmann.com and navigate to Company & SEBI section")
            return False
        
        # Wait for updates to load and verify page has content
        try:
            # Check if page has loaded with content
            WebDriverWait(self.driver, self.config.WEBDRIVER_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".article, .post, .update, .case-law, [class*='article'], [class*='post'], [class*='update'], [class*='case']"))
            )
        except Exception as e:
            logger.warning(f"Page may not have loaded properly, but continuing: {e}")
        
        logger.info("✅ Successfully navigated to Company & SEBI section")
        return True
            
    def scrape_yesterday_company_sebi_updates(self):
        """Scrape Company & SEBI updates from yesterday or weekend if today is Monday"""
        if not self.setup_driver():
            return []
            
        try:
            # Navigate to Company & SEBI section
            if not self.navigate_to_company_sebi_updates():
                logger.error("Failed to navigate to Company & SEBI updates, aborting scraping")
                return []
            
            # Get target dates (yesterday or weekend dates if Monday)
            target_dates = self.get_target_dates()
            
            all_updates = []
            
            # Log the current URL for debugging
            current_url = self.driver.current_url
            logger.info(f"Current page URL: {current_url}")
            
            # Log page title for debugging
            page_title = self.driver.title
            logger.info(f"Page title: {page_title}")
            
            # Take screenshot for debugging
            try:
                screenshot_path = f"taxmann_debug_{self.category.replace(' & ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Saved screenshot to {screenshot_path}")
            except Exception as e:
                logger.warning(f"Could not save screenshot: {e}")
                
            # Save page source for debugging
            self.save_page_source()
            
            # Find all update elements on the page using multiple selectors
            update_elements = self.find_update_elements_with_multiple_selectors()
            
            if not update_elements:
                logger.warning("No update elements found on the page")
                return []
            
            logger.info(f"Found {len(update_elements)} update elements")
            
            # Process each update
            for update_element in update_elements:
                update_info = self.extract_update_info(update_element)
                
                if not update_info:
                    continue
                
                # Skip updates categorized as "Opinion"
                if update_info["topic"].lower() == "opinion":
                    logger.info(f"Skipping 'Opinion' update: {update_info['title']}")
                    continue
                
                # Check if this update matches target dates
                if update_info["date"] and self.is_date_in_range(update_info["date"], target_dates):
                    logger.info(f"✅ Found target date update: {update_info['title']}")
                    
                    # Extract full content
                    content = self.extract_article_content(update_info["url"])
                    
                    # Create final data structure
                    update_data = {
                        "Title": update_info["title"],
                        "Content": content,
                        "Category": self.category,
                        "Sub-Category": update_info["topic"],
                        "Date": update_info["date"].strftime("%Y-%m-%d") if update_info["date"] else "N/A",
                        "Source": "Taxmann.com",
                        "URL": update_info["url"]
                    }
                    
                    all_updates.append(update_data)
            
            if len(all_updates) == 0:
                logger.warning(f"⚠️ No Company & SEBI updates found for the target dates")
            else:
                logger.info(f"✅ Scraping completed. Found {len(all_updates)} Company & SEBI updates")
            
            return all_updates
            
        except Exception as e:
            logger.error(f"❌ Company & SEBI scraping failed with error: {e}")
            return []
            
        finally:
            # Use the inherited cleanup method
            self.cleanup()

class TaxmannFEMABankingScraper(TaxmannGSTScraper):
    """Scraper for FEMA & Banking updates from Taxmann.com"""
    
    def __init__(self):
        super().__init__()
        self.category = "FEMA & Banking"
    
    def navigate_to_fema_banking_updates(self):
        """Navigate to FEMA & Banking section"""
        logger.info("Navigating to Taxmann.com FEMA & Banking section...")
        
        # Set target URL for FEMA & Banking updates
        self.target_url = "https://www.taxmann.com/research/fema-banking-insurance"
        
        # Use the inherited login_to_taxmann method which handles navigation to target_url
        if not self.login_to_taxmann():
            logger.error("Failed to login to Taxmann.com and navigate to FEMA & Banking section")
            return False
        
        # Wait for updates to load and verify page has content
        try:
            # Check if page has loaded with content
            WebDriverWait(self.driver, self.config.WEBDRIVER_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".article, .post, .update, .case-law, [class*='article'], [class*='post'], [class*='update'], [class*='case']"))
            )
        except Exception as e:
            logger.warning(f"Page may not have loaded properly, but continuing: {e}")
        
        logger.info("✅ Successfully navigated to FEMA & Banking section")
        return True
            
    def scrape_yesterday_fema_banking_updates(self):
        """Scrape FEMA & Banking updates from yesterday or weekend if today is Monday"""
        if not self.setup_driver():
            return []
            
        try:
            # Navigate to FEMA & Banking section
            if not self.navigate_to_fema_banking_updates():
                logger.error("Failed to navigate to FEMA & Banking updates, aborting scraping")
                return []
            
            # Get target dates (yesterday or weekend dates if Monday)
            target_dates = self.get_target_dates()
            
            all_updates = []
            
            # Log the current URL for debugging
            current_url = self.driver.current_url
            logger.info(f"Current page URL: {current_url}")
            
            # Log page title for debugging
            page_title = self.driver.title
            logger.info(f"Page title: {page_title}")
            
            # Take screenshot for debugging
            try:
                screenshot_path = f"taxmann_debug_{self.category.replace(' & ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Saved screenshot to {screenshot_path}")
            except Exception as e:
                logger.warning(f"Could not save screenshot: {e}")
                
            # Save page source for debugging
            self.save_page_source()
            
            # Find all update elements on the page using multiple selectors
            update_elements = self.find_update_elements_with_multiple_selectors()
            
            if not update_elements:
                logger.warning("No update elements found on the page")
                return []
            
            logger.info(f"Found {len(update_elements)} update elements")
            
            # Process each update
            for update_element in update_elements:
                update_info = self.extract_update_info(update_element)
                
                if not update_info:
                    continue
                
                # Skip updates categorized as "Opinion"
                if update_info["topic"].lower() == "opinion":
                    logger.info(f"Skipping 'Opinion' update: {update_info['title']}")
                    continue
                
                # Check if this update matches target dates
                if update_info["date"] and self.is_date_in_range(update_info["date"], target_dates):
                    logger.info(f"✅ Found target date update: {update_info['title']}")
                    
                    # Extract full content
                    content = self.extract_article_content(update_info["url"])
                    
                    # Create final data structure
                    update_data = {
                        "Title": update_info["title"],
                        "Content": content,
                        "Category": self.category,
                        "Sub-Category": update_info["topic"],
                        "Date": update_info["date"].strftime("%Y-%m-%d") if update_info["date"] else "N/A",
                        "Source": "Taxmann.com",
                        "URL": update_info["url"]
                    }
                    
                    all_updates.append(update_data)
            
            if len(all_updates) == 0:
                logger.warning(f"⚠️ No FEMA & Banking updates found for the target dates")
            else:
                logger.info(f"✅ Scraping completed. Found {len(all_updates)} FEMA & Banking updates")
            
            return all_updates
            
        except Exception as e:
            logger.error(f"❌ FEMA & Banking scraping failed with error: {e}")
            return []
            
        finally:
            # Use the inherited cleanup method
            self.cleanup()

class TaxmannArchivesScraper(TaxmannBaseScraper):
    """Scraper for Taxmann Archives updates (https://www.taxmann.com/research/all/archives)"""

    def __init__(self, driver):
        super().__init__(driver)
        self.base_url = "https://www.taxmann.com/"
        self.category = "Archives"
        self.target_url = "https://www.taxmann.com/research/all/archives"

    def navigate_to_archives(self):
        logger.info("Navigating to Taxmann.com Archives page...")
        logger.info(f"Target URL: {self.target_url}")
        self.driver.get(self.target_url)
        time.sleep(self.config.PAGE_LOAD_WAIT * 2)
        logger.info("✅ Successfully navigated to Archives page")
        return True

    def scrape_yesterday_archives_updates(self):
        if not self.setup_driver():
            return []
        try:
            if not self.navigate_to_archives():
                logger.error("Failed to navigate to Archives page, aborting scraping")
                return []

            # Compute yesterday's date in 'DD MMM YYYY' format
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%d %b %Y")
            logger.info(f"Looking for updates with date: {yesterday}")

            # Wait for the archives list to load
            WebDriverWait(self.driver, self.config.WEBDRIVER_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".archives-list, .archives, .archive-list, .list, .container"))
            )

            # Find all date headers and their corresponding update lists
            date_headers = self.driver.find_elements(By.XPATH, f"//h3[contains(text(), '{yesterday}')]")
            if not date_headers:
                logger.warning(f"No updates found for {yesterday}")
                return []

            all_updates = []
            for header in date_headers:
                # The updates are usually in the next sibling (ul or div)
                try:
                    updates_container = header.find_element(By.XPATH, "following-sibling::*[1]")
                    update_links = updates_container.find_elements(By.TAG_NAME, "a")
                except Exception as e:
                    logger.warning(f"Could not find updates container for date header: {e}")
                    continue
                for link in update_links:
                    url = link.get_attribute("href")
                    title = link.text.strip() or "No Title"
                    if not url or not url.startswith("http"):
                        continue
                    logger.info(f"Processing update: {title} | {url}")
                    # Extract content from the update page
                    content = self.extract_1st_and_3rd_paragraph(url)
                    if not content:
                        logger.info(f"Skipping update (less than 3 paragraphs): {url}")
                        continue
                    update_data = {
                        "Title": title,
                        "Content": content,
                        "Category": self.category,
                        "Sub-Category": "General",
                        "Date": yesterday,
                        "Source": "Taxmann.com",
                        "URL": url
                    }
                    all_updates.append(update_data)
            logger.info(f"✅ Scraping completed. Found {len(all_updates)} updates for {yesterday}")
            return all_updates
        except Exception as e:
            logger.error(f"❌ Archives scraping failed with error: {e}")
            return []
        finally:
            self.cleanup()

    def extract_1st_and_3rd_paragraph(self, url):
        try:
            self.driver.get(url)
            time.sleep(self.config.PAGE_LOAD_WAIT)
            selectors = [
                ".article-content p, .content p, .body p",
                "#content p, .post-content p, .entry-content p",
                ".case-law-content p, .update-content p",
                "[class*='article'] p, [class*='content'] p, [class*='body'] p",
                "[id*='article'] p, [id*='content'] p, [id*='body'] p"
            ]
            paragraphs = []
            for selector in selectors:
                try:
                    WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    paragraphs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if paragraphs:
                        break
                except:
                    continue
            if len(paragraphs) < 3:
                return None
            first_paragraph = self.safe_get_text(paragraphs[0])
            third_paragraph = self.safe_get_text(paragraphs[2])
            return f"{first_paragraph}\n\n{third_paragraph}"
        except Exception as e:
            logger.warning(f"Failed to extract paragraphs from {url}: {e}")
            return None