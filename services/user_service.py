import os
import json
import base64
from datetime import datetime
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

# Load .env
load_dotenv()

# Scopes for Google Sheets and Drive
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from environment
if os.getenv("GOOGLE_CREDS_JSON"):
    creds_info = json.loads(os.getenv("GOOGLE_CREDS_JSON"))
elif os.getenv("GOOGLE_CREDENTIALS_B64"):
    creds_json = base64.b64decode(os.getenv("GOOGLE_CREDENTIALS_B64")).decode("utf-8")
    creds_info = json.loads(creds_json)
else:
    raise RuntimeError("❌ Google credentials not found in environment variables.")

# Authorize client
creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
gc = gspread.authorize(creds)
sheet = gc.open("Database").worksheet("Login")

# 🔍 Get user by email
def get_user_by_email(email):
    records = sheet.get_all_records()
    for row in records:
        if row.get('Email') == email:
            return row
    return None

# 🔍 Get user by username (login name)
def get_user_by_username(username):
    records = sheet.get_all_records()
    for row in records:
        if row.get('User') == username:
            return row
    return None

# 🔐 Update password for user
def update_user_password(email, new_password):
    cell = sheet.find(email)
    if cell:
        row = cell.row
        sheet.update_cell(row, sheet.find("Password").col, new_password)
        return True
    return False

# 🔐 Set OTP and expiry for user
def set_otp_for_user(email, otp, expiry):
    cell = sheet.find(email)
    if cell:
        row = cell.row
        sheet.update_cell(row, sheet.find("OTP").col, otp)
        sheet.update_cell(row, sheet.find("OTP_Expiry").col, expiry.strftime('%Y-%m-%d %H:%M:%S'))

# ✅ Validate OTP against email
def validate_otp(email, entered_otp):
    cell = sheet.find(email)
    if not cell:
        return False

    row = cell.row
    otp = sheet.cell(row, sheet.find("OTP").col).value
    expiry_str = sheet.cell(row, sheet.find("OTP_Expiry").col).value

    try:
        expiry_time = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')
    except Exception:
        return False

    return otp == entered_otp and datetime.now() <= expiry_time

# 🧍 Get full name of user
def get_name_by_username(username):
    records = sheet.get_all_records()
    for row in records:
        if row.get("User", "").strip().lower() == username.strip().lower():
            return row.get("Name", "STAFF")
    return "STAFF"
