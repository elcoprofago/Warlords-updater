# Arma una guardada donde todos los pozos, remolinos y trampas ya están descubiertos por los 8 colores (máscara +6 =
# 0xff), para medir si la IA entra en los que ve. Escribe SAVES\<guardada>_PV.SAV y no toca la original.
# Uso: python ia\pozos_vistos.py Tanda_hex_pozos_control
import os, sys

import tanda


def pozos_vistos(d):
    d = bytearray(d)
    i = d.rfind(b'POZO')
    if i < 0:
        raise ValueError('la guardada no trae el bloque POZO')
    n = int.from_bytes(d[i + 4:i + 8], 'little')
    for k in range(n):
        d[i + 8 + k * 8 + 6] = 0xff
    return bytes(d), n


if __name__ == '__main__':
    g = sys.argv[1]
    origen = os.path.join(tanda.JUEGO, 'SAVES', g + '.SAV')
    with open(origen, 'rb') as f:
        d, n = pozos_vistos(f.read())
    base, ctl = (g[:-8], '_control') if g.lower().endswith('_control') else (g, '')
    destino = os.path.join(tanda.JUEGO, 'SAVES', base + '_PV' + ctl + '.SAV')
    with open(destino, 'wb') as f:
        f.write(d)
    print(f'{n} pozos a la vista de todos: {destino}')
