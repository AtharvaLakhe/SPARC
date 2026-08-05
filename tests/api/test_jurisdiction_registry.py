from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import date

from apps.api.reporting.jurisdiction_registry import list_jurisdictions, route_jurisdiction, validate_registry


class JurisdictionRegistryTests(unittest.TestCase):
    def test_packs_validate(self) -> None:
        self.assertEqual(validate_registry(), [])

    def test_nagpur_routes_to_exact_municipal_authority(self) -> None:
        route = route_jurisdiction(
            country_code="IN", administrative_areas=("Maharashtra",), district="Nagpur", municipality="Nagpur", issue_code="WATER_BODY_SHRINKAGE"
        )
        self.assertEqual(route["coverageState"], "FULLY_SUPPORTED")
        self.assertEqual(route["authorities"][0]["authorityId"], "nmc")

    def test_other_indian_state_routes_to_state_authority(self) -> None:
        route = route_jurisdiction(country_code="IN", administrative_areas=("Karnataka",), issue_code="AIR_POLLUTION")
        self.assertEqual(route["authorities"][0]["authorityId"], "kspcb")

    def test_us_and_uk_routes(self) -> None:
        self.assertEqual(route_jurisdiction(country_code="US", issue_code="AIR_POLLUTION")["authorities"][0]["authorityId"], "us-epa")
        self.assertEqual(route_jurisdiction(country_code="GB", administrative_areas=("England",), issue_code="WATER_POLLUTION")["authorities"][0]["authorityId"], "environment-agency-england")
        self.assertEqual(route_jurisdiction(country_code="GB", administrative_areas=("Northern Ireland",), issue_code="WATER_POLLUTION")["authorities"][0]["authorityId"], "daera-ni")

    def test_unsupported_is_export_only_without_guessing(self) -> None:
        route = route_jurisdiction(country_code="JP", issue_code="AIR_POLLUTION")
        self.assertEqual(route["coverageState"], "UNSUPPORTED_JURISDICTION")
        self.assertEqual(route["authorities"], [])
        self.assertEqual(route["fallback"]["submissionAdapter"], "ExportOnlyAdapter")

    def test_known_country_without_matching_issue_is_generation_only(self) -> None:
        route = route_jurisdiction(country_code="IN", administrative_areas=("Maharashtra",), issue_code="MINING_OR_QUARRYING")
        self.assertEqual(route["coverageState"], "REPORT_GENERATION_ONLY")
        self.assertTrue(route["selectionRequired"])

    def test_emergency_classification_keeps_manual_safety_boundary(self) -> None:
        route = route_jurisdiction(country_code="US", issue_code="WATER_POLLUTION", emergency=True)
        self.assertTrue(route["emergency"])
        self.assertIn("not an emergency-reporting service", route["reason"])

    def test_stale_record_is_rejected(self) -> None:
        record = list_jurisdictions()[0]
        stale = replace(record, last_verification_date="2020-01-01", review_date="2020-01-02")
        errors = validate_registry([stale], today=date(2026, 8, 5))
        self.assertTrue(any("stale" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
