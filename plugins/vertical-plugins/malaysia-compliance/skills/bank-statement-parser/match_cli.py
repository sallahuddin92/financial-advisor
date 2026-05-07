"""
CLI interface for invoice matching
"""

import argparse
import json
import importlib.util
import sys
from pathlib import Path
from typing import List

# Load modules using file path to avoid hyphen import issues
schema_path = Path(__file__).parent / "schema.py"
parser_path = Path(__file__).parent / "parser.py"
matcher_path = Path(__file__).parent / "invoice_matcher.py"

# Load schema module
spec = importlib.util.spec_from_file_location("schema", schema_path)
schema = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schema)

# Load parser module
spec = importlib.util.spec_from_file_location("parser", parser_path)
parser_module = importlib.util.module_from_spec(spec)
sys.modules["schema"] = schema  # Add to sys.modules for relative imports
parser_module.schema = schema  # Inject schema module
spec.loader.exec_module(parser_module)

# Load matcher module
spec = importlib.util.spec_from_file_location("matcher", matcher_path)
matcher_module = importlib.util.module_from_spec(spec)
sys.modules["schema"] = schema  # Add to sys.modules for relative imports
matcher_module.schema = schema  # Inject schema module
matcher_module.parser = parser_module  # Inject parser module
spec.loader.exec_module(matcher_module)

# Import classes from loaded modules
BankStatementParser = parser_module.BankStatementParser
InvoiceMatcher = matcher_module.InvoiceMatcher

def main():
    """CLI main function for invoice matching"""
    parser = argparse.ArgumentParser(description="Match bank statement transactions with invoices")
    parser.add_argument("bank_statement", type=Path, help="Path to bank statement CSV file")
    parser.add_argument("invoices", type=Path, nargs="+", help="Path(s) to invoice JSON file(s)")
    parser.add_argument("--bank", type=str, help="Bank name hint (maybank)", default=None)
    parser.add_argument("--json", action="store_true", help="Output reconciliation summary in JSON format")
    parser.add_argument("--format", choices=["json", "summary"], default="summary",
                       help="Output format")
    parser.add_argument("--date-tolerance", type=int, default=3,
                       help="Date tolerance in days (default: 3)")
    parser.add_argument("--amount-tolerance", type=float, default=0.01,
                       help="Amount tolerance as decimal (default: 0.01 = 1%)")

    args = parser.parse_args()

    # Validate files exist
    if not args.bank_statement.exists():
        print(f"Error: Bank statement file not found: {args.bank_statement}")
        return 1

    for invoice_path in args.invoices:
        if not invoice_path.exists():
            print(f"Error: Invoice file not found: {invoice_path}")
            return 1

    try:
        # Parse bank statement
        bank_parser = BankStatementParser()
        statement = bank_parser.parse_file(args.bank_statement, args.bank)

        # Match invoices
        invoice_matcher = InvoiceMatcher(
            date_tolerance_days=args.date_tolerance,
            amount_tolerance_percent=args.amount_tolerance
        )
        results = invoice_matcher.match_statement_to_invoices(statement, args.invoices)
        report = invoice_matcher.generate_matching_report(results)
        loaded_invoices = []
        for invoice_path in args.invoices:
            invoice = invoice_matcher.load_invoice(invoice_path)
            if invoice:
                loaded_invoices.append(invoice)
        reconciliation_report = invoice_matcher.build_reconciliation_report(
            statement, results, loaded_invoices
        )

        if args.json or args.format == "json":
            # JSON output
            print(json.dumps(reconciliation_report, indent=2))
        else:
            # Summary output
            print(f"=== Invoice Matching Report ===")
            print(f"Bank: {statement.bank_name}")
            print(f"Statement Period: {statement.statement_period_start} to {statement.statement_period_end}")
            print(f"Total Transactions: {report['total_transactions']}")
            print(f"\nMatch Summary:")
            print(f"  ✅ Matched: {report['matched']}")
            print(f"  🤔 Possible Matches: {report['possible_matches']}")
            print(f"  ❌ Unmatched: {report['unmatched']}")
            print(f"  💰 Overpaid: {report['overpaid']}")
            print(f"  💸 Underpaid: {report['underpaid']}")
            print(f"  📊 Average Confidence: {report['average_confidence']:.3f}")

            if report['warnings']:
                print(f"\nWarnings:")
                for warning in set(report['warnings']):  # Remove duplicates
                    print(f"  - {warning}")

            print(f"\nTransaction Details:")
            for i, detail in enumerate(report['details'][:5]):  # Show first 5
                status_emoji = {
                    "matched": "✅",
                    "possible_match": "🤔",
                    "unmatched": "❌",
                    "overpaid": "💰",
                    "underpaid": "💸"
                }.get(detail['status'], "❓")

                print(f"  {i+1}. {status_emoji} {detail['status']} (confidence: {detail['confidence']:.3f})")
                print(f"     Date: {detail['transaction_date']}")
                print(f"     Description: {detail['transaction_description'][:50]}")
                print(f"     Amount: {detail['transaction_amount']:.2f} (expected: {detail['expected_amount']:.2f})")
                if detail['warnings']:
                    print(f"     Warnings: {', '.join(detail['warnings'])}")
                print()

            if len(report['details']) > 5:
                print(f"  ... and {len(report['details']) - 5} more transactions")

            print(f"\n⚠️  HUMAN REVIEW REQUIRED")
            print(f"All matching results require manual verification.")
            print(f"This system assists with matching but does not replace professional judgment.")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
