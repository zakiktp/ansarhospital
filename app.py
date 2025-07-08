from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from pathlib import Path
import os
import pytz
import gspread
from datetime import datetime
import pandas as pd

print("✅ appointment_api.py is loaded and executing")


# Load .env before anything else
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# Google credentials
CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH")
gc = gspread.service_account(filename=CREDENTIALS_PATH)

# Environment-dependent imports
from config import spreadsheet, MODULES
from utils.sheet_utils import worksheet
from services.user_service import get_user_by_username
from utils.auth_utils import login_required, auth_utils_bp
from utils.forgot_password import forgot_password_bp

# Blueprints from controllers
from controllers.auth_controller import auth_bp
from controllers.appointment_controller import appointment_bp
from controllers.opd_controller import opd_bp
from controllers.patients_controller import patients_bp


# Blueprints from routes
from routes.attendance_routes import attendance_bp

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fallback-key')

# Utility functions
def get_today_appointment_count():
    today = datetime.now(pytz.timezone("Asia/Kolkata")).strftime('%d/%m/%Y')
    all_records = worksheet.get_all_records()
    return sum(1 for row in all_records if row.get('Date') == today)

def get_local_timestamp():
    india = pytz.timezone("Asia/Kolkata")
    return datetime.now(india).strftime('%d/%m/%Y %H:%M:%S')

# Routes
@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
def dashboard():
    user = session.get('user')
    today_count = get_today_appointment_count()
    return render_template('dashboard.html', user=user, today_count=today_count)

@app.route('/success')
def success():
    return "<h3>✅ OPD entry submitted successfully!</h3><a href='/opd'>← Back to OPD form</a>"

# Register Blueprints (only once)
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(appointment_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(auth_utils_bp)
app.register_blueprint(forgot_password_bp)
app.register_blueprint(opd_bp)
app.register_blueprint(patients_bp)

from routes.patient_api import patient_api_bp
app.register_blueprint(patient_api_bp)

from routes.appointment_api import appointment_api_bp
app.register_blueprint(appointment_api_bp)



# Jinja Contexts
app.jinja_env.globals.update(MODULES=MODULES)
app.jinja_env.globals.update(current_year=datetime.now().year)

# CLI route debugger
@app.cli.command("list-routes")
def list_routes():
    from urllib.parse import unquote
    import click

    routes = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        route = f"{rule.endpoint:40s} {methods:20s} {unquote(str(rule))}"
        routes.append(route)

    click.echo("\n🔍 Available Flask Endpoints:\n" + "-" * 80)
    for route in sorted(routes):
        click.echo(route)

# Run
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
