# Prueba de juguete de po_draw3 (build.py): en la 3.ª pasada del dibujo del mapa (0x459fb0), el borde del bosque que se
# derrama sobre una casilla vecina se pinta después de las obras; po_draw3 vuelve a pintar encima solo la pieza de arriba
# (p = 1, cuerpo sin sombra) de la torre o el faro de la casilla de abajo.
# Uso: python prueba_faro_bosque.py [carpeta]   (por defecto E:\Warlords-TEST\Warlords3; armarla antes con build.py)
# En su propia casilla, el cuerpo sin el pie (capas OD_ALTO). Controles: sin borde no pinta nada; muro: solo el borde.
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
calls = []
for k in range(0, 0x100):
    if img[PD3 - BASE + k] == 0xe8:
        t = PD3 + k + 5 + struct.unpack_from('<i', img, PD3 - BASE + k + 1)[0]
        if t != 0x4dd530 and BASE <= t < BASE + SIZE and t not in calls: calls.append(t)
OB_AT, OD_PUT, FL_OBRA = calls[:3]
_i = img.index(b'\x66\xa3', PD3 - BASE); PO_CX = struct.unpack_from('<I', img, _i + 2)[0]
_i = img.index(b'\xc6\x05', PD3 - BASE); OD_VARS = struct.unpack_from('<I', img, _i + 2)[0]
STACK, VIEW, CELL, REC = 0x1f0000, 0x180000, 0x170000, 0x175000

mal = 0
def ver(n, r, e):
    global mal
    ok = r == e; mal += not ok; print('OK ' if ok else 'MAL', n, '->', r)

def correr(borde, obra_en, tipo=5):
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(BASE, SIZE); mu.mem_write(BASE, img[:SIZE]); mu.mem_map(0x100000, 0x100000)
    mu.mem_write(VIEW + 0x28, struct.pack('<hh', 10, 20))
    mu.mem_write(CELL + 1, bytes([0x20 if borde else 0])); mu.mem_write(CELL + 0xc, struct.pack('<H', 3))
    mu.mem_write(REC + 4, bytes([tipo]))
    mu.mem_write(OD_VARS + 5, b'\x16')
    sp = STACK - 0x100
    mu.mem_write(sp + 0x14, struct.pack('<hh', 3, 4))
    for r, v in ((UC_X86_REG_ESP, sp), (UC_X86_REG_EBP, VIEW), (UC_X86_REG_ESI, CELL),
                 (UC_X86_REG_EDI, 144), (UC_X86_REG_EBX, 192)): mu.reg_write(r, v)
    log = []
    def ret(mu, v=None):
        esp = mu.reg_read(UC_X86_REG_ESP)
        if v is not None: mu.reg_write(UC_X86_REG_EAX, v)
        mu.reg_write(UC_X86_REG_ESP, esp + 4); mu.reg_write(UC_X86_REG_EIP, struct.unpack('<I', mu.mem_read(esp, 4))[0])
    def hook(mu, a, s, u):
        if a == 0x4dd530:
            log.append(('borde',)); ret(mu)
        elif a == OB_AT:
            xy = (mu.reg_read(UC_X86_REG_EAX), mu.reg_read(UC_X86_REG_EDX)); ret(mu, REC if xy == obra_en else 0)
        elif a == OD_PUT:
            v = bytes(mu.mem_read(OD_VARS, 6))
            log.append(('pieza', mu.reg_read(UC_X86_REG_ECX), v[0], v[5], struct.unpack('<hhhh', bytes(mu.mem_read(PO_CX, 8)))))
            ret(mu)
        elif a == FL_OBRA:
            log.append(('bandera',)); ret(mu)
        elif a == 0x459ffd:
            log.append(('fin', mu.reg_read(UC_X86_REG_ESP) - sp, mu.reg_read(UC_X86_REG_EDI), mu.reg_read(UC_X86_REG_EBX)))
            mu.emu_stop()
    mu.hook_add(UC_HOOK_CODE, hook)
    mu.emu_start(0x459fb0, 0, count=500)
    return log

FIN = ('fin', 0, 144, 192)
ver('faro abajo: borde, solo la pieza de arriba (capa 1, p 1, cuerpo) en x 144, y 192, y su bandera',
    correr(True, (13, 25)), [('borde',), ('pieza', 1, 1, 0, (13, 24, 144, 192)), ('bandera',), FIN])
ver('torre abajo: capa 0', correr(True, (13, 25), 4)[1][:2], ('pieza', 0))
ver('control: sin borde, nada', correr(False, (13, 25)), [FIN])
ver('faro en la misma casilla: su cuerpo sin el pie (capa OD_ALTO + 1, p 4), sin bandera',
    correr(True, (13, 24)), [('borde',), ('pieza', 110, 4, 0, (13, 24, 144, 192)), FIN])
ver('torre en la misma casilla: capa OD_ALTO', correr(True, (13, 24), 4)[1][:3], ('pieza', 109, 4))
ver('control: muro abajo, solo el borde', correr(True, (13, 25), 7), [('borde',), FIN])
ver('control: muro en la casilla, solo el borde', correr(True, (13, 24), 7), [('borde',), FIN])
print('MAL', mal)
sys.exit(1 if mal else 0)
