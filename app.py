import os
from flask import Flask, render_template, request, redirect, session, flash, url_for
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import csv, io
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallbacksecretkey")

# Google Sheets setup
CREDENTIALS_PATH = os.getenv("GOOGLE_CREDS_PATH", "/etc/secrets/credentials.json")
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_PATH, scope)
client = gspread.authorize(creds)
sheet = client.open("Database")
login_sheet = sheet.worksheet("Login")
appointment_sheet = sheet.worksheet("Appointment")
dropdown_sheet = sheet.worksheet("Dropdownlist")

# Mail config
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv("EMAIL_USER"),
    MAIL_PASSWORD=os.getenv("EMAIL_PASS")
)
mail = Mail(app)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        users = login_sheet.get_all_records()

        for user in users:
            print(f"Checking user: {user['User']} with password: {user['Password']}")
            if user["User"] == username and user["Password"] == password:
                session.update({
                    "username": username,
                    "name": user["Name"],
                    "role": user["Role"],
                    "access": user["Access"]
                })
                return redirect("/dashboard")
        
        flash("Invalid credentials", "error")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/")
    today = datetime.now().strftime("%Y-%m-%d")
    records = appointment_sheet.get_all_records()
    count_today = sum(1 for r in records if r.get("Timestamp", "").startswith(today))
    return render_template("dashboard.html", name=session["name"], role=session["role"],
                           access=session["access"], todays_appointments=count_today)

@app.route("/appointments", methods=["GET", "POST"])
def appointments():
    if "username" not in session:
        return redirect("/")
    results = []
    dropdown_values = [cell for cell in dropdown_sheet.col_values(1) if cell]
    if request.method == "POST":
        action = request.form.get("action")
        if action == "save":
            name = request.form["name"].upper().strip()
            hfn = request.form["husband_father_name"].upper().strip()
            address = request.form["address"]
            if address == "OTHER":
                address = request.form.get("custom_address", "").upper()
            mobile = request.form["mobile"]
            status = request.form["status"]
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            staff = session.get("name", "UNKNOWN")
            appointment_sheet.append_row([timestamp, name, hfn, address, mobile, status, staff])

            # Send email
            msg = Message("New Appointment Submitted", sender=app.config["MAIL_USERNAME"], recipients=["zakiup@gmail.com"])
            msg.body = f"New appointment:\n\nName: {name}\nFather/Husband Name: {hfn}\nAddress: {address}\nMobile: {mobile}\nStatus: {status}\nStaff: {staff}\nTime: {timestamp}"
            try:
                mail.send(msg)
            except Exception as e:
                print("Email error:", e)

            flash("Appointment saved successfully", "success")
            return redirect("/appointments")
    else:
        mobile_query = request.args.get("mobile", "").strip()
        start = request.args.get("start_date", "")
        end = request.args.get("end_date", "")
        all_rows = appointment_sheet.get_all_records()
        if start and end:
            results = [r for r in all_rows if start <= r["Timestamp"][:10] <= end]
        elif mobile_query:
            results = [r for r in all_rows if r["Mobile"] == mobile_query]
    return render_template("appointment.html", dropdown_values=dropdown_values, results=results)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/export_appointment/<file_type>")
def export_appointment(file_type):
    all_data = appointment_sheet.get_all_records()
    si = io.StringIO()
    cw = csv.DictWriter(si, fieldnames=all_data[0].keys())
    cw.writeheader()
    cw.writerows(all_data)
    mem = io.BytesIO()
    mem.write(si.getvalue().encode('utf-8'))
    mem.seek(0)

    ext = {"csv": "text/csv", "excel": "application/vnd.ms-excel", "pdf": "application/pdf"}.get(file_type, "text/csv")
    return (
        mem.read(),
        200,
        {
            "Content-Type": ext,
            "Content-Disposition": f"attachment; filename=appointments.{file_type if file_type != 'excel' else 'xls'}",
        },
    )

if __name__ == "__main__":
    app.run(debug=True)
