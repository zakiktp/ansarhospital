# test_sendgrid.py
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print("✅ .env loaded.")
else:
    print("❌ .env file not found.")

SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_SENDER_NAME = os.getenv('EMAIL_SENDER_NAME')

# Replace this with a verified recipient address
TEST_EMAIL = 'ansarpolyclinic@gmail.com'

def send_test_email():
    if not SENDGRID_API_KEY or not EMAIL_SENDER:
        print("❌ Missing SENDGRID_API_KEY or EMAIL_SENDER in .env")
        return

    message = Mail(
        from_email=(EMAIL_SENDER, EMAIL_SENDER_NAME),
        to_emails=TEST_EMAIL,
        subject="✅ SendGrid Test Email",
        plain_text_content="This is a test email from Ansar Hospital to confirm SendGrid setup is working."
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"✅ Test email sent to {TEST_EMAIL}. Status code: {response.status_code}")
    except Exception as e:
        print("❌ Failed to send test email:", str(e))

if __name__ == "__main__":
    send_test_email()
