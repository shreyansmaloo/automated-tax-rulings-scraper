#!/usr/bin/env python3
"""
Test script for email functionality with rulings.json data
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import config
from src.email_sender import EmailSender

def test_email():
    """Test email functionality with rulings.json data"""
    
    print("🧪 Testing email functionality with rulings.json data...")
    
    # Check if email is configured
    if not config.EMAIL_SENDER or not config.EMAIL_PASSWORD:
        print("⚠️ Email not configured. Set EMAIL_SENDER and EMAIL_PASSWORD in .env file")
        print("📧 Email would contain data from rulings.json file")
        return False
    
    try:
        email_sender = EmailSender()
        
        # Test HTML content generation with rulings.json data
        html_content = email_sender.create_html_content()
        print(f"✅ HTML content generated ({len(html_content)} characters)")
        
        # Test email sending
        if email_sender.send_email():
            print("✅ Email sent successfully!")
            return True
        else:
            print("❌ Failed to send email")
            return False
            
    except Exception as e:
        print(f"❌ Error testing email: {e}")
        return False

if __name__ == "__main__":
    test_email()
