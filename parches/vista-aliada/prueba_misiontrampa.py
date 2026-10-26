# Prueba de juguete de la misión dura «escoltar al equipo que desarma una trampa» (qt_*) sobre el exe parcheado, en unicorn.
# Uso: python prueba_misiontrampa.py [DarklordAV.exe] [Darklord.exe]
#      (por defecto C:\Warlords3\DarklordAV.exe y el original C:\Warlords3\Darklord.exe; armar antes con build.py)
# Mapa de 64x64 de tierra; el héroe del jugador 1 (humano) está en (5,5). Con Q = 0 la distancia de rey válida es 2..23.
# Trampas (x, y, tipo, estado, máscara de quién la vio, dueño):
#   T0 (10,5)  dist 5,  enemiga, vista por UI, entera   -> candidata
#   T1 (6,5)   dist 1,  demasiado cerca                 -> no
#   T2 (5,30)  dist 25, demasiado lejos                 -> no
#   T3 (12,12) dueño en paz                             -> no
#   T4 (15,5)  enemiga, no vista por UI                 -> no
#   T5 (8,8)   enemiga, vista, gastada (3 explosiones)  -> no
#   T6 (9,9)   propia                                   -> no
#   P7 (7,7)   un pozo visto, no una trampa             -> no
#   T8 (20,20) dist 15, enemiga, vista, entera          -> candidata
# El azar (0x4deb20) va guionado. Donde no hay trampas que dar, todo se compara contra el Darklord.exe original.
import sys, re, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

def load(path):
    pe = pefile.PE(path)
    return pe.OPTIONAL_HEADER.ImageBase, bytes(pe.get_memory_mapped_image()), (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
AV = load(sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe')
ORIG = load(sys.argv[2] if len(sys.argv) > 2 else r'C:\Warlords3\Darklord.exe')
PO_MAX, PO_REC, PO_TRAMPA, PO_POZO, QT, TR_USOS = 64, 8, 2, 0, 13, 2
PO_SAVE = AV[0] + AV[1].index(b'POZO' + bytes(4 + PO_MAX * PO_REC)); PO_N, PO_TAB = PO_SAVE + 4, PO_SAVE + 8
k = AV[1].index(bytes.fromhex('6031db0fb683'))                 # po_fall: pushad; xor ebx, ebx; movzx eax, byte [ebx + po_pend]
assert AV[1].find(bytes.fromhex('6031db0fb683'), k + 1) < 0
PO_FALL = AV[0] + k; PO_PEND = struct.unpack_from('<I', AV[1], k + 6)[0]

W = H = 64; SHIFT = 8; WATER, LAND = 3, 2
UI, ENEMY, PEACE = 1, 3, 4
HERO = 1                                  # ejército 1 = el héroe de UI; 2 = otro héroe de UI; 3 = una unidad de UI
STUB = 0x100000; STACK = 0x200000; END = 0x1fff00; OUT = 0x101000; USED = 0x101100; FMT = 0x101200; BUF = 0x101400
M = 1 << UI
TRAPS = [(10, 5, PO_TRAMPA, 0, M, ENEMY), (6, 5, PO_TRAMPA, 0, M, ENEMY), (5, 30, PO_TRAMPA, 0, M, ENEMY),
         (12, 12, PO_TRAMPA, 0, M, PEACE), (15, 5, PO_TRAMPA, 0, 0, ENEMY), (8, 8, PO_TRAMPA, TR_USOS, 0xff, ENEMY),
         (9, 9, PO_TRAMPA, 0, M, UI), (7, 7, PO_POZO, 0, M, 0xff), (20, 20, PO_TRAMPA, 0, M, ENEMY)]
CITIES = [((10, 7), ENEMY, True, 'Afland'), ((30, 30), ENEMY, True, 'Belgor'), ((4, 28), PEACE, False, 'Arrasada')]
HERO_NAME = 'Heroe Uno'

def tile_va(x, y): return ((y * 10) << SHIFT) + x * 10 + 0x503e58

def tr_name(traps, i, cities):
    """La regla de po_msg: la ciudad más cercana de todas (rey, en empate la primera) + 1 + anteriores con la misma."""
    def city(t):
        if not cities: return None
        return min(range(len(cities)), key=lambda c: (max(abs(cities[c][0][0] - t[0]), abs(cities[c][0][1] - t[1])), c))
    c = city(traps[i])
    if c is None: return None
    n = 1 + sum(1 for t in traps[:i] if t[2] == PO_TRAMPA and city(t) == c)
    return '%.20s%02d' % (cities[c][3], n)

class Bench:
    def __init__(self, exe=AV, traps=TRAPS, cities=CITIES, human=True, picks=(), q=0, war=(ENEMY,), fly=(), water=()):
        base, img, size = exe
        mu = self.mu = Uc(UC_ARCH_X86, UC_MODE_32)
        mu.mem_map(base, size); mu.mem_write(base, img[:size])
        mu.mem_map(STUB, 0x10000); mu.mem_map(STACK - 0x10000, 0x10000)
        mu.mem_write(0x503e00, struct.pack('<HH', W, H)); mu.mem_write(0x503e06, bytes([SHIFT]))
        mu.mem_write(0x535f0c + WATER * 0x58, struct.pack('<H', 1))
        mu.mem_write(0x535f0c + LAND * 0x58, struct.pack('<H', 0))
        for y in range(H):
            for x in range(W):
                mu.mem_write(tile_va(x, y), struct.pack('<H', WATER if (x, y) in water else LAND))
        mu.mem_write(0x537ce8, struct.pack('<h', UI))
        for p in range(8):
            mu.mem_write(0x536c12 + p * 0x1f8, struct.pack('<h', -1 if (p == UI and human) else 0))
        for p in war: mu.mem_write(0x55ee4c + UI * 56 + p, bytes([2]))   # en guerra
        mu.mem_write(0x56950a, struct.pack('<h', q))
        mu.mem_write(0x53c393, bytes([2]))
        mu.mem_write(0x569509, b'\1')                       # misiones Hard habilitadas
        mu.mem_write(0x537e2a, struct.pack('<h', len(cities)))
        for i, ((x, y), owner, alive, name) in enumerate(cities):
            c = i * 0xde
            mu.mem_write(0x537e2c + c, struct.pack('<hh', x, y) + name.encode() + b'\0')
            mu.mem_write(0x537ed0 + c, bytes([1 if alive else 0, owner]))
        if exe is AV:
            mu.mem_write(PO_N, struct.pack('<i', len(traps)))
            for i, t in enumerate(traps): mu.mem_write(PO_TAB + PO_REC * i, struct.pack('<hhBBBB', *t))
        # ejércitos: 1 y 2 héroes vivos de UI, 3 una unidad viva de UI
        mu.mem_write(0x54fe50, struct.pack('<h', 4))
        for a, (x, y, hidx) in ((1, (5, 5, 3)), (2, (6, 6, 4)), (3, (40, 40, 0))):
            r = a * 0x1c
            mu.mem_write(0x54fe52 + r, struct.pack('<hh', x, y))
            mu.mem_write(0x54fe5e + r, struct.pack('<H', (UI << 5) | (0x10 if hidx else 0)))
            mu.mem_write(0x54fe62 + r, struct.pack('<H', 0x4000 | (hidx << 8)))
            mu.mem_write(0x54fe63 + r, bytes([0x40 | hidx]))
        mu.mem_write(0x556bb4 + 3 * 0xb8, HERO_NAME.encode() + b'\0')
        mu.mem_write(0x556bb4 + 4 * 0xb8, b'Heroe Dos\0')
        self.fly = set(fly)
        self.picks = list(picks); self.rand = []; self.calls = []
        mu.mem_write(0x4dd390, bytes.fromhex('31c0c3'))         # partida de un solo equipo: xor eax, eax
        for va in (0x4621d0, 0x4def30, 0x4deb20, 0x48f9a0, 0x497010, 0x46c470, 0x441290, 0x4a2170, 0x4c2790,
                   0x4eca00, 0x4e6fd0, 0x4465e0):
            mu.mem_write(va, b'\xc3')
        mu.mem_write(0x4def30, b'\xc2\x08\x00'); mu.mem_write(0x4eca00, b'\xc2\x04\x00'); mu.mem_write(0x4e6fd0, b'\xc2\x08\x00')
        mu.mem_write(STUB, b'\xc3'); mu.mem_write(0x5a9bec, struct.pack('<I', STUB))   # sprintf
        mu.mem_write(FMT, b'%s must do something with %s.\0')
        mu.mem_write(END, b'\xf4'); mu.mem_write(0x49d1a0, b'\xf4')
        mu.hook_add(UC_HOOK_CODE, self.hook)

    def arg(self, k):
        esp = self.mu.reg_read(UC_X86_REG_ESP)
        return struct.unpack('<i', self.mu.mem_read(esp + 4 + 4 * k, 4))[0]
    def cstr(self, p, n=120): return bytes(self.mu.mem_read(p, n)).split(b'\0')[0].decode('latin1')

    def hook(self, uc, addr, size, _):
        if addr in self.stops:
            self.end = addr; uc.emu_stop(); return
        a = self.arg
        if addr == 0x4deb20:
            n = a(1) & 0xffff
            ret = struct.unpack('<I', self.mu.mem_read(self.mu.reg_read(UC_X86_REG_ESP), 4))[0]
            v = self.picks.pop(0) if self.picks else 0
            v = min(v, n - 1) if n else 0
            self.rand.append(dict(n=n, v=v, cave=not (0x401000 <= ret < 0x5a0000))); uc.reg_write(UC_X86_REG_EAX, v)
        elif addr == 0x4def30:
            self.calls.append(('text', a(0))); uc.reg_write(UC_X86_REG_EAX, FMT)
        elif addr == 0x4621d0:
            self.calls.append('premio')
        elif addr in (0x48f9a0, 0x497010):
            uc.reg_write(UC_X86_REG_EAX, 1 if (a(0) & 0xffff) in self.fly else 0)
        elif addr == 0x46c470:
            self.calls.append(('muere', a(0)))
        elif addr == STUB:
            fmt = self.cstr(a(1))
            specs = re.findall(r'%[-0-9.]*[sd]', fmt)
            vals = tuple(self.cstr(a(2 + i)) if s[-1] == 's' else a(2 + i) for i, s in enumerate(specs))
            out = fmt % vals
            uc.mem_write(a(0), out.encode('latin1') + b'\0'); self.calls.append(('sprintf', out))

    def run(self, start, args=(), stops=()):
        mu = self.mu
        esp = STACK - 0x400
        mu.mem_write(esp, struct.pack('<I', END) + b''.join(struct.pack('<I', v & 0xffffffff) for v in args) + bytes(0x40))
        base = dict(EAX=0x11111111, ECX=0x22222222, EDX=0x33333333, EBX=0x44444444, ESI=0x55555555,
                    EDI=0x66666666, EBP=0x77777777)
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
    def trap(self, i): return struct.unpack('<hhBBBB', self.mu.mem_read(PO_TAB + PO_REC * i, PO_REC))

res = []
def check(nombre, cond, detalle=''):
    res.append(cond); print(f'{"OK " if cond else "MAL"} {nombre}' + (f'   [{detalle}]' if not cond and detalle else ''))

# ---- generador, dificultad Hard
def gen(picks, used=(), **kw):
    b = Bench(picks=list(picks), **kw)
    b.mu.mem_write(USED, struct.pack(f'<{len(used)}h', *used))
    end = b.run(0x45ec40, (HERO, 2, OUT, USED, len(used)))
    return dict(end=end, al=b.r('EAX') & 0xff, saved=b.saved_ok(), rand=b.rand, out=bytes(b.mu.mem_read(OUT, 16)))
def qtype(g): return struct.unpack_from('<h', g['out'], 4)[0]
def target(g): return struct.unpack_from('<hh', g['out'], 6)

for pick, idx in ((0, 0), (1, 8)):
    g = gen([6, pick])
    r0 = g['rand'][:2]
    check(f'gen: hay candidatas -> se tira 0..6, el 6 es la misión; candidata {pick} = T{idx}',
          g['end'] == END and g['saved'] and g['al'] == 1 and r0[0]['n'] == 7 and r0[1]['n'] == 2
          and qtype(g) == QT and target(g) == (idx, ENEMY) and g['out'][0] == 1
          and struct.unpack_from('<h', g['out'], 2)[0] == HERO and struct.unpack_from('<h', g['out'], 0xa)[0] == 0,
          f"{g['out'].hex()} {g['rand']}")
g = gen([6, 0], traps=TRAPS[:5] + [TRAPS[5][:3] + (TR_USOS - 1,) + TRAPS[5][4:]] + TRAPS[6:])
check('gen: T5 con un uso todavía (2 explosiones), es candidata (3 candidatas)', g['rand'][1]['n'] == 3, g['rand'])
g = gen([6, 0], water={TRAPS[0][:2]})
check('gen: T0 en el agua (mina submarina) no es candidata: queda T8 sola', g['rand'][1]['n'] == 1 and target(g) == (8, ENEMY), g['rand'])
g = gen([6, 0], war=(ENEMY, PEACE))
check('gen: en guerra también con el de T3, entra (3 candidatas)', g['rand'][1]['n'] == 3 and target(g) == (0, ENEMY), g['rand'])
g = gen([6, 0], q=3)
check('gen: Q = 3 corre el tope a 35: entra T2 (3 candidatas, T0 primero)', g['rand'][1]['n'] == 3, g['rand'])
for nombre, kw in [('gen: sin trampas, igual al original', dict(traps=[])),
                   ('gen: solo trampas que no sirven, igual al original', dict(traps=TRAPS[1:8])),
                   ('gen: jugador de la computadora, igual al original', dict(human=False))]:
    for picks in ([0, 0, 0], [3, 1, 0], [5, 0, 2], [2, 4, 1]):
        a, o = gen(picks, **kw), gen(picks, exe=ORIG, **kw)
        ok = a['end'] == o['end'] == END and a['saved'] and (a['al'], a['out'], [(e['n'], e['v']) for e in a['rand']]) == \
             (o['al'], o['out'], [(e['n'], e['v']) for e in o['rand']])
        if not ok: break
    check(nombre, ok, f"av={a['out'].hex()} {a['rand']}  orig={o['out'].hex()} {o['rand']}")
for picks in ([0, 0, 0], [4, 1, 0]):
    a, o = gen(picks, used=(QT,)), gen(picks, used=(QT,), exe=ORIG)
    check(f'gen: el tipo ya ofrecido, igual al original {picks}', a['end'] == o['end'] == END and
          (a['al'], a['out'], [(e['n'], e['v']) for e in a['rand']]) == (o['al'], o['out'], [(e['n'], e['v']) for e in o['rand']]),
          f"{a['rand']} {o['rand']}")
# con candidatas y sin sacar el 6, los demás tipos salen como en el original (la tabla 0x46101c)
for pick in range(6):
    a, o = gen([pick, 0, 0, 0]), gen([pick, 0, 0, 0], exe=ORIG, traps=[])
    check(f'gen: con candidatas, tirada {pick} da el mismo tipo que el original', a['end'] == o['end'] == END and a['saved']
          and (a['al'], a['out']) == (o['al'], o['out']) and a['rand'][0]['n'] == 7 and o['rand'][0]['n'] == 6,
          f"av={a['out'].hex()} orig={o['out'].hex()}")

# ---- misión activa
def with_quest(tgt, a=0, typ=QT, hero=HERO, **kw):
    b = Bench(**kw)
    b.mu.mem_write(0x55edc4 + UI * 16, struct.pack('<BBhhhhhhh', 1, 0, hero, typ, tgt, ENEMY, a, 0, 2))
    return b
def det(traps, i, st=TR_USOS):
    t = list(traps); t[i] = t[i][:3] + (st, 0xff) + t[i][5:]; return t
DET0 = det(TRAPS, 0)
def arrive(xy, a=1, traps=DET0, **kw):
    b = with_quest(0, a, traps=traps, **kw)
    end = b.run(0x461a60, (5, HERO, xy[0], xy[1], 0, 1))
    return end == END and b.saved_ok(), b.status(), b.calls
for nombre, xy, kw, st in [
        ('llega: vecina al este, por tierra, detonada por él -> cumplida', (11, 5), {}, 1),
        ('llega: vecina en diagonal -> cumplida', (9, 4), {}, 1),
        ('llega: sobre la trampa misma -> cumplida', (10, 5), {}, 1),
        ('llega: a 2 casillas, no', (12, 5), {}, 0),
        ('llega: a 2 en y, no', (10, 7), {}, 0),
        ('llega: no la detonó él (+0xa = 0), no', (11, 5), dict(a=0), 0),
        ('llega: vecina pero en agua (en barco), no', (11, 5), dict(water={(11, 5)}), 0),
        ('llega: el héroe vuela, no', (11, 5), dict(fly={HERO}), 0),
        ('llega: el grupo que se mueve lleva un volador, no', (11, 5), dict(fly={2}), 0),
        ('llega: control, sin volador en el grupo, sí', (11, 5), dict(fly={3}), 1)]:
    group = 'fly' in kw
    b = with_quest(0, kw.pop('a', 1), traps=DET0, **kw)
    if group:
        b.mu.mem_write(0x56ea94 + UI * 0x4f0, struct.pack('<hhh', HERO, 2, 3))
        b.mu.mem_write(0x56eaa8 + UI * 0x4f0, struct.pack('<h', 3 if kw['fly'] != {HERO} else 1))
        if kw['fly'] == {3}: b.mu.mem_write(0x56eaa8 + UI * 0x4f0, struct.pack('<h', 1))
    end = b.run(0x461a60, (5, HERO, xy[0], xy[1], 0, 1))
    check(nombre, end == END and b.saved_ok() and b.status() == st, f'status={b.status()} {b.calls}')
for nombre, typ, tgt, xy in [('llega: escolta tipo 1 a la ciudad 0, igual al original', 1, 0, (10, 7)),
                             ('llega: escolta tipo 1 lejos de la ciudad, igual al original', 1, 0, (20, 20)),
                             ('llega: tipo 4 (ruina), igual al original', 4, 0, (10, 7))]:
    st = []
    for exe in (AV, ORIG):
        b = with_quest(tgt, typ=typ, exe=exe)
        end = b.run(0x461a60, (5, HERO, xy[0], xy[1], 0, 1))
        st.append((end, b.saved_ok(), b.status(), b.r('EAX') & 0xff, b.calls))
    check(nombre, st[0] == st[1] and st[0][0] == END, st)

for nombre, traps, a, st in [('turno: trampa entera, sigue', TRAPS, 0, 0),
                             ('turno: detonada por otro, fracasa', DET0, 0, 2),
                             ('turno: detonada por él, sigue', DET0, 1, 0),
                             ('turno: detonada otra trampa, sigue', det(TRAPS, 8), 0, 0),
                             ('turno: explotó 1 vez por otro, le quedan usos, sigue', det(TRAPS, 0, 1), 0, 0),
                             ('turno: explotó 2 veces por otro, gastada, fracasa', det(TRAPS, 0, 2), 0, 2),
                             ('turno: recién explotada (bit 7, jugador 3) con 1, sigue', det(TRAPS, 0, 0xb1), 0, 0),
                             ('turno: recién gastada (bit 7, jugador 3), fracasa', det(TRAPS, 0, 0xb2), 0, 2)]:
    b = with_quest(0, a, traps=traps)
    end = b.run(0x461a60, (0, 0, 0, 0, 0, 1))
    check(nombre, end == END and b.saved_ok() and b.status() == st, f'status={b.status()}')
for nombre, alive in [('turno: asesinar (tipo 11) con la víctima viva, igual al original', True),
                      ('turno: asesinar (tipo 11) con la víctima muerta, igual al original', False)]:
    st = []
    for exe in (AV, ORIG):
        b = with_quest(2, typ=11, exe=exe)
        b.mu.mem_write(0x55edc4 + UI * 16 + 8, struct.pack('<h', ENEMY))
        b.mu.mem_write(0x54fe5e + 2 * 0x1c, struct.pack('<H', (ENEMY << 5) | 0x10))
        if not alive: b.mu.mem_write(0x54fe63 + 2 * 0x1c, b'\4')
        end = b.run(0x461a60, (0, 0, 0, 0, 0, 1))
        st.append((end, b.status(), b.calls))
    check(nombre, st[0] == st[1] and st[0][0] == END, st)

# ---- textos
def text(fn, tgt, exe=AV, typ=QT, **kw):
    b = with_quest(tgt, typ=typ, exe=exe, **kw)
    end = b.run(fn, (0x55edc4 + UI * 16, BUF))
    return end == END and b.saved_ok(), b.cstr(BUF), b.calls
n0, n8 = tr_name(TRAPS, 0, CITIES), tr_name(TRAPS, 8, CITIES)
check('nombres esperados de juguete', (n0, n8) == ('Afland01', 'Belgor01'), (n0, n8))
for nombre, fn, tgt, kw, esperado in [
        ('nombre: con ciudades', 0x461130, 0, {}, f'Escort trap-disarming team to {n0}'),
        ('nombre: otra trampa', 0x461130, 8, {}, f'Escort trap-disarming team to {n8}'),
        ('nombre: sin ciudades', 0x461130, 0, dict(cities=[]), 'Escort trap-disarming team'),
        ('nombre: ciudad de nombre largo, recortado a 20', 0x461130, 0,
         dict(cities=[((10, 7), ENEMY, True, 'Ciudadconunnombremuylargo')]), 'Escort trap-disarming team to ' + 'Ciudadconunnombremuylargo'[:20] + '01'),
        ('objetivo: con ciudades', 0x461400, 0, {}, f'{HERO_NAME} must escort a trap-disarming team to the trap {n0}.'),
        ('objetivo: sin ciudades', 0x461400, 0, dict(cities=[]), f'{HERO_NAME} must escort a trap-disarming team to a trap.')]:
    ok, s, _ = text(fn, tgt, **kw)
    check(nombre, ok and s == esperado, repr(s))
check('nombre: el más largo entra en 0x40', len('Escort trap-disarming team to ' + 'x' * 20 + '99') < 0x40)
for typ in (1, 7, 10, 11):
    for nombre, fn in [('nombre', 0x461130), ('objetivo', 0x461400)]:
        a, o = text(fn, 0, typ=typ), text(fn, 0, typ=typ, exe=ORIG)
        check(f'{nombre}: tipo {typ} igual al original', a == o and a[0], f'{a} {o}')

# ---- po_fall: el jugador que cae marca su misión
def fall(player, tgt=0, typ=QT, trap=0):
    b = with_quest(tgt, typ=typ)
    x, y = TRAPS[trap][:2]
    b.mu.mem_write(0x54fe52 + 3 * 0x1c, struct.pack('<hh', x, y))
    b.mu.mem_write(0x54fe5e + 3 * 0x1c, struct.pack('<H', player << 5))
    m = b.mu.mem_read(0x54fe62 + 3 * 0x1c, 2)   # movimiento 12 (la trampa en tierra mata o paraliza: 26/10/2026)
    b.mu.mem_write(0x54fe62 + 3 * 0x1c, bytes([12, m[1]]))
    b.mu.mem_write(PO_PEND + player, bytes([trap + 1]))
    b.mu.mem_write(0x560b20, struct.pack('<h', 7))
    b.stops = {0x49d1a0}; b.end = None
    esp = STACK - 0x400; b.mu.reg_write(UC_X86_REG_ESP, esp)
    b.mu.emu_start(PO_FALL, 0, count=2000000)
    if b.mu.mem_read(0x54fe65 + 3 * 0x1c, 1)[0] & 0x80: b.calls.append(('paraliza', 3))
    return b.end == 0x49d1a0 and b.r('ESP') == esp, b.quest(), b.trap(trap), b.calls
for nombre, kw, marca in [('cae: UI en su trampa objetivo -> marca +0xa', dict(player=UI), 1),
                          ('cae: el enemigo en esa trampa -> no marca', dict(player=ENEMY), 0),
                          ('cae: UI en otra trampa -> no marca', dict(player=UI, trap=8), 0),
                          ('cae: misión de otro tipo con el mismo número -> no marca', dict(player=UI, typ=10), 0)]:
    ok, q, t, calls = fall(**kw)
    check(nombre, ok and q[6] == marca and t[3] & 0x0f == 1 and t[3] & 0x80 and (('muere', 3) in calls or ('paraliza', 3) in calls), f'{q} {t} {calls}')

check('SAV: la misión activa y su estado están en el bloque guardado (0x536b30..0x5643c4)',
      0x536b30 <= 0x55edc4 and 0x55edc4 + 8 * 16 <= 0x5643c4 and 0x55ee44 + 8 <= 0x5643c4)

print('TODO OK' if all(res) else f'FALLAN {res.count(False)} DE {len(res)}')
sys.exit(0 if all(res) else 1)
