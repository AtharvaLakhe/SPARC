"""Versioned, allowlisted authority records for manual portal handoff."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


REGISTRY_VERSION = "2026-08-04"


@dataclass(frozen=True)
class AuthorityRecord:
    id: str
    name: str
    jurisdiction: str
    issue_codes: tuple[str, ...]
    official_url: str
    submission_method: str
    requirements: tuple[str, ...]
    contacts: tuple[str, ...]
    escalation: tuple[str, ...]
    verification_date: str
    captcha_otp_api_notes: str
    locale_urls: tuple[str, ...] = ()
    escalation_only: bool = False

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["issueCodes"] = result.pop("issue_codes")
        result["officialUrl"] = result.pop("official_url")
        result["submissionMethod"] = result.pop("submission_method")
        result["verificationDate"] = result.pop("verification_date")
        result["captchaOtpApiNotes"] = result.pop("captcha_otp_api_notes")
        result["localeUrls"] = result.pop("locale_urls")
        result["escalationOnly"] = result.pop("escalation_only")
        return result


_AUTHORITIES: tuple[AuthorityRecord, ...] = (
    AuthorityRecord(
        id="mpcb",
        name="Maharashtra Pollution Control Board",
        jurisdiction="Maharashtra pollution regulation; regional and sub-regional offices",
        issue_codes=("pollution.air", "pollution.water", "pollution.industrial", "pollution.noise", "waste.hazardous"),
        official_url="https://www.mpcb.gov.in/en/faq",
        submission_method="manual_portal_or_regional_office",
        requirements=("review the complaint", "use the official portal or regional office route", "attach only evidence you consent to share"),
        contacts=("https://www.mpcb.gov.in/en/",),
        escalation=("Aaple Sarkar", "CPGRAMS where a central/state service escalation is appropriate"),
        verification_date="2026-08-04",
        captcha_otp_api_notes="No documented SPARC API; portal method and any CAPTCHA/OTP remain user-operated.",
        locale_urls=("https://www.mpcb.gov.in/en/faq",),
    ),
    AuthorityRecord(
        id="nmc",
        name="Nagpur Municipal Corporation",
        jurisdiction="Nagpur municipal services and civic nuisance within confirmed municipal limits",
        issue_codes=("municipal.sewage", "municipal.waste", "municipal.drain", "municipal.lake", "municipal.encroachment"),
        official_url="https://nmcnagpur.gov.in/grievance/complaint_form.php",
        submission_method="manual_portal",
        requirements=("confirm the location is within municipal limits", "mobile OTP handled by the user", "review and attach evidence manually"),
        contacts=("https://nmcnagpur.gov.in/",),
        escalation=("MPCB where the issue is also pollution-related", "Aaple Sarkar"),
        verification_date="2026-08-04",
        captcha_otp_api_notes="The portal currently begins with mobile OTP; SPARC never requests, receives, or automates the OTP.",
        locale_urls=("https://nmcnagpur.gov.in/grievance/complaint_form.php",),
    ),
    AuthorityRecord(
        id="maharashtra-forest",
        name="Maharashtra Forest Department",
        jurisdiction="Maharashtra forest land, tree-felling, wildlife, and forest-encroachment matters",
        issue_codes=("forest.land", "forest.tree_felling", "forest.wildlife", "forest.encroachment"),
        official_url="https://mahaforest.gov.in/home/index/en",
        submission_method="manual_department_route",
        requirements=("identify the relevant forest division where known", "review the neutral request", "submit through the official department channel"),
        contacts=("https://mahaforest.gov.in/fcawebsite/contactus",),
        escalation=("Aaple Sarkar", "CPGRAMS where applicable"),
        verification_date="2026-08-04",
        captcha_otp_api_notes="No SPARC API or automated submission route is approved.",
        locale_urls=("https://mahaforest.gov.in/home/index/en",),
    ),
    AuthorityRecord(
        id="aaple-sarkar",
        name="Aaple Sarkar",
        jurisdiction="Maharashtra state services and grievance escalation",
        issue_codes=("state.grievance", "state.escalation"),
        official_url="https://aaplesarkar.mahaonline.gov.in/",
        submission_method="manual_portal",
        requirements=("registered portal account where required", "review the selected department", "complete any portal verification yourself"),
        contacts=("https://aaplesarkar.mahaonline.gov.in/en/CommonForm/ContactUs",),
        escalation=("CPGRAMS for an appropriate central/public-grievance escalation",),
        verification_date="2026-08-04",
        captcha_otp_api_notes="Portal authentication and any CAPTCHA/OTP remain user-operated; SPARC stores no credentials.",
        locale_urls=("https://aaplesarkar.mahaonline.gov.in/",),
    ),
    AuthorityRecord(
        id="cpgrams",
        name="Centralized Public Grievance Redress and Monitoring System",
        jurisdiction="Central/state public-service grievance escalation where the portal accepts the matter",
        issue_codes=("central.grievance", "state.escalation"),
        official_url="https://pgportal.gov.in/",
        submission_method="manual_portal",
        requirements=("registered portal user", "review the department and wording", "use the portal's own tracking reference"),
        contacts=("https://pgportal.gov.in/Home/ContactUs",),
        escalation=("Use the portal appeal facility where available; do not treat SPARC as an appeal authority",),
        verification_date="2026-08-04",
        captcha_otp_api_notes="CPGRAMS requires registered users and does not accept grievance email; SPARC never automates login or portal controls.",
        locale_urls=("https://pgportal.gov.in/Home/LodgeGrievance",),
    ),
    AuthorityRecord(
        id="ngt",
        name="National Green Tribunal",
        jurisdiction="Legal/judicial environmental forum; escalation/reference only",
        issue_codes=("legal.escalation",),
        official_url="https://www.greentribunal.gov.in/",
        submission_method="manual_legal_route",
        requirements=("independent legal advice", "review applicable filing rules", "do not treat a SPARC package as a legal pleading"),
        contacts=("https://www.greentribunal.gov.in/",),
        escalation=(),
        verification_date="2026-08-04",
        captcha_otp_api_notes="No automated legal filing or portal integration is approved.",
        locale_urls=("https://www.greentribunal.gov.in/",),
        escalation_only=True,
    ),
)


def list_authorities() -> list[dict[str, Any]]:
    return [
        {"registryVersion": REGISTRY_VERSION, **record.as_dict()}
        for record in _AUTHORITIES
    ]


def get_authority(authority_id: str) -> AuthorityRecord | None:
    return next((record for record in _AUTHORITIES if record.id == authority_id), None)
