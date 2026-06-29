import pytest
import pandas as pd
from app.analysis.price_variance_new import run_variance_analysis

def test_price_variance_cross_vendor():
    # Setup mock data for PO
    po_df = pd.DataFrame({
        "PO No": ["PO001", "PO002", "PO003"],
        "Vendor Code": ["V001", "V002", "V003"],
        "Vendor Name": ["Vendor One", "Vendor Two", "Vendor Three"],
        "Item Code": ["ITEM001", "ITEM001", "ITEM002"],
        "Item Description": ["LED Bulb 10W", "LED Bulb 10W", "LED Tube 20W"],
        "Item Group": ["Lighting", "Lighting", "Lighting"],
        "UOM": ["PCS", "PCS", "PCS"],
        "PO Qty": ["10", "20", "30"],
        "PO Price": ["100.0", "120.0", "150.0"],
        "Document Currency": ["INR", "INR", "INR"],
        "Document Rate": ["1.0", "1.0", "1.0"]
    })

    # Setup mock data for GRPO
    grpo_df = pd.DataFrame({
        "PO Number": ["PO001", "PO002", "PO003"],
        "Item Code": ["ITEM001", "ITEM001", "ITEM002"],
        "GRPO No": ["GRN001", "GRN002", "GRN003"],
        "PO Qty": ["10", "15", "30"] # received qty
    })

    dfs = {
        "purchase_order": po_df,
        "grpo": grpo_df
    }

    result = run_variance_analysis(dfs, "cross")
    rows = result["rows"]
    kpis = result["kpis"]

    # PO001 and PO002 both have item "LED Bulb 10W"
    # Prices in INR are:
    # PO001: 100.0 (Min: 100.0, Max: 120.0) -> position: Highest (since it matches min)
    # PO002: 120.0 (Min: 100.0, Max: 120.0) -> position: Lowest (since it matches max)
    # %age above lowest:
    # PO001: 0%
    # PO002: 20%
    # Higher>5%:
    # PO001: 0
    # PO002: 1

    assert len(rows) == 3
    
    # Check that sorting groups the same item description together
    assert rows[0]["item_description"] == "LED Bulb 10W"
    assert rows[1]["item_description"] == "LED Bulb 10W"
    assert rows[2]["item_description"] == "LED Tube 20W"

    row_po001 = next(r for r in rows if r["vendor_code"] == "V001")
    row_po002 = next(r for r in rows if r["vendor_code"] == "V002")
    row_po003 = next(r for r in rows if r["vendor_code"] == "V003")

    assert row_po001["vendor_position"] == "Highest" # because rate == min_rate
    assert row_po002["vendor_position"] == "Lowest"  # because rate == max_rate
    assert row_po003["vendor_position"] == "—"       # because max_rate == min_rate (only 1 price)

    assert row_po001["pct_above_lowest"] == 0.0
    assert row_po002["pct_above_lowest"] == 20.0
    assert row_po003["pct_above_lowest"] == 0.0

    assert row_po001["higher_gt_5"] == 0
    assert row_po002["higher_gt_5"] == 1
    assert row_po003["higher_gt_5"] == 0

    assert row_po001["uom_consistency"] == 1
    assert row_po002["uom_consistency"] == 1
    assert row_po003["uom_consistency"] == 1

    assert kpis["vendor_items"] == 3
    assert kpis["variance_lines"] == 1
