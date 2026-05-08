"""Tests for local web demo usability helpers."""

import json
from pathlib import Path

import pytest

from malaysia_fsi.web_demo.app import (
    generate_timestamped_output_dir,
    run_demo_workflow,
    run_sample_kedai_makan_demo,
)


def test_web_demo_module_imports():
    import malaysia_fsi.web_demo.app as app

    assert hasattr(app, "run_demo_workflow")
    assert hasattr(app, "run_sample_kedai_makan_demo")
    assert hasattr(app, "main")


def test_timestamped_output_folder_creation(tmp_path):
    first = generate_timestamped_output_dir(base_dir=tmp_path, prefix="demo")
    second = generate_timestamped_output_dir(base_dir=tmp_path, prefix="demo")

    assert first.exists() and first.is_dir()
    assert second.exists() and second.is_dir()
    assert first != second
    assert first.name.startswith("demo-")
    assert second.name.startswith("demo-")


def test_web_demo_sample_run_generates_make_demo_outputs():
    result = run_sample_kedai_makan_demo(output_format="Markdown")
    output_dir = Path(result["output_dir"])

    assert output_dir.exists()
    expected_files = [
        "reconciliation.md",
        "reconciliation.json",
        "monthly-expense-summary.md",
        "categorized-expenses.csv",
        "warnings-summary.md",
        "index.md",
    ]
    for filename in expected_files:
        assert (output_dir / filename).exists(), f"Missing expected sample output: {filename}"


def test_error_handling_for_missing_inputs(tmp_path):
    with pytest.raises(FileNotFoundError, match="Missing bank CSV"):
        run_demo_workflow(
            bank_csv=tmp_path / "missing.csv",
            invoice_json_paths=[Path("test-fixtures/demo/invoices-exact-match/invoice-abc-001.json")],
            receipt_json_paths=[Path("test-fixtures/demo/receipts/grocery-receipt.json")],
            output_dir=tmp_path / "out",
            output_format="Markdown",
        )


def test_error_handling_invalid_invoice_json(tmp_path):
    invalid_invoice = tmp_path / "bad-invoice.json"
    invalid_invoice.write_text("{ bad json", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid invoice JSON"):
        run_demo_workflow(
            bank_csv=Path("test-fixtures/demo/maybank-valid.csv"),
            invoice_json_paths=[invalid_invoice],
            receipt_json_paths=[Path("test-fixtures/demo/receipts/grocery-receipt.json")],
            output_dir=tmp_path / "out2",
            output_format="Markdown",
        )


def test_report_preview_generation(tmp_path):
    result = run_demo_workflow(
        bank_csv=Path("test-fixtures/demo/maybank-valid.csv"),
        invoice_json_paths=sorted(Path("test-fixtures/demo/invoices-exact-match").glob("*.json")),
        receipt_json_paths=sorted(Path("test-fixtures/demo/receipts").glob("*.json")),
        output_dir=tmp_path / "preview-out",
        output_format="Markdown",
    )

    assert "<h1>" in result["reconciliation_preview_html"]
    assert "<h1>" in result["monthly_preview_html"]
    assert "<h1>" in result["warnings_preview_html"]
    assert "HUMAN REVIEW REQUIRED" in result["warnings_text"]

    # Ensure reconciliation JSON still exists for downstream review tooling.
    reconciliation_json = Path(result["output_dir"]) / "reconciliation.json"
    assert reconciliation_json.exists()
    payload = json.loads(reconciliation_json.read_text(encoding="utf-8"))
    assert payload["human_review_required"] is True
