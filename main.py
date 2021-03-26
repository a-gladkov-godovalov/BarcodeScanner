"""
Сканер штрих-кодов через несколько камер разного типа: вебкамеры, IP-камеры
"""

from imutils.video import VideoStream
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
from contextlib import contextmanager
from threading import Thread
import cv2
import os
import logging
import configparser
import socket
import sys
import pyodbc


class Stream(Thread):
    """
    Класс Потоковое видео наследник класса Поток
    """

    # Словарь для распознаных штрих-кодов
    found_barcodes = dict()

    def __init__(self, device_id):
        """
        Инициализация потока
        """

        # Вызываем конструктор базового класса
        super().__init__()

        self.device_id = device_id

    def run(self):
        """
        Запуск потока
        """

        self.process_stream()

    def init_stream(self):
        """
        Функция инициализации видеопотока
        """

        try:
            if self.device_type == IP:
                # Запускаем видеопоток с IP-камеры
                stream = cv2.VideoCapture(f"rtsp://{self.user_login}:{self.user_pass}@{self.device_ip}:554/ch1-s1?tcp")
            else:
                # Запускаем видеопоток с веб-камеры
                stream = VideoStream(src=self.device_port).start()
        except Exception as ex:
            _logger.exception(f"{self}: не удалось инициализировать видеопоток от камеры - {ex}")
        else:
            _logger.info(f"{self}: инициализировали видеопоток")

        return stream

    def process_stream(self):
        """
        Функция работы с потоком видео
        """

        # Запускаем видепоток с веб-камеры
        stream = self.init_stream()

        # Получаем каталог для сохранения изображений
        img_path = self.get_img_path()

        while True:
            try:
                if self.device_type == IP:
                    ret, frame = stream.read()
                else:
                    frame = stream.read()
            except Exception as ex:
                _logger.exception(f"{self}: не удалось произвести захват видеопотока от камеры - {ex}")
            else:
                frame = self.read_barcode(frame, img_path)
                # cv2.imshow('Barcode scanner', frame)

            if cv2.waitKey(1) & 0xFF == 27:
                break

        stream.release()
        cv2.destroyAllWindows()

    def read_barcode(self, frame, img_path):
        """
        Функция распознавания штрих-кодов из изображения
        При успешном распознании штрих-кода на изображение в область накладывается рамка
        и изображение сохряняется на диск
        """

        try:
            barcodes = pyzbar.decode(frame, symbols=[ZBarSymbol.QRCODE])
        except Exception as ex:
            _logger.exception(f"{self}: не удалось распознать QRCode - {ex}")
        else:
            for barcode in barcodes:
                # Сохраняем координаты штрих-кода и рисуем прямоугольник в этой области
                x, y, w, h = barcode.rect
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Сохраняем распознанный штри-код в строку
                barcode_text = barcode.data.decode('utf-8')

                # Обрезаем символ переноса каретки из штрих-кода
                barcode_text = barcode_text.rstrip('\n')

                if barcode_text not in self.found_barcodes.values():

                    # Определяем количество штрих-кодов в словаре
                    counter = len(self.found_barcodes)

                    # Обнуляем счетчик штрих-кодов в словаре, чтобы не хранить старые штрих-коды
                    if counter == 10:
                        counter = 0

                    # Добавляем штрих-код в словарь
                    self.found_barcodes[counter] = barcode_text

                    # Сохраняем изображение на диск
                    self.save_img(frame, img_path + barcode_text + ".png")

                    # Сохраняем штрих-код в БД
                    self.set_barcode_sql(barcode_text)

        return frame

    @staticmethod
    def set_barcode_sql(barcode):
        """
        Функция записи штрих-кода в базу данных на SQL
        """

        pass

    def save_img(self, frame, img_name):
        """
        Функция сохранения изображения на диск
        """

        # Сохраняем изображение
        try:
            cv2.imwrite(img_name, frame)

        except FileNotFoundError:
            _logger.exception(f"{self.device_id}: не удалось сохранить изображение - нет доступа к каталогу images")
        except Exception as ex:
            _logger.exception(f"{self.device_id}: не удалось сохранить изображение - {ex}")
        else:
            _logger.info(f"id={self.device_id}: изображение {img_name} сохранено")

    @staticmethod
    def get_img_path():
        """
        Функция получения каталога для сохранения изображений из потокового видео
        """

        # Создаем каталог для сохранения изображений
        path = "images/"

        if not os.path.exists(path):
            try:
                os.mkdir(path)
            except OSError:
                _logger.exception(f"Не удалось создать каталог для изображений - {path}")
            else:
                _logger.exception(f"Каталог для изображений успешно создан - {path}")

        return path


class IPCamera(Stream):
    """
    Класс IP-камера, наследник класса Потоковое видео
    """

    def __init__(self, device_id, device_ip, user_login, user_pass):
        """
        Инициализация класса
        """

        # Вызываем конструктор базового класса
        super().__init__(device_id)

        self.device_type = IP
        self.device_ip = device_ip
        self.user_login = user_login
        self.user_pass = user_pass

    def __repr__(self):
        """
        Вывод информации о классе
        """

        return f"id={self.device_id} type={self.device_type} ip={self.device_ip}"


class WebCamera(Stream):
    """
    Класс Web-камера, наследник класса Потоковое видео
    """

    def __init__(self, device_id, device_port):
        """
        Инициализация класса
        """

        # Вызываем конструктор базового класса
        super().__init__(device_id)

        self.device_type = WEB
        self.device_port = device_port

    def __repr__(self):
        """
        Вывод информации о классе
        """

        return f"id={self.device_id} type={self.device_type} port={self.device_port}"


def create_config():
    """
    Создание файла конфигурации
    """
    config = configparser.ConfigParser()

    # добавляем секцию Connection в конфигурационный файл
    config.add_section('Connection')
    config.set('Connection', 'Server', 'localhost')
    config.set('Connection', 'Database', 'master')
    config.set('Connection', 'Login', 'sa')
    config.set('Connection', 'Pass', 'password')

    with open(SETTINGS_PATH, 'w') as config_file:
        config.write(config_file)


def get_config():
    """
    Поиск файла конфигурации
    """
    if not os.path.exists(SETTINGS_PATH):
        create_config()

    config = configparser.ConfigParser()
    config.read(SETTINGS_PATH)
    return config


def get_setting(section, setting):
    """
    Чтение указанного параметра настроек из файла конфигурации
    """
    config = get_config()
    value = config.get(section, setting)
    return value


def init_log():
    """
    Создание файла для логирования событий приложения
    """

    _logger.setLevel(logging.INFO)

    # Создаем обработчик файла журнала приложения
    fh = logging.FileHandler('BarcodeScanner.log')

    # Задаем формат строки журнала
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    # Добавляем обработчик к объекту регистратора
    _logger.addHandler(fh)


@contextmanager
def open_sql_connection():
    """
    Открытие соединения с сервером MSSQL на период выполнения одного запроса
    """
    connection = pyodbc.connect(_sql_connect_str)
    cursor = connection.cursor()
    try:
        yield cursor
    except pyodbc.DatabaseError as err:
        error, = err.args
        sys.stderr.write(error.message)
        _logger.exception(error.message)
        raise err
        logger.exception(f'Ошибка подключения к SQL: {err}')
    finally:
        connection.close()


def get_sql_connect_str():
    """
    Получение строки подключения к серверу MSSQL
    """
    # Драйвер с помощью которого будем подключаться к MSSQL
    sql_driver = 'DRIVER={SQL Server}'
    # Имя сервера MSSQL
    sql_server = 'SERVER=' + get_setting('Connection', 'Server')
    # Порт сервера MSSQL
    sql_port = 'PORT=1433'
    # База данных на MSSQL
    sql_db = 'DATABASE=' + get_setting('Connection', 'Database')
    # Имя пользователя MSSQL
    sql_user = 'UID=' + get_setting('Connection', 'Login')
    # Пароль MSSQL
    sql_pw = 'PWD=' + get_setting('Connection', 'Pass')
    # Собираем готовую строку подключения к MSSQL
    connect_str = ';'.join([sql_driver, sql_server, sql_port, sql_db, sql_user, sql_pw])

    return connect_str


def get_cameras():
    """
    Функция поиска и инициализации работы камер
    """

    # Создаем словарь камер
    cameras_dict = dict()

    # Выполним запрос в SQL на получение списка новых заказов
    with open_sql_connection() as cursor:
        try:
            cursor.execute("select deviceId,typeId,ip,login,password,port from Conveyer_Camera_List where isActive = 1")
            for row in cursor:
                cameras_dict[row.deviceId] = {'type_id': row.typeId, 'ip': row.ip, 'login': row.login,
                                              'password': row.password, 'port': row.port}
        except Exception as err:
            _logger.exception(f'Ошибка при выполнении запроса - {err}')

    return cameras_dict


def main():
    """
    Запуск потоков
    """

    # Задаем настройки логирования приложения
    init_log()

    _logger.info('Запуск приложения на ' + socket.gethostname())

    # Получаем список камер из базы данных на SQL
    cameras = get_cameras()

    for camera in cameras.keys():
        camera_detail = cameras[camera]

        if camera_detail["type_id"] == 1:  # IP-камера
            camera_thread = IPCamera(device_id=camera, device_ip=camera_detail["ip"],
                                     user_login=camera_detail["login"], user_pass=camera_detail["password"])
        elif camera_detail["type_id"] == 2:  # Web-камера
            camera_thread = WebCamera(device_id=camera, device_port=camera_detail["port"])

        camera_thread.start()


if __name__ == "__main__":
    """
    Основная точка входа в приложение
    """

    # Задаем имя файла конфигурации приложения
    SETTINGS_PATH = 'Settings.ini'

    # Задаем типы камер
    WEB = "Webcamera"
    IP = "IPcamera"

    # Создаем лог приложения
    _logger = logging.getLogger('BarcodeScanner')

    # Получаем строку подключения к SQL
    _sql_connect_str = get_sql_connect_str()

    # Запускаем приложение
    main()
