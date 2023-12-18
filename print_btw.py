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
import yadisk


class RemoteOperation:
    """ Класс для работы с Яндекс.Диском. Блокирует главное окно программы при работе. """
    def __init__(self, token):
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


def print_btw(art, root):
    """ Печать этикеток.
    Принимает артикул и ссылку на главное окно программы """

    # Подключаемся к Яндекс.Диску
    y = yadisk.YaDisk(token=TOKEN)
    if y.check_token():
        print("Работа работается...")
    else:
        print("Неверный токен")
        raise Exception("Неверный токен")

    if not os.path.exists('btws.json'):
        # Если нет файла со списком этикеток, то пытаемся его получить с Яндекс.Диска
        #


    json_file = io.BytesIO()
    y.download(f'{SEARCH_START}/btws.json', json_file)
    json_file.seek(0)

    cast = json.loads(json_file.read().decode('utf-8'))
    if str(art) in cast:
        # Сохранить файл на локальный диск
        y.download(cast[str(art)], f'{art}.btw')
        # Печать файла
        print('Тут печатается файл')
        os.startfile(f'{art}.btw', 'print')
    else:
        print('Артикул не найден')



