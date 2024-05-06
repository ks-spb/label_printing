# Модуль для выбора и печати этикеток для Поставок.
# Программа работает с API Wildberries.

# Выводит модальное окно для выбора Поставки (найденные Поставки отображаются в списке).
# После выбора получает Сборочные задания из Поставки.
# Скачивает стикеры для всех заданий (стикеры готовятся на WB).
# Печатает Этикетку и Стикер.

import os
import json
import base64
import requests
import subprocess
import tkinter as tk
from config import env
import win32com.client

from tkinter.messagebox import showerror
from print_btw import print_btw


class WBClient():
    """Класс для получения и хранения данных от Wildberries."""
    def __init__(self, url: str, handler=None):
        """Готовим объект. Делаем запрос. Обрабатываем ответ.
        Принимает: URL эндпоинта, метод обработчик.
        Методы для обработки встраиваются в класс, при инициализации объекта
        указывается метод, которым будут обрабатываться данные запроса в этом объекте.
        Возвращает обработанные данные, формат зависит от метода.
        Если метод не указан - вернутся сырые данные ответа.
        """
        self.url = url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": env("TOKEN_WB")
        }
        self.handler = handler  # Метод для обработки данных запроса
        self.err_message = None

        # Получаем путь к папке stickers в текущей папке программы
        self.stickers_folder = os.path.join(os.path.dirname(__file__), 'stickers')

    def make_request(self, **kwargs):
        """Выполнение запроса.
        Принимает параметры для запроса в готовом виде (method, data, params...),
        кроме url и headers (они задаются при инициализации объекта).
        Возвращает данные пригодные для использования потребителем,
        обработанные методом заданным при инициализации.
        """
        self.err_message = 'Ошибка запроса API WB'
        try:
            response = requests.request(url=self.url, headers=self.headers, **kwargs)
            data = json.loads(response.content, parse_int=str)
            return self.handler(self, data)  # Обработка полученных данных ранее назначенным методом
        except Exception as e:
            showerror('Ошибка', f"{self.err_message}\n{e}")
            raise

    def extract_supplies(self, data):
        """Обработчик данных о поставках.
        Принимает сырые данные, которые вернул запрос API.
        Возвращает информацию о тех, которые имеют "done": false (не выполненные):
        [{'name': название поставки, 'id': id поставки}].
        https://openapi.wildberries.ru/marketplace/api/ru/#tag/Postavki/paths/~1api~1v3~1supplies/get
        """
        self.err_message = 'Ошибка обработки данных о Поставках, полученных от WB.'
        # Поиск поставок находящихся на сборке
        supplies = []
        for supply in reversed(data['supplies']):
            if not supply['done']:
                supplies.append({'name': supply['name'], 'id': supply['id']})
        return supplies

    def extract_orders(self, orders):
        """Выбор Номеров заданий и Артикулов (для печати этикеток).
        Получает список Сборочных заданий (это товар, может быть в разном количестве).
        Они должны быть отсортированы по складам, а внутри по артикулам (одинаковые рядом).
        Из всех данных нас интересуют Номер задания и Артикул (для печати этикеток).
        Возвращаем список: [{'order': Номер задания, 'article': артикул},...]
        https://openapi.wildberries.ru/marketplace/api/ru/#tag/Postavki/paths/~1api~1v3~1supplies~1%7BsupplyId%7D~1orders/get
        """
        self.err_message = 'Ошибка обработки данных Сборочных заданиях, полученных от WB.'
        # Создаем словарь идентификаторов складов со списками кортежей:
        # {id склада: [(Номер задания, артикул),...],...}
        whs = dict()
        for order in orders['orders']:
            whs_id = order['warehouseId']
            if whs_id in whs:
                whs[whs_id].append((order['id'], order['article']))
            else:
                whs[whs_id] = [(order['id'], order['article'])]

        # Сортируем списки кортежей по артикулам (второй элемент в кортеже).
        # И создаем список выходного формата.
        out = []
        for tpl in whs.values():
            tpl.sort(key=lambda x: x[1])
            out += [{'order': i[0], 'article': i[1]} for i in tpl]
        return out

    def extract_stickers(self, stickers):
        """Сохранение стикеров для Сборочных заданий.
        Принимает данные со списком в формате WB и путь для сохранения стикеров.
        https://openapi.wildberries.ru/marketplace/api/ru/#tag/Sborochnye-zadaniya/paths/~1api~1v3~1orders~1stickers/post
        """
        self.err_message = 'Ошибка сохранения стикеров.'
        # Сохранение файлов изображений
        for sticker in stickers['stickers']:
            # Декодирование base64 строки в бинарные данные
            decoded_data = base64.b64decode(sticker['file'])
            # Сохранение бинарных данных в файл формата png
            with open(f'{os.path.join(self.stickers_folder, sticker["orderId"])}.png', 'wb') as file:
                file.write(decoded_data)



def print_supplies(root):
    """Выбор Поставки из списка.
    Выводит окно для выбора.
    Печать Этикеток и Стикеров для сборочных заданий.
    """
    def on_select():
        """Обработка кнопки Печать"""
        selected_word = listbox.curselection()
        if not selected_word:
            return
        supply_id = supplies[selected_word[0]]['id']  # Получение id Поставки

        # Получение Сборочных заданий Поставки
        client = WBClient(url + f'supplies/{supply_id}/orders', handler=WBClient.extract_orders)  # Клиент запросов
        method = 'get'
        orders = client.make_request(method=method)

        # Получение этикеток сборочных заданий
        client = WBClient(url + f'orders/stickers', handler=WBClient.extract_stickers)  # Клиент запросов
        method = 'post'
        # Разбиваем список на части по 100 заданий
        start = 0
        while start < len(orders):
            to_params = [int(i['order']) for i in orders[start:start+100]]
            data = {
                "orders": to_params,
            }
            params = {
                'type': 'png',
                'width': 58,
                'height': 40,
            }
            client.make_request(method=method, data=json.dumps(data), params=params)

            start += 100

        top.destroy()  # Закрываем окно выбора

        # Печать этикеток и стикеров

        # Откроем Bartender для печати стикеров в формате PNG.
        # Картинки напрямую не печатаются, поэтому их вставляем в шаблон и печатаем его.
        # Создаем экземпляр программы BarTender
        bt_app = win32com.client.Dispatch("BarTender.Application")
        # Открываем окно (не показываем)
        bt_app.Visible = False
        # Открываем шаблон
        path = os.path.dirname(os.path.abspath(__file__))  # Текущая папка программы
        label_format = bt_app.Formats.Open(os.path.join(path, 'template.btw'), False, "")
        # Получаем COM-объекты с шаблона (там одна картинка)
        objects = label_format.Objects
        # Находим объект с картинкой
        for obj in objects:
            if obj.Type == 6:  # Тип объекта картинка, ее и будем менять
                break
        i = 0
        # Печать стикеров
        for order in orders:
            print('Печать стикера ' + order['article'])
            try:
                print_btw(order['article'], 1, root, run=True)
            except Exception as e:
                # Окно сообщения об ошибке стандартное
                showerror("Ошибка", f"{e}\n{order['article']}")

            # command = f'"{BARTENDER}" /P /XS /RUN /C=1 stickers/{order["order"]}.svg'
            obj.PicturePath = f'{os.path.join(client.stickers_folder, order["order"])}.png'
            # Печать измененной этикетки
            label_format.PrintOut(False, False)

            # Ограничение на количество печатаемых стикеров
            # if i == 6:
            #     break
            # i += 1

        # Close the BarTender application
        bt_app.Quit(1)

    url = 'https://suppliers-api.wildberries.ru/api/v3/'

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
    listbox = tk.Listbox(top, selectmode=tk.SINGLE)
    listbox.place(x=5, y=5, height=win_h-60, width=win_w-10)

    # Кнопка печати
    print_button = tk.Button(top, height=1, width=10, text='Печать', command=on_select)
    print_button.place(x=5, y=253, height=40, width=140)

    # Кнопка закрытия
    close_button = tk.Button(top, height=1, width=10, text='Отмена', command=top.destroy)
    close_button.place(x=155, y=253, height=40, width=140)

    # Запрос Поставок
    client = WBClient(url + '/supplies', handler=WBClient.extract_supplies)  # Клиент запросов
    params = {
        'limit': 1000,
        'next': 0,
    }
    method = 'get'
    supplies = client.make_request(params=params, method=method)

    # Выводим список поставок
    for supply in supplies:
        listbox.insert(tk.END, supply['name'])
    # Выбираем первую строку
    if supplies:
        listbox.select_set(0)


    top.grab_set()
    top.focus_set()
    top.wait_window()

