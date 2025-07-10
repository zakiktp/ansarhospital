from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from config import spreadsheet, MODULES
from utils.email_utils import send_mail
from utils.auth_utils import access_required, login_required
import pytz
import os
import pandas as pd
import json
from fpdf import FPDF
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# ✅ Setup Google credentials
scope = ['https://www.googleapis.com/auth/drive']
creds_json = os.environ.get("GOOGLE_CREDS_JSON")
if not creds_json:
    raise EnvironmentError("❌ GOOGLE_CREDS_JSON is not set in environment variables.")
info = json.loads(creds_json)
credentials = Credentials.from_service_account_info(info, scopes=scope)

appointment_bp = Blueprint('appointment_bp', __name__, url_prefix='/appointment')
EXPORT_DIR = r"G:\\My Drive\\Ansar Hospital\\Export"
os.makedirs(EXPORT_DIR, exist_ok=True)

def get_local_timestamp():
    india = pytz.timezone("Asia/Kolkata")
    return datetime.now(india).strftime('%d/%m/%Y, %H:%M:%S')

def upload_to_drive(file_path, filename, mime_type):
    service = build('drive', 'v3', credentials=credentials)
    folders = ["Ansar Hospital", "Backup"]
    parent_id = None
    for folder_name in folders:
        results = service.files().list(
            q=f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and '{parent_id or 'root'}' in parents and trashed=false",
            spaces='drive', fields='files(id, name)').execute()
        folder = results.get('files')
        if folder:
            parent_id = folder[0]['id']
        else:
            metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id] if parent_id else []}
            folder = service.files().create(body=metadata, fields='id').execute()
            parent_id = folder.get('id')
    file_metadata = {'name': filename, 'parents': [parent_id]}
    media = build('media', 'v1').MediaFileUpload(file_path, mimetype=mime_type)
    uploaded = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return uploaded.get('id')

@appointment_bp.route('/', methods=['GET'])
@login_required
@access_required('appointment')
def appointment_main():
    from urllib.parse import urlencode
    import requests

    dropdown_sheet = spreadsheet.worksheet("Dropdownlist")
    address_list = sorted(set(r.strip() for r in dropdown_sheet.col_values(1) if r.strip()))

    filters = {
        "name": request.args.get("name", "").strip(),
        "hf_name": request.args.get("hf_name", "").strip(),
        "mobile": request.args.get("mobile", "").strip(),
        "address": request.args.get("address", "").strip(),
        "doctor": request.args.get("doctor", "").strip(),
        "from_date": request.args.get("from_date", "").strip(),
        "to_date": request.args.get("to_date", "").strip()
    }

    try:
        from urllib.parse import urlencode

        # Check if any filter is applied
        if not any(filters.values()):
            today_str = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d")
            filters["from_date"] = today_str
            filters["to_date"] = today_str

        query = urlencode(filters)
        api_url = f"http://127.0.0.1:5000/api/search_appointments?{query}"
        response = requests.get(api_url)
        all_records = response.json() if response.status_code == 200 else []
    except Exception as e:
        flash(f"❌ Failed to load appointments: {e}", "danger")
        all_records = []

    for row in all_records:
        row["id"] = row.get("ID", "")
        row["prefix"] = row.get("Prefix", "")
        row["name"] = row.get("Name", "")
        row["titles"] = row.get("Titles", "")
        row["hf_name"] = row.get("H/F Name", "")
        row["gender"] = row.get("Gender", "")
        row["dob"] = row.get("DOB", "")
        row["age"] = row.get("Age", "")
        row["address"] = row.get("Address", "")
        row["city"] = row.get("City", "")
        row["mobile"] = row.get("Mobile", "")
        row["blood_group"] = row.get("B.Group", "")
        row["staff"] = row.get("Staff", "")
        row["doctor"] = row.get("Doctor", "")
        row["status"] = row.get("Status", "")

    stats = {
        'total': len(all_records),
        'reported': sum(1 for r in all_records if r.get('VisitStatus') == 'REPORTED'),
        'pending': sum(1 for r in all_records if r.get('VisitStatus') != 'REPORTED')
    }

    return render_template(
        'appointment.html',
        user=session['user'],
        access=session['user']['access'],
        modules=MODULES,
        address_list=address_list,
        records=all_records,
        stats=stats,
        selected_address='',
        selected_status=''
    )

@appointment_bp.route('/edit/<id>', methods=['GET', 'POST'])
def edit_appointment(id):
    sheet = spreadsheet.worksheet("Appointment")
    patient_sheet = spreadsheet.worksheet("Patient")
    address_sheet = spreadsheet.worksheet("Dropdownlist")
    records = sheet.get_all_records()
    address_list = [row[0] for row in address_sheet.get_all_values() if row]

    row_index = next((i for i, row in enumerate(records, start=2) if row.get("ID") == id), None)
    if not row_index:
        flash("Record not found", "danger")
        return redirect(url_for('appointment_bp.appointment_main'))

    if request.method == 'POST':
        data = request.form.to_dict()
        dob = data.get('dob', '').strip()
        if "-" in dob:
            try:
                dob = datetime.strptime(dob, "%Y-%m-%d").strftime("%d/%m/%Y")
            except:
                pass

        final_address = data.get("address", "")
        if final_address == "OTHER":
            final_address = data.get("new_address", "").strip().upper()

        updated_row = [
            row_index - 1,                       # No
            records[row_index - 2]["Date"],     # Date
            data.get("id", ""),                 # ID
            data.get("prefix", ""),             # Prefix
            data.get("name", ""),               # Name
            data.get("title", ""),              # Titles
            data.get("hf_name", ""),            # H/F Name
            data.get("gender", ""),             # Gender
            data.get("age", ""),                # Age
            dob,                                # DOB
            final_address,                      # Address
            data.get("city", ""),               # ✅ City
            data.get("mobile", ""),             # Mobile
            data.get("staff", ""),              # Staff
            data.get("status", ""),             # Status
            data.get("doctor", "")              # Doctor
        ]

        try:
            sheet.delete_rows(row_index)
            sheet.insert_row(updated_row, row_index)
            flash("✅ Appointment updated successfully!", "success")

            patient_records = patient_sheet.get_all_values()
            headers = patient_records[0]
            id_col = headers.index("ID") if "ID" in headers else 0

            for i, row in enumerate(patient_records[1:], start=2):
                if row and row[id_col] == id:
                    city = data.get("city", "")  # ✅ Use submitted City
                    update_row = [
                        data.get("id", ""),
                        data.get("prefix", ""),
                        data.get("name", ""),
                        data.get("title", ""),
                        data.get("hf_name", ""),
                        data.get("mobile", ""),
                        final_address,
                        city,                       # ✅ Correct city used
                        data.get("age", ""),
                        data.get("gender", ""),
                        dob
                    ]
                    patient_sheet.update(f"A{i}:K{i}", [update_row])
                    print(f"✅ Patient sheet updated with new City for ID: {id}")
                    break

            if data.get("address") == "OTHER" and final_address:
                try:
                    dropdown_sheet = spreadsheet.worksheet("Dropdownlist")
                    all_rows = dropdown_sheet.get_all_values()
                    col_a = [row[0].strip().upper() for row in all_rows if row and row[0].strip()]

                    if final_address not in col_a:
                        col_a.append(final_address)
                        sorted_a = sorted(set(col_a))
                        max_rows = max(len(sorted_a), len(all_rows))
                        updated_rows = []
                        for idx in range(max_rows):
                            existing = all_rows[idx] if idx < len(all_rows) else [""]
                            new_row = [sorted_a[idx]] if idx < len(sorted_a) else [""]
                            new_row += existing[1:] if len(existing) > 1 else []
                            updated_rows.append(new_row)

                        end_col = chr(65 + len(updated_rows[0]) - 1)
                        dropdown_sheet.update(f"A1:{end_col}{len(updated_rows)}", updated_rows)
                        print("✅ New address inserted and A:A sorted without losing other columns.")
                except Exception as addr_err:
                    print("⚠️ Failed to update Dropdownlist:", addr_err)

        except Exception as e:
            flash(f"❌ Failed to update: {e}", "danger")

        return redirect(url_for('appointment_bp.appointment_main'))

    record = records[row_index - 2]
    return render_template('edit_appointment.html', id=id, record=record, address_list=address_list)
