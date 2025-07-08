from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from utils.auth_utils import login_required
from utils.sheet_utils import append_to_google_sheet, read_from_google_sheet, get_sheet_service, read_sheet_as_dict
from utils.export_utils import export_opd_data
from datetime import datetime

opd_bp = Blueprint("opd", __name__, url_prefix="/opd")

SHEET_NAME = "OPD"
SHEET_HEADERS = ["Timestamp", "Name", "F/H Name", "ID", "Age", "DOB", "Gender", "Address", "Mobile", "Fee Recd", "Submitted By", "Doctor"]

@opd_bp.route("/", methods=["GET", "POST"])
@login_required
def opd_entry():
    username = session["user"]["name"]

    if request.method == "POST":
        form = request.form
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        new_row = [
            "",  # NO (auto-generated in sheet)
            now,
            form.get("name"),
            form.get("fh_name"),
            form.get("patient_id", ""),
            form.get("age"),
            form.get("dob"),
            form.get("sex"),
            form.get("address"),
            form.get("mobile"),
            form.get("fee"),
            username,
            form.get("doctor")
        ]
        append_to_google_sheet(SHEET_NAME, new_row)
        flash("OPD entry saved successfully", "success")
        return redirect(url_for("opd.opd_entry"))

    # GET: Load and filter records
    records = read_from_google_sheet(SHEET_NAME)
    header = records[0]
    data = records[1:]

    search = request.args.get("search_name", "").lower()
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    doctor_filter = request.args.get("doctor", "")

    def record_matches(r):
        match = True
        if search:
            match &= any(search in str(r[i]).lower() for i in [2, 3, 4, 8, 9])
        if start_date:
            try:
                match &= datetime.strptime(r[1][:10], "%d/%m/%Y") >= datetime.strptime(start_date, "%Y-%m-%d")
            except: pass
        if end_date:
            try:
                match &= datetime.strptime(r[1][:10], "%d/%m/%Y") <= datetime.strptime(end_date, "%Y-%m-%d")
            except: pass
        if doctor_filter:
            match &= doctor_filter.strip().lower() == r[12].strip().lower()
        return match

    filtered = [dict(zip(header, row)) for row in data if record_matches(row)]

    return render_template("opd.html", opd_records=filtered, address_list=["RAJPUR", "SHEESHGRAN", "MUGHLAIN"], username=username)

@opd_bp.route("/export/<format>")
@login_required
def export_opd_data_route(format):
    service, spreadsheet_id = get_sheet_service()
    all_records = read_sheet_as_dict(service, spreadsheet_id, SHEET_NAME, SHEET_HEADERS)

    search = request.args.get("search_name", "").lower()
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    doctor_filter = request.args.get("doctor", "")

    filtered = []
    for row in all_records:
        include = True
        if search:
            include &= any(search in str(row.get(k, "")).lower() for k in ["Name", "F/H Name", "ID", "Mobile", "Address"])
        if include and start_date:
            try:
                include &= datetime.strptime(row["Timestamp"][:10], "%d/%m/%Y") >= datetime.strptime(start_date, "%Y-%m-%d")
            except: pass
        if include and end_date:
            try:
                include &= datetime.strptime(row["Timestamp"][:10], "%d/%m/%Y") <= datetime.strptime(end_date, "%Y-%m-%d")
            except: pass
        if include and doctor_filter:
            include &= doctor_filter.strip().lower() == row.get("Doctor", "").strip().lower()

        if include:
            filtered.append(row)

    return export_opd_data(filtered, SHEET_HEADERS, format=format)
