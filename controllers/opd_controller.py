from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from config import spreadsheet, MODULES
from utils.auth_utils import login_required, access_required
import pytz
from gspread_formatting import (
    cellFormat, format_cell_range, borders, numberFormat
)

opd_bp = Blueprint('opd', __name__, url_prefix='/opd')

@opd_bp.route('/', methods=['GET', 'POST'])
@login_required
@access_required('opd')
def opd_entry():
    tz = pytz.timezone("Asia/Kolkata")
    today_str = datetime.now(tz).strftime('%d/%m/%Y')

    sheet = spreadsheet.worksheet("OPD")
    appointment_sheet = spreadsheet.worksheet("Appointment")
    dropdown_sheet = spreadsheet.worksheet("Dropdownlist")
    staff = session.get('user', {}).get('name', 'STAFF')

    # Fetch Dropdown Address List
    try:
        address_list = sorted(set(r.strip() for r in dropdown_sheet.col_values(1) if r.strip()))
    except Exception as e:
        address_list = []
        flash(f"⚠️ Failed to load address list: {e}", 'warning')

    # Handle POST (form submission)
    if request.method == 'POST':
        form = request.form
        name = form.get('name', '').strip()
        hf_name = form.get('fh_name', '').strip()
        age = form.get('age', '').strip()
        dob = form.get('dob', '').strip()
        gender = form.get('sex', '')
        address = form.get('address', '').strip()
        city = form.get('city', '').strip()
        mobile = form.get('mobile', '').strip()
        fee = form.get('fee', '0').strip()
        doctor = form.get('doctor', '').strip()
        patient_id = form.get('patient_id', '').strip()
        blood_group = form.get('blood_group', '').strip()
        prefix = form.get('prefix', '').strip()
        title = form.get('titles', '').strip()

        # Mobile validation
        if not mobile.isdigit() or len(mobile) != 10:
            flash("⚠️ Mobile number must be 10 digits.", 'danger')
            return redirect(url_for('opd.opd_entry'))

        now = datetime.now(tz)
        today_date = datetime.now(tz).strftime('%d/%m/%Y, %H:%M:%S')

        try:
            existing_opd = sheet.get_all_records()
        except Exception as e:
            flash(f"❌ Failed to read OPD sheet: {e}", 'danger')
            return redirect(url_for('opd.opd_entry'))

        next_no = str(len(existing_opd) + 1)

        new_row = [
            next_no,
            today_date,
            patient_id,
            prefix,
            name,
            title,
            hf_name,
            gender,
            age,
            dob,
            address,
            city,
            mobile,
            staff,
            "REPORTED",
            doctor,
            float(fee)
        ]

        try:
            sheet.append_row(new_row, value_input_option='USER_ENTERED')
            flash("✅ OPD entry saved successfully!", 'success')
        except Exception as e:
            flash(f"❌ Failed to save OPD entry: {e}", 'danger')

        return redirect(url_for('opd.opd_entry'))



    # Load only today's OPD records
    expected_headers = ["No", "Date", "ID", "Prefix", "Name", "Titles", "H/F Name", "Gender", "Age", "DOB", "Address", "City", "Mobile", "Fee Recd", "Staff", "Status", "Doctor"]
    all_opd = sheet.get_all_records(expected_headers=expected_headers)
    today_str = datetime.now(pytz.timezone("Asia/Kolkata")).strftime('%d/%m/%Y')
    opd_records = [r for r in all_opd if r.get("Date", "").strip().split(',')[0] == today_str]

    try:
        all_opd = sheet.get_all_records()
        opd_records = [r for r in all_opd if r.get("Date", "").strip().split(',')[0] == today_str]
    except Exception as e:
        opd_records = []
        flash(f"❌ Failed to load OPD data: {e}", 'danger')

    try:
        all_appointments = appointment_sheet.get_all_records()
        appointment_list = []
        for row in all_appointments:
            raw_date = row.get("Date", '')
            if ':' in raw_date and ',' not in raw_date:
                raw_date = raw_date.replace(':', ',', 1)
            row_date = raw_date.split(',')[0].strip()
            if row_date == today_str:
                appointment_list.append({
                    "id": row.get("ID", ""),
                    "prefix": row.get("Prefix", ""),
                    "name": row.get("Name", ""),
                    "titles": row.get("Titles", ""),
                    "hf_name": row.get("H/F Name", ""),
                    "gender": row.get("Gender", ""),
                    "dob": row.get("DOB", ""),
                    "age": row.get("Age", ""),
                    "address": row.get("Address", ""),
                    "city": row.get("City", ""),
                    "mobile": row.get("Mobile", ""),
                    "blood_group": row.get("B.Group", ""),
                    "staff": row.get("Staff", ""),
                    "doctor": row.get("Doctor", ""),
                    "status": row.get("Status", "")
                })
    except Exception as e:
        appointment_list = []
        flash(f"❌ Failed to load appointment list: {e}", 'danger')

    return render_template(
        'opd.html',
        user=session['user'],
        access=session['user']['access'],
        modules=MODULES,
        opd_records=opd_records,
        address_list=address_list,
        appointment_list=appointment_list
    )

@opd_bp.route('/copy_appointments_to_opd')
@login_required
@access_required('opd')
def copy_appointments_to_opd():
    from_date = request.args.get("start_date")
    to_date = request.args.get("end_date")

    tz = pytz.timezone("Asia/Kolkata")
    today_str = datetime.now(tz).strftime('%d/%m/%Y')

    # Parse incoming dates or use today's date
    try:
        from_obj = datetime.strptime(from_date, "%Y-%m-%d") if from_date else datetime.strptime(today_str, "%d/%m/%Y")
        to_obj = datetime.strptime(to_date, "%Y-%m-%d") if to_date else datetime.strptime(today_str, "%d/%m/%Y")
    except ValueError:
        flash("❌ Invalid date format. Use YYYY-MM-DD.", "danger")
        return redirect(url_for('opd.opd_entry'))

    # Sheets
    appointment_sheet = spreadsheet.worksheet("Appointment")
    opd_sheet = spreadsheet.worksheet("OPD")

    # Records
    appointments = appointment_sheet.get_all_records()
    opd_records = opd_sheet.get_all_records(expected_headers=[
        "No", "Date", "ID", "Prefix", "Name", "Titles", "H/F Name", "Gender",
        "Age", "DOB", "Address", "City", "Mobile", "Staff", "Status", "Doctor", "Fee Recd"
    ])
    existing_ids = {r.get("ID", "") for r in opd_records}
    new_rows = []

    for appt in appointments:
        appt_date_raw = appt.get("Date", "")
        appt_date_str = appt_date_raw.split(",")[0].strip()

        try:
            appt_date_obj = datetime.strptime(appt_date_str, "%d/%m/%Y")
        except ValueError:
            continue  # skip rows with invalid date

        # Check date range
        if not (from_obj <= appt_date_obj <= to_obj):
            continue

        # Skip if already exists in OPD
        if appt.get("ID", "") in existing_ids:
            continue

        new_row = [
            str(len(opd_records) + len(new_rows) + 1),      # Serial No
            appt.get("Date", ""),                           # Date
            appt.get("ID", ""),                             # ID
            appt.get("Prefix", ""),                         # Prefix
            appt.get("Name", ""),                           # Name
            appt.get("Titles", ""),                         # Titles
            appt.get("H/F Name", ""),                       # H/F Name
            appt.get("Gender", ""),                         # Gender
            str(appt.get("Age", "")),                       # Age
            appt.get("DOB", ""),                            # DOB
            appt.get("Address", ""),                        # Address
            appt.get("City", ""),                           # City
            str(appt.get("Mobile", "")),                    # Mobile
            appt.get("Staff", ""),                          # Staff
            appt.get("Status", ""),                         # Status
            appt.get("Doctor", ""),                         # Doctor
            ""                                              # Fee Recd (blank)
        ]
        new_rows.append(new_row)

    # Append new records if any
    if new_rows:
        opd_sheet.append_rows(new_rows, value_input_option="USER_ENTERED")

        # Row where the new data is added
        start_row = len(opd_records) + 2  # existing_opd → opd_records

        fmt_center = cellFormat(horizontalAlignment='CENTER')
        fmt_left = cellFormat(horizontalAlignment='LEFT')
        fmt_right = cellFormat(
            horizontalAlignment='RIGHT',
            numberFormat=numberFormat(type='NUMBER', pattern='0.00')
        )
        fmt_borders = cellFormat(borders=borders(
            top={'style': 'SOLID'},
            bottom={'style': 'SOLID'},
            left={'style': 'SOLID'},
            right={'style': 'SOLID'}
        ))

        # Alignment
        center_cols = ['A', 'B', 'C', 'D', 'F', 'H', 'I', 'J', 'L', 'M', 'N', 'O', 'P']
        left_cols = ['E', 'G', 'K']
        right_cols = ['Q']

        for col in center_cols:
            format_cell_range(opd_sheet, f"{col}{start_row}", fmt_center)
        for col in left_cols:
            format_cell_range(opd_sheet, f"{col}{start_row}", fmt_left)
        for col in right_cols:
            format_cell_range(opd_sheet, f"{col}{start_row}", fmt_right)

        # Apply border formatting
        format_cell_range(opd_sheet, f"A{start_row}:Q{start_row}", fmt_borders)

    flash(f"✅ {len(new_rows)} appointment(s) copied to OPD sheet.", "success")
    return redirect(url_for('opd.opd_entry'))
