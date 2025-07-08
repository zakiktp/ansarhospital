from flask import Blueprint, request, jsonify
from config import spreadsheet
from datetime import datetime
import pytz


print("🚀 patient_api.py is being executed")

patient_api_bp = Blueprint('patient_api', __name__, url_prefix='/api')

@patient_api_bp.route('/patient_lookup', methods=['GET'])
def patient_lookup():
    q = request.args.get('id', '').strip().lower()
    print(f"🔍 Lookup query: {q}")

    if not q or len(q) < 2:
        return jsonify([])

    try:
        sheet = spreadsheet.worksheet("Patient")
        records = sheet.get_all_records()
        results = []

        for row in records:
            # Lowercase and strip for all searchable fields
            name = str(row.get('Name', '')).strip().lower()
            hf_name = str(row.get('H/F Name', '')).strip().lower()
            mobile = str(row.get('Mobile', '')).strip()
            address = str(row.get('Address', '')).strip().lower()
            city = str(row.get('City', '')).strip().lower()

            # Check if query matches any field
            if (
                q in name or
                q in hf_name or
                q in mobile or
                q in address or
                q in city
            ):
                results.append({
                    "id": row.get('ID', '') or row.get('No', '') or row.get('id', ''),
                    "name": row.get('Name', ''),
                    "hf_name": row.get('H/F Name', ''),
                    "mobile": row.get('Mobile', ''),
                    "age": row.get('Age', ''),
                    "dob": row.get('DOB', ''),
                    "prefix": row.get('Prefix', ''),
                    "title": row.get('Title', ''),
                    "gender": "Male" if row.get('Gender') == "M" else "Female" if row.get('Gender') == "F" else "",
                    "address": row.get('Address', ''),
                    "city": row.get('City', ''),
                    "blood_group": row.get('B.Group', ''),
                    "doctor": row.get('Doctor', '')
                })

        print(f"✅ Matches found: {len(results)}")
        return jsonify(results[:10])  # Return top 10 matches

    except Exception as e:
        print(f"🔥 Error during lookup: {e}")
        return jsonify({"error": str(e)}), 500


@patient_api_bp.route('/next_patient_id')
def next_patient_id():
    try:
        sheet = spreadsheet.worksheet("Patient")
        ids = [row[0] for row in sheet.get_all_values()[1:] if row and row[0].startswith("AH")]

        if not ids:
            return jsonify({"next_id": "AH0001"})

        # Extract numeric part and find max
        numbers = [int(id[2:]) for id in ids if id[2:].isdigit()]
        max_number = max(numbers) if numbers else 0
        next_number = max_number + 1
        next_id = f"AH{next_number:04d}"

        return jsonify({"next_id": next_id})
    except Exception as e:
        print(f"❌ Error getting next ID: {e}")
        return jsonify({"error": str(e)}), 500


@patient_api_bp.route('/save_patient', methods=['POST'])
def save_patient():
    try:
        data = request.json
        print("📥 Saving patient:", data)

        sheet = spreadsheet.worksheet("Patient")
        all_rows = sheet.get_all_values()
        existing_ids = set(row[0].strip().upper() for row in all_rows[1:] if row and row[0].startswith("AH"))
        new_id = data.get("id", "").strip().upper()

        if new_id in existing_ids:
            print(f"⚠️ Patient ID {new_id} already exists. Skipping save.")
            return jsonify({"message": f"Patient ID {new_id} already exists. Skipped."}), 200

        # Format DOB
        dob_raw = data.get("dob", "").strip()
        if "-" in dob_raw:
            try:
                dob = datetime.strptime(dob_raw, "%Y-%m-%d").strftime("%d/%m/%Y")
            except:
                dob = dob_raw
        else:
            dob = dob_raw

        # Final address to store
        final_address = data.get("address")
        if final_address == "OTHER":
            final_address = data.get("new_address", "").strip().upper()

        # Prepare row with only required fields
        row = [
            new_id,
            data.get("prefix", ""),
            data.get("name", ""),
            data.get("title", ""),
            data.get("hf_name", ""),
            data.get("mobile", ""),
            final_address,
            data.get("city", ""),
            data.get("age", ""),
            data.get("gender", ""),
            dob
        ]

        # Append to Patient sheet
        sheet.append_row(row)
        print("✅ New patient saved:", row)

        # ✅ Save new address to Dropdownlist if applicable
        if data.get("address") == "OTHER" and final_address:
            try:
                dropdown_sheet = spreadsheet.worksheet("Dropdownlist")
                all_rows = dropdown_sheet.get_all_values()

                # Extract and deduplicate existing addresses from column A
                current_addresses = set(row[0].strip().upper() for row in all_rows if row and row[0].strip())

                if final_address not in current_addresses:
                    print(f"✅ New address to be added: {final_address}")
                    dropdown_sheet.append_row([final_address])  # Add to Column A

                    # Fetch updated values again
                    updated_rows = dropdown_sheet.get_all_values()

                    # Extract and sort only column A
                    addresses = sorted(set(row[0].strip().upper() for row in updated_rows if row and row[0].strip()))

                    # Update column A with sorted addresses
                    for i, addr in enumerate(addresses, start=2):  # Start at row 2 (skip header if any)
                        dropdown_sheet.update_cell(i, 1, addr)

                    print("🔤 Column A sorted safely without clearing other columns.")
            except Exception as addr_err:
                print("⚠️ Failed to save/sort address:", addr_err)


                return jsonify({"success": True}), 200

    except Exception as e:
        print(f"❌ Failed to save patient: {e}")
    return jsonify({"error": str(e)}), 500
