"""Create a controlled label template from a blinded exploratory sample frame."""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


MAX_INPUT_BYTES = 1_000_000
EXPECTED_SAMPLE_COUNT = 100
REQUIRED_SAMPLE_COLUMNS = {"sampleId", "referenceStatus", ".geo"}
FORBIDDEN_SAMPLE_COLUMNS = {"stratum", "ndvi", "baselineClass", "comparisonClass"}
LABEL_COLUMNS = (
    "sampleId",
    "referencePeriod0Class",
    "referencePeriod1Class",
    "referenceDates",
    "referenceSourceAndLicense",
    "interpreterId",
    "interpretationScale",
    "evidenceLinks",
    "uncertainReason",
    "adjudication",
    "notes",
)


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_blinded_sample_frame(path: Path) -> list[dict[str, str]]:
    try:
        if path.stat().st_size > MAX_INPUT_BYTES:
            raise ValueError("Sample frame exceeds the 1 MiB safety limit")
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except OSError as exc:
        raise ValueError(f"Could not read sample frame: {path}") from exc
    if not rows:
        raise ValueError("Sample frame is empty")
    columns = set(rows[0])
    if missing := REQUIRED_SAMPLE_COLUMNS - columns:
        raise ValueError(f"Sample frame is missing required columns: {sorted(missing)}")
    if forbidden := FORBIDDEN_SAMPLE_COLUMNS & columns:
        raise ValueError(f"Sample frame is not blinded; forbidden columns present: {sorted(forbidden)}")
    if len(rows) != EXPECTED_SAMPLE_COUNT:
        raise ValueError(f"Sample frame must contain exactly {EXPECTED_SAMPLE_COUNT} exploratory points")
    sample_ids = {row.get("sampleId") for row in rows}
    if None in sample_ids or "" in sample_ids or len(sample_ids) != len(rows):
        raise ValueError("Sample frame sampleId values must be present and unique")
    for row in rows:
        if row.get("referenceStatus") != "UNLABELLED":
            raise ValueError("Sample frame contains a non-UNLABELLED reference status")
        try:
            geometry = json.loads(row[".geo"])
            coordinates = geometry["coordinates"]
            longitude, latitude = float(coordinates[0]), float(coordinates[1])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("Sample frame contains invalid point geometry") from exc
        if geometry.get("type") != "Point" or not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
            raise ValueError("Sample frame contains an invalid longitude/latitude point")
    return rows


def create_label_template(sample_csv: Path, output_csv: Path, metadata_json: Path) -> dict[str, Any]:
    rows = read_blinded_sample_frame(sample_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LABEL_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({"sampleId": row["sampleId"]})
    metadata = {
        "status": "EXPLORATORY_REVIEW_ONLY",
        "sampleFrame": {
            "path": sample_csv.as_posix(),
            "sha256": _sha256_file(sample_csv),
            "count": len(rows),
            "blinded": True,
        },
        "labelTemplate": {
            "path": output_csv.as_posix(),
            "columns": list(LABEL_COLUMNS),
        },
        "requiredBeforeFormalValidation": [
            "Record temporally appropriate independent reference evidence for both periods.",
            "Record a known inclusion-probability design and stratum populations.",
            "Keep annotation blinded to map class and threshold-distance evidence.",
            "Adjudicate uncertainty and compute a design-consistent error matrix with intervals.",
        ],
    }
    metadata_json.parent.mkdir(parents=True, exist_ok=True)
    metadata_json.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-csv", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--metadata-json", type=Path, required=True)
    args = parser.parse_args()
    metadata = create_label_template(args.sample_csv, args.output_csv, args.metadata_json)
    print(f"Created {metadata['status']} label template with {metadata['sampleFrame']['count']} samples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
