from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.email_sender import send_otp_email
from services.user_service import (
    get_user_by_username,
    get_user_by_email,
    validate_otp,
    set_otp_for_user,
    update_user_password
)
import random
from datetime import datetime, timedelta
from config import spreadsheet
from urllib.parse import urlparse, urljoin

# 🔒 Auth Blueprint
auth_bp = Blueprint('auth', __name__)

# ✅ Safe redirect check
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

# =========================
# ✅ LOGIN ROUTE
# =========================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        login_sheet = spreadsheet.worksheet("Login")
        records = login_sheet.get_all_records()

        user_row = next((row for row in records if row['User'] == username), None)

        if user_row and user_row['Password'] == password:
            access = user_row.get('Access', 'all')
            access_list = [a.strip().lower() for a in access.split(',')] if access else []

            session['user'] = {
                'username': username,
                'name': user_row.get('Name', username),
                'role': user_row.get('Role', 'Staff'),
                'access': access_list
            }
            session['user_name'] = username  # 👈 Used in OPD Submission

            flash("✅ Login successful.", "success")

            next_url = request.args.get('next')
            if next_url and is_safe_url(next_url):
                return redirect(next_url)

            return redirect(url_for('dashboard'))
        else:
            flash("❌ Invalid credentials.", "danger")

    return render_template("login.html")


# =========================
# ✅ LOGOUT
# =========================
@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('auth.login'))


# =========================
# ✅ FORGOT PASSWORD
# =========================
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        user = get_user_by_username(username)

        if not user:
            flash("Invalid username", "danger")
            return redirect(url_for('auth.forgot_password'))

        email = user.get("Email")
        if not email:
            flash("Email not found in user record.", "danger")
            return redirect(url_for('auth.forgot_password'))

        otp = str(random.randint(100000, 999999))
        expiry = datetime.now() + timedelta(minutes=10)

        set_otp_for_user(email, otp, expiry)
        send_otp_email(email, otp)

        session['reset_email'] = email
        flash('OTP sent to your registered email.', 'success')
        return redirect(url_for('auth.verify_otp'))

    return render_template('forgot_password.html')


# =========================
# ✅ VERIFY OTP
# =========================
@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        email = session.get('reset_email')

        if not email:
            flash("Session expired. Please start again.", "danger")
            return redirect(url_for('auth.forgot_password'))

        if validate_otp(email, entered_otp):
            flash("OTP verified. You may now reset your password.", "success")
            return redirect(url_for('auth.reset_password'))
        else:
            flash("Invalid or expired OTP.", "danger")
            return redirect(url_for('auth.verify_otp'))

    return render_template('verify_otp.html')


# =========================
# ✅ RESET PASSWORD
# =========================
@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('auth.reset_password'))

        email = session.get('reset_email')
        if not email:
            flash("Session expired. Please start again.", "danger")
            return redirect(url_for('auth.forgot_password'))

        update_user_password(email, new_password)
        session.pop('reset_email', None)
        flash("Password successfully updated. Please log in.", "success")
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html')
