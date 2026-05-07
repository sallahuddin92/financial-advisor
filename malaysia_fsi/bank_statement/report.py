"""Reporting helpers for offline bank statement parsing and reconciliation."""

from typing import Any, Dict

from .schema import BankStatement


def format_transaction_output(statement: BankStatement) -> Dict[str, Any]:
    """Format bank statement data for JSON output."""
    return {
        "bank_name": statement.bank_name,
        "account_number": statement.account_number,
        "statement_period": {
            "start": statement.statement_period_start.isoformat() if statement.statement_period_start else None,
            "end": statement.statement_period_end.isoformat() if statement.statement_period_end else None,
        },
        "currency": statement.currency,
        "confidence": statement.confidence,
        "warnings": statement.warnings,
        "transaction_count": len(statement.transactions),
        "transactions": [
            {
                "date": tx.date.isoformat(),
                "description": tx.description,
                "debit": tx.debit,
                "credit": tx.credit,
                "amount": tx.amount,
                "direction": tx.direction.value if tx.direction else None,
                "balance": tx.balance,
                "currency": tx.currency,
                "source_bank": tx.source_bank,
                "confidence": tx.confidence,
                "warnings": tx.warnings,
            }
            for tx in statement.transactions
        ],
    }
