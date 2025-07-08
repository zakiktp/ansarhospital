import logging

# Set logging level to DEBUG to capture debug messages
logging.basicConfig(level=logging.DEBUG)

# Debugging message
logging.debug("Logging is set to DEBUG")

import os
logging.debug(f"DEBUG: {os.getenv('DEBUG')}")

logging.debug("📩 send_appointment_confirmation_email() triggered")

from utils.email_sender import send_appointment_confirmation_email

data = {
    "No": "12345",
    "Date": "08/07/2025, 00:01:19",
    "ID": "AH0002",
    "Prefix": "Mr.",
    "Name": "Naveen",
    "Titles": "S/O",
    "HFName": "Jai Parkash",
    "Gender": "Male",
    "Age": "34",
    "DOB": "28/02/1991",
    "Address": "Ansar Hospital",
    "Mobile": "8445617450",
    "Staff": "Dr. M. Affan Zaki Ansari",
    "Status": "NOT REPORTED",
    "Doctor": "Dr. M. Affan Zaki Ansari"
}

send_appointment_confirmation_email(data, "zakiup@gmail.com")
