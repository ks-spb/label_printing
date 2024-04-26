import os
from environs import Env


# Подготовка чтения файла конфигурации
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    env = Env()
    env.read_env(dotenv_path)
else:
    print('Отсутствует файл конфигурации.')
    raise Exception("Отсутствует файл конфигурации.")
