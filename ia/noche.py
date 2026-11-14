# Arma una guardada para medir el efecto noche (paso 5.4 de PENDIENTE-ia-innovaciones): enciende Day/Night (bit 2
# del byte 25 de las opciones, 0x53c38c + 25) y da la clase "Undead" (segunda clase, +0xa9; la primera no se toca) a
# las ranuras 1, 3, 5, 7 y 9 de los 8 bandos. Con la 11 (Demon en las guardadas Borderlands/Kor/Scarpart) quedan
# media lista de unidades de noche y media de día: la guardada se controla sola, comparando qué unidades atacan y con
# qué resultado en vueltas pares (noche) e impares (día). Escribe SAVES\<guardada>_NO<sufijo>.SAV y no toca la original.
# Uso: python ia\noche.py Tanda_Borderlands [_control]
import os, sys

import tanda

RANURAS = (1, 3, 5, 7, 9)
CLASE = b'Undead'
NOCHE = (b'monster', b'demon', b'undead')


def sav_off(va):
    off = 0x6d
    for b, t in tanda.SAV_BLOQUES:
        if b <= va < b + t:
            return off + va - b
        off += t
    raise ValueError(hex(va))


SHOPT = sav_off(0x53c38c + 25)


def unidad(c, s):
    return tanda.SAV_BANDOS + (c * 16 + s) * tanda.UNIDAD


def noche(d):
    d = bytearray(d)
    d[SHOPT] |= 2
    for c in range(8):
        if not d[unidad(c, 0):unidad(c, 0) + 1].isalpha():
            continue   # color sin bando
        for s in RANURAS:
            u = unidad(c, s)
            d[u + 0xa9:u + 0xb2] = CLASE.ljust(9, b'\0')
    return bytes(d)


def clases_noche(d, c):
    """Ranuras del color c con una clase de noche (como nm_sub: cualquiera de las dos, sin mayúsculas)."""
    out = []
    for s in range(16):
        u = unidad(c, s)
        cl = [d[u + o:u + o + 9].split(b'\0')[0].lower() for o in (0xa0, 0xa9)]
        if any(x in NOCHE for x in cl):
            out.append(s)
    return out


if __name__ == '__main__':
    g = sys.argv[1]
    suf = sys.argv[2] if len(sys.argv) > 2 else ''
    with open(os.path.join(tanda.JUEGO, 'SAVES', g + '.SAV'), 'rb') as f:
        orig = f.read()
    destino = os.path.join(tanda.JUEGO, 'SAVES', g + '_NO' + suf + '.SAV')
    with open(destino, 'wb') as f:
        f.write(noche(orig))
    with open(destino, 'rb') as f:   # verificar lo escrito, no lo calculado
        v = f.read()
    dif = sum(a != b for a, b in zip(orig, v))
    print(destino, len(v) == len(orig), f'{dif} bytes cambiados', f'día/noche {bool(v[SHOPT] & 2)}',
          [clases_noche(v, c) for c in range(8)])
