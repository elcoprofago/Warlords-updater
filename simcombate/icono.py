# Genera el ícono del Simulador de combate: el escudo azul del juego con dos espadas cruzadas en el medio.
# Uso: python simcombate\icono.py   (escribe simcombate\icono.png y simcombate\icono.ico; build.py los usa)
import os
from PIL import Image, ImageDraw

AQUI = os.path.dirname(os.path.abspath(__file__))
ESCUDO = os.path.join(AQUI, 'escudo.png')   # el escudo azul que pasó el usuario (46x54)
L = 512                                     # se dibuja grande y se achica, para bordes suaves


def espada(d, angulo, cx, cy, largo):
    """Una espada con hoja plateada, guarda y pomo dorados, rotada `angulo` grados alrededor del centro."""
    import math
    a = math.radians(angulo); ux, uy = math.sin(a), -math.cos(a); px, py = -uy, ux
    def P(t, s): return (cx + ux * t + px * s, cy + uy * t + py * s)
    h, g = largo * 0.5, largo * 0.055
    hoja = [P(-h * 0.25, -g), P(h * 0.8, -g), P(h, 0), P(h * 0.8, g), P(-h * 0.25, g)]
    d.polygon(hoja, fill='#e8eef4', outline='#000000', width=10)
    d.line([P(-h * 0.2, 0), P(h * 0.85, 0)], fill='#9aa8b8', width=6)            # filo central
    guarda = [P(-h * 0.3, -g * 3.2), P(-h * 0.17, -g * 3.2), P(-h * 0.17, g * 3.2), P(-h * 0.3, g * 3.2)]
    d.polygon(guarda, fill='#e8c048', outline='#000000', width=10)
    puño = [P(-h * 0.3, -g * 0.9), P(-h * 0.5, -g * 0.9), P(-h * 0.5, g * 0.9), P(-h * 0.3, g * 0.9)]
    d.polygon(puño, fill='#6a3a18', outline='#000000', width=10)
    x, y = P(-h * 0.56, 0); r = g * 1.3
    d.ellipse((x - r, y - r, x + r, y + r), fill='#e8c048', outline='#000000', width=10)


def generar():
    esc = Image.open(ESCUDO).convert('RGBA')
    # el negro de afuera del escudo (las esquinas) pasa a transparente; el reborde negro del escudo queda
    for p in ((0, 0), (esc.width - 1, 0), (0, esc.height - 1), (esc.width - 1, esc.height - 1)):
        if esc.getpixel(p)[:3] == (0, 0, 0): ImageDraw.floodfill(esc, p, (0, 0, 0, 0), thresh=10)
    W, H = L * esc.width // esc.height, L
    base = esc.resize((W, H), Image.LANCZOS)
    capa = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(capa)
    cx, cy, largo = W / 2, H * 0.47, H * 0.78
    espada(d, 45, cx, cy, largo); espada(d, -45, cx, cy, largo)
    img = Image.alpha_composite(base, capa)
    cuadro = Image.new('RGBA', (L, L), (0, 0, 0, 0)); cuadro.paste(img, ((L - W) // 2, 0), img)
    cuadro.resize((256, 256), Image.LANCZOS).save(os.path.join(AQUI, 'icono.png'))
    cuadro.save(os.path.join(AQUI, 'icono.ico'), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


if __name__ == '__main__':
    generar(); print('icono.png e icono.ico listos')
