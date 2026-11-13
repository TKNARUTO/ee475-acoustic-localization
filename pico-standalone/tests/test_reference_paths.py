"""Public reference selection must not depend on a retired root app."""
from pathlib import Path
import tempfile
import unittest

from run_offline_validation import REFERENCE_APP, resolve_reference_app, build_native


def reference(folder):
    folder.mkdir(parents=True)
    for name in ("beacon_dsp.py", "highband_dsp.py", "arrival_dsp.py", "array_geometry.json"):
        (folder / name).write_text("{}", encoding="utf-8")
    return folder.resolve()


class ReferencePaths(unittest.TestCase):
    def test_legacy_preferred_over_retired_root(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            expected = reference(project / REFERENCE_APP)
            reference(project / "SEN0325-Pico-Setup")
            self.assertEqual(resolve_reference_app(project), expected)

    def test_explicit_override(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            reference(project / REFERENCE_APP)
            selected = reference(project / "chosen-reference")
            self.assertEqual(resolve_reference_app(project, selected), selected)

    def test_root_only_does_not_silently_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            reference(project / "SEN0325-Pico-Setup")
            with self.assertRaisesRegex(FileNotFoundError, "reference-app"):
                resolve_reference_app(project)

    def test_incomplete_override_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            reference(project / REFERENCE_APP)
            with self.assertRaises(FileNotFoundError):
                resolve_reference_app(project, project / "missing")

    def test_missing_native_compiler_has_actionable_error(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            with self.assertRaisesRegex(FileNotFoundError, "--gcc"):
                build_native(project, project, project / "nonexistent-native-gcc")


if __name__ == "__main__":
    unittest.main()
