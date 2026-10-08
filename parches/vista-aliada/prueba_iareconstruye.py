# Prueba de juguete: la IA reconstruye puentes con la meta 9 del juego (la de reconstruir ciudades muertas), en unicorn.
# - El evaluador entero de ciudades muertas (0x41e290, con ai_brrebev en 0x41e4eb) contra un modelo en Python: qué
#   ciudades y puentes considera, con qué valor y costo (las líneas de depuración que arma) y cuál queda en la tabla de
#   candidatos ([0x5032e6]). Control: sin puentes derribados da lo mismo que Darklord.exe original.
# - La meta 9 (0x40dbf0, con ai_brreb) para un puente: va a la cabecera y lo repone con la orden de red 0x4b9ce0; con
#   una ciudad sigue por el código original.
# - Los nombres de los textos de la meta 9 (0x40ce24, 0x41f30c).
# Uso: python prueba_iareconstruye.py [DarklordAV.exe] [Darklord.exe] [casos al azar]
#      (por defecto C:\Warlords3\DarklordAV.exe y el original C:\Warlords3\Darklord.exe; armar antes con build.py)
# Corren de verdad: br_* y ai_brs, la distancia entre ciudades (0x4974a0), la hostilidad (0x49c1c0), el costo de
# reconstruir (0x4b65e0 con br_cost) y el mapa de caminos de la IA (0x4a65d0, sobre una grilla del banco). Van
# guionados y se anotan: la legalidad de la ciudad (0x41e580), el enemigo más cercano (0x497a90), las oportunidades
# (0x41d640, 0x41ec20), el azar (0x4deb20), el descuento (0x4057a0), el generador de nombres (0x4374a0), sprintf
# ([0x5a9bec]), el registro (0x427520), la pausa (0x4275b0), el movimiento (0x4973f0, 0x40d2b0), la orden de red
# (0x4b9ce0) y el fin de la pila (0x40d230).
import sys, math, random, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
from keystone import Ks, KS_ARCH_X86, KS_MODE_32

def load(path):
    pe = pefile.PE(path)
    return pe.OPTIONAL_HEADER.ImageBase, bytes(pe.get_memory_mapped_image()), (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
AV = load(sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe')
ORIG = load(sys.argv[2] if len(sys.argv) > 2 else r'C:\Warlords3\Darklord.exe')
NRAND = int(sys.argv[3]) if len(sys.argv) > 3 else 600

W = H = 64; SHIFT = 8; LAND, WATER, MOUNT = 2, 3, 5
AI, ENEMY, FRIEND = 2, 3, 4
HERO = 1
BC = lambda x, y: 0x2000 + (y << 7) + x
# Puentes del banco (casillas de agua, 4-conexas): el código es el de la casilla menor.
BRIDGES = {'A': [(20, 10), (21, 10)], 'B': [(40, 30), (40, 31)], 'C': [(10, 50), (11, 50), (12, 50)]}
PA = BRIDGES['A']; CA = BC(*PA[0])
BASE = 300                                      # [0x56950e]: el costo de fundar una ciudad
STUB = 0x100000; STACK = 0x200000; END = 0x1fff00
GRID = 0x300000; PLAN = 0x30c000
SPRINTF = STUB + 0x200; FTOL = STUB + 0x100
STUBS = {0x41e580: 'legal', 0x497a90: 'enemigo', 0x41d640: 'opa', 0x41ec20: 'opb', 0x4deb20: 'azar',
         0x4057a0: 'descuento', 0x4374a0: 'nombre', SPRINTF: 'sprintf', 0x427520: 'registro', 0x4275b0: 'pausa',
         0x4973f0: 'meta', 0x40d2b0: 'mover', 0x4b9ce0: 'reponer', 0x40d230: 'fin'}
F_LINE, F_BEST = 0x4f9edc, 0x4f9e7c
NAME = 'Belgor Bridge'

FTOL_CODE = bytes(Ks(KS_ARCH_X86, KS_MODE_32).asm('''
    sub esp, 12
    fnstcw word ptr [esp + 8]
    mov ax, word ptr [esp + 8]
    or ax, 0xc00
    mov word ptr [esp + 10], ax
    fldcw word ptr [esp + 10]
    fistp qword ptr [esp]
    fldcw word ptr [esp + 8]
    mov eax, dword ptr [esp]
    mov edx, dword ptr [esp + 4]
    add esp, 12
    ret''', FTOL)[0])

def tile_va(x, y): return ((y * 10) << SHIFT) + x * 10 + 0x503e58
def kd(a, b): return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

def caso(**kw):
    c = dict(bridges={'A': 'razed'}, stack=(10, 10), gold=1000, disc=0, temp=3, r=3, dip={}, cities=[], armies=[],
             legal=None, enemy={}, opp={}, unreach=set(), mount={}, road=set(), mpass=0, move='ok', plan9=False)
    c.update(kw); return c

class Bench:
    def __init__(self, c, exe=AV):
        base, img, size = exe
        mu = self.mu = Uc(UC_ARCH_X86, UC_MODE_32)
        mu.mem_map(base, size); mu.mem_write(base, img[:size])
        mu.mem_map(STUB, 0x10000); mu.mem_map(STACK - 0x10000, 0x10000); mu.mem_map(GRID, 0x10000)
        self.c = c
        mu.mem_write(0x503e00, struct.pack('<HH', W, H)); mu.mem_write(0x503e06, bytes([SHIFT]))
        for t, cls in ((LAND, 0), (WATER, 1), (MOUNT, 4)):
            mu.mem_write(0x535f0c + t * 0x58, struct.pack('<H', cls))
        for y in range(H):
            for x in range(W): self.set_tile(x, y, LAND, 0, 0x05)
        for xy, t in c['mount'].items(): self.set_tile(*xy, t, 0, 0x05)
        for xy in c['road']: mu.mem_write(0x57d158 + xy[0] * 0xa0 + xy[1], bytes([0x10]))
        mu.mem_write(0x4fe688, bytes([c['mpass']]))
        for k, st in c['bridges'].items():
            for x, y in BRIDGES[k]:
                if st == 'razed': self.set_tile(x, y, WATER, 0, 0x85)
                else: self.set_tile(x, y, WATER, 1, 0x05)
        mu.mem_write(0x537ce8, struct.pack('<h', AI)); mu.mem_write(0x4fb0ec, struct.pack('<h', AI))
        for p in range(8):
            mu.mem_write(0x536c12 + p * 0x1f8, struct.pack('<hi', 0, c['gold'] if p == AI else 0))
            mu.mem_write(0x561ef9 + p * 0x49a, bytes([c['temp'] if p == AI else 0]))
        mu.mem_write(0x56950e, struct.pack('<hh', BASE, 500))
        mu.mem_write(0x560e52, struct.pack('<h', 0))
        for q in range(9): mu.mem_write(0x55ee4c + AI * 56 + q, bytes([c['dip'].get(q, 2)]))
        # ciudades: (x, y, viva, dueño)
        mu.mem_write(0x537e2a, struct.pack('<h', len(c['cities'])))
        for i, (x, y, alive, owner) in enumerate(c['cities']):
            o = i * 0xde
            mu.mem_write(0x537e2c + o, struct.pack('<hh', x, y)); mu.mem_write(0x537e30 + o, b'Ciudad%d\0' % i)
            mu.mem_write(0x537ed0 + o, bytes([alive, owner]))
        # ejércitos: el líder (1) en la pila y los del caso ((x, y), dueño)
        arm = [(HERO, c['stack'], AI)] + [(2 + i, xy, o) for i, (xy, o) in enumerate(c['armies'])]
        mu.mem_write(0x54fe50, struct.pack('<h', 1 + len(arm)))
        for a, (x, y), owner in arm:
            r = a * 0x1c
            mu.mem_write(0x54fe52 + r, struct.pack('<hh', x, y))
            mu.mem_write(0x54fe5e + r, struct.pack('<H', owner << 5))
            mu.mem_write(0x54fe63 + r, bytes([0x40]))
        # mapa de caminos de la IA (0x4a65d0): costo kd + 1 desde la pila, 0 (sin camino) en las casillas del caso
        mu.mem_write(0x4fe670 + AI, bytes([1])); mu.mem_write(0x587168 + AI * 4, struct.pack('<I', GRID))
        g = bytearray(128 * 160 * 2)
        for y in range(H):
            for x in range(W):
                if (x, y) not in c['unreach']: struct.pack_into('<h', g, (x * 160 + y) * 2, kd(c['stack'], (x, y)) + 1)
        mu.mem_write(GRID, bytes(g))
        mu.mem_write(PLAN, struct.pack('<8h', 0, 0, 0, 9 if c['plan9'] else 0, 0, 0, HERO, 0))
        mu.mem_write(0x5020d4, struct.pack('<I', PLAN))
        mu.mem_write(0x5032e6, struct.pack('<hhh', 0x777, 0x777, 0x777))
        self.calls = []; self.lines = []
        for va in STUBS: mu.mem_write(va, b'\xc3')
        mu.mem_write(FTOL, FTOL_CODE); mu.mem_write(0x5a9ba8, struct.pack('<I', FTOL))
        mu.mem_write(0x5a9bec, struct.pack('<I', SPRINTF))
        mu.mem_write(END, b'\xf4')
        for va in STUBS: mu.hook_add(UC_HOOK_CODE, self.stub, begin=va, end=va)

    def set_tile(self, x, y, w0, struct_, b9):
        t = tile_va(x, y)
        self.mu.mem_write(t, struct.pack('<H', w0)); self.mu.mem_write(t + 3, bytes([struct_]))
        self.mu.mem_write(t + 9, bytes([b9]))

    def arg(self, k):
        esp = self.mu.reg_read(UC_X86_REG_ESP)
        return struct.unpack('<i', self.mu.mem_read(esp + 4 + 4 * k, 4))[0]
    def sarg(self, k): return struct.unpack('<h', struct.pack('<H', self.arg(k) & 0xffff))[0]
    def cstr(self, va): return bytes(self.mu.mem_read(va, 64)).split(b'\0')[0].decode('latin-1')
    def leader(self): return struct.unpack('<hh', self.mu.mem_read(0x54fe52 + HERO * 0x1c, 4))

    def stub(self, uc, addr, size, _):
        k = STUBS[addr]; s = self.sarg; c = self.c; ret = 0
        if k == 'legal': ret = 1 if c['legal'] is None or s(0) in c['legal'] else 0
        elif k == 'enemigo': ret = c['enemy'].get((s(0), s(1)), 99)
        elif k in ('opa', 'opb'): ret = c['opp'].get((s(0), s(1)), (0, 0))[k == 'opb'] & 0xffff
        elif k == 'azar': self.calls.append((k, s(0), s(1))); ret = c['r']
        elif k == 'descuento': ret = c['disc']
        elif k == 'nombre':
            uc.mem_write(self.arg(1), NAME.encode() + b'\0'); ret = 1
        elif k == 'sprintf':
            fmt = self.arg(1)
            if fmt == F_LINE: self.lines.append(('linea',) + tuple(self.arg(2 + i) for i in range(4))
                                                + (self.cstr(self.arg(6)),))
            elif fmt == F_BEST: self.lines.append(('mejor', self.arg(2), self.arg(3), self.cstr(self.arg(4))))
            else: self.lines.append(('otro', fmt))
        elif k == 'registro': pass
        elif k == 'meta': self.calls.append((k,) + tuple(s(i) for i in range(4)))
        elif k == 'mover':
            xy = (s(0), s(1)); self.calls.append((k,) + xy); m = c['move']
            if m in ('ok', 'die'): uc.mem_write(0x54fe52 + HERO * 0x1c, struct.pack('<hh', *xy))
            if m == 'die': uc.mem_write(0x54fe63 + HERO * 0x1c, bytes([0]))
            ret = 0 if m == 'fail' else 1
        elif k == 'reponer': self.calls.append((k, s(0), s(1), s(2)))
        else: self.calls.append(k)
        uc.reg_write(UC_X86_REG_EAX, ret)

    def run(self, start, frame, regs, stops):
        mu = self.mu
        esp = STACK - 0x400
        mu.mem_write(esp, frame + bytes(0x40))
        for k, v in regs.items(): mu.reg_write(globals()['UC_X86_REG_' + k], v)
        mu.reg_write(UC_X86_REG_ESP, esp)
        self.end = None; hs = []
        def stop(uc, addr, size, _):
            self.end = addr; uc.emu_stop()
        for va in set(stops) | {END}: hs.append(mu.hook_add(UC_HOOK_CODE, stop, begin=va, end=va))
        mu.emu_start(start, 0, count=50000000)
        for h in hs: mu.hook_del(h)
        self.esp0 = esp
        return self.end
    def reg(self, k): return self.mu.reg_read(globals()['UC_X86_REG_' + k])
    def table(self): return struct.unpack('<hhh', self.mu.mem_read(0x5032e6, 6))
    def plan(self): return struct.unpack('<hh', self.mu.mem_read(PLAN + 6, 4))

REGS = dict(EAX=0x11111111, ECX=0x22222222, EDX=0x33333333, EBX=0x44444444, ESI=0x55555555, EDI=0x66666666,
            EBP=0x77777777)
def saved(b): return all(b.reg(k) == REGS[k] for k in ('EBX', 'ESI', 'EDI', 'EBP'))

def ev(c, exe=AV):
    """0x41e290(x, y de la pila) entero, hasta su ret."""
    b = Bench(c, exe)
    end = b.run(0x41e290, struct.pack('<Iii', END, *c['stack']), REGS, ())
    ok = end == END and b.reg('ESP') == b.esp0 + 4 and saved(b)
    return dict(ok=ok, table=b.table(), lines=b.lines, calls=b.calls)

# ---- modelo del evaluador
def tdiv(a, b): q = abs(a) // abs(b); return q if (a >= 0) == (b > 0) else -q
def cost(c): return BASE + tdiv(BASE * c['disc'], -10)
def edist(a, b): return int(math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2))
def hostile(q, dip): return q != AI and (q == 8 or dip.get(q, 2) == 2)
def brs(c, p0):
    """ai_brs(código, AI, 1) como en prueba_iarazea: c + s, o None si la ciudad dueña lo descarta."""
    t = c['temp']; s = (-2 if t == 0 else 0) + 1
    live = [(i, ct) for i, ct in enumerate(c['cities']) if ct[2]]
    if live:
        owner = min(live, key=lambda ic: (kd(p0, ic[1][:2]), ic[0]))[1][3]
        if owner != 8:
            if not hostile(owner, c['dip']): return None
            s += 1
    for i, (x, y, _, o) in sorted(live, key=lambda ic: (edist(p0, ic[1][:2]), ic[0]))[:12]:
        d = edist(p0, (x, y))
        if d == 0 or d > 30: continue
        w = 2 if d < 15 else 1
        if o == AI: s -= w
        elif o != 8 and hostile(o, c['dip']): s += w
    k = sum(1 for _, ct in live if ct[3] == AI)
    return t + s + (k > 5) + (k > 15)
def tiles_of(c, kind):
    return [xy for k, st in c['bridges'].items() if st == kind for xy in BRIDGES[k]]
def heads(c, tiles):
    """Las cabeceras del puente con su clave de br_head."""
    bt = set(tiles_of(c, 'razed') + tiles_of(c, 'intact'))
    out = {}
    for x, y in tiles:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                h = (x + dx, y + dy)
                if (dx, dy) == (0, 0) or not (0 <= h[0] < W and 0 <= h[1] < H) or h in bt: continue
                t = c['mount'].get(h)
                if t == WATER or t == MOUNT and not c['mpass'] and h not in c['road']: continue
                if h == c['stack']: key = 0
                elif h not in c['unreach']: key = kd(c['stack'], h) + 1
                else: key = 0x10000 + kd(c['stack'], h)
                out[h] = key
    return out
def model_ev(c):
    lim = 15 if c['temp'] == 0 else 30
    best = [-1, -1, -1]                         # valor, costo, índice
    lines = []
    def opp(xy): a, b = c['opp'].get(xy, (0, 0)); return a + b
    for i in reversed(range(len(c['cities']))):
        x, y, alive, _ = c['cities'][i]
        if alive or (c['legal'] is not None and i not in c['legal']): continue
        d = 0 if (x, y) in c['unreach'] else kd(c['stack'], (x, y)) + 1
        if d == 0: continue
        e = c['enemy'].get((x, y), 99)
        if lim > e: continue
        v = max(0, 50 - d) + 2 * opp((x, y)) + c['r']
        if v > best[0]: best = [v, d, i]
        lines.append(('linea', v, d, opp((x, y)), e, f'Ciudad{i}'))
    for k in sorted((k for k, st in c['bridges'].items() if st == 'razed'), key=lambda k: BC(*BRIDGES[k][0])):
        tl = BRIDGES[k]; p0 = tl[0]; code = BC(*p0)
        if c['stack'] in tl or any(xy in tl for xy, _ in c['armies']): continue
        if cost(c) > c['gold']: continue
        hk = heads(c, tl)
        d = min(hk.values(), default=0x7fffffff)
        if d >= 0x10000: continue
        d = max(d, 1)
        e = c['enemy'].get(p0, 99)
        if lim > e: continue
        s = brs(c, p0)
        if s is not None and s >= 5: continue
        o = opp(p0)
        if o <= 0: continue
        v = max(0, 50 - d) + 2 * o + c['r']
        lines.append(('linea', v, d, o, e, NAME))
        if v > best[0]: best = [v, d, code]
    if best[2] >= 0x2000: lines.append(('mejor', 1, best[1], NAME))
    elif best[2] >= 0: lines.append(('mejor', 1, best[1], f'Ciudad{best[2]}'))
    table = (best[2], best[1], 1) if best[2] >= 0 else (0x777, 0x777, 0x777)
    return table, lines

res = []
def check(nombre, cond, detalle=''):
    res.append(cond); print(f'{"OK " if cond else "MAL"} {nombre}' + (f'   [{detalle}]' if not cond and detalle else ''))

def named(nombre, esperado=None, **kw):
    """esperado: la tabla que tiene que quedar (código, costo, 1), o None si ninguna (queda 0x777)."""
    c = caso(**kw); g = ev(c); t, lines = model_ev(c)
    want = esperado if esperado is not None else (0x777, 0x777, 0x777)
    check(nombre, g['ok'] and g['table'] == t == want and g['lines'] == lines, f'modelo {t} {lines} banco {g}')
    return g

OPP = {PA[0]: (1, 1)}
# Pila en (10,10): la cabecera más a mano del puente A es (19,9)/(19,10)/(19,11), a 9 de rey: costo 10.
g = named('base: puente A derribado, alcanzable, con algo que ganar', (CA, 10, 1), opp=OPP)
check('base: una línea por el puente y la de "es el mejor", con su nombre', len(g['lines']) == 2 and
      g['lines'][0] == ('linea', 40 + 4 + 3, 10, 2, 99, NAME), g['lines'])
g = ev(caso(opp=OPP), ORIG)
check('control: Darklord.exe original en el mismo caso no lo considera', g['ok'] and g['table'] == (0x777,) * 3
      and g['lines'] == [] and g['calls'] == ['pausa'], g)   # la pausa del final la hace siempre
named('puente entero: no es candidato', None, opp=OPP, bridges={'A': 'intact'})
named('sin puentes', None, opp=OPP, bridges={})
named('nada que ganar (0 + 0)', None)
named('oportunidades -1 + 1 = 0', None, opp={PA[0]: (-1, 1)})
named('oportunidades 1 + 0', (CA, 10, 1), opp={PA[0]: (1, 0)})
named('oportunidades en la otra casilla del puente no cuentan', None, opp={PA[1]: (3, 3)})
# vacío
named('ejército enemigo sobre el puente', None, opp=OPP, armies=[(PA[1], ENEMY)])
named('ejército propio sobre el puente', None, opp=OPP, armies=[(PA[0], AI)])
named('ejércitos en la cabecera (control)', (CA, 10, 1), opp=OPP, armies=[((22, 10), ENEMY), ((19, 10), AI)])
# oro: 300 sin descuento, 240 con descuento 2 (300 + 300 * 2 / -10)
named('oro = costo', (CA, 10, 1), opp=OPP, gold=300)
named('oro = costo - 1', None, opp=OPP, gold=299)
named('descuento 2: oro 240 alcanza', (CA, 10, 1), opp=OPP, gold=240, disc=2)
named('descuento 2: oro 239 no', None, opp=OPP, gold=239, disc=2)
# cabecera
named('pila en la cabecera: costo 1', (CA, 1, 1), opp=OPP, stack=(19, 10))
named('pila del otro lado', (CA, 10, 1), opp=OPP, stack=(31, 10))
named('sin camino a ninguna cabecera', None, opp=OPP,
      unreach={(x, y) for x in (19, 20, 21, 22) for y in (9, 10, 11)})
named('sin camino a las del oeste: va por (20,9), a 11', (CA, 11, 1), opp=OPP,
      unreach={(19, 9), (19, 10), (19, 11)})
named('cabeceras de agua alrededor: no hay cabecera', None, opp=OPP,
      mount={(x, y): WATER for x in (19, 20, 21, 22) for y in (9, 10, 11) if (x, y) not in PA})
named('montañas sin camino al oeste: va por (20,9)', (CA, 11, 1), opp=OPP,
      mount={(19, 9): MOUNT, (19, 10): MOUNT, (19, 11): MOUNT})
named('montañas con camino', (CA, 10, 1), opp=OPP, mount={(19, 9): MOUNT, (19, 10): MOUNT, (19, 11): MOUNT},
      road={(19, 10)})
named('montañas pisables', (CA, 10, 1), opp=OPP, mount={(19, 9): MOUNT, (19, 10): MOUNT, (19, 11): MOUNT}, mpass=1)
# enemigo cerca: límite 30, o 15 con temperamento 0
named('enemigo a 30 (= límite)', (CA, 10, 1), opp=OPP, enemy={PA[0]: 30})
named('enemigo a 29', None, opp=OPP, enemy={PA[0]: 29})
named('temperamento 0: enemigo a 15 pasa', (CA, 10, 1), opp=OPP, enemy={PA[0]: 15}, temp=0)
named('temperamento 0: enemigo a 14 no', None, opp=OPP, enemy={PA[0]: 14}, temp=0)
# no reponer lo que derribaría (ai_brs con bandera: el peor caso)
ENEMY_CITY = (23, 12, 1, ENEMY)
named('ciudad enemiga dueña y cerca: 3 + 1 + 1 + 2 = 7, lo derribaría', None, opp=OPP, cities=[ENEMY_CITY])
named('temperamento 1, ciudad enemiga lejos: 1 + 1 + 1 + 1 = 4', (CA, 10, 1), opp=OPP, temp=1,
      cities=[(36, 10, 1, ENEMY)])
named('temperamento 2, ciudad enemiga lejos: 5, lo derribaría', None, opp=OPP, temp=2, cities=[(36, 10, 1, ENEMY)])
named('ciudad dueña propia: nunca lo derribaría', (CA, 10, 1), opp=OPP, cities=[(23, 12, 1, AI), (30, 10, 1, ENEMY)])
named('ciudad dueña aliada', (CA, 10, 1), opp=OPP, cities=[(23, 12, 1, FRIEND), (25, 12, 1, ENEMY)], dip={FRIEND: 0})
named('dueña neutral, sin otras: 3 + 1 = 4', (CA, 10, 1), opp=OPP, cities=[(23, 12, 1, 8)])
named('dueña neutral y enemiga cerca: 6', None, opp=OPP, cities=[(23, 12, 1, 8), (26, 12, 1, ENEMY)])
# contra ciudades muertas (las del original)
DEAD = (12, 10, 0, ENEMY)                       # a 2 de la pila: costo 3, valor 47 + 3 = 50 > 47
named('ciudad muerta cerca gana', (0, 3, 1), opp=OPP, cities=[DEAD])
named('ciudad muerta lejos pierde', (CA, 10, 1), opp=OPP, cities=[(50, 50, 0, ENEMY)])
named('ciudad muerta ilegal no cuenta', (CA, 10, 1), opp=OPP, cities=[DEAD], legal=set())
named('empate 48 a 48: queda el primero (la ciudad)', (0, 5, 1), opp={BRIDGES['B'][0]: (1, 1)},
      cities=[(52, 40, 0, ENEMY)], stack=(48, 40), bridges={'B': 'razed'})
# varios puentes
CB = BC(*BRIDGES['B'][0]); CC = BC(*BRIDGES['C'][0])
named('dos derribados: gana el de más valor (B, lejos pero con más oportunidades)', (CB, 30, 1),
      opp={PA[0]: (1, 1), BRIDGES['B'][0]: (10, 10)}, bridges={'A': 'razed', 'B': 'razed'})
g = named('tres derribados: una línea por puente (el de 3 casillas, desde la menor)', (CC, 1, 1),
          opp={PA[0]: (1, 1), BRIDGES['B'][0]: (1, 1), BRIDGES['C'][0]: (1, 1)},
          bridges={'A': 'razed', 'B': 'razed', 'C': 'razed'}, stack=(12, 49))
check('tres derribados: 3 líneas y la del mejor', [l[0] for l in g['lines']] == ['linea'] * 3 + ['mejor'], g['lines'])
named('oportunidades en otra casilla del de 3 no cuentan', None, opp={BRIDGES['C'][1]: (1, 1)},
      bridges={'C': 'razed'})
named('B derribado y A entero', (CB, 30, 1), opp={PA[0]: (1, 1), BRIDGES['B'][0]: (1, 1)},
      bridges={'A': 'intact', 'B': 'razed'})

# ---- control: sin puentes derribados, igual que el original
rng = random.Random(7)
def rnd_cities(n, avoid):
    out = []
    for _ in range(n):
        while True:
            xy = (rng.randrange(64), rng.randrange(64))
            if xy not in avoid: break
        out.append(xy + (rng.choice([0, 0, 1]), rng.choice([AI, ENEMY, FRIEND, 5, 8])))
    return out
ALLB = {xy for t in BRIDGES.values() for xy in t}
same = 0; nc = 60
for n in range(nc):
    cities = rnd_cities(rng.randrange(0, 25), ALLB)
    c = caso(bridges={k: rng.choice(['intact', None]) for k in BRIDGES}, cities=cities,
             stack=(rng.randrange(64), rng.randrange(64)), temp=rng.choice([0, 1, 3]), r=rng.randrange(1, 7),
             legal={i for i in range(len(cities)) if rng.random() < .8},
             enemy={ct[:2]: rng.choice([5, 14, 15, 29, 30, 99]) for ct in cities},
             opp={ct[:2]: (rng.randrange(-2, 4), rng.randrange(-2, 4)) for ct in cities},
             unreach={ct[:2] for ct in cities if rng.random() < .2})
    c['bridges'] = {k: v for k, v in c['bridges'].items() if v}
    a, o = ev(c), ev(c, ORIG)
    if a['ok'] and a == o and (a['table'], a['lines']) == model_ev(c): same += 1
    elif same == n: print('DIFIERE', a, o, c)
check(f'control: sin puentes derribados, {nc} casos al azar iguales al original y al modelo', same == nc,
      f'iguales {same}')

# ---- al azar contra el modelo
bad = 0; cnt = {'puente': 0, 'ciudad': 0, 'nada': 0}
for n in range(NRAND):
    br = {k: rng.choice(['razed', 'razed', 'intact', None]) for k in BRIDGES}
    br = {k: v for k, v in br.items() if v}
    cities = rnd_cities(rng.randrange(0, 20), ALLB)
    keys = [ct[:2] for ct in cities] + [t[0] for t in BRIDGES.values()] + [t[1] for t in BRIDGES.values()]
    near = [(x + dx, y + dy) for t in BRIDGES.values() for x, y in t for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
    near = [h for h in near if h not in ALLB]
    c = caso(bridges=br, cities=cities,
             stack=rng.choice([(rng.randrange(64), rng.randrange(64)), rng.choice(near)]),
             gold=rng.choice([1000, 300, 299, 240, 0]), disc=rng.choice([0, 0, 2, -1]),
             temp=rng.choice([0, 1, 2, 3, 4]), r=rng.randrange(1, 7),
             dip={q: rng.choice([0, 1, 2, 2]) for q in range(8)},
             armies=[(rng.choice(list(ALLB) + near), rng.choice([AI, ENEMY])) for _ in range(rng.choice([0, 0, 1, 2]))],
             legal={i for i in range(len(cities)) if rng.random() < .8},
             enemy={xy: rng.choice([5, 14, 15, 29, 30, 99, 99]) for xy in keys},
             opp={xy: (rng.randrange(-2, 5), rng.randrange(-2, 5)) for xy in keys},
             unreach={h for h in near + [ct[:2] for ct in cities] if rng.random() < .3},
             mount={h: rng.choice([MOUNT, WATER]) for h in near if rng.random() < .15},
             road={h for h in near if rng.random() < .1}, mpass=rng.choice([0, 0, 1]))
    g = ev(c); t, lines = model_ev(c)
    cnt['nada' if t[0] == 0x777 else 'puente' if t[0] >= 0x2000 else 'ciudad'] += 1
    if not (g['ok'] and g['table'] == t and g['lines'] == lines):
        bad += 1
        if bad <= 3: print('DIFIERE', t, lines, g, c)
check(f'{NRAND} casos al azar iguales al modelo (puente {cnt["puente"]}, ciudad {cnt["ciudad"]}, nada {cnt["nada"]})',
      bad == 0 and min(cnt.values()) > NRAND // 20, f'difieren {bad}')

# ---- la meta 9: 0x40dbf0(código)
def goal(c, code=CA, exe=AV, stops=()):
    b = Bench(c, exe)
    end = b.run(0x40dbf0, struct.pack('<Ii', END, code), REGS, stops)
    return b, end
def g9(nombre, want, **kw):
    """want: las llamadas guionadas esperadas; reponer al final si corresponde."""
    c = caso(**kw); b, end = goal(c)
    ok = end == END and b.reg('ESP') == b.esp0 + 4 and saved(b) and b.reg('EAX') & 0xffff == 0
    check(f'meta 9: {nombre}', ok and b.calls == want, f'{b.calls} fin {end and hex(end)}')
    return b
REP = lambda gold_cost=300: [('reponer', CA, gold_cost, AI), 'pausa', 'fin']
b = g9('líder en la cabecera: lo repone', REP(), stack=(19, 10), plan9=True)
check('meta 9: limpia la meta del plan (+6, +8)', b.plan() == (0, 0), b.plan())
g9('líder en la cabecera de enfrente', REP(), stack=(22, 11))
b = g9('líder lejos: va a la cabecera y lo repone', [('meta', 7, 0, 19, 9), ('mover', 19, 9)] + REP())
check('meta 9: el líder quedó en la cabecera', b.leader() == (19, 9), b.leader())
c = caso(); hk = heads(c, PA); m = min(hk.values())
check('meta 9: (19,9) es una de las cabeceras más a mano', hk[(19, 9)] == m, hk)
b = g9('no llega (0x40d2b0 da 0)', [('meta', 7, 0, 19, 9), ('mover', 19, 9)], move='fail')
check('meta 9: deja la meta 9 en el plan si no llegó', b.plan() == (9, 0), b.plan())
g9('dice que llegó pero el líder no está ahí', [('meta', 7, 0, 19, 9), ('mover', 19, 9)], move='stay')
g9('llegó muerto', [('meta', 7, 0, 19, 9), ('mover', 19, 9)], move='die')
g9('sin camino: va a la más cercana de rey', [('meta', 7, 0, 19, 9), ('mover', 19, 9)] + REP(),
   unreach={(x, y) for x in range(64) for y in range(64)})
g9('desde el este va a la cabecera este', [('meta', 7, 0, 22, 9), ('mover', 22, 9)] + REP(), stack=(40, 5))
g9('puente entero: nada', [], stack=(19, 10), bridges={'A': 'intact'})
g9('sin cabecera (agua alrededor): nada', [], stack=(10, 10),
   mount={(x, y): WATER for x in (19, 20, 21, 22) for y in (9, 10, 11) if (x, y) not in PA})
g9('ejército sobre el puente al llegar', [], stack=(19, 10), armies=[(PA[1], ENEMY)])
g9('oro = costo', REP(), stack=(19, 10), gold=300)
g9('oro = costo - 1', [], stack=(19, 10), gold=299)
g9('descuento 2: costo 240', REP(240), stack=(19, 10), gold=240, disc=2)
c = caso(stack=(19, 10)); b, end = goal(c, BC(*PA[1]))
check('meta 9: con el código de la otra casilla repone el mismo puente',
      end == END and b.calls == [('reponer', BC(*PA[1]), 300, AI), 'pausa', 'fin'], b.calls)
# con una ciudad: sigue por el original (0x40dbf8) con la misma pila y registros
for code in (0, 5, 0x1fff):
    st = []
    for exe in (AV, ORIG):
        b, end = goal(caso(), code, exe, stops=(0x40dbf8,))
        st.append((end, b.reg('ESP') - b.esp0, b.reg('EAX'), saved(b), bytes(b.mu.mem_read(b.reg('ESP'), 12)), b.calls))
    check(f'meta 9 con ciudad {code:#x}: llega a 0x40dbf8 igual que el original', st[0] == st[1] and st[0][0] == 0x40dbf8,
          st)

# ---- nombres en los textos de la meta 9
def nm(start, stop, frame, code, exe=AV):
    b = Bench(caso(cities=[(5, 5, 0, ENEMY), (6, 6, 0, ENEMY)]), exe)
    b.mu.mem_write(0x5032e6, struct.pack('<h', code))
    end = b.run(start, frame, REGS, (stop,))
    return end, b.cstr(b.reg('EDX')), b.reg('ESI') & 0xffff, b.reg('ESP') - b.esp0
for code in (CA, 1):
    fr = bytearray(0x40); fr[0x1e:0x20] = struct.pack('<h', code)
    a = nm(0x40ce24, 0x40ce39, bytes(fr), code)
    want = NAME if code >= 0x2000 else 'Ciudad1'
    o = nm(0x40ce24, 0x40ce39, bytes(fr), code, ORIG) if code < 0x2000 else a
    check(f'"Ctd - Rebuild %s" con {code:#x}: {want}', a[0] == 0x40ce39 and a[1] == want and a[3] == 0 and a == o,
          f'{a} {o}')
    a = nm(0x41f30c, 0x41f326, bytes(0x40), code)
    o = nm(0x41f30c, 0x41f326, bytes(0x40), code, ORIG) if code < 0x2000 else a
    check(f'"Evaluate rebuild %s" con {code:#x}: {want}, si = código',
          a[0] == 0x41f326 and a[1] == want and a[2] == code and a[3] == 0 and a == o, f'{a} {o}')

# ---- instrumentos
b = Bench(caso())
b.run(0x4b65e0, struct.pack('<Iii', END, CA, AI), REGS, ())
k = b.reg('EAX') & 0xffff
b2 = Bench(caso(disc=2)); b2.run(0x4b65e0, struct.pack('<Iii', END, CA, AI), REGS, ())
check('instrumento: 0x4b65e0 de un puente cuesta [0x56950e] = 300, con descuento 2 240',
      (k, b2.reg('EAX') & 0xffff) == (300, 240), (k, b2.reg('EAX') & 0xffff))
d = []
for xy in ((19, 9), (30, 40), (5, 60)):
    b.run(0x4a65d0, struct.pack('<Iiii', END, AI, *xy), REGS, ()); d.append(b.reg('EAX') & 0xffff)
check('instrumento: la grilla de caminos da kd + 1 desde la pila (10,10)', d == [10, 31, 51], d)
b = Bench(caso(unreach={(19, 9)}))
b.run(0x4a65d0, struct.pack('<Iiii', END, AI, 19, 9), REGS, ())
check('instrumento: casilla sin camino da 0', b.reg('EAX') & 0xffff == 0, b.reg('EAX'))

print('TODO OK' if all(res) else f'FALLAN {res.count(False)} DE {len(res)}')
sys.exit(0 if all(res) else 1)
