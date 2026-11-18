# Dibujo de la balsa (bono de movimiento "Raft", pedido del 18/11/2026): una balsa precaria de troncos atados, con un
# mástil y una vela remendada, y su estela de agua. Genera ARMY\balsa.PCX y ARMY\balsa.SHP en la carpeta del juego de
# pruebas, con el formato de warship.PCX (521x250, paleta de 256 colores de warship):
#   - retrato 128x160 en (0, 0);
#   - dos íconos de 48x48 en y = 161: el segundo con el color del jugador marcado en verde (índice 187);
#   - grilla de movimiento: columna i = 129 + 49*i (dirección: S, NE, E, SE, N, SO, O, NO, como warship), fila
#     j = 1 + 49*j (cuadros 0 a 3 de la animación; la fila 4 es la máscara de color del jugador, en verde).
# El .ARM lo hace el usuario con el nombre "balsa" (el bono "Raft", movimiento y fuerza bajos).
# Uso: python balsa_img.py [carpeta ARMY de destino]   (por defecto <juego de pruebas>\ARMY)
import os as _os, sys as _sys; _sys.path.append(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..'))  # para encontrar juego_pruebas.py
from juego_pruebas import W3  # carpeta del juego de pruebas: se cambia solo ahi
import sys, os, math, random
from PIL import Image, ImageDraw

DEST = sys.argv[1] if len(sys.argv) > 1 else os.path.join(W3, 'ARMY')
plantilla = Image.open(os.path.join(W3, 'ARMY', 'warship.PCX'))
PAL = plantilla.getpalette()[:768]
NEGRO, FONDO, VERDE = 10, 11, 187
S = 4                                            # sobremuestreo

# colores permitidos: toda la paleta menos los especiales y lo que se parezca al fondo o al verde del jugador
def _d(a, b): return sum((x - y) ** 2 for x, y in zip(a, b))
USABLES = [i for i in range(256) if i not in (NEGRO, FONDO, VERDE)
           and _d(PAL[3*i:3*i+3], (255, 0, 255)) > 9000 and _d(PAL[3*i:3*i+3], (15, 255, 0)) > 9000]
_cache = {}
def idx(rgb):
    rgb = tuple(int(c) for c in rgb[:3])
    if rgb not in _cache:
        _cache[rgb] = min(USABLES, key=lambda i: _d(PAL[3*i:3*i+3], rgb))
    return _cache[rgb]

def mezcla(a, b, t): return tuple(a[k] + (b[k] - a[k]) * t for k in range(3))
MADERA = (128, 84, 44); MADERA_OSC = (66, 40, 20); MADERA_CLARA = (178, 128, 72)
SOGA = (204, 176, 112); SOGA_OSC = (120, 96, 56)
VELA = (239, 231, 171); VELA_OSC = (171, 171, 171)   # lino crudo (colores que existen en la paleta)
AGUA_OSC = (24, 44, 84); ESPUMA = (244, 250, 255); ESPUMA2 = (150, 205, 235)

# dirección de cada columna (x, y de pantalla; y hacia abajo)
R2 = math.sqrt(0.5)
DIRS = [(0, 1), (R2, -R2), (1, 0), (R2, R2), (0, -1), (-R2, R2), (-1, 0), (-R2, -R2)]

# troncos: (v del centro, corrimiento de la punta delantera, de la trasera, grosor) — desparejos, como balsa precaria
TRONCOS = [(-8.2, -1.5, 0.5, 1.9), (-4.1, 1.0, -1.0, 2.1), (0.0, 0.0, 1.5, 2.2), (4.2, 1.8, -0.5, 2.0), (8.3, -0.5, 1.0, 1.8)]
LARGO = 12.0


def balsa(cel, d, verde=False, centro=(24, 24), escala=1.0):
    """Dibuja la balsa en cel (RGBA, ya sobremuestreada) con rumbo d. Devuelve el conjunto de píxeles de vela."""
    dr = ImageDraw.Draw(cel)
    cx, cy = centro
    dx, dy = d; nx, ny = -dy, dx
    P = lambda u, v: ((cx + (u * dx + v * nx) * escala) * S, (cy + (u * dy + v * ny) * escala) * S)
    # sombra de agua oscura alrededor (línea de flotación)
    for v0, a, b, r in TRONCOS:
        dr.polygon([P(-LARGO + b - 1.2, v0 - r - 1.0), P(LARGO + a + 1.2, v0 - r - 1.0),
                    P(LARGO + a + 1.2, v0 + r + 1.0), P(-LARGO + b - 1.2, v0 + r + 1.0)], fill=AGUA_OSC + (255,))
    # troncos: cilindros sombreados por franjas a lo ancho, con vetas y puntas redondeadas
    rnd = random.Random(3)
    for k, (v0, a, b, r) in enumerate(TRONCOS):
        u0, u1 = -LARGO + b, LARGO + a
        n = 12
        for i in range(n):
            t0 = -1 + 2 * i / n; t1 = -1 + 2 * (i + 1) / n
            tm = (t0 + t1) / 2
            luz = math.cos(tm * math.pi / 2) * (1 - 0.35 * tm)          # luz del noroeste
            c = mezcla(MADERA_OSC, MADERA_CLARA, max(0, min(1, luz)))
            dr.polygon([P(u0, v0 + t0 * r), P(u1, v0 + t0 * r), P(u1, v0 + t1 * r), P(u0, v0 + t1 * r)],
                       fill=tuple(int(x) for x in c) + (255,))
        for _ in range(3):                                              # vetas
            vv = v0 + rnd.uniform(-0.6, 0.6) * r; ua = rnd.uniform(u0, u1 - 4)
            dr.line([P(ua, vv), P(ua + rnd.uniform(3, 7), vv)], fill=MADERA_OSC + (255,), width=max(1, S // 2))
        for uu in (u0, u1):                                             # cortes de los extremos (más claros)
            x, y = P(uu, v0); rr = r * escala * S * 0.85
            dr.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(196, 150, 96, 255), outline=MADERA_OSC + (255,))
    # ataduras de soga a lo ancho
    for ub in (-6.0, 5.5):
        dr.line([P(ub, -10.4), P(ub, 10.4)], fill=SOGA_OSC + (255,), width=int(2.0 * S * escala))
        dr.line([P(ub - 0.3, -10.2), P(ub - 0.3, 10.2)], fill=SOGA + (255,), width=int(1.0 * S * escala))
    # mástil (palo vertical en pantalla) con vela cuadrada remendada
    bx, by = P(-1.0, 0.0)
    alto = 15 * escala * S
    dr.line([(bx, by), (bx, by - alto)], fill=MADERA_OSC + (255,), width=int(1.4 * S * escala))
    w = 9.0 * escala * S; h = 9.0 * escala * S; top = by - alto + 1.0 * S * escala
    lado = 1 if dx >= 0 else -1                                         # la vela se hincha hacia adelante
    vela = [(bx - w * 0.5, top), (bx + w * 0.5, top), (bx + w * 0.5 + lado * 1.2 * S * escala, top + h),
            (bx - w * 0.5 + lado * 1.2 * S * escala, top + h)]
    dr.line([(bx - w * 0.6, top), (bx + w * 0.6, top)], fill=MADERA_OSC + (255,), width=int(1.2 * S * escala))
    if verde:
        dr.polygon(vela, fill=(15, 255, 0, 255))
    else:
        dr.polygon(vela, fill=VELA + (255,), outline=VELA_OSC + (255,))
        # remiendo y costura: tela precaria
        px0 = bx - w * 0.15; py0 = top + h * 0.45
        dr.rectangle([px0, py0, px0 + w * 0.3, py0 + h * 0.3], fill=(227, 219, 147, 255))
        dr.line([(bx, top), (bx + lado * 0.6 * S * escala, top + h)], fill=VELA_OSC + (255,), width=max(1, S // 2))


def estela(img, ox, oy, d, f):
    """Espuma de 1 píxel detrás de la balsa (en V que se abre) y una ola chica en la proa; f = cuadro 0..3."""
    dx, dy = d; nx, ny = -dy, dx
    rnd = random.Random(100 + f)
    px = img.load()
    def pon(u, v, c):
        x = round(24 + u * dx + v * nx); y = round(24 + u * dy + v * ny)
        if 1 <= x <= 46 and 1 <= y <= 46 and px[ox + x, oy + y] == FONDO:
            px[ox + x, oy + y] = idx(c)
    for s in range(0, 13):
        u = -LARGO - 1.5 - s
        abre = 9.5 + s * 0.55
        for lado in (-1, 1):
            if (s + f * 3 + (lado > 0) * 2) % 4 < 3:                    # la espuma corre hacia atrás cuadro a cuadro
                pon(u, lado * (abre + rnd.uniform(-0.6, 0.6)), ESPUMA if s < 6 else ESPUMA2)
            if (s + f * 3 + (lado > 0)) % 4 < 2:                        # segunda línea de espuma, más adentro
                pon(u, lado * (abre - 2.0), ESPUMA2)
            if s < 8 and rnd.random() < 0.55:
                pon(u + rnd.uniform(-0.5, 0.5), lado * (abre - 1.5 - rnd.uniform(0, 1.5)), ESPUMA2)
        if s < 7 and (s + f) % 2 == 0:                                  # remolino al medio de la estela
            pon(u, rnd.uniform(-4, 4), ESPUMA2 if s > 2 else ESPUMA)
    for v in range(-9, 10, 2):                                          # ola de proa, sube y baja
        if (v // 2 + f) % 2 == 0:
            pon(LARGO + 2.5 + 0.08 * abs(v) + (f % 2) * 0.6, v, ESPUMA)
    for lado in (-1, 1):                                                # salpicaduras en los costados
        for _ in range(2):
            pon(rnd.uniform(-LARGO, LARGO), lado * rnd.uniform(11, 12.5), ESPUMA2)


def pegar(img, ox, oy, cel):
    """Baja el sobremuestreo y pega en img (paleta) los píxeles opacos de cel; devuelve los que pintó en verde."""
    chico = cel.resize((cel.width // S, cel.height // S), Image.BOX)
    px = img.load()
    for y in range(chico.height):
        for x in range(chico.width):
            r, g, b, a = chico.getpixel((x, y))
            if a < 128: continue
            r, g, b = r * 255 / a, g * 255 / a, b * 255 / a          # quitar la mezcla con el transparente
            if g > 200 and r < 90 and b < 90: px[ox + x, oy + y] = VERDE
            else: px[ox + x, oy + y] = idx((r, g, b))


def celda(img, ox, oy, d, f, verde=False):
    for y in range(48):
        for x in range(48):
            img.putpixel((ox + x, oy + y), FONDO)
    cel = Image.new('RGBA', (48 * S, 48 * S), (0, 0, 0, 0))
    balsa(cel, d, verde)
    # ondulación: la balsa sube y baja medio píxel según el cuadro
    sube = (0, 1, 0, -1)[f] * S // 2
    cel = cel.transform(cel.size, Image.AFFINE, (1, 0, 0, 0, 1, -sube))
    pegar(img, ox, oy, cel)
    if verde:                       # contorno verde de selección alrededor de la balsa, como el casco de warship
        px = img.load()
        borde = [(x, y) for y in range(1, 47) for x in range(1, 47) if px[ox + x, oy + y] == FONDO
                 and any(px[ox + x + a, oy + y + b] not in (FONDO, VERDE) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        for x, y in borde: px[ox + x, oy + y] = VERDE
    estela(img, ox, oy, d, f)


def retrato(img):
    W, H = 128, 160
    cel = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 255))
    dr = ImageDraw.Draw(cel)
    HOR = 66
    for y in range(HOR * S):                                            # cielo de tormenta al atardecer
        t = y / (HOR * S)
        c = mezcla((70, 64, 86), (222, 150, 86), t ** 1.6)
        dr.line([(0, y), (W * S, y)], fill=tuple(int(x) for x in c) + (255,))
    rnd = random.Random(11)
    for _ in range(26):                                                 # nubes
        x = rnd.uniform(-20, W) * S; y = rnd.uniform(4, HOR - 18) * S; w = rnd.uniform(20, 55) * S; h = rnd.uniform(3, 8) * S
        c = mezcla((60, 54, 74), (170, 120, 100), y / (HOR * S))
        dr.ellipse([x, y, x + w, y + h], fill=tuple(int(v) for v in c) + (255,))
    dr.ellipse([88 * S, (HOR - 14) * S, 112 * S, (HOR + 10) * S], fill=(250, 214, 120, 255))     # sol bajo
    for y in range(HOR * S, H * S):                                     # mar
        t = (y - HOR * S) / ((H - HOR) * S)
        c = mezcla((64, 84, 104), (18, 34, 52), t ** 0.7)
        dr.line([(0, y), (W * S, y)], fill=tuple(int(x) for x in c) + (255,))
    for y in range(HOR, H, 3):                                          # olas: trazos claros que crecen hacia abajo
        k = (y - HOR) / (H - HOR)
        for _ in range(int(6 + 10 * k)):
            x = rnd.uniform(-10, W); w = (3 + 14 * k) * rnd.uniform(0.6, 1.3)
            c = (232, 190, 130) if x > 70 and k < 0.35 else (120, 150, 170)
            dr.line([(x * S, y * S), ((x + w) * S, (y + rnd.uniform(-0.5, 0.5)) * S)], fill=c + (255,), width=S)
    tierra = [(0, HOR), (14, HOR - 7), (30, HOR - 9), (44, HOR - 4), (52, HOR)]                    # costa lejana
    dr.polygon([(x * S, y * S) for x, y in tierra], fill=(52, 50, 60, 255))
    # balsa en perspectiva: cubierta de troncos vista de tres cuartos, puntas de los troncos hacia el frente
    cx, cy = 60, 120
    for k in range(6):
        x0 = cx - 40 + k * 13.5
        top_y = cy - 16 + k * 1.0
        dr.polygon([((x0 + 14) * S, top_y * S), ((x0 + 26) * S, top_y * S), ((x0 + 16) * S, (top_y + 24) * S),
                    ((x0 + 2) * S, (top_y + 24) * S)], fill=(110, 70, 36, 255))
        dr.line([((x0 + 18) * S, (top_y + 1) * S), ((x0 + 7) * S, (top_y + 23) * S)], fill=(160, 110, 60, 255), width=2 * S)
        dr.line([((x0 + 2) * S, (top_y + 24) * S), ((x0 + 14) * S, top_y * S)], fill=(60, 36, 18, 255), width=S)
        ex, ey = x0 + 9, top_y + 25                                     # punta cortada del tronco
        dr.ellipse([(ex - 7) * S, (ey - 5) * S, (ex + 7) * S, (ey + 5) * S], fill=(186, 140, 88, 255), outline=(70, 44, 22, 255), width=S)
        dr.ellipse([(ex - 3) * S, (ey - 2) * S, (ex + 3) * S, (ey + 2) * S], outline=(130, 92, 52, 255), width=S)
    for ty in (cy - 9, cy + 1):                                         # sogas
        dr.line([((cx - 38) * S, (ty + 2) * S), ((cx + 46) * S, (ty + 5) * S)], fill=SOGA_OSC + (255,), width=3 * S)
        dr.line([((cx - 38) * S, (ty + 1) * S), ((cx + 46) * S, (ty + 4) * S)], fill=SOGA + (255,), width=S)
    for x in range(cx - 52, cx + 60, 3):                                # espuma contra la balsa
        y = cy + 14 + rnd.uniform(-2, 3)
        dr.ellipse([x * S, y * S, (x + rnd.uniform(2, 5)) * S, (y + 2) * S], fill=(220, 236, 244, 255))
    mx = cx + 4                                                         # mástil y vela
    dr.line([(mx * S, (cy - 12) * S), (mx * S, (cy - 92) * S)], fill=(58, 36, 18, 255), width=3 * S)
    dr.line([((mx - 26) * S, (cy - 88) * S), ((mx + 22) * S, (cy - 90) * S)], fill=(58, 36, 18, 255), width=2 * S)
    vela = [((mx - 25) * S, (cy - 87) * S), ((mx + 21) * S, (cy - 89) * S), ((mx + 27) * S, (cy - 36) * S), ((mx - 18) * S, (cy - 32) * S)]
    dr.polygon(vela, fill=(206, 192, 156, 255), outline=(120, 104, 76, 255))
    dr.rectangle([(mx - 10) * S, (cy - 66) * S, (mx + 2) * S, (cy - 52) * S], fill=(227, 219, 147, 255), outline=(120, 104, 76, 255))
    dr.line([((mx + 8) * S, (cy - 88) * S), ((mx + 12) * S, (cy - 35) * S)], fill=(150, 134, 100, 255), width=S)
    dr.polygon([((mx - 22) * S, (cy - 34) * S), ((mx - 30) * S, (cy - 28) * S), ((mx - 15) * S, (cy - 32) * S)], fill=(206, 192, 156, 255))  # jirón
    # balsero con pértiga, en silueta
    fx, fy = cx - 22, cy - 14
    dr.ellipse([(fx - 3) * S, (fy - 30) * S, (fx + 3) * S, (fy - 24) * S], fill=(40, 30, 30, 255))
    dr.polygon([((fx - 4) * S, (fy - 24) * S), ((fx + 4) * S, (fy - 24) * S), ((fx + 5) * S, (fy - 8) * S), ((fx - 5) * S, (fy - 8) * S)], fill=(48, 36, 34, 255))
    dr.line([((fx - 3) * S, (fy - 8) * S), ((fx - 5) * S, fy * S)], fill=(40, 30, 30, 255), width=2 * S)
    dr.line([((fx + 3) * S, (fy - 8) * S), ((fx + 4) * S, fy * S)], fill=(40, 30, 30, 255), width=2 * S)
    dr.line([((fx + 14) * S, (fy - 40) * S), ((fx - 16) * S, (fy + 34) * S)], fill=(80, 54, 30, 255), width=2 * S)
    dr.line([((fx + 3) * S, (fy - 20) * S), ((fx + 8) * S, (fy - 27) * S)], fill=(40, 30, 30, 255), width=2 * S)
    chico = cel.resize((W, H), Image.BOX).convert('RGB')
    px = img.load()
    for y in range(H):
        for x in range(W):
            px[x, y] = idx(chico.getpixel((x, y)))


img = plantilla.copy()                                                  # grilla negra y fondo iguales a warship
retrato(img)
O = DIRS[6]                                                             # íconos: rumbo al oeste, como warship
for ox, verde in ((1, False), (50, True)):
    celda(img, ox, 161, O, 0, verde)
for i, d in enumerate(DIRS):
    for j in range(4):
        celda(img, 129 + 49 * i, 1 + 49 * j, d, j)
    celda(img, 129 + 49 * i, 1 + 49 * 4, d, 0, verde=True)
img.putpalette(PAL)
os.makedirs(DEST, exist_ok=True)
img.save(os.path.join(DEST, 'balsa.PCX'))
with open(os.path.join(DEST, 'balsa.SHP'), 'wb') as f:                  # marca de barco, igual que warship.SHP
    f.write(open(os.path.join(W3, 'ARMY', 'warship.SHP'), 'rb').read())
print('escrito', os.path.join(DEST, 'balsa.PCX'), 'y balsa.SHP')
