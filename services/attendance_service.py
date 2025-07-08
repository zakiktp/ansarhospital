import io
import pandas as pd
from flask import send_file, render_template
from datetime import datetime
from weasyprint import HTML
from utils.sheet_utils import get_attendance_sheet


def get_attendance_data_filtered(filters):
    sheet = get_attendance_sheet()
    all_records = sheet.get_all_records()

    # Filter logic
    def matches(record):
        if filters.get("name") and filters["name"].lower() not in record["Name"].lower():
            return False
        if filters.get("from_date") and filters.get("to_date"):
            date_fmt = "%d/%m/%Y"
            rec_date = datetime.strptime(record["Date"], date_fmt)
            from_date = datetime.strptime(filters["from_date"], date_fmt)
            to_date = datetime.strptime(filters["to_date"], date_fmt)
            if not (from_date <= rec_date <= to_date):
                return False
        return True

    return list(filter(matches, all_records))


def export_to_excel(data):
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Attendance Report')
        writer.close()
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="attendance_report.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


import os

def export_to_pdf(data):
    context = {
        'data': data,
        'now': datetime.now().strftime('%d-%m-%Y %H:%M'),
        'logo_url': os.path.abspath('static/images/logo_clinic.png')  # or use full URL if deployed
    }
    html_content = render_template("attendance_report_pdf.html", **context)
    pdf_file = HTML(string=html_content, base_url=".").write_pdf()
    return send_file(io.BytesIO(pdf_file), download_name="attendance_report.pdf", as_attachment=True, mimetype="application/pdf")


def get_staff_list():
    db_sheet = get_attendance_sheet("Dropdownlist")
    return db_sheet.col_values(1)[1:]  # Skip header


def save_attendance_checkin(staff_id, name, submitted_by):
    try:
        sheet = get_attendance_sheet()
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        row = ["", datetime.now().strftime("%d/%m/%Y"), name.upper(), staff_id, now, "", "PRESENT", submitted_by]
        sheet.append_row(row)
        return True
    except Exception as e:
        print("Check-in error:", e)
        return False


def save_attendance_checkout(staff_id, name, submitted_by):
    try:
        sheet = get_attendance_sheet()
        data = sheet.get_all_values()
        for idx in range(len(data) - 1, 0, -1):  # Reverse search
            if data[idx][2].strip().lower() == name.strip().lower() and not data[idx][5]:
                sheet.update_cell(idx + 1, 6, datetime.now().strftime("%d/%m/%Y %H:%M:%S"))  # Col F: Checkout
                return True
        return False
    except Exception as e:
        print("Check-out error:", e)
        return False


def get_attendance_sheet(sheet_name="Attendance"):
    from config import spreadsheet
    return spreadsheet.worksheet(sheet_name)

# ------------- for attendance confirmation mail ---------

from config import spreadsheet
from datetime import datetime

def get_last_checkin(name):
    try:
        sheet = spreadsheet.worksheet("Attendance")
        rows = sheet.get_all_values()[1:]  # Skip header

        # Filter rows where name matches (case-insensitive)
        name = name.strip().lower()
        relevant_rows = [
            r for r in rows
            if len(r) >= 4 and r[2].strip().lower() == name and r[3].strip()
        ]

        if not relevant_rows:
            return None

        # Sort by Check-In datetime descending
        def parse_dt(r):
            return datetime.strptime(r[3].strip(), "%d/%m/%Y %H:%M:%S")
        
        latest_row = sorted(relevant_rows, key=parse_dt, reverse=True)[0]

        return {
            "id": latest_row[1],
            "name": latest_row[2],
            "checkin": latest_row[3],
            "checkout": latest_row[4] if len(latest_row) > 4 else "",
            "status": latest_row[5] if len(latest_row) > 5 else "",
            "submitted_by": latest_row[6] if len(latest_row) > 6 else ""
        }
    except Exception as e:
        print("❌ Failed to fetch last check-in:", e)
        return None