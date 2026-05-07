"""
CLI interface for bank statement parser
"""

import argparse
import json
import importlib.util
import sys
from pathlib import Path
from typing import Dict, Any

# Load modules using file path to avoid hyphen import issues
schema_path = Path(__file__).parent / "schema.py"
parser_path = Path(__file__).parent / "parser.py"

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

# Import classes from loaded modules
BankStatementParser = parser_module.BankStatementParser
TransactionDirection = schema.TransactionDirection

def format_transaction_output(statement) -> Dict[str, Any]:
    """Format bank statement for JSON output"""
    return {
        "bank_name": statement.bank_name,
        "account_number": statement.account_number,
        "statement_period": {
            "start": statement.statement_period_start.isoformat() if statement.statement_period_start else None,
            "end": statement.statement_period_end.isoformat() if statement.statement_period_end else None
        },
        "currency": statement.currency,
        "confidence": statement.confidence,
        "warnings": statement.warnings,
        "transaction_count": len(statement.transactions),
        "transactions": [
            {
                "date": t.date.isoformat(),
                "description": t.description,
                "debit": t.debit,
                "credit": t.credit,
                "amount": t.amount,
                "direction": t.direction.value if t.direction else None,
                "balance": t.balance,
                "currency": t.currency,
                "source_bank": t.source_bank,
                "confidence": t.confidence,
                "warnings": t.warnings
            }
            for t in statement.transactions
        ]
    }

def main():
    """CLI main function"""
    parser = argparse.ArgumentParser(description="Parse Malaysian bank statement CSV files")
    parser.add_argument("file", type=Path, help="Path to bank statement CSV file")
    parser.add_argument("--bank", type=str, help="Bank name hint (maybank)", default=None)
    parser.add_argument("--format", choices=["json", "summary"], default="summary",
                       help="Output format")

    args = parser.parse_args()

    if not args.file.exists():
        print(f"Error: File not found: {args.file}")
        return 1

    try:
        # Parse the file
        bank_parser = BankStatementParser()
        statement = bank_parser.parse_file(args.file, args.bank)

        if args.format == "json":
            # JSON output
            output = format_transaction_output(statement)
            print(json.dumps(output, indent=2))
        else:
            # Summary output
            print(f"=== Bank Statement Summary ===")
            print(f"Bank: {statement.bank_name}")
            print(f"Period: {statement.statement_period_start} to {statement.statement_period_end}")
            print(f"Currency: {statement.currency}")
            print(f"Transactions: {len(statement.transactions)}")
            print(f"Confidence: {statement.confidence:.2f}")

            if statement.warnings:
                print(f"\nWarnings:")
                for warning in statement.warnings:
                    print(f"  - {warning}")

            print(f"\nFirst 5 transactions:")
            for i, t in enumerate(statement.transactions[:5]):
                direction_symbol = "→" if t.direction == TransactionDirection.CREDIT else "←"
                amount_str = f"{abs(t.amount or 0):.2f}" if t.amount else "0.00"
                print(f"  {i+1}. {t.date} {direction_symbol} {t.description[:50]} ({amount_str} {t.currency})")

            if len(statement.transactions) > 5:
                print(f"  ... and {len(statement.transactions) - 5} more")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())