"""Validated, jurisdiction-agnostic reporting registry.

Packs are data, not code: adding a jurisdiction must not require changing the
report generator.  The registry deliberately exposes only a small verified
set; every other country falls back to export-only behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
import json
from pathlib import Path
import re
from typing import Any, Iterable
from urllib.parse import urlparse

REGISTRY_VERSION = "2026-08-05"
STALE_AFTER_DAYS = 365

ISSUE_CODES = frozenset({
    "AIR_POLLUTION", "WATER_POLLUTION", "SEWAGE_DISCHARGE", "INDUSTRIAL_DISCHARGE",
    "WASTE_DUMPING", "HAZARDOUS_WASTE", "TREE_CUTTING", "FOREST_CLEARING",
    "WATER_BODY_SHRINKAGE", "WATER_BODY_ENCROACHMENT", "LAND_ENCROACHMENT",
    "VEGETATION_LOSS", "WILDLIFE_HARM", "MINING_OR_QUARRYING",
    "COASTAL_OR_MARINE_DAMAGE", "OTHER_ENVIRONMENTAL_CONCERN",
})
COVERAGE_STATES = frozenset({"FULLY_SUPPORTED", "REPORT_GENERATION_ONLY", "UNSUPPORTED_JURISDICTION"})
COUNTRY_RE = re.compile(r"^[A-Z]{2}$")


@dataclass(frozen=True)
class JurisdictionRecord:
    id: str
    country_code: str
    country: str
    administrative_areas: tuple[str, ...]
    municipality: str | None
    district: str | None
    authority_id: str
    authority_name: str
    issue_codes: tuple[str, ...]
    submission_channels: tuple[str, ...]
    identity_requirements: tuple[str, ...]
    language_support: tuple[str, ...]
    emergency_instructions: str
    official_source: str
    official_url: str
    verification_status: str
    last_verification_date: str
    review_date: str
    coverage_state: str
    priority: int
    submission_adapter: str
    allowlisted_hosts: tuple[str, ...] = ()
    open311_endpoint: str | None = None

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        aliases = {
            "country_code": "countryCode", "administrative_areas": "administrativeAreas",
            "authority_id": "authorityId", "authority_name": "authorityName",
            "issue_codes": "issueCodes", "submission_channels": "submissionChannels",
            "identity_requirements": "identityRequirements",
            "language_support": "languageSupport", "emergency_instructions": "emergencyInstructions",
            "official_source": "officialSource", "official_url": "officialUrl",
            "verification_status": "verificationStatus", "last_verification_date": "lastVerificationDate",
            "review_date": "reviewDate", "coverage_state": "coverageState",
            "submission_adapter": "submissionAdapter", "allowlisted_hosts": "allowlistedHosts",
            "open311_endpoint": "open311Endpoint",
        }
        return {aliases.get(key, key): item for key, item in value.items()}


def _pack_root() -> Path:
    return Path(__file__).with_name("jurisdictions")


def _load_records() -> tuple[JurisdictionRecord, ...]:
    records: list[JurisdictionRecord] = []
    for path in sorted(_pack_root().glob("**/*.json")):
        if path.name.startswith("README"):
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for row in data.get("records", []):
            records.append(JurisdictionRecord(
                id=row["id"], country_code=row["countryCode"], country=row["country"],
                administrative_areas=tuple(row.get("administrativeAreas", [])),
                municipality=row.get("municipality"), district=row.get("district"),
                authority_id=row["authorityId"], authority_name=row["authorityName"],
                issue_codes=tuple(row["issueCodes"]),
                submission_channels=tuple(row.get("submissionChannels", [])),
                identity_requirements=tuple(row.get("identityRequirements", [])),
                language_support=tuple(row.get("languageSupport", ["en"])),
                emergency_instructions=row.get("emergencyInstructions", "If there is an immediate threat, contact local emergency services."),
                official_source=row["officialSource"], official_url=row["officialUrl"],
                verification_status=row["verificationStatus"],
                last_verification_date=row["lastVerificationDate"], review_date=row["reviewDate"],
                coverage_state=row["coverageState"], priority=int(row.get("priority", 50)),
                submission_adapter=row.get("submissionAdapter", "ManualPortalAdapter"),
                allowlisted_hosts=tuple(row.get("allowlistedHosts", [])),
                open311_endpoint=row.get("open311Endpoint"),
            ))
    return tuple(records)


def list_jurisdictions() -> list[JurisdictionRecord]:
    return list(_load_records())


def get_jurisdiction(jurisdiction_id: str) -> JurisdictionRecord | None:
    return next((record for record in _load_records() if record.id == jurisdiction_id), None)


def _matches(record: JurisdictionRecord, *, country_code: str, areas: Iterable[str], municipality: str | None, district: str | None, issue_code: str) -> bool:
    if record.country_code != country_code or issue_code not in record.issue_codes:
        return False
    requested = {item.casefold() for item in areas if item}
    configured = {item.casefold() for item in record.administrative_areas if item}
    if configured and not configured.intersection(requested):
        return False
    if record.municipality and (municipality or "").casefold() != record.municipality.casefold():
        return False
    if record.district and district and record.district.casefold() != district.casefold():
        return False
    return True


def route_jurisdiction(*, country_code: str, administrative_areas: Iterable[str] = (), municipality: str | None = None, district: str | None = None, issue_code: str, emergency: bool = False) -> dict[str, Any]:
    """Return ranked records and an explicit coverage state; never guess."""
    if country_code not in {record.country_code for record in _load_records()}:
        fallback = next(record for record in _load_records() if record.id == "GENERIC-EXPORT")
        return {"coverageState": "UNSUPPORTED_JURISDICTION", "authorities": [], "fallback": fallback.as_dict(), "selectionRequired": False, "emergency": emergency, "reason": "No verified jurisdiction pack exists for this country; export is available without guessed routing."}
    candidates = [record for record in _load_records() if _matches(record, country_code=country_code, areas=administrative_areas, municipality=municipality, district=district, issue_code=issue_code)]
    candidates.sort(key=lambda item: item.priority)
    if not candidates:
        return {"coverageState": "REPORT_GENERATION_ONLY", "authorities": [], "selectionRequired": True, "emergency": emergency, "reason": "The location is recognized but no verified authority route matches this issue and administrative area."}
    fully = [record for record in candidates if record.coverage_state == "FULLY_SUPPORTED"]
    if not fully:
        return {"coverageState": "REPORT_GENERATION_ONLY", "authorities": [], "selectionRequired": True, "emergency": emergency, "reason": "Report generation is available, but authority routing is not verified for this location."}
    authorities = [{**record.as_dict(), "rank": index, "manualOnly": True} for index, record in enumerate(fully[:3], start=1)]
    reason = "Ranked by exact municipal, state/provincial, national, and escalation scope."
    if emergency:
        reason += " SPARC is not an emergency-reporting service; use the registry emergency instructions and local emergency services."
    return {"coverageState": "FULLY_SUPPORTED", "authorities": authorities, "selectionRequired": len(authorities) > 1 and not municipality, "emergency": emergency, "reason": reason}


def validate_registry(records: Iterable[JurisdictionRecord] | None = None, *, today: date | None = None) -> list[str]:
    rows = list(records if records is not None else _load_records())
    errors: list[str] = []
    today = today or date.today()
    seen_ids: set[str] = set()
    seen_authorities: set[str] = set()
    for record in rows:
        if record.id in seen_ids:
            errors.append(f"duplicate jurisdiction id: {record.id}")
        seen_ids.add(record.id)
        if record.authority_id in seen_authorities:
            errors.append(f"duplicate authority id: {record.authority_id}")
        seen_authorities.add(record.authority_id)
        if not COUNTRY_RE.fullmatch(record.country_code): errors.append(f"invalid country code: {record.id}")
        if record.coverage_state not in COVERAGE_STATES: errors.append(f"invalid coverage state: {record.id}")
        invalid = set(record.issue_codes) - ISSUE_CODES
        if invalid: errors.append(f"invalid issue codes for {record.id}: {sorted(invalid)}")
        for field_name, value in (("officialSource", record.official_source), ("officialUrl", record.official_url)):
            parsed = urlparse(value)
            if parsed.scheme != "https" or not parsed.hostname: errors.append(f"insecure {field_name}: {record.id}")
        if record.verification_status == "VERIFIED" and not record.official_source.startswith("https://"):
            errors.append(f"verified record missing official source URL: {record.id}")
        try:
            review = date.fromisoformat(record.review_date)
            verified = date.fromisoformat(record.last_verification_date)
            if review < today: errors.append(f"stale review date: {record.id}")
            if (today - verified).days > STALE_AFTER_DAYS: errors.append(f"stale verification date: {record.id}")
        except ValueError:
            errors.append(f"invalid verification/review date: {record.id}")
        if record.open311_endpoint and urlparse(record.open311_endpoint).scheme != "https": errors.append(f"insecure Open311 URL: {record.id}")
    return errors
