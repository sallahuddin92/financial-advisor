# Demo Fixtures

These fixtures are fully fake/anonymized and are intended for the `malaysia_fsi.demo` one-command run.

Example:

```bash
python3 -m malaysia_fsi.demo run \
  --bank maybank-valid.csv \
  --invoices invoices-exact-match/ \
  --receipts receipts/ \
  --output demo-report/
```

You can run from repository root. The demo CLI auto-resolves these names to `test-fixtures/demo/`.

## Included
- `maybank-valid.csv`
- `invoices-exact-match/`
- `receipts/`
- `screenshots/` placeholder folder
