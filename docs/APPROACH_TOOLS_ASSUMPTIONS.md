# Brief Documentation of Approach, Tools Used, and Assumptions Made

## Approach

I built a working prototype that assists TTB label reviewers by checking alcohol beverage label information against reviewer-provided paperwork data.

The prototype follows a reviewer-in-the-loop model. It does not make final legal determinations or automatically reject labels. Instead, it extracts likely label fields, compares them to expected paperwork values, and flags missing information or possible mismatches for human review.

The work was organized in phases:

1. **Requirements mapping:** Reviewed TTB labeling guidance and TTB F 5100.31 fields to identify required label elements and paperwork comparison fields.
2. **Standalone scanner prototype:** Built a local Python web application that accepts label text or images and checks required fields.
3. **Reviewer workflow:** Added side-by-side paperwork vs label comparison, reviewer decisions, notes, saved cases, and report generation.
4. **Presentation readiness:** Added sample data, documentation, demo script, security notes, and deployment support.
5. **Submission readiness:** Published the code to GitHub and deployed a public demo for evaluation.

The prototype currently supports distilled spirits, malt beverages, and wine. It checks common required fields such as brand name, class/type, alcohol content, net contents, name/address, government health warning, and country of origin for imports.

## Tools Used

- **Python 3:** Main implementation language.
- **Python standard library:** Used for the local web server, HTML rendering, JSON storage, file handling, subprocess calls, and tests.
- **Tesseract OCR:** Optional local OCR engine for uploaded label images when installed.
- **HTML/CSS:** Browser-based reviewer interface.
- **JSON:** Local prototype storage for saved review cases.
- **unittest:** Automated tests for core validation behavior.
- **OpenAI Codex:** Used as a coding assistant to help plan, implement, document, test, and package the prototype.
- **GitHub:** Public source code repository.
- **Render:** Public hosted demo deployment.

No external AI service, cloud OCR service, COLAs Online integration, or Public COLA Registry lookup is used.

## Assumptions Made

- For the prototype, paperwork data is entered manually by the reviewer instead of being imported from COLAs Online.
- The deployed Render version is for sample or non-sensitive test data only.
- Real government or applicant PII should not be entered into the public demo.
- OCR output can be imperfect, so the system should flag issues for review rather than making final compliance decisions.
- TTB rules vary by beverage type and may include exceptions, so conditional requirements are handled conservatively.
- The prototype prioritizes field presence and paperwork matching over advanced checks such as type size, exact placement, contrast, and full regulatory exception handling.
- Local JSON storage is acceptable for the prototype, but production should use encrypted storage, role-based access control, formal audit logs, and approved retention policies.
- The first goal is to reduce reviewer workload by pre-screening labels, not to replace trained reviewers.

## Security And Privacy Considerations

The local version is designed to run on a reviewer workstation and bind to `127.0.0.1`. It does not contact external government systems and does not use external OCR or AI services.

The public Render deployment exists only so evaluators can quickly access and test the prototype. Production deployment should occur in an approved government-controlled environment with encryption, authentication, authorization, audit logging, and retention controls.

## Repository And Demo

- Source code repository: `https://github.com/rocksteady81/treasurytakehometest`
- Deployed demo: `https://treasurytakehometest.onrender.com`
