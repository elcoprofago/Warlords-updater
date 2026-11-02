# Dibuja el ícono del Visor (medalla.png y medalla.ico): un trofeo dorado delante de dos espadas cruzadas (la guerra y
# la alianza), una de ellas quebrada (la traición), sobre un escudo. Se dibuja a 1024 px y se achica, para suavizar.
# Uso: python ia\visor-historia\icono.py
import os
from PIL import Image, ImageDraw

AQUI = os.path.dirname(os.path.abspath(__file__))
N = 1024
im = Image.new('RGBA', (N, N))
d = ImageDraw.Draw(im)
ORO, ORO_OSC, ORO_CLA = (232, 180, 40), (150, 100, 10), (255, 230, 120)
ACERO, ACERO_OSC = (215, 220, 230), (90, 95, 110)


def escudo(m, relleno, borde, ancho):
    # escudo heráldico: arriba recto, lados que bajan y se curvan hasta la punta
    import math
    pts = [(m, m), (N - m, m)]
    for i in range(41):
        t = i / 40
        pts.append((N - m - (N / 2 - m) * (1 - math.cos(t * math.pi / 2)), m + (N - 2 * m) * 0.42 + (N - 2 * m) * 0.58 * math.sin(t * math.pi / 2)))
    pts += [(N - x, y) for x, y in reversed(pts[2:])]
    d.polygon(pts, fill=relleno)
    d.line(pts + [pts[0]], fill=borde, width=ancho, joint='curve')
escudo(30, (110, 15, 20), ORO_OSC, 40)
escudo(70, (150, 25, 30), ORO, 18)


def espada(x0, y0, x1, y1, quebrada=False):
    """Hoja de (x0, y0), la empuñadura, a (x1, y1), la punta; la quebrada termina a mitad, con el corte en diagonal."""
    import math
    ang = math.atan2(y1 - y0, x1 - x0)
    ux, uy = math.cos(ang), math.sin(ang)
    px, py = -uy, ux
    largo = math.hypot(x1 - x0, y1 - y0) * (0.78 if quebrada else 1)
    w = 34
    a = (x0 + px * w, y0 + py * w)
    b = (x0 - px * w, y0 - py * w)
    if quebrada:
        c = (x0 + ux * largo - px * w, y0 + uy * largo - py * w)
        e = (x0 + ux * (largo + 60) + px * w, y0 + uy * (largo + 60) + py * w)
        hoja = [a, b, c, e]
        # la punta caída, suelta y torcida, más allá
        t = largo + 150
        q = [(x0 + ux * t + px * w * 0.8, y0 + uy * t + py * w * 0.8),
             (x0 + ux * (t - 40) - px * w * 0.8, y0 + uy * (t - 40) - py * w * 0.8),
             (x0 + ux * (t + 170), y0 + uy * (t + 170) + 30)]
        d.polygon(q, fill=ACERO, outline=ACERO_OSC, width=8)
    else:
        hoja = [a, b, (x0 + ux * (largo - 90) - px * w, y0 + uy * (largo - 90) - py * w), (x1, y1),
                (x0 + ux * (largo - 90) + px * w, y0 + uy * (largo - 90) + py * w)]
    d.polygon(hoja, fill=ACERO, outline=ACERO_OSC, width=8)
    # guarda, puño y pomo
    g = 120
    d.line([(x0 + px * g, y0 + py * g), (x0 - px * g, y0 - py * g)], fill=ORO, width=40)
    d.line([(x0, y0), (x0 - ux * 130, y0 - uy * 130)], fill=(90, 50, 20), width=36)
    d.ellipse([x0 - ux * 150 - 34, y0 - uy * 150 - 34, x0 - ux * 150 + 34, y0 - uy * 150 + 34], fill=ORO, outline=ORO_OSC, width=6)
espada(260, 780, 860, 150)                 # entera
espada(764, 780, 164, 150, quebrada=True)  # la traición

# trofeo: copa, asas, pie
cx = N / 2
d.ellipse([cx - 230, 230, cx + 230, 330], fill=ORO_CLA, outline=ORO_OSC, width=10)
d.chord([cx - 230, 30, cx + 230, 640], 0, 180, fill=ORO, outline=ORO_OSC, width=10)
d.rectangle([cx - 230, 280, cx + 230, 335], fill=ORO)
d.ellipse([cx - 230, 240, cx + 230, 320], fill=ORO_CLA, outline=ORO_OSC, width=10)
for s in (-1, 1):
    d.arc([cx + s * 240 - 80, 300, cx + s * 240 + 80, 500], 90 if s < 0 else 270, 270 if s < 0 else 90, fill=ORO_OSC, width=46)
    d.arc([cx + s * 240 - 80, 300, cx + s * 240 + 80, 500], 90 if s < 0 else 270, 270 if s < 0 else 90, fill=ORO, width=28)
d.polygon([(cx - 45, 620), (cx + 45, 620), (cx + 70, 760), (cx - 70, 760)], fill=ORO, outline=ORO_OSC, width=10)
d.rounded_rectangle([cx - 180, 750, cx + 180, 830], 20, fill=ORO, outline=ORO_OSC, width=10)
d.rounded_rectangle([cx - 140, 820, cx + 140, 880], 16, fill=ORO_OSC)
d.ellipse([cx - 120, 370, cx - 60, 520], fill=ORO_CLA)   # brillo
# estrella en la copa
import math
est = [(cx + (70 if i % 2 == 0 else 28) * math.sin(i * math.pi / 5), 460 - (70 if i % 2 == 0 else 28) * math.cos(i * math.pi / 5)) for i in range(10)]
d.polygon(est, fill=(150, 25, 30), outline=ORO_OSC, width=6)

ico = im.resize((256, 256), Image.LANCZOS)
ico.save(os.path.join(AQUI, 'medalla.png'))
ico.save(os.path.join(AQUI, 'medalla.ico'), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
