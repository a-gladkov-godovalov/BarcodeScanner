"""
Сканер штрих-кодов через веб-камеру
"""

from imutils.video import VideoStream
from pyzbar import pyzbar
import argparse
import datetime
from datetime import datetime
import imutils
import time
import cv2
import winsound

def webcam():
    """
    Инициализация веб-камеры
    """
    frequency = 2500  # Set Frequency To 2500 Hertz
    duration = 800  # Set Duration To 1000 ms == 1 second

    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", type=str, default="barcodesData.csv",
                    help="path to output CSV file ")
    args = vars(ap.parse_args())

    print("Starting webcam")

    vs = VideoStream(src=0).start()
    time.sleep(2.0)
    csvWrite = open("barcodesData.csv", "w")
    found = set()
    while True:
        frameData = vs.read()
        frameData = imutils.resize(frameData, width=600)
        barcodes = pyzbar.decode(frameData)
        for barcode in barcodes:
            (x, y, width, height) = barcode.rect
            cv2.rectangle(frameData, (x, y), (x + width, y + height), (0, 0, 255), 2)
            barcodeData = barcode.data.decode("utf-8")
            barcodeType = barcode.type
            textData = "{} ({})".format(barcodeData, barcodeType)
            cv2.putText(frameData, textData, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            if barcodeData not in found:
                csvWrite.write("{},{}\n".format(datetime.today().strftime('%Y-%m-%d'),
                                                barcodeData))
                csvWrite.flush()
                found.add(barcodeData)
                winsound.Beep(frequency, duration)
        cv2.imshow("Barcode Scanner", frameData)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("e"):
            break

    # close the output CSV file do a bit of cleanup
    print("\nWait while we calculate cost...")
    csvWrite.close()
    cv2.destroyAllWindows()
    vs.stop()


def main():
    """
    Основаня функция входа в приложение
    """
    webcam()


if __name__ == '__main__':
    main()

