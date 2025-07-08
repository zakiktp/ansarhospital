import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask

from utils.email_utils import send_attendance_email
from utils.report_utils import generate_pdf_report

# Load environment variables
load_dotenv()

# Required for access to app context if needed
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-default-secret-key")


def main():
    today = datetime.now().strftime('%Y-%m-%d')
    today_display = datetime.now().strftime('%d-%m-%Y')
    subject = f"Daily Attendance Report - {today_display}"
    body = f"Please find attached the attendance report for {today_display}.\n\nRegards,\nAnsar Hospital"

    # Generate the report using today as both start and end
    try:
        pdf_path = generate_pdf_report(
            start_date=today,
            end_date=today,
            filename=f"daily_report_{today_display}.pdf"
        )

        if pdf_path:
            sent = send_attendance_email(subject, body, attachment_path=pdf_path)
            if sent:
                print("✅ Email sent successfully.")
            else:
                print("❌ Failed to send email.")
        else:
            print("⚠️ Failed to generate the PDF report.")

    except Exception as e:
        print("❌ Error in generating or sending report:", e)


if __name__ == '__main__':
    with app.app_context():
        main()
