"""Bank statement parser for Malaysian banks (offline/manual workflows)."""

import csv
import re
from datetime import date, datetime
from pathlib import Path
from typing import Callable, List, Optional

from .schema import BankStatement, Transaction, warning

PLACEHOLDER_NOT_IMPLEMENTED_MESSAGE = "Real anonymized fixture required before enabling this bank format."


class BaseBankParser:
    """Base parser contract for bank-specific parsers."""

    def __init__(self, bank_name: str, implemented: bool):
        self.bank_name = bank_name
        self.implemented = implemented

    def parse_csv(self, file_path: Path) -> BankStatement:
        raise NotImplementedError


class PlaceholderBankParser(BaseBankParser):
    """Disabled parser for bank formats without anonymized fixtures."""

    def __init__(self, bank_name: str):
        super().__init__(bank_name=bank_name, implemented=False)

    def parse_csv(self, file_path: Path) -> BankStatement:
        raise NotImplementedError(PLACEHOLDER_NOT_IMPLEMENTED_MESSAGE)


class MaybankCSVParser(BaseBankParser):
    """Parser for Maybank CSV statement format."""

    def __init__(self):
        super().__init__(bank_name="Maybank", implemented=True)
        self.confidence = 0.9

    def parse_date(self, date_str: str) -> Optional[date]:
        date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        return None

    def normalize_amount(self, amount_str: str) -> Optional[float]:
        if not amount_str or amount_str.strip() == "":
            return None

        cleaned = re.sub(r"[^\d.-]", "", amount_str.strip())
        try:
            return float(cleaned)
        except ValueError:
            return None

    def parse_csv(self, file_path: Path) -> BankStatement:
        transactions = []
        warnings = []

        try:
            with open(file_path, "r", encoding="utf-8") as csvfile:
                sample = csvfile.read(1024)
                csvfile.seek(0)

                delimiter = csv.Sniffer().sniff(sample).delimiter
                reader = csv.DictReader(csvfile, delimiter=delimiter)

                expected_columns = ["Date", "Description", "Debit", "Credit", "Balance"]
                actual_columns = reader.fieldnames or []
                missing_columns = [col for col in expected_columns if col not in actual_columns]
                if missing_columns:
                    warnings.append(
                        warning(
                            "MISSING_COLUMN",
                            f"Missing expected columns: {missing_columns}",
                        )
                    )

                for row_num, row in enumerate(reader, start=2):
                    try:
                        date_obj = self.parse_date(row.get("Date", ""))
                        if not date_obj:
                            warnings.append(
                                warning(
                                    "INVALID_DATE",
                                    f"Row {row_num}: Could not parse date '{row.get('Date', '')}'",
                                )
                            )
                            continue

                        raw_debit = (row.get("Debit", "") or "").strip()
                        raw_credit = (row.get("Credit", "") or "").strip()
                        raw_balance = (row.get("Balance", "") or "").strip()

                        debit = self.normalize_amount(raw_debit)
                        credit = self.normalize_amount(raw_credit)
                        balance = self.normalize_amount(raw_balance)

                        if raw_debit and debit is None:
                            warnings.append(
                                warning(
                                    "INVALID_AMOUNT",
                                    f"Row {row_num}: Non-numeric debit '{raw_debit}'",
                                )
                            )
                        if raw_credit and credit is None:
                            warnings.append(
                                warning(
                                    "INVALID_AMOUNT",
                                    f"Row {row_num}: Non-numeric credit '{raw_credit}'",
                                )
                            )
                        if raw_balance and balance is None:
                            warnings.append(
                                warning(
                                    "INVALID_AMOUNT",
                                    f"Row {row_num}: Non-numeric balance '{raw_balance}'",
                                )
                            )

                        has_debit = debit is not None and debit > 0
                        has_credit = credit is not None and credit > 0

                        if has_debit and has_credit:
                            warnings.append(
                                warning(
                                    "BOTH_DEBIT_CREDIT_PRESENT",
                                    f"Row {row_num}: Both debit and credit are populated; treating row as debit",
                                )
                            )
                            credit = None
                            has_credit = False

                        if not has_debit and not has_credit:
                            warnings.append(
                                warning(
                                    "INVALID_AMOUNT",
                                    f"Row {row_num}: Missing amount (both debit and credit are empty or invalid)",
                                )
                            )
                            continue

                        transaction = Transaction(
                            date=date_obj,
                            description=row.get("Description", "").strip(),
                            debit=debit if has_debit else None,
                            credit=credit if has_credit else None,
                            balance=balance,
                            currency="MYR",
                            source_bank=self.bank_name,
                            confidence=self.confidence,
                        )
                        transactions.append(transaction)

                    except Exception as exc:
                        warnings.append(
                            warning("ROW_PARSE_ERROR", f"Row {row_num}: Error parsing row - {str(exc)}")
                        )
                        continue

        except Exception as exc:
            warnings.append(warning("FILE_READ_ERROR", f"Error reading file: {str(exc)}"))

        if transactions:
            statement_start = min(t.date for t in transactions)
            statement_end = max(t.date for t in transactions)
        else:
            statement_start = None
            statement_end = None
            warnings.append(warning("NO_TRANSACTIONS", "No transactions found in file"))

        warnings.append(
            warning(
                "HUMAN_REVIEW_REQUIRED",
                "Parsed statement output requires human review before financial decisions.",
            )
        )

        return BankStatement(
            bank_name=self.bank_name,
            statement_period_start=statement_start,
            statement_period_end=statement_end,
            currency="MYR",
            transactions=transactions,
            warnings=warnings,
            confidence=self.confidence if transactions else 0.0,
        )


class CIMBCSVParser(PlaceholderBankParser):
    def __init__(self):
        super().__init__(bank_name="CIMB")


class PublicBankCSVParser(PlaceholderBankParser):
    def __init__(self):
        super().__init__(bank_name="Public Bank")


class RHBCSVParser(PlaceholderBankParser):
    def __init__(self):
        super().__init__(bank_name="RHB")


class HongLeongBankCSVParser(PlaceholderBankParser):
    def __init__(self):
        super().__init__(bank_name="Hong Leong Bank")


class ParserRegistry:
    """Registry/factory for bank statement parsers and format detection."""

    def __init__(self):
        self._parsers = {}
        self._detectors = {}

    def register_parser(
        self,
        bank_code: str,
        parser: BaseBankParser,
        detector: Optional[Callable[[Path], bool]] = None,
    ) -> None:
        code = bank_code.lower()
        self._parsers[code] = parser
        if detector is not None:
            self._detectors[code] = detector

    def get_parser(self, bank_code: str) -> BaseBankParser:
        parser = self._parsers.get((bank_code or "").lower())
        if not parser:
            supported = ", ".join(sorted(self._parsers.keys()))
            raise ValueError(f"Unsupported bank hint '{bank_code}'. Supported banks: {supported}")
        return parser

    def list_banks(self) -> List[str]:
        return list(self._parsers.keys())

    def detect_bank(self, file_path: Path) -> Optional[str]:
        for bank_code, detector in self._detectors.items():
            try:
                if detector(file_path):
                    return bank_code
            except Exception:
                continue
        return None

    def get_bank_statuses(self) -> List[dict]:
        statuses = []
        for bank_code, parser in self._parsers.items():
            statuses.append(
                {
                    "bank_code": bank_code,
                    "bank_name": parser.bank_name,
                    "enabled": parser.implemented,
                    "production_ready": False,
                }
            )
        return statuses


class BankStatementParser:
    """Main parser interface."""

    def __init__(self):
        self.registry = ParserRegistry()
        self.registry.register_parser("maybank", MaybankCSVParser(), detector=self._detect_maybank_csv)
        self.registry.register_parser("cimb", CIMBCSVParser())
        self.registry.register_parser("public-bank", PublicBankCSVParser())
        self.registry.register_parser("rhb", RHBCSVParser())
        self.registry.register_parser("hong-leong-bank", HongLeongBankCSVParser())

    def _detect_maybank_csv(self, file_path: Path) -> bool:
        if file_path.suffix.lower() != ".csv":
            return False
        try:
            with open(file_path, "r", encoding="utf-8") as csvfile:
                sample = csvfile.read(1024)
                csvfile.seek(0)
                delimiter = csv.Sniffer().sniff(sample).delimiter
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                expected_columns = {"Date", "Description", "Debit", "Credit", "Balance"}
                actual_columns = set(reader.fieldnames or [])
                return expected_columns.issubset(actual_columns)
        except Exception:
            return False

    def parse_file(self, file_path: Path, bank_hint: Optional[str] = None) -> BankStatement:
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_path.suffix.lower() != ".csv":
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        if bank_hint:
            parser = self.registry.get_parser(bank_hint)
        else:
            detected_bank = self.registry.detect_bank(file_path)
            if not detected_bank:
                raise ValueError("Could not auto-detect a supported bank format from CSV headers")
            parser = self.registry.get_parser(detected_bank)

        return parser.parse_csv(file_path)

    def get_supported_banks(self) -> List[str]:
        return self.registry.list_banks()

    def get_enabled_banks(self) -> List[str]:
        return [
            status["bank_code"] for status in self.registry.get_bank_statuses() if status["enabled"]
        ]

    def get_bank_statuses(self) -> List[dict]:
        return self.registry.get_bank_statuses()

    def get_supported_formats(self) -> List[str]:
        return [".csv"]
