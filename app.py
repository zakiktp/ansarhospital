import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from fpdf import FPDF
import pandas as pd
import csv
from io import BytesIO, StringIO

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH", "credential.json")
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_PATH, scope)
client = gspread.authorize(creds)

# Load Google Sheets
spreadsheet = client.open("Database")
login_ws = spreadsheet.worksheet("Login")
appointment_ws = spreadsheet.worksheet("Appointment")
dropdown_ws = spreadsheet.worksheet("Dropdownlist")

def send_email(subject, body):
    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_PASSWORD")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_email
    msg["To"] = "zakiup@gmail.com"
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(smtp_email, smtp_password)
            smtp.send_message(msg)
            print("✅ Email sent successfully")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

@app.route("/test")
def test_credentials():
    try:
        spreadsheet.title
        return "✅ Google Sheets credentials work!"
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
        New Appointment Submitted:
        Name: {name}
        Guardian: {guardian}
        Address: {address}
        Mobile: {mobile}
        Status: {status}
        Staff: {staff}
        Timestamp: {now}
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

@app.route("/export_appointment/csv")
def export_csv():
    records = appointment_ws.get_all_records()
    si = StringIO()
    writer = csv.DictWriter(si, fieldnames=records[0].keys())
    writer.writeheader()
    writer.writerows(records)
    output = BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    return send_file(output, mimetype="text/csv", as_attachment=True, download_name="appointments.csv")

@app.route("/export_appointment/excel")
def export_excel():
    records = appointment_ws.get_all_records()
    df = pd.DataFrame(records)
    output = BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)
    return send_file(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name="appointments.xlsx")

@app.route("/export_appointment/pdf")
def export_pdf():
    records = appointment_ws.get_all_records()
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    col_width = 40
    for row in records:
        line = ", ".join(str(value) for value in row.values())
        pdf.multi_cell(0, 10, line)

    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return send_file(output, mimetype="application/pdf", as_attachment=True, download_name="appointments.pdf")

if __name__ == "__main__":
    app.run(debug=True)
