import gspread
from dotenv import load_dotenv
import os

load_dotenv()
gc = gspread.service_account(filename=os.getenv("GOOGLE_CREDENTIALS_PATH"))
sheet = gc.open("Hospital Login").worksheet("Login")

print("✅ Sheet Title:", sheet.title)
print("👥 Users:", sheet.get_all_records())
