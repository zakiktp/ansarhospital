from flask import Blueprint, render_template, request, redirect, url_for, flash, session, Response
from config import spreadsheet
from datetime import datetime
import pytz
from utils.auth_utils import login_required
from utils.email_sender import send_attendance_confirmation

attendance_bp = Blueprint("attendance_bp", __name__, url_prefix="/attendance")

@attendance_bp.route('/')
@login_required
def attendance():
    staff_entries = []
    records = []

    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)
    current_date_str = now.strftime('%Y-%m-%d')
    selected_date = request.args.get('date', current_date_str)

    try:
        dropdown_sheet = spreadsheet.worksheet("Dropdownlist")
        ids = dropdown_sheet.col_values(3)
        names = dropdown_sheet.col_values(4)

        if names and names[0].strip().lower() == "name":
            ids, names = ids[1:], names[1:]

        for name, sid in zip(names, ids):
            label = f"{name.strip()} ({sid.strip()})"
            staff_entries.append({
                "label": label,
                "value": label,
                "name": name.strip(),
                "id": sid.strip()
            })

        attendance_sheet = spreadsheet.worksheet("Attendance")
        all_rows = attendance_sheet.get_all_values()[1:]  # Skip header

        for row in all_rows:
            if len(row) >= 4 and row[3].strip():
                try:
                    checkin_dt = datetime.strptime(row[3], '%d/%m/%Y %H:%M:%S')
                    checkin_date = checkin_dt.strftime('%Y-%m-%d')

                    if checkin_date == selected_date:
                        records.append({
                            'id': row[1],
                            'name': row[2],
                            'checkin': row[3],
                            'checkout': row[4] if len(row) > 4 else '',
                            'status': row[5] if len(row) > 5 else '',
                            'submitted_by': row[6] if len(row) > 6 else '',
                        })
                except Exception as e:
                    print(f"❌ Date parsing error: {e} — row: {row}")

    except Exception as e:
        print("❌ Error loading data:", e)

    return render_template(
        "attendance.html",
        staff_entries=staff_entries,
        username=session['user']['name'],
        records=records,
        selected_date=selected_date
    )

@attendance_bp.route('/checkin', methods=['POST'])
@login_required
def check_in():
    try:
        full_combo = request.form.get('staff_combo')
        submitted_by = request.form.get('submitted_by')

        now = datetime.now(pytz.timezone("Asia/Kolkata"))
        current_date = now.strftime('%Y-%m-%d')
        selected_date = request.args.get('date', current_date)

        if selected_date != current_date:
            flash("⚠️ Check-In allowed only for today.")
            return redirect(url_for('attendance_bp.attendance', date=selected_date))

        if not full_combo or '(' not in full_combo or ')' not in full_combo:
            flash("❌ Invalid selection.")
            return redirect(url_for('attendance_bp.attendance', date=selected_date))

        name = full_combo.split('(')[0].strip()
        staff_id = full_combo.split('(')[1].replace(')', '').strip()

        sheet = spreadsheet.worksheet("Attendance")
        data = sheet.get_all_values()
        timestamp = now.strftime('%d/%m/%Y %H:%M:%S')

        for row in data[1:]:
            if len(row) >= 3 and row[1].strip() == staff_id and row[2].strip() == name and row[3].strip():
                if datetime.strptime(row[3], '%d/%m/%Y %H:%M:%S').strftime('%Y-%m-%d') == current_date:
                    flash("⚠️ Already checked in.")
                    return redirect(url_for('attendance_bp.attendance', date=selected_date))

        next_row = len(data) + 1
        serial_no = next_row - 1
        row_data = [serial_no, staff_id, name, timestamp, '', 'PRESENT', submitted_by]
        sheet.append_row(row_data)
        flash("✅ Check-in recorded.")

        # ✅ Send Check-In Confirmation Email
        try:
            send_attendance_confirmation(
                name=name,
                emp_id=staff_id,
                checkin=timestamp,
                checkout="—",
                status="Present",
                submitted_by=submitted_by,
                event_type="Check-In"
            )
        except Exception as e:
            print("⚠️ Email send failed (Check-In):", e)

    except Exception as e:
        print("❌ Check-in Error:", e)
        flash("❌ Error during check-in.")

    return redirect(url_for('attendance_bp.attendance', date=selected_date))


@attendance_bp.route('/checkout', methods=['POST'])
@login_required
def check_out():
    try:
        full_combo = request.form.get('staff_combo')
        submitted_by = request.form.get('submitted_by')

        now = datetime.now(pytz.timezone("Asia/Kolkata"))
        current_date = now.strftime('%Y-%m-%d')
        selected_date = request.args.get('date', current_date)

        if selected_date != current_date:
            flash("⚠️ Check-Out allowed only for today.")
            return redirect(url_for('attendance_bp.attendance', date=selected_date))

        if not full_combo or '(' not in full_combo or ')' not in full_combo:
            flash("❌ Invalid selection.")
            return redirect(url_for('attendance_bp.attendance', date=selected_date))

        name = full_combo.split('(')[0].strip()
        staff_id = full_combo.split('(')[1].replace(')', '').strip()

        sheet = spreadsheet.worksheet("Attendance")
        data = sheet.get_all_values()
        timestamp = now.strftime('%d/%m/%Y %H:%M:%S')

        updated = False
        for i, row in enumerate(data[1:], start=2):
            if len(row) >= 3 and row[1].strip() == staff_id and row[2].strip() == name:
                checkin_date = datetime.strptime(row[3], '%d/%m/%Y %H:%M:%S').strftime('%Y-%m-%d')
                if checkin_date == current_date:
                    if len(row) >= 5 and row[4].strip():
                        flash("⚠️ Already checked out.")
                        return redirect(url_for('attendance_bp.attendance', date=selected_date))
                    elif len(row) >= 4 and row[3].strip():
                        sheet.update_cell(i, 5, timestamp)
                        flash("✅ Check-out recorded.")
                        updated = True
                        break

        if not updated:
            flash("⚠️ No matching check-in found or check-in is missing.")
        # ✅ Send Check-Out Confirmation Email
        try:
            updated_row = sheet.row_values(i)  # Re-fetch row after update
            send_attendance_confirmation(
                name=updated_row[2],
                emp_id=updated_row[1],
                checkin=updated_row[3],
                checkout=updated_row[4],
                status=updated_row[5] if len(updated_row) > 5 else "Present",
                submitted_by=submitted_by,
                event_type="Check-Out"
            )
        except Exception as e:
            print("⚠️ Email send failed (Check-Out):", e)

    except Exception as e:
        print("❌ Check-out Error:", e)
        flash("❌ Error during check-out.")

    return redirect(url_for('attendance_bp.attendance', date=selected_date))


@attendance_bp.route('/export/<format>', methods=['POST'])
@login_required
def export_attendance(format):
    try:
        from utils.export import export_attendance_data

        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        names = request.form.get('names', '').split(',') if request.form.get('names') else []

        result = export_attendance_data(format, start_date, end_date, names)

        if not result:
            raise ValueError("Export function returned None")

        file_data, filename, mimetype = result

        return Response(
            file_data,
            mimetype=mimetype,
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )

    except Exception as e:
        print("❌ Export Error:", e)
        flash("❌ Error exporting report.")
        return redirect(url_for('attendance_bp.attendance'))


@attendance_bp.route('/report', methods=['GET', 'POST'])
@login_required
def attendance_report():
    from datetime import datetime
    staff_entries = []

    try:
        dropdown_sheet = spreadsheet.worksheet("Dropdownlist")
        ids = dropdown_sheet.col_values(3)
        names = dropdown_sheet.col_values(4)

        if names and names[0].strip().lower() == "name":
            ids, names = ids[1:], names[1:]

        for name, sid in zip(names, ids):
            label = f"{name.strip()} ({sid.strip()})"
            staff_entries.append({"label": label, "value": label, "name": name.strip(), "id": sid.strip()})

    except Exception as e:
        print("❌ Error loading Dropdownlist:", e)

    return render_template("attendance_report.html",
                           staff_entries=staff_entries,
                           username=session['user']['name'])
