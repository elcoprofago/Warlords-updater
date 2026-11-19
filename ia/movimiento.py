# Costo de movimiento por tierra y turnos de viaje, como los calcula el juego (punto 3.b de ia\PENDIENTE-ia-muros.md:
# en cuántos turnos llega un enemigo a un paso y a nuestras ciudades). Sin tocar el juego: lee una guardada.
# Verificado contra el código del juego con ia\prueba_movimiento.py (lo corre en el emulador de simcombate\motor.py).
#
# Costo de cada casilla (0x4a4f90, la grilla 0x57d158, índice x*0xa0 + y):
#   - el del terreno: palabra +0x34 del registro de terreno (tabla 0x535ed6, 0x58 bytes; +0x36 es la clase). Llanura 2,
#     colinas 4-5, pantano 5, roca 3-4, desierto 3, lava 9; 0 en montaña y bosque profundo (no se entra).
#   - +1 si la casilla tiene la capa de bosque (byte +3, bit 0x40). Además, en esa casilla la clase pasa a 2 (colinas)
#     si el mapa tiene el byte 0x536964, o a 3 si tiene el 0x536965 (Kor y Scarpart: el bosque cuenta como «woods»).
#   - camino (byte +3 & 7 == 1) o ciudad (== 3, salvo byte +8 bit 0x80): 1, sea cual sea el terreno.
# Al moverse (0x4a6490, modo 1 = por tierra): costo = grilla & 0xf; si el grupo tiene bono de terreno y el costo pasa
# de 2, baja a 2 en las casillas de su clase: bit 1 del bono con clase 3 (0x40 en la grilla), bit 2 con clase 2 (0x80).
# El paso solo se da si queda movimiento para pagarlo; lo que sobra no pasa al turno siguiente (0x4a6290).
#
# Movimiento de cada unidad: +0x9b de su registro en la guardada (la copia del .ARM: +0x9a fuerza, +0x9c vidas).
# +0xe0 es el tipo de movimiento (0x4ae10d, los nombres están en el mapa, 0x5368e9 + 0x20*(tipo-1)): 0 ninguno,
# 1 «Hills Move Bonus», 2 el segundo terreno del mapa («Marsh» en Hexagon y Borderlands, «Woods» en Kor y Scarpart),
# 3 los dos, 4 vuela (lo arma el cargador, 0x42f3a1, comparando los nombres de bono con «hills» y el del mapa). El bono
# del grupo (+0x1a de la estructura 0x56ea90 de cada jugador) lo arma 0x486ab0 (0x4870be y 0x4871e7): bit 1 si alguna
# unidad del grupo es de tipo 2 o 3, bit 2 si alguna es de tipo 1 o 3. Basta una unidad para que todo el grupo lo tenga.
# El movimiento de un ejército en el mapa (+0x10 de su registro en 0x54fe52) es el +0x9b de su unidad: coincidió en los
# 83 ejércitos comunes de las guardadas de prueba.
import heapq, struct

import historia
from muros import casilla, MAPA, TERRENOS
from sin_ruinas import offset

COSTO = TERRENOS - 2           # palabra +0x34 del registro de terreno (TERRENOS = +0x36, la clase)
BOSQUE_COLINA, BOSQUE_WOODS = 0x536964, 0x536965
COLINAS, SEGUNDO = 0x80, 0x40  # marcas de clase en la grilla del juego


def grilla(d):
    """{(x, y): byte de la grilla 0x57d158 del juego}: costo (bits 0-3) | 0x20 camino | 0x10 ciudad | 0x80 clase 2 |
    0x40 clase 3. Réplica de 0x4a4f90."""
    w, h, _ = struct.unpack('<hhxxB', d[offset(MAPA):][:7])
    f64, f65 = d[offset(BOSQUE_COLINA)], d[offset(BOSQUE_WOODS)]
    out = {}
    for y in range(h):
        for x in range(w):
            t = casilla(d, x, y)
            k = int.from_bytes(t[:2], 'little') & 0x1f
            c = int.from_bytes(d[offset(COSTO + k * 0x58):][:2], 'little')
            cl = int.from_bytes(d[offset(TERRENOS + k * 0x58):][:2], 'little')
            if t[3] & 0x40:                     # capa de bosque
                c += 1
                if f64 and cl in (0, 3):
                    cl = 2
                if f65 and cl in (0, 2):
                    cl = 3
            g = 0
            if t[3] & 7 == 1:                   # camino
                c, g = 1, 0x20
            if t[3] & 7 == 3 and not t[8] & 0x80:   # ciudad: también 1
                c, g = 1, g | 0x10
                if cl == 1:
                    cl = 0
            g |= c & 0xff
            if cl == 2:
                g |= COLINAS
            if cl == 3:
                g |= SEGUNDO
            out[x, y] = g & 0xff
    return out


def costo(g, bono=0):
    """Costo de entrar a una casilla por tierra (0x4a6490, modo 1). bono = bits del grupo: 1 clase 3, 2 clase 2."""
    c = g & 0xf
    if bono and c > 2 and (bono & 1 and g & SEGUNDO or bono & 2 and g & COLINAS):
        c = 2
    return c


def bono_de_tipo(tipo):
    """Bits del bono del grupo a partir de +0xe0 de la unidad (0x486ab0, ver arriba)."""
    return {1: 2, 2: 1, 3: 3}.get(tipo, 0)


def turnos(origen, mov, g, nodos, bono=0):
    """{casilla: (turno en que llega, movimiento que le queda)} saliendo de las casillas origen al empezar el turno 1,
    con mov puntos por turno, sin salir de nodos. Llega en el turno 1 = la alcanza en su primer movimiento."""
    best = {}
    pq = [(1, -mov, p) for p in origen if p in nodos]
    from pasos import VEC
    while pq:
        t, r, p = heapq.heappop(pq)
        if p in best:
            continue
        best[p] = (t, -r)
        for dx, dy in VEC:
            n = (p[0] + dx, p[1] + dy)
            if n not in nodos or n in best:
                continue
            c = costo(g[n], bono)
            if c <= 0 or c > mov:
                continue
            if c <= -r:
                heapq.heappush(pq, (t, r + c, n))
            else:
                heapq.heappush(pq, (t + 1, -mov + c, n))
    return best


def perfiles(d, color, ranuras=range(15)):
    """Unidades que puede producir el bando (ranuras 0-14; la 15 es el barco), sin voladores: la más rápida por cada
    bono de terreno. [(movimiento, bono, nombre)]."""
    import tanda
    mejor = {}
    for s in ranuras:
        u = tanda.SAV_BANDOS + (color * 16 + s) * tanda.UNIDAD
        r = d[u:u + tanda.UNIDAD]
        if not r[:1].isalpha() or r[0xe0] == 4 or not r[0x9b]:
            continue
        b = bono_de_tipo(r[0xe0])
        if r[0x9b] > mejor.get(b, (0,))[0]:
            mejor[b] = (r[0x9b], b, r[:16].split(b'\0')[0].decode('latin-1'))
    # un perfil con bono que no es más rápido que uno sin bono en ninguna casilla sigue sirviendo (baja colinas o
    # pantanos a 2): se dejan todos
    return sorted(mejor.values(), reverse=True)
