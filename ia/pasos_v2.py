# Pasos estratégicos, criterio v2 (corrección del usuario, 20/11/2026; ia\PENDIENTE-ia-muros.md, punto 3.a):
# «todo puerto o puente es un paso estratégico». pasos.py (v1) solo marcaba los tramos que, cerrados, cortan TODO
# camino por tierra entre dos zonas con ciudades; así dejaba afuera los corredores que tienen rodeo, aunque sea
# largo (el camino del bosque profundo de Scarpart, cuadrante I; los puentes del río central) y no miraba puertos.
# Ni v1 ni v2 miran voladores: si el enemigo de una partida los tiene se decide después, en la elección (mp_pick).
# v2 marca:
#  - CORTE: lo de v1 (cerrado, separa dos zonas con ciudades);
#  - CORREDOR: tramo recto de 1-3 casillas, con terreno intransitable (o borde) en las dos puntas, cuyo cierre
#    obliga a un rodeo de al menos RODEO casillas para pasar de un lado al otro. Cubre puentes (la cabecera:
#    sobre el puente no se construye), caminos de montaña y de bosque;
#  - PUENTE: casillas de tierra con camino en las puntas de cada puente (agua con camino);
#  - PUERTO: casillas de tierra vecinas de un puerto (agua con el bit 0x4000), las que usa quien desembarca.
# No pisa los .json de pasos.py (las tandas 189-191 se analizaron con esa numeración): escribe ia\pasos\<g>_v2.png
# y <g>_v2.json. Uso: python ia\pasos_v2.py Tanda_Scarpart [más guardadas]
import os, sys, json
from collections import deque

import tanda, historia
from muros import casilla, sirve
from pasos import detectar, VEC

RODEO = 24        # casillas: más o menos lo que un grupo camina en un turno


def rodeo(paso, seg, horiz, tope):
    """Pasos (8 direcciones) para ir de las vecinas de un lado del tramo a las del otro, con el tramo cerrado.
    None si no llega en `tope`."""
    s = set(seg)
    if horiz:
        a = {(x + dx, seg[0][1] - 1) for x, _ in seg for dx in (-1, 0, 1)}
        b = {(x + dx, seg[0][1] + 1) for x, _ in seg for dx in (-1, 0, 1)}
    else:
        a = {(seg[0][0] - 1, y + dy) for _, y in seg for dy in (-1, 0, 1)}
        b = {(seg[0][0] + 1, y + dy) for _, y in seg for dy in (-1, 0, 1)}
    a = {p for p in a if p in paso and p not in s}
    b = {p for p in b if p in paso and p not in s}
    if not a or not b:
        return 0                     # no es un paso: de un lado no hay por dónde venir
    dist = {p: 0 for p in a}
    q = deque(a)
    while q:
        p = q.popleft()
        if p in b:
            return dist[p]
        if dist[p] >= tope:
            continue
        for dx, dy in VEC:
            n = (p[0] + dx, p[1] + dy)
            if n in paso and n not in s and n not in dist:
                dist[n] = dist[p] + 1
                q.append(n)
    return None


def detectar_v2(d):
    w, h, paso, clase, camino, cs, cortes = detectar(d)
    celda_ciudad = {(c['x'] + a, c['y'] + b) for c in cs for a in (0, 1) for b in (0, 1)}
    ok = {p for p in paso if sirve(d, *p) and p not in celda_ciudad}
    corr = []
    for (x, y) in ok:
        for L in (1, 2, 3):
            for horiz in (True, False):
                seg = [(x + i, y) if horiz else (x, y + i) for i in range(L)]
                if not all(p in ok for p in seg):
                    continue
                e1 = (x - 1, y) if horiz else (x, y - 1)
                e2 = (x + L, y) if horiz else (x, y + L)
                if e1 in paso or e2 in paso:
                    continue
                r = rodeo(paso, seg, horiz, RODEO)
                if r is None and rodeo(paso, seg, horiz, 4 * RODEO) is not None:
                    corr.append(tuple(seg))   # rodeo largo, pero existe (sin rodeo es un rincón o un CORTE de v1)
    # varios tramos sobre el mismo corredor: un grupo por casillas que se tocan; queda el más corto, con camino
    marcados = {p for sg in cortes for p in sg[0]}
    corr = [sg for sg in corr if not marcados & set(sg)]
    grupos = []
    for sg in sorted(corr, key=lambda s: (len(s), not any(camino[p] for p in s), s)):
        cerca = {(px + dx, py + dy) for px, py in sg for dx in range(-6, 7) for dy in range(-6, 7)}
        if not any(cerca & set(g) for g in grupos):
            grupos.append(sg)
    # puertos
    puertos = []
    for p in clase:
        t = casilla(d, *p)
        if clase[p] == 1 and t[1] & 0x40:
            tierra = sorted((p[0] + dx, p[1] + dy) for dx, dy in VEC if (p[0] + dx, p[1] + dy) in paso
                            and clase[(p[0] + dx, p[1] + dy)] != 1)
            if tierra:
                puertos.append((p, tierra))
    # puentes: agua con camino (sobre el puente no se construye); se marcan las casillas de tierra de sus puntas
    agua_camino = {p for p in clase if clase[p] == 1 and camino[p]}
    puentes = []
    for comp in __import__('pasos').componentes(agua_camino):
        tierra = sorted({(x + dx, y + dy) for x, y in comp for dx, dy in VEC
                         if (x + dx, y + dy) in paso and clase[(x + dx, y + dy)] != 1 and camino[(x + dx, y + dy)]})
        if tierra:
            puentes.append((sorted(comp), tierra))
    return w, h, paso, clase, camino, cs, [c[0] for c in cortes], grupos, puertos, puentes


def dibujar(w, h, paso, clase, camino, cs, cortes, corr, puertos, puentes, bosque, dst):
    from PIL import Image, ImageDraw
    E = 5
    im = Image.new('RGB', (w * E, h * E))
    dr = ImageDraw.Draw(im)
    for (x, y), k in clase.items():
        col = (40, 90, 170) if k == 1 else (45, 45, 45) if k == 5 else (20, 70, 30) if (x, y) in bosque else \
            (110, 100, 90) if k == 4 else (90, 140, 70)
        if camino[x, y]:
            col = (200, 180, 120)
        dr.rectangle([x * E, y * E, x * E + E - 1, y * E + E - 1], fill=col)
    for c in cs:
        col = (255, 255, 255) if c['dueño'] >= 8 else (0, 0, 0)
        dr.rectangle([c['x'] * E, c['y'] * E, c['x'] * E + 2 * E - 1, c['y'] * E + 2 * E - 1], fill=col,
                     outline=(255, 255, 255))
    for p, tierra in puertos:
        for x, y in tierra:
            dr.rectangle([x * E, y * E, x * E + E - 1, y * E + E - 1], fill=(0, 220, 255))
    for comp, tierra in puentes:
        for x, y in tierra:
            dr.rectangle([x * E, y * E, x * E + E - 1, y * E + E - 1], fill=(230, 0, 230))
    n = 0
    for lista, col in ((cortes, (255, 0, 0)), (corr, (255, 140, 0))):
        for seg in lista:
            n += 1
            for x, y in seg:
                dr.rectangle([x * E - 1, y * E - 1, x * E + E, y * E + E], fill=col)
            x, y = seg[0]
            dr.text((x * E + 7, y * E - 4), str(n), fill=(255, 255, 0))
    im = im.resize((w * E * 2, h * E * 2), Image.NEAREST)
    im.save(dst)


if __name__ == '__main__':
    salida = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pasos')
    for g in sys.argv[1:]:
        d = open(os.path.join(tanda.JUEGO, 'SAVES', g + '.SAV'), 'rb').read()
        w, h, paso, clase, camino, cs, cortes, corr, puertos, puentes = detectar_v2(d)
        print(f'{g}: {len(cortes)} cortes (rojo, v1), {len(corr)} corredores (naranja), {len(puertos)} puertos (celeste), {len(puentes)} puentes (violeta)')
        for k, sg in enumerate(corr, len(cortes) + 1):
            print(f'  {k:2}. corredor {list(sg)} {"camino" if any(camino[p] for p in sg) else "sin camino"}')
        nom = historia.terrenos(d)
        bosque = {p for p in clase if clase[p] == 4 and nom[casilla(d, *p)[0] & 0x1f][0] == 'Forest'}
        with open(os.path.join(salida, g + '_v2.json'), 'w', encoding='utf-8') as f:
            json.dump({'cortes': cortes, 'corredores': corr, 'puertos': [{'puerto': p, 'tierra': t} for p, t in puertos],
                       'puentes': [{'puente': c, 'tierra': t} for c, t in puentes]}, f)
        dibujar(w, h, paso, clase, camino, cs, cortes, corr, puertos, puentes, bosque, os.path.join(salida, g + '_v2.png'))
