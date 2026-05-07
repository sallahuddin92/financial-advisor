"""Tests for local web demo workflow helpers."""

from pathlib import Path

from malaysia_fsi.web_demo.app import run_demo_workflow


def test_web_demo_module_imports():
    import malaysia_fsi.web_demo.app as app

    assert hasattr(app, "run_demo_workflow")
    assert hasattr(app, "main")


def test_run_demo_workflow_generates_reports(tmp_path):
    output_dir = tmp_path / "web-demo-reports"

    result = run_demo_workflow(
        bank_csv=Path("test-fixtures/demo/maybank-valid.csv"),
        invoice_json_paths=sorted(Path("test-fixtures/demo/invoices-exact-match").glob("*.json")),
        receipt_json_paths=sorted(Path("test-fixtures/demo/receipts").glob("*.json")),
        output_dir=output_dir,
        output_format="Markdown",
        run_id="test-run",
    )

    assert "reconciliation_text" in result
    assert "monthly_text" in result
    assert "warnings_text" in result
    assert "HUMAN REVIEW REQUIRED" in result["warnings_text"]

    expected_files = [
        "reconciliation.md",
        "monthly-expense-summary.md",
        "categorized-expenses.csv",
        "warnings-summary.md",
        "index.md",
    ]

    for name in expected_files:
        assert (output_dir / name).exists(), f"missing report file: {name}"


def test_run_demo_workflow_json_and_csv_outputs(tmp_path):
    invoice_paths = sorted(Path("test-fixtures/demo/invoices-exact-match").glob("*.json"))
    receipt_paths = sorted(Path("test-fixtures/demo/receipts").glob("*.json"))

    json_dir = tmp_path / "json-out"
    run_demo_workflow(
        bank_csv=Path("test-fixtures/demo/maybank-valid.csv"),
        invoice_json_paths=invoice_paths,
        receipt_json_paths=receipt_paths,
        output_dir=json_dir,
        output_format="JSON",
    )
    assert (json_dir / "reconciliation.json").exists()
    assert (json_dir / "monthly-expense-summary.json").exists()

    csv_dir = tmp_path / "csv-out"
    run_demo_workflow(
        bank_csv=Path("test-fixtures/demo/maybank-valid.csv"),
        invoice_json_paths=invoice_paths,
        receipt_json_paths=receipt_paths,
        output_dir=csv_dir,
        output_format="CSV",
    )
    assert (csv_dir / "reconciliation.csv").exists()
    assert (csv_dir / "monthly-expense-summary.csv").exists()
