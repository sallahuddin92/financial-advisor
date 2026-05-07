"""CLI for Malaysia FSI offline bank statement workflows."""

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from .invoice_matcher import InvoiceMatcher
from .parser import BankStatementParser
from .report import (
    export_reconciliation_csv,
    export_reconciliation_json,
    export_reconciliation_markdown,
    format_transaction_output,
)
from .schema import TransactionDirection


def _emit_output(payload: str, output_path: Optional[Path] = None) -> None:
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload, encoding="utf-8")
    else:
        print(payload)


def _error(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def _resolve_invoices(paths: Iterable[Path]) -> List[Path]:
    resolved: List[Path] = []
    for path in paths:
        if path.is_dir():
            resolved.extend(sorted(path.glob("*.json")))
        else:
            resolved.append(path)
    return resolved


def _validate_paths(csv_path: Optional[Path], invoice_paths: Optional[List[Path]]) -> Tuple[bool, List[str]]:
    errors = []
    if csv_path and not csv_path.exists():
        errors.append(f"CSV file not found: {csv_path}")
    if invoice_paths is not None:
        if len(invoice_paths) == 0:
            errors.append("No invoice JSON files found.")
        for invoice in invoice_paths:
            if not invoice.exists():
                errors.append(f"Invoice file not found: {invoice}")
    return (len(errors) == 0, errors)


def _parse_bank_value(bank_value: str) -> Optional[str]:
    if bank_value == "auto":
        return None
    return bank_value


def run_parse(args: argparse.Namespace) -> int:
    ok, errors = _validate_paths(args.input, None)
    if not ok:
        return _error("\n".join(errors))

    bank_parser = BankStatementParser()
    try:
        statement = bank_parser.parse_file(args.input, _parse_bank_value(args.bank))
    except Exception as exc:
        return _error(f"Parse failed: {exc}")

    payload = format_transaction_output(statement)

    if args.strict and statement.warnings:
        payload["strict_mode_failed"] = True

    if args.json:
        output_text = json.dumps(payload, indent=2)
    elif args.quiet:
        output_text = ""
    else:
        output_lines = [
            "=== Bank Statement Summary ===",
            f"Bank: {statement.bank_name}",
            f"Period: {statement.statement_period_start} to {statement.statement_period_end}",
            f"Currency: {statement.currency}",
            f"Transactions: {len(statement.transactions)}",
            f"Confidence: {statement.confidence:.2f}",
        ]
        output_text = "\n".join(output_lines)

    if output_text:
        _emit_output(output_text, args.output)

    if args.strict and statement.warnings:
        return 2
    return 0


def run_match(args: argparse.Namespace) -> int:
    invoice_paths = _resolve_invoices(args.invoices)
    ok, errors = _validate_paths(args.input, invoice_paths)
    if not ok:
        return _error("\n".join(errors))

    bank_parser = BankStatementParser()
    try:
        statement = bank_parser.parse_file(args.input, _parse_bank_value(args.bank))
    except Exception as exc:
        return _error(f"Parse failed: {exc}")

    matcher = InvoiceMatcher(
        date_tolerance_days=args.date_tolerance_days,
        amount_tolerance_percent=float(args.amount_tolerance),
    )

    try:
        results = matcher.match_statement_to_invoices(statement, invoice_paths)
        loaded_invoices = [invoice for invoice in (matcher.load_invoice(p) for p in invoice_paths) if invoice]
        reconciliation = matcher.build_reconciliation_report(statement, results, loaded_invoices)
    except Exception as exc:
        return _error(f"Match failed: {exc}")

    if args.strict and reconciliation.get("warnings"):
        reconciliation["strict_mode_failed"] = True

    output_format = "json" if args.json else args.format
    if output_format == "json":
        output_text = export_reconciliation_json(reconciliation)
    elif output_format == "csv":
        output_text = export_reconciliation_csv(reconciliation)
    elif output_format == "md":
        output_text = export_reconciliation_markdown(reconciliation)
    elif args.quiet:
        output_text = ""
    else:
        output_text = "\n".join(
            [
                "=== Reconciliation Summary ===",
                f"Bank: {reconciliation['statement_bank']}",
                f"Period: {reconciliation['statement_period']['start']} to {reconciliation['statement_period']['end']}",
                f"Transactions: {reconciliation['total_transactions']}",
                f"Invoices: {reconciliation['total_invoices']}",
                f"Matched: {reconciliation['matched_count']}",
                f"Possible: {reconciliation['possible_match_count']}",
                f"Unmatched: {reconciliation['unmatched_count']}",
                "HUMAN REVIEW REQUIRED",
            ]
        )

    if output_text:
        _emit_output(output_text, args.output)

    if args.strict and reconciliation.get("warnings"):
        return 2
    return 0


def run_validate(args: argparse.Namespace) -> int:
    matcher = InvoiceMatcher(
        date_tolerance_days=args.date_tolerance_days,
        amount_tolerance_percent=float(args.amount_tolerance),
    )

    payload = {
        "csv": None,
        "invoice": None,
        "valid": True,
        "warnings": [],
        "human_review_required": True,
    }

    if args.input:
        ok, errors = _validate_paths(args.input, None)
        if not ok:
            payload["csv"] = {"valid": False, "errors": errors}
            payload["valid"] = False
        else:
            try:
                statement = BankStatementParser().parse_file(args.input, _parse_bank_value(args.bank))
                payload["csv"] = {
                    "valid": True,
                    "bank": statement.bank_name,
                    "transaction_count": len(statement.transactions),
                    "warnings": statement.warnings,
                }
                payload["warnings"].extend(statement.warnings)
            except Exception as exc:
                payload["csv"] = {"valid": False, "errors": [str(exc)]}
                payload["valid"] = False

    if args.invoice:
        invoice_path = args.invoice
        if not invoice_path.exists():
            payload["invoice"] = {"valid": False, "errors": [f"Invoice file not found: {invoice_path}"]}
            payload["valid"] = False
        else:
            invoice = matcher.load_invoice(invoice_path)
            if not invoice:
                payload["invoice"] = {"valid": False, "errors": ["Invalid invoice JSON"]}
                payload["valid"] = False
            else:
                valid, invoice_warnings = matcher.validate_invoice(invoice)
                payload["invoice"] = {"valid": valid, "warnings": invoice_warnings}
                payload["warnings"].extend(invoice_warnings)
                if not valid:
                    payload["valid"] = False

    if args.strict and payload["warnings"]:
        payload["valid"] = False

    if args.json or args.quiet:
        output_text = json.dumps(payload, indent=2)
    else:
        output_text = "Validation passed" if payload["valid"] else "Validation failed"

    _emit_output(output_text, args.output)

    return 0 if payload["valid"] else 2


def build_main_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Malaysia FSI offline bank statement CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse_cmd = subparsers.add_parser("parse", help="Parse bank statement CSV")
    parse_cmd.add_argument("input", type=Path, help="Bank statement CSV path")
    parse_cmd.add_argument("--json", action="store_true", help="Emit JSON output")
    parse_cmd.add_argument("--output", type=Path, help="Write output to file")
    parse_cmd.add_argument("--bank", choices=["maybank", "auto"], default="auto")
    parse_cmd.add_argument("--strict", action="store_true")
    parse_cmd.add_argument("--quiet", action="store_true")

    match_cmd = subparsers.add_parser("match", help="Match CSV transactions to invoice JSON")
    match_cmd.add_argument("input", type=Path, help="Bank statement CSV path")
    match_cmd.add_argument("invoices", type=Path, nargs="+", help="Invoice JSON file(s) or directories")
    match_cmd.add_argument("--json", action="store_true", help="Emit JSON output")
    match_cmd.add_argument(
        "--format",
        choices=["summary", "json", "csv", "md"],
        default="summary",
        help="Match output format",
    )
    match_cmd.add_argument("--output", type=Path, help="Write output to file")
    match_cmd.add_argument("--bank", choices=["maybank", "auto"], default="auto")
    match_cmd.add_argument("--date-tolerance-days", type=int, default=3)
    match_cmd.add_argument("--amount-tolerance", default="0.01")
    match_cmd.add_argument("--strict", action="store_true")
    match_cmd.add_argument("--quiet", action="store_true")

    validate_cmd = subparsers.add_parser("validate", help="Validate CSV and/or invoice JSON")
    validate_cmd.add_argument("--input", type=Path, help="Bank statement CSV path")
    validate_cmd.add_argument("--invoice", type=Path, help="Invoice JSON path")
    validate_cmd.add_argument("--json", action="store_true", help="Emit JSON output")
    validate_cmd.add_argument("--output", type=Path, help="Write output to file")
    validate_cmd.add_argument("--bank", choices=["maybank", "auto"], default="auto")
    validate_cmd.add_argument("--date-tolerance-days", type=int, default=3)
    validate_cmd.add_argument("--amount-tolerance", default="0.01")
    validate_cmd.add_argument("--strict", action="store_true")
    validate_cmd.add_argument("--quiet", action="store_true")

    return parser


def parse_main(argv: Optional[List[str]] = None) -> int:
    """Legacy parser CLI compatibility endpoint."""
    legacy = argparse.ArgumentParser(description="Parse Malaysian bank statement CSV files")
    legacy.add_argument("file", type=Path)
    legacy.add_argument("--bank", type=str, default=None)
    legacy.add_argument("--format", choices=["json", "summary"], default="summary")
    args = legacy.parse_args(argv)

    bridge_args = argparse.Namespace(
        input=args.file,
        json=(args.format == "json"),
        output=None,
        bank=(args.bank if args.bank else "auto"),
        strict=False,
        quiet=False,
    )
    return run_parse(bridge_args)


def match_main(argv: Optional[List[str]] = None) -> int:
    """Legacy matcher CLI compatibility endpoint."""
    legacy = argparse.ArgumentParser(description="Match bank statement transactions with invoices")
    legacy.add_argument("bank_statement", type=Path)
    legacy.add_argument("invoices", type=Path, nargs="+")
    legacy.add_argument("--bank", type=str, default=None)
    legacy.add_argument("--json", action="store_true")
    legacy.add_argument("--format", choices=["json", "summary"], default="summary")
    legacy.add_argument("--date-tolerance", type=int, default=3)
    legacy.add_argument("--amount-tolerance", type=float, default=0.01)
    args = legacy.parse_args(argv)

    bridge_args = argparse.Namespace(
        input=args.bank_statement,
        invoices=args.invoices,
        json=(args.json or args.format == "json"),
        format="json" if (args.json or args.format == "json") else "summary",
        output=None,
        bank=(args.bank if args.bank else "auto"),
        date_tolerance_days=args.date_tolerance,
        amount_tolerance=str(args.amount_tolerance),
        strict=False,
        quiet=False,
    )
    return run_match(bridge_args)


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_main_parser()
    args = parser.parse_args(argv)

    if args.command == "parse":
        return run_parse(args)
    if args.command == "match":
        return run_match(args)
    if args.command == "validate":
        return run_validate(args)
    return _error("Unknown command")


if __name__ == "__main__":
    sys.exit(main())
