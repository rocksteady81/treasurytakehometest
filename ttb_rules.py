from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any


BEVERAGE_RULES: dict[str, dict[str, str]] = {
    "distilled_spirits": {
        "brand_name": "required",
        "class_type": "required",
        "alcohol_content": "required",
        "net_contents": "required",
        "name_address": "required",
        "health_warning": "required",
        "country_of_origin": "imports_only",
        "age_statement": "conditional",
        "color_disclosure": "conditional",
        "commodity_statement": "conditional",
    },
    "malt_beverage": {
        "brand_name": "required",
        "class_type": "required",
        "net_contents": "required",
        "name_address": "required",
        "health_warning": "required",
        "alcohol_content": "conditional",
        "country_of_origin": "imports_only",
        "color_disclosure": "conditional",
        "sulfite_aspartame": "conditional",
    },
    "wine": {
        "brand_name": "required",
        "class_type": "required",
        "alcohol_content": "required",
        "net_contents": "required",
        "name_address": "required",
        "health_warning": "required",
        "country_of_origin": "imports_only",
        "appellation": "conditional",
        "foreign_wine_percentage": "conditional",
        "color_disclosure": "conditional",
        "sulfite_declaration": "conditional",
    },
}


FIELD_LABELS = {
    "brand_name": "Brand Name",
    "class_type": "Class/Type",
    "alcohol_content": "Alcohol Content",
    "net_contents": "Net Contents",
    "name_address": "Name and Address",
    "health_warning": "Government Health Warning",
    "country_of_origin": "Country of Origin",
    "age_statement": "Age Statement",
    "color_disclosure": "Color Ingredient Disclosure",
    "commodity_statement": "Commodity Statement",
    "sulfite_aspartame": "Sulfite/Aspartame Declaration",
    "appellation": "Appellation of Origin",
    "foreign_wine_percentage": "Percentage of Foreign Wine",
    "sulfite_declaration": "Sulfite Declaration",
    "fanciful_name": "Fanciful Name",
    "grape_varietal": "Grape Varietal",
}


CLASS_TYPE_TERMS = {
    "distilled_spirits": [
        "bourbon",
        "whiskey",
        "whisky",
        "vodka",
        "gin",
        "rum",
        "tequila",
        "brandy",
        "liqueur",
        "cordial",
        "distilled spirits specialty",
    ],
    "malt_beverage": [
        "beer",
        "ale",
        "lager",
        "porter",
        "stout",
        "malt beverage",
        "flavored malt beverage",
        "hard seltzer",
    ],
    "wine": [
        "wine",
        "red wine",
        "white wine",
        "rose wine",
        "rosé wine",
        "table wine",
        "grape wine",
        "cider",
        "mead",
        "sparkling wine",
    ],
}


@dataclass
class PaperworkData:
    beverage_type: str
    brand_name: str = ""
    class_type: str = ""
    alcohol_content: str = ""
    net_contents: str = ""
    name_address: str = ""
    country_of_origin: str = ""
    fanciful_name: str = ""
    grape_varietal: str = ""
    appellation: str = ""
    formula_id: str = ""
    imported: bool = False


@dataclass
class ExtractedLabel:
    raw_text: str
    fields: dict[str, str] = field(default_factory=dict)


@dataclass
class ValidationIssue:
    severity: str
    field: str
    message: str


def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def similarity(left: str, right: str) -> float:
    left_norm = normalize_text(left)
    right_norm = normalize_text(right)
    if not left_norm or not right_norm:
        return 0.0
    if left_norm in right_norm or right_norm in left_norm:
        return 1.0
    return SequenceMatcher(None, left_norm, right_norm).ratio()


def has_text(raw_text: str, expected: str, threshold: float = 0.82) -> bool:
    if not expected:
        return False
    return similarity(raw_text, expected) >= threshold or normalize_text(expected) in normalize_text(raw_text)


def first_regex(pattern: str, raw_text: str, flags: int = re.IGNORECASE) -> str:
    match = re.search(pattern, raw_text, flags)
    if not match:
        return ""
    if match.groups():
        return " ".join(group.strip() for group in match.groups() if group)
    return match.group(0).strip()


def extract_alcohol_content(raw_text: str) -> str:
    patterns = [
        r"(\d{1,2}(?:\.\d+)?)\s*%\s*(?:alc\.?/vol\.?|abv|alcohol\s+by\s+volume)",
        r"alc\.?/vol\.?\s*(\d{1,2}(?:\.\d+)?)\s*%",
        r"(\d{1,3}(?:\.\d+)?)\s*proof",
    ]
    for pattern in patterns:
        found = first_regex(pattern, raw_text)
        if found:
            return found
    return ""


def extract_net_contents(raw_text: str) -> str:
    return first_regex(r"\b(\d+(?:\.\d+)?)\s*(ml|mL|ML|l|L|liter|liters|fl\.?\s*oz\.?|ounces|pint|pints|quart|quarts|gallon|gallons)\b", raw_text)


def extract_health_warning(raw_text: str) -> str:
    text = normalize_text(raw_text)
    required_groups = [
        "government warning",
        "birth defects",
        "operate machinery",
        "health problems",
    ]
    hits = [phrase for phrase in required_groups if phrase in text]
    if len(hits) >= 3:
        return "Detected government warning key phrases"
    return ""


def extract_class_type(raw_text: str, beverage_type: str) -> str:
    text = normalize_text(raw_text)
    terms = CLASS_TYPE_TERMS.get(beverage_type, [])
    matches = [term for term in terms if normalize_text(term) in text]
    if not matches:
        return ""
    return max(matches, key=len)


def extract_country_of_origin(raw_text: str) -> str:
    patterns = [
        r"\b(?:product\s+of|produced\s+in|made\s+in|imported\s+from)\s+([A-Z][A-Za-z .'-]+)",
        r"\bcountry\s+of\s+origin[:\s]+([A-Z][A-Za-z .'-]+)",
    ]
    for pattern in patterns:
        found = first_regex(pattern, raw_text)
        if found:
            return found
    return ""


def extract_name_address(raw_text: str) -> str:
    patterns = [
        r"\b(?:bottled|distilled|produced|brewed|vinted|cellared|imported)\s+by\s+([^\n]+(?:\n[^\n]+)?)",
        r"\b(?:bottled|distilled|produced|brewed|vinted|cellared|imported)\s+for\s+([^\n]+(?:\n[^\n]+)?)",
    ]
    for pattern in patterns:
        found = first_regex(pattern, raw_text)
        if found:
            return found
    city_state = first_regex(r"([A-Z][A-Za-z .'-]+,\s*[A-Z]{2}(?:\s+\d{5})?)", raw_text)
    return city_state


def extract_declared_brand(raw_text: str) -> str:
    patterns = [
        r"brand\s+name[:\s]+([^\n]+)",
        r"^([A-Z][A-Z0-9 &'.,-]{3,})$",
    ]
    for pattern in patterns:
        found = first_regex(pattern, raw_text, flags=re.IGNORECASE | re.MULTILINE)
        if found:
            return found
    for line in raw_text.splitlines():
        cleaned = line.strip()
        if len(cleaned) >= 4 and cleaned.upper() == cleaned and not re.search(r"\d", cleaned):
            return cleaned
    return ""


def extract_label_fields(raw_text: str, beverage_type: str) -> ExtractedLabel:
    fields = {
        "brand_name": extract_declared_brand(raw_text),
        "class_type": extract_class_type(raw_text, beverage_type),
        "alcohol_content": extract_alcohol_content(raw_text),
        "net_contents": extract_net_contents(raw_text),
        "name_address": extract_name_address(raw_text),
        "health_warning": extract_health_warning(raw_text),
        "country_of_origin": extract_country_of_origin(raw_text),
    }
    if beverage_type == "wine":
        fields["sulfite_declaration"] = first_regex(r"\bcontains\s+sulfites?\b", raw_text)
        fields["appellation"] = first_regex(r"\b(?:appellation|ava)[:\s]+([^\n]+)", raw_text)
    if beverage_type == "distilled_spirits":
        fields["age_statement"] = first_regex(r"\baged\s+\d+\s+(?:years?|months?)\b", raw_text)
    return ExtractedLabel(raw_text=raw_text, fields={key: value for key, value in fields.items() if value})


def paperwork_from_mapping(values: dict[str, Any]) -> PaperworkData:
    return PaperworkData(
        beverage_type=str(values.get("beverage_type", "distilled_spirits")),
        brand_name=str(values.get("brand_name", "")).strip(),
        class_type=str(values.get("class_type", "")).strip(),
        alcohol_content=str(values.get("alcohol_content", "")).strip(),
        net_contents=str(values.get("net_contents", "")).strip(),
        name_address=str(values.get("name_address", "")).strip(),
        country_of_origin=str(values.get("country_of_origin", "")).strip(),
        fanciful_name=str(values.get("fanciful_name", "")).strip(),
        grape_varietal=str(values.get("grape_varietal", "")).strip(),
        appellation=str(values.get("appellation", "")).strip(),
        formula_id=str(values.get("formula_id", "")).strip(),
        imported=str(values.get("imported", "")).lower() in {"1", "true", "yes", "on"},
    )


def compare_expected(field: str, label_value: str, paperwork_value: str, threshold: float = 0.82) -> ValidationIssue | None:
    if not paperwork_value:
        return None
    if not label_value:
        return ValidationIssue("warning", field, f"{FIELD_LABELS[field]} was supplied in paperwork but not confidently found on label.")
    score = similarity(label_value, paperwork_value)
    if score < threshold:
        return ValidationIssue(
            "warning",
            field,
            f"{FIELD_LABELS[field]} may not match paperwork. Label: '{label_value}' Paperwork: '{paperwork_value}'",
        )
    return None


def validate_label(extracted: ExtractedLabel, paperwork: PaperworkData) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    beverage_type = paperwork.beverage_type
    rule_set = BEVERAGE_RULES.get(beverage_type, BEVERAGE_RULES["distilled_spirits"])

    for field, requirement in rule_set.items():
        if requirement == "required" and not extracted.fields.get(field):
            issues.append(ValidationIssue("fail", field, f"Missing required {FIELD_LABELS[field]}."))
        if requirement == "imports_only" and paperwork.imported and not extracted.fields.get(field):
            issues.append(ValidationIssue("fail", field, f"Missing import-required {FIELD_LABELS[field]}."))

    expected_checks = {
        "brand_name": paperwork.brand_name,
        "class_type": paperwork.class_type,
        "alcohol_content": paperwork.alcohol_content,
        "net_contents": paperwork.net_contents,
        "name_address": paperwork.name_address,
        "country_of_origin": paperwork.country_of_origin,
        "appellation": paperwork.appellation,
    }
    for field, expected_value in expected_checks.items():
        issue = compare_expected(field, extracted.fields.get(field, ""), expected_value)
        if issue:
            issues.append(issue)

    if paperwork.fanciful_name and not has_text(extracted.raw_text, paperwork.fanciful_name):
        issues.append(ValidationIssue("warning", "fanciful_name", "Fanciful name was supplied in paperwork but not found on label."))

    if paperwork.grape_varietal and not has_text(extracted.raw_text, paperwork.grape_varietal):
        issues.append(ValidationIssue("warning", "grape_varietal", "Wine grape varietal was supplied in paperwork but not found on label."))

    if beverage_type == "malt_beverage" and paperwork.alcohol_content and not extracted.fields.get("alcohol_content"):
        issues.append(ValidationIssue("fail", "alcohol_content", "Alcohol content was supplied/required but not found on malt beverage label."))

    if paperwork.formula_id:
        formula_claim_terms = ["flavor", "natural", "artificial", "specialty", "cocktail", "seltzer"]
        if any(term in normalize_text(extracted.raw_text) for term in formula_claim_terms):
            issues.append(ValidationIssue("info", "formula_id", "Formula ID supplied; reviewer should confirm formula-dependent claims."))

    return issues


def summarize_result(issues: list[ValidationIssue]) -> str:
    if any(issue.severity == "fail" for issue in issues):
        return "Needs Review - Required Items Missing"
    if any(issue.severity == "warning" for issue in issues):
        return "Needs Review - Possible Mismatch"
    return "No Issues Found"
