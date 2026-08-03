"""Tests for blinded validation-frame label-template creation."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.data.create_validation_label_template import create_label_template


class LabelTemplateTests(unittest.TestCase):
    @staticmethod
    def _workspace_temp_dir() -> Path:
        directory = Path(__file__).resolve().parents[2] / "data" / "cache"
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def _frame(self, path: Path, *, method_id: str = "default") -> None:
        fields = (
            "sampleId",
            "referenceStatus",
            "indicatorId",
            "mapMethodId",
            "mapMethodVersion",
            ".geo",
        )
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for index in range(100):
                writer.writerow(
                    {
                        "sampleId": f"sample-{index}",
                        "referenceStatus": "UNLABELLED",
                        "indicatorId": "built-up",
                        "mapMethodId": method_id,
                        "mapMethodVersion": "p0-constrained-ndbi-v1",
                        ".geo": json.dumps({"type": "Point", "coordinates": [79.0 + index / 10000, 21.0]}),
                    }
                )

    def test_records_and_binds_a_declared_built_method(self) -> None:
        with TemporaryDirectory(dir=self._workspace_temp_dir()) as directory:
            root = Path(directory)
            frame, labels, metadata = root / "frame.csv", root / "labels.csv", root / "metadata.json"
            self._frame(frame)

            result = create_label_template(
                frame,
                labels,
                metadata,
                expected_indicator_id="built-up",
                expected_map_method_id="default",
                expected_map_method_version="p0-constrained-ndbi-v1",
            )

            self.assertEqual(result["sampleFrame"]["mapMethod"]["mapMethodId"], "default")
            self.assertEqual(len(labels.read_text(encoding="utf-8").splitlines()), 101)

    def test_rejects_a_swapped_method_frame(self) -> None:
        with TemporaryDirectory(dir=self._workspace_temp_dir()) as directory:
            root = Path(directory)
            frame = root / "frame.csv"
            self._frame(frame, method_id="built-ibi")

            with self.assertRaisesRegex(ValueError, "does not match"):
                create_label_template(
                    frame,
                    root / "labels.csv",
                    root / "metadata.json",
                    expected_indicator_id="built-up",
                    expected_map_method_id="default",
                    expected_map_method_version="p0-constrained-ndbi-v1",
                )


if __name__ == "__main__":
    unittest.main()
