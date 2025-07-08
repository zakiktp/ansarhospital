from config import spreadsheet
from utils.export_core import parse_date, clean_names_list
from utils.excel_renderer import generate_excel_report
from utils.pdf_renderer import generate_report_pdf

LOGO_PATH = "D:/Projects/ansarhospital/kiratpur/static/images/logo_clinic.png"

def export_opd_data(format, start_date, end_date, names):
    try:
        sheet = spreadsheet.worksheet("OPD")
        rows = sheet.get_all_values()[1:]

        start_dt = parse_date(start_date)
        end_dt = parse_date(end_date)
        clean_names = clean_names_list(names)

        filtered = []
        for row in rows:
            try:
                visit_date = datetime.strptime(row[2], "%d/%m/%Y").date()
                name = row[1].strip()
                if not (start_dt <= visit_date <= end_dt):
                    continue
                if clean_names and name.lower() not in clean_names:
                    continue
                filtered.append({
                    "sl": row[0], "name": name, "date": row[2],
                    "gender": row[3], "age": row[4],
                    "diagnosis": row[5], "doctor": row[6]
                })
            except: continue

        if not filtered:
            raise ValueError("No OPD records in range.")

        headers = ["#", "Name", "Visit Date", "Gender", "Age", "Diagnosis", "Doctor"]
        rows_out = [
            [i + 1, r["name"], r["date"], r["gender"], r["age"], r["diagnosis"], r["doctor"]]
            for i, r in enumerate(filtered)
        ]
        fname = f"OPD_Report_{start_date}_to_{end_date}"

        if format == "excel":
            x = generate_excel_report(headers, rows_out, title="OPD Report", sheet_name="OPD")
            return x, f"{fname}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            pdf = generate_report_pdf(
                title="ANSAR HOSPITAL", subtitle="OPD Report",
                start_date=start_date, end_date=end_date,
                headers=headers, rows=rows_out, logo_path=LOGO_PATH
            )
            return pdf, f"{fname}.pdf", "application/pdf"
    except Exception as e:
        print("❌ OPD export error:", e)
        return None