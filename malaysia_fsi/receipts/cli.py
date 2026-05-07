"""CLI for receipt categorization and monthly SME summaries."""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from .categorizer import batch_categorize_receipts, load_receipts_from_paths
from .monthly_expense_summary import build_monthly_expense_summary
from .report import (
    export_monthly_summary_csv,
    export_monthly_summary_json,
    export_monthly_summary_markdown,
)
from .schema import parse_receipt


def _emit(text: str, output: Optional[Path]) -> None:
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text)


def _error(msg: str) -> int:
    print(msg, file=sys.stderr)
    return 1


def _resolve_paths(paths: List[Path]) -> List[Path]:
    resolved: List[Path] = []
    for path in paths:
        if path.is_dir():
            resolved.extend(sorted(path.glob("*.json")))
        else:
            resolved.append(path)
    return resolved


def run_categorize(args: argparse.Namespace) -> int:
    paths = _resolve_paths(args.receipts)
    if not paths:
        return _error("No receipt JSON files found.")

    try:
        receipts = load_receipts_from_paths(paths)
        batch = batch_categorize_receipts(receipts)
    except Exception as exc:
        return _error(f"Categorization failed: {exc}")

    payload = {
        "receipt_count": len(batch["receipts"]),
        "duplicate_candidates": {
            "|".join([key[0], key[1].isoformat(), str(key[2])]): value
            for key, value in batch["duplicate_candidates"].items()
        },
        "human_review_required": True,
        "receipts": [
            {
                "receipt_id": item.receipt.receipt_id,
                "merchant_name": item.receipt.merchant_name,
                "receipt_date": item.receipt.receipt_date.isoformat(),
                "total_amount": float(item.receipt.total_amount),
                "inferred_category": item.inferred_category,
                "confidence_score": item.confidence_score,
                "warnings": item.warnings,
                "human_review_required": True,
            }
            for item in batch["receipts"]
        ],
    }

    text = json.dumps(payload, indent=2) if args.json else f"Categorized {payload['receipt_count']} receipts"
    if not args.quiet:
        _emit(text, args.output)

    if args.strict and payload["duplicate_candidates"]:
        return 2
    return 0


def run_summarize(args: argparse.Namespace) -> int:
    paths = _resolve_paths(args.receipts)
    if not paths:
        return _error("No receipt JSON files found.")

    try:
        receipts = load_receipts_from_paths(paths)
        batch = batch_categorize_receipts(receipts)
        summary = build_monthly_expense_summary(batch["receipts"])
    except Exception as exc:
        return _error(f"Summary failed: {exc}")

    output_format = "json" if args.json else args.format
    if output_format == "json":
        text = export_monthly_summary_json(summary)
    elif output_format == "csv":
        text = export_monthly_summary_csv(summary)
    elif output_format == "md":
        text = export_monthly_summary_markdown(summary)
    else:
        text = f"Total expenses: {summary['total_expenses']}"

    if not args.quiet:
        _emit(text, args.output)

    if args.strict and summary.get("uncategorized_receipts"):
        return 2
    return 0


def run_validate(args: argparse.Namespace) -> int:
    warnings = []
    valid = True
    details = []

    for path in _resolve_paths(args.receipts):
        if not path.exists():
            valid = False
            details.append({"path": str(path), "valid": False, "errors": ["File not found"]})
            continue

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            _, parsed_warnings = parse_receipt(payload)
            details.append({"path": str(path), "valid": True, "warnings": parsed_warnings})
            warnings.extend(parsed_warnings)
        except Exception as exc:
            valid = False
            details.append({"path": str(path), "valid": False, "errors": [str(exc)]})

    result = {
        "valid": valid,
        "warnings": warnings,
        "details": details,
        "human_review_required": True,
    }

    text = json.dumps(result, indent=2) if args.json else ("Validation passed" if valid else "Validation failed")
    if not args.quiet:
        _emit(text, args.output)

    if args.strict and warnings:
        return 2
    return 0 if valid else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Malaysia FSI receipt categorization CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    categorize = sub.add_parser("categorize", help="Categorize receipt JSON files")
    categorize.add_argument("receipts", nargs="+", type=Path)
    categorize.add_argument("--json", action="store_true")
    categorize.add_argument("--output", type=Path)
    categorize.add_argument("--strict", action="store_true")
    categorize.add_argument("--quiet", action="store_true")

    summarize = sub.add_parser("summarize", help="Generate monthly summary from receipts")
    summarize.add_argument("receipts", nargs="+", type=Path)
    summarize.add_argument("--json", action="store_true")
    summarize.add_argument("--format", choices=["json", "csv", "md"], default="json")
    summarize.add_argument("--output", type=Path)
    summarize.add_argument("--strict", action="store_true")
    summarize.add_argument("--quiet", action="store_true")

    validate = sub.add_parser("validate", help="Validate receipt JSON files")
    validate.add_argument("--receipt", dest="receipts", nargs="+", type=Path, required=True)
    validate.add_argument("--json", action="store_true")
    validate.add_argument("--output", type=Path)
    validate.add_argument("--strict", action="store_true")
    validate.add_argument("--quiet", action="store_true")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "categorize":
        return run_categorize(args)
    if args.command == "summarize":
        return run_summarize(args)
    if args.command == "validate":
        return run_validate(args)
    return _error("Unknown command")


if __name__ == "__main__":
    sys.exit(main())
