from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from config import spreadsheet, MODULES
from utils.email_utils import send_mail
from utils.auth_utils import access_required
import pytz
import os
import pandas as pd
from fpdf import FPDF
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

print("Import successful")

# Setup Google credentials
scope = ['https://www.googleapis.com/auth/drive']
credentials = Credentials.from_service_account_file(
    r"D:\\Projects\\ansarhospital\\credentials\\credentials.json", scopes=scope
)

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
        results = service.files().list(q=f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and '{parent_id or 'root'}' in parents and trashed=false",
                                       spaces='drive', fields='files(id, name)').execute()
        folder = results.get('files')
        if folder:
            parent_id = folder[0]['id']
        else:
            metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id] if parent_id else []
            }
            folder = service.files().create(body=metadata, fields='id').execute()
            parent_id = folder.get('id')

    file_metadata = {'name': filename, 'parents': [parent_id]}
    media = build('media', 'v1').MediaFileUpload(file_path, mimetype=mime_type)
    uploaded = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return uploaded.get('id')

@appointment_bp.route('/export/<file_format>')
def export_appointments(file_format):
    sheet = spreadsheet.worksheet('Appointment')
    data = sheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])
    today = datetime.now().strftime('%d-%m-%Y')

    try:
        if file_format == 'csv':
            filename = f"appointment_export_{today}.csv"
            path = os.path.join(EXPORT_DIR, filename)
            df.to_csv(path, index=False)
            flash(f"✅ CSV exported to: {path}")

        elif file_format == 'excel':
            filename = f"appointment_export_{today}.xlsx"
            path = os.path.join(EXPORT_DIR, filename)
            df.to_excel(path, index=False)
            flash(f"✅ Excel exported to: {path}")

        elif file_format == 'pdf':
            filename = f"appointment_export_{today}.pdf"
            path = os.path.join(EXPORT_DIR, filename)
            col_widths = [12, 28, 35, 30, 32, 20, 18, 20]
            headers = df.columns.tolist()
            pdf = FPDF(orientation='P', unit='mm', format='A4')
            pdf.set_auto_page_break(auto=True, margin=10)
            pdf.add_page()
            pdf.set_font("Arial", size=7)

            def render_header():
                pdf.set_fill_color(220, 230, 241)
                pdf.set_text_color(0)
                pdf.set_font('Arial', 'B', 7)
                for i, col in enumerate(headers):
                    pdf.cell(col_widths[i], 7, col, border=1, fill=True, align='C')
                pdf.ln(7)
                pdf.set_font('Arial', '', 6)

            render_header()
            for _, row in df.iterrows():
                cell_texts = [str(val) if pd.notnull(val) else '' for val in row]
                for i, text in enumerate(cell_texts):
                    align = 'C' if headers[i] in {'No', 'Date', 'Mobile', 'Staff', 'Status'} else 'L'
                    pdf.cell(col_widths[i], 6, text, border=1, align=align)
                pdf.ln(6)

            pdf.output(path)
            flash(f"✅ PDF exported to: {path}")

        elif file_format == 'google':
            filename = f"Appointment_Backup_{today}.xlsx"
            path = os.path.join(EXPORT_DIR, filename)
            df.to_excel(path, index=False)
            upload_to_drive(path, filename, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            flash("✅ Spreadsheet uploaded to Google Drive 'Ansar Hospital/Backup'.")

    except Exception as e:
        flash(f"❌ Export failed: {e}")
        print("Export error:", e)

    return redirect(url_for('appointment_bp.appointment_main'))

@appointment_bp.route('/', methods=['GET', 'POST'])
@access_required('appointment')
def appointment_main():
    sheet = spreadsheet.worksheet("Appointment")
    dropdown_sheet = spreadsheet.worksheet("Dropdownlist")
    staff = session.get('user', {}).get('name', 'STAFF')
    selected_address = 'OTHER'
    selected_status = 'NOT REPORTED'
    all_records = sheet.get_all_records()

    if request.method == 'POST':
        form = request.form
        if form.get('action') == 'update':
            raw_index = form.get('record_index', '').strip()
            if not raw_index.isdigit():
                flash("⚠️ Record index missing.", 'danger')
                return redirect(url_for('appointment_bp.appointment_main'))
            index = int(raw_index)
            try:
                updated_row = [
                    sheet.cell(index, 1).value or str(index - 1),
                    sheet.cell(index, 2).value or get_local_timestamp(),
                    form['update_name'].strip().upper(),
                    form['update_hf_name'].strip().upper(),
                    form['update_address'].strip().upper(),
                    form['update_mobile'].strip(),
                    sheet.cell(index, 7).value or staff,
                    form['update_status'].strip().upper(),
                ]
                if not updated_row[5].isdigit() or len(updated_row[5]) != 10:
                    flash("⚠️ Mobile number must be 10 digits.", 'danger')
                    return redirect(url_for('appointment_bp.appointment_main'))
                sheet.update(f'A{index}:H{index}', [updated_row])
                flash("✅ Appointment updated.", 'success')
            except Exception as e:
                flash(f"❌ Update failed: {e}", 'danger')
            return redirect(url_for('appointment_bp.appointment_main'))

        elif 'save' in form:
            try:
                name = form['name'].strip().upper()
                hf_name = form['hf_name'].strip().upper()
                address = form['address'].strip().upper()
                if address == 'OTHER':
                    address = form.get('other_address', '').strip().upper()
                mobile = form['mobile'].strip()
                status = form.get('status', 'NOT REPORTED').strip().upper()

                if not mobile.isdigit() or len(mobile) != 10:
                    flash("⚠️ Mobile number must be 10 digits.", 'danger')
                    return redirect(url_for('appointment_bp.appointment_main'))

                existing_addresses = [a.strip().upper() for a in dropdown_sheet.col_values(1)]
                if address and address not in existing_addresses:
                    dropdown_sheet.append_row([address])
                    address_set = sorted(set(existing_addresses + [address]) - {'OTHER'})
                    address_set.append("OTHER")
                    dropdown_sheet.clear()
                    dropdown_sheet.update('A1', [[v] for v in address_set])

                timestamp = get_local_timestamp()
                appointment_no = len(all_records) + 1
                new_row = [appointment_no, timestamp, name, hf_name, address, mobile, staff, status]
                sheet.append_row(new_row, value_input_option='USER_ENTERED')

                email_data = {
                    "name": name,
                    "hf_name": hf_name,
                    "address": address,
                    "staff": staff,
                    "number": appointment_no
                }
                send_mail(
                    to_email=os.getenv("EMAIL_RECEIVER", "zakiup@gmail.com"),
                    data=email_data
                )

                flash("✅ Appointment added.", 'success')
            except Exception as e:
                flash(f"❌ Save failed: {e}", 'danger')
            return redirect(url_for('appointment_bp.appointment_main'))

        elif form.get('search') == '1':
            name_q = form.get('search_name', '').lower()
            mobile_q = form.get('search_mobile', '')
            address_q = form.get('search_address', '').lower()
            start = form.get('start_date')
            end = form.get('end_date')
            filtered = []
            for i, row in enumerate(all_records, start=2):
                match = True
                if name_q and name_q not in str(row.get('Name', '')).lower():
                    match = False
                if mobile_q and mobile_q not in str(row.get('Mobile', '')):
                    match = False
                if address_q and address_q not in str(row.get('Address', '')).lower():
                    match = False
                if start or end:
                    try:
                        row_date = datetime.strptime(str(row.get('Date', '')).split(',')[0], '%d/%m/%Y')
                        if start and row_date < datetime.strptime(start, '%Y-%m-%d'):
                            match = False
                        if end and row_date > datetime.strptime(end, '%Y-%m-%d'):
                            match = False
                    except:
                        match = False
                if match:
                    row['SheetRowIndex'] = i
                    filtered.append(row)

            address_list = sorted(set(r.strip() for r in dropdown_sheet.col_values(1) if r.strip()))
            return render_template('appointment.html', user=session['user'], access=session['user']['access'], modules=MODULES, address_list=address_list, records=filtered, selected_address=selected_address, selected_status=selected_status)

    today = datetime.now().strftime('%d/%m/%Y')
    records = []
    for i, row in enumerate(all_records, start=2):
        if row.get('Date', '').startswith(today):
            row['SheetRowIndex'] = i
            records.append(row)
    if not records:
        for i, row in enumerate(all_records[-10:], start=len(all_records) - 10 + 2):
            row['SheetRowIndex'] = i
            records.append(row)

    address_list = sorted(set(r.strip() for r in dropdown_sheet.col_values(1) if r.strip()))
    return render_template('appointment.html', user=session['user'], access=session['user']['access'], modules=MODULES, address_list=address_list, records=records, selected_address=selected_address, selected_status=selected_status)
