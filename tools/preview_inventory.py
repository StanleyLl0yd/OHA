#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Inventory an M0 native preview without claiming third-party license clearance."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

MAX_ENTRIES = 20_000
MAX_TOTAL_BYTES = 2 * 1024**3
MAX_DEPS_BYTES = 16 * 1024**2
GITHUB_SOURCE = "https://github.com/StanleyLl0yd/OHA/tree/"
HEX_SHA = re.compile(r"^[0-9a-f]{40}$")
CHECKSUM_LINE = re.compile(r"^([0-9a-fA-F]{64})[ ]+\*?(.+)$")
CANDIDATE_SUFFIXES = {".dll", ".dylib", ".so", ".exe", ".winmd"}
OWN_BINARIES = {
    "windows": {"OHA.Windows.exe", "oha_ffi.dll"},
    "macos": {"Contents/MacOS/OHA", "Contents/Frameworks/liboha_ffi.dylib"},
}


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def inventory(root: Path, platform: str, source_commit: str) -> dict:
    if platform not in OWN_BINARIES:
        raise ValueError("platform must be windows or macos")
    if not HEX_SHA.fullmatch(source_commit):
        raise ValueError("source commit must be full lowercase SHA-1")
    if root.is_symlink() or not root.is_dir():
        raise ValueError("preview must be a real directory")
    prefix = "Contents/Resources/" if platform == "macos" else ""
    files = {}
    total = 0
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"symlink not permitted in preview: {path.name}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError(f"unsupported preview entry: {path.name}")
        rel = path.relative_to(root).as_posix()
        if len(files) >= MAX_ENTRIES or path.stat().st_size > MAX_TOTAL_BYTES - total:
            raise ValueError("preview file count or byte budget exceeded")
        size = path.stat().st_size
        total += size
        files[rel] = {"bytes": size, "sha256": digest(path)}
    for required in (
        prefix + "LICENSE", prefix + "THIRD_PARTY_NOTICES.md",
        prefix + "SOURCE-CODE.txt", *OWN_BINARIES[platform],
    ):
        if required not in files:
            raise ValueError(f"required preview file missing: {required}")
    if not (root / (prefix + "LICENSE")).read_text(encoding="utf-8").startswith(
        "Mozilla Public License Version 2.0\n"
    ):
        raise ValueError("expected project MPL-2.0 license text missing")
    source = (root / (prefix + "SOURCE-CODE.txt")).read_text(encoding="utf-8")
    if GITHUB_SOURCE + source_commit not in source:
        raise ValueError("source notice lacks exact build commit")
    if not (root / (prefix + "THIRD_PARTY_NOTICES.md")).read_text(encoding="utf-8").strip():
        raise ValueError("third-party inventory notice empty")

    checksum_file = root / ("Contents/SHA256SUMS.txt" if platform == "macos" else "SHA256SUMS.txt")
    checked = []
    if not checksum_file.is_file():
        raise ValueError("SHA256SUMS.txt missing")
    base = "Contents/" if platform == "macos" else ""
    for line in checksum_file.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        match = CHECKSUM_LINE.fullmatch(line)
        if not match:
            raise ValueError("malformed SHA256SUMS line")
        record_sha, name = match.groups()
        rel = base + name
        if rel in checked or rel not in files or record_sha.lower() != files[rel]["sha256"]:
            raise ValueError(f"SHA256SUMS mismatch or duplicate: {name}")
        checked.append(rel)
    if not checked or (platform == "windows" and
                       set(checked) != set(files) - {"SHA256SUMS.txt"}):
        raise ValueError("SHA256SUMS incomplete")
    if platform == "macos" and not OWN_BINARIES["macos"].issubset(set(checked)):
        raise ValueError("macOS binary checksums incomplete")

    deps = {}
    for rel in files:
        if not rel.endswith(".deps.json"):
            continue
        if files[rel]["bytes"] > MAX_DEPS_BYTES:
            raise ValueError("oversized .deps.json manifest")
        obj = json.loads((root / rel).read_text(encoding="utf-8"))
        libraries = obj.get("libraries")
        if not isinstance(libraries, dict):
            raise ValueError("malformed .NET dependency libraries")
        deps[rel] = [
            {"package": name, "type": value.get("type", "unknown")}
            for name, value in sorted(libraries.items())
            if isinstance(value, dict)
        ]
    candidates = [
        rel for rel in files
        if Path(rel).suffix.lower() in CANDIDATE_SUFFIXES
        and rel not in OWN_BINARIES[platform]
    ]
    return {
        "schema_version": 1,
        "purpose": "M0 preview binary inventory; NOT distribution/license clearance",
        "platform": platform, "source_commit": source_commit,
        "file_count": len(files), "total_bytes": total,
        "license_text_present": True,
        "checksums_verified": len(checked),
        "third_party_binary_candidates_unreviewed": candidates,
        "dotnet_dependency_manifests_unreviewed": deps,
        "files": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--platform", choices=("windows", "macos"), required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.root.resolve()):
        parser.error("inventory output must be outside inspected directory")
    result = inventory(args.root, args.platform, args.commit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Preview manifest PASS: {result['file_count']} files, "
          f"{len(result['third_party_binary_candidates_unreviewed'])} "
          "third-party candidates require separate review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
