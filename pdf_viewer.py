"""Открытие PDF через Windows и пакетная печать через SumatraPDF."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable


Launcher = Callable[[str, str], None]
PrintCommandLauncher = Callable[[str], None]
BatchPrintLauncher = Callable[[Path, int], None]

_PDF_FILE_PLACEHOLDER = re.compile(r"%(?:1|l|L)(?![0-9])")
_QUOTED_PDF_FILE_PLACEHOLDER = re.compile(r'"%(?:1|l|L)(?![0-9])"')
_SUMATRA_VERSION = "3.6.1"
_SUMATRA_EXE_NAME = f"SumatraPDF-{_SUMATRA_VERSION}-64.exe"
_PRINT_TIMEOUT_SECONDS = 300


class PdfViewerError(RuntimeError):
    """Просмотрщик не принял команду открытия или печати."""

    def __init__(self, message: str, dispatched: int = 0) -> None:
        super().__init__(message)
        self.dispatched = dispatched


class SumatraUnavailableError(PdfViewerError):
    """Пакетный просмотрщик не смог запуститься до отправки задания."""


def _windows_startfile(path: str, operation: str) -> None:
    """Передаёт файл обработчику соответствующего Windows shell verb."""
    os.startfile(path, operation)  # type: ignore[attr-defined]


def _windows_pdf_print_command() -> str:
    """Возвращает зарегистрированную Windows-команду печати для PDF."""
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, ".pdf") as extension_key:
            prog_id = winreg.QueryValueEx(extension_key, "")[0]
        if not isinstance(prog_id, str) or not prog_id:
            raise OSError("Для расширения .pdf не задано приложение.")
        command_key_path = rf"{prog_id}\shell\print\command"
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, command_key_path) as command_key:
            command = winreg.QueryValueEx(command_key, "")[0]
    except FileNotFoundError as exc:
        raise OSError(
            "У приложения PDF нет зарегистрированной команды печати."
        ) from exc

    if not isinstance(command, str) or not command.strip():
        raise OSError("Команда печати PDF не задана в Windows.")
    return command


def _windows_associated_print(path: str) -> None:
    """Запускает команду Print, зарегистрированную для текущего PDF-приложения."""
    command = _windows_pdf_print_command()
    quoted_path = subprocess.list2cmdline([path])
    if _QUOTED_PDF_FILE_PLACEHOLDER.search(command):
        command = _QUOTED_PDF_FILE_PLACEHOLDER.sub(quoted_path, command)
    elif _PDF_FILE_PLACEHOLDER.search(command):
        command = _PDF_FILE_PLACEHOLDER.sub(quoted_path, command)
    else:
        command = f"{command} {quoted_path}"
    subprocess.Popen(command, shell=False)


def _bundled_sumatra_executable() -> Path:
    """Возвращает путь к SumatraPDF внутри PyInstaller-сборки."""
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return bundle_root / "sumatra" / _SUMATRA_EXE_NAME


def _sumatra_appdata_directory() -> Path:
    """Хранит настройки portable-просмотрщика вне защищённой папки установки."""
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        root = Path(local_appdata)
    else:
        root = Path.home() / "AppData" / "Local"
    return root / "LabelPrinting" / "sumatra"


def _sumatra_print(
    pdf_path: Path,
    copies: int,
    *,
    executable: Path | None = None,
    appdata_directory: Path | None = None,
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> None:
    """Передаёт один PDF и число копий одним запуском SumatraPDF."""
    sumatra = executable or _bundled_sumatra_executable()
    if not sumatra.is_file():
        raise SumatraUnavailableError(
            f"Компонент пакетной печати не найден: {sumatra}"
        )

    settings_directory = appdata_directory or _sumatra_appdata_directory()
    try:
        settings_directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SumatraUnavailableError(
            "Не удалось подготовить настройки пакетной печати."
        ) from exc

    command = [
        str(sumatra),
        "-appdata",
        str(settings_directory),
        "-print-to-default",
        "-print-settings",
        f"{copies}x,fit",
        "-silent",
        str(pdf_path),
    ]
    try:
        completed = runner(
            command,
            shell=False,
            check=False,
            timeout=_PRINT_TIMEOUT_SECONDS,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired as exc:
        raise PdfViewerError(
            "Пакетная печать не завершилась за 5 минут. Проверьте очередь "
            "принтера перед повторной печатью: часть тиража могла быть "
            "передана."
        ) from exc
    except (OSError, AttributeError) as exc:
        raise SumatraUnavailableError(
            "Не удалось запустить компонент пакетной печати."
        ) from exc

    if completed.returncode != 0:
        raise PdfViewerError(
            "Пакетная печать завершилась с ошибкой "
            f"(код {completed.returncode}). Проверьте очередь принтера перед "
            "повторной печатью: часть тиража могла быть передана."
        )


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


def _legacy_print_pdf(
    pdf_path: Path,
    copies: int,
    launcher: Launcher,
    fallback_launcher: PrintCommandLauncher,
) -> int:
    """Печатает по одной копии, если пакетный компонент не смог стартовать."""
    dispatched = 0
    for _ in range(copies):
        try:
            launcher(str(pdf_path), "print")
        except (OSError, AttributeError) as startfile_error:
            try:
                fallback_launcher(str(pdf_path))
            except (OSError, AttributeError) as fallback_error:
                raise PdfViewerError(
                    "Не удалось передать PDF в печать. "
                    f"Передано копий: {dispatched}.\n\n"
                    f"Первый системный вызов: {startfile_error}\n"
                    f"Зарегистрированная команда PDF: {fallback_error}",
                    dispatched=dispatched,
                ) from fallback_error
        dispatched += 1
    return dispatched


def print_pdf(
    path: str | Path,
    copies: int,
    batch_launcher: BatchPrintLauncher = _sumatra_print,
    launcher: Launcher = _windows_startfile,
    fallback_launcher: PrintCommandLauncher = _windows_associated_print,
) -> int:
    """Печатает все копии одним заданием через встроенный SumatraPDF.

    Старый Windows-маршрут используется только если SumatraPDF не смог
    запуститься. Ошибка уже запущенного процесса не вызывает повторную печать,
    чтобы не создать двойной тираж.
    """
    if copies < 1:
        raise ValueError("Количество копий должно быть больше нуля.")
    pdf_path = _validated_pdf_path(path)
    try:
        batch_launcher(pdf_path, copies)
    except SumatraUnavailableError:
        return _legacy_print_pdf(
            pdf_path,
            copies,
            launcher=launcher,
            fallback_launcher=fallback_launcher,
        )
    return copies
