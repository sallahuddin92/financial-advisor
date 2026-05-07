"""Tests for receipt schema and categorization pipeline."""

from pathlib import Path

from malaysia_fsi.receipts.categorizer import (
    batch_categorize_receipts,
    categorize_receipt,
    load_receipts_from_paths,
    suggest_category_for_text,
)
from malaysia_fsi.receipts.schema import parse_receipt


FIXTURES = Path("test-fixtures/receipts")


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
    assert str(receipt.total_amount) == "120.50"
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


def test_suggest_category_keywords_for_known_merchants():
    category, confidence, _ = suggest_category_for_text("MYDIN SEREMBAN wholesale groceries")
    assert category == "FOOD_BUSINESS_RAW_MATERIAL"
    assert confidence > 0.5

    category, confidence, _ = suggest_category_for_text("TNB ONLINE PAYMENT")
    assert category == "UTILITIES"
    assert confidence > 0.5


def test_categorize_receipt_from_fixture():
    receipts = load_receipts_from_paths([FIXTURES / "utility-receipt.json"])
    result = categorize_receipt(receipts[0])
    assert result.inferred_category == "UTILITIES"
    assert result.human_review_required is True
    assert "HUMAN_REVIEW_REQUIRED" in warning_codes(result.warnings)


def test_batch_duplicate_detection():
    receipts = load_receipts_from_paths(
        [
            FIXTURES / "grocery-receipt.json",
            FIXTURES / "restaurant-supplier.json",
            FIXTURES / "packaging-purchase.json",
        ]
    )
    batch = batch_categorize_receipts(receipts)
    assert batch["human_review_required"] is True
    assert len(batch["duplicate_candidates"]) >= 1


def test_malformed_receipt_fixture_stays_review_required():
    receipts = load_receipts_from_paths([FIXTURES / "malformed-receipt.json"])
    result = categorize_receipt(receipts[0])
    assert result.human_review_required is True
    assert "INVALID_RECEIPT_ID" in warning_codes(result.warnings)
