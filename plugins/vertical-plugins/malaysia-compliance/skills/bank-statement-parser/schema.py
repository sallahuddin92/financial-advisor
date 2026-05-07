"""
Standard transaction schema for Malaysian bank statements
"""

from dataclasses import dataclass
from datetime import date
from typing import List, Optional
from enum import Enum

class TransactionDirection(Enum):
    DEBIT = "debit"
    CREDIT = "credit"

@dataclass
class Transaction:
    """Standard transaction schema for normalized bank statement data"""
    date: date
    description: str
    debit: Optional[float] = None
    credit: Optional[float] = None
    amount: Optional[float] = None  # Signed amount (negative for debit, positive for credit)
    direction: Optional[TransactionDirection] = None
    balance: Optional[float] = None
    currency: str = "MYR"
    source_bank: str = "unknown"
    confidence: float = 1.0
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

        # Calculate signed amount and direction if not provided
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
            # Derive direction from signed amount
            if self.amount < 0:
                self.direction = TransactionDirection.DEBIT
                if self.debit is None:
                    self.debit = abs(self.amount)
            elif self.amount > 0:
                self.direction = TransactionDirection.CREDIT
                if self.credit is None:
                    self.credit = self.amount

@dataclass
class BankStatement:
    """Container for parsed bank statement data"""
    bank_name: str
    account_number: Optional[str] = None
    statement_period_start: Optional[date] = None
    statement_period_end: Optional[date] = None
    currency: str = "MYR"
    transactions: List[Transaction] = None
    warnings: List[str] = None
    confidence: float = 1.0

    def __post_init__(self):
        if self.transactions is None:
            self.transactions = []
        if self.warnings is None:
            self.warnings = []