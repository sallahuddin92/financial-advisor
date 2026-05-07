"""Tests for receipt schema and categorization pipeline."""

from decimal import Decimal

from malaysia_fsi.receipts.schema import parse_receipt


def warning_codes(warnings):
    return [item.get("code") for item in warnings]


def test_parse_receipt_valid_minimal_payload():
    payload = {
        "receipt_id": "RCP-001",
        "merchant_name": "Sample Grocery Mart",
        "receipt_date": "2024-02-01",
        "total_amount": "120.50",
        "currency": "MYR",
        "payment_method": "cash",
        "inferred_category": "UNCATEGORIZED",
    }

    receipt, warnings = parse_receipt(payload)

    assert receipt.receipt_id == "RCP-001"
    assert receipt.total_amount == Decimal("120.50")
    assert "HUMAN_REVIEW_REQUIRED" in warning_codes(warnings)


def test_parse_receipt_invalid_payload_emits_structured_warnings():
    payload = {
        "receipt_id": "",
        "merchant_name": "",
        "receipt_date": "bad-date",
        "total_amount": "abc",
        "currency": "USD",
    }

    _, warnings = parse_receipt(payload)
    codes = warning_codes(warnings)

    assert "INVALID_RECEIPT_ID" in codes
    assert "MISSING_COUNTERPARTY" in codes
    assert "INVALID_DATE" in codes
    assert "INVALID_AMOUNT" in codes
    assert "INVALID_CURRENCY" in codes
