# Prueba de juguete del evento 44 (hechizo que lanza la IA; hs_ev en 0x49b883), en unicorn.
# Arma el marco del llamador (puntaje del elegido en [esp + 0x88 + 2 si]), un hechizo con efectos 7 y 12 y costo 3,
# y una unidad del color 5. Con IA.INI (ia_on = 1) tiene que llamar a ia_evt(44, 5, 712, 3, puntaje) y seguir a
# 0x4ba210 con la pila y los registros intactos. Control: sin IA.INI no anota nada y también sigue a 0x4ba210.
# Uso: python prueba_hechizolanzado.py [DarklordAV.exe]
import os as _os, sys as _sys; _sys.path.append(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..'))  # para encontrar juego_pruebas.py
from juego_pruebas import W3  # carpeta del juego de pruebas: se cambia solo ahi
import sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

pe = pefile.PE(sys.argv[1] if len(sys.argv) > 1 else W3 + r'\DarklordAV.exe')
BASE, IMG = pe.OPTIONAL_HEADER.ImageBase, bytes(pe.get_memory_mapped_image())
SIZE = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
SITE = 0x49b883
assert IMG[SITE - BASE] == 0xe8
HS = SITE + 5 + struct.unpack('<i', IMG[SITE - BASE + 1:SITE - BASE + 5])[0]
code = IMG[HS - BASE:HS - BASE + 0x80]
assert code[:2] == b'\x80\x3d'
IA_ON = struct.unpack('<I', code[2:6])[0]
k = code.index(b'\xe8', 0x40)   # call ia_evt
while code[k - 2:k] != b'\x6a\x2c':   # push 44 justo antes
    k = code.index(b'\xe8', k + 1)
IA_EVT = HS + k + 5 + struct.unpack('<i', code[k + 1:k + 5])[0]

STK, SP = 0x10000000, 0x20000000
fallas = 0
def run(ia_on):
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(BASE, SIZE); mu.mem_write(BASE, IMG)
    mu.mem_map(STK, 0x100000); mu.mem_map(SP, 0x1000)
    mu.mem_write(IA_ON, bytes([ia_on]))
    unit, si, score = 9, 2, 437
    mu.mem_write(0x54fe50 + unit * 0x1c + 0xe, struct.pack('<H', 5 << 5))
    sp = bytearray(0x200)
    struct.pack_into('<h', sp, 0x90, 3); struct.pack_into('<h', sp, 0x96, 7); struct.pack_into('<h', sp, 0xa6, 12)
    mu.mem_write(SP, bytes(sp))
    frame = STK + 0x80000            # esp del llamador antes de empujar los argumentos
    mu.mem_write(frame + 0x88 + 2 * si, struct.pack('<h', score))
    esp = frame - 16
    mu.mem_write(esp, struct.pack('<IIII', 0xcafe0000, unit, SP, 0))
    regs = {UC_X86_REG_EBX: unit, UC_X86_REG_ESI: si, UC_X86_REG_EDI: 0x1111, UC_X86_REG_EBP: 0x2222}
    for r, v in regs.items(): mu.reg_write(r, v)
    mu.reg_write(UC_X86_REG_ESP, esp)
    ev = []
    def hook(m, addr, size, _):
        if addr == IA_EVT:
            s = m.reg_read(UC_X86_REG_ESP)
            ev.append(struct.unpack('<5i', m.mem_read(s + 4, 20)))
            m.reg_write(UC_X86_REG_EIP, 0x49b8a4)   # un ret cualquiera del exe
        elif addr == 0x4ba210:
            m.emu_stop()
    mu.hook_add(UC_HOOK_CODE, hook)
    mu.emu_start(HS, 0, count=500)
    pila = mu.reg_read(UC_X86_REG_ESP) == esp
    intactos = all(mu.reg_read(r) == v for r, v in regs.items())
    return mu.reg_read(UC_X86_REG_EIP), ev, pila and intactos

def chk(ok, txt):
    global fallas
    fallas += not ok
    print(('   OK   ' if ok else '   FALLA') + ' ' + txt)

eip, ev, ok = run(1)
chk(eip == 0x4ba210, 'con IA.INI sigue a 0x4ba210')
chk(ev == [(44, 5, 712, 3, 437)], f'con IA.INI anota {ev}')
chk(ok, 'pila y registros intactos')
eip, ev, ok = run(0)
chk(eip == 0x4ba210 and ev == [] and ok, 'sin IA.INI no anota nada (control)')
print('TODO OK' if not fallas else f'{fallas} FALLAS')
sys.exit(1 if fallas else 0)
