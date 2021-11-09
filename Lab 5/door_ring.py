import cv2
import time
import numpy as np
import HandTrackingModule as htm
import math
from ctypes import cast, POINTER
import gtts
from pydub import AudioSegment
from pydub.playback import play
from io import BytesIO

################################
wCam, hCam = 640, 480
################################


def playsound(text):
    tts = gtts.gTTS(text, lang="en")
    mp3_fp = BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    song = AudioSegment.from_file(mp3_fp, format="mp3")
    play(song)


cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0

detector = htm.handDetector(detectionCon=0.7)
while True:
    success, img = cap.read()
    img = detector.findHands(img)
    lmList = detector.findPosition(img, draw=False)
    if len(lmList) != 0:

        thumbX, thumbY = lmList[4][1], lmList[4][2]  # thumb
        pointerX, pointerY = lmList[8][1], lmList[8][2]  # pointer

        middleX, middleY = lmList[12][1], lmList[12][2]
        ringX, ringY = lmList[16][1], lmList[16][2]
        pinkyX, pinkyY = lmList[20][1], lmList[20][2]

        cx, cy = (thumbX + pointerX) // 2, (thumbY + pointerY) // 2

        len_calc = lambda x1, y1, x2, y2: math.hypot(x2 - x1, y2 - y1)
        length = len_calc(thumbX, thumbY, pointerX, pointerY)
        length1 = len_calc(pointerX, pointerY, middleX, middleY)
        length2 = len_calc(middleX, middleY, ringX, ringY)
        length3 = len_calc(ringX, ringY, pinkyX, pinkyY)
        length4 = len_calc(thumbX, thumbY, ringX, ringY)
        print(length, length1, length2, length3, length4)
        condition_arnavi = (
            length < 100
            and length1 > 100
            and length2 < 25
            and length3 > 100
            and length4 < 100
        ) or (
            length > 100
            and length1 > 100
            and length1 < 180
            and length2 < 30
            and length3 > 100
            and length3 < 180
            and length4 > 100
        )

        condition_random = (
            length > 60 and length < 100
            and length1 > 30 and length1 < 40
            and length2 > 25 and length2 < 40
            and length3 > 35 and length3 < 55
            and length4 > 120 and length4 < 150
        )
        if condition_arnavi:
            playsound("Arnavi is home!")
            # time.sleep(1.0)
        elif condition_random:
            playsound("Someone is at the door")


    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime

    cv2.waitKey(1)
