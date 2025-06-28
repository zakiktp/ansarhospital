from functools import wraps
from flask import session, redirect, url_for, flash, Blueprint, render_template, request
from utils.sheets import spreadsheet
from utils.otp_utils import generate_otp, get_expiry_time
from services.user_service import update_user_password, get_user_by_username
from utils.email_sender import send_otp_email
from datetime import datetime

auth_utils_bp = Blueprint('auth_utils_bp', __name__)

# ✅ Access decorator
def access_required(module):
    def wrapper(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            if 'user' not in session:
                return redirect(url_for('module_login', module=module))
            access = session['user'].get('access', [])
            if 'all' not in access and module not in access:
                flash("Access denied.")
                return redirect(url_for('dashboard'))
            return func(*args, **kwargs)
        return decorated
    return wrapper

@auth_utils_bp.route('/logout')
def logout():
    session.clear()
    flash("✅ Password updated. Please log in.")
    return redirect(url_for('module_login', module='appointment'))

@auth_utils_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    try:
        sheet = spreadsheet.worksheet("Login")
    except Exception as e:
        flash("⚠️ Unable to access Login sheet.")
        print("Sheet error:", e)
        return redirect(url_for('module_login', module='appointment'))

    if request.method == 'POST':
        username = request.form['username'].strip()

        try:
            data = sheet.get_all_records()
            headers = list(data[0].keys()) if data else []
            print("Headers found:", headers)

            user_col_index = headers.index('User') + 1 if 'User' in headers else None
            pass_col_index = headers.index('Password') + 1 if 'Password' in headers else None
            otp_col_index = headers.index('OTP') + 1 if 'OTP' in headers else None
            expiry_col_index = headers.index('OTP_Expiry') + 1 if 'OTP_Expiry' in headers else None

            if not all([user_col_index, pass_col_index, otp_col_index, expiry_col_index]):
                flash("❌ Invalid sheet structure.")
                print("❌ Required columns missing:", headers)
                return redirect(url_for('auth_utils_bp.forgot_password'))

            for i, row in enumerate(data, start=2):
                if row.get('User') == username:
                    email = row.get('Email')
                    if not email:
                        flash("⚠️ No email associated with this user.")
                        return redirect(url_for('auth_utils_bp.forgot_password'))

                    otp = generate_otp()
                    expiry = get_expiry_time(10)
                    expiry_str = expiry.strftime('%Y-%m-%d %H:%M:%S')

                    # ✅ Insert OTP and expiry into the correct columns
                    sheet.update_cell(i, otp_col_index, otp)
                    sheet.update_cell(i, expiry_col_index, f"'{expiry_str}")  # Force string format

                    print(f"✅ OTP inserted for {username}: {otp} (expires {expiry_str})")

                    send_otp_email(email, otp)

                    session['otp_user'] = username
                    flash("✅ OTP sent to your email.")
                    return redirect(url_for('auth_utils_bp.verify_otp'))

            flash("❌ Username not found.")
        except Exception as e:
            print("❌ Password reset error:", e)
            flash("❌ Something went wrong. Please try again.")

    return render_template('forgot_password.html')


@auth_utils_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    sheet = spreadsheet.worksheet("Login")
    username = session.get('otp_user')

    if not username:
        flash("⚠️ Session expired. Please start again.")
        return redirect(url_for('auth_utils_bp.forgot_password'))

    if request.method == 'POST':
        entered_otp = request.form.get('otp', '').strip()
        data = sheet.get_all_records()

        for i, row in enumerate(data, start=2):
            if row.get('User') == username:
                stored_otp = str(row.get('OTP')).strip()
                expiry_str = row.get('OTP_Expiry')

                try:
                    expiry = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')
                except:
                    flash("⚠️ OTP expiry format invalid.")
                    return redirect(url_for('auth_utils_bp.forgot_password'))

                if datetime.now() > expiry:
                    flash("⏰ OTP expired. Please request again.")
                    return redirect(url_for('auth_utils_bp.forgot_password'))

                if entered_otp == stored_otp:
                    session['otp_verified_user'] = username
                    flash("✅ OTP verified. Please set a new password.")
                    return redirect(url_for('auth_utils_bp.reset_password'))
                else:
                    flash("❌ Incorrect OTP.")
                    return redirect(url_for('auth_utils_bp.verify_otp'))

        flash("⚠️ User not found.")
        return redirect(url_for('auth_utils_bp.forgot_password'))

    return render_template('verify_otp.html')

@auth_utils_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    from datetime import datetime
    try:
        sheet = spreadsheet.worksheet("Login")
    except Exception as e:
        flash("⚠️ Unable to access Login sheet.")
        print("Sheet access error:", e)
        return redirect(url_for('auth_utils_bp.forgot_password'))

    username = session.get('otp_verified_user')

    if not username:
        flash("⚠️ Session expired. Please restart the process.")
        return redirect(url_for('auth_utils_bp.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not password or not confirm_password:
            flash("❌ Please fill in all fields.")
            return redirect(url_for('auth_utils_bp.reset_password'))

        if password != confirm_password:
            flash("❌ Passwords do not match.")
            return redirect(url_for('auth_utils_bp.reset_password'))

        if len(password) < 6:
            flash("❌ Password must be at least 6 characters.")
            return redirect(url_for('auth_utils_bp.reset_password'))

        try:
            data = sheet.get_all_records()
            headers = list(data[0].keys()) if data else []
            password_col_index = headers.index("Password") + 1 if "Password" in headers else None
            user_col_index = headers.index("User") + 1 if "User" in headers else None

            if password_col_index is None:
                flash("❌ 'Password' column not found.")
                return redirect(url_for('auth_utils_bp.reset_password'))

            for i, row in enumerate(data, start=2):
                if row.get("User") == username:
                    sheet.update_cell(i, password_col_index, password)
                    flash("✅ Password updated. Please log in.")
                    session.clear()
                    return redirect(url_for('module_login', module='appointment'))

            flash("❌ User not found during reset.")

        except Exception as e:
            print("Reset password error:", e)
            flash("⚠️ An error occurred. Please try again.")

    return render_template('reset_password.html')



