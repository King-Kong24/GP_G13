#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["opencv-python", "numpy", "rich"]
# ///

"""

Como correr: 
    - uv run src/main.py

Como sair do programa: 
    - letra q 
"""
import cv2
 
MIN_AREA = 1500
cap = cv2.VideoCapture(0)
anterior = None
 
while True:
    ok, frame = cap.read()
    if not ok:
        break
    frame = cv2.flip(cv2.resize(frame, (640, 480)), 1)
 
    cinza = cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (21, 21), 0)
    if anterior is not None:
        delta = cv2.absdiff(anterior, cinza)
        a, mascara = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)
        mascara = cv2.dilate(mascara, None, iterations=2)
        contornos, a = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contornos:
            if cv2.contourArea(c) > MIN_AREA:
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    anterior = cinza
 
    cv2.imshow("Movimento", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
 
cap.release()
cv2.destroyAllWindows()