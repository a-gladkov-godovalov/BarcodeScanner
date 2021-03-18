"""
Сканер штрих-кодов через веб-камеру
"""

from imutils.video import VideoStream
from pyzbar import pyzbar
import imutils
import cv2
import winsound


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

    found = set()
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
            textData = "{} ({})".format(barcode_data, barcode_type)
            cv2.putText(frame_data, textData, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            if barcode_data not in found:
                image = barcode_data + '.png'

                # Сохраняем изображение
                cv2.imwrite(image, frame_data)

                # Добавляем штрих-код в множество
                found.add(barcode_data)

                # Подаем звуковой сигнал
                winsound.Beep(beep_frequency, beep_duration)
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
    webcam(1)
    webcam(0)

if __name__ == '__main__':
    main()
