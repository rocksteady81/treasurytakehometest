# TTB Label Compliance Prototype

Standalone Phase 5 prototype package for reviewing alcohol beverage label text against TTB-required label fields and reviewer-provided paperwork data.

This prototype is intentionally local-only:

- No COLAs Online integration.
- No Public COLA Registry lookup.
- No cloud OCR or external AI calls.
- Local JSON-only case storage for reviewer workflow.

## What It Does

The app lets a reviewer:

1. Enter paperwork fields based on TTB F 5100.31.
2. Upload a label image if local Tesseract OCR is installed, or paste OCR text manually.
3. Run local extraction for common required label fields.
4. See side-by-side paperwork values vs extracted label values.
5. Save a review case with reviewer decision and notes.
6. Generate a simple local text report.

Supported beverage types:

- Distilled spirits
- Malt beverages
- Wine

## Run The Prototype

```bash
python3 app.py
```

Then open:

```text
http://127.0.0.1:8765
```

If the browser does not open automatically, copy the address from the terminal.

To prevent auto-opening the browser:

```bash
python3 app.py --no-browser
```

On macOS, you can also double-click:

```text
run.command
```

## Demo Path

1. Run `python3 app.py` or double-click `run.command`.
2. Click `Load Sample Label`.
3. Click `Run Local Label Check`.
4. Confirm the summary says `No Issues Found`.
5. Delete the government warning text from the label text area.
6. Run the check again.
7. Confirm the app flags a missing government health warning.
8. Choose a reviewer decision.
9. Click `Save Review Case`.
10. Click `Generate Text Report`.

Saved cases appear at the bottom of the page and can be reopened by clicking their case ID.

For a fuller talk track, use `docs/DEMO_SCRIPT.md`.

## OCR Notes

If Tesseract is installed on the reviewer machine and available on `PATH`, uploaded label images are processed locally using:

```bash
tesseract <image> stdout --psm 6
```

The app also checks common macOS Homebrew paths such as `/opt/homebrew/bin/tesseract`.

If Tesseract is not installed, the app explains that OCR is unavailable and continues using pasted label text. This keeps the job-test demo dependable without network installs.

## Security Posture

Phase 4 keeps the prototype simple and safe:

- Runs on `127.0.0.1` only.
- Processes all data locally.
- Does not transmit images, text, or paperwork fields externally.
- Stores uploaded images only in the operating system temp directory for the current local run.
- Stores saved review cases in local JSON at `data/cases.json`.
- Stores generated text reports in `data/reports/`.
- Avoids logging paperwork field values beyond normal local server access logs.

Future phases should replace JSON storage with encrypted case storage, role-based access, stronger audit controls, retention controls, and packaged executable signing.

See `docs/SECURITY_ARCHITECTURE.md` for the government-computer security narrative.

## Build Submission Package

Create a clean zip bundle:

```bash
python3 package_submission.py
```

The output is:

```text
dist/ttb-label-compliance-prototype.zip
```

## Deploy For Treasury Testing

The take-home form asks for a public deployed application URL. Use:

- `docs/DEPLOYMENT.md` for GitHub + Render deployment steps.
- `docs/SUBMISSION_ANSWERS.md` for exactly what to paste into the form.

## Files

- `phase-1-requirements.md` — official TTB source mapping and Phase 1 rule inventory.
- `app.py` — standalone local browser app.
- `ttb_rules.py` — extraction and validation rules.
- `tests/test_ttb_rules.py` — unit tests for core validation behavior.
- `docs/DEMO_SCRIPT.md` — interview demo talk track.
- `docs/SECURITY_ARCHITECTURE.md` — local-only security architecture note.
- `docs/EXECUTIVE_SUMMARY.md` — concise project overview for reviewers.
- `docs/ARCHITECTURE.md` — Mermaid architecture and workflow diagrams.
- `docs/SUBMISSION_CHECKLIST.md` — final pre-submission checklist.
- `docs/DEPLOYMENT.md` — GitHub and Render deployment instructions.
- `docs/SUBMISSION_ANSWERS.md` — form-answer template.
- `samples/sample_label_text.txt` — demo label OCR text.
- `samples/sample_paperwork.json` — matching demo paperwork data.
- `samples/sample_label.svg` — visual sample label artifact.
- `run.command` — macOS launcher.
- `Procfile`, `render.yaml`, `requirements.txt` — deployment support files.
- `package_submission.py` — builds a clean zip bundle.
- `data/cases.json` — generated after saving a case; local-only review case storage.
- `data/reports/` — generated text review reports.

## Run Tests

```bash
python3 -m unittest discover -s tests
```

## Prototype Limitations

This is a Phase 5 job-test prototype package, not a production compliance system.

- OCR quality depends on local Tesseract availability and image quality.
- Type size, placement, contrast, and precise regulatory exceptions are not fully automated.
- Conditional disclosures are flagged conservatively for reviewer attention.
- Fuzzy matching is intended to assist reviewers, not make final legal determinations.
