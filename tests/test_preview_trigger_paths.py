# SPDX-License-Identifier: MPL-2.0
"""Guard native preview CI triggers for bundled compliance and inventory inputs."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / ".github" / "workflows" / "previews.yml"


class PreviewPathTriggerTests(unittest.TestCase):
    def test_windows_preview_exports_resolved_transitive_nuget_evidence(self):
        source = PREVIEW.read_text(encoding="utf-8")
        for fragment in (
            "dotnet package list --project apps/oha-windows/OHA.Windows.csproj",
            "--include-transitive --no-restore --format json --output-version 1",
            "OHA-M0-Windows-x64-nuget.json",
            "NuGet JSON contained no projects",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, source)
        self.assertGreaterEqual(source.count("OHA-M0-Windows-x64-nuget.json"), 2)

    def test_macos_preview_verifies_extracted_signed_bundle_without_mutating_it(self):
        source = PREVIEW.read_text(encoding="utf-8")
        mac = source.split("  macos-preview:", 1)[1]
        nested_sign = mac.index('codesign --force --sign - "$app/Contents/Frameworks/liboha_ffi.dylib"')
        sign = mac.index('codesign --force --sign - "$app"')
        checksum = mac.index('> "$RUNNER_TEMP/OHA-M0-macOS-SHA256SUMS.txt"')
        archive = mac.index('ditto -c -k --sequesterRsrc --keepParent')
        extract = mac.index('ditto -x -k "$RUNNER_TEMP/OHA-M0-macOS.zip"')
        final_check = mac.index('codesign --verify --deep --strict --verbose=2 "$unpacked"')
        self.assertLess(nested_sign, sign)
        self.assertLess(sign, checksum)
        self.assertLess(checksum, archive)
        self.assertLess(archive, extract)
        self.assertLess(extract, final_check)
        self.assertIn('--checksums "$RUNNER_TEMP/OHA-M0-macOS-SHA256SUMS.txt"', mac)
        self.assertIn('${{ runner.temp }}/OHA-M0-macOS-SHA256SUMS.txt', mac)
        self.assertNotIn('> SHA256SUMS.txt', mac)

    def test_both_events_rebuild_on_compliance_changes(self):
        source = PREVIEW.read_text(encoding="utf-8")
        self.assertIn("  pull_request:\n", source)
        self.assertIn("  push:\n", source)
        for entry in (
            ".github/workflows/previews.yml",
            "tools/preview_inventory.py",
            "crates/oha-analysis/**",
            "Cargo.toml",
            "Cargo.lock",
            "rust-toolchain.toml",
            "scripts/verify_ci_supply_chain.py",
            "LICENSE",
            "THIRD_PARTY_NOTICES.md",
        ):
            line = f'      - "{entry}"'
            with self.subTest(entry=entry):
                self.assertEqual(source.count(line), 2,
                                 f"{entry} must trigger previews on both PRs and main pushes")


if __name__ == "__main__":
    unittest.main()
