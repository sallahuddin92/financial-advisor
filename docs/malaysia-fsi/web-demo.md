# Local Web Demo

## Purpose

`malaysia_fsi.web_demo` provides a local browser UI for non-developers to run the current offline workflow:
- Maybank CSV parsing
- invoice matching
- receipt categorization
- monthly expense summaries

This is local-only tooling. It does not add external APIs, authentication, SaaS hosting, or database state.

## Start

```bash
make web-demo
```

Equivalent command:

```bash
python3 -m malaysia_fsi.web_demo.app
```

If `gradio` is installed, the app runs with Gradio.
Otherwise it falls back to FastAPI + simple HTML form (default local URL: `http://127.0.0.1:7860`).

## UX Improvements Included

- clearer landing page with required files and limitations
- dedicated sample button: **Run sample kedai makan demo**
- separate warnings section for easier review
- explicit report download links
- in-browser report previews for Markdown outputs
- timestamped output folders under `demo-output/`

## Inputs

The UI supports both:
- upload inputs
- path-based selection for local demo fixtures

Supported inputs:
- Maybank CSV
- invoice JSON files/folder
- receipt JSON files/folder
- output format: `Markdown`, `JSON`, or `CSV`

## Outputs

The web demo runs reconciliation + receipt summary and generates downloadable reports.

Standard outputs:
- reconciliation report (`.md` / `.json` / `.csv` based on selected format)
- monthly expense summary (`.md` / `.json` / `.csv` based on selected format)
- `categorized-expenses.csv`
- `warnings-summary.md`
- `index.md`

Sample button output is aligned with the CLI demo flow and includes:
- `reconciliation.md`
- `reconciliation.json`
- `monthly-expense-summary.md`
- `categorized-expenses.csv`
- `warnings-summary.md`
- `index.md`

## Error Messages

The web demo now provides explicit errors for:
- missing bank CSV
- unsupported bank format
- invalid invoice JSON
- invalid receipt JSON
- empty folder uploads
- unsupported file type

## Safety

- Local demo only
- No login/auth
- No database
- No external APIs
- **HUMAN REVIEW REQUIRED** for every output

See troubleshooting notes at `docs/malaysia-fsi/demo-troubleshooting.md`.
