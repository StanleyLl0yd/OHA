#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Minimal verified compression-probe harness (STORE, ZSTD, XZ).

The results are per-file codec measurements, NOT comparable to finished 7z/OHA archives.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def codecs_present() -> dict[str, tuple[list[str], list[str]] | None]:
    return {
        "STORE": None,
        "ZSTD-3": (["zstd", "-q", "-T1", "-3", "-c"], ["zstd", "-q", "-d", "-c"]) if shutil.which("zstd") else None,
        "ZSTD-9": (["zstd", "-q", "-T1", "-9", "-c"], ["zstd", "-q", "-d", "-c"]) if shutil.which("zstd") else None,
        "XZ-3": (["xz", "-T1", "-3", "-c"], ["xz", "-d", "-c"]) if shutil.which("xz") else None,
    }


def _run_stream(args: list[str], input_path: Path, output_path: Path) -> float:
    start = time.perf_counter()
    with input_path.open("rb") as inp, output_path.open("wb") as out:
        result = subprocess.run(args, stdin=inp, stdout=out, stderr=subprocess.PIPE, check=False, timeout=90)
    elapsed = (time.perf_counter() - start) * 1000
    if result.returncode != 0:
        raise RuntimeError(f"{args[0]} failed (code {result.returncode}): {result.stderr.decode('utf-8', 'replace')[:1000]}")
    return elapsed


def _copy_stream(src: Path, dst: Path) -> float:
    start = time.perf_counter()
    with src.open("rb") as inp, dst.open("wb") as out:
        shutil.copyfileobj(inp, out, length=1024 * 1024)
    return (time.perf_counter() - start) * 1000



def codec_version_banner(stdout: str, stderr: str) -> str:
    """Capture a nonblank version banner from stdout or stderr."""
    for line in (stdout + "\n" + stderr).splitlines():
        if line.strip():
            return line.strip()[:250]
    raise RuntimeError("empty compression codec version banner")


def measure_file(path: Path, repetitions: int = 1, codec_names: list[str] | None = None) -> list[dict]:
    if repetitions < 1:
        raise ValueError("repetitions must be positive")
    registry = codecs_present()
    names = list(registry) if codec_names is None else codec_names
    if not names:
        raise ValueError("at least one codec required")
    unknown = set(names).difference(registry)
    if unknown:
        raise ValueError(f"unknown codecs: {sorted(unknown)}")
    expected_hash = hash_file(path)
    output: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="oha-bench-") as temporary:
        directory = Path(temporary)
        for codec in names:
            spec = registry[codec]
            if codec != "STORE" and spec is None:
                output.append({"codec": codec, "status": "unavailable"})
                continue
            for repetition in range(repetitions):
                compressed = directory / "packed.bin"
                restored = directory / "restored.bin"
                try:
                    if spec is None:
                        encode_ms = _copy_stream(path, compressed)
                        decode_ms = _copy_stream(compressed, restored)
                    else:
                        encoder, decoder = spec
                        encode_ms = _run_stream(encoder, path, compressed)
                        decode_ms = _run_stream(decoder, compressed, restored)
                    if restored.stat().st_size != path.stat().st_size:
                        raise RuntimeError("round-trip size mismatch")
                    if hash_file(restored) != expected_hash:
                        raise RuntimeError("SHA-256 round-trip mismatch")
                    output.append({
                        "codec": codec,
                        "status": "ok",
                        "repetition": repetition + 1,
                        "encoded_bytes": compressed.stat().st_size,
                        "encode_ms": round(encode_ms, 3),
                        "decode_ms": round(decode_ms, 3),
                        "roundtrip_sha256": expected_hash,
                    })
                except (OSError, subprocess.TimeoutExpired, RuntimeError) as error:
                    output.append({"codec": codec, "status": "failed", "repetition": repetition + 1, "error": str(error)})
                    raise
    return output


def discover(
    root: Path, max_files: int, max_file_bytes: int,
    max_scan_entries: int = 100_000, max_total_bytes: int = 4 * 1024**3,
) -> list[Path]:
    if not root.exists():
        raise FileNotFoundError(root)
    if root.is_symlink():
        raise ValueError("symlink source not allowed")
    if min(max_files, max_file_bytes, max_scan_entries, max_total_bytes) < 1:
        raise ValueError("all limits must be positive")
    candidates = [root] if root.is_file() else root.rglob("*")
    files: list[Path] = []
    visited = 0
    total_bytes = 0
    for candidate in candidates:
        visited += 1
        if visited > max_scan_entries:
            raise ValueError(f"scan entries exceed --max-scan-entries={max_scan_entries}")
        if candidate.is_symlink() or not candidate.is_file():
            continue
        size = candidate.stat().st_size
        if size <= max_file_bytes:
            total_bytes += size
            if total_bytes > max_total_bytes:
                raise ValueError(f"corpus exceeds --max-total-bytes={max_total_bytes}")
            files.append(candidate)
            if len(files) > max_files:
                raise ValueError(f"file count exceeds --max-files={max_files}")
    return sorted(files)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="A single file or directory")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--max-files", type=int, default=1000)
    parser.add_argument("--max-file-bytes", type=int, default=256 * 1024 * 1024)
    parser.add_argument("--max-scan-entries", type=int, default=100_000)
    parser.add_argument("--max-total-bytes", type=int, default=4 * 1024**3)
    args = parser.parse_args(argv)
    if (args.repetitions < 1 or args.repetitions > 20 or min(
            args.max_files, args.max_file_bytes, args.max_scan_entries, args.max_total_bytes
    ) < 1):
        parser.error("invalid safety/benchmark bounds")

    if args.root.is_dir():
        try:
            args.output.resolve().relative_to(args.root.resolve())
        except ValueError:
            pass
        else:
            parser.error("--output must be outside the input corpus directory")

    files = discover(args.root, args.max_files, args.max_file_bytes,
                     args.max_scan_entries, args.max_total_bytes)
    records = []
    for file in files:
        print(f"Measuring {file} ({file.stat().st_size} bytes)", file=sys.stderr)
        records.append({
            "path": str(file.relative_to(args.root)) if args.root.is_dir() else file.name,
            "input_bytes": file.stat().st_size,
            "input_sha256": hash_file(file),
            "measurements": measure_file(file, args.repetitions),
        })
    result = {
        "schema_version": 1,
        "kind": "compression_probe_NOT_archive_benchmark",
        "notes": "Synthetic or arbitrary per-file samples. No archive metadata/solid grouping/peak RSS/cache normalization; avoid cross-machine comparisons.",
        "repetitions": args.repetitions,
        "environment": {
            "system": platform.system(), "release": platform.release(),
            "machine": platform.machine(), "python": platform.python_version(),
        },
        "limits": {
            "max_files": args.max_files, "max_file_bytes": args.max_file_bytes,
            "max_scan_entries": args.max_scan_entries, "max_total_bytes": args.max_total_bytes,
        },
        "tool_versions": {},
        "files": records,
    }
    for codec, pair in codecs_present().items():
        if pair is not None:
            binary = pair[0][0]
            if binary not in result["tool_versions"]:
                version = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=5)
                if version.returncode != 0:
                    raise RuntimeError(f"cannot identify {binary} codec version")
                result["tool_versions"][binary] = codec_version_banner(version.stdout, version.stderr)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Results: {args.output} ({len(files)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
