# Events Report de una guardada, con el texto que arma el juego (PENDIENTE-visor-historia.md, puntos 1 y 2).
# HISTORY.DAT va en 0x60427 del .SAV (largo en 0x60423); detrás, la tabla de la ronda en curso (16 x 0x1c), un dword
# y, si la partida tiene comarcas ([0x560774], 0x43a850), AREA.DAT con su largo delante (registros de 0x22).
# El texto de cada renglón sale de 0x4b4110: cadena del grupo 0xb2 + tipo de Sagetext.tex (variante 0 o 1).
# Uso: python ia\historia.py ABN_000_29
import os, struct, sys

import tanda
from sin_ruinas import offset
from ciudades import leer as leer_ciudades

HIST = 0x60427
JUGADORES, TAM_JUG = 0x536b34, 0x1f8       # +0 nombre
ITEMS, TAM_ITEM = 0x55cb74, 0xd8           # +0 nombre
ORO_ANTES, ORO_DESPUES = 0x56075f, 0x560765  # lo que rodea una cantidad de oro (MISC.DAT), 0x43ff50
MAPA_DIM, MAPA = 0x503e00, 0x503e58        # ancho, alto, desplazamiento de fila en +6; casillas de 10 bytes
VICTORIA, LIMITE = 0x560e52, 0x560e50      # word 0..6 (textos 0x1bf); límite de la partida (0 = sin límite)
RONDA, TOPE = 0x603d9, 0x603e5             # objeto 0x5032f8 (0x420850): +0x30 ronda, +0x54 tope de turnos (-1 = no)


TERRENOS = 0x535ed0                        # word cantidad; desde +6 registros de 0x58: +0 nombre, +0x10 textura
ESCUDO = 0xa0                              # en el registro del jugador: hojas B (fondo), O y C (figuras), 9 letras c/u


def textos(grupo, juego=tanda.JUEGO):
    """Cadenas de un grupo de Sagetext.tex: dword largo, tabla de grupos y por grupo word cantidad + dwords."""
    with open(os.path.join(juego, 'Sagetext.tex'), 'rb') as f:
        d = f.read()[4:]
    o = struct.unpack_from('<I', d, grupo * 4)[0]
    n = struct.unpack_from('<h', d, o)[0]
    return [d[p:d.index(b'\0', p)].decode('latin1')
            for p in struct.unpack_from(f'<{n}I', d, o + 4)]


def _w(b, o):
    return struct.unpack_from('<h', b, o)[0]


def _cad(b):
    return b.split(b'\0')[0].decode('latin1')


def areas(d):
    """Nombres de las comarcas guardadas en la partida, o None si no tiene (mapas aleatorios)."""
    o = HIST + struct.unpack_from('<I', d, HIST - 4)[0] + 16 * 0x1c + 4
    n = struct.unpack_from('<I', d, o)[0]
    if not n or n % 0x22 or n > 0x2000:
        return None
    return [_cad(d[o + 4 + i * 0x22:o + 4 + i * 0x22 + 0x20]) for i in range(n // 0x22)]


def renglones(d):
    """(ronda, jugador, renglón de 0x1c) de cada bloque de HISTORY.DAT, en el orden del archivo."""
    o, fin = HIST, HIST + struct.unpack_from('<I', d, HIST - 4)[0]
    while o < fin:
        tam, ronda, n = _w(d, o), _w(d, o + 2), _w(d, o + 0x44)
        for k in range(n):
            r = d[o + tam - (n - k) * 0x1c:][:0x1c]
            yield ronda, _w(r, 2), r
        o += tam


def terrenos(d):
    """(nombre, textura) de cada valor de terreno de la casilla: la tabla es de cada mapa (Plains, Water...).
    La textura es TERRAIN/DATA/<textura>.PCX."""
    o = offset(TERRENOS)
    return [(_cad(d[o + 6 + i * 0x58:][:0x10]), _cad(d[o + 6 + i * 0x58 + 0x10:][:9]))
            for i in range(struct.unpack_from('<h', d, o)[0])]


def duenos(d):
    """{ronda: dueño de cada ciudad (8 = neutral)} de cada bloque de HISTORY.DAT."""
    o, fin, out = HIST, HIST + struct.unpack_from('<I', d, HIST - 4)[0], {}
    while o < fin:
        out[_w(d, o + 2)] = d[o + 0x48:o + _w(d, o) - _w(d, o + 0x44) * 0x1c]
        o += _w(d, o)
    return out


def en_curso(d):
    """(jugador, renglón) de la tabla de la ronda en curso (16 casillas detrás de HISTORY.DAT; tipo 0 = vacía)."""
    o = HIST + struct.unpack_from('<I', d, HIST - 4)[0]
    for k in range(16):
        r = d[o + k * 0x1c:][:0x1c]
        if _w(r, 0):
            yield _w(r, 2), r


def cabecera(d, juego=tanda.JUEGO):
    """Datos del panel superior. Los primeros 0x6d bytes son 0x503da0 (0x58: nombre, archivo, +0x4c número al azar
    1..10000 que identifica la partida), el set (9) y el mapa (0xc: «Random» o el archivo del escenario), 0x439a00.
    El .SAV no guarda fechas: la única es la del archivo (último guardado)."""
    lim, tope = struct.unpack_from('<h', d, offset(LIMITE))[0], struct.unpack_from('<h', d, TOPE)[0]
    return {'nombre': _cad(d[:0x20]), 'archivo': _cad(d[0x20:0x40]), 'set': _cad(d[0x58:0x61]),
            'mapa': _cad(d[0x61:0x6d]), 'ronda': struct.unpack_from('<h', d, RONDA)[0],
            'victoria': textos(0x1bf, juego)[struct.unpack_from('<h', d, offset(VICTORIA))[0]],
            # 0x420760: con límite en turnos el juego lo copia al tope; si no, el límite es en minutos (sin comprobar)
            'limite': None if lim <= 0 else f'{lim} turnos' if tope == lim else f'{lim} min'}


def mapa(d):
    """Filas de casillas (terreno, explorados): terreno = byte +0 & 0x1f (0 agua, 1 llano...), explorados = byte +4,
    un bit por jugador. Es lo explorado al guardar, no por ronda: el .SAV no guarda la historia de la exploración."""
    w, h = struct.unpack_from('<hh', d, offset(MAPA_DIM))
    sh, b = d[offset(MAPA_DIM) + 6], offset(MAPA)
    return [[(d[b + ((y * 10) << sh) + x * 10] & 0x1f, d[b + ((y * 10) << sh) + x * 10 + 4]) for x in range(w)]
            for y in range(h)]


class Partida:
    def __init__(self, d, juego=tanda.JUEGO):
        self.d = d
        self.T = [textos(0xb2 + t, juego) for t in range(0x13)]
        self.sin_area = textos(0xa, juego)[0]   # 0x4410a0 sin AREA.DAT
        self.areas = areas(d)
        self.ciudades = leer_ciudades(d)
        # Cada bloque trae un byte por ciudad: si no coincide con el mapa, el historial es de otra partida (pasa en
        # las guardadas de tandas armadas a partir de otra) y los nombres de ciudad no se pueden confiar.
        # También es ajeno si los bloques no son las rondas 1..(ronda en curso - 1): la ronda en curso va aparte.
        o, fin, cant, rondas = HIST, HIST + struct.unpack_from('<I', d, HIST - 4)[0], set(), []
        while o < fin:
            cant.add(_w(d, o) - 0x48 - _w(d, o + 0x44) * 0x1c)
            rondas.append(_w(d, o + 2))
            o += _w(d, o)
        self.cabecera = cabecera(d, juego)
        self.ajena = cant != {len(self.ciudades)} or rondas != list(range(1, self.cabecera['ronda']))

    def _va(self, va, n=0x20):
        return _cad(self.d[offset(va):offset(va) + n])

    def jugador(self, p):
        return self._va(JUGADORES + p * TAM_JUG)

    def escudo(self, p):
        """Hojas de SHIELD que forman el escudo del jugador, de abajo arriba (fondo B, figuras O y C)."""
        o = offset(JUGADORES + p * TAM_JUG) + ESCUDO
        return [n for n in (_cad(self.d[o + k * 9:o + k * 9 + 9]) for k in range(3)) if n]

    def juega(self, p):
        return self.d[offset(JUGADORES - 4 + p * TAM_JUG) + 1] != 0

    def texto(self, r):
        t, p, par = _w(r, 0), _w(r, 2), _w(r, 4)
        nom, s = _cad(r[6:0x16]), self.T[t]
        ciudad = lambda i: self.ciudades[i]['nombre'] if 0 <= i < len(self.ciudades) else f'(ciudad {i})'
        if t == 0:
            return s[0]
        if t == 1:
            a = self.areas[par] if self.areas and 0 <= par < len(self.areas) else self.sin_area
            return s[1] % (nom, a) if nom else s[0] % a
        if t == 2:
            return s[1] % (nom, ciudad(par)) if nom else s[0] % ciudad(par)
        if t == 3:
            return s[0] % (nom, ciudad(par))
        if t in (4, 7, 0x10):
            return s[0] % nom
        if t in (5, 8):
            return s[0 if par == 1 else 1] % (nom, par)
        if t == 6:
            return s[0] % (nom, self._va(ORO_ANTES, 6) + str(par) + self._va(ORO_DESPUES, 10))
        if t == 9:
            return s[0] % (nom, self._va(ITEMS + par * TAM_ITEM))
        if t == 0xa:
            return s[0] % (nom, par + 1)
        if t in (0xb, 0xc, 0xd):
            return s[0] % self.jugador(par)
        if t == 0xe:                            # ciudad en (x, y) o una casilla antes, 0x440be0
            x, y = _w(r, 0x16), _w(r, 0x18)
            c = next((c for c in self.ciudades if c['x'] - x in (0, -1) and c['y'] - y in (0, -1)), None)
            return s[1] % (nom, c['nombre']) if c else s[0] % nom
        if t == 0xf:
            return s[0 if par == 0 else 1] % nom
        if t == 0x11:
            return s[0] % self.jugador(p)
        if t == 0x12:
            return s[0] % (nom, self.jugador(p))
        return f'(tipo {t})'                    # 0x13: votación de vista-aliada, sin texto en Sagetext.tex


if __name__ == '__main__':
    with open(os.path.join(tanda.JUEGO, 'SAVES', sys.argv[1] + '.SAV'), 'rb') as f:
        pa = Partida(f.read())
    if pa.ajena:
        print('Aviso: el historial guardado es de otro mapa (no coincide la cantidad de ciudades).')
    for ronda, p, r in renglones(pa.d):
        print(f'{ronda:3} {tanda.COLORES[p] if p < 8 else "neutral":8} {_w(r, 0):2} {pa.texto(r)}')
