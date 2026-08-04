"""Preregistration gate for the Nagpur vegetation probability validation sample.

This module is a *gate*, not a generator. It exists to make one failure mode
impossible: drawing a formal accuracy sample whose design was decided, adjusted,
or reconstructed after somebody had already seen the map.

`docs/validation-plan.md` requires a probability sample with a recorded
inclusion probability for every unit, and states plainly:

    do not invent one universal sample count. Calculate allocation after the
    discovery map reveals stratum areas and expected precision. Record the
    calculation, finite population, design, replacement policy, seed, and
    inclusion probability.

So the plan must be complete *before* the draw, and this module refuses every
incomplete plan rather than filling a gap with a default. There is deliberately
no fallback allocation anywhere in this file. The existing exploratory frames
use 25 points per stratum and are labelled `EXPLORATORY_REVIEW_ONLY`; promoting
that number here would turn a debugging exercise into an apparent probability
design, which is the exact substitution the validation plan forbids.

Two outputs are produced, and they are separate on purpose:

  * a **blinded reviewer CSV** — sample id and geometry only. A reviewer who can
    see the mapped stratum is no longer an independent reference; anchoring is
    not something a careful person can switch off by intending to.
  * a **restricted design-linkage CSV** — sample id, stratum, population, sample
    size and inclusion probability. This is what the estimator needs and what
    the reviewer must not have.

Usage:
    python -m scripts.data.create_probability_validation_plan validate PLAN.json
        --ledger LEDGER.csv --boundary-gate GATE.json

    python -m scripts.data.create_probability_validation_plan export PLAN.json
        --ledger LEDGER.csv --boundary-gate GATE.json
        --frame FRAME.csv --out-dir DIR [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass, field
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
from typing import Any

PLAN_STATUS_PREREGISTERED = "PREREGISTERED"
PLAN_STATUS_BLOCKED = "BLOCKED_PENDING_SCIENTIFIC_DECISION"

REPLACEMENT_POLICIES = {"WITH_REPLACEMENT", "WITHOUT_REPLACEMENT"}

EXPECTED_STRATA = (
    "stable_non_target",
    "stable_target",
    "mapped_gain",
    "mapped_loss",
)

#: Columns the blinded reviewer file may contain. Anything else leaks the map.
BLINDED_COLUMNS = ("sampleId", "longitude", "latitude", "referenceStatus")

#: Columns that must never reach a reviewer.
FORBIDDEN_IN_BLINDED = (
    "mappedStratum",
    "stratumId",
    "mappedClass",
    "class",
    "score",
    "confidence",
    "thresholdDistance",
    "inclusionProbability",
    "populationPixels",
    "sampleSize",
)

RESTRICTED_COLUMNS = (
    "sampleId",
    "mappedStratum",
    "populationPixels",
    "sampleSize",
    "inclusionProbability",
)

MAX_INPUT_BYTES = 8 * 1024 * 1024


class PreregistrationError(ValueError):
    """A plan, ledger or frame failed the preregistration gate."""


@dataclass
class StratumPlan:
    stratum_id: str
    population_pixels: int
    sample_size: int
    inclusion_probability: Fraction

    def as_record(self) -> dict[str, Any]:
        return {
            "stratumId": self.stratum_id,
            "populationPixels": self.population_pixels,
            "sampleSize": self.sample_size,
            # Recorded as an exact rational string. A float cannot represent
            # n/N exactly for these population sizes, and an estimator that
            # silently rounds the inclusion probability produces a biased
            # area estimate that nothing downstream would flag.
            "inclusionProbability": f"{self.inclusion_probability.numerator}/"
                                    f"{self.inclusion_probability.denominator}",
            "inclusionProbabilityDecimal": float(self.inclusion_probability),
        }


@dataclass
class ValidatedPlan:
    region_id: str
    indicator_id: str
    method_id: str
    method_version: str
    boundary_sha256: str
    raw_csv_sha256: str
    replacement_policy: str
    random_seed: int
    target_precision: dict[str, Any]
    strata: list[StratumPlan]
    bindings: list[str] = field(default_factory=list)

    @property
    def total_sample_size(self) -> int:
        return sum(s.sample_size for s in self.strata)


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise PreregistrationError(f"File does not exist: {path}")
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise PreregistrationError(f"File exceeds the {MAX_INPUT_BYTES} byte safety limit: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PreregistrationError(f"Could not parse JSON: {path}") from exc


def _require(value: Any, label: str) -> Any:
    """Reject null/empty rather than substituting anything."""
    if value is None:
        raise PreregistrationError(
            f"Plan field '{label}' is null. This is a scientific decision and "
            f"will not be defaulted; record it and preregister again."
        )
    if isinstance(value, str) and not value.strip():
        raise PreregistrationError(f"Plan field '{label}' is empty.")
    return value


def _require_positive_int(value: Any, label: str) -> int:
    _require(value, label)
    if isinstance(value, bool) or not isinstance(value, int):
        raise PreregistrationError(f"Plan field '{label}' must be an integer, got {value!r}.")
    if value <= 0:
        raise PreregistrationError(f"Plan field '{label}' must be positive, got {value}.")
    return value


def read_population_ledger(path: Path) -> dict[str, int]:
    """Finite population per stratum, from the imported v2 ledger CSV.

    Fractional totals are rejected outright: the v1 export was withdrawn for
    exactly that reason. A pixel count is a count, and a fractional one means a
    weighted histogram was summed where a population was intended.
    """
    if not path.is_file():
        raise PreregistrationError(f"Population ledger does not exist: {path}")
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise PreregistrationError("Population ledger exceeds the safety limit")

    populations: dict[str, int] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise PreregistrationError("Population ledger is empty")
        missing = {"stratumId", "populationPixels"} - set(reader.fieldnames)
        if missing:
            raise PreregistrationError(
                f"Population ledger is missing required columns: {sorted(missing)}"
            )
        for row in reader:
            stratum = (row.get("stratumId") or "").strip()
            raw = (row.get("populationPixels") or "").strip()
            if not stratum:
                raise PreregistrationError("Population ledger contains a blank stratumId")
            if stratum in populations:
                raise PreregistrationError(f"Population ledger repeats stratum '{stratum}'")
            try:
                value = Fraction(raw)
            except (ValueError, ZeroDivisionError) as exc:
                raise PreregistrationError(
                    f"Population ledger has a non-numeric population for '{stratum}': {raw!r}"
                ) from exc
            if value.denominator != 1:
                raise PreregistrationError(
                    f"Population ledger has a fractional population for '{stratum}': {raw}. "
                    "A finite population must be a whole pixel count; this is the v1 defect."
                )
            if value <= 0:
                raise PreregistrationError(
                    f"Population ledger has a non-positive population for '{stratum}': {raw}"
                )
            populations[stratum] = int(value)

    if not populations:
        raise PreregistrationError("Population ledger contains no strata")
    return populations


def validate_plan(
    plan: dict[str, Any],
    *,
    ledger_populations: dict[str, int],
    ledger_sha256: str,
    boundary_sha256: str,
) -> ValidatedPlan:
    """Bind the plan to its evidence, or refuse.

    Every binding below is a way the design could silently drift from the data
    it claims to describe. Checking them here is cheap; discovering afterwards
    that a sample was drawn against a superseded boundary is not recoverable
    without redrawing.
    """
    bindings: list[str] = []

    status = plan.get("planStatus")
    if status != PLAN_STATUS_PREREGISTERED:
        raise PreregistrationError(
            f"Plan status is {status!r}, not {PLAN_STATUS_PREREGISTERED!r}. "
            "An un-preregistered plan cannot authorise a formal sample."
        )
    bindings.append("planStatus == PREREGISTERED")

    region = plan.get("region") or {}
    indicator = plan.get("indicator") or {}
    ledger_block = plan.get("ledger") or {}
    design = plan.get("design") or {}

    region_id = _require(region.get("regionId"), "region.regionId")
    indicator_id = _require(indicator.get("indicatorId"), "indicator.indicatorId")
    method_id = _require(indicator.get("methodId"), "indicator.methodId")
    method_version = _require(indicator.get("methodVersion"), "indicator.methodVersion")
    bindings += ["region.regionId", "indicator.indicatorId",
                 "indicator.methodId", "indicator.methodVersion"]

    plan_boundary = _require(region.get("boundarySha256"), "region.boundarySha256")
    if plan_boundary != boundary_sha256:
        raise PreregistrationError(
            "Plan boundary checksum does not match the boundary gate record. "
            f"plan={plan_boundary} gate={boundary_sha256}"
        )
    bindings.append("region.boundarySha256 == boundary gate sha256")

    plan_csv = _require(ledger_block.get("rawCsvSha256"), "ledger.rawCsvSha256")
    if plan_csv != ledger_sha256:
        raise PreregistrationError(
            "Plan raw CSV checksum does not match the imported ledger. "
            f"plan={plan_csv} ledger={ledger_sha256}"
        )
    bindings.append("ledger.rawCsvSha256 == imported ledger sha256")

    replacement = _require(design.get("replacementPolicy"), "design.replacementPolicy")
    if replacement not in REPLACEMENT_POLICIES:
        raise PreregistrationError(
            f"design.replacementPolicy must be one of {sorted(REPLACEMENT_POLICIES)}, "
            f"got {replacement!r}."
        )
    bindings.append("design.replacementPolicy")

    seed = design.get("randomSeed")
    _require(seed, "design.randomSeed")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise PreregistrationError(f"design.randomSeed must be an integer, got {seed!r}.")
    bindings.append("design.randomSeed")

    precision = design.get("targetPrecision") or {}
    for key in ("metric", "targetStandardError", "confidenceLevel"):
        _require(precision.get(key), f"design.targetPrecision.{key}")
    _require(design.get("allocationRationale"), "design.allocationRationale")
    bindings += ["design.targetPrecision", "design.allocationRationale"]

    raw_strata = plan.get("strata")
    if not isinstance(raw_strata, list) or not raw_strata:
        raise PreregistrationError("Plan contains no strata")

    seen: set[str] = set()
    strata: list[StratumPlan] = []
    for entry in raw_strata:
        stratum_id = _require(entry.get("stratumId"), "strata[].stratumId")
        if stratum_id in seen:
            raise PreregistrationError(f"Plan repeats stratum '{stratum_id}'")
        seen.add(stratum_id)

        if stratum_id not in ledger_populations:
            raise PreregistrationError(
                f"Plan stratum '{stratum_id}' is absent from the imported ledger"
            )

        population = _require_positive_int(
            entry.get("populationPixels"), f"strata[{stratum_id}].populationPixels"
        )
        if population != ledger_populations[stratum_id]:
            raise PreregistrationError(
                f"Plan population for '{stratum_id}' does not match the imported ledger. "
                f"plan={population} ledger={ledger_populations[stratum_id]}"
            )

        sample_size = _require_positive_int(
            entry.get("sampleSize"), f"strata[{stratum_id}].sampleSize"
        )
        if replacement == "WITHOUT_REPLACEMENT" and sample_size > population:
            raise PreregistrationError(
                f"Stratum '{stratum_id}' draws {sample_size} without replacement from a "
                f"population of {population}."
            )

        # Exact rational. Comparing floats here would accept a plan whose
        # recorded probability is merely close, and "close" is a bias.
        expected = Fraction(sample_size, population)
        declared = entry.get("inclusionProbability")
        if declared is not None:
            try:
                declared_fraction = Fraction(str(declared))
            except (ValueError, ZeroDivisionError) as exc:
                raise PreregistrationError(
                    f"Stratum '{stratum_id}' has an unreadable inclusionProbability: {declared!r}"
                ) from exc
            if declared_fraction != expected:
                raise PreregistrationError(
                    f"Stratum '{stratum_id}' inclusion probability {declared!r} is not exactly "
                    f"sampleSize/populationPixels ({expected.numerator}/{expected.denominator})."
                )

        strata.append(StratumPlan(stratum_id, population, sample_size, expected))

    missing_strata = set(ledger_populations) - seen
    if missing_strata:
        raise PreregistrationError(
            f"Plan omits strata present in the ledger: {sorted(missing_strata)}. "
            "A partial design cannot produce a design-consistent estimate."
        )
    bindings += ["finite population counts == ledger",
                 "sample sizes present and valid",
                 "inclusion probability == sampleSize/populationPixels (exact)"]

    return ValidatedPlan(
        region_id=region_id,
        indicator_id=indicator_id,
        method_id=method_id,
        method_version=method_version,
        boundary_sha256=boundary_sha256,
        raw_csv_sha256=ledger_sha256,
        replacement_policy=replacement,
        random_seed=seed,
        target_precision=dict(precision),
        strata=strata,
        bindings=bindings,
    )


def read_candidate_frame(path: Path) -> list[dict[str, str]]:
    """Frame of candidate units, each already assigned to a mapped stratum."""
    if not path.is_file():
        raise PreregistrationError(f"Sample frame does not exist: {path}")
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise PreregistrationError("Sample frame exceeds the safety limit")
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise PreregistrationError("Sample frame is empty")
    required = {"sampleId", "longitude", "latitude", "mappedStratum"}
    missing = required - set(rows[0].keys())
    if missing:
        raise PreregistrationError(f"Sample frame is missing columns: {sorted(missing)}")
    ids = [r["sampleId"] for r in rows]
    if len(set(ids)) != len(ids) or not all(ids):
        raise PreregistrationError("Sample frame sampleId values must be present and unique")
    return rows


def export_formal_sample(
    validated: ValidatedPlan,
    frame_rows: list[dict[str, str]],
    out_dir: Path,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Write the blinded reviewer file and the restricted design-linkage file.

    Only reachable with a plan that already passed `validate_plan`, so the
    checks here are about the frame agreeing with that plan.
    """
    by_stratum: dict[str, list[dict[str, str]]] = {}
    for row in frame_rows:
        by_stratum.setdefault((row.get("mappedStratum") or "").strip(), []).append(row)

    for stratum in validated.strata:
        available = len(by_stratum.get(stratum.stratum_id, []))
        if available < stratum.sample_size:
            raise PreregistrationError(
                f"Frame holds {available} units for '{stratum.stratum_id}' but the plan "
                f"requires {stratum.sample_size}."
            )

    blinded: list[dict[str, str]] = []
    linkage: list[dict[str, Any]] = []
    for stratum in validated.strata:
        for row in by_stratum[stratum.stratum_id][: stratum.sample_size]:
            blinded.append({
                "sampleId": row["sampleId"],
                "longitude": row["longitude"],
                "latitude": row["latitude"],
                # The reviewer records a label; they are never shown ours.
                "referenceStatus": "UNLABELLED",
            })
            record = stratum.as_record()
            linkage.append({
                "sampleId": row["sampleId"],
                "mappedStratum": stratum.stratum_id,
                "populationPixels": stratum.population_pixels,
                "sampleSize": stratum.sample_size,
                "inclusionProbability": record["inclusionProbability"],
            })

    # Belt and braces: prove the blinded file cannot carry a forbidden field
    # before it is written, not after somebody has already opened it.
    for row in blinded:
        leaked = set(row) & set(FORBIDDEN_IN_BLINDED)
        if leaked:
            raise PreregistrationError(f"Blinded output would leak columns: {sorted(leaked)}")

    summary: dict[str, Any] = {
        "status": "DRY_RUN" if dry_run else "WRITTEN",
        "regionId": validated.region_id,
        "indicatorId": validated.indicator_id,
        "methodId": validated.method_id,
        "methodVersion": validated.method_version,
        "boundarySha256": validated.boundary_sha256,
        "rawCsvSha256": validated.raw_csv_sha256,
        "replacementPolicy": validated.replacement_policy,
        "randomSeed": validated.random_seed,
        "totalSampleSize": validated.total_sample_size,
        "strata": [s.as_record() for s in validated.strata],
        "bindingsVerified": validated.bindings,
        "blindedRows": len(blinded),
        "linkageRows": len(linkage),
    }

    if dry_run:
        return summary

    out_dir.mkdir(parents=True, exist_ok=True)
    blinded_path = out_dir / "nagpur-vegetation-formal-sample.blinded.csv"
    linkage_path = out_dir / "nagpur-vegetation-formal-sample.design-linkage.RESTRICTED.csv"

    for path, columns, rows in (
        (blinded_path, BLINDED_COLUMNS, blinded),
        (linkage_path, RESTRICTED_COLUMNS, linkage),
    ):
        if path.exists():
            raise PreregistrationError(
                f"Refusing to overwrite an existing sample export: {path}"
            )
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(columns))
            writer.writeheader()
            writer.writerows(rows)

    summary["blindedCsv"] = str(blinded_path)
    summary["blindedCsvSha256"] = _sha256_file(blinded_path)
    summary["designLinkageCsv"] = str(linkage_path)
    summary["designLinkageCsvSha256"] = _sha256_file(linkage_path)
    return summary


def _load_boundary_sha(path: Path) -> str:
    gate = _read_json(path)
    boundary = gate.get("boundary") or {}
    value = boundary.get("sha256")
    if not value:
        raise PreregistrationError(f"Boundary gate record has no boundary.sha256: {path}")
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("validate", "export"):
        p = sub.add_parser(name)
        p.add_argument("plan", type=Path)
        p.add_argument("--ledger", type=Path, required=True)
        p.add_argument("--boundary-gate", type=Path, required=True)
        if name == "export":
            p.add_argument("--frame", type=Path, required=True)
            p.add_argument("--out-dir", type=Path, required=True)
            p.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    try:
        plan = _read_json(args.plan)
        populations = read_population_ledger(args.ledger)
        validated = validate_plan(
            plan,
            ledger_populations=populations,
            ledger_sha256=_sha256_file(args.ledger),
            boundary_sha256=_load_boundary_sha(args.boundary_gate),
        )
        if args.command == "validate":
            print(json.dumps({
                "status": "PREREGISTRATION_VALID",
                "totalSampleSize": validated.total_sample_size,
                "bindingsVerified": validated.bindings,
                "strata": [s.as_record() for s in validated.strata],
            }, indent=2))
            return 0

        summary = export_formal_sample(
            validated,
            read_candidate_frame(args.frame),
            args.out_dir,
            dry_run=args.dry_run,
        )
        print(json.dumps(summary, indent=2))
        return 0
    except PreregistrationError as exc:
        print(json.dumps({"status": "REFUSED", "reason": str(exc)}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
