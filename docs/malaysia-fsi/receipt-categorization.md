# Receipt Categorization (WIP)

## Current Implementation

- Receipt JSON/manual ingestion schema is implemented in `malaysia_fsi.receipts.schema`.
- Structured validation warnings are implemented.
- Money fields use Decimal-safe normalization.

## Current Limitations

- No OCR yet.
- No PDF/image parsing yet.
- No automatic external verification.
- Human review required for every output.
