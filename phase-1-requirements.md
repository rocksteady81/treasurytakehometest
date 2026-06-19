# Phase 1 Requirements: TTB Label Compliance Prototype

Date: 2026-06-19
Scope: Phase 1 only. This document defines the required label fields and paperwork comparison fields for a standalone prototype that reviews alcohol beverage labels against TTB requirements and user-provided paperwork data. Phase 2 implementation should not begin until explicitly approved.

## Official TTB Sources Used

- TTB Labeling Resources: https://www.ttb.gov/labeling/labeling-resources
- TTB Distilled Spirits Labeling: https://www.ttb.gov/regulated-commodities/beverage-alcohol/distilled-spirits/labeling
- TTB Malt Beverage Labeling: https://www.ttb.gov/regulated-commodities/beverage-alcohol/beer/labeling
- TTB Wine Labeling: https://www.ttb.gov/regulated-commodities/beverage-alcohol/wine/labeling
- TTB Certificate of Label Approval page: https://www.ttb.gov/alfd/certificate-of-label-aproval-cola
- TTB F 5100.31, Application for and Certification/Exemption of Label/Bottle Approval: https://www.ttb.gov/system/files/images/pdfs/forms/f510031.pdf

## Phase 1 Objective

Create a machine-checkable rules inventory for the prototype. The program should eventually inspect label images, extract text, verify that required information appears, and compare extracted label fields against paperwork data manually entered or uploaded by the reviewer.

The Phase 1 deliverable is not software. It is the compliance field map and validation plan.

## Beverage Types In Scope

The prototype should classify each reviewed submission as one of:

- Wine, including cider and mead where regulated as wine.
- Distilled spirits.
- Malt beverages.

TTB F 5100.31 requires the applicant to identify the product type as wine, distilled spirits, or malt beverages. For this prototype, the app will not integrate with COLAs Online or retrieve COLA records automatically.

## Required Label Fields By Beverage Type

### Distilled Spirits

TTB lists the following mandatory distilled spirits label information for most labels:

| Field | Required | Prototype Detection Target |
| --- | --- | --- |
| Brand name | Yes | Extract brand text and compare to reviewer-provided brand name. |
| Class or type designation | Yes | Extract product identity, such as bourbon whiskey, vodka, gin, rum, liqueur. |
| Alcohol content | Yes | Extract ABV and optional proof if present. |
| Age statement | Conditional | Required for certain classes/types; flag for reviewer when class/type may require it. |
| Color ingredient disclosures | Conditional | Required if applicable. |
| Commodity statement | Conditional | Required if applicable. |
| Health warning statement | Yes | Detect required government warning text. |
| Name and address | Yes | Extract bottler, distiller, producer, importer, or responsible party name/address. |
| Net contents | Yes | Extract volume such as 750 mL, 1 L, 1.75 L. |
| Country of origin | Imports only | Detect country/origin statement for imported products. |

### Malt Beverages

TTB lists the following mandatory malt beverage label information for most labels:

| Field | Required | Prototype Detection Target |
| --- | --- | --- |
| Brand name | Yes | Extract brand text and compare to reviewer-provided brand name. |
| Net contents | Yes | Extract volume statement. |
| Class or type designation | Yes | Extract type such as beer, ale, lager, malt beverage, flavored malt beverage. |
| Name and address, domestic | Yes for domestic products | Extract brewer, bottler, packer, or responsible party name/address. |
| Name and address, imports | Yes for imports | Extract importer or foreign responsible party text. |
| Color additive disclosures | Conditional | Required if applicable. |
| Sulfite and aspartame declarations | Conditional | Required if applicable. |
| Alcohol content | Mandatory or optional depending on product/state/rules | Extract if present; require where the paperwork/product type indicates mandatory. |
| Country of origin | Imports only | Detect country/origin statement for imported products. |
| Health warning statement | Yes | Detect required government warning text. |

### Wine

TTB lists the following mandatory wine label information for most wine labels:

| Field | Required | Prototype Detection Target |
| --- | --- | --- |
| Appellation of origin | Conditional | Required in certain circumstances; compare if stated on label/paperwork. |
| Brand name | Yes | Extract brand text and compare to reviewer-provided brand name. |
| Class or type designation | Yes | Extract wine class/type, such as red wine, white wine, table wine, grape wine, cider, mead. |
| Percentage of foreign wine | Conditional | Required if applicable. |
| Alcohol content | Yes | Extract ABV or allowed wine alcohol statement. |
| Color ingredient disclosures | Conditional | Required if applicable. |
| Country of origin | Imports only | Detect country/origin statement for imported products. |
| Health warning statement | Yes | Detect required government warning text. |
| Name and address | Yes | Extract bottler, producer, importer, or responsible party name/address. |
| Net contents | Yes | Extract volume statement. |
| Sulfite declaration | Conditional | Required when applicable, commonly at 10+ ppm sulfur dioxide/sulfiting agents. |

## Common Required Label Checks

Across beverage types, the prototype should prioritize these cross-cutting checks:

1. Required field presence: whether each required or conditionally required field appears somewhere on the submitted label set.
2. Field-to-paperwork agreement: whether label text matches reviewer-entered paperwork data based on TTB F 5100.31 fields.
3. Low-confidence OCR: whether a field was detected but confidence is too low for automated pass.
4. Conditional applicability: whether product type, import status, formula, wine varietal, appellation, or special claims create extra review requirements.
5. Misleading or inconsistent text: whether label information conflicts with paperwork or other label text.
6. Manual reviewer handoff: any conditional, ambiguous, or low-confidence result should be flagged instead of auto-rejected.

## Government Health Warning Detection

The prototype should detect a government health warning statement on all beverage alcohol labels where required by TTB regulations. In Phase 1, define this as a required text-presence check with fuzzy matching, because OCR may read small warning text imperfectly.

Prototype matching should look for key phrase groups rather than exact full-text matching only:

- `GOVERNMENT WARNING`
- pregnancy / birth defects warning language
- driving or operating machinery warning language
- health problems warning language

A reviewer should confirm failures because small text, curved bottles, glare, and low-resolution scans may produce OCR misses.

## Paperwork Fields From TTB F 5100.31

TTB F 5100.31 is the primary paperwork reference for this prototype. The app will not connect to COLAs Online, query the Public COLA Registry, or automatically import COLA records. Instead, the reviewer will provide the needed paperwork values manually or through a local file upload.

| Form Item | Field | Required/Conditional | Prototype Use |
| --- | --- | --- | --- |
| 1 | Representative ID number | If any | Metadata only; not expected on label. |
| 2 | Plant registry, basic permit, or brewer's notice number | Required by instructions | Submission identity/routing; not usually label text. |
| 3 | Source of product | Required by instructions | Helps determine domestic/import/relabel handling. |
| 4 | Serial number | Required | Submission identity; not label text. |
| 5 | Type of product | Required | Select wine, distilled spirits, or malt beverage rule set. |
| 6 | Brand name | Required | Must match label brand name. |
| 7 | Fanciful name | If any | Must match label if present/applicable. |
| 8 | Applicant name and address as shown on permit/registry/brewer's notice | Required | Compare against responsible name/address on label when applicable. |
| 8a | Mailing address if different | Conditional | Metadata; generally not label text unless used. |
| 9 | Formula | Conditional | Determines whether approved formula or product evaluation information is required. |
| 10 | Grape varietal(s), wine only | Conditional | Compare if varietal appears on wine label. |
| 11 | Wine appellation | If on label | Compare if appellation appears on wine label. |
| 12 | Phone number | Required by form field | PII/contact; should not be label-comparison target unless printed on label. |
| 13 | Email address | Optional | PII/contact; should not be label-comparison target unless printed on label. |
| 14 | Type of application | Required | Determines approval/exemption/distinctive bottle/resubmission handling. |
| 15 | Blown, branded, embossed information and translations of foreign language label text | Conditional | Compare container text and translations to OCR/label image. |
| 16 | Date of application | Required | Audit metadata. |
| 17 | Signature of applicant or authorized agent | Required | PII/authentication metadata. |
| 18 | Printed name of applicant or authorized agent | Required | PII/authentication metadata. |

## Paperwork-to-Label Match Rules

The prototype should compare extracted label fields to paperwork fields as follows:

| Label Field | Paperwork Field | Match Rule |
| --- | --- | --- |
| Beverage type | Item 5 | Must choose the corresponding rule set. |
| Brand name | Item 6 | Exact or high-confidence fuzzy match; differences flagged. |
| Fanciful name | Item 7 | If submitted or present on label, compare and flag mismatch. |
| Responsible name/address | Item 8 and possibly 8a | Compare applicant/permit entity to label name/address where applicable; allow abbreviations and punctuation differences. |
| Formula-dependent claims | Item 9 | If formula appears required, verify reviewer supplied a formula ID or mark for manual review. |
| Wine grape varietal | Item 10 | If varietal appears on label, it must be listed on paperwork. |
| Wine appellation | Item 11 | If appellation appears on label, it must match paperwork. |
| Application type/exemption state | Item 14 | If exemption is checked, verify required state-only limitation appears where required. |
| Embossed/branded/container text | Item 15 | If item 15 lists net contents or other text not on paper labels, compare against image/container OCR when visible. |
| Foreign-language text | Item 15 | If foreign language appears on label, translation should be present in paperwork. |

## Security And PII Considerations For Future Phases

TTB paperwork includes contact information and signatures. For the prototype, these should be treated as sensitive submission data even if the primary label content is public-facing.

Minimum future controls:

- Local-only processing by default; no cloud OCR or external AI calls unless specifically authorized.
- Encrypt local storage containing label images, paperwork data, OCR output, reviewer actions, signatures, phone numbers, and email addresses.
- Avoid storing unnecessary PII in logs.
- Separate reviewer-visible label compliance fields from administrative contact/signature fields.
- Maintain immutable audit events for uploads, OCR extraction, edits, approvals, rejections, and exports.
- Apply role-based access before pilot use.
- Support data retention and deletion policies aligned with agency requirements.

## Phase 1 Prototype Rule Priorities

For the first working prototype after Phase 1 approval, prioritize rules in this order:

1. Product type selection from reviewer-provided paperwork data.
2. Brand name presence and match.
3. Class/type designation presence.
4. Alcohol content presence and match where mandatory or submitted.
5. Net contents presence.
6. Name/address presence.
7. Government health warning presence.
8. Country of origin for imports.
9. Wine varietal/appellation checks when present.
10. Formula/product-evaluation conditional flagging.
11. Conditional disclosures such as sulfites, color additives, aspartame, commodity statements, age statements, and percentage of foreign wine.

## Out Of Scope Until Later Phases

Do not begin these until Phase 2 or later is approved:

- OCR implementation.
- Desktop application UI.
- Database schema.
- Automated reviewer workflow.
- COLAs Online, Public COLA Registry, or other external system integration.
- Packaging as a standalone executable.
- Model training or benchmark testing.

## Open Questions For TTB/Product Owner

1. Will the prototype receive paperwork data by manual entry, completed PDF forms, or structured local files?
2. Should the first prototype focus on all three beverage types, or start with distilled spirits because the sample label is distilled spirits?
3. Should the prototype validate only field presence/matching, or also type-size, legibility, placement, and contrast?
4. What is the expected scan quality: flat label images, bottle photos, scanned PDFs, or local label image uploads?
5. Which data retention standard should govern local prototype storage?
