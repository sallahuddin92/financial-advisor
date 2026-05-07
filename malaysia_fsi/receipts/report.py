"""Receipt reporting exporters for monthly SME summaries."""

import csv
import io
import json
from typing import Dict


def export_monthly_summary_json(summary: Dict) -> str:
    return json.dumps(summary, indent=2)


def export_monthly_summary_csv(summary: Dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["field", "value"])
    writer.writerow(["receipt_count", summary.get("receipt_count")])
    writer.writerow(["total_expenses", summary.get("total_expenses")])

    for category, amount in summary.get("expenses_by_category", {}).items():
        writer.writerow([f"category_{category}", amount])

    writer.writerow(["uncategorized_count", len(summary.get("uncategorized_receipts", []))])
    writer.writerow(["suspicious_count", len(summary.get("suspicious_receipts", []))])
    writer.writerow(["high_value_count", len(summary.get("high_value_transactions", []))])
    writer.writerow(["duplicate_candidate_groups", len(summary.get("duplicate_candidates", {}))])
    writer.writerow(["human_review_required", summary.get("human_review_required")])

    for idx, item in enumerate(summary.get("warnings", []), start=1):
        writer.writerow([f"warning_{idx}_code", item.get("code")])
        writer.writerow([f"warning_{idx}_message", item.get("message")])

    return output.getvalue()


def export_monthly_summary_markdown(summary: Dict) -> str:
    lines = [
        "# Monthly SME Expense Summary",
        "",
        f"- Receipt Count: {summary.get('receipt_count')}",
        f"- Total Expenses: {summary.get('total_expenses')}",
        "",
        "## Expenses By Category",
    ]

    for category, amount in summary.get("expenses_by_category", {}).items():
        lines.append(f"- {category}: {amount}")

    lines.extend(
        [
            "",
            "## Exceptions",
            f"- Uncategorized Receipts: {len(summary.get('uncategorized_receipts', []))}",
            f"- Suspicious Receipts: {len(summary.get('suspicious_receipts', []))}",
            f"- Missing Categories: {len(summary.get('missing_categories', []))}",
            f"- High Value Transactions: {len(summary.get('high_value_transactions', []))}",
            f"- Duplicate Candidate Groups: {len(summary.get('duplicate_candidates', {}))}",
            "",
            "## Warnings",
        ]
    )

    for item in summary.get("warnings", []):
        lines.append(f"- `{item.get('code')}`: {item.get('message')}")

    lines.extend(
        [
            "",
            "## Disclaimer",
            "**HUMAN REVIEW REQUIRED**: This monthly summary is advisory and must be reviewed by an accountant.",
        ]
    )
    return "\n".join(lines)
