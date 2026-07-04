"""
Item Master Analysis Module.
Combines Item Master data with Purchase Order details.
Modular design to easily add new KPIs and data points.
"""

from __future__ import annotations
import pandas as pd

# ── Helper Functions ─────────────────────────────────────────────────────────

def find_col(df: pd.DataFrame, aliases: list[str]) -> str | None:
    """Find column using case-insensitive aliases."""
    if df is None or df.empty:
        return None
    aliases_set = {a.lower().strip() for a in aliases}
    for col in df.columns:
        if str(col).lower().strip() in aliases_set:
            return col
    return None

def parse_numeric_val(val) -> float:
    """Parse numeric value safely."""
    if pd.isna(val) or val == "" or val is None:
        return 0.0
    try:
        if isinstance(val, str):
            val = val.replace(",", "").strip()
        return float(val)
    except:
        return 0.0

def normalize_id(val) -> str:
    """Normalize identifier string."""
    if pd.isna(val) or val is None:
        return ""
    val_str = str(val).strip()
    if val_str.endswith(".0"):
        val_str = val_str[:-2]
    return val_str

def clean_str_val(val, default="—") -> str:
    """Clean string value."""
    if pd.isna(val) or val is None:
        return default
    val_str = str(val).strip()
    if val_str.lower() in ("nan", "none", "null", ""):
        return default
    return val_str

# ── Column Configuration ─────────────────────────────────────────────────────

# Define item master columns to display (modular - add new columns here)
ITEM_MASTER_COLUMNS = {
    "Item No.": ["item no.", "item no", "item code", "material no", "part no"],
    "Item Description": ["item description", "description", "material description", "item name"],
    "Group Name": ["group name", "group", "item group"],
    "Purchasing Item": ["purchasing item"],
    "Sales Item": ["sales item"],
    "Inventory Item": ["inventory item"],
    "Default Warehouse": ["default warehouse", "warehouse"],
    "Preferred Vendor": ["preferred vendor", "vendor", "supplier"],
    "Purchasing UoM": ["purchasing uom", "purchasing uom", "uom"],
    "Items per Purchasing Unit": ["items per purchasing unit", "purchasing unit qty"],
    "Sales UoM": ["sales uom", "sales uom", "uom"],
    "No. of Items per Sales Unit": ["no. of items per sales unit", "sales unit qty"],
    "Valuation Method": ["valuation method", "valuation"],
    "Active": ["active", "is active"],
    "Inactive": ["inactive", "is inactive"],
    "Issue Method": ["issue method"],
    "Inventory UoM": ["inventory uom", "inventory uom"],
    "Planning Method": ["planning method"],
    "Procurement Method": ["procurement method"],
    "Group": ["group"],
    "Subgroup": ["subgroup", "sub group"],
    "ItemCodeOld": ["itemcodeold", "old item code"],
    "Item Service Type": ["item service type", "service type"],
    "Approval Status": ["approval status"],
    "Production Date": ["production date"],
}

# Columns to exclude from output
EXCLUDED_COLUMNS = {
    "set g/l accounts by",
    "wtax liable",
}

# ── KPI Calculation Functions (Modular - Add New Functions Here) ────────────

def calculate_distinct_item_codes(df_items: pd.DataFrame, col_item_no: str) -> int:
    """Calculate number of distinct item codes."""
    if col_item_no is None or df_items.empty:
        return 0
    return int(df_items[col_item_no].nunique())

def calculate_items_with_pos(df_items: pd.DataFrame, df_po: pd.DataFrame, col_item_no: str, col_po_item_code: str) -> int:
    """Calculate number of items that have purchase orders."""
    if col_item_no is None or df_items.empty or df_po is None or df_po.empty or col_po_item_code is None:
        return 0
    
    # Get unique item codes from PO
    po_items = df_po[col_po_item_code].astype(str).str.strip().str.upper().unique()
    
    # Get unique item codes from Item Master
    im_items = df_items[col_item_no].astype(str).str.strip().str.upper().unique()
    
    # Count items that appear in both
    items_with_po = set(po_items) & set(im_items)
    return len(items_with_po)

def calculate_unique_pos(df_po: pd.DataFrame, col_po_no: str) -> int:
    """Calculate number of unique purchase orders."""
    if col_po_no is None or df_po is None or df_po.empty:
        return 0
    return int(df_po[col_po_no].nunique())

# ── KPI Registry (Modular - Add New KPIs by Adding Entries Here) ────────────

KPI_DEFINITIONS = {
    "distinct_item_codes": {
        "label": "Distinct Item Codes",
        "description": "Total unique items in master",
        "func": calculate_distinct_item_codes,
        "args": ["df_items", "col_item_no"],
    },
    "items_with_pos": {
        "label": "Items Purchased",
        "description": "Items with active POs",
        "func": calculate_items_with_pos,
        "args": ["df_items", "df_po", "col_item_no", "col_po_item_code"],
    },
    "unique_pos": {
        "label": "Unique POs",
        "description": "Total unique purchase orders",
        "func": calculate_unique_pos,
        "args": ["df_po", "col_po_no"],
    },
}

# ── Main Analysis Function ───────────────────────────────────────────────────

def run(dfs_or_df: dict[str, pd.DataFrame] | pd.DataFrame) -> dict:
    """Run item master analysis."""
    # Support both DataFrame (for tests) and dict of DataFrames (for production)
    if isinstance(dfs_or_df, pd.DataFrame):
        df_items = dfs_or_df
        dfs = {"item_master": df_items}
    else:
        dfs = dfs_or_df
        df_items = dfs.get("item_master")

    if df_items is None or df_items.empty:
        return {"kpis": {}, "charts": {}, "tables": []}

    # Get Purchase Order data for joining
    df_po = dfs.get("purchase_order")
    
    # ── Detect All Columns in Item Master ────────────────────────────────────
    detected_columns = {}
    for col_display_name, aliases in ITEM_MASTER_COLUMNS.items():
        detected_col = find_col(df_items, aliases)
        if detected_col:
            detected_columns[col_display_name] = detected_col
    
    # ── Detect PO Columns ────────────────────────────────────────────────────
    col_po_no = None
    col_po_item_code = None
    col_po_qty = None
    col_po_price = None
    col_line_total = None
    
    if df_po is not None and not df_po.empty:
        col_po_no = find_col(df_po, ["po no", "po no.", "po number", "purchase order no", "purchase order number"])
        col_po_item_code = find_col(df_po, ["item code", "item_code", "item no", "item no.", "itemno"])
        col_po_qty = find_col(df_po, ["po qty", "ordered qty", "order qty", "quantity", "qty"])
        col_po_price = find_col(df_po, ["po price", "unit price", "price", "rate", "po_price"])
        col_line_total = find_col(df_po, ["line total", "linetotal", "total", "line_total"])
    
    col_item_no = detected_columns.get("Item No.")
    
    # ── Build KPIs Using Modular Registry ────────────────────────────────────
    kpis = {}
    for kpi_key, kpi_def in KPI_DEFINITIONS.items():
        try:
            func = kpi_def["func"]
            args_list = kpi_def["args"]
            
            # Build arguments for this KPI
            kwargs = {}
            for arg in args_list:
                if arg == "df_items":
                    kwargs[arg] = df_items
                elif arg == "df_po":
                    kwargs[arg] = df_po
                elif arg == "col_item_no":
                    kwargs[arg] = col_item_no
                elif arg == "col_po_item_code":
                    kwargs[arg] = col_po_item_code
                elif arg == "col_po_no":
                    kwargs[arg] = col_po_no
            
            kpis[kpi_key] = func(**kwargs)
        except Exception as e:
            kpis[kpi_key] = 0
    
    # ── Build Main Data Table with All Columns ───────────────────────────────
    table_data = []
    po_item_lookup = {}
    
    # Pre-build PO lookup for performance
    if df_po is not None and not df_po.empty and col_po_item_code:
        for _, po_row in df_po.iterrows():
            item_code = normalize_id(po_row.get(col_po_item_code)).upper()
            if item_code:
                if item_code not in po_item_lookup:
                    po_item_lookup[item_code] = []
                po_item_lookup[item_code].append(po_row)
    
    for _, item_row in df_items.iterrows():
        row = {}
        
        # Add all detected item master columns
        for col_display_name, col_actual in detected_columns.items():
            col_lower = col_display_name.lower()
            
            # Skip excluded columns
            if col_lower in EXCLUDED_COLUMNS or col_actual.lower() in EXCLUDED_COLUMNS:
                continue
            
            row[col_display_name] = clean_str_val(item_row.get(col_actual))
        
        # Add PO information if available
        if col_item_no:
            item_code = normalize_id(item_row.get(col_item_no)).upper()
            po_rows = po_item_lookup.get(item_code, [])
            
            if po_rows:
                po_row = po_rows[0]  # First matching PO
                
                row["PO Number"] = clean_str_val(po_row.get(col_po_no)) if col_po_no else "—"
                
                if col_po_qty:
                    qty_val = parse_numeric_val(po_row.get(col_po_qty))
                    row["PO Qty"] = f"{qty_val:,.0f}" if qty_val > 0 else "—"
                else:
                    row["PO Qty"] = "—"
                
                if col_po_price:
                    price_val = parse_numeric_val(po_row.get(col_po_price))
                    row["Rate"] = f"{price_val:,.2f}" if price_val > 0 else "—"
                else:
                    row["Rate"] = "—"
                
                if col_line_total:
                    total_val = parse_numeric_val(po_row.get(col_line_total))
                    row["Price"] = f"{total_val:,.2f}" if total_val > 0 else "—"
                else:
                    row["Price"] = "—"
            else:
                row["PO Number"] = "—"
                row["PO Qty"] = "—"
                row["Rate"] = "—"
                row["Price"] = "—"
        
        table_data.append(row)
    
    tables = [
        {
            "title": "Item Master with PO Details",
            "description": "Complete item master records with associated purchase order information",
            "data": table_data,  # All rows - frontend handles pagination
            "total_rows": len(table_data),
        }
    ]
    
    charts = {}
    
    return {
        "kpis": kpis,
        "charts": charts,
        "tables": tables,
    }
