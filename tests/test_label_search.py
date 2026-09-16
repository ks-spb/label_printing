"""Тесты кэша и правил поиска PDF-этикеток."""

import tempfile
import unittest
from pathlib import Path

from label_search import (
    PdfLabelDirectoryError,
    find_pdf_matches,
    load_pdf_index,
)


class LabelSearchTests(unittest.TestCase):
    def test_loads_only_direct_pdf_files_in_natural_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            (folder / "020062-10.pdf").write_bytes(b"pdf")
            (folder / "020062-2.PDF").write_bytes(b"pdf")
            (folder / "note.txt").write_text("ignore", encoding="utf-8")
            nested = folder / "nested"
            nested.mkdir()
            (nested / "020062-1.pdf").write_bytes(b"pdf")

            index = load_pdf_index(folder)

            self.assertEqual(
                [path.name for path in index],
                ["020062-2.PDF", "020062-10.pdf"],
            )

    def test_missing_or_non_directory_path_raises_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            with self.assertRaises(PdfLabelDirectoryError):
                load_pdf_index(folder / "missing")
            file_path = folder / "label.pdf"
            file_path.write_bytes(b"pdf")
            with self.assertRaises(PdfLabelDirectoryError):
                load_pdf_index(file_path)

    def test_exact_match_has_priority_over_prefixes(self) -> None:
        index = [Path("020062-1.pdf"), Path("020062.pdf"), Path("020062-2.pdf")]

        matches = find_pdf_matches("020062", index)

        self.assertEqual(matches, [Path("020062.pdf")])

    def test_exact_match_is_case_insensitive(self) -> None:
        index = [Path("ITAL2KG.PDF"), Path("ital2kg-2.pdf")]

        self.assertEqual(find_pdf_matches("ital2kg", index), [Path("ITAL2KG.PDF")])

    def test_toggles_exactly_one_leading_zero_in_both_directions(self) -> None:
        self.assertEqual(
            find_pdf_matches("20058", [Path("020058.pdf")]),
            [Path("020058.pdf")],
        )
        self.assertEqual(
            find_pdf_matches("030001", [Path("30001.pdf")]),
            [Path("30001.pdf")],
        )
        self.assertEqual(find_pdf_matches("20058", [Path("0020058.pdf")]), [])

    def test_prefix_match_supports_zero_variant_and_natural_sort(self) -> None:
        index = [
            Path("020062-10.pdf"),
            Path("020062-2.pdf"),
            Path("020062-1.pdf"),
        ]

        matches = find_pdf_matches("20062", index)

        self.assertEqual(
            [path.name for path in matches],
            ["020062-1.pdf", "020062-2.pdf", "020062-10.pdf"],
        )

    def test_text_and_punctuation_are_matched_literally(self) -> None:
        index = [
            Path("ital2kg-blue.pdf"),
            Path("12-0225-60-120-80.pdf"),
            Path("12-0225-60-120-80-2.pdf"),
        ]

        self.assertEqual(
            find_pdf_matches("ital2kg", index),
            [Path("ital2kg-blue.pdf")],
        )
        self.assertEqual(
            find_pdf_matches("12-0225-60-120-80", index),
            [Path("12-0225-60-120-80.pdf")],
        )

    def test_empty_query_does_not_match_every_file(self) -> None:
        self.assertEqual(find_pdf_matches("   ", [Path("020058.pdf")]), [])

    def test_loaded_index_does_not_change_until_reloaded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            (folder / "020058.pdf").write_bytes(b"pdf")
            cached_index = load_pdf_index(folder)
            (folder / "020059.pdf").write_bytes(b"pdf")

            self.assertEqual(find_pdf_matches("020059", cached_index), [])
            self.assertEqual(
                [path.name for path in load_pdf_index(folder)],
                ["020058.pdf", "020059.pdf"],
            )


if __name__ == "__main__":
    unittest.main()
