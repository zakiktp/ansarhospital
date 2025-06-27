import os
import json
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

# ✅ Load .env for local dev
load_dotenv()

# ✅ Load credentials from environment variable
google_creds_json = os.getenv("GOOGLE_CREDS_JSON")
if not google_creds_json:
    raise EnvironmentError("❌ GOOGLE_CREDS_JSON not found in environment variables.")

creds_dict = json.loads(google_creds_json)

# ✅ Authorize with Google API using dictionary credentials
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# ✅ Open spreadsheet using env var
spreadsheet = client.open_by_key(os.getenv("SHEET_ID"))

# ✅ Define enabled modules
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
        "name": "Birth Certificate",
        "endpoint": "birth_bp.certificate",
        "roles": ["admin", "receptionist"],
        "enabled": True,
        "icon": "🍼"
    }
]
