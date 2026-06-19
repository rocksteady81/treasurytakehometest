# Security Architecture Note

## Prototype Security Goals

The prototype is designed for a government-computer evaluation setting where the safest default is local-only processing.

Primary goals:

- Avoid external data transmission.
- Avoid COLA or Public COLA Registry integration.
- Keep the tool understandable and auditable.
- Treat paperwork contact fields and reviewer notes as sensitive data.
- Preserve human reviewer authority over final compliance decisions.

## Current Local-Only Design

| Area | Prototype Choice |
| --- | --- |
| App hosting | Local HTTP server bound to `127.0.0.1` |
| OCR | Local Tesseract binary only |
| External APIs | None |
| Database | Local JSON case file |
| Reports | Local text files |
| Network requirement | None |
| COLA integration | None |

## Sensitive Data

The prototype may process:

- Label images.
- Extracted OCR text.
- Reviewer-provided paperwork fields.
- Applicant names and addresses.
- Phone/email fields if added later.
- Reviewer decisions and notes.

For the prototype, generated case data is stored locally in `data/cases.json`, and reports are stored in `data/reports/`.

## Controls Implemented In Prototype

- Binds only to localhost.
- Uses no cloud OCR.
- Uses no external AI services.
- Does not call TTB systems.
- Keeps generated artifacts local.
- Keeps validation explainable through deterministic rules.

## Controls Recommended For Production

1. **Encrypted Storage**
   - Encrypt label images, OCR text, paperwork fields, decisions, and reports at rest.

2. **Role-Based Access Control**
   - Separate reviewer, supervisor, and administrator permissions.

3. **Formal Audit Logging**
   - Log case creation, OCR runs, field corrections, decisions, exports, and report generation.
   - Use tamper-evident audit records.

4. **Data Retention**
   - Apply agency-approved retention and deletion policies.

5. **Packaging And Deployment**
   - Package as a signed executable or managed desktop application.
   - Disable debug logging in production.
   - Deploy through approved endpoint-management tooling.

6. **Accessibility And Usability**
   - Validate keyboard navigation, contrast, screen-reader labels, and readable error states.

7. **Accuracy Validation**
   - Test on representative label samples.
   - Track false positives, false negatives, OCR confidence, and reviewer time saved.

## Reviewer-In-The-Loop Principle

The system should not automatically reject a label based only on OCR output. OCR mistakes, low-quality scans, curved bottle photos, glare, and conditional regulatory rules require reviewer confirmation.

