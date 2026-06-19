# Interview Demo Script

## Opening

This prototype is a standalone label screening tool for TTB-style alcohol beverage label review. It does not integrate with COLAs Online or any external government system. For the prototype, reviewer-provided paperwork data is compared against OCR or pasted label text. It can run locally on a workstation, and a hosted Render demo is available for evaluation with sample or non-sensitive data.

## Problem Statement

TTB reviews a high volume of alcohol beverage labels each year. The goal of this prototype is not to replace reviewers, but to reduce review time by pre-screening labels for missing required information and paperwork mismatches.

## Demo Flow

1. Start the app:

   ```bash
   python3 app.py
   ```

2. Open:

   ```text
   http://127.0.0.1:8765
   ```

3. Point out the readiness cards:

   - No COLA integration or external government system calls.
   - No COLA integration.
   - Tesseract OCR availability.
   - Save case and report workflow.

4. Click `Load Sample Label`.

5. Click `Run Local Label Check`.

6. Explain the side-by-side comparison:

   - Left column is reviewer-provided paperwork data.
   - Middle column is what the app extracted from the label.
   - Right column flags OK, warning, or fail.

7. Show a failure:

   - Delete the government warning text from the label text area.
   - Click `Run Local Label Check`.
   - Point out the missing required government health warning.

8. Save the review:

   - Choose `Needs Applicant Correction`.
   - Add a note such as `Government warning missing from submitted label image.`
   - Click `Save Review Case`.

9. Generate a report:

   - Click `Generate Text Report`.
   - Explain that the report is generated locally in `data/reports/`.

10. Reopen the saved case from the `Saved Review Cases` table.

## What To Emphasize

- The prototype is intentionally narrow, safe, and explainable.
- All processing is local.
- OCR is treated as reviewer assistance, not a final legal determination.
- Ambiguous or conditional rules are flagged for human review.
- The architecture leaves room for later encrypted storage, role-based access, and official deployment packaging.

## Likely Questions And Answers

### Does this replace a reviewer?

No. It reduces manual scanning time by highlighting likely missing required fields and mismatches. Final compliance decisions remain with trained reviewers.

### Why Python?

Python is the fastest path for a working prototype because it has strong OCR, text-processing, and desktop packaging support. It can run fully offline and can later be packaged for government workstations.

### Why no COLA integration?

For this prototype, the requirement is to compare labels against supplied paperwork data without relying on external systems. That keeps the demo secure, portable, and realistic for a job-test environment.

### What would production need?

Encrypted storage, formal audit logs, role-based access control, retention policy enforcement, signed packaging, accessibility testing, and validation against a large labeled test set.
