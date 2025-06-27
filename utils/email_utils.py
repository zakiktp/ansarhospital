import os
import gspread
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from google.oauth2.service_account import Credentials

# Step 1: Get Appointment Data from Google Sheet
def get_appointments_from_sheet():
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    SERVICE_ACCOUNT_FILE = "path/to/your/service_account.json"

    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)

    sheet = client.open("Database").worksheet("Appointment")
    data = sheet.get_all_values()

    appointments = []
    for row in data[1:]:  # Skip header
        if len(row) >= 7:
            appointments.append({
                "date": row[1],
                "name": row[2],
                "fh_name": row[3],
                "address": row[4],
                "mobile": row[5],
                "staff": row[6]
            })
    return appointments

# Step 2: Format Appointments into Email Table
def format_email_content(appointments):
    if not appointments:
        return "<p>No appointment data available.</p>"

    html = """
    <h3>🩺 Appointment Summary</h3>
    <table border='1' cellpadding='6' cellspacing='0'>
        <tr>
            <th>Date</th><th>Name</th><th>F/H Name</th><th>Address</th><th>Mobile</th><th>Staff</th>
        </tr>"""
    for appt in appointments:
        html += f"""
        <tr>
            <td>{appt['date']}</td>
            <td>{appt['name']}</td>
            <td>{appt['fh_name']}</td>
            <td>{appt['address']}</td>
            <td>{appt['mobile']}</td>
            <td>{appt['staff']}</td>
        </tr>"""
    html += "</table>"
    return html

# Step 3: Send Email

import os
import base64
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To

def send_mail(to_email, data):
    print("📩 send_mail() triggered")

    from_email = os.getenv("EMAIL_SENDER")
    from_name = os.getenv("EMAIL_SENDER_NAME", "Ansar Hospital")
    api_key = os.getenv("SENDGRID_API_KEY")

    if not (api_key and from_email):
        print("❌ Missing SENDGRID_API_KEY or EMAIL_SENDER in environment.")
        return False

    # Appointment details
    name = data.get("name", "N/A")
    hf_name = data.get("hf_name", "N/A")
    address = data.get("address", "N/A")
    staff = data.get("staff", "N/A")
    number = data.get("number", "N/A")
    timestamp = datetime.now().strftime('%d/%m/%Y, %H:%M:%S')

    # Logo path (relative to project)
    logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'images', 'logo_clinic.png'))

    # Attempt to embed logo
    try:
        with open(logo_path, "rb") as image_file:
            logo_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            logo_html = f"""
            <div style="text-align: center; margin-bottom: 10px;">
                <img src="data:image/png;base64,{logo_base64}" alt="ANSAR HOSPITAL" style="height:60px;" />
                <h2 style="margin: 0; color: #006400;">ANSAR HOSPITAL</h2>
            </div>
            """
    except Exception as e:
        print(f"⚠️ Logo load failed: {e}")
        logo_html = """
        <div style="text-align: center; margin-bottom: 10px;">
            <h2 style="color: #006400;">ANSAR HOSPITAL</h2>
        </div>
        """

    subject = "Appointment Confirmation - Ansar Hospital"

    plain_text = f"""
ANSAR HOSPITAL - Appointment Confirmation

No: {number}
Date: {timestamp}
Name: {name}
H/F Name: {hf_name}
Address: {address}
Staff: {staff}

Thank you,
Ansar Hospital
Kiratpur, Bijnor UP
"""

    html_content = f"""
<html>
  <body style="font-family: Arial, sans-serif;">
    <div style="max-width: 600px; margin: auto; border: 1px solid #ddd; padding: 20px;">
      {logo_html}
      <h3 style="text-align: center; color: #006400;">Appointment Confirmation</h3>
      <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
        <tr style="background-color: #f2f2f2;">
          <th style="border: 1px solid #ccc; padding: 8px;">Field</th>
          <th style="border: 1px solid #ccc; padding: 8px;">Details</th>
        </tr>
        <tr><td style="border: 1px solid #ccc; padding: 8px;">No</td><td style="border: 1px solid #ccc; padding: 8px;">{number}</td></tr>
        <tr><td style="border: 1px solid #ccc; padding: 8px;">Date</td><td style="border: 1px solid #ccc; padding: 8px;">{timestamp}</td></tr>
        <tr><td style="border: 1px solid #ccc; padding: 8px;">Name</td><td style="border: 1px solid #ccc; padding: 8px;">{name}</td></tr>
        <tr><td style="border: 1px solid #ccc; padding: 8px;">H/F Name</td><td style="border: 1px solid #ccc; padding: 8px;">{hf_name}</td></tr>
        <tr><td style="border: 1px solid #ccc; padding: 8px;">Address</td><td style="border: 1px solid #ccc; padding: 8px;">{address}</td></tr>
        <tr><td style="border: 1px solid #ccc; padding: 8px;">Staff</td><td style="border: 1px solid #ccc; padding: 8px;">{staff}</td></tr>
      </table>
      <p style="font-size: 12px; color: #555; margin-top: 20px; text-align: center;">
        This message was sent by <strong>Ansar Hospital</strong>, Dargopur Nangli.<br>
        If you did not request this appointment, please reply to this email.
      </p>
    </div>
  </body>
</html>
"""

    try:
        message = Mail(
            from_email=Email(from_email, from_name),
            to_emails=To(to_email),
            subject=subject,
            plain_text_content=plain_text,
            html_content=html_content
        )
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        print(f"✅ Email sent to {to_email} | Status: {response.status_code}")
        return response.status_code in (200, 202)
    except Exception as e:
        print(f"❌ Email send error: {e}")
        return False
