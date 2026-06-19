# Submission Checklist

Use this before sending or presenting the prototype.

## Run Check

- [ ] Start the app with `python3 app.py` or `run.command`.
- [ ] Confirm the browser opens to `http://127.0.0.1:8765`.
- [ ] Confirm Phase 5 readiness cards appear.
- [ ] Confirm Tesseract status appears in the OCR card.

## Demo Check

- [ ] Click `Load Sample Label`.
- [ ] Click `Run Local Label Check`.
- [ ] Confirm the sample label returns `No Issues Found`.
- [ ] Remove the government warning text.
- [ ] Rerun the check.
- [ ] Confirm the app flags the missing government health warning.
- [ ] Save a review case.
- [ ] Generate a text report.
- [ ] Reopen the saved case from the saved cases table.

## Files To Highlight

- [ ] `README.md`
- [ ] `docs/EXECUTIVE_SUMMARY.md`
- [ ] `docs/DEMO_SCRIPT.md`
- [ ] `docs/SECURITY_ARCHITECTURE.md`
- [ ] `docs/ARCHITECTURE.md`
- [ ] `phase-1-requirements.md`
- [ ] `app.py`
- [ ] `ttb_rules.py`
- [ ] `samples/`
- [ ] `tests/`

## Talking Points

- [ ] No COLA integration or external government system calls.
- [ ] No COLA integration.
- [ ] Reviewer-provided paperwork data.
- [ ] Tesseract OCR is local and optional.
- [ ] Reviewer-in-the-loop design.
- [ ] Production path includes encryption, RBAC, audit logs, and signed packaging.
