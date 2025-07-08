import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv
import gspread
from gspread.exceptions import APIError
from google.oauth2.service_account import Credentials
from gspread_formatting import format_cell_range, CellFormat, Borders

# Load .env locally if running outside Render
load_dotenv()

# Define scopes
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from environment variable (minified JSON)
google_creds_json = os.getenv("GOOGLE_CREDS_JSON")
if not google_creds_json:
    raise EnvironmentError("GOOGLE_CREDS_JSON not found in environment variables.")

creds_dict = json.loads(google_creds_json)
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)

# Service account file path for legacy functions
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = os.path.join(os.getcwd(), 'credentials.json')

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

# -------------------- Basic Utilities --------------------

def get_sheet_service():
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )
    gc = gspread.authorize(credentials)
    return gc

def read_sheet_as_dict(spreadsheet_name, worksheet_name):
    gc = get_sheet_service()
    sheet = gc.open(spreadsheet_name).worksheet(worksheet_name)
    return sheet.get_all_records()

def append_to_sheet(spreadsheet_name, worksheet_name, row_data):
    gc = get_sheet_service()
    sheet = gc.open(spreadsheet_name).worksheet(worksheet_name)
    sheet.append_row(row_data, value_input_option='USER_ENTERED')

def read_from_google_sheet(sheet_name):
    try:
        sheet = spreadsheet.worksheet(sheet_name)
        return sheet.get_all_values()
    except Exception as e:
        print(f"Error reading from sheet '{sheet_name}':", e)
        return []

# -------------------- OPD Logic --------------------

def get_today_appointment_count():
    today = datetime.now().strftime('%Y-%m-%d')
    try:
        records = worksheet.get_all_records()
        return sum(1 for row in records if row.get('appointment_date') == today)
    except Exception as e:
        print(f"Error fetching appointment count: {e}")
        return 0

def safe_load_sheet(sheet_name, expected_headers=None):
    try:
        sheet = spreadsheet.worksheet(sheet_name)
        header_row = sheet.row_values(1)
        cleaned = [h.strip() for h in header_row if h.strip()]

        if len(cleaned) != len(set(cleaned)):
            print(f"Duplicate or blank headers in '{sheet_name}':", header_row)
            return []

        if expected_headers and cleaned != expected_headers:
            print(f"Header mismatch in '{sheet_name}'. Expected: {expected_headers}")
            return []

        return sheet.get_all_records()
    except Exception as e:
        print(f"Error loading sheet '{sheet_name}': {e}")
        return []

def get_gsheet():
    return spreadsheet.worksheet("OPD")

def update_opd_sheet(row_data):
    sheet = get_gsheet()
    last_row = len(sheet.get_all_values()) + 1
    row_data[0] = last_row - 1  # Column A: row number
    sheet.append_row(row_data, value_input_option="USER_ENTERED")
    format_last_row(sheet, last_row)

def format_last_row(sheet, row):
    fmt_center = CellFormat(horizontalAlignment='CENTER')
    fmt_border = CellFormat(
        borders=Borders(
            top={'style': 'SOLID'},
            bottom={'style': 'SOLID'},
            left={'style': 'SOLID'},
            right={'style': 'SOLID'}
        )
    )
    for col in ['A', 'B', 'E', 'F', 'G', 'H', 'J', 'L']:
        format_cell_range(sheet, f"{col}{row}", fmt_center)
        format_cell_range(sheet, f"{col}{row}", fmt_border)
    format_cell_range(sheet, f"A{row}:L{row}", fmt_border)

# -------------------- Patients Master Logic --------------------

def get_patient_id_by_match(data):
    patient_id = find_existing_patient_id(
        name=data.get("name", ""),
        fh_name=data.get("fh_name", ""),
        address=data.get("address", ""),
        mobile=data.get("mobile", "")
    )
    if patient_id:
        return patient_id
    else:
        new_id = generate_new_patient_id()
        add_new_patient({
            "ID": new_id,
            "Name": data.get("name", ""),
            "F/H Name": data.get("fh_name", ""),
            "Address": data.get("address", ""),
            "Mobile": data.get("mobile", ""),
            "DOB": data.get("dob", ""),
            "Sex": data.get("sex", "F")
        })
        return new_id

def find_existing_patient_id(name, fh_name, address, mobile):
    try:
        patients_sheet = spreadsheet.worksheet("Patients")
        records = patients_sheet.get_all_records()
        for row in records:
            if (
                row.get("Name", "").strip().lower() == name.strip().lower() and
                row.get("F/H Name", "").strip().lower() == fh_name.strip().lower() and
                row.get("Address", "").strip().lower() == address.strip().lower() and
                row.get("Mobile", "").strip() == mobile.strip()
            ):
                return row.get("ID")
    except Exception as e:
        print("[find_existing_patient_id] Error:", e)
    return None

def generate_new_id():
    """
    Generates a new unique ID like AH0001, AH0002 based on the OPD sheet.
    """
    try:
        sheet = get_gsheet()
        ids = [row['ID'] for row in sheet.get_all_records() if row.get('ID')]
        max_id = 0
        for i in ids:
            if i.startswith("AH"):
                try:
                    max_id = max(max_id, int(i[2:]))
                except:
                    continue
        return f"AH{max_id + 1:04d}"
    except Exception as e:
        print("[generate_new_id] Error:", e)
        return "AH0001"


def generate_new_patient_id():
    try:
        patients_sheet = spreadsheet.worksheet("Patients")
        ids = [row['ID'] for row in patients_sheet.get_all_records() if row.get('ID')]
        max_id = 0
        for i in ids:
            try:
                if i.startswith("AH"):
                    max_id = max(max_id, int(i[2:]))
            except:
                continue
        return f"AH{max_id + 1:04d}"
    except:
        return "AH0001"

def add_new_patient(patient_data):
    try:
        patients_sheet = spreadsheet.worksheet("Patients")
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        row = [
            patient_data["ID"],
            patient_data["Name"].upper(),
            patient_data["F/H Name"].upper(),
            patient_data["Address"].upper(),
            patient_data["Mobile"],
            patient_data.get("DOB", ""),
            patient_data.get("Sex", "F"),
            now
        ]
        patients_sheet.append_row(row, value_input_option="USER_ENTERED")
        print(f"✅ New patient added: {patient_data['ID']}")
    except Exception as e:
        print("[add_new_patient] Error:", e)

def find_patients_by_name(name):
    try:
        sheet = spreadsheet.worksheet("Patients")
        records = sheet.get_all_records()
        name_lower = name.strip().lower()
        return [
            {
                "id": row.get("ID", ""),
                "name": row.get("Name", ""),
                "fh_name": row.get("F/H Name", ""),
                "address": row.get("Address", ""),
                "mobile": row.get("Mobile", ""),
                "dob": row.get("DOB", ""),
                "sex": row.get("Sex", "")
            }
            for row in records if name_lower in row.get("Name", "").lower()
        ]
    except Exception as e:
        print("Error finding patients:", e)
        return []

# -------------------- Misc Utilities --------------------

def get_submitter_full_name(user_id):
    try:
        login_sheet = spreadsheet.worksheet("Login")
        records = login_sheet.get_all_records()
        for row in records:
            if row.get("User", "").strip().lower() == user_id.strip().lower():
                return row.get("Name", "UNKNOWN").strip()
    except Exception as e:
        print("[get_submitter_full_name] Error:", e)
    return "UNKNOWN"

def get_address_list():
    dropdown_sheet = spreadsheet.worksheet("Dropdownlist")
    addresses = dropdown_sheet.col_values(1)
    return [addr.strip() for addr in addresses if addr.strip()]

def append_to_google_sheet(sheet_name, row_data):
    try:
        sheet = spreadsheet.worksheet(sheet_name)
        last_row = len(sheet.get_all_values()) + 1
        row_data[0] = last_row - 1
        sheet.append_row(row_data, value_input_option="USER_ENTERED")
        format_last_row(sheet, last_row)
        print(f"✅ Row appended to {sheet_name}: {row_data}")
    except Exception as e:
        print(f"❌ Error appending to sheet '{sheet_name}':", e)
