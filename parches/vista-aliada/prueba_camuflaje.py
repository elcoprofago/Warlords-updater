# Prueba de juguete del camuflaje (bono de movimiento "camo"; cam_blit, vía crdraw en 0x459d0d) sobre el exe
# parcheado, en unicorn. Usa el banco de prueba_dianoche.py (mapa, vista y dn_pre para poner la noche).
# Uso: python prueba_camuflaje.py [DarklordAV.exe]   (por defecto C:\Warlords3\DarklordAV.exe; armarlo antes con build.py)
# Cada caso dibuja el ejército quieto de una celda y compara: la copia (0x4dd530, stub) siempre, con los mismos
# argumentos; y de noche, si todas las unidades del bando en la casilla tienen "camo", el recoloreo (0x4ee3c0, stub)
# con esos mismos argumentos y la tabla gris (comparada con el mismo cálculo en Python).
# Controles: grupo mixto, grupo con héroe, unidades de otro bando en la misma casilla, de día, sin la opción.
import os, sys, struct
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prueba_dianoche.py'), encoding='utf-8').read()
exec(src.split('\nb = Bench()')[0])

CRDRAW = struct.unpack_from('<i', img, 0x459d0d - BASE + 1)[0] + 0x459d12
assert img[0x459d0d - BASE] == 0xe8
TYPES = 0x53c410

pal = open(r'C:\Warlords3\war3.pal', 'rb').read()
rgb = [tuple(pal[3 * i:3 * i + 3]) for i in range(256)]
cand = [10] + [i for i in range(16, 245) if i != 187]
CAM = bytearray(range(256))
for i in range(256):
    if i == 11: continue
    t = tuple(c * 0.4 + 32 * 0.6 for c in rgb[i])
    CAM[i] = min(cand, key=lambda j: sum((a - c) ** 2 for a, c in zip(rgb[j], t)))

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

    def draw(self, x, y, owner):
        mu = self.mu
        self.blits = []; self.calls = []
        c, r = x - VX, y - VY
        cell = CELLS + (r * VW + c) * 0x1c
        mu.mem_write(cell + 4, struct.pack('<H', owner))
        args = (0x2f + owner, 96, 48, 48, 48, 0x27, c * 48, r * 48)
        sp = STACK - 0x400
        mu.mem_write(sp, struct.pack('<I', END) + struct.pack('<8I', *args) + bytes(0x14) + struct.pack('<hh', c, r))
        mu.reg_write(UC_X86_REG_ESP, sp); mu.reg_write(UC_X86_REG_ESI, cell); mu.reg_write(UC_X86_REG_EBP, VIEW)
        mu.reg_write(UC_X86_REG_EBX, 0xbbbb); mu.reg_write(UC_X86_REG_EDI, 0xd1d1)
        mu.emu_start(CRDRAW, 0, count=5_000_000)
        assert mu.reg_read(UC_X86_REG_EIP) == END
        assert mu.reg_read(UC_X86_REG_ESP) == sp + 4
        assert (mu.reg_read(UC_X86_REG_ESI), mu.reg_read(UC_X86_REG_EBP)) == (cell, VIEW)
        assert (mu.reg_read(UC_X86_REG_EBX), mu.reg_read(UC_X86_REG_EDI)) == (0xbbbb, 0xd1d1)
        assert self.blits == [args], self.blits
        if not self.calls: return False
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
assert res == {'camo': True, 'mixto': False, 'héroe': False, 'enemigo': True, 'sin': False, 'vacía': False}
for night, opt, hid, name in ((False, True, False, 'día'), (True, False, False, 'sin opción'), (True, True, True, 'Hidden Map')):
    b.set(night=night, option=opt, hidden=hid); b.pre()
    assert not b.draw(12, 8, ME) and not b.draw(18, 8, ENEMY), name
print('2) día / sin opción / Hidden Map: solo la copia, sin gris')
gray = sum(1 for i in range(256) if i != 11 and CAM[i] != i)
print(f'3) tabla gris: {gray} colores cambian')
print('TODO OK')
