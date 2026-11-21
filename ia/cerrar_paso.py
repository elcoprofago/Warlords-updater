# Punto 3.c de ia\PENDIENTE-ia-muros.md: la regla con la que un bando de la computadora decide qué paso clave cerrar
# con MURALLA. Prototipo en Python de lo que va a hacer el juego, con los mismos datos que el juego tiene a mano (sin
# tocarlo): lee una guardada y, si se le da una partida del banco y un turno, toma los dueños de las ciudades, el oro
# y la diplomacia de ese turno (datos.db), para ver la regla a mitad de partida y no solo al empezar.
# Vocabulario (CLAUDE.md): MURALLA = lo que se construye; MURO = terreno «Walls» del escenario.
#
# La regla (v1, 19/11/2026):
# 1. Condiciones del bando (usuario, 19/11/2026): Artificer o Engineer; oro >= AW_DIV x precio de un bloque (el
#    mismo margen que ai_wrep: que no quede sin oro para sus tropas); y alguna unidad con «build» que pueda producir
#    (sin constructor no hay muralla). El precio, como bd_price: fundar una ciudad (BuildCity de Default.rul) a la
#    mitad por ser de la computadora (0x536c12 != -1; ese es el campo que la nota daba por «sin identificar»), menos
#    10 % por punto de ingeniería (+6 Artificer, +2 Engineer, + el mejor héroe ingeniero, tope 9), x OB_FRAC/20.
#    Sin héroes ingenieros: Artificer 80, Engineer 160 (el humano paga el doble).
# 2. Por cada paso (pasos.detectar) que no esté ya cerrado y por cada lado D con ciudades propias (f(D) >= 1):
#    amenaza = suma, por cada bando no aliado (en guerra o en paz: el enemigo potencial, criterio del usuario) con
#    ciudades del otro lado O y ninguna en D, de sus ciudades en O que llegan al paso en HORIZONTE turnos o menos
#    («3-4 jugadas»), x 2 si no puede rodear el paso, x 1 si lo rodea por agua («cerrarlo vale menos») y x 0 si lo
#    rodea por aire (v2, 19/11/2026: la tanda 190, sin voladores, mostró que la MURALLA protege; la 189, con
#    voladores, que la burlan).
#    - Llegar al paso (aproximado, para el juego): un recorrido hacia atrás desde el tramo por O con el costo de cada
#      casilla (movimiento.grilla, la grilla 0x57d158 del juego), uno por bono de terreno; la ciudad llega en
#      techo(costo / movimiento) turnos con la unidad no voladora más rápida del enemigo (movimiento.perfiles). Lo
#      exacto (movimiento.turnos: lo que sobra de un turno se pierde) puede dar un turno más: se compara y se informa.
#    - Por aire: si puede producir voladores o ya los tiene. La MURALLA no los frena nunca (la sobrevuelan), así que
#      no hace falta mirar por dónde vuelan.
#    - Por agua (simplificado para el juego): con barco común, si los dos lados tienen puerto; con «Landing», si O
#      tiene puerto y D costa; con «Raft», si los dos tienen costa. No mira si es el mismo mar: se compara con el
#      cálculo exacto de amenaza.py y se informa si difieren.
# 3. Se descartan los pasos cuya ciudad propia más cercana queda a más de MP_DIST casillas (el constructor tendría
#    que cruzar medio mapa) y los que no tienen amenaza.
# 4. Elige la mayor amenaza; a igualdad, la ciudad propia más cerca del paso y después el tramo más corto.
# 5. Con la tabla de obras, mirando todos los tramos que cortan las mismas ciudades: un paso que el bando (o un
#    aliado) ya empezó a cerrar va primero (terminar lo empezado); después, uno con MURALLA ajena (señal de que el paso
#    importa: le sirve solo al enemigo, usuario 19/11/2026); uno ya cerrado del todo no se elige. Se construye en un
#    tramo sin obras ajenas (encima no se puede), con preferencia por el empezado y por uno de nuestro lado.
# Regla vigente (usuario, 21/11/2026; vista-aliada 1.0.284.0): la IA construye cuando hay a la vez a) amenaza: enemigo
# potencial cercano; b) un paso obligado o un corredor defendible (PUENTE o PUERTO que se puede rodear); c) oro
# suficiente; d) Artificer o Engineer; e) una unidad con «build»; f) sin importar si el enemigo tiene voladores (ya no
# anulan la amenaza); g) sin importar si el paso ya tiene una MURALLA enemiga (ni adelanta el paso ni lo descarta).
# Uso: python ia\cerrar_paso.py Tanda_Borderlands [partida turno] [--control]
import os, sys, json, sqlite3, collections, heapq, struct

import tanda
import ciudades
import historia
import pasos
import amenaza
import movimiento
from muros import casilla, sirve
from pasos import VEC, componentes

AW_DIV = 2
OB_FRAC, BD_DIV = 10, 20
BUILD_CITY = 800          # Default.rul, BuildCity
MP_DIST = 20              # casillas: más lejos, el constructor no va
CONTROL = False           # --control: compara los turnos aproximados con los exactos (lento)
HORIZONTE = 4             # turnos: «3-4 jugadas» (usuario); un enemigo que tarda más en llegar al paso no cuenta
ARTIFICER, ENGINEER = 1 << 19, 1 << 18
OB_MURO = 7               # MURALLA en la tabla de obras (build.py)
ORO = 0xe4                # oro en el registro del jugador (0x536c14 - 0x536b30)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'datos.db')


def precio(perfil, heroe=0):
    aj = min(9, heroe + (6 if perfil & ARTIFICER else 2 if perfil & ENGINEER else 0))
    base = BUILD_CITY // 2                     # de la computadora
    base += base * aj // -10
    return base * OB_FRAC // BD_DIV


def constructor(d, c):
    """Nombres de las unidades con «build» que el bando puede producir (sus 16 ranuras)."""
    out = []
    for s in range(16):
        u = tanda.SAV_BANDOS + (c * 16 + s) * tanda.UNIDAD
        r = d[u:u + tanda.UNIDAD]
        if r[:1].isalpha() and any(r[0xb2 + k * 9:0xbb + k * 9].split(b'\0')[0].lower() == b'build' for k in range(4)):
            out.append(r[:16].split(b'\0')[0].decode('latin-1'))
    return out


def hacia_atras(destino, nodos, g, bono):
    """{casilla: puntos de movimiento para llegar desde ella a una de las casillas destino, sin salir de nodos}."""
    best = {}
    pq = [(0, p) for p in destino if p in nodos]
    while pq:
        c, p = heapq.heappop(pq)
        if p in best:
            continue
        best[p] = c
        paso = movimiento.costo(g[p], bono)       # lo que cuesta entrar a p desde una vecina
        if paso <= 0:
            continue
        for dx, dy in VEC:
            n = (p[0] + dx, p[1] + dy)
            if n in nodos and n not in best:
                heapq.heappush(pq, (c + paso, n))
    return best


def obras(d):
    """{(x, y): (tipo, dueño)} de la tabla de obras de la guardada (bloque 'OBR2', o 'OBRA' en las viejas)."""
    for tag in (b'OBR2', b'OBRA'):
        o = d.rfind(tag)
        if o >= 0 and len(d) - o <= 8 + 512 * 8 + 8:
            n = struct.unpack_from('<I', d, o + 4)[0]
            return {(x, y): (t, du) for x, y, t, _, du, _ in
                    (struct.unpack_from('<hhBBBB', d, o + 8 + k * 8) for k in range(n))}
    return {}


def estado(d, guardada, partida=None, turno=None):
    """(dueño de cada ciudad, oro de cada color, aliados de cada color) de la guardada o de esa partida y turno."""
    cs = ciudades.leer(d)
    dueño = {c['i']: c['dueño'] for c in cs}
    js = tanda.jugadores(d)
    oro = {c: int.from_bytes(d[o + ORO:o + ORO + 4], 'little', signed=True) for c, o in js.items()}
    ali = amenaza.aliados(guardada)
    if partida:
        db = sqlite3.connect(DB)
        for (ci, at) in db.execute('select ciudad, atacante from batalla where partida=? and turno<=? and ciudad>=0 '
                                   'and resultado=1 order by turno, rowid', (partida, turno)):
            dueño[ci] = at
        oro = {c: o for c, o in db.execute('select color, oro from turno where partida=? and turno=?',
                                           (partida, turno))}
        ali = collections.defaultdict(set)
        for row in db.execute('select color, d0, d1, d2, d3, d4, d5, d6, d7 from diplo where partida=? and turno=?',
                              (partida, turno)):
            ali[row[0]] = {k for k in range(8) if row[1 + k] == 0 and k != row[0]}
    return dueño, oro, ali


def analizar(guardada, partida=None, turno=None, ob=None):
    """ob: tabla de obras {(x, y): (tipo, dueño)} en lugar de la de la guardada (para las pruebas)."""
    d = open(os.path.join(tanda.JUEGO, 'SAVES', guardada + '.SAV'), 'rb').read()
    ob = obras(d) if ob is None else ob
    w, h, tierra, clase, camino, cs, final, otros = pasos.detectar(d, todos=True)
    dueño, oro, ali = estado(d, guardada, partida, turno)
    base = componentes(tierra)
    comp_de = {p: k for k, c in enumerate(base) for p in c}
    nom = historia.terrenos(d)
    agua = {p for p in clase if clase[p] == 1 and not camino[p]
            and not nom[casilla(d, *p)[0] & 0x1f][0].lower().startswith('lava')}
    puerto = {p for p in agua if casilla(d, *p)[1] & 0x40}
    # solo ciudades en pie (tamaño > 0), como pasos.py y el juego (mp_scan): una arrasada no se defiende ni amenaza
    celdas = {c['i']: amenaza.celdas(c) for c in ciudades.leer(d) if c['tam']}
    jugando = set(tanda.jugadores(d))
    perfil = {c: v for c, v in tanda.perfiles(guardada).items()}
    info = {c: amenaza.bando(d, c) for c in jugando}
    volando = amenaza.voladores_en_mapa(d)
    exacto = {r['n']: r for r in amenaza.analizar(guardada)[0]} if not partida else {}
    mg = movimiento.grilla(d)
    perf = {c: movimiento.perfiles(d, c) for c in jugando}
    atras = {}                    # (paso, lado, bono): {casilla: puntos hasta el tramo}
    llegan = []                   # (paso, enemigo, ciudad, turnos aproximados, turnos exactos) para el control

    def turnos_ciudad(n, k, zona, seg, e, i):
        """Turnos (aproximados) en que la ciudad i del enemigo e, del lado k, llega al tramo; None si no llega."""
        mejor = None
        for mov, b, _ in perf.get(e, []):
            if (n, k, b) not in atras:
                atras[n, k, b] = hacia_atras(seg, zona | set(seg), mg, b)
            c = min((atras[n, k, b].get(q, 10 ** 6) for q in celdas[i]), default=10 ** 6)
            if c < 10 ** 6:
                t = max(1, -(-c // mov))
                mejor = t if mejor is None else min(mejor, t)
        return mejor

    def turnos_exactos(zona, seg, e, i):
        nodos = zona | set(seg)
        ts = [min((tt[t][0] for t in seg if t in tt), default=None)
              for mov, b, _ in perf.get(e, [])
              for tt in [movimiento.turnos([q for q in celdas[i] if q in nodos], mov, mg, nodos, b)]]
        ts = [t for t in ts if t]
        return min(ts) if ts else None

    pas = []
    for n, (seg, con) in enumerate(final, 1):
        todo = base[comp_de[seg[0]]] - set(seg)
        chico, _ = pasos.separa(todo, seg)
        lados = []
        for zona in (chico, todo - chico):
            ids = [i for i in celdas if any(q in zona for q in celdas[i])]
            vec = {(x + dx, y + dy) for x, y in zona for dx, dy in VEC}
            lados.append({'zona': zona, 'ids': ids, 'costa': bool(vec & agua), 'puerto': bool(vec & puerto),
                          'dist': amenaza.dist([q for t in seg for q in ((t[0] + dx, t[1] + dy) for dx, dy in VEC)
                                                if q in zona], zona)})
        pas.append({'n': n, 'tramo': seg, 'camino': any(camino[t] for t in seg), 'lados': lados,
                    'otros': otros[n - 1]})
    # Criterio v2 (usuario, 20/11/2026): CORREDORES, después de los cortes, como mp_scan (mp_modelo.detectar_v2).
    # No separan: cada lado es lo que queda más cerca de cada boca con el tramo cerrado, y la distancia y el costo
    # hasta el tramo se miden por todo el componente (el enemigo puede llegar dando el rodeo).
    import mp_modelo
    _, _, G, C, mpas, _ = mp_modelo.detectar_v2(d, ob)
    # Desde 1.0.284.0 (usuario, 21/11/2026) los corredores son PUENTES (tipo 2) y PUERTOS (tipo 3); los de terreno
    # (tipo 1) siguen sin elegirse. PUERTO: se protege solo la tierra (lado 1); el otro lado es el mar: las ciudades con
    # puerto a mp_modelo.PRAD casillas o menos, que llegan por barco en un turno (mp_pside).
    for p in mpas:
        if 'corredor' not in p:
            continue
        seg = [mp_modelo.xy(i) for i in p['tramos'][0][1]]
        todo = base[comp_de[seg[0]]] - set(seg)
        vec_t = [q for t in seg for q in ((t[0] + dx, t[1] + dy) for dx, dy in VEC) if q in todo]
        dd = amenaza.dist(vec_t, todo)
        lados = []
        for _, _, cs_ in mp_modelo.lados_corredor(G, C, p['tramos'][0][1], p['corredor'], p['tipo']):
            zona = {mp_modelo.xy(i) for i in cs_}
            ids = [i for i in celdas if any(q in zona for q in celdas[i])]
            vec = {(x + dx, y + dy) for x, y in zona for dx, dy in VEC}
            lados.append({'zona': zona, 'mov': todo, 'ids': ids, 'costa': bool(vec & agua),
                          'puerto': bool(vec & puerto), 'dist': dd})
        if p['tipo'] == 3:
            lados[0].update(ids=sorted(p['mar']), costa=True, puerto=True, mar=True,
                            dist={q: p['mar'][i] for i in p['mar'] for q in celdas[i]})
        pas.append({'n': len(pas) + 1, 'tramo': seg, 'camino': any(camino[t] for t in seg), 'lados': lados,
                    'otros': [seg], 'corredor': True, 'tipo': p['tipo']})

    out = {}
    for p in sorted(jugando):
        r = {'perfil': tanda.nombre_perfil(perfil.get(p, 0) & (ARTIFICER | ENGINEER)), 'oro': oro.get(p, 0),
             'precio': precio(perfil.get(p, 0)), 'constructor': constructor(d, p), 'opciones': []}
        r['cumple'] = bool(perfil.get(p, 0) & (ARTIFICER | ENGINEER)) and r['oro'] >= AW_DIV * r['precio']
        if not any(dueño[i] == p for i in dueño):
            r['eliminado'] = True
        amigos = {p} | ali[p]
        for P in pas:
            # Los corredores de terreno (tipo 1) no se eligen desde 1.0.283.0: tienen rodeo y enemigos de los dos
            # lados (tanda 195). Los de PUENTE y PUERTO sí (regla del usuario, 21/11/2026).
            if P.get('tipo') == 1:
                continue
            # Regla 5, con todos los tramos que cortan las mismas ciudades (pasos.detectar(todos=True)):
            # - uno cerrado entero con MURALLA del bando o de sus aliados: el paso está cerrado, no se elige;
            # - una MURALLA ajena no cambia nada (punto g del usuario, 21/11/2026: «es indiferente que el paso ya tenga
            #   construida una muralla enemiga»): ni adelanta el paso ni descarta el tramo;
            # - se construye en un tramo con alguna casilla vacía y sin obras que no sean MURALLA: primero el ya
            #   empezado, después uno de nuestro lado, después el orden de pasos.py (el más corto, mejor con camino).
            def propio(t):
                return ob.get(t, (0, 9))[0] == OB_MURO and ob[t][1] in amigos
            if any(all(propio(t) for t in tr) for tr in P['otros']):
                continue
            ajena = any(t in ob and ob[t][0] == OB_MURO and ob[t][1] not in amigos for tr in P['otros'] for t in tr)
            libres = [tr for tr in P['otros'] if all(t not in ob or ob[t][0] == OB_MURO for t in tr)
                      and any(t not in ob for t in tr)]
            if not libres:
                continue
            for k, D in enumerate(P['lados']):
                O = P['lados'][1 - k]
                if D.get('mar'):
                    continue
                mias = [i for i in D['ids'] if dueño[i] == p]
                if not mias:
                    continue
                cerca = min(D['dist'].get(q, 10 ** 6) for i in mias for q in celdas[i])
                enem, total = [], 0
                for e in sorted(jugando - {p} - ali[p]):
                    if any(dueño[i] == e for i in D['ids']):
                        continue
                    en_o = 0
                    for i in O['ids']:
                        if dueño[i] != e:
                            continue
                        if O.get('mar'):     # PUERTO: por barco, en un turno, si tiene con qué moverse
                            t = 1 if perf.get(e) else None
                        else:
                            t = turnos_ciudad(P['n'], 1 - k, O.get('mov', O['zona']), P['tramo'], e, i)
                        if CONTROL and (P['n'], e, i) not in {x[:3] for x in llegan}:
                            llegan.append((P['n'], e, i, t, turnos_exactos(O['zona'], P['tramo'], e, i)))
                        en_o += bool(t and t <= HORIZONTE)
                    if not en_o:
                        continue
                    barco, vol = info[e]
                    aire = bool(vol or volando[e])     # se informa, pero ya no anula (punto f, 21/11/2026)
                    if barco == amenaza.RAFT:
                        mar = O['costa'] and D['costa']
                    elif barco == amenaza.LANDING:
                        mar = O['puerto'] and D['costa']
                    else:
                        mar = O['puerto'] and D['puerto']
                    peso = en_o * (1 if mar else 2)
                    total += peso
                    enem.append((e, en_o, 'agua' if mar else '', 'aire' if aire else '', peso))
                if total:
                    tr = min(libres, key=lambda tr: (-sum(map(propio, tr)), not all(t in D['zona'] for t in tr)
                                                     and tr != P['tramo'], P['otros'].index(tr)))
                    r['opciones'].append({'paso': P['n'], 'tramo': tr, 'lado': 'chico' if k == 0 else 'grande',
                                          'mias': len(mias), 'cerca': cerca, 'amenaza': total, 'enemigos': enem,
                                          'lejos': cerca > MP_DIST, 'hechos': sum(map(propio, tr)), 'ajena': ajena})
        r['opciones'].sort(key=lambda o: (o['lejos'], not o['hechos'], -o['amenaza'], o['cerca'],
                                          len(o['tramo'])))
        out[p] = r
    # control del agua simplificado contra el cálculo exacto de amenaza.py (solo con los dueños de la guardada)
    difiere = []
    for n, rr in exacto.items():
        for lado in rr['lados']:
            for dfn in lado['defensores']:
                for e in dfn['enemigos']:
                    simple = next((x for o in out[dfn['color']]['opciones'] if o['paso'] == n
                                   for x in o['enemigos'] if x[0] == e['color']), None)
                    if simple and bool(simple[2]) != e['por_agua']:
                        difiere.append((n, dfn['color'], e['color'], simple[2], e['por_agua']))
    return out, pas, difiere, llegan


def empezado(o):
    return ((f", empezado ({o['hechos']} de {len(o['tramo'])})" if o['hechos'] else '') +
            (f", MURALLA ajena, se cierra en {list(o['tramo'])}" if o['ajena'] else ''))


def informe(guardada, partida=None, turno=None):
    out, pas, difiere, llegan = analizar(guardada, partida, turno)
    print(f'{guardada}' + (f', partida {partida}, turno {turno}' if partida else ' (al empezar)') +
          f': {len(pas)} pasos')
    for p, r in out.items():
        if r.get('eliminado'):
            print(f'\n color {p}: eliminado')
            continue
        cond = (f"{r['perfil']}, oro {r['oro']}, bloque {r['precio']} (mínimo {AW_DIV * r['precio']}), constructor: "
                f"{', '.join(r['constructor']) or 'ninguno'}")
        elige = next((o for o in r['opciones'] if not o['lejos']), None)
        if not r['cumple']:
            dec = 'no construye (sin Artificer/Engineer)' if r['perfil'] == 'ninguno' else 'no construye (poco oro)'
        elif not r['constructor']:
            dec = 'no puede construir (sin unidad con «build»)'
        elif not elige:
            dec = 'no construye (ningún paso amenazado a su alcance)'
        else:
            dec = f"cierra el paso {elige['paso']} {list(elige['tramo'])}"
        print(f'\n color {p}: {cond}\n   -> {dec}')
        for o in r['opciones'][:4]:
            en = ', '.join(f"{e} ({c} ciudades{'; rodea ' + ' y '.join(x for x in (a, b) if x) if a or b else ''})"
                           for e, c, a, b, _ in o['enemigos'])
            print(f"   paso {o['paso']:2}: amenaza {o['amenaza']:2}, {o['mias']} ciudades propias del lado {o['lado']}, "
                  f"la más cercana a {o['cerca']} casillas{' (LEJOS)' if o['lejos'] else ''}"
                  f"{empezado(o)}; enemigos: {en}")
    if difiere:
        print('\n agua simplificada distinta de la exacta (paso, defensor, enemigo, simple, exacta):', difiere)
    if CONTROL:
        dentro = lambda t: bool(t and t <= HORIZONTE)
        mal = [x for x in llegan if dentro(x[3]) != dentro(x[4])]
        dif = collections.Counter((x[4] or 0) - (x[3] or 0) for x in llegan if x[3] and x[4])
        print(f'\n control de turnos: {len(llegan)} ciudades enemigas; exacto - aproximado: {dict(sorted(dif.items()))}; '
              f'sin llegar: aprox {sum(not x[3] for x in llegan)}, exacto {sum(not x[4] for x in llegan)}; '
              f'distinto dentro/fuera del horizonte: {len(mal)}' + (f' (p. ej. {mal[:5]})' if mal else ''))


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--control' in a:
        a.remove('--control')
        CONTROL = True
    informe(a[0], int(a[1]) if len(a) > 1 else None, int(a[2]) if len(a) > 2 else None)
