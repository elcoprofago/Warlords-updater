# Prueba de juguete de la misión de héroe "derribar un puente" sobre el exe parcheado, en unicorn.
# Uso: python prueba_misionpuente.py [DarklordAV.exe] [Darklord.exe]
#      (por defecto C:\Warlords3\DarklordAV.exe y el original C:\Warlords3\Darklord.exe; armar antes con build.py)
# Mapa de 64x64 de tierra; el héroe del jugador 1 (humano, o de la computadora: recibe lo mismo) está en (5,5). Con Q = 0 la distancia de rey válida para
# el objetivo es 14..34. Puentes (código canónico = la casilla de menor y*128+x):
#   B5 (25,30)-(26,30) dist 25, dueña C1 enemiga                                   -> candidato
#   B1 (20,5)-(21,5)   dist 15, la más cercana C3 está arrasada: dueña C2, en paz    -> no
#   B3 (10,8)-(11,8)   dist 6, demasiado cerca                                     -> no
#   B2 (5,45)-(5,46)   dist 40, demasiado lejos                                    -> no
#   B4 (30,20)-(31,20) dist 25, dueña C0 propia                                    -> no
#   B7 (30,10)-(31,10) dist 25, dueña C2 en paz                                    -> no
#   B6 (15,25)-(16,25) dist 20, dueña C1 enemiga, pero ya derribado                -> no
# La ciudad dueña de un puente (br_city) sigue la regla de 0x440f60 para un sitio; se compara contra la original.
# El azar (0x4deb20) va guionado: elige el tipo 10 en la tabla de Average y después el candidato pedido.
# Lo que no tiene puentes se compara contra el Darklord.exe original: tiene que dar exactamente lo mismo.
import sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

def load(path):
    pe = pefile.PE(path)
    return pe.OPTIONAL_HEADER.ImageBase, bytes(pe.get_memory_mapped_image()), (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
AV = load(sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe')
ORIG = load(sys.argv[2] if len(sys.argv) > 2 else r'C:\Warlords3\Darklord.exe')

W = H = 64; SHIFT = 8; WATER, LAND = 3, 2
UI, ENEMY, PEACE = 1, 3, 4
HERO = 1                                  # ejército 1 = el héroe de UI; 2 = otro héroe de UI
BC = lambda x, y: 0x2000 + (y << 7) + x
STUB = 0x100000; STACK = 0x200000; END = 0x1fff00; OUT = 0x101000; USED = 0x101100; FMT = 0x101200
BRIDGES = {'B1': ((20, 5), (21, 5)), 'B5': ((25, 30), (26, 30)), 'B3': ((10, 8), (11, 8)), 'B2': ((5, 45), (5, 46)),
           'B4': ((30, 20), (31, 20)), 'B7': ((30, 10), (31, 10)), 'B6': ((15, 25), (16, 25))}
RAZED = {'B6'}
CITIES = [((32, 22), UI, True, 'Propia'), ((27, 32), ENEMY, True, 'Enemiga'), ((32, 12), PEACE, True, 'Amiga'),
          ((21, 3), UI, False, 'Arrasada')]
SITES = [((28, 28), 'SitioA'), ((40, 40), 'SitioLejos')]    # A: dist 23, dueña C1 enemiga (vale); el otro, lejos
HERO_NAME = 'Heroe Uno'

def tile_va(x, y): return ((y * 10) << SHIFT) + x * 10 + 0x503e58

class Bench:
    def __init__(self, exe=AV, bridges=None, sites=(), cities=CITIES, human=True, picks=(), q=0, razed=RAZED, war=(ENEMY,), regions={}):
        base, img, size = exe
        mu = self.mu = Uc(UC_ARCH_X86, UC_MODE_32)
        mu.mem_map(base, size); mu.mem_write(base, img[:size])
        mu.mem_map(STUB, 0x10000); mu.mem_map(STACK - 0x10000, 0x10000)
        mu.mem_write(0x503e00, struct.pack('<HH', W, H)); mu.mem_write(0x503e06, bytes([SHIFT]))
        mu.mem_write(0x535f0c + WATER * 0x58, struct.pack('<H', 1))
        mu.mem_write(0x535f0c + LAND * 0x58, struct.pack('<H', 0))
        for y in range(H):
            for x in range(W):
                self.set_tile(x, y, LAND, 0, 0x05)
        for k, xy in (BRIDGES if bridges is None else bridges).items():
            for x, y in xy:
                if k in razed: self.set_tile(x, y, WATER, 0, 0x85)
                else: self.set_tile(x, y, WATER, 1, 0x05)
        mu.mem_write(0x537ce8, struct.pack('<h', UI))
        for p in range(8):
            mu.mem_write(0x536c12 + p * 0x1f8, struct.pack('<h', -1 if (p == UI and human) else 0))
        for p in war: mu.mem_write(0x55ee4c + UI * 56 + p, bytes([2]))   # en guerra
        mu.mem_write(0x56950a, struct.pack('<h', q))
        mu.mem_write(0x53c393, bytes([2]))
        mu.mem_write(0x569507, b'')                         # misiones Easy/Average/Hard habilitadas
        # ciudades
        mu.mem_write(0x537e2a, struct.pack('<h', len(cities)))
        for i, ((x, y), owner, alive, name) in enumerate(cities):
            c = i * 0xde
            mu.mem_write(0x537e2c + c, struct.pack('<hh', x, y) + name.encode() + b'\0')
            mu.mem_write(0x537ed0 + c, bytes([1 if alive else 0, owner]))
        for (x, y), r in regions.items(): mu.mem_write(tile_va(x, y) + 2, bytes([r]))   # región de la casilla
        # sitios
        mu.mem_write(0x55acb4, struct.pack('<h', len(sites)))
        for i, ((x, y), name) in enumerate(sites):
            s = i * 0x96
            mu.mem_write(0x55acb6 + s, struct.pack('<hh', x, y) + name.encode() + b'\0')
            mu.mem_write(0x55ad4b + s, b'\0')
        # ejércitos: 1 y 2 héroes vivos de UI
        mu.mem_write(0x54fe50, struct.pack('<h', 3))
        for a, (x, y, hidx) in ((1, (5, 5, 3)), (2, (6, 6, 4))):
            r = a * 0x1c
            mu.mem_write(0x54fe52 + r, struct.pack('<hh', x, y))
            mu.mem_write(0x54fe5e + r, struct.pack('<H', (UI << 5) | 0x10))
            mu.mem_write(0x54fe62 + r, struct.pack('<H', 0x4000 | (hidx << 8)))
            mu.mem_write(0x54fe63 + r, bytes([0x40 | hidx]))
        mu.mem_write(0x556bb4 + 3 * 0xb8, HERO_NAME.encode() + b'\0')
        mu.mem_write(0x556bb4 + 4 * 0xb8, b'Heroe Dos\0')
        self.picks = list(picks); self.rand = []; self.calls = []
        mu.mem_write(0x4dd390, bytes.fromhex('31c0c3'))         # partida de un solo equipo: xor eax, eax
        for va, n in {0x4621d0: 0, 0x4def30: 8}.items():
            mu.mem_write(va, b'\xc2' + struct.pack('<H', n) if n else b'\xc3')
        mu.mem_write(0x4deb20, b'\xc3')
        mu.mem_write(STUB, b'\xc3'); mu.mem_write(0x5a9bec, struct.pack('<I', STUB))   # sprintf
        mu.mem_write(FMT, b'%s must destroy %s.\0')
        mu.mem_write(END, b'\xf4')
        mu.hook_add(UC_HOOK_CODE, self.hook)

    def set_tile(self, x, y, w0, struct_, b9):
        t = tile_va(x, y)
        self.mu.mem_write(t, struct.pack('<H', w0)); self.mu.mem_write(t + 3, bytes([struct_]))
        self.mu.mem_write(t + 9, bytes([b9]))

    def arg(self, k):
        esp = self.mu.reg_read(UC_X86_REG_ESP)
        return struct.unpack('<i', self.mu.mem_read(esp + 4 + 4 * k, 4))[0]
    def cstr(self, p): return bytes(self.mu.mem_read(p, 80)).split(b'\0')[0].decode('latin1')

    def hook(self, uc, addr, size, _):
        if addr in self.stops:
            self.end = addr; uc.emu_stop(); return
        a = self.arg
        if addr == 0x4deb20:
            cnt, n, add = a(0) & 0xffff, a(1) & 0xffff, a(2)
            ret = struct.unpack('<I', self.mu.mem_read(self.mu.reg_read(UC_X86_REG_ESP), 4))[0]
            entry = dict(n=n, ret=ret)
            if ret == 0x460e15:                                     # elección del objetivo del tipo 10
                lst = self.mu.reg_read(UC_X86_REG_ESP) + 4 + 0x40
                entry['cand'] = list(struct.unpack(f'<{n}h', self.mu.mem_read(lst, 2 * n))) if n else []
            v = self.picks.pop(0) if self.picks else 0
            v = min(v, n - 1) if n else 0
            entry['v'] = v; self.rand.append(entry)
            uc.reg_write(UC_X86_REG_EAX, v)
        elif addr == 0x4def30:
            self.calls.append(('text', a(0))); uc.reg_write(UC_X86_REG_EAX, FMT)
        elif addr == 0x4621d0:
            self.calls.append('premio')
        elif addr == STUB:
            fmt = self.cstr(a(1))
            out = fmt % (self.cstr(a(2)), self.cstr(a(3))) if fmt.count('%s') == 2 else fmt % self.cstr(a(2))
            uc.mem_write(a(0), out.encode('latin1') + b'\0'); self.calls.append(('sprintf', out))

    def run(self, start, args=(), regs=None, stops=()):
        mu = self.mu
        esp = STACK - 0x400
        mu.mem_write(esp, struct.pack('<I', END) + b''.join(struct.pack('<I', v & 0xffffffff) for v in args) + bytes(0x40))
        base = dict(EAX=0x11111111, ECX=0x22222222, EDX=0x33333333, EBX=0x44444444, ESI=0x55555555,
                    EDI=0x66666666, EBP=0x77777777)
        base.update(regs or {})
        for k, v in base.items(): mu.reg_write(globals()['UC_X86_REG_' + k], v)
        mu.reg_write(UC_X86_REG_ESP, esp)
        self.stops = set(stops) | {END}; self.end = None
        mu.emu_start(start, 0, count=5000000)
        self.esp0 = esp; self.regs_in = base
        return self.end

    def r(self, k): return self.mu.reg_read(globals()['UC_X86_REG_' + k])
    def saved_ok(self):
        return all(self.r(k) == self.regs_in[k] for k in ('EBX', 'ESI', 'EDI', 'EBP')) and self.r('ESP') == self.esp0 + 4
    def quest(self, p=UI): return struct.unpack('<BBhhhhhhh', self.mu.mem_read(0x55edc4 + p * 16, 16))
    def status(self, p=UI): return self.mu.mem_read(0x55ee44 + p, 1)[0]

res = []
def check(nombre, cond, detalle=''):
    res.append(cond); print(f'{"OK " if cond else "MAL"} {nombre}' + (f'   [{detalle}]' if not cond and detalle else ''))

def gen(**kw):
    """Corre el generador 0x45ec40(héroe, Average, out, usados, 0) eligiendo el tipo 10 y el candidato pick."""
    pick = kw.pop('pick', 0)
    b = Bench(picks=[6, pick], **kw)
    end = b.run(0x45ec40, (HERO, 1, OUT, USED, 0))
    cand = next((e['cand'] for e in b.rand if 'cand' in e), None)
    return dict(end=end, al=b.r('EAX') & 0xff, saved=b.saved_ok(), rand=b.rand, cand=cand,
                out=bytes(b.mu.mem_read(OUT, 16)))
def target(g): return struct.unpack_from('<h', g['out'], 6)[0] & 0xffff
def qtype(g): return struct.unpack_from('<h', g['out'], 4)[0]
NOCITY = []
B = {k: BC(*min(v, key=lambda t: (t[1], t[0]))) for k, v in BRIDGES.items()}

# ---- br_city contra 0x440f60 del original: mismas ciudades, regiones y punto (el sitio 0 puesto en el punto)
import random, capstone
_cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def _jmp(va):
    i = next(_cs.disasm(AV[1][va - AV[0]:va - AV[0] + 8], va)); assert i.mnemonic == 'jmp'; return int(i.op_str, 16)
QB_TEXT = _jmp(0x461876)
BR_CITY = next(int(i.op_str, 16) for i in _cs.disasm(AV[1][QB_TEXT - AV[0]:QB_TEXT - AV[0] + 0x40], QB_TEXT)
               if i.mnemonic == 'call')
rnd = random.Random(1234)
ba, bo = Bench(cities=NOCITY), Bench(exe=ORIG, cities=NOCITY, sites=[((0, 0), 'P')])
bad = []; kinds = set()
for trial in range(400):
    n = rnd.randint(0, 7)
    cities = [((rnd.randrange(W), rnd.randrange(H)), rnd.randrange(8), rnd.random() < 0.75, f'C{i}') for i in range(n)]
    px, py = rnd.randrange(W), rnd.randrange(H)
    regs = {xy: rnd.randrange(3) for xy, *_ in cities}; regs[(px, py)] = rnd.randrange(3)
    out = []
    for b in (ba, bo):
        for y in range(H):
            for x in range(W): b.mu.mem_write(tile_va(x, y) + 2, b'\0')
        for (x, y), r in regs.items(): b.mu.mem_write(tile_va(x, y) + 2, bytes([r]))
        b.mu.mem_write(0x537e2a, struct.pack('<h', n))
        for i, ((x, y), owner, alive, name) in enumerate(cities):
            b.mu.mem_write(0x537e2c + i * 0xde, struct.pack('<hh', x, y))
            b.mu.mem_write(0x537ed0 + i * 0xde, bytes([1 if alive else 0, owner]))
    bo.mu.mem_write(0x55acb6, struct.pack('<hh', px, py))
    e1 = ba.run(BR_CITY, (BC(px, py),)); r1 = ba.r('EAX'); s1 = ba.saved_ok()
    e2 = bo.run(0x440f60, (0,)); r2 = struct.unpack('<h', struct.pack('<H', bo.r('EAX') & 0xffff))[0]
    alive = [i for i, c in enumerate(cities) if c[2]]
    near = min(alive, key=lambda i: (max(abs(cities[i][0][0] - px), abs(cities[i][0][1] - py)), i)) if alive else -1
    kinds.add('ninguna' if r2 < 0 else 'la más cercana' if r2 == near else 'misma región, más lejos')
    if not (e1 == e2 == END and s1 and struct.unpack('<i', struct.pack('<I', r1))[0] == r2):
        bad.append((trial, cities, (px, py), regs, hex(r1), r2))
check('br_city = 0x440f60 del original en 400 mapas al azar', not bad and len(kinds) == 3, (bad[:2], kinds))

# ---- generador: qué puentes entran
for nombre, kw, esperado in [
        ('gen: solo B5 (enemiga)',               {}, [B['B5']]),
        ('gen: en guerra también con C2, entran B1 y B7', dict(war=(ENEMY, PEACE)), [B['B1'], B['B7'], B['B5']]),
        ('gen: con sitio, el sitio va primero',  dict(sites=SITES), [0, B['B5']]),
        ('gen: B6 entero también entra (control del derribado)', dict(razed=set()), [B['B6'], B['B5']]),
        ('gen: C3 viva y enemiga mete a B1',     dict(cities=CITIES[:3] + [((21, 3), ENEMY, True, 'Viva')]), [B['B1'], B['B5']]),
        ('gen: sin ciudades, todo lo que está a distancia', dict(cities=NOCITY), [B['B1'], B['B7'], B['B4'], B['B5']]),
        ('gen: solo ciudades arrasadas = sin dueño', dict(cities=[(xy, o, False, n) for xy, o, _, n in CITIES]),
         [B['B1'], B['B7'], B['B4'], B['B5']]),
        ('gen: misma región manda sobre la distancia', dict(regions={(20, 5): 7, (27, 32): 7}), [B['B1']]),
        ('gen: Q = 3 corre la distancia a 23..46', dict(q=3), [B['B5'], B['B2']]),
        ('gen: jugador de la computadora, lo mismo', dict(human=False), [B['B5']]),
        ('gen: computadora con sitio, el sitio va primero', dict(human=False, sites=SITES), [0, B['B5']])]:
    g = gen(**kw)
    check(nombre, g['end'] == END and g['saved'] and g['cand'] == esperado, f"cand={g['cand']} end={g['end']}")
g = gen(pick=2, war=(ENEMY, PEACE))
check('gen: elegido B5 -> misión tipo 10 con su código', g['al'] == 1 and qtype(g) == 10 and target(g) == B['B5']
      and g['out'][0] == 1 and struct.unpack_from('<h', g['out'], 2)[0] == HERO, g['out'].hex())

# ---- generador: donde no hay puentes que dar, idéntico al original
for nombre, kw in [
        ('igual al original: sin puentes, con sitios', dict(bridges={}, sites=SITES)),
        ('igual al original: sin puentes ni sitios (cae a otro tipo)', dict(bridges={})),
        ('igual al original: computadora, sin puentes, con sitios', dict(human=False, bridges={}, sites=SITES)),
        ('igual al original: puentes todos fuera de distancia', dict(bridges={k: BRIDGES[k] for k in ('B2', 'B3')}, sites=SITES))]:
    a, o = gen(**kw), gen(exe=ORIG, **kw)
    check(nombre, a['end'] == o['end'] == END and (a['al'], a['out'], a['rand']) == (o['al'], o['out'], o['rand'])
          and a['saved'], f"av={a['out'].hex()} {a['rand']}  orig={o['out'].hex()} {o['rand']}")
g = gen(bridges={}); check('  (y ese caso de verdad no tenía tipo 10)', qtype(g) != 10 and len(g['rand']) > 2, g['rand'])

# ---- misión activa: cumplir (evento 6) y fracasar (evento 0)
def with_quest(tgt, hero=HERO, **kw):
    b = Bench(**kw)
    b.mu.mem_write(0x55edc4 + UI * 16, struct.pack('<BBhhhhhhh', 1, 0, hero, 10, tgt, 0, 0, 0, 1))
    return b
def event(b, ev, army, param):
    end = b.run(0x461a60, (ev, army, 0, 0, param, 1))
    return end == END and b.saved_ok()
for nombre, tgt, army, param, st in [
        ('cumplir: el héroe derriba el puente objetivo', B['B5'], HERO, B['B5'], 1),
        ('cumplir: otro puente no',                    B['B5'], HERO, B['B1'], 0),
        ('cumplir: otro héroe derriba el objetivo, no', B['B5'], 2, B['B5'], 0),
        ('cumplir: sitio 0 arrasado por el héroe (control)', 0, HERO, 0, 1),
        ('cumplir: sitio 0, arrasado otro sitio (control)', 0, HERO, 1, 0)]:
    b = with_quest(tgt, sites=SITES)
    ok = event(b, 6, army, param)
    check(nombre, ok and b.status() == st and b.quest()[0] == 1, f'status={b.status()} quest={b.quest()}')

def raze(b, k):
    for x, y in BRIDGES[k]: b.set_tile(x, y, WATER, 0, 0x85)
for nombre, tgt, prep, st in [
        ('turno: objetivo entero, sigue',            B['B5'], lambda b: None, 0),
        ('turno: objetivo derribado por otro, fracasa', B['B5'], lambda b: raze(b, 'B5'), 2),
        ('turno: derribado otro puente, sigue',      B['B5'], lambda b: raze(b, 'B1'), 0),
        ('turno: ya cumplida y derribado, sigue cumplida', B['B5'],
         lambda b: (raze(b, 'B5'), b.mu.mem_write(0x55ee44 + UI, b'\1')), 1),
        ('turno: sitio 0 entero (control)',           0, lambda b: None, 0),
        ('turno: sitio 0 arrasado (control)',         0, lambda b: b.mu.mem_write(0x55ad4b, b'\1'), 2)]:
    b = with_quest(tgt, sites=SITES); prep(b)
    ok = event(b, 0, 0, 0)
    check(nombre, ok and b.status() == st, f'status={b.status()}')
for nombre, razed_site in [('turno: igual al original con sitio entero', False), ('turno: igual al original con sitio arrasado', True)]:
    st = []
    for exe in (AV, ORIG):
        b = with_quest(0, sites=SITES, exe=exe)
        if razed_site: b.mu.mem_write(0x55ad4b, b'\1')
        event(b, 0, 0, 0); st.append((b.status(), b.r('EAX') & 0xff, b.calls))
    check(nombre, st[0] == st[1], st)

# ---- textos: nombre del tipo (0x461130) y objetivo (0x461400)
BUF = 0x101400
def text(fn, tgt, exe=AV, cities=CITIES):
    b = with_quest(tgt, sites=SITES, exe=exe, cities=cities)
    end = b.run(fn, (0x55edc4 + UI * 16, BUF))
    return end == END and b.saved_ok(), b.cstr(BUF), b.calls
for nombre, fn, tgt, kw, esperado in [
        ('nombre: puente', 0x461130, B['B5'], {}, 'Destroying a Bridge'),
        ('objetivo: puente cerca de una ciudad', 0x461400, B['B5'], {}, f'{HERO_NAME} must destroy the bridge near Enemiga.'),
        ('objetivo: puente sin ciudades', 0x461400, B['B5'], dict(cities=NOCITY), f'{HERO_NAME} must destroy a bridge.')]:
    ok, s, _ = text(fn, tgt, **kw)
    check(nombre, ok and s == esperado, repr(s))
for nombre, fn in [('nombre: sitio igual al original', 0x461130), ('objetivo: sitio igual al original', 0x461400)]:
    a, o = text(fn, 0), text(fn, 0, exe=ORIG)
    check(nombre, a == o and a[0] and a[1], f'{a} {o}')

# ---- la IA lee el lugar del objetivo (0x436178 y 0x436442)
def ailoc1(tgt, exe=AV):
    b = Bench(sites=SITES, exe=exe)
    b.mu.mem_write(0x55acb6 + 0x96, struct.pack('<hh', 40, 41))
    end = b.run(0x436178, regs=dict(EDI=0x66660000 | tgt), stops=(0x436199,))
    return end, b.r('EDX') & 0xffff, b.r('EAX') & 0xffff, b.r('EBP') & 0xffff, b.r('EDI'), b.r('EBX'), b.r('ESI'), b.r('ESP')
for nombre, tgt, xy in [('IA 1: puente', B['B5'], (25, 30)), ('IA 1: puente vertical', B['B2'], (5, 45))]:
    r = ailoc1(tgt)
    check(nombre, r[0] == 0x436199 and r[1:4] == xy + (1,), r)
for t in (0, 1):
    a, o = ailoc1(t), ailoc1(t, ORIG)
    check(f'IA 1: sitio {t} igual al original', a == o and a[0] == 0x436199, f'{a} {o}')
def ailoc2(tgt, exe=AV):
    b = Bench(sites=SITES, exe=exe)
    b.mu.mem_write(0x55acb6 + 0x96, struct.pack('<hh', 40, 41))
    T, X, Y = 0x101500, 0x101504, 0x101508
    b.mu.mem_write(T, bytes(12))
    esp = STACK - 0x400
    b.mu.mem_write(esp, struct.pack('<IIII', 0x6666, 0x5555, 0x4444, END))   # edi, esi, ebx guardados
    for k, v in dict(EAX=0x11117777, ECX=0x22220000 | tgt, EDX=Y, EBX=T, ESI=X, EDI=0x99999999, EBP=0x77777777).items():
        b.mu.reg_write(globals()['UC_X86_REG_' + k], v)
    b.mu.reg_write(UC_X86_REG_ESP, esp); b.stops = {END}; b.end = None
    b.mu.emu_start(0x436442, 0, count=1000)
    t, x, y = struct.unpack('<hxxhxxh', b.mu.mem_read(T, 10))
    return b.end, t & 0xffff, x, y, b.r('EAX'), b.r('EDI'), b.r('ESI'), b.r('EBX'), b.r('EBP'), b.r('ESP') - esp
for nombre, tgt, xy in [('IA 2: puente', B['B5'], (25, 30)), ('IA 2: puente vertical', B['B2'], (5, 45))]:
    r = ailoc2(tgt)
    check(nombre, r[0] == END and r[1] == tgt and r[2:4] == xy and r[4] == 0x11117777
          and r[5:9] == (0x6666, 0x5555, 0x4444, 0x77777777) and r[9] == 0x10, r)
for t in (0, 1):
    a, o = ailoc2(t), ailoc2(t, ORIG)
    check(f'IA 2: sitio {t} igual al original', a == o and a[0] == END, f'{a} {o}')

# ---- guardar y cargar: la misión activa vive dentro del bloque que guarda el SAV
check('SAV: la misión activa y su estado están en el bloque guardado (0x536b30..0x5643c4)',
      0x536b30 <= 0x55edc4 and 0x55edc4 + 8 * 16 <= 0x5643c4 and 0x55ee44 + 8 <= 0x5643c4)

print('TODO OK' if all(res) else f'FALLAN {res.count(False)} DE {len(res)}')
sys.exit(0 if all(res) else 1)
