"""Central configuration — tolerances, limits, penalty rates, file roles."""

# Analysis constants
VARIANCE_TOLERANCE_PCT = 5.0       # qty/price variance threshold
MSME_PAYMENT_LIMIT_DAYS = 45       # MSMED Act §16
MSME_PENALTY_RATE_PA = 0.27        # 27% p.a. (3 × RBI Bank Rate 9%)
SERVICES_ITEM_PREFIX = "SV"        # Item codes starting with this = services

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
