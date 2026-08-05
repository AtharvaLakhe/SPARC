"""Claim-safe environmental reporting services.

The reporting package is deliberately provider- and portal-independent.  It
creates bounded evidence packages and records a user's manual handoff; it never
submits to an authority or handles government credentials.
"""

from .authority_registry import AuthorityRecord, get_authority, list_authorities
from .evidence_manifest import (
    MAX_ATTACHMENT_BYTES,
    MAX_ATTACHMENTS,
    MAX_TOTAL_ATTACHMENT_BYTES,
    build_manifest,
)
from .routing_rules import route_concern
from .jurisdiction_registry import ISSUE_CODES, COVERAGE_STATES, list_jurisdictions, route_jurisdiction, validate_registry
from .submission_adapters import ManualPortalAdapter, Open311Adapter, OfficialCustomApiAdapter, PhoneInstructionAdapter, ExportOnlyAdapter

__all__ = [
    "AuthorityRecord",
    "MAX_ATTACHMENT_BYTES",
    "MAX_ATTACHMENTS",
    "MAX_TOTAL_ATTACHMENT_BYTES",
    "build_manifest",
    "get_authority",
    "list_authorities",
    "route_concern",
    "ISSUE_CODES",
    "COVERAGE_STATES",
    "list_jurisdictions",
    "route_jurisdiction",
    "validate_registry",
    "ManualPortalAdapter",
    "Open311Adapter",
    "OfficialCustomApiAdapter",
    "PhoneInstructionAdapter",
    "ExportOnlyAdapter",
]
