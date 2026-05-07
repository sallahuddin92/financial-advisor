# Monthly SME Reporting

## Current Implementation

- Monthly summary builder: `malaysia_fsi.receipts.monthly_expense_summary`
- Exporters:
  - JSON
  - CSV
  - Markdown

## Summary Fields

- total expenses
- expenses by category
- uncategorized receipts
- suspicious receipts
- missing categories
- high-value transactions
- duplicate candidates

## Safety

- Reporting is advisory only.
- No regulatory/tax filing submission.
- **HUMAN REVIEW REQUIRED** before accountant use.
- Reconciliation integration adds unmatched transaction category hints for analyst review only.
