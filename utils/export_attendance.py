import io
import pandas as pd
from config import spreadsheet
from utils.export_core import parse_date, build_date_range, clean_names_list
from utils.pdf_renderer import generate_report_pdf
from utils.excel_renderer import generate_excel_report
from datetime import datetime, timedelta

LOGO_PATH = "D:/Projects/ansarhospital/kiratpur/static/images/logo_clinic.png"

def export_attendance_data(format, start_date, end_date, names):
    try:
        sheet = spreadsheet.worksheet("Attendance")
        rows = sheet.get_all_values()[1:]

        start_dt = parse_date(start_date)
        end_dt = parse_date(end_date)
        clean_names = clean_names_list(names)

        filtered = []
        for row in rows:
            try:
                checkin = row[3].strip()
                name = row[2].strip()
                if not checkin:
                    continue
                checkin_dt = datetime.strptime(checkin, "%d/%m/%Y %H:%M:%S").date()
                if not (start_dt <= checkin_dt <= end_dt):
                    continue
                if clean_names and name.lower() not in clean_names:
                    continue
                filtered.append({
                    "id": row[1], "name": name, "checkin": checkin,
                    "checkout": row[4] if len(row) > 4 else '',
                    "status": row[5] if len(row) > 5 else 'ABSENT',
                    "submitted_by": row[6] if len(row) > 6 else ''
                })
            except: continue

        if not filtered:
            raise ValueError("No records found.")

        headers = ["#", "ID", "Name", "Check-In", "Check-Out", "Status", "Submitted By"]
        rows_out = [
            [i+1, r["id"], r["name"], r["checkin"], r["checkout"], r["status"], r["submitted_by"]]
            for i, r in enumerate(filtered)
        ]
        fname = f"Attendance_Report_{start_date}_to_{end_date}"

        if format == "excel":
            data = generate_excel_report(headers, rows_out, title="Attendance Report", sheet_name="Attendance")
            return data, f"{fname}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            pdf = generate_report_pdf(
                title="ANSAR HOSPITAL", subtitle="Attendance Report",
                start_date=start_date, end_date=end_date,
                headers=headers, rows=rows_out, logo_path=LOGO_PATH
            )
            return pdf, f"{fname}.pdf", "application/pdf"
    except Exception as e:
        print("❌ Attendance export error:", e)
        return None

def export_attendance_summary(format, start_date, end_date, names):
    try:
        sheet = spreadsheet.worksheet("Attendance")
        rows = sheet.get_all_values()[1:]

        start_dt = parse_date(start_date)
        end_dt = parse_date(end_date)
        date_range = build_date_range(start_dt, end_dt)

        clean_names = [n.strip() for n in names if n.strip()] if names else sorted({
            r[2].strip() for r in rows if len(r) > 2 and r[2].strip()
        })

        summary = []
        for name in clean_names:
            row = [name]
            total_p = 0
            for d in date_range:
                present = any(
                    r for r in rows if len(r) > 3 and
                    r[2].strip().lower() == name.lower() and
                    datetime.strptime(r[3], "%d/%m/%Y %H:%M:%S").date() == d
                )
                row.append("P" if present else "A")
                total_p += int(present)
            total_a = len(date_range) - total_p
            row.extend([total_p, total_a])
            summary.append(row)

        # Excel-style headers: Two header rows
        day_nums = [d.strftime("%d") for d in date_range]
        day_names = [d.strftime("%a") for d in date_range]
        excel_headers = ["Name"] + day_nums + ["Total P", "Total A"]
        fname = f"Attendance_Summary_{start_date}_to_{end_date}"

        if format == "excel":
            output = io.BytesIO()
            df = pd.DataFrame(summary, columns=["Name"] + day_nums + ["Total P", "Total A"])

            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name="Summary", startrow=2, header=False)

                wb = writer.book
                ws = writer.sheets["Summary"]

                # Title and Subtitle
                title_format = wb.add_format({'bold': True, 'font_size': 14, 'align': 'center'})
                subtitle_format = wb.add_format({'italic': True, 'font_size': 11, 'align': 'center'})
                ws.merge_range(0, 0, 0, len(excel_headers) - 1, "ANSAR HOSPITAL", title_format)
                ws.merge_range(1, 0, 1, len(excel_headers) - 1, f"Attendance Summary: {start_date} to {end_date}", subtitle_format)

                # Header row 1: Date numbers
                header_fmt = wb.add_format({
                    'bold': True, 'font_size': 11, 'bg_color': '#d9d9d9',
                    'border': 1, 'align': 'center', 'valign': 'vcenter'
                })
                for col, col_name in enumerate(excel_headers):
                    ws.write(2, col, col_name, header_fmt)
                    ws.set_column(col, col, 12 if col == 0 else 8)

                # Header row 2: Day names (skip Total P/A columns)
                for i, day in enumerate(day_names):
                    ws.write(3, i + 1, day, header_fmt)  # +1 to skip "Name" column
                ws.write(3, 0, "", header_fmt)
                ws.write(3, len(day_names) + 1, "", header_fmt)
                ws.write(3, len(day_names) + 2, "", header_fmt)

                # Format body
                cell_fmt = wb.add_format({'font_size': 10, 'align': 'center'})
                for row_idx, row_data in enumerate(summary, start=4):
                    for col_idx, val in enumerate(row_data):
                        ws.write(row_idx, col_idx, val, cell_fmt)

            output.seek(0)
            return output.read(), f"{fname}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        else:
            # PDF headers = ["Name", "01", "02", ..., "Total P", "Total A"]
            headers = ["Name"] + day_nums + ["Total P", "Total A"]
            pdf = generate_report_pdf(
                title="ANSAR HOSPITAL",
                subtitle="Attendance Summary",
                start_date=start_date,
                end_date=end_date,
                headers=headers,
                rows=summary,
                logo_path=LOGO_PATH
            )
            return pdf, f"{fname}.pdf", "application/pdf"

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("❌ Summary export error:", e)
        return None