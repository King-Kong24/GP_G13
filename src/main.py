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

ZONAS = ["zona1_mesa", "zona2_prato", "zona3_copo"]
MIN_AREA = 1500
cap = cv2.VideoCapture(0)
anterior = None

while True:
    ok, frame = cap.read()
    if not ok:
        break
    frame = cv2.flip(cv2.resize(frame, (640, 480)), 1)
    largura_zona = frame.shape[1] / len(ZONAS)

    cinza = cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (21, 21), 0)
    ativas = set()
    if anterior is not None:
        a, mascara = cv2.threshold(cv2.absdiff(anterior, cinza), 25, 255, cv2.THRESH_BINARY)
        mascara = cv2.dilate(mascara, None, iterations=2)
        contornos, a = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contornos:
            if cv2.contourArea(c) > MIN_AREA:
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                ativas.add(min(int((x + w / 2) / largura_zona), len(ZONAS) - 1))
    anterior = cinza

    for i, nome in enumerate(ZONAS):
        x0 = int(i * largura_zona)
        if i > 0:
            cv2.line(frame, (x0, 0), (x0, 480), (255, 255, 0), 1)
        cor = (0, 255, 0) if i in ativas else (255, 255, 0)
        cv2.putText(frame, nome, (x0 + 6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, cor, 2)

    cv2.imshow("Zonas", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
