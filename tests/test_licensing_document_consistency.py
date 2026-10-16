# SPDX-License-Identifier: MPL-2.0
"""Ensure M0 licensing research cannot revert the accepted source license."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LicensingDocumentConsistencyTests(unittest.TestCase):
    def test_research_and_accepted_adr_agree_on_mpl_and_open_release_gate(self):
        research = (ROOT / "docs/LICENSING_RESEARCH.md").read_text(encoding="utf-8")
        adr = (ROOT / "docs/adr/0004-licensing.md").read_text(encoding="utf-8")
        overview = (ROOT / "docs/RESEARCH.md").read_text(encoding="utf-8")
        self.assertIn("MPL-2.0", research)
        self.assertIn("MPL-2.0", adr)
        self.assertIn("2026-10-14", research)
        self.assertIn("ACCEPTED", adr)
        self.assertIn("OPEN", research)
        self.assertIn("Third-party redistribution clearance", research)
        self.assertIn("accepted MPL-2.0", overview)
        self.assertIn("third-party binary redistribution gate", overview)
        self.assertNotIn("application LICENSE and precise dependency versions remain unresolved", overview)
        self.assertNotIn("Project license still requires owner approval", research)
        self.assertNotIn("Do not add a `LICENSE` file until approved", research)


if __name__ == "__main__":
    unittest.main()
