import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# ✅ Use pre-loaded .env (no need to reload here if loaded in app.py)
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
EMAIL_SENDER = os.getenv('EMAIL_SENDER', 'noreply@ansarhospital.com')
EMAIL_SENDER_NAME = os.getenv('EMAIL_SENDER_NAME', 'Ansar Hospital')

def send_otp_email(to_email, otp):
    print(f"🧪 Sending OTP: {otp} to {to_email}")
    subject = "🔐 OTP for Password Reset"
    message = f"""
Dear User,

You requested a password reset. Please use the following OTP:

🔐 OTP: {otp}

This OTP is valid for 10 minutes.

If you did not request this, please ignore this email.

Regards,  
{EMAIL_SENDER_NAME}
"""

    email = Mail(
        from_email=(EMAIL_SENDER, EMAIL_SENDER_NAME),
        to_emails=to_email,
        subject=subject,
        plain_text_content=message
    )

    try:
        print(f"🔐 SENDGRID_API_KEY is {'set' if SENDGRID_API_KEY else 'NOT set'}")
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(email)
        print(f"✅ OTP email sent to {to_email}, status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to send OTP email to {to_email}: {e}")
        if hasattr(e, 'body'):
            print(e.body)
