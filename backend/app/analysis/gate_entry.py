"""
Gate Entry Date Integrity Analysis.

Logic (verified against client output file):
  - Source files: Gate Entry Report + GRPO Report
  - Join: GE file (all rows) LEFT JOIN GRPO on Gate Entry No
  - For each GE row take the FIRST matching GRPO item (for table display cols)
  - GRN Date  = GRPO Posting Date (from GRPO file, NOT GE file's GRN Date)
  - GRN No.   = GRPO No (from GRPO file)
  - PO No.    = PO Number from GRPO file
  - GRPO Days = GRPO Posting Date − Gate Entry Date (calendar days)

Sequence Gap classification:
  - No GRPO match              → "PO & GRN No. is Missing"
  - GRPO Days == 0             → "Same Day"
  - GRPO Days < 0              → "Exception"   (GE date AFTER GRPO date — audit flag)
  - 1 ≤ GRPO Days ≤ 3         → "Normal"
  - GRPO Days > 3              → "GRN Date Exceeds 3 Days"

KPIs (7 exactly as per client sheet):
  1. Total Gate-Entry         = unique Gate Entry Nos in GE file
  2. Total Value (INR)        = sum of all GRPO line totals for GE Nos that exist
  3. Sequence Exceptions      = unique Gate Entry Nos with "Exception" classification
  4. Exceeds 3 day window     = unique Gate Entry Nos with "GRN Date Exceeds 3 Days"
  5. Avg GRN Days             = average of GRPO Days where GRPO Days >= 0 (rounded to int)
  6. Unique PO Numbers        = unique valid PO Numbers from GRPO file (joined rows)
  7. Unique GRN (GRPO Nos.)   = unique GRPO Nos in joined result
  8. Unique GRNs with No PO   = unique GRPO Nos where PO Number is missing/blank
"""

from __future__ import annotations

import warnings
import pandas as pd
import numpy as np

warnings.simplefilter(action='ignore', category=UserWarning)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _find_col(df: pd.DataFrame, aliases: list[str]) -> str | None:
    if df is None or df.empty:
        return None
    cols_map = {str(col).lower().strip(): col for col in df.columns}
    for alias in aliases:
        a = alias.lower().strip()
        if a in cols_map:
            return cols_map[a]
    return None


def _clean(val, default="—") -> str:
    if pd.isna(val) or val is None:
        return default
    s = str(val).strip()
    if s.lower() in ("nan", "none", "null", ""):
        return default
    # Remove trailing .0 from numeric IDs stored as floats
    if s.endswith(".0") and s[:-2].lstrip("-").isdigit():
        return s[:-2]
    return s


def _parse_num(val) -> float:
    if pd.isna(val) or val is None or val == "":
        return 0.0
    try:
        if isinstance(val, str):
            val = val.replace(",", "").strip()
        return float(val)
    except Exception:
        return 0.0


def _fmt_cr(val: float) -> str:
    """Format large INR value as Cr string."""
    cr = val / 1e7
    return f"{cr:.2f} Cr"


def _fmt_date(ts) -> str:
    if ts is None or pd.isna(ts):
        return "—"
    try:
        return pd.Timestamp(ts).strftime("%d/%m/%y")
    except Exception:
        return "—"


def _parse_single_date(val):
    if pd.isna(val) or val is None or val == "":
        return pd.NaT
    try:
        dt = pd.to_datetime(val, format="%d/%m/%y", errors="coerce")
        if pd.notna(dt):
            return dt
        dt = pd.to_datetime(val, format="%d-%m-%Y", errors="coerce")
        if pd.notna(dt):
            return dt
        return pd.to_datetime(val, errors="coerce", dayfirst=True)
    except Exception:
        return pd.NaT


def _parse_date_col(series: pd.Series) -> pd.Series:
    """Try common date formats used in client ERP exports."""
    if not isinstance(series, pd.Series):
        return _parse_single_date(series)
    # Try dd/mm/yy first (GE file format)
    result = pd.to_datetime(series, format="%d/%m/%y", errors="coerce")
    # For NaTs try dd-mm-yyyy (GRPO file format)
    mask = result.isna()
    if mask.any():
        result[mask] = pd.to_datetime(series[mask], format="%d-%m-%Y", errors="coerce")
    # Final fallback
    mask2 = result.isna()
    if mask2.any():
        result[mask2] = pd.to_datetime(series[mask2], errors="coerce", dayfirst=True)
    return result


def run(dfs: dict[str, pd.DataFrame]) -> dict:
    if not isinstance(dfs, dict):
        dfs = {}

    df_ge_raw = dfs.get("gate_entry")
    df_grpo_raw = dfs.get("grpo")

    # Empty guard
    if df_ge_raw is None or df_ge_raw.empty:
        return _empty_result()

    # ── Column detection – Gate Entry ────────────────────────────────────────
    c_ge_no   = _find_col(df_ge_raw, ["gate entry no", "gate entry no.", "ge no", "gate entry number"])
    c_ge_date = _find_col(df_ge_raw, ["gate entry date", "ge date", "entry date"])
    c_ge_vc   = _find_col(df_ge_raw, ["vendor code", "bp code", "supplier code"])
    c_ge_vn   = _find_col(df_ge_raw, ["vendor name", "bp name", "supplier name"])
    c_ge_vb   = _find_col(df_ge_raw, ["vendor bill no", "vendor ref no", "bill no",
                                       "challan no", "supplier invoice no"])
    c_ge_br   = _find_col(df_ge_raw, ["branch", "branch name"])
    c_ge_cr   = _find_col(df_ge_raw, ["ge creater id", "ge creator id", "creater id",
                                       "creator id", "created by"])
    c_ge_grn  = _find_col(df_ge_raw, ["grn no.", "grn no", "grn gate entry no", "grpo no"])
    c_ge_grn_date = _find_col(df_ge_raw, ["grn date", "grn date."])

    # ── Column detection – GRPO ──────────────────────────────────────────────
    if df_grpo_raw is not None and not df_grpo_raw.empty:
        c_gp_ge_no  = _find_col(df_grpo_raw, ["gate entry no", "gate entry no.", "ge no"])
        c_gp_grpo   = _find_col(df_grpo_raw, ["grpo no", "grpo no.", "grn no", "grn no.",
                                               "receipt no", "goods receipt no"])
        c_gp_po     = _find_col(df_grpo_raw, ["po number", "po no", "po no.",
                                               "purchase order number", "purchase order no"])
        c_gp_date   = _find_col(df_grpo_raw, ["posting date", "document date", "grpo date",
                                               "receipt date", "doc date"])
        c_gp_vc     = _find_col(df_grpo_raw, ["vendor code", "bp code", "supplier code"])
        c_gp_vn     = _find_col(df_grpo_raw, ["vendor name", "bp name", "supplier name"])
        c_gp_vref   = _find_col(df_grpo_raw, ["vendor ref no", "vendor ref. no.", "vendor bill no",
                                               "bill no", "supplier invoice no"])
        c_gp_br     = _find_col(df_grpo_raw, ["branch", "branch name"])
        c_gp_cr_id  = _find_col(df_grpo_raw, ["ge creater id", "ge creator id", "created by"])
        c_gp_ic     = _find_col(df_grpo_raw, ["item code", "item no", "item no."])
        c_gp_id     = _find_col(df_grpo_raw, ["item description", "description",
                                               "item/service description", "item name"])
        c_gp_ig     = _find_col(df_grpo_raw, ["item group", "item group name", "group name"])
        c_gp_uom    = _find_col(df_grpo_raw, ["uom", "unit of measure", "purchasing uom"])
        c_gp_qty    = _find_col(df_grpo_raw, ["grpo qty", "quantity", "qty"])
        c_gp_price  = _find_col(df_grpo_raw, ["grpo price", "unit price", "price"])
        c_gp_curr   = _find_col(df_grpo_raw, ["document currency", "currency", "doc currency"])
        c_gp_rate   = _find_col(df_grpo_raw, ["document rate", "doc rate"])
        c_gp_lt     = _find_col(df_grpo_raw, ["line total", "linetotal"])
    else:
        (c_gp_ge_no, c_gp_grpo, c_gp_po, c_gp_date, c_gp_vc, c_gp_vn, c_gp_vref,
         c_gp_br, c_gp_cr_id, c_gp_ic, c_gp_id, c_gp_ig, c_gp_uom,
         c_gp_qty, c_gp_price, c_gp_curr, c_gp_rate, c_gp_lt) = [None] * 18

    # ── Parse Gate Entry dates and sort numerically ─────────────────────────
    df_ge = df_ge_raw.copy()
    if c_ge_no:
        df_ge["_ge_no_str"] = df_ge[c_ge_no].astype(str).str.strip().str.replace(".0", "", regex=False)
        df_ge["_ge_num"] = pd.to_numeric(df_ge["_ge_no_str"], errors="coerce")
        df_ge = df_ge.sort_values("_ge_num", kind="stable").reset_index(drop=True)
    else:
        df_ge["_ge_no_str"] = ""

    if c_ge_date:
        df_ge["_ge_date"] = _parse_date_col(df_ge[c_ge_date])
    else:
        df_ge["_ge_date"] = pd.NaT

    # ── Build GRPO lookups (GE No lookup and GRN No lookup) ─────────────────
    grpo_first_by_ge: dict = {}
    grpo_first_by_grn: dict = {}
    grpo_sumlt_by_ge: dict = {}

    if df_grpo_raw is not None and not df_grpo_raw.empty:
        df_grpo = df_grpo_raw.copy()
        if c_gp_ge_no:
            df_grpo["_ge_no_str"] = df_grpo[c_gp_ge_no].astype(str).str.strip().str.replace(".0", "", regex=False)
        else:
            df_grpo["_ge_no_str"] = ""

        if c_gp_grpo:
            df_grpo["_grpo_no_str"] = df_grpo[c_gp_grpo].astype(str).str.strip().str.replace(".0", "", regex=False)
        else:
            df_grpo["_grpo_no_str"] = ""

        if c_gp_date:
            df_grpo["_posting_date"] = _parse_date_col(df_grpo[c_gp_date])
        else:
            df_grpo["_posting_date"] = pd.NaT

        if c_gp_lt:
            df_grpo["_lt_num"] = df_grpo[c_gp_lt].astype(str).str.replace(",", "")
            df_grpo["_lt_num"] = pd.to_numeric(df_grpo["_lt_num"], errors="coerce").fillna(0.0)
        else:
            df_grpo["_lt_num"] = 0.0

        if c_gp_ge_no:
            lt_by_ge = df_grpo.groupby("_ge_no_str")["_lt_num"].sum()
            grpo_sumlt_by_ge = lt_by_ge.to_dict()

            grpo_first_df = df_grpo.groupby("_ge_no_str", sort=False).first().reset_index()
            for _, row in grpo_first_df.iterrows():
                ge_key = row["_ge_no_str"]
                if ge_key and ge_key not in ("nan", "None", ""):
                    grpo_first_by_ge[ge_key] = row

        if c_gp_grpo:
            grpo_grn_df = df_grpo.groupby("_grpo_no_str", sort=False).first().reset_index()
            for _, row in grpo_grn_df.iterrows():
                grn_key = row["_grpo_no_str"]
                if grn_key and grn_key not in ("nan", "None", ""):
                    grpo_first_by_grn[grn_key] = row

    def _total_value_for_ge(ge_no: str) -> float:
        return grpo_sumlt_by_ge.get(ge_no, 0.0)

    # ── Classify sequence gap ─────────────────────────────────────────────────
    def _classify(ge_date, grpo_posting_date, has_grpo: bool) -> tuple[str, int]:
        """Returns (label, grpo_days)."""
        if not has_grpo:
            return "PO & GRN No. is Missing", None
        if pd.isna(ge_date) or pd.isna(grpo_posting_date):
            return "PO & GRN No. is Missing", None
        days = int((pd.Timestamp(grpo_posting_date) - pd.Timestamp(ge_date)).days)
        if days == 0:
            return "Same Day", 0
        if days < 0:
            return "Exception", days
        if 1 <= days <= 3:
            return "Normal", days
        return "GRN Date Exceeds 3 Days", days

    # ── Build result table rows ───────────────────────────────────────────────
    rows = []
    for _, ge_row in df_ge.iterrows():
        ge_no_str = ge_row["_ge_no_str"]
        ge_date   = ge_row["_ge_date"]
        if not ge_no_str or ge_no_str in ("nan", "None", ""):
            continue

        # Step 1: GE -> GRPO lookup by Gate Entry No
        ge_grpo_row = grpo_first_by_ge.get(ge_no_str)
        
        # Determine GRN No
        grn_no = "—"
        if ge_grpo_row is not None and c_gp_grpo:
            grn_no = _clean(ge_grpo_row.get(c_gp_grpo))
        if (not grn_no or grn_no in ("—", "nan", "None", "")) and c_ge_grn:
            grn_no = _clean(ge_row.get(c_ge_grn))
            
        # Determine GRN Date
        grpo_post = pd.NaT
        if ge_grpo_row is not None:
            grpo_post = ge_grpo_row.get("_posting_date")
        if pd.isna(grpo_post) and c_ge_grn_date:
            grpo_post = _parse_date_col(ge_row.get(c_ge_grn_date))

        has_grpo = (ge_grpo_row is not None) or (grn_no != "—" and grn_no in grpo_first_by_grn)
        
        # Step 2: GRN -> GRPO lookup by GRN No for item & financial details
        grn_grpo_row = grpo_first_by_grn.get(grn_no) if grn_no != "—" else None
        target_grpo_row = grn_grpo_row if grn_grpo_row is not None else ge_grpo_row

        seq_gap, grpo_days = _classify(ge_date, grpo_post, has_grpo)

        def _gf(col, default="—"):
            if target_grpo_row is None or col is None:
                return default
            return _clean(target_grpo_row.get(col, default), default)

        po_no     = _gf(c_gp_po, "0")
        item_code = _gf(c_gp_ic)
        item_desc = _gf(c_gp_id)
        item_group= _gf(c_gp_ig)
        uom       = _gf(c_gp_uom)

        grpo_qty_raw = target_grpo_row.get(c_gp_qty) if (target_grpo_row is not None and c_gp_qty) else None
        grpo_price_raw = target_grpo_row.get(c_gp_price) if (target_grpo_row is not None and c_gp_price) else None
        doc_curr  = _gf(c_gp_curr)
        doc_rate_raw = target_grpo_row.get(c_gp_rate) if (target_grpo_row is not None and c_gp_rate) else None
        line_total_raw = target_grpo_row.get("_lt_num") if target_grpo_row is not None else 0.0

        grpo_qty   = _parse_num(grpo_qty_raw)
        grpo_price = _parse_num(grpo_price_raw)
        doc_rate   = _parse_num(doc_rate_raw) if doc_rate_raw is not None else 1.0
        if doc_rate <= 0:
            doc_rate = 1.0
        value      = _parse_num(line_total_raw)

        # Vendor / branch / creator from GRPO (fallback to GE)
        vcode = (_gf(c_gp_vc) if c_gp_vc else "—") or _clean(ge_row.get(c_ge_vc, ""), "—")
        if not vcode or vcode == "—":
            vcode = _clean(ge_row.get(c_ge_vc, ""), "—")
        vname = (_gf(c_gp_vn) if c_gp_vn else "—") or _clean(ge_row.get(c_ge_vn, ""), "—")
        if not vname or vname == "—":
            vname = _clean(ge_row.get(c_ge_vn, ""), "—")
        vbill = (_gf(c_gp_vref) if c_gp_vref else "—")
        if not vbill or vbill == "—":
            vbill = _clean(ge_row.get(c_ge_vb, ""), "—")
        branch  = (_gf(c_gp_br) if c_gp_br else "—")
        if not branch or branch == "—":
            branch = _clean(ge_row.get(c_ge_br, ""), "—")
        creator = (_gf(c_gp_cr_id) if c_gp_cr_id else "—")
        if not creator or creator == "—":
            creator = _clean(ge_row.get(c_ge_cr, ""), "—")

        rows.append({
            "Gate Entry No": ge_no_str,
            "Gate Entry Date": _fmt_date(ge_date),
            "GRN Date": _fmt_date(grpo_post),
            "GRN No.": grn_no,
            "PO No.": po_no,
            "Sequence Gap": seq_gap,
            "GRPO Days": grpo_days if grpo_days is not None else "—",
            "Vendor Code": vcode,
            "Vendor Name": vname,
            "Vendor Bill No": vbill,
            "Branch": branch,
            "GE Creater ID": creator,
            "Item Code": item_code,
            "Item Description": item_desc,
            "Item Group": item_group,
            "UOM": uom,
            "GRPO Qty": grpo_qty,
            "GRPO Price": grpo_price,
            "Document Currency": doc_curr,
            "Document Rate": doc_rate,
            "Value": value,
            # Flags for chart usage
            "_is_exception": 1 if seq_gap == "Exception" else 0,
            "_exceeds_3d": 1 if seq_gap == "GRN Date Exceeds 3 Days" else 0,
            "_missing": 1 if seq_gap == "PO & GRN No. is Missing" else 0,
        })

    # ── KPI Calculations ──────────────────────────────────────────────────────
    total_ge_unique = df_ge["_ge_no_str"].nunique()

    # Total Value = sum of ALL line totals from GRPO for every Gate Entry No in GE file
    unique_ge_nos = set(df_ge["_ge_no_str"].unique())
    total_value = sum(_total_value_for_ge(g) for g in unique_ge_nos if g not in ("nan","None",""))

    # Sequence Exceptions = unique Gate Entry Nos classified as Exception
    exc_ge_nos = set(r["Gate Entry No"] for r in rows if r["_is_exception"] == 1)
    seq_exceptions = len(exc_ge_nos)

    # Exceeds 3 day window = unique Gate Entry Nos with GRN Date Exceeds 3 Days
    exc3_ge_nos = set(r["Gate Entry No"] for r in rows if r["_exceeds_3d"] == 1)
    exceeds_3d = len(exc3_ge_nos)

    # Avg GRN Days (rounded to int, from all rows with numeric GRPO Days >= 0)
    valid_days = [r["GRPO Days"] for r in rows
                  if isinstance(r["GRPO Days"], (int, float)) and r["GRPO Days"] >= 0]
    avg_grn_days = int(round(sum(valid_days) / len(valid_days))) if valid_days else 0

    # Unique PO Numbers (valid, non-blank, non-zero)
    unique_po = set(r["PO No."] for r in rows
                    if r["PO No."] and r["PO No."] not in ("—", "", "nan", "None", "0"))
    unique_po_count = len(unique_po)

    # Unique GRN (GRPO Nos.) in joined rows
    unique_grn = set(r["GRN No."] for r in rows
                     if r["GRN No."] and r["GRN No."] not in ("—", "", "nan", "None"))
    unique_grn_count = len(unique_grn)

    # Unique GRNs with No PO Number
    no_po_grns = set(r["GRN No."] for r in rows
                     if r["GRN No."] not in ("—", "", "nan", "None")
                     and (not r["PO No."] or r["PO No."] in ("—", "", "nan", "None")))
    unique_no_po_grn = len(no_po_grns)

    # Charts (Unique Gate Entry counts matching 7 KPIs)
    total_rows = len(rows)
    
    # Row counts (total line items)
    same_day_rows  = sum(1 for r in rows if r["Sequence Gap"] == "Same Day")
    normal_rows    = sum(1 for r in rows if r["Sequence Gap"] == "Normal")
    exception_rows = sum(1 for r in rows if r["Sequence Gap"] == "Exception")
    exc_3d_rows    = sum(1 for r in rows if r["Sequence Gap"] == "GRN Date Exceeds 3 Days")
    missing_rows   = sum(1 for r in rows if r["Sequence Gap"] == "PO & GRN No. is Missing")

    # Unique Gate Entry counts (matching KPI cards)
    same_day_ge  = len(set(r["Gate Entry No"] for r in rows if r["Sequence Gap"] == "Same Day"))
    normal_ge    = len(set(r["Gate Entry No"] for r in rows if r["Sequence Gap"] == "Normal"))
    exception_ge = len(set(r["Gate Entry No"] for r in rows if r["_is_exception"] == 1)) # 22
    exc_3d_ge    = len(set(r["Gate Entry No"] for r in rows if r["_exceeds_3d"] == 1))    # 17
    missing_ge   = len(set(r["Gate Entry No"] for r in rows if r["_missing"] == 1))       # 5

    pass_count_ge = total_ge_unique - exception_ge
    integrity_pct = round(pass_count_ge / total_ge_unique * 100, 1) if total_ge_unique else 100.0

    CIRC = 314.0
    pass_dash = round(pass_count_ge / total_ge_unique * CIRC) if total_ge_unique else 0
    exc_dash  = round(exception_ge / total_ge_unique * CIRC) if total_ge_unique else 0

    # Clean rows for frontend (remove internal flags)
    clean_rows = []
    for r in rows:
        row_out = {k: v for k, v in r.items() if not k.startswith("_")}
        clean_rows.append(row_out)

    return {
        "kpis": {
            # 7 KPIs matching client output file exactly
            "total_gate_entry": total_ge_unique,
            "total_value_inr": total_value,
            "sequence_exceptions": seq_exceptions,
            "exceeds_3_day_window": exceeds_3d,
            "avg_grn_days": avg_grn_days,
            "unique_po_numbers": unique_po_count,
            "unique_grn_nos": unique_grn_count,
            "unique_grns_no_po": unique_no_po_grn,
            # Legacy aliases
            "gate_entries": total_ge_unique,
            "exceptions": seq_exceptions,
            "ge_gt_grpo": exception_ge,
            "ge_lt_grpo": normal_ge,
            "ge_eq_grpo": same_day_ge,
            "missing_grpo_date": missing_ge,
            "integrity_pct": integrity_pct,
        },
        "charts": {
            "pass_vs_exception": {
                "total": total_ge_unique,
                "integrity_pct": integrity_pct,
                "segments": [
                    {"label": "Pass (Correct Order)",   "value": pass_count_ge, "dash": pass_dash, "offset": 0},
                    {"label": "Exception (GE > GRPO)",  "value": exception_ge,  "dash": exc_dash,  "offset": -pass_dash},
                ],
            },
            "detailed_checks": [
                {"label": "Total Unique Gate Entries","value": total_ge_unique, "pct": 100},
                {"label": "GE = GRPO (same)",         "value": same_day_ge,     "pct": round(same_day_ge  / total_ge_unique * 100, 1) if total_ge_unique else 0},
                {"label": "GE < GRPO (normal)",       "value": normal_ge,       "pct": round(normal_ge    / total_ge_unique * 100, 1) if total_ge_unique else 0},
                {"label": "GE > GRPO (exception)",    "value": exception_ge,    "pct": round(exception_ge / total_ge_unique * 100, 1) if total_ge_unique else 0},
                {"label": "GRN Date Exceeds 3 Days",  "value": exc_3d_ge,       "pct": round(exc_3d_ge    / total_ge_unique * 100, 1) if total_ge_unique else 0},
                {"label": "PO & GRN No. is Missing",  "value": missing_ge,      "pct": round(missing_ge   / total_ge_unique * 100, 1) if total_ge_unique else 0},
            ],
            "row_level_checks": [
                {"label": "Total Line Items",         "value": total_rows,     "pct": 100},
                {"label": "GE = GRPO (same)",         "value": same_day_rows,  "pct": round(same_day_rows  / total_rows * 100, 1) if total_rows else 0},
                {"label": "GE < GRPO (normal)",       "value": normal_rows,    "pct": round(normal_rows    / total_rows * 100, 1) if total_rows else 0},
                {"label": "GE > GRPO (exception)",    "value": exception_rows, "pct": round(exception_rows / total_rows * 100, 1) if total_rows else 0},
                {"label": "GRN Date Exceeds 3 Days",  "value": exc_3d_rows,    "pct": round(exc_3d_rows    / total_rows * 100, 1) if total_rows else 0},
                {"label": "PO & GRN No. is Missing",  "value": missing_rows,   "pct": round(missing_rows   / total_rows * 100, 1) if total_rows else 0},
            ]
        },
        "tables": [
            {
                "title": "Gate Entry Check",
                "rows": clean_rows,
            },
            {
                "title": "Sequence Exceptions (GE > GRPO)",
                "rows": [r for r in clean_rows if r["Sequence Gap"] == "Exception"],
            },
            {
                "title": "GRN Date Exceeds 3 Days",
                "rows": [r for r in clean_rows if r["Sequence Gap"] == "GRN Date Exceeds 3 Days"],
            },
        ],
    }


def _empty_result() -> dict:
    return {
        "kpis": {
            "total_gate_entry": 0,
            "total_value_inr": 0,
            "sequence_exceptions": 0,
            "exceeds_3_day_window": 0,
            "avg_grn_days": 0,
            "unique_po_numbers": 0,
            "unique_grn_nos": 0,
            "unique_grns_no_po": 0,
            "gate_entries": 0,
            "exceptions": 0,
            "ge_gt_grpo": 0,
            "ge_lt_grpo": 0,
            "ge_eq_grpo": 0,
            "missing_grpo_date": 0,
            "integrity_pct": 100.0,
        },
        "charts": {
            "pass_vs_exception": {
                "total": 0,
                "integrity_pct": 100.0,
                "segments": [
                    {"label": "Pass (Correct Order)",  "value": 0, "dash": 0, "offset": 0},
                    {"label": "Exception (GE > GRPO)", "value": 0, "dash": 0, "offset": 0},
                ],
            },
            "detailed_checks": [],
        },
        "tables": [
            {"title": "Gate Entry Check", "rows": []},
            {"title": "Sequence Exceptions (GE > GRPO)", "rows": []},
            {"title": "GRN Date Exceeds 3 Days", "rows": []},
        ],
    }
