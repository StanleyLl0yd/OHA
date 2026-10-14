# SPDX-License-Identifier: MPL-2.0
"""Unit tests for the M0 Python research harness."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


benchmark = load_module("oha_bench", ROOT / "tools" / "benchmark.py")
corpus = load_module("oha_corpus", ROOT / "tools" / "make_corpus.py")


class HarnessTests(unittest.TestCase):
    def test_generated_corpus_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = corpus.generate(root / "one")
            second = corpus.generate(root / "two")
            self.assertEqual(len(first), 6)
            self.assertEqual([benchmark.hash_file(x) for x in first],
                             [benchmark.hash_file(x) for x in second])

    def test_store_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "sample.dat"
            file.write_bytes(b"hello\x00world" * 128)
            rows = benchmark.measure_file(file, repetitions=2, codec_names=["STORE"])
            self.assertEqual(len(rows), 2)
            self.assertTrue(all(x["status"] == "ok" for x in rows))
            self.assertTrue(all(x["encoded_bytes"] == file.stat().st_size for x in rows))

    def test_discover_excludes_symlinks_and_large_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "small").write_bytes(b"hello")
            (root / "large").write_bytes(b"hello world" * 100)
            self.assertEqual([x.name for x in benchmark.discover(root, 10, 5)], ["small"])

    def test_unknown_codec_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample"
            path.write_bytes(b"hi")
            with self.assertRaises(ValueError):
                benchmark.measure_file(path, codec_names=["MADEUP"])

    def test_available_codecs_decode(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "sample.dat"
            file.write_bytes(b"A" * 20_000 + bytes(range(256)) * 50)
            available = [name for name, info in benchmark.codecs_present().items()
                         if name == "STORE" or info is not None]
            rows = benchmark.measure_file(file, repetitions=1, codec_names=available)
            self.assertEqual(len(rows), len(available))
            self.assertTrue(all(row["status"] == "ok" for row in rows))


if __name__ == "__main__":
    unittest.main()

class HarnessBoundaryTests(unittest.TestCase):
    def test_file_count_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for i in range(4):
                (root / f"file-{i}").write_bytes(b"a")
            with self.assertRaises(ValueError):
                benchmark.discover(root, max_files=3, max_file_bytes=128)

    def test_scan_limit_is_enforced_even_for_skipped_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for i in range(5):
                (root / f"skip-{i}").write_bytes(b"A" * 20)
            with self.assertRaisesRegex(ValueError, "scan entries"):
                benchmark.discover(root, max_files=10, max_file_bytes=2,
                                   max_scan_entries=3)

    def test_total_size_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for i in range(3):
                (root / f"file-{i}").write_bytes(b"abcde")
            with self.assertRaisesRegex(ValueError, "corpus exceeds"):
                benchmark.discover(root, max_files=10, max_file_bytes=30,
                                   max_total_bytes=10)

    def test_empty_codec_list_is_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input"
            path.write_bytes(b"hello")
            with self.assertRaises(ValueError):
                benchmark.measure_file(path, codec_names=[])

    def test_symlink_file_not_included(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "real").write_bytes(b"hello")
            try:
                (root / "link").symlink_to(root / "real")
            except (OSError, NotImplementedError):
                self.skipTest("symlinks are not supported on this host")
            self.assertEqual([x.name for x in benchmark.discover(root, 10, 10)], ["real"])

    def test_cli_output_manifest_records_sha_and_bounds(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus_dir = root / "corpus"
            corpus_dir.mkdir()
            (corpus_dir / "sample").write_bytes(b"sample data")
            out = root / "result.json"
            status = benchmark.main([str(corpus_dir), "--output", str(out),
                                     "--repetitions", "1"])
            self.assertEqual(status, 0)
            report = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(report["files"][0]["input_sha256"],
                             benchmark.hash_file(corpus_dir / "sample"))
            self.assertEqual(report["limits"]["max_files"], 1000)

    def test_roundtrip_empty_file(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "empty"
            file.touch()
            rows = benchmark.measure_file(file, repetitions=1, codec_names=["STORE"])
            self.assertEqual(rows[0]["encoded_bytes"], 0)
            self.assertEqual(rows[0]["status"], "ok")


if __name__ == "__main__":
    unittest.main()
