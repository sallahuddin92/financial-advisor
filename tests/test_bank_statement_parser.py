"""Unit tests for bank statement parser."""

import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from malaysia_fsi.bank_statement.parser import (
    PLACEHOLDER_NOT_IMPLEMENTED_MESSAGE,
    BankStatementParser,
    MaybankCSVParser,
)
from malaysia_fsi.bank_statement.schema import BankStatement, Transaction, TransactionDirection


def warning_codes(warnings):
    return [item.get("code") for item in warnings]


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

    def test_parse_malformed_csv_produces_warnings(self):
        """Test malformed Maybank CSV rows produce explicit warnings"""
        malformed_file = Path("test-fixtures/sample-data/sample-maybank-statement-malformed.csv")

        if not malformed_file.exists():
            pytest.skip("Malformed sample file not found")

        parser = MaybankCSVParser()
        statement = parser.parse_csv(malformed_file)

        assert len(statement.transactions) == 2
        codes = warning_codes(statement.warnings)
        assert "INVALID_AMOUNT" in codes
        assert "INVALID_DATE" in codes
        assert "BOTH_DEBIT_CREDIT_PRESENT" in codes
        assert "HUMAN_REVIEW_REQUIRED" in codes

class TestBankStatementParser:
    """Test main parser interface"""

    def test_get_supported_banks(self):
        """Test supported banks list"""
        parser = BankStatementParser()
        supported = parser.get_supported_banks()

        assert "maybank" in supported
        assert "cimb" in supported
        assert "public-bank" in supported
        assert "rhb" in supported
        assert "hong-leong-bank" in supported
        assert len(supported) == 5

    def test_get_enabled_banks(self):
        """Test enabled banks list (implemented parsers only)"""
        parser = BankStatementParser()
        enabled = parser.get_enabled_banks()

        assert enabled == ["maybank"]

    def test_disabled_banks_listed_but_not_enabled(self):
        """Test disabled bank parsers are visible but clearly disabled"""
        parser = BankStatementParser()
        statuses = parser.get_bank_statuses()
        status_by_bank = {entry["bank_code"]: entry for entry in statuses}

        for bank_code in ["cimb", "public-bank", "rhb", "hong-leong-bank"]:
            assert bank_code in status_by_bank
            assert status_by_bank[bank_code]["enabled"] is False
            assert status_by_bank[bank_code]["production_ready"] is False

    def test_no_unsupported_bank_claims_production_support(self):
        """Test unsupported bank formats never claim production readiness"""
        parser = BankStatementParser()
        statuses = parser.get_bank_statuses()

        for status in statuses:
            if not status["enabled"]:
                assert status["production_ready"] is False

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

    def test_parse_file_without_bank_hint_unknown_csv(self):
        """Test clear error when CSV headers do not match supported detectors"""
        unknown_file = Path("test-unknown-bank.csv")
        unknown_file.write_text("TxnDate,Details,Out,In,Bal\n2024-01-01,Test,100,,1000\n")

        try:
            parser = BankStatementParser()
            with pytest.raises(ValueError, match="Could not auto-detect a supported bank format"):
                parser.parse_file(unknown_file)
        finally:
            if unknown_file.exists():
                unknown_file.unlink()

    def test_disabled_bank_parsers_raise_not_implemented(self):
        """Test placeholders raise clear disabled message for unimplemented banks"""
        sample_file = Path("test-fixtures/sample-data/sample-maybank-statement.csv")

        if not sample_file.exists():
            pytest.skip("Sample file not found")

        parser = BankStatementParser()
        for bank_code in ["cimb", "public-bank", "rhb", "hong-leong-bank"]:
            with pytest.raises(NotImplementedError, match=PLACEHOLDER_NOT_IMPLEMENTED_MESSAGE):
                parser.parse_file(sample_file, bank_code)

    def test_legacy_plugin_parser_cli_still_works(self):
        """Test legacy plugin CLI path remains callable."""
        sample_file = Path("test-fixtures/sample-data/sample-maybank-statement.csv")
        cli_path = Path(
            "plugins/vertical-plugins/malaysia-compliance/skills/bank-statement-parser/cli.py"
        )

        if not sample_file.exists():
            pytest.skip("Sample file not found")

        proc = subprocess.run(
            [sys.executable, str(cli_path), str(sample_file), "--format", "json", "--bank", "maybank"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert proc.returncode == 0, proc.stderr
        assert "\"bank_name\": \"Maybank\"" in proc.stdout

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
        assert any(item["code"] == "INVALID_AMOUNT" for item in tx.warnings)
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
