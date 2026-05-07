"""Tests for malaysia_fsi.demo one-command report generation."""

import subprocess
import sys
from pathlib import Path


def test_demo_run_generates_all_outputs(tmp_path):
    output_dir = tmp_path / "demo-report"

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "malaysia_fsi.demo",
            "run",
            "--bank",
            "maybank-valid.csv",
            "--invoices",
            "invoices-exact-match/",
            "--receipts",
            "receipts/",
            "--output",
            str(output_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr

    expected_files = [
        "reconciliation.md",
        "reconciliation.json",
        "monthly-expense-summary.md",
        "categorized-expenses.csv",
        "warnings-summary.md",
        "index.md",
    ]

    for filename in expected_files:
        assert (output_dir / filename).exists(), f"Missing output file: {filename}"

    index_text = (output_dir / "index.md").read_text(encoding="utf-8")
    assert "Reconciliation (Markdown)" in index_text
    assert "monthly-expense-summary.md" in index_text

    warnings_text = (output_dir / "warnings-summary.md").read_text(encoding="utf-8")
    assert "HUMAN REVIEW REQUIRED" in warnings_text
