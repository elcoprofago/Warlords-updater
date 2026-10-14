# Informe de una tanda (specs\ia-destrezas-v1.md, req. 6), desde ia\datos.db.
# Uso: python ia\informe.py [tanda]      (sin número: la última)
#
# Por IA (original / prueba), sobre las partidas terminadas (estado ok o tope):
#   promedio por color al final de PV, ciudades, oro y ejércitos (eliminados: 0);
#   partidas ganadas (único primer puesto), primeros puestos compartidos con la otra IA y con la misma;
#   ataques desangrantes: ataque perdido que repite atacante, casilla y composición de otro ataque perdido antes;
#   turnos sin progreso: los registra la destreza 1 (todavía no existe).
import os, sqlite3, sys
from collections import defaultdict

DB = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)),
                  'datos.db')
IAS = {0: 'original', 1: 'prueba', 2: 'valor inválido (original)'}


def main(tid=None):
    db = sqlite3.connect(DB)
    if tid is None:
        tid = int(sys.argv[1]) if len(sys.argv) > 1 else db.execute('select max(id) from tanda').fetchone()[0]
    if tid is None:
        sys.exit('No hay tandas en la base.')
    parts = db.execute('select id, n, guardada, asignacion, estado, turnos from partida where tanda=? order by n',
                       (tid,)).fetchall()
    print(f'Tanda {tid}: {len(parts)} partidas')
    for pid, n, g, asig, est, tur in parts:
        print(f'  {n + 1:2}. {g:18} {asig}  {est:8} {tur or 0:3} turnos')
    validas = [p[0] for p in parts if p[4] in ('ok', 'tope')]
    if not validas:
        return
    q = ','.join('?' * len(validas))
    suma = defaultdict(lambda: defaultdict(float)); cuenta = defaultdict(int)
    for pid, color, ia, pv, ci, oro in db.execute(
            f'select partida, color, ia, pv, ciudades, oro from resultado where partida in ({q})', validas):
        ej = db.execute('select ejercitos from turno where partida=? and color=? order by turno desc limit 1',
                        (pid, color)).fetchone()
        elim = db.execute('select eliminado_turno from resultado where partida=? and color=?', (pid, color)).fetchone()[0]
        for k, v in (('pv', pv), ('ciudades', ci), ('oro', oro), ('ejercitos', 0 if elim else (ej[0] if ej else 0))):
            suma[ia][k] += v
        cuenta[ia] += 1
    gana = defaultdict(int); comp_otra = defaultdict(int); comp_misma = defaultdict(int)
    for pid in validas:
        prim = [ia for (ia,) in db.execute('select ia from resultado where partida=? and puesto=1', (pid,))]
        if len(prim) == 1:
            gana[prim[0]] += 1
        elif len(set(prim)) > 1:
            for ia in set(prim): comp_otra[ia] += 1
        elif prim:
            comp_misma[prim[0]] += 1
    desang = defaultdict(int); ataques = defaultdict(int); perdidos = defaultdict(int)
    comp = ', '.join(f'a{i}' for i in range(17))
    for pid in validas:
        vistos = set()
        for row in db.execute(f'select atacante, ia_a, x, y, resultado, {comp} from batalla where partida=? '
                              'order by rowid', (pid,)):
            at, ia, x, y, res = row[:5]; ataques[ia] += 1
            if res != 1:
                perdidos[ia] += 1
                k = (at, x, y, row[5:])
                if k in vistos: desang[ia] += 1
                vistos.add(k)
    print(f'\nPartidas válidas: {len(validas)}   (promedios por color al final de la partida)')
    print(f'{"IA":28} {"colores":>7} {"PV":>6} {"ciudades":>8} {"oro":>7} {"ejérc.":>7} {"ganadas":>7} '
          f'{"1.º comp.":>9} {"ataques":>7} {"perdidos":>8} {"desangr.":>8}')
    for ia in sorted(cuenta):
        c = cuenta[ia]; s = suma[ia]
        print(f'{IAS.get(ia, ia):28} {c:7} {s["pv"] / c:6.1f} {s["ciudades"] / c:8.1f} {s["oro"] / c:7.0f} '
              f'{s["ejercitos"] / c:7.1f} {gana[ia]:7} {comp_otra[ia] + comp_misma[ia]:9} {ataques[ia]:7} '
              f'{perdidos[ia]:8} {desang[ia]:8}')
    print('\nTurnos sin progreso: los registra la destreza 1 (todavía no implementada).')


if __name__ == '__main__':
    main()
