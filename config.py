import os
from dotenv import load_dotenv
from utils.sheets import spreadsheet
import gspread


base_dir = os.path.dirname(os.path.abspath(__file__))
cred_path = os.path.abspath(os.path.join(base_dir, '..', 'credentials', 'credentials.json'))

if not os.path.exists(cred_path):
    raise FileNotFoundError(f"Google credentials file not found at: {cred_path}")

spreadsheet = gspread.service_account(filename=cred_path).open("Database")
load_dotenv()

MODULES = [
    {
        "name": "Appointment",
        "endpoint": "appointment_bp.appointment_main",  # ← must match function name
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