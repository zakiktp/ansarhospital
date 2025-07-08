from datetime import datetime, timedelta

def parse_date(date_str, fmt="%Y-%m-%d"):
    return datetime.strptime(date_str, fmt).date()

def build_date_range(start_dt, end_dt):
    dates = []
    current = start_dt
    while current <= end_dt:
        dates.append(current)
        current += timedelta(days=1)
    return dates

def clean_names_list(names):
    return [n.strip().lower() for n in names] if names else []