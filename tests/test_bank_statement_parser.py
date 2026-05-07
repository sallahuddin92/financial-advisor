"""
Unit tests for bank statement parser
"""

import importlib.util
import sys
from datetime import date
from pathlib import Path
import pytest

# Load modules using file path to avoid hyphen import issues
base_path = Path(__file__).parent.parent
parser_path = base_path / "plugins" / "vertical-plugins" / "malaysia-compliance" / "skills" / "bank-statement-parser" / "parser.py"
schema_path = base_path / "plugins" / "vertical-plugins" / "malaysia-compliance" / "skills" / "bank-statement-parser" / "schema.py"

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
Transaction = schema.Transaction
TransactionDirection = schema.TransactionDirection
BankStatement = schema.BankStatement
BankStatementParser = parser_module.BankStatementParser
MaybankCSVParser = parser_module.MaybankCSVParser

class TestMaybankCSVParser:
    """Test Maybank CSV parser"""

    def test_parse_sample_data(self):
        """Test parsing the sample Maybank CSV file"""
        sample_file = Path("test-fixtures/sample-data/sample-maybank-statement.csv")

        if not sample_file.exists():
            pytest.skip("Sample file not found")

        parser = MaybankCSVParser()
        statement = parser.parse_csv(sample_file)

        # Basic validation
        assert statement.bank_name == "Maybank"
        assert statement.currency == "MYR"
        assert len(statement.transactions) == 10  # Expected number of transactions
        assert statement.confidence > 0.8

        # Check first transaction (Salary Credit)
        first_tx = statement.transactions[0]
        assert first_tx.date == date(2024, 1, 2)
        assert "Salary Credit" in first_tx.description
        assert first_tx.credit == 15000.00
        assert first_tx.debit is None
        assert first_tx.amount == 15000.00
        assert first_tx.direction.value == "credit"  # Compare value instead of enum instance
        assert first_tx.balance == 15000.00

        # Check a debit transaction
        debit_tx = statement.transactions[1]  # Payment to ABC Supplier
        assert debit_tx.date == date(2024, 1, 5)
        assert "ABC Supplier" in debit_tx.description
        assert debit_tx.debit == 2500.00
        assert debit_tx.credit is None
        assert debit_tx.amount == -2500.00
        assert debit_tx.direction.value == "debit"  # Compare value instead of enum instance
        assert debit_tx.balance == 12500.00

        # Check statement period
        assert statement.statement_period_start == date(2024, 1, 2)
        assert statement.statement_period_end == date(2024, 1, 30)

    def test_date_parsing(self):
        """Test date parsing with various formats"""
        parser = MaybankCSVParser()

        # Test various date formats
        test_cases = [
            ("2024-01-15", date(2024, 1, 15)),
            ("15/01/2024", date(2024, 1, 15)),
            ("15-01-2024", date(2024, 1, 15)),
            ("2024/01/15", date(2024, 1, 15)),
        ]

        for date_str, expected in test_cases:
            result = parser.parse_date(date_str)
            assert result == expected, f"Failed to parse {date_str}"

    def test_amount_normalization(self):
        """Test amount normalization"""
        parser = MaybankCSVParser()

        test_cases = [
            ("15000.00", 15000.00),
            ("2,500.00", 2500.00),
            ("RM 100.50", 100.50),
            ("", None),
            ("N/A", None),
            ("abc", None),
        ]

        for amount_str, expected in test_cases:
            result = parser.normalize_amount(amount_str)
            assert result == expected, f"Failed to normalize {amount_str}"

class TestBankStatementParser:
    """Test main parser interface"""

    def test_get_supported_banks(self):
        """Test supported banks list"""
        parser = BankStatementParser()
        supported = parser.get_supported_banks()

        assert "maybank" in supported
        assert len(supported) == 1  # Only Maybank implemented

    def test_get_supported_formats(self):
        """Test supported formats list"""
        parser = BankStatementParser()
        formats = parser.get_supported_formats()

        assert ".csv" in formats
        assert len(formats) == 1  # Only CSV implemented

    def test_parse_file_with_bank_hint(self):
        """Test parsing with explicit bank hint"""
        sample_file = Path("test-fixtures/sample-data/sample-maybank-statement.csv")

        if not sample_file.exists():
            pytest.skip("Sample file not found")

        parser = BankStatementParser()
        statement = parser.parse_file(sample_file, "maybank")

        assert statement.bank_name == "Maybank"
        assert len(statement.transactions) > 0

    def test_parse_file_without_bank_hint(self):
        """Test parsing without bank hint (auto-detection)"""
        sample_file = Path("test-fixtures/sample-data/sample-maybank-statement.csv")

        if not sample_file.exists():
            pytest.skip("Sample file not found")

        parser = BankStatementParser()
        statement = parser.parse_file(sample_file)  # No bank hint

        assert statement.bank_name == "Maybank"
        assert len(statement.transactions) > 0

    def test_file_not_found(self):
        """Test error handling for missing file"""
        parser = BankStatementParser()

        with pytest.raises(FileNotFoundError):
            parser.parse_file(Path("nonexistent.csv"))

    def test_unsupported_format(self):
        """Test error handling for unsupported format"""
        # Create a dummy text file
        dummy_file = Path("test-dummy.txt")
        dummy_file.write_text("dummy content")

        try:
            parser = BankStatementParser()

            with pytest.raises(ValueError, match="Unsupported file format"):
                parser.parse_file(dummy_file)
        finally:
            # Clean up
            if dummy_file.exists():
                dummy_file.unlink()

class TestTransactionSchema:
    """Test transaction schema"""

    def test_transaction_with_debit(self):
        """Test transaction with debit amount"""
        tx = Transaction(
            date=date(2024, 1, 15),
            description="Test debit",
            debit=100.00,
            source_bank="Maybank"
        )

        assert tx.amount == -100.00
        assert tx.direction == TransactionDirection.DEBIT
        assert tx.credit is None

    def test_transaction_with_credit(self):
        """Test transaction with credit amount"""
        tx = Transaction(
            date=date(2024, 1, 15),
            description="Test credit",
            credit=200.00,
            source_bank="Maybank"
        )

        assert tx.amount == 200.00
        assert tx.direction == TransactionDirection.CREDIT
        assert tx.debit is None

    def test_transaction_with_signed_amount(self):
        """Test transaction with signed amount"""
        tx = Transaction(
            date=date(2024, 1, 15),
            description="Test signed amount",
            amount=-150.00,
            source_bank="Maybank"
        )

        assert tx.direction == TransactionDirection.DEBIT
        assert tx.debit == 150.00
        assert tx.credit is None

    def test_transaction_defaults(self):
        """Test transaction defaults"""
        tx = Transaction(
            date=date(2024, 1, 15),
            description="Test defaults"
        )

        assert tx.currency == "MYR"
        assert tx.warnings == []
        assert tx.confidence == 1.0

class TestBankStatementSchema:
    """Test bank statement schema"""

    def test_bank_statement_defaults(self):
        """Test bank statement defaults"""
        statement = BankStatement(bank_name="Test Bank")

        assert statement.currency == "MYR"
        assert statement.transactions == []
        assert statement.warnings == []
        assert statement.confidence == 1.0