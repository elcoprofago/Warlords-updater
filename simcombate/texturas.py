# Texturas para el fondo de los paneles (atacante, defensor y terreno), elegibles en Configuración (13/11/2026).
# Son claras a propósito: la letra de los paneles es oscura. Se generan con PIL (sin archivos aparte) salvo el
# mármol, que es MARBLE.PCX del juego aclarado; si no está la carpeta del juego, esa opción queda en liso.
import os
from PIL import Image, ImageFilter, ImageChops, ImageOps

NOMBRES = {'liso': 'Liso (sin textura)', 'pergamino': 'Pergamino', 'piedra': 'Piedra', 'madera': 'Madera',
           'marmol': 'Mármol claro (del juego)'}


def _ruido(w, h, escala, sigma=64, blur=0):
    """Ruido gris de grano `escala` (1 = fino), estirado al tamaño pedido."""
    r = Image.effect_noise((max(1, w // escala), max(1, h // escala)), sigma).resize((w, h), Image.BICUBIC)
    return r.filter(ImageFilter.GaussianBlur(blur)) if blur else r


def _tenir(gris, oscuro, claro):
    """Pasa un gris a la rampa oscuro→claro."""
    return Image.merge('RGB', [gris.point(lambda v, a=a, b=b: a + (b - a) * v // 255) for a, b in zip(oscuro, claro)])


def textura(nombre, w, h, juego=None, pcx=None):
    """La textura `nombre` de w×h, o None para liso (o si falta lo que hace falta para hacerla)."""
    if nombre == 'pergamino':
        g = ImageChops.add(_ruido(w, h, 40, 50, 6), _ruido(w, h, 1, 30), scale=2.0)
        return _tenir(g, (200, 176, 128), (250, 238, 205))
    if nombre == 'piedra':
        g = ImageChops.add(_ruido(w, h, 12, 60, 2), _ruido(w, h, 1, 40), scale=2.0)
        return _tenir(g, (170, 168, 160), (230, 228, 222))
    if nombre == 'madera':
        vetas = ImageOps.autocontrast(_ruido(w, h, 1, 80).resize((max(1, w // 60), h)).resize((w, h), Image.BICUBIC), cutoff=2)
        g = ImageChops.add(vetas, _ruido(w, h, 1, 25), scale=2.0)
        return _tenir(g, (176, 132, 84), (232, 200, 152))
    if nombre == 'marmol' and juego and pcx:
        t = pcx(os.path.join(juego, 'EDPICTS', 'MARBLE.PCX'))
        if t is None: return None
        t = t.convert('L'); m = Image.new('L', (w, h))
        for y in range(0, h, t.height):
            for x in range(0, w, t.width): m.paste(t, (x, y))
        return _tenir(m, (170, 186, 204), (240, 246, 252))
    return None


def promedio(im):
    """Color medio de la textura (#rrggbb), para lo que no puede llevar imagen de fondo (casillas de opción)."""
    r, g, b = im.resize((1, 1), Image.BOX).getpixel((0, 0))
    return f'#{r:02x}{g:02x}{b:02x}'
