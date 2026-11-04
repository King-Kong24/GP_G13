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
 
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise SystemExit("Não consegui abrir a câmara")
 
while True:
    ok, frame = cap.read()
    if not ok:
        break
    frame = cv2.flip(cv2.resize(frame, (640, 480)), 1) 
    cv2.imshow("Camara", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"): 
        break
 
cap.release()
cv2.destroyAllWindows()
 