# Prueba de juguete de construir caminos (bd_* de build.py, paso C.1 de PENDIENTE-construcciones.md), en unicorn.
# Uso: python prueba_caminos.py [carpeta]   (por defecto C:\Warlords3; la que se le pasó a build.py)
# Menú: br_menu -> tr_check -> bd_check, que deja BD_FLAG. Costo: 0x4b65e0(BD_MARK, jugador) con br_cost.
# Diálogo: br_rebtxt con BD_MARK; tr_send arma BD_PKT. Red: bd_recv (desde 0x4b6a22) con un paquete de juguete.
# Mapa de juguete: x >= 30 agua; (20..22, *) montaña; (25, *) colinas; columna x = 10 camino de la hoja 0.
# Paso C.2: montaña vecina (bd_pick rota N, E, S, O con cada clic). Controles: sin el bono, héroe, "build" como bono de combate, agua, montaña, ya hay camino, ciudad, edificio, no
# es su turno; en la red: otra máquina, sin oro, bando de la computadora, casilla no apta.
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
assert img[BR_MENU - BASE:BR_MENU - BASE + 2] == b'\xc6\x05' and img[BR_MENU - BASE + 7:BR_MENU - BASE + 9] == b'\xc6\x05'
TR_FLAG, BD_FLAG = d32(BR_MENU + 2), d32(BR_MENU + 9)
TR_X, TR_Y = TR_FLAG + 2, TR_FLAG + 4
TR_SEND = dest(0x4b6236)
_i = img.index(b'\xb9\xa4\x02\x00\x00\xba', TR_SEND - BASE)
assert _i < TR_SEND - BASE + 0x40
BD_X = d32(BASE + _i + 6); BD_Y, BD_LX, BD_LY, BD_DIR = BD_X + 2, BD_X + 4, BD_X + 6, BD_X + 8
BD_PW = BD_X + 10
BD_HASB = BD_X + 12                # bd_check lo pone en 1 si el grupo tiene constructor
TR_CLICK = dest(0x4b0487)
_j = img.index(b'\x85\xc0\x0f\x84', TR_CLICK - BASE)
BD_PICK = dest(BASE + _j - 5)
BD_RECV = dest(0x4b6a22, 2)
if img[BD_RECV - BASE] == 0x3d and d32(BD_RECV + 1) == 0x2a5 + 8: BD_RECV = dest(BD_RECV + 5, 2)   # pp_recv (pausa manual) va primero
assert img[BD_RECV - BASE] == 0x3d and d32(BD_RECV + 1) == 0x2a4 + 8
BD_MARK, BD_PKT = 0x7ffe, 0x2a4
CIUDAD = 200                      # costo de fundar una ciudad ([0x56950e]); precio = CIUDAD * paso / 20
# tipo de terreno: (clase, costo de paso)
TERR = {0: (2, 2), 1: (1, 0), 2: (4, 0), 3: (3, 5)}
NOMBRE = {1: b'Water', 2: b'Mountains', 3: b'Hills'}

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
        for t, (c, paso) in TERR.items():
            mu.mem_write(0x535f0a + t * 0x58, struct.pack('<hh', paso, c))
            mu.mem_write(0x535ed6 + t * 0x58, NOMBRE.get(t, b'Plains') + b'\0')
        for y in range(30):
            for x in range(40):
                t = 1 if x >= 30 else 2 if 20 <= x <= 22 else 3 if x == 25 else 0
                est = 1 if x == 10 else 0
                mu.mem_write(casilla(x, y), struct.pack('<HBBxxxxH', t, 1, 0x18 | est, 0x91 if not est else 0))
        mu.mem_write(0x537e2a, struct.pack('<h', 0))
        mu.mem_write(0x56950e, struct.pack('<h', CIUDAD))
        for p in range(8):
            mu.mem_write(0x536c12 + p * 0x1f8, struct.pack('<h', -1))
        self.llamadas = []
        self.ajuste = {}
        self.interceptar(0x4057a0, lambda a: self.ajuste.get(a[0], 0))
    def interceptar(self, addr, fn, pop=0):
        def g(mu, a, size, _):
            sp = mu.reg_read(UC_X86_REG_ESP)
            ret, *args = struct.unpack('<9I', mu.mem_read(sp, 36))
            mu.reg_write(UC_X86_REG_EAX, (fn(args) or 0) & 0xffffffff)
            mu.reg_write(UC_X86_REG_ESP, sp + 4 + pop); mu.reg_write(UC_X86_REG_EIP, ret)
        self.mu.hook_add(UC_HOOK_CODE, g, begin=addr, end=addr)
    def anotar(self, addr, nombre, n, pop=0):
        self.interceptar(addr, lambda a: self.llamadas.append((nombre, *[v & 0xffffffff for v in a[:n]])), pop)
    def tile(self, x, y): return bytes(self.mu.mem_read(casilla(x, y), 10))
    def setp8(self, x, y, v): self.mu.mem_write(casilla(x, y) + 8, struct.pack('<H', v))
    def setb(self, x, y, off, v): self.mu.mem_write(casilla(x, y) + off, bytes([v]))
    def correr(self, start, stop, pila, regs=()):
        mu = self.mu
        mu.mem_write(STACK, pila); mu.reg_write(UC_X86_REG_ESP, STACK)
        for r, v in regs: mu.reg_write(r, v)
        mu.emu_start(start, stop, count=2000000)
        assert mu.reg_read(UC_X86_REG_EIP) == stop, hex(mu.reg_read(UC_X86_REG_EIP))

print('-- menú: bd_check desde br_menu')
# Desde 1.0.154.0 el muro de piedra se puede construir sobre un camino: las pruebas de camino y puente sobre una
# casilla con camino llenan la tabla de obras (lleno), así no se ofrece obra y siguen probando lo suyo.
_OB = b'OBRA'
_OBN = BASE + img.index(_OB) + 4
def lleno(prep=None):
    def f(g, *a):
        if prep: prep(g, *a)
        g.mu.mem_write(_OBN, struct.pack('<I', 64))
    return f
def menu(ejs, x=5, y=7, turno=0, p=0, prep=None):
    g = Juego(); mu = g.mu
    if prep: prep(g)
    mu.mem_write(0x537ce8, struct.pack('<h', p))
    for i, (ranura, comb, bonos) in enumerate(ejs, 1):
        a = 0x54fe50 + i * 0x1c
        mu.mem_write(a + 2, struct.pack('<hh', x, y)); mu.mem_write(a + 0xe, struct.pack('<H', ranura | p << 5))
        if ranura < 16:
            rec = 0x53c410 + ((p << 4) + ranura) * 0xfc
            mu.mem_write(rec + 0xb2, b''.join(b.encode().ljust(9, b'\0') for b in bonos).ljust(36, b'\0'))
            mu.mem_write(rec + 0xd6, comb.encode().ljust(9, b'\0'))
        mu.mem_write(p * 0x4f0 + 0x56ea94 + (i - 1) * 2, struct.pack('<h', i))
    mu.mem_write(p * 0x4f0 + 0x56eaa8, struct.pack('<h', len(ejs)))
    mu.mem_write(BD_FLAG, b'\x07')
    g.correr(BR_MENU, RET, bytes(4 * 4 + 0x14) + struct.pack('<I', RET),
             [(UC_X86_REG_ESI, 0x150000), (UC_X86_REG_EBX, turno), (UC_X86_REG_EBP, 1)])
    return mu.mem_read(BD_FLAG, 1)[0]
B = [(3, '', ['Build'])]
ver('unidad con "Build" en llanura libre: se puede', menu(B), 1)
ver('  "BUILD" en la tercera ranura, en el segundo ejército', menu([(2, '', ['Landing']), (4, '', ['hills', 'x', 'BUILD'])]), 1)
ver('  jugador 5, en colinas', menu(B, x=25, p=5), 1)
ver('control: sin el bono', menu([(3, '', ['Landing'])]), 0)
ver('control: "Build" como bono de combate no vale', menu([(3, 'Build', [])]), 0)
ver('control: solo un héroe con "Build"', menu([(0x10, '', ['Build'])]), 0)
ver('control: "Builder" no es "Build"', menu([(3, '', ['Builder'])]), 0)
ver('control: agua', menu(B, x=33), 0)
ver('control: montaña sin montaña vecina libre (pared de 3 con camino a los lados)', menu(B, x=21, prep=lambda g: [g.setb(x, y, 3, 0x19) for x in (20, 22) for y in (6, 7, 8)] + [g.setb(21, y, 3, 0x19) for y in (6, 8)]), 0)
ver('C.2: parado en camino junto a la montaña: se puede', menu(B, x=19, prep=lambda g: g.setb(19, 7, 3, 0x19)), 1)
ver('C.2: (volador) sobre montaña con montañas alrededor: se puede', menu(B, x=21), 1)
ver('control C.2: en camino lejos de montañas', menu(B, x=10, prep=lleno()), 0)
ver('  con lugar en la tabla: se puede (muro de piedra sobre el camino)', menu(B, x=10), 1)
ver('control: ciudad (estructura 3)', menu(B, prep=lambda g: g.setb(5, 7, 3, 0x1b)), 0)
ver('control: edificio (palabra 0 & 0x4000)', menu(B, prep=lambda g: g.mu.mem_write(casilla(5, 7), struct.pack('<H', 0x4000))), 0)
ver('control: no es su turno', menu(B, turno=1), 0)

print('-- costo: 0x4b65e0(BD_MARK, jugador)')
def costo(x, y, indice=BD_MARK, nombre=None, bando=0, rebaja=False, ajuste=0):
    g = Juego(); mu = g.mu
    g.ajuste[bando] = ajuste
    if rebaja:
        mu.mem_write(0x536c12 + bando * 0x1f8, struct.pack('<h', 0))
    if nombre:
        mu.mem_write(0x535ed6, nombre + b'\0')
    mu.mem_write(BD_X, struct.pack('<hh', x, y))
    g.correr(0x4b65e0, RET, struct.pack('<3I', RET, indice, bando))
    return struct.unpack('<h', struct.pack('<I', mu.reg_read(UC_X86_REG_EAX))[:2])[0]
ver('llanura: 5 % de 200 = 10', costo(5, 7), 10)
ver('colinas: 15 % = 30', costo(25, 7), 30)
for nom in (b'Desert', b'Desert Pla', b'Ice', b'Snow', b'Floor'):
    ver(f'{nom.decode()}: 15 % = 30', costo(5, 7, nombre=nom), 30)
for nom in (b'Forest', b'Marsh', b'Icy', b'Outlands'):
    ver(f'control {nom.decode()}: 5 % = 10', costo(5, 7, nombre=nom), 10)
ver('ciudad a mitad de precio para el bando (rebaja del juego): montaña 25 % de 100 = 25', costo(21, 7, bando=3, rebaja=True), 25)
ver('ajuste 0x4057a0 = 5 (ciudad -50 %): colinas 15 % de 100 = 15', costo(25, 7, bando=2, ajuste=5), 15)
ver('ajuste -5 (ciudad +50 %): llanura 5 % de 300 = 15', costo(5, 7, bando=1, ajuste=-5), 15)
ver('control: la rebaja de otro bando no cuenta', costo(21, 7, bando=4), 50)
ver('C.2 montaña (paso fijo 5, un cuarto de ciudad): 50', costo(21, 7), 50)
ver('control: un puente (BR_CODE) sigue costando una ciudad', costo(5, 7, 0x2000), CIUDAD)

print('-- diálogo: texto y envío')
def texto(d):
    g = Juego(); mu = g.mu
    mu.mem_write(0x587e5c, struct.pack('<h', BD_MARK)); mu.mem_write(BD_DIR, bytes([d]))
    g.anotar(0x4dd260, '4dd260', 3)
    g.correr(0x4b64f0, 0x4b651e, struct.pack('<I', RET))
    _, que, fmt, nombre = g.llamadas[0]
    return que, bytes(mu.mem_read(fmt, 32)).split(b'\0')[0], nombre
ver('br_rebtxt con BD_MARK en la casilla del líder: "Building a road"', texto(4), (5, b'Building a road', 0))
ver('  hacia el este: el mismo texto (la dirección va con flecha)', texto(1), (5, b'Building a road', 0))
def flecha(d, marca=None):
    g = Juego(); mu = g.mu
    mu.mem_write(0x587e5c, struct.pack('<h', BD_MARK if marca is None else marca)); mu.mem_write(BD_DIR, bytes([d]))
    g.anotar(0x4dd590, '4dd590', 7)
    g.correr(0x4b64a0, RET, struct.pack('<IIII', RET, 4, 100, 200))
    return [c[1:] for c in g.llamadas]
ver('flecha norte: mvarrow (0,128) 32x32 centrada', flecha(0), [(163, 0, 128, 32, 32, 108, 208)])
ver('flecha este', flecha(1), [(163, 64, 192, 32, 32, 108, 208)])
ver('flecha sur', flecha(2), [(163, 128, 0, 32, 32, 108, 208)])
ver('flecha oeste', flecha(3), [(163, 192, 64, 32, 32, 108, 208)])
ver('casilla propia: sin dibujo', flecha(4), [])
ver('  BD_DIR inválido: el texto común', texto(0xff), (5, b'Building a road', 0))
def enviar(indice):
    g = Juego(); mu = g.mu
    mu.mem_write(TR_X, struct.pack('<hh', 3, 4)); mu.mem_write(BD_X, struct.pack('<hh', 5, 7))
    g.anotar(0x4b9ce0, 'reconstruir', 3)
    paquetes = []
    g.interceptar(0x4dd3b0, lambda a: paquetes.append((a[0], struct.unpack('<4h', mu.mem_read(a[1], 8)), a[2])))
    g.correr(TR_SEND, RET, struct.pack('<4I', RET, indice, 20, 0xabcd0002))
    return paquetes, [l for l in g.llamadas if l[0] == 'reconstruir'], mu.reg_read(UC_X86_REG_ESP) == STACK + 4
ver('tr_send con BD_MARK: BD_PKT (bando, x, y, 0)', enviar(BD_MARK), ([(BD_PKT, (2, 5, 7, 0), 8)], [], True))
ver('control: la trampa sigue mandando 0x2a3 con la casilla del líder', enviar(0x7fff)[0][0][:2], (0x2a3, (2, 3, 4, 0)))
ver('control: un sitio sigue a 0x4b9ce0', enviar(4), ([], [('reconstruir', 4, 20, 0xabcd0002)], True))

print('-- C.2: bd_pick (cada clic ofrece el siguiente destino)')
def picks(x, y, n, prep=None, moverse=None):
    g = Juego(); mu = g.mu
    if prep: prep(g)
    mu.mem_write(BD_HASB, b'')
    mu.mem_write(TR_X, struct.pack('<hh', x, y))
    r = []
    for i in range(n):
        if moverse and i == moverse[0]: mu.mem_write(TR_X, struct.pack('<hh', *moverse[1]))
        g.correr(BD_PICK, RET, struct.pack('<I', RET))
        ok = mu.reg_read(UC_X86_REG_EAX)
        r.append((ok, *struct.unpack('<hh', mu.mem_read(BD_X, 4)), mu.mem_read(BD_DIR, 1)[0]) if ok else (0,))
    return r
ver('líder en llanura libre: siempre su casilla', picks(5, 7, 2), [(1, 5, 7, 4), (1, 5, 7, 255)])   # el segundo clic ofrece la torre
ver('volador sobre montaña: N, E, S, O y vuelve a N', picks(21, 7, 5),
    [(1, 21, 6, 0), (1, 22, 7, 1), (1, 21, 8, 2), (1, 20, 7, 3), (1, 21, 6, 0)])
cam19 = lambda g: g.setb(19, 7, 3, 0x19)
ver('en camino junto a la montaña: solo el este, una y otra vez', picks(19, 7, 2, lleno(cam19)), [(1, 20, 7, 1)] * 2)
ver('  se mueve: empieza de nuevo por el norte', picks(21, 7, 2, moverse=(1, (21, 12))), [(1, 21, 6, 0), (1, 21, 11, 0)])
ver('control: en camino lejos de montañas, nada', picks(10, 7, 1, lleno()), [(0,)])
ver('  con lugar en la tabla: el muro en su casilla (dirección N)', picks(10, 7, 1), [(1, 10, 7, 8)])

print('-- red: bd_recv')
PKT = 0x150000
def recibir(p=2, x=5, y=7, maquina=1, oro=100, humano=True, tipo=BD_PKT, prep=None, pw=0):
    g = Juego(); mu = g.mu
    if prep: prep(g)
    s = 0x536b30 + p * 0x1f8
    mu.mem_write(s, b'\1'); mu.mem_write(s + 3, bytes([1]))
    mu.mem_write(0x536c12 + p * 0x1f8, struct.pack('<h', -1 if humano else 0))
    mu.mem_write(0x536c14 + p * 0x1f8, struct.pack('<i', oro))
    mu.mem_write(PKT + 6, struct.pack('<h', maquina)); mu.mem_write(PKT + 0xc, struct.pack('<4h', p, x, y, pw))
    cobros = []
    g.interceptar(0x43fd60, lambda a: cobros.append((a[0] & 0xffff, struct.unpack('<i', struct.pack('<I', a[1]))[0])))
    g.interceptar(0x4a4f20, lambda a: g.llamadas.append('grafo'))
    g.interceptar(0x4a2170, lambda a: g.llamadas.append('redibujo'))
    g.interceptar(0x4d7ed0, lambda a: 0)
    fin = 0x4b85bb if tipo == BD_PKT else dest(BD_RECV + 5, 2)
    g.correr(BD_RECV, fin, struct.pack('<I', RET), [(UC_X86_REG_EAX, tipo + 8), (UC_X86_REG_ESI, PKT)])
    return g, cobros
def pieza(g, x, y):
    t = g.tile(x, y); v = struct.unpack('<H', t[8:10])[0]
    return t[3] & 7, (v >> 8) & 3, (v >> 5) & 7, v & 0x1f
g, c = recibir()
ver('camino suelto en llanura: cobra 10 (5 %), estructura 1, pieza horizontal (0,1), hoja 0', (c, pieza(g, 5, 7)), ([(2, -10)], (1, 0, 1, 0)))
ver('  conserva los otros bits de la casilla (byte 3 = 0x19) y rehace grafo y vista', (g.tile(5, 7)[3], g.llamadas), (0x19, ['grafo', 'redibujo']))
g, c = recibir(x=11, prep=lambda g: [g.setp8(10, y, 0x10 | (2 << 5)) for y in range(30)])
ver('al lado de la columna de camino: nueva = solo O (3,0) con el bit 0x10 del vecino',
    pieza(g, 11, 7), (1, 3, 0, 0x10))
ver('  la vecina pasa a N+E+S (0,6); las de arriba y abajo quedan N+S (0,2)',
    [pieza(g, 10, y)[1:3] for y in (6, 7, 8)], [(0, 2), (0, 6), (0, 2)])
def hoja1(g):
    for y in range(30): g.setp8(10, y, 1 | (2 << 5))
g, c = recibir(x=11, prep=hoja1)
ver('control: un vecino de otra hoja no se toca y no presta su hoja', (pieza(g, 10, 7), pieza(g, 11, 7)), ((1, 0, 2, 1), (1, 3, 0, 0)))
def puente(g):
    g.setb(30, 7, 3, 0x19); g.setp8(30, 7, (1 << 8) | (6 << 5))
g, c = recibir(x=29, prep=puente)
ver('junto a un puente: empalma (solo E, (3,1)) y el puente no se toca', (pieza(g, 29, 7), pieza(g, 30, 7)), ((1, 3, 1, 0), (1, 1, 6, 0)))
ver('justo con el oro del costo', recibir(oro=10)[1], [(2, -10)])
def nada(**kw):
    g, c = recibir(**kw)
    return c, g.llamadas, g.tile(kw.get('x', 5), kw.get('y', 7))[3] & 7
ver('control: lo manda otra máquina', nada(maquina=0), ([], [], 0))
ver('control: no alcanza el oro', nada(oro=9), ([], [], 0))
ver('control: bando de la computadora', nada(humano=False), ([], [], 0))
ver('control: bando fuera de rango', nada(p=9), ([], [], 0))
g, c = recibir(x=21)
ver('C.2: camino en montaña: cobra 50, estructura 1, pieza (0,1)', (c, pieza(g, 21, 7)), ([(2, -50)], (1, 0, 1, 0)))
ver('control: montaña sin oro suficiente', nada(x=21, oro=49), ([], [], 0))
ver('control: montaña con camino (no cobra dos veces)', nada(x=21, prep=lambda g: g.setb(21, 7, 3, 0x19)), ([], [], 1))
ver('control: agua', nada(x=33), ([], [], 0))
ver('control: ya hay camino (no cobra dos veces)', nada(x=10), ([], [], 1))
ver('control: otro paquete sigue a tr_recv sin tocar nada', nada(tipo=0x2a3), ([], [], 0))

print('-- puente nuevo sobre agua (punto 8)')
# Lago en la fila 15: agua x = 30..33 y tierra en 34. Fila 20: 9 de agua (30..38) y tierra en 39: demasiado largo.
# Vertical en x = 31: tierra en (31, 2) y (31, 6), agua 3..5. Lava: tipo 4 (clase 1, "Lava") en (31, 25), tierra en 32.
def lago(g, camino=True):
    mu = g.mu
    mu.mem_write(0x535f0a + 4 * 0x58, struct.pack('<hh', 9, 1)); mu.mem_write(0x535ed6 + 4 * 0x58, b'Lava\0')
    for x, y in ((34, 15), (39, 20), (31, 2), (31, 6), (32, 25), (29, 25)):
        mu.mem_write(casilla(x, y), struct.pack('<H', 0))
    mu.mem_write(casilla(31, 25), struct.pack('<H', 4))
    mu.mem_write(casilla(30, 25), struct.pack('<H', 0))
    if camino:
        for x, y in ((29, 15), (29, 20), (31, 2), (30, 25)): g.setb(x, y, 3, 0x19); g.setp8(x, y, 0)
ver('menú: en camino a orillas del lago: se puede (puente)', menu(B, x=29, y=15, prep=lago), 1)
ver('control: en camino frente al mar abierto: no', menu(B, x=29, y=7, prep=lleno(lambda g: g.setb(29, 7, 3, 0x19))), 0)
ver('control: 9 casillas de agua no llegan: no', menu(B, x=29, y=20, prep=lleno(lago)), 0)
def picks_pw(x, y, n, prep):
    g = Juego(); mu = g.mu; prep(g)
    mu.mem_write(BD_HASB, b'')
    mu.mem_write(TR_X, struct.pack('<hh', x, y))
    r = []
    for i in range(n):
        g.correr(BD_PICK, RET, struct.pack('<I', RET))
        ok = mu.reg_read(UC_X86_REG_EAX)
        r.append((ok, *struct.unpack('<hh', mu.mem_read(BD_X, 4)), mu.mem_read(BD_DIR, 1)[0],
                  struct.unpack('<H', mu.mem_read(BD_PW, 2))[0]) if ok else (0,))
    return r
ver('bd_pick en camino junto al lago: puente al este, una y otra vez', picks_pw(29, 15, 2, lleno(lago)), [(1, 30, 15, 1, 0x101)] * 2)
ver('  sin camino: su casilla (camino) y luego el puente', picks_pw(29, 15, 3, lambda g: lago(g, False)),
    [(1, 29, 15, 4, 0), (1, 30, 15, 1, 0x101), (1, 29, 15, 255, 0x4004)])   # después, la torre
ver('  puente vertical al sur', picks_pw(31, 2, 1, lago), [(1, 31, 3, 2, 0x102)])
def costo_pw(x, y, pw):
    g = Juego(); mu = g.mu; lago(g)
    mu.mem_write(BD_X, struct.pack('<hh', x, y)); mu.mem_write(BD_PW, struct.pack('<H', pw))
    g.correr(0x4b65e0, RET, struct.pack('<III', RET, BD_MARK, 0))
    return mu.reg_read(UC_X86_REG_EAX) & 0xffff
ver('costo: puente de 4 sobre agua = 4 x 30 % de 200 = 240', costo_pw(30, 15, 0x101), 240)
ver('costo: lava de 1 = 60 % = 120', costo_pw(31, 25, 0x101), 120)
def texto_pw():
    g = Juego(); mu = g.mu
    mu.mem_write(0x587e5c, struct.pack('<h', BD_MARK)); mu.mem_write(BD_DIR, b'\1'); mu.mem_write(BD_PW, struct.pack('<H', 0x101))
    g.anotar(0x4dd260, '4dd260', 3)
    g.correr(0x4b64f0, 0x4b651e, struct.pack('<I', RET))
    return bytes(mu.mem_read(g.llamadas[0][2], 32)).split(b'\0')[0]
ver('texto: "Building a bridge"', texto_pw(), b'Building a bridge')
def enviar_pw():
    g = Juego(); mu = g.mu
    mu.mem_write(BD_X, struct.pack('<hh', 30, 15)); mu.mem_write(BD_PW, struct.pack('<H', 0x101))
    paquetes = []
    g.interceptar(0x4dd3b0, lambda a: paquetes.append((a[0], struct.unpack('<4h', mu.mem_read(a[1], 8)))))
    g.correr(TR_SEND, RET, struct.pack('<4I', RET, BD_MARK, 20, 2))
    return paquetes
ver('envío: BD_PKT con 0x101 (puente al este)', enviar_pw(), [(BD_PKT, (2, 30, 15, 0x101))])
g, c = recibir(x=30, y=15, pw=0x101, oro=500, prep=lago)
ver('red: puente de 4 al este: cobra 240, punta (1,6) + medios (3,4) + punta (1,7)',
    (c, [pieza(g, x, 15)[:3] for x in range(30, 34)], g.llamadas),
    ([(2, -240)], [(1, 1, 6), (1, 3, 4), (1, 3, 4), (1, 1, 7)], ['grafo', 'redibujo']))
ver('  el camino de la orilla oeste empalma (solo E)', pieza(g, 29, 15)[:3], (1, 3, 1))
g, c = recibir(x=31, y=3, pw=0x102, oro=500, prep=lago)
ver('red: vertical de 3 al sur: (2,7) (3,5) (2,6), cobra 180', (c, [pieza(g, 31, y)[:3] for y in (3, 4, 5)]),
    ([(2, -180)], [(1, 2, 7), (1, 3, 5), (1, 2, 6)]))
g, c = recibir(x=33, y=15, pw=0x103, oro=500, prep=lambda g: (lago(g), g.setb(34, 15, 3, 0x19)))
ver('red: el mismo lago desde el este (oeste): (1,7) en 33 ... (1,6) en 30', [pieza(g, x, 15)[:3] for x in (30, 31, 33)],
    [(1, 1, 6), (1, 3, 4), (1, 1, 7)])
g, c = recibir(x=31, y=25, pw=0x101, oro=500, prep=lago)
ver('red: lava de una casilla: tramo medio (3,4), cobra 120', (c, pieza(g, 31, 25)[:3]), ([(2, -120)], (1, 3, 4)))
def nada_pw(x, y, pw, oro=500, prep=lago):
    g, c = recibir(x=x, y=y, pw=pw, oro=oro, prep=prep)
    return c, g.llamadas, [g.tile(xx, y)[3] & 7 for xx in range(30, 34)]
ver('control: no alcanza el oro (239)', nada_pw(30, 15, 0x101, oro=239), ([], [], [0, 0, 0, 0]))
ver('control: 9 de agua no llegan', nada_pw(30, 20, 0x101), ([], [], [0, 0, 0, 0]))
ver('control: mar abierto', nada_pw(30, 7, 0x101), ([], [], [0, 0, 0, 0]))
ver('control: empieza en agua (la de atrás también es agua)', nada_pw(31, 15, 0x101), ([], [], [0, 0, 0, 0]))
ver('control: un puente derribado en el medio', nada_pw(30, 15, 0x101, prep=lambda g: (lago(g), g.setb(32, 15, 9, 0x80))),
    ([], [], [0, 0, 0, 0]))
ver('control: un edificio en el agua', nada_pw(30, 15, 0x101, prep=lambda g: (lago(g), g.mu.mem_write(casilla(31, 15), struct.pack('<H', 0x4001)))),
    ([], [], [0, 0, 0, 0]))

print('MAL:', mal)
sys.exit(1 if mal else 0)
