from config import spreadsheet

def fetch_patient_by_id(patient_id):
    sheet = spreadsheet.worksheet("Patient")
    rows = sheet.get_all_values()[1:]  # Skip header
    for row in rows:
        if row[0].strip() == patient_id:
            return {
                "id": row[0],
                "name": row[1],
                "fh_name": row[2],
                "address": row[3],
                "mobile": row[4],
                "dob": row[5],
                "gender": row[6],
                "created_at": row[7],
            }
    return None

from config import spreadsheet

def search_patients(query):
    """
    Searches the Patient sheet for records matching the given query.
    Supports search by ID, Name, H/F Name, Mobile, Address, and City.
    """
    query = query.strip().lower()
    if not query:
        return []

    sheet = spreadsheet.worksheet("Patient")
    records = sheet.get_all_records()

    matched = []
    for row in records:
        # Searchable fields
        searchable_fields = ["ID", "Name", "H/F Name", "Mobile", "Address", "City"]
        if any(query in str(row.get(field, "")).lower() for field in searchable_fields):
            matched.append({
                "id": row.get("ID", ""),
                "name": row.get("Name", ""),
                "hf_name": row.get("H/F Name", ""),
                "mobile": row.get("Mobile", ""),
                "address": row.get("Address", ""),
                "city": row.get("City", ""),
                "age": row.get("Age", ""),
                "gender": row.get("Gender", ""),
                "blood_group": row.get("B.Group", ""),
                "dob": row.get("DOB", ""),
            })

    return matched


import datetime

def generate_patient_id():
    patient_sheet = spreadsheet.worksheet("Patient")
    last_id = patient_sheet.col_values(1)[-1]  # Last ID in Column 1
    next_id = int(last_id.replace('AH', '')) + 1 if last_id.startswith('AH') else 1
    return f"PT{next_id:04d}"

from flask import jsonify
from config import spreadsheet

def search_patients(query):
    """
    Search for patients in the 'Patient' sheet based on the given query.
    Query can match on 'ID', 'Name', 'H/F Name', 'Mobile', or 'Address'.
    """
    query = query.strip().lower()  # Ensure query is trimmed and lowercased
    if not query:
        return jsonify([])

    # Access the "Patient" sheet in the spreadsheet
    sheet = spreadsheet.worksheet("Patient")
    records = sheet.get_all_records()  # Get all records from the Patient sheet

    matched = []
    for row in records:
        # Search through relevant fields (ID, Name, H/F Name, Mobile, Address)
        if any(
            query in str(row.get(field, "")).lower()
            for field in ["ID", "Name", "H/F Name", "Mobile", "Address"]
        ):
            matched.append({
                "id": row.get("ID", ""),
                "name": row.get("Name", ""),
                "hf_name": row.get("H/F Name", ""),
                "mobile": row.get("Mobile", ""),
                "address": row.get("Address", ""),
                "age": row.get("Age", ""),
                "gender": row.get("Gender", ""),
                "blood_group": row.get("Blood Group", ""),
            })

    return matched
