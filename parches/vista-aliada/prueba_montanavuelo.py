# Prueba de «montañas altas, ni por aire» (mtnfly, gancho en 0x4a52a9 del armado del grafo 0x4a4f90) sobre el exe
# parcheado, en unicorn, contra el original, con la partida Aliados03.
# Uso: python prueba_montanavuelo.py [DarklordAV.exe] [Darklord.exe] [partida.SAV]
# Esperado:
#  - enlaces de vuelo (0x578158): iguales al original salvo los que entran a una montaña («Mountains», clase 4) sin
#    camino ni puente, que desaparecen; y desaparece al menos uno;
#  - controles que deben sobrevivir: entrar a bosque profundo (clase 4, otro nombre), a colinas, a una montaña con
#    camino, y salir de una montaña (los enlaces de tierra los cambian otras reglas del parche: no se comparan);
#  - el armado preserva ebx, esi, edi, ebp y la pila.
import os as _os, sys as _sys; _sys.path.append(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..'))
from juego_pruebas import W3
import sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

NEW = sys.argv[1] if len(sys.argv) > 1 else W3 + r'\DarklordAV.exe'
OLD = sys.argv[2] if len(sys.argv) > 2 else W3 + r'\Darklord.exe'
sav = open(sys.argv[3] if len(sys.argv) > 3 else W3 + r'\Saves\Aliados03.SAV', 'rb').read()

class Maquina:
    def __init__(s, exe):
        pe = pefile.PE(exe); img = pe.get_memory_mapped_image()
        s.mu = mu = Uc(UC_ARCH_X86, UC_MODE_32)
        mu.mem_map(0x400000, (len(img) + 0xfff) & ~0xfff); mu.mem_write(0x400000, img)
        mu.mem_map(0x10000000, 0x100000); mu.mem_map(0xdead0000, 0x1000); mu.mem_write(0xdead0000, b'\xc3' * 0x1000)
        off = 0x6d
        for va, n in ((0x503e00, 0x12), (0x503e58, 0x32000), (0x535ed0, 0xa96), (0x536b30, 0x2d894)):
            mu.mem_write(va, sav[off:off + n]); off += n
        mu.mem_map(0xdead1000, 0x10000); k = 0
        for d in pe.DIRECTORY_ENTRY_IMPORT:
            for imp in d.imports:
                mu.mem_write(imp.address, struct.pack('<I', 0xdead1000 + 16 * k)); k += 1
        def h(m, a, size, ud): raise RuntimeError('importación no esperada')
        mu.hook_add(UC_HOOK_CODE, h, begin=0xdead1000, end=0xdead1000 + 16 * k)
    def grafo(s, regs={}):
        mu = s.mu; sp = 0x10080000 - 4; mu.mem_write(sp, struct.pack('<I', 0xdead0000)); mu.reg_write(UC_X86_REG_ESP, sp)
        for r, v in regs.items(): mu.reg_write(r, v)
        mu.emu_start(0x4a4f90, 0xdead0000, count=50_000_000)
    def rd(s, a, n): return bytes(s.mu.mem_read(a, n))

nueva, orig = Maquina(NEW), Maquina(OLD)
REGS = {UC_X86_REG_EBX: 0x1111, UC_X86_REG_ESI: 0x2222, UC_X86_REG_EDI: 0x3333, UC_X86_REG_EBP: 0x4444}
nueva.grafo(REGS); orig.grafo()
m = nueva
fallas = 0
def check(nombre, cond, detalle=''):
    global fallas
    print(('OK   ' if cond else 'FALLA'), nombre, '' if cond else detalle); fallas += not cond

check('0x4a4f90 preserva ebx, esi, edi, ebp y la pila',
      all(m.mu.reg_read(r) == v for r, v in REGS.items()) and m.mu.reg_read(UC_X86_REG_ESP) == 0x10080000)
W, H = struct.unpack('<hh', m.rd(0x503e00, 4)); sh = m.rd(0x503e06, 1)[0]
D640 = struct.unpack('<8h', m.rd(0x4fe640, 16)); D658 = struct.unpack('<8h', m.rd(0x4fe658, 16))
VEC = [(D658[k], D640[k]) for k in range(8)]
def tipo(x, y): return struct.unpack('<H', m.rd(0x503e58 + ((y * 10) << sh) + x * 10, 2))[0] & 0x1f
def clase(x, y): return struct.unpack('<H', m.rd(0x535f0c + tipo(x, y) * 0x58, 2))[0]
def nombre(x, y): return m.rd(0x535f0c + tipo(x, y) * 0x58 - 0x36, 12).split(b'\0')[0].decode('latin1')
def camino(x, y): return m.rd(0x57d158 + x * 0xa0 + y, 1)[0] & 0x30
def montana(x, y): return clase(x, y) == 4 and nombre(x, y).lower().startswith('moun') and not camino(x, y)

N, O = m.rd(0x578158, 0x5000), orig.rd(0x578158, 0x5000)
malos, cuenta = [], {'quitado': 0, 'bosque': 0, 'colina': 0, 'mtn_camino': 0, 'salida': 0}
for x in range(W):
    for y in range(H):
        for k, (dx, dy) in enumerate(VEC):
            t = (x + dx, y + dy)
            if not (0 <= t[0] < W and 0 <= t[1] < H): continue
            o, n = O[x * 0xa0 + y] >> k & 1, N[x * 0xa0 + y] >> k & 1
            debe = o and not montana(*t)
            if n != debe: malos.append(((x, y), t, o, n, nombre(*t)))
            if o and not n: cuenta['quitado'] += 1
            if n and clase(*t) == 4 and not nombre(*t).lower().startswith('moun'): cuenta['bosque'] += 1
            if n and nombre(*t).lower().startswith('hill'): cuenta['colina'] += 1
            if n and clase(*t) == 4 and nombre(*t).lower().startswith('moun') and camino(*t): cuenta['mtn_camino'] += 1
            if n and montana(x, y): cuenta['salida'] += 1
check('vuelo: igual al original salvo entrar a montaña sin camino', not malos, malos[:5])
print('     ', cuenta)
check('se quitaron enlaces hacia montañas', cuenta['quitado'] > 0)
for c in ('bosque', 'colina', 'salida'):
    check(f'control sobrevive: {c}', cuenta[c] > 0)
if not cuenta['mtn_camino']: print('AVISO el mapa no tiene montaña con camino: ese control no se pudo medir')
print('\nTODO OK' if not fallas else f'\n{fallas} FALLAS'); sys.exit(1 if fallas else 0)
