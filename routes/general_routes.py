# routes/general_routes.py

from flask import Blueprint, request, jsonify
from config import spreadsheet

general_bp = Blueprint("general", __name__)

@general_bp.route('/search-patients', methods=['POST'])
def search_patients():
    try:
        data = request.get_json()
        query = data.get("query", "").strip().lower()

        if not query:
            return jsonify([])

        sheet = spreadsheet.worksheet("Patient")
        records = sheet.get_all_records()

        matched = []
        for row in records:
            # Check all searchable fields
            if any(
                query in str(row.get(field, "")).lower()
                for field in ["ID", "Name", "H/F Name", "Mobile", "Address"]
            ):
                matched.append({
                    "id": row.get("ID", ""),
                    "name": row.get("Name", ""),
                    "hf_name": row.get("H/F Name", ""),
                    "mobile": row.get("Mobile", ""),
                    "address": row.get("Address", "")
                })

        return jsonify(matched[:20])  # Return top 20 matches

    except Exception as e:
        print("❌ Patient search error:", e)
        return jsonify([]), 500

from flask import jsonify, request
from utils.patient_utils import search_patients

@general_bp.route('/search-patients')
def search_patients_route():
    query = request.args.get("q", "")
    return jsonify(search_patients(query))

