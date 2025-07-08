import os
import json
import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

# ✅ Load .env for local dev
load_dotenv()

# ✅ Load credentials from environment variable
creds_json = os.getenv("GOOGLE_CREDS_JSON")
if not creds_json:
    raise EnvironmentError("❌ GOOGLE_CREDS_JSON not found in environment variables.")

creds_dict = json.loads(creds_json)

# ✅ Authorize Google Sheets access
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
gspread_client = gspread.authorize(credentials)

# ✅ Open target spreadsheet using its ID from .env
spreadsheet = gspread_client.open_by_key(os.getenv("SHEET_ID"))

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
