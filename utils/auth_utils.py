from flask import Blueprint, session, redirect, url_for, flash, request
from functools import wraps

auth_utils_bp = Blueprint('auth_utils_bp', __name__)

# ✅ Login required decorator to protect private routes
from functools import wraps
from flask import session, redirect, url_for, flash, request

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):  # <- FIX: Add *args
        if 'user' not in session:
            flash("You must be logged in to access this page.", "danger")
            return redirect(url_for('auth.login', next=request.url))
        return view(*args, **kwargs)  # <- FIX: pass *args too

    return wrapped_view



# ✅ Restrict based on access level
def access_required(module_name):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = session.get("user")
            if not user:
                flash("⚠️ You must be logged in to access this page.", "danger")
                return redirect(url_for('auth.login', next=request.url))

            access_raw = user.get("access", [])
            if isinstance(access_raw, str):
                access_list = [a.strip().lower() for a in access_raw.split(",")]
            elif isinstance(access_raw, list):
                access_list = [a.strip().lower() for a in access_raw]
            else:
                access_list = []

            print("ACCESS DEBUG:", access_list, "MODULE:", module_name)

            if 'all' in access_list or module_name.lower() in access_list:
                return f(*args, **kwargs)

            flash("❌ You are not authorized to access this module.", "danger")
            return redirect(url_for('dashboard'))
        return wrapper
    return decorator
