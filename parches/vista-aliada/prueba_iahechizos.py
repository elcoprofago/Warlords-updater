# Prueba de juguete: la IA de prueba pesa en 0 los efectos vacíos de un hechizo (hs_w, en 0x49b7ed), en unicorn.
# Llama a la rutina que quedó en 0x49b7ed (hs_w en DarklordAV.exe, 0x492c40 en Darklord.exe) con una unidad de cada
# dueño y un efecto vacío o lleno, con IA.INI (ia_on = 1) y sin él, y compara contra Darklord.exe original. El azar
# (0x4deb20) va guionado: devuelve siempre el máximo pedido, así un vacío original vale 6 * 6 = 36 antes del ajuste.
# Controles que deben quedar como el original: efecto lleno, color original, sin IA.INI.
# Uso: python prueba_iahechizos.py [DarklordAV.exe] [Darklord.exe]
import os as _os, sys as _sys; _sys.path.append(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..'))  # para encontrar juego_pruebas.py
from juego_pruebas import W3  # carpeta del juego de pruebas: se cambia solo ahi
import sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import *

def load(path):
    pe = pefile.PE(path)
    return pe.OPTIONAL_HEADER.ImageBase, bytes(pe.get_memory_mapped_image()), (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
AV = load(sys.argv[1] if len(sys.argv) > 1 else W3 + r'\DarklordAV.exe')
ORIG = load(sys.argv[2] if len(sys.argv) > 2 else W3 + r'\Darklord.exe')
SITE = 0x49b7ed

def target(img, base):
    o = SITE - base
    assert img[o] == 0xe8
    return SITE + 5 + struct.unpack('<i', img[o + 1:o + 5])[0]
HS = target(AV[1], AV[0]); assert target(ORIG[1], ORIG[0]) == 0x492c40 and HS != 0x492c40
# ia_on e ia_mode: los operandos de los dos primeros cmp de hs_w (80 3d <ia_on> 00 ... 80 b8 <ia_mode> 01)
_i = AV[1][HS - AV[0]:HS - AV[0] + 0x60]
assert _i[:2] == b'\x80\x3d'
IA_ON = struct.unpack('<I', _i[2:6])[0]
_k = _i.index(b'\x80\xb8'); IA_MODE = struct.unpack('<I', _i[_k + 2:_k + 6])[0]

STK, END, EFF = 0x10000000, 0xdead0000, 0x20000000
def run(exe, unit, owner, eid, ia_on, modes):
    base, img, size = exe
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(base, size); mu.mem_write(base, img)
    mu.mem_map(STK, 0x100000); mu.mem_map(END, 0x1000); mu.mem_map(EFF, 0x1000)
    mu.mem_write(END, b'\xc3')
    # azar(a, b, c) guionado: devuelve b (el máximo)
    mu.mem_write(0x4deb20, bytes.fromhex('8b442408c3'))
    rec = 0x54fe50 + unit * 0x1c
    mu.mem_write(rec + 0xe, struct.pack('<H', owner << 5))
    mu.mem_write(EFF, struct.pack('<hh', eid, 3))
    if exe is AV:
        mu.mem_write(IA_ON, bytes([ia_on])); mu.mem_write(IA_MODE, bytes(modes))
    sp = STK + 0x80000
    for a in reversed((unit, EFF, 1)): sp -= 4; mu.mem_write(sp, struct.pack('<I', a))
    sp -= 4; mu.mem_write(sp, struct.pack('<I', END))
    mu.reg_write(UC_X86_REG_ESP, sp)
    mu.emu_start(target(img, base), END, count=100000)
    return struct.unpack('<h', struct.pack('<H', mu.reg_read(UC_X86_REG_EAX) & 0xffff))[0]

ok = True
def check(c, msg):
    global ok; print('  ', 'OK   ' if c else 'FALLA', msg); ok &= c
modes = [1, 0, 1, 0, 1, 0, 1, 0]    # pares en prueba, impares original
for eid, nom in ((0, 'vacío'), (12, 'lleno (id 12)'), (5, 'lleno (id 5)')):
    for owner in (2, 3):
        for on in (1, 0):
            o = run(ORIG, 7, owner, eid, 0, modes)
            a = run(AV, 7, owner, eid, on, modes)
            cero = eid == 0 and on and modes[owner] == 1
            check(a == (0 if cero else o), f'efecto {nom:14} dueño {owner} ({"prueba" if modes[owner] else "original"}) '
                  f'IA.INI {"sí" if on else "no"}: {a} (original {o}{", debe ser 0" if cero else ""})')
check(run(ORIG, 7, 2, 0, 0, modes) > 0, 'en el original un vacío vale más que 0 (el error existe)')
print('TODO OK' if ok else 'HAY FALLAS'); sys.exit(0 if ok else 1)
