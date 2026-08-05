from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_city_catalog import validate_city_catalog
from apps.api.reporting.jurisdiction_registry import route_jurisdiction


ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "data" / "catalog" / "supported-cities.json"


def _catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def test_city_catalog_binds_requested_set_and_packs() -> None:
    result = validate_city_catalog(CATALOG_PATH, ROOT)
    assert result == {"catalogVersion": "2026-08-05.1", "cities": 13, "validatedPacks": 2}


def test_city_catalog_has_country_codes_and_explicit_boundaries() -> None:
    cities = _catalog()["cities"]
    assert {city["slug"] for city in cities} == {
        "nagpur", "bengaluru", "mumbai", "delhi", "chennai", "bhopal",
        "new-york", "washington-dc", "tokyo", "london", "cairo", "sydney", "reykjavik",
    }
    assert all(len(city["countryCode"]) == 2 for city in cities)
    assert all(city["boundary"]["kind"] in {"validated-adm2", "catalog-envelope"} for city in cities)
    assert sum(city["boundary"]["status"] == "VALIDATED" for city in cities) == 2
    assert all(city["boundary"]["sha256"].startswith("sha256:") for city in cities)


def test_report_only_cities_use_a_safe_contract_fallback() -> None:
    report_only = [city for city in _catalog()["cities"] if city["analyticsCoverage"] == "REPORT_GENERATION_ONLY"]
    assert len(report_only) == 11
    for city in report_only:
        assert city["processingPack"]["status"] == "NOT_AVAILABLE"
        assert city["processingPack"]["files"] == {}
        assert city["processingPack"]["checksums"] == {}
        assert city["boundary"]["status"] == "CATALOG_ONLY"
        assert "not an ADM boundary" in city["boundary"]["definition"]


def test_catalog_city_routing_uses_verified_packs_or_explicit_fallback() -> None:
    nagpur = route_jurisdiction(
        country_code="IN", administrative_areas=("Maharashtra",), municipality="Nagpur",
        district="Nagpur", issue_code="WATER_BODY_SHRINKAGE",
    )
    assert nagpur["coverageState"] == "FULLY_SUPPORTED"
    assert nagpur["authorities"][0]["authorityId"] == "nmc"

    bengaluru = route_jurisdiction(
        country_code="IN", administrative_areas=("Karnataka",), municipality="Bengaluru",
        issue_code="AIR_POLLUTION",
    )
    assert bengaluru["coverageState"] == "FULLY_SUPPORTED"
    assert bengaluru["authorities"][0]["authorityId"] == "kspcb"

    new_york = route_jurisdiction(
        country_code="US", administrative_areas=("New York",), municipality="New York City",
        issue_code="WATER_POLLUTION",
    )
    assert new_york["coverageState"] == "FULLY_SUPPORTED"
    assert new_york["authorities"][0]["authorityId"] == "us-epa"

    london = route_jurisdiction(
        country_code="GB", administrative_areas=("England",), municipality="London",
        issue_code="WATER_POLLUTION",
    )
    assert london["coverageState"] == "FULLY_SUPPORTED"
    assert london["authorities"][0]["authorityId"] == "environment-agency-england"

    tokyo = route_jurisdiction(country_code="JP", administrative_areas=("Tokyo",), municipality="Tokyo", issue_code="WATER_POLLUTION")
    assert tokyo["coverageState"] == "UNSUPPORTED_JURISDICTION"
    assert tokyo["authorities"] == []
    assert tokyo["fallback"]["id"] == "GENERIC-EXPORT"
