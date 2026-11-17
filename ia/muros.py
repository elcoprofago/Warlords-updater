# Arma una guardada de tanda con murallas (ia\PENDIENTE-ia-innovaciones.md, paso 5.5): un anillo de bloques de muro de
# piedra (OB_MURO = 7, sin daño) alrededor de la capital de la mitad de los colores activos; la otra mitad queda sin
# muro, como control dentro de la misma partida. La IA no construye muros, así que sin esto ninguna tanda los tiene.
# El bloque 'OBRA' (528 bytes: magia, cantidad, 64 registros de 8, 8 de pausas) va detrás de 'POZO' (el juego lo lee
# solo si POZO está antes): sirve una guardada que ya termine en POZO (Tanda_hex_*).
# Registro: x, y (palabras), +4 tipo, +5 libre, +6 dueño, +7 arqueros muertos (0 = entero).
# Anillo: las 12 casillas que rodean la ciudad de 2x2 (de x-1 a x+2, de y-1 a y+2). Se saltea el agua (los puentes
# son agua), ciudades, ruinas y sitios; los caminos sí llevan muro (bloque con puerta, como en el juego).
# Uso: python ia\muros.py Tanda_hex_control [colores, por defecto la mitad par de los activos]
#      escribe SAVES\<guardada>_MU.SAV (si termina en _control: <base>_MU_control.SAV) y no toca la original.
import os, struct, sys

import tanda
from intercambiar import capital
import ciudades
from sin_ruinas import offset

OB_MAX, OB_MURO = 64, 7
MAPA, GRILLA, TERRENOS = 0x503e00, 0x503e58, 0x535f0c


def casilla(d, x, y):
    w, h, sh = struct.unpack('<hhxxB', d[offset(MAPA):][:7])
    if not (0 <= x < w and 0 <= y < h):
        return None
    return d[offset(GRILLA + ((y * 10) << sh) + x * 10):][:10]


def sirve(d, x, y):
    t = casilla(d, x, y)
    if t is None:
        return False
    wd = int.from_bytes(t[:2], 'little')
    if wd & 0x4000:                                   # edificio
        return False
    if int.from_bytes(d[offset(TERRENOS + (wd & 0x1f) * 0x58):][:2], 'little') == 1:   # agua (y puentes)
        return False
    return t[3] & 7 in (0, 1)                         # nada o camino


def activos(d):
    return sorted({c['dueño'] for c in ciudades.leer(d) if c['dueño'] < 8 and c['tam']})


def anillo(cx, cy):
    return [(x, y) for y in range(cy - 1, cy + 3) for x in range(cx - 1, cx + 3)
            if not (cx <= x <= cx + 1 and cy <= y <= cy + 1)]


def amurallar(d, colores):
    d = bytearray(d)
    if d[-520:-516] != b'POZO' or b'OBRA' in d[-520:]:
        raise SystemExit('la guardada tiene que terminar en el bloque POZO y no tener OBRA')
    cs = ciudades.leer(d)
    recs, info = [], []
    for col in colores:
        c = cs[capital(d, col)]
        ok = [(x, y) for x, y in anillo(c['x'], c['y']) if sirve(d, x, y)]
        info.append((col, c['nombre'], c['x'], c['y'], len(ok)))
        recs += [struct.pack('<hhBBBB', x, y, OB_MURO, 0, col, 0) for x, y in ok]
    if len(recs) > OB_MAX:
        raise SystemExit(f'{len(recs)} bloques, el tope es {OB_MAX}')
    d += b'OBRA' + struct.pack('<I', len(recs)) + b''.join(recs).ljust(OB_MAX * 8, b'\0') + bytes(8)
    return bytes(d), info


if __name__ == '__main__':
    g = sys.argv[1]
    src = os.path.join(tanda.JUEGO, 'SAVES', g + '.SAV')
    d = open(src, 'rb').read()
    cols = [int(c) for c in sys.argv[2].split(',')] if len(sys.argv) > 2 else activos(d)[::2]
    out, info = amurallar(d, cols)
    nombre = g[:-len('_control')] + '_MU_control' if g.endswith('_control') else g + '_MU'
    dst = os.path.join(tanda.JUEGO, 'SAVES', nombre + '.SAV')
    open(dst, 'wb').write(out)
    # verificación: releer lo escrito
    r = open(dst, 'rb').read()
    assert r[:len(d)] == d and r[len(d):len(d) + 4] == b'OBRA' and len(r) == len(d) + 528
    n = struct.unpack('<I', r[len(d) + 4:len(d) + 8])[0]
    print(f'{nombre}.SAV: {n} bloques; activos {activos(d)}')
    for col, nom, x, y, k in info:
        print(f'  {tanda.COLORES[col]:9} capital {nom} ({x},{y}): {k} de 12 bloques')
