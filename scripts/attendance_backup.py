from utils.sheet_utils import get_sheet, create_backup_sheet
from datetime import datetime

def backup_attendance_sheet():
    sheet = get_sheet('Attendance')
    data = sheet.get_all_values()
    if not data:
        return

    today = datetime.now().strftime('%Y-%m-%d')
    backup_title = f"Attendance_Backup_{today}"

    create_backup_sheet(data, backup_title, folder_name='ATTENDANCE_BACKUPS')
