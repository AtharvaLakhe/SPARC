from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

import yaml
from jsonschema import Draft202012Validator, FormatChecker


REPO = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO / "packages" / "contracts" / "schemas" / "sparc.schema.json"
OPENAPI_PATH = REPO / "contracts" / "openapi.yaml"
EXAMPLES = REPO / "contracts" / "examples"

SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
DEFS = SCHEMA["$defs"]
OPENAPI = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))

EXAMPLE_SCHEMA = {
    "district-summary": "DistrictSummaryResponse",
    "water-comparison": "IndicatorComparisonResponse",
    "vegetation-comparison": "IndicatorComparisonResponse",
    "built-up-comparison": "IndicatorComparisonResponse",
    "lst-comparison": "IndicatorComparisonResponse",
    "partial-data": "IndicatorComparisonResponse",
    "time-series": "TimeSeriesResponse",
    "block-results": "BlockResultsResponse",
    "layer-descriptor": "LayerResponse",
    "processing-job": "JobResponse",
    "api-error": "ProblemDetails",
}

RELATIVE_FIELDS = [
    ("RegionRef", "geometryUrl"),
    ("LayerDescriptor", "href"),
    ("LayerDescriptor", "tileJsonHref"),
    ("Links", "self"),
    ("Links", "related", "items"),
    ("IndicatorSummary", "comparisonUrl"),
    ("Job", "resultUrl"),
]
ID_FIELDS = [
    ("RegionRef", "id"),
    ("RegionRef", "parentId"),
    ("DatasetSource", "datasetId"),
    ("Provenance", "algorithmId"),
    ("Interpretation", "ruleId"),
    ("LayerDescriptor", "id"),
    ("ResponseMeta", "requestId"),
    ("IndicatorComparisonData", "comparisonId"),
    ("Job", "id"),
    ("ComparisonRequest", "regionId"),
    ("ProblemDetails", "traceId"),
]


def node_at(definition: str, *path: str) -> dict:
    node = DEFS[definition]
    for segment in path:
        node = node["items"] if segment == "items" else node["properties"][segment]
    return node


class ContractSecurityTests(unittest.TestCase):
    def test_schema_and_every_example_validate(self) -> None:
        Draft202012Validator.check_schema(SCHEMA)
        checker = FormatChecker()
        found = set()
        for path in sorted(EXAMPLES.glob("*.mock.json")):
            stem = path.name.removesuffix(".mock.json")
            definition = EXAMPLE_SCHEMA.get(stem)
            self.assertIsNotNone(definition, f"unmapped example: {path.name}")
            found.add(stem)
            validator = Draft202012Validator(
                {**SCHEMA, "$ref": f"#/$defs/{definition}"},
                format_checker=checker,
            )
            errors = sorted(
                validator.iter_errors(json.loads(path.read_text(encoding="utf-8"))),
                key=lambda error: list(error.path),
            )
            self.assertFalse(errors, f"{path.name}: {[error.message for error in errors[:3]]}")
        self.assertEqual(found, set(EXAMPLE_SCHEMA))

    def test_all_relative_url_fields_reject_offsite_and_traversal(self) -> None:
        bad_values = [
            "//attacker.example/x",
            "/../../etc/passwd",
            "./../secret",
            "/%2e%2e%2fsecret",
            "/\\attacker.example/x",
            "/safe\r\nX-Header: injected",
            "",
        ]
        for field in RELATIVE_FIELDS:
            node = node_at(*field)
            self.assertIn("maxLength", node, field)
            pattern = re.compile(node["pattern"])
            for bad in bad_values:
                self.assertIsNone(pattern.fullmatch(bad), f"{field} accepts {bad!r}")
            for good in ["/api/v1/regions/mock:district:nagpur", "./demo/layer.webp"]:
                self.assertIsNotNone(pattern.fullmatch(good), f"{field} rejects {good!r}")

    def test_all_opaque_identifiers_reject_path_syntax(self) -> None:
        bad_values = ["../secret", "a/b", "a\\b", "/absolute", "UPPER", "a b", "a%2fb", ""]
        for field in ID_FIELDS:
            node = node_at(*field)
            pattern = re.compile(node["pattern"])
            for bad in bad_values:
                self.assertIsNone(pattern.fullmatch(bad), f"{field} accepts {bad!r}")
            self.assertIsNotNone(pattern.fullmatch("mock:district:nagpur"), field)

    def test_external_urls_require_https_and_are_bounded(self) -> None:
        for field in [("DatasetSource", "sourceUrl"), ("Attribution", "url")]:
            node = node_at(*field)
            self.assertLessEqual(node["maxLength"], 2048)
            pattern = re.compile(node["pattern"])
            for bad in [
                "javascript:alert(1)",
                "data:text/html,test",
                "http://example.com",
                "file:///etc/passwd",
                "https://example.com/line\r\nbreak",
            ]:
                self.assertIsNone(pattern.fullmatch(bad), f"{field} accepts {bad!r}")
            self.assertIsNotNone(pattern.fullmatch("https://example.com/path?x=1"))

    def test_every_string_and_array_is_explicitly_bounded(self) -> None:
        unbounded_strings: list[str] = []
        unbounded_arrays: list[str] = []

        fixed_patterns = {
            r"^sha256:[a-f0-9]{64}$",
            r"^#[0-9A-Fa-f]{6}$",
        }

        def walk(node, path: str) -> None:
            if isinstance(node, dict):
                node_type = node.get("type")
                accepts_string = node_type == "string" or (
                    isinstance(node_type, list) and "string" in node_type
                )
                if (
                    accepts_string
                    and "enum" not in node
                    and "const" not in node
                    and "maxLength" not in node
                    and node.get("pattern") not in fixed_patterns
                ):
                    unbounded_strings.append(path)
                if node_type == "array" and "maxItems" not in node:
                    unbounded_arrays.append(path)
                for key, value in node.items():
                    if isinstance(value, (dict, list)):
                        walk(value, f"{path}.{key}")
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    walk(value, f"{path}[{index}]")

        walk(SCHEMA, "$")
        self.assertEqual(unbounded_strings, [])
        self.assertEqual(unbounded_arrays, [])

    def test_every_object_is_closed_recursively(self) -> None:
        offenders: list[str] = []

        def walk(node, path: str) -> None:
            if isinstance(node, dict):
                if node.get("type") == "object" and node.get("additionalProperties") is not False:
                    offenders.append(path)
                for key, value in node.items():
                    if isinstance(value, (dict, list)):
                        walk(value, f"{path}.{key}")
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    walk(value, f"{path}[{index}]")

        walk(SCHEMA, "$")
        self.assertEqual(offenders, [])

    def test_openapi_parses_and_all_external_refs_resolve(self) -> None:
        self.assertEqual(OPENAPI["openapi"], "3.1.0")
        refs: list[str] = []

        def walk(node) -> None:
            if isinstance(node, dict):
                if "$ref" in node:
                    refs.append(node["$ref"])
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(OPENAPI)
        for reference in refs:
            if reference.startswith("#"):
                continue
            file_part, fragment = reference.split("#", 1)
            target = (OPENAPI_PATH.parent / file_part).resolve(strict=True)
            document = json.loads(target.read_text(encoding="utf-8"))
            node = document
            for token in fragment.lstrip("/").split("/"):
                node = node[token.replace("~1", "/").replace("~0", "~")]
            self.assertIsNotNone(node)

    def test_openapi_inline_constraints_match_security_policy(self) -> None:
        region_parameters = OPENAPI["paths"]["/api/v1/regions"]["get"]["parameters"]
        parent_id = next(item for item in region_parameters if item.get("name") == "parentId")["schema"]
        self.assertIn("pattern", parent_id)
        self.assertIsNone(re.fullmatch(parent_id["pattern"], "../../secret"))

        time_parameters = OPENAPI["paths"]["/api/v1/regions/{regionId}/timeseries"]["get"]["parameters"]
        for name in ("startDate", "endDate"):
            date_schema = next(item for item in time_parameters if item.get("name") == name)["schema"]
            self.assertEqual(date_schema["maxLength"], 10)
            self.assertIn("pattern", date_schema)

        for path in ("/api/v1/comparisons", "/api/v1/processing/jobs"):
            location = OPENAPI["paths"][path]["post"]["responses"]["202"]["headers"]["Location"]["schema"]
            pattern = re.compile(location["pattern"])
            self.assertIsNotNone(pattern.fullmatch("/api/v1/processing/jobs/mock:job:nagpur-water"))
            self.assertIsNone(pattern.fullmatch("/api/v1/processing/jobs/good/../../secret"))

        comparison_responses = OPENAPI["paths"]["/api/v1/comparisons"]["post"]["responses"]
        self.assertIn("413", comparison_responses)

        tiles = OPENAPI["paths"]["/api/v1/layers/{layerId}/tilejson.json"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["properties"]["tiles"]
        self.assertGreaterEqual(tiles["minItems"], 1)
        self.assertIn("maxItems", tiles)
        tile_pattern = re.compile(tiles["items"]["pattern"])
        self.assertIsNone(tile_pattern.fullmatch("//attacker.example/{z}/{x}/{y}.png"))


if __name__ == "__main__":
    unittest.main()
