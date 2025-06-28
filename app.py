# ✅ STEP 1: Load .env BEFORE importing anything that uses it
import os
from dotenv import load_dotenv
from pathlib import Path
from utils.env_loader import *  # This loads and validates env variables

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# Debug check
print("✅ Loaded .env from:", env_path)
print("🔐 CREDENTIALS_PATH =", os.getenv("CREDENTIALS_PATH"))

# ✅ STEP 2: Now safe to import things that depend on env
from flask import Flask, render_template, request, redirect, url_for, session, flash
from services.user_service import get_user_by_username  # now this works
from utils.sheets import worksheet
from config import spreadsheet, MODULES
from controllers.appointment_controller import appointment_bp
from utils.auth_utils import auth_utils_bp, access_required
import pandas as pd
import pytz
from datetime import datetime

# Now your environment variables are available globally
CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH")

import gspread
gc = gspread.service_account(filename=CREDENTIALS_PATH)
print("📂 Current Working Directory:", os.getcwd())
print("📄 .env file exists here:", os.path.exists(".env"))

for key in ["SENDGRID_API_KEY", "EMAIL_SENDER", "EMAIL_SENDER_NAME"]:
    value = os.getenv(key)
    if value:
        os.environ[key] = value
    else:
        print(f"⚠️ WARNING: {key} is not set in environment variables.")

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fallback-key')

# Utility: today's appointment count
def get_today_appointment_count():
    today = datetime.now(pytz.timezone("Asia/Kolkata")).strftime('%d/%m/%Y')
    all_records = worksheet.get_all_records()
    return sum(1 for row in all_records if row.get('Date') == today)

# Local time for logging
def get_local_timestamp():
    india = pytz.timezone("Asia/Kolkata")
    return datetime.now(india).strftime('%d/%m/%Y %H:%M:%S')

# Root route
@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    user = session.get('user')
    today_count = get_today_appointment_count()
    return render_template('dashboard.html', user=user, today_count=today_count)

# Login per module
@app.route('/auth/<module>', methods=['GET', 'POST'])
def module_login(module):
    login_sheet = spreadsheet.worksheet("Login")
    users = get_user_credentials(login_sheet)

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        user = users.get(username)

        if user and user['Password'] == password:
            session['user'] = {
                'username': username,
                'name': user.get('Name', username),
                'role': user.get('Role', ''),
                'access': [a.strip().lower() for a in user.get('Access', '').split(',')]
            }

            # Log activity
            log_sheet = spreadsheet.worksheet('Log')
            timestamp = get_local_timestamp()
            log_sheet.append_row([timestamp, username, module.upper(), 'Login Successful'])

            return redirect(url_for(f'{module}_bp.{module}_main'))

        flash('Invalid username or password')

    return render_template('login.html', module=module)

# Credential utility
def get_user_credentials(sheet):
    data = sheet.get_all_records()
    return {row['User']: row for row in data}

# Optional legacy login
@app.route('/log', methods=['GET', 'POST'])
def general_login():
    module = request.args.get('module', 'appointment')

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        login_sheet = spreadsheet.worksheet("Login")
        records = login_sheet.get_all_records()
        credentials = {row['User']: row['Password'] for row in records}

        if username in credentials and credentials[username] == password:
            session['user'] = {
                'username': username,
                'name': username,
                'role': '',
                'access': ['all']
            }
            flash("✅ Login successful.")
            return redirect(url_for('appointment_main'))
        else:
            flash("❌ Invalid credentials.", 'danger')

    return render_template("login.html", module=module)

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('index'))

from utils.forgot_password import forgot_password_bp

# Register Blueprints
app.register_blueprint(appointment_bp)
app.register_blueprint(auth_utils_bp)
app.register_blueprint(forgot_password_bp)

# Jinja globals
app.jinja_env.globals.update(MODULES=MODULES)
app.jinja_env.globals.update(current_year=datetime.now().year)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
