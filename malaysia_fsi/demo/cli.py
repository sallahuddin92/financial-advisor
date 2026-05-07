"""Single-command demo orchestration for offline SME reconciliation flows."""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from malaysia_fsi.bank_statement.invoice_matcher import InvoiceMatcher
from malaysia_fsi.bank_statement.parser import BankStatementParser
from malaysia_fsi.bank_statement.report import (
    export_reconciliation_json,
    export_reconciliation_markdown,
)
from malaysia_fsi.receipts.categorizer import batch_categorize_receipts, load_receipts_from_paths
from malaysia_fsi.receipts.monthly_expense_summary import build_monthly_expense_summary
from malaysia_fsi.receipts.report import export_monthly_summary_markdown


RECONCILIATION_MD = "reconciliation.md"
RECONCILIATION_JSON = "reconciliation.json"
MONTHLY_MD = "monthly-expense-summary.md"
CATEGORIZED_CSV = "categorized-expenses.csv"
WARNINGS_MD = "warnings-summary.md"
INDEX_MD = "index.md"


def _error(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def _resolve_input(path: Path, search_roots: Sequence[Path]) -> Path:
    if path.exists():
        return path

    for root in search_roots:
        candidate = root / path
        if candidate.exists():
            return candidate

    return path


def _resolve_invoice_paths(path: Path) -> List[Path]:
    if path.is_dir():
        return sorted(path.glob("*.json"))
    return [path]


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_categorized_csv(path: Path, categorized_items: Iterable) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "receipt_id",
                "merchant_name",
                "receipt_date",
                "total_amount",
                "inferred_category",
                "confidence_score",
                "human_review_required",
                "warning_codes",
            ]
        )
        for item in categorized_items:
            warning_codes = sorted({entry.get("code", "") for entry in item.warnings})
            writer.writerow(
                [
                    item.receipt.receipt_id,
                    item.receipt.merchant_name,
                    item.receipt.receipt_date.isoformat(),
                    f"{item.receipt.total_amount:.2f}",
                    item.inferred_category,
                    f"{item.confidence_score:.3f}",
                    "true",
                    "|".join(code for code in warning_codes if code),
                ]
            )


def _render_warnings_markdown(reconciliation: dict, monthly_summary: dict, categorized_items: Iterable) -> str:
    collected = []

    for warning in reconciliation.get("warnings", []):
        collected.append(("reconciliation", warning.get("code", "UNKNOWN"), warning.get("message", "")))

    for warning in monthly_summary.get("warnings", []):
        collected.append(("monthly_summary", warning.get("code", "UNKNOWN"), warning.get("message", "")))

    for item in categorized_items:
        for warning in item.warnings:
            collected.append(
                (
                    f"receipt:{item.receipt.receipt_id or 'unknown'}",
                    warning.get("code", "UNKNOWN"),
                    warning.get("message", ""),
                )
            )

    unique = []
    seen = set()
    for source, code, message in collected:
        marker = (source, code, message)
        if marker not in seen:
            seen.add(marker)
            unique.append(marker)

    lines = [
        "# Warnings Summary",
        "",
        f"- Total warning entries: {len(unique)}",
        "- Human review required: true",
        "",
        "## Aggregated Warnings",
    ]

    if unique:
        for source, code, message in unique:
            lines.append(f"- [{source}] `{code}`: {message}")
    else:
        lines.append("- No warnings found")

    lines.extend(
        [
            "",
            "## Disclaimer",
            "**HUMAN REVIEW REQUIRED**: Outputs are advisory only and must be reviewed before financial/accounting decisions.",
        ]
    )
    return "\n".join(lines)


def _render_index_markdown(output_dir: Path) -> str:
    lines = [
        "# Malaysia FSI Demo Output Index",
        "",
        "Generated reports:",
        f"- [Reconciliation (Markdown)]({RECONCILIATION_MD})",
        f"- [Reconciliation (JSON)]({RECONCILIATION_JSON})",
        f"- [Monthly Expense Summary (Markdown)]({MONTHLY_MD})",
        f"- [Categorized Expenses (CSV)]({CATEGORIZED_CSV})",
        f"- [Warnings Summary (Markdown)]({WARNINGS_MD})",
        "",
        "## Notes",
        "- All outputs are offline-assistance artifacts.",
        "- **HUMAN REVIEW REQUIRED** for every report.",
        f"- Output directory: `{output_dir}`",
    ]
    return "\n".join(lines)


def run_demo(bank_path: Path, invoices_path: Path, receipts_path: Path, output_dir: Path) -> int:
    repo_root = Path.cwd()
    bank = _resolve_input(bank_path, [repo_root / "test-fixtures" / "demo", repo_root / "test-fixtures" / "sample-data"])
    invoices = _resolve_input(invoices_path, [repo_root / "test-fixtures" / "demo", repo_root / "test-fixtures" / "sample-data"])
    receipts = _resolve_input(receipts_path, [repo_root / "test-fixtures" / "demo", repo_root / "test-fixtures"])

    if not bank.exists():
        return _error(f"Bank CSV not found: {bank_path}")
    if not invoices.exists():
        return _error(f"Invoices path not found: {invoices_path}")
    if not receipts.exists():
        return _error(f"Receipts path not found: {receipts_path}")

    invoice_files = _resolve_invoice_paths(invoices)
    if not invoice_files:
        return _error(f"No invoice JSON files found at: {invoices}")

    try:
        statement = BankStatementParser().parse_file(bank, bank_hint="maybank")
        matcher = InvoiceMatcher()
        results = matcher.match_statement_to_invoices(statement, invoice_files)
        loaded_invoices = [invoice for invoice in (matcher.load_invoice(path) for path in invoice_files) if invoice]
        reconciliation = matcher.build_reconciliation_report(statement, results, loaded_invoices)

        receipt_paths = [receipts]
        receipt_items = load_receipts_from_paths(receipt_paths)
        categorized_batch = batch_categorize_receipts(receipt_items)
        categorized_receipts = categorized_batch["receipts"]
        monthly_summary = build_monthly_expense_summary(categorized_receipts)

        output_dir.mkdir(parents=True, exist_ok=True)

        _write_text(output_dir / RECONCILIATION_MD, export_reconciliation_markdown(reconciliation))
        _write_text(output_dir / RECONCILIATION_JSON, export_reconciliation_json(reconciliation))
        _write_text(output_dir / MONTHLY_MD, export_monthly_summary_markdown(monthly_summary))
        _write_categorized_csv(output_dir / CATEGORIZED_CSV, categorized_receipts)
        _write_text(
            output_dir / WARNINGS_MD,
            _render_warnings_markdown(reconciliation, monthly_summary, categorized_receipts),
        )
        _write_text(output_dir / INDEX_MD, _render_index_markdown(output_dir))

        print(f"Demo report generated at: {output_dir}")
        print(f"- {RECONCILIATION_MD}")
        print(f"- {RECONCILIATION_JSON}")
        print(f"- {MONTHLY_MD}")
        print(f"- {CATEGORIZED_CSV}")
        print(f"- {WARNINGS_MD}")
        print(f"- {INDEX_MD}")
        return 0
    except Exception as exc:  # pragma: no cover - defensive CLI handling
        return _error(f"Demo run failed: {exc}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Malaysia FSI one-command demo runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_cmd = subparsers.add_parser("run", help="Generate all demo outputs in one command")
    run_cmd.add_argument("--bank", required=True, type=Path, help="Bank CSV filename/path")
    run_cmd.add_argument("--invoices", required=True, type=Path, help="Invoice JSON dir/path")
    run_cmd.add_argument("--receipts", required=True, type=Path, help="Receipt JSON dir/path")
    run_cmd.add_argument("--output", required=True, type=Path, help="Output directory")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "run":
        return run_demo(
            bank_path=args.bank,
            invoices_path=args.invoices,
            receipts_path=args.receipts,
            output_dir=args.output,
        )
    return _error("Unknown command")
