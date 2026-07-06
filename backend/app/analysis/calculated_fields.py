"""
Shared helper for building calculated_fields metadata.
Each analysis module can call these helpers to annotate which columns
are computed and what their inputs are.
"""

from __future__ import annotations


def field(
    formula: str,
    expression: str = "",
    inputs: list[dict] | None = None,
) -> dict:
    """Build a calculated field descriptor.

    Args:
        formula: Human-readable formula (e.g. "GRN Date − Gate Entry Date")
        expression: Machine-readable expression (e.g. "ABS(GRN_Date − GE_Date)")
        inputs: List of input descriptors, each with:
            - field: Column name of the input
            - source_file: Where the input originates
            - source_record: Record identifier column

    Returns:
        dict with keys: formula, expression, inputs
    """
    return {
        "formula": formula,
        "expression": expression or formula,
        "inputs": inputs or [],
    }


def input_ref(field: str, source_file: str = "Same row", source_record: str = "Same row") -> dict:
    """Build an input reference descriptor."""
    return {
        "field": field,
        "source_file": source_file,
        "source_record": source_record,
    }


def same_row(field: str) -> dict:
    """Shorthand for an input from the same row."""
    return input_ref(field, "Same row", "Same row")