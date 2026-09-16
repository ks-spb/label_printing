"""Тесты PDF-first маршрутизации без запуска Tkinter и чтения .env."""

import unittest
from pathlib import Path

from label_printing import LabelPrintingApp, dispatch_label_action, is_valid_count
from label_search import PdfLabelDirectoryError


class LabelWorkflowTests(unittest.TestCase):
    def test_single_match_opens_immediately_without_chooser(self) -> None:
        opened: list[Path] = []

        result = dispatch_label_action(
            query="  ital2kg  ",
            count=0,
            pdf_index=[Path("ital2kg.pdf")],
            chooser=lambda _paths: self.fail("chooser must not be called"),
            open_action=opened.append,
            print_action=lambda _path, _count: self.fail("print must not be called"),
            fallback_action=lambda _query, _count: self.fail("fallback must not run"),
        )

        self.assertEqual(result, "open")
        self.assertEqual(opened, [Path("ital2kg.pdf")])

    def test_multiple_matches_offer_choice_and_print_selected_file(self) -> None:
        printed: list[tuple[Path, int]] = []
        index = [Path("020062-2.pdf"), Path("020062-1.pdf")]

        result = dispatch_label_action(
            query="20062",
            count=4,
            pdf_index=index,
            chooser=lambda paths: paths[1],
            open_action=lambda _path: self.fail("open must not be called"),
            print_action=lambda path, count: printed.append((path, count)),
            fallback_action=lambda _query, _count: self.fail("fallback must not run"),
        )

        self.assertEqual(result, "print")
        self.assertEqual(printed, [(Path("020062-2.pdf"), 4)])

    def test_cancelled_choice_does_not_run_any_action_or_fallback(self) -> None:
        calls: list[str] = []

        result = dispatch_label_action(
            query="20062",
            count=1,
            pdf_index=[Path("020062-1.pdf"), Path("020062-2.pdf")],
            chooser=lambda _paths: None,
            open_action=lambda _path: calls.append("open"),
            print_action=lambda _path, _count: calls.append("print"),
            fallback_action=lambda _query, _count: calls.append("fallback"),
        )

        self.assertEqual(result, "cancelled")
        self.assertEqual(calls, [])

    def test_no_match_uses_trimmed_original_query_and_count_for_fallback(self) -> None:
        fallback_calls: list[tuple[str, int]] = []

        result = dispatch_label_action(
            query="  SKU-alias  ",
            count=3,
            pdf_index=[Path("020058.pdf")],
            chooser=lambda _paths: None,
            open_action=lambda _path: None,
            print_action=lambda _path, _count: None,
            fallback_action=lambda query, count: fallback_calls.append((query, count)),
        )

        self.assertEqual(result, "fallback")
        self.assertEqual(fallback_calls, [("SKU-alias", 3)])

    def test_empty_query_does_nothing(self) -> None:
        calls: list[str] = []

        result = dispatch_label_action(
            query="   ",
            count=1,
            pdf_index=[],
            chooser=lambda _paths: None,
            open_action=lambda _path: calls.append("open"),
            print_action=lambda _path, _count: calls.append("print"),
            fallback_action=lambda _query, _count: calls.append("fallback"),
        )

        self.assertEqual(result, "empty")
        self.assertEqual(calls, [])

    def test_count_validator_accepts_only_empty_or_positive_integer(self) -> None:
        self.assertTrue(is_valid_count(""))
        self.assertTrue(is_valid_count("12"))
        self.assertFalse(is_valid_count("0"))
        self.assertFalse(is_valid_count("-1"))
        self.assertFalse(is_valid_count("one"))

    def test_busy_app_ignores_repeated_action(self) -> None:
        app = object.__new__(LabelPrintingApp)
        app.busy = True
        app.pdf_error = None

        app._handle_action(count=1)

        self.assertTrue(app.busy)

    def test_unavailable_pdf_directory_blocks_action_without_fallback(self) -> None:
        app = object.__new__(LabelPrintingApp)
        app.busy = False
        app.pdf_error = PdfLabelDirectoryError("missing")

        app._handle_action(count=1)

        self.assertFalse(app.busy)


if __name__ == "__main__":
    unittest.main()
