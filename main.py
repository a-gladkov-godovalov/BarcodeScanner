"""
Сканер штрих-кодов через веб-камеру
"""

from imutils.video import VideoStream
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
import imutils
import cv2
import winsound
import os


class Stream(object):
    """
    Класс Потоковое видео
    """

    # Словарь для распознаных штрих-кодов
    found_barcodes = dict()

    def init_stream(self):
        """
        Функция инициализации потока видео
        """

        if self.device_type == IP:
            # Запускаем видепоток с IP-камеры
            stream = cv2.VideoCapture(f'rtsp://{self.user_login}:{self.user_pass}@{self.device_ip}:554/ch1-s1?tcp')
        else:
            # Запускаем видепоток с веб-камеры
            stream = VideoStream(src=self.device_id).start()

        return stream

    def run_stream(self):
        """
        Функция работы с потоком видео
        """
        # Запускаем видепоток с веб-камеры
        stream = self.init_stream()

        while True:
            if self.device_type == IP:
                ret, frame = stream.read()
            else:
                frame = stream.read()

            frame = self.read_barcode(frame)
            cv2.imshow('Barcode scanner', frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

        stream.release()
        cv2.destroyAllWindows()

    def read_barcode(self, frame):
        """
        Функция распознавания штрих-кодов из изображения
        При успешном распознании штрих-кода на изображение в область накладывается рамка
        """

        barcodes = pyzbar.decode(frame, symbols=[ZBarSymbol.QRCODE, ZBarSymbol.CODE128])
        for barcode in barcodes:
            # Сохраняем координаты штрих-кода
            x, y, w, h = barcode.rect

            # Сохраняем распознанный штри-код в строку
            barcode_text = barcode.data.decode('utf-8')

            # Обрезаем символ переноса каретки из штрих-кода
            barcode_text = barcode_text.rstrip('\n')

            if barcode_text not in self.found_barcodes.values():
                print(f"Отсканирован штри-код {barcode_text}")

                # Определяем количество штрих-кодов в словаре
                counter = len(self.found_barcodes)

                # Обнуляем счетчик штрих-кодов в словаре, чтобы не хранить старые штрих-коды
                if counter == 10:
                    counter = 0

                # Добавляем штрих-код в словарь
                self.found_barcodes[counter] = barcode_text

                # Сохраняем изображение на диск
                self.save_img(frame, barcode_text + ".png")

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        return frame

    @staticmethod
    def save_img(frame, img_name):
        """
        Функция сохранения изображения на диск
        """

        # Получаем каталог для сохранения изображений
        img_path = Stream.get_img_path()

        # Сохраняем изображение
        try:
            cv2.imwrite(img_path + img_name, frame)
        except Exception as ex:
            print(f"Не удалось сохранить изображение: {ex}")
        else:
            print(f"Изображение {img_name} успешно сохранено")

    @staticmethod
    def get_img_path():
        """
        Функция получения каталога для сохранения изображений из потокового видео
        """

        # Создаем каталог для сохранения изображений
        path = "images/"
        try:
            os.mkdir(path)
        except OSError:
            print("Не удалось создать каталог для изображений %s " % path)
        else:
            print("Каталог для изображений успешно создан %s " % path)

        return path


class IPCamera(Stream):
    """
    Класс IP-камера, наследник класса Потоковое видео
    """

    def __init__(self, device_type, device_ip, user_login, user_pass):
        """
        Инициализация класса
        """

        self.device_type = device_type
        self.device_ip = device_ip
        self.user_login = user_login
        self.user_pass = user_pass


class WebCamera(Stream):
    """
    Класс Веб-камера, наследник класса Потоковое видео
    """

    def __init__(self, device_type, device_id,):
        """
        Инициализация класса
        """

        self.device_type = device_type
        self.device_id = device_id


if __name__ == "__main__":
    """
    Основаня точка входа в приложение
    """

    WEB = "Webcamera"
    IP = "IPcamera"

    ip_camera = IPCamera(device_type=IP, device_ip="172.94.3.156", user_login="admin", user_pass="Apteka514")
    ip_camera.run_stream()

    web_camera = WebCamera(device_type=WEB, device_id=0)
    web_camera.run_stream()
