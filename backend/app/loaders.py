"""Load Excel / CSV / TSV files into pandas DataFrames."""

import io
import pandas as pd
from pathlib import Path


def load_file(path_or_bytes, filename: str) -> pd.DataFrame:
    """
    Read an .xlsx, .xls, or .csv file and return a DataFrame.
    Supports binary Excel, openpyxl, xlrd, HTML tables, and text files (CSV/TSV)
    in UTF-16, UTF-8, etc.
    """
    ext = Path(filename).suffix.lower()
    if ext in (".xlsx", ".xls"):
        return _load_excel(path_or_bytes, filename)
    elif ext == ".csv":
        return _load_csv(path_or_bytes)
    else:
        raise ValueError(f"Unsupported file type '{ext}' for file '{filename}'.")


def _load_excel(path_or_bytes, filename: str) -> pd.DataFrame:
    ext = Path(filename).suffix.lower()
    engines_to_try = ["openpyxl", None, "xlrd"] if ext == ".xlsx" else [None, "xlrd", "openpyxl"]

    # 1. Standard pandas read_excel with engine & header variations
    for engine in engines_to_try:
        for hdr in (0, 1):
            try:
                if hasattr(path_or_bytes, "seek"):
                    path_or_bytes.seek(0)
                df = pd.read_excel(path_or_bytes, engine=engine, header=hdr, dtype=str)
                if df is not None and not df.empty and len(df.columns) > 1:
                    return df.dropna(how="all").reset_index(drop=True)
            except Exception:
                continue

    # 2. Try HTML table parsing (for ERP exports saved with .xls extension)
    try:
        if hasattr(path_or_bytes, "seek"):
            path_or_bytes.seek(0)
        dfs = pd.read_html(path_or_bytes)
        if dfs and len(dfs) > 0:
            for df in dfs:
                if not df.empty and len(df.columns) > 1:
                    df.columns = [str(c).strip() for c in df.columns]
                    return df.astype(str).dropna(how="all").reset_index(drop=True)
    except Exception:
        pass

    # 3. Try CSV / TSV text parsing fallback (for UTF-16 TSV exports from SQL Server / SAP saved as .xls)
    try:
        if hasattr(path_or_bytes, "seek"):
            path_or_bytes.seek(0)
        return _load_csv(path_or_bytes)
    except Exception:
        pass

    raise ValueError(f"Could not parse Excel file '{filename}'. Ensure it is a valid .xlsx, .xls, or CSV file.")


def _load_csv(path_or_bytes) -> pd.DataFrame:
    if isinstance(path_or_bytes, (str, Path)):
        with open(path_or_bytes, "rb") as f:
            data = f.read()
    elif hasattr(path_or_bytes, "read"):
        if hasattr(path_or_bytes, "seek"):
            path_or_bytes.seek(0)
        data = path_or_bytes.read()
    else:
        data = path_or_bytes

    if isinstance(data, bytes):
        encodings = ("utf-16", "utf-16-le", "utf-16-be", "utf-8-sig", "utf-8", "latin-1", "cp1252")
        separators = ("\t", ",", ";")
        for enc in encodings:
            try:
                decoded_str = data.decode(enc)
            except Exception:
                continue

            for sep in separators:
                for hdr in (0, 1):
                    try:
                        df = pd.read_csv(
                            io.StringIO(decoded_str), sep=sep, header=hdr, dtype=str
                        )
                        if df is not None and not df.empty and len(df.columns) > 1:
                            return df.dropna(how="all").reset_index(drop=True)
                    except Exception:
                        continue

        raise ValueError("Could not decode CSV/TSV with any known encoding or delimiter.")

    return pd.read_csv(data, dtype=str).dropna(how="all").reset_index(drop=True)
