# Prueba de ia\cerrar_paso.py con MURALLAS puestas a mano (en memoria; no toca ninguna guardada), en Borderlands,
# partida 1477, turno 15, donde el 7 elige el paso 4 y también tiene el 8 y el 6, y el 3 tiene el 8:
# A. un bloque del 7 en el paso 8: para el 7 va primero (terminar lo empezado, en ese mismo tramo); para el 3, que no
#    es su aliado, es MURALLA ajena: el paso 8 sigue, marcado, y se cierra en otro tramo sin esa casilla.
# B. el paso 4 cerrado entero por el 7: desaparece de sus opciones.
# C. una torre (obra que no es MURALLA) del 7 en el paso 8: el paso sigue, sin marca, en otro tramo sin la torre.
# D. un bloque de un bando no aliado del 7 en el paso 8 (amenaza 52, contra 62 del paso 4): para el 7 pasa primero
#    (señal de que el paso importa, usuario 19/11/2026), en el otro tramo (el paso 8 tiene dos, sin casillas comunes).
# E. ese mismo bloque en el paso 6, cuyos dos tramos comparten (13,83) y (13,84): no queda tramo donde construir
#    (sobre una obra no se construye), así que el 7 no puede cerrarlo y sale de la lista.
# Control: las opciones del 6 (pasos 10 y 3, sin obras) no cambian en ningún caso. Además, la lectura de la tabla de
# obras de una guardada que las tiene (Tanda_hex_MU, armada con muros.py): cada bloque tiene que estar en el anillo de
# una ciudad de su dueño (sin las casillas donde no se puede construir, por eso no son siempre 12 por ciudad).
# Uso: python ia\prueba_cerrar_paso.py
import os, sys

import tanda
import ciudades
import muros
import cerrar_paso as cp

GUARDADA, PARTIDA, TURNO = 'Tanda_Borderlands', 1477, 15
OB_TORRE = 4


def pasos_de(out, c):
    return [(o['paso'], o['hechos']) for o in out[c]['opciones']]


def opcion(out, c, n):
    return next((o for o in out[c]['opciones'] if o['paso'] == n), None)


def main():
    ok = True

    def ver(nombre, cond):
        nonlocal ok
        ok &= cond
        print(f'  {nombre}: {"bien" if cond else "MAL"}')

    base, pas, _, _ = cp.analizar(GUARDADA, PARTIDA, TURNO, ob={})
    tramo = {P['n']: P['tramo'] for P in pas}
    b7, b3, b6 = pasos_de(base, 7), pasos_de(base, 3), pasos_de(base, 6)
    print(f'sin obras: 7 {b7}, 3 {b3}, 6 {b6}')
    ver('punto de partida (7 elige el 4 y tiene el 8; 3 tiene el 8)',
        b7[0][0] == 4 and 8 in dict(b7) and 8 in dict(b3))

    a, _, _, _ = cp.analizar(GUARDADA, PARTIDA, TURNO, ob={tramo[8][0]: (cp.OB_MURO, 7)})
    print(f'A: 7 {pasos_de(a, 7)}, 3 {pasos_de(a, 3)}')
    ver('A: el 7 termina lo empezado (paso 8 primero, 1 hecho, mismo tramo)',
        pasos_de(a, 7)[0] == (8, 1) and tramo[8][0] in opcion(a, 7, 8)['tramo'])
    o3 = opcion(a, 3, 8)
    ver('A: el 3 sigue con el paso 8, marcado como MURALLA ajena, en un tramo sin esa casilla',
        bool(o3) and o3['ajena'] and tramo[8][0] not in o3['tramo'] and not opcion(base, 3, 8)['ajena'])
    ver('A: control, el 6 no cambia', pasos_de(a, 6) == b6)

    b, _, _, _ = cp.analizar(GUARDADA, PARTIDA, TURNO, ob={t: (cp.OB_MURO, 7) for t in tramo[4]})
    print(f'B: 7 {pasos_de(b, 7)}')
    ver('B: el paso 4 cerrado no se elige', 4 not in dict(pasos_de(b, 7)) and pasos_de(b, 7)[0][0] == 8)
    ver('B: control, el 6 no cambia', pasos_de(b, 6) == b6)

    c, _, _, _ = cp.analizar(GUARDADA, PARTIDA, TURNO, ob={tramo[8][0]: (OB_TORRE, 7)})
    print(f'C: 7 {pasos_de(c, 7)}')
    o8 = opcion(c, 7, 8)
    ver('C: con una torre en el tramo, el paso 8 sigue, sin marca, en otro tramo',
        bool(o8) and not o8['ajena'] and tramo[8][0] not in o8['tramo'] and pasos_de(c, 7) == b7)
    ver('C: control, el 6 no cambia', pasos_de(c, 6) == b6)

    sav = open(os.path.join(tanda.JUEGO, 'SAVES', GUARDADA + '.SAV'), 'rb').read()
    ali = cp.estado(sav, GUARDADA, PARTIDA, TURNO)[2]
    otro = min(c for c in range(8) if c != 7 and c not in ali[7])
    dd, _, _, _ = cp.analizar(GUARDADA, PARTIDA, TURNO, ob={tramo[8][0]: (cp.OB_MURO, otro)})
    o8 = opcion(dd, 7, 8)
    print(f'D: MURALLA del {otro} en el paso 8: 7 {pasos_de(dd, 7)}, tramo {o8 and o8["tramo"]}')
    ver('D: el paso 8 pasa primero para el 7 (antes que el 4, de más amenaza), en un tramo sin esa casilla',
        pasos_de(dd, 7)[0][0] == 8 and o8['ajena'] and tramo[8][0] not in o8['tramo'])
    ver('D: control, el 6 no cambia', pasos_de(dd, 6) == b6)

    e, _, _, _ = cp.analizar(GUARDADA, PARTIDA, TURNO, ob={tramo[6][0]: (cp.OB_MURO, otro)})
    print(f'E: MURALLA del {otro} en la casilla que comparten los 2 tramos del paso 6: 7 {pasos_de(e, 7)}')
    ver('E: el paso 6 no se puede cerrar (no hay tramo libre) y sale de la lista; lo demás igual',
        6 not in dict(pasos_de(e, 7)) and [x for x in b7 if x[0] != 6] == pasos_de(e, 7))
    ver('E: control, el 6 no cambia', pasos_de(e, 6) == b6)

    d = open(os.path.join(tanda.JUEGO, 'SAVES', 'Tanda_hex_MU.SAV'), 'rb').read()
    ob = cp.obras(d)
    n_muros = sum(t == cp.OB_MURO for t, _ in ob.values())
    print(f'Tanda_hex_MU: {len(ob)} obras, {n_muros} MURALLAS, dueños {sorted({du for _, du in ob.values()})}')
    anillos = {(t, c['dueño']) for c in ciudades.leer(d) for t in muros.anillo(c['x'], c['y'])}
    ver('lectura de la tabla de obras (cada bloque en el anillo de una ciudad de su dueño)',
        n_muros > 0 and all((t, du) in anillos for t, (_, du) in ob.items()))
    print('TODO OK' if ok else 'FALLA')
    return ok


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
