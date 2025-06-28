from functools import wraps
from flask import session, redirect, url_for, flash, Blueprint, render_template, request
from utils.sheets import spreadsheet
from utils.otp_utils import generate_otp, get_expiry_time
from services.user_service import update_user_password, get_user_by_username

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

# Other routes like forgot_password etc.


@auth_utils_bp.route('/logout')
def logout():
    session.clear()
    flash("✅ Password updated. Please log in.")
    return redirect(url_for('module_login', module='appointment'))  # Adjust as needed

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
        new_password = request.form['new_password'].strip()

        try:
            data = sheet.get_all_records()
            headers = list(data[0].keys()) if data else []
            print("Headers found:", headers)

            user_col_index = headers.index('User') + 1 if 'User' in headers else None
            pass_col_index = headers.index('Password') + 1 if 'Password' in headers else None

            if user_col_index is None or pass_col_index is None:
                flash("Invalid sheet structure.")
                return redirect(url_for('auth_utils_bp.forgot_password'))

            for i, row in enumerate(data, start=2):  # Row 2 onwards
                if row.get('User') == username:
                    resp = sheet.update_cell(i, pass_col_index, new_password)
                    print("Password updated:", resp)
                    flash("✅ Password updated. Please log in.")
                    return redirect(url_for('module_login', module='appointment'))

            flash("User not found.")
        except Exception as e:
            print("Password reset error:", e)
            flash("❌ Something went wrong.")

    return render_template('forgot_password.html')