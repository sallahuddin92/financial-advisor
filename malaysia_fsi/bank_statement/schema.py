"""Standard transaction schema for Malaysian bank statements."""

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Dict, List, Optional


class TransactionDirection(Enum):
    DEBIT = "debit"
    CREDIT = "credit"


def warning(code: str, message: str) -> Dict[str, str]:
    """Create structured warning payload."""
    return {"code": code, "message": message}


@dataclass
class Transaction:
    """Standard transaction schema for normalized bank statement data."""

    date: date
    description: str
    debit: Optional[float] = None
    credit: Optional[float] = None
    amount: Optional[float] = None
    direction: Optional[TransactionDirection] = None
    balance: Optional[float] = None
    currency: str = "MYR"
    source_bank: str = "unknown"
    confidence: float = 1.0
    warnings: List[Dict[str, str]] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

        if self.amount is None:
            if self.debit and self.debit > 0:
                self.amount = -self.debit
                self.direction = TransactionDirection.DEBIT
            elif self.credit and self.credit > 0:
                self.amount = self.credit
                self.direction = TransactionDirection.CREDIT
            else:
                self.amount = 0.0
                self.direction = None
        else:
            if self.amount < 0:
                self.direction = TransactionDirection.DEBIT
                if self.debit is None:
                    self.debit = abs(self.amount)
            elif self.amount > 0:
                self.direction = TransactionDirection.CREDIT
                if self.credit is None:
                    self.credit = self.amount

        self.warnings.extend(validate_transaction(self))


@dataclass
class BankStatement:
    """Container for parsed bank statement data."""

    bank_name: str
    account_number: Optional[str] = None
    statement_period_start: Optional[date] = None
    statement_period_end: Optional[date] = None
    currency: str = "MYR"
    transactions: List[Transaction] = None
    warnings: List[Dict[str, str]] = None
    confidence: float = 1.0

    def __post_init__(self):
        if self.transactions is None:
            self.transactions = []
        if self.warnings is None:
            self.warnings = []


def validate_transaction(transaction: Transaction) -> List[Dict[str, str]]:
    """Validate transaction consistency and return warning payloads."""
    warnings: List[Dict[str, str]] = []

    if not transaction.description:
        warnings.append(warning("MISSING_DESCRIPTION", "Transaction description is empty."))

    if transaction.debit and transaction.credit:
        warnings.append(
            warning(
                "BOTH_DEBIT_CREDIT_PRESENT",
                "Both debit and credit are present; row should be manually reviewed.",
            )
        )

    if transaction.amount is None:
        warnings.append(warning("INVALID_AMOUNT", "Transaction amount could not be derived."))

    if transaction.amount == 0:
        warnings.append(
            warning("INVALID_AMOUNT", "Transaction amount is zero; verify source statement row.")
        )

    return warnings
