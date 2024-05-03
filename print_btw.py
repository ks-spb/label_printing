# ---------------------- Печать этикеток -------------------------
# 1. Поиск файла по артикулу в списке сохраненном программой search_btw на Yandex диске.
# 2. Скачивание файла на локальную машину
# 3. Вывод файла на печать заданное количество раз.

# ВСЕ НАСТРОЙКИ ДЛЯ ПРОГРАММЫ В ФАЙЛЕ .env
# TOKEN - токен доступа к Yandex диску
# SEARCH_START - Папка на Yandex диске, в которой будет производиться поиск

import io
import subprocess
import os
import json
import re
from tkinter.messagebox import askyesno
import yadisk

from config import env


class RemoteOperation:
    """ Класс для работы с Яндекс.Диском.
    Выводит сообщения в поле для вывода, которое получает при инициализации. """
    def __init__(self, root):
        # Данные о путях и токены для доступа к API берем из .env файла
        self.root = root

        self.TOKEN = env("TOKEN")
        self.SEARCH_START = env("SEARCH_START")

        self.status = 'start'  # Статус файла со списком

        # Подключаемся к Яндекс.Диску
        self.show_message('Подключение')  # Вывод сообщения
        try:
            self.yandex = yadisk.YaDisk(token=self.TOKEN)
            if self.yandex.check_token():
                print("Подключение к Yandex.Disk...")
            else:
                print("Неверный токен")
                raise
            self.hide_message()
        except Exception:
            self.hide_message()
            raise Exception("Ошибка подключения к сети.")

    def show_message(self, message):
        """Меняем текст сообщения на кнопке Печать главного окна"""
        self.root.config(text=message)
        self.root.update()

    def hide_message(self):
        """Возвращаем слово Печать"""
        self.root.config(text='')
        self.root.update()

    def change_status(self):
        """ Меняет статус файла со списком этикеток.
        Cтатус может быть 'start', 'local', 'yandex', 'last', 'current'.
        'start' после проверки существования файла меняется на local.
        Возвращает: новый статус. Статус 'current' возвращает, когда список этикеток актуален.
        Если файл отсутствует на локальном диске, пытается загрузить его с Яндекс.Диска.
        Если файл отсутствует на Яндекс.Диске, проводит сканирование и создает его, потом загружает.
        Статус меняет в зависимости от способа получения файла."""

        if not os.path.exists('btws.json') or self.status == 'local':
            self.show_message('Загрузка обновлений')  # Открываем окно ожидания
            # Если нет файла со списком этикеток или он есть, но не актуален,
            # то пытаемся его получить с Яндекс.Диска
            self.status = 'yandex'  # Список взят с Яндекс.Диска
            if self.download():
                return self.status  # Файл получен с Яндекс.Диска
        if self.status == 'start':
            # При старте статус меняем на local, проверив что файл существует
            self.status = 'local'
            return self.status
        if self.status == 'yandex':
            # Список уже получен с Яндекс.Диска или попытка получить его с Яндекс.Диска не удалась
            # Проводим сканирование и создаем файл
            try:
                self.search_btw()
                self.status = 'last'  # Список уже обновлен
                # Загружаем файл на Яндекс.Диска
                if self.download():
                    return self.status  # Файл получен с Яндекс.Диска
                else:
                    raise Exception('Ошибка загрузки файла c Яндекс диска.')
            except Exception as e:
                print('Ошибка поиска этикеток:', e)
                raise Exception('Ошибка поиска этикеток.', e)
        else:
            self.status = 'current'  # Список актуален
        return self.status

    def download(self, file_yandex='btws.json', name_for_save=''):
        """Загружает файл с Яндекс диска на локальный компьютер

        Принимает:
        - полное имя (с путем) файла на Яндекс, если имя btws.json
        то качает с корневой папки заданной для программы и сохраняет с таким же именем.
        - Иначе во втором параметре передается имя для сохранения файла (артикул).
        Возвращает False - если запрашиваемого файла нет.
        Или имя сохраненного файла."""

        if file_yandex == 'btws.json':
            message = 'Загрузка обновлений'
            file_local = file_yandex
            file_yandex = f'{self.SEARCH_START}/{file_yandex}'
        else:
            message = 'Загрузка этикетки'
            file_local = name_for_save + '.btw'
        if self.yandex.exists(file_yandex):
            self.show_message(message)  # Показываем сообщение
            # Загрузка файла
            self.yandex.download(file_yandex, file_local)
            self.hide_message()
            return file_local
        return False

    def search_btw(self):
        """ Поиск этикеток на Яндекс.Диске """
        self.show_message('Создание списка 1-2 мин.')  # Открываем окно ожидания
        def search_files(dir_path):
            """ Рекурсивно перебираем все папки в заданной и переименовываем файлы в них."""

            dirs = self.yandex.listdir(dir_path)  # Получаем список файлов и папок в заданной папке
            dir = []  # Список объектов папок
            for d in dirs:
                self.root.update()  # Обновляем окно программы
                if d['type'] == 'dir':
                    dir.append(d)
                    continue
                elif d['name'].endswith('.btw'):
                    name = d['name'].strip().strip('_')
                    # Это файл .btw. Для попадания в список он должен начинаться с артикула
                    match = re.search(r'^\d+(?:-\d+)* ', name)
                    if match:
                        btws[match.group(0).strip()] = d['path']

            for d in dir:
                search_files(d['path'])
            return

        btws = dict()  # Словарь из артикулов и путей к файлам
        search_files(self.SEARCH_START)

        # Преобразуем словарь в строку JSON
        json_str = json.dumps(btws, indent=4, ensure_ascii=False)

        # Сохраняем в файл в формате json на yandex диске
        self.yandex.upload(io.BytesIO(json_str.encode('utf-8')), f'{self.SEARCH_START}/btws.json', overwrite=True)

        self.hide_message()


def print_btw(art: str, count: int, root):
    """ Печать этикеток.
    Принимает артикул, количество копий печати и ссылку на поле для вывода сообщений.
    Если количество 0 - то этикетку нужно не печатать, а просто открыть в редакторе."""
    art = ARTICLE_DICT.get(art, art)  # Проверяем артикул в словаре перевода
    yandex = RemoteOperation(root)  # Подключаемся к Яндекс.Диску
    yandex.change_status()  # Подготовка файла со списком этикеток
    print('Печать этикеток')
    # Открываем файл со списком этикеток ищем и печатаем нужную.
    # Если не находим артикул, то обновляем список этикеток и пытаемся найти снова.
    while yandex.status != 'current':
        json_file = open('btws.json', 'rb')
        cast = json.loads(json_file.read().decode('utf-8'))
        name = None
        if str(art) in cast:
            name = yandex.download(cast[str(art)], str(art))
        if name:
            # Удачно сохранили файл на диск еще в условии: yandex.download.
            # Получили имя файла, под которым сохранили.
            if count:
                print('Печать этикетки ' + str(art))
                # Печать файла с указанием количества копий
                command = f'"{BARTENDER}" /P /XS /RUN /C={count} {name}'
            else:
                # Печать файла
                print('Открытие этикетки ' + str(art))
                # Открытие файла в редакторе
                command = f'"{BARTENDER}" /RUN {name}'

            subprocess.Popen(command, shell=True)
            return
        else:
            # Артикул не найден
            print('Артикул или файл не найден, пытаемся обновить список этикеток.')
            if yandex.status == 'yandex':
                if not askyesno("Ошибка", "Артикул или файл не найден. Произвести поиск этикеток?"):
                    print('Поиск этикеток отменен.')
                    raise Exception('Поиск этикеток отменен.')
            yandex.change_status()

    print('Артикул или файл не найден.')
    raise Exception('Артикул или файл не найден.')


BARTENDER = env("BARTENDER")  # Путь к программе Bartender для печати этикеток
if BARTENDER[-1] != '\\':
    BARTENDER += '\\'
BARTENDER = BARTENDER.replace('\\', '\\\\') + "bartend.exe"

# Читаем в память файл для перевода артикулов articles_dict.json
# из папки программы и переводим его в словарь.
try:
    with open('articles_dict.json', 'rb') as file:
        ARTICLE_DICT = json.loads(file.read().decode('utf-8'))
except Exception as e:
    print('Ошибка чтения словаря артикулов:', e)
    ARTICLE_DICT = dict()
