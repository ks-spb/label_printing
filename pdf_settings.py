"""Локальное сохранение выбранной пользователем PDF-папки."""

from __future__ import annotations

import json
import os
from pathlib import Path


SETTINGS_DIRECTORY_NAME = "LabelPrinting"
SETTINGS_FILE_NAME = "settings.json"
PDF_LABELS_DIR_KEY = "pdf_labels_dir"


def get_settings_path(local_app_data: str | Path | None = None) -> Path:
    """Возвращает путь настроек текущего пользователя Windows."""
    base_directory = local_app_data or os.environ.get("LOCALAPPDATA")
    if not base_directory:
        base_directory = Path.home() / "AppData" / "Local"
    return Path(base_directory) / SETTINGS_DIRECTORY_NAME / SETTINGS_FILE_NAME


def load_pdf_labels_dir(
    default_directory: str | Path,
    settings_path: Path | None = None,
) -> Path:
    """Возвращает сохранённую PDF-папку либо переданный путь по умолчанию."""
    path = settings_path or get_settings_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return Path(default_directory)

    saved_directory = data.get(PDF_LABELS_DIR_KEY) if isinstance(data, dict) else None
    if isinstance(saved_directory, str) and saved_directory.strip():
        return Path(saved_directory.strip())
    return Path(default_directory)


def save_pdf_labels_dir(
    directory: str | Path,
    settings_path: Path | None = None,
) -> None:
    """Запоминает выбранную PDF-папку, сохраняя возможные будущие настройки."""
    path = settings_path or get_settings_path()
    data: dict[str, object] = {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            data = loaded
    except (OSError, json.JSONDecodeError):
        pass

    data[PDF_LABELS_DIR_KEY] = str(Path(directory))
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)
