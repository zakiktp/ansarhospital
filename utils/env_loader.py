import os
import base64
from dotenv import load_dotenv
from pathlib import Path

# Step 1: Load .env (for local use)
dotenv_path = Path(__file__).resolve().parents[1] / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path)
    print(f"✅ Loaded .env from: {dotenv_path}")
else:
    print("⚠️ .env not found. Assuming Render-style environment variables.")

# Step 2: Handle credentials from base64 or .env path
default_path = Path(__file__).resolve().parents[1] / "secrets" / "credentials.json"
b64_creds = os.getenv("GOOGLE_CREDENTIALS_B64")

if b64_creds:
    print("🔐 Decoding GOOGLE_CREDENTIALS_B64...")
    default_path.parent.mkdir(parents=True, exist_ok=True)
    with open(default_path, "wb") as f:
        f.write(base64.b64decode(b64_creds))
    os.environ["CREDENTIALS_PATH"] = str(default_path)
elif not os.getenv("CREDENTIALS_PATH"):
    raise EnvironmentError("❌ Missing credentials: neither GOOGLE_CREDENTIALS_B64 nor CREDENTIALS_PATH found.")

# Step 3: Validate required environment keys
REQUIRED_KEYS = [
    "CREDENTIALS_PATH",
    "SENDGRID_API_KEY",
    "EMAIL_SENDER",
    "EMAIL_SENDER_NAME"
]

for key in REQUIRED_KEYS:
    value = os.getenv(key)
    if not value or value.strip() == "":
        raise EnvironmentError(f"❌ Missing or empty {key} in environment")
    if key == "SENDGRID_API_KEY" and not value.startswith("SG."):
        raise EnvironmentError(f"❌ {key} does not appear to be a valid SendGrid key")
    print(f"🔐 {key} = {value}")
