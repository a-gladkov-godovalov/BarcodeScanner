"""
Сканер штрих-кодов через веб-камеру
"""

from imutils.video import VideoStream
from pyzbar import pyzbar
import imutils
import cv2
import winsound
import pathlib
from pathlib import Path


def webcam(device_id):
    """
    Инициализация веб-камеры
    """
    # Задаем частоту звукового сигнала в Гц
    beep_frequency = 2500

    # Задачем продолжительность звукового сигнала в мс
    beep_duration = 800

    print("Starting webcam")

    vs = VideoStream(src=device_id).start()

    # Словарь для распознаных штрих-кодов
    found = dict()

    # Счетчик распознанных штрих-кодов
    counter = 0

    while True:
        frame_data = vs.read()
        frame_data = imutils.resize(frame_data, width=600)
        barcodes = pyzbar.decode(frame_data)
        for barcode in barcodes:
            (x, y, width, height) = barcode.rect
            cv2.rectangle(frame_data, (x, y), (x + width, y + height), (0, 0, 255), 2)

            # Сохраняем распознанный штри-код в строку
            barcode_data = barcode.data.decode("utf-8")

            # Обрезаем символ переноса каретки из штрих-кода
            barcode_data = barcode_data.rstrip('\n')

            barcode_type = barcode.type
            text_data = "{} ({})".format(barcode_data, barcode_type)
            cv2.putText(frame_data, text_data, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            if barcode_data not in found.values():
                # Прибавляем счетчик
                counter += 1

                # Задаем каталог и имя файла для сохранения изображения
                image = barcode_data + ".png"
                print(image)
                # Сохраняем изображение
                cv2.imwrite(image, frame_data)

                # Добавляем штрих-код в словарь
                found[counter] = barcode_data

                # Подаем звуковой сигнал
                winsound.Beep(beep_frequency, beep_duration)

                # Обнуляем счетчик штрих-кодов в словаре для того, чтобы не хранить старые штрих-коды
                if counter == 10:
                    counter = 0

                print(found)
        cv2.imshow("Barcode Scanner", frame_data)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("e"):
            break

    cv2.destroyAllWindows()
    vs.stop()


def main():
    """
    Основаня функция входа в приложение
    """
    webcam(0)

if __name__ == "__main__":
    main()
