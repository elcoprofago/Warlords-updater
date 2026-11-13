# Contador general de pruebas del Simulador (pedido del usuario, 13/11/2026): cuenta cada «INICIAR COMBATE», no se
# borra al cerrar (va en el .ini, sección [contador]) y se pone en cero a mano o solo, por período (día, semana, mes,
# año). odometro() lo dibuja como un contador mecánico de rodillos: marco negro con bisel, rodillos cilíndricos con
# el número vivo al centro y el anterior/siguiente asomando arriba y abajo.
import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PERIODOS = {'manual': 'Solo a mano', 'dia': 'Reset diario', 'semana': 'Reset semanal', 'mes': 'Reset mes',
            'anio': 'Reset año'}

def clave(periodo, d=None):
    """Identifica el período de la fecha d: cuando cambia, el contador vuelve a cero."""
    d = d or datetime.date.today()
    return {'dia': d.isoformat(), 'semana': '%d-S%02d' % d.isocalendar()[:2], 'mes': d.strftime('%Y-%m'),
            'anio': str(d.year)}.get(periodo, '')

def _fuente(px):
    for f in ('arialbd.ttf', 'seguisb.ttf', 'DejaVuSans-Bold.ttf'):
        try: return ImageFont.truetype(f, px)
        except OSError: pass
    return ImageFont.load_default()

def odometro(n, digitos=6, alto=38):
    """Imagen RGBA del contador con el valor n (se recorta a los últimos `digitos`)."""
    s = 3; H = alto * s                      # se dibuja a 3x y se achica: bordes suaves
    rw, gap, bor = int(H * 0.52), int(H * 0.06), int(H * 0.16)
    W = bor * 2 + digitos * rw + (digitos - 1) * gap
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    # marco: placa negra con bisel claro arriba y oscuro abajo, y la ventana hundida
    d.rounded_rectangle((0, 0, W - 1, H - 1), radius=H // 10, fill=(28, 30, 32), outline=(90, 94, 98), width=s * 2)
    d.line((H // 10, s, W - H // 10, s), fill=(140, 145, 150), width=s)
    v0, v1 = bor - gap, H - bor + gap
    d.rectangle((bor - gap * 2, v0 - gap, W - bor + gap * 2, v1 + gap), fill=(8, 8, 9), outline=(60, 62, 66), width=s)
    f_big, f_sm = _fuente(int(H * 0.36)), _fuente(int(H * 0.22))
    txt = str(max(0, n))[-digitos:].rjust(digitos, '0')
    alto_r = v1 - v0
    for k, ch in enumerate(txt):
        x0 = bor + k * (rw + gap)
        r = Image.new('RGBA', (rw, alto_r)); rd = ImageDraw.Draw(r)
        for y in range(alto_r):              # cilindro: brillo máximo un poco arriba del centro
            t = abs((y - alto_r * 0.42) / (alto_r / 2)); v = int(70 * max(0, 1 - t * t)) + 6
            rd.line((0, y, rw, y), fill=(v, v + 2, v + 4, 255))
        c = int(ch)
        for dy, num, f, col in ((-0.36, (c - 1) % 10, f_sm, 150), (0.0, c, f_big, 250), (0.36, (c + 1) % 10, f_sm, 150)):
            rd.text((rw / 2, alto_r / 2 + dy * alto_r), str(num), font=f, fill=(col, col, col, 255), anchor='mm')
        sombra = Image.new('L', (rw, alto_r), 0); sd = ImageDraw.Draw(sombra)
        for y in range(alto_r):              # los bordes del rodillo se pierden en la oscuridad
            t = abs((y - alto_r / 2) / (alto_r / 2)); sd.line((0, y, rw, y), fill=int(255 * min(1, max(0, (t - 0.45) / 0.55)) ** 1.5))
        r = Image.composite(Image.new('RGBA', r.size, (4, 4, 5, 255)), r, sombra)
        rd = ImageDraw.Draw(r); rd.line((0, 0, 0, alto_r), fill=(0, 0, 0, 255), width=s); rd.line((rw - 1, 0, rw - 1, alto_r), fill=(0, 0, 0, 255), width=s)
        im.paste(r, (x0, v0))
    # reflejo del vidrio
    brillo = Image.new('RGBA', im.size, (0, 0, 0, 0)); bd = ImageDraw.Draw(brillo)
    bd.rectangle((bor, v0, W - bor, v0 + alto_r * 0.3), fill=(255, 255, 255, 22))
    im.alpha_composite(brillo.filter(ImageFilter.GaussianBlur(s * 2)))
    return im.resize((W // s, alto), Image.LANCZOS)

if __name__ == '__main__':
    import sys; odometro(int(sys.argv[1]) if len(sys.argv) > 1 else 1234).save(sys.argv[2] if len(sys.argv) > 2 else 'odometro.png')
