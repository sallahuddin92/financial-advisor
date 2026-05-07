"""Receipt data model and validators for offline SME workflows."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple


RECEIPT_WARNING_CODES = {
    "INVALID_RECEIPT_ID",
    "INVALID_DATE",
    "INVALID_AMOUNT",
    "INVALID_CURRENCY",
    "MISSING_COUNTERPARTY",
    "MISSING_CATEGORY",
    "HUMAN_REVIEW_REQUIRED",
    "DUPLICATE_CANDIDATE",
}


def warning(code: str, message: str) -> Dict[str, str]:
    return {"code": code, "message": message}


def to_money(value: object) -> Decimal:
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0.00")


@dataclass
class ReceiptLineItem:
    description: str
    quantity: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    total: Optional[Decimal] = None

    @classmethod
    def from_dict(cls, payload: Dict) -> "ReceiptLineItem":
        return cls(
            description=str(payload.get("description", "")).strip(),
            quantity=to_money(payload.get("quantity")) if payload.get("quantity") is not None else None,
            unit_price=to_money(payload.get("unit_price")) if payload.get("unit_price") is not None else None,
            total=to_money(payload.get("total")) if payload.get("total") is not None else None,
        )


@dataclass
class Receipt:
    receipt_id: str
    merchant_name: str
    receipt_date: date
    total_amount: Decimal
    currency: str = "MYR"
    payment_method: str = "unknown"
    line_items: Optional[List[ReceiptLineItem]] = None
    inferred_category: str = "UNCATEGORIZED"
    confidence_score: float = 0.0
    warnings: Optional[List[Dict[str, str]]] = None

    def __post_init__(self):
        if self.line_items is None:
            self.line_items = []
        if self.warnings is None:
            self.warnings = []


def parse_receipt(payload: Dict) -> Tuple[Receipt, List[Dict[str, str]]]:
    warnings: List[Dict[str, str]] = []

    receipt_id = str(payload.get("receipt_id", "")).strip()
    merchant_name = str(payload.get("merchant_name", "")).strip()
    receipt_date = payload.get("receipt_date")
    if isinstance(receipt_date, str):
        try:
            receipt_date = date.fromisoformat(receipt_date)
        except ValueError:
            warnings.append(warning("INVALID_DATE", "receipt_date must be ISO-8601 date."))
            receipt_date = date(1970, 1, 1)
    elif not isinstance(receipt_date, date):
        warnings.append(warning("INVALID_DATE", "receipt_date missing or invalid."))
        receipt_date = date(1970, 1, 1)

    raw_amount = payload.get("total_amount", "0")
    total_amount = to_money(raw_amount)
    if total_amount == Decimal("0.00") and str(raw_amount) not in {"0", "0.0", "0.00"}:
        warnings.append(warning("INVALID_AMOUNT", "total_amount could not be parsed as money."))

    line_items = [ReceiptLineItem.from_dict(item) for item in payload.get("line_items", [])]

    receipt = Receipt(
        receipt_id=receipt_id,
        merchant_name=merchant_name,
        receipt_date=receipt_date,
        total_amount=total_amount,
        currency=str(payload.get("currency", "MYR")).upper(),
        payment_method=str(payload.get("payment_method", "unknown")).strip() or "unknown",
        line_items=line_items,
        inferred_category=str(payload.get("inferred_category", "UNCATEGORIZED")).strip() or "UNCATEGORIZED",
        confidence_score=float(payload.get("confidence_score", 0.0) or 0.0),
        warnings=list(payload.get("warnings", [])) if isinstance(payload.get("warnings", []), list) else [],
    )

    validations = validate_receipt(receipt)
    warnings.extend(validations)
    warnings.append(
        warning(
            "HUMAN_REVIEW_REQUIRED",
            "Receipt categorization output must be reviewed by a human before accounting use.",
        )
    )
    receipt.warnings.extend(warnings)

    return receipt, warnings


def validate_receipt(receipt: Receipt) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []

    if not receipt.receipt_id:
        issues.append(warning("INVALID_RECEIPT_ID", "receipt_id is required."))

    if not receipt.merchant_name:
        issues.append(warning("MISSING_COUNTERPARTY", "merchant_name is required."))

    if receipt.total_amount < Decimal("0.00"):
        issues.append(warning("INVALID_AMOUNT", "total_amount cannot be negative."))

    if receipt.currency != "MYR":
        issues.append(warning("INVALID_CURRENCY", "Only MYR is supported in current offline MVP."))

    if receipt.inferred_category == "UNCATEGORIZED":
        issues.append(warning("MISSING_CATEGORY", "Receipt remains uncategorized and needs manual classification."))

    return issues
