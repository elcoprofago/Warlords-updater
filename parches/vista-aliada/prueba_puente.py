# Prueba de juguete de los restos del puente derribado (br_vfill en 0x45846d y br_vdraw en 0x459a9f) sobre el exe
# parcheado, en unicorn.
# Uso: python prueba_puente.py [DarklordAV.exe]   (por defecto C:\Warlords3\DarklordAV.exe; armarlo antes con build.py)
# Copia: corre de 0x45846d a 0x45847f con una casilla del mapa y una celda de la vista, y mira [celda] y [celda+0xe].
# Dibujo: corre de 0x459a9f a 0x459af5 con 0x4dd530 interceptada, y mira cada llamada (hoja, origen, tamaño, destino).
# Controles: camino y puente entero (el dibujo de siempre, entero), agua sin el bit, el bit en tierra, celda con
# estructura que no es camino, pieza que no es de puente, y los registros que el lazo del juego sigue usando.
import sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

pe = pefile.PE(sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe'); BASE = pe.OPTIONAL_HEADER.ImageBase
img = bytes(pe.get_memory_mapped_image())
SIZE = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
STACK, CELDA = 0x1f0000, 0x130000
AGUA, TIERRA = 3, 5                     # tipos de terreno de prueba; clase en 0x535f0c + tipo*0x58
CASILLA = 0x503e58 + 10 * 7             # casilla (7, 0) del mapa
BLIT = 0x4dd530
S = 18

def maquina():
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(BASE, SIZE); mu.mem_write(BASE, img[:SIZE])
    mu.mem_map(0x100000, 0x100000)
    mu.mem_write(0x535f0c + AGUA * 0x58, struct.pack('<H', 1))
    mu.mem_write(0x535f0c + TIERRA * 0x58, struct.pack('<H', 0))
    return mu

def copia(tipo, estructura, w8, previo, edificio=False):
    mu = maquina()
    w0 = tipo | (0x4000 if edificio else 0)
    mu.mem_write(CASILLA, struct.pack('<HBBHHH', w0, 0, estructura, 0, 0, w8))
    mu.mem_write(CELDA, struct.pack('<H', 0x5555) + bytes(12) + struct.pack('<H', previo))
    bp = (tipo & 0x1f) | ((estructura & 7) << 10)
    regs = dict(ecx=CASILLA, edi=CELDA, ebp=0x77770000 | bp, ebx=0x1111, esi=0x2222, edx=0x3333)
    for r, v in regs.items(): mu.reg_write(getattr(sys.modules[__name__], 'UC_X86_REG_' + r.upper()), v)
    mu.reg_write(UC_X86_REG_ESP, STACK)
    mu.emu_start(0x45846d, 0x45847f, count=2000)
    assert mu.reg_read(UC_X86_REG_EIP) == 0x45847f
    assert mu.reg_read(UC_X86_REG_ESP) == STACK
    for r in ('ecx', 'edi', 'ebp', 'ebx', 'esi', 'edx'):
        assert mu.reg_read(getattr(sys.modules[__name__], 'UC_X86_REG_' + r.upper())) == regs[r], r
    w, = struct.unpack('<H', mu.mem_read(CELDA, 2))
    assert w == bp, hex(w)
    return struct.unpack('<H', mu.mem_read(CELDA + 0xe, 2))[0]

def dibujo(w0, we, x=96, y=144):
    mu = maquina()
    mu.mem_write(CELDA, struct.pack('<H', w0) + bytes(12) + struct.pack('<H', we))
    esp = STACK
    marco = bytes(range(0x40))
    mu.mem_write(esp, marco); mu.mem_write(esp + 0x1c, struct.pack('<i', y))
    regs = dict(esi=CELDA, edi=x, ebx=0xabcd, ebp=0x120000)
    for r, v in regs.items(): mu.reg_write(getattr(sys.modules[__name__], 'UC_X86_REG_' + r.upper()), v)
    mu.reg_write(UC_X86_REG_ESP, esp)
    llamadas = []
    def gancho(mu, addr, size, _):
        if addr == BLIT:
            sp = mu.reg_read(UC_X86_REG_ESP)
            ret, *a = struct.unpack('<9I', mu.mem_read(sp, 36))
            llamadas.append(tuple(v - (1 << 32) if v >= 1 << 31 else v for v in a))
            mu.reg_write(UC_X86_REG_ESP, sp + 4); mu.reg_write(UC_X86_REG_EIP, ret)
            for r in (UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EDX): mu.reg_write(r, 0xdead0000)
    mu.hook_add(UC_HOOK_CODE, gancho, begin=BLIT, end=BLIT)
    mu.emu_start(0x459a9f, 0x459af5, count=20000)
    assert mu.reg_read(UC_X86_REG_EIP) == 0x459af5
    assert mu.reg_read(UC_X86_REG_ESP) == esp
    if not (w0 >> 8) & 0x1c == 4:          # el camino del juego pisa ebx, como siempre
        for r in ('esi', 'edi', 'ebx', 'ebp'):
            assert mu.reg_read(getattr(sys.modules[__name__], 'UC_X86_REG_' + r.upper())) == regs[r], r
    assert bytes(mu.mem_read(esp, 0x1c)) == marco[:0x1c] and bytes(mu.mem_read(esp + 0x20, 0x20)) == marco[0x20:]
    return llamadas

def pieza(fila, col, hoja=0, derribado=True):
    return (0x8000 if derribado else 0) | (fila << 8) | (col << 5) | hoja

mal = 0
def ver(nombre, r, esperado):
    global mal
    ok = r == esperado
    mal += not ok
    print('OK ' if ok else 'MAL', nombre, '->', r if isinstance(r, list) else hex(r))

# Copia a la celda.
ver('derribado en agua', copia(AGUA, 0, pieza(1, 6), 0x1234), pieza(1, 6))
ver('derribado, hoja 1', copia(AGUA, 0, pieza(2, 7, 1) | 0x10, 0), pieza(2, 7, 1) | 0x10)
ver('puente entero', copia(AGUA, 1, pieza(1, 7, derribado=False), 0x9999), pieza(1, 7, derribado=False))
ver('camino', copia(TIERRA, 1, 0x0123, 0x8000), 0x0123)
ver('control: agua sin el bit', copia(AGUA, 0, pieza(1, 6, derribado=False), 0x8000 | 0x1234), 0x1234)
ver('control: el bit en tierra', copia(TIERRA, 0, pieza(1, 6), 0x8000 | 0x0042), 0x0042)
ver('control: edificio', copia(AGUA, 0, pieza(1, 6), 0x8042, edificio=True), 0x0042)
ver('control: celda sin nada', copia(AGUA, 0, 0, 0x7abc), 0x7abc)

# Dibujo.
X, Y = 96, 144
def full(fila, col, hoja=0): return [(0x21 + hoja, col * 48, fila * 48, 48, 48, 0x27, X, Y)]
ver('horizontal izq.', dibujo(0, pieza(1, 6)), [(0x21, 288, 48, S, 48, 0x27, X, Y)])
ver('horizontal der.', dibujo(0, pieza(1, 7)), [(0x21, 336 + 48 - S, 48, S, 48, 0x27, X + 48 - S, Y)])
ver('vertical arriba', dibujo(0, pieza(2, 7)), [(0x21, 336, 96, 48, S, 0x27, X, Y)])
ver('vertical abajo', dibujo(0, pieza(2, 6, 1)), [(0x22, 288, 96 + 48 - S, 48, S, 0x27, X, Y + 48 - S)])
ver('una casilla, horizontal', dibujo(0, pieza(3, 4)),
    [(0x21, 192, 144, S, 48, 0x27, X, Y), (0x21, 192 + 48 - S, 144, S, 48, 0x27, X + 48 - S, Y)])
ver('una casilla, vertical', dibujo(0, pieza(3, 5)),
    [(0x21, 240, 144, 48, S, 0x27, X, Y), (0x21, 240, 144 + 48 - S, 48, S, 0x27, X, Y + 48 - S)])
ver('control: camino', dibujo(0x0400 | AGUA, 0x0123), full(1, 1, 3))
ver('control: puente entero con el bit', dibujo(0x0400 | AGUA, pieza(1, 6)), full(1, 6))
ver('control: sin el bit', dibujo(0, pieza(1, 6, derribado=False)), [])
ver('control: estructura de sitio', dibujo(0x1000, pieza(1, 6)), [])
ver('control: estructura 5', dibujo(0x1400, pieza(1, 6)), [])
ver('control: pieza de camino', dibujo(0, pieza(0, 1)), [])
print('MAL:', mal)
sys.exit(1 if mal else 0)
