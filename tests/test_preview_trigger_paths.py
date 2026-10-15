# SPDX-License-Identifier: MPL-2.0
"""Guard native preview CI triggers for bundled compliance and inventory inputs."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / ".github" / "workflows" / "previews.yml"


class PreviewPathTriggerTests(unittest.TestCase):
    def test_both_events_rebuild_on_compliance_changes(self):
        source = PREVIEW.read_text(encoding="utf-8")
        self.assertIn("  pull_request:\n", source)
        self.assertIn("  push:\n", source)
        for entry in (
            ".github/workflows/previews.yml",
            "tools/preview_inventory.py",
            "LICENSE",
            "THIRD_PARTY_NOTICES.md",
        ):
            line = f'      - "{entry}"'
            with self.subTest(entry=entry):
                self.assertEqual(source.count(line), 2,
                                 f"{entry} must trigger previews on both PRs and main pushes")


if __name__ == "__main__":
    unittest.main()
