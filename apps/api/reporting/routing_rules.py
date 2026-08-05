"""Deterministic authority routing with explicit uncertainty."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .authority_registry import AuthorityRecord, get_authority
from .jurisdiction_registry import route_jurisdiction


@dataclass(frozen=True)
class RouteDecision:
    primary: dict[str, Any] | None
    secondary: tuple[dict[str, Any], ...]
    selection_required: bool
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "primary": self.primary,
            "secondary": list(self.secondary),
            "selectionRequired": self.selection_required,
            "reason": self.reason,
        }


def route_global(
    *,
    country_code: str,
    administrative_areas: tuple[str, ...] = (),
    municipality: str | None = None,
    district: str | None = None,
    issue_code: str,
    emergency: bool = False,
) -> dict[str, Any]:
    """Route using validated jurisdiction packs.

    This is additive to the legacy Maharashtra helper below.  Existing clients
    can continue to send the frozen P0 concernCode while new clients use the
    universal location and issue-code fields.
    """
    return route_jurisdiction(
        country_code=country_code,
        administrative_areas=administrative_areas,
        municipality=municipality,
        district=district,
        issue_code=issue_code,
        emergency=emergency,
    )


def _candidate(authority_id: str, rank: int, rationale: str, confidence: str) -> dict[str, Any]:
    authority = get_authority(authority_id)
    if authority is None:
        raise ValueError(f"unknown authority: {authority_id}")
    return {
        "authorityId": authority.id,
        "name": authority.name,
        "rank": rank,
        "rationale": rationale,
        "jurisdictionConfidence": confidence,
        "officialUrl": authority.official_url,
        "manualOnly": True,
        "escalationOnly": authority.escalation_only,
    }


def route_concern(
    issue_code: str,
    *,
    region_id: str,
    municipal_confirmed: bool = False,
) -> RouteDecision:
    """Return one primary and optional secondary route.

    The function intentionally does not infer municipal jurisdiction from a
    district boundary.  A district-level coordinate must be confirmed as
    municipal before NMC can be ranked primary.
    """

    if issue_code.startswith("pollution.") or issue_code == "waste.hazardous":
        primary = _candidate("mpcb", 1, "Pollution or hazardous-waste concern matches MPCB scope.", "high")
        secondary = ()
        if issue_code in {"pollution.water", "pollution.air"} and municipal_confirmed:
            secondary = (_candidate("nmc", 2, "Municipal responsibility may also apply within confirmed NMC limits.", "medium"),)
        return RouteDecision(primary, secondary, False, "Route is based on the selected pollution issue code.")

    if issue_code.startswith("municipal."):
        if not municipal_confirmed:
            return RouteDecision(
                None,
                (_candidate("nmc", 1, "Issue matches municipal services, but municipal limits were not confirmed.", "low"),),
                True,
                "Confirm municipal jurisdiction before selecting NMC as the primary route.",
            )
        primary = _candidate("nmc", 1, "Confirmed municipal jurisdiction matches NMC civic-service scope.", "high")
        secondary = (_candidate("mpcb", 2, "MPCB may also be relevant if the municipal issue is pollution-related.", "medium"),) if issue_code in {"municipal.sewage", "municipal.lake"} else ()
        return RouteDecision(primary, secondary, False, "Route is based on confirmed municipal jurisdiction.")

    if issue_code.startswith("forest."):
        return RouteDecision(
            _candidate("maharashtra-forest", 1, "Forest, tree-felling, wildlife, or forest-encroachment scope matches the Forest Department.", "medium"),
            (_candidate("aaple-sarkar", 2, "Aaple Sarkar is an optional state grievance escalation route.", "medium"),),
            False,
            "Route is based on the selected forest issue code; the boundary is not legal cadastral evidence.",
        )

    if issue_code in {"state.grievance", "state.escalation"}:
        return RouteDecision(
            _candidate("aaple-sarkar", 1, "Selected issue is a Maharashtra state grievance or escalation.", "high"),
            (_candidate("cpgrams", 2, "CPGRAMS may be appropriate where the grievance concerns an eligible public service.", "medium"),),
            False,
            "Route is a state-grievance default; the user must confirm the department.",
        )

    if issue_code == "central.grievance":
        return RouteDecision(
            _candidate("cpgrams", 1, "Selected issue is a central/public-service grievance.", "high"),
            (),
            False,
            "Route is based on the selected central grievance issue code.",
        )

    if issue_code == "legal.escalation":
        return RouteDecision(
            None,
            (_candidate("ngt", 1, "NGT is an escalation/reference route only and is never an automatically generated legal filing.", "low"),),
            True,
            "Independent legal advice and manual selection are required.",
        )

    return RouteDecision(
        None,
        (),
        True,
        f"No deterministic route exists for issue code {issue_code!r} in region {region_id!r}.",
    )
