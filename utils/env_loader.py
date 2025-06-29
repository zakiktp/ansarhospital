import os
import base64
from dotenv import load_dotenv
from pathlib import Path

dotenv_path = Path(__file__).resolve().parents[1] / '.env'
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print(f"✅ Loaded .env from: {dotenv_path}")
else:
    print(f"⚠️ .env not found. Assuming environment variables are set in hosting environment.")

# Decode credentials if available in base64
CREDENTIALS_PATH = Path(__file__).resolve().parents[1] / "credentials" / "credentials.json"
b64_creds = os.getenv("GOOGLE_CREDENTIALS_B64")

if b64_creds:
    print("🔐 Decoding credentials from environment...")
    CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CREDENTIALS_PATH, "wb") as f:
        f.write(base64.b64decode(b64_creds))
    os.environ["CREDENTIALS_PATH"] = str(CREDENTIALS_PATH)
else:
    # Use default .env method
    if not os.getenv("CREDENTIALS_PATH"):
        raise EnvironmentError("❌ Missing credentials: neither CREDENTIALS_PATH nor GOOGLE_CREDENTIALS_B64 found.")

# Validate required keys
REQUIRED_KEYS = [
    "CREDENTIALS_PATH",
    "SENDGRID_API_KEY",
    "EMAIL_SENDER",
    "EMAIL_SENDER_NAME"
]

for key in REQUIRED_KEYS:
    value = os.getenv(key)
    if not value or value.strip() == "":
        raise EnvironmentError(f"❌ Missing or empty {key} in environment variables")
    if key == "SENDGRID_API_KEY" and not value.startswith("SG."):
        raise EnvironmentError(f"❌ {key} does not appear to be a valid SendGrid key")
    print(f"🔐 {key} = {value}")
