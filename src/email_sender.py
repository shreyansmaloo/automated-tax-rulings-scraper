#!/usr/bin/env python3
"""
Email Sender Module for Automated Tax Rulings Scraper
Sends daily updates via email with M2K branding and rulings.json data
"""

import smtplib
import ssl
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Any
import logging
from pathlib import Path

from config.settings import config

logger = logging.getLogger(__name__)

class EmailSender:
    """Email sender class for daily tax rulings updates with M2K branding"""
    
    def __init__(self):
        """Initialize email sender with configuration"""
        self.smtp_server = config.EMAIL_SMTP_SERVER
        self.smtp_port = config.EMAIL_SMTP_PORT
        self.sender_email = config.EMAIL_SENDER
        self.sender_password = config.EMAIL_PASSWORD
        self.recipient_emails = config.get_email_recipients()
        
        # M2K Brand Colors
        self.m2k_primary = "#ea580c"  # Orange
        self.m2k_dark = "black"     # Dark Blue
        self.m2k_light = "#f97316"    # Light Orange
        self.m2k_gray = "#64748b"     # Gray
        
    def load_rulings_data(self) -> Dict[str, Any]:
        """Load data from rulings.json file"""
        try:
            rulings_file = Path("downloads/rulings.json")
            if rulings_file.exists():
                with open(rulings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning("rulings.json not found, using empty data")
                return {"taxsutra": {}, "taxmann": {}}
        except Exception as e:
            logger.error(f"Error loading rulings.json: {e}")
            return {"taxsutra": {}, "taxmann": {}}
        
    def categorize_content(self, item: Dict[str, Any]) -> str:
        """Categorize content based on URL and category/sub-category"""
        url = item.get("URL", "").lower()
        
        # Check if it's Taxsutra
        if "taxsutra.com" in url:
            return "taxsutra"
        # Check if it's Taxmann
        elif "taxmann.com" in url:
            return "taxmann"
        
        # Fallback based on category/sub-category
        category = item.get("Category", "").lower()
        sub_category = item.get("Sub-Category", "").lower()
        
        if "article" in sub_category or "expert" in sub_category or "litigation" in sub_category:
            return "articles"
        elif "gst" in category:
            return "taxmann"
        elif "direct tax" in category:
            return "taxmann"
        else:
            return "taxsutra"  # Default to taxsutra
            
    def get_summary(self, ruling: Dict[str, Any]) -> str:
        """Get the best summary from ruling data, prioritizing conclusion"""
        conclusion = ruling.get("Conclusion", "")
        decision_summary = ruling.get("Decision Summary", "")
        
        # Prioritize conclusion over decision summary
        if conclusion and conclusion != "N/A":
            return conclusion
        elif decision_summary and decision_summary != "N/A":
            return decision_summary
        else:
            return ""
    
    def ensure_full_content(self, html_content: str) -> str:
        """Ensure email content is not truncated by email clients"""
        # Add meta tags to prevent truncation
        meta_tags = """
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="format-detection" content="telephone=no">
        <meta name="format-detection" content="date=no">
        <meta name="format-detection" content="address=no">
        <meta name="format-detection" content="email=no">
        """
        
        # Replace the existing head section
        html_content = html_content.replace('<head>', f'<head>{meta_tags}')
        
        return html_content

    def extract_court_abbreviation(self, judicial_level_location):
        """Extract court abbreviation (e.g., HC MAD) from judicial level and location"""
        # Extract court type abbreviation
        court_abbr = ""
        if "High Court" in judicial_level_location:
            court_abbr = "HC"
        elif "Supreme Court" in judicial_level_location:
            court_abbr = "SC"
        elif "ITAT" in judicial_level_location:
            court_abbr = "ITAT"
        elif "Tribunal" in judicial_level_location:
            court_abbr = "Tribunal"
        else:
            court_abbr = "Court"
        return court_abbr


    def create_html_content(self, all_data: Dict[str, Any] = None) -> str:
        """
        Create HTML content for the email with M2K branding
        Uses data from rulings.json if all_data is not provided
        """
        
        # Load data from rulings.json if not provided
        if all_data is None:
            all_data = self.load_rulings_data()
        
        # Extract and categorize data
        articles = []
        taxsutra_updates = []
        taxmann_updates = []
        
        # Process Taxsutra data
        taxsutra_data = all_data.get("taxsutra", {})
        
        # Add rulings and litigation tracker as articles
        for ruling in taxsutra_data.get("rulings", []):
            taxsutra_updates.append(ruling)
        for ruling in taxsutra_data.get("litigation_tracker", []):
            articles.append(ruling)
            
        # Add expert corner as articles
        for article in taxsutra_data.get("expert_corner", []):
            articles.append(article)
        
        # Process Taxmann data
        taxmann_data = all_data.get("taxmann", {})
        for category, items in taxmann_data.items():
            for item in items:
                taxmann_updates.append(item)
        
        # Create optimized HTML content with inline styles for better email client compatibility
        
        # Create optimized HTML content with inline styles for better email client compatibility
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Daily Tax Updates - M2K Advisors</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f8fafc; }}
                .container {{ background-color: white; margin: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden; }}
                .header {{ background: linear-gradient(135deg, {self.m2k_primary}, {self.m2k_light}); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 32px; font-weight: 700; }}
                .header p {{ margin: 10px 0 0 0; font-size: 16px; opacity: 0.9; }}
                .m2k-logo {{ font-size: 14px; margin-top: 15px; opacity: 0.8; }}
                .section {{ margin: 25px 0; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
                .section-header {{ background: linear-gradient(135deg, {self.m2k_primary}, {self.m2k_light}); color: white; padding: 20px; font-weight: 600; font-size: 18px; }}
                .section-content {{ padding: 25px; background-color: white; }}
                .item {{ margin-bottom: 35px; padding: 25px; border-radius: 8px; border-left: 4px solid {self.m2k_primary}; background-color: #fefefe; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
                .item-title {{ font-weight: 600; color: {self.m2k_dark} !important; margin-bottom: 12px; font-size: 18px; line-height: 1.4; }}
                .item-summary {{ color: #4a5568; margin: 20px 0; font-size: 14px; line-height: 1.6; background-color: #f7fafc; padding: 20px; border-radius: 6px; border-left: 3px solid {self.m2k_light}; }}
                .item-link {{ color: white !important; text-decoration: none; font-weight: 600; font-size: 14px; display: inline-block; padding: 8px 16px; background-color: {self.m2k_light}; border-radius: 6px; }}
                .meta-item {{ color: {self.m2k_gray}; font-size: 16px; margin-top: 20px; }}
                .no-data {{ color: {self.m2k_gray}; font-style: italic; text-align: center; padding: 30px; background-color: #f8fafc; border-radius: 6px; }}
                .footer {{ background: linear-gradient(135deg, {self.m2k_primary}, {self.m2k_light}); color: white; padding: 25px; text-align: center; margin-top: 30px; }}
                .footer p {{ margin: 5px 0; opacity: 0.9; }}
                .stats {{ display: flex; justify-content: space-between; margin: 20px 0; padding: 20px; background-color: #f8fafc; border-radius: 8px; width: 100%; }}
                .stat-item {{ text-align: center; flex: 1; margin: 0 15px; }}
                .stat-item:first-child {{ margin-left: 0; }}
                .stat-item:last-child {{ margin-right: 0; }}
                .stat-number {{ font-size: 24px; font-weight: 700; color: {self.m2k_primary}; }}
                .stat-label {{ font-size: 12px; color: {self.m2k_gray}; margin-top: 5px; }}
                @media only screen and (max-width: 600px) {{
                    .container {{ margin: 10px; }}
                    .header {{ padding: 20px; }}
                    .header h1 {{ font-size: 24px; }}
                    .section-content {{ padding: 15px; }}
                    .item {{ padding: 15px; margin-bottom: 20px; }}
                    .stats {{ flex-direction: column; gap: 15px; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Daily Tax Updates</h1>
                    <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                    <div class="m2k-logo">M2K Advisors</div>
                </div>
                
                <div class="stats">
                    <div class="stat-item">
                        <div class="stat-number">{len(articles)}</div>
                        <div class="stat-label">Articles</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">{len(taxsutra_updates)}</div>
                        <div class="stat-label">Taxsutra Updates</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">{len(taxmann_updates)}</div>
                        <div class="stat-label">Taxmann Updates</div>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-header">
                        📰 Articles ({len(articles)})
                    </div>
                    <div class="section-content">
        """
        
        if articles:
            for article in articles:
                title = article.get("title", article.get("Title", "No Title"))
                date = article.get("date", article.get("Date", article.get("Published Date", "")))
                url = article.get("url", article.get("URL", ""))
                summary = article.get("summary", article.get("Summary", ""))
                
                html_content += f"""
                        <div class="item">
                            <div class="item-title">{title}</div>
                            {f'<section class="item-summary">{summary}</section>' if summary and summary != "N/A" else ''}
                            <div class="item-meta">
                            </div>
                        </div>
                    """
        else:
            html_content += '<div class="no-data">No articles found for this period.</div>'
            
        html_content += f"""
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-header">
                        ⚖️  Taxsutra Updates ({len(taxsutra_updates)})
                    </div>
                    <div class="section-content">
        """
        
        if taxsutra_updates:
            for ruling in taxsutra_updates:
                title = ruling.get("Title", "No Title")
                url = ruling.get("URL", "")
                case_name = ruling.get("Case Name", "")
                judicial_level_location = ruling.get("Judicial Level & Location", "")
                citation = ruling.get("Citation", "")
                court_abbr = self.extract_court_abbreviation(judicial_level_location)

                
                # Get summary using the new method
                summary = self.get_summary(ruling)
                summary_line = f"{case_name} - {judicial_level_location} - {citation}:{court_abbr}"
                html_content += f"""
                        <div class="item">
                            <div class="item-title">{title}</div>
                            {f'<div class="item-summary">{summary}</div> <a href ="{url}" target="_blank">Read More</a>' if summary else ''}
                            <div class="item-meta">
                                {f'<div class="meta-item">  |  {summary_line}</div>' if summary_line else ''}
                            </div>
                        </div>
                    """
        else:
            html_content += '<div class="no-data">No Taxsutra updates found for this period.</div>'
            
        html_content += f"""
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-header">
                        📋 Taxmann Updates ({len(taxmann_updates)})
                    </div>
                    <div class="section-content">
        """
        
        if taxmann_updates:
            for update in taxmann_updates:
                title = update.get("Title", "No Title")
                url = update.get("URL", "")
                summary = update.get("Summary", "")
                citation = update.get("Citation", "")
                
                html_content += f"""
                        <div class="item">
                            <div class="item-title">{title}</div>
                            {f'<section class="item-summary">{summary}</section>' if summary and summary != "N/A" else ''}
                            {f'<div class="meta-item">{citation}</div>' if citation else ''}
                        </div>
                    """
        else:
            html_content += '<div class="no-data">No Taxmann updates found for this period.</div>'
            
        html_content += """
                    </div>
                </div>
                
                <div class="footer">
                    <p>This email was automatically generated by the M2K Advisors Tax Rulings Scraper.</p>
                    <p>For questions or support, please contact our team at admin@m2k.co.in</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def send_email(self, all_data: Dict[str, Any] = None) -> bool:
        """
        Send daily update email with the scraped data
        
        Args:
            all_data: Dictionary containing all scraped data (optional, will use rulings.json if not provided)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message with proper headers to prevent truncation
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Daily Tax Updates - M2K Advisors - {datetime.now().strftime('%Y-%m-%d')}"
            msg["From"] = self.sender_email
            msg["To"] = ", ".join(self.recipient_emails)
            msg["X-Priority"] = "1"
            msg["X-MSMail-Priority"] = "High"
            msg["Importance"] = "high"
            msg["X-Mailer"] = "M2K Tax Rulings Scraper"
            
            # Create HTML content
            html_content = self.create_html_content(all_data)
            
            # Ensure full content is displayed
            html_content = self.ensure_full_content(html_content)
            
            # Attach HTML content with proper encoding
            html_part = MIMEText(html_content, "html", "utf-8")
            html_part.add_header("Content-Type", "text/html; charset=utf-8")
            msg.attach(html_part)
            
            # Create SSL context
            context = ssl.create_default_context()
            
            # Send email with timeout
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context, timeout=30) as server:
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, self.recipient_emails, msg.as_string())
            
            logger.info(f"✅ Email sent successfully to {', '.join(self.recipient_emails)}")
            logger.info(f"📧 Email size: {len(html_content)} characters ({len(html_content)/1024:.1f} KB)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            return False
 