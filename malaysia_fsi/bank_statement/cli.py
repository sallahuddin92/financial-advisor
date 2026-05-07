"""CLI helpers for Malaysia FSI bank statement workflows."""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from .invoice_matcher import InvoiceMatcher
from .parser import BankStatementParser
from .report import format_transaction_output
from .schema import TransactionDirection


def parse_main(argv: Optional[List[str]] = None) -> int:
    """Parse-only CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Parse Malaysian bank statement CSV files")
    parser.add_argument("file", type=Path, help="Path to bank statement CSV file")
    parser.add_argument("--bank", type=str, help="Bank name hint (maybank)", default=None)
    parser.add_argument("--format", choices=["json", "summary"], default="summary", help="Output format")

    args = parser.parse_args(argv)

    if not args.file.exists():
        print(f"Error: File not found: {args.file}")
        return 1

    try:
        bank_parser = BankStatementParser()
        statement = bank_parser.parse_file(args.file, args.bank)

        if args.format == "json":
            print(json.dumps(format_transaction_output(statement), indent=2))
        else:
            print("=== Bank Statement Summary ===")
            print(f"Bank: {statement.bank_name}")
            print(f"Period: {statement.statement_period_start} to {statement.statement_period_end}")
            print(f"Currency: {statement.currency}")
            print(f"Transactions: {len(statement.transactions)}")
            print(f"Confidence: {statement.confidence:.2f}")

            if statement.warnings:
                print("\nWarnings:")
                for warning in statement.warnings:
                    print(f"  - {warning}")

            print("\nFirst 5 transactions:")
            for idx, tx in enumerate(statement.transactions[:5], start=1):
                direction_symbol = "→" if tx.direction == TransactionDirection.CREDIT else "←"
                amount_str = f"{abs(tx.amount or 0):.2f}" if tx.amount else "0.00"
                print(f"  {idx}. {tx.date} {direction_symbol} {tx.description[:50]} ({amount_str} {tx.currency})")

            if len(statement.transactions) > 5:
                print(f"  ... and {len(statement.transactions) - 5} more")

        return 0

    except Exception as exc:
        print(f"Error: {exc}")
        return 1


def match_main(argv: Optional[List[str]] = None) -> int:
    """Matcher CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Match bank statement transactions with invoices")
    parser.add_argument("bank_statement", type=Path, help="Path to bank statement CSV file")
    parser.add_argument("invoices", type=Path, nargs="+", help="Path(s) to invoice JSON file(s)")
    parser.add_argument("--bank", type=str, help="Bank name hint (maybank)", default=None)
    parser.add_argument("--json", action="store_true", help="Output reconciliation summary in JSON format")
    parser.add_argument("--format", choices=["json", "summary"], default="summary", help="Output format")
    parser.add_argument("--date-tolerance", type=int, default=3, help="Date tolerance in days (default: 3)")
    parser.add_argument(
        "--amount-tolerance",
        type=float,
        default=0.01,
        help="Amount tolerance as decimal (default: 0.01 = 1%)",
    )

    args = parser.parse_args(argv)

    if not args.bank_statement.exists():
        print(f"Error: Bank statement file not found: {args.bank_statement}")
        return 1

    for invoice_path in args.invoices:
        if not invoice_path.exists():
            print(f"Error: Invoice file not found: {invoice_path}")
            return 1

    try:
        bank_parser = BankStatementParser()
        statement = bank_parser.parse_file(args.bank_statement, args.bank)

        matcher = InvoiceMatcher(
            date_tolerance_days=args.date_tolerance,
            amount_tolerance_percent=args.amount_tolerance,
        )
        results = matcher.match_statement_to_invoices(statement, args.invoices)
        report = matcher.generate_matching_report(results)

        loaded_invoices = []
        for invoice_path in args.invoices:
            invoice = matcher.load_invoice(invoice_path)
            if invoice:
                loaded_invoices.append(invoice)
        reconciliation_report = matcher.build_reconciliation_report(statement, results, loaded_invoices)

        if args.json or args.format == "json":
            print(json.dumps(reconciliation_report, indent=2))
        else:
            print("=== Invoice Matching Report ===")
            print(f"Bank: {statement.bank_name}")
            print(f"Statement Period: {statement.statement_period_start} to {statement.statement_period_end}")
            print(f"Total Transactions: {report['total_transactions']}")
            print("\nMatch Summary:")
            print(f"  ✅ Matched: {report['matched']}")
            print(f"  🤔 Possible Matches: {report['possible_matches']}")
            print(f"  ❌ Unmatched: {report['unmatched']}")
            print(f"  💰 Overpaid: {report['overpaid']}")
            print(f"  💸 Underpaid: {report['underpaid']}")
            print(f"  📊 Average Confidence: {report['average_confidence']:.3f}")

            if report["warnings"]:
                print("\nWarnings:")
                for warning in set(report["warnings"]):
                    print(f"  - {warning}")

            print("\n⚠️  HUMAN REVIEW REQUIRED")
            print("All matching results require manual verification.")
            print("This system assists with matching but does not replace professional judgment.")

        return 0

    except Exception as exc:
        print(f"Error: {exc}")
        return 1


def main() -> int:
    """Default module entrypoint keeps parse behavior for compatibility."""
    return parse_main()


if __name__ == "__main__":
    sys.exit(main())
