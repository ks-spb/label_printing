"""Графический интерфейс поиска, открытия и печати этикеток."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog
from tkinter.messagebox import showerror
from typing import Callable, Iterable, Sequence

from label_search import PdfLabelDirectoryError, find_pdf_matches, load_pdf_index
from pdf_settings import load_pdf_labels_dir, save_pdf_labels_dir
from pdf_viewer import open_pdf, print_pdf


Chooser = Callable[[Sequence[Path]], Path | None]
OpenAction = Callable[[Path], None]
PrintDispatch = Callable[[Path, int], object]
PdfPrintAction = Callable[[Path, int], int]
FallbackAction = Callable[[str, int], None]
PdfDirectorySaver = Callable[[Path], None]
APP_VERSION = "1.1.4"


def is_valid_count(text: str) -> bool:
    """Разрешает пустое поле или положительное целое число."""
    return text == "" or (text.isdigit() and text != "0")


def dispatch_label_action(
    query: str,
    count: int,
    pdf_index: Iterable[Path],
    chooser: Chooser,
    open_action: OpenAction,
    print_action: PrintDispatch,
    fallback_action: FallbackAction,
) -> str:
    """Выбирает PDF-first маршрут и выполняет переданное действие."""
    normalized_query = query.strip()
    if not normalized_query:
        return "empty"

    matches = find_pdf_matches(normalized_query, pdf_index)
    if not matches:
        fallback_action(normalized_query, count)
        return "fallback"

    selected = matches[0] if len(matches) == 1 else chooser(matches)
    if selected is None:
        return "cancelled"
    if count:
        print_action(selected, count)
        return "print"
    open_action(selected)
    return "open"


class PdfChoiceDialog:
    """Модальное окно выбора одной этикетки из найденных вариантов."""

    def __init__(self, parent: tk.Misc, paths: Sequence[Path]) -> None:
        self.paths = list(paths)
        self.result: Path | None = None
        self.window = tk.Toplevel(parent)
        self.window.title("Выберите этикетку")
        self.window.transient(parent)
        self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self._cancel)
        self._build_widgets()
        self.window.bind("<Return>", self._confirm)
        self.window.bind("<Escape>", self._cancel)

    def _build_widgets(self) -> None:
        tk.Label(self.window, text="Найдено несколько этикеток:").pack(
            padx=20, pady=(15, 8)
        )
        frame = tk.Frame(self.window)
        frame.pack(padx=20, fill=tk.BOTH, expand=True)
        scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL)
        self.listbox = tk.Listbox(
            frame,
            width=45,
            height=min(10, len(self.paths)),
            exportselection=False,
            yscrollcommand=scrollbar.set,
        )
        scrollbar.config(command=self.listbox.yview)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        for path in self.paths:
            self.listbox.insert(tk.END, path.name)
        self.listbox.selection_set(0)
        self.listbox.activate(0)
        self.listbox.bind("<Double-Button-1>", self._confirm)
        self._build_buttons()

    def _build_buttons(self) -> None:
        buttons = tk.Frame(self.window)
        buttons.pack(pady=15)
        tk.Button(buttons, text="Выбрать", command=self._confirm).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(buttons, text="Отмена", command=self._cancel).pack(
            side=tk.LEFT, padx=5
        )

    def _confirm(self, _event: object = None) -> None:
        selection = self.listbox.curselection()
        if selection:
            self.result = self.paths[selection[0]]
            self.window.destroy()

    def _cancel(self, _event: object = None) -> None:
        self.result = None
        self.window.destroy()

    @classmethod
    def choose(cls, parent: tk.Misc, paths: Sequence[Path]) -> Path | None:
        """Показывает диалог и возвращает выбранный путь или None."""
        dialog = cls(parent, paths)
        dialog.window.grab_set()
        dialog.listbox.focus_set()
        parent.wait_window(dialog.window)
        return dialog.result


class LabelPrintingApp:
    """Главное окно программы печати этикеток."""

    def __init__(
        self,
        root: tk.Tk,
        pdf_index: Sequence[Path],
        pdf_error: PdfLabelDirectoryError | None,
        pdf_directory: Path,
        fallback_printer: Callable[[str, int, tk.Widget], None],
        supplies_printer: Callable[[tk.Widget], None],
        open_action: OpenAction = open_pdf,
        print_action: PdfPrintAction = print_pdf,
        pdf_directory_saver: PdfDirectorySaver = save_pdf_labels_dir,
    ) -> None:
        self.root = root
        self.pdf_index = tuple(pdf_index)
        self.pdf_error = pdf_error
        self.pdf_directory = pdf_directory
        self.fallback_printer = fallback_printer
        self.supplies_printer = supplies_printer
        self.open_action = open_action
        self.print_action = print_action
        self.pdf_directory_saver = pdf_directory_saver
        self.busy = False
        self._configure_window()
        self._build_widgets()
        if self.pdf_error:
            self._update_controls()
            self.root.after(0, self._show_pdf_startup_error)

    def _configure_window(self) -> None:
        self.root.title(f"Печать этикеток {APP_VERSION} (тест)")
        self.root.iconbitmap("ico.ico")
        self.root.resizable(False, False)
        width, height = 650, 250
        left = (self.root.winfo_screenwidth() - width) // 2
        top = (self.root.winfo_screenheight() - height) // 2
        self.root.geometry(f"{width}x{height}+{left}+{top}")
        self.root.option_add("*Font", "Arial 20")

    def _build_widgets(self) -> None:
        tk.Label(self.root, text="Артикул").place(x=30, y=20)
        self.entry_article = tk.Entry(self.root, width=16)
        self.entry_article.place(x=150, y=20)
        self.entry_article.focus_set()
        tk.Label(self.root, text="Кол-во").place(x=455, y=20)
        count_check = (self.root.register(is_valid_count), "%P")
        self.entry_count = tk.Entry(
            self.root, width=3, validate="key", validatecommand=count_check
        )
        self.entry_count.insert(0, "1")
        self.entry_count.place(x=555, y=20)
        self.message = tk.Label(
            self.root, text="", width=39, justify="center", fg="red"
        )
        self.message.place(x=0, y=70)
        self._build_buttons_and_menu()

    def _build_buttons_and_menu(self) -> None:
        self.print_button = tk.Button(
            self.root, text="Печать", relief=tk.GROOVE, command=self.print_label
        )
        self.print_button.place(x=30, y=120, width=285, height=100)
        self.open_button = tk.Button(
            self.root, text="Открыть", relief=tk.GROOVE, command=self.open_label
        )
        self.open_button.place(x=335, y=120, width=285, height=100)
        self.root.bind("<Control-p>", lambda _event: self.print_label())
        self.root.bind("<Return>", lambda _event: self.print_label())
        self.mainmenu = tk.Menu(self.root)
        self.root.config(menu=self.mainmenu)
        self.mainmenu.add_command(
            label="Папка PDF…", command=self.choose_pdf_directory
        )
        self.mainmenu.add_command(
            label="Поставки", command=lambda: self.supplies_printer(self.message)
        )

    def _update_controls(self) -> None:
        label_state = tk.DISABLED if self.busy or self.pdf_error else tk.NORMAL
        self.print_button.config(state=label_state)
        self.open_button.config(state=label_state)
        directory_state = tk.DISABLED if self.busy else tk.NORMAL
        self.mainmenu.entryconfig("Папка PDF…", state=directory_state)
        supplies_state = tk.DISABLED if self.busy else tk.NORMAL
        self.mainmenu.entryconfig("Поставки", state=supplies_state)

    def _set_busy(self, value: bool) -> None:
        self.busy = value
        self._update_controls()

    def _show_pdf_startup_error(self) -> None:
        if self.choose_pdf_directory():
            return
        showerror(
            "Папка PDF недоступна",
            f"{self.pdf_error}\n\nВыберите папку через меню «Папка PDF…».",
            parent=self.root,
        )

    def choose_pdf_directory(self) -> bool:
        """Выбирает, проверяет и запоминает PDF-папку пользователя."""
        if self.busy:
            return False

        initial_directory = self.pdf_directory
        if not initial_directory.is_dir():
            initial_directory = initial_directory.parent
        selected_directory = filedialog.askdirectory(
            parent=self.root,
            title="Выберите папку с PDF-этикетками",
            initialdir=str(initial_directory),
            mustexist=True,
        )
        if not selected_directory:
            return False

        directory = Path(selected_directory)
        try:
            index = load_pdf_index(directory)
        except PdfLabelDirectoryError as exc:
            showerror("Папка PDF недоступна", str(exc), parent=self.root)
            return False

        self.pdf_directory = directory
        self.pdf_index = tuple(index)
        self.pdf_error = None
        self._update_controls()
        self.message.config(text=f"Выбрана PDF-папка: {directory}")
        try:
            self.pdf_directory_saver(directory)
        except OSError as exc:
            showerror(
                "Не удалось запомнить папку PDF",
                f"Папка будет использоваться до закрытия программы.\n\n{exc}",
                parent=self.root,
            )
        return True

    def _choose_pdf(self, paths: Sequence[Path]) -> Path | None:
        return PdfChoiceDialog.choose(self.root, paths)

    def _run_fallback(self, query: str, count: int) -> None:
        self._set_busy(True)
        try:
            self.fallback_printer(query, count, self.message)
        except Exception as exc:
            showerror("Ошибка", str(exc), parent=self.root)
        finally:
            self._set_busy(False)

    def _open_selected_pdf(self, path: Path) -> None:
        self._set_busy(True)
        try:
            self.open_action(path)
            self.message.config(text=f"Открыто: {path.name}")
        except Exception as exc:
            showerror("Ошибка", str(exc), parent=self.root)
        finally:
            self._set_busy(False)

    def _start_pdf_print(self, path: Path, count: int) -> None:
        self._set_busy(True)
        self.message.config(text="Передача PDF в печать")
        worker = threading.Thread(
            target=self._print_worker,
            args=(path, count),
            daemon=True,
        )
        worker.start()

    def _print_worker(self, path: Path, count: int) -> None:
        try:
            dispatched = int(self.print_action(path, count))
            self.root.after(0, self._finish_print, path, dispatched, None)
        except Exception as exc:
            self.root.after(0, self._finish_print, path, 0, exc)

    def _finish_print(
        self,
        path: Path,
        dispatched: int,
        error: Exception | None,
    ) -> None:
        if error:
            showerror("Ошибка", str(error), parent=self.root)
            self.message.config(text="Ошибка передачи в печать")
        else:
            self.message.config(
                text=f"Передано в печать: {dispatched} шт. ({path.name})"
            )
        self._set_busy(False)

    def _handle_action(self, count: int) -> None:
        if self.busy or self.pdf_error:
            return
        dispatch_label_action(
            query=self.entry_article.get(),
            count=count,
            pdf_index=self.pdf_index,
            chooser=self._choose_pdf,
            open_action=self._open_selected_pdf,
            print_action=self._start_pdf_print,
            fallback_action=self._run_fallback,
        )

    def open_label(self) -> None:
        """Открывает найденную этикетку без печати."""
        self._handle_action(count=0)

    def print_label(self) -> None:
        """Печатает указанное количество этикеток."""
        count_text = self.entry_count.get()
        if count_text:
            self._handle_action(count=int(count_text))


def _clear_cached_btw_files() -> None:
    """Удаляет временные BarTender-файлы предыдущего запуска."""
    stickers = Path(__file__).with_name("stickers")
    if not stickers.is_dir():
        return
    for path in stickers.iterdir():
        if path.is_file() and path.suffix.casefold() in {".btw", ".png"}:
            path.unlink()


def main() -> None:
    """Загружает конфигурацию и запускает Tkinter-приложение."""
    from config import PDF_LABELS_DIR
    from print_btw import print_btw
    from print_supplyes import print_supplies

    _clear_cached_btw_files()
    pdf_directory = load_pdf_labels_dir(PDF_LABELS_DIR)
    pdf_error = None
    try:
        pdf_index = load_pdf_index(pdf_directory)
    except PdfLabelDirectoryError as exc:
        pdf_index = ()
        pdf_error = exc

    root = tk.Tk()
    LabelPrintingApp(
        root=root,
        pdf_index=pdf_index,
        pdf_error=pdf_error,
        pdf_directory=pdf_directory,
        fallback_printer=print_btw,
        supplies_printer=print_supplies,
    )
    root.mainloop()


if __name__ == "__main__":
    main()
