"""Excel serial date number → YYYY-MM-DD converter.

Usage:
    from excel_date import excel_to_date
    excel_to_date("38728")  # → "2006-01-11"
"""

from datetime import datetime, timedelta

_EXCEL_EPOCH = datetime(1899, 12, 30)


def excel_to_date(serial):
    """Convert Excel serial date number (string or int) to ISO date string.
    
    Handles the Excel 1900 date system. Numbers < 60 are unreliable
    (Excel's Lotus 1-2-3 compatibility bug) and return empty string.
    """
    try:
        n = int(float(serial))
        if n < 60:
            return ""
        return (_EXCEL_EPOCH + timedelta(days=n)).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return ""
