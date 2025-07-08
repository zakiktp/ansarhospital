from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from config import spreadsheet, MODULES
from utils.auth_utils import login_required, access_required
import pytz

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

        new_row = [
            timestamp, name, hf_name, patient_id, age, dob,
            gender, address, mobile, fee, staff, doctor, blood_group
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