# Prueba de juguete del pintado de la noche (dn_pre / dn_post) sobre el exe parcheado, en unicorn.
# Uso: python prueba_dianoche.py [DarklordAV.exe]   (por defecto C:\Warlords3\DarklordAV.exe; armarlo antes con build.py)
# Mapa de 30x30 de tierra con una ciudad 2x2 en (10,10), una ruina en (20,5), un sitio en (8,22), un puente en
# (5,20)-(6,20) y un ejército de quien mira en (15,17). Controles que no deben dar luz: un camino de tierra en (22,17),
# un puente derribado en (22,12) y un ejército enemigo en (24,8). La vista es de 20x15 desde (5,5).
# Se comparan la grilla de niveles, las celdas marcadas sucias y cada llamada al recoloreo (0x4ee3c0, stub) con el
# mismo cálculo hecho en Python. Después: sin cambios no se ensucia nada; mover el ejército ensucia solo su entorno;
# de día, con Hidden Map o sin la opción no se pinta nada y se ensucia lo que estaba oscuro.
# Minimapa (dn_mini, en 0x4114ef) de 100x125: cada fila de píxeles se recolorea (0x4ede30, stub) en tramos de igual
# nivel, con el nivel de la casilla del mapa entero; no toca la grilla de la vista; de día no pinta, y el cambio
# entre día y noche marca el minimapa para rearmar.
import sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

pe = pefile.PE(sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe'); BASE = pe.OPTIONAL_HEADER.ImageBase
img = bytes(pe.get_memory_mapped_image())
SIZE = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
def jmp_target(va):
    assert img[va - BASE] == 0xe9
    return va + 5 + struct.unpack_from('<i', img, va - BASE + 1)[0]
DN_PRE, DN_POST, DN_MINI = jmp_target(0x459790), jmp_target(0x45aa6e), jmp_target(0x4114ef)

N = 8; MIN = 1
MW = MH = 30; SHIFT = 8; WATER, LAND = 3, 2
VX, VY, VW, VH = 5, 5, 20, 15
ME, ENEMY = 1, 2
SHOPT, OPT, TURN = 0x53c38c + 25, 0x53c38e, 0x5032f8 + 0x30
STUB = 0x100000; STACK = 0x200000; END = 0x1fff00
VIEW = 0x110000; CELLS = 0x120000; SHEET = 0x130000; MINI = 0x138000; MMW, MMH = 100, 125

def tile_va(x, y): return ((y * 10) << SHIFT) + x * 10 + 0x503e58

class Bench:
    def __init__(self):
        mu = self.mu = Uc(UC_ARCH_X86, UC_MODE_32)
        mu.mem_map(BASE, SIZE); mu.mem_write(BASE, img[:SIZE])
        mu.mem_map(STUB, 0x40000); mu.mem_map(STACK - 0x10000, 0x10000)
        mu.mem_write(0x503e00, struct.pack('<HH', MW, MH)); mu.mem_write(0x503e06, bytes([SHIFT]))
        mu.mem_write(0x535f0c + WATER * 0x58, struct.pack('<H', 1))
        mu.mem_write(0x535f0c + LAND * 0x58, struct.pack('<H', 0))
        for y in range(MH):
            for x in range(MW):
                self.tile(x, y, LAND, 0)
        for x, y in ((10, 10), (11, 10), (10, 11), (11, 11)): self.tile(x, y, LAND, 3)
        self.tile(20, 5, LAND, 2); self.tile(8, 22, LAND, 4)
        self.tile(5, 20, WATER, 1); self.tile(6, 20, WATER, 1)
        self.tile(22, 17, LAND, 1)                                  # camino: no es luz
        self.tile(22, 12, WATER, 0, 0x80)                           # puente derribado: no es luz
        mu.mem_write(0x560b20, struct.pack('<h', ME))
        self.armies([(15, 17, ME), (24, 8, ENEMY)])
        mu.mem_write(VIEW + 0x20, struct.pack('<hh', VW, VH))
        mu.mem_write(VIEW + 0x28, struct.pack('<hh', VX, VY))
        mu.mem_write(VIEW + 0x40, struct.pack('<I', CELLS))
        mu.mem_write(SHEET + 8, struct.pack('<I', 1))
        self.calls = []; self.mcalls = []
        mu.mem_write(MINI + 0x20, struct.pack('<hh', MMW, MMH))
        mu.mem_write(0x57276c, struct.pack('<I', MINI))
        mu.hook_add(UC_HOOK_CODE, self.hook)
        self.set(night=True)

    def tile(self, x, y, typ, struct_, b9=0):
        self.mu.mem_write(tile_va(x, y), struct.pack('<HBB', typ, 0, struct_) + bytes(5) + bytes([b9]))

    def armies(self, lst):
        self.mu.mem_write(0x54fe50, struct.pack('<h', len(lst) + 1))
        for i, (x, y, p) in enumerate(lst, 1):
            a = 0x54fe50 + i * 0x1c
            self.mu.mem_write(a + 2, struct.pack('<hh', x, y))
            self.mu.mem_write(a + 0xe, struct.pack('<H', (p << 5) | 3))
            self.mu.mem_write(a + 0x13, bytes([0x40]))
        self.army_list = lst

    def set(self, night=True, hidden=False, option=True):
        self.mu.mem_write(SHOPT, bytes([2 if option else 0]))
        self.mu.mem_write(OPT, bytes([0x10 if hidden else 0]))
        self.mu.mem_write(TURN, struct.pack('<h', 4 if night else 5))
        self.lit = night and option and not hidden

    def hook(self, mu, addr, size, _):
        esp = mu.reg_read(UC_X86_REG_ESP)
        if addr in (0x45979a, END, 0x4114f7):
            mu.emu_stop()
        elif addr == 0x4e4a90:
            assert struct.unpack('<I', mu.mem_read(esp + 4, 4))[0] == 0x48
            mu.reg_write(UC_X86_REG_EAX, SHEET)
            self.ret(esp, 4)
        elif addr == 0x4dd3f0:
            raise AssertionError('no debía cargar la hoja')
        elif addr == 0x4ee3c0:
            self.calls.append(struct.unpack('<9I', mu.mem_read(esp + 4, 36)))
            self.ret(esp, 0)
        elif addr == 0x4ede30:
            self.mcalls.append(struct.unpack('<6I', mu.mem_read(esp + 4, 24)))
            self.ret(esp, 0)

    def ret(self, esp, n):
        r = struct.unpack('<I', self.mu.mem_read(esp, 4))[0]
        self.mu.reg_write(UC_X86_REG_ESP, esp + 4 + n); self.mu.reg_write(UC_X86_REG_EIP, r)

    def clear_dirty(self):
        for i in range(VW * VH):
            self.mu.mem_write(CELLS + i * 0x1c + 6, bytes([0]))

    def dirty(self):
        return {(i % VW, i // VW) for i in range(VW * VH) if self.mu.mem_read(CELLS + i * 0x1c + 6, 1)[0] & 0x20}

    def pre(self):
        mu = self.mu
        mu.reg_write(UC_X86_REG_ECX, VIEW)
        mu.reg_write(UC_X86_REG_ESP, STACK - 0x100)
        mu.mem_write(STACK - 0x100, struct.pack('<I', END))
        mu.emu_start(DN_PRE, 0, count=5_000_000)
        assert mu.reg_read(UC_X86_REG_EIP) == 0x45979a
        assert mu.reg_read(UC_X86_REG_ESP) == STACK - 0x100 - 0x14
        assert mu.reg_read(UC_X86_REG_ECX) == VIEW

    def post(self, full=False):
        mu = self.mu
        self.calls = []
        mu.mem_write(VIEW + 0x1a5, bytes([1 if full else 0]))
        sp = STACK - 0x200
        mu.mem_write(sp, struct.pack('<4I', 0xb0b0, 0xd1d1, 0x5151, 0xbbbb) + bytes(0x14) + struct.pack('<I', END))
        mu.reg_write(UC_X86_REG_ESP, sp); mu.reg_write(UC_X86_REG_EBP, VIEW)
        mu.emu_start(DN_POST, 0, count=5_000_000)
        assert mu.reg_read(UC_X86_REG_EIP) == END
        assert mu.reg_read(UC_X86_REG_EBP) == 0xb0b0 and mu.reg_read(UC_X86_REG_EDI) == 0xd1d1
        assert mu.reg_read(UC_X86_REG_ESI) == 0x5151 and mu.reg_read(UC_X86_REG_EBX) == 0xbbbb

    def mini(self):
        mu = self.mu
        self.mcalls = []
        sp = STACK - 0x300
        mu.mem_write(sp + 0x2c, struct.pack('<H', 0x7777))
        mu.reg_write(UC_X86_REG_ESP, sp); mu.reg_write(UC_X86_REG_ESI, MINI); mu.reg_write(UC_X86_REG_EBX, 0xbbbb)
        mu.emu_start(DN_MINI, 0, count=50_000_000)
        assert mu.reg_read(UC_X86_REG_EIP) == 0x4114f7
        assert mu.reg_read(UC_X86_REG_ESP) == sp + 0x20 and mu.reg_read(UC_X86_REG_CX) == 0x7777
        assert mu.reg_read(UC_X86_REG_ESI) == MINI and mu.reg_read(UC_X86_REG_EBX) == 0xbbbb

# ---- el mismo cálculo en Python
def level(b, x, y):
    lev = N
    for lx, ly, r0, round_ in lights(b):
        dx, dy = abs(x - lx), abs(y - ly)
        if round_:
            d = 0
            while dx * dx + dy * dy > d * d + d: d += 1   # raíz redondeada
        else:
            d = max(dx, dy) + min(dx, dy) // 2
        lev = min(lev, max(d - r0, 0) + MIN)
    return lev

def lights(b):
    out = []
    for x, y in ((10, 10), (11, 10), (10, 11), (11, 11)): out.append((x, y, 1, False))
    out += [(20, 5, 0, True), (8, 22, 0, True), (5, 20, 0, True), (6, 20, 0, True)]
    out += [(x, y, 1, True) for x, y, p in b.army_list if p == ME]
    return out

def grid(b):
    g = {}
    for gy in range(-1, VH + 1):
        for gx in range(-1, VW + 1):
            if not b.lit: g[gx, gy] = 0; continue
            g[gx, gy] = level(b, VX + gx, VY + gy)
    return g

TAB = None
def edges(b, g):
    tab = struct.unpack('256b', img[0x4fbfc8 - BASE:0x4fbfc8 - BASE + 256])
    nb = list(zip((0, 1, 1, 1, 0, -1, -1, -1), (-1, -1, 0, 1, 1, 1, 0, -1)))
    out = []
    for r in range(VH):
        for c in range(VW):
            for k in range(1, g[c, r] + 1):
                m = sum(1 << i for i, (dx, dy) in enumerate(nb) if g[c + dx, r + dy] >= k)
                e = tab[m]
                if e >= 0: out.append((c, r, k, e))
    return out

def check_calls(b, g, cells=None):
    exp = [(c, r, e) for c, r, k, e in edges(b, g) if cells is None or (c, r) in cells]
    got = []
    tabs = set()
    for a in b.calls:
        sheet, sx, sy, w, h, z, x, y, t = a
        assert (sheet, w, h, z) == (0x48, 48, 48, 0x27), a
        assert sx % 49 == 0 and sy % 49 == 0 and x % 48 == 0 and y % 48 == 0
        e = sx // 49 + 8 * (sy // 49 - 2)
        got.append((x // 48, y // 48, e)); tabs.add(t)
    assert got == exp, (len(got), len(exp), [g_ for g_ in got if g_ not in exp][:5], [e for e in exp if e not in got][:5])
    assert len(tabs) <= 1
    return len(got)

def changed(g0, g1):
    return {(c, r) for r in range(VH) for c in range(VW)
            if any(g0[c + dx, r + dy] != g1[c + dx, r + dy] for dx in (-1, 0, 1) for dy in (-1, 0, 1))}

b = Bench()
zero = {k: 0 for k in grid(b)}
# 1) primera noche: todo lo oscuro (o vecino de lo oscuro) queda sucio, y el pintado sigue al cálculo
b.pre()
g = grid(b)
assert b.dirty() == changed(zero, g), 'sucias 1'
b.post()
n = check_calls(b, g, b.dirty())
print(f'1) noche: {len(b.dirty())} celdas sucias, {n} pasadas de recoloreo')
assert g[15 - VX, 17 - VY] == MIN and g[10 - VX, 10 - VY] == MIN and g[20 - VX, 5 - VY] == MIN
assert g[24 - VX, 8 - VY] > MIN, 'el ejército enemigo no debe dar luz'
assert g[22 - VX, 17 - VY] > MIN and g[22 - VX, 12 - VY] > MIN, 'camino y puente derribado no deben dar luz'
# 2) sin cambios: nada sucio y nada que pintar
b.clear_dirty(); b.pre(); assert b.dirty() == set(), 'sucias 2'
b.post(); assert b.calls == [], 'pintó sin celdas sucias'
# 3) redibujo entero ([vista+0x1a5]): pinta todo
b.post(full=True); n = check_calls(b, g); print(f'3) redibujo entero: {n} pasadas')
# 4) el ejército se mueve: solo se ensucia su entorno
b.armies([(18, 12, ME), (24, 8, ENEMY)]); b.clear_dirty(); b.pre()
g2 = grid(b); assert b.dirty() == changed(g, g2) and b.dirty(), 'sucias 4'
b.post(); check_calls(b, g2, b.dirty()); print(f'4) movida: {len(b.dirty())} celdas sucias')
# 5) de día, con Hidden Map, o sin la opción: no pinta y ensucia lo que estaba oscuro
for kw in (dict(night=False), dict(hidden=True), dict(option=False)):
    b.set(**{'night': True, **kw}); b.clear_dirty(); b.pre()
    g3 = grid(b); assert all(v == 0 for v in g3.values())
    assert b.dirty() == changed(g2, g3), ('sucias 5', kw)
    b.post(full=True); assert b.calls == [], kw
    b.set(night=True); b.clear_dirty(); b.pre(); assert b.dirty() == changed(g3, g2); g2 = grid(b)
print('5) día / Hidden Map / sin opción: OK')
# 6) minimapa: tramos de igual nivel por fila, tablas compuestas, y la vista intacta
b.set(night=True); b.pre(); g = grid(b)
lev = [[level(b, x, y) for x in range(MW)] for y in range(MH)]
exp = []
for py in range(MMH):
    row = [lev[py * MH // MMH][px * MW // MMW] for px in range(MMW)]
    px = 0
    while px < MMW:
        s0 = px
        while px < MMW and row[px] == row[s0]: px += 1
        exp.append((s0, py, px - s0, row[s0]))
b.mini()
assert all(c[0] == 0x28 and c[4] == 1 for c in b.mcalls)
mt = b.mcalls[0][5] - exp[0][3] * 256
got = [(x, y, w, (t - mt) // 256) for sheet, x, y, w, h, t in b.mcalls]
assert got == exp, ([e for e in got if e not in exp][:5], [e for e in exp if e not in got][:5])
tabs = [bytes(b.mu.mem_read(mt + 256 * L, 256)) for L in range(N + 1)]
assert tabs[0] == bytes(range(256)) and all(tabs[L + 1] == bytes(tabs[1][c] for c in tabs[L]) for L in range(N))
assert tabs[1] != tabs[0]
b.post(full=True); check_calls(b, g)
print(f'6) minimapa: {len(got)} tramos de recoloreo')
# 7) minimapa de día / Hidden Map / sin opción: nada; el cambio día<->noche lo marca para rearmar
for kw in (dict(night=False), dict(hidden=True), dict(option=False)):
    b.set(**{'night': True, **kw}); b.mini(); assert b.mcalls == [], kw
b.set(night=True); b.pre()
for night, expect in ((False, 1), (False, 0), (True, 1), (True, 0)):
    b.mu.mem_write(MINI + 0xc, struct.pack('<I', 0)); b.set(night=night); b.pre()
    assert struct.unpack('<I', b.mu.mem_read(MINI + 0xc, 4))[0] == expect, (night, expect)
print('7) minimapa de día / Hidden Map / sin opción / marca de rearmado: OK')
print('TODO OK')
