# CLI Usage

Main entrypoint:

```bash
python3 -m malaysia_fsi.bank_statement.cli
```

## Parse

```bash
python3 -m malaysia_fsi.bank_statement.cli parse <csv> --json
```

## Match

```bash
python3 -m malaysia_fsi.bank_statement.cli match <csv> <invoice-json-or-dir> --format md --output /tmp/reconciliation-report.md
```

## Validate

```bash
python3 -m malaysia_fsi.bank_statement.cli validate --input <csv> --invoice <invoice-json> --json
```

All commands are offline only and preserve `human_review_required: true` behavior.

## Receipt Categorize

```bash
python3 -m malaysia_fsi.receipts.cli categorize test-fixtures/receipts --json
```

## Receipt Summarize

```bash
python3 -m malaysia_fsi.receipts.cli summarize test-fixtures/receipts --format md --output /tmp/monthly-receipts.md
```

## Receipt Validate

```bash
python3 -m malaysia_fsi.receipts.cli validate --receipt test-fixtures/receipts/grocery-receipt.json --json
```
