#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Deterministic tar+codec M0 baseline, NOT 7-Zip or OHA benchmarking."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import shutil
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path

import benchmark


def make_tar(source: Path, files: list[Path], output: Path) -> float:
    started = time.perf_counter()
    with tarfile.open(output, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for file in files:
            name = file.relative_to(source).as_posix()
            metadata = tarfile.TarInfo(name)
            metadata.size = file.stat().st_size
            metadata.mtime = 0
            metadata.mode = 0o644
            metadata.uid = 0
            metadata.gid = 0
            with file.open("rb") as stream:
                archive.addfile(metadata, stream)
    return (time.perf_counter() - started) * 1000


def verify_tar(tar_path: Path, source: Path, files: list[Path]) -> None:
    expected = {file.relative_to(source).as_posix():
                (file.stat().st_size, benchmark.hash_file(file)) for file in files}
    seen = set()
    with tarfile.open(tar_path, mode="r:") as archive:
        for entry in archive:
            if not entry.isfile() or entry.name not in expected or entry.name in seen:
                raise RuntimeError("tar has unknown, non-regular or duplicate entry")
            seen.add(entry.name)
            size, digest = expected[entry.name]
            if entry.size != size:
                raise RuntimeError("tar entry size mismatch")
            body = archive.extractfile(entry)
            if body is None:
                raise RuntimeError("tar entry body missing")
            sha = hashlib.sha256()
            read_bytes = 0
            with body:
                for block in iter(lambda: body.read(1024 * 1024), b""):
                    read_bytes += len(block)
                    sha.update(block)
            if read_bytes != size or sha.hexdigest() != digest:
                raise RuntimeError("tar content SHA-256 mismatch")
    if seen != set(expected):
        raise RuntimeError("tar has missing entries")



def codec_version(executable: str) -> str:
    """Capture the actual codec CLI banner (including stderr-only tools)."""
    result = subprocess.run([executable, "--version"], capture_output=True,
                            text=True, timeout=15, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"cannot identify {executable} version")
    for line in (result.stdout + "\n" + result.stderr).splitlines():
        if line.strip():
            return line.strip()[:250]
    raise RuntimeError(f"empty {executable} version banner")


def measure_directory(source: Path, files: list[Path], repetitions: int = 3) -> dict:
    if repetitions < 1 or repetitions > 20:
        raise ValueError("invalid repetitions")
    if not source.is_dir() or source.is_symlink() or not files:
        raise ValueError("non-symlink directory with nonempty file list required")
    coders = {name: args for name, args in {
        "TAR+ZSTD-3": (["zstd", "-q", "-T1", "-3", "-c"], ["zstd", "-q", "-d", "-c"]),
        "TAR+XZ-3": (["xz", "-T1", "-3", "-c"], ["xz", "-d", "-c"]),
    }.items() if shutil.which(args[0][0])}
    if not coders:
        raise RuntimeError("neither zstd nor xz available")
    versions = {encoder[0]: codec_version(encoder[0])
                for encoder, _ in coders.values()}
    plan = [(n, name) for n in range(1, repetitions + 1)
            for name in coders]
    random.Random(271828).shuffle(plan)
    records = []
    with tempfile.TemporaryDirectory(prefix="oha-tar-baseline-") as directory:
        tmp = Path(directory)
        for order, (repetition, name) in enumerate(plan, 1):
                encoder, decoder = coders[name]
                packed_tar = tmp / "input.tar"
                compressed = tmp / "packed.out"
                restored_tar = tmp / "restored.tar"
                tar_ms = make_tar(source, files, packed_tar)
                encoded_ms = benchmark._run_stream(encoder, packed_tar, compressed)
                decoded_ms = benchmark._run_stream(decoder, compressed, restored_tar)
                if packed_tar.stat().st_size != restored_tar.stat().st_size:
                    raise RuntimeError("tar size mismatch after decoder")
                if benchmark.hash_file(packed_tar) != benchmark.hash_file(restored_tar):
                    raise RuntimeError("tar SHA-256 mismatch after decoder")
                started = time.perf_counter()
                verify_tar(restored_tar, source, files)
                verify_ms = (time.perf_counter() - started) * 1000
                records.append({"codec": name, "repetition": repetition,
                                "order_position": order,
                                "tar_bytes": packed_tar.stat().st_size,
                                "compressed_bytes": compressed.stat().st_size,
                                "tar_build_ms": round(tar_ms, 3),
                                "encode_ms": round(encoded_ms, 3),
                                "decode_ms": round(decoded_ms, 3),
                                "verify_ms": round(verify_ms, 3),
                                "status": "sha256-verified"})
    return {"schema_version": 1, "kind": "deterministic_tar_baseline_NOT_oha_or_7z",
            "notes": "Reproducibly shuffled codec/repetition order. No RSS/random-file extraction/cold cache controls."
                     " End-to-end package+encode = tar_build_ms + encode_ms.",
            "method": {"run_order_seed": 271828, "repetitions": repetitions,
                       "cache_control": "uncontrolled warm/variable", "threads": 1},
            "environment": {"os": platform.platform(), "machine": platform.machine(),
                            "python": platform.python_version()},
            "tool_versions": versions,
            "input_files": [{"path": f.relative_to(source).as_posix(),
                             "size": f.stat().st_size, "sha256": benchmark.hash_file(f)} for f in files],
            "runs": records}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--max-files", type=int, default=1000)
    parser.add_argument("--max-file-bytes", type=int, default=256 * 1024 * 1024)
    parser.add_argument("--max-total-bytes", type=int, default=4 * 1024**3)
    parser.add_argument("--max-scan-entries", type=int, default=100_000)
    args = parser.parse_args(argv)
    if not args.root.is_dir() or args.root.is_symlink():
        parser.error("root must be a real directory")
    if args.repetitions < 1 or args.repetitions > 20:
        parser.error("repetitions must be in 1..20")
    if args.output.resolve().is_relative_to(args.root.resolve()):
        parser.error("output must be outside corpus")
    files = benchmark.discover(args.root, args.max_files, args.max_file_bytes,
                               args.max_scan_entries, args.max_total_bytes)
    result = measure_directory(args.root, files, args.repetitions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Recorded {len(result['runs'])} verified directory-archive baselines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
