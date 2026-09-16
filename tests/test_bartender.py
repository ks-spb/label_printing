"""Тесты необязательной интеграции с BarTender."""

import tempfile
import unittest
from pathlib import Path

from bartender import BarTenderUnavailableError, resolve_bartender_executable


class BarTenderTests(unittest.TestCase):
    def test_missing_setting_is_reported_only_when_resolved(self) -> None:
        with self.assertRaises(BarTenderUnavailableError) as context:
            resolve_bartender_executable(None)

        self.assertIn("требуется BarTender", str(context.exception))
        self.assertIn("PDF-этикетки можно печатать без BarTender", str(context.exception))

    def test_missing_executable_has_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            expected = Path(temp_dir) / "bartend.exe"

            with self.assertRaises(BarTenderUnavailableError) as context:
                resolve_bartender_executable(temp_dir)

        self.assertIn(str(expected), str(context.exception))

    def test_directory_or_full_executable_path_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            executable = Path(temp_dir) / "bartend.exe"
            executable.write_bytes(b"test")

            self.assertEqual(resolve_bartender_executable(temp_dir), executable)
            self.assertEqual(
                resolve_bartender_executable(str(executable)),
                executable,
            )


if __name__ == "__main__":
    unittest.main()
