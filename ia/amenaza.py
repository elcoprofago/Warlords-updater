# Punto 3.b de ia\PENDIENTE-ia-muros.md: por cada paso clave (ia\pasos.py, ia\pasos\<mapa>.json), quién queda de
# cada lado, qué enemigos llegan por él, a cuántas casillas, y si lo pueden rodear por agua o por aire. Sin tocar el
# juego: lee una guardada. Vocabulario (CLAUDE.md): MURALLA = lo que se construye; MURO = terreno «Walls».
# - Por tierra: distancia en casillas (8 direcciones) desde el paso a la ciudad más cercana de cada bando, por tierra
#   transitable (pasos.grilla).
# - Turnos (ia\movimiento.py, verificado contra el juego): en qué turno llega el enemigo al paso y a la ciudad más
#   cercana del defensor, saliendo de sus ciudades del otro lado al empezar el turno 1, por su lado, el tramo y el
#   nuestro. Con la unidad no voladora más rápida que puede producir, por cada bono de terreno (colinas, pantano o
#   bosque), y se queda con la que llega antes. No cuenta héroes, objetos, el oro del enemigo ni las MURALLAS ya
#   construidas: es el peor caso de un ejército recién producido.
# - Por agua: agua = clase 1 sin camino que no sea lava. El barco de cada bando (ranura 15) con «Landing» sube en un
#   puerto propio y baja en cualquier costa (build.py, LANDING); con «Raft» zarpa y baja en cualquier costa, sin
#   alejarse más de 1 casilla de tierra; sin ninguno de los dos, sube y baja solo en puertos (casilla de agua con el
#   bit 0x4000: el grafo 0x4a4f90 une agua y tierra solo ahí).
# - Por aire: la MURALLA no frena a los voladores. Volador = unidad del bando con tipo +0xe0 == 4 (el criterio de
#   isfly en build.py); se cuentan las que puede producir (sus 16 ranuras) y las que ya tiene en el mapa. Se mira si
#   llegan volando (pasos.vuelo: ni MURO ni montaña sin camino) desde sus ciudades a las del otro lado.
# Uso: python ia\amenaza.py Tanda_hex_perfiles [pasos de otra guardada del mismo mapa, p. ej. Tanda_Scarpart]
import os, sys, json, collections

import tanda
import ciudades
import historia
from intercambiar import EJERCITOS_N, EJERCITOS, EJ_TAM
from muros import casilla
import movimiento
from pasos import grilla, vuelo, VEC, componentes
from sin_ruinas import offset

LANDING, RAFT, VOLADOR = 'landing', 'raft', 4
BONOS = {1: 'pantano/bosque', 2: 'colinas', 3: 'colinas y pantano/bosque'}


def bando(d, c):
    """(barco: 'landing' | 'raft' | '', nombres de las unidades voladoras que puede producir)."""
    barco, vol = '', []
    for s in range(16):
        u = tanda.SAV_BANDOS + (c * 16 + s) * tanda.UNIDAD
        r = d[u:u + tanda.UNIDAD]
        if not r[:1].isalpha():
            continue
        bonos = [r[0xb2 + k * 9:0xbb + k * 9].split(b'\0')[0].decode('latin-1').lower() for k in range(4)]
        if s == 15:
            barco = LANDING if LANDING in bonos else RAFT if RAFT in bonos else ''
        if r[0xe0] == VOLADOR:
            vol.append(r[:16].split(b'\0')[0].decode('latin-1'))
    return barco, vol


def voladores_en_mapa(d):
    """{color: cantidad de ejércitos voladores (no héroes) en el mapa}."""
    out = collections.Counter()
    n = int.from_bytes(d[offset(EJERCITOS_N):][:2], 'little')
    for i in range(n):
        p = offset(EJERCITOS + i * EJ_TAM)
        if d[p + 9] != 0xff:
            continue
        w = int.from_bytes(d[p + 0xc:p + 0xe], 'little')
        ranura, dueño = w & 0x1f, w >> 5 & 0xf
        if ranura < 16 and dueño < 8:
            u = tanda.SAV_BANDOS + (dueño * 16 + ranura) * tanda.UNIDAD
            if d[u + 0xe0] == VOLADOR:
                out[dueño] += 1
    return out


def aliados(guardada):
    eq = tanda.alianzas(guardada).split(';')[0]
    out = collections.defaultdict(set)
    if eq.startswith('equipos '):
        for e in eq[8:].split('|'):
            for c in e:
                out[int(c)] |= {int(x) for x in e} - {int(c)}
    return out


def dist(origen, nodos):
    """Distancia en casillas (8 direcciones) desde las casillas origen, sin salir de nodos."""
    q, dd = collections.deque(origen), {p: 0 for p in origen}
    while q:
        x, y = q.popleft()
        for dx, dy in VEC:
            n = (x + dx, y + dy)
            if n in nodos and n not in dd:
                dd[n] = dd[x, y] + 1
                q.append(n)
    return dd


def celdas(c):
    return [(c['x'] + a, c['y'] + b) for a in (0, 1) for b in (0, 1)]


def analizar(guardada, mapa=None):
    d = open(os.path.join(tanda.JUEGO, 'SAVES', guardada + '.SAV'), 'rb').read()
    pasos = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pasos',
                                        (mapa or guardada) + '.json'), encoding='utf-8'))
    w, h, tierra, clase, camino = grilla(d)
    aire = vuelo(d, clase, camino)
    nom = historia.terrenos(d)
    agua = {p for p in clase if clase[p] == 1 and not camino[p]
            and not nom[casilla(d, *p)[0] & 0x1f][0].lower().startswith('lava')}
    seco = {p for p in clase if clase[p] != 1 or camino[p]}
    costa_agua = {p for p in agua if any((p[0] + dx, p[1] + dy) in seco for dx, dy in VEC)}
    cuerpo = {p: k for k, c in enumerate(componentes(agua)) for p in c}           # mares y ríos
    orilla = {p: k for k, c in enumerate(componentes(costa_agua)) for p in c}     # por donde anda la balsa
    # puertos: casillas de agua con el bit 0x4000 de la palabra 0 (el grafo 0x4a4f90 une ahí agua y tierra)
    puerto = {p: cuerpo[p] for p in cuerpo if casilla(d, *p)[1] & 0x40}
    cvuelo = {p: k for k, c in enumerate(componentes(aire)) for p in c}
    cs = {c['i']: c for c in ciudades.leer(d)}
    jugando = set(tanda.jugadores(d))
    info = {c: bando(d, c) for c in jugando}
    volando = voladores_en_mapa(d)
    ali = aliados(guardada)
    mg = movimiento.grilla(d)
    perf = {c: movimiento.perfiles(d, c) for c in jugando}

    def vecinas(casillas, conj):
        return {conj[(x + dx, y + dy)] for x, y in casillas for dx, dy in VEC if (x + dx, y + dy) in conj}

    out = []
    for n, p in enumerate(pasos, 1):
        tramo = [tuple(t) for t in p['tramo']]
        sin = tierra - set(tramo)
        dd = dist([q for t in tramo for q in ((t[0] + dx, t[1] + dy) for dx, dy in VEC) if q in sin], sin)
        lados = []
        for lado in p['lados']:
            ids = lado['ciudades']
            # casillas de tierra de este lado: las alcanzables sin el tramo desde una de sus ciudades
            alc = dist([q for q in celdas(cs[ids[0]]) if q in sin], sin)
            lados.append((ids, set(alc)))
        res = {'n': n, 'tramo': tramo, 'camino': any(camino[t] for t in tramo), 'lados': []}
        viajes = {}
        for k, (ids, zona) in enumerate(lados):
            otro_ids, otra = lados[1 - k] if len(lados) == 2 else ([], set())
            nodos = otra | set(tramo) | zona
            dueños = collections.Counter(cs[i]['dueño'] for i in ids)
            enemigos = collections.Counter(cs[i]['dueño'] for i in otro_ids)
            costa = {q for q in zona if any((q[0] + dx, q[1] + dy) in agua for dx, dy in VEC)}
            defensores = []
            for dfn in sorted(c for c in dueños if c < 8):
                cerca = min(dd.get(q, 10**6) for i in ids if cs[i]['dueño'] == dfn for q in celdas(cs[i]))
                ame = []
                for e in sorted(c for c in enemigos if c < 8 and c != dfn and c not in ali[dfn]):
                    suyas = [i for i in otro_ids if cs[i]['dueño'] == e]
                    lejos = min(dd.get(q, 10**6) for i in suyas for q in celdas(cs[i]))
                    barco, vol = info.get(e, ('', []))
                    if barco == RAFT:       # de costa a costa, sin alejarse más de 1 casilla de tierra
                        por_agua = bool(vecinas(otra, orilla) & vecinas(zona, orilla))
                    elif barco == LANDING:  # sube en un puerto de su lado, baja en cualquier costa
                        por_agua = bool(vecinas(otra, puerto) & vecinas(zona, cuerpo))
                    else:                   # de puerto a puerto
                        por_agua = bool(vecinas(otra, puerto) & vecinas(zona, puerto))
                    llega_vuelo = bool({cvuelo.get(q) for i in suyas for q in celdas(cs[i])} &
                                       {cvuelo.get(q) for i in ids if cs[i]['dueño'] == dfn for q in celdas(cs[i])}
                                       - {None})
                    if (k, e) not in viajes:     # una vez por lado y enemigo: [(mov, bono, nombre, {casilla: (turno, resto)})]
                        origen = [q for i in suyas for q in celdas(cs[i])]
                        viajes[k, e] = [(m, b, nm, movimiento.turnos(origen, m, mg, nodos, b)) for m, b, nm in perf.get(e, [])]
                    blanco = [q for i in ids if cs[i]['dueño'] == dfn for q in celdas(cs[i])]
                    mejor = None
                    for m, b, nm, tt in viajes[k, e]:
                        al_paso = min((tt[t][0] for t in tramo if t in tt), default=None)
                        a_ciudad = min((tt[q][0] for q in blanco if q in tt), default=None)
                        clave = (a_ciudad or 10**6, al_paso or 10**6)
                        if a_ciudad and (mejor is None or clave < mejor[0]):
                            mejor = (clave, {'paso': al_paso, 'ciudad': a_ciudad, 'unidad': nm, 'mov': m, 'bono': b})
                    ame.append({'color': e, 'ciudades': len(suyas), 'casillas': lejos, 'barco': barco,
                                'turnos': mejor and mejor[1],
                                'por_agua': por_agua, 'voladores': vol, 'volando': volando[e],
                                'por_aire': llega_vuelo and bool(vol or volando[e])})
                defensores.append({'color': dfn, 'ciudades': dueños[dfn], 'casillas': cerca, 'enemigos': ame})
            res['lados'].append({'ciudades': len(ids), 'neutrales': dueños.get(8, 0), 'costa': len(costa), 'puertos': sum(any((x + dx, y + dy) in zona for dx, dy in VEC) for x, y in puerto),
                                 'defensores': defensores})
        out.append(res)
    return out, ali


def informe(guardada, mapa=None):
    out, ali = analizar(guardada, mapa)
    print(f'{guardada}: {len(out)} pasos; aliados: {tanda.alianzas(guardada)}')
    for r in out:
        print(f"\n{r['n']:2}. tramo {r['tramo']} ({'camino' if r['camino'] else 'sin camino'})")
        for k, l in enumerate(r['lados']):
            print(f"   lado {'AB'[k]}: {l['ciudades']} ciudades ({l['neutrales']} neutrales), {l['costa']} casillas de costa, {l['puertos']} puertos")
            for dfn in l['defensores']:
                print(f"     defiende {dfn['color']} ({dfn['ciudades']} ciudades, la más cercana a {dfn['casillas']} casillas"
                      f" del paso)")
                for e in sorted(dfn['enemigos'], key=lambda e: (e['turnos'] or {}).get('ciudad', 10**6)):
                    rodea = [t for t, v in (('por agua (' + (e['barco'] or 'barco común, de puerto a puerto') + ')', e['por_agua']),
                                            ('por aire', e['por_aire'])) if v]
                    t = e['turnos']
                    tx = (f"llega al paso en el turno {t['paso']} y a la ciudad en el {t['ciudad']} ({t['unidad']}, "
                          f"mov {t['mov']}{', bono ' + BONOS[t['bono']] if t['bono'] else ''})" if t
                          else 'no llega por tierra')
                    print(f"       enemigo {e['color']}: {e['ciudades']} ciudades del otro lado, la más cercana a "
                          f"{e['casillas']} casillas; {tx}; " + ('lo rodea ' + ' y '.join(rodea) if rodea
                                                          else 'no lo rodea: la muralla lo frena')
                          + (f"; voladores: {', '.join(e['voladores'])} ({e['volando']} en el mapa)"
                             if e['voladores'] or e['volando'] else ''))


if __name__ == '__main__':
    informe(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
