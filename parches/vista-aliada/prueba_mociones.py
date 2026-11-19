# Prueba de juguete de las mociones de votación (mo_* de build.py) sobre el exe parcheado, en unicorn.
# Uso: python prueba_mociones.py [carpeta]   (por defecto E:\Warlords-TEST\Warlords3; armarla antes con build.py)
# Submenú: «Votacion» abre el diálogo de mociones; un renglón habilitado manda TL_OPEN con la moción, uno
# deshabilitado no. Recepción (0x4b6a16 real): la moción va a la línea de comandos de votacion.exe. Cierre (estado
# "cerrado"): «Partida a prueba» pone la marca solo con SI de todos los humanos en juego. Controles: un humano vota NO;
# un humano no votó; un bando de la computadora vota NO (no cuenta); votación libre; moción fuera de rango.
# Guardado/carga del bloque 'MOCI', partida nueva, y la P en el mapa (después del marco, 0x4c1b92).
import os as _os, sys as _sys; _sys.path.append(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..'))  # para encontrar juego_pruebas.py
from juego_pruebas import W3  # carpeta del juego de pruebas: se cambia solo ahi
import os, sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

DIR = sys.argv[1] if len(sys.argv) > 1 else W3
pe = pefile.PE(os.path.join(DIR, 'DarklordAV.exe')); BASE = pe.OPTIONAL_HEADER.ImageBase
img = bytes(pe.get_memory_mapped_image())
SIZE = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
STACK, RET, STUBS, PKT = 0x1f0000, 0x100, 0x300000, 0x150000
MACHINE, SIDE, SIDE_ON, SIDE_HUMAN = 0x5899fc, 0x1f8, 0x536b30, 0x536c12
VOTE_HOT = 0x1a
k = img.index(b'MOCI' + bytes(4))
MO_FLAGS = BASE + k + 4
MO_ON, MO_CUR = BASE + k - 32, BASE + k - 28
OPCMD = BASE + img.index(b'votacion.exe" --operador --mocion 0 --bando 0\0')
SPCMD = BASE + img.index(b'votacion.exe" --espectador 00000000 --mocion 0 --bando 0\0')
SIDE_ALIVE, SIDE_MACHINE, PV = SIDE_ON + 1, 0x536b33, 0x5643c8

mal = 0
def ver(nombre, r, esperado):
    global mal
    ok = r == esperado
    mal += not ok
    print('OK ' if ok else 'MAL', nombre, '->', r)

def cstr(mu, a):
    s = bytes(mu.mem_read(a, 512)); return s[:s.index(b'\0')].decode('latin1')
def rd(mu, a): return struct.unpack('<I', mu.mem_read(a, 4))[0]

class Juego:
    def __init__(self, machine=0):
        mu = self.mu = Uc(UC_ARCH_X86, UC_MODE_32)
        mu.mem_map(BASE, SIZE); mu.mem_write(BASE, img[:SIZE])
        mu.mem_map(0x100000, 0x100000)
        mu.mem_map(STUBS, 0x1000)
        mu.mem_write(MACHINE, struct.pack('<H', machine))
        self.log = []
        imp = {i.name.decode(): i.address for e in pe.DIRECTORY_ENTRY_IMPORT for i in e.imports if i.name}
        for n, nombre in enumerate(('GetTickCount', 'timeGetTime')):
            stub = STUBS + 0x10 * n
            mu.mem_write(imp[nombre], struct.pack('<I', stub))
            def g(mu, a, size, _):
                sp = mu.reg_read(UC_X86_REG_ESP)
                mu.reg_write(UC_X86_REG_EAX, 1000000)
                mu.reg_write(UC_X86_REG_EIP, struct.unpack('<I', mu.mem_read(sp, 4))[0]); mu.reg_write(UC_X86_REG_ESP, sp + 4)
            mu.hook_add(UC_HOOK_CODE, g, begin=stub, end=stub)
    def interceptar(self, addr, fn, pop=0):
        def g(mu, a, size, _):
            sp = mu.reg_read(UC_X86_REG_ESP)
            ret, *args = struct.unpack('<11I', mu.mem_read(sp, 44))
            r = fn(args)
            mu.reg_write(UC_X86_REG_EAX, (r or 0) & 0xffffffff)
            mu.reg_write(UC_X86_REG_ESP, sp + 4 + pop); mu.reg_write(UC_X86_REG_EIP, ret)
        self.mu.hook_add(UC_HOOK_CODE, g, begin=addr, end=addr)
    def correr(self, start, args=(), hasta=RET):
        mu = self.mu
        mu.mem_write(STACK, struct.pack('<I', RET) + b''.join(struct.pack('<I', x) for x in args))
        regs = ((UC_X86_REG_EBX, 0x9abc), (UC_X86_REG_EDI, 0x5678), (UC_X86_REG_EBP, 0xdef0))
        for r, v in regs: mu.reg_write(r, v)
        mu.reg_write(UC_X86_REG_ESP, STACK)
        mu.emu_start(start, hasta, count=200000)
        assert mu.reg_read(UC_X86_REG_EIP) == hasta, hex(mu.reg_read(UC_X86_REG_EIP))
        if hasta == RET:
            assert mu.reg_read(UC_X86_REG_ESP) == STACK + 4
            for r, v in regs: assert mu.reg_read(r) == v, (start, r)
    def paquete(self, tipo, carga, remitente=0):
        mu = self.mu
        mu.mem_write(PKT, struct.pack('<IhhI', 0, tipo, remitente, 7) + carga)
        mu.reg_write(UC_X86_REG_ESP, STACK); mu.reg_write(UC_X86_REG_ESI, PKT)
        mu.emu_start(0x4b6a16, 0x4b85bb, count=5000)
        assert mu.reg_read(UC_X86_REG_EIP) == 0x4b85bb
    def bandos(self, humanos, compu=()):
        for s in range(8):
            on = s in humanos or s in compu
            self.mu.mem_write(SIDE_ON + SIDE * s, bytes([on]))
            self.mu.mem_write(SIDE_HUMAN + SIDE * s, struct.pack('<h', -1 if s in humanos else 0))
    def flags(self): return rd(self.mu, MO_FLAGS)

# ---------------------------------------------------------------- submenú
def menu(clics, machine=0, humanos=(0, 1), muertos=()):
    g = Juego(machine)
    g.bandos(humanos)
    for s in humanos: g.mu.mem_write(SIDE_ALIVE + SIDE * s, b'\0' if s in muertos else b'\1')
    g.interceptar(0x4d7d70, lambda a: g.log.append(('cerrar',)))
    g.interceptar(0x4dd3b0, lambda a: g.log.append(('red', a[0], bytes(g.mu.mem_read(a[1], a[2])))))
    g.interceptar(0x408a00, lambda a: g.log.append(('chat',)))
    g.interceptar(0x4d7980, lambda a: g.log.append(('abrir', a[0], hex(a[1]))), pop=40)
    g.interceptar(0x4d8230, lambda a: None, pop=8)
    g.interceptar(0x4d82a0, lambda a: None)
    g.interceptar(0x4bd180, lambda a: g.log.append(('dibujar', a[0])))
    g.interceptar(0x4d7f60, lambda a: None)
    for c in clics: g.correr(0x4bd520, [c])
    return g, g.log

print('-- submenú de mociones')
g, r = menu([VOTE_HOT])
ver('«Votacion» abre el diálogo 134 con los manejadores del menú', r, [('cerrar',), ('abrir', 134, '0x4bcc60'), ('dibujar', 1)])
ver('  queda en modo mociones', g.mu.mem_read(MO_ON, 1)[0], 1)
g, r = menu([VOTE_HOT, 0xc])
ver('«Partida a prueba»: cierra y manda abrir con moción 1', r[3:], [('cerrar',), ('red', 0x2a0, struct.pack('<III', 0, 1, 0))])
ver('  y sale del modo mociones', g.mu.mem_read(MO_ON, 1)[0], 0)
g, r = menu([VOTE_HOT, 0xb])
ver('«Votacion libre»: moción 0', r[3:], [('cerrar',), ('red', 0x2a0, struct.pack('<III', 0, 0, 0))])
for hot, n, nombre in ((VOTE_HOT, 2, 'Finalizacion'), (0xe, 4, 'Vale todo'), (0xf, 5, 'Enganche')):
    g, r = menu([VOTE_HOT, hot])
    ver(f'«{nombre}»: moción {n}', r[3:], [('cerrar',), ('red', 0x2a0, struct.pack('<III', 0, n, 0))])
ABRIR = [('cerrar',), ('abrir', 134, '0x4bcc60'), ('dibujar', 1)]
g, r = menu([VOTE_HOT, 0xd], humanos=(0, 3, 5), muertos=(5,))
ver('«Descalificacion»: cierra y reabre el submenú con los colores', r[3:], ABRIR)
ver('  en modo colores', g.mu.mem_read(MO_ON, 1)[0], 2)
g, r = menu([VOTE_HOT, 0xd, 0xd], humanos=(0, 3, 5), muertos=(5,))
ver('  Rojo (humano vivo): moción 3, bando 3', r[6:], [('cerrar',), ('red', 0x2a0, struct.pack('<III', 0, 3, 3))])
ver('  y sale del modo', g.mu.mem_read(MO_ON, 1)[0], 0)
g, r = menu([VOTE_HOT, 0xd, 0xf], humanos=(0, 3, 5), muertos=(5,))
ver('  control: Azul (humano muerto) deshabilitado', r[6:], [])
g, r = menu([VOTE_HOT, 0xd, 0xc], humanos=(0, 3, 5), muertos=(5,))
ver('  control: Amarillo (no juega) deshabilitado', r[6:], [])
g, r = menu([VOTE_HOT, 0xd, VOTE_HOT], humanos=(0, 3))
ver('  control: en colores, Naranja (no juega) no manda', r[6:], [])
g, r = menu([VOTE_HOT, 0xc], machine=2)
ver('control: otra máquina no manda (solo cierra)', r[3:], [('cerrar',)])
# ---------------------------------------------------------------- recepción y cierre
VOT = lambda fase, marcas, res=0: f'VOT ab12cd34 {fase} 0 {res} {marcas}'.encode()
def votacion(mocion, marcas, humanos=(0, 1), compu=(), carga=None, remitente=0, bando=0, todo=False):
    g = Juego(3)
    g.interceptar(0x4dd3b0, lambda a: None)
    acu = []
    g.bandos(humanos, compu)
    g.paquete(0x2a0, carga if carga is not None else struct.pack('<III', 0, mocion, bando), remitente)
    op, sp = cstr(g.mu, OPCMD), cstr(g.mu, SPCMD)
    cmd = (op[-11], op[-1], sp[-11], sp[-1]) if todo else (op[-11], sp[-11])
    g.paquete(0x2a1, struct.pack('<I', 0) + VOT('libre', marcas))
    g.paquete(0x2a1, struct.pack('<I', 0) + VOT('cerrado', marcas))
    return (cmd, g.flags(), acu) if todo else (cmd, g.flags())

print('-- moción a votacion.exe y marca P')
ver('P, los dos humanos SI: --mocion 1 y marca', votacion(1, 'ss------'), (('1', '1'), 1))
ver('control: un humano NO', votacion(1, 'sn------'), (('1', '1'), 0))
ver('control: un humano no votó', votacion(1, 's-------'), (('1', '1'), 0))
ver('bando de la computadora NO: no cuenta', votacion(1, 'ssn-----', compu=(2,)), (('1', '1'), 1))
ver('control: votación libre con todos SI no marca', votacion(0, 'ss------'), (('0', '0'), 0))
ver('control: moción fuera de rango = libre', votacion(77, 'ss------'), (('0', '0'), 0))
ver('control: bando humano fuera de juego no cuenta', votacion(1, 's-------', humanos=(0,)), (('1', '1'), 1))

print('-- mociones por mayoría (SI > NO, humanos y virtuales)')
ver('Finalizacion 2 SI 1 NO: marca F (bit 4), sin cerrar la partida', votacion(2, 'ssn-----', compu=(2,), todo=True), (('2', '0', '2', '0'), 4, []))
ver('control: Finalizacion empate', votacion(2, 'sn------', todo=True), (('2', '0', '2', '0'), 0, []))
ver('control: Finalizacion más NO', votacion(2, 'snn-----', compu=(2,), todo=True), (('2', '0', '2', '0'), 0, []))
ver('Campeonato aprobado: marca C (bit 8)', votacion(6, 'ss------'), (('6', '6'), 8))
ver('control: Campeonato rechazado', votacion(6, 'sn------'), (('6', '6'), 0))
ver('Torneo especial aprobado: marca T (bit 0x10)', votacion(7, 'ss------'), (('7', '7'), 0x10))
ver('Partida anulada aprobada: marca A (bit 0x20)', votacion(8, 'ssn-----', compu=(2,)), (('8', '8'), 0x20))
ver('control: Partida anulada rechazada', votacion(8, 'nn------'), (('8', '8'), 0))
ver('control: moción 9 (fuera de rango) = libre', votacion(9, 'ss------'), (('0', '0'), 0))
ver('Descalificacion de Rojo aprobada: bits 8-11 = 4', votacion(3, 'ss-n-s--', humanos=(0, 1, 3), compu=(5,), bando=3, todo=True), (('3', '3', '3', '3'), 0x400, []))
ver('control: Descalificacion rechazada', votacion(3, 'sn-n----', humanos=(0, 1, 3), bando=3, todo=True), (('3', '3', '3', '3'), 0, []))
ver('control: Descalificacion con bando 9 = votación libre', votacion(3, 'ss------', bando=9, todo=True), (('0', '1', '0', '1'), 0, []))
ver('Vale todo aprobada: bit 2', votacion(4, 'ss------'), (('4', '4'), 2))
ver('control: Vale todo rechazada', votacion(4, 'nn------'), (('4', '4'), 0))
ver('Enganche aprobado: bit 0x1000', votacion(5, 'ssn-----', compu=(2,)), (('5', '5'), 0x1000))
ver('control: Partida a prueba sigue pidiendo unanimidad humana', votacion(1, 'snss----', compu=(2, 3)), (('1', '1'), 0))

print('-- segunda aprobación de la misma moción: quita la marca (19/11/2026)')
def votaciones(seq, humanos=(0, 1), compu=(), cierres=1):
    """Varias votaciones seguidas en la misma partida; cierres = estados «cerrado» repetidos de cada una."""
    g = Juego(3)
    g.interceptar(0x4dd3b0, lambda a: None)
    g.bandos(humanos, compu)
    out = []
    for mocion, marcas in seq:
        g.paquete(0x2a0, struct.pack('<III', 0, mocion, 0), 0)
        g.paquete(0x2a1, struct.pack('<I', 0) + VOT('libre', marcas))
        for _ in range(cierres): g.paquete(0x2a1, struct.pack('<I', 0) + VOT('cerrado', marcas))
        out.append(g.flags())
    return out
ver('P aprobada dos veces: aparece y desaparece', votaciones([(1, 'ss------'), (1, 'ss------')]), [1, 0])
ver('P tres veces: vuelve a aparecer', votaciones([(1, 'ss------')] * 3), [1, 0, 1])
ver('control: segunda P rechazada, la P sigue', votaciones([(1, 'ss------'), (1, 'sn------')]), [1, 1])
ver('control: el mismo cierre recibido dos veces no la quita', votaciones([(1, 'ss------')], cierres=2), [1])
ver('C dos veces: aparece y desaparece', votaciones([(6, 'ss------'), (6, 'ss------')]), [8, 0])
ver('F, V, T, A: cada una se quita con su segunda aprobación', votaciones([(2, 'ss------'), (4, 'ss------'), (7, 'ss------'),
    (8, 'ss------'), (2, 'ss------'), (4, 'ss------'), (7, 'ss------'), (8, 'ss------')]),
    [4, 6, 0x16, 0x36, 0x32, 0x30, 0x20, 0])
ver('control: quitar C no toca la P', votaciones([(1, 'ss------'), (6, 'ss------'), (6, 'ss------')]), [1, 9, 1])
ver('control: votación libre en el medio no cambia nada', votaciones([(6, 'ss------'), (0, 'ss------')]), [8, 8])

print('-- fin de ronda (mo_round desde 0x4988d0)')
def ronda(flags, humanos, compu=(), muertos=(), maq=None, pv=None, ret=0x498c1d):
    g = Juego()
    g.bandos(humanos, compu)
    for s in list(humanos) + list(compu):
        g.mu.mem_write(SIDE_ALIVE + SIDE * s, b'\0' if s in muertos else b'\1')
        g.mu.mem_write(SIDE_MACHINE + SIDE * s, bytes([(maq or {}).get(s, s if s in humanos else 0)]))
    g.mu.mem_write(MO_FLAGS, struct.pack('<I', flags))
    g.interceptar(0x440840, lambda a: g.mu.mem_write(PV, struct.pack('<8h', *(pv or [0] * 8))))
    g.mu.mem_write(STACK, struct.pack('<I', ret)); g.mu.reg_write(UC_X86_REG_ESP, STACK)
    g.mu.emu_start(0x4988d0, 0x4988d5, count=20000)
    assert g.mu.reg_read(UC_X86_REG_EIP) == 0x4988d5
    est = []
    for s in range(8):
        h = struct.unpack('<h', g.mu.mem_read(SIDE_HUMAN + SIDE * s, 2))[0]
        est.append(('H' if h == -1 else 'C' if h == 2 else '.') + format(g.mu.mem_read(SIDE_MACHINE + SIDE * s, 1)[0], 'x'))
    return ' '.join(est), g.flags()
ver('Descalificacion de Rojo: pasa al sistema (2, máquina ff)', ronda(0x401, (0, 3)), ('H0 .0 .0 Cff .0 .0 .0 .0', 1))
ver('control: partida nueva (otra dirección) no aplica', ronda(0x401, (0, 3), ret=0x42de68), ('H0 .0 .0 H3 .0 .0 .0 .0', 0x401))
ver('control: Rojo ya no es humano', ronda(0x400, (0,), compu=(3,)), ('H0 .0 .0 .0 .0 .0 .0 .0', 0))
ver('Enganche: el humano muerto toma el sistema vivo con menos puntos', ronda(0x1000, (0, 1), compu=(2, 4, 6), muertos=(1,), pv=[9, 0, 50, 0, 20, 0, 30, 0]), ('H0 C1 .0 .0 H1 .0 .0 .0', 0))
ver('control: el más débil está muerto, toma el vivo siguiente', ronda(0x1000, (0, 1), compu=(2, 4, 6), muertos=(1, 4), pv=[9, 0, 50, 0, 20, 0, 30, 0]), ('H0 C1 .0 .0 .0 .0 H1 .0', 0))
ver('control: su PC tiene otro bando humano vivo, no engancha', ronda(0x1000, (0, 1, 5), compu=(2,), muertos=(1,), maq={5: 1}, pv=[9, 0, 5, 0, 0, 0, 0, 0]), ('H0 H1 .0 .0 .0 H1 .0 .0', 0))
ver('control: sin eliminado no pasa nada', ronda(0x1000, (0, 1), compu=(2,)), ('H0 H1 .0 .0 .0 .0 .0 .0', 0))
ver('control: sin sistema vivo no pasa nada', ronda(0x1000, (0, 1), compu=(2,), muertos=(1, 2)), ('H0 H1 .0 .0 .0 .0 .0 .0', 0))
ver('control: sin mociones pendientes, Vale todo intacto', ronda(2, (0, 1), muertos=(1,)), ('H0 H1 .0 .0 .0 .0 .0 .0', 2))

# ---------------------------------------------------------------- .SAV
print('-- guardado y carga')
g = Juego(); escrito = []
g.mu.mem_write(MO_FLAGS, struct.pack('<I', 1))
g.interceptar(0x4dfd70, lambda a: escrito.append(bytes(g.mu.mem_read(a[0], a[1]))), pop=8)
g.interceptar(0x4dfdc0, lambda a: None)
# vt_savef (lo llama 0x439c8a)
sav = struct.unpack('<i', img[0x439c8b - BASE:0x439c8f - BASE])[0] + 0x439c8f
g.correr(sav)
ver('el último bloque del .SAV es MOCI + banderas', escrito[-1], b'MOCI\1\0\0\0')

# po_loadf lee POZO y OBRA antes; para probar solo MOCI se arranca en obl_end
k2 = img.index(b'\xc7\x05' + struct.pack('<I', MO_FLAGS) + bytes(4))
OBL_END = BASE + k2 - 5   # call ob_rebuild justo antes
def carga(resto):
    g = Juego(); datos = bytearray(resto)
    def leer(a):
        n = min(a[1], len(datos)); g.mu.mem_write(a[0], bytes(datos[:n])); del datos[:n]; return n
    g.mu.mem_write(MO_FLAGS, struct.pack('<I', 7))
    g.interceptar(0x4dfd20, leer, pop=8)
    ob = OBL_END + 5 + struct.unpack('<i', img[OBL_END - BASE + 1:OBL_END - BASE + 5])[0]
    g.interceptar(ob, lambda a: None)
    g.mu.mem_write(STACK, struct.pack('<I', RET))
    g.mu.reg_write(UC_X86_REG_ESP, STACK - 32); g.mu.reg_write(UC_X86_REG_EBP, 0x180000)
    g.mu.emu_start(OBL_END, RET, count=2000)
    return g.flags()
ver('carga con MOCI marcada', carga(b'MOCI\1\0\0\0'), 1)
ver('control: .SAV viejo sin MOCI', carga(b''), 0)
ver('control: otro bloque', carga(b'XXXX\1\0\0\0'), 0)
ver('control: MOCI cortado', carga(b'MOCI\1\0'), 0)

# ---------------------------------------------------------------- la P en el mapa
print('-- P en el mapa')
def dibujo(flag, cargada=True):
    g = Juego(); out = []
    g.mu.mem_write(MO_FLAGS, struct.pack('<I', flag))
    hoja = 0x180000; g.mu.mem_write(hoja + 8, struct.pack('<I', 1 if cargada else 0))
    g.interceptar(0x4e4a90, lambda a: hoja, pop=4)
    g.interceptar(0x4dd3f0, lambda a: out.append(('cargar', a[0])) or 1)
    g.interceptar(0x4dd530, lambda a: out.append(('pegar', *a[:8])))
    g.mu.mem_write(0x53c393, b'\x08')
    for r, v in ((UC_X86_REG_ESI, 0x7777), (UC_X86_REG_EBX, 100), (UC_X86_REG_EBP, 30), (UC_X86_REG_ESP, STACK)):
        g.mu.reg_write(r, v)
    g.mu.emu_start(0x4c1b92, 0x4c1b9c, count=200000)
    ok = (g.mu.reg_read(UC_X86_REG_ESI) == 0x7777 and g.mu.reg_read(UC_X86_REG_EBX) == 100
          and g.mu.reg_read(UC_X86_REG_ESP) == STACK + 0x20 and not g.mu.reg_read(UC_X86_REG_EFLAGS) & 0x40)
    return out, ok
MOP = 172
o, ok = dibujo(1)
ver('marcada: pega la hoja 34x40 dentro del marco (x0+0x24+8, y0+0x54+8), después de los paneles', (o[0][0], o[0][2:], ok), ('pegar', (0, 0, 34, 40, 0x7777, 144, 122), True))
o, ok = dibujo(1, cargada=False)
ver('hoja sin cargar: la carga antes', ([x[0] for x in o], ok), (['cargar', 'pegar'], True))
o, ok = dibujo(0x3f)
ver('las seis marcas: P, F, V, C, T, A de izquierda a derecha', ([(x[1], x[7]) for x in o], ok), ([(MOP, 144), (MOP + 2, 182), (MOP + 1, 220), (MOP + 3, 258), (MOP + 4, 296), (MOP + 5, 334)], True))
o, ok = dibujo(4)
ver('solo F: en el primer lugar', ([(x[1], x[7]) for x in o], ok), ([(MOP + 2, 144)], True))
ver('control: sin marca no dibuja nada', dibujo(0), ([], True))
ver('control: solo Descalificación y Enganche pendientes, sin letra', dibujo(0x1400), ([], True))

print('MAL', mal)
sys.exit(1 if mal else 0)
