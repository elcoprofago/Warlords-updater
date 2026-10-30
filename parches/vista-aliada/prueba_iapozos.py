# Prueba de juguete de po_pf (build.py; ia\PENDIENTE-ia-innovaciones.md, paso 3): en el buscador de caminos
# (0x4a5c40), un pozo, remolino o trampa activa que el jugador del camino ve es intransitable, salvo la ruta expresa
# de un humano a esa misma casilla. Corre en unicorn el tramo de un vecino desde 0x4a5d34 (di = x, bx = y) y mira a
# dónde salta: 0x4a5d40 = la casilla sigue en el camino, 0x4a5e31 = se descarta.
# Uso: python prueba_iapozos.py [carpeta]   (por defecto C:\Warlords3; armarla antes con build.py)
# Controles: el exe original pasa siempre; el registro con los registros que preserva sale igual.
import os, sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

DIR = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3'
STACK = 0x1f0000
MAPW, MAPH, MAPSH = 0x503e00, 0x503e02, 0x503e06
PO_MAX, PO_REC = 64, 8
POZO, REMOLINO, TRAMPA, TUMBA = 0, 1, 2, 3
PLAYER, DESTX, DESTY = 0x58715c, 0x5878d4, 0x5878d8
SIDE, SIDE_HUMAN = 0x1f8, 0x536c12
OPT, DIPLO_OPT, DIPLO = 0x53c38e, 0x53c393, 0x55ee4c
SIGUE, CORTA = 0x4a5d40, 0x4a5e31

def cargar(nombre):
    pe = pefile.PE(os.path.join(DIR, nombre))
    return pe, pe.OPTIONAL_HEADER.ImageBase, bytes(pe.get_memory_mapped_image())
AV, ORIG = cargar('DarklordAV.exe'), cargar('Darklord.exe')
_, BASE, img = AV
PO_SAVE = BASE + img.index(b'POZO' + bytes(4 + PO_MAX * PO_REC)); PO_TAB = PO_SAVE + 8
PO_MAP = PO_SAVE + 8 + PO_MAX * PO_REC + 4   # po_magic (4 bytes) y después po_map

mal = 0
def ver(nombre, r, esperado):
    global mal
    ok = r == esperado
    mal += not ok
    print('OK ' if ok else 'MAL', nombre, '->', 'sigue' if r == SIGUE else 'corta' if r == CORTA else r)

def correr(exe, x, y, regs, jugador=1, humano=False, dest=(-1, -1), aliado=None):
    pe, base, imagen = exe
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    size = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
    mu.mem_map(base, size); mu.mem_write(base, imagen[:size])
    mu.mem_map(0x100000, 0x100000)
    mu.mem_write(MAPW, struct.pack('<hh', 40, 30)); mu.mem_write(MAPSH, b'\6')   # 40 x 30, filas de 64
    if exe is AV:
        for i, (rx, ry, tipo, estado, mascara, dueno) in enumerate(regs):
            mu.mem_write(PO_TAB + i * PO_REC, struct.pack('<hhBBBB', rx, ry, tipo, estado, mascara, dueno))
            mu.mem_write(PO_MAP + (ry << 6) + rx, bytes([i + 1]))
    mu.mem_write(PLAYER, struct.pack('<h', jugador))
    mu.mem_write(SIDE_HUMAN + jugador * SIDE, struct.pack('<h', -1 if humano else 2))
    mu.mem_write(DESTX, struct.pack('<h', dest[0])); mu.mem_write(DESTY, struct.pack('<h', dest[1]))
    if aliado is not None:   # vista aliada con diplomacia: aliado y jugador, aliados mutuos
        mu.mem_write(OPT, bytes([0x90])); mu.mem_write(DIPLO_OPT, bytes([8]))
        for a, b in ((aliado, jugador), (jugador, aliado)):
            mu.mem_write(DIPLO + a * 56 + b, b'\0')
        for a in range(8):   # los demás, en guerra
            for b in range(8):
                if {a, b} != {aliado, jugador} and a != b:
                    mu.mem_write(DIPLO + a * 56 + b, b'\2')
    mu.reg_write(UC_X86_REG_ESP, STACK)
    mu.reg_write(UC_X86_REG_EDI, 0xdead0000 | x); mu.reg_write(UC_X86_REG_EBX, 0xbeef0000 | y)
    mu.reg_write(UC_X86_REG_ESI, 0x11112222); mu.reg_write(UC_X86_REG_EBP, 0x33334444)
    fin = []
    def hook(uc, addr, sz, _):
        if addr in (SIGUE, CORTA):
            fin.append(addr); uc.emu_stop()
    mu.hook_add(UC_HOOK_CODE, hook)
    mu.emu_start(0x4a5d34, 0, count=2000)
    r = fin[0] if fin else None
    if r == SIGUE:   # lo reemplazado: edx = x, eax = x*160, ecx = y; el resto, intacto
        esperado = (x, x * 160, y, 0xdead0000 | x, 0xbeef0000 | y, 0x11112222, 0x33334444, STACK)
        leido = tuple(mu.reg_read(r_) for r_ in (UC_X86_REG_EDX, UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EDI,
                                                  UC_X86_REG_EBX, UC_X86_REG_ESI, UC_X86_REG_EBP, UC_X86_REG_ESP))
        if leido != esperado:
            return ('registros', [hex(v) for v in leido])
    elif r == CORTA:
        leido = tuple(mu.reg_read(r_) for r_ in (UC_X86_REG_EDI, UC_X86_REG_EBX, UC_X86_REG_ESI, UC_X86_REG_EBP,
                                                  UC_X86_REG_ESP))
        if leido != (0xdead0000 | x, 0xbeef0000 | y, 0x11112222, 0x33334444, STACK):
            return ('registros', [hex(v) for v in leido])
    return r

J, OTRO = 1, 4
VE, NOVE = 1 << J, 1 << OTRO
regs = [(5, 5, POZO, 0, VE, 0), (6, 5, POZO, 0, NOVE, 0), (7, 5, REMOLINO, 0, VE, 0),
        (8, 5, TRAMPA, 0, 0, J), (9, 5, TRAMPA, 0, 0, OTRO), (10, 5, TRAMPA, 2, VE, OTRO),
        (11, 5, TRAMPA, 1, VE, OTRO), (12, 5, TUMBA, 0, 0xff, 0)]

print('-- la computadora')
ver('pozo visto', correr(AV, 5, 5, regs), CORTA)
ver('pozo no visto (lo ve otro)', correr(AV, 6, 5, regs), SIGUE)
ver('remolino visto', correr(AV, 7, 5, regs), CORTA)
ver('trampa propia (no descubierta)', correr(AV, 8, 5, regs), CORTA)
ver('trampa ajena no vista', correr(AV, 9, 5, regs), SIGUE)
ver('trampa ajena de un aliado con vista aliada', correr(AV, 9, 5, regs, aliado=OTRO), CORTA)
ver('trampa gastada (2 explosiones) vista', correr(AV, 10, 5, regs), SIGUE)
ver('trampa con 1 explosión, vista', correr(AV, 11, 5, regs), CORTA)
ver('tumba', correr(AV, 12, 5, regs), SIGUE)
ver('casilla sin nada', correr(AV, 20, 20, regs), SIGUE)
ver('pozo visto, destino de la computadora', correr(AV, 5, 5, regs, dest=(5, 5)), CORTA)
ver('fuera del mapa', correr(AV, 45, 5, regs), SIGUE)
ver('jugador del camino fuera de rango (8)', correr(AV, 5, 5, regs, jugador=8), SIGUE)
print('-- el humano')
ver('pozo visto, de paso', correr(AV, 5, 5, regs, humano=True, dest=(9, 9)), CORTA)
ver('pozo visto, destino expreso', correr(AV, 5, 5, regs, humano=True, dest=(5, 5)), SIGUE)
ver('pozo visto, destino en la misma columna', correr(AV, 5, 5, regs, humano=True, dest=(5, 6)), CORTA)
print('-- el original')
ver('original, pozo visto', correr(ORIG, 5, 5, regs), SIGUE)
print('MAL:', mal)
sys.exit(1 if mal else 0)
