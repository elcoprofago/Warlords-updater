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
HM = 24         # alto del muro de piedra: el frente de la ruina grande menos 2 hiladas del pie (pedido del 9/11/2026)
RT = 15         # radio de la torre redonda del muro de piedra
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

    def sombra(self, alto, prohibido=(), trama=False):
        # trama: sombra tramada que deja ver algo del suelo; tres de cada cuatro píxeles (pedido del 9/11/2026: un poco
        # más oscura que el damero de antes)
        for (gx, gy), h in alto.items():
            for s in range(0, h + 1, 1):
                q = (round(gx + s * 0.55), round(gy + s * 0.22))
                if trama and q[0] % 2 and q[1] % 2: continue
                if q not in self.cuerpo and q not in prohibido: self.px[q] = (16, 14, 10)

    def imagen(self, pal):
        im = Image.new('P', (144, 144), 11); im.putpalette(pal)
        for (x, y), c in self.px.items():
            if not (0 <= x < 144 and 0 <= y < 144): continue
            if len(c) == 4:
                c = c[:3]
                if _BAYER[y % 4][x % 4] < 3:
                    lum = sum(c) / 3
                    im.putpixel((x, y), min(PARDOS, key=lambda i: abs(sum(pal[3 * i:3 * i + 3]) / 3 - lum * 0.8)))
                    continue
            im.putpixel((x, y), self.color(c))
        return im


def _limpia(c, u, v):
    # Sin las manchas blancas (brillos casi blancos) ni la hiedra verde de la ruina (pedido del 9/11/2026): esos
    # píxeles pasan a piedra gris de brillo medio, con un poco de variación para que no quede liso.
    r, g, b = c
    if max(c) > 175 or (g > r + 12 and g > b + 12):
        k = 96 + 10 * ((u * 5 + v * 3) % 3)
        return (k, k, k - 6)
    return c


_CALZ = []
def _calzada(gx, gy):
    # Calzada de arriba del muro (pedido del 9/11/2026): la textura del camino de tierra del juego (road0.PCX de
    # TERRAIN/DATA, el tramo horizontal de la primera pieza, x 0..95, y 18..31) pasada a gris oscuro.
    if not _CALZ:
        im = Image.open(r'C:/Warlords3/TERRAIN/DATA/road0.PCX').convert('RGB')
        for y in range(18, 32):
            _CALZ.append([im.getpixel((x, y)) for x in range(96)])
    r, g, b = _CALZ[gy % 14][gx % 96]
    k = int((0.3 * r + 0.59 * g + 0.11 * b) * 0.62)
    return (k, k, k + 3)


def _mul(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def _pardo(c):
    # gris amarronado (pedido del 9/11/2026). La paleta del mapa no tiene grises pardos: el píxel queda marcado y
    # Lienzo.imagen lo trama, gris en la mayoría de los píxeles y un marrón de igual brillo en tres de cada dieciséis, un poco más oscuro.
    return tuple(c[:3]) + ('p',)


PARDOS = range(128, 136)        # rampa marrón de la paleta del mapa (la usan los gráficos de cavernas)
_BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


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


ORDEN_MURO = [0, 7, 1, 6, 2, None, 5, 3, 4]      # orden de las capas dentro de una casilla (od_ord de build.py; None = centro)


def cuerpos_muro(empal, d):
    """Píxeles de pantalla de los cuerpos que el juego pinta antes que la capa d (None = centro) en la misma casilla de
    pantalla, donde su sombra no puede caer: los de las capas anteriores de la propia casilla (ORDEN_MURO) y todos los
    de las vecinas de la fila de arriba y de la izquierda (ob_draw recorre las 9 vecinas de noroeste a sudeste). Lo
    que se pinta después tapa la sombra solo (pedido del 9/11/2026: con todo prohibido el muro casi no tenía sombra)."""
    def cuerpo(dd):
        lz = Lienzo(Image.new('RGB', (87, 88)), lambda c: 0)
        _muro_en(lz, dd, empal, sombra=False)
        return lz.cuerpo
    cu = {dd: cuerpo(dd) for dd in ORDEN_MURO}
    out = set().union(*(cu[dd] for dd in ORDEN_MURO[:ORDEN_MURO.index(d)]))
    for ox in (-1, 0, 1):
        for oy in (-1, 0, 1):
            if not (oy < 0 or (oy == 0 and ox < 0)): continue
            for dd, c in cu.items():
                # un brazo diagonal de la vecina que pasa al lado de esta casilla no existe si aquí hay muro (ob_wmask
                # descarta la diagonal cuando una de las dos casillas de en medio tiene muro)
                if dd is not None and dd % 2 and (0, 0) in ((ox, oy + RDY[dd]), (ox + RDX[dd], oy)): continue
                out |= {(x + 48 * ox, y + 48 * oy) for x, y in c}
    return out


def _torre_muro(cx, cy):
    """Torre redonda del muro de piedra centrada en (cx, cy): {(gx, gy): alto}, con almenas en el borde."""
    t = {}
    for gx in range(cx - RT, cx + RT):
        for gy in range(cy - RT, cy + RT):
            nx, ny = gx - cx + 0.5, gy - cy + 0.5
            r = math.hypot(nx, ny)
            if r > RT: continue
            u = int((math.atan2(ny, nx) + math.pi) * RT)
            t[(gx, gy)] = HM + 4 + ((6 if u % 8 < 5 else 2) if r > RT - 3 else 0)
    return t


def _ladrillo(u, v, luz):
    """Frente como el de la ruina grande: v = 0 moldura, 1 sombra, 2 línea negra; desde 3 hiladas de 4 (3 de piedra y
    1 de junta) con ladrillos de 6 + junta trabados media pieza; u corre a lo largo de la cara."""
    if v == 0: return _mul((152, 152, 152), luz)
    if v == 1: return _mul((114, 114, 116), luz)
    if v == 2: return _mul((24, 22, 22), luz)
    fila, r = divmod(v - 3, 4)
    if r == 3: return _mul((63, 61, 61), luz)
    pieza, q = divmod(u + (3 if fila % 2 else 0), 7)
    if q == 6: return _mul((63, 61, 61), luz)
    k = (87, 103, 111, 119, 95, 127)[(pieza * 5 + fila * 3) % 6]
    if (pieza * 7 + fila * 13) % 11 == 0: k = int(k * 0.62)   # algún que otro ladrillo más oscuro
    if r == 0: k = min(191, int(k * 1.4))           # canto de arriba, claro
    k = int(k * (1.0 - 0.05 * q))                   # se oscurece hacia la derecha
    return _mul((k, k, k + (2 if k % 2 else 0)), luz)


def _parapeto(t, oscura, luz):
    c = (184, 168, 154, 140, 130, 122)[min(t, 5)]
    if oscura: c = int(c * 0.8)
    return _mul((c, c, c), luz)


def _muro_en(lz, d, empal, sombra=True, prohibido=()):
    if not empal: return _muro_piedra(lz, d, sombra, prohibido)
    if d is None:
        ancho = T + 1
        huella = _huella_centro(round(ancho))
        base = H
        if False:
            # Piedra: torre redonda en cada casilla (pedido del 9/11/2026: las puntas de los tramos parecían un
            # código de barras), más ancha y 4 más alta que el muro, con almenas alrededor.
            huella = {(gx, gy): (gx - C, gy - C) for gx in range(C - RT, C + RT) for gy in range(C - RT, C + RT)
                      if math.hypot(gx - C + 0.5, gy - C + 0.5) <= RT}
            base = HM + 4
    else:
        # piedra: el brazo que corre de norte a sur se ve de costado y parecía muy fino (pedido del 9/11/2026):
        # se ensancha según cuánto avanza hacia el norte o el sur
        ancho = T if empal else TM + 6 * abs(RDY[d]) / math.hypot(RDX[d], RDY[d])
        huella = _huella_brazo(d, ancho)
        base = H if empal else HM
    alto, coord = {}, {}
    if d is not None and not empal:     # el tramo arranca en el borde de la torre: no la tapa con sus costados
        huella = {q: aw for q, aw in huella.items() if math.hypot(q[0] - C + 0.5, q[1] - C + 0.5) > RT - 0.5}
    for (gx, gy), (a, w) in huella.items():
        if empal:
            k = int(a) % 4 if d is not None else int(gx) % 4
            h = base + 2 - (0 if k in (1, 2) else 3)               # estacas aguzadas
        else:
            # Parapeto de 3 de grueso en los dos bordes (2 más alto que la calzada) con almenas de 5 cada 8 (4 más);
            # en el centro, solo pilares en las 4 esquinas, para no cortar la calzada de ningún brazo.
            if d is None:
                r = math.hypot(gx - C + 0.5, gy - C + 0.5)
                ang = math.atan2(gy - C + 0.5, gx - C + 0.5)
                h = base + ((6 if int((ang + math.pi) * RT) % 8 < 5 else 2) if r > RT - 3 else 0)
            else:
                borde = abs(w) > ancho / 2 - 3
                h = base + ((6 if a % 8 < 5 else 2) if borde else 0)
        alto[(gx, gy)] = h
        coord[(gx, gy)] = (a, w)
    if sombra: lz.sombra(alto, prohibido)
    amax = max((a for a, w in coord.values()), default=0)

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
        # Como el frente de la ruina grande (pedido del 9/11/2026): hiladas de 4 (3 de piedra y 1 de junta oscura),
        # ladrillos de 6 + junta, trabados media pieza por hilada, con el canto de arriba claro como en la ruina;
        # bajo la calzada una moldura clara y una línea de sombra; arriba parapeto y almenas de piedra clara. Las
        # hiladas se cuentan desde la calzada hacia abajo (v) y a lo largo del muro (u = a), así siguen al muro en
        # cualquier dirección, también en diagonal.
        def cara(gx, gy, z, lado):
            a, w = coord[(gx, gy)]
            if d is not None:
                # en la cara del extremo del tramo (la que topa con la torre vecina) los ladrillos corren a lo ancho
                u = int(a) if a < amax - 1.5 else int(w + 50)
                nx, ny = gx - C + 0.5, gy - C + 0.5
                if math.hypot(nx, ny) < RT + 2.5: u = int((math.atan2(ny, nx) + math.pi) * RT)   # junto a la torre
                luz = (1.0, 0.7, 0.85)[lado]
            else:                                           # torre: ladrillos alrededor, luz según hacia dónde mira
                nx, ny = gx - C + 0.5, gy - C + 0.5
                u = int((math.atan2(ny, nx) + math.pi) * RT)
                luz = 0.62 + 0.38 * max(0.0, (-0.45 * nx + 0.9 * ny) / max(1e-6, math.hypot(nx, ny)))
            if z >= base:                                   # parapeto y almenas
                t = alto[(gx, gy)] - z
                c = (184, 168, 154, 140, 130, 122)[min(t, 5)]
                if alto[(gx, gy)] > base + 2 and (int(a) if d is not None else u) % 8 >= 4: c = int(c * 0.8)
                return _mul((c, c, c), luz)
            v = base - 1 - z
            if v == 0: return _mul((152, 152, 152), luz)
            if v == 1: return _mul((114, 114, 116), luz)
            if v == 2: return _mul((24, 22, 22), luz)
            v -= 3
            fila, r = divmod(v, 4)
            if r == 3: return _mul((63, 61, 61), luz)
            uu = u + (3 if fila % 2 else 0)
            pieza, q = divmod(uu, 7)
            if q == 6: return _mul((63, 61, 61), luz)
            k = (87, 103, 111, 119, 95, 127)[(pieza * 5 + fila * 3) % 6]
            if r == 0: k = min(191, int(k * 1.4))           # canto de arriba, claro
            k = int(k * (1.0 - 0.05 * q))                   # se oscurece hacia la derecha
            return _mul((k, k, k + (2 if k % 2 else 0)), luz)

        def arriba(gx, gy):
            if alto[(gx, gy)] > base: return (190, 190, 186) if alto[(gx, gy)] > base + 2 else (156, 156, 154)
            return _calzada(gx, gy)
    lz.voxeles(alto, cara, arriba)




def _muro_piedra(lz, d, sombra, prohibido, puerta=None):
    # Muro de piedra (pedidos del 9/11/2026): torre redonda en cada casilla y tramos hasta la mitad del camino a la
    # vecina. Cada tramo se dibuja junto con las dos torres que une (la propia y la de la vecina), para que el orden de
    # pintado del juego (casillas de norte a sur) no deje un tramo encima de la torre de adelante: los píxeles de las
    # torres que repinta son iguales a los de su propia capa.
    torres = [(C, C)] if d is None else [(C, C), (C + 48 * RDX[d], C + 48 * RDY[d])]
    alto, quien = {}, {}
    for cx, cy in torres:
        for q, h in _torre_muro(cx, cy).items():
            alto[q] = h; quien[q] = (cx, cy)
    tramo = {}
    if d is not None:
        ancho = TM + 6 * abs(RDY[d]) / math.hypot(RDX[d], RDY[d])
        for (gx, gy), (a, w) in _huella_brazo(d, ancho).items():
            if any(math.hypot(gx - cx + 0.5, gy - cy + 0.5) <= RT for cx, cy in torres): continue
            borde = abs(w) > ancho / 2 - 3
            tramo[(gx, gy)] = (a, w)
            alto[(gx, gy)] = HM + ((6 if a % 8 < 5 else 2) if borde else 0)
    if sombra: lz.sombra({q: h for q, h in alto.items() if q in tramo or quien.get(q) == (C, C)}, prohibido, trama=True)

    def cara(gx, gy, z, lado):
        if (gx, gy) in tramo:
            a, w = tramo[(gx, gy)]
            u, luz, base = int(a), (1.0, 0.7, 0.85)[lado], HM
            # la cara que mira a lo largo del tramo (su punta, si no hay torre que la tape) va a lo ancho
            dx, dy = (RDX[d], RDY[d])
            nx, ny = ((0, 1), (1, 0), (-1, 0))[lado]
            if abs(nx * dx + ny * dy) / math.hypot(dx, dy) > 0.75: u = int(w + 50)
            oscura = a % 8 >= 4
        else:
            cx, cy = quien[(gx, gy)]
            nx, ny = gx - cx + 0.5, gy - cy + 0.5
            u = int((math.atan2(ny, nx) + math.pi) * RT)
            luz = 0.62 + 0.38 * max(0.0, (-0.45 * nx + 0.9 * ny) / max(1e-6, math.hypot(nx, ny)))
            base, oscura = HM + 4, u % 8 >= 4
        if z >= base: return _pardo(_parapeto(alto[(gx, gy)] - z, alto[(gx, gy)] > base + 2 and oscura, luz * 1.12))
        if puerta and (gx, gy) not in tramo and quien[(gx, gy)] == (C, C) and ny > 0:
            c = _arco(gx - C + 0.5, z, puerta)
            if c: return c
        # tostado (pedido del 9/11/2026): más claro arriba, más oscuro al pie
        return _pardo(_ladrillo(u, base - 1 - z, luz * (0.68 + 0.44 * z / base)))

    def arriba(gx, gy):
        base = HM if (gx, gy) in tramo else HM + 4
        if alto[(gx, gy)] > base: return _pardo((190, 190, 186) if alto[(gx, gy)] > base + 2 else (156, 156, 154))
        return _calzada(gx, gy)
    lz.voxeles(alto, cara, arriba)


AW, AH = 8, 13          # medio ancho del vano de la puerta y alto de sus jambas


def _arco(dx, z, puerta):
    """Puerta en el frente de la torre del muro sobre un camino (pedido del 9/11/2026): vano de medio punto con un
    anillo de dovelas claras; adentro un portón de tablas con dos herrajes (cerrada) o el hueco oscuro con las dos
    hojas abiertas contra las jambas (abierta). dx: distancia al eje de la torre; z: altura. None: ladrillo común."""
    ax = abs(dx)
    r = math.hypot(ax, max(0.0, z - AH))            # el arco: medio círculo de radio AW sobre las jambas
    if r > AW + 2.2: return None
    if r > AW:                                      # dovelas: claras, con juntas radiales
        ang = math.atan2(max(0.0, z - AH), dx)
        if z > AH and int(ang * 9) % 2 == 0 and r > AW + 1.2: return _pardo((92, 88, 84))
        return _pardo((170, 164, 156))
    if puerta == 'abierta':
        if ax > AW - 2: return (108, 70, 34) if int(z) % 5 else (60, 40, 22)    # hojas abiertas, de canto
        return (22, 17, 12)
    if abs(dx) < 0.6: return (40, 26, 14)           # junta de las dos hojas
    if int(z) in (3, 9): return (58, 54, 52)        # herrajes
    k = 1.0 if int(dx + 20) % 3 else 0.7            # tablas
    return _mul((126, 82, 40), k)


def muro(ruina, color, pal, d, empal, prohibido, puerta=None):
    lz = Lienzo(ruina, color)
    if puerta: _muro_piedra(lz, None, True, prohibido, puerta)
    else: _muro_en(lz, d, empal, prohibido=prohibido)
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
