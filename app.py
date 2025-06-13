import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# SendGrid API Key
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Use different path depending on environment
if os.getenv("RENDER") == "true":
    CREDENTIALS_PATH = "/etc/secrets/credentials.json"  # Render
else:
    CREDENTIALS_PATH = "service_account.json"  # Local

creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_PATH, scope)
client = gspread.authorize(creds)


# Load Google Sheets
spreadsheet = client.open("Database")
login_ws = spreadsheet.worksheet("Login")
appointment_ws = spreadsheet.worksheet("Appointment")
dropdown_ws = spreadsheet.worksheet("Dropdownlist")

def send_email(subject, content):
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        message = Mail(
            from_email='noreply@ansarhospital.com',
            to_emails='zakiup@gmail.com',
            subject=subject,
            html_content=content
        )
        sg.send(message)
    except Exception as e:
        print("Email sending error:", e)

@app.route("/test")
def test_credentials():
    try:
        # Try accessing a sheet
        spreadsheet.title
        return "✅ Credentials and Google Sheets access successful."
    except Exception as e:
        return f"❌ Error: {e}"

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        users = login_ws.get_all_records()
        for user in users:
            if user["User"] == username and user["Password"] == password:
                session["user"] = user["Name"]
                session["role"] = user["Role"]
                return redirect(url_for("appointments"))
        flash("Invalid credentials", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for("login"))

@app.route("/appointments", methods=["GET", "POST"])
def appointments():
    if "user" not in session:
        return redirect(url_for("login"))

    dropdown_values = dropdown_ws.col_values(1)
    results = []

    if request.method == "POST":
        name = request.form["name"].strip().upper()
        guardian = request.form["guardian"].strip().upper()
        mobile = request.form["mobile"].strip()
        address = request.form["address"].strip().upper()
        if address == "OTHER":
            address = request.form["custom_address"].strip().upper()
            if address and address not in dropdown_values:
                dropdown_ws.append_row([address])
                dropdown_values.append(address)

        status = request.form["status"].strip().upper()
        staff = session["user"]
        now = datetime.now().strftime("%d/%m/%Y:%H:%M:%S")

        new_row = ["", now, name, guardian, address, mobile, status, staff]
        appointment_ws.append_row(new_row)

        email_body = f"""
        <h3>New Appointment Submitted</h3>
        <ul>
            <li><strong>Name:</strong> {name}</li>
            <li><strong>Guardian:</strong> {guardian}</li>
            <li><strong>Address:</strong> {address}</li>
            <li><strong>Mobile:</strong> {mobile}</li>
            <li><strong>Status:</strong> {status}</li>
            <li><strong>Staff:</strong> {staff}</li>
            <li><strong>Timestamp:</strong> {now}</li>
        </ul>
        """
        send_email("New Appointment Entry", email_body)
        flash("Appointment saved successfully!", "success")
        return redirect(url_for("appointments"))

    if request.method == "GET":
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        mobile = request.args.get("mobile")
        all_records = appointment_ws.get_all_records()

        for row in all_records:
            try:
                row_date = datetime.strptime(row["Date"], "%d/%m/%Y:%H:%M:%S")
                date_match = (
                    (not start_date or row_date >= datetime.strptime(start_date, "%Y-%m-%d")) and
                    (not end_date or row_date <= datetime.strptime(end_date, "%Y-%m-%d"))
                )
            except:
                date_match = True

            mobile_match = not mobile or row.get("Mobile", "") == mobile
            if date_match and mobile_match:
                results.append(row)

    return render_template("appointment.html", dropdown_values=dropdown_values, results=results)

if __name__ == "__main__":
    app.run(debug=True)
