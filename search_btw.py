# --------------- Подготовка списка этикеток ---------------
# 1. Чтение файлов в заданной папке Yandex Disk и ее подпапках
# 2. Выбор файлов с расширением btw имеющих в начале имени артикул (могут быть цифры и тире)
# 3. Сохранение в словарь артикула и пути к файлу
# 4. Запись списка в файл btws.json в заданной (корневой) папке, в формате JSON.

# ВСЕ НАСТРОЙКИ ДЛЯ ПРОГРАММЫ В ФАЙЛЕ .env
# TOKEN - токен доступа к Yandex диску
# SEARCH_START - Папка на Yandex диске, в которой будет производиться поиск

import io
import os
import json
import re
from environs import Env
import yadisk


# Данные о путях и токены для доступа к API берем из .env файла
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    env = Env()
    env.read_env(dotenv_path)
else:
    print('Отсутствует файл конфигурации.')
    exit()

TOKEN = env("TOKEN")
SEARCH_START = env("SEARCH_START")

# Подключаемся к Яндекс.Диску
y = yadisk.YaDisk(token=TOKEN)
if y.check_token():
    print("Работа работается...")
else:
    print("Неверный токен")
    exit()

def search_files(dir_path):
    """ Рекурсивно перебираем все папки в заданной и переименовываем файлы в них.

    """
    dirs = y.listdir(dir_path)  # Получаем список файлов и папок в заданной папке
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
search_files(SEARCH_START)

# Преобразуем словарь в строку JSON
json_str = json.dumps(btws, indent=4)

# Сохраняем в файл в формате json на yandex диске
y.upload(io.BytesIO(json_str.encode()), f'{SEARCH_START}/btws.json', overwrite=True)



