"""
Bank statement parser for Malaysian banks
Currently supports Maybank CSV format
"""

import csv
import re
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pathlib import Path

# Handle both standalone and relative imports
try:
    from .schema import Transaction, BankStatement, TransactionDirection
except ImportError:
    # Fallback for standalone execution
    import importlib.util
    import sys
    from pathlib import Path

    schema_path = Path(__file__).parent / "schema.py"
    spec = importlib.util.spec_from_file_location("schema", schema_path)
    schema = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(schema)

    Transaction = schema.Transaction
    BankStatement = schema.BankStatement
    TransactionDirection = schema.TransactionDirection

class MaybankCSVParser:
    """Parser for Maybank CSV statement format"""

    def __init__(self):
        self.bank_name = "Maybank"
        self.confidence = 0.9

    def parse_date(self, date_str: str) -> Optional[date]:
        """Parse date from various formats"""
        date_formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d"
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue

        return None

    def normalize_amount(self, amount_str: str) -> Optional[float]:
        """Normalize amount string to float"""
        if not amount_str or amount_str.strip() == "":
            return None

        # Remove currency symbols and formatting
        cleaned = re.sub(r'[^\d.-]', '', amount_str.strip())

        try:
            return float(cleaned)
        except ValueError:
            return None

    def parse_csv(self, file_path: Path) -> BankStatement:
        """Parse Maybank CSV file"""
        transactions = []
        warnings = []

        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                # Read header to understand structure
                sample = csvfile.read(1024)
                csvfile.seek(0)

                # Detect delimiter
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter

                reader = csv.DictReader(csvfile, delimiter=delimiter)

                # Expected columns based on sample data
                expected_columns = ['Date', 'Description', 'Debit', 'Credit', 'Balance']
                actual_columns = reader.fieldnames or []

                missing_columns = [col for col in expected_columns if col not in actual_columns]
                if missing_columns:
                    warnings.append(f"Missing expected columns: {missing_columns}")

                for row_num, row in enumerate(reader, start=2):  # Start at 2 due to header
                    try:
                        # Parse date
                        date_obj = self.parse_date(row.get('Date', ''))
                        if not date_obj:
                            warnings.append(f"Row {row_num}: Could not parse date '{row.get('Date', '')}'")
                            continue

                        # Parse amounts
                        raw_debit = (row.get('Debit', '') or '').strip()
                        raw_credit = (row.get('Credit', '') or '').strip()
                        raw_balance = (row.get('Balance', '') or '').strip()

                        debit = self.normalize_amount(raw_debit)
                        credit = self.normalize_amount(raw_credit)
                        balance = self.normalize_amount(raw_balance)

                        if raw_debit and debit is None:
                            warnings.append(f"Row {row_num}: Non-numeric debit '{raw_debit}'")
                        if raw_credit and credit is None:
                            warnings.append(f"Row {row_num}: Non-numeric credit '{raw_credit}'")
                        if raw_balance and balance is None:
                            warnings.append(f"Row {row_num}: Non-numeric balance '{raw_balance}'")

                        has_debit = debit is not None and debit > 0
                        has_credit = credit is not None and credit > 0

                        if has_debit and has_credit:
                            warnings.append(f"Row {row_num}: Both debit and credit are populated; treating row as debit")
                            credit = None
                            has_credit = False

                        if not has_debit and not has_credit:
                            warnings.append(f"Row {row_num}: Missing amount (both debit and credit are empty or invalid)")
                            continue

                        # Create transaction
                        transaction = Transaction(
                            date=date_obj,
                            description=row.get('Description', '').strip(),
                            debit=debit if has_debit else None,
                            credit=credit if has_credit else None,
                            balance=balance,
                            currency="MYR",
                            source_bank=self.bank_name,
                            confidence=self.confidence
                        )

                        transactions.append(transaction)

                    except Exception as e:
                        warnings.append(f"Row {row_num}: Error parsing row - {str(e)}")
                        continue

        except Exception as e:
            warnings.append(f"Error reading file: {str(e)}")

        # Determine statement period
        if transactions:
            statement_start = min(t.date for t in transactions)
            statement_end = max(t.date for t in transactions)
        else:
            statement_start = statement_end = None
            warnings.append("No transactions found in file")

        return BankStatement(
            bank_name=self.bank_name,
            statement_period_start=statement_start,
            statement_period_end=statement_end,
            currency="MYR",
            transactions=transactions,
            warnings=warnings,
            confidence=self.confidence if transactions else 0.0
        )

class BankStatementParser:
    """Main parser interface"""

    def __init__(self):
        self.parsers = {
            'maybank': MaybankCSVParser(),
        }

    def parse_file(self, file_path: Path, bank_hint: Optional[str] = None) -> BankStatement:
        """Parse bank statement file"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # For now, only support Maybank CSV
        if bank_hint and bank_hint.lower() in self.parsers:
            parser = self.parsers[bank_hint.lower()]
        else:
            # Default to Maybank for CSV files
            if file_path.suffix.lower() == '.csv':
                parser = self.parsers['maybank']
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")

        return parser.parse_csv(file_path)

    def get_supported_banks(self) -> List[str]:
        """Get list of supported banks"""
        return list(self.parsers.keys())

    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats"""
        return ['.csv']
