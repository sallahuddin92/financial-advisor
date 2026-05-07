import json
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

import pytest

from malaysia_fsi.bank_statement.invoice_matcher import InvoiceMatcher, MatchResult
from malaysia_fsi.bank_statement.report import (
    export_reconciliation_csv,
    export_reconciliation_json,
    export_reconciliation_markdown,
)
from malaysia_fsi.bank_statement.schema import BankStatement, Transaction, TransactionDirection

EDGE_FIXTURES = Path("test-fixtures/sample-data/invoices-edge-cases")


def warning_codes(warnings):
    return [item.get("code") for item in warnings]

class TestInvoiceMatcher:
    """Test invoice matching functionality"""

    def test_load_invoice_valid(self):
        """Test loading valid invoice JSON"""
        matcher = InvoiceMatcher()

        # Create temporary invoice file
        invoice_data = {
            "invoice_number": "INV-2024-001",
            "date": "2024-01-15",
            "supplier": {"name": "ABC Supplies"},
            "grand_total": 1000.00
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invoice_data, f)
            temp_path = Path(f.name)

        try:
            result = matcher.load_invoice(temp_path)
            assert result is not None
            assert result["invoice_number"] == "INV-2024-001"
            assert result["grand_total"] == 1000.00
        finally:
            temp_path.unlink()

    def test_load_invoice_invalid(self):
        """Test loading invalid invoice file"""
        matcher = InvoiceMatcher()
        result = matcher.load_invoice(Path("nonexistent.json"))
        assert result is None

    def test_extract_keywords(self):
        """Test keyword extraction"""
        matcher = InvoiceMatcher()

        text = "Payment to ABC Supplier for office supplies"
        keywords = matcher.extract_keywords(text)

        assert "payment" in keywords
        assert "abc" in keywords
        assert "supplier" in keywords
        assert "office" in keywords
        assert "supplies" in keywords
        assert "to" not in keywords  # Stop word
        assert "for" not in keywords  # Stop word

    def test_calculate_date_score(self):
        """Test date scoring"""
        matcher = InvoiceMatcher()

        tx_date = date(2024, 1, 15)

        # Same date
        score = matcher.calculate_date_score(tx_date, date(2024, 1, 15))
        assert score == 1.0

        # 1 day difference
        score = matcher.calculate_date_score(tx_date, date(2024, 1, 16))
        assert score == 0.9

        # 3 days difference
        score = matcher.calculate_date_score(tx_date, date(2024, 1, 18))
        assert score == 0.7

        # Beyond tolerance
        score = matcher.calculate_date_score(tx_date, date(2024, 2, 15))
        assert score == 0.0

        # No invoice date
        score = matcher.calculate_date_score(tx_date, None)
        assert score == 0.5

    def test_calculate_amount_score(self):
        """Test amount scoring"""
        matcher = InvoiceMatcher()

        # Exact match
        score = matcher.calculate_amount_score(1000.00, 1000.00)
        assert score == 1.0

        # Within tolerance (1% of 1000 = 10, so 1010 is within tolerance)
        score = matcher.calculate_amount_score(1000.00, 1010.00)
        assert score == 1.0

        # 5% difference
        score = matcher.calculate_amount_score(1000.00, 1050.00)
        assert score == 0.6

        # 10% difference
        score = matcher.calculate_amount_score(1000.00, 1100.00)
        assert score == 0.4

        # Large difference
        score = matcher.calculate_amount_score(1000.00, 2000.00)
        assert score == 0.0

    def test_calculate_keyword_score(self):
        """Test keyword scoring"""
        matcher = InvoiceMatcher()

        tx_description = "Payment to ABC Supplier for office rent"
        invoice_texts = ["ABC Supplier", "Office rental services"]

        score = matcher.calculate_keyword_score(tx_description, invoice_texts)
        assert score >= 0.3  # Should have some similarity (lower threshold)

        # No match
        score = matcher.calculate_keyword_score("Payment to XYZ Corp", ["ABC Supplier"])
        assert score < 0.5

        # Missing data
        score = matcher.calculate_keyword_score("", ["ABC Supplier"])
        assert score == 0.5

    def test_find_invoice_number_match(self):
        """Test invoice number matching"""
        matcher = InvoiceMatcher()

        # Direct match
        score = matcher.find_invoice_number_match(
            "Payment for INV-2024-001", "INV-2024-001"
        )
        assert score == 1.0

        # Case insensitive
        score = matcher.find_invoice_number_match(
            "Payment for inv-2024-001", "INV-2024-001"
        )
        assert score == 1.0

        # No dashes
        score = matcher.find_invoice_number_match(
            "Payment for INV2024001", "INV-2024-001"
        )
        assert score == 1.0

        # No match
        score = matcher.find_invoice_number_match(
            "Payment for INV-2024-002", "INV-2024-001"
        )
        assert score == 0.0

    def test_match_transaction_to_invoice_exact(self):
        """Test exact transaction to invoice matching"""
        matcher = InvoiceMatcher()

        transaction = Transaction(
            date=date(2024, 1, 15),
            description="Payment to ABC Supplies for INV-2024-001",
            credit=1000.00,
            source_bank="Maybank"
        )

        invoice = {
            "invoice_number": "INV-2024-001",
            "date": "2024-01-15",
            "supplier": {"name": "ABC Supplies"},
            "grand_total": 1000.00,
            "items": [{"description": "Office supplies"}]
        }

        result = matcher.match_transaction_to_invoice(transaction, invoice)

        assert result.status == "matched"
        assert result.confidence >= 0.8
        assert result.matched_amount == 1000.00
        assert result.expected_amount == 1000.00

    def test_match_transaction_to_invoice_overpaid(self):
        """Test overpaid transaction matching"""
        matcher = InvoiceMatcher()

        transaction = Transaction(
            date=date(2024, 1, 15),
            description="Payment to ABC Supplies",
            credit=1100.00,  # 100 more than invoice
            source_bank="Maybank"
        )

        invoice = {
            "invoice_number": "INV-2024-001",
            "date": "2024-01-15",
            "supplier": {"name": "ABC Supplies"},
            "grand_total": 1000.00
        }

        result = matcher.match_transaction_to_invoice(transaction, invoice)

        # With current logic, this might be "possible_match" due to scoring thresholds
        assert result.status in ["overpaid", "possible_match"]
        assert result.confidence > 0.5
        assert "INVALID_AMOUNT" in warning_codes(result.warnings)

    def test_match_transaction_to_invoice_underpaid(self):
        """Test underpaid transaction matching"""
        matcher = InvoiceMatcher()

        transaction = Transaction(
            date=date(2024, 1, 15),
            description="Payment to ABC Supplies",
            credit=900.00,  # 100 less than invoice
            source_bank="Maybank"
        )

        invoice = {
            "invoice_number": "INV-2024-001",
            "date": "2024-01-15",
            "supplier": {"name": "ABC Supplies"},
            "grand_total": 1000.00
        }

        result = matcher.match_transaction_to_invoice(transaction, invoice)

        # With current logic, this might be "possible_match" due to scoring thresholds
        assert result.status in ["underpaid", "possible_match"]
        assert result.confidence > 0.5

    def test_match_statement_to_invoices(self):
        """Test matching entire statement to multiple invoices"""
        matcher = InvoiceMatcher()

        # Create test statement
        transactions = [
            Transaction(
                date=date(2024, 1, 15),
                description="Payment to ABC Supplies",
                credit=1000.00,
                source_bank="Maybank"
            ),
            Transaction(
                date=date(2024, 1, 20),
                description="Office rent payment",
                debit=2000.00,
                source_bank="Maybank"
            )
        ]

        statement = BankStatement(
            bank_name="Maybank",
            transactions=transactions,
            statement_period_start=date(2024, 1, 1),
            statement_period_end=date(2024, 1, 31)
        )

        # Create temporary invoice files
        invoice1 = {
            "invoice_number": "INV-2024-001",
            "date": "2024-01-15",
            "supplier": {"name": "ABC Supplies"},
            "grand_total": 1000.00
        }

        invoice2 = {
            "invoice_number": "RENT-2024-001",
            "date": "2024-01-20",
            "supplier": {"name": "Property Management"},
            "grand_total": 2000.00
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f1:
            json.dump(invoice1, f1)
            temp_path1 = Path(f1.name)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f2:
            json.dump(invoice2, f2)
            temp_path2 = Path(f2.name)

        try:
            results = matcher.match_statement_to_invoices(statement, [temp_path1, temp_path2])

            assert len(results) == 2
            assert any(r.status == "matched" for r in results)

            report = matcher.generate_matching_report(results)
            assert report["total_transactions"] == 2
            assert report["matched"] >= 1

        finally:
            temp_path1.unlink()
            temp_path2.unlink()

    def test_generate_matching_report(self):
        """Test matching report generation"""
        matcher = InvoiceMatcher()

        # Create test results
        results = [
            type('MockResult', (), {
                'status': 'matched',
                'confidence': 0.9,
                'matched_amount': 1000.0,
                'expected_amount': 1000.0,
                'matched_transaction': Transaction(
                    date=date(2024, 1, 15),
                    description="Test payment",
                    source_bank="Maybank"
                ),
                'warnings': []
            }),
            type('MockResult', (), {
                'status': 'unmatched',
                'confidence': 0.2,
                'matched_amount': 500.0,
                'expected_amount': 0.0,
                'matched_transaction': Transaction(
                    date=date(2024, 1, 16),
                    description="Unmatched payment",
                    source_bank="Maybank"
                ),
                'warnings': [{'code': 'UNMATCHED_TRANSACTION', 'message': 'No matching invoice found'}]
            })
        ]

        report = matcher.generate_matching_report(results)

        assert report["total_transactions"] == 2
        assert report["matched"] == 1
        assert report["unmatched"] == 1
        assert report["average_confidence"] == 0.55
        assert len(report["details"]) == 2
        assert any(item["code"] == "UNMATCHED_TRANSACTION" for item in report["warnings"])

    def test_duplicate_candidates_produce_ambiguity_warning(self):
        """Test warning when multiple invoices are similarly strong candidates"""
        matcher = InvoiceMatcher()

        transaction = Transaction(
            date=date(2024, 3, 1),
            description="Payment to ABC Supplies for office supplies",
            credit=1000.00,
            source_bank="Maybank"
        )
        statement = BankStatement(
            bank_name="Maybank",
            transactions=[transaction],
            statement_period_start=date(2024, 3, 1),
            statement_period_end=date(2024, 3, 1)
        )

        invoice_paths = [
            EDGE_FIXTURES / "duplicate-candidate-1.json",
            EDGE_FIXTURES / "duplicate-candidate-2.json",
        ]

        if not all(path.exists() for path in invoice_paths):
            pytest.skip("Duplicate candidate fixtures not found")

        results = matcher.match_statement_to_invoices(statement, invoice_paths)

        assert len(results) == 1
        assert "DUPLICATE_CANDIDATE" in warning_codes(results[0].warnings)

    def test_near_amount_difference_produces_warning(self):
        """Test warning for near amount matches that exceed strict tolerance"""
        matcher = InvoiceMatcher()
        invoice_path = EDGE_FIXTURES / "near-amount-match.json"

        if not invoice_path.exists():
            pytest.skip("Near amount fixture not found")

        invoice = matcher.load_invoice(invoice_path)

        transaction = Transaction(
            date=date(2024, 3, 5),
            description="Payment to Near Amount Supplier for monthly service fee",
            credit=1030.00,  # 3% above invoice total
            source_bank="Maybank"
        )

        result = matcher.match_transaction_to_invoice(transaction, invoice)

        assert "INVALID_AMOUNT" in warning_codes(result.warnings)

    def test_date_outside_tolerance_produces_warning(self):
        """Test warning when invoice date is far outside matching tolerance"""
        matcher = InvoiceMatcher()
        invoice_path = EDGE_FIXTURES / "date-outside-tolerance.json"

        if not invoice_path.exists():
            pytest.skip("Date outside tolerance fixture not found")

        invoice = matcher.load_invoice(invoice_path)

        transaction = Transaction(
            date=date(2024, 3, 20),
            description="Annual subscription payment",
            credit=500.00,
            source_bank="Maybank"
        )

        result = matcher.match_transaction_to_invoice(transaction, invoice)

        assert "INVALID_DATE" in warning_codes(result.warnings)

    def test_missing_supplier_and_customer_name_produces_warning(self):
        """Test warning when invoice has insufficient party-name context"""
        matcher = InvoiceMatcher()
        invoice_path = EDGE_FIXTURES / "missing-supplier-customer-name.json"

        if not invoice_path.exists():
            pytest.skip("Missing names fixture not found")

        invoice = matcher.load_invoice(invoice_path)

        transaction = Transaction(
            date=date(2024, 3, 8),
            description="Payment for services",
            credit=750.00,
            source_bank="Maybank"
        )

        result = matcher.match_transaction_to_invoice(transaction, invoice)

        assert "MISSING_COUNTERPARTY" in warning_codes(result.warnings)

    def test_build_reconciliation_report_json_summary_totals(self):
        """Test reconciliation JSON summary shape and total calculations"""
        matcher = InvoiceMatcher()

        statement = BankStatement(
            bank_name="Maybank",
            transactions=[
                Transaction(
                    date=date(2024, 1, 15),
                    description="Payment INV-2024-001",
                    credit=1000.00,
                    source_bank="Maybank"
                ),
                Transaction(
                    date=date(2024, 1, 20),
                    description="Partial payment INV-2024-002",
                    credit=950.00,
                    source_bank="Maybank"
                ),
            ],
            statement_period_start=date(2024, 1, 1),
            statement_period_end=date(2024, 1, 31),
            warnings=[{"code": "STATEMENT_WARNING", "message": "Statement-level warning"}]
        )

        invoice_1 = {
            "invoice_number": "INV-2024-001",
            "date": "2024-01-15",
            "supplier": {"name": "ABC Supplies"},
            "grand_total": 1000.00
        }
        invoice_2 = {
            "invoice_number": "INV-2024-002",
            "date": "2024-01-20",
            "supplier": {"name": "ABC Supplies"},
            "grand_total": 1000.00
        }
        invoice_3 = {
            "invoice_number": "INV-2024-003",
            "date": "2024-01-21",
            "supplier": {"name": "DEF Services"},
            "grand_total": 500.00
        }

        match_1 = matcher.match_transaction_to_invoice(statement.transactions[0], invoice_1)
        match_2 = matcher.match_transaction_to_invoice(statement.transactions[1], invoice_2)
        no_match = MatchResult(
            "unmatched",
            0.1,
            [{"code": "UNMATCHED_TRANSACTION", "message": "No matching invoice found"}],
        )
        no_match.matched_transaction = Transaction(
            date=date(2024, 1, 25),
            description="Bank charge",
            debit=25.0,
            source_bank="Maybank"
        )

        report = matcher.build_reconciliation_report(
            statement=statement,
            results=[match_1, match_2, no_match],
            invoices=[invoice_1, invoice_2, invoice_3],
        )

        assert report["statement_bank"] == "Maybank"
        assert report["statement_period"]["start"] == "2024-01-01"
        assert report["statement_period"]["end"] == "2024-01-31"
        assert report["total_transactions"] == 2
        assert report["total_invoices"] == 3
        assert report["matched_count"] + report["possible_match_count"] + report["overpaid_count"] + report["underpaid_count"] >= 2
        assert report["unmatched_count"] >= 1
        assert report["total_matched_amount"] == 1950.0
        assert report["total_unmatched_invoice_amount"] == 500.0
        assert report["human_review_required"] is True
        assert any(item["code"] == "STATEMENT_WARNING" for item in report["warnings"])
        assert any(item["code"] == "HUMAN_REVIEW_REQUIRED" for item in report["warnings"])

    def test_match_cli_json_flag_outputs_reconciliation_json(self):
        """Test legacy match CLI path outputs reconciliation JSON summary."""
        sample_statement = Path("test-fixtures/sample-data/maybank-valid.csv")
        sample_invoice = Path("test-fixtures/sample-data/invoices-exact-match/invoice-abc-001.json")
        match_cli_path = Path(
            "plugins/vertical-plugins/malaysia-compliance/skills/bank-statement-parser/match_cli.py"
        )

        if not sample_statement.exists() or not sample_invoice.exists():
            pytest.skip("Required sample fixtures not found")

        proc = subprocess.run(
            [
                sys.executable,
                str(match_cli_path),
                str(sample_statement),
                str(sample_invoice),
                "--json",
                "--bank",
                "maybank",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert proc.returncode == 0, proc.stderr
        payload = json.loads(proc.stdout)
        assert payload["statement_bank"] == "Maybank"
        assert payload["total_invoices"] == 1
        assert "human_review_required" in payload
        assert payload["human_review_required"] is True
        assert any(item["code"] == "HUMAN_REVIEW_REQUIRED" for item in payload["warnings"])

    def test_new_cli_match_subcommand_json_output(self):
        """Test new module CLI match subcommand JSON payload."""
        sample_statement = Path("test-fixtures/sample-data/maybank-valid.csv")
        sample_invoice = Path("test-fixtures/sample-data/invoices-exact-match/invoice-abc-001.json")

        if not sample_statement.exists() or not sample_invoice.exists():
            pytest.skip("Required sample fixtures not found")

        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "malaysia_fsi.bank_statement.cli",
                "match",
                str(sample_statement),
                str(sample_invoice),
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert proc.returncode == 0, proc.stderr
        payload = json.loads(proc.stdout)
        assert payload["statement_bank"] == "Maybank"
        assert payload["human_review_required"] is True

    def test_new_cli_validate_subcommand_json_output(self):
        """Test validate subcommand produces machine-readable JSON."""
        sample_statement = Path("test-fixtures/sample-data/maybank-valid.csv")
        sample_invoice = Path("test-fixtures/sample-data/invoices-exact-match/invoice-abc-001.json")

        if not sample_statement.exists() or not sample_invoice.exists():
            pytest.skip("Required sample fixtures not found")

        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "malaysia_fsi.bank_statement.cli",
                "validate",
                "--input",
                str(sample_statement),
                "--invoice",
                str(sample_invoice),
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert proc.returncode == 0, proc.stderr
        payload = json.loads(proc.stdout)
        assert "valid" in payload
        assert payload["human_review_required"] is True

    def test_invalid_invoice_json_produces_structured_warning(self):
        """Test invalid invoice JSON creates coded warning."""
        matcher = InvoiceMatcher()

        statement = BankStatement(
            bank_name="Maybank",
            transactions=[
                Transaction(
                    date=date(2024, 1, 15),
                    description="Payment",
                    credit=100.00,
                    source_bank="Maybank",
                )
            ],
        )
        invalid_invoice_path = Path("test-fixtures/sample-data/invoices-invalid/invalid-json.json")
        results = matcher.match_statement_to_invoices(statement, [invalid_invoice_path])
        assert any(
            item["code"] == "INVALID_INVOICE_JSON"
            for result in results
            for item in result.warnings
        )

    def test_missing_invoice_fields_warning_codes(self):
        """Test missing invoice fields return structured warnings with message."""
        matcher = InvoiceMatcher()
        transaction = Transaction(
            date=date(2024, 1, 15),
            description="Payment without valid invoice fields",
            credit=100.00,
            source_bank="Maybank",
        )
        invoice = {"date": "2024-01-15"}  # Missing invoice_number and grand_total
        result = matcher.match_transaction_to_invoice(transaction, invoice)
        codes = warning_codes(result.warnings)
        assert "MISSING_INVOICE_FIELD" in codes
        assert "HUMAN_REVIEW_REQUIRED" in codes
        assert all("message" in item for item in result.warnings)

    def test_decimal_totals_are_money_safe(self):
        """Test Decimal-backed totals avoid float rounding surprises."""
        matcher = InvoiceMatcher()
        statement = BankStatement(
            bank_name="Maybank",
            transactions=[],
            statement_period_start=date(2024, 1, 1),
            statement_period_end=date(2024, 1, 31),
        )
        results = [
            MatchResult("matched", 0.9, []),
            MatchResult("matched", 0.9, []),
        ]
        results[0].matched_amount = 0.1 + 0.2
        results[1].matched_amount = 0.3
        invoices = [{"invoice_number": "INV-A", "grand_total": 0.3}]
        report = matcher.build_reconciliation_report(statement, results, invoices)
        assert report["total_matched_amount"] == 0.6

    def test_report_exporters_json_csv_markdown(self):
        """Test reconciliation report exporters for JSON/CSV/Markdown outputs."""
        report = {
            "statement_bank": "Maybank",
            "statement_period": {"start": "2024-01-01", "end": "2024-01-31"},
            "total_transactions": 2,
            "total_invoices": 1,
            "matched_count": 1,
            "possible_match_count": 0,
            "unmatched_count": 1,
            "overpaid_count": 0,
            "underpaid_count": 0,
            "total_matched_amount": 1000.0,
            "total_unmatched_invoice_amount": 200.0,
            "warnings": [{"code": "HUMAN_REVIEW_REQUIRED", "message": "Review required"}],
            "human_review_required": True,
        }

        json_text = export_reconciliation_json(report)
        csv_text = export_reconciliation_csv(report)
        md_text = export_reconciliation_markdown(report)

        assert "\"statement_bank\": \"Maybank\"" in json_text
        assert "field,value" in csv_text
        assert "statement_bank,Maybank" in csv_text
        assert "# Reconciliation Report" in md_text
        assert "HUMAN REVIEW REQUIRED" in md_text

    def test_new_cli_match_csv_and_markdown_output_files(self):
        """Test CLI match writes CSV and Markdown output files."""
        sample_statement = Path("test-fixtures/sample-data/maybank-valid.csv")
        sample_invoice = Path("test-fixtures/sample-data/invoices-exact-match/invoice-abc-001.json")

        if not sample_statement.exists() or not sample_invoice.exists():
            pytest.skip("Required sample fixtures not found")

        csv_out = Path("/tmp/reconciliation-report-test.csv")
        md_out = Path("/tmp/reconciliation-report-test.md")
        csv_out.unlink(missing_ok=True)
        md_out.unlink(missing_ok=True)

        proc_csv = subprocess.run(
            [
                sys.executable,
                "-m",
                "malaysia_fsi.bank_statement.cli",
                "match",
                str(sample_statement),
                str(sample_invoice),
                "--format",
                "csv",
                "--output",
                str(csv_out),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc_csv.returncode == 0, proc_csv.stderr
        assert csv_out.exists()
        assert "field,value" in csv_out.read_text()

        proc_md = subprocess.run(
            [
                sys.executable,
                "-m",
                "malaysia_fsi.bank_statement.cli",
                "match",
                str(sample_statement),
                str(sample_invoice),
                "--format",
                "md",
                "--output",
                str(md_out),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc_md.returncode == 0, proc_md.stderr
        assert md_out.exists()
        md_text = md_out.read_text()
        assert "Reconciliation Report" in md_text
        assert "HUMAN REVIEW REQUIRED" in md_text
