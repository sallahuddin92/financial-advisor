"""Rule-based receipt categorization for Malaysia SME expense workflows."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
import json

from .schema import Receipt, parse_receipt, warning


CATEGORIES = [
    "FOOD_BUSINESS_RAW_MATERIAL",
    "PACKAGING",
    "UTILITIES",
    "RENT",
    "SALARY_WAGES",
    "DELIVERY_FEES",
    "TRANSPORT",
    "OFFICE_SUPPLIES",
    "EQUIPMENT",
    "BANK_CHARGES",
    "MARKETING",
    "CASH_WITHDRAWAL",
    "UNCATEGORIZED",
]


CATEGORY_RULES: Dict[str, List[str]] = {
    "FOOD_BUSINESS_RAW_MATERIAL": [
        "mydin",
        "tesco",
        "lotus",
        "giant",
        "pasar",
        "supplier",
        "wholesale",
        "grocer",
    ],
    "PACKAGING": ["packaging", "plastic", "container", "box", "label", "shopee express"],
    "UTILITIES": ["tnb", "air selangor", "syabas", "utilities", "electric", "water"],
    "RENT": ["rental", "rent", "sewa", "property"],
    "SALARY_WAGES": ["salary", "wages", "payroll", "gaji", "epf"],
    "DELIVERY_FEES": ["grabfood", "foodpanda", "delivery", "courier", "lalamove", "shopee express"],
    "TRANSPORT": ["petrol", "diesel", "parking", "toll", "transport", "grab"],
    "OFFICE_SUPPLIES": ["stationery", "office", "printer", "paper", "ink"],
    "EQUIPMENT": ["machine", "equipment", "tool", "repair", "maintenance"],
    "BANK_CHARGES": ["bank charge", "processing fee", "service charge"],
    "MARKETING": ["ads", "advert", "marketing", "facebook", "tiktok"],
    "CASH_WITHDRAWAL": ["atm withdrawal", "cash withdrawal", "withdrawal"],
}


@dataclass
class CategorizedReceipt:
    receipt: Receipt
    inferred_category: str
    confidence_score: float
    human_review_required: bool
    warnings: List[Dict[str, str]]


def _normalize_text(receipt: Receipt) -> str:
    line_text = " ".join(item.description for item in (receipt.line_items or []) if item.description)
    return f"{receipt.merchant_name} {line_text}".lower()


def suggest_category_for_text(description: str) -> Tuple[str, float, List[Dict[str, str]]]:
    text = (description or "").lower()
    best_category = "UNCATEGORIZED"
    best_score = 0

    for category, keywords in CATEGORY_RULES.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_score = score
            best_category = category

    if best_score == 0:
        return (
            "UNCATEGORIZED",
            0.0,
            [warning("MISSING_CATEGORY", "No category keywords matched; manual categorization required.")],
        )

    confidence = min(0.95, 0.45 + (best_score * 0.15))
    warnings = []
    if confidence < 0.7:
        warnings.append(warning("MISSING_CATEGORY", "Low-confidence category assignment; verify manually."))
    return best_category, confidence, warnings


def categorize_receipt(receipt: Receipt) -> CategorizedReceipt:
    category, confidence, warnings = suggest_category_for_text(_normalize_text(receipt))
    merged_warnings = list(receipt.warnings) + warnings

    if category == "UNCATEGORIZED":
        merged_warnings.append(warning("MISSING_CATEGORY", "Receipt is uncategorized."))

    merged_warnings.append(
        warning("HUMAN_REVIEW_REQUIRED", "Expense category is advisory and requires accountant review.")
    )

    receipt.inferred_category = category
    receipt.confidence_score = confidence
    receipt.warnings = merged_warnings

    return CategorizedReceipt(
        receipt=receipt,
        inferred_category=category,
        confidence_score=confidence,
        human_review_required=True,
        warnings=merged_warnings,
    )


def _duplicate_key(receipt: Receipt) -> Tuple[str, date, Decimal]:
    return (
        (receipt.merchant_name or "").strip().lower(),
        receipt.receipt_date,
        receipt.total_amount,
    )


def detect_duplicate_candidates(receipts: Sequence[Receipt]) -> Dict[Tuple[str, date, Decimal], List[str]]:
    grouped: Dict[Tuple[str, date, Decimal], List[str]] = defaultdict(list)
    for receipt in receipts:
        grouped[_duplicate_key(receipt)].append(receipt.receipt_id)
    return {key: ids for key, ids in grouped.items() if len(ids) > 1}


def batch_categorize_receipts(receipts: Sequence[Receipt]) -> Dict[str, object]:
    categorized = [categorize_receipt(receipt) for receipt in receipts]
    duplicates = detect_duplicate_candidates([item.receipt for item in categorized])

    if duplicates:
        duplicate_warning = warning(
            "DUPLICATE_CANDIDATE",
            "Duplicate receipt candidates detected with same merchant/date/amount.",
        )
        for item in categorized:
            key = _duplicate_key(item.receipt)
            if key in duplicates:
                item.warnings.append(duplicate_warning)

    return {
        "receipts": categorized,
        "duplicate_candidates": duplicates,
        "human_review_required": True,
    }


def load_receipts_from_paths(paths: Iterable[Path]) -> List[Receipt]:
    receipts: List[Receipt] = []
    for path in paths:
        if path.is_dir():
            for json_file in sorted(path.glob("*.json")):
                with open(json_file, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                receipt, _ = parse_receipt(payload)
                receipts.append(receipt)
        else:
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            receipt, _ = parse_receipt(payload)
            receipts.append(receipt)
    return receipts
