#!/usr/bin/env python3
"""Verification script for Malaysia FSI offline reconciliation MVP."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_step(name: str, cmd: list[str]) -> None:
    print(f"\n== {name} ==")
    print("$ " + " ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> int:
    run_step(
        "Parser/Matcher Tests",
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_bank_statement_parser.py",
            "tests/test_invoice_matcher.py",
            "-v",
        ],
    )
    run_step("Phase 1 Validator", [sys.executable, "scripts/validate_malaysia_phase1.py"])
    run_step(
        "CLI Parse Smoke",
        [
            sys.executable,
            "-m",
            "malaysia_fsi.bank_statement.cli",
            "parse",
            "test-fixtures/sample-data/maybank-valid.csv",
            "--json",
            "--quiet",
        ],
    )
    run_step(
        "CLI Match Smoke",
        [
            sys.executable,
            "-m",
            "malaysia_fsi.bank_statement.cli",
            "match",
            "test-fixtures/sample-data/maybank-valid.csv",
            "test-fixtures/sample-data/invoices-exact-match",
            "--format",
            "md",
            "--output",
            "/tmp/reconciliation-report-verify.md",
        ],
    )
    run_step(
        "CLI Validate Smoke",
        [
            sys.executable,
            "-m",
            "malaysia_fsi.bank_statement.cli",
            "validate",
            "--input",
            "test-fixtures/sample-data/maybank-valid.csv",
            "--invoice",
            "test-fixtures/sample-data/invoices-exact-match/invoice-abc-001.json",
            "--json",
            "--quiet",
        ],
    )
    print("\nAll Malaysia FSI verification checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
