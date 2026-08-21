"""Central configuration — tolerances, limits, penalty rates, file roles."""

# Analysis constants
VARIANCE_TOLERANCE_PCT = 5.0       # qty/price variance threshold
MSME_PAYMENT_LIMIT_DAYS = 45       # MSMED Act §16
MSME_PENALTY_RATE_PA = 0.27        # 27% p.a. (3 × RBI Bank Rate 9%)
SERVICES_ITEM_PREFIX = "SV"        # Item codes starting with this = services

ENTITY_OPTIONS = ["ITL", "ISPL"]
PROCESS_OPTIONS = ["P2P", "Consumption"]

# Default / legacy FILE_ROLES dictionary for backward compatibility
FILE_ROLES = {
    "vendor_master":     "BP Master",
    "purchase_order":    "Purchase Order Report",
    "gate_entry":        "Gate Entry Report",
    "grpo":              "GRPO Report",
    "purchase_register": "Purchase Register",
    "general_ledger":    "General Ledger",
    "ap_credit_note":    "AP Credit Note",
    "ap_invoice_report": "AP Invoice Report",
    "item_master":       "Item Master",
}

# Comprehensive registry of file slots by (Entity, Process)
FILE_SLOTS_REGISTRY = {
    ("ITL", "P2P"): [
        {"role": "ap_credit_note", "label": "AP Credit Note", "desc": "ITL Credit memos and invoice adjustments", "icon": "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"},
        {"role": "ap_invoice_report", "label": "AP Invoice Report", "desc": "ITL Accounts payable invoice ledger", "icon": "M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"},
        {"role": "vendor_master", "label": "BP Master", "desc": "ITL Business Partner / Vendor master file", "icon": "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"},
        {"role": "gate_entry", "label": "Gate Entry Report", "desc": "ITL Security gate material entry logs", "icon": "M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"},
        {"role": "general_ledger", "label": "General Ledger", "desc": "ITL Full accounts and financial journal", "icon": "M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"},
        {"role": "grpo", "label": "GRPO Report", "desc": "ITL Goods Receipt Purchase Orders (receipts)", "icon": "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"},
        {"role": "item_master", "label": "Item Master", "desc": "ITL Material master codes and attributes", "icon": "M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"},
        {"role": "purchase_order", "label": "Purchase Order Report", "desc": "ITL PO header and line items detail", "icon": "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"},
        {"role": "purchase_register", "label": "Purchase Register", "desc": "ITL Tax invoice registration registry", "icon": "M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"},
    ],
    ("ISPL", "P2P"): [
        {"role": "ap_credit_note", "label": "AP Credit Note", "desc": "Credit memos and invoice adjustments", "icon": "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"},
        {"role": "ap_invoice_report", "label": "AP Invoice Report", "desc": "Accounts payable invoice ledger", "icon": "M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"},
        {"role": "vendor_master", "label": "BP Master", "desc": "Business Partner / Vendor master file", "icon": "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"},
        {"role": "gate_entry", "label": "Gate Entry Report", "desc": "Security gate material entry logs", "icon": "M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"},
        {"role": "general_ledger", "label": "General Ledger", "desc": "Full accounts and financial journal", "icon": "M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"},
        {"role": "grpo", "label": "GRPO Report", "desc": "Goods Receipt Purchase Orders (receipts)", "icon": "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"},
        {"role": "item_master", "label": "Item Master", "desc": "Material master codes and attributes", "icon": "M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"},
        {"role": "purchase_order", "label": "Purchase Order Report", "desc": "PO header and line items detail", "icon": "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"},
        {"role": "purchase_register", "label": "Purchase Register", "desc": "Tax invoice registration registry", "icon": "M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"},
    ],
    ("ISPL", "Consumption"): [
        {"role": "bom_report", "label": "BOM Report", "desc": "Bill of Materials structural breakdown and standard rates", "icon": "M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"},
        {"role": "production_order", "label": "Production Order Report", "desc": "Work order issuance and planned vs actual qty", "icon": "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"},
        {"role": "receipt_from_production", "label": "Receipt from Production Report", "desc": "Finished goods production receipts and yield logs", "icon": "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"},
        {"role": "goods_issue", "label": "Goods Issue Report", "desc": "Raw material issue and consumption entries", "icon": "M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"},
    ],
    ("ITL", "Consumption"): [
        {"role": "bom_report", "label": "BOM Report", "desc": "Bill of Materials report", "icon": "M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"},
        {"role": "production_order", "label": "Production Order Report", "desc": "Production order status & details", "icon": "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"},
        {"role": "receipt_from_production", "label": "Receipt from Production Report", "desc": "Receipt from production report", "icon": "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"},
    ]
}

def get_file_slots(entity: str = "ITL", process: str = "P2P") -> list[dict]:
    ent = entity.upper() if entity else "ITL"
    prc = "Consumption" if process and process.upper() == "CONSUMPTION" else "P2P"
    key = (ent, prc)
    if key in FILE_SLOTS_REGISTRY:
        return FILE_SLOTS_REGISTRY[key]
    return FILE_SLOTS_REGISTRY[("ITL", "P2P")]

def get_file_roles_dict(entity: str = "ITL", process: str = "P2P") -> dict[str, str]:
    slots = get_file_slots(entity, process)
    return {item["role"]: item["label"] for item in slots}


# Canonical alias dict.
# ORDERING RULE: when multiple canonicals share the same alias string,
# LAST-WRITER WINS because detect_columns iterates in insertion order and
# later entries overwrite earlier ones. Therefore, the canonical you most
# want to "own" a given alias must appear LATEST in this dict.
#
# Ordering principles:
#   1. Shared/generic cross-file canonicals (vendor_code) first.
#   2. "Less specific" file-role canonicals (pr_po_no, grpo_base_po) before
#      the primary canonical (po_no) so that po_no wins for "PO No".
#   3. File-section overrides last.
COLUMN_ALIASES = {
    # ── Shared / universal ───────────────────────────────────────────────────
    "vendor_code":      ["vendor code", "bp code", "supplier code", "vendorcode",
                         "bpcode", "account code", "accountcode", "vendor"],
    "vendor_name":      ["vendor name", "bp name", "supplier name", "vendorname",
                         "bpname", "account name", "accountname", "party name", "name"],

    # ── Ambiguous cross-file canonicals (lower priority — overridden later) ──
    # pr_po_no and grpo_base_po both alias "po no" but po_no comes LAST → wins
    "pr_po_no":         ["base document", "base ref", "base po no", "po number",
                         "purchase order no", "order no", "po no", "po no."],
    "grpo_base_po":     ["base ref.", "base doc no", "po no", "po no.",
                         "purchase order no", "order no"],
    # gate_entry_no comes before ge_no → ge_no wins for "gate entry no"
    "gate_entry_no":    ["gate entry no", "ge no", "gate entry number",
                         "gateentryno", "security entry no", "linked gate entry",
                         "gate no", "entry no"],
    # ge_grpo_no comes before grpo_no → grpo_no wins for "grpo no"
    "ge_grpo_no":       ["grpo no", "grpo no.", "linked grpo", "base grpo no",
                         "grpo number"],

    # ── PO-specific (po_no is LAST to win "po no") ───────────────────────────
    "item_code":        ["item no.", "item no", "item code", "material no",
                         "part no", "part number", "itemcode", "material code",
                         "material number"],
    "item_description": ["item description", "description", "material description",
                         "part description", "descript", "item name"],
    "po_qty":           ["po qty", "ordered qty", "order qty", "orderqty",
                         "quantiy", "quantity", "qty"],
    "unit_price":       ["unit price", "unitprice", "price per unit",
                         "unit rate", "unitrate"],
    "invoice_amount":   ["invoice amount", "amount", "net amount", "total amount",
                         "invoice total", "payable amount", "doc total",
                         "base amount"],
    "line_total":       ["line total", "linetotal", "line amount", "u_total",
                         "total"],
    "open_qty":         ["open qty", "outstanding qty", "remaining qty",
                         "openqty", "balance qty", "open quantity",
                         "remaining quantity"],
    "po_date":          ["po date", "order date", "podate"],
    "posting_date":     ["posting date", "document date", "doc date", "docdate",
                         "date"],
    "po_status":        ["po status", "order status", "status"],
    "po_no":            ["po no", "po no.", "po number", "purchase order no",
                         "purchase order number", "docnum", "docentry",
                         "order number", "doc no", "order no", "document no"],

    # ── GRPO (grpo_no last → wins over ge_grpo_no for "grpo no") ────────────
    "grpo_qty":         ["received qty", "receipt qty", "grpo qty",
                         "received quantity", "grpoqty"],
    "grpo_rate":        ["grpo rate", "receipt rate", "received rate",
                         "item price", "unit cost", "rate", "price"],
    "grpo_amount":      ["grpo amount", "receipt amount", "grpo total"],
    "grpo_date":        ["grpo date", "receipt date", "grpodate"],
    "grpo_no":          ["grpo no", "grpo no.", "receipt no", "receipt number",
                         "grpono", "goods receipt no", "grpo number"],

    # ── Gate Entry (ge_no last → wins over gate_entry_no for "gate entry no") ─
    "ge_date":          ["ge date", "gate entry date", "entry date",
                         "security date"],
    "vendor_bill_date": ["vendor bill date", "bill date",
                         "supplier invoice date", "vendor inv date",
                         "vend bill date"],
    "vendor_bill_no":   ["vendor bill no", "bill no",
                         "supplier invoice no", "vendor inv no"],
    "ge_no":            ["gate entry no", "gate entry no.", "ge no", "ge no.",
                         "gate entry number", "security entry no",
                         "security entry number"],

    # ── Purchase Register ─────────────────────────────────────────────────────
    "invoice_no":       ["invoice no", "invoice no.", "ap invoice no",
                         "ap no", "inv no", "invoice number"],
    "invoice_date":     ["invoice date", "inv date", "ap date"],
    "due_date":         ["due date", "payment due date", "pay due date",
                         "duedate", "maturity date"],
    "payment_date":     ["payment date", "paid date", "clearing date",
                         "payment clearing date", "value date", "paid on"],
    "payment_terms":    ["payment terms", "pay terms", "credit days",
                         "credit period", "terms"],

    # ── General Ledger ────────────────────────────────────────────────────────
    "gl_date":          ["transaction date", "gl date"],
    "debit":            ["debit", "dr amount", "debit amount", "dr", "debit amt"],
    "credit":           ["credit", "cr amount", "credit amount", "cr", "credit amt"],
    "gl_ref":           ["invoice ref", "reference", "doc ref",
                         "document reference", "ref no", "narration",
                         "transaction ref", "remarks", "particulars"],
    "trans_type":       ["transaction type", "trans type", "tran type",
                         "trans", "voucher type", "type"],

    # ── Vendor Master ─────────────────────────────────────────────────────────
    "msme_category":    ["msme reg", "msme category", "msme type",
                         "enterprise type", "msmereg", "msme registration",
                         "udyam category", "udyam type", "msme status",
                         "enterprise category"],
    "gstin":            ["gstin", "gst number", "gst no", "gst", "gstin no",
                         "tax id", "gst id"],
    "pan":              ["pan", "pan no", "pan number", "permanent account number"],
    "state":            ["state", "state code", "location", "registered state"],
}
