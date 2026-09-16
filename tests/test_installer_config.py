"""Проверки параллельной установки тестовой версии."""

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class InstallerConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.installer = (PROJECT_ROOT / "installer" / "label_printing.iss").read_text(
            encoding="utf-8"
        )
        cls.build_script = (PROJECT_ROOT / "build_release.ps1").read_text(
            encoding="utf-8"
        )

    def test_test_version_has_separate_identity_folder_and_shortcut(self) -> None:
        self.assertIn(
            "AppId=LabelPrinting.SideBySide.{#MyAppVersion}.Test",
            self.installer,
        )
        self.assertIn(
            r"DefaultDirName=C:\LabelPrinting-{#MyAppVersion}-test",
            self.installer,
        )
        self.assertIn(r'Name: "{autodesktop}\{#MyAppName}"', self.installer)
        self.assertNotIn("C13D75DA-E430-4CCF-BBFA-17D5A0DF39A7", self.installer)

    def test_old_env_is_copied_only_for_a_fresh_test_install(self) -> None:
        old_env = r'Source: "C:\LabelPrinting\_internal\.env"'
        bundled_env = r'Source: "..\dist\label_printing\_internal\.env"'

        self.assertIn(old_env, self.installer)
        self.assertIn("external skipifsourcedoesntexist onlyifdoesntexist", self.installer)
        self.assertLess(self.installer.index(old_env), self.installer.index(bundled_env))

    def test_release_filename_contains_the_version(self) -> None:
        self.assertIn(
            "OutputBaseFilename=label_printing_{#MyAppVersion}_setup",
            self.installer,
        )
        self.assertIn('$releaseBaseName = "label_printing_$($appVersion)_setup"', self.build_script)


if __name__ == "__main__":
    unittest.main()
