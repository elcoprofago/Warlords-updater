# Arma una guardada donde el barco (ranura 15) de los 8 bandos tiene solo el bono de movimiento "Raft" (balsa: zarpa y
# desembarca en cualquier costa, lleva hasta 3, no se aleja más de 1 casilla de tierra), para medir si la IA la usa
# y qué le cambia (paso 5.6 de PENDIENTE-ia-innovaciones). Escribe SAVES\<guardada>_RF.SAV y no toca la original,
# que queda de control en la misma tanda.
# Uso: python ia\balsa.py Tanda_Scarpart
import os, sys

import convoy
import tanda

convoy.BONOS = (b'Raft', b'', b'', b'')

if __name__ == '__main__':
    g = sys.argv[1]
    with open(os.path.join(tanda.JUEGO, 'SAVES', g + '.SAV'), 'rb') as f:
        orig = f.read()
    destino = os.path.join(tanda.JUEGO, 'SAVES', g + '_RF.SAV')
    with open(destino, 'wb') as f:
        f.write(convoy.convoy(orig))
    with open(destino, 'rb') as f:   # verificar lo escrito, no lo calculado
        v = f.read()
    dif = sum(a != b for a, b in zip(orig, v))
    print(destino, len(v) == len(orig), f'{dif} bytes cambiados',
          [convoy.leer_bonos(orig, c) for c in range(8)], '->', [convoy.leer_bonos(v, c) for c in range(8)])
