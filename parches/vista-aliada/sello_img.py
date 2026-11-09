# Imagen del sello de Army List (pedido del usuario, 8/11/2026): certif.png (sello dorado «CERTIFIED») de base, con su
# centro («ISO 14001») tapado por un disco blanco con sombra suave y centro.png (la estrella azul) reducida encima.
import os
from PIL import Image, ImageDraw, ImageFilter
AQUI = os.path.dirname(os.path.abspath(__file__))
CX, CY, R_TAPA, ANCHO_CENTRO = 120, 112, 44, 80

def sello_rgba():
    b = Image.open(os.path.join(AQUI, 'certif.png')).convert('RGB'); w, h = b.size
    # afuera = blanco que se toca con los bordes
    blanco = lambda c: min(c) >= 235
    afuera, pila = set(), [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for x in (0, w - 1) for y in range(h)]
    while pila:
        x, y = pila.pop()
        if (x, y) in afuera or not (0 <= x < w and 0 <= y < h) or not blanco(b.getpixel((x, y))): continue
        afuera.add((x, y)); pila += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    a = b.convert('RGBA')
    for x, y in afuera: a.putpixel((x, y), (0, 0, 0, 0))
    # disco que tapa «ISO 14001»: gris claro en el borde, blanco al centro
    tapa = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(tapa)
    for r in range(R_TAPA, 0, -1):
        v = 238 + round(17 * (1 - r / R_TAPA))
        d.ellipse((CX - r, CY - r, CX + r, CY + r), fill=(v, v, v, 255))
    m = Image.new('L', (w, h)); ImageDraw.Draw(m).ellipse((CX - R_TAPA, CY - R_TAPA, CX + R_TAPA, CY + R_TAPA), fill=255)
    tapa.putalpha(m.filter(ImageFilter.GaussianBlur(2)))
    a = Image.alpha_composite(a, tapa)
    c = Image.open(os.path.join(AQUI, 'centro.png')).convert('RGBA')
    # su fondo negro (lo que se toca con los bordes) pasa a transparente
    cw, ch = c.size
    negro = lambda q: max(q[:3]) <= 40
    vis, pila = set(), [(x, y) for x in range(cw) for y in (0, ch - 1)] + [(x, y) for x in (0, cw - 1) for y in range(ch)]
    while pila:
        x, y = pila.pop()
        if (x, y) in vis or not (0 <= x < cw and 0 <= y < ch) or not negro(c.getpixel((x, y))): continue
        vis.add((x, y)); pila += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    # y los pozos oscuros que quedan entre los rayos, sin tocar la gema del medio
    for y in range(ch):
        for x in range(cw):
            if (x - cw / 2) ** 2 + (y - ch / 2) ** 2 > 14 ** 2 and max(c.getpixel((x, y))[:3]) <= 60: vis.add((x, y))
    for q in vis: c.putpixel(q, (0, 0, 0, 0))
    c = c.resize((ANCHO_CENTRO, round(c.height * ANCHO_CENTRO / c.width)), Image.LANCZOS)
    a.alpha_composite(c, (CX - c.width // 2, CY - c.height // 2))
    return a.crop(a.getbbox())

if __name__ == '__main__':
    import sys
    s = sello_rgba(); s.save(sys.argv[1]); s.resize((54, round(54 * s.height / s.width)), Image.LANCZOS).save(sys.argv[2])
