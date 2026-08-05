"""Validate jurisdiction packs before they are shipped.

Usage: python scripts/data/validate_jurisdiction_registry.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from apps.api.reporting.jurisdiction_registry import validate_registry


def main() -> int:
    errors = validate_registry()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("jurisdiction registry: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
