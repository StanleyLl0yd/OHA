# SPDX-License-Identifier: MPL-2.0
"""Tar baseline round-trip verification tests; never use unsafe extractall."""

import importlib.util
import shutil
from types import SimpleNamespace
from unittest.mock import patch
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
            original = base.input_manifest(corpus, files)
            base.make_tar(corpus, files, archive)
            base.verify_tar(archive, original)
            (corpus / "one").write_bytes(b"xyz" * 1000)
            # An intact archive is still validated against its ORIGINAL bytes.
            base.verify_tar(archive, original)
            self.assertNotEqual(base.input_manifest(corpus, files), original)
            changed_archive = root / "changed.tar"
            base.make_tar(corpus, files, changed_archive)
            with self.assertRaisesRegex(RuntimeError, "SHA-256"):
                base.verify_tar(changed_archive, original)

    def test_duplicate_and_symlink_inputs_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            file = root / "data"
            file.write_bytes(b"data")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                base.input_manifest(root, [file, file])
            other = root / "elsewhere"
            other.mkdir()
            (other / "outside").write_bytes(b"outside")
            with self.assertRaisesRegex(ValueError, "within"):
                base.input_manifest(other, [file])
            link = root / "link"
            try:
                link.symlink_to(file)
            except (NotImplementedError, OSError):
                pass
            else:
                with self.assertRaisesRegex(ValueError, "unsupported"):
                    base.input_manifest(root, [link])

    @unittest.skipUnless(shutil.which("xz"), "XZ CLI not installed")
    def test_measure_rejects_mutation_after_tar_was_packed(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            file = source / "original"
            file.write_bytes(b"abc" * 1000)
            original_make = base.make_tar
            mutated = False

            def change_after_pack(root, paths, destination):
                nonlocal mutated
                result = original_make(root, paths, destination)
                if not mutated:
                    file.write_bytes(b"XYZ" * 1000)
                    mutated = True
                return result

            with patch.object(base, "make_tar", side_effect=change_after_pack):
                with self.assertRaisesRegex(RuntimeError, "source corpus changed"):
                    base.measure_directory(source, [file], repetitions=1)
            self.assertTrue(mutated)

    def test_empty_corpus_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                base.measure_directory(Path(directory), [], 1)

    def test_codec_version_banner(self):
        with patch.object(base.subprocess, "run", return_value=SimpleNamespace(
                returncode=0, stdout="\n", stderr="  xz 5.6.0\n")):
            self.assertEqual(base.codec_version("xz"), "xz 5.6.0")
        with patch.object(base.subprocess, "run", return_value=SimpleNamespace(
                returncode=0, stdout="   ", stderr="\n")):
            with self.assertRaisesRegex(RuntimeError, "empty"):
                base.codec_version("xz")

    @unittest.skipUnless(shutil.which("xz"), "XZ CLI not installed")
    def test_real_tar_baseline_reproducible_run_order(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "a.txt").write_bytes(b"hello " * 120)
            result = base.measure_directory(source, [source / "a.txt"], repetitions=2)
            codecs = {record["codec"] for record in result["runs"]}
            expected = {(n, codec) for n in (1, 2) for codec in codecs}
            actual = {(record["repetition"], record["codec"]) for record in result["runs"]}
            self.assertEqual(actual, expected)
            self.assertEqual(result["method"]["run_order_seed"], 271828)
            self.assertTrue(result["tool_versions"])
            self.assertTrue(all(rec["status"] == "sha256-verified" for rec in result["runs"]))
            self.assertEqual({rec["order_position"] for rec in result["runs"]},
                             set(range(1, len(result["runs"]) + 1)))

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
