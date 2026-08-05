"""Runtime repository for generated precomputed contract artifacts."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any


class StaticPrecomputedRepository:
    """Serve only the generated, checksum-listed response inventory."""

    def __init__(self, examples_root: Path) -> None:
        self._root = examples_root.resolve(strict=True)
        manifest = self._load("manifest.json")
        self._verify_manifest(manifest)
        self._summaries: dict[str, dict[str, Any]] = {}
        self._comparisons: dict[tuple[str, str], dict[str, Any]] = {}
        for filename in manifest["files"]:
            name = filename["name"]
            if name.endswith("-summary.json"):
                payload = self._load(name)
                region_id = payload["data"]["region"]["id"]
                self._summaries[region_id] = payload
            elif name.endswith(".json"):
                payload = self._load(name)
                data = payload["data"]
                self._comparisons[(data["region"]["id"], data["indicator"]["id"])] = payload
        if not self._summaries or not self._comparisons:
            raise RuntimeError("Precomputed contract manifest contains no usable responses")
        self._regions = {
            region_id: payload["data"]["region"] for region_id, payload in self._summaries.items()
        }

    def _load(self, filename: str) -> dict[str, Any]:
        if Path(filename).name != filename or Path(filename).suffix != ".json":
            raise RuntimeError(f"Unsafe precomputed contract filename: {filename}")
        path = (self._root / filename).resolve(strict=True)
        if path.parent != self._root:
            raise RuntimeError("Precomputed contract resolved outside its fixed root")
        return json.loads(path.read_text(encoding="utf-8"))

    def _verify_manifest(self, manifest: dict[str, Any]) -> None:
        if manifest.get("manifestVersion") != "1" or not isinstance(manifest.get("files"), list):
            raise RuntimeError("Unsupported precomputed contract manifest")
        for entry in manifest["files"]:
            name = entry.get("name")
            expected = entry.get("sha256")
            if not isinstance(name, str) or not isinstance(expected, str):
                raise RuntimeError("Malformed precomputed contract manifest entry")
            path = (self._root / name).resolve(strict=True)
            if path.parent != self._root:
                raise RuntimeError("Precomputed manifest resolved outside its fixed root")
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != expected:
                raise RuntimeError(f"Precomputed contract checksum mismatch: {name}")

    def list_regions(self, region_type: str | None, parent_id: str | None) -> list[dict[str, Any]]:
        regions = list(self._regions.values())
        if region_type is not None:
            regions = [region for region in regions if region["type"] == region_type]
        if parent_id is not None:
            regions = [region for region in regions if region["parentId"] == parent_id]
        return deepcopy(sorted(regions, key=lambda region: region["id"]))

    def get_region(self, region_id: str) -> dict[str, Any] | None:
        region = self._regions.get(region_id)
        return deepcopy(region) if region else None

    def get_summary(self, region_id: str) -> dict[str, Any] | None:
        payload = self._summaries.get(region_id)
        return deepcopy(payload) if payload else None

    def list_indicators(self, region_id: str) -> list[dict[str, Any]] | None:
        summary = self.get_summary(region_id)
        return summary["data"]["indicators"] if summary else None

    def get_indicator(self, region_id: str, indicator_id: str) -> dict[str, Any] | None:
        payload = self._comparisons.get((region_id, indicator_id))
        return deepcopy(payload) if payload else None

    def get_time_series(self, region_id: str, indicator_id: str) -> dict[str, Any] | None:
        return None

    def get_comparison_summary(self, comparison_id: str) -> dict[str, Any] | None:
        for payload in self._comparisons.values():
            if payload["data"]["comparisonId"] == comparison_id:
                return self.get_summary(payload["data"]["region"]["id"])
        return None

    def get_layer(self, layer_id: str) -> dict[str, Any] | None:
        return None

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        return None

    def list_datasets(self) -> list[dict[str, Any]]:
        datasets: dict[str, dict[str, Any]] = {}
        for payload in self._comparisons.values():
            for source in payload["data"]["provenance"]["sources"]:
                datasets[source["datasetId"]] = source
        return deepcopy(sorted(datasets.values(), key=lambda item: item["datasetId"]))

    def list_indicator_metadata(self) -> list[dict[str, Any]]:
        indicators = {
            payload["data"]["indicator"]["id"]: payload["data"]["indicator"]
            for payload in self._comparisons.values()
        }
        return deepcopy(sorted(indicators.values(), key=lambda item: item["id"]))

    @property
    def summary_periods(self) -> tuple[dict[str, Any], dict[str, Any]]:
        first = next(iter(self._summaries.values()))["data"]
        return deepcopy(first["baselinePeriod"]), deepcopy(first["comparisonPeriod"])

    @property
    def base_meta(self) -> dict[str, Any]:
        return deepcopy(next(iter(self._summaries.values()))["meta"])
