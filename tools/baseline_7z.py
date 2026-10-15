#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Independent 7-Zip LZMA2 end-to-end baseline, not OHA compression results."""

from __future__ import annotations

import argparse
import json
import os
import platform
import random
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import benchmark



def input_manifest(root: Path, files: list[Path]) -> dict[str, dict]:
    result = {}
    if root.is_symlink() or not root.is_dir() or not files:
        raise ValueError("non-symlink directory containing files required")
    for file in files:
        rel = file.relative_to(root).as_posix()
        if ("\n" in rel or "\r" in rel or not rel or rel in result
                or file.is_symlink() or not file.is_file()):
            raise ValueError("unsupported 7-Zip input filename or file type")
        result[rel] = {"bytes": file.stat().st_size, "sha256": benchmark.hash_file(file)}
    return result


def verify_extract(root: Path, expected: dict[str, dict]) -> None:
    seen: set[str] = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise RuntimeError("extracted archive includes symlink")
        if path.is_dir():
            continue
        rel = path.relative_to(root).as_posix()
        if not path.is_file() or rel not in expected or rel in seen:
            raise RuntimeError("unexpected extracted entry or duplicate")
        seen.add(rel)
        item = expected[rel]
        if path.stat().st_size != item["bytes"] or benchmark.hash_file(path) != item["sha256"]:
            raise RuntimeError("extracted content SHA-256 or size mismatch")
    if seen != set(expected):
        raise RuntimeError("missing files after extraction")


def timed_run(args: list[str], cwd: Path, timeout: int) -> dict:
    # GNU time measures the child process peak RSS without conflating prior runs.
    with tempfile.TemporaryDirectory(prefix="oha-rss-") as temp:
        rss_path = Path(temp) / "rss.txt"
        use_gnu_time = sys.platform.startswith("linux") and Path("/usr/bin/time").is_file()
        wrapped = (["/usr/bin/time", "-f", "%M", "-o", str(rss_path)] + args
                   if use_gnu_time else args)
        start = time.perf_counter()
        completed = subprocess.run(wrapped, cwd=cwd,
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.PIPE, timeout=timeout, check=False)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 3)
        if completed.returncode != 0:
            detail = completed.stderr.decode("utf-8", "replace")[-1200:]
            raise RuntimeError(f"7z subprocess failed ({completed.returncode}): {detail}")
        rss = int(rss_path.read_text().strip()) if use_gnu_time else None
        return {"elapsed_ms": elapsed_ms, "peak_rss_kib": rss}



def version_banner(output: str) -> str:
    for line in output.splitlines():
        cleaned = line.strip()
        if cleaned:
            return cleaned[:250]
    raise RuntimeError("7-Zip returned no identifiable version text")


def measure(root: Path, files: list[Path], *, sevenzip: str, repetitions: int = 3,
            solid_options: tuple[bool, ...] = (False, True), timeout: int = 600) -> dict:
    if repetitions < 1 or repetitions > 20 or timeout < 1 or timeout > 3600 or not solid_options:
        raise ValueError("invalid run parameters")
    if not shutil.which(sevenzip):
        raise FileNotFoundError(f"7-Zip executable not found: {sevenzip}")
    expected = input_manifest(root, files)
    total_input = sum(v["bytes"] for v in expected.values())
    # For each repetition use the same independently selected target in both
    # solid modes. Hash extracted files on disk so memory use is bounded even
    # when all corpus files are large (database/VM/media benchmarks).
    selection_rng = random.Random(314159)
    targets = sorted(expected)
    selected_by_repetition = {
        number: selection_rng.choice(targets)
        for number in range(1, repetitions + 1)
    }
    version = subprocess.run([sevenzip, "i"], capture_output=True, text=True,
                             timeout=30, check=False)
    if version.returncode != 0:
        raise RuntimeError("unable to identify 7-Zip version")
    plan = [(n, solid) for n in range(1, repetitions + 1) for solid in solid_options]
    random.Random(271828).shuffle(plan)
    records = []
    with tempfile.TemporaryDirectory(prefix="oha-7z-baseline-") as temporary:
        scratch = Path(temporary)
        file_list = scratch / "input-files.txt"
        file_list.write_text("\n".join(expected) + "\n", encoding="utf-8")
        for repetition, solid in plan:
            archive = scratch / "archive.7z"
            archive.unlink(missing_ok=True)
            unpacked = scratch / "restored"
            if unpacked.exists():
                shutil.rmtree(unpacked)
            unpacked.mkdir()
            common = [sevenzip, "-bso0", "-bsp0", "-bse1"]
            options = ["-t7z", "-m0=lzma2", "-mx=5", "-mmt=1", "-scsUTF-8",
                       "-ms=on" if solid else "-ms=off"]
            packed = timed_run(common[:1] + ["a"] + options + common[1:] +
                               [str(archive), "@" + str(file_list)], root, timeout)
            compressed_bytes = archive.stat().st_size
            extracted = timed_run(common[:1] + ["x", "-y", "-o" + str(unpacked)] +
                                  common[1:] + [str(archive)], root, timeout)
            start_verify = time.perf_counter()
            verify_extract(unpacked, expected)
            verify_ms = round((time.perf_counter() - start_verify) * 1000, 3)
            random_target = selected_by_repetition[repetition]
            selected = scratch / "selected"
            if selected.exists():
                shutil.rmtree(selected)
            selected.mkdir()
            selective = timed_run(common[:1] + ["x", "-y", "-o" + str(selected)] +
                                  common[1:] + [str(archive), random_target], root, timeout)
            # Never buffer selected contents in the benchmark process. This also
            # detects unexpected files or links, not just a matching content hash.
            verify_extract(selected, {random_target: expected[random_target]})
            records.append({"repetition": repetition, "solid": solid,
                            "archive_bytes": compressed_bytes, "input_bytes": total_input,
                            "encode_ms": packed["elapsed_ms"], "encode_peak_rss_kib": packed["peak_rss_kib"],
                            "extract_all_ms": extracted["elapsed_ms"], "extract_peak_rss_kib": extracted["peak_rss_kib"],
                            "verify_ms": verify_ms, "selective_file": random_target,
                            "selective_ms": selective["elapsed_ms"],
                            "selective_input_bytes": expected[random_target]["bytes"],
                            "selective_peak_rss_kib": selective["peak_rss_kib"],
                            "integrity": "all files and selective SHA-256 verified"})
    return {"schema_version": 1, "kind": "independent_7zip_LZMA2_archive_baseline_NOT_OHA",
            "tool": sevenzip,
            "version": version_banner(version.stdout + "\n" + version.stderr),
            "environment": {"os": platform.platform(), "python": platform.python_version(),
                            "machine": platform.machine(), "gnu_time_rss": sys.platform.startswith("linux") and Path("/usr/bin/time").exists()},
            "method": {"archive": "7z", "codec": "LZMA2", "level": 5, "threads": 1,
                       "repetitions": repetitions, "run_order_seed": 271828,
                       "selected_file_seed": 314159,
                       "selected_file_mode": "extract-to-disk-and-streaming-SHA256",
                       "cache_control": "uncontrolled warm/variable", "source": "user-selected local directory"},
            "corpus": expected, "runs": records}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path, help="Local trusted input directory")
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--sevenzip", default="7z")
    p.add_argument("--repetitions", type=int, default=3)
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("--max-files", type=int, default=1000)
    p.add_argument("--max-file-bytes", type=int, default=64 * 1024 * 1024)
    p.add_argument("--max-total-bytes", type=int, default=512 * 1024 * 1024)
    p.add_argument("--max-scan-entries", type=int, default=100_000)
    args = p.parse_args(argv)
    if not args.source.is_dir() or args.source.is_symlink():
        p.error("source must be a real directory")
    if args.output.resolve().is_relative_to(args.source.resolve()):
        p.error("output must be outside corpus")
    if min(args.max_files, args.max_file_bytes, args.max_total_bytes, args.max_scan_entries) < 1:
        p.error("limits must be positive")
    files = benchmark.discover(args.source, args.max_files, args.max_file_bytes,
                               args.max_scan_entries, args.max_total_bytes)
    result = measure(args.source, files, sevenzip=args.sevenzip,
                     repetitions=args.repetitions, timeout=args.timeout)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Verified {len(result['runs'])} LZMA2 full/selective extraction runs: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
