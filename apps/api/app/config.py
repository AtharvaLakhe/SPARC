"""Server-only configuration with conservative local defaults."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    repo_root: Path
    examples_root: Path
    data_mode: str
    allowed_origins: tuple[str, ...]
    max_request_bytes: int
    comparison_requests_per_minute: int

    @classmethod
    def from_environment(cls) -> "Settings":
        repo_root = Path(__file__).resolve().parents[3]
        data_mode = os.getenv("SPARC_DATA_MODE", "demo").strip().lower()
        if data_mode != "demo":
            raise RuntimeError("The first API slice supports SPARC_DATA_MODE=demo only")

        origins_value = os.getenv(
            "SPARC_ALLOWED_ORIGINS",
            "http://localhost:5173,http://localhost:8123",
        )
        origins = tuple(origin.strip() for origin in origins_value.split(",") if origin.strip())
        if not origins or "*" in origins:
            raise RuntimeError("SPARC_ALLOWED_ORIGINS must contain explicit origins")

        max_request_bytes = _bounded_int("SPARC_MAX_REQUEST_BYTES", 65_536, 1_024, 1_048_576)
        requests_per_minute = _bounded_int(
            "SPARC_COMPARISON_REQUESTS_PER_MINUTE", 60, 1, 10_000
        )
        return cls(
            repo_root=repo_root,
            examples_root=repo_root / "contracts" / "examples",
            data_mode=data_mode,
            allowed_origins=origins,
            max_request_bytes=max_request_bytes,
            comparison_requests_per_minute=requests_per_minute,
        )


def _bounded_int(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if not minimum <= value <= maximum:
        raise RuntimeError(f"{name} must be between {minimum} and {maximum}")
    return value

