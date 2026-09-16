"""Проверка доступности BarTender для резервного маршрута .btw."""

from __future__ import annotations

from pathlib import Path


class BarTenderUnavailableError(RuntimeError):
    """BarTender не настроен или его исполняемый файл недоступен."""


def resolve_bartender_executable(configured_path: str | None) -> Path:
    """Возвращает путь к bartend.exe или понятную ошибку для пользователя."""
    value = (configured_path or "").strip().strip('"')
    if not value:
        raise BarTenderUnavailableError(
            "Этикетка не найдена среди PDF, поэтому для неё требуется BarTender.\n\n"
            "BarTender не настроен: установите программу и укажите папку в "
            "переменной BARTENDER файла .env. PDF-этикетки можно печатать без "
            "BarTender."
        )

    configured = Path(value)
    executable = (
        configured
        if configured.name.casefold() == "bartend.exe"
        else configured / "bartend.exe"
    )
    if not executable.is_file():
        raise BarTenderUnavailableError(
            "Этикетка не найдена среди PDF, поэтому для неё требуется BarTender.\n\n"
            f"Файл BarTender не найден: {executable}\n"
            "Установите BarTender или исправьте переменную BARTENDER в файле .env."
        )
    return executable
