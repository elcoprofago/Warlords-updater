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
#   8 vecina de puerto. MP_C (byte): ciudad + 1 (solo ciudades con tamaño > 0).
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
            if k == 1 and not road:
                nom = d[offset(NOMBRES + (t[0] & 0x1f) * 0x58):][:4]
                if bytes(b | 0x20 for b in nom) != b'lava':
                    agua[i] = 2 if t[1] & 0x40 else 1
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
