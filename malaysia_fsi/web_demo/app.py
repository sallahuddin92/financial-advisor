"""Local web demo app for offline SME reconciliation and receipt summaries."""

import csv
import html
import importlib.util
import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from malaysia_fsi.bank_statement.invoice_matcher import InvoiceMatcher
from malaysia_fsi.bank_statement.parser import BankStatementParser
from malaysia_fsi.bank_statement.report import (
    export_reconciliation_csv,
    export_reconciliation_json,
    export_reconciliation_markdown,
)
from malaysia_fsi.demo.cli import run_demo as run_cli_demo
from malaysia_fsi.receipts.categorizer import batch_categorize_receipts, load_receipts_from_paths
from malaysia_fsi.receipts.monthly_expense_summary import build_monthly_expense_summary
from malaysia_fsi.receipts.report import (
    export_monthly_summary_csv,
    export_monthly_summary_json,
    export_monthly_summary_markdown,
)

OUTPUT_FORMATS = {"Markdown", "JSON", "CSV"}
REPO_ROOT = Path.cwd()
DEMO_OUTPUT_ROOT = REPO_ROOT / "demo-output"
DEMO_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)


def generate_timestamped_output_dir(base_dir: Path = DEMO_OUTPUT_ROOT, prefix: str = "web-demo") -> Path:
    """Create a timestamped output directory and return it."""

    run_id = datetime.utcnow().strftime("%Y%m%d%H%M%S") + "-" + uuid.uuid4().hex[:8]
    output_dir = base_dir / f"{prefix}-{run_id}"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _resolve_input(path: Path, search_roots: Sequence[Path]) -> Path:
    if path.exists():
        return path
    for root in search_roots:
        candidate = root / path
        if candidate.exists():
            return candidate
    return path


def _resolve_json_paths(path: Path) -> List[Path]:
    if path.is_dir():
        return sorted(path.glob("*.json"))
    return [path]


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_categorized_csv(path: Path, categorized_items: Iterable) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "receipt_id",
                "merchant_name",
                "receipt_date",
                "total_amount",
                "inferred_category",
                "confidence_score",
                "human_review_required",
                "warning_codes",
            ]
        )
        for item in categorized_items:
            warning_codes = sorted({entry.get("code", "") for entry in item.warnings})
            writer.writerow(
                [
                    item.receipt.receipt_id,
                    item.receipt.merchant_name,
                    item.receipt.receipt_date.isoformat(),
                    f"{item.receipt.total_amount:.2f}",
                    item.inferred_category,
                    f"{item.confidence_score:.3f}",
                    "true",
                    "|".join(code for code in warning_codes if code),
                ]
            )


def _render_warnings_markdown(reconciliation: dict, monthly_summary: dict, categorized_items: Iterable) -> str:
    collected = []

    for item in reconciliation.get("warnings", []):
        collected.append(("reconciliation", item.get("code", "UNKNOWN"), item.get("message", "")))

    for item in monthly_summary.get("warnings", []):
        collected.append(("monthly_summary", item.get("code", "UNKNOWN"), item.get("message", "")))

    for categorized in categorized_items:
        for item in categorized.warnings:
            collected.append(
                (
                    f"receipt:{categorized.receipt.receipt_id or 'unknown'}",
                    item.get("code", "UNKNOWN"),
                    item.get("message", ""),
                )
            )

    unique: List[Tuple[str, str, str]] = []
    seen = set()
    for source, code, message in collected:
        marker = (source, code, message)
        if marker not in seen:
            seen.add(marker)
            unique.append(marker)

    lines = [
        "# Warnings Summary",
        "",
        f"- Total warning entries: {len(unique)}",
        "- Human review required: true",
        "",
        "## Aggregated Warnings",
    ]

    if unique:
        for source, code, message in unique:
            lines.append(f"- [{source}] `{code}`: {message}")
    else:
        lines.append("- No warnings found")

    lines.extend(
        [
            "",
            "## Disclaimer",
            "**HUMAN REVIEW REQUIRED**: Outputs are advisory only and must be reviewed before financial/accounting decisions.",
        ]
    )
    return "\n".join(lines)


def _render_index_markdown(files: Dict[str, str], run_dir_name: str) -> str:
    lines = [
        "# Malaysia FSI Web Demo Output Index",
        "",
        "Generated reports:",
    ]

    for label, filename in files.items():
        lines.append(f"- [{label}](/download/{run_dir_name}/{filename})")

    lines.extend(
        [
            "",
            "## Notes",
            "- Local demo only (no external APIs, no SaaS, no database).",
            "- **HUMAN REVIEW REQUIRED** for every output.",
        ]
    )
    return "\n".join(lines)


def _reconciliation_text(reconciliation: dict) -> str:
    period = reconciliation.get("statement_period", {})
    lines = [
        "Reconciliation Summary",
        f"Bank: {reconciliation.get('statement_bank')}",
        f"Period: {period.get('start')} to {period.get('end')}",
        f"Transactions: {reconciliation.get('total_transactions')}",
        f"Invoices: {reconciliation.get('total_invoices')}",
        f"Matched: {reconciliation.get('matched_count')}",
        f"Possible: {reconciliation.get('possible_match_count')}",
        f"Unmatched: {reconciliation.get('unmatched_count')}",
        f"Overpaid: {reconciliation.get('overpaid_count')}",
        f"Underpaid: {reconciliation.get('underpaid_count')}",
        "HUMAN REVIEW REQUIRED",
    ]
    return "\n".join(lines)


def _monthly_text(monthly: dict) -> str:
    lines = [
        "Monthly Expense Summary",
        f"Receipt count: {monthly.get('receipt_count')}",
        f"Total expenses: {monthly.get('total_expenses')}",
        f"Uncategorized: {len(monthly.get('uncategorized_receipts', []))}",
        f"Suspicious: {len(monthly.get('suspicious_receipts', []))}",
        f"High value: {len(monthly.get('high_value_transactions', []))}",
        "HUMAN REVIEW REQUIRED",
    ]
    return "\n".join(lines)


def _inline_markdown(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def markdown_to_html(markdown_text: str) -> str:
    """Small markdown renderer for local preview without extra dependencies."""

    lines = markdown_text.splitlines()
    html_lines: List[str] = []
    in_list = False

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("# "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h1>{_inline_markdown(line[2:])}</h1>")
            continue
        if line.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h2>{_inline_markdown(line[3:])}</h2>")
            continue
        if line.startswith("### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h3>{_inline_markdown(line[4:])}</h3>")
            continue
        if line.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{_inline_markdown(line[2:])}</li>")
            continue

        if in_list:
            html_lines.append("</ul>")
            in_list = False

        if line == "":
            html_lines.append("<br/>")
        else:
            html_lines.append(f"<p>{_inline_markdown(line)}</p>")

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


def _read_json(path: Path, label: str) -> Dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Invalid {label} JSON: {path.name}. {exc}") from exc


def _validate_input_files(
    bank_csv: Path,
    invoice_json_paths: Sequence[Path],
    receipt_json_paths: Sequence[Path],
) -> None:
    if not bank_csv.exists():
        raise FileNotFoundError(f"Missing bank CSV: {bank_csv}")
    if bank_csv.suffix.lower() != ".csv":
        raise ValueError("Unsupported file type for bank statement. Please upload/select a .csv file.")

    if not invoice_json_paths:
        raise ValueError("Empty invoice folder/upload. Provide at least one invoice JSON file.")
    for path in invoice_json_paths:
        if path.suffix.lower() != ".json":
            raise ValueError(f"Unsupported invoice file type: {path.name}. Only .json is supported.")
        if not path.exists():
            raise FileNotFoundError(f"Invoice file not found: {path}")
        _read_json(path, "invoice")

    if not receipt_json_paths:
        raise ValueError("Empty receipt folder/upload. Provide at least one receipt JSON file.")
    for path in receipt_json_paths:
        if path.suffix.lower() != ".json":
            raise ValueError(f"Unsupported receipt file type: {path.name}. Only .json is supported.")
        if not path.exists():
            raise FileNotFoundError(f"Receipt file not found: {path}")
        _read_json(path, "receipt")


def _build_output_files(output_format: str) -> Tuple[str, str]:
    if output_format == "Markdown":
        return "reconciliation.md", "monthly-expense-summary.md"
    if output_format == "JSON":
        return "reconciliation.json", "monthly-expense-summary.json"
    return "reconciliation.csv", "monthly-expense-summary.csv"


def run_demo_workflow(
    bank_csv: Path,
    invoice_json_paths: Sequence[Path],
    receipt_json_paths: Sequence[Path],
    output_dir: Path,
    output_format: str = "Markdown",
) -> Dict[str, object]:
    """Run reconciliation + receipt summary and persist report artifacts."""

    if output_format not in OUTPUT_FORMATS:
        raise ValueError(f"Unsupported output format: {output_format}")

    _validate_input_files(bank_csv, invoice_json_paths, receipt_json_paths)

    output_dir.mkdir(parents=True, exist_ok=True)

    statement = BankStatementParser().parse_file(bank_csv, bank_hint="maybank")
    warning_codes = {item.get("code") for item in statement.warnings}
    if "MISSING_COLUMN" in warning_codes or "NO_TRANSACTIONS" in warning_codes:
        raise ValueError("Unsupported bank format. Only Maybank CSV statement format is currently implemented.")

    matcher = InvoiceMatcher()
    invoice_paths = [path for path in invoice_json_paths if path.exists()]
    results = matcher.match_statement_to_invoices(statement, invoice_paths)
    loaded_invoices = [invoice for invoice in (matcher.load_invoice(path) for path in invoice_paths) if invoice]
    reconciliation = matcher.build_reconciliation_report(statement, results, loaded_invoices)

    receipt_paths = [path for path in receipt_json_paths if path.exists()]
    receipts = load_receipts_from_paths(receipt_paths)
    categorized_batch = batch_categorize_receipts(receipts)
    categorized_receipts = categorized_batch["receipts"]
    monthly_summary = build_monthly_expense_summary(categorized_receipts)

    reconciliation_filename, monthly_filename = _build_output_files(output_format)

    if output_format == "Markdown":
        _write_text(output_dir / reconciliation_filename, export_reconciliation_markdown(reconciliation))
        _write_text(output_dir / monthly_filename, export_monthly_summary_markdown(monthly_summary))
    elif output_format == "JSON":
        _write_text(output_dir / reconciliation_filename, export_reconciliation_json(reconciliation))
        _write_text(output_dir / monthly_filename, export_monthly_summary_json(monthly_summary))
    else:
        _write_text(output_dir / reconciliation_filename, export_reconciliation_csv(reconciliation))
        _write_text(output_dir / monthly_filename, export_monthly_summary_csv(monthly_summary))

    # Always generate markdown previews for browser rendering.
    reconciliation_md = export_reconciliation_markdown(reconciliation)
    monthly_md = export_monthly_summary_markdown(monthly_summary)
    warnings_md = _render_warnings_markdown(reconciliation, monthly_summary, categorized_receipts)

    if reconciliation_filename != "reconciliation.md":
        _write_text(output_dir / "reconciliation.md", reconciliation_md)
    if monthly_filename != "monthly-expense-summary.md":
        _write_text(output_dir / "monthly-expense-summary.md", monthly_md)

    _write_text(output_dir / "reconciliation.json", export_reconciliation_json(reconciliation))
    _write_text(output_dir / "monthly-expense-summary.json", export_monthly_summary_json(monthly_summary))

    _write_categorized_csv(output_dir / "categorized-expenses.csv", categorized_receipts)
    _write_text(output_dir / "warnings-summary.md", warnings_md)

    files = {
        "Reconciliation": reconciliation_filename,
        "Monthly Expense Summary": monthly_filename,
        "Categorized Expenses": "categorized-expenses.csv",
        "Warnings Summary": "warnings-summary.md",
    }

    index_md = _render_index_markdown(files, run_dir_name=output_dir.name)
    _write_text(output_dir / "index.md", index_md)
    files["Index"] = "index.md"

    warnings = reconciliation.get("warnings", []) + monthly_summary.get("warnings", [])

    return {
        "reconciliation": reconciliation,
        "monthly_summary": monthly_summary,
        "warnings": warnings,
        "reconciliation_text": _reconciliation_text(reconciliation),
        "monthly_text": _monthly_text(monthly_summary),
        "warnings_text": warnings_md,
        "reconciliation_preview_html": markdown_to_html(reconciliation_md),
        "monthly_preview_html": markdown_to_html(monthly_md),
        "warnings_preview_html": markdown_to_html(warnings_md),
        "files": files,
        "output_dir": str(output_dir),
        "human_review_required": True,
    }


def run_sample_kedai_makan_demo(output_format: str = "Markdown") -> Dict[str, object]:
    """Run sample demo using test-fixtures/demo and generate same outputs as make demo."""

    output_dir = generate_timestamped_output_dir(prefix="sample-kedai-makan")
    bank = REPO_ROOT / "test-fixtures" / "demo" / "maybank-valid.csv"
    invoices = REPO_ROOT / "test-fixtures" / "demo" / "invoices-exact-match"
    receipts = REPO_ROOT / "test-fixtures" / "demo" / "receipts"

    exit_code = run_cli_demo(bank_path=bank, invoices_path=invoices, receipts_path=receipts, output_dir=output_dir)
    if exit_code != 0:
        raise RuntimeError("Sample demo run failed")

    reconciliation_json_path = output_dir / "reconciliation.json"
    monthly_md_path = output_dir / "monthly-expense-summary.md"
    reconciliation_md_path = output_dir / "reconciliation.md"
    warnings_md_path = output_dir / "warnings-summary.md"

    if not reconciliation_json_path.exists():
        raise RuntimeError("Sample demo did not generate reconciliation.json")

    reconciliation = _read_json(reconciliation_json_path, "reconciliation")
    monthly_preview = monthly_md_path.read_text(encoding="utf-8") if monthly_md_path.exists() else ""
    reconciliation_preview = (
        reconciliation_md_path.read_text(encoding="utf-8") if reconciliation_md_path.exists() else ""
    )
    warnings_preview = warnings_md_path.read_text(encoding="utf-8") if warnings_md_path.exists() else ""

    files = {
        "Reconciliation (Markdown)": "reconciliation.md",
        "Reconciliation (JSON)": "reconciliation.json",
        "Monthly Expense Summary (Markdown)": "monthly-expense-summary.md",
        "Categorized Expenses": "categorized-expenses.csv",
        "Warnings Summary": "warnings-summary.md",
        "Index": "index.md",
    }

    return {
        "reconciliation": reconciliation,
        "reconciliation_text": _reconciliation_text(reconciliation),
        "monthly_text": "Sample monthly summary generated",
        "warnings_text": warnings_preview,
        "reconciliation_preview_html": markdown_to_html(reconciliation_preview),
        "monthly_preview_html": markdown_to_html(monthly_preview),
        "warnings_preview_html": markdown_to_html(warnings_preview),
        "files": files,
        "output_dir": str(output_dir),
        "human_review_required": True,
    }


def _resolve_demo_paths(
    bank_path_input: str,
    invoices_path_input: str,
    receipts_path_input: str,
) -> Tuple[Path, List[Path], List[Path]]:
    bank = _resolve_input(
        Path(bank_path_input),
        [REPO_ROOT / "test-fixtures" / "demo", REPO_ROOT / "test-fixtures" / "sample-data"],
    )

    invoices_path = _resolve_input(
        Path(invoices_path_input),
        [REPO_ROOT / "test-fixtures" / "demo", REPO_ROOT / "test-fixtures" / "sample-data"],
    )

    receipts_path = _resolve_input(
        Path(receipts_path_input),
        [REPO_ROOT / "test-fixtures" / "demo", REPO_ROOT / "test-fixtures"],
    )

    invoice_jsons = _resolve_json_paths(invoices_path)
    receipt_jsons = _resolve_json_paths(receipts_path)

    return bank, invoice_jsons, receipt_jsons


def _build_download_links(files: Dict[str, str], run_dir_name: str) -> str:
    links = []
    for label, filename in files.items():
        href = f"/download/{run_dir_name}/{filename}"
        links.append(f"<li><a href=\"{href}\"><strong>{html.escape(label)}</strong>: {html.escape(filename)}</a></li>")
    return "\n".join(links)


def _build_result_html(result: Dict[str, object]) -> str:
    output_dir = Path(str(result["output_dir"]))
    links_html = _build_download_links(result["files"], output_dir.name)

    return f"""
    <section style=\"border: 1px solid #ddd; padding: 1rem; margin-top: 1rem;\">
      <h2>Run Complete</h2>
      <p><strong>HUMAN REVIEW REQUIRED</strong> for all outputs.</p>
      <p>Output folder: <code>{html.escape(str(output_dir))}</code></p>

      <h3>Reconciliation Summary</h3>
      <pre>{html.escape(str(result['reconciliation_text']))}</pre>

      <h3>Monthly Expense Summary</h3>
      <pre>{html.escape(str(result['monthly_text']))}</pre>

      <h3>Warnings (Separate Review Section)</h3>
      <pre>{html.escape(str(result['warnings_text']))}</pre>

      <h3>Report Previews</h3>
      <h4>Reconciliation Report Preview</h4>
      <div>{result['reconciliation_preview_html']}</div>
      <h4>Monthly Expense Summary Preview</h4>
      <div>{result['monthly_preview_html']}</div>
      <h4>Warnings Summary Preview</h4>
      <div>{result['warnings_preview_html']}</div>

      <h3>Download Reports</h3>
      <ul>
        {links_html}
      </ul>
    </section>
    """


def _render_fastapi_page(message_html: str = "") -> str:
    return f"""
    <html>
      <head>
        <title>Malaysia FSI Local Web Demo</title>
      </head>
      <body style=\"font-family: sans-serif; margin: 2rem; max-width: 980px;\">
        <h1>Malaysia FSI Local Web Demo</h1>
        <p>
          Offline-only SME assistant demo for Maybank CSV + invoice JSON + receipt JSON workflows.
          <strong>HUMAN REVIEW REQUIRED</strong> for every output.
        </p>

        <section style=\"background: #fff7d6; padding: 1rem; border: 1px solid #d8c36b;\">
          <h3>Required Files</h3>
          <ul>
            <li>Bank statement: <code>.csv</code> (Maybank format only)</li>
            <li>Invoices: one or more <code>.json</code> files</li>
            <li>Receipts: one or more <code>.json</code> files</li>
          </ul>
        </section>

        <section style=\"margin-top: 1rem;\">
          <form action=\"/run-sample\" method=\"post\">
            <label>Sample output format:</label>
            <select name=\"output_format\">
              <option>Markdown</option>
              <option>JSON</option>
              <option>CSV</option>
            </select>
            <button type=\"submit\">Run sample kedai makan demo</button>
          </form>
        </section>

        <section style=\"margin-top: 1rem; border-top: 1px solid #ddd; padding-top: 1rem;\">
          <h3>Run With Your Files</h3>
          <form action=\"/run\" method=\"post\" enctype=\"multipart/form-data\">
            <h4>Use Existing Paths</h4>
            <label>Maybank CSV path/name:</label><br/>
            <input name=\"bank_path\" value=\"maybank-valid.csv\" style=\"width: 40rem;\"/><br/><br/>

            <label>Invoice JSON folder/path:</label><br/>
            <input name=\"invoices_path\" value=\"invoices-exact-match/\" style=\"width: 40rem;\"/><br/><br/>

            <label>Receipt JSON folder/path:</label><br/>
            <input name=\"receipts_path\" value=\"receipts/\" style=\"width: 40rem;\"/><br/><br/>

            <h4>Or Upload Files</h4>
            <label>Maybank CSV upload:</label><br/>
            <input type=\"file\" name=\"bank_file\" accept=\".csv\"/><br/><br/>

            <label>Invoice JSON upload (multi-select):</label><br/>
            <input type=\"file\" name=\"invoice_files\" accept=\".json\" multiple/><br/><br/>

            <label>Receipt JSON upload (multi-select):</label><br/>
            <input type=\"file\" name=\"receipt_files\" accept=\".json\" multiple/><br/><br/>

            <label>Output format:</label>
            <select name=\"output_format\">
              <option>Markdown</option>
              <option>JSON</option>
              <option>CSV</option>
            </select><br/><br/>

            <button type=\"submit\">Run reconciliation + receipt summary</button>
          </form>
        </section>

        <section style=\"margin-top: 1rem; background: #ffe6e6; padding: 1rem; border: 1px solid #d77;\">
          <h3>Current Limitations (Unsupported)</h3>
          <ul>
            <li>Only Maybank CSV is implemented.</li>
            <li>No OCR and no PDF/image receipt parsing.</li>
            <li>No MyInvois, SSM, JPN, BNM, CTOS, Bursa, or external APIs.</li>
            <li>No login/auth, no database, no SaaS deployment flow.</li>
          </ul>
        </section>

        {message_html}
      </body>
    </html>
    """


def create_fastapi_app():
    """Create FastAPI app lazily to avoid hard dependency during import-only tests."""

    from fastapi import FastAPI, File, Form, Request, UploadFile
    from fastapi.responses import FileResponse, HTMLResponse

    app = FastAPI(title="Malaysia FSI Local Web Demo")

    @app.get("/", response_class=HTMLResponse)
    async def home() -> str:
        return _render_fastapi_page()

    @app.post("/run-sample", response_class=HTMLResponse)
    async def run_sample(output_format: str = Form("Markdown")) -> str:
        try:
            result = run_sample_kedai_makan_demo(output_format=output_format)
            return _render_fastapi_page(_build_result_html(result))
        except Exception as exc:
            message = f"<p style=\"color: red;\">Sample run failed: {html.escape(str(exc))}</p>"
            return _render_fastapi_page(message)

    @app.post("/run", response_class=HTMLResponse)
    async def run(
        request: Request,
        bank_path: str = Form("maybank-valid.csv"),
        invoices_path: str = Form("invoices-exact-match/"),
        receipts_path: str = Form("receipts/"),
        output_format: str = Form("Markdown"),
        bank_file: Optional[UploadFile] = File(None),
        invoice_files: Optional[List[UploadFile]] = File(None),
        receipt_files: Optional[List[UploadFile]] = File(None),
    ) -> str:
        del request
        run_dir = generate_timestamped_output_dir(prefix="custom-run")
        upload_dir = run_dir / "uploads"

        try:
            upload_dir.mkdir(parents=True, exist_ok=True)

            if bank_file and bank_file.filename:
                if not bank_file.filename.lower().endswith(".csv"):
                    raise ValueError("Unsupported bank file type. Please upload a .csv file.")
                bank_csv = upload_dir / bank_file.filename
                bank_csv.write_bytes(await bank_file.read())
            else:
                bank_csv, _, _ = _resolve_demo_paths(bank_path, invoices_path, receipts_path)

            if invoice_files:
                invoice_dir = upload_dir / "invoices"
                invoice_dir.mkdir(parents=True, exist_ok=True)
                invoice_jsons: List[Path] = []
                for file in invoice_files:
                    if not file or not file.filename:
                        continue
                    if not file.filename.lower().endswith(".json"):
                        raise ValueError(
                            f"Unsupported invoice file type: {file.filename}. Only .json is supported."
                        )
                    file_path = invoice_dir / file.filename
                    file_path.write_bytes(await file.read())
                    invoice_jsons.append(file_path)
            else:
                _, invoice_jsons, _ = _resolve_demo_paths(bank_path, invoices_path, receipts_path)

            if receipt_files:
                receipt_dir = upload_dir / "receipts"
                receipt_dir.mkdir(parents=True, exist_ok=True)
                receipt_jsons: List[Path] = []
                for file in receipt_files:
                    if not file or not file.filename:
                        continue
                    if not file.filename.lower().endswith(".json"):
                        raise ValueError(
                            f"Unsupported receipt file type: {file.filename}. Only .json is supported."
                        )
                    file_path = receipt_dir / file.filename
                    file_path.write_bytes(await file.read())
                    receipt_jsons.append(file_path)
            else:
                _, _, receipt_jsons = _resolve_demo_paths(bank_path, invoices_path, receipts_path)

            result = run_demo_workflow(
                bank_csv=bank_csv,
                invoice_json_paths=invoice_jsons,
                receipt_json_paths=receipt_jsons,
                output_dir=run_dir,
                output_format=output_format,
            )
            return _render_fastapi_page(_build_result_html(result))
        except Exception as exc:
            message = f"<p style=\"color: red;\">Run failed: {html.escape(str(exc))}</p>"
            return _render_fastapi_page(message)

    @app.get("/download/{run_dir_name}/{filename}")
    async def download(run_dir_name: str, filename: str):
        file_path = DEMO_OUTPUT_ROOT / run_dir_name / filename
        if not file_path.exists() or not file_path.is_file():
            return HTMLResponse("File not found", status_code=404)
        return FileResponse(path=file_path, filename=filename)

    return app


def _build_gradio_demo():
    import gradio as gr

    def run_custom(
        bank_file,
        invoice_files,
        receipt_files,
        bank_path,
        invoices_path,
        receipts_path,
        output_format,
    ):
        run_dir = generate_timestamped_output_dir(prefix="gradio-custom")

        if bank_file:
            bank_csv = Path(bank_file)
            if bank_csv.suffix.lower() != ".csv":
                raise ValueError("Unsupported bank file type. Please upload a .csv file.")
        else:
            bank_csv, _, _ = _resolve_demo_paths(bank_path, invoices_path, receipts_path)

        if invoice_files:
            invoice_jsons = [Path(item) for item in invoice_files]
        else:
            _, invoice_jsons, _ = _resolve_demo_paths(bank_path, invoices_path, receipts_path)

        if receipt_files:
            receipt_jsons = [Path(item) for item in receipt_files]
        else:
            _, _, receipt_jsons = _resolve_demo_paths(bank_path, invoices_path, receipts_path)

        result = run_demo_workflow(
            bank_csv=bank_csv,
            invoice_json_paths=invoice_jsons,
            receipt_json_paths=receipt_jsons,
            output_dir=run_dir,
            output_format=output_format,
        )

        file_paths = [str(run_dir / filename) for filename in result["files"].values()]
        return (
            result["reconciliation_text"],
            result["monthly_text"],
            result["warnings_text"],
            result["reconciliation_preview_html"],
            result["monthly_preview_html"],
            result["warnings_preview_html"],
            file_paths,
            str(run_dir),
        )

    def run_sample(output_format):
        del output_format
        result = run_sample_kedai_makan_demo()
        run_dir = Path(str(result["output_dir"]))
        file_paths = [str(run_dir / filename) for filename in result["files"].values()]
        return (
            result["reconciliation_text"],
            result["monthly_text"],
            result["warnings_text"],
            result["reconciliation_preview_html"],
            result["monthly_preview_html"],
            result["warnings_preview_html"],
            file_paths,
            str(run_dir),
        )

    with gr.Blocks(title="Malaysia FSI Local Web Demo") as demo:
        gr.Markdown("# Malaysia FSI Local Web Demo")
        gr.Markdown(
            "Offline local demo only. **HUMAN REVIEW REQUIRED** for all outputs. "
            "Only Maybank CSV parser is implemented."
        )

        gr.Markdown(
            "## Required Files\n"
            "- Bank statement: `.csv` (Maybank format only)\n"
            "- Invoice input: `.json` files\n"
            "- Receipt input: `.json` files (manual/JSON only)\n"
            "\n"
            "## Unsupported\n"
            "- No OCR/PDF/image parsing\n"
            "- No external APIs (MyInvois/SSM/JPN/BNM/CTOS/Bursa)\n"
            "- No login/auth, database, or SaaS"
        )

        output_format = gr.Dropdown(choices=sorted(OUTPUT_FORMATS), value="Markdown", label="Output format")
        sample_button = gr.Button("Run sample kedai makan demo")

        with gr.Row():
            bank_file = gr.File(label="Upload Maybank CSV", file_types=[".csv"])
            invoice_files = gr.Files(label="Upload Invoice JSON files", file_types=[".json"])
            receipt_files = gr.Files(label="Upload Receipt JSON files", file_types=[".json"])

        with gr.Row():
            bank_path = gr.Textbox(label="Or CSV path", value="maybank-valid.csv")
            invoices_path = gr.Textbox(label="Or invoices folder/path", value="invoices-exact-match/")
            receipts_path = gr.Textbox(label="Or receipts folder/path", value="receipts/")

        run_button = gr.Button("Run reconciliation + receipt summary")

        reconciliation_text = gr.Textbox(label="Reconciliation Summary", lines=10)
        monthly_text = gr.Textbox(label="Monthly Expense Summary", lines=8)

        warnings_text = gr.Textbox(label="Warnings (separate section)", lines=12)
        reconciliation_preview = gr.HTML(label="Reconciliation report preview")
        monthly_preview = gr.HTML(label="Monthly report preview")
        warnings_preview = gr.HTML(label="Warnings preview")
        report_files = gr.Files(label="Download generated reports")
        output_path = gr.Textbox(label="Output folder", lines=1)

        run_button.click(
            fn=run_custom,
            inputs=[bank_file, invoice_files, receipt_files, bank_path, invoices_path, receipts_path, output_format],
            outputs=[
                reconciliation_text,
                monthly_text,
                warnings_text,
                reconciliation_preview,
                monthly_preview,
                warnings_preview,
                report_files,
                output_path,
            ],
        )

        sample_button.click(
            fn=run_sample,
            inputs=[output_format],
            outputs=[
                reconciliation_text,
                monthly_text,
                warnings_text,
                reconciliation_preview,
                monthly_preview,
                warnings_preview,
                report_files,
                output_path,
            ],
        )

    return demo


def main() -> int:
    """Run web demo. Uses Gradio if installed; otherwise FastAPI fallback."""
    has_gradio = importlib.util.find_spec("gradio") is not None
    if has_gradio:
        demo = _build_gradio_demo()
        demo.launch(server_name="127.0.0.1", server_port=7860, show_error=True)
        return 0

    has_fastapi = importlib.util.find_spec("fastapi") is not None
    has_uvicorn = importlib.util.find_spec("uvicorn") is not None
    if not (has_fastapi and has_uvicorn):
        print(
            "Web demo requires either gradio, or fastapi+uvicorn. "
            "Install one of those sets and rerun `python3 -m malaysia_fsi.web_demo.app`."
        )
        return 1

    import uvicorn

    app = create_fastapi_app()
    print("Starting FastAPI local web demo at http://127.0.0.1:7860")
    uvicorn.run(app, host="127.0.0.1", port=7860)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
