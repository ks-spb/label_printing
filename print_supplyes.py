# Модуль для выбора и печати этикеток для Поставок.
# Программа работает с API Wildberries.

# Выводит модальное окно для выбора Поставки (найденные Поставки отображаются в списке).
# После выбора получает Сборочные задания из Поставки.
# Скачивает стикеры для всех заданий (стикеры готовятся на WB).
# Печатает Этикетку и Стикер.

import os
import tkinter as tk


def print_supplyes(root):

    top = tk.Toplevel()  # Новое окно

    # Размер экране
    w = root.winfo_screenwidth()
    h = root.winfo_screenheight()

    # Размер окна
    win_w = 300
    win_h = 300
    top.geometry(f'{win_w}x{win_h}+{(w - win_w) // 2}+{(h - win_h) // 2}')  # Рисуем окно
    top.resizable(width=False, height=False)

    top.title("Поставки")
    top.iconbitmap('ico.ico')
    top.transient(root)  # Поверх окна

    words = ['apple', 'banana', 'cherry', 'date', 'elderberry']
    # создание виджета списка
    listbox = tk.Listbox(top)
    listbox.place(x=5, y=5, height=win_h-60, width=win_w-10)
    for word in words:
        listbox.insert(tk.END, word)

    # Кнопка печати
    print_button = tk.Button(top, height=1, width=10, text='Печать', command=None)
    print_button.place(x=5, y=253, height=40, width=140)

    # Кнопка закрытия
    close_button = tk.Button(top, height=1, width=10, text='Отмана', command=top.destroy)
    close_button.place(x=155, y=253, height=40, width=140)


    top.grab_set()
    top.focus_set()
    top.wait_window()
