import tkinter as tk
from tkinter.messagebox import showerror
import re

from print_btw import print_btw


def is_valid1(text):
    """ Разрешен ввод только цифр и тире между ними """
    if text == "":
        return True
    pattern = r'^(\d+)(\d*(-\d*)?|\d*)$'
    result = re.match(pattern, text)
    if result:
        return True
    else:
        return False

def is_valid2(text):
    """ Разрешен ввод только цифр """
    if text == "":
        return True
    if text == "0":
        return False
    pattern = r'^\d+$'
    result = re.match(pattern, text)
    if result:
        return True
    else:
        return False

def print_label():
    """ Печать этикеток """
    art = entry_article.get()  # Артикул
    cou = entry_count.get()  # Количество
    if art == "" or cou == "":
        return
    try:
        print_btw(entry_article.get(), int(cou), root)  # Печать этикеток
    except Exception as e:
        # Окно сообщения об ошибке стандартное
        showerror("Ошибка", e)
        return


root = tk.Tk()
root.title("Печать этикеток")
root.resizable(False, False)
root.geometry("560x250+500+300")

root.option_add("*Font", "Arial 20")  # установка размера шрифта

check = (root.register(is_valid1), "%P")

label_article = tk.Label(root, text="Артикул")
label_article.place(x=40, y=20)
entry_article = tk.Entry(root, width=10, validate="key", validatecommand=check)
entry_article.place(x=160, y=20)
entry_article.focus_set()  # Фокус на поле ввода артикула

check1 = (root.register(is_valid2), "%P")

label_count = tk.Label(root, text="Кол-во")
label_count.place(x=360, y=20)
entry_count = tk.Entry(root, width=3, validate="key", validatecommand=check1)
entry_count.insert(0, "1")
entry_count.place(x=460, y=20)

button_print = tk.Button(root, text="Печать", relief=tk.GROOVE)
button_print.place(x=40, y=120, width=470, height=100)

# Нажатие Enter и Ctrl-P начинает печать
root.bind('<Control-p>', lambda event: print_label())
root.bind('<Return>', lambda event: print_label())

root.mainloop()
