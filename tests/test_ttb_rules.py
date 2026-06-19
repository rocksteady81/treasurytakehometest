import unittest

from ttb_rules import extract_label_fields, paperwork_from_mapping, summarize_result, validate_label


SAMPLE_SPIRITS = """OLD TOM DISTILLERY
Kentucky Straight Bourbon Whiskey
45% Alc./Vol. (90 Proof)
750 mL
Bottled by Old Tom Distillery, Louisville, KY
GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages
during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs
your ability to drive a car or operate machinery, and may cause health problems.
"""


class TtbRuleTests(unittest.TestCase):
    def test_distilled_spirits_sample_passes_core_checks(self):
        paperwork = paperwork_from_mapping(
            {
                "beverage_type": "distilled_spirits",
                "brand_name": "OLD TOM DISTILLERY",
                "class_type": "Kentucky Straight Bourbon Whiskey",
                "alcohol_content": "45% Alc./Vol.",
                "net_contents": "750 mL",
                "name_address": "Old Tom Distillery, Louisville, KY",
            }
        )
        extracted = extract_label_fields(SAMPLE_SPIRITS, paperwork.beverage_type)
        issues = validate_label(extracted, paperwork)

        self.assertEqual(summarize_result(issues), "No Issues Found")
        self.assertIn("brand_name", extracted.fields)
        self.assertIn("health_warning", extracted.fields)

    def test_missing_health_warning_fails(self):
        paperwork = paperwork_from_mapping(
            {
                "beverage_type": "distilled_spirits",
                "brand_name": "OLD TOM DISTILLERY",
                "class_type": "Bourbon Whiskey",
                "alcohol_content": "45%",
                "net_contents": "750 mL",
            }
        )
        label_text = """OLD TOM DISTILLERY
Bourbon Whiskey
45% Alc./Vol.
750 mL
Bottled by Old Tom Distillery, Louisville, KY
"""
        extracted = extract_label_fields(label_text, paperwork.beverage_type)
        issues = validate_label(extracted, paperwork)

        self.assertTrue(any(issue.field == "health_warning" and issue.severity == "fail" for issue in issues))
        self.assertEqual(summarize_result(issues), "Needs Review - Required Items Missing")

    def test_import_requires_country_of_origin(self):
        paperwork = paperwork_from_mapping(
            {
                "beverage_type": "wine",
                "brand_name": "TEST WINE",
                "class_type": "Red Wine",
                "alcohol_content": "13%",
                "net_contents": "750 mL",
                "imported": "on",
            }
        )
        label_text = """TEST WINE
Red Wine
13% alcohol by volume
750 mL
Bottled by Example Winery, Paris
GOVERNMENT WARNING: birth defects operate machinery health problems
"""
        extracted = extract_label_fields(label_text, paperwork.beverage_type)
        issues = validate_label(extracted, paperwork)

        self.assertTrue(any(issue.field == "country_of_origin" for issue in issues))


if __name__ == "__main__":
    unittest.main()
