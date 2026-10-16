# SPDX-License-Identifier: MPL-2.0
"""Negative and descriptive checks for baseline statistics, no OHA comparisons."""
import importlib.util
from pathlib import Path
import unittest

module = Path(__file__).resolve().parents[1] / "tools" / "summarize_baseline.py"
spec = importlib.util.spec_from_file_location("summarize_baseline", module)
summary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summary)


def example_7z():
    rows = []
    for repetition in (1, 2):
        for solid in (False, True):
            rows.append({
                "repetition": repetition, "solid": solid,
                "integrity": "all files and selective SHA-256 verified",
                "archive_bytes": 200 if solid else 250,
                "encode_ms": 5 if repetition == 1 else 9,
                "extract_all_ms": 12, "verify_ms": 2,
                "encode_peak_rss_kib": None,
                "extract_peak_rss_kib": None,
                # Different file each iteration: never aggregate this timing.
                "selective_file": f"file-{repetition}",
                "selective_ms": 1 if repetition == 1 else 500,
            })
    return {"schema_version": 1, "kind": summary.SEVEN_Z,
            "method": {"repetitions": 2, "cache_control": "uncontrolled"},
            "version": "7z test", "runs": rows}


def example_tar():
    return {"schema_version": 1, "kind": summary.TAR,
            "method": {"repetitions": 3, "cache_control": "uncontrolled"},
            "runs": [
                {"codec": "TAR+XZ-3", "repetition": i, "status": "sha256-verified",
                 "compressed_bytes": 100, "tar_build_ms": float(i),
                 "encode_ms": float(i + 2), "decode_ms": 8.0,
                 "verify_ms": 1.0}
                for i in (1, 2, 3)
            ]}


class BaselineDispersionTests(unittest.TestCase):
    def test_7z_modes_separate_and_selective_not_aggregated(self):
        report = summary.summarize(example_7z())
        self.assertEqual(set(report["scenarios"]), {"solid", "non-solid"})
        for scenario in report["scenarios"].values():
            self.assertEqual(scenario["encode_ms"]["median"], 7)
            self.assertEqual(scenario["encode_ms"]["median_absolute_deviation"], 2)
            self.assertIsNone(scenario["encode_peak_rss_kib"])
            self.assertNotIn("selective_ms", scenario)
        self.assertEqual(report["repetitions_per_scenario"], 2)

    def test_tar_package_plus_encode_and_median(self):
        report = summary.summarize(example_tar())
        data = report["scenarios"]["TAR+XZ-3"]
        self.assertEqual(data["tar_build_plus_encode_ms"]["median"], 6)
        self.assertEqual(data["tar_build_plus_encode_ms"]["minimum"], 4)
        self.assertEqual(data["tar_build_plus_encode_ms"]["maximum"], 8)
        self.assertEqual(data["tar_build_plus_encode_ms"]["median_absolute_deviation"], 2)

    def test_duplicate_or_missing_repetitions_rejected(self):
        obj = example_7z()
        obj["runs"] = obj["runs"][:-1]
        with self.assertRaisesRegex(summary.BaselineSummaryError, "missing"):
            summary.summarize(obj)
        obj = example_tar()
        obj["runs"][1]["repetition"] = 1
        with self.assertRaisesRegex(summary.BaselineSummaryError, "duplicate"):
            summary.summarize(obj)

    def test_corrupt_integrity_rejected(self):
        obj = example_7z()
        obj["runs"][0]["integrity"] = "failed"
        with self.assertRaisesRegex(summary.BaselineSummaryError, "integrity"):
            summary.summarize(obj)
        obj = example_tar()
        obj["runs"][0]["status"] = "unverified"
        with self.assertRaisesRegex(summary.BaselineSummaryError, "integrity"):
            summary.summarize(obj)

    def test_mixed_rss_cannot_be_misrepresented_as_zero(self):
        obj = example_7z()
        obj["runs"][0]["encode_peak_rss_kib"] = 400
        with self.assertRaisesRegex(summary.BaselineSummaryError, "mixed"):
            summary.summarize(obj)

    def test_nonfinite_metric_and_wrong_baseline_rejected(self):
        obj = example_tar()
        obj["runs"][0]["encode_ms"] = float("nan")
        with self.assertRaisesRegex(summary.BaselineSummaryError, "invalid"):
            summary.summarize(obj)
        obj = example_7z()
        obj["kind"] = "actual_OHA_performance"
        with self.assertRaisesRegex(summary.BaselineSummaryError, "only verified"):
            summary.summarize(obj)


if __name__ == "__main__":
    unittest.main()
