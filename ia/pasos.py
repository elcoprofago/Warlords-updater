# Detecta pasos clave en el mapa de una guardada (ia\PENDIENTE-ia-muros.md, punto 3.a), sin tocar el juego.
# Paso clave = tramo recto de 1 a 3 casillas de tierra donde se puede poner muralla (muros.sirve) que, cerrado, corta
# TODO camino por tierra entre dos zonas del mapa que tienen ciudades. Es el criterio del usuario (19/11/2026): un
# camino entre montañas o costa, cerrado con un tramo corto de muralla, en vez de un anillo alrededor de una ciudad.
# Vocabulario (CLAUDE.md): MURALLA = lo que se construye; MURO = terreno «Walls» del escenario.
# Transitable por tierra: todo terreno salvo agua (clase 1) y montaña o bosque profundo («Forest», también clase 4)
# sin camino, y el MURO del escenario («Walls», clase 5: Hexagon lo tiene alrededor de los núcleos y en el borde;
# intransitable también por aire; una casilla con camino no es muro, es camino: se pasa, como en el juego,
# 0x4a4f90; usuario 19/11/2026); un puente (agua con
# camino) y un camino de montaña sí (la misma regla del constructor y del desembarco, build.py 0x4a52c3).
# Se mueve en 8 direcciones (como el juego), por eso solo valen tramos horizontales o verticales: uno en diagonal
# deja pasar en zigzag. No mira barcos ni voladores (eso es el punto 3.b), ni grupos que cruzan montañas.
# Uso: python ia\pasos.py Tanda_hex_perfiles [más guardadas]  -> lista y dibuja <guardada>_pasos.png en ia\pasos\
import os, struct, sys, collections

import tanda
import historia
import ciudades
from muros import casilla, sirve, MAPA, TERRENOS
from sin_ruinas import offset

R = 7            # radio de la ventana del filtro local
MIN_LADO = 12    # casillas mínimas de cada lado (descarta rincones)


def grilla(d):
    w, h, _ = struct.unpack('<hhxxB', d[offset(MAPA):][:7])
    clase, camino = {}, {}
    for y in range(h):
        for x in range(w):
            t = casilla(d, x, y)
            wd = int.from_bytes(t[:2], 'little')
            clase[x, y] = int.from_bytes(d[offset(TERRENOS + (wd & 0x1f) * 0x58):][:2], 'little')
            camino[x, y] = t[3] & 7 == 1
    paso = {p for p in clase if clase[p] not in (1, 4, 5) or camino[p]}
    return w, h, paso, clase, camino


def vuelo(d, clase, camino):
    """Casillas donde un volador puede entrar (para el punto 3.b). Igual que el juego con vista-aliada (build.py,
    «Montañas altas: tampoco por aire», pedido del usuario 19/11/2026): todo salvo el MURO del escenario (clase 5) y
    la montaña sin camino ni puente (clase 4 cuyo nombre empieza con «moun»; el bosque profundo, también clase 4, sí
    se sobrevuela). El MURO sin camino tampoco: no lo traspasa nadie (definición del usuario 19/11/2026)."""
    nom = historia.terrenos(d)
    def alta(p):
        return clase[p] == 4 and nom[casilla(d, *p)[0] & 0x1f][0].lower().startswith('moun')
    return {p for p in clase if camino[p] or not (clase[p] == 5 or alta(p))}


VEC = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]


def componentes(nodos):
    nodos, out = set(nodos), []
    while nodos:
        s = nodos.pop(); comp = {s}; q = [s]
        while q:
            x, y = q.pop()
            for dx, dy in VEC:
                n = (x + dx, y + dy)
                if n in nodos:
                    nodos.remove(n); comp.add(n); q.append(n)
        out.append(comp)
    return out


def tramos(paso, ok):
    for (x, y) in sorted(ok):
        for L in (1, 2, 3):
            for dx, dy in ((1, 0), (0, 1)):
                seg = [(x + dx * i, y + dy * i) for i in range(L)]
                if all(s in ok for s in seg) and (L > 1 or dx == 1):
                    yield tuple(seg)


def detectar(d):
    w, h, paso, clase, camino = grilla(d)
    cs = [c for c in ciudades.leer(d) if c['tam']]
    celda_ciudad = {}
    for i, c in enumerate(cs):
        for a in (0, 1):
            for b in (0, 1):
                celda_ciudad[c['x'] + a, c['y'] + b] = i
    ok = {p for p in paso if sirve(d, *p) and p not in celda_ciudad}
    base = componentes(paso)
    comp_de = {p: k for k, c in enumerate(base) for p in c}
    hallados = []
    for seg in tramos(paso, ok):
        cx, cy = seg[len(seg) // 2]
        ven = {p for p in paso if abs(p[0] - cx) <= R and abs(p[1] - cy) <= R} - set(seg)
        borde = [c for c in componentes(ven)
                 if any(abs(p[0] - cx) == R or abs(p[1] - cy) == R for p in c)]
        if len(borde) < 2:
            continue
        # comprobación global: sin el tramo, ¿quedan separadas zonas con ciudades?
        todo = base[comp_de[seg[0]]] - set(seg)
        partes = componentes(todo)
        con = [(len(p), sorted({celda_ciudad[q] for q in p if q in celda_ciudad})) for p in partes]
        con = [c for c in con if c[0] >= MIN_LADO and c[1]]
        if len(con) >= 2:
            hallados.append((seg, con))
    # un paso por corte: tramos que separan las mismas ciudades son el mismo paso; queda el más corto, con
    # preferencia por el que cierra un camino (ahí pasa el enemigo) y, si no, el primero
    por_corte = {}
    for seg, con in hallados:
        chico = min(con, key=lambda c: c[0])
        clave = tuple(sorted(tuple(c[1]) for c in con))
        orden = (len(seg), not any(camino[p] for p in seg))
        if clave not in por_corte or orden < por_corte[clave][0]:
            por_corte[clave] = (orden, seg, con, chico)
    final = [(v[1], v[2]) for v in sorted(por_corte.values(), key=lambda v: (v[3][0], v[1]))]
    return w, h, paso, clase, camino, cs, final


def dibujar(nombre, w, h, paso, clase, camino, cs, final, dst, bosque=()):
    from PIL import Image, ImageDraw
    E = 5
    im = Image.new('RGB', (w * E, h * E))
    dr = ImageDraw.Draw(im)
    for (x, y), k in clase.items():
        col = (40, 90, 170) if k == 1 else (45, 45, 45) if k == 5 else (20, 70, 30) if (x, y) in bosque else (110, 100, 90) if k == 4 else (90, 140, 70)
        if camino[x, y]:
            col = (200, 180, 120)
        dr.rectangle([x * E, y * E, x * E + E - 1, y * E + E - 1], fill=col)
    for c in cs:
        col = (255, 255, 255) if c['dueño'] >= 8 else (0, 0, 0)
        dr.rectangle([c['x'] * E, c['y'] * E, c['x'] * E + 2 * E - 1, c['y'] * E + 2 * E - 1], fill=col,
                     outline=(255, 255, 255))
    for n, (seg, con) in enumerate(final, 1):
        for x, y in seg:
            dr.rectangle([x * E - 1, y * E - 1, x * E + E, y * E + E], fill=(255, 0, 0))
        x, y = seg[0]
        dr.text((x * E + 7, y * E - 4), str(n), fill=(255, 255, 0))
    im = im.resize((w * E * 2, h * E * 2), Image.NEAREST)
    im.save(dst)


if __name__ == '__main__':
    salida = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pasos')
    os.makedirs(salida, exist_ok=True)
    for g in sys.argv[1:]:
        d = open(os.path.join(tanda.JUEGO, 'SAVES', g + '.SAV'), 'rb').read()
        w, h, paso, clase, camino, cs, final = detectar(d)
        print(f'{g}: {w}x{h}, {len(cs)} ciudades, {len(final)} pasos')
        for n, (seg, con) in enumerate(final, 1):
            lados = '; '.join(f'{t} casillas, {len(cc)} ciudades' + (': ' + ', '.join(cs[i]['nombre'] for i in cc)
                              if len(cc) <= 12 else '') for t, cc in sorted(con))
            print(f'  {n:2}. {seg}  {"camino" if any(camino[p] for p in seg) else "sin camino"} | {lados}')
        nom = historia.terrenos(d)
        bosque = {p for p in clase if clase[p] == 4 and nom[casilla(d, *p)[0] & 0x1f][0] == 'Forest'}
        print(f'  ({len(bosque)} casillas de bosque profundo, intransitables salvo con camino)')
        dibujar(g, w, h, paso, clase, camino, cs, final, os.path.join(salida, g + '_pasos.png'), bosque)
