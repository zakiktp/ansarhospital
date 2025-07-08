import os
from flask import render_template
from base64 import b64encode
from datetime import datetime
from email.utils import formataddr
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName, FileType, Disposition
)

# ✅ Use pre-loaded .env (no need to reload here if loaded in app.py)
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
EMAIL_SENDER = os.getenv('EMAIL_SENDER', 'info@ansarhospital.com')
EMAIL_SENDER_NAME = os.getenv('EMAIL_SENDER_NAME', 'Ansar Hospital')

# send_otp_email ---------

def send_otp_email(to_email, otp):
    print(f"🧪 Sending OTP: {otp} to {to_email}")
    subject = "🔐 OTP for Password Reset"
    message = f"""
Dear User,

You requested a password reset. Please use the following OTP:

🔐 OTP: {otp}

This OTP is valid for 10 minutes.

If you did not request this, please ignore this email.

Regards,  
{EMAIL_SENDER_NAME}
"""

    email = Mail(
        from_email=(EMAIL_SENDER, EMAIL_SENDER_NAME),
        to_emails=to_email,
        subject=subject,
        plain_text_content=message
    )

    try:
        print(f"🔐 SENDGRID_API_KEY is {'set' if SENDGRID_API_KEY else 'NOT set'}")
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(email)
        print(f"✅ OTP email sent to {to_email}, status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to send OTP email to {to_email}: {e}")
        if hasattr(e, 'body'):
            print(e.body)

# send_opd_confirmation_email

def send_opd_confirmation_email(data):
    try:
        logo_url = "https://i.postimg.cc/Fsjypdtn/logo-clinic.png"  # ✅ Public image link

        msg = Mail(
            from_email=(os.getenv("EMAIL_SENDER"), os.getenv("EMAIL_SENDER_NAME")),
            to_emails=os.getenv("EMAIL_RECEIVER"),
            subject="✅ OPD Submission Confirmation",
            html_content=f"""
            <div style="font-family: Arial, sans-serif; text-align: center;">
              <img src="{logo_url}" alt="Ansar Hospital Logo" style="height:80px; margin-bottom:10px;" />
              <h2 style="color: #02457A;">ANSAR HOSPITAL</h2>
              <h4 style="margin-bottom: 20px; color: #555;">🩺 OPD Record Submitted</h4>

              <table align="center" cellpadding="10" cellspacing="0" border="1" style="margin:auto; border-collapse: collapse; font-size: 14px; width: 80%;">
                <tr><td style="font-weight:bold; background:#f0f4fa;">NO</td><td>{data.get('no')}</td></tr>
                <tr><td style="font-weight:bold; background:#f0f4fa;">Date</td><td>{data.get('date')}</td></tr>
                <tr><td style="font-weight:bold; background:#f0f4fa;">Name</td><td>{data.get('name')}</td></tr>
                <tr><td style="font-weight:bold; background:#f0f4fa;">F/H Name</td><td>{data.get('fh_name')}</td></tr>
                <tr><td style="font-weight:bold; background:#f0f4fa;">Patient ID</td><td>{data.get('patient_id')}</td></tr>
                <tr><td style="font-weight:bold; background:#f0f4fa;">Age</td><td>{data.get('age')}</td></tr>
                <tr><td style="font-weight:bold; background:#f0f4fa;">DOB</td><td>{data.get('dob')}</td></tr>
                <tr><td style="font-weight:bold; background:#f0f4fa;">Sex</td><td>{data.get('sex')}</td></tr>
                <tr><td style="font-weight:bold; background:#f0f4fa;">Address</td><td>{data.get('address')}</td></tr>
                <tr><td style="font-weight:bold; background:#f0f4fa;">Mobile</td><td>{data.get('mobile')}</td></tr>
                <tr><td style="font-weight:bold; background:#f0f4fa;">Fee Received</td><td>₹{data.get('fee')}</td></tr>
                <tr><td style="font-weight:bold; background:#f0f4fa;">Submitted By</td><td>{data.get('submitted_by')}</td></tr>
              </table>

              <p style="margin-top: 25px; font-size: 12px; color: #777;">
                — This is an automated confirmation from Ansar Hospital OPD System
              </p>
            </div>
            """
        )

        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sg.send(msg)
        print(f"✅ OPD confirmation email sent, status: {response.status_code}")
    except Exception as e:
        print("❌ Failed to send OPD confirmation email:", e)

#----------- ATTENDANCE CONFIRMATION MAIL SENDING-------------- 

# send_attendance_confirmation
import os
from flask import render_template
from base64 import b64encode
from email.utils import formataddr
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName, FileType, Disposition
)

def send_attendance_confirmation(name, emp_id, checkin, checkout, status, submitted_by, event_type="Check-In", to_emails=None):
    try:
        sender_email = os.getenv("EMAIL_SENDER")
        sender_name = os.getenv("EMAIL_SENDER_NAME", "Attendance System")
        recipients = to_emails or os.getenv("EMAIL_TO", "").split(",")

        # Customize subject and subtitle
        subject = f"✅ {event_type} Confirmation for {name}"

        # Render dynamic template
        html_content = render_template(
            "email/attendance_confirmation.html",
            name=name,
            id=emp_id,
            checkin=checkin,
            checkout=checkout,
            status=status,
            submitted_by=submitted_by,
            event_type=event_type
        )

        message = Mail(
            from_email=formataddr((sender_name, sender_email)),
            to_emails=recipients,
            subject=subject,
            html_content=html_content
        )

        # Embed logo
        # ✅ Relative to project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        logo_path = os.path.join(project_root, 'static', 'images', 'logo_clinic.png')

        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                encoded_logo = b64encode(f.read()).decode()
                attachment = Attachment()
                attachment.file_content = FileContent(encoded_logo)
                attachment.file_type = FileType("image/png")
                attachment.file_name = FileName("logo_clinic.png")
                attachment.disposition = Disposition("inline")
                attachment.content_id = "logo_clinic"
                message.attachment = attachment

        # Deliver email
        if os.getenv("EMAIL_DEBUG", "False").lower() == "true":
            print("📧 Debug Mode: Email HTML Preview Below\n" + html_content)
        else:
            print("📨 Attempting to send email via SendGrid...")
            sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
            response = sg.send(message)
            print(f"✅ Email sent | Status: {response.status_code}")

    except Exception as e:
        print("❌ Failed to send attendance confirmation:", e)





from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import datetime
import base64
import logging
import os
from pathlib import Path

def send_appointment_confirmation_email(data, row):
    try:
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict for data, got {type(data)}")

        # Extract recipient email
        to_email = data.get("email", "").strip()
        if not to_email:
            logging.warning("⚠️ No recipient email provided; using fallback.")
            to_email = "zakiup@gmail.com"

        if "@" not in to_email:
            raise ValueError(f"Invalid email: {to_email}")

        # Unpack values
        no, date, patient_id, prefix, name, title, hf_name, gender, age, dob_raw, address, mobile, staff, status, doctor = row

        # Format DOB
        try:
            dob_str = datetime.strptime(dob_raw, "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            try:
                dob_str = datetime.strptime(dob_raw, "%d/%m/%Y").strftime("%d/%m/%Y")
            except ValueError:
                dob_str = dob_raw
                logging.warning(f"⚠️ DOB format not recognized: {dob_raw}")

        # Load logo as Base64
        try:
            logo_path = Path(__file__).resolve().parent.parent / "static" / "images" / "logo_clinic.png"
            with open(logo_path, "rb") as img_file:
                logo_data = base64.b64encode(img_file.read()).decode("utf-8")
            logo_html = f'<img src="data:image/png;base64,{logo_data}" alt="Logo" style="height: 60px;"><br><br>'
        except Exception as e:
            logging.warning(f"⚠️ Logo not found or failed to load: {e}")
            logo_html = "<h3>ANSAR HOSPITAL</h3>"

        # Build HTML content
        html_content = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            {logo_html}
            <h2 style="color: #2c3e50;">Appointment Confirmation – ANSAR HOSPITAL</h2>

            <table border="1" cellspacing="0" cellpadding="8" style="border-collapse: collapse; width: 100%;">
                <tr><th align="left">Appointment No</th><td>{no}</td></tr>
                <tr><th align="left">Date</th><td>{date}</td></tr>
                <tr><th align="left">Patient ID</th><td>{patient_id}</td></tr>
                <tr><th align="left">Name</th><td>{prefix} {name}</td></tr>
                <tr><th align="left">F/H Name</th><td>{title} {hf_name}</td></tr>
                <tr><th align="left">Gender</th><td>{gender}</td></tr>
                <tr><th align="left">Age</th><td>{age}</td></tr>
                <tr><th align="left">DOB</th><td>{dob_str}</td></tr>
                <tr><th align="left">Address</th><td>{address}</td></tr>
                <tr><th align="left">Mobile</th><td>{mobile}</td></tr>
                <tr><th align="left">Staff</th><td>{staff}</td></tr>
                <tr><th align="left">Status</th><td>{status}</td></tr>
                <tr><th align="left">Doctor</th><td>{doctor}</td></tr>
            </table>

            <p style="margin-top: 20px; font-size: 13px; color: #666;">
                Please arrive 10 minutes early. For assistance, contact us at +91-XXX-XXX-XXXX.
            </p>
        </div>
        """

        # Send email
        message = Mail(
            from_email=("info@ansarhospital.in", "Ansar Hospital"),
            to_emails=to_email,
            subject=f"Appointment Confirmation - {prefix} {name}",
            html_content=html_content
        )

        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sg.send(message)

        print(f"📧 Email sent to: {to_email} | Status: {response.status_code}")

    except Exception as e:
        logging.error(f"❌ Failed to send appointment email: {e}", exc_info=True)
