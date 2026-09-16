"""Поиск PDF-этикеток по имени файла."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable


class PdfLabelDirectoryError(RuntimeError):
    """Папка PDF-этикеток недоступна или не может быть прочитана."""


def _natural_sort_key(path: Path) -> tuple[tuple[int, str | int], ...]:
    """Возвращает ключ, сортирующий числовые части как числа."""
    parts = re.split(r"(\d+)", path.stem.casefold())
    return tuple(
        (1, int(part)) if part.isdigit() else (0, part)
        for part in parts
        if part
    )


def _toggle_first_zero(value: str) -> str | None:
    """Добавляет или удаляет ровно один ведущий ноль."""
    if not value:
        return None
    if value.startswith("0"):
        return value[1:] or None
    return f"0{value}"


def _is_zero_equivalent(stem: str, query: str) -> bool:
    """Проверяет равенство после одного изменения ведущего нуля."""
    query_variant = _toggle_first_zero(query)
    stem_variant = _toggle_first_zero(stem)
    return stem == query_variant or stem_variant == query


def _is_prefix_match(stem: str, query: str) -> bool:
    """Проверяет буквальный префикс с учётом одного ведущего нуля."""
    if stem.startswith(query):
        return True
    query_variant = _toggle_first_zero(query)
    if query_variant and stem.startswith(query_variant):
        return True
    stem_variant = _toggle_first_zero(stem)
    return bool(stem_variant and stem_variant.startswith(query))


def _unique_sorted(paths: Iterable[Path]) -> list[Path]:
    """Удаляет дубли путей и применяет естественную сортировку."""
    unique = {str(path).casefold(): path for path in paths}
    return sorted(unique.values(), key=_natural_sort_key)


def load_pdf_index(directory: str | Path) -> tuple[Path, ...]:
    """Один раз загружает PDF-файлы непосредственно из указанной папки."""
    folder = Path(directory)
    try:
        if not folder.exists() or not folder.is_dir():
            raise PdfLabelDirectoryError(
                f"Папка PDF-этикеток недоступна: {folder}"
            )
        pdf_files = (
            item.resolve()
            for item in folder.iterdir()
            if item.is_file() and item.suffix.casefold() == ".pdf"
        )
        return tuple(_unique_sorted(pdf_files))
    except PdfLabelDirectoryError:
        raise
    except OSError as exc:
        raise PdfLabelDirectoryError(
            f"Не удалось прочитать папку PDF-этикеток: {folder}"
        ) from exc


def find_pdf_matches(query: str, index: Iterable[Path]) -> list[Path]:
    """Ищет точные, zero-equivalent и затем префиксные совпадения."""
    normalized_query = query.strip().casefold()
    if not normalized_query:
        return []

    paths = list(index)
    exact = [path for path in paths if path.stem.casefold() == normalized_query]
    if exact:
        return _unique_sorted(exact)

    zero_exact = [
        path
        for path in paths
        if _is_zero_equivalent(path.stem.casefold(), normalized_query)
    ]
    if zero_exact:
        return _unique_sorted(zero_exact)

    prefix = [
        path
        for path in paths
        if _is_prefix_match(path.stem.casefold(), normalized_query)
    ]
    return _unique_sorted(prefix)
