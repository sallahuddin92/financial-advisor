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
python3 -m malaysia_fsi.web_demo.app
```

If `gradio` is installed, the app runs with Gradio.
Otherwise it falls back to FastAPI + simple HTML form (default local URL: `http://127.0.0.1:7860`).

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

The web demo runs reconciliation + receipt summary and generates downloadable reports:
- reconciliation (`.md` / `.json` / `.csv` by selected format)
- monthly expense summary (`.md` / `.json` / `.csv` by selected format)
- `categorized-expenses.csv`
- `warnings-summary.md`
- `index.md`

## Safety

- Local demo only
- No login/auth
- No database
- No external APIs
- **HUMAN REVIEW REQUIRED** for every output
