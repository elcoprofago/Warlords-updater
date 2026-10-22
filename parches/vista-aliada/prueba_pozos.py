# Prueba de juguete de pozos, remolinos y trampas (po_* de build.py) sobre el exe parcheado y el original, en unicorn.
# Uso: python prueba_pozos.py [carpeta]   (por defecto C:\Warlords3; armarla antes con build.py)
# Parte 1, datos + SAV: guardar y cargar corren desde la última escritura y la última lectura del .SAV (0x439c84,
# 0x439fda) con el archivo de mentira (un dict).
# Parte 2, generación: po_gen (desde 0x4a1961) con un mapa de juguete y el dado en Python; po_start (desde 0x42ddc1).
# Parte 3, caer: po_step (desde 0x49ce08) anota y po_fall (desde 0x4b6e9d) mata, con 0x46c470, el aviso y el sonido
# de mentira; vuela quien diga el diccionario (0x497010 / 0x48f9a0).
# Parte 4, descubrir: po_step (desde 0x49ce08) con el 0x4a1ce0 real (sin ruinas), que avanza el contador de pasos.
# Nombres (21/10/2026): po_gen los reparte en +5; los avisos los arman con sprintf ([0x5a9bec], de mentira).
# Parte 5, dibujo: po_draw (desde 0x459b95) con una vista y una celda de juguete; 0x4dd530, 0x4e4a90 y 0x4dd3f0 de
# mentira. Remolino de 3x3 (22/10/2026): cada casilla de agua pinta su pieza de los remolinos de ella y sus vecinas.
# Controles: la tabla de la Votación sigue igual delante; un .SAV viejo (sin VOTA, o con VOTA y sin POZO), roto o con
# otra marca carga la tabla vacía; un registro fuera del mapa no se marca en po_map; el original carga el .SAV nuevo.
import os, re, sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

DIR = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3'
STACK, RET, FRAME, OPTS = 0x1f0000, 0x100, 0x1e0000, 0x4fae68
MAPW, MAPH, MAPSH = 0x503e00, 0x503e02, 0x503e06
PO_MAX, PO_REC, PO_MAPSZ, VT_MAX = 64, 8, 0x32000 // 10, 8
SPRINTF = 0x1f8000   # dirección de mentira para [0x5a9bec]

def cargar(nombre):
    # el original se lee de C:\Warlords3 si la carpeta armada no lo tiene
    ruta = os.path.join(DIR, nombre)
    pe = pefile.PE(ruta if os.path.exists(ruta) else os.path.join(r'C:\Warlords3', nombre))
    return pe, pe.OPTIONAL_HEADER.ImageBase, bytes(pe.get_memory_mapped_image())
AV, ORIG = cargar('DarklordAV.exe'), cargar('Darklord.exe')
_, BASE, img = AV
# po_save: 'POZO' y la tabla en cero; vt_save: 'VOTA' y la suya
PO_SAVE = BASE + img.index(b'POZO' + bytes(4 + PO_MAX * PO_REC)); PO_N, PO_TAB = PO_SAVE + 4, PO_SAVE + 8
VT_N = BASE + img.index(b'VOTA' + bytes(4 + VT_MAX * 0x1c)) + 4
# po_map: lo primero que borra po_rebuild (pushad; mov edi, po_map)
k = img.index(b'\x60\xbf') ; PO_MAP = struct.unpack_from('<I', img, k + 2)[0]
while not (PO_MAP == PO_SAVE + 8 + PO_MAX * PO_REC + 4):
    k = img.index(b'\x60\xbf', k + 1); PO_MAP = struct.unpack_from('<I', img, k + 2)[0]

mal = 0
def ver(nombre, r, esperado):
    global mal
    ok = r == esperado
    mal += not ok
    print('OK ' if ok else 'MAL', nombre, '->', r)

class Juego:
    def __init__(self, exe=AV):
        pe, base, imagen = exe
        mu = self.mu = Uc(UC_ARCH_X86, UC_MODE_32)
        size = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
        mu.mem_map(base, size); mu.mem_write(base, imagen[:size])
        mu.mem_map(0, 0x1000); mu.mem_map(0x100000, 0x100000)
        self.fs, self.abiertos = {}, {}
        mu.mem_write(MAPW, struct.pack('<hh', 40, 30)); mu.mem_write(MAPSH, b'\6')   # 40 x 30, filas de 64
        self.interceptar(0x4dfd70, self.escribir, pop=8)
        self.interceptar(0x4dfd20, self.leer, pop=8)
        self.interceptar(0x4dfdc0, lambda a: self.abiertos.pop(self.mu.reg_read(UC_X86_REG_ECX), None) and 0)
        mu.mem_write(0x5a9bec, struct.pack('<I', SPRINTF)); self.interceptar(SPRINTF, self.sprintf)   # solo %s
    def cadena(self, a): return bytes(self.mu.mem_read(a, 256)).split(b'\0')[0]
    def sprintf(self, a):   # %s y %d (con ancho y precisión), hasta dos argumentos
        f = self.cadena(a[1]).decode('latin1'); ts = re.findall(r'%[-.0-9]*([sd])', f)
        t = (f % tuple(self.cadena(v).decode('latin1') if c == 's' else v for c, v in zip(ts, a[2:]))).encode('latin1')
        self.mu.mem_write(a[0], t + b'\0'); return len(t)
    def ciudades(self, cs):   # (x, y, nombre)
        self.mu.mem_write(0x537e2a, struct.pack('<h', len(cs)))
        for i, (x, y, n) in enumerate(cs): self.mu.mem_write(0x537e2c + i * 0xde, struct.pack('<hh', x, y) + n.encode() + b'\0')
    def interceptar(self, addr, fn, pop=0):
        def g(mu, a, size, _):
            sp = mu.reg_read(UC_X86_REG_ESP)
            ret, *args = struct.unpack('<5I', mu.mem_read(sp, 20))
            mu.reg_write(UC_X86_REG_EAX, (fn(args) or 0) & 0xffffffff)
            mu.reg_write(UC_X86_REG_ESP, sp + 4 + pop); mu.reg_write(UC_X86_REG_EIP, ret)
        self.mu.hook_add(UC_HOOK_CODE, g, begin=addr, end=addr)
    def escribir(self, a):
        f = self.abiertos[self.mu.reg_read(UC_X86_REG_ECX)]; d = self.fs[f[0]]
        d[f[1]:f[1] + a[1]] = bytes(self.mu.mem_read(a[0], a[1])); f[1] += a[1]; return a[1]
    def leer(self, a):
        f = self.abiertos[self.mu.reg_read(UC_X86_REG_ECX)]; d = self.fs[f[0]]
        b = bytes(d[f[1]:f[1] + a[1]]); self.mu.mem_write(a[0], b); f[1] += len(b); return len(b)
    def correr(self, start, stop, regs=()):
        mu = self.mu
        mu.mem_write(STACK, struct.pack('<I', RET)); mu.reg_write(UC_X86_REG_ESP, STACK)
        for r, v in regs: mu.reg_write(r, v)
        mu.emu_start(start, stop, count=2000000)
        assert mu.reg_read(UC_X86_REG_EIP) == stop, hex(mu.reg_read(UC_X86_REG_EIP))
    def poner(self, regs):
        self.mu.mem_write(PO_N, struct.pack('<i', len(regs)))
        for i, r in enumerate(regs): self.mu.mem_write(PO_TAB + PO_REC * i, struct.pack('<hhBBBB', *r))
    def tabla(self):
        n = struct.unpack('<i', self.mu.mem_read(PO_N, 4))[0]
        return [struct.unpack('<hhBBBB', self.mu.mem_read(PO_TAB + PO_REC * i, PO_REC)) for i in range(n)]
    def mapa(self):
        m = bytes(self.mu.mem_read(PO_MAP, PO_MAPSZ))
        return {(i & 63, i >> 6): v for i, v in enumerate(m) if v}

OPC = bytes(range(0x18))
def guardar(g):
    g.fs[b'P.SAV'] = bytearray(b'PRINCIPIO'); g.abiertos[FRAME - 0x12c] = [b'P.SAV', 9]
    g.mu.mem_write(FRAME - 0x12c + 0x108, struct.pack('<I', 1)); g.mu.mem_write(OPTS, OPC)
    g.correr(0x439c72, 0x439c8f, regs=[(UC_X86_REG_EBP, FRAME)])
    return bytes(g.fs[b'P.SAV'])
def cargar_sav(g, datos, basura=True):
    g.fs[b'P.SAV'] = bytearray(datos); g.abiertos[FRAME - 0x120] = [b'P.SAV', 9]
    g.mu.mem_write(FRAME - 0x120 + 0x108, struct.pack('<I', 1)); g.mu.mem_write(OPTS, bytes(0x18))
    if basura:                                           # lo de una partida anterior: tiene que quedar lo del archivo
        g.poner([(1, 1, 0, 0, 0, 0xff)] * 3); g.mu.mem_write(PO_MAP + 65, b'\3')
    g.correr(0x439fda, 0x43a010, regs=[(UC_X86_REG_EBP, FRAME)])
    return g.tabla(), g.mapa(), bytes(g.mu.mem_read(OPTS, 0x18)) == OPC

print('-- guardar y cargar')
REGS = [(5, 7, 0, 0, 0x01, 0xff), (39, 29, 1, 0, 0x05, 0xff), (0, 0, 2, 1, 0xff, 3)]
g = Juego(); g.poner(REGS); g.mu.mem_write(VT_N, struct.pack('<i', 1))
sav = guardar(g)
VT_FIN = 0x21 + 8 + VT_MAX * 0x1c
ver('guardado: lo del original, VOTA y después POZO, cantidad y tabla',
    (sav[:0x21] == b'PRINCIPIO' + OPC, sav[0x21:0x25], struct.unpack_from('<i', sav, 0x25)[0], sav[VT_FIN:VT_FIN + 4],
     struct.unpack_from('<i', sav, VT_FIN + 4)[0], len(sav) - VT_FIN - 8),
    (True, b'VOTA', 1, b'POZO', 3, PO_MAX * PO_REC))
ver('  el original no escribe nada más', len(guardar(Juego(ORIG))), 0x21)
MAPA = {(5, 7): 1, (39, 29): 2, (0, 0): 3}
ver('cargado: la tabla vuelve y po_map se rearma', cargar_sav(Juego(), sav), (REGS, MAPA, True))
ver('  la Votación también', (lambda g: (cargar_sav(g, sav), struct.unpack('<i', g.mu.mem_read(VT_N, 4))[0])[1])(Juego()), 1)
ver('control: .SAV viejo (sin VOTA): vacía', cargar_sav(Juego(), sav[:0x21]), ([], {}, True))
ver('control: .SAV con VOTA y sin POZO: vacía', cargar_sav(Juego(), sav[:VT_FIN]), ([], {}, True))
ver('control: otra marca: vacía', cargar_sav(Juego(), sav[:VT_FIN] + b'XOZO' + sav[VT_FIN + 4:]), ([], {}, True))
ver('control: tabla cortada: vacía', cargar_sav(Juego(), sav[:-1]), ([], {}, True))
ver('control: cantidad mayor que el tope: vacía',
    cargar_sav(Juego(), sav[:VT_FIN + 4] + struct.pack('<i', PO_MAX + 1) + sav[VT_FIN + 8:]), ([], {}, True))
ver('control: VOTA cortada: tampoco lee POZO', cargar_sav(Juego(), sav[:0x30] + sav[VT_FIN:])[:2], ([], {}))
FUERA = [(40, 0, 0, 0, 0, 0xff), (0, 30, 0, 0, 0, 0xff), (-1, 2, 0, 0, 0, 0xff), (3, 4, 1, 0, 0, 0xff)]
g = Juego(); g.poner(FUERA)
ver('control: fuera del mapa no se marca (sí el de dentro)', cargar_sav(Juego(), guardar(g))[:2], (FUERA, {(3, 4): 4}))
ver('control: el original carga el .SAV nuevo igual que uno viejo', (lambda g: (
    g.fs.__setitem__(b'P.SAV', bytearray(sav)), g.abiertos.__setitem__(FRAME - 0x120, [b'P.SAV', 9]),
    g.mu.mem_write(FRAME - 0x120 + 0x108, struct.pack('<I', 1)),
    g.correr(0x439fda, 0x43a010, regs=[(UC_X86_REG_EBP, FRAME)]),
    bytes(g.mu.mem_read(OPTS, 0x18)) == OPC)[-1])(Juego(ORIG)), True)
print('-- parte 2: generación y descubrir al empezar')
import random
PO_GEN = 0x4a1961 + 5 + struct.unpack_from('<i', img, 0x4a1961 - BASE + 1)[0]
PO_START = 0x42ddc1 + 5 + struct.unpack_from('<i', img, 0x42ddc1 - BASE + 1)[0]
TIERRA, AGUA, MONTE = 0, 1, 2      # tipos de terreno -> clase 2, 1 y 4
CAP = (5, 5)
def casilla(x, y): return 0x503e58 + ((y * 10) << 6) + x * 10
def armar(g, agua=True, hidden=True, ruinas=10):
    mu = g.mu
    for t, c in ((TIERRA, 2), (AGUA, 1), (MONTE, 4)): mu.mem_write(0x535f0c + t * 0x58, struct.pack('<h', c))
    for y in range(30):
        for x in range(40):
            t, reg = (AGUA, 2) if agua and x >= 30 else (TIERRA, 1)
            if y == 0: t = MONTE
            w2 = reg
            if x == 10: w2 |= 0x100                     # camino
            if (x, y) == (12, 12): w2 |= 0x300          # ciudad
            w0 = t | (0x4000 if (x, y) == (14, 14) else 0)
            if (x, y) == (35, 15): w2 |= 0x100           # puente: estructura 1 ([+3] & 7)
            mu.mem_write(casilla(x, y), struct.pack('<HH', w0, w2))
    mu.mem_write(0x536b30, b'\1\1'); mu.mem_write(0x536c22, struct.pack('<h', 0))
    mu.mem_write(0x536b30 + 0x1f8, b'\0\0')               # el jugador 1 no juega
    mu.mem_write(0x537e2a, struct.pack('<h', 1)); mu.mem_write(0x537e2c, struct.pack('<hh', *CAP))
    mu.mem_write(0x558872, struct.pack('<h', ruinas)); mu.mem_write(0x53c393, b'\x10' if hidden else b'\0')
def generar(g, seed=1, **k):
    armar(g, **k); g.poner([(1, 1, 0, 0, 0, 0xff)] * 5)   # lo de una partida anterior
    r = random.Random(seed)
    g.interceptar(0x4deb20, lambda a: sum(r.randint(1, a[1]) for _ in range(a[0])) + struct.unpack('<h', struct.pack('<H', a[2] & 0xffff))[0])
    fin = 0x4a103c if k.get('ruinas', 10) == 0 else 0x4a1971
    g.mu.reg_write(UC_X86_REG_ESP, STACK); g.mu.emu_start(PO_GEN, fin, count=5000000)
    assert g.mu.reg_read(UC_X86_REG_EIP) == fin
    return g.tabla()
def valido(r):
    x, y, t = r[:3]
    if not (0 <= x < 40 and 0 <= y < 30) or y == 0 or x == 10 or (x, y) in ((12, 12), (14, 14), (35, 15)): return False
    if t == 1: return x >= 30
    return x < 30 and max(abs(x - CAP[0]), abs(y - CAP[1])) > 2
def resumen(t): return (sum(r[2] == 0 for r in t), sum(r[2] == 1 for r in t))
ver('sin Hidden Ruins: tabla vacía (se borra la anterior)', generar(Juego(), hidden=False), [])
malos = []
for s in range(40):
    g = Juego(); t = generar(g, seed=s)
    if (resumen(t) != (2, 4) or len({r[:2] for r in t}) != 6 or not all(map(valido, t)) or
            any(r[4:] != (0, 0xff) for r in t) or g.mapa() != {r[:2]: i + 1 for i, r in enumerate(t)} or
            any([r[3] for r in t if r[2] == k] != [(t0 + i) % n for i in range(len([r for r in t if r[2] == k]))]
                for k, n in ((0, 16), (1, 32)) for t0 in [next(r[3] for r in t if r[2] == k)])):
        malos.append((s, t))
ver('10 ruinas, 40 semillas: 2 pozos y 4 remolinos (el doble) en casillas válidas, distintas y en po_map', malos, [])
ver('0 ruinas: 1 pozo, 2 remolinos y sigue en 0x4a103c', resumen(generar(Juego(), ruinas=0)), (1, 2))
t = generar(Juego(), ruinas=1000)
ver('1000 ruinas: tope de 16 pozos y 32 remolinos', resumen(t), (16, 32))
ver('  con los 16 y los 32 nombres, sin repetir', [sorted(r[3] for r in t if r[2] == k) for k in (0, 1)],
    [list(range(16)), list(range(32))])
ver('nombres: el comienzo cambia con la partida', len({generar(Juego(), seed=s)[0][3] for s in range(20)}) > 4, True)
ver('control: mapa sin agua: solo pozos', resumen(generar(Juego(), agua=False)), (2, 0))
def empezar(g):
    g.mu.mem_write(STACK, struct.pack('<I', RET)); g.mu.reg_write(UC_X86_REG_ESP, STACK)
    g.mu.emu_start(PO_START, 0x4a1e20, count=1000000)
    return [r[4] for r in g.tabla()]
g = Juego(); generar(g)
ver('al empezar: el jugador 0 descubre los pozos de la región de su capital, no los remolinos', empezar(g), [1, 1, 0, 0, 0, 0])
g = Juego(); generar(g); g.mu.mem_write(0x53c393, b'\0')
ver('control: sin Hidden Ruins no descubre nada', empezar(g), [0] * 6)
print('-- parte 3: caer')
PO_STEP = 0x49ce08 + 5 + struct.unpack_from('<i', img, 0x49ce08 - BASE + 1)[0]
PO_FALL = 0x4b6e9d + 5 + struct.unpack_from('<i', img, 0x4b6e9d - BASE + 1)[0]
def caer(regs, ejs, pasos, mira=2, snd=0x20, cs=()):
    # ejs: (x, y, dueño, héroe, vuela); pasos: (jugador, x, y). Devuelve muertos (ejército, arg), avisos, sonidos,
    # la tabla y lo que quedó anotado.
    g = Juego(); mu = g.mu; g.poner(regs); g.ciudades(cs)
    for i, r in enumerate(regs): mu.mem_write(PO_MAP + (r[1] << 6) + r[0], bytes([i + 1]))
    mu.mem_write(0x54fe50, struct.pack('<h', len(ejs) + 1))
    vuela = {}
    for i, (x, y, d, h, v) in enumerate(ejs, 1):
        a = 0x54fe50 + i * 0x1c
        mu.mem_write(a + 2, struct.pack('<hh', x, y)); mu.mem_write(a + 0xe, struct.pack('<H', (0x10 if h else 3) | d << 5))
        mu.mem_write(a + 0x13, b'@'); vuela[i] = v
    mu.mem_write(0x560b20, struct.pack('<h', mira))
    muertos, avisos, sonidos = [], [], []
    def matar(a):
        muertos.append((a[0] & 0xffff, a[1] & 0xff)); b = 0x54fe50 + (a[0] & 0xffff) * 0x1c + 0x13
        mu.mem_write(b, bytes([mu.mem_read(b, 1)[0] & ~0x40]))
    g.interceptar(0x46c470, matar)
    g.interceptar(0x497010, lambda a: vuela[a[0] & 0xffff]); g.interceptar(0x48f9a0, lambda a: vuela[a[0] & 0xffff])
    g.interceptar(0x4c2790, lambda a: avisos.append(bytes(mu.mem_read(a[0], 64)).split(b'\0')[0].decode()))
    g.interceptar(0x4465e0, lambda a: sonidos.append((a[0] & 0xffff, a[1] & 0xffff)))
    # sonido suelto (Burst en la trampa): 0x4eca00(id) da el buffer, 0x4e6fd0 lo toca
    mu.mem_write(0x564d08, bytes([snd]))
    g.interceptar(0x4eca00, lambda a: 0x1f7000 + a[0], pop=4)
    g.interceptar(0x4e6fd0, lambda a: sonidos.append((('fx', mu.reg_read(UC_X86_REG_ECX) - 0x1f7000), 0)), pop=8)
    for f in (0x441290, 0x4a2170): g.interceptar(f, lambda a: 0)
    for j, x, y in pasos:
        mu.mem_write(STACK, struct.pack('<5I', RET, j, x & 0xffff, y & 0xffff, 1)); mu.reg_write(UC_X86_REG_ESP, STACK)
        mu.emu_start(PO_STEP, 0x4a1ce0, count=100000); assert mu.reg_read(UC_X86_REG_EIP) == 0x4a1ce0
    mu.mem_write(STACK, struct.pack('<I', RET)); mu.reg_write(UC_X86_REG_ESP, STACK)
    mu.emu_start(PO_FALL, 0x49d1a0, count=1000000); assert mu.reg_read(UC_X86_REG_EIP) == 0x49d1a0
    assert mu.reg_read(UC_X86_REG_ESP) == STACK
    return muertos, avisos, [s[0] for s in sonidos], g.tabla()
POZOS = [(10, 10, 0, 0, 0, 0xff), (20, 10, 1, 0, 0, 0xff), (15, 15, 2, 0, 0, 3), (16, 16, 2, 1, 0xff, 3)]
GRUPO = [(10, 10, 2, 0, 0), (10, 10, 2, 1, 0), (10, 10, 2, 0, 0)]
r = caer(POZOS, GRUPO + [(10, 10, 3, 0, 0), (11, 10, 2, 0, 0)], [(2, 10, 10)])
ver('pozo: mueren los 3 del grupo (héroe incluido), con 0; otro bando y otra casilla quedan', r[0], [(1, 0), (2, 0), (3, 0)])
ver('pozo: aviso y sonido 7 en la PC del que cayó; descubierto para él', (r[1], r[2], r[3][0][4]),
    (['Your army fell into the Well of Souls!'], [7], 0x04))
ver('nombre: +5 = 3 del pozo y 31 del remolino', [caer([(10, 10, 0, 3, 0, 0xff)], GRUPO, [(2, 10, 10)])[1],
    caer([(20, 10, 1, 31, 0, 0xff)], [(20, 10, 2, 0, 0)], [(2, 20, 10)])[1]],
    [['Your army fell into the Chasm of Woe!'], ["Your army was swallowed by the Sea Wolf's Den!"]])
ver('control: +5 fuera de la lista no se sale de ella', caer([(10, 10, 0, 0x13, 0, 0xff)], GRUPO, [(2, 10, 10)])[1],
    ['Your army fell into the Chasm of Woe!'])
r = caer(POZOS, GRUPO, [(2, 10, 10)], mira=1)
ver('control: en otra PC mueren igual, sin aviso ni sonido', (r[0], r[1], r[2]), ([(1, 0), (2, 0), (3, 0)], [], []))
r = caer(POZOS, [(10, 10, 2, 0, 1), (10, 10, 2, 0, 0)], [(2, 10, 10)])
ver('pozo con volador: el volador sigue', r[0], [(2, 0)])
r = caer(POZOS, [(10, 10, 2, 0, 1), (10, 10, 2, 1, 1)], [(2, 10, 10)])
ver('solo voladores: nadie cae, no se descubre, sin aviso', (r[0], r[1], r[3][0][4]), ([], [], 0))
r = caer(POZOS, [(20, 10, 2, 0, 0), (20, 10, 2, 0, 0), (20, 10, 2, 0, 1)], [(2, 20, 10)])
ver('remolino: se hunde todo lo que no vuela, con 1 (como el disband)', (r[0], r[1]),
    ([(1, 1), (2, 1)], ['Your army was swallowed by the Maelstrom of Kor!']))
r = caer(POZOS, [(15, 15, 3, 0, 0)], [(3, 15, 15)], mira=3)
ver('trampa: cae hasta el dueño; lleva 1 explosión, recién explotada por el 3, y la ve solo quien cayó',
    (r[0], r[1], r[3][2][3:]), ([(1, 0)], ['Your army fell into a trap!'], (0x80 | 3 << 4 | 1, 0x08, 3)))
ver('trampa: suena Burst (sonido 56) y el grito', r[2], [('fx', 56), 7])
ver('control: sin la opción de sonido, sin Burst', caer(POZOS, [(15, 15, 3, 0, 0)], [(3, 15, 15)], mira=3, snd=0)[2], [7])
ver('control: en otra PC, la trampa no suena', caer(POZOS, [(15, 15, 3, 0, 0)], [(3, 15, 15)], mira=1)[2], [])
for k in (1, 2):
    t = POZOS[:2] + [(15, 15, 2, k, 0, 3)] + POZOS[3:]
    r = caer(t, [(15, 15, 2, 0, 0)], [(2, 15, 15)])
    ver(f'trampa con {k} explosión(es): mata otra vez y suma una', (r[0], r[3][2][3:5]), ([(1, 0)], (0xa0 | k + 1, 0x04)))
r = caer(POZOS[:2] + [(15, 15, 2, 0xb1, 0x08, 3)] + POZOS[3:], [(15, 15, 2, 0, 0)], [(2, 15, 15)])
ver('recién explotada por otro (bits 4-7): mata igual y queda a nombre del último', (r[0], r[3][2][3:5]), ([(1, 0)], (0xa2, 0x0c)))
r = caer(POZOS, [(16, 16, 2, 0, 0)], [(2, 16, 16)])
ver('SAV viejo: trampa detonada (+5 = 1) mata de nuevo, le quedan 2 usos', (r[0], r[1]), ([(1, 0)], ['Your army fell into a trap!']))
for e in (3, 0xa3):
    r = caer(POZOS[:3] + [(16, 16, 2, e, 0xff, 3)], [(16, 16, 2, 0, 0)], [(2, 16, 16)])
    ver(f'control: trampa gastada (+5 = {e:#x}) ya no mata', (r[0], r[1]), ([], []))
print('-- trampa: tr_turn al empezar el turno')
k = 0x4223ad + 5 + struct.unpack_from('<i', img, 0x4223ad - BASE + 1)[0] - BASE
k = img.index(bytes([0xe8]), k + 9); TR_TURN = k + BASE + 5 + struct.unpack_from('<i', img, k + 1)[0]
def turno(regs, p):
    g = Juego(); mu = g.mu; g.poner(regs)
    mu.mem_write(STACK, struct.pack('<I', RET)); mu.reg_write(UC_X86_REG_ESP, STACK); mu.reg_write(UC_X86_REG_EBX, p)
    mu.emu_start(TR_TURN, RET, count=100000); assert mu.reg_read(UC_X86_REG_EBX) == p
    return [r[3] for r in g.tabla()]
T = [(1, 1, 2, 0xb1, 8, 0), (2, 1, 2, 0xa2, 4, 0), (3, 1, 2, 0xb3, 8, 0), (4, 1, 0, 0xb1, 8, 0), (5, 1, 3, 0xb1, 8, 0)]
ver('empieza el 3: sus trampas dejan de estar recién explotadas; las del 2, pozo y tumba igual', turno(T, 3),
    [1, 0xa2, 3, 0xb1, 0xb1])
ver('empieza el 2', turno(T, 2), [0xb1, 2, 0xb3, 0xb1, 0xb1])
r = caer(POZOS, GRUPO, [(2, 11, 10), (2, -1, 10), (2, 40, 10), (9, 10, 10)])
ver('control: casilla sin pozo, fuera del mapa o jugador inválido: nada', r[0], [])
r = caer(POZOS, GRUPO + [(20, 10, 4, 0, 0)], [(2, 10, 10), (4, 20, 10)])
ver('dos jugadores en el mismo lote: cada uno en lo suyo', r[0], [(1, 0), (2, 0), (3, 0), (4, 1)])
print('-- nombres de trampas')
CS = [(5, 5, 'Afland'), (30, 20, 'Belgor'), (14, 14, 'Corvin'), (0, 0, 'Xenomorphic Stronghold of Doom')]
TR = [(15, 15, 2, 0, 0, 3), (40, 40, 2, 1, 0xff, 3), (13, 13, 2, 0, 0, 1), (16, 13, 2, 0, 0, 3), (28, 22, 2, 0, 0, 5)]
def trampa(i, cs=CS): return caer(TR, [(TR[i][0], TR[i][1], 3, 0, 0)], [(3, TR[i][0], TR[i][1])], mira=3, cs=cs)[1]
ver('caer: ciudad más cercana y número correlativo por ciudad (la de 40,40 es de Belgor: no cuenta para Corvin)',
    [trampa(i) for i in (0, 2, 3, 4)], [['Your army fell into the trap Corvin01!'], ['Your army fell into the trap Corvin02!'],
                                        ['Your army fell into the trap Corvin03!'], ['Your army fell into the trap Belgor02!']])
ver('empate de distancia: la primera ciudad', trampa(0, [(13, 15, 'Afland'), (17, 15, 'Belgor')]), ['Your army fell into the trap Afland01!'])
ver('nombre largo: a 20 letras', trampa(0, [(15, 16, 'Xenomorphic Stronghold of Doom')]), ['Your army fell into the trap Xenomorphic Strongho01!'])
ver('control: sin ciudades, el aviso de antes', trampa(0, []), ['Your army fell into a trap!'])
print('-- tumbas al caer en un pozo')
def tumbas(t, n=len(POZOS)): return [r for r in t[n:] if r[2] == 3]
r = caer(POZOS, GRUPO, [(2, 10, 10)])
tb = tumbas(r[3])
ver('pozo: una tumba a 2 o menos, no en el pozo, imagen 0..2, vista por todos; el resto de la tabla igual',
    (len(tb), all(max(abs(x - 10), abs(y - 10)) <= 2 and (x, y) != (10, 10) and k <= 2 and (m, d) == (0xff, 0xff)
                  for x, y, _, k, m, d in tb), r[3][1:len(POZOS)] == POZOS[1:], len(r[3])), (1, True, True, 5))
ver('control: la misma caída da la misma tumba (en todas las PC igual)', tumbas(caer(POZOS, GRUPO, [(2, 10, 10)], mira=1)[3]), tb)
ver('control: la tumba no mata ni se anota al pisarla', caer(POZOS + tb, [(tb[0][0], tb[0][1], 2, 0, 0)],
    [(2, tb[0][0], tb[0][1])])[:2], ([], []))
t2 = tumbas(caer(POZOS + tb, GRUPO, [(2, 10, 10)])[3], len(POZOS) + 1)
ver('segunda caída: otra tumba, en otra casilla', (len(t2), t2[0][:2] != tb[0][:2], max(abs(t2[0][0] - 10), abs(t2[0][1] - 10)) <= 2), (1, True, True))
t = POZOS
for i in range(30):
    t = caer(t, GRUPO, [(2, 10, 10)])[3]
n = len(tumbas(t))
ver('30 caídas: entre 16 y 24 tumbas (las 24 casillas alrededor; con pocas libres, 32 tiros pueden no acertar), distintas',
    (16 <= n <= 24, len({r[:2] for r in tumbas(t)}) == n), (True, True))
ver('las tres imágenes salen', sorted({r[3] for r in tumbas(t)}), [0, 1, 2])
ver('control: remolino y trampa no dejan tumba', [len(tumbas(caer(POZOS, [(x, y, 3, 0, 0)], [(3, x, y)])[3])) for x, y in ((20, 10), (15, 15))], [0, 0])
ver('control: solo voladores (nadie muere): sin tumba', len(tumbas(caer(POZOS, [(10, 10, 2, 0, 1)], [(2, 10, 10)])[3])), 0)
lleno = POZOS + [(1, 1 + i // 30, 3, 0, 0xff, 0xff) for i in range(PO_MAX - len(POZOS))]
r = caer(lleno, GRUPO, [(2, 10, 10)])
ver('control: tabla llena: caen igual, sin tumba', (len(r[0]), len(r[3])), (3, PO_MAX))
print('-- parte 4: descubrir')
def descubrir(regs, pasos, cont=9, opc=0x30, mira=2, grupo=(0,), cs=()):
    # pasos: (jugador, x, y, radio del grupo, que ya no cuenta). grupo: si vuela cada ejército del grupo en movimiento.
    # Devuelve las máscaras, los avisos y el contador al final.
    g = Juego(); mu = g.mu; g.poner(regs); g.ciudades(cs)
    for j in range(8):
        mu.mem_write(0x56ea94 + j * 0x4f0, struct.pack(f'<{len(grupo)}h', *range(1, len(grupo) + 1)))
        mu.mem_write(0x56eaa8 + j * 0x4f0, struct.pack('<h', len(grupo)))
    for i in range(1, len(grupo) + 1): mu.mem_write(0x54fe50 + i * 0x1c + 0xe, struct.pack('<H', 3))
    g.interceptar(0x497010, lambda a: grupo[(a[0] & 0xffff) - 1]); g.interceptar(0x48f9a0, lambda a: grupo[(a[0] & 0xffff) - 1])
    mu.mem_write(0x558872, struct.pack('<h', 0)); mu.mem_write(0x53c393, bytes([opc]))
    mu.mem_write(0x4fe5e8, struct.pack('<h', cont)); mu.mem_write(0x560b20, struct.pack('<h', mira))
    avisos = []
    g.interceptar(0x4c2790, lambda a: avisos.append(bytes(mu.mem_read(a[0], 64)).split(b'\0')[0].decode()))
    g.interceptar(REDRAW_, lambda a: 0)
    for j, x, y, rad in pasos:
        mu.mem_write(STACK, struct.pack('<5I', RET, j, x & 0xffff, y & 0xffff, rad)); mu.reg_write(UC_X86_REG_ESP, STACK)
        mu.emu_start(PO_STEP, RET, count=100000); assert mu.reg_read(UC_X86_REG_EIP) == RET
        assert mu.reg_read(UC_X86_REG_ESP) == STACK + 4
    return [r[4] for r in g.tabla()], avisos, struct.unpack('<h', mu.mem_read(0x4fe5e8, 2))[0]
REDRAW_ = 0x4a2170
LEJOS = [(30, 20, 0, 0, 0, 0xff), (10, 11, 0, 0, 0, 0xff), (11, 11, 1, 0, 0, 0xff), (10, 13, 2, 0, 0, 3)]
ver('contador 9 -> 0 < radio 1: descubre el pozo a 1 (solo el primero), aviso en su PC',
    descubrir(LEJOS, [(2, 10, 10, 1)]), ([0, 4, 0, 0], ['You have discovered the Well of Souls!'], 0))
ver('control: contador 0 -> 1, no < radio 1: nada', descubrir(LEJOS, [(2, 10, 10, 1)], cont=0)[:2], ([0, 0, 0, 0], []))
ver('el primero no visto a 1; ya visto se saltea',
    descubrir([(10, 11, 0, 0, 4, 0xff)] + LEJOS[2:], [(2, 11, 10, 1)])[:2],
    ([4, 4, 0], ['You have discovered the Maelstrom of Kor!']))
ver('trampa a 1: aviso de trampa', descubrir(LEJOS[3:], [(2, 10, 12, 1)])[:2], ([4], ['You have discovered a hidden trap!']))
ver('trampa a 1, con ciudades: aviso con su nombre', descubrir(TR[2:3], [(2, 13, 12, 1)], cs=CS)[:2],
    ([4], ['You have discovered the trap Corvin01!']))
ver('control: a 2 no, aunque el grupo tenga radio 7', descubrir(LEJOS[3:], [(2, 10, 11, 7)])[:2], ([0], []))
ver('control: radio del grupo 3 y contador -> 1: nada (cuenta 1, no el radio)', descubrir(LEJOS, [(2, 10, 10, 3)], cont=0)[:2], ([0] * 4, []))
ver('contador 4 -> 5: descubre (1 de cada 5 pasos)', descubrir(LEJOS, [(2, 10, 10, 1)], cont=4)[0], [0, 4, 0, 0])
ver('control: contador 5 -> 6 y 3 -> 4: nada', [descubrir(LEJOS, [(2, 10, 10, 1)], cont=c)[0] for c in (5, 3)], [[0] * 4] * 2)
ver('grupo de voladores: no descubre', descubrir(LEJOS, [(2, 10, 10, 1)], grupo=(1, 1))[:2], ([0] * 4, []))
ver('grupo con un volador y uno de a pie: descubre', descubrir(LEJOS, [(2, 10, 10, 1)], grupo=(1, 0))[0], [0, 4, 0, 0])
ver('control: grupo vacío: nada', descubrir(LEJOS, [(2, 10, 10, 1)], grupo=())[:2], ([0] * 4, []))
ver('control: otra PC descubre igual, sin aviso', descubrir(LEJOS, [(2, 10, 10, 1)], mira=1)[:2], ([0, 4, 0, 0], []))
ver('control: sin Discover Ruins nada (el contador avanza igual)', descubrir(LEJOS, [(2, 10, 10, 1)], opc=0x10), ([0] * 4, [], 0))
ver('control: sin Hidden Ruins nada', descubrir(LEJOS, [(2, 10, 10, 1)], opc=0x20)[:2], ([0] * 4, []))
ver('control: jugador inválido nada', descubrir(LEJOS, [(9, 10, 10, 1)])[:2], ([0] * 4, []))
ver('10 pasos con radio 1: el contador da una vuelta (un 0x4a1ce0 por paso), descubre una vez (el primero sirve)',
    descubrir(LEJOS[1:2], [(2, 10, 10, 1)] * 10), ([4], ['You have discovered the Well of Souls!'], 9))
print('-- parte 5: dibujo')
PO_DRAW = 0x459b95 + 5 + struct.unpack_from('<i', img, 0x459b95 - BASE + 1)[0]
VISTA, CELDA, HOJA = 0x180000, 0x181000, 0x182000
PO_FILE = 168
def dibujar(regs, celda=(3, 2), origen=(10, 20), mira=2, fase=0, aliados=(), vista=True, cargada=True, hay=True,
            sitio=0, agua=(), puente=()):
    # Una celda de la vista: columna/fila celda, origen de la vista, quien mira. Devuelve los dibujos de 0x4dd530
    # (hoja, x, y, ancho, alto, destino, x, y en pantalla), las cargas de la hoja y por dónde siguió.
    g = Juego(); mu = g.mu; g.poner(regs)
    mu.mem_write(0x535f0c + AGUA * 0x58, struct.pack('<h', 1))
    for x, y in agua: mu.mem_write(casilla(x, y), struct.pack('<HH', AGUA, 0x100 if (x, y) in puente else 0))
    for i, r in enumerate(regs): mu.mem_write(PO_MAP + (r[1] << 6) + r[0], bytes([i + 1]))
    mu.mem_write(VISTA + 0x28, struct.pack('<hh', *origen)); mu.mem_write(VISTA + 0x3c, struct.pack('<h', fase))
    mu.mem_write(CELDA + 0x10, bytes([sitio])); mu.mem_write(0x560b20, struct.pack('<h', mira))
    mu.mem_write(0x55ee4c, b'\2' * 56 * 8)
    for a, b in aliados: mu.mem_write(0x55ee4c + a * 56 + b, b'\0'); mu.mem_write(0x55ee4c + b * 56 + a, b'\0')
    mu.mem_write(0x53c38e, b'\x90' if vista else b'\x10'); mu.mem_write(0x53c393, b'\x08')
    mu.mem_write(HOJA + 8, struct.pack('<I', 1 if cargada else 0))
    dibujos, cargas = [], []
    g.interceptar(0x4e4a90, lambda a: HOJA if hay and a[0] == PO_FILE else 0, pop=4)
    def cargar(a):
        cargas.append(a[0]); mu.mem_write(HOJA + 8, struct.pack('<I', 1)); return 1
    g.interceptar(0x4dd3f0, cargar)
    def blit(a):
        sp = mu.reg_read(UC_X86_REG_ESP)
        dibujos.append(struct.unpack('<8i', mu.mem_read(sp + 4, 32)))
    g.interceptar(0x4dd530, blit)
    sp = STACK - 0x40
    mu.mem_write(sp + 0x14, struct.pack('<hhhh', celda[0], celda[1], celda[0] * 48, celda[1] * 48))
    mu.reg_write(UC_X86_REG_ESP, sp); mu.reg_write(UC_X86_REG_EBP, VISTA); mu.reg_write(UC_X86_REG_ESI, CELDA)
    sigue = None
    for fin in (0x459b9b, 0x459bb9):
        mu.hook_add(UC_HOOK_CODE, lambda mu, a, s, _, f=fin: mu.emu_stop(), begin=fin, end=fin)
    mu.emu_start(PO_DRAW, 0, count=100000)
    sigue = mu.reg_read(UC_X86_REG_EIP)
    assert mu.reg_read(UC_X86_REG_ESP) == sp and mu.reg_read(UC_X86_REG_EBP) == VISTA
    assert mu.reg_read(UC_X86_REG_ESI) == CELDA
    return [(d[1] // 48,) + d[2:] for d in dibujos if d[0] == PO_FILE], cargas, hex(sigue)
EN = (13, 22)       # la casilla de la celda (3, 2) con origen (10, 20); en pantalla (144, 96)
def en(t, est=0, m=0, d=0xff): return [EN + (t, est, m, d)]
ver('pozo visto por quien mira: cuadro 0, 48x48 en la celda, al destino 0x27; sin sitio salta al fin de la celda',
    dibujar(en(0, m=0x04)), ([(0, 0, 48, 48, 0x27, 144, 96)], [], '0x459bb9'))
ver('control: con sitio en la celda sigue a dibujarlo', dibujar(en(0, m=0x04), sitio=1)[2], '0x459b9b')
ver('control: pozo no descubierto por quien mira: nada', dibujar(en(0, m=0x08))[0], [])
ver('control: otra casilla: nada', dibujar(en(0, m=0x04), celda=(4, 2))[0], [])
MAR = [(x, y) for x in range(8, 20) for y in range(17, 28)]
R0 = 13             # PO_REMO0: remolino, 4 fases x 9 piezas
ver('remolino en el agua: pieza del medio, R0 + fase * 9 + 4', [dibujar(en(1, m=0x04), fase=f, agua=MAR)[0] for f in range(6)],
    [[(R0 + (f & 3) * 9 + 4, 0, 48, 48, 0x27, 144, 96)] for f in range(6)])
ver('vecinas de agua: cada una su pieza (dy + 1) * 3 + (dx + 1)',
    [dibujar(en(1, m=0x04), celda=(3 + dx, 2 + dy), fase=1, agua=MAR)[0][0][:1] for dy in (-1, 0, 1) for dx in (-1, 0, 1)],
    [(R0 + 9 + k,) for k in range(9)])
ver('control: a dos casillas, nada', [dibujar(en(1, m=0x04), celda=c, agua=MAR)[0] for c in ((5, 2), (3, 4), (1, 0))], [[]] * 3)
ver('control: vecina en tierra, nada', dibujar(en(1, m=0x04), celda=(4, 2), agua=[EN])[0], [])
ver('control: vecina con puente, nada', dibujar(en(1, m=0x04), celda=(4, 2), agua=MAR, puente=[(14, 22)])[0], [])
ver('control: remolino no descubierto por quien mira, ni en su casilla ni en las vecinas',
    [dibujar(en(1, m=0x08), celda=c, agua=MAR)[0] for c in ((3, 2), (4, 3))], [[], []])
ver('dos remolinos vecinos: la casilla del medio pinta una pieza de cada uno',
    [d[0] for d in dibujar([(12, 22, 1, 0, 4, 0xff), (14, 22, 1, 0, 4, 0xff)], agua=MAR)[0]], [R0 + 5, R0 + 3])
ver('pozo en una vecina de agua: primero la pieza del remolino, encima el pozo',
    [d[0] for d in dibujar([EN + (1, 0, 4, 0xff), (14, 22, 0, 0, 4, 0xff)], celda=(4, 2), agua=MAR)[0]], [R0 + 5, 0])
ver('remolino en el borde del mapa: las vecinas de afuera no cuentan',
    [d[0] for d in dibujar([(0, 0, 1, 0, 4, 0xff)], celda=(0, 0), origen=(0, 0), agua=[(0, 0)])[0]], [R0 + 4])
ver('trampa del que mira (no descubierta): cuadro 5', dibujar(en(2, d=2))[0][0][0], 5)
ver('trampa de un aliado con vista aliada: se ve', dibujar(en(2, d=3), aliados=[(2, 3)])[0][0][0], 5)
ver('control: aliado sin vista aliada: no', dibujar(en(2, d=3), aliados=[(2, 3)], vista=False)[0], [])
ver('control: trampa de otro (no aliado): no', dibujar(en(2, d=3))[0], [])
ver('trampa ajena descubierta: se ve', dibujar(en(2, m=0x04, d=3))[0][0][0], 5)
ver('trampa con 1 o 2 explosiones (turno siguiente): la mina (cuadro 5)', [dibujar(en(2, k, 0x04, 3))[0][0][0] for k in (1, 2)], [5, 5])
ver('recién explotada: agujero con humo, 6 + fase', [dibujar(en(2, 0xa1, 0x04, 3), fase=f)[0][0][0] for f in range(5)], [6, 7, 8, 9, 6])
ver('control: recién explotada, quien no la descubrió no la ve', dibujar(en(2, 0xa1, 0x08, 3))[0], [])
ver('gastada: agujero con humo para todos, aunque no la hayan descubierto',
    [dibujar(en(2, e, 0, 3), mira=m, fase=1)[0][0][0] for e, m in ((3, 2), (0xa3, 5), (3, 0))], [7, 7, 7])
ver('tumba, lápida y cruz (vistas por todos): cuadros 10, 11 y 12', [dibujar(en(3, k, 0xff), mira=m)[0][0][0] for k, m in ((0, 0), (1, 5), (2, 7))],
    [10, 11, 12])
ver('control: tumba con imagen fuera de rango: nada', dibujar(en(3, 3, 0xff))[0], [])
ver('hoja sin cargar: la carga una vez y dibuja', dibujar(en(0, m=0x04), cargada=False)[:2],
    ([(0, 0, 48, 48, 0x27, 144, 96)], [PO_FILE]))
ver('control: hoja inexistente: no dibuja ni insiste', dibujar(en(0, m=0x04), hay=False)[:2], ([], []))
ver('control: quien mira inválido: nada', dibujar(en(0, m=0xff), mira=9)[0], [])
ver('control: casilla fuera del mapa: nada', dibujar([(45, 22, 0, 0, 0xff, 0xff)], origen=(42, 20))[0], [])
print('MAL:', mal)
sys.exit(1 if mal else 0)
