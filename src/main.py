#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["opencv-python", "numpy", "rich"]
# ///
"""A cena reage ao movimento (versão simples: 3 zonas).

Uso:  uv run src/main.py            (MOG2)
      uv run src/main.py --diff     (diferença de frames)
Teclas: q = sair
"""
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from rich.console import Console

# Nomes das pastas em assets/ 
ZONAS = ["zona1_mesa", "zona2_vaso", "zona3_copo"]
FPS_ANIM = 24
TAMANHO = 220        # tamanho do overlay (px)
PAUSA = 1         # segundos sem movimento até terminar a deteção
MIN_AREA = 1500      # área mínima da região com movimento

console = Console()


def carregar_animacao(nome):
    """Lê os PNG da pasta assets/<nome> com canal alfa. Sem PNG -> círculo provisório."""
    frames = []
    for f in sorted(Path("assets", nome).glob("*.png")):
        img = cv2.imread(str(f), cv2.IMREAD_UNCHANGED)
        if img is not None and img.ndim == 3 and img.shape[2] == 4:
            frames.append(cv2.resize(img, (TAMANHO, TAMANHO)))
    if not frames:
        console.log(f"[yellow]Sem PNG em assets/{nome} -> animação provisória[/]")
        for i in range(48):
            img = np.zeros((TAMANHO, TAMANHO, 4), np.uint8)
            y = int(130 - 60 * abs(np.sin(np.pi * i / 24)))
            cv2.circle(img, (TAMANHO // 2, y), 50, (0, 180, 255, 255), -1)
            frames.append(img)
    return frames


def colar(fundo, img, x, y):
    """Cola img (BGRA) em fundo (BGR) usando o canal alfa."""
    h, w = img.shape[:2]
    H, W = fundo.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x0 >= x1 or y0 >= y1:
        return
    f = img[y0 - y:y1 - y, x0 - x:x1 - x]
    a = f[:, :, 3:4] / 255.0
    fundo[y0:y1, x0:x1] = (a * f[:, :, :3] + (1 - a) * fundo[y0:y1, x0:x1]).astype(np.uint8)


def detetar(frame, anterior, mog2):
    """Devolve as caixas (x, y, w, h) com movimento e o frame cinzento atual."""
    cinza = cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (21, 21), 0)
    if mog2 is None:                                   # diferença de frames
        if anterior is None:
            return [], cinza
        a, mascara = cv2.threshold(cv2.absdiff(anterior, cinza), 25, 255, cv2.THRESH_BINARY)
    else:                                              # subtração de fundo
        a, mascara = cv2.threshold(mog2.apply(frame), 200, 255, cv2.THRESH_BINARY)  # 127 = sombra
    mascara = cv2.dilate(mascara, None, iterations=2)
    contornos, a = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return [cv2.boundingRect(c) for c in contornos if cv2.contourArea(c) > MIN_AREA], cinza


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--diff", action="store_true", help="usar diferença de frames em vez de MOG2")
    ap.add_argument("--source", default="0", help="câmara (0, 1...) ou ficheiro de vídeo")
    args = ap.parse_args()

    cap = cv2.VideoCapture(int(args.source) if args.source.isdigit() else args.source)
    if not cap.isOpened():
        console.log("[red]Não consegui abrir a câmara[/]")
        return
    mog2 = None if args.diff else cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=32)
    animacoes = [carregar_animacao(n) for n in ZONAS]

    estado = [None] * len(ZONAS)       
    registo = []                       
    anterior = None
    Path("evidencias").mkdir(exist_ok=True)

    def terminar(i, agora):
        e = estado[i]
        e["writer"].release()
        registo.append({"inicio": e["inicio"].isoformat(timespec="seconds"),
                        "duracao_s": round(e["ultimo"] - e["t0"], 2),
                        "zona": ZONAS[i], "ficheiro": e["ficheiro"], "caixas": e["caixas"][:300]})
        Path("evidencias/deteccoes.json").write_text(json.dumps(registo, indent=2), encoding="utf-8")
        console.log(f"[red]FIM[/] {ZONAS[i]} ({e['ultimo'] - e['t0']:.1f}s) -> {e['ficheiro']}")
        estado[i] = None

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(cv2.resize(frame, (640, 480)), 1)
        agora = time.time()
        caixas, anterior = detetar(frame, anterior, mog2)
        largura_zona = frame.shape[1] / len(ZONAS)

        # caixas por zona (pelo centro da caixa)
        por_zona = [[] for a in ZONAS]
        for (x, y, w, h) in caixas:
            por_zona[min(int((x + w / 2) / largura_zona), len(ZONAS) - 1)].append((x, y, w, h))
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        for i, cx in enumerate(por_zona):
            if cx:
                if estado[i] is None:                                  # novo evento
                    dt = datetime.now().astimezone()
                    pasta = Path("evidencias") / dt.strftime("%Y-%m-%d")
                    pasta.mkdir(parents=True, exist_ok=True)
                    ficheiro = str(pasta / f"{ZONAS[i]}a{dt:%Y%m%d_%H%M%S}.mp4")
                    writer = cv2.VideoWriter(ficheiro, cv2.VideoWriter_fourcc(*"mp4v"), 20, (640, 480))
                    estado[i] = {"inicio": dt, "t0": agora, "ficheiro": ficheiro,
                                 "writer": writer, "caixas": [], "ultimo": agora}
                    console.log(f"[green]INICIO[/] {ZONAS[i]}")
                estado[i]["ultimo"] = agora
                estado[i]["caixas"].append([list(map(int, b)) for b in cx])
            elif estado[i] and agora - estado[i]["ultimo"] > PAUSA:
                terminar(i, agora)

        # desenhar zonas e animações
        for i in range(len(ZONAS)):
            x0 = int(i * largura_zona)
            if i > 0:
                cv2.line(frame, (x0, 0), (x0, 480), (255, 255, 0), 1)
            cv2.putText(frame, f"Z{i + 1}", (x0 + 6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            if estado[i]:
                anim = animacoes[i]
                img = anim[int((agora - estado[i]["t0"]) * FPS_ANIM) % len(anim)]
                colar(frame, img, int((i + 0.5) * largura_zona) - TAMANHO // 2, 480 // 2)
                estado[i]["writer"].write(frame)

        cv2.imshow("A cena reage ao movimento", frame)
        if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
            break

    for i, e in enumerate(estado):
        if e:
            terminar(i, time.time())
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()