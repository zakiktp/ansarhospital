import os
import json
import gspread
import base64
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

# ✅ Load .env for local dev
load_dotenv()

# ✅ Define Google scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# ✅ Load credentials from JSON or Base64
if os.getenv("GOOGLE_CREDS_JSON"):
    creds_info = json.loads(os.getenv("GOOGLE_CREDS_JSON"))
elif os.getenv("GOOGLE_CREDENTIALS_B64"):
    decoded = os.getenv("GOOGLE_CREDENTIALS_B64")
    creds_info = json.loads(
        base64.b64decode(decoded).decode("utf-8")
    )
else:
    raise EnvironmentError("❌ GOOGLE_CREDS_JSON or GOOGLE_CREDENTIALS_B64 is required.")

# ✅ Authorize Google Sheets access
credentials = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
gspread_client = gspread.authorize(credentials)

# ✅ Open target spreadsheet using its ID from .env
SPREADSHEET_ID = os.getenv("SHEET_ID")
if not SPREADSHEET_ID:
    raise EnvironmentError("❌ SHEET_ID is missing in environment variables.")

spreadsheet = gspread_client.open_by_key(SPREADSHEET_ID)

# ✅ Define enabled modules for the sidebar/dashboard
MODULES = [
    {
        "name": "Appointment",
        "endpoint": "appointment_bp.appointment_main",
        "roles": ["admin", "staff"],
        "enabled": True,
        "icon": "🗓️"
    },
    {
        "name": "Attendance",
        "endpoint": "attendance_bp.attendance",
        "roles": ["admin"],
        "enabled": True,
        "icon": "📋"
    },
    {
        "name": "OPD",
        "endpoint": "opd_bp.opd",
        "roles": ["admin", "doctor"],
        "enabled": True,
        "icon": "🏥"
    },
    {
        "name": "Discharge",
        "endpoint": "discharge_bp.discharge",
        "roles": ["admin", "doctor"],
        "enabled": True,
        "icon": "📤"
    },
    {
        "name": "Pharmacy",
        "endpoint": "birth_bp.certificate",
        "roles": ["admin", "receptionist"],
        "enabled": True,
        "icon": "🍼"
    }
]
