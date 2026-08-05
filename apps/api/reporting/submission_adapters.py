"""Submission adapter interfaces.

Only manual handoff is active in P0.  The other adapters are deliberately
non-operational interfaces so a future provider integration must be reviewed
and documented rather than silently added to the report route.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class SubmissionAdapter(Protocol):
    name: str

    def describe(self, *, official_url: str | None = None) -> dict[str, object]: ...


@dataclass(frozen=True)
class ManualPortalAdapter:
    name: str = "ManualPortalAdapter"

    def describe(self, *, official_url: str | None = None) -> dict[str, object]:
        return {"adapter": self.name, "manualOnly": True, "officialUrl": official_url, "automated": False}


@dataclass(frozen=True)
class Open311Adapter:
    name: str = "Open311Adapter"

    def describe(self, *, official_url: str | None = None) -> dict[str, object]:
        return {"adapter": self.name, "manualOnly": False, "officialUrl": official_url, "automated": False, "availability": "verified-endpoint-required"}


class OfficialCustomApiAdapter:
    """P1 interface only; no implementation or credentials in P0."""

    name = "OfficialCustomApiAdapter"

    def describe(self, *, official_url: str | None = None) -> dict[str, object]:
        return {"adapter": self.name, "manualOnly": False, "officialUrl": official_url, "automated": False, "status": "interface-only"}


@dataclass(frozen=True)
class PhoneInstructionAdapter:
    name: str = "PhoneInstructionAdapter"

    def describe(self, *, official_url: str | None = None) -> dict[str, object]:
        return {"adapter": self.name, "manualOnly": True, "officialUrl": official_url, "automated": False}


@dataclass(frozen=True)
class ExportOnlyAdapter:
    name: str = "ExportOnlyAdapter"

    def describe(self, *, official_url: str | None = None) -> dict[str, object]:
        return {"adapter": self.name, "manualOnly": True, "officialUrl": None, "automated": False, "exportOnly": True}

