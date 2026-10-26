# Prueba de juguete del camuflaje (bono de movimiento "camo"; cam_blit, vía crdraw en 0x459d0d) sobre el exe
# parcheado, en unicorn. Usa el banco de prueba_dianoche.py (mapa, vista y dn_pre para poner la noche).
# Uso: python prueba_camuflaje.py [DarklordAV.exe]   (por defecto C:\Warlords3\DarklordAV.exe; armarlo antes con build.py)
# Cada caso dibuja el ejército quieto de una celda (2ª pasada vía crdraw y 3ª pasada, globito, vía cam_blit3) y
# compara: la copia (0x4dd530, stub) con los mismos argumentos; o de noche, si todas las unidades del bando en la casilla
# tienen "camo", en su lugar el recoloreo (0x4ee3c0, stub) con esos argumentos y la tabla al 30 % (comparada con el
# mismo cálculo en Python). Y el Army Report (0x414d50): de noche no muestra el ejército camuflado ajeno.
# Controles: grupo mixto, grupo con héroe, unidades de otro bando en la misma casilla, de día, sin la opción.
import os, sys, struct
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prueba_dianoche.py'), encoding='utf-8').read()
exec(src.split('\nb = Bench()')[0])

def call_target(va):
    assert img[va - BASE] == 0xe8
    return struct.unpack_from('<i', img, va - BASE + 1)[0] + va + 5
CRDRAW = call_target(0x459d0d)
SITES3 = (0x45a14f, 0x45a18e, 0x45a267, 0x45a2ac, 0x45a2cc, 0x45a34a, 0x45a3a5)
BLIT3 = call_target(0x45a267)
assert all(call_target(va) == BLIT3 for va in SITES3)
TYPES = 0x53c410

pal = open(r'C:\Warlords3\war3.pal', 'rb').read()
rgb = [tuple(pal[3 * i:3 * i + 3]) for i in range(256)]
cand = [10] + [i for i in range(16, 245) if i != 187]
CAM = bytearray(range(256))
for i in range(256):
    if i == 11: continue
    t = tuple(o * (0.8 + 0.4 * sum(w * c for w, c in zip((0.3, 0.59, 0.11), rgb[i])) / 63) for o in (24, 28, 15))
    pool = range(48, 54) if i % 2 else cand   # la mitad de los tonos a verde oscuro: sin gris verdoso en la paleta
    CAM[i] = min(pool, key=lambda j: sum((a - c) ** 2 for a, c in zip(rgb[j], t)))

class Cam(Bench):
    def __init__(self):
        super().__init__()
        self.blits = []
        self.mu.mem_write(0x560758, bytes([1]))       # sin animaciones: crdraw va derecho a la copia
        self.mu.hook_add(UC_HOOK_CODE, self.hook2)

    def hook2(self, mu, addr, size, _):
        if addr == 0x4dd530:
            esp = mu.reg_read(UC_X86_REG_ESP)
            self.blits.append(struct.unpack('<8I', mu.mem_read(esp + 4, 32)))
            mu.reg_write(UC_X86_REG_EAX, 0x1234)
            self.ret(esp, 0)

    def bonus(self, p, slot, names):
        a = TYPES + (p * 16 + slot) * 0xfc + 0xb2
        self.mu.mem_write(a, b''.join(n.ljust(9, b'\0') for n in names + [b''] * (4 - len(names))))

    def units(self, lst):   # (x, y, bando, ranura)
        self.mu.mem_write(0x54fe50, struct.pack('<h', len(lst) + 1))
        for i, (x, y, p, s) in enumerate(lst, 1):
            a = 0x54fe50 + i * 0x1c
            self.mu.mem_write(a + 2, struct.pack('<hh', x, y))
            self.mu.mem_write(a + 0xe, struct.pack('<H', (p << 5) | s))
            self.mu.mem_write(a + 0x13, bytes([0x40]))
        self.army_list = [(x, y, p) for x, y, p, s in lst]

    def draw(self, x, y, owner, entry=None):
        mu = self.mu
        self.blits = []; self.calls = []
        c, r = x - VX, y - VY
        cell = CELLS + (r * VW + c) * 0x1c
        mu.mem_write(cell + 4, struct.pack('<H', owner))
        args = (0x2f + owner, 96, 48, 48, 48, 0x27, c * 48, r * 48)
        sp = STACK - 0x400
        mu.mem_write(sp, struct.pack('<I', END) + struct.pack('<8I', *args) + bytes(0x14) + struct.pack('<hh', c, r))
        mu.reg_write(UC_X86_REG_ESP, sp); mu.reg_write(UC_X86_REG_EBP, VIEW)
        cr, other = (cell, 0xd1d1) if entry is None else (0x5151, cell)   # 3ª pasada: la celda en edi
        mu.reg_write(UC_X86_REG_ESI, cr); mu.reg_write(UC_X86_REG_EDI, other); mu.reg_write(UC_X86_REG_EBX, 0xbbbb)
        mu.emu_start(entry or CRDRAW, 0, count=5_000_000)
        assert mu.reg_read(UC_X86_REG_EIP) == END
        assert mu.reg_read(UC_X86_REG_ESP) == sp + 4
        assert (mu.reg_read(UC_X86_REG_ESI), mu.reg_read(UC_X86_REG_EBP)) == (cr, VIEW)
        assert (mu.reg_read(UC_X86_REG_EBX), mu.reg_read(UC_X86_REG_EDI)) == (0xbbbb, other)
        if not self.calls:
            assert self.blits == [args], self.blits
            return False
        assert self.blits == [args], self.blits
        assert len(self.calls) == 1 and self.calls[0][:8] == args, self.calls
        tab = bytes(mu.mem_read(self.calls[0][8], 256))
        assert tab == bytes(CAM), 'tabla gris distinta del cálculo en Python'
        return True

b = Cam()
b.bonus(ME, 3, [b'landing', b'camo'])
b.bonus(ME, 4, [b'CaMo'])                 # sin distinguir mayúsculas
b.bonus(ME, 5, [b'camouflage'[:8]])       # otro nombre: no vale
b.bonus(ENEMY, 3, [b'camo'])
b.mu.mem_write(TYPES + (ME * 16 + 16) * 0xfc + 0xb2, b'camo'.ljust(9, b'\0'))   # ranura de héroe: no se mira
b.units([(12, 8, ME, 3), (12, 8, ME, 4),                  # todo camo
         (14, 8, ME, 3), (14, 8, ME, 5),                  # mixto
         (16, 8, ME, 3), (16, 8, ME, 16),                 # con héroe
         (18, 8, ENEMY, 3), (18, 8, ME, 5),               # el enemigo camo; otro bando sin camo en la casilla
         (20, 8, ME, 5)])                                 # sin camo
b.set(night=True); b.pre()
res = {k: b.draw(x, y, p) for k, (x, y, p) in {'camo': (12, 8, ME), 'mixto': (14, 8, ME), 'héroe': (16, 8, ME),
       'enemigo': (18, 8, ENEMY), 'sin': (20, 8, ME), 'vacía': (22, 9, ME)}.items()}
print('1) noche:', res)
EXP = {'camo': True, 'mixto': False, 'héroe': False, 'enemigo': True, 'sin': False, 'vacía': False}
assert res == EXP
res3 = {k: b.draw(x, y, p, BLIT3) for k, (x, y, p) in {'camo': (12, 8, ME), 'mixto': (14, 8, ME), 'héroe': (16, 8, ME),
        'enemigo': (18, 8, ENEMY), 'sin': (20, 8, ME), 'vacía': (22, 9, ME)}.items()}
print('1b) noche, 3ª pasada (globito, barra, iconos):', res3)
assert res3 == EXP
for night, opt, hid, name in ((False, True, False, 'día'), (True, False, False, 'sin opción'), (True, True, True, 'Hidden Map')):
    b.set(night=night, option=opt, hidden=hid); b.pre()
    for e in (None, BLIT3):
        assert not b.draw(12, 8, ME, e) and not b.draw(18, 8, ENEMY, e), name
print('2) día / sin opción / Hidden Map: solo la copia, sin camuflaje')

# Army Report: el minimapa 0x414d50 llama a 0x414e50 (stub) por cada ejército que muestra.
REP_OBJ = 0x118000
def report():
    mu = b.mu; shown = []
    def h(mu, addr, size, _):
        if addr == 0x414e50:
            esp = mu.reg_read(UC_X86_REG_ESP)
            a = struct.unpack('<4i', mu.mem_read(esp + 4, 16))
            shown.append((a[1] & 0xffff, a[2] & 0xffff, a[3] & 0xffff))
            b.ret(esp, 0x10)
    hh = mu.hook_add(UC_HOOK_CODE, h, begin=0x414e50, end=0x414e50)
    sp = STACK - 0x400
    mu.mem_write(sp, struct.pack('<II', END, 0x7777))
    mu.reg_write(UC_X86_REG_ESP, sp); mu.reg_write(UC_X86_REG_ECX, REP_OBJ)
    mu.reg_write(UC_X86_REG_EBX, 0xbbbb); mu.reg_write(UC_X86_REG_ESI, 0x5151); mu.reg_write(UC_X86_REG_EDI, 0xd1d1)
    mu.reg_write(UC_X86_REG_EBP, 0xb0b0)
    mu.emu_start(0x414d50, 0, count=5_000_000)
    mu.hook_del(hh)
    assert mu.reg_read(UC_X86_REG_EIP) == END and mu.reg_read(UC_X86_REG_ESP) == sp + 8
    assert [mu.reg_read(r) for r in (UC_X86_REG_EBX, UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP)] == [0xbbbb, 0x5151, 0xd1d1, 0xb0b0]
    return set(shown)
ALL = {(x, y, p) for x, y, p in b.army_list}
b.set(night=True); b.pre()
r = report()
print('3) Army Report de noche (mira el bando', ME, '):', sorted(ALL - r), 'ocultos')
assert r == ALL - {(18, 8, ENEMY)}, sorted(r)          # el enemigo todo camo se oculta; el propio camo se ve
b.mu.mem_write(0x560b20, struct.pack('<h', ENEMY)); b.pre()
r = report()
assert r == ALL - {(12, 8, ME)}, sorted(r)             # visto por el otro: se oculta el de ME todo camo
b.mu.mem_write(0x560b20, struct.pack('<h', ME))
b.set(night=False); b.pre()
assert report() == ALL
print('4) Army Report de día: todos')
gray = sum(1 for i in range(256) if i != 11 and CAM[i] != i)
print(f'5) tabla silueta: {gray} colores cambian')
print('TODO OK')
