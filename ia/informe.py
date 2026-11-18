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
    ruido(db, validas)
    print('\nTurnos sin progreso: los registra la destreza 1 (todavía no implementada).')
    alianzas(db, desde, validas, cuenta)
    innovaciones(db, validas)
    candidatos(db, validas)
    muros(db, validas)
    asaltos(db, validas)
    defensa(db, validas)
    hechizos(db, validas, cuenta)
    perfiles(db, validas)


def ruido(db, validas):
    """Paso 6.1 (ia\\PENDIENTE-ia-innovaciones.md): diferencia prueba − original de PV y puesto medio, partida por
    partida, con su intervalo del 95 % (± 1,96 × desvío / √partidas). Si el intervalo cruza el 0, la diferencia es del
    tamaño del ruido: la destreza no se juzga ganadora ni perdedora con esas partidas."""
    dpv, dpu = [], []
    for pid in validas:
        d = {ia: (pv, pu) for ia, pv, pu in db.execute(
            # eliminado (puesto vacío) = último puesto; si no, el promedio lo ignora y favorece a quien pierde colores
            'select ia, avg(pv), avg(coalesce(puesto, (select count(*) from resultado where partida=?))) '
            'from resultado where partida=? group by ia', (pid, pid))}
        if 0 in d and 1 in d:
            dpv.append(d[1][0] - d[0][0]); dpu.append(d[1][1] - d[0][1])
    if len(dpv) < 2:
        return
    n = len(dpv)
    print(f'\nPrueba - original, partida por partida ({n} partidas con las dos IA; intervalo del 95 %):')
    for nombre, v, mejor in (('PV', dpv, 'más'), ('puesto medio', dpu, 'menos')):
        m = sum(v) / n; sd = (sum((x - m) ** 2 for x in v) / (n - 1)) ** 0.5; h = 1.96 * sd / n ** 0.5
        veredicto = 'dentro del ruido' if m - h <= 0 <= m + h else ('prueba mejor' if (m > 0) == (mejor == 'más')
                                                                     else 'original mejor')
        print(f'  {nombre:13} {m:+6.2f}  ({m - h:+.2f} a {m + h:+.2f})  {veredicto}')


def innovaciones(db, validas):
    """Pozos y puentes (ia\\PENDIENTE-ia-innovaciones.md), por IA y color: caídas en pozos, remolinos y trampas que el
    que cayó ya veía (error evitable) u ocultos, con los ejércitos muertos, y puentes derribados por criterio propio."""
    q = ','.join('?' * len(validas))
    filas = db.execute(f'select ia, color, tipo, n from evento where partida in ({q}) and tipo in (1, 18, 19, 20)',
                       validas).fetchall()
    if not filas:
        print('\nInnovaciones: la tanda no registró caídas en pozos ni derribos de puentes.')
        return
    c = defaultdict(lambda: [0] * 6)   # caídas vistas, muertos en ellas, caídas ocultas, muertos, puentes, por defensa
    for ia, color, tipo, n in filas:
        e = c[ia, color]
        if tipo == 1: e[4] += 1; e[5] += n in (100, 101)   # n = 100: ai_brdef (paso 4 B); 101: fue a derribarlo (4 D)
        else: k = 0 if n >= 100 else 2; e[k] += 1; e[k + 1] += n % 100
    print('\nInnovaciones (caídas en pozo, remolino o trampa: vistas = error evitable)')
    print(f'{"IA":28} {"color":>5} {"vistas":>6} {"muertos":>7} {"ocultas":>7} {"muertos":>7} {"puentes":>7} {"defensa":>7}')
    for (ia, color), e in sorted(c.items()):
        print(f'{IAS.get(ia, ia):28} {color:5} ' + ' '.join(f'{v:{w}}' for v, w in zip(e, (6, 7, 7, 7, 7, 7))))


def muros(db, validas):
    """Eventos 46 y 47 (paso 5.5 de ia\\PENDIENTE-ia-innovaciones.md, solo en tandas): 46 = la IA atacó un bloque de
    muro (n = arqueros muertos, + 100 si el bloque cayó); 47 = turno en que la IA tenía pilas junto a un muro enemigo
    (n = casillas vecinas ocupadas). Muestra si la IA ataca el muro, lo rodea o se queda frente a él."""
    q = ','.join('?' * len(validas))
    filas = db.execute(f'select ia, color, tipo, n from evento where partida in ({q}) and tipo in (46, 47)',
                       validas).fetchall()
    if not filas:
        print('\nMuros: la tanda no registró ataques a murallas ni pilas junto a ellas.')
        return
    c = defaultdict(lambda: [0] * 4)   # ataques, bloques caídos, turnos junto al muro, pilas-casilla junto al muro
    for ia, color, tipo, n in filas:
        e = c[ia, color]
        if tipo == 46: e[0] += 1; e[1] += n >= 100
        else: e[2] += 1; e[3] += n
    print('\nMuros (ataques a bloques de muralla y turnos con pilas junto a un muro enemigo)')
    print(f'{"IA":28} {"color":>5} {"ataques":>7} {"caídos":>6} {"turnos":>6} {"vecinas":>7}')
    for (ia, color), e in sorted(c.items()):
        print(f'{IAS.get(ia, ia):28} {color:5} ' + ' '.join(f'{v:{w}}' for v, w in zip(e, (7, 6, 6, 7))))


def asaltos(db, validas):
    """Evento 48 (paso 5.5 de ia\\PENDIENTE-ia-innovaciones.md, punto 2, solo en tandas): cada asalto a una ciudad que
    la computadora estuvo por dar, con el % de victoria que calculó (0x497390); + 1000 si la IA de prueba no lo dio
    (menos de AP_PCT). Por IA y tramo de %: cuántos, cuántos no se dieron y, de los dados, cuántos ganó (batalla del
    mismo turno, atacante y casilla). Sirve para calibrar AP_PCT."""
    q = ','.join('?' * len(validas))
    filas = db.execute(f'select e.ia, e.n, (select max(b.resultado) from batalla b where b.partida = e.partida and '
                       f'b.turno = e.turno and b.atacante = e.color and b.x = e.x and b.y = e.y) '
                       f'from evento e where e.partida in ({q}) and e.tipo = 48', validas).fetchall()
    if not filas:
        return
    c = defaultdict(lambda: [0] * 4)   # evaluados, no dados, dados con batalla, ganados
    for ia, n, res in filas:
        e = c[ia, min(n % 1000, 100) // 10 * 10]
        e[0] += 1
        if n >= 1000: e[1] += 1
        elif res is not None: e[2] += 1; e[3] += res == 1
    print('\nAsaltos a ciudades (evento 48: % de victoria que calculó la IA antes de asaltar)')
    print(f'{"IA":28} {"%":>7} {"asaltos":>7} {"no dados":>8} {"con bat.":>8} {"ganados":>7}')
    for (ia, t), e in sorted(c.items()):
        r = f'{t:3}-{min(t + 9, 100):3}'
        print(f'{IAS.get(ia, ia):28} {r:>7} ' + ' '.join(f'{v:{w}}' for v, w in zip(e, (7, 8, 8, 7))))


DIAG = {1: 'ejército encima', 2: 'en el camino de la pila', 3: 'IA original (sin defensa)',
        4: 'sin ciudad propia cerca', 5: 'ciudad propia, sin enemigo del otro lado'}


def candidatos(db, validas):
    """Evento 21 (desde 1.0.103.0, solo en tandas): cada vez que una pila de la IA terminó junto a un puente entero y
    no lo derribó, por qué. Sirve para ver qué condición de ai_brdef no se cumple nunca. Aparte, «lo derribó ese turno»:
    la pila de la prueba que iba a derribarlo (paso 4 D) deja el evento 21 al llegar y lo derriba en el mismo turno
    (evento 1, n = 101, mismo color y puente); no es un puente que quedó en pie (tandas 180-182, 7 de cada 10)."""
    q = ','.join('?' * len(validas))
    filas = db.execute(f'select ia, n, exists(select 1 from evento b where b.partida = e.partida and b.tipo = 1 and '
                       f'b.n = 101 and b.color = e.color and b.x = e.x and b.y = e.y and b.turno = e.turno), count(*) '
                       f'from evento e where partida in ({q}) and tipo = 21 group by 1, 2, 3', validas).fetchall()
    if not filas:
        return
    print('\nPuentes junto a una pila de la IA que no se derribaron (evento 21), por motivo')
    for ia, n, luego, k in sorted(filas):
        print(f'{IAS.get(ia, ia):28} {DIAG.get(n, n) + (" (lo derribó ese turno)" if luego else ""):45} {k:6}')


def hechizos(db, validas, cuenta):
    """Evento 44 (desde 1.0.233.0, solo en tandas): hechizo que lanza la IA (ia\\PENDIENTE-ideas-moddb.md, Paso 3).
    x = efecto 1 * 100 + efecto 2, y = costo, n = puntaje con que lo eligió. Por IA: cuántos lanza por color, puntaje
    medio, cuántos son de un solo efecto (los que el error del original inflaba) y los más lanzados."""
    q = ','.join('?' * len(validas))
    filas = db.execute(f'select ia, x, y, n from evento where partida in ({q}) and tipo = 44', validas).fetchall()
    if not filas:
        return
    por = defaultdict(list)
    for ia, x, y, n in filas:
        por[ia].append((x, y, n))
    print('\nHechizos lanzados (evento 44; un efecto = el segundo casillero vacío)')
    print(f'{"IA":28} {"lanzados":>8} {"por color":>9} {"puntaje":>7} {"un efecto":>9}  más lanzados (efectos/costo: veces)')
    for ia in sorted(por):
        v = por[ia]
        uno = sum(1 for x, _, _ in v if x % 100 == 0)
        top = defaultdict(int)
        for x, y, _ in v:
            top[(x // 100, x % 100, y)] += 1
        t = ', '.join(f'{a}+{b}/{c}: {k}' if b else f'{a}/{c}: {k}'
                      for (a, b, c), k in sorted(top.items(), key=lambda e: -e[1])[:5])
        print(f'{IAS.get(ia, ia):28} {len(v):8} {len(v) / max(cuenta.get(ia, 1), 1):9.1f} '
              f'{sum(n for _, _, n in v) / len(v):7.0f} {100 * uno / len(v):8.0f}%  {t}')


DEFNO = {1: 'ejército encima al llegar', 2: 'ya no había amenaza al llegar'}


def defensa(db, validas):
    """Paso 4 D (desde 1.0.105.0, solo en tandas): evento 22, la IA eligió ir a derribar un puente que amenaza una
    ciudad propia (n = costo del viaje); evento 23, llegó y no lo derribó (n = motivo). Los que sí derribó son el
    evento 1 con n = 101."""
    q = ','.join('?' * len(validas))
    filas = db.execute(f'select ia, tipo, n from evento where partida in ({q}) and tipo in (22, 23)'
                       f' union all select ia, 1, n from evento where partida in ({q}) and tipo = 1 and n = 101',
                       validas + validas).fetchall()
    if not filas:
        return
    c = defaultdict(lambda: [0, 0, 0, 0, 0])   # elegidos, costo total, derribados, ejército encima, sin amenaza
    for ia, tipo, n in filas:
        e = c[ia]
        if tipo == 22: e[0] += 1; e[1] += n
        elif tipo == 1: e[2] += 1
        elif n in (1, 2): e[2 + n] += 1
    print('\nIr a derribar un puente que amenaza una ciudad propia (eventos 22, 23 y 1 con n = 101)')
    print(f'{"IA":28} {"elegidos":>8} {"costo medio":>11} {"derribados":>10} {DEFNO[1]:>25} {DEFNO[2]:>29}')
    for ia, e in sorted(c.items()):
        m = f'{e[1] / e[0]:.1f}' if e[0] else '-'
        print(f'{IAS.get(ia, ia):28} {e[0]:8} {m:>11} {e[2]:10} {e[3]:25} {e[4]:29}')


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
