@"
# 🏥 Ansar Hospital Management System

A secure, modular, Google Sheets–integrated web application for managing hospital operations such as appointments, OPD records, and staff attendance.

---

## 🔧 Tech Stack

- **Backend:** Flask (Python)
- **Frontend:** HTML, Bootstrap
- **Database:** Google Sheets via gspread API
- **Email:** SendGrid (for OTP verification)
- **Environment:** `.env` for credentials and secrets

---

## ✨ Features

- ✅ Google Login & Module-Based Access
- ✅ Patient Appointment Booking & Logs
- ✅ Staff Attendance with Check-In & Reports
- ✅ Email OTP Verification for Password Reset
- ✅ Daily Data Backup to Google Drive
- ✅ Export to PDF & Excel
- ✅ Mobile-Responsive UI
- ✅ Role-Based Access from \`Login\` Sheet

---

## 📁 Folder Structure

    kiratpur/
    ├── app.py
    ├── controllers/
    ├── utils/
    ├── templates/
    ├── static/
    ├── .env
    └── README.md

---

## 🚀 Getting Started

1. Clone the repo:
   \`\`\`bash
   git clone https://github.com/zakiktp/ansarhospital.git
   cd ansarhospital/kiratpur
   \`\`\`

2. Create virtual environment:
   \`\`\`bash
   python -m venv venv
   venv\Scripts\activate
   \`\`\`

3. Install dependencies:
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

4. Configure .env:
   \`\`\`dotenv
   CREDENTIALS_PATH=D:\Projects\ansarhospital\secrets\credentials.json
   SENDGRID_API_KEY=your_key
   EMAIL_SENDER=info@ansarhospital.in
   \`\`\`

5. Run the app:
   \`\`\`bash
   python app.py
   \`\`\`

---

## 🧠 Author

**Mohammad Zaki Ansari**  
📧 zakiktp@gmail.com  
🌐 [github.com/zakiktp](https://github.com/zakiktp)

---
"@ | Set-Content -Encoding UTF8 README.md
