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
import time
from pathlib import Path

import cv2
import numpy as np

ZONAS = ["zona1_mesa", "zona2_prato", "zona3_copo"]
FPS_ANIM = 24
TAMANHO = 220
PAUSA = 1
MIN_AREA = 1500


def carregar_animacao(nome):
    frames = []
    for f in sorted(Path("assets", nome).glob("*.png")):
        img = cv2.imread(str(f), cv2.IMREAD_UNCHANGED)       # mantém o canal alfa
        if img is not None and img.ndim == 3 and img.shape[2] == 4:
            frames.append(cv2.resize(img, (TAMANHO, TAMANHO)))
    if not frames:                                           # caso nao tenha animação
        for i in range(48):
            img = np.zeros((TAMANHO, TAMANHO, 4), np.uint8)
            y = int(130 - 60 * abs(np.sin(np.pi * i / 24)))
            cv2.circle(img, (TAMANHO // 2, y), 50, (0, 180, 255, 255), -1)
            frames.append(img)
    return frames


def colar(fundo, img, x, y):
    h, w = img.shape[:2]
    H, W = fundo.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x0 >= x1 or y0 >= y1:
        return
    f = img[y0 - y:y1 - y, x0 - x:x1 - x]
    a = f[:, :, 3:4] / 255.0
    fundo[y0:y1, x0:x1] = (a * f[:, :, :3] + (1 - a) * fundo[y0:y1, x0:x1]).astype(np.uint8)


animacoes = [carregar_animacao(n) for n in ZONAS]
inicio = [None] * len(ZONAS)      # quando a animação da zona começou
ultimo = [0.0] * len(ZONAS)       # último instante com movimento
cap = cv2.VideoCapture(0)
anterior = None

while True:
    ok, frame = cap.read()
    if not ok:
        break
    frame = cv2.flip(cv2.resize(frame, (640, 480)), 1)
    agora = time.time()
    largura_zona = frame.shape[1] / len(ZONAS)

    cinza = cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (21, 21), 0)
    if anterior is not None:
        a, mascara = cv2.threshold(cv2.absdiff(anterior, cinza), 25, 255, cv2.THRESH_BINARY)
        mascara = cv2.dilate(mascara, None, iterations=2)
        contornos, a = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contornos:
            if cv2.contourArea(c) > MIN_AREA:
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                i = min(int((x + w / 2) / largura_zona), len(ZONAS) - 1)
                if inicio[i] is None:
                    inicio[i] = agora
                ultimo[i] = agora
    anterior = cinza

    for i in range(len(ZONAS)):
        x0 = int(i * largura_zona)
        if i > 0:
            cv2.line(frame, (x0, 0), (x0, 480), (255, 255, 0), 1)
        if inicio[i] is not None:
            if agora - ultimo[i] > PAUSA:
                inicio[i] = None
            else:
                anim = animacoes[i]
                img = anim[int((agora - inicio[i]) * FPS_ANIM) % len(anim)]
                colar(frame, img, int((i + 0.5) * largura_zona) - TAMANHO // 2, 240)

    cv2.imshow("Cena", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()