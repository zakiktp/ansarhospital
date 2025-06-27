import os
import time
import pandas as pd
from datetime import datetime
from schedule import every, run_pending
from config import spreadsheet  # already connected to "Database"

EXPORT_DIR = r'G:\My Drive\Ansar Hospital\Export'

def backup_all_sheets():
    print(f"\n📦 Backup started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    for sheet in spreadsheet.worksheets():
        data = sheet.get_all_values()
        if not data:
            print(f"⚠️  Skipped empty sheet: {sheet.title}")
            continue

        df = pd.DataFrame(data[1:], columns=data[0])
        filename = f"{sheet.title}_backup_{datetime.now().strftime('%Y-%m-%d')}.csv"
        path = os.path.join(EXPORT_DIR, filename)
        df.to_csv(path, index=False)
        print(f"✅ Sheet '{sheet.title}' backed up to:\n   {path}")

    print("🎉 Backup complete.\n")

# Schedule to run daily at 9:00 PM
every().day.at("21:00").do(backup_all_sheets)

print("🕒 Daily backup script initialized. Waiting for schedule...")
while True:
    run_pending()
    time.sleep(60)