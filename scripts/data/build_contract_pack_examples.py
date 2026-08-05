"""Materialize reviewed precomputed packs as browser/API contract examples.

The Earth Engine reports remain in the ignored processing workspace. This
script creates the small, contract-shaped artifacts that can be reviewed and
packaged with the static browser bundle. It never recomputes imagery.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "contracts" / "examples" / "precomputed"
sys.path.insert(0, str(ROOT))

from apps.api.app.precomputed_repository import PrecomputedPackRepository


def canonical_bytes(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def build() -> dict[str, str]:
    repository = PrecomputedPackRepository(
        ROOT / "data" / "processed" / "prepublication-packs",
        ROOT / "data" / "processed" / "earth-engine-p0",
        ROOT
        / "data"
        / "metadata"
        / "boundaries"
        / "geoBoundaries-IND-ADM2-76128533"
        / "release-metadata.json",
    )
    OUTPUT.mkdir(parents=True, exist_ok=True)
    checksums: dict[str, str] = {}
    for region in repository.list_regions("district", None):
        region_id = region["id"]
        slug = region_id.replace(":", "-")
        summary = repository.get_summary(region_id)
        if summary is None:
            raise RuntimeError(f"No summary for {region_id}")
        payloads = {f"{slug}-summary.json": summary}
        for indicator_id in region["indicatorIds"]:
            detail = repository.get_indicator(region_id, indicator_id)
            if detail is None:
                raise RuntimeError(f"No {indicator_id} detail for {region_id}")
            payloads[f"{slug}-{indicator_id}.json"] = detail
        for filename, payload in payloads.items():
            content = canonical_bytes(payload)
            (OUTPUT / filename).write_bytes(content)
            checksums[filename] = hashlib.sha256(content).hexdigest()

    manifest = {
        "manifestVersion": "1",
        "generatedBy": "scripts/data/build_contract_pack_examples.py",
        "source": "data/processed/prepublication-packs/*-p0-v2.json",
        "files": [{"name": name, "sha256": checksums[name]} for name in sorted(checksums)],
    }
    (OUTPUT / "manifest.json").write_bytes(canonical_bytes(manifest))
    return checksums


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    checksums = build()
    print(f"Wrote {len(checksums)} contract examples to {OUTPUT}")


if __name__ == "__main__":
    main()
