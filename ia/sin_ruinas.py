# Arma una guardada para tandas sin el azar de las ruinas: todas quedan exploradas (+0x95 = 1), visibles y vacías,
# así ningún héroe saca ítems, aliados ni oro de ellas. Escribe SAVES\<guardada>_SR.SAV y no toca la original.
# Uso: python ia\sin_ruinas.py Tanda_hex_simple
import os, sys

import tanda

RUINAS_N, RUINAS, TAM = 0x558872, 0x558874, 0xb8   # tabla de ruinas del exe (parches\vista-aliada\PENDIENTE-pozos-y-trampas.md)


def offset(va):
    o = 0x6d
    for b, t in tanda.SAV_BLOQUES:
        if b <= va < b + t:
            return o + va - b
        o += t
    raise ValueError(hex(va))


def sin_ruinas(d):
    d = bytearray(d)
    n = int.from_bytes(d[offset(RUINAS_N):offset(RUINAS_N) + 2], 'little')
    for i in range(n):
        r = offset(RUINAS + i * TAM)
        d[r + 0x95] = 1      # explorada
        d[r + 0x96] = 0      # sin contenido
        d[r + 0x98] = 254    # sin guardián (como las que no lo tienen)
        d[r + 0x9a] = 0      # no oculta
    return bytes(d), n


if __name__ == '__main__':
    g = sys.argv[1]
    origen = os.path.join(tanda.JUEGO, 'SAVES', g + '.SAV')
    with open(origen, 'rb') as f:
        d, n = sin_ruinas(f.read())
    destino = os.path.join(tanda.JUEGO, 'SAVES', g + '_SR.SAV')
    with open(destino, 'wb') as f:
        f.write(d)
    print(f'{n} ruinas exploradas y vacías: {destino}')
