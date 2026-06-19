# Architecture

## Local-Only Prototype Architecture

```mermaid
flowchart LR
    reviewer["Reviewer"]
    browser["Local Browser UI<br/>127.0.0.1:8765"]
    app["Python Local App<br/>app.py"]
    rules["Validation Rules<br/>ttb_rules.py"]
    ocr["Local Tesseract OCR<br/>optional"]
    storage["Local JSON Storage<br/>data/cases.json"]
    reports["Local Text Reports<br/>data/reports/"]

    reviewer --> browser
    browser --> app
    app --> rules
    app --> ocr
    app --> storage
    app --> reports
    rules --> app
```

## Review Workflow

```mermaid
flowchart TD
    start["Start Local App"]
    paperwork["Enter Reviewer-Provided<br/>Paperwork Fields"]
    label["Upload Label Image<br/>or Paste OCR Text"]
    extract["Extract Label Fields"]
    validate["Compare Against<br/>TTB Rule Map"]
    review["Reviewer Reviews<br/>Flags and Mismatches"]
    decision["Save Decision<br/>and Notes"]
    report["Generate Local<br/>Text Report"]

    start --> paperwork
    paperwork --> label
    label --> extract
    extract --> validate
    validate --> review
    review --> decision
    decision --> report
```

## Key Design Decisions

- **Python standard library app shell:** keeps the prototype portable and avoids dependency-install risk during the job-test demo.
- **Local browser UI:** gives a clean reviewer workflow without requiring a full desktop framework.
- **Tesseract adapter:** uses local OCR when available, while still supporting pasted OCR text for demo reliability.
- **Rules module separation:** keeps regulatory checks separate from the UI.
- **JSON storage:** simple Phase 5 submission artifact; production should replace it with encrypted storage.
- **Reviewer-in-the-loop:** flags problems for human confirmation instead of making final legal determinations.

## Production Evolution

```mermaid
flowchart LR
    prototype["Current Prototype"]
    encrypted["Encrypted Storage"]
    auth["Role-Based Access"]
    audit["Tamper-Evident Audit Logs"]
    package["Signed Desktop Package"]
    validation["Accuracy Benchmarking"]
    pilot["Controlled Pilot"]

    prototype --> encrypted
    encrypted --> auth
    auth --> audit
    audit --> package
    package --> validation
    validation --> pilot
```

