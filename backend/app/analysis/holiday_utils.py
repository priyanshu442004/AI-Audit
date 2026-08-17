from __future__ import annotations
import os
import re
import pandas as pd
from datetime import datetime, timedelta

STATIC_HOLIDAYS_MAP = {
    # 2025
    "2025-01-01": "New Year", "2025-01-26": "Republic Day", "2025-03-14": "Holi", "2025-03-31": "Eid-ul-Fitr",
    "2025-04-10": "Mahavir Jayanti", "2025-04-18": "Good Friday", "2025-05-12": "Buddha Purnima", "2025-08-15": "Independence Day",
    "2025-10-02": "Gandhi Jayanti", "2025-10-20": "Dussehra", "2025-10-23": "Diwali", "2025-11-05": "Guru Nanak Jayanti", "2025-12-25": "Christmas",
    # 2026
    "2026-01-01": "New Year", "2026-01-26": "Republic Day", "2026-03-04": "Holi", "2026-03-05": "Holi", "2026-03-26": "Ram Navami",
    "2026-04-02": "Good Friday", "2026-04-14": "Ambedkar Jayanti", "2026-05-01": "May Day", "2026-08-15": "Independence Day",
    "2026-08-28": "Raksha Bandhan", "2026-10-02": "Gandhi Jayanti", "2026-10-18": "Dussehra", "2026-10-20": "Dussehra",
    "2026-10-22": "Diwali", "2026-11-09": "Dipavali", "2026-11-10": "Govardhan Puja", "2026-11-11": "Bhai Dooj", "2026-12-25": "Christmas"
}

def load_holiday_map(dfs) -> dict[str, str]:
    """Extract holiday date -> name mapping from dfs or fallback static list."""
    holiday_map = dict(STATIC_HOLIDAYS_MAP)
    
    holidays_df = dfs.get("holidays") if isinstance(dfs, dict) else None
    if holidays_df is not None and not holidays_df.empty:
        for _, row in holidays_df.iterrows():
            for cell in row:
                if pd.notna(cell):
                    dt = pd.to_datetime(cell, errors='coerce', dayfirst=True)
                    if pd.notna(dt) and 2000 <= dt.year <= 2100:
                        holiday_map[dt.strftime("%Y-%m-%d")] = "Holiday"
    return holiday_map

def calc_business_days(start_val, end_val, holiday_set: set[str] = None) -> int | None:
    """
    Calculate calendar working days between start_val and end_val.
    Excludes Sundays (weekday == 6) and dates present in holiday_set (YYYY-MM-DD format).
    Returns None if either date is invalid or end_val < start_val.
    """
    if start_val is None or end_val is None:
        return None
    try:
        d_start = pd.to_datetime(start_val, errors="coerce", dayfirst=True)
        d_end   = pd.to_datetime(end_val,   errors="coerce", dayfirst=True)
        if pd.isna(d_start) or pd.isna(d_end):
            return None
        
        # If dates are equal, 0 business days lag
        if d_start == d_end:
            return 0
        
        # If start is after end, return negative or abs working days
        reverse = False
        if d_start > d_end:
            d_start, d_end = d_end, d_start
            reverse = True

        if holiday_set is None:
            holiday_set = set(STATIC_HOLIDAYS_MAP.keys())

        # Count days excluding Sundays and holiday dates
        curr = d_start + timedelta(days=1)
        b_days = 0
        while curr <= d_end:
            # Check Sunday (6) or Holiday
            dt_str = curr.strftime("%Y-%m-%d")
            if curr.weekday() != 6 and dt_str not in holiday_set:
                b_days += 1
            curr += timedelta(days=1)
            
        return -b_days if reverse else b_days
    except Exception:
        return None
