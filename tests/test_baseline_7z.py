# SPDX-License-Identifier: MPL-2.0
"""Independent 7-Zip benchmark contract tests, actual baseline optional locally."""

import importlib.util
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
spec = importlib.util.spec_from_file_location("oha_baseline7z", ROOT / "tools" / "baseline_7z.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


class Baseline7ZipTests(unittest.TestCase):
    def test_manifest_rejects_symlinks_and_newline_names(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            good = root / "hello.txt"
            good.write_text("abc")
            manifest = base.input_manifest(root, [good])
            self.assertEqual(manifest["hello.txt"]["bytes"], 3)
            nested = root / "nested"
            nested.mkdir()
            with self.assertRaisesRegex(ValueError, "unsupported"):
                base.input_manifest(nested, [nested / ".." / "hello.txt"])
            linkdir = root / "symlink-dir"
            try:
                linkdir.symlink_to(nested, target_is_directory=True)
            except (NotImplementedError, OSError):
                pass
            else:
                other = nested / "file"
                other.write_bytes(b"nested")
                with self.assertRaisesRegex(ValueError, "unsupported"):
                    base.input_manifest(root, [linkdir / "file"])
            bad = root / "strange\nname"
            bad.write_bytes(b"x")
            with self.assertRaisesRegex(ValueError, "filename"):
                base.input_manifest(root, [bad])
            link = root / "link"
            try:
                link.symlink_to(good)
            except (NotImplementedError, OSError):
                pass
            else:
                with self.assertRaisesRegex(ValueError, "filename"):
                    base.input_manifest(root, [link])

    def test_verify_extract_rejects_modified_missing_and_extra(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            one = root / "one"
            one.write_bytes(b"hello")
            expected = base.input_manifest(root, [one])
            base.verify_extract(root, expected)
            one.write_bytes(b"HELLO")
            with self.assertRaisesRegex(RuntimeError, "SHA-256"):
                base.verify_extract(root, expected)
            one.write_bytes(b"hello")
            (root / "extra").write_bytes(b"z")
            with self.assertRaisesRegex(RuntimeError, "unexpected"):
                base.verify_extract(root, expected)
            (root / "extra").unlink()
            one.unlink()
            with self.assertRaisesRegex(RuntimeError, "missing"):
                base.verify_extract(root, expected)

    @unittest.skipUnless(shutil.which("7z"), "7-Zip executable not installed")
    def test_measure_rejects_source_drift_after_selective_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            file = root / "file"
            file.write_bytes(b"original" * 1000)
            original_run = base.timed_run
            calls = 0

            def mutate_after_selective(*args, **kwargs):
                nonlocal calls
                result = original_run(*args, **kwargs)
                calls += 1
                if calls == 3:
                    file.write_bytes(b"modified" * 1000)
                return result

            with patch.object(base, "timed_run", side_effect=mutate_after_selective):
                with self.assertRaisesRegex(RuntimeError, "source corpus changed"):
                    base.measure(root, [file], sevenzip="7z",
                                 repetitions=1, solid_options=(False,))
            self.assertEqual(calls, 3)

    def test_version_banner_skips_leading_blank_lines(self):
        self.assertEqual(
            base.version_banner("\n\n7-Zip (a) 24.09\nMore information\n"),
            "7-Zip (a) 24.09",
        )
        with self.assertRaisesRegex(RuntimeError, "version"):
            base.version_banner(" \n\t\n")

    def test_empty_input_and_invalid_parameters(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with self.assertRaises(ValueError):
                base.input_manifest(root, [])
            with self.assertRaises(ValueError):
                base.measure(root, [], sevenzip="7z", repetitions=0)

    @unittest.skipUnless(shutil.which("7z"), "7-Zip executable not installed")
    def test_selective_extract_with_only_large_file(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            big = root / "large-only.bin"
            big.write_bytes(b"abcdef0123456789" * (128 * 1024))
            result = base.measure(root, [big], sevenzip="7z", repetitions=1,
                                  solid_options=(False,))
            self.assertEqual(len(result["runs"]), 1)
            self.assertEqual(result["runs"][0]["selective_file"], "large-only.bin")
            self.assertEqual(result["runs"][0]["selective_input_bytes"], 2 * 1024 * 1024)

    @unittest.skipUnless(shutil.which("7z"), "7-Zip executable not installed")
    def test_7z_real_archive_integration(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "source"
            root.mkdir()
            (root / "a.txt").write_bytes(b"abc" * 200)
            (root / "b.txt").write_bytes(b"hello" * 10)
            (root / "large.bin").write_bytes(b"0123456789abcdef" * (96 * 1024))
            files = sorted(root.iterdir())
            result = base.measure(root, files, sevenzip="7z", repetitions=1)
            self.assertEqual(len(result["runs"]), 2)
            self.assertTrue(all(x["integrity"].endswith("verified") for x in result["runs"]))
            self.assertTrue(all(x["selective_input_bytes"] >= 0 for x in result["runs"]))
            self.assertEqual(result["method"]["selected_file_mode"],
                             "extract-to-disk-and-streaming-SHA256")


if __name__ == "__main__":
    unittest.main()
