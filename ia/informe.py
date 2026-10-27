# Informe de una tanda (specs\ia-destrezas-v1.md, req. 6), desde ia\datos.db.
# Uso: python ia\informe.py [tanda]      (sin número: la última; «65-69» junta varias tandas)
#
# Por IA (original / prueba), sobre las partidas terminadas (estado ok o tope):
#   promedio por color al final de PV, ciudades, oro y ejércitos (eliminados: 0);
#   partidas ganadas (único primer puesto), primeros puestos compartidos con la otra IA y con la misma;
#   ataques desangrantes: ataque perdido que repite atacante, casilla y composición de otro ataque perdido antes;
#   turnos sin progreso: los registra la destreza 1 (todavía no existe).
# Alianzas (specs\ia-alianzas-v1.md, req. 12), por IA: a. pilas amenazadas y sobrevivientes al turno siguiente
# (eventos 11 y 12); b. refugios (eventos 5 y 7), salidas (8), hasta el final (9), defensa del refugio (13), refuerzos
# (10, hasta 1.0.37.0), turnos en que un refuerzo se queda (14, solo 1.0.37.0), refugios de héroe perseguido (7 con
# n = 3, desde 1.0.39.0), idas a defender una ciudad aliada (15) y turnos que se queda en ella (16); c. batallas en ciudad con defensores de más de un color (colores_d) y cuántas ganó la defensa; d. ciudades
# compartidas atacadas (defensor con un aliado ese turno y la opción de ciudades compartidas) y cuántas resistieron
# el turno; e. héroes vivos al final; f. qué equipo ganó (PV por equipo, con los equipos de la guardada). Lo que una
# tanda vieja no registró queda en blanco.
import json, os, sqlite3, sys
from collections import defaultdict

DB = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)),
                  'datos.db')
IAS = {0: 'original', 1: 'prueba', 2: 'valor inválido (original)'}
# Guardada de medición -> su guardada de control (el mismo perfil en todos los colores; ia\PENDIENTE-mapa-pruebas.md,
# paso 3). Con ella, el informe de perfiles compara el PV de cada color contra el PV medio de su lugar en el control.
CONTROL = {'Tanda_hex_perfiles_SR': 'Tanda_hex_control'}


def main(tid=None):
    db = sqlite3.connect(DB)
    if tid is None:
        tid = sys.argv[1] if len(sys.argv) > 1 else db.execute('select max(id) from tanda').fetchone()[0]
    if tid is None:
        sys.exit('No hay tandas en la base.')
    desde, _, hasta = str(tid).partition('-')
    desde = int(desde); hasta = int(hasta or desde)
    parts = db.execute('select id, n, guardada, asignacion, estado, turnos from partida where tanda between ? and ? '
                       'order by tanda, n', (desde, hasta)).fetchall()
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
    alianzas(db, desde, validas, cuenta)
    innovaciones(db, validas)
    perfiles(db, validas)


def innovaciones(db, validas):
    """Pozos y puentes (ia\\PENDIENTE-ia-innovaciones.md), por IA y color: caídas en pozos, remolinos y trampas que el
    que cayó ya veía (error evitable) u ocultos, con los ejércitos muertos, y puentes derribados por criterio propio."""
    q = ','.join('?' * len(validas))
    filas = db.execute(f'select ia, color, tipo, n from evento where partida in ({q}) and tipo in (1, 18, 19, 20)',
                       validas).fetchall()
    if not filas:
        print('\nInnovaciones: la tanda no registró caídas en pozos ni derribos de puentes.')
        return
    c = defaultdict(lambda: [0] * 5)   # caídas vistas, muertos en ellas, caídas ocultas, muertos, puentes
    for ia, color, tipo, n in filas:
        e = c[ia, color]
        if tipo == 1: e[4] += 1
        else: k = 0 if n >= 100 else 2; e[k] += 1; e[k + 1] += n % 100
    print('\nInnovaciones (caídas en pozo, remolino o trampa: vistas = error evitable)')
    print(f'{"IA":28} {"color":>5} {"vistas":>6} {"muertos":>7} {"ocultas":>7} {"muertos":>7} {"puentes":>7}')
    for (ia, color), e in sorted(c.items()):
        print(f'{IAS.get(ia, ia):28} {color:5} ' + ' '.join(f'{v:{w}}' for v, w in zip(e, (6, 7, 7, 7, 7))))


def perfiles(db, validas):
    """Ronda de personalidades: resultado por perfil (el de cada color de la guardada), sea cual sea la ubicación."""
    q = ','.join('?' * len(validas))
    filas = db.execute(f'select id, guardada, perfiles from partida where id in ({q}) and perfiles is not null',
                       validas).fetchall()
    if not filas:
        return
    import tanda
    nombres = {}; suma = defaultdict(lambda: [0, 0, 0, 0])   # partidas, ganadas, PV, eliminado
    base = {}; dif = defaultdict(list)                       # PV medio de cada lugar en el control; PV - base
    for pid, g, txt in filas:
        if g not in nombres:
            try:
                nombres[g] = {c: tanda.nombre_perfil(b) for c, b in tanda.perfiles(g).items()}
            except OSError:
                nombres[g] = {}
        if g not in base:
            base[g] = {c: pv for c, pv in db.execute(
                "select r.color, avg(r.pv) from resultado r join partida p on p.id = r.partida "
                "where p.guardada = ? and p.estado in ('ok', 'tope') group by r.color", (CONTROL.get(g),))}
        origen = {int(c): o for c, o in json.loads(txt).items()}
        prim = [c for (c,) in db.execute('select color from resultado where partida=? and puesto=1', (pid,))]
        for color, pv, elim in db.execute('select color, pv, eliminado_turno from resultado where partida=?', (pid,)):
            k = (g, origen.get(color, color)); t = suma[k]
            t[0] += 1; t[1] += prim == [color]; t[2] += pv or 0; t[3] += elim is not None
            if color in base[g]:
                dif[k].append((pv or 0) - base[g][color])
    print('\nPersonalidades (por perfil, rotado entre ubicaciones; ganadas = único primer puesto)')
    print(f'{"perfil (color de la guardada)":58} {"partidas":>8} {"ganadas":>7} {"PV":>6} {"elimin.":>7} '
          f'{"PV contra su lugar":>18}')
    for (g, o), (n, gan, pv, el) in sorted(suma.items(), key=lambda kv: (-kv[1][1], -kv[1][2])):
        nom = f'{tanda.COLORES[o]}: {nombres[g].get(o, "?")}'
        d = dif.get((g, o), [])
        if len(d) > 1:
            m = sum(d) / len(d); err = (sum((x - m) ** 2 for x in d) / (len(d) - 1) / len(d)) ** .5
            contra = f'{m:+.1f} ± {err:.1f}'
        else:
            contra = 'sin control' if g not in CONTROL else '-'
        print(f'{nom:58} {n:8} {gan:7} {pv / n:6.1f} {el:7} {contra:>18}')


def equipos_de(texto):
    if not texto or not texto.startswith('equipos '):
        return []
    return [set(map(int, e)) for e in texto.split()[1].rstrip(';').split('|')]


def alianzas(db, tid, validas, cuenta):
    q = ','.join('?' * len(validas))
    ev = defaultdict(lambda: defaultdict(int))
    hay_ev = db.execute(f'select count(*) from evento where partida in ({q})', validas).fetchone()[0]
    for ia, tipo, n, k in db.execute(f'select ia, tipo, n, count(*) from evento where partida in ({q}) '
                                     'group by ia, tipo, n', validas):
        ev[ia][tipo] += k
        if tipo == 12 and n == 1: ev[ia]['sobrevivio'] += k
        if tipo == 7 and n == 3: ev[ia]['heroe'] += k
    # amigos[(partida, turno, color)] = aliados ese turno, si la partida tiene ciudades compartidas
    amigos = {}
    for row in db.execute(f'select partida, turno, color, opciones, {", ".join(f"d{i}" for i in range(8))} from diplo '
                          f'where partida in ({q})', validas):
        if row[3] & 1:
            amigos[row[:3]] = {j for j in range(8) if j != row[2] and row[4 + j] == 0}
    hay_dip = bool(db.execute(f'select count(*) from diplo where partida in ({q})', validas).fetchone()[0])
    multi = defaultdict(lambda: [0, 0]); comp = defaultdict(dict); hay_col = False
    for pid, tur, de, ciu, res, ia, col in db.execute(
            f'select partida, turno, defensor, ciudad, resultado, ia_d, colores_d from batalla '
            f'where partida in ({q}) and ciudad >= 0', validas):
        if col is not None:
            hay_col = True
            if bin(col).count('1') > 1:
                multi[ia][0] += 1; multi[ia][1] += res != 1
        if amigos.get((pid, tur, de)):
            k = (pid, tur, ciu); comp[ia][k] = comp[ia].get(k, True) and res != 1
    heroes = defaultdict(int)
    for pid, color, ia, elim in db.execute(f'select partida, color, ia, eliminado_turno from resultado '
                                           f'where partida in ({q})', validas):
        h = db.execute('select heroes from turno where partida=? and color=? order by turno desc limit 1',
                       (pid, color)).fetchone()
        heroes[ia] += 0 if elim or not h else h[0]
    b = lambda v, ok: str(v) if ok else ''
    print('\nAlianzas (req. 12; en blanco lo que la tanda no registró)')
    print(f'{"IA":28} {"amenaz.":>7} {"sobrev.":>7} {"refug.":>6} {"salid.":>6} {"final":>5} {"def.ref":>7} '
          f'{"refuer.":>7} {"ref.qda":>7} {"ref.hér":>7} {"def.ali":>7} {"def.qda":>7} {"bat.multi":>9} {"ganó def":>8} {"compart.":>8} {"resist.":>7} {"héroes":>6}')
    for ia in sorted(cuenta):
        e = ev[ia]; ok = bool(hay_ev)
        print(f'{IAS.get(ia, ia):28} {b(e[11], ok):>7} {b(e["sobrevivio"], ok):>7} {b(e[5] + e[7], ok):>6} '
              f'{b(e[8], ok):>6} {b(e[9], ok):>5} {b(e[13], ok):>7} {b(e[10], ok):>7} {b(e[14], ok):>7} {b(e["heroe"], ok):>7} {b(e[15], ok):>7} {b(e[16], ok):>7} {b(multi[ia][0], hay_col):>9} '
              f'{b(multi[ia][1], hay_col):>8} {b(len(comp[ia]), hay_dip):>8} '
              f'{b(sum(comp[ia].values()), hay_dip):>7} {heroes[ia]:6}')
    al = json.loads(db.execute('select alianzas from tanda where id=?', (tid,)).fetchone()[0] or '{}')
    print('\nEquipo ganador por partida (PV por equipo; IA del equipo: O original, P prueba, M mezcla)')
    for pid, n, g, asig in db.execute(f'select id, n, guardada, asignacion from partida where id in ({q}) order by n',
                                      validas):
        eqs = equipos_de(al.get(g))
        if len(eqs) < 2:
            print(f'  {n + 1:2}. sin equipos'); continue
        pv = dict(db.execute('select color, pv from resultado where partida=?', (pid,)).fetchall())
        tot = sorted(((sum(pv.get(c) or 0 for c in e), e) for e in eqs), key=lambda t: -t[0])
        ias = lambda e: (lambda s: s.pop() if len(s) == 1 else 'M')({asig[c] for c in e})
        txt = ', '.join(f'{"".join(map(str, sorted(e)))} ({ias(e)}) {v}' for v, e in tot)
        gan = 'empate' if tot[0][0] == tot[1][0] else f'gana {"".join(map(str, sorted(tot[0][1])))}'
        print(f'  {n + 1:2}. {txt}: {gan}')


if __name__ == '__main__':
    main()
