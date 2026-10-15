# SPDX-License-Identifier: MPL-2.0
"""Rights-clean synthetic dataset generator tests (not representative benchmarks)."""
import importlib.util
import tempfile
from pathlib import Path
import unittest

source = Path(__file__).resolve().parents[1] / "tools" / "make_mixed_corpus.py"
spec = importlib.util.spec_from_file_location("oha_mixed_corpus", source)
corpus = importlib.util.module_from_spec(spec)
spec.loader.exec_module(corpus)


class OwnedMixedCorpusTests(unittest.TestCase):
    def test_repeatable_file_sha256_and_manifest(self):
        with tempfile.TemporaryDirectory() as root:
            first = corpus.generate(Path(root) / "first")
            second = corpus.generate(Path(root) / "second")
            self.assertEqual(first, second)
            self.assertEqual(first["file_count"], 136)
            self.assertGreater(first["total_bytes"], 9 * 1024 * 1024)
            paths = {x["path"] for x in first["files"]}
            self.assertIn("sample.sqlite", paths)
            self.assertIn("sparse-disk.img", paths)
            self.assertIn("already-compressed.zip", paths)
            self.assertIn("already-compressed.gz", paths)
            self.assertIn("uniform.bin", paths)
            for rootdir in ("first", "second"):
                for record in first["files"]:
                    file = Path(root) / rootdir / "files" / record["path"]
                    self.assertTrue(file.is_file())
                    self.assertFalse(file.is_symlink())
                    self.assertEqual(file.stat().st_size, record["bytes"])
                    self.assertEqual(corpus.file_sha256(file), record["sha256"])

    def test_nonempty_destination_rejected_without_modification(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            original = target / "existing.txt"
            original.write_text("preserve", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "empty"):
                corpus.generate(target)
            self.assertEqual(original.read_text(encoding="utf-8"), "preserve")

    def test_generator_has_no_external_corpus_dependency(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = corpus.generate(Path(temporary) / "generated")
            self.assertIn("SYNTHETIC", result["kind"])
            self.assertEqual(result["limits"]["synthetic_disk_image_bytes"],
                             8 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
