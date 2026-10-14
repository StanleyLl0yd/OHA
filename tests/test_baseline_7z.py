"""Independent 7-Zip benchmark contract tests, actual baseline optional locally."""

import importlib.util
import shutil
import sys
import tempfile
import unittest
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

    def test_empty_input_and_invalid_parameters(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with self.assertRaises(ValueError):
                base.input_manifest(root, [])
            with self.assertRaises(ValueError):
                base.measure(root, [], sevenzip="7z", repetitions=0)

    @unittest.skipUnless(shutil.which("7z"), "7-Zip executable not installed")
    def test_7z_real_archive_integration(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "source"
            root.mkdir()
            (root / "a.txt").write_bytes(b"abc" * 200)
            (root / "b.txt").write_bytes(b"hello" * 10)
            files = sorted(root.iterdir())
            result = base.measure(root, files, sevenzip="7z", repetitions=1)
            self.assertEqual(len(result["runs"]), 2)
            self.assertTrue(all(x["integrity"].endswith("verified") for x in result["runs"]))


if __name__ == "__main__":
    unittest.main()
