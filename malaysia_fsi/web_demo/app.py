"""Local web demo app for offline SME reconciliation and receipt summaries."""

import csv
import html
import importlib.util
import json
import shutil
import tempfile
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
from malaysia_fsi.receipts.categorizer import batch_categorize_receipts, load_receipts_from_paths
from malaysia_fsi.receipts.monthly_expense_summary import build_monthly_expense_summary
from malaysia_fsi.receipts.report import (
    export_monthly_summary_csv,
    export_monthly_summary_json,
    export_monthly_summary_markdown,
)

OUTPUT_FORMATS = {"Markdown", "JSON", "CSV"}
RUN_ROOT = Path(tempfile.gettempdir()) / "malaysia_fsi_web_demo"
RUN_ROOT.mkdir(parents=True, exist_ok=True)


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


def _render_index_markdown(files: Dict[str, str], run_id: Optional[str] = None) -> str:
    lines = [
        "# Malaysia FSI Web Demo Output Index",
        "",
        "Generated reports:",
    ]

    for label, filename in files.items():
        if run_id:
            lines.append(f"- [{label}](/download/{run_id}/{filename})")
        else:
            lines.append(f"- [{label}]({filename})")

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


def run_demo_workflow(
    bank_csv: Path,
    invoice_json_paths: Sequence[Path],
    receipt_json_paths: Sequence[Path],
    output_dir: Path,
    output_format: str = "Markdown",
    run_id: Optional[str] = None,
) -> Dict[str, object]:
    """Run reconciliation + receipt summary and persist report artifacts."""

    if output_format not in OUTPUT_FORMATS:
        raise ValueError(f"Unsupported output format: {output_format}")

    if not bank_csv.exists():
        raise FileNotFoundError(f"Bank CSV not found: {bank_csv}")

    if not invoice_json_paths:
        raise ValueError("At least one invoice JSON input is required")

    if not receipt_json_paths:
        raise ValueError("At least one receipt JSON input is required")

    output_dir.mkdir(parents=True, exist_ok=True)

    statement = BankStatementParser().parse_file(bank_csv, bank_hint="maybank")
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

    if output_format == "Markdown":
        reconciliation_filename = "reconciliation.md"
        monthly_filename = "monthly-expense-summary.md"
        reconciliation_content = export_reconciliation_markdown(reconciliation)
        monthly_content = export_monthly_summary_markdown(monthly_summary)
    elif output_format == "JSON":
        reconciliation_filename = "reconciliation.json"
        monthly_filename = "monthly-expense-summary.json"
        reconciliation_content = export_reconciliation_json(reconciliation)
        monthly_content = export_monthly_summary_json(monthly_summary)
    else:
        reconciliation_filename = "reconciliation.csv"
        monthly_filename = "monthly-expense-summary.csv"
        reconciliation_content = export_reconciliation_csv(reconciliation)
        monthly_content = export_monthly_summary_csv(monthly_summary)

    _write_text(output_dir / reconciliation_filename, reconciliation_content)
    _write_text(output_dir / monthly_filename, monthly_content)

    categorized_filename = "categorized-expenses.csv"
    warnings_filename = "warnings-summary.md"
    index_filename = "index.md"

    _write_categorized_csv(output_dir / categorized_filename, categorized_receipts)
    warnings_markdown = _render_warnings_markdown(reconciliation, monthly_summary, categorized_receipts)
    _write_text(output_dir / warnings_filename, warnings_markdown)

    files = {
        "Reconciliation": reconciliation_filename,
        "Monthly Expense Summary": monthly_filename,
        "Categorized Expenses": categorized_filename,
        "Warnings Summary": warnings_filename,
    }
    index_markdown = _render_index_markdown(files, run_id=run_id)
    _write_text(output_dir / index_filename, index_markdown)

    files["Index"] = index_filename

    warnings = reconciliation.get("warnings", []) + monthly_summary.get("warnings", [])

    return {
        "reconciliation": reconciliation,
        "monthly_summary": monthly_summary,
        "warnings": warnings,
        "reconciliation_text": _reconciliation_text(reconciliation),
        "monthly_text": _monthly_text(monthly_summary),
        "warnings_text": warnings_markdown,
        "files": files,
        "output_dir": str(output_dir),
    }


def _resolve_demo_paths(
    bank_path_input: str,
    invoices_path_input: str,
    receipts_path_input: str,
) -> Tuple[Path, List[Path], List[Path]]:
    repo_root = Path.cwd()

    bank = _resolve_input(
        Path(bank_path_input),
        [repo_root / "test-fixtures" / "demo", repo_root / "test-fixtures" / "sample-data"],
    )

    invoices_path = _resolve_input(
        Path(invoices_path_input),
        [repo_root / "test-fixtures" / "demo", repo_root / "test-fixtures" / "sample-data"],
    )

    receipts_path = _resolve_input(
        Path(receipts_path_input),
        [repo_root / "test-fixtures" / "demo", repo_root / "test-fixtures"],
    )

    invoice_jsons = _resolve_json_paths(invoices_path)
    receipt_jsons = _resolve_json_paths(receipts_path)

    return bank, invoice_jsons, receipt_jsons


def _build_result_html(result: Dict[str, object], run_id: str) -> str:
    files = result["files"]
    link_items = []
    for label, filename in files.items():
        href = f"/download/{run_id}/{filename}"
        link_items.append(f"<li><a href=\"{href}\">{html.escape(label)}: {html.escape(filename)}</a></li>")

    return f"""
    <h2>Run Complete</h2>
    <p><strong>HUMAN REVIEW REQUIRED</strong> for all outputs.</p>
    <h3>Reconciliation Summary</h3>
    <pre>{html.escape(str(result['reconciliation_text']))}</pre>
    <h3>Monthly Expense Summary</h3>
    <pre>{html.escape(str(result['monthly_text']))}</pre>
    <h3>Warnings</h3>
    <pre>{html.escape(str(result['warnings_text']))}</pre>
    <h3>Download Reports</h3>
    <ul>
      {''.join(link_items)}
    </ul>
    """


def _render_fastapi_form(message_html: str = "") -> str:
    return f"""
    <html>
      <head>
        <title>Malaysia FSI Local Web Demo</title>
      </head>
      <body style=\"font-family: sans-serif; margin: 2rem;\">
        <h1>Malaysia FSI Local Web Demo</h1>
        <p>Offline-only demo. No external APIs. <strong>HUMAN REVIEW REQUIRED</strong>.</p>
        <form action=\"/run\" method=\"post\" enctype=\"multipart/form-data\">
          <h3>Use Existing Demo Paths (recommended)</h3>
          <label>Maybank CSV path/name:</label><br/>
          <input name=\"bank_path\" value=\"maybank-valid.csv\" style=\"width: 40rem;\"/><br/><br/>

          <label>Invoice JSON folder/path:</label><br/>
          <input name=\"invoices_path\" value=\"invoices-exact-match/\" style=\"width: 40rem;\"/><br/><br/>

          <label>Receipt JSON folder/path:</label><br/>
          <input name=\"receipts_path\" value=\"receipts/\" style=\"width: 40rem;\"/><br/><br/>

          <h3>Or Upload Files</h3>
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

          <button type=\"submit\">Run Reconciliation + Receipt Summary</button>
        </form>
        <hr/>
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
        return _render_fastapi_form()

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
        run_id = datetime.utcnow().strftime("%Y%m%d%H%M%S") + "-" + uuid.uuid4().hex[:8]
        run_dir = RUN_ROOT / run_id
        upload_dir = run_dir / "uploads"
        output_dir = run_dir / "reports"

        try:
            upload_dir.mkdir(parents=True, exist_ok=True)

            if bank_file and bank_file.filename:
                bank_csv = upload_dir / bank_file.filename
                bank_csv.write_bytes(await bank_file.read())
            else:
                bank_csv, _, _ = _resolve_demo_paths(bank_path, invoices_path, receipts_path)

            if invoice_files:
                invoice_dir = upload_dir / "invoices"
                invoice_dir.mkdir(parents=True, exist_ok=True)
                invoice_jsons: List[Path] = []
                for file in invoice_files:
                    if file and file.filename:
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
                    if file and file.filename:
                        file_path = receipt_dir / file.filename
                        file_path.write_bytes(await file.read())
                        receipt_jsons.append(file_path)
            else:
                _, _, receipt_jsons = _resolve_demo_paths(bank_path, invoices_path, receipts_path)

            result = run_demo_workflow(
                bank_csv=bank_csv,
                invoice_json_paths=invoice_jsons,
                receipt_json_paths=receipt_jsons,
                output_dir=output_dir,
                output_format=output_format,
                run_id=run_id,
            )
            message = _build_result_html(result, run_id)
            return _render_fastapi_form(message)
        except Exception as exc:
            message = f"<p style=\"color: red;\">Run failed: {html.escape(str(exc))}</p>"
            return _render_fastapi_form(message)

    @app.get("/download/{run_id}/{filename}")
    async def download(run_id: str, filename: str):
        file_path = RUN_ROOT / run_id / "reports" / filename
        if not file_path.exists() or not file_path.is_file():
            return HTMLResponse("File not found", status_code=404)
        return FileResponse(path=file_path, filename=filename)

    return app


def _build_gradio_demo():
    import gradio as gr

    def run_gradio(
        bank_file,
        invoice_files,
        receipt_files,
        bank_path,
        invoices_path,
        receipts_path,
        output_format,
    ):
        run_id = datetime.utcnow().strftime("%Y%m%d%H%M%S") + "-" + uuid.uuid4().hex[:8]
        run_dir = RUN_ROOT / run_id
        output_dir = run_dir / "reports"

        if bank_file:
            bank_csv = Path(bank_file)
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
            output_dir=output_dir,
            output_format=output_format,
            run_id=run_id,
        )

        files = [str(output_dir / name) for name in result["files"].values()]
        return result["reconciliation_text"], result["monthly_text"], result["warnings_text"], files

    with gr.Blocks(title="Malaysia FSI Local Web Demo") as demo:
        gr.Markdown("# Malaysia FSI Local Web Demo")
        gr.Markdown("Offline local demo only. **HUMAN REVIEW REQUIRED** for all outputs.")

        with gr.Row():
            bank_file = gr.File(label="Upload Maybank CSV", file_types=[".csv"])
            invoice_files = gr.Files(label="Upload Invoice JSON files", file_types=[".json"])
            receipt_files = gr.Files(label="Upload Receipt JSON files", file_types=[".json"])

        with gr.Row():
            bank_path = gr.Textbox(label="Or CSV path", value="maybank-valid.csv")
            invoices_path = gr.Textbox(label="Or invoices folder/path", value="invoices-exact-match/")
            receipts_path = gr.Textbox(label="Or receipts folder/path", value="receipts/")

        output_format = gr.Dropdown(choices=sorted(OUTPUT_FORMATS), value="Markdown", label="Output format")
        run_button = gr.Button("Run Reconciliation + Receipt Summary")

        reconciliation_text = gr.Textbox(label="Reconciliation Summary", lines=10)
        monthly_text = gr.Textbox(label="Monthly Expense Summary", lines=8)
        warnings_text = gr.Textbox(label="Warnings", lines=12)
        report_files = gr.Files(label="Download generated reports")

        run_button.click(
            fn=run_gradio,
            inputs=[bank_file, invoice_files, receipt_files, bank_path, invoices_path, receipts_path, output_format],
            outputs=[reconciliation_text, monthly_text, warnings_text, report_files],
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
