# Prueba de juguete del resultado de la votación en el Events Report (vt_* de build.py) sobre el exe parcheado y el
# original, en unicorn.
# Uso: python prueba_votoinforme.py [carpeta]   (por defecto C:\Warlords3; armarla antes con build.py)
# Los estados de la Votación entran por la recepción real (0x4b6a16); el fin de ronda (0x4989d0), el informe
# (0x499450) y el renglón (0x4b4110) corren enteros con el archivo de mentira (HISTORY.DAT en un dict) y el dibujo
# interceptado; guardar y cargar, desde la última escritura y la última lectura del .SAV (0x439c84, 0x439fda).
# Controles: sin votaciones, HISTORY.DAT y el informe son idénticos byte a byte a los del Darklord.exe original; los
# sucesos comunes se dibujan igual que en el original; no se anota nada sin orden de abrir, con Sorteo, de otro
# remitente, sin votos, con el cierre de emergencia, ni un "cerrado" repetido; un .SAV viejo o roto carga la tabla vacía.
import os, re, sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

DIR = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3'
STACK, RET, STUBS, PKT, HEAP, FRAME = 0x1f0000, 0x100, 0x300000, 0x150000, 0x2000000, 0x1e0000
TABLE, NCITIES, SIDES, SPRINTF, OPTS = 0x572788, 0x537e2a, 0x536b30, 0x5a9bec, 0x4fae68
SIDE = 0x1f8   # bando i: activo en SIDES + SIDE*i, máquina en +3, humano (-1) en +0xe2
FONT_TXT = b'Recibe algo en %s\0'

def cargar(nombre):
    pe = pefile.PE(os.path.join(DIR, nombre)); base = pe.OPTIONAL_HEADER.ImageBase
    imports = {i.name.decode(): i.address for e in pe.DIRECTORY_ENTRY_IMPORT for i in e.imports if i.name}
    return pe, base, bytes(pe.get_memory_mapped_image()), imports
AV, ORIG = cargar('DarklordAV.exe'), cargar('Darklord.exe')
_, BASE, img, _ = AV
# vt_clear empieza con "mov dword ptr [VT_N], 0"; detrás de VT_N, la tabla
CLEAR = 0x4988d0 + 5 + struct.unpack_from('<i', img, 0x4988d1 - BASE)[0]
assert img[CLEAR - BASE:CLEAR - BASE + 2] == b'\xc7\x05'
VT_N = struct.unpack_from('<I', img, CLEAR + 2 - BASE)[0]; VT_TAB = VT_N + 4
VT_MAX = 8
PZ_ARM = BASE + img.index(b'Votacion en curso: partida en pausa\0') + 36 + 1

mal = 0
def ver(nombre, r, esperado):
    global mal
    ok = r == esperado
    mal += not ok
    print('OK ' if ok else 'MAL', nombre, '->', r)

def cstr(mu, a):
    s = bytes(mu.mem_read(a, 512)); return s[:s.index(b'\0')]

def printf(mu, fmt, sp):
    out, k = b'', 0
    for m in re.finditer(rb'%(-?\d*)([sdc%])|[^%]+', fmt):
        if not m.group(2): out += m.group(0); continue
        if m.group(2) == b'%': out += b'%'; continue
        v = struct.unpack('<i', mu.mem_read(sp + 4 * k, 4))[0]; k += 1
        out += cstr(mu, v & 0xffffffff) if m.group(2) == b's' else str(v).encode()
    return out

def rec(tipo, jug, param=0, nombre=b'', w=(0, 0, 0)):
    return struct.pack('<hhh16s3h', tipo, jug, param, nombre, *w)
VOTO = lambda si, no: rec(0x13, 8, 0, b'', (si, no, 0))

class Juego:
    """Una PC con el exe dado, HISTORY.DAT en un dict y el dibujo interceptado."""
    def __init__(self, exe=AV):
        pe, base, imagen, imports = exe
        self.av = exe is AV
        mu = self.mu = Uc(UC_ARCH_X86, UC_MODE_32)
        size = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
        mu.mem_map(base, size); mu.mem_write(base, imagen[:size])
        mu.mem_map(0, 0x1000)                         # fs:[0], la cadena de excepciones
        mu.mem_map(0x100000, 0x100000)
        mu.mem_map(STUBS, 0x1000)
        mu.mem_map(HEAP, 0x100000)
        self.t, self.ronda, self.fs, self.abiertos, self.dibujo, self.heap = 1000000, 1, {}, {}, [], HEAP
        stubs = {imports['GetTickCount']: (0, lambda a: self.t), imports['timeGetTime']: (0, lambda a: self.t),
                 SPRINTF: (None, self.sprintf)}
        for k, (iat, (n, fn)) in enumerate(stubs.items()):
            stub = STUBS + 0x10 * k
            mu.mem_write(iat, struct.pack('<I', stub))
            def g(mu, a, size, _, n=n, fn=fn):
                sp = mu.reg_read(UC_X86_REG_ESP)
                ret = struct.unpack('<I', mu.mem_read(sp, 4))[0]
                mu.reg_write(UC_X86_REG_EAX, fn(sp + 4) & 0xffffffff)
                mu.reg_write(UC_X86_REG_ESP, sp + 4 + 4 * (n or 0)); mu.reg_write(UC_X86_REG_EIP, ret)
            mu.hook_add(UC_HOOK_CODE, g, begin=stub, end=stub)
        mu.mem_write(SIDES, b'\1\1')                  # el bando 0 activo, para que la cabecera tenga algo
        mu.mem_write(NCITIES, struct.pack('<h', 5))
        self.interceptar(0x440840, lambda a: 0)
        self.interceptar(0x420a80, lambda a: self.ronda)
        self.interceptar(0x4dfbd0, self.abrir_arch, pop=0xc)
        self.interceptar(0x4dfd70, self.escribir, pop=8)
        self.interceptar(0x4dfd20, self.leer, pop=8)
        self.interceptar(0x4dfdf0, self.posicionar, pop=8)
        self.interceptar(0x4dfeb0, lambda a: len(self.fs[self.abiertos[self.ecx()][0]]))
        self.interceptar(0x4dfdc0, self.cerrar)
        self.interceptar(0x4deff0, self.malloc)
        self.interceptar(0x4dd0f0, lambda a: None)
        self.interceptar(0x4dd080, lambda a: self.dibujo.append(('escudo', a[0], a[1], a[2])))
        self.interceptar(0x4dd120, lambda a: self.dibujo.append(('texto', a[0], a[1], cstr(self.mu, a[2]).decode())))
        self.interceptar(0x4def30, lambda a: 0x1ff000, pop=8)
        mu.mem_write(0x1ff000, FONT_TXT)
    def ecx(self): return self.mu.reg_read(UC_X86_REG_ECX)
    def interceptar(self, addr, fn, pop=0):
        def g(mu, a, size, _):
            sp = mu.reg_read(UC_X86_REG_ESP)
            ret, *args = struct.unpack('<5I', mu.mem_read(sp, 20))
            r = fn(args)
            mu.reg_write(UC_X86_REG_EAX, (r or 0) & 0xffffffff)
            mu.reg_write(UC_X86_REG_ESP, sp + 4 + pop); mu.reg_write(UC_X86_REG_EIP, ret)
        self.mu.hook_add(UC_HOOK_CODE, g, begin=addr, end=addr)
    def sprintf(self, sp):
        dst, fmt = struct.unpack('<II', self.mu.mem_read(sp, 8))
        s = printf(self.mu, cstr(self.mu, fmt), sp + 8)
        self.mu.mem_write(dst, s + b'\0'); return len(s)
    def malloc(self, a):
        p = self.heap; self.heap += (a[0] + 15) & ~15; return p
    # archivos: objeto (ecx) -> [nombre, posición]; abierto en +0x108 como en el original
    def abrir_arch(self, a):
        nombre, modo = cstr(self.mu, a[0]), a[1]
        if modo == 2: self.fs[nombre] = bytearray()
        elif nombre not in self.fs: return 0
        self.abiertos[self.ecx()] = [nombre, 0]
        self.mu.mem_write(self.ecx() + 0x108, struct.pack('<I', 1)); return 1
    def escribir(self, a):
        f = self.abiertos[self.ecx()]; d = self.fs[f[0]]
        d[f[1]:f[1] + a[1]] = bytes(self.mu.mem_read(a[0], a[1])); f[1] += a[1]; return a[1]
    def leer(self, a):
        f = self.abiertos[self.ecx()]; d = self.fs[f[0]]
        b = bytes(d[f[1]:f[1] + a[1]]); self.mu.mem_write(a[0], b); f[1] += len(b); return len(b)
    def posicionar(self, a):
        f = self.abiertos[self.ecx()]; f[1] = (0 if a[1] == 0 else f[1]) + a[0]; return f[1]
    def cerrar(self, a):
        self.abiertos.pop(self.ecx(), None); self.mu.mem_write(self.ecx() + 0x108, struct.pack('<I', 0))
    def correr(self, start, args=(), stop=RET, regs=()):
        mu = self.mu
        mu.mem_write(STACK, struct.pack('<I', RET) + b''.join(struct.pack('<I', x) for x in args))
        mu.reg_write(UC_X86_REG_ESP, STACK)
        for r, v in regs: mu.reg_write(r, v)
        mu.emu_start(start, stop, count=500000)
        assert mu.reg_read(UC_X86_REG_EIP) == stop, hex(mu.reg_read(UC_X86_REG_EIP))
        return mu.reg_read(UC_X86_REG_EAX)
    # el juego
    def suceso(self, tipo, jug, param=0, w1=0):
        self.mu.mem_write(0x1fe000, b'Nombre\0')
        self.correr(0x498910, [tipo, jug, param, 0x1fe000, w1, 0, 0])
    def fin_de_ronda(self):
        self.correr(0x4989d0); self.ronda += 1
    def historia(self): return bytes(self.fs.get(b'HISTORY.DAT', b''))
    def informe(self):
        """Lo que arma 0x499450: [(página, [renglones])] por ronda, y el búfer crudo."""
        p = self.correr(0x499450); out = []; crudo = b''
        for _ in range(self.ronda):
            tam, n, pag = struct.unpack('<3h', self.mu.mem_read(p, 6))
            crudo += bytes(self.mu.mem_read(p, tam))
            assert tam == 6 + 0x1c * n, (tam, n)
            out.append((pag, [bytes(self.mu.mem_read(p + 6 + 0x1c * i, 0x1c)) for i in range(n)]))
            p += tam
        return out, crudo
    def renglon(self, r, x=100, y=200):
        self.dibujo.clear(); self.mu.mem_write(0x1fd000, r)
        self.correr(0x4b4110, [x, y, 0x1fd000]); return list(self.dibujo)
    # la red
    def paquete(self, tipo, carga, remitente=0):
        mu = self.mu
        mu.mem_write(PKT, struct.pack('<IhhI', 0, tipo, remitente, 7) + carga)
        mu.reg_write(UC_X86_REG_ESP, STACK); mu.reg_write(UC_X86_REG_ESI, PKT)
        mu.emu_start(0x4b6a16, 0x4b85bb, count=5000)
        assert mu.reg_read(UC_X86_REG_EIP) == 0x4b85bb
    def abrir(self, t=0, remitente=0): self.paquete(0x2a0, struct.pack('<I', t), remitente)
    def estado(self, texto, t=0, remitente=0):
        self.paquete(0x2a1, struct.pack('<I', t) + texto.encode() + b'\0', remitente)
    def votos(self):
        n = struct.unpack('<i', self.mu.mem_read(VT_N, 4))[0]
        return [struct.unpack('<hh', self.mu.mem_read(VT_TAB + 0x1c * i + 0x16, 4)) for i in range(n)]
    def duenos(self):
        n = struct.unpack('<i', self.mu.mem_read(VT_N, 4))[0]
        return [struct.unpack('<h', self.mu.mem_read(VT_TAB + 0x1c * i + 2, 2))[0] for i in range(n)]
    def bando(self, i, activo=1, humano=True, maquina=0):
        self.mu.mem_write(SIDES + SIDE * i, bytes([activo]))
        self.mu.mem_write(SIDES + SIDE * i + 0xe2, struct.pack('<h', -1 if humano else 0))
        self.mu.mem_write(SIDES + SIDE * i + 3, bytes([maquina]))

def votacion(g, ses, *estados, cerrar=True):
    """Una sesión de la Votación: la orden de abrir, los estados (fase, reinicios, marcas) y, si cerrar, el cierre."""
    g.abrir()
    for fase, res, marcas in estados: g.estado(f'VOT {ses} {fase} 0 {res} {marcas}')
    if cerrar: g.estado(f'VOT {ses} cerrado 0 {estados[-1][1]} {estados[-1][2]}')

def partida(g, votar):
    """Ronda 1 con sucesos; ronda 2 con sucesos y (si votar) una votación 5 a 3; ronda 3 en curso con sucesos y (si
    votar) dos votaciones, la primera anotada por un reinicio y la segunda por el cierre."""
    g.suceso(5, 0); g.suceso(9, 3, 2); g.fin_de_ronda()
    g.suceso(2, 1, 4); g.suceso(7, 1); g.suceso(1, 6)
    if votar: votacion(g, 'aa11bb22', ('libre', 0, 'ss-n-s--'), ('libre', 0, 'sssnsnns'))
    g.fin_de_ronda()
    g.suceso(3, 2)
    if votar: votacion(g, 'cc33dd44', ('libre', 0, 'sn------'), ('libre', 1, '--------'), ('auto', 1, 'nnnn----'))

# ---------------------------------------------------------------- HISTORY.DAT y el informe
print('-- sin votaciones: igual que el original')
av, orig = Juego(), Juego(ORIG)
partida(av, False); partida(orig, False)
ver('HISTORY.DAT idéntico al del original', (av.historia() == orig.historia(), len(av.historia())), (True, 0x126))
ver('el informe idéntico al del original', av.informe()[1] == orig.informe()[1], True)

print('-- con votaciones')
av = Juego(); partida(av, True)
ver('ronda en curso: las dos votaciones en la tabla (5-3 ya pasó a HISTORY.DAT)', av.votos(), [(1, 1), (0, 4)])
h, o = av.historia(), orig.historia()
b1 = struct.unpack_from('<h', o, 0)[0]
cab = bytearray(o[b1:b1 + 0x48]); struct.pack_into('<h', cab, 0, struct.unpack_from('<h', cab, 0)[0] + 0x1c)
struct.pack_into('<h', cab, 0x44, struct.unpack_from('<h', cab, 0x44)[0] + 1)
cab[0x46:0x48] = h[b1 + 0x46:b1 + 0x48]   # relleno que el original no escribe: lo que haya en la pila
esperado = o[:b1] + bytes(cab) + o[b1 + 0x48:b1 + 0x48 + 5] + VOTO(5, 3) + o[b1 + 0x48 + 5:]
ver('HISTORY.DAT: ronda 1 igual; ronda 2 con la votación primero, tamaño y cantidad +1', h == esperado, True)
inf, _ = av.informe(); inf_o, _ = orig.informe()
ver('informe: ronda 1 igual al original', inf[0] == inf_o[0], True)
ver('informe: ronda 2 = la votación + los sucesos del original', inf[1], (inf_o[1][0], [VOTO(5, 3)] + inf_o[1][1]))
ver('informe: ronda en curso = las dos votaciones + los sucesos', inf[2], (inf_o[2][0], [VOTO(1, 1), VOTO(0, 4)] + inf_o[2][1]))
av.fin_de_ronda()
ver('fin de la ronda 3: la tabla queda vacía', av.votos(), [])
inf, _ = av.informe()
ver('  y las dos votaciones pasan a la ronda 3 de HISTORY.DAT', inf[2][1][:2], [VOTO(1, 1), VOTO(0, 4)])
ver('  ronda 4 en curso, sin votaciones', [len(r) for _, r in inf], [2, 4, 3, 0])

print('-- el renglón')
av, orig = Juego(), Juego(ORIG)
ver('votación de un bando: su escudo y el texto, igual que un suceso común de ese bando', [
    av.renglon(rec(0x13, p, 0, b'', (5, 3, 0))) == orig.renglon(rec(0, p, 0, b'Nombre'))[:1] + [('texto', 120, 200, 'Resultados votacion: 5 por el SI, 3 por el NO')]
    for p in range(8)], [True] * 8)
ver('  (el escudo del bando 5)', av.renglon(rec(0x13, 5, 0, b'', (5, 3, 0)))[0], ('escudo', 0x69 + 5, 100, 200))
ver('votación sin bando (8, de un .SAV de 1.0.18.0): el texto, sin escudo, donde va el texto de los demás', av.renglon(VOTO(5, 3)),
    [('texto', 120, 200, 'Resultados votacion: 5 por el SI, 3 por el NO')])
ver('  con 0 y 8', av.renglon(VOTO(0, 8))[0][3], 'Resultados votacion: 0 por el SI, 8 por el NO')
ver('control: bando fuera de rango (-1, 9): sin escudo', [[d[0] for d in av.renglon(rec(0x13, p, 0, b'', (1, 1, 0)))] for p in (-1, 9)],
    [['texto'], ['texto']])
r = rec(0, 3, 0, b'Nombre')
ver('control: un suceso común se dibuja igual que en el original', av.renglon(r), orig.renglon(r))
ver('  (escudo del jugador 3 y texto)', [d[0] for d in av.renglon(r)], ['escudo', 'texto'])
ver('control: el original con un renglón de votación solo dibuja un escudo', [d[0] for d in orig.renglon(VOTO(5, 3))], ['escudo'])

# ---------------------------------------------------------------- cuándo se anota
print('-- cuándo se anota una votación')
def caso(*pasos):
    g = Juego()
    for p in pasos: p(g)
    return g.votos()
ver('se anota al cerrar', caso(lambda g: votacion(g, 's1', ('libre', 0, 'sns-----'))), [(2, 1)])
ver('se anota al reiniciar (y al cerrar, la siguiente)', caso(lambda g: votacion(
    g, 's1', ('libre', 0, 'ss------'), ('libre', 1, '--------'), ('libre', 1, 'n-------'), ('libre', 2, '--------'),
    ('libre', 2, 'sssnnnn-'))), [(2, 0), (0, 1), (3, 4)])
ver('reinicio sin votos: nada', caso(lambda g: votacion(g, 's1', ('libre', 0, '--------'), ('libre', 1, '--------'),
                                                         ('libre', 1, 's-------'))), [(1, 0)])
ver('la votación automática cuenta', caso(lambda g: votacion(g, 's1', ('auto', 0, 'snsnsnss'))), [(5, 3)])
ver('control: sin votos, al cerrar no se anota', caso(lambda g: votacion(g, 's1', ('libre', 0, '--------'))), [])
ver('control: "cerrado" repetido no anota dos veces', caso(
    lambda g: votacion(g, 's1', ('libre', 0, 's-------')), lambda g: g.estado('VOT s1 cerrado 0 0 s-------')), [(1, 0)])
ver('control: estados sin orden de abrir (un .op viejo) no anotan', caso(
    lambda g: g.estado('VOT s1 libre 0 0 ssss----'), lambda g: g.estado('VOT s1 cerrado 0 0 ssss----')), [])
ver('control: cierre de emergencia no anota', caso(lambda g: g.abrir(), lambda g: g.estado('VOT - cerrado 0 0 --------')), [])
ver('control: programa muerto sin cerrar; la sesión siguiente no hereda sus votos', caso(
    lambda g: votacion(g, 's1', ('libre', 0, 'ssss----'), cerrar=False),
    lambda g: votacion(g, 's2', ('libre', 0, '--------'))), [])
ver('  ni aunque la siguiente arranque con otro número de reinicios', caso(
    lambda g: votacion(g, 's1', ('libre', 3, 'ssss----'), cerrar=False),
    lambda g: votacion(g, 's2', ('libre', 0, 'n-------'))), [(0, 1)])
ver('control: estados de Sorteo no anotan', caso(
    lambda g: g.abrir(), lambda g: g.estado('VOT s1 libre 0 0 ss------', t=1),
    lambda g: g.estado('VOT s1 cerrado 0 0 ss------', t=1)), [])
ver('control: estados de otra PC no anotan', caso(
    lambda g: g.abrir(), lambda g: g.estado('VOT s1 libre 0 0 ss------', remitente=3),
    lambda g: g.estado('VOT s1 cerrado 0 0 ss------', remitente=3)), [])
ver(f'tope de {VT_MAX} por ronda', len(caso(*[lambda g, i=i: votacion(g, f's{i}', ('libre', 0, 's-------'))
                                               for i in range(11)])), VT_MAX)
ver('control: la pausa sigue funcionando (el cierre la levanta)', (lambda g: (votacion(g, 's1', ('libre', 0, 's-------')),
    g.mu.mem_read(PZ_ARM - 1, 2) == b'\0\0')[1])(Juego()), True)

print('-- de quién es la votación (el escudo)')
def dueno(*bandos):
    g = Juego()
    for b in bandos: g.bando(*b)
    votacion(g, 's1', ('libre', 0, 's-------'))
    return g.duenos()
ver('el primer bando humano de la PC anfitriona (máquina 0)', dueno((0, 1, True, 1), (1, 1, False, 0), (2, 1, True, 0), (5, 1, True, 0)), [2])
ver('  el bando 0, si es el humano de la anfitriona', dueno((0, 1, True, 0), (3, 1, True, 0)), [0])
ver('  el bando 7', dueno((7, 1, True, 0)), [7])
ver('control: ningún humano en la anfitriona: sin bando (8)', dueno((0, 1, True, 1), (1, 1, False, 0), (4, 1, True, 2)), [8])
ver('control: un humano de la anfitriona que no juega no cuenta', dueno((1, 0, True, 0), (6, 1, True, 0)), [6])
g = Juego(); g.bando(2, 1, True, 0)
g.abrir(); g.bando(2, 1, True, 1); g.bando(4, 1, True, 0)   # cambia después de abrir
g.estado('VOT s1 libre 0 0 s-------'); g.estado('VOT s1 libre 1 1 --------')
g.estado('VOT s1 libre 1 1 n-------'); g.estado('VOT s1 cerrado 0 1 n-------')
votacion(g, 's2', ('libre', 0, 'nn------'))
ver('se fija al abrir: el reinicio y el cierre llevan el de la apertura; la sesión siguiente, el nuevo', g.duenos(), [2, 2, 4])

g = Juego(); votacion(g, 's1', ('libre', 0, 's-------')); g.correr(0x4988d0)
ver('partida nueva (0x4988d0): la tabla queda vacía', g.votos(), [])

# ---------------------------------------------------------------- .SAV
print('-- guardar y cargar')
OPC = bytes(range(0x18))
def guardar(g):
    g.fs[b'P.SAV'] = bytearray(b'PRINCIPIO'); g.abiertos[FRAME - 0x12c] = [b'P.SAV', 9]
    g.mu.mem_write(FRAME - 0x12c + 0x108, struct.pack('<I', 1)); g.mu.mem_write(OPTS, OPC)
    g.correr(0x439c72, stop=0x439c8f, regs=[(UC_X86_REG_EBP, FRAME)])
    return bytes(g.fs[b'P.SAV'])
def cargar_sav(g, datos):
    g.fs[b'P.SAV'] = bytearray(datos); g.abiertos[FRAME - 0x120] = [b'P.SAV', 9]
    g.mu.mem_write(FRAME - 0x120 + 0x108, struct.pack('<I', 1)); g.mu.mem_write(OPTS, bytes(0x18))
    g.mu.mem_write(VT_N, struct.pack('<i', 5))          # basura de antes: tiene que quedar lo del archivo
    g.correr(0x439fda, stop=0x43a010, regs=[(UC_X86_REG_EBP, FRAME)])
    return g.votos(), bytes(g.mu.mem_read(OPTS, 0x18)) == OPC
g = Juego(); votacion(g, 's1', ('libre', 0, 'sssnn---')); votacion(g, 's2', ('libre', 0, 'n-------'))
sav = guardar(g)
ver('guardado: lo del original y después VOTA, cantidad y tabla',
    (sav[:9 + 0x18] == b'PRINCIPIO' + OPC, sav[0x21:0x25], struct.unpack_from('<i', sav, 0x25)[0], len(sav) - 0x29),
    (True, b'VOTA', 2, VT_MAX * 0x1c))
ver('  el original no escribe nada más', len(guardar(Juego(ORIG))), 9 + 0x18)
ver('cargado: la tabla vuelve', cargar_sav(Juego(), sav), ([(3, 2), (0, 1)], True))
ver('control: .SAV viejo (sin VOTA): tabla vacía', cargar_sav(Juego(), sav[:0x21]), ([], True))
ver('control: .SAV con 0x18 incompleto: tabla vacía', cargar_sav(Juego(), sav[:0x1d]), ([], False))
ver('control: otra marca: tabla vacía', cargar_sav(Juego(), sav[:0x21] + b'XOTA' + sav[0x25:]), ([], True))
ver('control: tabla cortada: vacía', cargar_sav(Juego(), sav[:-1]), ([], True))
ver('control: cantidad mayor que el tope: vacía', cargar_sav(Juego(), sav[:0x25] + struct.pack('<i', 9) + sav[0x29:]), ([], True))
ver('control: el original carga el .SAV nuevo igual que uno viejo', (lambda g: (
    g.fs.__setitem__(b'P.SAV', bytearray(sav)), g.abiertos.__setitem__(FRAME - 0x120, [b'P.SAV', 9]),
    g.mu.mem_write(FRAME - 0x120 + 0x108, struct.pack('<I', 1)),
    g.correr(0x439fda, stop=0x43a010, regs=[(UC_X86_REG_EBP, FRAME)]),
    bytes(g.mu.mem_read(OPTS, 0x18)) == OPC)[-1])(Juego(ORIG)), True)
print('MAL:', mal)
sys.exit(1 if mal else 0)
