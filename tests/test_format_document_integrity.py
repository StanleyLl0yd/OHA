# SPDX-License-Identifier: MPL-2.0
"""Protect the unapproved format proposal from accidental duplicated sections."""
from pathlib import Path
import unittest

DOC = Path(__file__).resolve().parents[1] / "docs" / "FORMAT_V1_PROPOSAL.md"


class FormatProposalIntegrityTests(unittest.TestCase):
    def test_main_sections_are_not_duplicated_or_truncated(self):
        source = DOC.read_text(encoding="utf-8")
        for marker in (
            "# Candidate `.oha` wire format v1 (M0 design proposal only)",
            "## 1. 64-byte archive header at offset zero",
            "## 2. Physical frame sequence (candidate)",
            "## 3. Footer: final 128 bytes at EOF",
            "## Candidate portable path semantics (research-only)",
            "### Extended Win32 console-name negatives (M0)",
        ):
            with self.subTest(marker=marker):
                self.assertEqual(source.count(marker), 1)
        self.assertLess(len(source.splitlines()), 200, "Unexpected duplicated format proposal")
        self.assertIn("including superscript COM/LPT digits", source)
        self.assertIn("CONIN$", source)
        self.assertIn("CONOUT$", source)
        self.assertIn("CLOCK$", source)


if __name__ == "__main__":
    unittest.main()
