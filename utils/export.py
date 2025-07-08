import io
import pandas as pd
from datetime import datetime, timedelta
from config import spreadsheet
from utils.pdf_renderer import generate_report_pdf
from utils.excel_renderer import generate_excel_report

LOGO_PATH = "D:/Projects/ansarhospital/kiratpur/static/images/logo_clinic.png"

def export_attendance_data(format, start_date, end_date, names):
    try:
        if not start_date or not end_date:
            raise ValueError("Start date and end date are required.")

        sheet = spreadsheet.worksheet("Attendance")
        rows = sheet.get_all_values()[1:]

        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        clean_names = [n.strip().lower() for n in names] if names else []

        filtered = []
        for row in rows:
            try:
                checkin = row[3].strip() if len(row) > 3 else ""
                name = row[2].strip() if len(row) > 2 else ""
                if not checkin:
                    continue
                checkin_dt = datetime.strptime(checkin, "%d/%m/%Y %H:%M:%S").date()
                if not (start_dt <= checkin_dt <= end_dt):
                    continue
                if clean_names and name.lower() not in clean_names:
                    continue
                filtered.append({
                    "id": row[1],
                    "name": name,
                    "checkin": checkin,
                    "checkout": row[4] if len(row) > 4 else '',
                    "status": row[5] if len(row) > 5 else 'ABSENT',
                    "submitted_by": row[6] if len(row) > 6 else ''
                })
            except Exception as e:
                print("⚠️ Skipping row due to parse error:", e)

        if not filtered:
            raise ValueError("No records found.")

        headers = ["#", "ID", "Name", "Check-In", "Check-Out", "Status", "Submitted By"]
        rows_out = [
            [i + 1, r["id"], r["name"], r["checkin"], r["checkout"], r["status"], r["submitted_by"]]
            for i, r in enumerate(filtered)
        ]
        fname = f"Attendance_Report_{start_date}_to_{end_date}"

        if format == "excel":
            data = generate_excel_report(headers, rows_out, title="Attendance Report", sheet_name="Attendance")
            return data, f"{fname}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif format == "pdf":
            pdf = generate_report_pdf(
                title="ANSAR HOSPITAL",
                subtitle="Attendance Report",
                start_date=start_date,
                end_date=end_date,
                headers=headers,
                rows=rows_out,
                logo_path=LOGO_PATH
            )
            return pdf, f"{fname}.pdf", "application/pdf"
        else:
            raise ValueError("Unsupported format.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("❌ Attendance export failed:", e)
        return None

def export_attendance_summary(format, start_date, end_date, names):
    try:
        if not start_date or not end_date:
            raise ValueError("Start date and end date are required.")

        sheet = spreadsheet.worksheet("Attendance")
        raw_rows = sheet.get_all_values()[1:]

        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()

        # Build complete date range
        date_range = []
        cursor = start_dt
        while cursor <= end_dt:
            date_range.append(cursor)
            cursor += timedelta(days=1)

        # Extract available names if not specified
        clean_names = [n.strip() for n in names if n.strip()] if names else sorted({
            r[2].strip() for r in raw_rows if len(r) > 2 and r[2].strip()
        })

        summary = []
        for name in clean_names:
            row = [name]
            total_p = 0
            for d in date_range:
                found = False
                for r in raw_rows:
                    try:
                        if len(r) < 4 or not r[3]:
                            continue
                        if r[2].strip().lower() == name.lower():
                            checkin_dt = datetime.strptime(r[3], "%d/%m/%Y %H:%M:%S").date()
                            if checkin_dt == d:
                                found = True
                                break
                    except Exception as e:
                        print("⚠️ Skipping row due to error:", r, "|", e)
                        continue

                row.append("P" if found else "A")
                total_p += int(found)
            total_a = len(date_range) - total_p
            row += [total_p, total_a]
            summary.append(row)

        day_nums = [d.strftime("%d") for d in date_range]
        day_names = [d.strftime("%a") for d in date_range]
        headers = ["Name"] + day_nums + ["Total P", "Total A"]
        filename = f"Attendance_Summary_{start_date}_to_{end_date}"

        if format == "excel":
            output = io.BytesIO()
            df = pd.DataFrame(summary, columns=["Name"] + day_nums + ["Total P", "Total A"])
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name="Summary", startrow=2, header=False)
                wb = writer.book
                ws = writer.sheets["Summary"]

                title_fmt = wb.add_format({'bold': True, 'font_size': 14, 'align': 'center'})
                ws.merge_range(0, 0, 0, len(headers) - 1, "ANSAR HOSPITAL", title_fmt)
                subtitle_fmt = wb.add_format({'italic': True, 'font_size': 11, 'align': 'center'})
                ws.merge_range(1, 0, 1, len(headers) - 1, f"Attendance Summary: {start_date} to {end_date}", subtitle_fmt)

                header_fmt = wb.add_format({'bold': True, 'font_size': 12, 'bg_color': '#d9d9d9',
                                            'border': 1, 'align': 'center', 'valign': 'vcenter'})
                for col, col_name in enumerate(headers):
                    ws.write(2, col, col_name, header_fmt)
                    ws.set_column(col, col, 8 if col != 0 else 16)

                for i, day in enumerate(day_names):
                    ws.write(3, i + 1, day, header_fmt)
                ws.write(3, 0, "", header_fmt)
                ws.write(3, len(day_names) + 1, "", header_fmt)
                ws.write(3, len(day_names) + 2, "", header_fmt)

                cell_fmt = wb.add_format({'font_size': 10, 'align': 'center'})
                for row_idx, row_data in enumerate(summary, start=4):
                    for col_idx, val in enumerate(row_data):
                        ws.write(row_idx, col_idx, val, cell_fmt)

            output.seek(0)
            return output.read(), f"{filename}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        elif format == "pdf":
            pdf = generate_report_pdf(
                title="ANSAR HOSPITAL",
                subtitle="Attendance Summary",
                start_date=start_date,
                end_date=end_date,
                headers=headers,
                rows=summary,
                logo_path=LOGO_PATH
            )
            return pdf, f"{filename}.pdf", "application/pdf"
        else:
            raise ValueError("Unsupported format.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("❌ Summary export failed:", e)
        return None

from utils.export_utils import export_opd_data

__all__ = [
    "export_attendance_data",
    "export_attendance_summary",
    "export_opd_data"
]
