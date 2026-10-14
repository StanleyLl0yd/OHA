# SPDX-License-Identifier: MPL-2.0
"""Tar baseline round-trip verification tests; never use unsafe extractall."""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
spec = importlib.util.spec_from_file_location("oha_tar_baseline", ROOT / "tools" / "baseline_tar.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


class BaselineTests(unittest.TestCase):
    def test_tar_roundtrip_and_reject_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "one").write_bytes(b"abc" * 1000)
            (corpus / "two").write_bytes(b"")
            files = sorted(corpus.iterdir())
            archive = root / "a.tar"
            base.make_tar(corpus, files, archive)
            base.verify_tar(archive, corpus, files)
            (corpus / "one").write_bytes(b"xyz" * 1000)
            with self.assertRaisesRegex(RuntimeError, "SHA-256"):
                base.verify_tar(archive, corpus, files)

    def test_empty_corpus_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                base.measure_directory(Path(directory), [], 1)

    def test_tar_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "a").write_bytes(b"ab" * 10)
            (corpus / "b").write_bytes(b"\0" * 10)
            a, b = root / "a.tar", root / "b.tar"
            base.make_tar(corpus, sorted(corpus.iterdir()), a)
            base.make_tar(corpus, sorted(corpus.iterdir()), b)
            self.assertEqual(a.read_bytes(), b.read_bytes())


if __name__ == "__main__":
    unittest.main()
