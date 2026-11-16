# Prueba de juguete de po_draw3 (build.py): en la 3.ª pasada del dibujo del mapa (0x459fb0), el borde del bosque que se
# derrama sobre una casilla vecina se pinta después de las obras; po_draw3 vuelve a pintar las obras de esa casilla.
# Uso: python prueba_faro_bosque.py [carpeta]   (por defecto E:\Warlords-TEST\Warlords3; armarla antes con build.py)
# Se corre la 3.ª pasada desde 0x459fb0 con una celda con borde (+1 bit 0x20) y otra sin borde (control).
import os as _os, sys as _sys; _sys.path.append(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..'))
from juego_pruebas import W3
import os, sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

DIR = sys.argv[1] if len(sys.argv) > 1 else W3
pe = pefile.PE(os.path.join(DIR, 'DarklordAV.exe')); BASE = pe.OPTIONAL_HEADER.ImageBase
img = bytes(pe.get_memory_mapped_image()); SIZE = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
J = 0x459ff5
assert img[J - BASE] == 0xe9, 'falta el salto a po_draw3'
PD3 = J + 5 + struct.unpack_from('<i', img, J - BASE + 1)[0]
OB = None
for k in range(0, 0x40):                  # el call a ob_draw dentro de po_draw3
    if img[PD3 - BASE + k] == 0xe8 and PD3 + k + 5 + struct.unpack_from('<i', img, PD3 - BASE + k + 1)[0] != 0x4dd530:
        OB = PD3 + k + 5 + struct.unpack_from('<i', img, PD3 - BASE + k + 1)[0]; break
assert OB
STACK, VIEW, CELL = 0x1f0000, 0x180000, 0x170000

mal = 0
def ver(n, r, e):
    global mal
    ok = r == e; mal += not ok; print('OK ' if ok else 'MAL', n, '->', r)

def correr(borde):
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(BASE, SIZE); mu.mem_write(BASE, img[:SIZE]); mu.mem_map(0x100000, 0x100000)
    mu.mem_write(VIEW + 0x28, struct.pack('<hh', 10, 20))
    mu.mem_write(CELL + 1, bytes([0x20 if borde else 0])); mu.mem_write(CELL + 0xc, struct.pack('<H', 3))
    sp = STACK - 0x100
    mu.mem_write(sp + 0x14, struct.pack('<hh', 3, 4))
    for r, v in ((UC_X86_REG_ESP, sp), (UC_X86_REG_EBP, VIEW), (UC_X86_REG_ESI, CELL),
                 (UC_X86_REG_EDI, 144), (UC_X86_REG_EBX, 192)): mu.reg_write(r, v)
    log = []
    def hook(mu, a, s, u):
        if a == 0x4dd530:
            esp = mu.reg_read(UC_X86_REG_ESP)
            log.append(('blit', struct.unpack('<I', mu.mem_read(esp + 4, 4))[0]))
            mu.reg_write(UC_X86_REG_ESP, esp + 4); mu.reg_write(UC_X86_REG_EIP, struct.unpack('<I', mu.mem_read(esp, 4))[0])
        elif a == OB:
            cx = bytes(mu.mem_read(po, 8))
            log.append(('ob_draw', struct.unpack('<hhhh', cx), mu.reg_read(UC_X86_REG_ESI)))
            esp = mu.reg_read(UC_X86_REG_ESP)
            mu.reg_write(UC_X86_REG_ESP, esp + 4); mu.reg_write(UC_X86_REG_EIP, struct.unpack('<I', mu.mem_read(esp, 4))[0])
        elif a == 0x459ffd:
            log.append(('fin', mu.reg_read(UC_X86_REG_ESP) - sp, mu.reg_read(UC_X86_REG_EDI), mu.reg_read(UC_X86_REG_EBX)))
            mu.emu_stop()
    mu.hook_add(UC_HOOK_CODE, hook)
    mu.emu_start(0x459fb0, 0, count=500)
    return log

# po_cx: el primer "mov word ptr [po_cx], ax" de po_draw3
_i = img.index(b'\x66\xa3', PD3 - BASE); po = struct.unpack_from('<I', img, _i + 2)[0]

r = correr(True)
ver('con borde: blit del borde, obras de la celda (10+3, 20+4) en x 144, y 192, y vuelve igual',
    r, [('blit', 0x73 + 3), ('ob_draw', (13, 24, 144, 192), CELL), ('fin', 0, 144, 192)])
r = correr(False)
ver('sin borde (control): ni blit ni obras', r, [('fin', 0, 144, 192)])
print('MAL', mal)
sys.exit(1 if mal else 0)
