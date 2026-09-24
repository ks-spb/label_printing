"""Проверки параллельной установки тестовой версии."""

import re
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
        cls.app_source = (PROJECT_ROOT / "label_printing.py").read_text(
            encoding="utf-8"
        )
        cls.notices = (PROJECT_ROOT / "THIRD_PARTY_NOTICES.txt").read_text(
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

    def test_application_and_installer_versions_match(self) -> None:
        installer_version = re.search(
            r'#define MyAppVersion "([^"]+)"', self.installer
        )
        app_version = re.search(r'APP_VERSION = "([^"]+)"', self.app_source)

        self.assertIsNotNone(installer_version)
        self.assertIsNotNone(app_version)
        self.assertEqual(installer_version.group(1), "1.1.4")
        self.assertEqual(app_version.group(1), installer_version.group(1))

    def test_build_bundles_verified_sumatra_pdf(self) -> None:
        self.assertIn('$sumatraVersion = "3.6.1"', self.build_script)
        self.assertIn(
            "98B33A518D42986856D225064B0CD2D3643ECF78CBF84AB873D26CC51877A544",
            self.build_script,
        )
        self.assertIn("Get-FileHash", self.build_script)
        self.assertIn('--add-binary "$sumatraExecutable;sumatra"', self.build_script)
        self.assertIn("THIRD_PARTY_NOTICES.txt", self.build_script)
        self.assertIn("SumatraPDF 3.6.1", self.notices)


if __name__ == "__main__":
    unittest.main()
