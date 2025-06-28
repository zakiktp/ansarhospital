# utils/otp_utils.py

from datetime import datetime, timedelta
import random

def generate_otp(length=6):
    """Generate a numeric OTP of specified length (default is 6 digits)."""
    return ''.join(str(random.randint(0, 9)) for _ in range(length))

def get_expiry_time(minutes=10):
    """Return a datetime object X minutes into the future."""
    return datetime.now() + timedelta(minutes=minutes)
