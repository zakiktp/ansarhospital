from flask import Blueprint, session, redirect, url_for, flash, request
from functools import wraps

auth_utils_bp = Blueprint('auth_utils_bp', __name__)

# ✅ Login required decorator to protect private routes
def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if 'user' not in session:
            flash("You must be logged in to access this page.", "danger")
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view


# ✅ Restrict based on access level
def access_required(module_name):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = session.get('user')
            if not user:
                flash("⚠️ Please log in to access this page.", "warning")
                return redirect(url_for('auth.login'))

            access_list = user.get('access', [])
            access_list = [a.strip().lower() for a in access_list]  # 🔑 Normalize

            print("ACCESS DEBUG:", access_list, "MODULE:", module_name)

            if 'all' in access_list or module_name.lower() in access_list:
                return f(*args, **kwargs)
            else:
                flash("❌ You are not authorized to access this module.", "danger")
                return redirect(url_for('dashboard'))

        return wrapper
    return decorator

from flask import session

def get_logged_user(sess=None):
    """
    Returns the logged-in user's name from session.
    """
    if sess is None:
        sess = session
    return sess.get("user_name", "UNKNOWN").upper()

