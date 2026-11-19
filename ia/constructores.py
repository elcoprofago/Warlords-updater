# Arma una guardada donde todas las unidades de los 8 bandos llevan «build» (en su primer bono de movimiento libre:
# no se pisa ninguno), para la tanda del punto 4 de ia\PENDIENTE-ia-muros.md (la IA levanta MURALLA en un paso).
# Ninguna guardada del banco tiene constructores. Escribe SAVES\<guardada>_BD.SAV y no toca la original.
# Uso: python ia\constructores.py Tanda_hex_control
import os, sys

import tanda


def constructores(d):
    d = bytearray(d)
    for c in range(8):
        for s in range(16):
            u = tanda.SAV_BANDOS + (c * 16 + s) * tanda.UNIDAD
            if not d[u:u + 1].isalpha():
                continue
            bonos = [d[u + 0xb2 + k * 9:u + 0xbb + k * 9].split(b'\0')[0].lower() for k in range(4)]
            if b'build' in bonos or b'' not in bonos:
                continue
            k = bonos.index(b'')
            d[u + 0xb2 + k * 9:u + 0xbb + k * 9] = b'build'.ljust(9, b'\0')
    return bytes(d)


def con_build(d, c):
    n = 0
    for s in range(16):
        u = tanda.SAV_BANDOS + (c * 16 + s) * tanda.UNIDAD
        n += d[u:u + 1].isalpha() and any(d[u + 0xb2 + k * 9:u + 0xbb + k * 9].split(b'\0')[0].lower() == b'build'
                                          for k in range(4))
    return n


if __name__ == '__main__':
    for g in sys.argv[1:]:
        with open(os.path.join(tanda.JUEGO, 'SAVES', g + '.SAV'), 'rb') as f:
            orig = f.read()
        destino = os.path.join(tanda.JUEGO, 'SAVES', g + '_BD.SAV')
        with open(destino, 'wb') as f:
            f.write(constructores(orig))
        with open(destino, 'rb') as f:   # verificar lo escrito, no lo calculado
            v = f.read()
        dif = sum(a != b for a, b in zip(orig, v))
        print(destino, len(v) == len(orig), f'{dif} bytes cambiados',
              [con_build(orig, c) for c in range(8)], '->', [con_build(v, c) for c in range(8)])
