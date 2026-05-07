"""Tests for monthly SME receipt summary reporting."""

from pathlib import Path

from malaysia_fsi.receipts.categorizer import batch_categorize_receipts, load_receipts_from_paths
from malaysia_fsi.receipts.monthly_expense_summary import build_monthly_expense_summary
from malaysia_fsi.receipts.report import (
    export_monthly_summary_csv,
    export_monthly_summary_json,
    export_monthly_summary_markdown,
)


FIXTURES = Path("test-fixtures/receipts")


def test_monthly_summary_totals_and_flags():
    receipts = load_receipts_from_paths(
        [
            FIXTURES / "grocery-receipt.json",
            FIXTURES / "utility-receipt.json",
            FIXTURES / "packaging-purchase.json",
            FIXTURES / "restaurant-supplier.json",
        ]
    )
    batch = batch_categorize_receipts(receipts)
    summary = build_monthly_expense_summary(batch["receipts"])

    assert summary["receipt_count"] == 4
    assert summary["total_expenses"] > 0
    assert summary["human_review_required"] is True
    assert "FOOD_BUSINESS_RAW_MATERIAL" in summary["expenses_by_category"]
    assert "duplicate_candidates" in summary


def test_monthly_export_formats():
    receipts = load_receipts_from_paths([FIXTURES / "utility-receipt.json"])
    batch = batch_categorize_receipts(receipts)
    summary = build_monthly_expense_summary(batch["receipts"])

    json_text = export_monthly_summary_json(summary)
    csv_text = export_monthly_summary_csv(summary)
    md_text = export_monthly_summary_markdown(summary)

    assert "\"total_expenses\"" in json_text
    assert "field,value" in csv_text
    assert "Monthly SME Expense Summary" in md_text
    assert "HUMAN REVIEW REQUIRED" in md_text
