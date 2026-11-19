# Prueba de ia\movimiento.py contra el código del juego (DarklordAV.exe en el emulador de simcombate\motor.py):
# 1. la grilla de costos: corre 0x4a4f90 sobre la guardada y compara byte a byte 0x57d158 (x*0xa0 + y) con
#    movimiento.grilla;
# 2. el costo de un paso: llama a 0x4a6490(ranura, x, y, 0, 1) con cada bono 0-3 en 0x587192 y lo compara con
#    movimiento.costo, en todas las casillas de costo mayor que 2 y en una de cada 7 de las demás;
# 3. control: la misma grilla sin el +1 de la capa de bosque tiene que fallar en los mapas que la usan;
# 4. movimiento.turnos en un caso de juguete: una fila de llanuras (costo 2) y una colina (5), con movimiento 5. Control:
#    si el sobrante pasara al turno siguiente, la casilla 5 se alcanzaría en el turno 2, no en el 3.
# Uso: python ia\prueba_movimiento.py [guardadas...]   (por defecto las cuatro de ia\pasos)
import os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'simcombate'))
import tanda
import movimiento
from motor import Motor

GRID, RANURA, BONO = 0x57d158, 0x58715c, 0x587192


def probar(guardada):
    sav = os.path.join(tanda.JUEGO, 'SAVES', guardada + '.SAV')
    d = open(sav, 'rb').read()
    m = Motor(os.path.join(tanda.JUEGO, 'DarklordAV.exe'), sav)
    m.call(0x4a4f90, [])
    juego = bytes(m.mu.mem_read(GRID, 0x5000))
    g = movimiento.grilla(d)
    mal = [(p, g[p], juego[p[0] * 0xa0 + p[1]]) for p in g if g[p] != juego[p[0] * 0xa0 + p[1]]]
    ok = not mal
    print(f'{guardada}: grilla {len(g)} casillas, {len(mal)} distintas' + (f' (p. ej. {mal[:3]})' if mal else ''))
    # control: sin el +1 de la capa de bosque
    capa = [p for p in g if movimiento.casilla(d, *p)[3] & 0x40 and movimiento.casilla(d, *p)[3] & 7 not in (1, 3)]
    if capa:                      # sin el +1, la réplica tiene que diferir del juego en todas
        ctrl = all((juego[x * 0xa0 + y] & 0xf) != (g[x, y] & 0xf) - 1 for x, y in capa)
        print(f'   control capa de bosque: {len(capa)} casillas, sin el +1 la réplica falla en todas: '
              f'{"sí" if ctrl else "NO"}')
        ok &= ctrl
    # costo de un paso con cada bono
    m.mu.mem_write(RANURA, (0).to_bytes(2, 'little'))
    malp, n = [], 0
    for i, (x, y) in enumerate(sorted(g)):
        if (g[x, y] & 0xf) <= 2 and i % 7:
            continue
        for b in range(4):
            m.mu.mem_write(BONO, b.to_bytes(2, 'little'))
            v = m.call(0x4a6490, [0, x, y, 0, 1]) & 0xffff
            n += 1
            if v != movimiento.costo(g[x, y], b):
                malp.append(((x, y), b, v, movimiento.costo(g[x, y], b)))
    print(f'   costo de paso: {n} llamadas, {len(malp)} distintas' + (f' (p. ej. {malp[:3]})' if malp else ''))
    return ok and not malp


def juguete():
    g = {(x, 0): 2 for x in range(8)}
    g[3, 0] = 5 | movimiento.COLINAS              # colina en la casilla 3
    nodos = set(g)
    sin = {p[0]: v[0] for p, v in movimiento.turnos([(0, 0)], 5, g, nodos).items()}
    con = {p[0]: v[0] for p, v in movimiento.turnos([(0, 0)], 5, g, nodos, bono=2).items()}
    # sin bono: t1 llega a 1 (queda 3) y 2 (queda 1); la colina (5) en t2 (queda 0); 4 en t3 (3), 5 en t3 (1), 6 en t4
    # con bono de colinas la colina cuesta 2: t1 1, 2; t2 3 (queda 3), 4 (1); t3 5, 6; t4 7
    esperado_sin = {0: 1, 1: 1, 2: 1, 3: 2, 4: 3, 5: 3, 6: 4, 7: 4}
    esperado_con = {0: 1, 1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 4}
    ok = sin == esperado_sin and con == esperado_con
    # control: sin colina, con arrastre del sobrante (2 puntos por casilla, 5 por turno acumulados) la casilla 5 cuesta
    # 10 y se alcanzaría en el turno 2; la réplica tiene que dar 3
    llano = {(x, 0): 2 for x in range(8)}
    ctrl = movimiento.turnos([(0, 0)], 5, llano, set(llano))[5, 0][0] == 3
    print(f'juguete de turnos: {"bien" if ok else "MAL " + str((sin, con))}; control del sobrante: '
          f'{"sí" if ctrl else "NO"}')
    return ok and ctrl


if __name__ == '__main__':
    gs = sys.argv[1:] or ['Tanda_hex_perfiles', 'Tanda_Borderlands', 'Tanda_Kor', 'Tanda_Scarpart']
    todo = juguete()
    todo = all([probar(x) for x in gs]) and todo
    print('TODO OK' if todo else 'FALLA')
    sys.exit(0 if todo else 1)
