from flask import Blueprint, request, render_template, flash, redirect, url_for, session
from utils.sheets import spreadsheet
from utils.otp_utils import generate_otp, get_expiry_time
from utils.email_sender import send_otp_email
from datetime import datetime, timedelta

forgot_password_bp = Blueprint('forgot_password_bp', __name__)
auth_utils_bp = Blueprint('auth_utils_bp', __name__)

@auth_utils_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    sheet = spreadsheet.worksheet("Login")

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        data = sheet.get_all_records()

        for i, row in enumerate(data, start=2):
            if row.get('User') == username:
                email = row.get('Email')
                if not email:
                    flash("⚠️ No email associated with this user.")
                    return redirect(url_for('auth_utils_bp.forgot_password'))

                otp = generate_otp()
                expiry = get_expiry_time(10)

                sheet.update_cell(i, sheet.find("OTP").col, otp)
                sheet.update_cell(i, sheet.find("OTP_Expiry").col, expiry.strftime('%Y-%m-%d %H:%M:%S'))
                send_otp_email(email, otp)

                session['otp_user'] = username
                flash("✅ OTP sent to your email.")
                return redirect(url_for('auth_utils_bp.verify_otp'))

        flash("❌ Username not found.")
    return render_template('forgot_password.html')




@auth_utils_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    sheet = spreadsheet.worksheet("Login")
    username = session.get('otp_user')

    if not username:
        flash("⚠️ Session expired. Please start over.")
        return redirect(url_for('auth_utils_bp.forgot_password'))

    if request.method == 'POST':
        entered_otp = request.form.get('otp', '').strip()
        data = sheet.get_all_records()

        for i, row in enumerate(data, start=2):
            if row.get('User') == username:
                saved_otp = row.get('OTP')
                expiry_str = row.get('OTP_Expiry')
                if not saved_otp or not expiry_str:
                    flash("❌ OTP not found or expired.")
                    return redirect(url_for('auth_utils_bp.forgot_password'))

                expiry = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')

                if entered_otp == saved_otp and datetime.now() <= expiry:
                    session['otp_verified_user'] = username
                    flash("✅ OTP verified. Please reset your password.")
                    return redirect(url_for('auth_utils_bp.reset_password'))
                else:
                    flash("❌ Invalid or expired OTP.")
                break

    return render_template('verify_otp.html')


@auth_utils_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    sheet = spreadsheet.worksheet("Login")
    username = session.get('otp_verified_user')

    if not username:
        flash("⚠️ Session expired. Please start over.")
        return redirect(url_for('auth_utils_bp.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm_password', '').strip()

        if not password or not confirm:
            flash("⚠️ All fields are required.")
            return redirect(url_for('auth_utils_bp.reset_password'))

        if password != confirm:
            flash("❌ Passwords do not match.")
            return redirect(url_for('auth_utils_bp.reset_password'))

        if len(password) < 6:
            flash("❌ Password must be at least 6 characters long.")
            return redirect(url_for('auth_utils_bp.reset_password'))

        # Update password in sheet
        data = sheet.get_all_records()
        for i, row in enumerate(data, start=2):
            if row.get('User') == username:
                sheet.update_cell(i, sheet.find("Password").col, password)
                flash("✅ Password updated successfully. Please log in.")
                session.clear()
                return redirect(url_for('module_login', module='appointment'))

        flash("❌ User not found.")
    return render_template('reset_password.html')
