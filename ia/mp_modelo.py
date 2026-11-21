# Modelo en Python de mp_scan, la búsqueda de pasos clave que hace el juego (punto 3.c de ia\PENDIENTE-ia-muros.md).
# Es el mismo algoritmo que build.py escribe en ensamblador, paso por paso y con las mismas estructuras, para dos cosas:
# 1. medir que la versión del juego (cola FIFO por grupo, se expande de a una casilla) da los mismos pasos que
#    ia\pasos.py (que expande capas enteras): `python ia\mp_modelo.py [guardadas]`;
# 2. ser la referencia contra la que se compara el ensamblador en el emulador (ia\prueba_mp_scan.py).
# Vocabulario (CLAUDE.md): MURALLA = lo que se construye; MURO = terreno «Walls» del escenario.
#
# Estructuras (las mismas que en build.py):
# - índice de casilla con borde: i = (x + 1) * MP_P + (y + 1), MP_P = 162 (alto máximo 160 + 2); el borde vale 0 en
#   todas las grillas, así que los recorridos no miran los límites del mapa. Vecinas en el orden de pasos.VEC.
# - MP_G (byte): 1 tierra transitable, 2 candidata (ahí se puede poner MURALLA o ya hay una), 4 vecina de agua (costa),
#   8 vecina de puerto, 0x10 camino, 0x20 puente (camino sobre agua), 0x40 casilla de puerto (agua). MP_C (byte): ciudad + 1 (solo ciudades con tamaño > 0).
# - componentes de tierra (palabra por casilla) con su tamaño y su máscara de ciudades (80 bits).
# - separación de cada tramo: sello por casilla (24 bits de tramo, 8 de grupo; 0xff = casilla del tramo), un grupo por
#   vecina del tramo (hasta 12) con su cola FIFO; se expande una casilla del grupo vivo más chico (a igualdad, el de
#   menor número), sacándola de la primera cola no vacía de sus miembros (los grupos que se le unieron).
import os, sys, struct

import tanda
from muros import casilla, MAPA, TERRENOS
from sin_ruinas import offset

MP_P = 162
MIN_LADO = 12
OB_MURO = 7
VEC = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
DV = [dx * MP_P + dy for dx, dy in VEC]
NOMBRES = 0x535ed6           # nombre de cada terreno (0x58 bytes por terreno), como bd_ok y el puente sobre lava


def idx(x, y):
    return (x + 1) * MP_P + (y + 1)


def xy(i):
    return i // MP_P - 1, i % MP_P - 1


def grilla(d, obras=None):
    """(W, H, G, C, ciudades): las grillas de mp_scan. obras = {(x, y): (tipo, dueño)}."""
    obras = obras or {}
    w, h, _ = struct.unpack('<hhxxB', d[offset(MAPA):][:7])
    G = bytearray((w + 2) * MP_P)
    C = bytearray((w + 2) * MP_P)
    n = int.from_bytes(d[offset(0x537e2a):][:2], 'little')
    for c in range(n):
        r = d[offset(0x537e2c + c * 0xde):][:0xde]
        if r[0xa4]:
            cx, cy = struct.unpack('<hh', r[:4])
            for a in (0, 1):
                for b in (0, 1):
                    if 0 <= cx + a < w and 0 <= cy + b < h:
                        C[idx(cx + a, cy + b)] = c + 1
    clase = lambda t: int.from_bytes(d[offset(TERRENOS + (int.from_bytes(t[:2], 'little') & 0x1f) * 0x58):][:2], 'little')
    agua = bytearray(len(G))
    for x in range(w):
        for y in range(h):
            t = casilla(d, x, y)
            k, road = clase(t), t[3] & 7 == 1
            i = idx(x, y)
            if k not in (1, 4, 5) or road:
                G[i] |= 1
            if road:
                G[i] |= 0x10
                if k == 1:
                    G[i] |= 0x20            # puente: camino sobre agua
            if k == 1 and not road:
                nom = d[offset(NOMBRES + (t[0] & 0x1f) * 0x58):][:4]
                if bytes(b | 0x20 for b in nom) != b'lava':
                    agua[i] = 2 if t[1] & 0x40 else 1
                    if agua[i] == 2:
                        G[i] |= 0x40        # casilla de puerto (en el agua)
            # candidata: ob_okt(OB_MURO) del juego sin obras (pasos.sirve) o ya hay una MURALLA; nunca ciudad
            wd = int.from_bytes(t[:2], 'little')
            ok = not wd & 0x4000 and k != 1 and t[3] & 7 in (0, 1)
            ob = obras.get((x, y))
            if ob:
                ok = ob[0] == OB_MURO
            if G[i] & 1 and ok and not C[i]:
                G[i] |= 2
    for x in range(w):
        for y in range(h):
            i = idx(x, y)
            for dv in DV:
                if agua[i + dv]:
                    G[i] |= 4
                    if agua[i + dv] == 2:
                        G[i] |= 8
    return w, h, G, C


def componentes(w, G, C):
    """(etiqueta por casilla (1..), [tamaño], [máscara de ciudades]) en orden de x, y."""
    lab = [0] * len(G)
    tam, msk = [0], [0]
    for x in range(w + 2):
        for y in range(MP_P):
            s = x * MP_P + y
            if not G[s] & 1 or lab[s]:
                continue
            k = len(tam)
            tam.append(0); msk.append(0)
            lab[s] = k
            pila = [s]
            while pila:
                i = pila.pop()
                tam[k] += 1
                if C[i]:
                    msk[k] |= 1 << (C[i] - 1)
                for dv in DV:
                    j = i + dv
                    if G[j] & 1 and not lab[j]:
                        lab[j] = k
                        pila.append(j)
    return lab, tam, msk


def tramos(w, h, G):
    for x in range(w):
        for y in range(h):
            for L in (1, 2, 3):
                for dd in (MP_P, 1):           # horizontal (x + 1) y después vertical
                    if L == 1 and dd == 1:
                        continue
                    seg = [idx(x, y) + dd * k for k in range(L)]
                    if all(G[s] & 2 for s in seg):
                        yield seg


def separa(G, C, seg):
    """(grupo que se agotó: (tamaño, máscara, casillas) o None, visitas). Igual que el ensamblador."""
    marca = {s: 0xff for s in seg}
    sem = []
    for s in seg:
        for dv in DV:
            j = s + dv
            if G[j] & 1 and j not in marca:
                marca[j] = len(sem)
                sem.append(j)
    n = len(sem)
    cola = [[s] for s in sem]
    cab = [0] * n
    padre = list(range(n))
    tam = [1] * n
    msk = [(1 << (C[s] - 1)) if C[s] else 0 for s in sem]

    def raiz(k):
        while padre[k] != k:
            k = padre[k]
        return k
    vis = 0
    while True:
        vivos = [k for k in range(n) if padre[k] == k]
        if len(vivos) < 2:
            return None, vis
        for k in vivos:
            if all(cab[m] == len(cola[m]) for m in range(n) if raiz(m) == k):
                return (tam[k], msk[k], [c for m in range(n) if raiz(m) == k for c in cola[m]]), vis
        k = min(vivos, key=lambda k: (tam[k], k))
        m = next(m for m in range(n) if raiz(m) == k and cab[m] < len(cola[m]))
        i = cola[m][cab[m]]
        cab[m] += 1
        for dv in DV:
            j = i + dv
            if not G[j] & 1:
                continue
            vis += 1
            g = marca.get(j)
            if g is None:
                marca[j] = k
                cola[k].append(j)
                tam[k] += 1
                if C[j]:
                    msk[k] |= 1 << (C[j] - 1)
            elif g != 0xff:
                r = raiz(g)
                if r != k:
                    padre[r] = k
                    tam[k] += tam[r]
                    msk[k] |= msk[r]


def detectar(d, obras=None):
    """Pasos como los arma mp_scan: [{'tramos': [(orden, seg)...] en orden de hallazgo, 'principal': índice,
    'lados': [(casillas, máscara), (casillas, máscara)] del principal (el chico primero), 'clave'}] en el orden final
    (pasos.py: lado más chico del principal, después el tramo), y las visitas."""
    w, h, G, C = grilla(d, obras)
    lab, ctam, cmsk = componentes(w, G, C)
    pas, por_clave, vis = [], {}, 0
    for seg in tramos(w, h, G):
        r, v = separa(G, C, seg)
        vis += v
        if not r:
            continue
        t, m, _ = r
        k = lab[seg[0]]
        lados = [(t, m), (ctam[k] - len(seg) - t, cmsk[k] & ~m)]
        if not all(c >= MIN_LADO and mm for c, mm in lados):
            continue
        clave = tuple(sorted(mm for _, mm in lados))
        orden = (len(seg), not any(camino_de(d, s) for s in seg))
        if clave not in por_clave:
            por_clave[clave] = len(pas)
            pas.append({'tramos': [], 'principal': 0, 'lados': lados, 'clave': clave})
        p = pas[por_clave[clave]]
        p['tramos'].append((orden, seg))
        if orden < p['tramos'][p['principal']][0]:
            p['principal'] = len(p['tramos']) - 1
            p['lados'] = lados
    for p in pas:
        p['chico'] = min(c for c, _ in p['lados'])     # pasos.py: min(con) por casillas (a igualdad, el primero)
    pas.sort(key=lambda p: (p['chico'], [xy(s) for s in p['tramos'][p['principal']][1]]))
    return w, h, G, C, pas, vis


def camino_de(d, i):
    x, y = xy(i)
    return casilla(d, x, y)[3] & 7 == 1


def otros(p):
    """Los tramos del paso en el orden de pasos.detectar(todos=True): el principal y después por orden (estable)."""
    pr = p['tramos'][p['principal']][1]
    return [pr] + [s for _, s in sorted(p['tramos'], key=lambda o: o[0]) if s != pr]


def comparar(g):
    import pasos
    d = open(os.path.join(tanda.JUEGO, 'SAVES', g + '.SAV'), 'rb').read()
    w, h, paso, clase, camino, cs, final, ot = pasos.detectar(d, todos=True)
    idx_ciudad = {c['i']: k for k, c in enumerate(cs)}       # pasos.py numera solo las ciudades con tamaño
    ref = []
    for (seg, con), oo in zip(final, ot):
        ref.append(([tuple(s) for s in oo], sorted((t, tuple(cc)) for t, cc in con)))
    _, _, G, C, pas, vis = detectar(d)
    mio = []
    for p in pas:
        lados = sorted((t, tuple(sorted(idx_ciudad[c] for c in range(80) if m >> c & 1))) for t, m in p['lados'])
        mio.append(([tuple(xy(s) for s in seg) for seg in otros(p)], lados))
    mal = [(n, a, b) for n, (a, b) in enumerate(zip(ref, mio), 1) if a != b]
    ok = len(ref) == len(mio) and not mal
    print(f'{g}: pasos.py {len(ref)} pasos, modelo {len(mio)}; {sum(len(p["tramos"]) for p in pas)} tramos; '
          f'{vis} visitas; {"IGUALES" if ok else "DISTINTOS"}')
    for n, a, b in mal[:3]:
        print(f'  paso {n}:\n    pasos.py {a}\n    modelo   {b}')
    return ok


if __name__ == '__main__':
    gs = sys.argv[1:] or ['Tanda_hex_perfiles', 'Tanda_Borderlands', 'Tanda_Kor', 'Tanda_Scarpart']
    r = [comparar(g) for g in gs]
    print('TODO OK' if all(r) else 'FALLA')
    sys.exit(0 if all(r) else 1)


# ---- Criterio v2 (ia\pasos_v2.py, confirmado por el usuario el 20/11/2026): CORREDORES.
# Tramo recto de 1-3 candidatas con algo intransitable (o el borde) en las dos puntas, cuyo cierre obliga a un rodeo
# de más de RODEO casillas y de RODEO_MAX o menos (sin rodeo es un rincón o un CORTE de v1). Se ordenan como pasos_v2
# (largo, sin camino, casillas) y se queda uno por zona (a 6 casillas o menos de uno ya elegido, se descarta), sin
# los que pisan el tramo principal de un CORTE. Cada corredor es un paso de un solo tramo, después de los cortes.
# Sus dos lados: cada casilla del componente queda del lado de la boca (fila de un lado del tramo) que tenga más
# cerca, con el tramo cerrado (recorrido FIFO desde las dos bocas a la vez, primero la de arriba / izquierda).
RODEO, RODEO_MAX, ZONA = 24, 96, 6


def bocas(G, seg, dd):
    """(a, b): vecinas transitables de un lado y del otro del tramo, en orden a lo largo del tramo."""
    perp = 1 if dd == MP_P else MP_P
    s = set(seg)
    fila = [seg[0] - dd] + list(seg) + [seg[-1] + dd]
    a = [i - perp for i in fila if G[i - perp] & 1 and i - perp not in s]
    b = [i + perp for i in fila if G[i + perp] & 1 and i + perp not in s]
    return a, b


def rodeo(G, seg, dd, tope=RODEO_MAX):
    """Pasos de una boca a la otra con el tramo cerrado; None si son más de tope; 0 si falta una boca. Devuelve
    también las visitas (vecinas transitables miradas)."""
    a, b = bocas(G, seg, dd)
    if not a or not b:
        return 0, 0
    dist = {i: 0 for i in a}
    for i in seg:
        dist[i] = -1
    fin, q, k, vis = set(b), list(a), 0, 0
    while k < len(q):
        i = q[k]; k += 1
        if i in fin:
            return dist[i], vis
        if dist[i] >= tope:
            continue
        for dv in DV:
            j = i + dv
            if G[j] & 1:
                vis += 1
                if j not in dist:
                    dist[j] = dist[i] + 1
                    q.append(j)
    return None, vis


def puerto(G, seg):
    """La primera casilla de puerto vecina del tramo cuyas vecinas de tierra están todas en el tramo, o 0."""
    for t in seg:
        for dv in DV:
            q = t + dv
            if G[q] & 0x40 and all(not G[q + e] & 1 or q + e in seg for e in DV):
                return q
    return 0


def puente(G, seg):
    return any(G[t + dv] & 0x20 for t in seg for dv in DV)


def corredores(w, h, G, pas):
    """Corredores en el orden de mp_scan: [(seg, dd, tipo, puerto)], y las visitas. Tipo (usuario, 21/11/2026:
    corredor = puerto o puente que se puede rodear): 3 PUERTO (el tramo tapa todas las vecinas de tierra de un puerto),
    2 PUENTE (vecino de un puente; cerrado, el rodeo pasa de RODEO o no aparece dentro de RODEO_MAX), 1 corredor de
    terreno (puntas intransitables y rodeo de más de RODEO). Puertos y puentes van antes que los de terreno."""
    principal = {i for p in pas for i in p['tramos'][p['principal']][1]}
    cand, vis = [], 0
    for seg in tramos(w, h, G):
        dds = (MP_P, 1) if len(seg) == 1 else ((seg[1] - seg[0]),)
        for dd in dds:
            P = puerto(G, seg)
            if P:
                cand.append((seg, dd, 3, P))
                break
            if puente(G, seg):
                r, v = rodeo(G, seg, dd)
                vis += v
                if r is None or r > RODEO:
                    cand.append((seg, dd, 2, 0))
                    break
                continue
            if G[seg[0] - dd] & 1 or G[seg[-1] + dd] & 1:
                continue
            r, v = rodeo(G, seg, dd)
            vis += v
            if r is not None and r > RODEO:
                cand.append((seg, dd, 1, 0))
                break
    cand = [c for c in cand if not principal & set(c[0])]
    cand.sort(key=lambda c: (c[2] == 1, len(c[0]), not any(G[i] & 0x10 for i in c[0]), [xy(i) for i in c[0]]))
    elegidos = []
    for c in cand:
        if not any(max(abs(xy(i)[0] - xy(j)[0]), abs(xy(i)[1] - xy(j)[1])) <= ZONA
                   for e in elegidos for i in e[0] for j in c[0]):
            elegidos.append(c)
    return elegidos, vis


def lados_corredor(G, C, seg, dd, tipo=1):
    """[(tamaño, máscara, casillas)] de cada lado del corredor (0 = boca a, 1 = boca b). PUERTO (tipo 3): toda la
    tierra es del lado 1 (el lado 0, el mar, lo arma ciudades_puerto)."""
    a, b = bocas(G, seg, dd)
    if tipo == 3:   # PUERTO en la punta de una península: la tierra también sigue por las puntas del tramo
        b = b + [i for i in (seg[0] - dd, seg[-1] + dd) if G[i] & 1]
    lado = {i: 0xff for i in seg}
    q = []
    for g, bb in ((0, a), (1, b)):
        for i in bb:
            if i not in lado:
                lado[i] = 1 if tipo == 3 else g
                q.append(i)
    k = 0
    while k < len(q):
        i = q[k]; k += 1
        for dv in DV:
            j = i + dv
            if G[j] & 1 and j not in lado:
                lado[j] = lado[i]
                q.append(j)
    out = []
    for g in (0, 1):
        cs = [i for i in q if lado[i] == g]
        m = 0
        for i in cs:
            if C[i]:
                m |= 1 << (C[i] - 1)
        out.append((len(cs), m, cs))
    return out


PRAD = 24


def ciudades_puerto(d, G, C, P, m1):
    """Lado 0 (el mar) de un PUERTO, como mp_pside: {ciudad: distancia} de las ciudades en pie que no están en m1, con
    una casilla vecina de puerto y a PRAD casillas o menos (Chebyshev desde su esquina) de la casilla de puerto P."""
    w, h = struct.unpack('<hh', d[offset(MAPA):][:4])
    px, py = xy(P)
    out = {}
    n = min(80, int.from_bytes(d[offset(0x537e2a):][:2], 'little', signed=True))
    for c in range(n):
        r = d[offset(0x537e2c + c * 0xde):][:0xde]
        if not r[0xa4] or m1 >> c & 1:
            continue
        cx, cy = struct.unpack('<hh', r[:4])
        if not any(0 <= cx + a < w and 0 <= cy + b < h and C[idx(cx + a, cy + b)] == c + 1
                   and G[idx(cx + a, cy + b)] & 8 for a in (0, 1) for b in (0, 1)):
            continue
        dd = max(abs(cx - px), abs(cy - py))
        if dd <= PRAD:
            out[c] = dd
    return out


def detectar_v2(d, obras=None):
    """detectar() más los corredores al final: cada uno {'tramos': [(orden, seg)], 'principal': 0, 'lados',
    'corredor': dd, 'tipo', 'puerto'} (PUERTO: 'mar' = {ciudad: distancia} del lado 0)."""
    w, h, G, C, pas, vis = detectar(d, obras)
    corr, v2 = corredores(w, h, G, pas)
    for s, dd, tipo, P in corr:
        ld = lados_corredor(G, C, s, dd, tipo)
        lados = [(t, m) for t, m, _ in ld]
        p = {'tramos': [((len(s), not any(G[i] & 0x10 for i in s)), s)], 'principal': 0, 'corredor': dd,
             'tipo': tipo, 'puerto': P}
        if tipo == 3:
            p['mar'] = ciudades_puerto(d, G, C, P, lados[1][1])
            lados[0] = (0, sum(1 << c for c in p['mar']))
        p['lados'] = lados
        pas.append(p)
    return w, h, G, C, pas, vis + v2


def comparar_v2(g):
    import json
    d = open(os.path.join(tanda.JUEGO, 'SAVES', g + '.SAV'), 'rb').read()
    ref = [[tuple(p) for p in s] for s in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                     'pasos', g + '_v2.json')))['corredores']]
    w, h, G, C, pas, vis = detectar(d)
    corr, v = corredores(w, h, G, pas)
    mio = [[xy(i) for i in c[0]] for c in corr if c[2] == 1]
    ok = mio == ref
    print(f'{g}: pasos_v2 {len(ref)} corredores, modelo {len(mio)}; {v} visitas; {"IGUALES" if ok else "DISTINTOS"}')
    if not ok:
        print('  solo pasos_v2:', [s for s in ref if s not in mio][:5])
        print('  solo modelo:  ', [s for s in mio if s not in ref][:5])
    return ok
