"""Тесты сохранения PDF-папки для текущего пользователя."""

import json
import tempfile
import unittest
from pathlib import Path

from pdf_settings import load_pdf_labels_dir, save_pdf_labels_dir


class PdfSettingsTests(unittest.TestCase):
    def test_missing_settings_uses_default_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"

            result = load_pdf_labels_dir("D:/default-labels", settings_path)

        self.assertEqual(result, Path("D:/default-labels"))

    def test_selected_directory_is_saved_and_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"
            selected = Path(temp_dir) / "PDF labels"

            save_pdf_labels_dir(selected, settings_path)
            result = load_pdf_labels_dir("D:/default-labels", settings_path)

        self.assertEqual(result, selected)

    def test_invalid_settings_uses_default_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"
            settings_path.write_text("not json", encoding="utf-8")

            result = load_pdf_labels_dir("D:/default-labels", settings_path)

        self.assertEqual(result, Path("D:/default-labels"))

    def test_saving_keeps_unrelated_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"
            settings_path.write_text(
                json.dumps({"other_setting": "kept"}),
                encoding="utf-8",
            )

            save_pdf_labels_dir("C:/labels", settings_path)
            data = json.loads(settings_path.read_text(encoding="utf-8"))

        self.assertEqual(data["other_setting"], "kept")
        self.assertEqual(data["pdf_labels_dir"], str(Path("C:/labels")))


if __name__ == "__main__":
    unittest.main()
