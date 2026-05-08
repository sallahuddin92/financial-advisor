# Demo Troubleshooting

## Common Issues

### 1) Missing bank CSV

Message example:
- `Missing bank CSV: ...`

Fix:
- Ensure a `.csv` file is provided.
- Use demo fixture: `test-fixtures/demo/maybank-valid.csv`.

### 2) Unsupported bank format

Message example:
- `Unsupported bank format. Only Maybank CSV statement format is currently implemented.`

Fix:
- Use Maybank CSV layout with expected columns.
- Do not use CIMB/Public/RHB/Hong Leong formats yet.

### 3) Invalid invoice JSON

Message example:
- `Invalid invoice JSON: <file>.json`

Fix:
- Confirm JSON syntax is valid.
- Ensure invoice file extension is `.json`.

### 4) Invalid receipt JSON

Message example:
- `Invalid receipt JSON: <file>.json`

Fix:
- Confirm JSON syntax is valid.
- Ensure receipt file extension is `.json`.

### 5) Empty folder upload/input

Message example:
- `Empty invoice folder/upload. Provide at least one invoice JSON file.`
- `Empty receipt folder/upload. Provide at least one receipt JSON file.`

Fix:
- Add at least one `.json` file in each required input set.

### 6) Unsupported file type

Message examples:
- `Unsupported bank file type. Please upload a .csv file.`
- `Unsupported invoice file type ... Only .json is supported.`
- `Unsupported receipt file type ... Only .json is supported.`

Fix:
- Use only supported extensions (`.csv` for bank, `.json` for invoices/receipts).

## Output Folder Behavior

- Web demo writes timestamped outputs under `demo-output/`.
- Each run gets a unique folder to avoid overwriting previous runs.
- Reports can be downloaded from links shown in the UI after each run.

## Sample Demo Shortcut

Use **Run sample kedai makan demo** for a known-good end-to-end run with existing fixtures.

## Safety Reminder

This is an offline assistance tool. It does not make final accounting, tax, or compliance decisions.

**HUMAN REVIEW REQUIRED** for every generated output.
