"""Открытие и печать PDF через зарегистрированный просмотрщик Windows."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Callable


Launcher = Callable[[str, str], None]
Sleeper = Callable[[float], None]


class PdfViewerError(RuntimeError):
    """Системный просмотрщик не принял команду открытия или печати."""

    def __init__(self, message: str, dispatched: int = 0) -> None:
        super().__init__(message)
        self.dispatched = dispatched


def _windows_startfile(path: str, operation: str) -> None:
    """Передаёт файл обработчику соответствующего Windows shell verb."""
    os.startfile(path, operation)  # type: ignore[attr-defined]


def _validated_pdf_path(path: str | Path) -> Path:
    """Проверяет существование PDF перед передачей внешней программе."""
    pdf_path = Path(path)
    try:
        resolved = pdf_path.resolve(strict=True)
    except OSError as exc:
        raise PdfViewerError(f"PDF-файл недоступен: {pdf_path}") from exc
    if not resolved.is_file() or resolved.suffix.casefold() != ".pdf":
        raise PdfViewerError(f"Файл не является PDF-этикеткой: {resolved}")
    return resolved


def open_pdf(path: str | Path, launcher: Launcher = _windows_startfile) -> None:
    """Открывает PDF в приложении, зарегистрированном в Windows."""
    pdf_path = _validated_pdf_path(path)
    try:
        launcher(str(pdf_path), "open")
    except (OSError, AttributeError) as exc:
        raise PdfViewerError(
            "Не удалось открыть PDF через установленный просмотрщик."
        ) from exc


def print_pdf(
    path: str | Path,
    copies: int,
    launcher: Launcher = _windows_startfile,
    sleeper: Sleeper = time.sleep,
    delay_seconds: float = 1.0,
) -> int:
    """Последовательно передаёт Windows одну команду печати на копию."""
    if copies < 1:
        raise ValueError("Количество копий должно быть больше нуля.")
    pdf_path = _validated_pdf_path(path)
    dispatched = 0
    for copy_number in range(copies):
        try:
            launcher(str(pdf_path), "print")
        except (OSError, AttributeError) as exc:
            raise PdfViewerError(
                f"Не удалось передать PDF в печать. Передано копий: {dispatched}.",
                dispatched=dispatched,
            ) from exc
        dispatched += 1
        if copy_number + 1 < copies:
            sleeper(delay_seconds)
    return dispatched
