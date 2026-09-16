"""Тесты Windows-адаптера открытия и печати PDF."""

import tempfile
import unittest
from pathlib import Path

from pdf_viewer import PdfViewerError, open_pdf, print_pdf


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

    def test_print_dispatches_one_command_per_copy_with_delays(self) -> None:
        calls: list[tuple[str, str]] = []
        sleeps: list[float] = []

        dispatched = print_pdf(
            self.pdf_path,
            copies=3,
            launcher=lambda path, verb: calls.append((path, verb)),
            sleeper=sleeps.append,
        )

        self.assertEqual(dispatched, 3)
        self.assertEqual([verb for _path, verb in calls], ["print"] * 3)
        self.assertEqual(sleeps, [1.0, 1.0])

    def test_print_reports_how_many_copies_were_dispatched_before_error(self) -> None:
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
                launcher=failing_launcher,
                sleeper=lambda _delay: None,
            )

        self.assertEqual(context.exception.dispatched, 1)
        self.assertIn("Передано копий: 1", str(context.exception))

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
