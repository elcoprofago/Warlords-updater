# Prueba de juguete de la IA que siembra trampas (tr_ai de build.py, paso 5.3 de ia\PENDIENTE-ia-innovaciones.md),
# en unicorn. Uso: python prueba_iatrampas.py [carpeta]   (por defecto C:\Warlords3; la que se le pasó a build.py)
# tr_ai se encuentra desde el parche de 0x40cc3f (call tr_me; tr_me empieza con call tr_ai). Se interceptan
# 0x4974a0 (distancia: la de rey), 0x497a90 (enemigo visible más cercano: lo fija el caso), 0x4b65e0 (costo),
# 0x4dd3b0 (red) e ia_evt. reccomb y pg_ok corren de verdad.
# Controles: sin el bono, héroe con el bono, casilla de ciudad, lejos de ciudad propia, ciudad propia muerta o de
# otro, enemigo lejos, casilla ocupada, tabla llena, sin oro (con y sin la reserva), ya sembró este turno, bando
# humano, sin IA.INI, color con la IA original.
import os, sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

DIR = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3'
STACK, RET = 0x1f0000, 0x100
PO_MAX, PO_REC = 64, 8
pe = pefile.PE(os.path.join(DIR, 'DarklordAV.exe'))
BASE, img = pe.OPTIONAL_HEADER.ImageBase, bytes(pe.get_memory_mapped_image())
def d32(va): return struct.unpack_from('<I', img, va - BASE)[0]
def dest(va, n=1): return va + n + 4 + struct.unpack_from('<i', img, va - BASE + n)[0]
def buscar(desde, patron, hasta=0x400): return BASE + img.index(patron, desde - BASE, desde - BASE + hasta)
PO_SAVE = BASE + img.index(b'POZO' + bytes(4 + PO_MAX * PO_REC)); PO_N, PO_TAB = PO_SAVE + 4, PO_SAVE + 8
PO_MAP = PO_SAVE + 8 + PO_MAX * PO_REC + 4
assert img[0x40cc3f - BASE] == 0xe8
TR_ME = dest(0x40cc3f); assert img[TR_ME - BASE] == 0xe8
TR_AI = dest(TR_ME)
assert img[TR_AI - BASE:TR_AI - BASE + 6] == bytes.fromhex('6083ec10803d'), img[TR_AI - BASE:TR_AI - BASE + 8].hex()
IA_ON = d32(TR_AI + 6)
IA_MODE = d32(buscar(TR_AI, b'\x80\xbb') + 2)
TRA_LAST = d32(buscar(TR_AI, b'\x39\x04\x9d') + 3)
IA_EVT = dest(buscar(TR_AI, b'\x6a\x29\xe8') + 2)
assert IA_EVT == dest(buscar(TR_AI, b'\x6a\x2a\xe8') + 2)
STK = 0x150000
TURNO = 7

mal = 0
def ver(nombre, r, esperado):
    global mal
    ok = r == esperado
    mal += not ok
    print('OK ' if ok else 'MAL', nombre, '->', r)

def casilla(x, y): return 0x503e58 + ((y * 10) << 6) + x * 10
def sg(v): return struct.unpack('<i', struct.pack('<I', v & 0xffffffff))[0]
def caso(ejs=((3, 'Trap'),), x=5, y=7, p=2, humano=False, ia_on=1, modo=1, oro=100, mant=10, costo=20,
         enemigo=8, ciudades=((7, 7, 1, 2),), urb=(), regs=(), ultimo=0):
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    size = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
    mu.mem_map(BASE, size); mu.mem_write(BASE, img[:size])
    mu.mem_map(0, 0x1000); mu.mem_map(0x100000, 0x100000)
    mu.mem_write(0x503e00, struct.pack('<hh', 40, 30)); mu.mem_write(0x503e06, b'\6')
    for yy in range(30):
        for xx in range(40):
            mu.mem_write(casilla(xx, yy), struct.pack('<HHB', 0, 1, 0))
    for ux, uy in urb:
        mu.mem_write(casilla(ux, uy) + 3, bytes([3]))
    mu.mem_write(PO_N, struct.pack('<i', len(regs)))
    for i, r in enumerate(regs):
        mu.mem_write(PO_TAB + PO_REC * i, struct.pack('<hhBBBB', *r))
        mu.mem_write(PO_MAP + (r[1] << 6) + r[0], bytes([i + 1]))
    mu.mem_write(IA_ON, bytes([ia_on])); mu.mem_write(IA_MODE, bytes([modo] * 8))
    pp = min(p, 7)
    mu.mem_write(TRA_LAST + 4 * pp, struct.pack('<i', ultimo))
    mu.mem_write(0x4fb0ec, struct.pack('<h', p)); mu.mem_write(0x503328, struct.pack('<h', TURNO))
    mu.mem_write(0x536c12 + pp * 0x1f8, struct.pack('<h', -1 if humano else 0))
    mu.mem_write(0x536c14 + pp * 0x1f8, struct.pack('<h', oro))
    mu.mem_write(0x5643d8 + 2 * pp, struct.pack('<h', mant))
    mu.mem_write(0x537e2a, struct.pack('<h', len(ciudades)))
    for i, (cx, cy, viva, dueno) in enumerate(ciudades):
        c = 0x537e2c + i * 0xde
        mu.mem_write(c, struct.pack('<hh', cx, cy)); mu.mem_write(c + 0xa4, bytes([viva, dueno]))
    pila = list(range(1, len(ejs) + 1)) + [-1] * (8 - len(ejs))
    mu.mem_write(STK + 0xc, struct.pack('<8h', *pila)); mu.mem_write(0x5020d4, struct.pack('<I', STK))
    for i, (ranura, comb) in enumerate(ejs, 1):
        a = 0x54fe50 + i * 0x1c
        mu.mem_write(a + 2, struct.pack('<hh', x, y)); mu.mem_write(a + 0xe, struct.pack('<H', ranura | pp << 5))
        if ranura < 16:
            rec = 0x53c410 + ((pp << 4) + ranura) * 0xfc
            mu.mem_write(rec + 0xd6, comb.encode().ljust(9, b'\0'))
    paquetes, eventos = [], []
    def interceptar(addr, fn):
        def g(mu, a, size, _):
            sp = mu.reg_read(UC_X86_REG_ESP)
            ret, *args = struct.unpack('<6I', mu.mem_read(sp, 24))
            mu.reg_write(UC_X86_REG_EAX, (fn(args) or 0) & 0xffffffff)
            mu.reg_write(UC_X86_REG_ESP, sp + 4); mu.reg_write(UC_X86_REG_EIP, ret)
        mu.hook_add(UC_HOOK_CODE, g, begin=addr, end=addr)
    interceptar(0x4974a0, lambda a: max(abs(sg(a[0]) - sg(a[2])), abs(sg(a[1]) - sg(a[3]))))
    interceptar(0x497a90, lambda a: enemigo)
    interceptar(0x4b65e0, lambda a: costo if (a[0] & 0xffff) == 0x7fff and (a[1] & 0xffff) == p else 9999)
    interceptar(0x4dd3b0, lambda a: paquetes.append((a[0], struct.unpack('<4h', mu.mem_read(a[1], 8)), a[2])))
    interceptar(IA_EVT, lambda a: eventos.append(tuple(sg(v) for v in a[:5])))
    regs0 = [0x11, 0x22, 0x33, 0x44, 0x55, 0x66]
    rr = (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_ESI, UC_X86_REG_EDI)
    for r, v in zip(rr, regs0): mu.reg_write(r, v)
    mu.reg_write(UC_X86_REG_EBP, 0x77)
    mu.mem_write(STACK, struct.pack('<I', RET)); mu.reg_write(UC_X86_REG_ESP, STACK)
    mu.emu_start(TR_AI, RET, count=2000000)
    intacto = [mu.reg_read(r) for r in rr] == regs0 and mu.reg_read(UC_X86_REG_EBP) == 0x77 \
        and mu.reg_read(UC_X86_REG_ESP) == STACK + 4
    ultimo = struct.unpack('<i', mu.mem_read(TRA_LAST + 4 * pp, 4))[0]
    return paquetes, eventos, ultimo, intacto

SI = ([(0x2a3, (2, 5, 7, 0), 8)], [(41, 2, 5, 7, 20)], TURNO + 1, True)
def no(motivo): return ([], [(42, 2, 5, 7, motivo)], 0, True)
NADA = ([], [], 0, True)
print('-- siembra')
ver('pila con "Trap" junto a su ciudad y enemigo cerca: TR_PKT (2, 5, 7), evento 41, TRA_LAST, registros intactos', caso(), SI)
ver('  "Trap" en el segundo ejército, el líder sin bono', caso(ejs=((2, ''), (4, 'TRAP'))), SI)
ver('  a 3 casillas justas de la ciudad', caso(ciudades=((8, 7, 1, 2),)), SI)
ver('  enemigo a 12 justos', caso(enemigo=12), SI)
ver('  oro justo: costo + 2 x mantenimiento', caso(oro=40), SI)
ver('  sin mantenimiento, oro = costo', caso(oro=20, mant=0), SI)
ver('  la más cercana de varias ciudades (otra lejos, una de otro al lado)',
    caso(ciudades=((30, 20, 1, 2), (5, 6, 1, 3), (6, 8, 1, 2))), SI)
ver('  un pozo en otra casilla no molesta', caso(regs=[(6, 7, 0, 0, 0, 0xff)])[0], SI[0])
ver('  sembró el turno anterior', caso(ultimo=TURNO), SI)
print('-- no siembra (evento 42 con el motivo)')
ver('control: sin el bono (sin evento)', caso(ejs=((3, ''),)), NADA)
ver('control: héroe con "Trap" (sin evento)', caso(ejs=((0x10, 'Trap'),)), NADA)
ver('casilla de ciudad: motivo 1', caso(urb=[(5, 7)]), no(1))
ver('a 4 de la ciudad: motivo 2', caso(ciudades=((9, 7, 1, 2),)), no(2))
ver('  ciudad propia arrasada: motivo 2', caso(ciudades=((6, 7, 0, 2),)), no(2))
ver('  ciudad de otro: motivo 2', caso(ciudades=((6, 7, 1, 3),)), no(2))
ver('  sin ciudades: motivo 2', caso(ciudades=()), no(2))
ver('enemigo a 13: motivo 3', caso(enemigo=13), no(3))
ver('casilla con un pozo: motivo 4', caso(regs=[(5, 7, 0, 0, 0, 0xff)]), no(4))
ver('  con su propia trampa (no apila): motivo 4', caso(regs=[(5, 7, 2, 0, 4, 2)]), no(4))
ver('  tabla llena: motivo 4', caso(regs=[(1, 1, 0, 0, 0, 0xff)] * PO_MAX), no(4))
ver('oro uno menos que costo + reserva: motivo 5', caso(oro=39), no(5))
print('-- fuera de su alcance (sin evento)')
ver('control: ya sembró este turno', caso(ultimo=TURNO + 1), ([], [], TURNO + 1, True))
ver('control: bando humano', caso(humano=True), NADA)
ver('control: sin IA.INI (ia_on = 0; hasta que una tanda lo confirme)', caso(ia_on=0), NADA)
ver('control: color con la IA original (ia_mode 0)', caso(modo=0), NADA)
ver('control: bando fuera de rango', caso(p=9)[0:2], ([], []))
print('MAL:', mal)
sys.exit(1 if mal else 0)
