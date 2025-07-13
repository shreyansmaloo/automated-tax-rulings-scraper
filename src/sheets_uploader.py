"""
Google Sheets uploader for automated tax rulings data
Handles authentication, sheet creation, and data upload
"""

import logging
import re
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
            "Date",
            "Category", 
            "Sub-Category",
            "Summary"
        ]
    
    def extract_case_reference(self, ruling_data):
        """Extract case reference like [TS-797-HC-2025(MAD)] from citation data"""
        # First try to get from Citation field (extracted from .citationNumber class)
        citation = ruling_data.get("Citation", "N/A")
        if citation != "N/A":
            # Extract the citation in format [TS-797-HC-2025(MAD)]
            match = re.search(r'\[(TS-\d+-[A-Z]+-\d+\([A-Z]+\))\]', citation)
            if match:
                return match.group(0)
            
            # If no bracket format, return the citation as is
            return citation
        
        # Fallback to title if citation not found
        title = ruling_data.get("Title", "")
        match = re.search(r'\[(TS-\d+-[A-Z]+-\d+\([A-Z]+\))\]', title)
        if match:
            return match.group(0)
            
        return ""
    
    def extract_judicial_level_location(self, ruling_data):
        """Extract judicial level and location from the Judicial Level & Location field"""
        # Use the extracted Judicial Level & Location field directly
        judicial_level_location = ruling_data.get("Judicial Level & Location", "N/A")
        
        if judicial_level_location != "N/A":
            return judicial_level_location
        
        # Fallback to case law information parsing if the direct field is not available
        case_law_info = ruling_data.get("Case Law Information", "")
        
        # Look for common patterns like "High Court Madras" or "Supreme Court"
        court_patterns = [
            r'High Court ([A-Za-z]+)',
            r'Supreme Court',
            r'ITAT ([A-Za-z]+)',
            r'Tribunal ([A-Za-z]+)'
        ]
        
        for pattern in court_patterns:
            match = re.search(pattern, case_law_info)
            if match:
                return match.group(0)
        
        # If specific patterns don't match, look for any mention of Court
        court_match = re.search(r'([A-Za-z]+ Court|Tribunal|ITAT)', case_law_info)
        if court_match:
            return court_match.group(0)
            
        # Check for "HC" in the title and extract the location
        if "HC" in case_law_info:
            match = re.search(r'HC\s+([A-Z]{3})', case_law_info)
            if match:
                return f"High Court {match.group(1)}"
                
        return "N/A"
    
    def extract_case_name(self, ruling_data):
        """Extract case name - prefer Case Name field, fallback to Taxpayer Name"""
        # First priority: Use Case Name field if available
        case_name = ruling_data.get("Case Name", "N/A")
        if case_name != "N/A":
            return case_name
        
        # Second priority: Use Taxpayer Name
        taxpayer_name = ruling_data.get("Taxpayer Name", "N/A")
        if taxpayer_name != "N/A":
            # Construct case name from taxpayer name
            case_law_info = ruling_data.get("Case Law Information", "")
            
            if "commissioner" in case_law_info.lower() or "cit" in case_law_info.lower():
                return f"Commissioner of Income Tax Vs {taxpayer_name}"
            else:
                return f"{taxpayer_name} Vs Commissioner of Income Tax"
        
        # Fallback: Try to extract from case law info
        case_law_info = ruling_data.get("Case Law Information", "")
        
        vs_patterns = [
            r'([A-Za-z0-9\s\.]+)\s+[Vv][sS]\.?\s+([A-Za-z0-9\s\.]+)',
            r'([A-Za-z0-9\s\.]+)\s+[Vv]\.\s+([A-Za-z0-9\s\.]+)'
        ]
        
        for pattern in vs_patterns:
            match = re.search(pattern, case_law_info)
            if match:
                return f"{match.group(1).strip()} Vs {match.group(2).strip()}"
        
        # If no vs pattern, try to get the first line or sentence
        lines = case_law_info.split('\n')
        if lines and lines[0]:
            return lines[0].strip()
            
        return case_law_info[:50] if len(case_law_info) > 50 else case_law_info
    
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
            
        # Extract location abbreviation
        location_abbr = ""
        if "High Court" in judicial_level_location:
            location_match = re.search(r'High Court\s+([A-Za-z]+)', judicial_level_location)
            if location_match:
                location = location_match.group(1)
                location_abbr = location[:3].upper()
        elif "ITAT" in judicial_level_location:
            location_match = re.search(r'ITAT\s+([A-Za-z]+)', judicial_level_location)
            if location_match:
                location = location_match.group(1)
                location_abbr = location[:3].upper()
                
        if location_abbr:
            return f"{court_abbr} {location_abbr}"
        return court_abbr
    
    def prepare_data_for_upload(self, rulings_data):
        """Prepare rulings data for Google Sheets upload"""
        headers = self.get_sheet_headers()
        
        # Start with headers
        data = [headers]
        
        # Add data rows
        for ruling in rulings_data:
            # Extract date from ruling date
            date_value = ruling.get("Ruling Date", "N/A")
            if date_value == "N/A":
                date_value = ruling.get("Published Date", "N/A")
            
            # Category is always "Direct Tax"
            category = "Direct Tax"
            
            # Sub-Category is always "Case Laws"
            sub_category = "Case Laws"
            
            # Extract components for the summary
            title = ruling.get("Title", "")
            conclusion = ruling.get("Conclusion", "")
            
            # Extract case reference from citation
            case_reference = self.extract_case_reference(ruling)
            
            # Extract judicial level and location
            judicial_level_location = self.extract_judicial_level_location(ruling)
            
            # Extract case name
            case_name = self.extract_case_name(ruling)
            
            # Extract court abbreviation
            court_abbr = self.extract_court_abbreviation(judicial_level_location)
            
            # Format summary as requested:
            # Title
            # 
            # Conclusion
            # 
            # Case Name - Judicial Level & Location - [TS-797-HC-2025(MAD)]
            # The last line should be in orange color
            summary_line = f"{case_name} - {judicial_level_location} - {case_reference}:{court_abbr}"
            summary = f"{title}\n\n{conclusion}\n\n{summary_line}"
            
            row = [
                date_value,
                category,
                sub_category,
                summary
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
    
    def get_next_available_row(self, sheet_name="Sheet1"):
        """Get the next available row number for appending data"""
        try:
            # Get all values from the sheet
            range_name = f'{sheet_name}!A:A'
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.config.SPREADSHEET_ID,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                # Sheet is empty, start from row 1
                return 1
            
            # Return the next row after the last populated row
            return len(values) + 1
            
        except HttpError as e:
            logger.warning(f"Error getting next available row: {e}")
            # Default to row 1 if there's an error
            return 1

    def upload_data(self, taxsutra_rulings_data, sheet_name="Sheet1", clear_first=False):
        """Upload rulings data to Google Sheets - preserving existing data by default"""
        if not self.service:
            if not self.authenticate():
                return False
        
        try:
            # Prepare data
            data = self.prepare_data_for_upload(taxsutra_rulings_data)
            
            if clear_first:
                # Only clear if explicitly requested
                self.clear_sheet(sheet_name)
                range_name = f'{sheet_name}!A1'
                logger.info("🧹 Cleared existing sheet data")
            else:
                # Preserve existing data - find next available row
                next_row = self.get_next_available_row(sheet_name)
                
                if next_row == 1:
                    # Sheet is empty, include headers
                    range_name = f'{sheet_name}!A1'
                    logger.info("📄 Sheet is empty, adding headers and data")
                else:
                    # Sheet has data, skip headers and append to next row
                    data = data[1:]  # Remove headers from new data
                    range_name = f'{sheet_name}!A{next_row}'
                    logger.info(f"📋 Appending data starting from row {next_row} (preserving existing data)")
            
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
            logger.info(f"📋 {len(taxsutra_rulings_data)} rulings uploaded")
            
            # Apply formatting only if we're starting fresh or it's the first upload
            if clear_first or next_row == 1:
                self.format_sheet(sheet_name)
                # Apply rich text formatting to summary lines
                self.format_summary_lines(sheet_name)
            else:
                # Apply rich text formatting to the newly added rows
                self.format_summary_lines(sheet_name, start_row=next_row)
            
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
                            "endIndex": 4
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
                },
                # Set wrap text for summary column
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 1,
                            "startColumnIndex": 3,
                            "endColumnIndex": 4
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "wrapStrategy": "WRAP"
                            }
                        },
                        "fields": "userEnteredFormat.wrapStrategy"
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
    
    def format_summary_lines(self, sheet_name="Sheet1", start_row=2):
        """Apply rich text formatting to summary cells: title bold, third paragraph orange"""
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
                logger.warning(f"Sheet '{sheet_name}' not found for summary formatting")
                return
            
            # Get all data from the summary column to process each cell
            range_name = f'{sheet_name}!D:D'  # Summary column (D)
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.config.SPREADSHEET_ID,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if len(values) < start_row:
                logger.info("No data to format in summary column")
                return
            
            requests = []
            
            # Process each cell from start_row onwards
            for row_idx in range(start_row - 1, len(values)):  # 0-based indexing
                cell_value = values[row_idx][0] if values[row_idx] else ""
                
                if not cell_value.strip():
                    continue
                
                # Split into paragraphs using double newlines
                paragraphs = [p.strip() for p in cell_value.split('\n\n') if p.strip()]
                
                if len(paragraphs) < 3:
                    # If less than 3 paragraphs, apply basic formatting only
                    requests.append({
                        "repeatCell": {
                            "range": {
                                "sheetId": sheet_id,
                                "startRowIndex": row_idx,
                                "endRowIndex": row_idx + 1,
                                "startColumnIndex": 3,  # Column D
                                "endColumnIndex": 4
                            },
                            "cell": {
                                "userEnteredFormat": {
                                    "wrapStrategy": "WRAP",
                                    "verticalAlignment": "TOP"
                                }
                            },
                            "fields": "userEnteredFormat.wrapStrategy,userEnteredFormat.verticalAlignment"
                        }
                    })
                    continue
                
                # Build rich text runs for each paragraph
                text_format_runs = []
                
                # Find positions of each paragraph in the original text
                paragraph_positions = []
                current_search_pos = 0
                
                for i, paragraph in enumerate(paragraphs):
                    # Find the start position of this paragraph in the original text
                    start_pos = cell_value.find(paragraph, current_search_pos)
                    if start_pos == -1:
                        # If not found, skip this paragraph
                        continue
                    
                    end_pos = start_pos + len(paragraph)
                    paragraph_positions.append((i, start_pos, end_pos))
                    current_search_pos = end_pos
                
                # Create comprehensive text format runs that cover all text
                # Google Sheets needs complete coverage of all text with format runs
                text_format_runs = []
                
                # Sort paragraph positions by start index
                paragraph_positions.sort(key=lambda x: x[1])  # Sort by start_pos
                
                current_pos = 0
                
                for i, start_pos, end_pos in paragraph_positions:
                    # Add a format run for any gap before this paragraph (if any)
                    if current_pos < start_pos:
                        # Default formatting for the gap (newlines, etc.)
                        text_format_runs.append({
                            "startIndex": current_pos,
                            "format": {}  # Default formatting
                        })
                    
                    # Determine formatting for this paragraph
                    if i == 0:  # First paragraph (title) - bold
                        paragraph_format = {
                            "bold": True
                        }
                    elif i == 2:  # Third paragraph (summary_line) - orange
                        paragraph_format = {
                            "foregroundColor": {
                                "red": 1.0,
                                "green": 0.647,
                                "blue": 0.0
                            }
                        }
                    else:  # Second paragraph (conclusion) - default
                        paragraph_format = {}
                    
                    # Add format run for this paragraph
                    text_format_runs.append({
                        "startIndex": start_pos,
                        "format": paragraph_format
                    })
                    
                    current_pos = end_pos
                
                # Add final format run for any remaining text after the last paragraph
                if current_pos < len(cell_value):
                    text_format_runs.append({
                        "startIndex": current_pos,
                        "format": {}  # Default formatting
                    })
                
                # Remove consecutive runs with the same formatting to optimize
                optimized_runs = []
                for run in text_format_runs:
                    if not optimized_runs or optimized_runs[-1]["format"] != run["format"]:
                        optimized_runs.append(run)
                
                text_format_runs = optimized_runs
                
                # Create the update request for rich text
                requests.append({
                    "updateCells": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": row_idx,
                            "endRowIndex": row_idx + 1,
                            "startColumnIndex": 3,  # Column D
                            "endColumnIndex": 4
                        },
                        "rows": [{
                            "values": [{
                                "userEnteredValue": {
                                    "stringValue": cell_value
                                },
                                "userEnteredFormat": {
                                    "wrapStrategy": "WRAP",
                                    "verticalAlignment": "TOP"
                                },
                                "textFormatRuns": text_format_runs if text_format_runs else None
                            }]
                        }],
                        "fields": "userEnteredValue,userEnteredFormat.wrapStrategy,userEnteredFormat.verticalAlignment" + (",textFormatRuns" if text_format_runs else "")
                    }
                })
            
            # Execute all formatting requests in batches (Google Sheets has limits)
            if requests:
                batch_size = 50  # Reduced batch size for rich text formatting
                for i in range(0, len(requests), batch_size):
                    batch_requests = requests[i:i + batch_size]
                    
                    self.service.spreadsheets().batchUpdate(
                        spreadsheetId=self.config.SPREADSHEET_ID,
                        body={"requests": batch_requests}
                    ).execute()
                    
                    logger.info(f"✅ Applied rich text formatting to batch {i//batch_size + 1}")
                
                logger.info("✅ Applied rich text formatting - first paragraph bold, third paragraph orange")
            else:
                logger.info("No cells found to format")
            
        except Exception as e:
            logger.error(f"❌ Rich text formatting failed: {e}")
            # Fallback to basic formatting
            self._apply_simple_formatting(sheet_name, start_row)
    
    def _apply_simple_formatting(self, sheet_name="Sheet1", start_row=2):
        """Apply simple formatting as fallback - just wrap text and basic styling"""
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
                logger.warning(f"Sheet '{sheet_name}' not found")
                return
            
            # Get all data to determine the range
            range_name = f'{sheet_name}!D:D'  # Summary column (D)
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.config.SPREADSHEET_ID,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if len(values) < start_row:
                logger.info("No data to format")
                return
            
            end_row = len(values)
            
            # Apply basic formatting to the summary column
            requests = [{
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": start_row - 1,  # 0-based index
                        "endRowIndex": end_row,
                        "startColumnIndex": 3,  # Column D (0-based)
                        "endColumnIndex": 4
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "wrapStrategy": "WRAP",
                            "verticalAlignment": "TOP"
                        }
                    },
                    "fields": "userEnteredFormat.wrapStrategy,userEnteredFormat.verticalAlignment"
                }
            }]
            
            # Execute formatting
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.config.SPREADSHEET_ID,
                body={"requests": requests}
            ).execute()
            
            logger.info("✅ Applied basic formatting to summary column")
            
        except Exception as e:
            logger.warning(f"⚠️ Basic formatting failed: {e}")
    
    def get_sheet_url(self):
        """Get the URL of the Google Sheet"""
        return f"https://docs.google.com/spreadsheets/d/{self.config.SPREADSHEET_ID}/edit"

    def get_first_sheet_name(self):
        """Return the name of the first sheet/tab in the spreadsheet."""
        if not self.service:
            if not self.authenticate():
                return None
        try:
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.config.SPREADSHEET_ID
            ).execute()
            sheets = sheet_metadata.get('sheets', [])
            if not sheets:
                logger.error("No sheets found in the spreadsheet.")
                return None
            return sheets[0]['properties']['title']
        except Exception as e:
            logger.error(f"Failed to get first sheet name: {e}")
            return None

    def upload_expert_corner_data(self, taxsutra_expert_corner_data, sheet_name=None, clear_first=False):
        """Upload expert corner data to Google Sheets with custom mapping. If sheet_name is None, use the first sheet."""
        if not self.service:
            if not self.authenticate():
                return False
        try:
            if sheet_name is None:
                sheet_name = self.get_first_sheet_name()
                if not sheet_name:
                    logger.error("No valid sheet to upload expert corner data.")
                    return False
            # Prepare data
            headers = ["Date", "Category", "Sub-Category", "Summary"]
            data = [headers]
            for article in taxsutra_expert_corner_data:
                row = [
                    article.get("date", "N/A"),
                    "Direct tax",
                    "Article",
                    article.get("title", "")
                ]
                data.append(row)
            if clear_first:
                self.clear_sheet(sheet_name)
                range_name = f'{sheet_name}!A1'
            else:
                next_row = self.get_next_available_row(sheet_name)
                if next_row == 1:
                    range_name = f'{sheet_name}!A1'
                else:
                    data = data[1:]  # Remove headers from new data
                    range_name = f'{sheet_name}!A{next_row}'
            value_range = {'values': data}
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.config.SPREADSHEET_ID,
                range=range_name,
                valueInputOption='RAW',
                body=value_range
            ).execute()
            cells_updated = result.get('updatedCells', 0)
            logger.info(f"✅ Successfully uploaded expert corner data to Google Sheets")
            logger.info(f"📊 {cells_updated} cells updated")
            logger.info(f"📋 {len(taxsutra_expert_corner_data)} expert articles uploaded")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to upload expert corner data to Google Sheets: {e}")
            return False

    def upload_litigation_tracker_data(self, taxsutra_litigation_data, sheet_name=None, clear_first=False):
        """Upload litigation tracker data to Google Sheets with custom mapping and formatting."""
        if not self.service:
            if not self.authenticate():
                return False
        try:
            if sheet_name is None:
                sheet_name = self.get_first_sheet_name()
                if not sheet_name:
                    logger.error("No valid sheet to upload litigation tracker data.")
                    return False
            headers = ["Date", "Category", "Sub-Category", "Summary"]
            data = [headers]
            for entry in taxsutra_litigation_data:
                # Ensure summary is present and not just title
                title = entry.get('title', '')
                summary_text = entry.get('summary', '')
                summary = f"{title}\n\n{summary_text}" if summary_text else title
                row = [
                    entry.get("date", "N/A"),
                    "Direct Tax",
                    "Litigation",
                    summary
                ]
                print(f"Uploading row: {row}")  # Debug print
                data.append(row)
            if clear_first:
                self.clear_sheet(sheet_name)
                range_name = f'{sheet_name}!A1'
            else:
                next_row = self.get_next_available_row(sheet_name)
                if next_row == 1:
                    range_name = f'{sheet_name}!A1'
                else:
                    data = data[1:]  # Remove headers from new data
                    range_name = f'{sheet_name}!A{next_row}'
            value_range = {'values': data}
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.config.SPREADSHEET_ID,
                range=range_name,
                valueInputOption='RAW',
                body=value_range
            ).execute()
            cells_updated = result.get('updatedCells', 0)
            logger.info(f"✅ Successfully uploaded litigation tracker data to Google Sheets")
            logger.info(f"📊 {cells_updated} cells updated")
            logger.info(f"📋 {len(taxsutra_litigation_data)} litigation tracker articles uploaded")
            # Apply formatting: bold first line of summary
            self.format_litigation_summary(sheet_name, start_row=next_row)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to upload litigation tracker data to Google Sheets: {e}")
            return False

    def format_litigation_summary(self, sheet_name, start_row=2):
        """Apply bold formatting to the first line of the summary column for litigation tracker uploads."""
        try:
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.config.SPREADSHEET_ID
            ).execute()
            sheet_id = None
            for sheet in sheet_metadata.get('sheets', []):
                if sheet['properties']['title'] == sheet_name:
                    sheet_id = sheet['properties']['sheetId']
                    break
            if sheet_id is None:
                logger.warning(f"Sheet '{sheet_name}' not found for summary formatting")
                return
            range_name = f'{sheet_name}!D:D'  # Summary column (D)
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.config.SPREADSHEET_ID,
                range=range_name
            ).execute()
            values = result.get('values', [])
            if len(values) < start_row:
                logger.info("No data to format in summary column")
                return
            requests = []
            for row_idx in range(start_row - 1, len(values)):
                cell_value = values[row_idx][0] if values[row_idx] else ""
                if not cell_value.strip():
                    continue
                first_newline = cell_value.find('\n')
                if first_newline == -1:
                    bold_end = len(cell_value)
                else:
                    bold_end = first_newline
                text_format_runs = [
                    {"startIndex": 0, "format": {"bold": True}},
                    {"startIndex": bold_end, "format": {}}
                ]
                requests.append({
                    "updateCells": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": row_idx,
                            "endRowIndex": row_idx + 1,
                            "startColumnIndex": 3,  # Column D
                            "endColumnIndex": 4
                        },
                        "rows": [{
                            "values": [{
                                "userEnteredValue": {"stringValue": cell_value},
                                "userEnteredFormat": {"wrapStrategy": "WRAP", "verticalAlignment": "TOP"},
                                "textFormatRuns": text_format_runs
                            }]
                        }],
                        "fields": "userEnteredValue,userEnteredFormat.wrapStrategy,userEnteredFormat.verticalAlignment,textFormatRuns"
                    }
                })
            if requests:
                batch_size = 50
                for i in range(0, len(requests), batch_size):
                    batch_requests = requests[i:i + batch_size]
                    self.service.spreadsheets().batchUpdate(
                        spreadsheetId=self.config.SPREADSHEET_ID,
                        body={"requests": batch_requests}
                    ).execute()
                    logger.info(f"✅ Applied bold formatting to litigation summary batch {i//batch_size + 1}")
            else:
                logger.info("No cells found to format for litigation summary")
        except Exception as e:
            logger.error(f"❌ Litigation summary formatting failed: {e}") 
            
    def prepare_taxmann_data_for_upload(self, taxmann_data):
        """Prepare Taxmann data for Google Sheets upload"""
        headers = self.get_sheet_headers()
        
        # Start with headers
        data = [headers]
        
        # Add data rows
        for update in taxmann_data:
            # Extract date
            date_value = update.get("Date", "N/A")
            
            # Category (GST, Company & SEBI, or FEMA & Banking)
            category = update.get("Category", "N/A")
            
            # Sub-Category from the topic
            sub_category = update.get("Sub-Category", "General")
            
            # Format summary as requested:
            # Title
            # 
            # Content (1st paragraph + 3rd paragraph)
            # 
            # Source: Taxmann.com - URL
            title = update.get("Title", "")
            content = update.get("Content", "")
            url = update.get("URL", "")
            source_line = f"Source: Taxmann.com - {url}"
            
            summary = f"{title}\n\n{content}\n\n{source_line}"
            
            row = [
                date_value,
                category,
                sub_category,
                summary
            ]
            data.append(row)
        
        return data
    
    def upload_taxmann_data(self, taxmann_data, sheet_name="Sheet1", clear_first=False):
        """Upload Taxmann data to Google Sheets - preserving existing data by default"""
        if not self.service:
            if not self.authenticate():
                return False
        
        try:
            # Prepare data
            data = self.prepare_taxmann_data_for_upload(taxmann_data)
            
            if clear_first:
                # Only clear if explicitly requested
                self.clear_sheet(sheet_name)
                range_name = f'{sheet_name}!A1'
                logger.info("🧹 Cleared existing sheet data")
            else:
                # Preserve existing data - find next available row
                next_row = self.get_next_available_row(sheet_name)
                
                if next_row == 1:
                    # Sheet is empty, include headers
                    range_name = f'{sheet_name}!A1'
                    logger.info("📄 Sheet is empty, adding headers and data")
                else:
                    # Sheet has data, skip headers and append to next row
                    data = data[1:]  # Remove headers from new data
                    range_name = f'{sheet_name}!A{next_row}'
                    logger.info(f"📋 Appending data starting from row {next_row} (preserving existing data)")
            
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
            logger.info(f"✅ Successfully uploaded Taxmann data to Google Sheets")
            logger.info(f"📊 {cells_updated} cells updated")
            logger.info(f"📋 {len(taxmann_data)} updates uploaded")
            
            # Apply formatting only if we're starting fresh or it's the first upload
            if clear_first or next_row == 1:
                self.format_sheet(sheet_name)
            
            # Apply rich text formatting to the newly added rows
            self.format_taxmann_summary_lines(sheet_name, start_row=next_row if next_row > 1 else 2)
            
            return True
            
        except HttpError as e:
            logger.error(f"❌ Failed to upload Taxmann data to Google Sheets: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error during Taxmann data upload: {e}")
            return False
    
    def format_taxmann_summary_lines(self, sheet_name="Sheet1", start_row=2):
        """Apply rich text formatting to Taxmann summary cells: title bold, source line orange"""
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
                logger.warning(f"Sheet '{sheet_name}' not found for Taxmann summary formatting")
                return
            
            # Get all data from the summary column to process each cell
            range_name = f'{sheet_name}!D:D'  # Summary column (D)
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.config.SPREADSHEET_ID,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if len(values) < start_row:
                logger.info("No data to format in Taxmann summary column")
                return
            
            requests = []
            
            # Process each cell from start_row onwards
            for row_idx in range(start_row - 1, len(values)):
                cell_value = values[row_idx][0] if values[row_idx] else ""
                
                if not cell_value.strip():
                    continue
                
                # Split into paragraphs using double newlines
                paragraphs = [p.strip() for p in cell_value.split('\n\n') if p.strip()]
                
                if len(paragraphs) < 3:
                    # If less than 3 paragraphs, apply basic formatting only
                    requests.append({
                        "repeatCell": {
                            "range": {
                                "sheetId": sheet_id,
                                "startRowIndex": row_idx,
                                "endRowIndex": row_idx + 1,
                                "startColumnIndex": 3,  # Column D
                                "endColumnIndex": 4
                            },
                            "cell": {
                                "userEnteredFormat": {
                                    "wrapStrategy": "WRAP",
                                    "verticalAlignment": "TOP"
                                }
                            },
                            "fields": "userEnteredFormat.wrapStrategy,userEnteredFormat.verticalAlignment"
                        }
                    })
                    continue
                
                # Find positions of each paragraph in the original text
                paragraph_positions = []
                current_search_pos = 0
                
                for i, paragraph in enumerate(paragraphs):
                    # Find the start position of this paragraph in the original text
                    start_pos = cell_value.find(paragraph, current_search_pos)
                    if start_pos == -1:
                        # If not found, skip this paragraph
                        continue
                    
                    end_pos = start_pos + len(paragraph)
                    paragraph_positions.append((i, start_pos, end_pos))
                    current_search_pos = end_pos
                
                # Sort paragraph positions by start index
                paragraph_positions.sort(key=lambda x: x[1])  # Sort by start_pos
                
                # Create text format runs
                text_format_runs = []
                current_pos = 0
                
                for i, start_pos, end_pos in paragraph_positions:
                    # Add a format run for any gap before this paragraph (if any)
                    if current_pos < start_pos:
                        # Default formatting for the gap (newlines, etc.)
                        text_format_runs.append({
                            "startIndex": current_pos,
                            "format": {}  # Default formatting
                        })
                    
                    # Determine formatting for this paragraph
                    if i == 0:  # First paragraph (title) - bold
                        paragraph_format = {
                            "bold": True
                        }
                    elif i == len(paragraphs) - 1:  # Last paragraph (source line) - orange
                        paragraph_format = {
                            "foregroundColor": {
                                "red": 1.0,
                                "green": 0.647,
                                "blue": 0.0
                            }
                        }
                    else:  # Middle paragraphs (content) - default
                        paragraph_format = {}
                    
                    # Add format run for this paragraph
                    text_format_runs.append({
                        "startIndex": start_pos,
                        "format": paragraph_format
                    })
                    
                    current_pos = end_pos
                
                # Add final format run for any remaining text after the last paragraph
                if current_pos < len(cell_value):
                    text_format_runs.append({
                        "startIndex": current_pos,
                        "format": {}  # Default formatting
                    })
                
                # Remove consecutive runs with the same formatting to optimize
                optimized_runs = []
                for run in text_format_runs:
                    if not optimized_runs or optimized_runs[-1]["format"] != run["format"]:
                        optimized_runs.append(run)
                
                text_format_runs = optimized_runs
                
                # Create the update request for rich text
                requests.append({
                    "updateCells": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": row_idx,
                            "endRowIndex": row_idx + 1,
                            "startColumnIndex": 3,  # Column D
                            "endColumnIndex": 4
                        },
                        "rows": [{
                            "values": [{
                                "userEnteredValue": {
                                    "stringValue": cell_value
                                },
                                "userEnteredFormat": {
                                    "wrapStrategy": "WRAP",
                                    "verticalAlignment": "TOP"
                                },
                                "textFormatRuns": text_format_runs if text_format_runs else None
                            }]
                        }],
                        "fields": "userEnteredValue,userEnteredFormat.wrapStrategy,userEnteredFormat.verticalAlignment" + (",textFormatRuns" if text_format_runs else "")
                    }
                })
            
            # Execute all formatting requests in batches (Google Sheets has limits)
            if requests:
                batch_size = 50  # Reduced batch size for rich text formatting
                for i in range(0, len(requests), batch_size):
                    batch_requests = requests[i:i + batch_size]
                    
                    self.service.spreadsheets().batchUpdate(
                        spreadsheetId=self.config.SPREADSHEET_ID,
                        body={"requests": batch_requests}
                    ).execute()
                    
                    logger.info(f"✅ Applied rich text formatting to Taxmann batch {i//batch_size + 1}")
                
                logger.info("✅ Applied rich text formatting to Taxmann data - title bold, source line orange")
            else:
                logger.info("No cells found to format for Taxmann data")
            
        except Exception as e:
            logger.error(f"❌ Taxmann rich text formatting failed: {e}")
            # Fallback to basic formatting
            self._apply_simple_formatting(sheet_name, start_row)