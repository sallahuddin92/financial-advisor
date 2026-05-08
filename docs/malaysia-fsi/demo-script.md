# Demo Script

## 1. What Problem This Solves

Malaysia SMEs often track statements, invoices, and receipts separately. This demo shows a local offline assistant that helps teams:
- parse Maybank CSV statements,
- match transactions to invoice JSON,
- categorize receipt JSON expenses,
- generate review-ready summaries with warnings.

## 2. Who It Is For

Primary users:
- SME owner/operator
- bookkeeper
- accountant supporting SMEs

Typical SME profiles:
- roadside restaurant
- food stall
- workshop
- mini market
- homestay owner
- small contractor

## 3. What Files To Prepare

Required demo inputs:
- Maybank CSV statement file
- invoice JSON files (single file or folder)
- receipt JSON files (single file or folder)

Quick local fixtures:
- `test-fixtures/demo/maybank-valid.csv`
- `test-fixtures/demo/invoices-exact-match/`
- `test-fixtures/demo/receipts/`

## 4. How To Run `make web-demo`

From repo root:

```bash
make web-demo
```

Then open the local URL shown in terminal (default local demo port: `7860`).

In the UI:
1. Upload files, or use demo fixture paths.
2. Select output format (`Markdown`, `JSON`, or `CSV`).
3. Click run.
4. Download generated reports.

## 5. Walkthrough Of Outputs

Expected downloadable outputs:
- reconciliation report (`md`/`json`/`csv` based on selected format)
- monthly expense summary (`md`/`json`/`csv` based on selected format)
- `categorized-expenses.csv`
- `warnings-summary.md`
- `index.md` (links to generated reports)

Walkthrough points:
1. Reconciliation counts: matched, possible, unmatched, overpaid, underpaid.
2. Monthly expense totals and category breakdown.
3. Warning codes and messages that require manual follow-up.
4. Suggested categories are advisory only.

## 6. What The System Cannot Do Yet

- No MyInvois submission
- No SSM/JPN/BNM verification
- No live bank API integrations
- No OCR/PDF/image receipt parsing
- No automated accounting/tax/regulatory decisions

## 7. Human Review Required Disclaimer

All demo outputs are assistance-only and require human review before any accounting, tax, compliance, legal, or operational decision.

**HUMAN REVIEW REQUIRED** for every workflow output.
