# Prueba de juguete del efecto noche de las clases monster, demon y undead (nm_kind, nm_unit en 0x46787d, nm_grp en 0x46907c) sobre el exe parcheado,
# en unicorn. Uso: python prueba_nightmare.py [DarklordAV.exe]   (por defecto C:\Warlords3\DarklordAV.exe; armarlo antes con build.py)
# Arma registros de tipo en la tabla 0x53c410 y compara el resultado con el mismo cálculo en Python: el sorteo de la
# noche (FNV-1a de la vuelta y los nombres), la lista de opciones de cada unidad (fuerza, hits, bono si tiene uno,
# habilidad si tiene una que cuente) y el +2 en la ficha (+3, +4) o en una copia del registro (+0xdf, +0xe8).
# Controles: de día, sin la opción, otra clase (orc, dragon), habilidad que no cuenta, y el registro real intacto.
import sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

pe = pefile.PE(sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe'); BASE = pe.OPTIONAL_HEADER.ImageBase
img = bytes(pe.get_memory_mapped_image())
SIZE = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
def jmp_target(va):
    assert img[va - BASE] == 0xe9
    return va + 5 + struct.unpack_from('<i', img, va - BASE + 1)[0]
NM_UNIT, NM_GRP = jmp_target(0x46787d), jmp_target(0x46907c)
SHOPT, TURN = 0x53c38c + 25, 0x5032f8 + 0x30
TYPES = 0x53c410
STACK = 0x200000; END = 0x1fff00; ENTRY = 0x150000
M = 0xffffffff

mu = Uc(UC_ARCH_X86, UC_MODE_32)
mu.mem_map(BASE, SIZE); mu.mem_write(BASE, img[:SIZE])
mu.mem_map(STACK - 0x10000, 0x10000); mu.mem_map(ENTRY, 0x1000)
stops = {0x467885, 0x469083, END}
mu.hook_add(UC_HOOK_CODE, lambda mu, a, s, _: mu.emu_stop() if a in stops else None)

def rec(slot, side=0): return TYPES + (side * 16 + slot) * 0xfc
def mkrec(slot, name, bonus=(), subs=(), cb=(b'', 0), ab=(0, 0), side=0):
    r = bytearray(0xfc)
    r[0x90:0x90 + len(name)] = name
    r[0x9a] = 5; r[0x9c] = 2
    for k, s in enumerate(subs): r[0xa0 + 9 * k:0xa0 + 9 * k + len(s)] = s
    for k, s in enumerate(bonus): r[0xb2 + 9 * k:0xb2 + 9 * k + len(s)] = s
    r[0xd6:0xd6 + len(cb[0])] = cb[0]; r[0xdf] = cb[1]
    struct.pack_into('<hh', r, 0xe6, *ab)
    mu.mem_write(rec(slot, side), bytes(r))
    return rec(slot, side)

def setn(night=True, option=True, turn=None):
    mu.mem_write(SHOPT, bytes([2 if option else 0]))
    mu.mem_write(TURN, struct.pack('<h', turn if turn is not None else (6 if night else 7)))

def draw():
    t = struct.unpack('<H', mu.mem_read(TURN, 2))[0]
    h = ((t * 0x9e3779b9) & M) ^ 0x811c9dc5
    names = bytes(mu.mem_read(TYPES + 0x90, 128 * 0xfc))
    for i in range(128):
        for b in names[i * 0xfc:i * 0xfc + 10]:
            h = ((h ^ b) * 0x01000193) & M
    h ^= h >> 15; h = (h * 0x2c1b3c6d) & M; h ^= h >> 12
    return h

CODES = {1, 2, 3, 4, 5, 6, 26, 27, 28, 30, 32, 33, 34, 37, 38, 39, 40, 41, 42, 43, 52, 53, 54}
def expect(r):   # 0 nada, 1 fuerza, 2 hits, 3 bono, 4 habilidad
    d = bytes(mu.mem_read(r, 0xfc))
    sh = mu.mem_read(SHOPT, 1)[0]; t = struct.unpack('<H', mu.mem_read(TURN, 2))[0]
    if not sh & 2 or t & 1: return 0
    low = lambda o: d[o:o + 9].split(b'\0')[0].lower()
    if not {b'monster', b'demon', b'undead'} & {low(0xa0), low(0xa9)}: return 0
    opts = [1, 2]
    if d[0xdf] and d[0xd6] and low(0xd6) != b'none': opts.append(3)
    code, val = struct.unpack_from('<hh', d, 0xe6)
    if val and 0 <= code < 64 and code in CODES: opts.append(4)
    return opts[draw() % len(opts)]

def unit(r):
    sp = STACK - 0x400
    mu.mem_write(sp, bytes(0x40))
    mu.mem_write(ENTRY, bytes(range(0x20)))
    regs = {UC_X86_REG_EAX: r, UC_X86_REG_ESI: ENTRY, UC_X86_REG_EDI: 0xd1d1, UC_X86_REG_EBX: 0xbbbb,
            UC_X86_REG_EBP: 0xb0b0, UC_X86_REG_EDX: 0xeded, UC_X86_REG_ESP: sp}
    for k, v in regs.items(): mu.reg_write(k, v)
    real = bytes(mu.mem_read(r, 0xfc))
    mu.emu_start(NM_UNIT, 0, count=1_000_000)
    assert mu.reg_read(UC_X86_REG_EIP) == 0x467885 and mu.reg_read(UC_X86_REG_ESP) == sp
    for k in (UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBX, UC_X86_REG_EBP): assert mu.reg_read(k) == regs[k]
    assert bytes(mu.mem_read(r, 0xfc)) == real, 'tocó el registro real'
    p = struct.unpack('<I', mu.mem_read(sp + 0x30, 4))[0]
    assert mu.reg_read(UC_X86_REG_ECX) == p
    e = bytes(mu.mem_read(ENTRY, 0x20))
    diff = [i for i in range(0x20) if e[i] != i]
    if p == r:
        if diff == [3]: assert e[3] == 5; return 1
        if diff == [4]: assert e[4] == 6; return 2
        assert diff == []; return 0
    assert diff == []
    c = bytes(mu.mem_read(p, 0xfc))
    d = [i for i in range(0xfc) if c[i] != real[i]]
    if d == [0xdf]: assert c[0xdf] == real[0xdf] + 2; return 3
    assert d in ([0xe8], [0xe8, 0xe9])
    assert struct.unpack_from('<h', c, 0xe8)[0] == struct.unpack_from('<h', real, 0xe8)[0] + 2
    return 4

def grp(r):
    sp = STACK - 0x400
    regs = {UC_X86_REG_EAX: 0xa0a0, UC_X86_REG_ECX: r, UC_X86_REG_ESI: 0x5151, UC_X86_REG_EDI: 0xd1d1,
            UC_X86_REG_EBX: 0xbbbb, UC_X86_REG_EBP: 0xb0b0, UC_X86_REG_ESP: sp}
    for k, v in regs.items(): mu.reg_write(k, v)
    real = bytes(mu.mem_read(r, 0xfc))
    mu.emu_start(NM_GRP, 0, count=1_000_000)
    assert mu.reg_read(UC_X86_REG_EIP) == 0x469083 and mu.reg_read(UC_X86_REG_ESP) == sp
    for k in (UC_X86_REG_EAX, UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBX, UC_X86_REG_EBP): assert mu.reg_read(k) == regs[k]
    assert bytes(mu.mem_read(r, 0xfc)) == real
    c = mu.reg_read(UC_X86_REG_ECX)
    assert mu.reg_read(UC_X86_REG_EDX) == struct.unpack_from('<h', real, 0xe6)[0] & M
    if c == r: return False
    v = struct.unpack('<h', mu.mem_read(c + 0xe8, 2))[0]
    assert v == struct.unpack_from('<h', real, 0xe8)[0] + 2
    return True

NM = [b'landing']   # los bonos de movimiento ya no cuentan
recs = {
    'solo fuerza/hits':  mkrec(1, b'Wolves', NM, [b'monster']),
    'con bono':          mkrec(2, b'Wraiths', [], [b'human', b'Monster'], (b'city', 1)),
    'con habilidad':     mkrec(3, b'Dragons', NM, [b'monster'], ab=(2, 1)),
    'todo':              mkrec(4, b'Demons', NM, [b'monster'], (b'vs elves', 2), (38, 3)),
    'bono none':         mkrec(5, b'Ghosts', NM, [b'monster'], (b'none', 2)),
    'hab. que no cuenta': mkrec(6, b'Spiders', NM, [b'monster'], ab=(51, 1)),
    'demon':             mkrec(7, b'Devils', [], [b'DEMON'], (b'city', 1), (2, 1)),
    'undead':            mkrec(9, b'Skeletons', [], [b'infantry', b'undead'], ab=(3, 1)),
    'orc':               mkrec(8, b'Orcs', NM, [b'orc', b'infantry'], ab=(2, 1)),
    'dragon':            mkrec(10, b'Red Drag', [], [b'dragon', b'flying'], (b'city', 1), (2, 1)),
    'enemigo':           mkrec(1, b'Imps', NM, [b'demon'], (b'city', 2), (3, 2), side=1),
}
NEVER = {'orc', 'dragon'}
seen = {k: set() for k in recs}
for turn in range(2, 80):
    setn(turn=turn)
    for k, r in recs.items():
        e = expect(r); u = unit(r); g = grp(r)
        assert u == e, (turn, k, u, e)
        assert g == (e == 4), (turn, k, g, e)
        seen[k].add(u)
print('1) noches y días de las vueltas 2..79, por unidad:', {k: sorted(v) for k, v in seen.items()})
for k in recs:
    assert 0 in seen[k]                            # de día nunca
    if k in NEVER: assert seen[k] == {0}, k
assert seen['solo fuerza/hits'] == {0, 1, 2} and seen['bono none'] == {0, 1, 2} and seen['hab. que no cuenta'] == {0, 1, 2}
assert seen['con bono'] == {0, 1, 2, 3} and seen['con habilidad'] == {0, 1, 2, 4} and seen['todo'] == {0, 1, 2, 3, 4}
assert seen['demon'] == {0, 1, 2, 3, 4} and seen['undead'] == {0, 1, 2, 4}
setn(night=True, option=False)
assert all(unit(r) == 0 and not grp(r) for r in recs.values())
print('2) sin la opción Day/Night: nada')
# un mismo sorteo por noche: cambiar otro nombre de tipo cambia el sorteo; repetir la misma noche no
setn(turn=10); a = [unit(r) for r in recs.values()]; assert a == [unit(r) for r in recs.values()]
print('3) la misma noche da lo mismo cada vez:', a)
print('TODO OK')
