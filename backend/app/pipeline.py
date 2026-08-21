"""
Pipeline: load → clean → run all modules → assemble output contract.
Yields SSE progress events as each stage completes.
"""

from __future__ import annotations

import io
from typing import AsyncGenerator, Callable, Any

from app.loaders import load_file
from app.session import Session
from app.analysis import (
    po_status, gate_entry, grn_to_ap, qty_variance, price_variance,
    gl_balances, payment_aging, msme, vendor_master, item_master,
    grpo_exceptions, three_way, executive,
)


async def run_pipeline(
    session: Session,
    emit: Callable[[str, int, str], Any],
    dfs_override: dict[str, pd.DataFrame] = None,
    entity: str = "ISPL",
    process: str = "P2P",
) -> dict:
    """
    emit(stage, pct, message) is called at each step.
    Returns the full output contract dict.
    """
    entity_clean = entity.upper() if entity else "ISPL"
    process_clean = process.upper() if process else "P2P"

    if dfs_override is not None:
        dfs = dfs_override
    else:
        files = session.files

        # ── Load DataFrames ──────────────────────────────────────────────────────
        await emit("loading", 5, "Validating data sources…")

        dfs = {}
        for role, uf in files.items():
            try:
                df = load_file(io.BytesIO(uf.data), uf.filename)
                dfs[role] = df
            except Exception as exc:
                raise ValueError(f"Failed to read {uf.filename} ({role}): {exc}") from exc

    # Run P2P analysis pipeline for P2P process (ISPL or ITL)
    if process_clean == "P2P":
        await emit("loading", 12, "Cleaning and normalising columns…")

        results: dict = {}
        cover_kpis: dict = {}

        # Cover KPIs — just row counts from each file
        role_labels = {
            "purchase_order":    "purchase_orders",
            "grpo":              "grpo_documents",
            "gate_entry":        "gate_entries",
            "purchase_register": "ap_invoices",
            "general_ledger":    "gl_transactions",
            "vendor_master":     "vendor_records",
        }
        for role, label in role_labels.items():
            cover_kpis[label] = len(dfs[role]) if role in dfs else 0

        # Active vendors = unique vendor codes in purchase_register
        if "purchase_register" in dfs:
            from app.cleaning import detect_columns, rename_canonical
            m = detect_columns(dfs["purchase_register"])
            if "pr_vendor_code" in m:
                cover_kpis["active_vendors"] = int(
                    dfs["purchase_register"][m["pr_vendor_code"]].nunique()
                )
            else:
                cover_kpis["active_vendors"] = 0
        else:
            cover_kpis["active_vendors"] = 0

        results["cover"] = {"kpis": cover_kpis}

        # ── PO Status ────────────────────────────────────────────────────────────
        await emit("po_status", 18, "Running PO status analysis…")
        if "purchase_order" in dfs:
            try:
                results["postatus"] = po_status.run(dfs)
            except Exception as e:
                results["postatus"] = {"error": str(e), "kpis": {}, "charts": {}, "tables": []}

        # ── Gate Entry ───────────────────────────────────────────────────────────
        await emit("gate_entry", 28, "Checking gate-entry date integrity…")
        if "gate_entry" in dfs:
            try:
                results["gateentry"] = gate_entry.run(dfs)
            except Exception as e:
                results["gateentry"] = {"error": str(e), "kpis": {}, "charts": {}, "tables": []}

        # ── GRN to AP Invoice Check ──────────────────────────────────────────────
        await emit("grn_to_ap", 36, "Building GRN to AP Invoice reconciliation table…")
        if "grpo" in dfs:
            try:
                results["grntoap"] = grn_to_ap.run(dfs)
            except Exception as e:
                results["grntoap"] = {"error": str(e), "kpis": {}, "charts": {}, "tables": []}

        # ── Quantity Variance ────────────────────────────────────────────────────
        await emit("qty_variance", 38, "Analysing quantity variances…")
        if "purchase_order" in dfs and "grpo" in dfs:
            try:
                results["qtyvariance"] = qty_variance.run(dfs["purchase_order"], dfs["grpo"])
            except Exception as e:
                results["qtyvariance"] = {"error": str(e), "kpis": {}, "charts": {}, "tables": []}

        # ── Price Variance ───────────────────────────────────────────────────────
        await emit("price_variance", 48, "Checking pricing exceptions…")
        if "grpo" in dfs:
            try:
                results["pricevariance"] = price_variance.run(dfs["grpo"])
            except Exception as e:
                results["pricevariance"] = {"error": str(e), "kpis": {}, "charts": {}, "tables": []}

        # ── GL Balances ──────────────────────────────────────────────────────────
        await emit("gl_balances", 56, "Computing GL vendor balances…")
        if "general_ledger" in dfs:
            try:
                results["glbalances"] = gl_balances.run(dfs["general_ledger"])
            except Exception as e:
                results["glbalances"] = {"error": str(e), "kpis": {}, "charts": {}, "tables": []}

        # ── Payment Aging ────────────────────────────────────────────────────────
        await emit("payment_aging", 64, "Calculating payment aging…")
        if "purchase_register" in dfs:
            try:
                results["paymentaging"] = payment_aging.run(dfs["purchase_register"])
            except Exception as e:
                results["paymentaging"] = {"error": str(e), "kpis": {}, "charts": {}, "tables": []}

        # ── MSME Compliance ──────────────────────────────────────────────────────
        await emit("msme", 72, "Validating MSME compliance…")
        if "purchase_register" in dfs and "vendor_master" in dfs:
            try:
                results["msme"] = msme.run(dfs["purchase_register"], dfs["vendor_master"])
            except Exception as e:
                results["msme"] = {"error": str(e), "kpis": {}, "charts": {}, "tables": []}

        # ── Vendor Master ────────────────────────────────────────────────────────
        await emit("vendor_master", 78, "Validating vendor master data…")
        if "vendor_master" in dfs:
            try:
                results["vendormaster"] = vendor_master.run(dfs["vendor_master"])
            except Exception as e:
                results["vendormaster"] = {"error": str(e), "kpis": {}, "charts": {}, "tables": []}

        # ── Item Master ──────────────────────────────────────────────────────────
        await emit("item_master", 81, "Analysing item master data…")
        if "item_master" in dfs:
            try:
                results["itemmaster"] = item_master.run(dfs)
            except Exception as e:
                results["itemmaster"] = {"error": str(e), "kpis": {}, "charts": {}, "tables": []}

        # ── GRPO Exceptions ──────────────────────────────────────────────────────
        await emit("grpo_exceptions", 84, "Checking GRPO/GE/Invoice linkages…")
        if "grpo" in dfs and "gate_entry" in dfs and "purchase_register" in dfs:
            try:
                results["grpoexcept"] = grpo_exceptions.run(
                    dfs["grpo"], dfs["gate_entry"], dfs["purchase_register"]
                )
            except Exception as e:
                results["grpoexcept"] = {"error": str(e), "kpis": {}, "charts": {}, "tables": []}

        # ── 3-Way Matching ───────────────────────────────────────────────────────
        await emit("three_way", 90, "Running 3-way matching…")
        if "purchase_order" in dfs and "grpo" in dfs and "purchase_register" in dfs:
            try:
                results["threeway"] = three_way.run(
                    dfs["purchase_order"], dfs["grpo"], dfs["purchase_register"]
                )
            except Exception as e:
                results["threeway"] = {"error": str(e), "kpis": {}, "charts": {}, "tables": []}

        # ── Executive Dashboard ──────────────────────────────────────────────────
        await emit("executive", 96, "Generating audit report…")
        try:
            results["executive"] = executive.run(results)
        except Exception as e:
            results["executive"] = {"error": str(e), "kpis": {}, "charts": {}, "top_risks": []}

        await emit("done", 100, "Done! Welcome to the dashboard")
        return results

    # Flexible Pipeline Handler for ITL & Consumption Processes
    await emit("loading", 20, f"Initializing {entity_clean} {process_clean} pipeline…")
    results: dict = {}
    cover_kpis: dict = {}

    for role, df in dfs.items():
        cover_kpis[f"{role}_count"] = len(df)

    results["cover"] = {"kpis": cover_kpis, "entity": entity_clean, "process": process_clean}

    await emit("analysis", 60, f"Processing {entity_clean} {process_clean} data structures…")
    
    # Generic Executive Summary for non-ISPL P2P runs
    total_records = sum(len(df) for df in dfs.values())
    results["executive"] = {
        "kpis": {
            "entity": entity_clean,
            "process": process_clean,
            "total_files_processed": len(dfs),
            "total_records_analyzed": total_records,
            "audit_status": "Ready for domain rules",
        },
        "charts": {},
        "top_risks": [
            {
                "title": f"{entity_clean} {process_clean} Data Verification",
                "severity": "Info",
                "description": f"Successfully loaded {len(dfs)} input files containing {total_records} records for {entity_clean} {process_clean}."
            }
        ]
    }

    await emit("done", 100, f"Done! {entity_clean} {process_clean} processing complete")
    return results
