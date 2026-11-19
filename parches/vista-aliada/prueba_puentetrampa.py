# Prueba de juguete: al derribar un puente, sus trampas caen al agua (br_untrap de build.py, pedido del clan 18/11/2026).
# Uso: python prueba_puentetrampa.py [carpeta]   (por defecto la del juego de pruebas)
# Controles que deben sobrevivir: trampa fuera del puente, pozo (no trampa) sobre el puente, puente con 0 casillas.
# Sonido (1.0.266.0): la mina que cae suena "splash" (0x4465e0(0xd, -1); hasta 1.0.277.0 se usaba 0x18, que es Slayer) solo en la PC ([0x560b20]) de su dueño o de
# quien la había descubierto; control: una mina ajena y no descubierta cae sin sonar, y sin minas que caigan no suena.
import os as _os, sys as _sys; _sys.path.append(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..'))
from juego_pruebas import W3
import os, sys, re, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EIP

DIR = sys.argv[1] if len(sys.argv) > 1 else W3
STACK, RET = 0x1f0000, 0x100
PO_MAX, PO_REC = 64, 8
pe = pefile.PE(os.path.join(DIR, 'DarklordAV.exe'))
BASE, img = pe.OPTIONAL_HEADER.ImageBase, bytes(pe.get_memory_mapped_image())
def d32(va): return struct.unpack_from('<I', img, va - BASE)[0]
PO_SAVE = BASE + img.index(b'POZO' + bytes(4 + PO_MAX * PO_REC)); PO_N, PO_TAB = PO_SAVE + 4, PO_SAVE + 8
PO_MAP = PO_SAVE + 8 + PO_MAX * PO_REC + 4
# en br_razeapply: call br_drown; add esp, 8; push esi; call [br_untrap_ptr]; add esp, 4
m = [x.start() for x in re.finditer(rb'\x83\xc4\x08\x56\xff\x15(.{4})\x83\xc4\x04', img, re.S)]
assert len(m) == 1, m
BR_UNTRAP = d32(d32(BASE + m[0] + 6))
cod = img[BR_UNTRAP - BASE:BR_UNTRAP - BASE + 0x80]
BR_XY = struct.unpack_from('<I', cod, cod.index(b'\x3b\x14\x8d') + 3)[0]

mal = 0
def ver(nombre, r, esperado):
    global mal
    ok = r == esperado; mal += not ok
    print('OK ' if ok else 'MAL', nombre, '->', r)

def correr(regs, puente, local=0, sonidos=None):
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    size = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
    mu.mem_map(BASE, size); mu.mem_write(BASE, img[:size])
    mu.mem_map(0, 0x1000); mu.mem_map(0x100000, 0x100000)
    mu.mem_write(0x503e00, struct.pack('<hh', 40, 30)); mu.mem_write(0x503e06, b'\6')
    mu.mem_write(PO_N, struct.pack('<i', len(regs)))
    for i, r in enumerate(regs): mu.mem_write(PO_TAB + PO_REC * i, struct.pack('<hhBBBB', *r))
    for i, (x, y) in enumerate(puente): mu.mem_write(BR_XY + 4 * i, struct.pack('<hh', x, y))
    mu.mem_write(0x560b20, struct.pack('<h', local))
    def snd(m, a, size, _):   # 0x4465e0(sonido, -1): se anota y vuelve
        sp = m.reg_read(UC_X86_REG_ESP); ret, s1, s2 = struct.unpack('<Iii', m.mem_read(sp, 12))
        (sonidos if sonidos is not None else []).append((s1, s2)); m.reg_write(UC_X86_REG_ESP, sp + 4); m.reg_write(UC_X86_REG_EIP, ret)
    mu.hook_add(UC_HOOK_CODE, snd, begin=0x4465e0, end=0x4465e0)
    mu.mem_write(STACK, struct.pack('<II', RET, len(puente))); mu.reg_write(UC_X86_REG_ESP, STACK)
    mu.emu_start(BR_UNTRAP, RET, count=2000000)
    n = struct.unpack('<i', mu.mem_read(PO_N, 4))[0]
    t = sorted(struct.unpack('<hhBBBB', mu.mem_read(PO_TAB + PO_REC * i, PO_REC)) for i in range(n))
    mapa = {(x, y): mu.mem_read(PO_MAP + (y << 6) + x, 1)[0] for x in range(40) for y in range(30)}
    return t, {k for k, v in mapa.items() if v}

T = 2
puente = [(10, 5), (10, 6), (10, 7)]
regs = [(10, 5, T, 0, 1, 0), (3, 3, T, 0, 2, 1), (10, 6, 0, 0, 0, 0), (10, 7, T, 0x08, 1, 0), (20, 20, T, 0, 4, 2)]
t, m2 = correr(regs, puente)
ver('quedan la trampa de afuera, el pozo y la del (20,20)', t, sorted([regs[1], regs[2], regs[4]]))
ver('po_map rearmado', m2, {(3, 3), (10, 6), (20, 20)})
t, m2 = correr(regs, [])
ver('puente vacío: no toca nada', t, sorted(regs))
t, m2 = correr([(10, 5, T, 0, 1, 0)], puente)
ver('única trampa sobre el puente', t, [])
SPL = [(0xd, -1)]   # splash: sonido lógico 0xd (recurso 24); hasta 1.0.277.0 era 0x18 = Slayer (TAREAS 269)
for nombre, rr, local, esperado in (
        ('mina propia: suena', [(10, 5, T, 0, 0, 3)], 3, SPL),
        ('mina ajena descubierta por el local: suena', [(10, 5, T, 0, 1 << 3, 5)], 3, SPL),
        ('mina ajena no descubierta: no suena', [(10, 5, T, 0, 1 << 2, 5)], 3, []),
        ('dos minas propias: suena una vez', [(10, 5, T, 0, 0, 3), (10, 6, T, 0, 0, 3)], 3, SPL),
        ('mina fuera del puente: no suena', [(3, 3, T, 0, 0xff, 3)], 3, []),
        ('pozo sobre el puente: no suena', [(10, 5, 0, 0, 0xff, 3)], 3, [])):
    sn = []; correr(rr, puente, local, sn); ver(nombre, sn, esperado)
print('TODO OK' if not mal else f'{mal} MAL'); sys.exit(1 if mal else 0)
