# Prueba de juguete del paso G de PENDIENTE-construcciones.md (ciudad propia -> puerto), en unicorn.
# Uso: python prueba_puerto.py [carpeta]   (por defecto C:\Warlords3; la que se le pasó a build.py)
# Mapa: x >= 30 agua. Ciudad 0 «Delingor» del bando 2 en (28, 10) (casillas 28..29, 10..11): el puerto va a (30, 10),
# la primera casilla de agua libre del anillo. Ciudad 1 del bando 2 en (5, 5). Ya hay 3 sitios.
# Menú: bd_check sin constructor. Rotación: bd_pick (destino 5). Costo, texto, envío. Red: bd_recv con PW 0x8000|ciudad.
# Controles: ciudad ajena, última ciudad, sin agua, 50 sitios, sin oro, x, y que no es la del puerto, una ciudad arrasada
# común sigue estando en el mapa y sigue siendo meta 9 de la IA.
import os, sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

DIR = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3'
STACK, RET = 0x1f0000, 0x100
pe = pefile.PE(os.path.join(DIR, 'DarklordAV.exe'))
BASE, img = pe.OPTIONAL_HEADER.ImageBase, bytes(pe.get_memory_mapped_image())
def d32(va): return struct.unpack_from('<I', img, va - BASE)[0]
def dest(va, n=1): return va + n + 4 + struct.unpack_from('<i', img, va - BASE + n)[0]
BR_MENU = dest(0x4b0a1c)
TR_FLAG, BD_FLAG = d32(BR_MENU + 2), d32(BR_MENU + 9)
TR_X = TR_FLAG + 2
TR_SEND = dest(0x4b6236)
_i = img.index(b'\xb9\xa4\x02\x00\x00\xba', TR_SEND - BASE)
BD_X = d32(BASE + _i + 6); BD_DIR, BD_PW, BD_HASB = BD_X + 8, BD_X + 10, BD_X + 12
TR_CLICK = dest(0x4b0487)
_j = img.index(b'\x85\xc0\x0f\x84', TR_CLICK - BASE)
BD_PICK = dest(BASE + _j - 5)
BD_RECV = dest(0x4b6a22, 2)
assert img[BD_RECV - BASE] == 0x3d and d32(BD_RECV + 1) == 0x2a4 + 8
assert img[0x440c26 - BASE] == 0xe9 and img[0x41e30a - BASE] == 0xe9, 'faltan los ganchos 0x440c26 / 0x41e30a'
BD_MARK, BD_PKT = 0x7ffe, 0x2a4
CIUDAD = 200
CITIES, SITES, NSITES = 0x537e2c, 0x55acb6, 0x55acb4
P = 2

mal = 0
def ver(nombre, r, esperado):
    global mal
    ok = r == esperado
    mal += not ok
    print('OK ' if ok else 'MAL', nombre, '->', r)

def casilla(x, y): return 0x503e58 + ((y * 10) << 6) + x * 10
class Juego:
    def __init__(self, dueno1=P, nombre=b'Delingor'):
        mu = self.mu = Uc(UC_ARCH_X86, UC_MODE_32)
        size = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
        mu.mem_map(BASE, size); mu.mem_write(BASE, img[:size])
        mu.mem_map(0, 0x1000); mu.mem_map(0x100000, 0x100000)
        mu.mem_write(0x503e00, struct.pack('<hh', 40, 30)); mu.mem_write(0x503e06, b'\6')
        for t, (c, paso, nom) in {0: (2, 2, b'Plains'), 1: (1, 0, b'Water')}.items():
            mu.mem_write(0x535f0a + t * 0x58, struct.pack('<hh', paso, c))
            mu.mem_write(0x535ed6 + t * 0x58, nom + b'\0')
        for y in range(30):
            for x in range(40):
                mu.mem_write(casilla(x, y), struct.pack('<HBBxxxxH', 1 if x >= 30 else 0, 1, 0x18, 0x91))
        # tierra común del anillo con palabra 1 baja 0: (27, 10) es la primera en el orden de pt_ring -> plantilla 0x123
        mu.mem_write(casilla(27, 10) + 2, b'\0'); mu.mem_write(casilla(27, 10) + 8, struct.pack('<H', 0x123))
        for i, (cx, cy, dueno) in enumerate(((28, 10, P), (5, 5, dueno1))):
            c = CITIES + i * 0xde
            mu.mem_write(c, struct.pack('<hh', cx, cy)); mu.mem_write(c + 4, (nombre if i == 0 else b'Otra') + b'\0')
            mu.mem_write(c + 0xa4, bytes([2, dueno]))
            for dx in (0, 1):
                for dy in (0, 1):
                    mu.mem_write(casilla(cx + dx, cy + dy), struct.pack('<HBB', 0x4000 | (dueno << 10), 5, 0x1b))
                    mu.mem_write(casilla(cx + dx, cy + dy) + 8, struct.pack('<H', 0x77))
        mu.mem_write(0x537e2a, struct.pack('<h', 2))
        mu.mem_write(NSITES, struct.pack('<h', 3))
        mu.mem_write(0x56950e, struct.pack('<h', CIUDAD))
        for p in range(8):
            mu.mem_write(0x536c12 + p * 0x1f8, struct.pack('<h', -1))
        mu.mem_write(0x537ce8, struct.pack('<h', P))
        self.llamadas = []
        self.interceptar(0x4057a0, lambda a: 0)
    def interceptar(self, addr, fn, pop=0):
        def g(mu, a, size, _):
            sp = mu.reg_read(UC_X86_REG_ESP)
            ret, *args = struct.unpack('<9I', mu.mem_read(sp, 36))
            mu.reg_write(UC_X86_REG_EAX, (fn(args) or 0) & 0xffffffff)
            mu.reg_write(UC_X86_REG_ESP, sp + 4 + pop); mu.reg_write(UC_X86_REG_EIP, ret)
        self.mu.hook_add(UC_HOOK_CODE, g, begin=addr, end=addr)
    def anotar(self, addr, nombre, n):
        self.interceptar(addr, lambda a: self.llamadas.append((nombre, *[v & 0xffffffff for v in a[:n]])))
    def tile(self, x, y):
        t = bytes(self.mu.mem_read(casilla(x, y), 10))
        return struct.unpack('<H', t[:2])[0], t[2], t[3], struct.unpack('<H', t[8:])[0]
    def correr(self, start, stop, pila, regs=()):
        mu = self.mu
        mu.mem_write(STACK, pila); mu.reg_write(UC_X86_REG_ESP, STACK)
        for r, v in regs: mu.reg_write(r, v)
        mu.emu_start(start, stop, count=2000000)
        assert mu.reg_read(UC_X86_REG_EIP) == stop, hex(mu.reg_read(UC_X86_REG_EIP))
    def ciudad_en(self, x, y):
        self.correr(0x440be0, RET, struct.pack('<3I', RET, x, y))
        return struct.unpack('<h', struct.pack('<H', self.mu.reg_read(UC_X86_REG_EAX) & 0xffff))[0]

sin_agua = lambda g: [g.mu.mem_write(casilla(30, y), struct.pack('<H', 0)) for y in (10, 11)]
sitios50 = lambda g: g.mu.mem_write(NSITES, struct.pack('<h', 50))

print('-- menú: bd_check desde br_menu (sin constructor)')
def menu(x=28, y=10, bonos=('Landing',), prep=None, **kw):
    g = Juego(**kw); mu = g.mu
    if prep: prep(g)
    a = 0x54fe50 + 0x1c
    mu.mem_write(a + 2, struct.pack('<hh', x, y)); mu.mem_write(a + 0xe, struct.pack('<H', 3 | P << 5))
    rec = 0x53c410 + ((P << 4) + 3) * 0xfc
    mu.mem_write(rec + 0xb2, b''.join(b.encode().ljust(9, b'\0') for b in bonos).ljust(36, b'\0'))
    mu.mem_write(P * 0x4f0 + 0x56ea94, struct.pack('<h', 1)); mu.mem_write(P * 0x4f0 + 0x56eaa8, struct.pack('<h', 1))
    mu.mem_write(BD_FLAG, b'\x07')
    g.correr(BR_MENU, RET, bytes(4 * 4 + 0x14) + struct.pack('<I', RET),
             [(UC_X86_REG_ESI, 0x150000), (UC_X86_REG_EBX, 0), (UC_X86_REG_EBP, 1)])
    return mu.mem_read(BD_FLAG, 1)[0], mu.mem_read(BD_HASB, 1)[0]
ver('en su ciudad costera, sin "Build": se puede (y no hay constructor)', menu(), (1, 0))
ver('  en otra casilla de la ciudad (29, 11)', menu(29, 11), (1, 0))
ver('  con "Build" también', menu(bonos=('Build',)), (1, 1))
ver('control: ciudad ajena', menu(prep=lambda g: g.mu.mem_write(CITIES + 0xa5, b'\3')), (0, 0))
ver('control: es su última ciudad', menu(dueno1=3), (0, 0))
ver('control: la otra ciudad está arrasada (cuenta como última)', menu(prep=lambda g: g.mu.mem_write(CITIES + 0xde + 0xa4, b'\0')), (0, 0))
ver('control: sin agua al lado', menu(prep=sin_agua), (0, 0))
ver('control: ya hay 50 sitios', menu(prep=sitios50), (0, 0))
ver('control: fuera de la ciudad, en llanura', menu(12, 12), (0, 0))

print('-- bd_pick: destino 5 (puerto)')
def picks(n, hasb=0, prep=None):
    g = Juego(); mu = g.mu
    if prep: prep(g)
    mu.mem_write(BD_HASB, bytes([hasb])); mu.mem_write(TR_X, struct.pack('<hh', 28, 10))
    r = []
    for _ in range(n):
        g.correr(BD_PICK, RET, struct.pack('<I', RET))
        ok = mu.reg_read(UC_X86_REG_EAX)
        r.append((ok, *struct.unpack('<hh', mu.mem_read(BD_X, 4)), mu.mem_read(BD_DIR, 1)[0],
                  struct.unpack('<H', mu.mem_read(BD_PW, 2))[0]) if ok else (0,))
    return r
ver('sin constructor: el puerto, una y otra vez', picks(2), [(1, 30, 10, 0xff, 0x8000)] * 2)
ver('con constructor en la ciudad (no hay camino posible): el puerto', picks(2, 1), [(1, 30, 10, 0xff, 0x8000)] * 2)
ver('con (30, 10) ocupada: el puerto va a (30, 11)', picks(1, prep=lambda g: g.mu.mem_write(casilla(30, 10) + 3, b'\x1c')),
    [(1, 30, 11, 0xff, 0x8000)])

print('-- costo, texto y envío')
def costo(rebaja=False):
    g = Juego(); mu = g.mu
    if rebaja: mu.mem_write(0x536c12 + P * 0x1f8, struct.pack('<h', 0))
    mu.mem_write(BD_X, struct.pack('<hh', 30, 10)); mu.mem_write(BD_PW, struct.pack('<H', 0x8000))
    g.correr(0x4b65e0, RET, struct.pack('<III', RET, BD_MARK, P))
    return mu.reg_read(UC_X86_REG_EAX) & 0xffff
ver('costo: el doble de fundar una ciudad = 400', costo(), 400)
ver('  con la rebaja de ciudad del bando: 200', costo(True), 200)
def texto():
    g = Juego(); mu = g.mu
    mu.mem_write(0x587e5c, struct.pack('<h', BD_MARK)); mu.mem_write(BD_DIR, b'\xff'); mu.mem_write(BD_PW, struct.pack('<H', 0x8000))
    g.anotar(0x4dd260, '4dd260', 3)
    g.correr(0x4b64f0, 0x4b651e, struct.pack('<I', RET))
    return bytes(mu.mem_read(g.llamadas[0][2], 32)).split(b'\0')[0]
ver('texto: "City into a port"', texto(), b'City into a port')
def enviar():
    g = Juego(); mu = g.mu
    mu.mem_write(BD_X, struct.pack('<hh', 30, 10)); mu.mem_write(BD_PW, struct.pack('<H', 0x8000))
    paquetes = []
    g.interceptar(0x4dd3b0, lambda a: paquetes.append((a[0], struct.unpack('<4H', mu.mem_read(a[1], 8)))))
    g.correr(TR_SEND, RET, struct.pack('<4I', RET, BD_MARK, 20, P))
    return paquetes
ver('envío: BD_PKT (2, 30, 10, 0x8000)', enviar(), [(BD_PKT, (P, 30, 10, 0x8000))])

print('-- red: bd_recv')
PKT = 0x150000
def recibir(p=P, x=30, y=10, pw=0x8000, oro=500, prep=None, **kw):
    g = Juego(**kw); mu = g.mu
    if prep: prep(g)
    s = 0x536b30 + p * 0x1f8
    mu.mem_write(s, b'\1'); mu.mem_write(s + 3, bytes([1]))
    mu.mem_write(0x536c14 + p * 0x1f8, struct.pack('<i', oro))
    mu.mem_write(PKT + 6, struct.pack('<h', 1)); mu.mem_write(PKT + 0xc, struct.pack('<4H', p, x, y, pw))
    cobros = []
    g.interceptar(0x43fd60, lambda a: cobros.append((a[0] & 0xffff, struct.unpack('<i', struct.pack('<I', a[1]))[0])))
    g.anotar(0x46a3a0, 'dueño', 2); g.anotar(0x46a120, 'avisa', 1); g.anotar(0x441290, 'dueños', 0)
    g.interceptar(0x4a4f20, lambda a: g.llamadas.append('grafo'))
    g.interceptar(0x4a2170, lambda a: g.llamadas.append('redibujo'))
    g.interceptar(0x4d7ed0, lambda a: 0)
    g.correr(BD_RECV, 0x4b85bb, struct.pack('<I', RET), [(UC_X86_REG_EAX, BD_PKT + 8), (UC_X86_REG_ESI, PKT)])
    return g, cobros
g, c = recibir()
mu = g.mu
ver('cobra 400 y avisa (dueño 8, 0x46a120, 0x441290) y rehace grafo y vista',
    (c, g.llamadas), ([(P, -400)], [('dueño', 0, 8), ('avisa', 0), ('dueños',), 'grafo', 'redibujo']))
ver('  la ciudad queda arrasada y marcada (+0xa4 = 0, +0xdd = 1)', (mu.mem_read(CITIES + 0xa4, 1)[0], mu.mem_read(CITIES + 0xdd, 1)[0]), (0, 1))
ver('  0x440be0 ya no la encuentra en ninguna de sus 4 casillas', [g.ciudad_en(x, y) for x in (28, 29) for y in (10, 11)], [-1] * 4)
ver('  control: la otra ciudad sigue en (5, 5) y (6, 6)', (g.ciudad_en(5, 5), g.ciudad_en(6, 6)), (1, 1))
ver('  sus 4 casillas: sin edificio, estructura 0, palabra 1 baja 0, +8 = 0x123 de (27, 10)',
    [g.tile(x, y) for x in (28, 29) for y in (10, 11)], [(P << 10, 0, 0x18, 0x123)] * 4)
ver('  el puerto en (30, 10): agua, dueño 8 | 0x4000, estructura 4, +8 = 0x20', g.tile(30, 10), (0x6001, 0, 0x1c, 0x20))
ver('  control: (30, 11) no se toca', g.tile(30, 11), (1, 1, 0x18, 0x91))
sitio = bytes(mu.mem_read(SITES + 3 * 0x96, 0x96))
ver('  sitio nuevo 3: (30, 10) «Port Delingor» tipo 0, y ya son 4',
    (struct.unpack('<hh', sitio[:4]), sitio[4:20].split(b'\0')[0], sitio[0x94], sitio[0x95], struct.unpack('<h', mu.mem_read(NSITES, 2))[0]),
    ((30, 10), b'Port Delingor', 0, 0, 4))
g, c = recibir(nombre=b'Delingorxyzw12')
ver('nombre largo: «Port » + 10 letras', bytes(g.mu.mem_read(SITES + 3 * 0x96 + 4, 16)).split(b'\0')[0], b'Port Delingorxy')
ver('justo con el oro del costo', recibir(oro=400)[1], [(P, -400)])
def nada(**kw):
    g, c = recibir(**kw)
    return c, g.llamadas, g.mu.mem_read(CITIES + 0xdd, 1)[0], struct.unpack('<h', g.mu.mem_read(NSITES, 2))[0]
NADA = ([], [], 0, 3)
ver('control: no alcanza el oro', nada(oro=399), NADA)
ver('control: x, y que no es la del puerto', nada(x=30, y=11), NADA)
ver('control: ciudad ajena (paquete de otro bando)', nada(p=3), NADA)
ver('control: es su última ciudad', nada(dueno1=3), NADA)
ver('control: sin agua al lado', nada(prep=sin_agua)[:3], NADA[:3])
ver('control: ya hay 50 sitios', nada(prep=sitios50)[:3], NADA[:3])
ver('control: índice de ciudad fuera de rango', nada(pw=0x8005), NADA)
ver('control: ya convertida (marcada) no se cobra de nuevo', nada(prep=lambda g: g.mu.mem_write(CITIES + 0xdd, b'\1'))[:2], ([], []))

print('-- ciudad arrasada común (sin marca): todo como antes')
g = Juego(); g.mu.mem_write(CITIES + 0xa4, b'\0')
ver('0x440be0 la sigue encontrando', g.ciudad_en(29, 11), 0)
def meta9(marca):
    g = Juego(); mu = g.mu
    mu.mem_write(CITIES + 0xa4, b'\0'); mu.mem_write(CITIES + 0xdd, bytes([marca]))
    fin = []
    for a in (0x41e311, 0x41e4d8):
        mu.hook_add(UC_HOOK_CODE, lambda mu, ad, s, _: (fin.append(ad), mu.emu_stop()), begin=a, end=a)
    mu.reg_write(UC_X86_REG_EAX, 0); mu.reg_write(UC_X86_REG_ESP, STACK)
    mu.emu_start(0x41e30a, 0, count=20)
    return fin[0], mu.reg_read(UC_X86_REG_EFLAGS) >> 6 & 1
ver('meta 9: la arrasada común sigue (0x41e311 con ZF = 1, «está muerta»)', meta9(0), (0x41e311, 1))
ver('meta 9: la convertida en puerto se salta (0x41e4d8)', meta9(1)[0], 0x41e4d8)

print('-- pantalla de ciudades (0x404893) y minimapa (0x412320, 0x412809, 0x412bde): la marcada no está (tarea 97)')
def salto(inicio, fines, marca, i=0, regs=(), pila=b''):
    # Corre desde el gancho hasta la primera dirección de «fines»; ciudad i marcada o no (2 ciudades).
    g = Juego(); mu = g.mu
    mu.mem_write(CITIES + i * 0xde + 0xdd, bytes([marca]))
    fin = []
    for a in fines:
        mu.hook_add(UC_HOOK_CODE, lambda mu, ad, s, _: (fin.append(ad), mu.emu_stop()), begin=a, end=a)
    mu.mem_write(STACK, pila.ljust(0x40, b'\0')); mu.reg_write(UC_X86_REG_ESP, STACK)
    for r, v in regs: mu.reg_write(r, v)
    mu.emu_start(inicio, 0, count=200)
    return fin[0] if fin else None, mu
for m in (0, 1):
    a, mu = salto(0x404893, (0x40489a, 0x4048cb), m, regs=((UC_X86_REG_EBX, 0),))
    ver(f'pantalla: marca {m}', (a, mu.reg_read(UC_X86_REG_AX) if a == 0x40489a else None),
        ((0x40489a, 28), (0x4048cb, None))[m])
    a, mu = salto(0x412809, (0x41280f, 0x412a61), m, regs=((UC_X86_REG_DI, 0),))
    ver(f'minimapa 2: marca {m}', (a, mu.reg_read(UC_X86_REG_EDX) if a == 0x41280f else None),
        ((0x41280f, 0), (0x412a61, None))[m])
for f, (sig, ret, sal, off) in {1: (0x412325, 0x412320, 0x412551, 0x16), 3: (0x412be3, 0x412bde, 0x412ed2, 0x1a)}.items():
    for m, i, esp in ((0, 0, sig), (1, 0, ret), (1, 1, sal)):
        pila = bytearray(0x40); struct.pack_into('<h', pila, off, i)
        a, mu = salto(dest(ret), (sig, sal, ret), m, i, pila=bytes(pila))
        if (m, i) == (1, 0):  # vuelve al gancho con la siguiente ciudad
            a = (a, struct.unpack('<h', mu.mem_read(STACK + off, 2))[0])
            esp = (ret, 1)
        ver(f'minimapa {f}: ciudad {i} marca {m}', a, esp)

print('-- minimapas de pantallas (0x4125a2, City Improvements; 0x41303b): la marcada no está (tarea 98)')
for f, (ini, sig, sal, reg, chk) in {4: (0x4125a2, 0x4125a8, 0x4127ca, UC_X86_REG_BX, UC_X86_REG_ECX),
                                     5: (0x41303b, 0x413042, 0x413142, UC_X86_REG_DI, UC_X86_REG_EBP)}.items():
    for m in (0, 1):
        a, mu = salto(ini, (sig, sal), m, regs=((reg, 0),))
        ver(f'minimapa {f}: marca {m}', (a, mu.reg_read(chk) if a == sig else mu.reg_read(reg)),
            ((sig, 0), (sal, 1))[m])

print('-- trucos del chat desactivados (0x4552cf salta a la salida 0x456444)')
a, mu = salto(0x4552cf, (0x4552d3, 0x4552d9, 0x456444), 0, regs=((UC_X86_REG_SI, 1),))
ver('con un solo humano igual sale sin aplicar', a, 0x456444)

print('-- Acerca de: controles 8-10 con parche, fecha y créditos; pila igual que en el original')
g = Juego(); textos = []
g.interceptar(0x4dd260, lambda a: textos.append((a[0], bytes(g.mu.mem_read(a[1], 64)).split(b'\0')[0].decode())))
ABOUT = dest(0x4a97b7)
g.mu.reg_write(UC_X86_REG_ESP, STACK); g.mu.emu_start(ABOUT, 0x4a9886, count=500)
ver('vuelve a 0x4a9886 con 0xc bytes menos de pila', g.mu.reg_read(UC_X86_REG_ESP) - STACK, 0xc)
ver_txt = next(l.split('|')[1] for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'parches.txt'),
                                              encoding='latin1') if l.startswith('vista-aliada|'))
ver('valores 8-10 vacíos', textos, [(8, ''), (9, ''), (10, '')])
_r = open(r'C:\Warlords3\DATA\WAR3AV.RES', 'rb').read(); _o = 8
while struct.unpack_from('<II', _r, _o)[:2] != (7, 94): _o += 20 + struct.unpack_from('<I', _r, _o + 16)[0]
_p = _o + 20; _col = {}
for _ in range(struct.unpack_from('<I', _r, _o + 8)[0]):
    _t, _i = struct.unpack_from('<II', _r, _p)
    if _t == 0x12 and _i in (5, 6, 7): _col[_i] = (struct.unpack_from('<I', _r, _p + 8)[0], struct.unpack_from('<I', _r, _p + 0x24)[0],
                                                   _r[_p + 0x2c:_p + 0x6c].split(b'\0')[0].decode('latin1'))
    _p += 4 + {0x12: 0x68, 0x13: 0x28, 0x15: 0xac}[_t]
ver('rótulos claros 5-7 centrados con el texto completo', [(_col[i][0], _col[i][1], _col[i][2].split(',')[0]) for i in (5, 6, 7)],
    [(0xb1, 1, f'Patch vista-aliada {ver_txt}'), (0xb1, 1, 'Credits: @elCoprofago'), (0xb1, 1, 'Anthropic Claude')])
print('   ', _col[5][2])
print('MAL:', mal)
sys.exit(1 if mal else 0)
