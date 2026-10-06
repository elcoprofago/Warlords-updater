# Prueba de juguete del tope "Landing" (landcap) sobre el exe parcheado, en unicorn.
# Uso: python prueba_landcap.py [DarklordAV.exe]   (por defecto C:\Warlords3\DarklordAV.exe; armarlo antes con build.py)
# Stubs: 0x4411b0 (ejércitos en la casilla) y 0x49e770; termina en 0x49e4ae (pasa) o 0x49e4dd con código 4 (bloquea).
import sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

pe = pefile.PE(sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe'); BASE = pe.OPTIONAL_HEADER.ImageBase
img = bytes(pe.get_memory_mapped_image())
SIZE = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff

P = 1; GRP = P * 0x4f0; X, Y = 5, 6; SHIFT = 8
WATER, LAND = 3, 2

def run(count, occ, embarked=False, mode=0, landing=True, dest='water', building=False, bridge=False,
        noembark=(), carrier=False):
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(BASE, SIZE); mu.mem_write(BASE, img[:SIZE])
    mu.mem_map(0x100000, 0x10000)
    # stubs: 0x4411b0 -> ax = occ ; 0x49e770 -> al = 0
    mu.mem_write(0x4411b0, b'\x66\xb8' + struct.pack('<H', occ) + b'\xc3')
    mu.mem_write(0x49e770, b'\x31\xc0\xc3')
    mu.mem_write(0x503e06, bytes([SHIFT]))
    mu.mem_write(0x535f0c + WATER * 0x58, struct.pack('<H', 1))
    mu.mem_write(0x535f0c + LAND * 0x58, struct.pack('<H', 0))
    tile = ((Y * 10) << SHIFT) + X * 10 + 0x503e58
    w0 = (WATER if dest in ('water', 'port') else LAND) | (0x4000 if building else 0)
    mu.mem_write(tile, struct.pack('<HH', w0, 0x100 if bridge else 0))
    mu.mem_write(0x582158 + X * 0xa0 + Y, bytes([{'water': 0x80, 'port': 0xc0, 'land': 0x40}[dest]]))
    mu.mem_write(GRP + 0x56eaa8, struct.pack('<HHH', count, 8 if embarked else 0, mode))
    mu.mem_write(GRP + 0x56eab0, bytes(1 if i in noembark else 0 for i in range(8)))
    boat = 0x53c410 + (P * 16 + 15) * 0xfc + 0xb2
    mu.mem_write(boat, b'Ice\0\0\0\0\0\0' + ((b'LANDING\0\0') if landing else b'Bridge\0\0\0')
                 + (b'CARRIER\0\0' if carrier else b'\0' * 9))
    esp = 0x108000
    mu.mem_write(esp, b'\0' * 0x40)
    regs = dict(EAX=0x11111111, ECX=0x22222222, EDX=0x33333333, EBX=GRP, ESP=esp, EBP=P,
                ESI=0xabcd0000 | X, EDI=0xdcba0000 | Y)
    for k, v in regs.items(): mu.reg_write(globals()['UC_X86_REG_' + k], v)
    end = {}
    def hook(uc, addr, size, _):
        if addr in (0x49e4ae, 0x49e4dd):
            end['at'] = addr; uc.emu_stop()
    mu.hook_add(UC_HOOK_CODE, hook)
    mu.emu_start(0x49e4a7, 0x49e5ff, count=10000)
    code = struct.unpack('<H', mu.mem_read(esp + 0x16, 2))[0]
    after = {k: mu.reg_read(globals()['UC_X86_REG_' + k]) for k in ('EBX', 'EBP', 'ESI', 'EDI')}
    exp_esp = esp - 8 if end.get('at') == 0x49e4ae else esp   # pasa: push edi/esi pendientes (add esp,8 en 0x49e4ae)
    ok_regs = after == {k: regs[k] for k in after} and mu.reg_read(UC_X86_REG_ESP) == exp_esp
    return ('BLOQ' if end.get('at') == 0x49e4dd and code == 4 else 'PASA' if end.get('at') == 0x49e4ae else 'RARO'), ok_regs

casos = [
    ('6 embarcan, landing',              dict(count=6, occ=0), 'BLOQ'),
    ('5 embarcan, landing',              dict(count=5, occ=0), 'PASA'),
    ('6 embarcan, sin landing',          dict(count=6, occ=0, landing=False), 'PASA'),
    ('6 vuelan',                         dict(count=6, occ=0, mode=2), 'PASA'),
    ('6 a tierra',                       dict(count=6, occ=0, dest='land'), 'PASA'),
    ('6 a transbordo',                   dict(count=6, occ=0, dest='port'), 'PASA'),
    ('6 a agua con edificio',            dict(count=6, occ=0, building=True), 'PASA'),
    ('6 a agua con puente',              dict(count=6, occ=0, bridge=True), 'PASA'),
    ('6 naves (nadie embarca)',          dict(count=6, occ=0, noembark=range(6)), 'PASA'),
    ('6, 1 nave + 5 embarcan',           dict(count=6, occ=0, noembark=(0,)), 'BLOQ'),
    ('4 + 2 propios en el agua',         dict(count=4, occ=2), 'BLOQ'),
    ('3 + 2 propios en el agua',         dict(count=3, occ=2), 'PASA'),
    ('embarcados 8 a agua vacia',        dict(count=8, occ=0, embarked=True), 'PASA'),
    ('embarcados 3 + 3',                 dict(count=3, occ=3, embarked=True), 'BLOQ'),
    ('embarcados 3 + 2',                 dict(count=3, occ=2, embarked=True), 'PASA'),
    # barco con los dos bonos: tope de 6; el código 4 es el que forma el convoy
    ('landing+carrier: 3 + 4',           dict(count=3, occ=4, embarked=True, carrier=True), 'BLOQ'),
    ('landing+carrier: 3 + 3',           dict(count=3, occ=3, embarked=True, carrier=True), 'PASA'),
    ('landing+carrier: 7 embarcan',      dict(count=7, occ=0, carrier=True), 'BLOQ'),
    ('landing+carrier: 6 embarcan',      dict(count=6, occ=0, carrier=True), 'PASA'),
    # "Carrier" solo: sin tope propio (rige el del bando)
    ('carrier solo: 4 + 4',              dict(count=4, occ=4, embarked=True, landing=False, carrier=True), 'PASA'),
    ('carrier solo: 8 embarcan',         dict(count=8, occ=0, landing=False, carrier=True), 'PASA'),
]
mal = 0
for nombre, kw, esperado in casos:
    r, regs_ok = run(**kw)
    estado = 'OK ' if r == esperado and regs_ok else 'MAL'
    mal += estado == 'MAL'
    print(f'{estado} {nombre:32} {r} (esperado {esperado}) regs={"ok" if regs_ok else "ALTERADOS"}')
print('TODO OK' if not mal else f'{mal} MAL'); sys.exit(1 if mal else 0)
