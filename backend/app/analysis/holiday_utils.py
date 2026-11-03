from __future__ import annotations
import os
import re
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

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


def parse_p2p_dates(values: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(values, errors="coerce", dayfirst=True, format="mixed")
    iso_dates = values.astype("string").str.match(r"^\d{4}-\d{2}-\d{2}(?:$|[ T])", na=False)
    if iso_dates.any():
        parsed.loc[iso_dates] = pd.to_datetime(
            values.loc[iso_dates],
            errors="coerce",
            dayfirst=False,
        )
    return parsed


def load_p2p_holiday_frame(holidays_dir: str | os.PathLike) -> pd.DataFrame:
    """Load the user-managed holiday calendar, falling back to the existing static list."""
    static = pd.DataFrame(
        [{"Holiday": name, "Date": day} for day, name in STATIC_HOLIDAYS_MAP.items()]
    )
    static.attrs["source"] = "static"
    static.attrs["covered_years"] = {int(day[:4]) for day in STATIC_HOLIDAYS_MAP}

    directory = Path(holidays_dir)
    if not directory.is_dir():
        return static
    files = sorted(
        (
            path for path in directory.iterdir()
            if path.is_file()
            and path.suffix.lower() in {".csv", ".xls", ".xlsx"}
            and not path.stem.lower().startswith("dummy")
        ),
        key=lambda path: path.stat().st_mtime,
    )
    if not files:
        return static

    from app.loaders import load_file

    custom = load_file(files[-1], files[-1].name, role="holiday")
    normalized = {
        re.sub(r"[^a-z0-9]", "", str(column).lower()): column
        for column in custom.columns
    }
    date_column = next(
        (
            normalized[name]
            for name in ("date", "holidaydate", "holidate")
            if name in normalized
        ),
        None,
    )
    if date_column is None:
        date_candidates = [
            (column, parse_p2p_dates(custom[column]).notna().mean())
            for column in custom.columns
        ]
        date_column = max(date_candidates, key=lambda item: item[1])[0] if date_candidates else None
        if date_column is None or parse_p2p_dates(custom[date_column]).notna().sum() == 0:
            raise ValueError(f"Holiday calendar {files[-1].name!r} has no parseable date column.")

    name_column = next(
        (
            normalized[name]
            for name in ("holiday", "holidayname", "festival", "name")
            if name in normalized and normalized[name] != date_column
        ),
        None,
    )
    dates = parse_p2p_dates(custom[date_column])
    valid = dates.notna()
    if not valid.any():
        raise ValueError(f"Holiday calendar {files[-1].name!r} contains no valid holiday dates.")
    custom_frame = pd.DataFrame({
        "Holiday": custom[name_column].astype(str) if name_column else "Public Holiday",
        "Date": dates.dt.strftime("%Y-%m-%d"),
    }).loc[valid]
    combined = pd.concat([static, custom_frame], ignore_index=True)
    combined = combined.drop_duplicates(subset="Date", keep="last").reset_index(drop=True)
    combined.attrs["source"] = "uploaded"
    combined.attrs["covered_years"] = set(
        pd.to_datetime(combined["Date"], errors="coerce").dropna().dt.year
    )
    return combined


def load_holiday_map(dfs) -> dict[str, str]:
    """Extract holiday date -> name mapping from dfs or fallback static list."""
    holiday_map = dict(STATIC_HOLIDAYS_MAP)
    
    holidays_df = dfs.get("holidays") if isinstance(dfs, dict) else None
    if holidays_df is not None and not holidays_df.empty:
        for _, row in holidays_df.iterrows():
            for cell in row:
                if pd.notna(cell):
                    dt = parse_p2p_dates(pd.Series([cell])).iloc[0]
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
        d_start = parse_p2p_dates(pd.Series([start_val])).iloc[0]
        d_end   = parse_p2p_dates(pd.Series([end_val])).iloc[0]
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
