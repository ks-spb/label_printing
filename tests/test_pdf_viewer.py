"""Тесты Windows-адаптера открытия и печати PDF."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pdf_viewer import (
    PdfViewerError,
    SumatraUnavailableError,
    _sumatra_print,
    _windows_associated_print,
    open_pdf,
    print_pdf,
)


class PdfViewerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.pdf_path = Path(self.temp_dir.name) / "label.pdf"
        self.pdf_path.write_bytes(b"pdf")

    def test_open_uses_registered_open_verb(self) -> None:
        calls: list[tuple[str, str]] = []

        open_pdf(self.pdf_path, launcher=lambda path, verb: calls.append((path, verb)))

        self.assertEqual(calls, [(str(self.pdf_path.resolve()), "open")])

    def test_print_dispatches_all_copies_in_one_batch(self) -> None:
        calls: list[tuple[Path, int]] = []

        dispatched = print_pdf(
            self.pdf_path,
            copies=20,
            batch_launcher=lambda path, copies: calls.append((path, copies)),
        )

        self.assertEqual(dispatched, 20)
        self.assertEqual(calls, [(self.pdf_path.resolve(), 20)])

    def test_sumatra_command_uses_copy_count_fit_and_separate_path_arguments(
        self,
    ) -> None:
        executable = Path(self.temp_dir.name) / "Sumatra PDF.exe"
        executable.write_bytes(b"exe")
        appdata = Path(self.temp_dir.name) / "настройки Sumatra"
        pdf_path = Path(self.temp_dir.name) / "русская этикетка 01.pdf"
        pdf_path.write_bytes(b"pdf")
        calls: list[tuple[list[str], dict[str, object]]] = []

        class Result:
            returncode = 0

        def runner(command: list[str], **kwargs: object) -> Result:
            calls.append((command, kwargs))
            return Result()

        _sumatra_print(
            pdf_path.resolve(),
            copies=20,
            executable=executable,
            appdata_directory=appdata,
            runner=runner,
        )

        self.assertEqual(len(calls), 1)
        command, options = calls[0]
        self.assertEqual(
            command,
            [
                str(executable),
                "-appdata",
                str(appdata),
                "-print-to-default",
                "-print-settings",
                "20x,fit",
                "-silent",
                str(pdf_path.resolve()),
            ],
        )
        self.assertIs(options["shell"], False)
        self.assertEqual(options["timeout"], 300)

    def test_missing_sumatra_falls_back_to_legacy_printing(self) -> None:
        calls: list[tuple[str, str]] = []

        def missing_batch(path: Path, copies: int) -> None:
            _sumatra_print(
                path,
                copies,
                executable=Path(self.temp_dir.name) / "missing.exe",
            )

        dispatched = print_pdf(
            self.pdf_path,
            copies=3,
            batch_launcher=missing_batch,
            launcher=lambda path, verb: calls.append((path, verb)),
        )

        self.assertEqual(dispatched, 3)
        self.assertEqual([verb for _path, verb in calls], ["print"] * 3)

    def test_unlaunchable_sumatra_falls_back_to_legacy_printing(self) -> None:
        executable = Path(self.temp_dir.name) / "SumatraPDF.exe"
        executable.write_bytes(b"exe")
        legacy_calls: list[tuple[str, str]] = []

        def unavailable_batch(path: Path, copies: int) -> None:
            _sumatra_print(
                path,
                copies,
                executable=executable,
                appdata_directory=Path(self.temp_dir.name) / "settings",
                runner=lambda _command, **_kwargs: (_ for _ in ()).throw(
                    OSError("process blocked")
                ),
            )

        dispatched = print_pdf(
            self.pdf_path,
            copies=2,
            batch_launcher=unavailable_batch,
            launcher=lambda path, verb: legacy_calls.append((path, verb)),
        )

        self.assertEqual(dispatched, 2)
        self.assertEqual([verb for _path, verb in legacy_calls], ["print"] * 2)

    def test_legacy_print_reports_dispatched_copies_before_error(self) -> None:
        calls = 0

        def failing_launcher(_path: str, _verb: str) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("association failed")

        with self.assertRaises(PdfViewerError) as context:
            print_pdf(
                self.pdf_path,
                copies=3,
                batch_launcher=lambda _path, _copies: (_ for _ in ()).throw(
                    SumatraUnavailableError("missing")
                ),
                launcher=failing_launcher,
                fallback_launcher=lambda _path: (_ for _ in ()).throw(
                    OSError("fallback association failed")
                ),
            )

        self.assertEqual(context.exception.dispatched, 1)
        self.assertIn("Передано копий: 1", str(context.exception))
        self.assertIn("association failed", str(context.exception))

    def test_print_uses_registered_command_when_startfile_fails(self) -> None:
        fallback_calls: list[str] = []

        dispatched = print_pdf(
            self.pdf_path,
            copies=1,
            batch_launcher=lambda _path, _copies: (_ for _ in ()).throw(
                SumatraUnavailableError("missing")
            ),
            launcher=lambda _path, _verb: (_ for _ in ()).throw(
                OSError("startfile failed")
            ),
            fallback_launcher=fallback_calls.append,
        )

        self.assertEqual(dispatched, 1)
        self.assertEqual(fallback_calls, [str(self.pdf_path.resolve())])

    def test_batch_failure_does_not_repeat_print_through_legacy_route(self) -> None:
        legacy_calls: list[tuple[str, str]] = []

        with self.assertRaisesRegex(PdfViewerError, "Проверьте очередь"):
            print_pdf(
                self.pdf_path,
                copies=20,
                batch_launcher=lambda _path, _copies: (_ for _ in ()).throw(
                    PdfViewerError(
                        "Ошибка. Проверьте очередь принтера перед повтором."
                    )
                ),
                launcher=lambda path, verb: legacy_calls.append((path, verb)),
            )

        self.assertEqual(legacy_calls, [])

    def test_sumatra_nonzero_exit_is_an_uncertain_print_error(self) -> None:
        executable = Path(self.temp_dir.name) / "SumatraPDF.exe"
        executable.write_bytes(b"exe")

        class Result:
            returncode = 7

        with self.assertRaisesRegex(PdfViewerError, "код 7") as context:
            _sumatra_print(
                self.pdf_path.resolve(),
                copies=2,
                executable=executable,
                appdata_directory=Path(self.temp_dir.name) / "settings",
                runner=lambda _command, **_kwargs: Result(),
            )

        self.assertIn("Проверьте очередь", str(context.exception))

    def test_sumatra_timeout_is_an_uncertain_print_error(self) -> None:
        executable = Path(self.temp_dir.name) / "SumatraPDF.exe"
        executable.write_bytes(b"exe")

        def timeout_runner(command: list[str], **_kwargs: object) -> None:
            raise subprocess.TimeoutExpired(command, 300)

        with self.assertRaisesRegex(PdfViewerError, "5 минут") as context:
            _sumatra_print(
                self.pdf_path.resolve(),
                copies=2,
                executable=executable,
                appdata_directory=Path(self.temp_dir.name) / "settings",
                runner=timeout_runner,
            )

        self.assertIn("Проверьте очередь", str(context.exception))

    @patch("pdf_viewer.subprocess.Popen")
    @patch("pdf_viewer._windows_pdf_print_command")
    def test_registered_command_receives_pdf_path_once(
        self, command_mock, popen_mock
    ) -> None:
        command_mock.return_value = (
            '"C:\\Program Files\\Adobe\\Acrobat.exe" /p /h "%1"'
        )
        pdf_path = r"C:\\PDF labels\\030001.pdf"

        _windows_associated_print(pdf_path)

        popen_mock.assert_called_once_with(
            '"C:\\Program Files\\Adobe\\Acrobat.exe" /p /h '
            '"C:\\PDF labels\\030001.pdf"',
            shell=False,
        )

    def test_open_wraps_file_association_error(self) -> None:
        def failing_launcher(_path: str, _verb: str) -> None:
            raise OSError("no handler")

        with self.assertRaises(PdfViewerError):
            open_pdf(self.pdf_path, launcher=failing_launcher)

    def test_missing_or_non_pdf_file_is_rejected(self) -> None:
        with self.assertRaises(PdfViewerError):
            open_pdf(Path(self.temp_dir.name) / "missing.pdf")
        text_path = Path(self.temp_dir.name) / "label.txt"
        text_path.write_text("text", encoding="utf-8")
        with self.assertRaises(PdfViewerError):
            open_pdf(text_path)

    def test_zero_copies_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            print_pdf(self.pdf_path, copies=0)


if __name__ == "__main__":
    unittest.main()
