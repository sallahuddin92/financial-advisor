"""Reporting helpers for offline bank statement parsing and reconciliation."""

from typing import Any, Dict

from .schema import BankStatement


def validate_reconciliation_report(report: Dict[str, Any]) -> list:
    """Validate required report fields for safe downstream use."""
    required_keys = [
        "statement_bank",
        "statement_period",
        "total_transactions",
        "total_invoices",
        "matched_count",
        "possible_match_count",
        "unmatched_count",
        "overpaid_count",
        "underpaid_count",
        "total_matched_amount",
        "total_unmatched_invoice_amount",
        "warnings",
        "human_review_required",
    ]
    missing = [key for key in required_keys if key not in report]
    return missing


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
