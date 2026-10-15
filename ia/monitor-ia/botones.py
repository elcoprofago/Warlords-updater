# Arma los botones cuadrados del Monitor de IA (assets/nueva_*.png y cortar_*.png) a partir de las imágenes
# AM_*.png y red_*.png, que traen el rótulo "LMF SOLO" / "LMF MUTE": borra ese texto rellenándolo con el brillo de
# alrededor y escribe el nuevo con el mismo color de letra. Correr de nuevo solo si cambian las imágenes o el texto.
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
# nombre: (imagen de base, líneas de texto, corrimiento de tono en grados: el naranja sale del ámbar)
BOTONES = {'nueva': ('AM', ('NUEVA', 'TANDA'), 0), 'retomar': ('AM', ('RETOMAR',), -22),
           'cortar': ('red', ('CORTAR',), 0)}


def tono(img, grados):
    if not grados:
        return img
    alfa = img.getchannel('A')
    h, s, v = img.convert('RGB').convert('HSV').split()
    h = h.point(lambda x: int(x + grados * 256 / 360) % 256)
    img = Image.merge('HSV', (h, s, v)).convert('RGBA')
    img.putalpha(alfa)
    return img
FUENTE = r'C:\Windows\Fonts\arialbd.ttf'


def rehacer(origen, lineas, grados=0):
    img = tono(Image.open(os.path.join(ASSETS, origen)).convert('RGBA'), grados)
    a = np.asarray(img).astype(float)
    w, h = img.size
    # La cara iluminada del botón: el centro, lejos del marco.
    x0, x1, y0, y1 = int(w * .22), int(w * .78), int(h * .22), int(h * .78)
    lum = a[..., :3].mean(axis=2)
    # Letra: lo bastante más oscuro que su vecindad (la cara tiene degradé, un umbral fijo no sirve).
    vecindad = np.asarray(Image.fromarray(lum.astype(np.uint8)).filter(ImageFilter.MedianFilter(21))).astype(float)
    letra = np.zeros(lum.shape, bool)
    letra[y0:y1, x0:x1] = (vecindad - lum)[y0:y1, x0:x1] > 12
    tinta = tuple(int(v) for v in np.median(a[letra][:, :3], axis=0)) if letra.any() else (40, 30, 20)
    mascara = np.asarray(Image.fromarray(letra.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(5))) > 0
    # Rellenar lo enmascarado difundiendo los colores de alrededor.
    rgb = a[..., :3].copy()
    conocido = ~mascara
    rgb[mascara] = 0
    for _ in range(400):
        if conocido.all():
            break
        suma = np.zeros_like(rgb); cuenta = np.zeros(lum.shape)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            suma += np.roll(np.where(conocido[..., None], rgb, 0), (dy, dx), (0, 1))
            cuenta += np.roll(conocido, (dy, dx), (0, 1))
        nuevos = ~conocido & (cuenta > 0)
        rgb[nuevos] = suma[nuevos] / cuenta[nuevos][:, None]
        conocido = conocido | nuevos
    # Suavizar el relleno para que no queden vetas.
    liso = np.asarray(Image.fromarray(rgb.astype(np.uint8)).filter(ImageFilter.GaussianBlur(4))).astype(float)
    rgb[mascara] = liso[mascara]
    a[..., :3] = rgb
    img = Image.fromarray(a.astype(np.uint8), 'RGBA')

    d = ImageDraw.Draw(img)
    tam = 27 if len(lineas) > 1 else 25
    f = ImageFont.truetype(FUENTE, tam)
    alto = tam * 1.15
    y = h / 2 - alto * len(lineas) / 2
    for ln in lineas:
        ancho = d.textlength(ln, font=f)
        while ancho > w * .58:
            tam -= 1; f = ImageFont.truetype(FUENTE, tam); ancho = d.textlength(ln, font=f)
        d.text((w / 2 - ancho / 2, y), ln, font=f, fill=tinta + (235,))
        y += alto
    return img


if __name__ == '__main__':
    for nombre, (base, lineas, grados) in BOTONES.items():
        for estado in ('on', 'off'):
            rehacer(f'{base}_{estado}.png', lineas, grados).save(os.path.join(ASSETS, f'{nombre}_{estado}.png'))
            print(f'assets/{nombre}_{estado}.png')
