from flask import Blueprint, request, jsonify
from utils.sheet_utils import find_patients_by_name

patients_bp = Blueprint("patients", __name__)

@patients_bp.route("/patients/search", methods=["GET"])
def search_patients():
    name = request.args.get("name", "").strip()
    if not name:
        return jsonify([])

    matches = find_patients_by_name(name)
    return jsonify(matches)

