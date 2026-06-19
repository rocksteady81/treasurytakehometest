from __future__ import annotations

import html
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ttb_rules import FIELD_LABELS, extract_label_fields, paperwork_from_mapping, summarize_result, validate_label


HOST = os.environ.get("HOST") or ("0.0.0.0" if os.environ.get("PORT") else "127.0.0.1")
PORT = int(os.environ.get("PORT", "8765"))
DATA_DIR = Path("data")
CASES_PATH = DATA_DIR / "cases.json"
REPORTS_DIR = DATA_DIR / "reports"
COMPARISON_FIELDS = [
    "brand_name",
    "class_type",
    "alcohol_content",
    "net_contents",
    "name_address",
    "health_warning",
    "country_of_origin",
    "appellation",
    "sulfite_declaration",
]


SAMPLE_TEXT = """OLD TOM DISTILLERY
Kentucky Straight Bourbon Whiskey
45% Alc./Vol. (90 Proof)
750 mL
Bottled by Old Tom Distillery, Louisville, KY
GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages
during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs
your ability to drive a car or operate machinery, and may cause health problems.
"""


def find_tesseract() -> str:
    candidates = [
        shutil.which("tesseract"),
        "/opt/homebrew/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/opt/local/bin/tesseract",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)
    return ""


def tesseract_status() -> str:
    tesseract_path = find_tesseract()
    if not tesseract_path:
        return "Image OCR unavailable: Tesseract was not found on this machine."
    try:
        completed = subprocess.run(
            [tesseract_path, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return f"Image OCR available at {tesseract_path}."
    version = completed.stdout.splitlines()[0] if completed.stdout else "Tesseract installed"
    return f"Image OCR available: {version} ({tesseract_path})."


def run_ocr(image_path: Path) -> tuple[str, str]:
    tesseract_path = find_tesseract()
    if not tesseract_path:
        return "", "Tesseract OCR was not found. Paste OCR/sample label text below, or install Tesseract for image OCR."
    try:
        completed = subprocess.run(
            [tesseract_path, str(image_path), "stdout", "--psm", "6"],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except Exception as exc:
        return "", f"OCR failed: {exc}"
    if completed.returncode != 0:
        return "", completed.stderr.strip() or "OCR failed with no error details."
    return completed.stdout.strip(), "OCR completed locally using Tesseract."


def parse_multipart(body: bytes, content_type: str) -> dict[str, str]:
    boundary_marker = "boundary="
    if boundary_marker not in content_type:
        return {}
    boundary = content_type.split(boundary_marker, 1)[1].strip().strip('"')
    parts = body.split(("--" + boundary).encode())
    fields: dict[str, str] = {}
    temp_dir = Path(tempfile.gettempdir()) / "ttb_label_prototype"
    temp_dir.mkdir(parents=True, exist_ok=True)

    for part in parts:
        if not part or part in {b"--\r\n", b"--"}:
            continue
        header_blob, _, data = part.partition(b"\r\n\r\n")
        if not data:
            continue
        headers = header_blob.decode("utf-8", errors="ignore")
        data = data.removesuffix(b"\r\n").removesuffix(b"--")
        name = ""
        filename = ""
        for header in headers.splitlines():
            if "Content-Disposition" not in header:
                continue
            for chunk in header.split(";"):
                chunk = chunk.strip()
                if chunk.startswith("name="):
                    name = chunk.split("=", 1)[1].strip('"')
                if chunk.startswith("filename="):
                    filename = os.path.basename(chunk.split("=", 1)[1].strip('"'))
        if not name:
            continue
        if filename and data:
            safe_name = "".join(char for char in filename if char.isalnum() or char in "._-") or "label_image"
            file_path = temp_dir / safe_name
            file_path.write_bytes(data)
            fields[name] = str(file_path)
        else:
            fields[name] = data.decode("utf-8", errors="replace")
    return fields


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_storage() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    REPORTS_DIR.mkdir(exist_ok=True)
    if not CASES_PATH.exists():
        CASES_PATH.write_text("[]", encoding="utf-8")


def load_cases() -> list[dict[str, object]]:
    ensure_storage()
    try:
        loaded = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if isinstance(loaded, list):
        return loaded
    return []


def save_cases(cases: list[dict[str, object]]) -> None:
    ensure_storage()
    CASES_PATH.write_text(json.dumps(cases, indent=2), encoding="utf-8")


def find_case(case_id: str) -> dict[str, object] | None:
    for review_case in load_cases():
        if review_case.get("case_id") == case_id:
            return review_case
    return None


def upsert_case(review_case: dict[str, object]) -> None:
    cases = load_cases()
    for index, existing in enumerate(cases):
        if existing.get("case_id") == review_case.get("case_id"):
            cases[index] = review_case
            save_cases(cases)
            return
    cases.append(review_case)
    save_cases(cases)


def append_audit(review_case: dict[str, object], action: str, detail: str) -> None:
    audit = review_case.setdefault("audit", [])
    if isinstance(audit, list):
        audit.append({"timestamp": utc_now(), "action": action, "detail": detail})


def selected(value: str, expected: str) -> str:
    return "selected" if value == expected else ""


def checked(values: dict[str, str], name: str) -> str:
    return "checked" if values.get(name) in {"on", "true", "1", "yes"} else ""


def issue_for_field(issues: list[object], field: str) -> str:
    matches = [issue for issue in issues if getattr(issue, "field", "") == field]
    if not matches:
        return "OK"
    highest = "INFO"
    for issue in matches:
        severity = getattr(issue, "severity", "info").upper()
        if severity == "FAIL":
            return "FAIL"
        if severity == "WARNING":
            highest = "WARNING"
    return highest


def render_case_list() -> str:
    cases = sorted(load_cases(), key=lambda item: str(item.get("updated_at", "")), reverse=True)
    if not cases:
        return '<p class="muted">No saved review cases yet.</p>'
    rows = []
    for review_case in cases[:12]:
        summary = escape(review_case.get("summary", ""))
        brand = escape(review_case.get("paperwork", {}).get("brand_name", "") if isinstance(review_case.get("paperwork"), dict) else "")
        decision = escape(review_case.get("decision", "Pending"))
        updated = escape(review_case.get("updated_at", ""))
        case_id = escape(review_case.get("case_id", ""))
        rows.append(
            f"<tr><td><a href=\"/case/{case_id}\">{case_id}</a></td><td>{brand}</td><td>{summary}</td><td>{decision}</td><td>{updated}</td></tr>"
        )
    return f"""<table>
      <thead><tr><th>Case</th><th>Brand</th><th>System Summary</th><th>Decision</th><th>Updated</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>"""


def render_comparison_table(paperwork: dict[str, str], extracted_fields: dict[str, str], issues: list[object]) -> str:
    rows = []
    for field in COMPARISON_FIELDS:
        paper_value = paperwork.get(field, "")
        label_value = extracted_fields.get(field, "")
        if not paper_value and not label_value and field not in {"health_warning"}:
            continue
        status = issue_for_field(issues, field)
        status_class = status.lower()
        rows.append(
            "<tr>"
            f"<td>{escape(FIELD_LABELS.get(field, field))}</td>"
            f"<td>{escape(paper_value)}</td>"
            f"<td>{escape(label_value)}</td>"
            f"<td><span class=\"pill {status_class}\">{escape(status)}</span></td>"
            "</tr>"
        )
    if not rows:
        return '<p class="muted">No comparison fields available yet.</p>'
    return f"""<table>
      <thead><tr><th>Field</th><th>Paperwork</th><th>Extracted From Label</th><th>Status</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>"""


def report_text(review_case: dict[str, object]) -> str:
    paperwork = review_case.get("paperwork", {})
    extracted = review_case.get("extracted_fields", {})
    issues = review_case.get("issues", [])
    audit = review_case.get("audit", [])
    lines = [
        "TTB LABEL COMPLIANCE REVIEW REPORT",
        f"Case ID: {review_case.get('case_id', '')}",
        f"Created: {review_case.get('created_at', '')}",
        f"Updated: {review_case.get('updated_at', '')}",
        f"System Summary: {review_case.get('summary', '')}",
        f"Reviewer Decision: {review_case.get('decision', 'Pending')}",
        f"Reviewer Notes: {review_case.get('reviewer_notes', '')}",
        "",
        "PAPERWORK VS LABEL",
    ]
    if isinstance(paperwork, dict) and isinstance(extracted, dict):
        for field in COMPARISON_FIELDS:
            lines.append(f"- {FIELD_LABELS.get(field, field)}")
            lines.append(f"  Paperwork: {paperwork.get(field, '')}")
            lines.append(f"  Label: {extracted.get(field, '')}")
    lines.extend(["", "ISSUES"])
    if isinstance(issues, list) and issues:
        for issue in issues:
            if isinstance(issue, dict):
                lines.append(f"- [{issue.get('severity', '').upper()}] {issue.get('field', '')}: {issue.get('message', '')}")
    else:
        lines.append("- No issues found.")
    lines.extend(["", "AUDIT"])
    if isinstance(audit, list):
        for event in audit:
            if isinstance(event, dict):
                lines.append(f"- {event.get('timestamp', '')} | {event.get('action', '')} | {event.get('detail', '')}")
    return "\n".join(lines) + "\n"


def write_report(review_case: dict[str, object]) -> Path:
    ensure_storage()
    case_id = str(review_case.get("case_id", "case"))
    path = REPORTS_DIR / f"{case_id}.txt"
    path.write_text(report_text(review_case), encoding="utf-8")
    return path


def render_form(
    result: str = "",
    extracted_text: str = "",
    status: str = "",
    values: dict[str, str] | None = None,
    comparison_html: str = "",
    case_id: str = "",
    decision: str = "Pending",
    reviewer_notes: str = "",
) -> bytes:
    values = values or {}
    beverage_type = values.get("beverage_type", "distilled_spirits")
    imported = checked(values, "imported")
    source_text = extracted_text or values.get("label_text", "")
    case_list = render_case_list()
    case_id_input = f'<input type="hidden" name="case_id" value="{escape(case_id)}">' if case_id else ""
    ocr_status = tesseract_status()
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TTB Label Compliance Prototype</title>
  <style>
    :root {{ color-scheme: light; --ink: #1f2937; --muted: #5b6472; --blue: #174ea6; --bg: #f7f9fc; --card: #ffffff; --line: #d7dde8; --ok:#167a3f; --warn:#a15c00; --fail:#b42318; }}
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--ink); }}
    header {{ background: linear-gradient(135deg, #12284c, #174ea6); color: white; padding: 28px 32px; }}
    main {{ max-width: 1180px; margin: 24px auto; padding: 0 20px 40px; }}
    h1 {{ margin: 0 0 6px; font-size: 28px; }}
    h2 {{ margin: 0 0 14px; font-size: 19px; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; align-items: start; }}
    .cards {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 18px; }}
    .metric {{ background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 14px; box-shadow: 0 8px 30px rgba(18, 40, 76, .05); }}
    .metric strong {{ display:block; font-size: 13px; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; margin-bottom: 5px; }}
    .metric span {{ font-weight: 800; }}
    .wide {{ grid-column: 1 / -1; }}
    .card {{ background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 18px; box-shadow: 0 8px 30px rgba(18, 40, 76, .06); }}
    label {{ display: block; font-weight: 650; margin: 12px 0 6px; }}
    input, select, textarea {{ width: 100%; box-sizing: border-box; border: 1px solid var(--line); border-radius: 9px; padding: 10px; font: inherit; }}
    textarea {{ min-height: 180px; resize: vertical; }}
    .row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    .checkbox {{ display: flex; align-items: center; gap: 8px; margin-top: 12px; font-weight: 600; }}
    .checkbox input {{ width: auto; }}
    button {{ background: var(--blue); color: white; border: 0; border-radius: 10px; padding: 12px 16px; font-weight: 750; cursor: pointer; margin-top: 14px; }}
    .secondary {{ background: #eef3fb; color: var(--blue); margin-left: 8px; }}
    .muted {{ color: var(--muted); }}
    .status {{ padding: 12px 14px; background: #eef6ff; border-left: 4px solid var(--blue); border-radius: 8px; margin-bottom: 14px; }}
    .result {{ white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 14px; }}
    .badge {{ display: inline-block; padding: 5px 9px; border-radius: 999px; font-size: 13px; font-weight: 750; background: #eef3fb; color: var(--blue); }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 9px; text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); font-size: 13px; }}
    a {{ color: var(--blue); font-weight: 700; }}
    .pill {{ display:inline-block; border-radius:999px; padding:3px 8px; font-weight:800; font-size:12px; background:#eef3fb; }}
    .pill.ok {{ color: var(--ok); background:#edf9f1; }}
    .pill.warning {{ color: var(--warn); background:#fff5e8; }}
    .pill.fail {{ color: var(--fail); background:#fff0ee; }}
    .pill.info {{ color: var(--blue); background:#eef3fb; }}
    .actions {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; }}
    .actions button {{ margin-top: 14px; }}
    .navlinks {{ margin-top: 10px; font-size: 14px; }}
    .navlinks a {{ color: white; margin-right: 14px; }}
    @media (max-width: 980px) {{ .cards {{ grid-template-columns: 1fr 1fr; }} }}
    @media (max-width: 820px) {{ .grid, .row, .cards {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <header>
    <h1>TTB Label Compliance Prototype</h1>
    <div>Phase 4 presentation build · local-only · reviewer-assisted compliance screening</div>
    <div class="navlinks">
      <a href="#review">Run Review</a>
      <a href="#results">Results</a>
      <a href="#cases">Saved Cases</a>
    </div>
  </header>
  <main>
    <section class="cards" aria-label="Prototype readiness summary">
      <div class="metric"><strong>Scope</strong><span>No COLA integration</span></div>
      <div class="metric"><strong>Processing</strong><span>Local-only</span></div>
      <div class="metric"><strong>OCR</strong><span>{escape(ocr_status)}</span></div>
      <div class="metric"><strong>Workflow</strong><span>Save case + report</span></div>
    </section>
    <form method="post" enctype="multipart/form-data">
      {case_id_input}
      <div class="grid" id="review">
        <section class="card">
          <h2>1. Reviewer-Provided Paperwork Data</h2>
          <p class="muted">Enter the fields the reviewer would normally compare against the label.</p>
          <label>Beverage Type</label>
          <select name="beverage_type">
            <option value="distilled_spirits" {selected(beverage_type, "distilled_spirits")}>Distilled Spirits</option>
            <option value="malt_beverage" {selected(beverage_type, "malt_beverage")}>Malt Beverage</option>
            <option value="wine" {selected(beverage_type, "wine")}>Wine</option>
          </select>
          <div class="row">
            <div><label>Brand Name</label><input name="brand_name" value="{escape(values.get("brand_name", "OLD TOM DISTILLERY"))}"></div>
            <div><label>Class/Type</label><input name="class_type" value="{escape(values.get("class_type", "Kentucky Straight Bourbon Whiskey"))}"></div>
          </div>
          <div class="row">
            <div><label>Alcohol Content</label><input name="alcohol_content" value="{escape(values.get("alcohol_content", "45% Alc./Vol."))}"></div>
            <div><label>Net Contents</label><input name="net_contents" value="{escape(values.get("net_contents", "750 mL"))}"></div>
          </div>
          <label>Name and Address</label>
          <input name="name_address" value="{escape(values.get("name_address", "Old Tom Distillery, Louisville, KY"))}">
          <div class="row">
            <div><label>Country of Origin</label><input name="country_of_origin" value="{escape(values.get("country_of_origin", ""))}"></div>
            <div><label>Formula/Product Eval ID</label><input name="formula_id" value="{escape(values.get("formula_id", ""))}"></div>
          </div>
          <div class="row">
            <div><label>Fanciful Name</label><input name="fanciful_name" value="{escape(values.get("fanciful_name", ""))}"></div>
            <div><label>Wine Varietal/Appellation</label><input name="grape_varietal" value="{escape(values.get("grape_varietal", ""))}"></div>
          </div>
          <label class="checkbox"><input type="checkbox" name="imported" {imported}> Imported product</label>
        </section>
        <section class="card">
          <h2>2. Label Image or OCR Text</h2>
          <p class="muted">Upload an image if Tesseract is installed, or paste OCR/sample text for a guaranteed demo.</p>
          <label>Label Image</label>
          <input type="file" name="label_image" accept="image/*">
          <label>Label Text</label>
          <textarea name="label_text">{escape(source_text)}</textarea>
          <div class="actions">
            <button type="submit" name="action" value="analyze">Run Local Label Check</button>
            <button class="secondary" type="submit" name="use_sample" value="1">Load Sample Label</button>
          </div>
        </section>
      </div>
      <section class="card wide" id="results" style="margin-top:18px;">
        <h2>3. Side-by-Side Review</h2>
        {f'<div class="status">{escape(status)}</div>' if status else '<p class="muted">Run a check to compare paperwork fields with extracted label fields.</p>'}
        {comparison_html or '<p class="muted">No comparison table yet.</p>'}
        <h2 style="margin-top:20px;">Reviewer Decision</h2>
        <div class="row">
          <div>
            <label>Decision</label>
            <select name="decision">
              <option {selected(decision, "Pending")}>Pending</option>
              <option {selected(decision, "Approved")}>Approved</option>
              <option {selected(decision, "Needs Applicant Correction")}>Needs Applicant Correction</option>
              <option {selected(decision, "Rejected")}>Rejected</option>
            </select>
          </div>
          <div>
            <label>Case ID</label>
            <input readonly value="{escape(case_id or 'Not saved yet')}">
          </div>
        </div>
        <label>Reviewer Notes / OCR Corrections</label>
        <textarea name="reviewer_notes">{escape(reviewer_notes)}</textarea>
        <div class="actions">
          <button type="submit" name="action" value="save_case">Save Review Case</button>
          <button class="secondary" type="submit" name="action" value="generate_report">Generate Text Report</button>
        </div>
        <h2 style="margin-top:20px;">System Result Details</h2>
        <div class="result">{result}</div>
      </section>
    </form>
    <section class="card" id="cases" style="margin-top:18px;">
      <h2>Saved Review Cases</h2>
      {case_list}
    </section>
  </main>
</body>
</html>"""
    return html_doc.encode("utf-8")


def format_result(fields: dict[str, str], issues: list[Any], summary: str) -> str:
    lines = [f"SUMMARY: {summary}", "", "EXTRACTED FIELDS:"]
    if not fields:
        lines.append("  No fields extracted.")
    for key, value in fields.items():
        lines.append(f"  {key}: {value}")
    lines.extend(["", "ISSUES:"])
    if not issues:
        lines.append("  No issues found.")
    for issue in issues:
        lines.append(f"  [{issue.severity.upper()}] {issue.field}: {issue.message}")
    return "\n".join(lines)


def issue_to_dict(issue: object) -> dict[str, str]:
    return {
        "severity": str(getattr(issue, "severity", "")),
        "field": str(getattr(issue, "field", "")),
        "message": str(getattr(issue, "message", "")),
    }


def build_review_case(
    values: dict[str, str],
    label_text: str,
    extracted_fields: dict[str, str],
    issues: list[object],
    summary: str,
    existing: dict[str, object] | None = None,
) -> dict[str, object]:
    now = utc_now()
    case_id = values.get("case_id") or str(uuid.uuid4())[:8].upper()
    review_case = dict(existing or {})
    review_case.update(
        {
            "case_id": case_id,
            "updated_at": now,
            "paperwork": {
                "beverage_type": values.get("beverage_type", ""),
                "brand_name": values.get("brand_name", ""),
                "class_type": values.get("class_type", ""),
                "alcohol_content": values.get("alcohol_content", ""),
                "net_contents": values.get("net_contents", ""),
                "name_address": values.get("name_address", ""),
                "country_of_origin": values.get("country_of_origin", ""),
                "fanciful_name": values.get("fanciful_name", ""),
                "grape_varietal": values.get("grape_varietal", ""),
                "appellation": values.get("appellation", ""),
                "formula_id": values.get("formula_id", ""),
                "imported": "true" if values.get("imported") in {"on", "true", "1", "yes"} else "",
            },
            "label_text": label_text,
            "extracted_fields": extracted_fields,
            "issues": [issue_to_dict(issue) for issue in issues],
            "summary": summary,
            "decision": values.get("decision", "Pending"),
            "reviewer_notes": values.get("reviewer_notes", ""),
        }
    )
    review_case.setdefault("created_at", now)
    return review_case


def values_from_case(review_case: dict[str, object]) -> dict[str, str]:
    paperwork = review_case.get("paperwork", {})
    values: dict[str, str] = {}
    if isinstance(paperwork, dict):
        values.update({str(key): str(value) for key, value in paperwork.items()})
    values["label_text"] = str(review_case.get("label_text", ""))
    values["case_id"] = str(review_case.get("case_id", ""))
    return values


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path.startswith("/case/"):
            case_id = path.rsplit("/", 1)[-1]
            review_case = find_case(case_id)
            if not review_case:
                self.send_error(404, "Review case not found")
                return
            values = values_from_case(review_case)
            extracted_fields = review_case.get("extracted_fields", {})
            issues = []
            if isinstance(review_case.get("issues"), list):
                for issue in review_case["issues"]:
                    if isinstance(issue, dict):
                        issues.append(type("Issue", (), issue))
            comparison_html = render_comparison_table(values, extracted_fields if isinstance(extracted_fields, dict) else {}, issues)
            result = report_text(review_case)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                render_form(
                    result=result,
                    extracted_text=str(review_case.get("label_text", "")),
                    status=f"Loaded saved case {case_id}.",
                    values=values,
                    comparison_html=comparison_html,
                    case_id=case_id,
                    decision=str(review_case.get("decision", "Pending")),
                    reviewer_notes=str(review_case.get("reviewer_notes", "")),
                )
            )
            return
        if path.startswith("/reports/"):
            report_name = os.path.basename(path.rsplit("/", 1)[-1])
            report_path = REPORTS_DIR / report_name
            if not report_path.exists():
                self.send_error(404, "Report not found")
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(report_path.read_bytes())
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(render_form())

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        content_type = self.headers.get("Content-Type", "")
        if content_type.startswith("multipart/form-data"):
            values = parse_multipart(body, content_type)
        else:
            values = {key: vals[-1] for key, vals in parse_qs(body.decode()).items()}

        action = values.get("action", "analyze")
        status_parts: list[str] = []
        label_text = values.get("label_text", "").strip()
        if values.get("use_sample"):
            label_text = SAMPLE_TEXT
            status_parts.append("Loaded built-in distilled spirits sample.")

        image_path = values.get("label_image", "")
        if image_path and Path(image_path).exists():
            ocr_text, ocr_status = run_ocr(Path(image_path))
            status_parts.append(ocr_status)
            if ocr_text:
                label_text = ocr_text

        paperwork = paperwork_from_mapping(values)
        extracted = extract_label_fields(label_text, paperwork.beverage_type)
        issues = validate_label(extracted, paperwork)
        summary = summarize_result(issues)
        result = format_result(extracted.fields, issues, summary)
        status_parts.append("Analysis completed locally. No external systems were contacted.")
        comparison_html = render_comparison_table(values, extracted.fields, issues)
        case_id = values.get("case_id", "")

        if action in {"save_case", "generate_report"}:
            existing = find_case(case_id) if case_id else None
            review_case = build_review_case(values, label_text, extracted.fields, issues, summary, existing=existing)
            append_audit(review_case, "analyzed", summary)
            append_audit(review_case, "decision", str(review_case.get("decision", "Pending")))
            if action == "generate_report":
                append_audit(review_case, "report_generated", "Text report generated locally.")
            upsert_case(review_case)
            case_id = str(review_case["case_id"])
            status_parts.append(f"Saved review case {case_id}.")
            if action == "generate_report":
                report_path = write_report(review_case)
                status_parts.append(f"Generated report: /reports/{report_path.name}")
            result = report_text(review_case)
            comparison_html = render_comparison_table(review_case["paperwork"], extracted.fields, issues) if isinstance(review_case.get("paperwork"), dict) else comparison_html

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            render_form(
                result=result,
                extracted_text=label_text,
                status=" ".join(status_parts),
                values=values,
                comparison_html=comparison_html,
                case_id=case_id,
                decision=values.get("decision", "Pending"),
                reviewer_notes=values.get("reviewer_notes", ""),
            )
        )

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


def main() -> int:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    display_host = "127.0.0.1" if HOST == "0.0.0.0" else HOST
    url = f"http://{display_host}:{PORT}"
    print(f"TTB Label Compliance Prototype running at {url}")
    print("Press Ctrl+C to stop. Processing is local-only.")
    if "--no-browser" not in sys.argv:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping prototype.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
