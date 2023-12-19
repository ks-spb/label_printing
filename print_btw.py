# ---------------------- Печать этикеток -------------------------
# 1. Поиск файла по артикулу в списке сохраненном программой search_btw на Yandex диске.
# 2. Скачивание файла на локальную машину
# 3. Вывод файла на печать заданное количество раз.

# ВСЕ НАСТРОЙКИ ДЛЯ ПРОГРАММЫ В ФАЙЛЕ .env
# TOKEN - токен доступа к Yandex диску
# SEARCH_START - Папка на Yandex диске, в которой будет производиться поиск

import io
import os
import json
import re
from environs import Env
from tkinter.messagebox import askyesno
import yadisk


class RemoteOperation:
    """ Класс для работы с Яндекс.Диском.
    Блокирует главное окно программы при работе. """
    def __init__(self, root):
        # Данные о путях и токены для доступа к API берем из .env файла
        dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(dotenv_path):
            env = Env()
            env.read_env(dotenv_path)
        else:
            print('Отсутствует файл конфигурации.')
            raise Exception("Отсутствует файл конфигурации.")

        self.TOKEN = env("TOKEN")
        self.SEARCH_START = env("SEARCH_START")

        # Подключаемся к Яндекс.Диску
        try:
            self.y = yadisk.YaDisk(token=self.TOKEN)
            if self.y.check_token():
                print("Подключение к Yandex.Disk...")
            else:
                print("Неверный токен")
                raise
        except Exception:
            raise Exception("Ошибка подключения к сети.")

    def download(self, file_yandex='btws.json', file_local='last.btw'):
        if file_yandex == 'btws.json':
            file_local = file_yandex
            file_yandex = f'{self.SEARCH_START}/{file_yandex}'

        """ Скачивание файла с Яндекс.Диска """
        self.y.download(file_yandex, file_local)

    def search_btw(self):
        """ Поиск этикеток на Яндекс.Диске """
        def search_files(dir_path):
            """ Рекурсивно перебираем все папки в заданной и переименовываем файлы в них.

            """
            dirs = self.y.listdir(dir_path)  # Получаем список файлов и папок в заданной папке
            dir = []  # Список объектов папок
            for d in dirs:
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
        json_str = json.dumps(btws, indent=4)

        # Сохраняем в файл в формате json на yandex диске
        self.y.upload(io.BytesIO(json_str.encode()), f'{self.SEARCH_START}/btws.json', overwrite=True)


def print_btw(art: str, count: int, root):
    """ Печать этикеток.
    Принимает артикул и ссылку на главное окно программы """
    try:
        yandex = RemoteOperation(root)  # Подключаемся к Яндекс.Диску
    except Exception as e:
        raise Exception(e)

    status = 'local'  # Список взят с локального диска
    if not os.path.exists('btws.json'):
        # Если нет файла со списком этикеток, то пытаемся его получить с Яндекс.Диска
        try:
            yandex.download()
            status = 'yandex'  # Список взят с Яндекс.Диска
        except yadisk.exceptions.PathNotFoundError:
            print('Файл со списком этикеток не найден')
            raise Exception('Файл со списком этикеток не найден')

    print('Печать этикеток')
    # Открываем файл со списком этикеток

    while True:
        json_file = open('btws.json', 'rb')
        cast = json.loads(json_file.read().decode('utf-8'))
        if str(art) in cast:
            # Сохранить файл на локальный диск
            yandex.download(cast[str(art)])
            # Печать файла
            print('Печать этикетки')
            # Печать файла с указанием количества копий
            for i in range(count+1):
                os.startfile('last.btw', 'print')
            return

        else:
            # Артикул не найден
            if status == 'local':
                # Список взят с локального диска
                try:
                    status = 'yandex'  # Список взят с Яндекс.Диска
                    yandex.download()
                    continue
                except yadisk.exceptions.PathNotFoundError:
                    print('Файл со списком этикеток не найден. Пробуем перечитать список.')

            if status == 'yandex':
                # Список взят с Яндекс. Диска, но артикула там нет
                if askyesno("Ошибка", "Артикул не найден. Произвести поиск этикеток?"):
                    try:
                        yandex.search_btw()
                        status = 'error'  # Список уже обновлен
                        continue
                    except Exception:
                        print('Ошибка поиска этикеток.')
                        raise Exception('Ошибка поиска этикеток.')

            raise Exception('Артикул не найден.')


