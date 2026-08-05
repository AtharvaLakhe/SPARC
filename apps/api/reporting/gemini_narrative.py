"""Optional Gemini narrative drafting for environmental reports.

Gemini receives only a minimized, non-identifying drafting context. Sensitive
complainant fields, exact coordinates, attachments, signature and contact data
are appended locally by SPARC after the draft returns. The deterministic local
generator remains the fallback when Gemini consent is not supplied.
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable
from urllib import error, request


DEFAULT_MODEL = "gemini-3.6-flash"


class GeminiGenerationError(RuntimeError):
    """A safe, user-facing Gemini failure without credentials or response data."""


def safe_context(payload: dict[str, Any]) -> dict[str, Any]:
    evidence = payload.get("evidence") or {}
    snapshots = payload.get("evidenceSnapshots") or []
    return {
        "reportTitle": payload.get("reportTitle") or "Environmental concern request for verification",
        "receivingAuthority": payload.get("receivingAuthority") or payload.get("concernCode"),
        "region": payload.get("regionId"),
        "administrativeAreas": payload.get("administrativeAreas", []),
        "issueCodes": payload.get("issueCodes") or [payload.get("concernCode")],
        "observation": payload.get("observation", ""),
        "evidence": evidence,
        "evidenceSnapshots": snapshots,
        "analysis": payload.get("analysis", {}),
        "limitations": [
            "Satellite-derived estimates are proxies and do not prove a violation, cause, or responsible party.",
            "The boundary is suitable for prototype analysis but is not an authoritative legal or cadastral boundary.",
        ],
    }


def _prompt(context: dict[str, Any]) -> str:
    return (
        "Draft a neutral environmental inspection request from the structured facts below. "
        "Return plain text with these headings: Environmental concern category, "
        "Personal observations, Satellite-derived findings, Data quality and limitations, "
        "Requested action. Never name a person or organization as responsible, never assert "
        "illegality, pollution, deforestation, encroachment, causation, or legal proof. "
        "Do not invent facts, numbers, dates, authorities, contacts, or events. "
        "If a fact is absent, write 'Not provided'. Keep the request concise.\n\n"
        + json.dumps(context, ensure_ascii=False, sort_keys=True)
    )


def generate_narrative(
    context: dict[str, Any],
    *,
    api_key: str | None = None,
    model: str | None = None,
    opener: Callable[..., Any] | None = None,
) -> dict[str, str]:
    key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise GeminiGenerationError("Gemini is not configured on the server.")
    selected_model = (model or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)).strip()
    if not selected_model or any(char in selected_model for char in "\r\n/ "):
        raise GeminiGenerationError("The configured Gemini model is invalid.")
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent"
    body = {
        "contents": [{"parts": [{"text": _prompt(context)}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1800},
    }
    req = request.Request(
        endpoint,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
        method="POST",
    )
    opener = opener or request.urlopen
    try:
        with opener(req, timeout=30) as response:
            raw = response.read()
    except (error.HTTPError, error.URLError, TimeoutError, OSError) as exc:
        raise GeminiGenerationError("Gemini report drafting is temporarily unavailable.") from exc
    try:
        decoded = json.loads(raw.decode("utf-8"))
        text = "\n".join(
            part.get("text", "")
            for candidate in decoded.get("candidates", [])
            for part in candidate.get("content", {}).get("parts", [])
            if isinstance(part.get("text"), str)
        ).strip()
    except (ValueError, TypeError, AttributeError) as exc:
        raise GeminiGenerationError("Gemini returned an invalid report draft.") from exc
    if not text or len(text) > 20_000:
        raise GeminiGenerationError("Gemini returned an empty or oversized report draft.")
    return {"text": text, "model": selected_model}

