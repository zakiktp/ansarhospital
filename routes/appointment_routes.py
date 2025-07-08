from flask import Blueprint, request, jsonify
from config import spreadsheet
from datetime import datetime
import pytz

appointment_api_bp = Blueprint('appointment_api', __name__, url_prefix='/api')

@appointment_api_bp.route('/save_appointment', methods=['POST'])
def save_appointment():
    # your implementation
    try:
        data = request.json
        print("📥 Received appointment data:", data)

        sheet = spreadsheet.worksheet("Appointment")
        timestamp = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%d/%m/%Y, %H:%M:%S")

        # Format DOB
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

        from utils.email_sender import send_appointment_confirmation_email
        send_appointment_confirmation_email(data, row)

        return jsonify({"success": True})

    except Exception as e:
        print(f"🔥 Error saving appointment: {e}")
        return jsonify({"error": str(e)}), 500


@appointment_api_bp.route('/test', methods=['GET'])
def test_route():
    return jsonify({"message": "working!"})