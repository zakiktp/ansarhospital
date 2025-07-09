from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from config import spreadsheet, MODULES
from utils.auth_utils import login_required, access_required
import pytz
from flask import send_file
import pandas as pd

opd_bp = Blueprint('opd', __name__, url_prefix='/opd')

@opd_bp.route('/', methods=['GET', 'POST'])
@login_required
@access_required('opd')
def opd_entry():
    sheet = spreadsheet.worksheet("OPD")
    appointment_sheet = spreadsheet.worksheet("Appointment")
    dropdown_sheet = spreadsheet.worksheet("Dropdownlist")
    staff = session.get('user', {}).get('name', 'STAFF')

    # Load address list
    address_list = sorted(set(r.strip() for r in dropdown_sheet.col_values(1) if r.strip()))

    # Load today's appointments (for modal)
    today_str = datetime.now(pytz.timezone("Asia/Kolkata")).strftime('%d/%m/%Y')
    all_appointments = appointment_sheet.get_all_records()
    appointment_list = []
    for row in all_appointments:
        raw_date = row.get("Date", '')
        if ':' in raw_date and ',' not in raw_date:
            raw_date = raw_date.replace(':', ',', 1)
        row_date = raw_date.split(',')[0].strip()
        if row_date == today_str:
            appointment_list.append({
                "name": row.get("Name", ""),
                "hf_name": row.get("H/F Name", ""),
                "mobile": row.get("Mobile", ""),
                "gender": row.get("Gender", "F"),
                "dob": row.get("DOB", ""),
                "address": row.get("Address", ""),
                "city": row.get("City", ""),
                "id": row.get("ID", ""),
                "blood_group": row.get("B.Group", "")
            })

    # Handle POST for new entry
    if request.method == 'POST':
        form = request.form
        name = form.get('name').strip()
        hf_name = form.get('fh_name').strip()
        age = form.get('age').strip()
        dob = form.get('dob').strip()
        gender = form.get('sex')
        address = form.get('address').strip()
        city = form.get('city').strip()
        mobile = form.get('mobile').strip()
        fee = form.get('fee').strip()
        doctor = form.get('doctor').strip()
        patient_id = form.get('patient_id', '')
        blood_group = form.get('blood_group', '')

        if not mobile.isdigit() or len(mobile) != 10:
            flash("⚠️ Mobile number must be 10 digits.", 'danger')
            return redirect(url_for('opd.opd_entry'))

        now = datetime.now(pytz.timezone("Asia/Kolkata"))
        timestamp = now.strftime('%d/%m/%Y %H:%M:%S')
        today_date = now.strftime('%d/%m/%Y')

        all_opd = sheet.get_all_records()
        next_no = str(len(all_opd) + 1)

        new_row = [
            next_no,         # No
            today_date,      # Date
            patient_id,      # ID
            form.get('prefix', ''),
            name,
            form.get('title', ''),
            hf_name,
            gender,
            age,
            dob,
            address,
            mobile,
            float(fee),
            staff,
            "REPORTED",
            doctor
        ]

        try:
            sheet.append_row(new_row, value_input_option='USER_ENTERED')
            flash("✅ OPD entry saved successfully!", 'success')
        except Exception as e:
            flash(f"❌ Failed to save entry: {e}", 'danger')

        return redirect(url_for('opd.opd_entry'))

    # Load recent OPD records (last 30 rows)
    all_opd = sheet.get_all_records()
    opd_records = all_opd[-30:] if len(all_opd) > 30 else all_opd

    return render_template(
        'opd.html',
        user=session['user'],
        access=session['user']['access'],
        modules=MODULES,
        opd_records=opd_records,
        address_list=address_list,
        appointment_list=appointment_list
    )

@opd_bp.route('/export/<format>', methods=['GET'])
@login_required
@access_required('opd')
def export_opd_data(format):
    sheet = spreadsheet.worksheet("OPD")
    data = sheet.get_all_records()

    df = pd.DataFrame(data)

    filename = f"OPD_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    if format == 'csv':
        path = f"{filename}.csv"
        df.to_csv(path, index=False)
        return send_file(path, as_attachment=True)

    elif format == 'excel':
        path = f"{filename}.xlsx"
        df.to_excel(path, index=False)
        return send_file(path, as_attachment=True)

    elif format == 'pdf':
        flash("PDF export not yet implemented.", "warning")
        return redirect(url_for('opd.opd_entry'))

    else:
        flash("Unsupported export format.", "danger")
        return redirect(url_for('opd.opd_entry'))

@opd_bp.route('/copy_appointments_to_opd')
@login_required
@access_required('opd')
def copy_appointments_to_opd():
    appointment_sheet = spreadsheet.worksheet("Appointment")
    opd_sheet = spreadsheet.worksheet("OPD")

    appointments = appointment_sheet.get_all_records()
    opd_records = opd_sheet.get_all_records()
    existing_ids = {r.get("ID", "") for r in opd_records}

    new_rows = []
    today_str = datetime.now(pytz.timezone("Asia/Kolkata")).strftime('%d/%m/%Y')

    for appt in appointments:
        appt_date = appt.get("Date", "")
        appt_date_part = appt_date.split(",")[0].strip()
        if appt_date_part != today_str:
            continue

        if appt.get("ID", "") in existing_ids:
            continue  # Skip if already copied

        new_row = [
            str(len(opd_records) + len(new_rows) + 1),
            appt.get("Date", ""),
            appt.get("ID", ""),
            appt.get("Prefix", ""),
            appt.get("Name", ""),
            appt.get("Titles", ""),
            appt.get("H/F Name", ""),
            appt.get("Gender", ""),
            appt.get("Age", ""),
            appt.get("DOB", ""),
            appt.get("Address", ""),
            appt.get("Mobile", ""),
            "",  # Fee Recd
            appt.get("Staff", ""),
            appt.get("Status", ""),
            appt.get("Doctor", "")
        ]
        new_rows.append(new_row)

    if new_rows:
        opd_sheet.append_rows(new_rows, value_input_option="USER_ENTERED")

    flash(f"✅ {len(new_rows)} appointment(s) copied to OPD sheet.", "success")
    return redirect(url_for('opd.opd_entry'))
