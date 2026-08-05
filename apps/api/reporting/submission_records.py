"""Ephemeral report, handoff, and acknowledgement records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import shutil
import secrets
from typing import Any


RETENTION_HOURS = 24


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


@dataclass
class ReportRecord:
    report_id: str
    access_token: str
    payload: dict[str, Any]
    created_at: datetime = field(default_factory=now_utc)
    last_access_at: datetime = field(default_factory=now_utc)
    status: str = "READY_FOR_DOWNLOAD"
    handoff: dict[str, Any] | None = None
    acknowledgement: dict[str, Any] | None = None
    artifacts: dict[str, bytes] = field(default_factory=dict, repr=False)
    manifest: dict[str, Any] | None = None
    workspace_dir: Path | None = field(default=None, repr=False)

    @property
    def expires_at(self) -> datetime:
        return self.last_access_at + timedelta(hours=RETENTION_HOURS)

    def expired(self, at: datetime | None = None) -> bool:
        return (at or now_utc()) >= self.expires_at

    def public(self) -> dict[str, Any]:
        report_payload = dict(self.payload)
        eligibility = report_payload.pop("eligibility", None)
        authority_routes = report_payload.pop("authorityRoutes", None)
        artifacts = report_payload.pop("artifacts", None)
        coverage_state = report_payload.pop("coverageState", "FULLY_SUPPORTED")
        jurisdiction_routing = report_payload.pop("jurisdictionRouting", None)
        return {
            "id": self.report_id,
            "status": "EXPIRED" if self.expired() else self.status,
            "createdAt": self.created_at.isoformat().replace("+00:00", "Z"),
            "expiresAt": self.expires_at.isoformat().replace("+00:00", "Z"),
            "payload": report_payload,
            "eligibility": eligibility,
            "authorityRoutes": authority_routes,
            "coverageState": coverage_state,
            "jurisdictionRouting": jurisdiction_routing,
            "artifacts": artifacts,
            "handoff": self.handoff,
            "acknowledgement": self.acknowledgement,
        }


class EphemeralReportStore:
    """Private, process-local P0 store with per-report temporary directories."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self._records: dict[str, ReportRecord] = {}
        configured = workspace or os.getenv("SPARC_REPORT_WORKSPACE", "data/cache/reporting")
        self._workspace = Path(configured).resolve()
        self._workspace.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _write_artifacts(record: ReportRecord) -> None:
        if record.workspace_dir is None:
            return
        for artifact_id, data in record.artifacts.items():
            target = record.workspace_dir / artifact_id
            target.write_bytes(data)

    @staticmethod
    def _remove_workspace(record: ReportRecord) -> None:
        if record.workspace_dir is not None:
            shutil.rmtree(record.workspace_dir, ignore_errors=True)

    def create(
        self,
        payload: dict[str, Any],
        *,
        artifacts: dict[str, bytes] | None = None,
        manifest: dict[str, Any] | None = None,
    ) -> ReportRecord:
        report_id = f"report:{secrets.token_hex(16)}"
        token = secrets.token_urlsafe(32)
        record = ReportRecord(
            report_id=report_id,
            access_token=token,
            payload=payload,
            artifacts=artifacts or {},
            manifest=manifest,
            workspace_dir=self._workspace / secrets.token_hex(16),
        )
        record.workspace_dir.mkdir()
        self._write_artifacts(record)
        self._records[report_id] = record
        return record

    def replace_artifacts(self, record: ReportRecord, artifacts: dict[str, bytes]) -> None:
        self._remove_workspace(record)
        record.artifacts = artifacts
        record.workspace_dir = self._workspace / secrets.token_hex(16)
        record.workspace_dir.mkdir()
        self._write_artifacts(record)

    def get(self, report_id: str, token: str) -> ReportRecord | None:
        record = self._records.get(report_id)
        if record is None or not secrets.compare_digest(record.access_token, token):
            return None
        if record.expired():
            self._records.pop(report_id, None)
            self._remove_workspace(record)
            return record
        record.last_access_at = now_utc()
        return record

    def delete(self, report_id: str, token: str) -> bool:
        record = self._records.get(report_id)
        if record is None or not secrets.compare_digest(record.access_token, token):
            return False
        self._records.pop(report_id, None)
        self._remove_workspace(record)
        return True

    def purge_expired(self) -> int:
        expired = [report_id for report_id, record in self._records.items() if record.expired()]
        for report_id in expired:
            record = self._records.pop(report_id, None)
            if record is not None:
                self._remove_workspace(record)
        return len(expired)

    def record_handoff(self, record: ReportRecord, authority: dict[str, Any]) -> None:
        record.handoff = {
            "authorityId": authority["authorityId"],
            "officialUrl": authority["officialUrl"],
            "openedAt": now_utc().isoformat().replace("+00:00", "Z"),
            "manualOnly": True,
        }
        record.status = "HANDOFF_RECORDED"

    def record_acknowledgement(self, record: ReportRecord, acknowledgement: dict[str, Any]) -> None:
        record.acknowledgement = acknowledgement
        record.status = "ACKNOWLEDGED"
