from flask import Blueprint, request, jsonify
from config import spreadsheet
from datetime import datetime
import pytz

appointment_api_bp = Blueprint('appointment_api', __name__, url_prefix='/api')
print("✅ appointment_api.py is loaded")

@appointment_api_bp.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "appointment API active"})


@appointment_api_bp.route('/search_appointments', methods=['GET'])
def search_appointments():
    name = request.args.get('name', '').strip().lower()
    hf_name = request.args.get('hf_name', '').strip().lower()
    mobile = request.args.get('mobile', '').strip()
    address = request.args.get('address', '').strip().lower()
    doctor = request.args.get('doctor', '').strip().lower()
    from_date = request.args.get('from_date', '').strip()
    to_date = request.args.get('to_date', '').strip()

    print("🔍 Searching with:", name, hf_name, mobile, address, doctor, from_date, to_date)

    def parse_date(date_str, is_start=True):
        try:
            date_str = date_str.strip()
            if len(date_str) == 10:  # Only date, no time
                date_str += " 00:00:00" if is_start else " 23:59:59"
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print(f"❌ parse_date failed: {date_str} — {e}")
            return None

    def parse_sheet_date(date_str):
        date_str = date_str.strip()
        for fmt in ("%d/%m/%Y, %H:%M:%S", "%d/%m/%Y %H:%M:%S"):
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        print(f"⚠️ Unable to parse sheet date: '{date_str}'")
        return None

    from_dt = parse_date(from_date, is_start=True) if from_date else None
    to_dt = parse_date(to_date, is_start=False) if to_date else None
    print(f"📅 Date Range: {from_dt} to {to_dt}")

    try:
        sheet = spreadsheet.worksheet("Appointment")
        records = sheet.get_all_records()
        results = []

        for row in records:
            match = True

            # Normalize key names
            row["ID"] = row.get("ID") or row.get("Id") or row.get("id") or ""  # ← Add this line
            row["VisitStatus"] = row.get("Status", "").strip().upper()
            if match and not row["ID"]:
                print(f"⚠️ Matched row missing ID: {row}")


            # Normalize fields
            row_name = str(row.get("Name", "")).strip().lower()
            row_hf_name = str(row.get("H/F Name", "")).strip().lower()
            row_mobile = str(row.get("Mobile", "")).strip()
            row_address = str(row.get("Address", "")).strip().lower()
            row_doctor = str(row.get("Doctor", "")).strip().lower()
            row_date_str = str(row.get("Date", "")).strip()

            # Text filters
            if name and name not in row_name:
                match = False
            if hf_name and hf_name not in row_hf_name:
                match = False
            if mobile and mobile not in row_mobile:
                match = False
            if address and address not in row_address:
                match = False
            if doctor and doctor not in row_doctor:
                match = False

            # Date filter
            if from_dt or to_dt:
                appt_dt = parse_sheet_date(row_date_str)
                if not appt_dt:
                    match = False
                else:
                    if from_dt and appt_dt < from_dt:
                        match = False
                    if to_dt and appt_dt > to_dt:
                        match = False

            if match:
                results.append(row)

        print(f"✅ Matched {len(results)} appointments")
        return jsonify(results)

    except Exception as e:
        print(f"❌ Error during search: {e}")
        return jsonify({"error": str(e)}), 500

@appointment_api_bp.route('/save_appointment', methods=['POST'])
def save_appointment():
    try:
        data = request.json
        print("📥 Received appointment data:", data)

        sheet = spreadsheet.worksheet("Appointment")
        timestamp = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%d/%m/%Y, %H:%M:%S")

        dob_raw = data.get("dob", "")
        if "-" in dob_raw:
            try:
                dob = datetime.strptime(dob_raw, "%Y-%m-%d").strftime("%d/%m/%Y")
            except:
                dob = dob_raw
        else:
            dob = dob_raw

        next_id = len(sheet.get_all_values())
        row = [
            next_id,
            timestamp,
            data.get("id"),
            data.get("prefix"),
            data.get("name"),
            data.get("title"),
            data.get("hf_name"),
            data.get("gender"),
            data.get("age"),
            dob,
            data.get("address") if data.get("address") != "OTHER" else data.get("new_address"),
            data.get("mobile"),
            data.get("staff"),
            data.get("status"),
            data.get("doctor")
        ]

        sheet.append_row(row)
        print("✅ Appointment saved:", row)

        # ✅ Send confirmation email
        from utils.email_sender import send_appointment_confirmation_email
        to_email = data.get("email", "").strip()
        if not to_email:
            print("⚠️ No recipient email provided; using fallback.")
            to_email = "zakiup@gmail.com"

        send_appointment_confirmation_email(data, row)
        print(f"📧 Email sent to: {to_email}")

        return jsonify({"success": True}), 200

    except Exception as e:
        print(f"🔥 Error saving appointment: {e}")
        return jsonify({"error": str(e)}), 500
