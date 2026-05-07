# Receipt Categorization (WIP)

## Current Implementation

- Receipt JSON/manual ingestion schema is implemented in `malaysia_fsi.receipts.schema`.
- Rule-based categorization is implemented in `malaysia_fsi.receipts.categorizer`.
- Structured validation warnings are implemented.
- Money fields use Decimal-safe normalization.
- Duplicate candidate detection is implemented for same merchant/date/amount receipts.

## Category Set

- `FOOD_BUSINESS_RAW_MATERIAL`
- `PACKAGING`
- `UTILITIES`
- `RENT`
- `SALARY_WAGES`
- `DELIVERY_FEES`
- `TRANSPORT`
- `OFFICE_SUPPLIES`
- `EQUIPMENT`
- `BANK_CHARGES`
- `MARKETING`
- `CASH_WITHDRAWAL`
- `UNCATEGORIZED`

## Current Limitations

- No OCR yet.
- No PDF/image parsing yet.
- No automatic external verification.
- Human review required for every output.

## CLI

```bash
python3 -m malaysia_fsi.receipts.cli categorize test-fixtures/receipts --json
python3 -m malaysia_fsi.receipts.cli summarize test-fixtures/receipts --format md --output /tmp/monthly-receipts.md
python3 -m malaysia_fsi.receipts.cli validate --receipt test-fixtures/receipts/grocery-receipt.json --json
```
