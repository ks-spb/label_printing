import os
from environs import Env


DEFAULT_PDF_LABELS_DIR = (
    r"D:\Yandex.Disk\Шплинты\Этикетки\Принтер, фасовка\рабочие этикетки"
    r"\МАРКЕТПЛЕЙСЫ\Этикетки PDF"
)


# Подготовка чтения файла конфигурации
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    env = Env()
    env.read_env(dotenv_path)
    PDF_LABELS_DIR = env.str("PDF_LABELS_DIR", default=DEFAULT_PDF_LABELS_DIR)
else:
    print('Отсутствует файл конфигурации.')
    raise Exception("Отсутствует файл конфигурации.")
