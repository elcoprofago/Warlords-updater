# Tabla de ciudades de una guardada (ia\PENDIENTE-mapa-pruebas.md, paso 1).
# Registro 0x537e2c + i*0xde, cantidad [0x537e2a]: +0 x, +2 y (palabras), +4 nombre, +0xa4 tamaño (0 = arrasada),
# +0xa5 dueño (8 = neutral), +0xa7 ingreso, +0xaa cuatro tropas de 9 letras que la ciudad puede producir.
# Sin identificar todavía: +0xa6, +0xa8, +0xa9 y +0xce..+0xdd (cambian con la producción comprada).
# Uso: python ia\ciudades.py Tanda_hex_perfiles_SR
import os, sys

import tanda
from sin_ruinas import offset

CIUDADES_N, CIUDADES, TAM = 0x537e2a, 0x537e2c, 0xde


def leer(d):
    n = int.from_bytes(d[offset(CIUDADES_N):offset(CIUDADES_N) + 2], 'little')
    out = []
    for i in range(n):
        r = d[offset(CIUDADES + i * TAM):][:TAM]
        out.append({'i': i, 'x': int.from_bytes(r[0:2], 'little'), 'y': int.from_bytes(r[2:4], 'little'),
                    'nombre': r[4:0x24].split(b'\0')[0].decode('latin1'), 'tam': r[0xa4], 'dueño': r[0xa5],
                    'ingreso': r[0xa7], 'tropas': [r[0xaa + k * 9:0xaa + k * 9 + 9].split(b'\0')[0].decode('latin1')
                                                   for k in range(4)]})
    return out


def dar(d, i, color):
    """La guardada d (bytearray) con la ciudad i del color dado."""
    d[offset(CIUDADES + i * TAM) + 0xa5] = color
    return d


if __name__ == '__main__':
    with open(os.path.join(tanda.JUEGO, 'SAVES', sys.argv[1] + '.SAV'), 'rb') as f:
        cs = leer(f.read())
    for c in cs:
        dn = tanda.COLORES[c['dueño']] if c['dueño'] < 8 else 'neutral'
        print(f"{c['i']:3} ({c['x']:3},{c['y']:3}) {c['nombre']:20} {dn:9} tam {c['tam']} ingreso {c['ingreso']:3} "
              f"{', '.join(t for t in c['tropas'] if t)}")
