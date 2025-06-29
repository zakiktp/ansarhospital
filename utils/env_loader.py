import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from the project root
dotenv_path = Path(__file__).resolve().parents[1] / '.env'

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print(f"✅ Loaded .env from: {dotenv_path}")
else:
    print(f"⚠️ .env not found at {dotenv_path}. Assuming environment variables are set in the hosting environment.")

# List of required keys
REQUIRED_KEYS = [
    "CREDENTIALS_PATH",
    "SENDGRID_API_KEY",
    "EMAIL_SENDER",
    "EMAIL_SENDER_NAME"
]

# Validate required keys
for key in REQUIRED_KEYS:
    value = os.getenv(key)
    if not value or value.strip() == "":
        raise EnvironmentError(f"❌ Missing or empty {key} in environment variables")
    if key == "SENDGRID_API_KEY" and not value.startswith("SG."):
        raise EnvironmentError(f"❌ {key} does not appear to be a valid SendGrid key")
    print(f"🔐 {key} = {value}")
