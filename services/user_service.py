import gspread
import os
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

import os
CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH")

if not CREDENTIALS_PATH or not os.path.exists(CREDENTIALS_PATH):
    raise FileNotFoundError(f"❌ CREDENTIALS_PATH is missing or invalid: {CREDENTIALS_PATH}")


# Connect to Google Sheets
gc = gspread.service_account(filename=CREDENTIALS_PATH)
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

def get_name_by_username(username):
    import gspread
    gc = gspread.service_account(filename="credentials.json")  # Adjust path if needed
    sheet = gc.open("Database").worksheet("Login")  # 👈 Updated sheet name
    rows = sheet.get_all_values()

    header = rows[0]
    user_index = header.index("User")
    name_index = header.index("Name")

    for row in rows[1:]:
        if row[user_index].strip().lower() == username.strip().lower():
            return row[name_index]
    return "STAFF"