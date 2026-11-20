# Prueba de mp_scan / mp_pick (punto 3.c de ia\PENDIENTE-ia-muros.md) en el emulador de simcombate\motor.py:
# 1. pasos: los que arma el juego (orden, tramos en orden de hallazgo, principal, lados con su tamaño y sus ciudades)
#    contra ia\mp_modelo.py, que da los mismos que ia\pasos.py;
# 2. por paso y ciudad: distancia en casillas al tramo y costo de movimiento con cada bono, contra amenaza.dist y
#    cerrar_paso.hacia_atras sobre cada lado; costa y puerto de cada lado; de qué lado queda cada tramo;
# 3. la elección de cada color (mp_obj y el evento 51) contra cerrar_paso.analizar;
# 4. controles (lo que tiene que cambiar la elección): sin Artificer/Engineer, sin oro, sin unidad con «build», tabla de
#    obras llena (ninguna candidata), tramo cerrado con MURALLA propia (el paso no se elige), MURALLA ajena (va primero),
#    y el caché: sin cambios no recalcula; con una obra nueva, sí.
# Uso: python ia\prueba_mp_scan.py [exe] [guardadas...]   (exe por defecto: el instalado en la carpeta de pruebas)
# Vocabulario (CLAUDE.md): MURALLA = lo que se construye; MURO = terreno «Walls» del escenario.
import os, sys, struct, time, collections, tempfile, builtins

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'simcombate'))
import tanda
import amenaza
import movimiento
import ciudades
import cerrar_paso
import mp_modelo
from mp_modelo import idx, xy, MP_P
from motor import Motor, STK, RET
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EBX

SIDE = 0x1f8
PERS, ORO = 0x536bf0, 0x536c14
ARTIFICER, ENGINEER = 0x80000, 0x40000
OB_MURO = 7


class Juego:
    def __init__(self, exe, g):
        self.g = g
        sav = FORZADAS.get(g) or os.path.join(tanda.JUEGO, 'SAVES', g + '.SAV')
        self.d = open(sav, 'rb').read()
        self.m = Motor(exe, sav, rul=os.path.join(tanda.JUEGO, 'Default.rul'))
        # Motor solo carga [COMBAT]; el precio de la MURALLA (bd_price) sale de BuildCity ([0x56950e]), que está en
        # otra sección del .rul: sin esto queda en 0, el precio en 1 y la condición de oro no se prueba.
        for ln in open(os.path.join(tanda.JUEGO, 'Default.rul'), encoding='latin-1'):
            if ln.strip().lower().startswith('buildcity='):
                self.m.mu.mem_write(0x56950e, struct.pack('<h', int(ln.split('=', 1)[1])))
        img = open(exe, 'rb').read()
        import pefile
        pe = pefile.PE(data=img)
        o = img.find(b'MPSYM\0\0\0')
        assert o > 0, 'este exe no tiene mp_scan'
        va = pe.get_rva_from_offset(o) + pe.OPTIONAL_HEADER.ImageBase
        (self.scan, self.pick, self.grid, self.sep, self.bss, self.G, self.C, self.PAS, self.TR, self.PC, self.ORD,
         self.VAR, self.OBJ, self.E, self.LAB, self.K) = struct.unpack('<16I', bytes(self.m.mu.mem_read(va + 8, 64)))
        # la entrada de ia_evt: para ver el evento 51 sin escribir archivos
        self.eventos = []

    def var(self, k):
        return struct.unpack('<I', bytes(self.m.mu.mem_read(self.VAR + 4 * k, 4)))[0]

    def llamar(self, addr, ebx=0):
        mu = self.m.mu
        sp = STK + 0x80000 - 4
        mu.mem_write(sp, struct.pack('<I', RET))
        mu.reg_write(UC_X86_REG_ESP, sp)
        mu.reg_write(UC_X86_REG_EBX, ebx)
        self.m.fallo = None
        mu.emu_start(addr, RET, count=4_000_000_000)
        if self.m.fallo:
            raise RuntimeError(f'{addr:#x}: {self.m.fallo}')
        assert mu.reg_read(UC_X86_REG_ESP) == sp + 4, 'la pila no quedó igual'

    def pasos(self):
        """[(q, {principal, tramos [(celdas, orden, flags)], lados [(tamaño, máscara)], banderas})] en el orden de ORD."""
        mu = self.m.mu
        np_, nt = self.var(1), self.var(2)
        tr = [struct.unpack('<HBBBBH', bytes(mu.mem_read(self.TR + 8 * k, 8))) for k in range(nt)]
        out = []
        for j in range(np_):
            q = struct.unpack('<I', bytes(mu.mem_read(self.ORD + 4 * j, 4)))[0]
            r = bytes(mu.mem_read(self.PAS + 64 * q, 64))
            ma, mb = int.from_bytes(r[:16], 'little'), int.from_bytes(r[16:32], 'little')
            sa, sb, pr = struct.unpack_from('<III', r, 32)
            ts = []
            for k, (c, L, v, o, f, pq) in enumerate(tr):
                if pq == q:
                    dd = 1 if v else MP_P
                    ts.append((k, [c + dd * i for i in range(L)], o, f))
            out.append((q, {'principal': pr, 'tramos': ts, 'lados': [(sa, ma), (sb, mb)], 'banderas': (r[45], r[46])}))
        return out

    def pc(self, q):
        b = bytes(self.m.mu.mem_read(self.PC + q * 20 * 80, 20 * 80))
        return [struct.unpack_from('<5I', b, 20 * i) for i in range(80)]


# Variante «forzada» de una guardada (g + '_F'): todos los colores que juegan con Artificer y 5000 de oro, y «build» en
# la ranura 0 del que no tiene constructor, para que haya colores que elijan. Va a una carpeta temporal; el emulador la
# carga desde ahí y cerrar_paso, tanda y amenaza la leen por el mismo nombre (open redirigido en esos módulos).
FORZADAS = {}
_open = builtins.open


def _abrir(f, *a, **k):
    b = os.path.basename(str(f))
    if b.endswith('.SAV') and b[:-4] in FORZADAS:
        f = FORZADAS[b[:-4]]
    return _open(f, *a, **k)


for _m in (cerrar_paso, tanda, amenaza):
    _m.open = _abrir
_amenaza_analizar = amenaza.analizar


def _amenaza(guardada, mapa=None):
    """El control de agua exacto de cerrar_paso necesita ia/pasos/<guardada>.json: sin él (variantes forzadas), vacío."""
    try:
        if not mapa:   # el mapa sin los sufijos de las variantes (_F forzada, _BD/_BDA/_BDSV de constructores.py)
            mapa = guardada.removesuffix('_F')
            for suf in ('_BDA', '_BDSV', '_BD'):
                mapa = mapa.removesuffix(suf)
        return _amenaza_analizar(guardada, mapa)
    except FileNotFoundError:
        return [], None


amenaza.analizar = _amenaza


def forzar(g):
    d = bytearray(_open(os.path.join(tanda.JUEGO, 'SAVES', g + '.SAV'), 'rb').read())
    for c, o in tanda.jugadores(bytes(d)).items():
        v = int.from_bytes(d[o + tanda.PERFIL:o + tanda.PERFIL + 3], 'little') | ARTIFICER
        d[o + tanda.PERFIL:o + tanda.PERFIL + 3] = v.to_bytes(3, 'little')
        d[o + cerrar_paso.ORO:o + cerrar_paso.ORO + 4] = struct.pack('<i', 5000)
        if not cerrar_paso.constructor(bytes(d), c):
            u = tanda.SAV_BANDOS + c * 16 * tanda.UNIDAD
            if d[u:u + 1].isalpha():
                d[u + 0xb2 + 3 * 9:u + 0xb2 + 4 * 9] = b'build'.ljust(9, bytes(1))
    f = os.path.join(tempfile.gettempdir(), 'prueba_mp_scan_' + g + '_F.SAV')
    _open(f, 'wb').write(d)
    FORZADAS[g + '_F'] = f
    return g + '_F'


def comparar_pasos(J, obras=None):
    """Punto 1 y 2. Devuelve (ok, pasos del juego)."""
    ok = True
    w, _, G, C, pas, vis = mp_modelo.detectar_v2(J.d, obras)
    jp = J.pasos()
    gj = bytes(J.m.mu.mem_read(J.G, len(G)))
    if any((a & 0xf) != (b & 0xf) for a, b in zip(gj, G)):
        mal = [(xy(i), a, b) for i, (a, b) in enumerate(zip(gj, G)) if (a & 0xf) != (b & 0xf)]
        print(f'   grilla distinta en {len(mal)} casillas, p. ej. {mal[:4]}')
        ok = False
    if len(jp) != len(pas):
        print(f'   pasos: juego {len(jp)}, modelo {len(pas)}')
        return False, jp
    mg = movimiento.grilla(J.d)
    cs = [c for c in ciudades.leer(J.d)]
    nmal = 0
    for n, ((q, a), b) in enumerate(zip(jp, pas), 1):
        segs = [s for _, s, _, _ in a['tramos']]
        prin = [k for k, (t, _, _, _) in enumerate(a['tramos']) if t == a['principal']]
        if segs != [s for _, s in b['tramos']] or prin != [b['principal']] or a['lados'] != [tuple(x) for x in b['lados']]:
            print(f'   paso {n}: juego {[[xy(c) for c in s] for s in segs][:4]} lados {a["lados"]}\n'
                  f'           modelo {[[xy(c) for c, in [s[:1]]] for _, s in b["tramos"]][:4]} lados {b["lados"]}')
            ok = False
            continue
        # lados del principal, con el modelo: el grupo agotado es el lado 0
        seg = b['tramos'][b['principal']][1]
        lab, _, _ = mp_modelo.componentes(w, G, C)
        comp = {xy(i) for i in range(len(G)) if lab[i] == lab[seg[0]]}
        sg = [xy(i) for i in seg]
        if 'corredor' in b:
            # corredor: lados por la boca más cercana; distancias y costos por todo el componente
            l0, l1 = mp_modelo.lados_corredor(G, C, seg, b['corredor'])
            z0, z1 = {xy(i) for i in l0[2]}, {xy(i) for i in l1[2]}
        else:
            (_, _, celdas0), _ = mp_modelo.separa(G, C, seg)
            z0 = {xy(i) for i in celdas0}
            z1 = comp - z0 - set(sg)
        agua = {xy(i) for i in range(len(G)) if not G[i] & 1}
        pcs = J.pc(q)
        for k, z in enumerate((z0, z1)):
            vec = {(x + dx, y + dy) for x, y in z for dx, dy in mp_modelo.VEC}
            ban = a['banderas'][k]
            costa = any(G[idx(*p)] & 4 for p in z)
            puerto = any(G[idx(*p)] & 8 for p in z)
            if bool(ban & 4) != costa or bool(ban & 8) != puerto:
                print(f'   paso {n} lado {k}: costa/puerto juego {ban & 12:#x}, Python {costa}/{puerto}')
                ok = False
            zd = comp - set(sg) if 'corredor' in b else z
            dist = amenaza.dist([q2 for t in sg for q2 in ((t[0] + dx, t[1] + dy) for dx, dy in mp_modelo.VEC)
                                 if q2 in zd], zd)
            atras = [cerrar_paso.hacia_atras(sg, zd | set(sg), mg, bb) for bb in range(4)]
            for c in cs:
                if not c['tam']:
                    continue
                cel = [p for p in amenaza.celdas(c) if p in z]
                if not cel:
                    continue
                if 'corredor' in b:
                    cel = amenaza.celdas(c)     # la ciudad entera, como cerrar_paso (puede tocar los dos lados)
                esp = (min(dist.get(p, 0xffffffff) for p in cel),) + tuple(min(at.get(p, 0xffffffff) for p in cel) for at in atras)
                if tuple(pcs[c['i']]) != esp:
                    nmal += 1
                    if nmal <= 4:
                        print(f'   paso {n} ciudad {c["i"]} lado {k}: juego {pcs[c["i"]]}, Python {esp}')
                    ok = False
        # de qué lado queda cada tramo
        for t, s, o, f in a['tramos']:
            cel = {xy(i) for i in s}
            esp = 0 if t == a['principal'] else (1 if cel <= z0 else 0) | (2 if cel <= z1 else 0)
            if f != esp:
                print(f'   paso {n} tramo {[xy(i) for i in s]}: lado juego {f}, Python {esp}')
                ok = False
    return ok, jp


def eleccion(J, jp, p):
    """(paso n, tramo [(x, y)], lado k) o None, del mp_obj[p] del juego."""
    v = struct.unpack('<i', bytes(J.m.mu.mem_read(J.OBJ + 4 * p, 4)))[0]
    if v < 0:
        return None
    q, k, r = v & 0xff, v >> 8 & 0xff, v >> 16
    n = next(n for n, (qq, _) in enumerate(jp, 1) if qq == q)
    s = next(s for t, s, _, _ in jp[n - 1][1]['tramos'] if t == r)
    return n, [xy(i) for i in s], k


def esperado(out, p):
    r = out.get(p)
    if not r or r.get('eliminado') or not r['cumple'] or not r['constructor']:
        return None
    e = next((o for o in r['opciones'] if not o['lejos']), None)
    if not e:
        return None
    return e['paso'], [tuple(t) for t in e['tramo']], 0 if e['lado'] == 'chico' else 1, e['amenaza']


def picks(J, jp, out, etiqueta, colores=range(8)):
    ok = True
    res = {}
    for p in colores:
        J.llamar(J.pick, p)
        a, b = eleccion(J, jp, p), esperado(out, p)
        res[p] = a
        if (a is None) != (b is None) or (a and b and a != b[:3]):
            print(f'   {etiqueta} color {p}: juego {a}, cerrar_paso {b}')
            ok = False
    return ok, res


def probar(exe, g):
    t0 = time.time()
    J = Juego(exe, g)
    J.llamar(J.scan)
    t1 = time.time()
    if not J.var(0) & 0xff:
        print(f'{g}: mp_scan no terminó (MP_OK = 0)')
        return False
    ok, jp = comparar_pasos(J)
    vis, full = J.var(8), J.var(24)
    print(f'{g}: {len(jp)} pasos, {J.var(2)} tramos, {vis} visitas, {t1 - t0:.1f} s; pasos, lados, distancias y '
          f'costos {"IGUALES" if ok else "DISTINTOS"}' + (' (TABLA DE PASOS LLENA)' if full else ''))
    out, cpas = cerrar_paso.analizar(g)[:2]
    ok2, base = picks(J, jp, out, 'elección')
    print(f'   elección de cada color: {"IGUAL" if ok2 else "DISTINTA"} a cerrar_paso: '
          + ', '.join(f'{p}: paso {a[0]} lado {a[2]}' if a else f'{p}: nada' for p, a in base.items()
                      if p in out and not out[p].get('eliminado')))
    ok &= ok2
    # caché: otro mp_scan sin cambios no recalcula
    n0 = J.var(29)
    J.llamar(J.scan)
    cache = J.var(29) == n0
    print(f'   caché sin cambios: {"no recalcula" if cache else "RECALCULA"}')
    ok &= cache
    elegidos = [p for p, a in base.items() if a]
    if not elegidos:
        print('   (ningún color elige: sin controles de elección en este mapa)')
        return ok
    p = elegidos[0]
    n, tramo, k = base[p]
    mu = J.m.mu

    def control(nombre, cambia, deshace):
        cambia()
        J.llamar(J.pick, p)
        a = eleccion(J, jp, p)
        deshace()
        bien = a is None
        print(f'   control {nombre} (color {p}): {"no construye" if bien else "ELIGE " + str(a)}')
        return bien
    pers = bytes(mu.mem_read(PERS + p * SIDE, 4))
    oro = bytes(mu.mem_read(ORO + p * SIDE, 4))
    ok &= control('sin Artificer/Engineer', lambda: mu.mem_write(PERS + p * SIDE, struct.pack(
        '<I', struct.unpack('<I', pers)[0] & ~(ARTIFICER | ENGINEER))), lambda: mu.mem_write(PERS + p * SIDE, pers))
    ok &= control('sin oro', lambda: mu.mem_write(ORO + p * SIDE, bytes(4)), lambda: mu.mem_write(ORO + p * SIDE, oro))
    # sin «build»: se borra la palabra en las 16 ranuras del color
    bandos = 0x53c410 + p * 16 * 0xfc
    orig = bytes(mu.mem_read(bandos, 16 * 0xfc))
    sin = bytearray(orig)
    for s in range(16):
        for b in range(4):
            o = s * 0xfc + 0xb2 + b * 9
            if sin[o:o + 9].split(b'\0')[0].lower() == b'build':
                sin[o:o + 9] = bytes(9)
    ok &= control('sin unidad con «build»', lambda: mu.mem_write(bandos, bytes(sin)), lambda: mu.mem_write(bandos, orig))
    # tabla de obras llena: ob_okt rechaza todo -> ninguna candidata (salvo MURALLAS, que no hay) -> ningún paso
    omap, tab = J.m.ob
    n_orig = bytes(mu.mem_read(tab - 4, 4))
    ok &= control('tabla de obras llena', lambda: mu.mem_write(tab - 4, struct.pack('<I', 512)),
                  lambda: mu.mem_write(tab - 4, n_orig))
    J.llamar(J.scan)
    J.llamar(J.scan)
    G0 = mp_modelo.grilla(J.d)[2:4]

    def murallas(nombre, p, celdas, dueño, espera):
        """Pone MURALLAS de dueño en celdas (en lugar de la tabla de la guardada) y compara pasos y elección de p;
        espera(a) dice si la elección es la buscada. El caché recalcula solo si cambia la grilla."""
        obras = {}
        mu.mem_write(omap, bytes(J.m.obw * 0x32000 // 10))
        for i, (x, y) in enumerate(celdas):
            mu.mem_write(tab + 8 * i, struct.pack('<hhBBBB', x, y, OB_MURO, 0, dueño, 0))
            mu.mem_write(omap + J.m.obw * ((y << J.m.sh) + x), struct.pack('<H', i + 1)[:J.m.obw])
            obras[x, y] = (OB_MURO, dueño)
        mu.mem_write(tab - 4, struct.pack('<I', len(celdas)))
        n0 = J.var(29)
        J.llamar(J.scan)
        rec = (J.var(29) != n0) == (mp_modelo.grilla(J.d, obras)[2:4] != G0)
        okp, jp2 = comparar_pasos(J, obras)
        out2 = cerrar_paso.analizar(g, ob=obras)[0]
        oke, r2 = picks(J, jp2, out2, nombre, [p])
        a = r2[p]
        bien = espera(a)
        print(f'   control {nombre} {celdas} (color {p}, dueño {dueño}): caché {"bien" if rec else "MAL"}, '
              f'pasos {"iguales" if okp else "DISTINTOS"}, elige {"paso %d lado %d" % (a[0], a[2]) if a else "nada"} '
              f'{"= cerrar_paso" if oke else "DISTINTO de cerrar_paso"}{"" if bien else " (NO ES LO ESPERADO)"}')
        mu.mem_write(omap, J.m.obmap0)
        mu.mem_write(tab - 4, J.m.obtab0)
        J.llamar(J.scan)
        return rec and okp and oke and bien
    # MURALLA propia en todo el tramo elegido: el paso queda cerrado y se elige otro o nada
    ok &= murallas('MURALLA propia en el tramo', p, tramo, p, lambda a: not a or a[0] != n)
    # MURALLA ajena (o un bloque propio: tramo empezado) en un paso que no es el elegido y que conserva un tramo
    # libre: ese paso pasa adelante
    def otro_paso(nombre, cual):
        for q in elegidos:
            ali = {q} | set(amenaza.aliados(g)[q])
            dueño = next(c for c in range(8) if c not in ali) if cual == 'ajeno' else q
            for o in out[q]['opciones']:
                if o['lejos'] or o['paso'] == base[q][0]:
                    continue
                otros = cpas[o['paso'] - 1]['otros']
                # una casilla que deja otro tramo libre y que no es por sí sola un tramo (si no, el paso queda cerrado)
                t = next((t for tr in otros for t in tr if any(t not in tr2 for tr2 in otros)
                          and all(tuple(tr2) != (t,) for tr2 in otros)), None)
                if t:
                    return murallas(nombre, q, [t], dueño, lambda a, n2=o['paso']: a and a[0] == n2)
        print(f'   ({nombre}: ningún color con una segunda opción)')
        return True
    for nombre, cual in (('MURALLA ajena en otro paso', 'ajeno'), ('tramo empezado en otro paso', 'propio')):
        ok &= otro_paso(nombre, cual)
    return ok


if __name__ == '__main__':
    args = sys.argv[1:]
    exe = os.path.join(tanda.JUEGO, 'DarklordAV.exe')
    if args and args[0].lower().endswith('.exe'):
        exe = args.pop(0)
    gs = args or ['Tanda_hex_perfiles', 'Tanda_Borderlands', 'Tanda_Kor', 'Tanda_Scarpart', 'build_01', 'roads02',
                  'agua04']
    gs = gs + [forzar(g) for g in gs]
    r = [probar(exe, g) for g in gs]
    print('TODO OK' if all(r) else 'FALLA')
    sys.exit(0 if all(r) else 1)
