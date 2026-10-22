# Prueba de juguete de construir trampas (tr_* de build.py, parte 7 de PENDIENTE-pozos-y-trampas.md), en unicorn.
# Uso: python prueba_trampas.py [carpeta]   (por defecto C:\Warlords3; la que se le pasó a build.py)
# Menú: br_menu (desde su entrada) llama a tr_check, que deja TR_FLAG; el grupo de juguete está en 0x56ea94.
# Diálogo: br_rebtxt con TR_MARK; tr_send arma TR_PKT (0x4dd3b0 de mentira) o sigue a 0x4b9ce0 si no es la trampa.
# Red: tr_recv (desde 0x4b6a22) con un paquete de juguete; 0x43fd60, 0x4057a0 y el redibujo de mentira.
# Controles: héroe con "Trap", sin el bono, casilla con camino, agua, ciudad u ocupada por un pozo, tabla llena, no es su
# turno; en la red: otra máquina, sin oro, casilla mala, tabla llena, bando de la computadora.
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
PO_SAVE = BASE + img.index(b'POZO' + bytes(4 + PO_MAX * PO_REC)); PO_N, PO_TAB = PO_SAVE + 4, PO_SAVE + 8
PO_MAP = PO_SAVE + 8 + PO_MAX * PO_REC + 4
BR_MENU = dest(0x4b0a1c)
assert img[BR_MENU - BASE:BR_MENU - BASE + 2] == b'\xc6\x05'
TR_FLAG = d32(BR_MENU + 2)
TR_X, TR_Y = TR_FLAG + 2, TR_FLAG + 4
TR_SEND = dest(0x4b6236)
TR_RECV = dest(0x4b6a22, 2)
TR_MARK = 0x7fff
CIUDAD = 15                       # costo de fundar una ciudad ([0x56950e])

mal = 0
def ver(nombre, r, esperado):
    global mal
    ok = r == esperado
    mal += not ok
    print('OK ' if ok else 'MAL', nombre, '->', r)

def casilla(x, y): return 0x503e58 + ((y * 10) << 6) + x * 10
class Juego:
    def __init__(self):
        mu = self.mu = Uc(UC_ARCH_X86, UC_MODE_32)
        size = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
        mu.mem_map(BASE, size); mu.mem_write(BASE, img[:size])
        mu.mem_map(0, 0x1000); mu.mem_map(0x100000, 0x100000)
        mu.mem_write(0x503e00, struct.pack('<hh', 40, 30)); mu.mem_write(0x503e06, b'\6')
        for t, c in ((0, 2), (1, 1), (2, 4)): mu.mem_write(0x535f0c + t * 0x58, struct.pack('<h', c))
        for y in range(30):
            for x in range(40):
                t = 1 if x >= 30 else 0
                w2 = 1 | (0x100 if x == 10 else 0) | (0x300 if (x, y) == (12, 12) else 0)
                mu.mem_write(casilla(x, y), struct.pack('<HHB', t, w2, 0))
        mu.mem_write(0x537e2a, struct.pack('<h', 0))   # sin ciudades: ni capitales ni puentes que buscar
        mu.mem_write(0x56950e, struct.pack('<h', CIUDAD))
        self.llamadas = []
    def interceptar(self, addr, fn, pop=0):
        def g(mu, a, size, _):
            sp = mu.reg_read(UC_X86_REG_ESP)
            ret, *args = struct.unpack('<5I', mu.mem_read(sp, 20))
            mu.reg_write(UC_X86_REG_EAX, (fn(args) or 0) & 0xffffffff)
            mu.reg_write(UC_X86_REG_ESP, sp + 4 + pop); mu.reg_write(UC_X86_REG_EIP, ret)
        self.mu.hook_add(UC_HOOK_CODE, g, begin=addr, end=addr)
    def anotar(self, addr, nombre, n, pop=0):
        self.interceptar(addr, lambda a: self.llamadas.append((nombre, *[v & 0xffffffff for v in a[:n]])), pop)
    def poner(self, regs):
        self.mu.mem_write(PO_N, struct.pack('<i', len(regs)))
        for i, r in enumerate(regs):
            self.mu.mem_write(PO_TAB + PO_REC * i, struct.pack('<hhBBBB', *r))
            self.mu.mem_write(PO_MAP + (r[1] << 6) + r[0], bytes([i + 1]))
    def tabla(self):
        n = struct.unpack('<i', self.mu.mem_read(PO_N, 4))[0]
        return [struct.unpack('<hhBBBB', self.mu.mem_read(PO_TAB + PO_REC * i, PO_REC)) for i in range(n)]
    def correr(self, start, stop, pila, regs=()):
        mu = self.mu
        mu.mem_write(STACK, pila); mu.reg_write(UC_X86_REG_ESP, STACK)
        for r, v in regs: mu.reg_write(r, v)
        mu.emu_start(start, stop, count=2000000)
        assert mu.reg_read(UC_X86_REG_EIP) == stop, hex(mu.reg_read(UC_X86_REG_EIP))

print('-- menú: tr_check desde br_menu')
def menu(ejs, x=5, y=7, turno=0, regs=(), p=0):
    # ejs: (ranura, bonos) del grupo de p; el primero es el líder, en (x, y).
    g = Juego(); mu = g.mu; g.poner(regs)
    mu.mem_write(0x537ce8, struct.pack('<h', p))
    for i, (ranura, bonos) in enumerate(ejs, 1):
        a = 0x54fe50 + i * 0x1c
        mu.mem_write(a + 2, struct.pack('<hh', x, y)); mu.mem_write(a + 0xe, struct.pack('<H', ranura | p << 5))
        if ranura < 16:
            rec = 0x53c410 + ((p << 4) + ranura) * 0xfc + 0xb2
            mu.mem_write(rec, b''.join(b.encode().ljust(9, b'\0') for b in bonos).ljust(36, b'\0'))
        mu.mem_write(p * 0x4f0 + 0x56ea94 + (i - 1) * 2, struct.pack('<h', i))
    mu.mem_write(p * 0x4f0 + 0x56eaa8, struct.pack('<h', len(ejs)))
    mu.mem_write(TR_FLAG, b'\x07')
    g.correr(BR_MENU, RET, bytes(4 * 4 + 0x14) + struct.pack('<I', RET),
             [(UC_X86_REG_ESI, 0x150000), (UC_X86_REG_EBX, turno), (UC_X86_REG_EBP, 1)])
    return mu.mem_read(TR_FLAG, 1)[0], struct.unpack('<hh', mu.mem_read(TR_X, 4))
ver('unidad con "Trap" en tierra libre: se puede, en la casilla del líder', menu([(3, ['Trap'])]), (1, (5, 7)))
ver('  "TRAP" entre otros bonos, en el segundo ejército', menu([(2, ['Landing']), (4, ['Carrier', 'TRAP'])])[0], 1)
ver('  jugador 3', menu([(3, ['Trap'])], p=3)[0], 1)
ver('control: sin el bono', menu([(3, ['Landing'])])[0], 0)
ver('control: solo un héroe con "Trap" (ranura 0x10)', menu([(0x10, ['Trap'])])[0], 0)
ver('control: "Traps" no es "Trap"', menu([(3, ['Traps'])])[0], 0)
ver('control: casilla con camino', menu([(3, ['Trap'])], x=10)[0], 0)
ver('control: ciudad', menu([(3, ['Trap'])], x=12, y=12)[0], 0)
ver('control: agua', menu([(3, ['Trap'])], x=33)[0], 0)
ver('control: ya hay un pozo ahí', menu([(3, ['Trap'])], regs=[(5, 7, 0, 0, 0, 0xff)])[0], 0)
ver('control: ya hay una trampa detonada ahí', menu([(3, ['Trap'])], regs=[(5, 7, 2, 1, 0xff, 0)])[0], 0)
ver('control: tabla llena', menu([(3, ['Trap'])], regs=[(1, 1, 0, 0, 0, 0xff)] * PO_MAX)[0], 0)
ver('control: no es su turno', menu([(3, ['Trap'])], turno=1)[0], 0)
ver('control: un pozo en otra casilla no molesta', menu([(3, ['Trap'])], regs=[(6, 7, 0, 0, 0, 0xff)])[0], 1)

print('-- diálogo: texto y envío')
g = Juego(); mu = g.mu
mu.mem_write(0x587e5c, struct.pack('<h', TR_MARK))
g.anotar(0x4dd260, '4dd260', 3)
g.correr(0x4b64f0, 0x4b651e, struct.pack('<I', RET))
_, que, fmt, nombre = g.llamadas[0]
txt = bytes(mu.mem_read(fmt, 32)).split(b'\0')[0]
ver('br_rebtxt con TR_MARK: 0x4dd260(5, "Building a trap", 0)', (que, txt, nombre), (5, b'Building a trap', 0))
def enviar(indice):
    g = Juego(); mu = g.mu
    mu.mem_write(TR_X, struct.pack('<hh', 5, 7))
    g.anotar(0x4b9ce0, 'reconstruir', 3)
    paquetes = []
    def red(a):
        paquetes.append((a[0], struct.unpack('<4h', mu.mem_read(a[1], 8)), a[2]))
    g.interceptar(0x4dd3b0, red)
    g.correr(TR_SEND, RET, struct.pack('<4I', RET, indice, CIUDAD, 0xabcd0002))
    return paquetes, [l for l in g.llamadas if l[0] == 'reconstruir'], mu.reg_read(UC_X86_REG_ESP) == STACK + 4
ver('tr_send con TR_MARK: TR_PKT (bando, x, y, 0), 8 bytes, y la pila queda bien',
    enviar(TR_MARK), ([(0x2a3, (2, 5, 7, 0), 8)], [], True))
ver('control: un sitio sigue a 0x4b9ce0(índice, costo, jugador)',
    enviar(4), ([], [('reconstruir', 4, CIUDAD, 0xabcd0002)], True))

print('-- red: tr_recv')
PKT = 0x150000
def recibir(p=2, x=5, y=7, maquina=1, oro=100, humano=True, regs=(), tipo=0x2a3):
    g = Juego(); mu = g.mu; g.poner(regs)
    s = 0x536b30 + p * 0x1f8
    mu.mem_write(s, b'\1'); mu.mem_write(s + 3, bytes([1]))                      # activo; máquina 1
    mu.mem_write(0x536c12 + p * 0x1f8, struct.pack('<h', -1 if humano else 0))
    mu.mem_write(0x536c14 + p * 0x1f8, struct.pack('<i', oro))
    mu.mem_write(PKT + 6, struct.pack('<h', maquina)); mu.mem_write(PKT + 0xc, struct.pack('<4h', p, x, y, 0))
    cobros = []
    g.interceptar(0x43fd60, lambda a: cobros.append((a[0] & 0xffff, struct.unpack('<i', struct.pack('<I', a[1]))[0])))
    g.interceptar(0x4057a0, lambda a: 0)
    g.interceptar(0x4a2170, lambda a: g.llamadas.append('redibujo'))
    fin = 0x4b85bb if tipo == 0x2a3 else dest(TR_RECV + 5, 2)
    g.correr(TR_RECV, fin, struct.pack('<I', RET), [(UC_X86_REG_EAX, tipo + 8), (UC_X86_REG_ESI, PKT)])
    return g.tabla()[len(regs):], cobros, mu.reg_read(UC_X86_REG_ESI) == PKT, mu.mem_read(PO_MAP + (y << 6) + x, 1)[0]
ver('trampa del bando 2: se cobra, se anota oculta (solo su bit) y entra en po_map',
    recibir(), ([(5, 7, 2, 0, 4, 2)], [(2, -CIUDAD)], True, 1))
ver('  detrás de lo que ya había', recibir(regs=[(1, 1, 0, 0, 0, 0xff)])[0::3], ([(5, 7, 2, 0, 4, 2)], 2))
ver('  justo con el oro del costo', recibir(oro=CIUDAD)[1], [(2, -CIUDAD)])
NADA = ([], [], True, 0)
ver('control: lo manda otra máquina', recibir(maquina=0), NADA)
ver('control: no alcanza el oro', recibir(oro=CIUDAD - 1), NADA)
ver('control: casilla con camino', recibir(x=10)[:3], NADA[:3])
ver('control: agua', recibir(x=33), NADA)
ver('control: bando de la computadora', recibir(humano=False), NADA)
ver('control: bando fuera de rango', recibir(p=9)[:3], NADA[:3])
ver('control: tabla llena', recibir(regs=[(1, 1, 0, 0, 0, 0xff)] * PO_MAX)[:2], NADA[:2])
ver('control: casilla ocupada por una trampa', recibir(regs=[(5, 7, 2, 0, 1, 0)])[:2], NADA[:2])
ver('control: otro paquete sigue a or_recv sin tocar nada', recibir(tipo=0x2a2)[:2], NADA[:2])

print('MAL:', mal)
sys.exit(1 if mal else 0)
