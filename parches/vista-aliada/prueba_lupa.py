# Prueba de juguete de la lupa y el botón derecho sobre pozos, remolinos y trampas (po_look, po_find, po_cur,
# po_curclr y po_info de build.py), en unicorn, sobre el exe parcheado y el original.
# Uso: python prueba_lupa.py [carpeta]   (por defecto C:\Warlords3; armarla antes con build.py)
# Decodificador: corre desde 0x473d32 (sin grupo elegido, con la casilla, la ciudad y la ruina / el sitio en su marco)
# hasta la vuelta, y devuelve el código (0x14 = lupa del cuadro de ruinas, 3 = nada). Acción: 0x473e80 con ese
# código, con 0x4a2170, 0x4a4980 (cuadro de ruinas) y 0x4c7a10 (cuadro de información) de mentira.
# Controles: la casilla vacía devuelve 3 y la ruina de verdad sigue abriendo su cuadro después de una lupa de pozo;
# el original devuelve 3 sobre el pozo.
import os, re, sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

DIR = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3'
STACK, RET = 0x1f0000, 0x100
MAPW, MAPH, MAPSH = 0x503e00, 0x503e02, 0x503e06
PO_MAX, PO_REC = 64, 8
SPRINTF = 0x1f8000   # dirección de mentira para [0x5a9bec]
OUT = 0x1e0000       # out* del decodificador y de la acción
AGUA = 1

def cargar(nombre):
    ruta = os.path.join(DIR, nombre)
    pe = pefile.PE(ruta if os.path.exists(ruta) else os.path.join(r'C:\Warlords3', nombre))
    return pe, pe.OPTIONAL_HEADER.ImageBase, bytes(pe.get_memory_mapped_image())
AV, ORIG = cargar('DarklordAV.exe'), cargar(r'C:\Warlords3\Darklord.exe')
_, BASE, img = AV
PO_SAVE = BASE + img.index(b'POZO' + bytes(4 + PO_MAX * PO_REC)); PO_N, PO_TAB = PO_SAVE + 4, PO_SAVE + 8
PO_MAP = PO_SAVE + 8 + PO_MAX * PO_REC + 4

mal = 0
def ver(nombre, r, esperado):
    global mal
    ok = r == esperado
    mal += not ok
    print('OK ' if ok else 'MAL', nombre, '->', r)

def casilla(x, y): return 0x503e58 + ((y * 10) << 6) + x * 10

class Juego:
    def __init__(self, exe=AV):
        pe, base, imagen = exe
        mu = self.mu = Uc(UC_ARCH_X86, UC_MODE_32)
        size = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
        mu.mem_map(base, size); mu.mem_write(base, imagen[:size])
        mu.mem_map(0, 0x1000); mu.mem_map(0x100000, 0x100000)
        mu.mem_write(MAPW, struct.pack('<hh', 40, 30)); mu.mem_write(MAPSH, b'\6')
        mu.mem_write(0x535f0c + AGUA * 0x58, struct.pack('<h', 1))
        mu.mem_write(0x55ee4c, b'\2' * 56 * 8)   # nadie aliado
        mu.mem_write(0x5a9bec, struct.pack('<I', SPRINTF)); self.interceptar(SPRINTF, self.sprintf)
        mu.mem_write(0x560b20, struct.pack('<h', 1)); mu.mem_write(0x537ce8, struct.pack('<h', 1))
        self.cuadros, self.ruinas = [], []
        self.interceptar(0x420a70, lambda a: 0)
        self.interceptar(0x4a2170, lambda a: 0)
        self.interceptar(0x4a4980, lambda a: self.ruinas.append((a[0] & 0xffff, a[1] & 0xffff)))
        self.interceptar(0x4c7a10, lambda a: self.cuadros.append(
            (self.cadena(a[0]).decode('latin1'), self.cadena(a[1]).decode('latin1'), a[2], a[3])))
    def cadena(self, a): return bytes(self.mu.mem_read(a, 256)).split(b'\0')[0]
    def sprintf(self, a):
        f = self.cadena(a[1]).decode('latin1'); ts = re.findall(r'%[-.0-9]*([sd])', f)
        t = (f % tuple(self.cadena(v).decode('latin1') if c == 's' else v for c, v in zip(ts, a[2:]))).encode('latin1')
        self.mu.mem_write(a[0], t + b'\0'); return len(t)
    def ciudades(self, cs):
        self.mu.mem_write(0x537e2a, struct.pack('<h', len(cs)))
        for i, (x, y, n) in enumerate(cs): self.mu.mem_write(0x537e2c + i * 0xde, struct.pack('<hh', x, y) + n.encode() + b'\0')
    def interceptar(self, addr, fn, pop=0):
        def g(mu, a, size, _):
            sp = mu.reg_read(UC_X86_REG_ESP)
            ret, *args = struct.unpack('<5I', mu.mem_read(sp, 20))
            mu.reg_write(UC_X86_REG_EAX, (fn(args) or 0) & 0xffffffff)
            mu.reg_write(UC_X86_REG_ESP, sp + 4 + pop); mu.reg_write(UC_X86_REG_EIP, ret)
        self.mu.hook_add(UC_HOOK_CODE, g, begin=addr, end=addr)
    def poner(self, regs, agua=()):
        mu = self.mu
        mu.mem_write(PO_N, struct.pack('<i', len(regs)))
        for i, r in enumerate(regs):
            mu.mem_write(PO_TAB + PO_REC * i, struct.pack('<hhBBBB', *r))
            mu.mem_write(PO_MAP + (r[1] << 6) + r[0], bytes([i + 1]))
        for x, y in agua: mu.mem_write(casilla(x, y), struct.pack('<HH', AGUA, 0))
    def decodificar(self, x, y, ciudad=-1, ruina=-1, sitio=-1, px=(111, 222)):
        # marco del cuerpo de 0x4735c0: 4 registros + 0x24 de locales, la vuelta en [esp+0x34], los argumentos después
        mu = self.mu; sp = STACK - 0x34
        mu.mem_write(sp, bytes(0x34)); mu.mem_write(STACK, struct.pack('<IIIII', RET, px[0], px[1], 0, OUT))
        mu.mem_write(sp + 0x2c, struct.pack('<hh', x, y)); mu.mem_write(sp + 0x2a, struct.pack('<h', ruina))
        mu.mem_write(sp + 0x1e, struct.pack('<h', sitio)); mu.mem_write(OUT, bytes(4))
        mu.reg_write(UC_X86_REG_ESP, sp); mu.reg_write(UC_X86_REG_EBP, ciudad & 0xffffffff); mu.reg_write(UC_X86_REG_EBX, 1)
        mu.emu_start(0x473d32, RET, count=200000)
        return mu.reg_read(UC_X86_REG_EAX) & 0xffff, struct.unpack('<hh', mu.mem_read(OUT, 4))
    def accion(self, codigo, px=(111, 222)):
        mu = self.mu
        mu.mem_write(STACK, struct.pack('<IIIII', RET, codigo, px[0], px[1], OUT)); mu.reg_write(UC_X86_REG_ESP, STACK)
        mu.emu_start(0x473e80, RET, count=200000)
        assert mu.reg_read(UC_X86_REG_ESP) == STACK + 4
        c, r = self.cuadros, self.ruinas; self.cuadros, self.ruinas = [], []
        return c, r

def clic(regs, x, y, agua=(), cs=(), mira=1, **k):
    # código del decodificador y lo que abre la acción con ese código
    g = Juego(); g.poner(regs, agua); g.ciudades(cs); g.mu.mem_write(0x560b20, struct.pack('<h', mira))
    cod, out = g.decodificar(x, y, **k)
    return cod, out, g.accion(cod) if cod == 0x14 else None

MIO = 1 << 1   # máscara de descubierto de quien mira (jugador 1)
print('-- pozo')
r = clic([(5, 7, 0, 0, MIO, 0xff)], 5, 7)
ver('pozo descubierto: lupa (0x14) con la casilla; un cuadro con el tipo, en el mouse; ninguna ruina',
    (r[0], r[1], [c[1:] for c in r[2][0]], r[2][1]),
    (0x14, (5, 7), [('A hidden pit. Any army that steps into it dies; only flyers are safe.', 111, 222)], []))
print('   título:', r[2][0][0][0])
ver('  el título empieza en mayúscula', bool(r[2] and r[2][0] and r[2][0][0][0][:1].isupper()), True)
ver('pozo no descubierto: nada (3)', clic([(5, 7, 0, 0, 1 << 2, 0xff)], 5, 7)[0], 3)
ver('pozo descubierto por otro y visto por él: lupa', clic([(5, 7, 0, 0, 1 << 2, 0xff)], 5, 7, mira=2)[0], 0x14)
print('-- remolino')
AG = [(x, y) for x in range(9, 14) for y in range(4, 9)]
r = clic([(11, 6, 1, 3, MIO, 0xff)], 11, 6, agua=AG)
ver('remolino descubierto: lupa y cuadro de remolino', (r[0], r[2][0][0][1]),
    (0x14, 'A whirlpool. Any ship that sails into its eye sinks with all aboard; only flyers are safe.'))
print('   título:', r[2][0][0][0])
ver('  también en una pieza vecina del dibujo (3x3)', clic([(11, 6, 1, 3, MIO, 0xff)], 12, 7, agua=AG)[0], 0x14)
ver('control: dos casillas más allá, no', clic([(11, 6, 1, 3, MIO, 0xff)], 13, 6, agua=AG)[0], 3)
ver('control: remolino no descubierto, no', clic([(11, 6, 1, 3, 0, 0xff)], 12, 7, agua=AG)[0], 3)
print('-- trampas')
CS = [(20, 20, 'Ironhold')]
r = clic([(3, 3, 2, 1 << 4, 0, 1)], 3, 3, cs=CS)
ver('trampa propia, nueva: título con la ciudad y número, 3 de 3', (r[0], r[2][0][0][:2]),
    (0x14, ('Trap Ironhold01', 'A mine. Explosions left: 3 of 3.')))
r = clic([(3, 3, 2, 1 << 4 | 1, 0, 1)], 3, 3, cs=CS)
ver('trampa propia con una explosión: 2 de 3', r[2][0][0][1], 'A mine. Explosions left: 2 of 3.')
r = clic([(3, 3, 2, 3, 0, 4)], 3, 3, cs=CS)
ver('trampa gastada (de otro, la ven todos): gastada', r[2][0][0][1], 'A spent mine: it will not explode again.')
ver('trampa de otro, sin descubrir: nada', clic([(3, 3, 2, 0, 0, 4)], 3, 3, cs=CS)[0], 3)
ver('trampa de otro, descubierta: lupa', clic([(3, 3, 2, 0, MIO, 4)], 3, 3, cs=CS)[0], 0x14)
r = clic([(11, 6, 2, 1, 0, 1)], 11, 6, agua=AG, cs=CS)
ver('mina submarina propia: su texto', r[2][0][0][1], 'A sea mine. Explosions left: 2 of 3.')
ver('mina submarina recién explotada (no se dibuja): nada', clic([(11, 6, 2, 0x81, 0, 1)], 11, 6, agua=AG)[0], 3)
ver('mina submarina gastada (no se dibuja): nada', clic([(11, 6, 2, 3, 0, 1)], 11, 6, agua=AG)[0], 3)
ver('sin ciudades: título "Trap"', clic([(3, 3, 2, 0, 0, 1)], 3, 3)[2][0][0][0], 'Trap')
print('-- lo demás sigue primero')
ver('tumba: nada', clic([(3, 3, 3, 0, 0xff, 0xff)], 3, 3)[0], 3)
ver('trampa en una ciudad: manda la ciudad (0xc)', clic([(3, 3, 2, 0, 0, 1)], 3, 3, ciudad=0)[0], 0xc)
ver('pozo en una ruina descubierta: manda la ruina', clic([(5, 7, 0, 0, MIO, 0xff)], 5, 7, ruina=2)[2], ([], [(5, 7)]))
ver('pozo en un sitio: manda el sitio (0x15)', clic([(5, 7, 0, 0, MIO, 0xff)], 5, 7, sitio=0)[0], 0x15)
ver('control: casilla vacía: 3 con el lugar en pantalla', clic([(5, 7, 0, 0, MIO, 0xff)], 6, 7)[:2], (3, (111, 222)))
g = Juego(); g.poner([(5, 7, 0, 0, MIO, 0xff)])
g.decodificar(5, 7); g.decodificar(9, 9, ruina=1)
ver('control: lupa de pozo y después una ruina: abre la ruina, no el pozo', g.accion(0x14), ([], [(9, 9)]))
g = Juego(ORIG)   # sin la tabla de pozos (fuera de su imagen)
ver('control: el original sobre el pozo: 3', g.decodificar(5, 7)[0], 3)
print('MAL:', mal)
sys.exit(1 if mal else 0)
