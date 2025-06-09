"""
Google Sheets uploader for automated tax rulings data
Handles authentication, sheet creation, and data upload
"""

import logging
from datetime import datetime
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config.settings import config

logger = logging.getLogger(__name__)

class SheetsUploader:
    """Google Sheets uploader for rulings data"""
    
    def __init__(self):
        self.config = config
        self.service = None
        self.credentials = None
        
    def authenticate(self):
        """Authenticate with Google Sheets API using service account"""
        try:
            credentials_path = Path(self.config.SERVICE_ACCOUNT_FILE)
            
            if not credentials_path.exists():
                logger.error(f"Service account file not found: {credentials_path}")
                return False
            
            # Define the scope
            SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
            
            # Authenticate
            self.credentials = service_account.Credentials.from_service_account_file(
                str(credentials_path), scopes=SCOPES
            )
            
            # Build the service
            self.service = build('sheets', 'v4', credentials=self.credentials)
            
            logger.info("✅ Google Sheets authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Google Sheets authentication failed: {e}")
            return False
    
    def get_sheet_headers(self):
        """Define the headers for the data"""
        return [
            "Title",
            "Published Date", 
            "Ruling Date",
            "Conclusion",
            "Decision Summary",
            "Case Law Information",
            "URL",
            "Date Scraped"
        ]
    
    def prepare_data_for_upload(self, rulings_data):
        """Prepare rulings data for Google Sheets upload"""
        headers = self.get_sheet_headers()
        
        # Current timestamp for "Date Scraped"
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Start with headers
        data = [headers]
        
        # Add data rows
        for ruling in rulings_data:
            row = [
                ruling.get("Title", ""),
                ruling.get("Published Date", ""),
                ruling.get("Ruling Date", ""),
                ruling.get("Conclusion", ""),
                ruling.get("Decision Summary", ""),
                ruling.get("Case Law Information", ""),
                ruling.get("URL", ""),
                current_timestamp
            ]
            data.append(row)
        
        return data
    
    def clear_sheet(self, sheet_name="Sheet1"):
        """Clear all data from the sheet"""
        try:
            # Clear the sheet
            clear_request = {
                'range': f'{sheet_name}!A:Z',
            }
            
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.config.SPREADSHEET_ID,
                range=clear_request['range']
            ).execute()
            
            logger.info(f"✅ Cleared sheet: {sheet_name}")
            return True
            
        except HttpError as e:
            logger.error(f"❌ Failed to clear sheet: {e}")
            return False
    
    def upload_data(self, rulings_data, sheet_name="Sheet1", clear_first=True):
        """Upload rulings data to Google Sheets"""
        if not self.service:
            if not self.authenticate():
                return False
        
        try:
            # Prepare data
            data = self.prepare_data_for_upload(rulings_data)
            
            if clear_first:
                self.clear_sheet(sheet_name)
            
            # Define the range (starting from A1)
            range_name = f'{sheet_name}!A1'
            
            # Create the value range object
            value_range = {
                'values': data
            }
            
            # Upload data
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.config.SPREADSHEET_ID,
                range=range_name,
                valueInputOption='RAW',
                body=value_range
            ).execute()
            
            cells_updated = result.get('updatedCells', 0)
            logger.info(f"✅ Successfully uploaded data to Google Sheets")
            logger.info(f"📊 {cells_updated} cells updated")
            logger.info(f"📋 {len(rulings_data)} rulings uploaded")
            
            # Apply formatting
            self.format_sheet(sheet_name)
            
            return True
            
        except HttpError as e:
            logger.error(f"❌ Failed to upload data to Google Sheets: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error during upload: {e}")
            return False
    
    def format_sheet(self, sheet_name="Sheet1"):
        """Apply basic formatting to the sheet"""
        try:
            # Get sheet ID
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.config.SPREADSHEET_ID
            ).execute()
            
            sheet_id = None
            for sheet in sheet_metadata.get('sheets', []):
                if sheet['properties']['title'] == sheet_name:
                    sheet_id = sheet['properties']['sheetId']
                    break
            
            if sheet_id is None:
                logger.warning(f"Sheet '{sheet_name}' not found for formatting")
                return
            
            # Formatting requests
            requests = [
                # Bold headers
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 1
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "textFormat": {
                                    "bold": True
                                },
                                "backgroundColor": {
                                    "red": 0.9,
                                    "green": 0.9,
                                    "blue": 0.9
                                }
                            }
                        },
                        "fields": "userEnteredFormat(textFormat,backgroundColor)"
                    }
                },
                # Auto-resize columns
                {
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": 0,
                            "endIndex": 8
                        }
                    }
                },
                # Freeze header row
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet_id,
                            "gridProperties": {
                                "frozenRowCount": 1
                            }
                        },
                        "fields": "gridProperties.frozenRowCount"
                    }
                }
            ]
            
            # Execute formatting
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.config.SPREADSHEET_ID,
                body={"requests": requests}
            ).execute()
            
            logger.info("✅ Sheet formatting applied")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to apply formatting: {e}")
    
    def get_sheet_url(self):
        """Get the URL of the Google Sheet"""
        return f"https://docs.google.com/spreadsheets/d/{self.config.SPREADSHEET_ID}/edit" 