import io
import pandas as pd
from datetime import datetime

def generate_excel_report(headers, rows, title="Report", sheet_name="Sheet1"):
    output = io.BytesIO()
    df = pd.DataFrame(rows, columns=headers)

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)

        wb = writer.book
        ws = writer.sheets[sheet_name]

        title_format = wb.add_format({'bold': True, 'font_size': 16, 'align': 'center'})
        header_format = wb.add_format({
            'bold': True, 'bg_color': '#d9d9d9',
            'border': 1, 'align': 'center', 'valign': 'vcenter'
        })

        # Title (merged across all header columns)
        ws.merge_range(0, 0, 0, len(headers) - 1, title, title_format)

        # Write header row
        for col, name in enumerate(headers):
            ws.write(1, col, name, header_format)
            ws.set_column(col, col, 18)  # Default width

    output.seek(0)
    return output.read()