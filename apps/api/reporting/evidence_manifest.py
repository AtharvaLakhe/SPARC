"""Bounded evidence files and canonical SHA-256 manifests."""

from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import json
from pathlib import PurePosixPath
import re
from typing import Any, Iterable


MAX_ATTACHMENTS = 6
MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024
MAX_TOTAL_ATTACHMENT_BYTES = 20 * 1024 * 1024
MAX_ZIP_BYTES = 25 * 1024 * 1024
MAX_USER_TEXT = 4_000
ALLOWED_MEDIA_TYPES = frozenset({"image/jpeg", "image/png", "application/pdf"})
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")


class EvidenceManifestError(ValueError):
    """A report file or manifest violates a safety/integrity rule."""


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return f"sha256:{sha256(value).hexdigest()}"


def sanitize_filename(name: str, *, fallback: str = "attachment") -> str:
    candidate = PurePosixPath(str(name).replace("\\", "/")).name
    candidate = re.sub(r"[^A-Za-z0-9._-]", "-", candidate)[:120].strip(".")
    if not candidate or candidate in {".", ".."} or not SAFE_NAME.fullmatch(candidate):
        return fallback
    return candidate


def validate_attachment(media_type: str, payload: bytes, name: str) -> dict[str, Any]:
    if media_type not in ALLOWED_MEDIA_TYPES:
        raise EvidenceManifestError("unsupported attachment media type")
    if not payload or len(payload) > MAX_ATTACHMENT_BYTES:
        raise EvidenceManifestError("attachment exceeds the 5 MiB limit or is empty")
    raw_name = str(name).replace("\\", "/")
    if "/" in raw_name or ".." in PurePosixPath(raw_name).parts or any(ord(char) < 32 for char in raw_name):
        raise EvidenceManifestError("attachment filename contains a path or control character")
    safe_name = sanitize_filename(name)
    if safe_name == "attachment" and name not in {"attachment", ""}:
        raise EvidenceManifestError("attachment filename is unsafe")
    return {
        "name": safe_name,
        "mediaType": media_type,
        "bytes": len(payload),
        "sha256": sha256_bytes(payload),
    }


def normalize_attachment(media_type: str, payload: bytes) -> bytes:
    """Strip image metadata and reject oversized pixel dimensions.

    PDF bytes are retained as supplied but are still bounded by
    :func:`validate_attachment`.  Image normalization is intentionally done
    before hashing so the manifest represents exactly what is redistributed.
    """

    if media_type == "application/pdf":
        if not payload.startswith(b"%PDF-"):
            raise EvidenceManifestError("attachment is not a valid PDF")
        return payload
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - dependency installation failure
        raise EvidenceManifestError("Pillow is required for image metadata stripping") from exc
    try:
        with Image.open(BytesIO(payload)) as image:
            expected_format = {"image/jpeg": "JPEG", "image/png": "PNG"}.get(media_type)
            if image.format != expected_format:
                raise EvidenceManifestError("attachment content does not match its media type")
            if image.width > 8192 or image.height > 8192:
                raise EvidenceManifestError("image dimensions exceed the 8192-pixel limit")
            output = BytesIO()
            if media_type == "image/jpeg":
                image.convert("RGB").save(output, format="JPEG", quality=95, optimize=False, exif=b"")
            else:
                image.save(output, format="PNG", optimize=False)
            return output.getvalue()
    except EvidenceManifestError:
        raise
    except Exception as exc:
        raise EvidenceManifestError("attachment is not a valid image") from exc


def build_manifest(
    *,
    report_id: str,
    provenance: dict[str, Any],
    files: Iterable[tuple[str, str, bytes]],
) -> dict[str, Any]:
    entries = []
    seen: set[str] = set()
    total = 0
    for path, media_type, payload in files:
        safe_path = str(PurePosixPath(path))
        if safe_path.startswith("/") or ".." in PurePosixPath(safe_path).parts:
            raise EvidenceManifestError("manifest path traversal is not allowed")
        if safe_path in seen:
            raise EvidenceManifestError("manifest contains duplicate paths")
        if not payload:
            raise EvidenceManifestError(f"manifest file is empty: {safe_path}")
        seen.add(safe_path)
        total += len(payload)
        entries.append({
            "path": safe_path,
            "mediaType": media_type,
            "bytes": len(payload),
            "sha256": sha256_bytes(payload),
        })
    entries.sort(key=lambda entry: entry["path"])
    return {
        "schemaVersion": "1.0.0",
        "reportId": report_id,
        "generatedBy": "sparc-reporting-p0",
        "totalBytes": total,
        "files": entries,
        "provenance": provenance,
    }


def verify_manifest(manifest: dict[str, Any], files: dict[str, bytes]) -> None:
    expected = {entry["path"]: entry for entry in manifest.get("files", [])}
    if set(expected) != set(files):
        raise EvidenceManifestError("manifest files do not match the supplied files")
    for path, payload in files.items():
        entry = expected[path]
        if entry["bytes"] != len(payload) or entry["sha256"] != sha256_bytes(payload):
            raise EvidenceManifestError(f"manifest checksum mismatch for {path}")
