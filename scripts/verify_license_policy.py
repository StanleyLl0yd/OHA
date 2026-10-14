#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Verify locally owned OHA source license markers, not third-party legal clearance."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CODE_DIRS = ("apps", "crates", "include", "scripts", "tests", "tools")
SOURCE_SUFFIXES = {".rs", ".swift", ".cs", ".h", ".py", ".xaml", ".manifest"}
REQUIRED = ("LICENSE", "AUTHORS.md", "CONTRIBUTING.md", "THIRD_PARTY_NOTICES.md")


def verify() -> list[str]:
    errors = []
    for item in REQUIRED:
        if not (ROOT / item).is_file():
            errors.append("missing " + item)
    license_path = ROOT / "LICENSE"
    if license_path.is_file():
        data = license_path.read_text(encoding="utf-8")
        if not data.startswith("Mozilla Public License Version 2.0\n"):
            errors.append("LICENSE is not canonical MPL-2.0")
        if "Exhibit A - Source Code Form License Notice" not in data or len(data) < 16000:
            errors.append("LICENSE is incomplete")
    for top in CODE_DIRS:
        for path in (ROOT / top).rglob("*"):
            if not path.is_file() or path.suffix not in SOURCE_SUFFIXES:
                continue
            first = "\n".join(path.read_text(encoding="utf-8").splitlines()[:7])
            if "SPDX-License-Identifier: MPL-2.0" not in first:
                errors.append(str(path.relative_to(ROOT)) + " lacks an MPL SPDX header")
    root_manifest = (ROOT / "Cargo.toml").read_text(encoding="utf-8")
    if 'license = "MPL-2.0"' not in root_manifest:
        errors.append("Cargo workspace license must be MPL-2.0")
    for manifest in sorted((ROOT / "crates").glob("*/Cargo.toml")) + sorted((ROOT / "apps").glob("*/Cargo.toml")):
        data = manifest.read_text(encoding="utf-8")
        if "license.workspace = true" not in data:
            errors.append(str(manifest.relative_to(ROOT)) + " must inherit MPL")
    if (ROOT / "Package.swift").read_text(encoding="utf-8").splitlines()[0] != "// swift-tools-version: 6.0":
        errors.append("SwiftPM tools-version directive must remain first")
    if not any("SPDX-License-Identifier: MPL-2.0" in line for line in (ROOT / "Package.swift").read_text(encoding="utf-8").splitlines()[:5]):
        errors.append("Package.swift needs MPL marker")
    return errors


if __name__ == "__main__":
    problems = verify()
    if problems:
        print("\n".join(problems), file=sys.stderr)
        raise SystemExit(1)
    print("OHA source license markers PASS (MPL-2.0); third-party audit remains separate")
