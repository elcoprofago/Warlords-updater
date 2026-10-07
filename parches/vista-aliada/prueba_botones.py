# Prueba de juguete de los botones de Votación y Sorteo (tl_* de build.py) sobre el exe y el RES parcheados, en unicorn.
# Uso: python prueba_botones.py [carpeta]   (por defecto C:\Warlords3; armarla antes con build.py)
# Menú: corre el armado del menú de partida (0x4bd180) y su despachador (0x4bd520) con las llamadas de dibujo, cierre
# y red interceptadas. Preparación: el final de la inicialización (0x46f341) y el clic (0x46e889). Red: la recepción
# (0x4b6a16) con paquetes armados a mano. Ociosa: 0x4dea40 con las funciones de Windows simuladas sobre un sistema de
# archivos de mentira (un dict). RES: los registros nuevos de los diálogos 35 y 7.
# Controles: Chat Mode y otro ítem del menú, otro control de la preparación, otra máquina, otro remitente, otro tipo de
# paquete, herramienta fuera de rango, el reloj sin cumplir, .ver trabado y el RES original sin los registros.
import os, sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

DIR = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3'
pe = pefile.PE(os.path.join(DIR, 'DarklordAV.exe')); BASE = pe.OPTIONAL_HEADER.ImageBase
img = bytes(pe.get_memory_mapped_image())
SIZE = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
STACK, RET, STUBS, PKT = 0x1f0000, 0x100, 0x300000, 0x150000
MACHINE = 0x5899fc
VOTE_TXT, VOTE_HOT, COIN = 0x19, 0x1a, 97

# Datos de tl_*: "Votacion\0" + nombre del juego + variables (place_data no alinea).
GAME = b'Warlords III Era de Alianzas\0'
k = img.index(b'Votacion\0' + GAME)
TL_VARS = BASE + k + 9 + len(GAME)
TL_TICK, TL_BUSY, TL_PEND_OPEN, TL_PEND_STATE = TL_VARS, TL_VARS + 4, TL_VARS + 8, TL_VARS + 0xc
TL_BUF = TL_VARS + 16 + 4 + 4 + 260
ERR = [BASE + img.index(f'No se pudo abrir Herramientas\\{n}.exe\0'.encode()) for n in ('votacion', 'sorteo')]

def maquina(machine=0):
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(BASE, SIZE); mu.mem_write(BASE, img[:SIZE])
    mu.mem_map(0x100000, 0x100000)
    mu.mem_map(STUBS, 0x1000)
    mu.mem_write(MACHINE, struct.pack('<H', machine))
    return mu

def cstr(mu, a):
    s = bytes(mu.mem_read(a, 512)); return s[:s.index(b'\0')].decode('latin1')

def interceptar(mu, addr, pop, fn, registro):
    """En addr: anota fn(mu, args) y vuelve (pop = bytes de argumentos que limpia la llamada)."""
    def g(mu, a, size, _):
        sp = mu.reg_read(UC_X86_REG_ESP)
        ret, *args = struct.unpack('<9I', mu.mem_read(sp, 36))
        r = fn(mu, args)
        if r is not None and registro is not None: registro.append(r)
        mu.reg_write(UC_X86_REG_EAX, getattr(fn, 'eax', 0) if not callable(getattr(fn, 'eax', None)) else fn.eax())
        mu.reg_write(UC_X86_REG_ESP, sp + 4 + pop); mu.reg_write(UC_X86_REG_EIP, ret)
    mu.hook_add(UC_HOOK_CODE, g, begin=addr, end=addr)

def correr(mu, start, args, hasta=RET, count=200000):
    esp = STACK
    mu.mem_write(esp, struct.pack('<I', RET) + b''.join(struct.pack('<I', a) for a in args))
    regs = ((UC_X86_REG_EBX, 0x9abc), (UC_X86_REG_EDI, 0x5678), (UC_X86_REG_EBP, 0xdef0))
    for r, v in regs: mu.reg_write(r, v)
    mu.reg_write(UC_X86_REG_ESP, esp)
    mu.emu_start(start, hasta, count=count)
    assert mu.reg_read(UC_X86_REG_EIP) == hasta, hex(mu.reg_read(UC_X86_REG_EIP))
    if hasta == RET:
        assert mu.reg_read(UC_X86_REG_ESP) == esp + 4
        for r, v in regs: assert mu.reg_read(r) == v
    return mu

mal = 0
def ver(nombre, r, esperado):
    global mal
    ok = r == esperado
    mal += not ok
    print('OK ' if ok else 'MAL', nombre, '->', r)

# ---------------------------------------------------------------- menú de partida
def menu(flag, hover, machine=0):
    mu = maquina(machine); out = []
    textos = lambda mu, a: ('texto', a[0], cstr(mu, a[1])) if a[0] == VOTE_TXT else None
    colores = lambda mu, a: ('color', a[0], a[1]) if a[0] in (VOTE_TXT, 2) else None
    def hit(mu, a): return None
    hit.eax = hover
    interceptar(mu, 0x4dcee0, 0, hit, out)
    interceptar(mu, 0x4def30, 8, lambda mu, a: None, out)
    interceptar(mu, 0x4dd240, 0, textos, out)
    interceptar(mu, 0x4dd2b0, 0, colores, out)
    interceptar(mu, 0x4d7f60, 0, lambda mu, a: ('refresco',), out)
    correr(mu, 0x4bd180, [flag, 50, 80])
    return out

# Chat Mode (texto 2) sale gris (0x56) sin red, como en el original; resaltado (0xf) con el puntero encima.
print('-- menú de partida: texto y color de "Votacion"')
ver('anfitrión, puntero sobre Votacion', menu(1, VOTE_HOT),
    [('color', 2, 0x56), ('texto', VOTE_TXT, 'Votacion'), ('color', VOTE_TXT, 0xf), ('refresco',)])
ver('anfitrión, sin texto (mover el puntero)', menu(0, VOTE_HOT), [('color', 2, 0x56), ('color', VOTE_TXT, 0xf), ('refresco',)])
ver('control: puntero sobre Chat Mode', menu(0, 0xc), [('color', 2, 0xf), ('color', VOTE_TXT, 0x5c), ('refresco',)])
ver('control: otra máquina, puntero sobre Votacion', menu(0, VOTE_HOT, 3),
    [('color', 2, 0x56), ('color', VOTE_TXT, 0x56), ('refresco',)])

# Al abrirse (0x4bce20) el menú habilita (0) o deshabilita (2) cada línea; sin esto la zona de Votacion no responde.
def menu_init(machine, partida):
    mu = maquina(machine); out = []
    def p(mu, a): return None
    p.eax = partida
    interceptar(mu, 0x421310, 0, p, out)
    interceptar(mu, 0x4dcec0, 0, lambda mu, a: ('estado', a[0], a[1]) if a[0] in (VOTE_HOT, 0xb) else None, out)
    correr(mu, 0x4bce20, [])
    return out
print('-- menú de partida: al abrirse')
for partida in (0, 1):
    ver(f'anfitrión (0x421310 -> {partida}): Votacion habilitada', menu_init(0, partida),
        [('estado', VOTE_HOT, 0), ('estado', 0xb, 0)])
ver('otra máquina: Votacion deshabilitada', menu_init(3, 1), [('estado', VOTE_HOT, 2), ('estado', 0xb, 0)])

def despacho(item, machine=0):
    mu = maquina(machine); out = []
    interceptar(mu, 0x4d7d70, 0, lambda mu, a: ('cerrar',), out)
    interceptar(mu, 0x4dd3b0, 0, lambda mu, a: ('red', a[0], bytes(mu.mem_read(a[1], a[2]))), out)
    interceptar(mu, 0x408a00, 0, lambda mu, a: ('chat',), out)
    correr(mu, 0x4bd520, [item])
    return out
print('-- menú de partida: clic')
ver('anfitrión, Votacion', despacho(VOTE_HOT), [('cerrar',), ('red', 0x2a0, struct.pack('<I', 0))])
ver('control: otra máquina, Votacion', despacho(VOTE_HOT, 1), [('cerrar',)])
ver('control: Chat Mode', despacho(0xc), [('cerrar',), ('chat',)])
ver('control: control desconocido', despacho(0x30), [('cerrar',)])

# ---------------------------------------------------------------- pantalla de preparación
def prep_init(machine):
    mu = maquina(machine); out = []
    interceptar(mu, 0x4dcec0, 0, lambda mu, a: ('mostrar', a[0], a[1]), out)
    interceptar(mu, 0x4d7f60, 0, lambda mu, a: ('refresco',), out)
    correr(mu, 0x46f341, [], hasta=0x46f34b)
    return out
def prep_clic(cid, machine=0):
    mu = maquina(machine); out = []
    mu.mem_write(PKT, struct.pack('<II', 3, cid))
    mu.reg_write(UC_X86_REG_ESI, PKT)
    interceptar(mu, 0x4dd3b0, 0, lambda mu, a: ('red', a[0], bytes(mu.mem_read(a[1], a[2]))), out)
    correr(mu, 0x46e889, [], hasta=0x46ed83, count=50)
    return out
print('-- preparación')
ver('anfitrión: moneda visible', prep_init(0), [('mostrar', COIN, 0), ('refresco',)])
ver('otra máquina: moneda deshabilitada', prep_init(2), [('mostrar', COIN, 2), ('refresco',)])
ver('anfitrión: clic en la moneda', prep_clic(COIN), [('red', 0x2a0, struct.pack('<I', 1))])
ver('control: otra máquina, clic en la moneda', prep_clic(COIN, 2), [])
ver('control: control 98', prep_clic(98), [])
mu = maquina(); mu.mem_write(PKT, struct.pack('<II', 3, 80)); mu.reg_write(UC_X86_REG_ESI, PKT)
mu.emu_start(0x46e889, 0, count=4)
ver('control: Chat (80) sigue a su tabla', hex(mu.reg_read(UC_X86_REG_EIP)), hex(0x46e898))

# ---------------------------------------------------------------- recepción
def recibir(tipo, remitente, carga):
    mu = maquina(2)
    mu.mem_write(PKT, struct.pack('<IhhI', 0, tipo, remitente, 7) + carga)
    mu.reg_write(UC_X86_REG_ESP, STACK); mu.reg_write(UC_X86_REG_ESI, PKT)
    mu.emu_start(0x4b6a16, 0x4b85bb, count=2000)
    eip = mu.reg_read(UC_X86_REG_EIP)
    return (hex(eip) if eip != 0x4b85bb else 'fin', list(mu.mem_read(TL_PEND_OPEN, 2)), list(mu.mem_read(TL_PEND_STATE, 2)),
            cstr(mu, TL_BUF), cstr(mu, TL_BUF + 256))
print('-- recepción')
ver('abrir Sorteo', recibir(0x2a0, 0, struct.pack('<I', 1)), ('fin', [0, 1], [0, 0], '', ''))
ver('estado de Votación', recibir(0x2a1, 0, struct.pack('<I', 0) + b'v1 libre 0 0 s-n-----\0'),
    ('fin', [0, 0], [1, 0], 'v1 libre 0 0 s-n-----', ''))
r = recibir(0x2a1, 0, struct.pack('<I', 1) + b'x' * 300)
ver('estado largo: se corta en 255', (r[2], len(r[4])), ([0, 1], 255))
ver('control: otro remitente', recibir(0x2a0, 1, struct.pack('<I', 0)), ('fin', [0, 0], [0, 0], '', ''))
ver('control: otro remitente, estado', recibir(0x2a1, 3, struct.pack('<I', 0) + b'abc\0'), ('fin', [0, 0], [0, 0], '', ''))
ver('control: herramienta 2', recibir(0x2a0, 0, struct.pack('<I', 2)), ('fin', [0, 0], [0, 0], '', ''))
ver('control: tipo 0x2a2', recibir(0x2a2, 0, struct.pack('<I', 0)), ('fin', [0, 0], [0, 0], '', ''))
mu = maquina(); mu.mem_write(PKT, struct.pack('<IhhI', 0, 0x10, 0, 0)); mu.reg_write(UC_X86_REG_ESI, PKT)
mu.emu_start(0x4b6a16, 0, count=4)
ver('control: tipo 0x10 sigue a su tabla', hex(mu.reg_read(UC_X86_REG_EIP)), hex(0x4b6a28))

# ---------------------------------------------------------------- función ociosa
IMPORTS = {}
for e in pe.DIRECTORY_ENTRY_IMPORT:
    for i in e.imports:
        if i.name: IMPORTS[i.name.decode()] = i.address

class Windows:
    """Sistema de archivos de mentira y las llamadas que usa tl_idle. trabados: no se pueden borrar ni pisar."""
    def __init__(self, mu, archivos, tick, proceso_ok=True, trabados=()):
        self.fs, self.tick, self.ok, self.trabados = dict(archivos), tick, proceso_ok, set(trabados)
        self.h, self.n, self.log = {}, 100, []
        api = {'GetTickCount': (0, self.GetTickCount), 'DeleteFileA': (1, self.DeleteFileA),
               'MoveFileA': (2, self.MoveFileA), 'CreateFileA': (7, self.CreateFileA), 'ReadFile': (5, self.ReadFile),
               'WriteFile': (5, self.WriteFile), 'CloseHandle': (1, self.CloseHandle),
               'CreateProcessA': (10, self.CreateProcessA), 'CreateThread': (6, self.CreateThread),
               'MessageBoxA': (4, self.MessageBoxA), 'strlen': (0, self.strlen)}
        for k, (nombre, (n, fn)) in enumerate(api.items()):
            stub = STUBS + 0x10 * k
            mu.mem_write(IMPORTS[nombre], struct.pack('<I', stub))
            def g(mu, a, size, _, n=n, fn=fn):
                sp = mu.reg_read(UC_X86_REG_ESP)
                ret, *args = struct.unpack('<11I', mu.mem_read(sp, 44))
                mu.reg_write(UC_X86_REG_EAX, fn(mu, args) & 0xffffffff)
                mu.reg_write(UC_X86_REG_ESP, sp + 4 + 4 * n); mu.reg_write(UC_X86_REG_EIP, ret)
            mu.hook_add(UC_HOOK_CODE, g, begin=stub, end=stub)
    def GetTickCount(self, mu, a): return self.tick
    def DeleteFileA(self, mu, a):
        f = cstr(mu, a[0])
        if f in self.trabados or f not in self.fs: return 0
        del self.fs[f]; return 1
    def MoveFileA(self, mu, a):
        s, d = cstr(mu, a[0]), cstr(mu, a[1])
        if s not in self.fs or d in self.fs: return 0
        self.fs[d] = self.fs.pop(s); return 1
    def CreateFileA(self, mu, a):
        f, acc, disp = cstr(mu, a[0]), a[1], a[4]
        if disp == 3 and f not in self.fs: return -1
        if disp == 2:
            if f in self.trabados: return -1
            self.fs[f] = b''
        self.n += 1; self.h[self.n] = [f, 0]; return self.n
    def ReadFile(self, mu, a):
        f, pos = self.h[a[0]]; d = self.fs[f][pos:pos + a[2]]
        mu.mem_write(a[1], d); mu.mem_write(a[3], struct.pack('<I', len(d))); self.h[a[0]][1] += len(d); return 1
    def WriteFile(self, mu, a):
        f = self.h[a[0]][0]; self.fs[f] += bytes(mu.mem_read(a[1], a[2]))
        mu.mem_write(a[3], struct.pack('<I', a[2])); return 1
    def CloseHandle(self, mu, a):
        if a[0] in self.h: del self.h[a[0]]
        else: self.log.append(('cerrar', a[0]))
        return 1
    def CreateProcessA(self, mu, a):
        self.log.append(('proceso', cstr(mu, a[0]), cstr(mu, a[1]), a[7]))
        if not self.ok: return 0
        mu.mem_write(a[9], struct.pack('<II', 0x501, 0x502)); return 1
    def CreateThread(self, mu, a):
        self.log.append(('hilo', a[2], a[3])); return 0x601
    def MessageBoxA(self, mu, a):
        self.log.append(('aviso', cstr(mu, a[1]), cstr(mu, a[2]), hex(a[3]))); return 1
    def strlen(self, mu, a): return len(cstr(mu, a[0]))

def ociosa(machine=0, archivos=(), tick=1000, abrir=(0, 0), estado=(0, 0), bufs=('', ''), lados=(), **kw):
    mu = maquina(machine)
    w = Windows(mu, dict(archivos), tick, **kw)
    mu.mem_write(TL_PEND_OPEN, bytes(abrir)); mu.mem_write(TL_PEND_STATE, bytes(estado))
    for t, b in enumerate(bufs): mu.mem_write(TL_BUF + 256 * t, b.encode() + b'\0')
    for s, (on, humano, maq) in lados:
        mu.mem_write(0x536b30 + s * 0x1f8, bytes([on])); mu.mem_write(0x536b33 + s * 0x1f8, bytes([maq]))
        mu.mem_write(0x536c12 + s * 0x1f8, struct.pack('<h', -1 if humano else 2))
    out = []
    interceptar(mu, 0x4dd3b0, 0, lambda mu, a: ('red', a[0], bytes(mu.mem_read(a[1], a[2])).rstrip(b'\0'), a[2]), out)
    interceptar(mu, 0x4ec800, 0, lambda mu, a: ('juego', hex(mu.reg_read(UC_X86_REG_ECX))), out)
    interceptar(mu, 0x4df3e0, 0, lambda mu, a: ('red-poll', hex(mu.reg_read(UC_X86_REG_ECX))), out)
    regs = {r: 0x1000 + r for r in (UC_X86_REG_ESI, UC_X86_REG_EDX)}
    for r, v in regs.items(): mu.reg_write(r, v)
    correr(mu, 0x4dea40, [])
    for r, v in regs.items(): assert mu.reg_read(r) == v
    assert out[-2:] == [('juego', '0x5a6f50'), ('red-poll', '0x5899f8')], out
    return w, out[:-2], list(mu.mem_read(TL_PEND_OPEN, 2)), list(mu.mem_read(TL_PEND_STATE, 2)), mu

H = 'Herramientas\\'
print('-- función ociosa')
w, red, po, ps, _ = ociosa(0, {H + 'votacion.op': b'v1 auto 1 0 s-------', H + 'votacion.ver': b'viejo'}, abrir=(1, 0))
ver('anfitrión abre Votación como operador', [x for x in w.log if x[0] == 'proceso'],
    [('proceso', H + 'votacion.exe', f'"{H}votacion.exe" --operador', 0)])
ver('  y cierra los handles del proceso', [x for x in w.log if x[0] == 'cerrar'], [('cerrar', 0x501), ('cerrar', 0x502)])
ver('  y manda su estado', red, [('red', 0x2a1, struct.pack('<I', 0) + b'v1 auto 1 0 s-------', 260)])
ver('  sin dejar .op, .env ni .ver viejo', sorted(w.fs), [])
ver('  pedidos limpios', (po, ps), ([0, 0], [0, 0]))
lados = [(1, (1, 1, 2)), (3, (1, 1, 1)), (5, (1, 0, 2)), (6, (0, 1, 2)), (7, (1, 1, 2))]
w, red, po, ps, _ = ociosa(2, {H + 'sorteo.op': b'no es mio'}, abrir=(0, 1), lados=lados)
ver('espectador abre Sorteo con sus bandos (1 y 7)', [x for x in w.log if x[0] == 'proceso'],
    [('proceso', H + 'sorteo.exe', f'"{H}sorteo.exe" --espectador 01000001', 0)])
ver('control: el espectador no manda ni toca .op', (red, sorted(w.fs)), ([], [H + 'sorteo.op']))
w, red, po, ps, _ = ociosa(1, {H + 'votacion.ver': b'viejo'}, estado=(1, 0), bufs=('v1 libre 0 1 sn------', ''))
ver('espectador recibe estado: .ver nuevo', (w.fs, ps), ({H + 'votacion.ver': b'v1 libre 0 1 sn------'}, [0, 0]))
w, red, po, ps, _ = ociosa(1, {H + 'votacion.ver': b'viejo'}, estado=(1, 0), bufs=('nuevo', ''), trabados=[H + 'votacion.ver'])
ver('control: .ver trabado, se reintenta', (w.fs[H + 'votacion.ver'], ps), (b'viejo', [1, 0]))
w, red, po, ps, _ = ociosa(0, {}, abrir=(0, 1), proceso_ok=False)
hilo = [x for x in w.log if x[0] == 'hilo']
ver('sin el programa: aviso en un hilo', [(x[0], x[2]) for x in hilo], [('hilo', ERR[1])])
ver('  y se cierra el hilo', ('cerrar', 0x601) in w.log, True)
mu = maquina(); w2 = Windows(mu, {}, 0)
mu.reg_write(UC_X86_REG_ESP, STACK); mu.mem_write(STACK, struct.pack('<II', RET, ERR[1]))
mu.emu_start(hilo[0][1], RET, count=100)
ver('  el hilo muestra el aviso y vuelve', (w2.log, mu.reg_read(UC_X86_REG_ESP)),
    ([('aviso', 'No se pudo abrir Herramientas\\sorteo.exe', 'Warlords III Era de Alianzas', '0x41030')], STACK + 8))
def reloj_corto():
    mu = maquina(); w = Windows(mu, {H + 'votacion.op': b'x'}, 1100)
    mu.mem_write(TL_TICK, struct.pack('<I', 1000)); mu.mem_write(TL_PEND_OPEN, bytes([1, 1]))
    out = []
    interceptar(mu, 0x4dd3b0, 0, lambda mu, a: ('red',), out)
    interceptar(mu, 0x4ec800, 0, lambda mu, a: None, out)
    interceptar(mu, 0x4df3e0, 0, lambda mu, a: None, out)
    correr(mu, 0x4dea40, [])
    return w.log, out, list(mu.mem_read(TL_PEND_OPEN, 2))
ver('control: a los 100 ms no hace nada', reloj_corto(), ([], [], [1, 1]))

# ---------------------------------------------------------------- RES
SZ = {1: 0x80, 2: 0x9c, 3: 0x6c, 4: 0xac, 5: 0xa8, 6: 0xa0, 7: 0x1c, 8: 0x1c, 9: 0x1c, 0xa: 0x20,
      0xb: 0x64, 0xc: 0x64, 0xd: 0x3c, 0xe: 0x30, 0x11: 0x14, 0x12: 0x68, 0x13: 0x28, 0x14: 0x2c, 0x15: 0xac}
def recs(path, did):
    d = open(path, 'rb').read(); o = 8
    while True:
        h = struct.unpack_from('<5I', d, o)
        if h[0] == 7 and h[1] == did: break
        o += 20 + h[4]
    p = o + 20; out = {}
    for _ in range(h[2]):
        t, i = struct.unpack_from('<II', d, p); out[i] = d[p:p + 4 + SZ[t]]; p += 4 + SZ[t]
    assert p == o + 20 + h[4]
    return out
NUEVO, ORIG = os.path.join(DIR, 'DATA', 'WAR3AV.RES'), r'C:\Warlords3\DATA\War3.RES'
print('-- RES')
n35, o35 = recs(NUEVO, 35), recs(ORIG, 35)
ver('menú: 26 registros (24 + 2)', (len(n35), len(o35)), (26, 24))
ys = sorted(struct.unpack_from('<I', r, 0xc)[0] for i, r in n35.items() if r[0] == 0x13)
ver('menú: textos cada 16 píxeles', ys, list(range(46, 239, 16)))
ver('menú: Votacion debajo de Chat Mode', [struct.unpack_from('<I', n35[i], 0xc)[0] for i in (2, VOTE_TXT, 0x15)], [62, 78, 94])
ver('menú: zona de Votacion', struct.unpack_from('<6I', n35[VOTE_HOT], 8), (26, 74, 1, 0, 138, 16))
ver('control: zona de Help conserva x y ancho', struct.unpack_from('<6I', n35[0xb], 8), (28, 42, 1, 0, 136, 16))
n7, o7 = recs(NUEVO, 7), recs(ORIG, 7)
ver('preparación: botón de Sorteo', struct.unpack_from('<11I', n7[COIN], 0), (1, COIN, 567, 409, 1, 1, 166, 0, 0, 64, 60))
def rect(r): x, y = struct.unpack_from('<II', r, 8); w, h = struct.unpack_from('<II', r, 0x24); return x, y, x + w, y + h
x0, y0, x1, y1 = rect(n7[COIN])
ver('preparación: Sorteo dentro de la pantalla y sin tapar otro botón', (x1 <= 640 and y1 <= 480,
    [i for i, r in n7.items() if r[0] == 1 and i != COIN and not (rect(r)[2] <= x0 or x1 <= rect(r)[0] or rect(r)[3] <= y0 or y1 <= rect(r)[1])]),
    (True, []))
def archivos(path):
    d = open(path, 'rb').read(); o = 8
    while True:
        h = struct.unpack_from('<5I', d, o)
        if h[0] == 2 and h[1] == 0: break
        o += 20 + h[4]
    return [d[o + 20 + 60 * i:o + 80 + 60 * i] for i in range(h[2])]
fn, fo = archivos(NUEVO), archivos(ORIG)
ver('archivos: dos más (165 y 166)', (len(fn), len(fo)), (167, 165))
ver('archivo 166: sorteo en SETS\\Fantasy', (struct.unpack_from('<I', fn[166])[0], fn[166][4:11], struct.unpack_from('<6I', fn[166], 36)),
    (166, b'sorteo\0', (16, 1, 0, 0, 0, 0)))
ver('control: archivos originales intactos', fn[:165] == fo, True)
from PIL import Image
hoja = Image.open(os.path.join(DIR, 'SETS', 'Fantasy', 'sorteo.pcx'))
ver('sorteo.pcx: esquinas transparentes (11), centro dibujado', [hoja.getpixel((x, 60 * k + y)) == 11 for k in range(4) for x, y in ((0, 0), (63, 59), (32, 30))],
    [True, True, False] * 4)
ver('sorteo.pcx: 4 cuadros de 64x60, misma paleta que BUTT_STD', (hoja.mode, hoja.size, hoja.getpalette()[:768]),
    ('P', (64, 240), Image.open(r'C:\Warlords3\SETS\Fantasy\BUTT_STD.PCX').getpalette()[:768]))
ver('control: Chat intacto', n7[80], o7[80])
ver('control: el original no tiene la moneda', COIN in o7, False)
ver('control: diálogo 9 sigue con sus casillas nuevas', len(recs(NUEVO, 9)) - len(recs(ORIG, 9)), 2)
print('MAL:', mal)
sys.exit(1 if mal else 0)
