"""Receipt ingestion and expense categorization utilities for Malaysia FSI."""

from .categorizer import (
    CATEGORIES,
    CATEGORY_RULES,
    CategorizedReceipt,
    batch_categorize_receipts,
    categorize_receipt,
    detect_duplicate_candidates,
    suggest_category_for_text,
)
from .schema import Receipt, ReceiptLineItem, warning, validate_receipt

__all__ = [
    "Receipt",
    "ReceiptLineItem",
    "CATEGORIES",
    "CATEGORY_RULES",
    "CategorizedReceipt",
    "categorize_receipt",
    "batch_categorize_receipts",
    "detect_duplicate_candidates",
    "suggest_category_for_text",
    "warning",
    "validate_receipt",
]
