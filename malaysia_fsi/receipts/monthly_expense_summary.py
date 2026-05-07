"""Monthly expense summary builder for categorized receipt data."""

from collections import defaultdict
from dataclasses import asdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Iterable, List

from .categorizer import CATEGORIES, CategorizedReceipt, detect_duplicate_candidates
from .schema import warning


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def build_monthly_expense_summary(categorized_receipts: Iterable[CategorizedReceipt]) -> Dict:
    items = list(categorized_receipts)

    total_expenses = Decimal("0.00")
    by_category = defaultdict(lambda: Decimal("0.00"))
    uncategorized_receipts = []
    suspicious_receipts = []
    missing_categories = []
    high_value_transactions = []

    receipt_objects = []
    for item in items:
        receipt = item.receipt
        receipt_objects.append(receipt)
        total_expenses += receipt.total_amount
        by_category[item.inferred_category] += receipt.total_amount

        if item.inferred_category == "UNCATEGORIZED":
            uncategorized_receipts.append(receipt.receipt_id)
            missing_categories.append(receipt.receipt_id)

        if item.confidence_score < 0.6:
            suspicious_receipts.append(receipt.receipt_id)

        if receipt.total_amount >= Decimal("1000.00"):
            high_value_transactions.append(receipt.receipt_id)

    duplicate_candidates = {
        "|".join([key[0], key[1].isoformat(), str(key[2])]): ids
        for key, ids in detect_duplicate_candidates(receipt_objects).items()
    }

    warnings = []
    if uncategorized_receipts:
        warnings.append(
            warning("MISSING_CATEGORY", "Some receipts remain uncategorized and require manual accounting review.")
        )
    if duplicate_candidates:
        warnings.append(
            warning("DUPLICATE_CANDIDATE", "Duplicate receipt candidates detected in monthly summary.")
        )
    warnings.append(
        warning("HUMAN_REVIEW_REQUIRED", "Monthly SME expense summary is advisory and must be reviewed by a human.")
    )

    category_totals = {category: float(_money(by_category.get(category, Decimal("0.00")))) for category in CATEGORIES}

    return {
        "total_expenses": float(_money(total_expenses)),
        "expenses_by_category": category_totals,
        "uncategorized_receipts": uncategorized_receipts,
        "suspicious_receipts": suspicious_receipts,
        "missing_categories": missing_categories,
        "high_value_transactions": high_value_transactions,
        "duplicate_candidates": duplicate_candidates,
        "warnings": warnings,
        "human_review_required": True,
        "receipt_count": len(items),
    }
