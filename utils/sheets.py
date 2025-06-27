import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv
import gspread
from gspread.exceptions import APIError
from google.oauth2.service_account import Credentials

# Load .env locally if running outside Render
load_dotenv()

# Define scopes
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# 🌐 Load credentials from environment variable (minified JSON)
google_creds_json = os.getenv("GOOGLE_CREDS_JSON")
if not google_creds_json:
    raise EnvironmentError("❌ GOOGLE_CREDS_JSON not found in environment variables.")

creds_dict = json.loads(google_creds_json)
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)

# Authorize client
client = gspread.authorize(creds)

# Load spreadsheet
SPREADSHEET_NAME = os.getenv('SPREADSHEET_NAME', 'Database')

# Retry logic for opening Google Sheet
for attempt in range(3):
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)
        break
    except APIError as e:
        if "503" in str(e):
            print(f"Google API returned 503. Retrying... (Attempt {attempt + 1})")
            time.sleep(2)
        else:
            raise

# Default worksheet
worksheet = spreadsheet.worksheet("Appointment")


def get_today_appointment_count():
    """
    Counts today's appointments based on 'appointment_date' in the 'Appointment' worksheet.
    """
    today = datetime.now().strftime('%Y-%m-%d')
    try:
        records = worksheet.get_all_records()
        return sum(1 for row in records if row.get('appointment_date') == today)
    except Exception as e:
        print(f"Error fetching appointment count: {e}")
        return 0


def safe_load_sheet(sheet_name, expected_headers=None):
    """
    Safely load a worksheet by name and validate its header row.

    Args:
        sheet_name (str): Name of the worksheet/tab to load.
        expected_headers (list, optional): List of headers to validate against.

    Returns:
        list[dict]: Cleaned records from the sheet or an empty list if invalid.
    """
    try:
        sheet = spreadsheet.worksheet(sheet_name)
        header_row = sheet.row_values(1)
        cleaned = [h.strip() for h in header_row if h.strip()]

        if len(cleaned) != len(set(cleaned)):
            print(f"❌ Duplicate or blank headers in '{sheet_name}':", header_row)
            return []

        if expected_headers and cleaned != expected_headers:
            print(f"⚠️ Header mismatch in '{sheet_name}'. Expected: {expected_headers}")
            return []

        return sheet.get_all_records()
    except Exception as e:
        print(f"❌ Error loading sheet '{sheet_name}': {e}")
        return []
