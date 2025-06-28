import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_login_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("client_secret.json", scope)
    client = gspread.authorize(creds)

    spreadsheet = client.open("Your Spreadsheet Name")  # Replace with actual name
    return spreadsheet.worksheet("Login")
