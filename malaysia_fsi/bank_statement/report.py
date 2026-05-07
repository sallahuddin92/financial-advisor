"""Reporting helpers for offline bank statement parsing and reconciliation."""

import csv
import io
import json
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


def export_reconciliation_json(report: Dict[str, Any]) -> str:
    """Serialize reconciliation report as pretty JSON."""
    return json.dumps(report, indent=2)


def export_reconciliation_csv(report: Dict[str, Any]) -> str:
    """Export reconciliation report as spreadsheet-friendly key/value CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["field", "value"])
    writer.writerow(["statement_bank", report.get("statement_bank")])
    period = report.get("statement_period", {})
    writer.writerow(["statement_period_start", period.get("start")])
    writer.writerow(["statement_period_end", period.get("end")])
    writer.writerow(["total_transactions", report.get("total_transactions")])
    writer.writerow(["total_invoices", report.get("total_invoices")])
    writer.writerow(["matched_count", report.get("matched_count")])
    writer.writerow(["possible_match_count", report.get("possible_match_count")])
    writer.writerow(["unmatched_count", report.get("unmatched_count")])
    writer.writerow(["overpaid_count", report.get("overpaid_count")])
    writer.writerow(["underpaid_count", report.get("underpaid_count")])
    writer.writerow(["total_matched_amount", report.get("total_matched_amount")])
    writer.writerow(["total_unmatched_invoice_amount", report.get("total_unmatched_invoice_amount")])
    writer.writerow(["human_review_required", report.get("human_review_required")])
    warnings = report.get("warnings", [])
    writer.writerow(["warning_count", len(warnings)])
    for idx, item in enumerate(warnings, start=1):
        writer.writerow([f"warning_{idx}_code", item.get("code")])
        writer.writerow([f"warning_{idx}_message", item.get("message")])
    return output.getvalue()


def export_reconciliation_markdown(report: Dict[str, Any]) -> str:
    """Export reconciliation report as a markdown review document."""
    period = report.get("statement_period", {})
    lines = [
        "# Reconciliation Report",
        "",
        f"- Statement Bank: {report.get('statement_bank')}",
        f"- Statement Period: {period.get('start')} to {period.get('end')}",
        f"- Transaction Count: {report.get('total_transactions')}",
        f"- Invoice Count: {report.get('total_invoices')}",
        "",
        "## Status Counts",
        f"- Matched: {report.get('matched_count')}",
        f"- Possible Match: {report.get('possible_match_count')}",
        f"- Unmatched: {report.get('unmatched_count')}",
        f"- Overpaid: {report.get('overpaid_count')}",
        f"- Underpaid: {report.get('underpaid_count')}",
        "",
        "## Totals",
        f"- Total Matched Amount: {report.get('total_matched_amount')}",
        f"- Total Unmatched Invoice Amount: {report.get('total_unmatched_invoice_amount')}",
        "",
        "## Warnings",
    ]
    warnings = report.get("warnings", [])
    if warnings:
        for item in warnings:
            lines.append(f"- `{item.get('code')}`: {item.get('message')}")
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Disclaimer",
            "**HUMAN REVIEW REQUIRED**: This report is offline reconciliation assistance only and must be manually verified.",
        ]
    )
    return "\n".join(lines)
