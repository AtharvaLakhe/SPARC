"""Tests for blinded validation-frame controls."""

from __future__ import annotations

import unittest

from scripts.data.create_validation_label_template import EXPECTED_SAMPLE_COUNT, LABEL_COLUMNS


class ValidationTemplateTests(unittest.TestCase):
    def test_exploratory_frame_shape_is_fixed(self) -> None:
        self.assertEqual(EXPECTED_SAMPLE_COUNT, 100)
        self.assertEqual(LABEL_COLUMNS[0], "sampleId")
        self.assertIn("referenceSourceAndLicense", LABEL_COLUMNS)
        self.assertIn("uncertainReason", LABEL_COLUMNS)


if __name__ == "__main__":
    unittest.main()
