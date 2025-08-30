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
from typing import Dict, Any
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
            rulings_file = Path("./rulings.json")
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
        summary = ruling.get("Summary", "")
        
        # Prioritize conclusion over decision summary and summary
        if conclusion and conclusion != "N/A":
            return conclusion
        elif decision_summary and decision_summary != "N/A":
            return decision_summary
        elif summary and summary != "N/A":
            return summary
        else:
            return ""
    
    def ensure_full_content(self, html_content: str) -> str:
        """Minimal meta tags for Gmail compatibility"""
        return html_content.replace('<head>', "<head><meta http-equiv=Content-Type content='text/html;charset=utf-8'><meta name=viewport content='width=device-width,initial-scale=1'>")

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

    def shorten_summary(self, summary: str, max_lines: int = 6) -> str:
        """
        Truncate the summary to approximately max_lines lines (about 120 characters per line).
        If the summary is short, return as is. Otherwise, truncate at the last word boundary and add ellipsis.
        """
        if not summary or summary == "N/A":
            return ''
        max_chars = max_lines * 300
        if len(summary) <= max_chars:
            return summary.strip()
        truncated = summary[:max_chars]
        # Avoid breaking in the middle of a word
        if ' ' in truncated:
            truncated = truncated.rsplit(' ', 1)[0]
        return truncated.strip()

    def create_html_content(self, all_data: Dict[str, Any] = None) -> str:
        """
        Create a simple, formal, and minimal HTML content for the daily tax updates email.
        Only includes essential information in a compact table format.
        """
        if all_data is None:
            all_data = self.load_rulings_data()

        # Collect all updates
        taxsutra_updates = all_data.get("taxsutra", {}).get("rulings", [])
        litigation_articles = all_data.get("taxsutra", {}).get("litigation_tracker", [])
        expert_articles = all_data.get("taxsutra", {}).get("expert_corner", [])
        taxmann_updates = []
        for category, items in all_data.get("taxmann", {}).items():
            taxmann_updates.extend(items)

        def row_html(item, source, serial_number):
            """Generate a single table row with minimized HTML"""
            title = item.get("Title") or item.get("title") or "-"
            summary = self.get_summary(item)
            url = item.get("URL") or item.get("url") or ""
            # Hardcode category as 'Direct Tax' for Taxsutra items
            category = "Direct Tax" if source == "Taxsutra" else (item.get("Category") or item.get("category") or "-")
            sub_category = item.get("Sub-Category") or item.get("sub-category") or ""
            
            # Build category info
            if source == "Taxsutra":
                cat_info = f"[{category} | {source}]"
            else:
                cat_info = f"[{category} | {source}]"
            
            # Minimal HTML with inline styles
            return (f"<tr>"
                    f"<td style='padding:4px 8px;font-size:14px; font-family:tahoma'>{serial_number}</td>"
                    f"<td style='padding:4px 8px;font-family:tahoma'>"
                    f"<a href='{url}' style='color:{self.m2k_primary};text-decoration:none;font-weight:bold; font-size:15px !important'>{title}</a> <span style='color:#0a0a0a;text-decoration:italic;font-weight:bold'> | [{category}]</span>"
                    # f"<br><span style='color:#0a0a0a;text-decoration:underline'>{cat_info}</span>"
                    f"<span style='color:#0a0a0a; font-size:5px !important;'><p> </p></span> <br><span style='color:#0a0a0a; font-size:13px !important'>{summary}</span>"
                    "</td></tr>")

        # Initialize HTML parts
        html_parts = [
            "<!DOCTYPE html><html><head>",
            "<meta http-equiv=Content-Type content='text/html;charset=utf-8'>",
            "<meta name=viewport content='width=device-width,initial-scale=1'>",
            "<title>Tax Updates</title>",
            "<style>body{font-family:Arial,sans-serif;font-size:13px;margin:0;padding:0}",
            "table{width:100%;border-collapse:collapse;margin:0}",
            "th,td{border:1px solid #ddd;padding:4px 8px}",
            "th{background:#f2f2f2;font-weight:700}",
            "tr:nth-child(even){background:#fafafa}",
            "h2{font-size:16px;margin:12px 0 4px}",
            "</style></head><body>"
        ]

        # Taxsutra Rulings Table
        if taxsutra_updates:
            html_parts.extend([
                "<h2>Taxsutra Rulings</h2>",
                "<table><tr><th>S.No</th><th>Title, Category, Source & Summary</th></tr>"
            ])
            for serial_number, item in enumerate(taxsutra_updates, start=1):
                html_parts.append(row_html(item, "Taxsutra", serial_number))
            html_parts.append("</table>")

        # Litigation Tracker Table
        if litigation_articles:
            html_parts.extend([
                "<h2>Litigation Tracker</h2>",
                "<table><tr><th>S.No</th><th>Title, Category, Source & Summary</th></tr>"
            ])
            for serial_number, item in enumerate(litigation_articles, start=1):
                html_parts.append(row_html(item, "Litigation Tracker", serial_number))
            html_parts.append("</table>")

        # TaxSutra Expert Corner Table
        if expert_articles:
            html_parts.extend([
                "<h2>Taxsutra Expert Corner</h2>",
                "<table><tr><th>S.No</th><th>Title, Category, Source & Summary</th></tr>"
            ])
            for serial_number, item in enumerate(expert_articles, start=1):
                html_parts.append(row_html(item, "Taxsutra Expert Corner", serial_number))
            html_parts.append("</table>")

        # Taxmann Updates Table
        if taxmann_updates:
            html_parts.extend([
                "<h2>Taxmann Updates</h2>",
                "<table><tr><th>S.No</th><th>Title, Category, Source & Summary</th></tr>"
            ])
            for serial_number, item in enumerate(taxmann_updates, start=1):
                html_parts.append(row_html(item, "Taxmann", serial_number))
            html_parts.append("</table>")

        if not (taxsutra_updates or litigation_articles or expert_articles or taxmann_updates):
            html_parts.append("<p style='color:#888'>No updates available for today.</p>")

        # Add footer and close HTML
        html_parts.extend([
            "<hr><div style='font-size:11px;color:#888'>This is an automated email. For queries, contact M2K Advisors.</div>",
            "</body></html>"
        ])
        
        # Join all parts with minimal whitespace
        return "".join(html_parts)
    
    
    def send_email(self, all_data: Dict[str, Any] = None) -> bool:
        """
        Send daily update email with the scraped data
        
        Args:
            all_data: Dictionary containing all scraped data (optional, will use rulings.json if not provided)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create a simple MIME message with proper headers for Gmail
            msg = MIMEMultipart()
            msg["Subject"] = f"Daily Tax Updates - M2K Advisors - {datetime.now().strftime('%Y-%m-%d')}"
            msg["From"] = self.sender_email
            msg["To"] = ", ".join(self.recipient_emails)
            msg["X-Priority"] = "1"
            msg["X-MSMail-Priority"] = "High"
            msg["Importance"] = "high"
            msg["X-Mailer"] = "M2K Tax Rulings Scraper"
            msg["MIME-Version"] = "1.0"
            msg["Content-Type"] = "text/html; charset=utf-8"
            msg.preamble = 'This is a multi-part message in MIME format.'
            
            # Create HTML content
            html_content = self.create_html_content(all_data)
            
            # Ensure full content is displayed
            html_content = self.ensure_full_content(html_content)
            
            # Set the message body directly
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
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
 