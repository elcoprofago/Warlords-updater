# Gráficos de las obras (PENDIENTE-construcciones, pedido del 9/11/2026 después de 1.0.150.0): más grandes y en la
# perspectiva del juego (de arriba y de frente, como las ruinas y las ciudades: el frente sur se ve, la sombra cae al
# sureste). Cada capa es un lienzo de 144x144 = 3x3 casillas de 48 con la casilla de la obra en el medio; build.py la
# corta en 9 piezas y po_draw pinta en cada celda las piezas que le tocan de las obras de sus 8 vecinas y la propia.
# Así una torre puede asomar sobre la casilla de arriba y un muro empalmar con el del vecino sin cortes.
#
# Render por vóxeles: un mapa de alturas sobre el suelo (x, y del lienzo); cada columna se pinta de z = 0 a su altura
# en (x, y - z), de atrás (norte) hacia adelante (sur), así lo de adelante tapa lo de atrás. La cara de frente (la
# vecina sur es más baja) lleva la textura; la de arriba, más clara; los costados, más oscuros (luz del oeste).
# Muro de piedra: la piedra y las almenas de la ruina grande del juego (RUINS\ruin_lrg.PCX, pedido del usuario).
import math, random
from PIL import Image

C = 72          # centro del lienzo = centro de la casilla de la obra
T = 9           # ancho de la empalizada en el suelo
H = 15          # alto de la empalizada
TM = 16         # ancho del muro de piedra en el suelo
HM = 32         # alto del muro de piedra: como el frente de la ruina grande (pedido del 9/11/2026)
RDX = [0, 1, 1, 1, 0, -1, -1, -1]       # N, NE, E, SE, S, SO, O, NO
RDY = [-1, -1, 0, 1, 1, 1, 0, -1]


class Lienzo:
    def __init__(self, ruina, color):
        self.r = ruina.convert('RGB')     # cuadro 0 de ruin_lrg (87x88)
        self.color = color                # rgb -> índice de la paleta del mapa
        self.px = {}                      # (x, y) pantalla -> rgb
        self.cuerpo = set()               # píxeles de pantalla del cuerpo (no sombra)

    def piedra(self, u, v):               # frente de la ruina sobre la puerta: x 31..54, y 29..40
        return _limpia(self.r.getpixel((31 + u % 24, 29 + v % 12)), u, v)

    def almena(self, u, v):               # banda de almenas de la ruina: x 28..63, y 19..28
        return _limpia(self.r.getpixel((28 + u % 36, 19 + min(9, max(0, v)))), u, v)

    def voxeles(self, alto, cara, arriba):
        # alto: {(gx, gy): h}; cara(gx, gy, z, lado) -> rgb, lado 0 frente, 1 costado este, 2 costado oeste;
        # arriba(gx, gy) -> rgb
        for gy in sorted({p[1] for p in alto}):
            for gx in sorted(p[0] for p in alto if p[1] == gy):
                h = alto[(gx, gy)]
                for z in range(h + 1):
                    if z == h: c = arriba(gx, gy)
                    elif alto.get((gx, gy + 1), -1) < z: c = cara(gx, gy, z, 0)
                    elif alto.get((gx + 1, gy), -1) < z: c = cara(gx, gy, z, 1)
                    elif alto.get((gx - 1, gy), -1) < z: c = cara(gx, gy, z, 2)
                    else: c = cara(gx, gy, z, 0)
                    q = (gx, gy - z)
                    self.px[q] = c
                    self.cuerpo.add(q)

    def sombra(self, alto, prohibido=()):
        for (gx, gy), h in alto.items():
            for s in range(0, h + 1, 1):
                q = (round(gx + s * 0.55), round(gy + s * 0.22))
                if q not in self.cuerpo and q not in prohibido: self.px[q] = (16, 14, 10)

    def imagen(self, pal):
        im = Image.new('P', (144, 144), 11); im.putpalette(pal)
        for (x, y), c in self.px.items():
            if 0 <= x < 144 and 0 <= y < 144: im.putpixel((x, y), self.color(c))
        return im


def _limpia(c, u, v):
    # Sin las manchas blancas (brillos casi blancos) ni la hiedra verde de la ruina (pedido del 9/11/2026): esos
    # píxeles pasan a piedra gris de brillo medio, con un poco de variación para que no quede liso.
    r, g, b = c
    if max(c) > 175 or (g > r + 12 and g > b + 12):
        k = 96 + 10 * ((u * 5 + v * 3) % 3)
        return (k, k, k - 6)
    return c


def _mul(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


# ---- muros: brazo d (0..7) o centro (d = None)
def _huella_brazo(d, ancho):
    n = math.hypot(RDX[d], RDY[d])
    largo = 24 * n
    ux, uy = RDX[d] / n, RDY[d] / n
    pts = {}
    for gy in range(C - 30, C + 31):
        for gx in range(C - 30, C + 31):
            a = (gx + 0.5 - C) * ux + (gy + 0.5 - C) * uy        # a lo largo
            w = -(gx + 0.5 - C) * uy + (gy + 0.5 - C) * ux       # de costado
            if 0 <= a < largo and abs(w) < ancho / 2:
                pts[(gx, gy)] = (a, w)
    return pts


def _huella_centro(lado):
    return {(gx, gy): (gx - C, gy - C) for gx in range(C - lado // 2, C - lado // 2 + lado)
            for gy in range(C - lado // 2, C - lado // 2 + lado)}


def cuerpos_muro(empal):
    """Píxeles de pantalla de todos los cuerpos posibles (brazos, centro, y los de las 8 vecinas): la sombra no los pisa."""
    tot = set()
    for d in list(range(8)) + [None]:
        lz = Lienzo(Image.new('RGB', (87, 88)), lambda c: 0)
        _muro_en(lz, d, empal, sombra=False)
        tot |= lz.cuerpo
    out = set()
    for ox in (-48, 0, 48):
        for oy in (-48, 0, 48):
            out |= {(x + ox, y + oy) for x, y in tot}
    return out


def _muro_en(lz, d, empal, sombra=True, prohibido=()):
    if d is None:
        ancho = T + 1 if empal else TM + 6     # piedra: el centro cubre al brazo más ancho
        huella = _huella_centro(round(ancho))
        base = H if empal else HM
    else:
        # piedra: el brazo que corre de norte a sur se ve de costado y parecía muy fino (pedido del 9/11/2026):
        # se ensancha según cuánto avanza hacia el norte o el sur
        ancho = T if empal else TM + 6 * abs(RDY[d]) / math.hypot(RDX[d], RDY[d])
        huella = _huella_brazo(d, ancho)
        base = H if empal else HM
    alto, coord = {}, {}
    for (gx, gy), (a, w) in huella.items():
        if empal:
            k = int(a) % 4 if d is not None else int(gx) % 4
            h = base + 2 - (0 if k in (1, 2) else 3)               # estacas aguzadas
        else:
            borde = abs(w) > ancho / 2 - 3.5
            k = int(a if d is not None else gx) // 4 % 2
            h = base + (5 if borde and k == 0 else 0)            # almenas en los bordes
        alto[(gx, gy)] = h
        coord[(gx, gy)] = (a, w)
    if sombra: lz.sombra(alto, prohibido)

    if empal:
        def cara(gx, gy, z, lado):
            a, w = coord[(gx, gy)]
            k = int(a if d is not None else gx) % 4
            c = (128, 86, 44) if k in (1, 2) else (92, 62, 32)
            if z in (4, H - 4): c = (64, 44, 24)                 # travesaños
            return _mul(c, (1.0, 0.65, 0.85)[lado] * (0.92 + 0.08 * ((gx * 7 + z * 3) % 3)))

        def arriba(gx, gy):
            return (150, 108, 60)
    else:
        # Sin rayas tipo «código de barras» (pedido del 9/11/2026): la textura de piedra se toma con la coordenada
        # de la cara que se ve (x en el frente, y en los costados) y la altura en pantalla, así las hiladas quedan
        # horizontales y continuas; la parte de arriba es piedra lisa con apenas ruido, no la banda de almenas.
        def cara(gx, gy, z, lado):
            u = gx if lado == 0 else gy
            return _mul(lz.piedra(u, gy - z), (1.0, 0.7, 0.85)[lado])

        def arriba(gx, gy):
            k = 128 + 6 * ((gx * 7 + gy * 13) % 3)
            return (k, k - 2, k - 8)
    lz.voxeles(alto, cara, arriba)


def muro(ruina, color, pal, d, empal, prohibido):
    lz = Lienzo(ruina, color)
    _muro_en(lz, d, empal, prohibido=prohibido)
    return lz.imagen(pal)


# ---- torre de vigía y faro: cilindros que asoman sobre la casilla de arriba
def torre(ruina, color, pal, faro=False):
    lz = Lienzo(ruina, color)
    cy = C + 8                                   # base hacia el frente de la casilla
    R = 10 if faro else 12
    Ht = 44 if faro else 40
    alto, ang = {}, {}
    for gy in range(cy - R - 1, cy + R + 2):
        for gx in range(C - R - 1, C + R + 2):
            dx, dy = gx + 0.5 - C, gy + 0.5 - cy
            r = math.hypot(dx, dy)
            if r <= R:
                a = math.atan2(dy, dx)
                h = Ht
                if not faro and r > R - 3 and int((a + math.pi) / (2 * math.pi) * 16) % 2 == 0: h += 4   # almenas
                alto[(gx, gy)] = h
                ang[(gx, gy)] = (dx / R, a)
    lz.sombra(alto)

    def cara(gx, gy, z, lado):
        nx, a = ang[(gx, gy)]
        luz = 1.05 - 0.45 * max(-1, min(1, nx))
        u = int((a + math.pi) * R)
        if faro:
            c = (205, 45, 38) if ((Ht - z) // 8) % 2 else (228, 224, 212)
            c = _mul(c, luz * (0.94 + 0.06 * ((u + z) % 2)))
        else:
            c = _mul(lz.piedra(u, Ht - z), luz)
            if alto[(gx, gy)] > Ht and z >= Ht - 1: c = _mul(lz.almena(u, 3), luz)
        # puerta y ventana en el frente
        if abs(gx + 0.5 - C) < 3 and gy >= cy + R - 2:
            if z < 9: c = (48, 30, 14) if z < 8 else (30, 22, 12)
            if 22 <= z < 27 and abs(gx + 0.5 - C) < 2: c = (14, 12, 10)
        return c

    def arriba(gx, gy):
        if faro: return (70, 62, 55)
        return (52, 48, 42) if alto[(gx, gy)] == Ht else _mul(lz.almena(gx, 1), 1.0)
    lz.voxeles(alto, cara, arriba)

    if faro:                                     # balcón, linterna encendida y cúpula
        top = cy - Ht
        for y in range(top - 2, top + 1):
            for x in range(C - R - 2, C + R + 2): lz.px[(x, y)] = (58, 52, 46)
        for y in range(top - 12, top - 2):
            for x in range(C - 6, C + 6):
                f = 1 - abs(x + 0.5 - C) / 7
                lz.px[(x, y)] = (255, int(205 + 45 * f), int(70 + 120 * f)) if (x - C) % 4 else (50, 45, 40)
        for y in range(top - 19, top - 12):
            w = (y - (top - 20)) * 1.2
            for x in range(C - 9, C + 9):
                if abs(x + 0.5 - C) <= w: lz.px[(x, y)] = (110, 30, 25) if x >= C else (175, 52, 40)
        for x in range(C - 22, C + 22):          # destello
            if abs(x + 0.5 - C) > 8 and x % 2 == 0: lz.px[(x, top - 7)] = (255, 240, 140)
    return lz.imagen(pal)
