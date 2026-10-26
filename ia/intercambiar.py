# Intercambia los lugares de salida de dos colores en una guardada (ia\PENDIENTE-mapa-pruebas.md, paso 5'):
# las ciudades de cada uno pasan al otro, la capital del registro de jugador (+0xf2 y +0xf4) también, y los ejércitos
# de cada color se trasladan a la casilla equivalente de la otra capital. El orden de turno sigue siendo por color.
# Uso: python ia\intercambiar.py Tanda_hex_control 1 4 Tanda_hex_lugar_control
import os, sys

import ciudades, tanda
from sin_ruinas import offset

JUGADORES, JUG_TAM = 0x536b30, 0x1f8
EJERCITOS_N, EJERCITOS, EJ_TAM = 0x54fe50, 0x54fe52, 0x1c


def capital(d, color):
    return d[offset(JUGADORES + color * JUG_TAM) + 0xf2]


def intercambiar(d, a, b):
    cs = ciudades.leer(d)
    ca, cb = cs[capital(d, a)], cs[capital(d, b)]
    for c in cs:
        if c['dueño'] in (a, b):
            ciudades.dar(d, c['i'], b if c['dueño'] == a else a)
    for o in (0xf2, 0xf4):
        pa, pb = offset(JUGADORES + a * JUG_TAM) + o, offset(JUGADORES + b * JUG_TAM) + o
        d[pa], d[pb] = d[pb], d[pa]
    n = int.from_bytes(d[offset(EJERCITOS_N):][:2], 'little')
    for i in range(n):
        p = offset(EJERCITOS + i * EJ_TAM)
        if d[p + 9] != 0xff:
            continue
        dueño = int.from_bytes(d[p + 0xc:p + 0xe], 'little') >> 5 & 0xf
        if dueño not in (a, b):
            continue
        de, a_ = (ca, cb) if dueño == a else (cb, ca)
        for k, eje in ((0, 'x'), (2, 'y')):
            v = int.from_bytes(d[p + k:p + k + 2], 'little') - de[eje] + a_[eje]
            d[p + k:p + k + 2] = v.to_bytes(2, 'little')
    return d


if __name__ == '__main__':
    g, a, b, destino = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    with open(os.path.join(tanda.JUEGO, 'SAVES', g + '.SAV'), 'rb') as f:
        d = bytearray(f.read())
    with open(os.path.join(tanda.JUEGO, 'SAVES', destino + '.SAV'), 'wb') as f:
        f.write(intercambiar(d, a, b))
