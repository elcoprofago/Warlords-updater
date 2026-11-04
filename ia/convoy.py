# Arma una guardada donde el barco (ranura 15) de los 8 bandos tiene solo el bono de movimiento "Carrier", para medir
# si la IA arma convoyes (eventos 2, 24 y 25). Paso 5.1 de PENDIENTE-ia-innovaciones. Escribe SAVES\<guardada>_CA.SAV
# y no toca la original (que queda de control). Sin "Landing": cada bono va en una unidad distinta, para obligar a
# elegir al armar el bando (las _CR de las tandas 127-130 juntaban los dos y la IA prefería desembarcar en playa).
# Uso: python ia\convoy.py Tanda_Scarpart
import os, sys

import tanda

BONOS = (b'Carrier', b'', b'', b'')   # bonos de movimiento: +0xb2 + k*9, 9 bytes cada uno


def convoy(d):
    d = bytearray(d)
    for c in range(8):
        u = tanda.SAV_BANDOS + (c * 16 + 15) * tanda.UNIDAD
        if not d[u:u + 1].isalpha():
            continue   # color sin bando
        for k, b in enumerate(BONOS):
            d[u + 0xb2 + k * 9:u + 0xbb + k * 9] = b.ljust(9, b'\0')
    return bytes(d)


def leer_bonos(d, c):
    u = tanda.SAV_BANDOS + (c * 16 + 15) * tanda.UNIDAD
    return [d[u + 0xb2 + k * 9:u + 0xbb + k * 9].split(b'\0')[0].decode('latin-1') for k in range(4)]


if __name__ == '__main__':
    g = sys.argv[1]
    with open(os.path.join(tanda.JUEGO, 'SAVES', g + '.SAV'), 'rb') as f:
        orig = f.read()
    d = convoy(orig)
    destino = os.path.join(tanda.JUEGO, 'SAVES', g + '_CA.SAV')
    with open(destino, 'wb') as f:
        f.write(d)
    with open(destino, 'rb') as f:   # verificar lo escrito, no lo calculado
        v = f.read()
    dif = sum(a != b for a, b in zip(orig, v))
    print(destino, len(v) == len(orig), f'{dif} bytes cambiados', [leer_bonos(v, c) for c in range(8)])
