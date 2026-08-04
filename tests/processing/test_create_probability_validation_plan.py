"""Rejection tests for the preregistration gate.

The gate's whole value is what it refuses, so most of these assert a refusal.
A gate that only has happy-path tests is a gate nobody has checked.

Populations are the imported Nagpur vegetation v2 ledger figures.
"""

from __future__ import annotations

import csv
import json
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.data.create_probability_validation_plan import (
    PLAN_STATUS_BLOCKED,
    PLAN_STATUS_PREREGISTERED,
    PreregistrationError,
    export_formal_sample,
    read_candidate_frame,
    read_population_ledger,
    validate_plan,
)

POPULATIONS = {
    "stable_non_target": 7_371_132,
    "stable_target": 82_372_144,
    "mapped_gain": 3_350_162,
    "mapped_loss": 6_124_575,
}

LEDGER_SHA = "ea1000f8ed4d389c77c3e1231ed1e465495b3853e9968e38982643dd8f7a0386"
BOUNDARY_SHA = "f811022adbe26c7634ba4d884db3251c53bd2d23b8d55e18f6d24fe3cb3b2b33"

# Illustrative sample sizes for tests only. These are NOT a proposed allocation:
# the real ones are a blocked scientific decision (docs/validation-plan.md).
TEST_SAMPLE_SIZES = {
    "stable_non_target": 120,
    "stable_target": 400,
    "mapped_gain": 90,
    "mapped_loss": 110,
}


def _plan() -> dict:
    return {
        "planStatus": PLAN_STATUS_PREREGISTERED,
        "region": {"regionId": "gbopen:district:nagpur", "boundarySha256": BOUNDARY_SHA},
        "indicator": {
            "indicatorId": "vegetation",
            "methodId": "ndvi-green-cover",
            "methodVersion": "2.0.0",
        },
        "ledger": {"rawCsvSha256": LEDGER_SHA},
        "design": {
            "samplingDesign": "STRATIFIED_RANDOM",
            "replacementPolicy": "WITHOUT_REPLACEMENT",
            "randomSeed": 20260804,
            "targetPrecision": {
                "metric": "overall_accuracy",
                "targetStandardError": 0.02,
                "confidenceLevel": 0.95,
            },
            "allocationRationale": "Illustrative allocation for unit tests only.",
        },
        "strata": [
            {
                "stratumId": key,
                "populationPixels": POPULATIONS[key],
                "sampleSize": TEST_SAMPLE_SIZES[key],
                "inclusionProbability": None,
            }
            for key in POPULATIONS
        ],
    }


def _validate(plan: dict, **overrides):
    kwargs = {
        "ledger_populations": POPULATIONS,
        "ledger_sha256": LEDGER_SHA,
        "boundary_sha256": BOUNDARY_SHA,
    }
    kwargs.update(overrides)
    return validate_plan(plan, **kwargs)


# ── acceptance ───────────────────────────────────────────────────────────────

def test_complete_plan_validates_and_binds_every_required_field():
    validated = _validate(_plan())
    joined = " ".join(validated.bindings)
    for expected in (
        "planStatus", "region.regionId", "indicator.methodId", "indicator.methodVersion",
        "boundary gate sha256", "imported ledger sha256", "replacementPolicy",
        "randomSeed", "targetPrecision", "finite population counts",
        "sample sizes", "inclusion probability",
    ):
        assert expected in joined, f"binding not recorded: {expected}"
    assert validated.total_sample_size == sum(TEST_SAMPLE_SIZES.values())


def test_inclusion_probability_is_exact_not_rounded():
    validated = _validate(_plan())
    target = next(s for s in validated.strata if s.stratum_id == "stable_target")
    # 400 / 82,372,144 has no exact float representation; the gate keeps it rational.
    assert target.inclusion_probability.numerator == 25
    assert target.inclusion_probability.denominator == 5_148_259
    assert target.as_record()["inclusionProbability"] == "25/5148259"


# ── refusals ─────────────────────────────────────────────────────────────────

def test_refuses_plan_that_is_not_preregistered():
    plan = _plan()
    plan["planStatus"] = PLAN_STATUS_BLOCKED
    with pytest.raises(PreregistrationError, match="not 'PREREGISTERED'"):
        _validate(plan)


@pytest.mark.parametrize("path", [
    ("region", "boundarySha256"),
    ("indicator", "methodId"),
    ("indicator", "methodVersion"),
    ("ledger", "rawCsvSha256"),
    ("design", "replacementPolicy"),
    ("design", "randomSeed"),
    ("design", "allocationRationale"),
])
def test_refuses_any_null_field(path):
    plan = _plan()
    plan[path[0]][path[1]] = None
    with pytest.raises(PreregistrationError):
        _validate(plan)


@pytest.mark.parametrize("key", ["metric", "targetStandardError", "confidenceLevel"])
def test_refuses_incomplete_target_precision(key):
    plan = _plan()
    plan["design"]["targetPrecision"][key] = None
    with pytest.raises(PreregistrationError, match="targetPrecision"):
        _validate(plan)


@pytest.mark.parametrize("bad", [None, 0, -5, 12.5, "120", True])
def test_refuses_absent_or_invalid_sample_sizes(bad):
    plan = _plan()
    plan["strata"][0]["sampleSize"] = bad
    with pytest.raises(PreregistrationError):
        _validate(plan)


def test_refuses_inclusion_probability_that_does_not_match_the_population():
    plan = _plan()
    # Plausible-looking but wrong: rounded to six places instead of exact.
    plan["strata"][1]["inclusionProbability"] = 0.000005
    with pytest.raises(PreregistrationError, match="not exactly"):
        _validate(plan)


def test_refuses_population_that_disagrees_with_the_ledger():
    plan = _plan()
    plan["strata"][0]["populationPixels"] = POPULATIONS["stable_non_target"] + 1
    with pytest.raises(PreregistrationError, match="does not match the imported ledger"):
        _validate(plan)


def test_refuses_ledger_checksum_mismatch():
    plan = _plan()
    plan["ledger"]["rawCsvSha256"] = "0" * 64
    with pytest.raises(PreregistrationError, match="raw CSV checksum"):
        _validate(plan)


def test_refuses_boundary_checksum_mismatch():
    plan = _plan()
    plan["region"]["boundarySha256"] = "1" * 64
    with pytest.raises(PreregistrationError, match="boundary checksum"):
        _validate(plan)


def test_refuses_unknown_replacement_policy():
    plan = _plan()
    plan["design"]["replacementPolicy"] = "SOMETIMES"
    with pytest.raises(PreregistrationError, match="replacementPolicy"):
        _validate(plan)


def test_refuses_sample_larger_than_population_without_replacement():
    plan = _plan()
    plan["strata"][2]["sampleSize"] = POPULATIONS["mapped_gain"] + 1
    with pytest.raises(PreregistrationError, match="without replacement"):
        _validate(plan)


def test_refuses_plan_missing_a_ledger_stratum():
    plan = _plan()
    plan["strata"] = plan["strata"][:3]
    with pytest.raises(PreregistrationError, match="omits strata"):
        _validate(plan)


def test_refuses_stratum_absent_from_the_ledger():
    plan = _plan()
    plan["strata"][0]["stratumId"] = "invented_stratum"
    with pytest.raises(PreregistrationError, match="absent from the imported ledger"):
        _validate(plan)


# ── ledger reading ───────────────────────────────────────────────────────────

def _write_ledger(tmp_path: Path, rows: list[tuple[str, str]]) -> Path:
    path = tmp_path / "ledger.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["stratumId", "populationPixels"])
        writer.writerows(rows)
    return path


def test_reads_a_whole_number_ledger(tmp_path):
    path = _write_ledger(tmp_path, [(k, str(v)) for k, v in POPULATIONS.items()])
    assert read_population_ledger(path) == POPULATIONS


def test_refuses_fractional_population_the_v1_defect(tmp_path):
    path = _write_ledger(tmp_path, [("stable_target", "82372144.5")])
    with pytest.raises(PreregistrationError, match="fractional population"):
        read_population_ledger(path)


def test_refuses_duplicate_stratum_in_ledger(tmp_path):
    path = _write_ledger(tmp_path, [("mapped_gain", "10"), ("mapped_gain", "20")])
    with pytest.raises(PreregistrationError, match="repeats stratum"):
        read_population_ledger(path)


# ── export separation ────────────────────────────────────────────────────────

def _write_frame(tmp_path: Path) -> Path:
    path = tmp_path / "frame.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["sampleId", "longitude", "latitude", "mappedStratum"])
        n = 0
        for stratum, size in TEST_SAMPLE_SIZES.items():
            for i in range(size):
                n += 1
                writer.writerow([f"S{n:05d}", 79.0 + i * 1e-4, 21.0 + i * 1e-4, stratum])
    return path


def test_export_writes_two_separate_files_and_blinds_the_reviewer_one(tmp_path):
    validated = _validate(_plan())
    rows = read_candidate_frame(_write_frame(tmp_path))
    out = tmp_path / "out"
    summary = export_formal_sample(validated, rows, out, dry_run=False)

    blinded = out / "nagpur-vegetation-formal-sample.blinded.csv"
    linkage = out / "nagpur-vegetation-formal-sample.design-linkage.RESTRICTED.csv"
    assert blinded.is_file() and linkage.is_file()

    with blinded.open(encoding="utf-8") as handle:
        header = next(csv.reader(handle))
    assert header == ["sampleId", "longitude", "latitude", "referenceStatus"]
    for forbidden in ("mappedStratum", "inclusionProbability", "populationPixels", "score"):
        assert forbidden not in header, f"blinded file leaks {forbidden}"

    with linkage.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == [
            "sampleId", "mappedStratum", "populationPixels", "sampleSize", "inclusionProbability",
        ]
        first = next(reader)
    assert "/" in first["inclusionProbability"], "linkage must keep the exact rational"
    assert summary["totalSampleSize"] == sum(TEST_SAMPLE_SIZES.values())


def test_dry_run_writes_nothing(tmp_path):
    validated = _validate(_plan())
    rows = read_candidate_frame(_write_frame(tmp_path))
    out = tmp_path / "out"
    summary = export_formal_sample(validated, rows, out, dry_run=True)
    assert summary["status"] == "DRY_RUN"
    assert not out.exists()


def test_export_refuses_when_the_frame_is_short(tmp_path):
    validated = _validate(_plan())
    rows = read_candidate_frame(_write_frame(tmp_path))
    trimmed = [r for r in rows if r["mappedStratum"] != "mapped_gain"][:10]
    with pytest.raises(PreregistrationError, match="requires"):
        export_formal_sample(validated, trimmed, tmp_path / "out2", dry_run=True)


def test_export_refuses_to_overwrite_an_existing_export(tmp_path):
    validated = _validate(_plan())
    rows = read_candidate_frame(_write_frame(tmp_path))
    out = tmp_path / "out"
    export_formal_sample(validated, rows, out, dry_run=False)
    with pytest.raises(PreregistrationError, match="Refusing to overwrite"):
        export_formal_sample(validated, rows, out, dry_run=False)


# ── the shipped template must stay blocked ───────────────────────────────────

def test_shipped_template_is_blocked_and_cannot_authorise_a_sample():
    template = Path("docs/templates/nagpur-vegetation-probability-design.template.json")
    plan = json.loads(template.read_text(encoding="utf-8"))
    assert plan["planStatus"] == PLAN_STATUS_BLOCKED
    with pytest.raises(PreregistrationError):
        _validate(plan)


def test_template_does_not_ship_the_exploratory_25_per_stratum_allocation():
    template = Path("docs/templates/nagpur-vegetation-probability-design.template.json")
    plan = json.loads(template.read_text(encoding="utf-8"))
    for stratum in plan["strata"]:
        assert stratum["sampleSize"] is None, (
            "Template must not carry a sample size. 25/stratum is EXPLORATORY_REVIEW_ONLY "
            "and must never be promoted into a probability design."
        )
