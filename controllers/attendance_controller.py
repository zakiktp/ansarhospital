import io
from utils.export import export_attendance_data, export_attendance_summary
from flask import send_file
from flask import Blueprint, render_template, request, redirect, session, flash, url_for
from services.attendance_service import (
    save_attendance_checkin, save_attendance_checkout,
    get_attendance_data_filtered, export_to_excel, export_to_pdf
)
from config import spreadsheet
from utils.auth_utils import login_required  # ✅ Decorator to enforce login
from utils.email_sender import send_attendance_confirmation

# 🔹 Register Blueprint
attendance_bp = Blueprint('attendance_bp', __name__, url_prefix='/attendance')

# ✅ Attendance Form Page (protected)

print("📌 attendance() route hit")


@attendance_bp.route('/')
@login_required
def attendance():
    name_list = []  # Default value to avoid NameError
    try:
        dropdown_sheet = spreadsheet.worksheet("Dropdownlist")

        # 🔍 Debug: Log full sheet
        all_data = dropdown_sheet.get_all_values()
        print("\n🟨 Full 'Dropdownlist' Sheet:")
        for i, row in enumerate(all_data, 1):
            print(f"Row {i}:", row)

        # 🔍 Debug: Log raw column D
        raw_col_d = dropdown_sheet.col_values(4)
        print("🟡 Raw Column D (with header):", raw_col_d)

        # ✅ Handle header: "Name" is expected at index 0
        if raw_col_d and raw_col_d[0].strip().upper() == "NAME":
            name_list = [name.strip() for name in raw_col_d[1:] if name.strip()]
        else:
            name_list = [name.strip() for name in raw_col_d if name.strip()]

    except Exception as e:
        print("❌ Error loading name_list:", e)

    # 🔍 Final print
    print("✅ Final name_list used in template:", name_list)
    # DEBUG: Write name_list to file
    try:
        with open("attendance_name_debug.txt", "w", encoding="utf-8") as f:
            f.write("Name list from Column D (Dropdownlist):\n")
            for i, name in enumerate(name_list, 1):
                f.write(f"{i}. {name}\n")
    except Exception as file_err:
        print("❌ Failed to write debug file:", file_err)

    return render_template(
        'attendance.html',
        user=session['user'],
        name_list=name_list
    )

# ✅ Check-In Handler (protected)
@attendance_bp.route('/checkin', methods=['POST'])
@login_required
def check_in():
    name = request.form.get('name')
    staff_id = request.form.get('staff_id')
    submitted_by = session['user']['name']

    success = save_attendance_checkin(staff_id, name, submitted_by)
    flash('Checked in successfully!' if success else 'Check-in failed.')
    return redirect(url_for('attendance_bp.attendance'))


# ✅ Check-Out Handler (protected)
@attendance_bp.route('/checkout', methods=['POST'])
@login_required
def check_out():
    name = request.form.get('name')
    staff_id = request.form.get('staff_id')
    submitted_by = session['user']['name']

    success = save_attendance_checkout(staff_id, name, submitted_by)
    flash('Checked out successfully!' if success else 'Check-out failed.')
    return redirect(url_for('attendance_bp.attendance'))

# ✅ Attendance Report Page (protected)
@attendance_bp.route('/report', methods=['GET'])
@login_required
def attendance_report():
    return render_template('attendance_report.html')

# ✅ Export Handler (protected)
@attendance_bp.route('/export/<format>', methods=['POST'])
@login_required
def export_attendance(format):
    try:
        filters = request.form.to_dict()
        names = request.form.getlist("names")
        summary = filters.get("view", "") == "summary"  # 🔁 Add a toggle in frontend

        start = filters.get("start")
        end = filters.get("end")

        if summary:
            result = export_attendance_summary(format, start, end, names)
        else:
            result = export_attendance_data(format, start, end, names)

        if not result:
            flash("❌ No data found for export.", "warning")
            return redirect(url_for('attendance_bp.attendance_report'))

        file_data, filename, mimetype = result
        return send_file(io.BytesIO(file_data), as_attachment=True, download_name=filename, mimetype=mimetype)

    except Exception as e:
        flash(f"❌ Export failed: {e}", "danger")
        return redirect(url_for('attendance_bp.attendance_report'))
