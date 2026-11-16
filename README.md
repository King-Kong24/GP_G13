# Esplanada Viva: a cena reage ao movimento

Projeto de Grupo · Computação Visual 2026/27 · LESTI · ISE, Universidade do Algarve

**Grupo:** GP_G13

| Elemento | Nº de aluno |
|----------|-------------|
| Cecilia Gutierrez   | a93524       |
| Raul Vilela   | a94290        |
| Duarte Mendonça   | a94182      |
| João Medeiros   | a94570       |

## Tema

Uma esplanada (mesa redonda, quatro cadeiras e lugares postos) criada em Blender que **reage a quem se mexe em frente à câmara**. A aplicação em Python + OpenCV divide a imagem da câmara em zonas; quando deteta movimento numa zona, mostra por cima do vídeo a animação do objeto dessa zona.

## Zonas

| Zona | Objeto | Animação (ciclo de 48 frames) | Pasta em `assets/` |
|------|--------|-------------------------------|--------------------|
| 1 (esquerda) | Mesa  | rotação da mesa | `assets/zona1_mesa/`  |
| 2 (centro)   | vaso | relva a sair do vaso     | `assets/zona2_vaso/` |
| 3 (direita)  | Copo  | gelo a cair no copo    | `assets/zona3_copo/`  |

## Estrutura do projeto

```
GP_Gn/
├── blender/        # um .blend por objeto/pessoa + render-base.blend (Blender 5.2 LTS, Pack Resources)
├── assets/         # sequências PNG (RGBA, 512x512, 24 fps), uma pasta por objeto
├── src/main.py     # aplicação (OpenCV)
├── apresemtação/          # conteudos para a apresentação
├── evidencias/     # gerado ao correr: vídeos MP4 e deteccoes.json
└── README.md
```

## Como correr

Requer [uv](https://docs.astral.sh/uv/) e uma câmara (ou um ficheiro de vídeo). As dependências (`opencv-python`, `numpy`, `rich`) estão declaradas no topo de `src/main.py` e o `uv` instala-as automaticamente.

```
uv run src/main.py                     # subtração de fundo (MOG2)
uv run src/main.py --diff              # diferença de frames
```

Correr a partir da pasta raiz do projeto (para encontrar `assets/` e escrever em `evidencias/`). Tecla **q** (ou ESC) para sair.

Se uma pasta de `assets/` não tiver PNG, a aplicação mostra uma animação provisória (círculo a saltar) e avisa na consola.

## Como funciona

**Parte A: Blender.** Os objetos foram modelados pelo grupo e têm materiais. Cada objeto que reage tem uma animação em ciclo, renderizada como sequência PNG com fundo transparente (`Render › Film › Transparent`, PNG RGBA, 512×512, 24 fps), com a mesma câmara e luz (`render-base.blend`).

**Parte B: OpenCV (visão computacional clássica, sem redes neuronais).**
1. Captura de vídeo em tempo real e redimensionamento para 640×480 (espelhado).
2. Deteção de movimento:
   - *diferença de frames:* cinzento, desfocagem gaussiana, `absdiff`, limiar, dilatação;
   - *subtração de fundo:* `MOG2` (sombras descartadas pelo limiar).
3. `findContours`, filtro por área mínima e `boundingRect` para obter as caixas com movimento, desenhadas no vídeo.
4. A imagem é dividida em colunas (zonas). A zona é a que contém o **centro** da caixa.
5. Numa zona com movimento, a animação PNG (lida com `cv2.IMREAD_UNCHANGED`) é composta sobre a imagem da câmara pelo canal alfa, em ciclo. A animação termina 1 s depois do último movimento.

## Evidências e registo

- Cada deteção grava um vídeo em `evidencias/AAAA-MM-DD/<zona>_<AAAAMMDD_HHMMSS>.mp4`.
- `evidencias/deteccoes.json` regista, por deteção: `inicio` (ISO 8601), `duracao_s`, `zona`, `ficheiro` e `caixas` (limitado a 300 entradas).
- A consola mostra o registo com cores e timestamps (`rich`).

## Declaração do uso de IA

- **Escrita de código:** (ex.: `src/main.py` foram escritos com ajuda de um assistente de IA (Claude) e depois revistos, testados e adaptados pelo grupo)
- **Outros usos:** apresentação, correção linguística do README. Indicar o quê e onde.)
- Os objetos 3D e as animações foram modelados e criados pelo grupo no Blender.

## Limitações conhecidas

- A deteção é sensível a mudanças de luz e a movimento no fundo; a subtração de fundo precisa de alguns segundos para estabilizar.
