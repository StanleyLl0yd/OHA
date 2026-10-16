#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Descriptive dispersion for verified independent baseline runs, NOT OHA speed."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import median

SEVEN_Z = "independent_7zip_LZMA2_archive_baseline_NOT_OHA"
TAR = "deterministic_tar_baseline_NOT_oha_or_7z"
METRICS = {
    SEVEN_Z: ("archive_bytes", "encode_ms", "extract_all_ms", "verify_ms",
              "encode_peak_rss_kib", "extract_peak_rss_kib"),
    TAR: ("compressed_bytes", "tar_build_ms", "encode_ms", "decode_ms",
          "verify_ms"),
}


class BaselineSummaryError(ValueError):
    pass


def numeric(value, field: str):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise BaselineSummaryError("invalid nonnegative metric: " + field)
    return value


def describe(samples: list, name: str):
    if all(value is None for value in samples):
        return None  # Unmeasured RSS, not zero RSS.
    if any(value is None for value in samples):
        raise BaselineSummaryError("mixed measured/unmeasured metric: " + name)
    values = [numeric(value, name) for value in samples]
    mid = median(values)
    return {
        "samples": len(values),
        "median": mid,
        "minimum": min(values),
        "maximum": max(values),
        "median_absolute_deviation": median(abs(value - mid) for value in values),
    }


def summarize(report: dict) -> dict:
    if type(report) is not dict or report.get("schema_version") != 1:
        raise BaselineSummaryError("unsupported baseline report version")
    kind = report.get("kind")
    if kind not in METRICS:
        raise BaselineSummaryError("only verified 7z and TAR external baselines supported")
    method = report.get("method")
    rows = report.get("runs")
    if type(method) is not dict or type(rows) is not list or not rows:
        raise BaselineSummaryError("missing baseline method/runs")
    repetitions = method.get("repetitions")
    if type(repetitions) is not int or not 1 <= repetitions <= 20:
        raise BaselineSummaryError("invalid repetition count")
    groups: dict[str, list[dict]] = {}
    for row in rows:
        if type(row) is not dict:
            raise BaselineSummaryError("malformed baseline run")
        repetition = row.get("repetition")
        if type(repetition) is not int or not 1 <= repetition <= repetitions:
            raise BaselineSummaryError("invalid baseline repetition")
        if kind == SEVEN_Z:
            if type(row.get("solid")) is not bool:
                raise BaselineSummaryError("invalid 7z solid mode")
            if row.get("integrity") != "all files and selective SHA-256 verified":
                raise BaselineSummaryError("7z integrity not verified")
            scenario = "solid" if row["solid"] else "non-solid"
        else:
            if row.get("status") != "sha256-verified":
                raise BaselineSummaryError("TAR integrity not verified")
            scenario = row.get("codec")
            if scenario not in ("TAR+XZ-3", "TAR+ZSTD-3"):
                raise BaselineSummaryError("unknown TAR external codec")
        groups.setdefault(scenario, []).append(row)
    summary = {}
    for scenario, data in sorted(groups.items()):
        repeats = [item["repetition"] for item in data]
        if sorted(repeats) != list(range(1, repetitions + 1)):
            raise BaselineSummaryError("missing or duplicate baseline repetitions")
        stats = {}
        for name in METRICS[kind]:
            stats[name] = describe([item.get(name) for item in data], name)
        if kind == TAR:
            # Full directory package construction belongs in total encode time.
            totals = [numeric(item.get("tar_build_ms"), "tar_build_ms") +
                      numeric(item.get("encode_ms"), "encode_ms") for item in data]
            stats["tar_build_plus_encode_ms"] = describe(totals, "tar_build_plus_encode_ms")
        summary[scenario] = stats
    return {
        "schema_version": 1,
        "kind": "descriptive_external_baseline_dispersion_NOT_OHA_performance",
        "source_kind": kind,
        "repetitions_per_scenario": repetitions,
        "environment": report.get("environment"),
        "tool_versions": report.get("tool_versions") if kind == TAR else report.get("version"),
        "method": method,
        "scenarios": summary,
        "cautions": (
            "Median, min, max and MAD are descriptive for these few CI samples only; "
            "uncontrolled cache/hardware and synthetic or historical data cannot establish "
            "OHA performance. 7z selective-file latencies target potentially different files "
            "between repetitions and are intentionally NOT aggregated; no OHA writer exists."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Raw JSON output of baseline_7z.py or baseline_tar.py")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.output.resolve() == args.source.resolve():
        parser.error("summary must not overwrite raw baseline")
    source = args.source.read_bytes()
    result = summarize(json.loads(source))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Summarized {len(result['scenarios'])} verified baseline scenarios")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
