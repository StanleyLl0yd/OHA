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
        bootstrap = (ROOT / "docs/GITHUB_BOOTSTRAP.md").read_text(encoding="utf-8")
        self.assertIn("MPL-2.0", research)
        self.assertIn("MPL-2.0", adr)
        self.assertIn("2026-10-14", research)
        self.assertIn("ACCEPTED", adr)
        self.assertIn("OPEN", research)
        self.assertIn("Third-party binary redistribution clearance", research)
        self.assertIn("issue [#40]", research)
        self.assertIn("issue #40 tracks", adr)
        self.assertIn("#4 was closed", research)
        notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        preview = (ROOT / "docs/PREVIEW_M0.md").read_text(encoding="utf-8")
        self.assertIn("#40 remains open", notices)
        self.assertIn("#40 remains open", preview)
        self.assertNotIn("Issue #4 stays OPEN", notices)
        self.assertIn("accepted MPL-2.0", overview)
        self.assertIn("third-party binary redistribution gate", overview)
        self.assertNotIn("application LICENSE and precise dependency versions remain unresolved", overview)
        self.assertIn("later on 2026-10-14 the owner approved MPL-2.0", bootstrap)
        self.assertIn("third-party binary redistribution clearance", bootstrap)
        self.assertNotIn("No repository LICENSE has been selected.", bootstrap)
        self.assertNotIn("Project license still requires owner approval", research)
        self.assertNotIn("Do not add a `LICENSE` file until approved", research)


if __name__ == "__main__":
    unittest.main()
