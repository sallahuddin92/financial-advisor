# Invoice Matching

## What It Does

- Matches parsed statement transactions against offline invoice JSON files
- Produces status counts (`matched`, `possible_match`, `unmatched`, `overpaid`, `underpaid`)
- Emits structured warning codes and human-readable messages

## What It Does Not Do

- Does not submit to LHDN
- Does not call MyInvois
- Does not verify SSM/JPN/BNM data
- Does not replace accountant/regulatory review

## Command

```bash
python3 -m malaysia_fsi.bank_statement.cli match \
  test-fixtures/sample-data/maybank-valid.csv \
  test-fixtures/sample-data/invoices-exact-match \
  --json
```
