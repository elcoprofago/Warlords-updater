# Prueba de la IA con barcos "Landing" y "Carrier" (1.0.25.0: landchk desde tierra, ai_move, ai_conv, ai_free) sobre
# el exe parcheado, en unicorn, con la partida Aliados03 (jugador 2, como en prueba_cabotaje.py).
# Uso: python prueba_iabarcos.py ANTERIOR.exe [DarklordAV.exe] [partida.SAV]
#      ANTERIOR = el exe armado con el build.py de la versión anterior (referencia: el original ya difiere por los
#      puentes solo de tierra y los puertos arrasados).
# Esperado:
#  - mapa de distancias de la IA (0x497750, desde un grupo a pie junto a un puerto): sin bono, o con "Landing" en otro
#    bando, igual al anterior; con "Landing", solo cambian casillas de tierra, siempre más baratas o recién alcanzadas;
#  - caminos a pie hacia esas casillas: cada paso es un enlace del grafo o un desembarco de agua pura a tierra
#    transitable (nunca se embarca fuera de un puerto), y alguno no existía en el anterior;
#  - movimiento de la IA (0x4c4a10 entero, con stubs alrededor): si el barco no alcanza (código 5 con lchit = 1), el
#    grupo se parte hasta que entra; los que bajan quedan libres o en una pila nueva de la IA; la lista del marco (la
#    que recibe 0x4c4da0) es la del grupo nuevo; controles: humano, lchit 2, código 1, grupo de 1;
#  - convoyes (ai_conv): la orden de ir a la casilla vecina solo con todas las condiciones; un control por condición.
import sys, struct, collections, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

PREV = sys.argv[1]
NEW = sys.argv[2] if len(sys.argv) > 2 else r'C:\Warlords3\DarklordAV.exe'
sav = open(sys.argv[3] if len(sys.argv) > 3 else r'C:\Warlords3\Saves\Aliados03.SAV', 'rb').read()
P, STK = 2, 17
REC = lambda p: 0x53c410 + (p * 16 + 15) * 0xfc
GRP = 0x56ea90 + P * 0x4f0
ARMY = lambda i: 0x54fe52 + i * 0x1c
AIREC = lambda i: 0x561f00 + P * 0x49a + i * 0x40
SIDE = 0x536c08 + P * 0x1f8
DATA = (0x4f9000, 0xb0000)
LAND, CARR = (P, 1, b'Landing'), (P, 2, b'Carrier')

class Maquina:
    def __init__(s, exe):
        pe = pefile.PE(exe); s.pe = pe
        img = pe.get_memory_mapped_image()
        s.mu = mu = Uc(UC_ARCH_X86, UC_MODE_32)
        mu.mem_map(0x400000, (len(img) + 0xfff) & ~0xfff); mu.mem_write(0x400000, img)
        mu.mem_map(0x10000000, 0x100000); mu.mem_map(0xdead0000, 0x1000); mu.mem_write(0xdead0000, b'\xc3' * 0x1000)
        off = 0x6d
        for va, n in ((0x503e00, 0x12), (0x503e58, 0x32000), (0x535ed0, 0xa96), (0x536b30, 0x2d894)):
            mu.mem_write(va, sav[off:off + n]); off += n
        s.imports()
        s.data = bytes(mu.mem_read(*DATA))
        s.log = []; s.script = []
    def imports(s):
        mu = s.mu; mu.mem_map(0xdead1000, 0x10000); mu.mem_map(0x30000000, 0x4000000)
        names, k = {}, 0
        for d in s.pe.DIRECTORY_ENTRY_IMPORT:
            for imp in d.imports:
                stub = 0xdead1000 + 16 * k; k += 1
                mu.mem_write(imp.address, struct.pack('<I', stub)); names[stub] = (imp.name or b'?').decode()
        ARGS = {'GlobalAlloc': 2, 'GlobalLock': 1, 'GlobalUnlock': 1, 'GlobalFree': 1, 'GlobalHandle': 1}
        s.heap = 0x30000000
        def h(m, a, size, ud):
            n = names.get(a); sp = m.reg_read(UC_X86_REG_ESP)
            ret = struct.unpack('<I', m.mem_read(sp, 4))[0]; args = struct.unpack('<4I', m.mem_read(sp + 4, 16))
            if n == 'GlobalAlloc':
                sz = (args[1] + 15) & ~15; r = s.heap; s.heap += sz; m.mem_write(r, bytes(sz))
            elif n in ('GlobalLock', 'GlobalHandle'): r = args[0]
            elif n in ('GlobalUnlock', 'GlobalFree'): r = 0
            else: raise RuntimeError('importación no emulada: ' + n)
            m.reg_write(UC_X86_REG_EAX, r); m.reg_write(UC_X86_REG_ESP, sp + 4 + 4 * ARGS[n]); m.reg_write(UC_X86_REG_EIP, ret)
        mu.hook_add(UC_HOOK_CODE, h, begin=0xdead1000, end=0xdead1000 + 16 * k)
    def stub(s, addr, fn):
        # cdecl: fn(args) -> eax; vuelve al llamador sin tocar la pila de argumentos.
        def h(m, a, size, ud):
            sp = m.reg_read(UC_X86_REG_ESP)
            ret = struct.unpack('<I', m.mem_read(sp, 4))[0]; args = struct.unpack('<6i', m.mem_read(sp + 4, 24))
            m.reg_write(UC_X86_REG_EAX, fn(args) & 0xffffffff)
            m.reg_write(UC_X86_REG_ESP, sp + 4); m.reg_write(UC_X86_REG_EIP, ret)
        s.mu.hook_add(UC_HOOK_CODE, h, begin=addr, end=addr)
    def reset(s, bonos=()):
        s.mu.mem_write(DATA[0], s.data); s.heap = 0x30000000; s.log = []
        for q, ranura, txt in bonos:
            s.mu.mem_write(REC(q) + 0xb2 + ranura * 9, txt.ljust(9, b'\0'))
    def call(s, addr, args, regs={}):
        mu = s.mu; sp = 0x10080000
        for a in reversed(args): sp -= 4; mu.mem_write(sp, struct.pack('<i', a))
        sp -= 4; mu.mem_write(sp, struct.pack('<I', 0xdead0000)); mu.reg_write(UC_X86_REG_ESP, sp)
        for r, v in regs.items(): mu.reg_write(r, v)
        mu.emu_start(addr, 0xdead0000, count=50_000_000)
        return mu.reg_read(UC_X86_REG_EAX)
    def rd(s, a, n): return bytes(s.mu.mem_read(a, n))
    def u16(s, a): return struct.unpack('<H', s.rd(a, 2))[0]
    def s16(s, a): return struct.unpack('<h', s.rd(a, 2))[0]
    def w(s, a, fmt, *v): s.mu.mem_write(a, struct.pack(fmt, *v))
    def grupo(s, ini, embarcado=False):
        # El ejército STK del jugador P solo en ini, grupo de 1, 16 de 30 pasos (como en las pruebas de Landing).
        s.w(0x537ce8, '<h', P); s.w(0x4fb0ec, '<h', P); s.call(0x4a4f90, [])
        s.w(ARMY(STK), '<hh', *ini)
        f = s.u16(ARMY(STK) + 0x12); s.w(ARMY(STK) + 0x12, '<H', (f | 8) if embarcado else (f & ~8))
        s.w(GRP, '<h', STK); s.w(GRP + 4, '<h', STK); s.w(GRP + 0x14, '<hhh', 16, 30, 1)
        f = s.u16(GRP + 0x1a); s.w(GRP + 0x1a, '<H', (f | 8) if embarcado else (f & ~8)); s.w(GRP + 0x1c, '<h', 0)
    def mapa(s, ini, bonos=()):
        s.reset(bonos); s.grupo(ini)
        s.call(0x497750, [200])
        raw = s.rd(struct.unpack('<I', s.rd(0x587168 + P * 4, 4))[0], W * 0xa0 * 2)
        return {(x, y): struct.unpack_from('<h', raw, (x * 0xa0 + y) * 2)[0] for x in range(W) for y in range(H)}
    def camino(s, ini, dest, bonos=()):
        s.reset(bonos); s.grupo(ini)
        s.call(0x485e30, [P, dest[0], dest[1]])
        out = []
        for k in range(60):
            x, y = struct.unpack('<hh', s.rd(GRP + 0x34 + k * 4, 4))
            if x <= 0 and y <= 0: break
            out.append((x, y))
        return out

fallas = 0
def check(nombre, cond, detalle=''):
    global fallas
    print(('OK   ' if cond else 'FALLA'), nombre, detalle if not cond else '')
    fallas += not cond

nueva, prev = Maquina(NEW), Maquina(PREV)
m = nueva; m.reset(); m.call(0x4a4f90, [])
W, H = m.u16(0x503e00), m.u16(0x503e02)
med = lambda x, y: m.rd(0x582158 + x * 0xa0 + y, 1)[0]
LINK = m.rd(0x573158, W * 0xa0)
D640 = struct.unpack('<8h', m.rd(0x4fe640, 16)); D658 = struct.unpack('<8h', m.rd(0x4fe658, 16))
VEC = [(D658[k], D640[k]) for k in range(8)]
dentro = lambda x, y: 0 <= x < W and 0 <= y < H
def montana(x, y):
    sh = m.rd(0x503e06, 1)[0]
    t = struct.unpack('<H', m.rd(0x503e58 + ((y * 10) << sh) + x * 10, 2))[0] & 0x1f
    return m.u16(0x535f0c + t * 0x58) == 4 and not m.rd(0x57d158 + x * 0xa0 + y, 1)[0] & 0x30

# ---------------------------------------------------------------- mapa de distancias de la IA y caminos desde tierra
puertos = [(x, y) for x in range(W) for y in range(H) if med(x, y) == 0xc0]
inicios = [(px + dx, py + dy) for px, py in puertos for dx, dy in VEC
           if dentro(px + dx, py + dy) and med(px + dx, py + dy) == 0x40 and not montana(px + dx, py + dy)][::3]
check('hay inicios a pie junto a un puerto', len(inicios) >= 3, inicios)
mejores, con_dif = [], 0
for S in inicios:
    a0, b0 = nueva.mapa(S), prev.mapa(S)
    check(f'mapa desde {S}: sin bono, igual al anterior', a0 == b0)
    check(f'mapa desde {S}: "Landing" en otro bando, igual al anterior', nueva.mapa(S, [(0, 1, b'Landing')]) == b0)
    a, b = nueva.mapa(S, [LAND]), prev.mapa(S, [LAND])
    dif = [k for k in a if a[k] != b[k]]
    # más barato en tierra abarata los puertos que se alcanzan desde ahí, y con ellos el agua; nada se encarece ni se
    # pierde, y lo recién alcanzado es tierra (las playas)
    nuevas = [k for k in dif if b[k] == 0]
    malos = [(k, a[k], b[k], med(*k)) for k in dif if a[k] == 0 or (b[k] != 0 and a[k] > b[k])
             or (b[k] == 0 and med(*k) != 0x40)]
    check(f'mapa desde {S} con "Landing": {len(dif)} casillas más baratas '
          f'({sum(med(*k) == 0x40 for k in dif)} de tierra), {len(nuevas)} recién alcanzadas', not malos, malos[:5])
    con_dif += bool(dif)
    mejores += [(S, k) for k in sorted(nuevas)[:3]]

check(f'"Landing" cambia el mapa desde {con_dif} de {len(inicios)} inicios', con_dif >= 3)
def paso_ok(u, v):
    k = next(i for i, d in enumerate(VEC) if (u[0] + d[0], u[1] + d[1]) == v)
    return bool(LINK[u[0] * 0xa0 + u[1]] >> k & 1) or (med(*u) == 0x80 and med(*v) == 0x40 and not montana(*v))
malos, distintos = [], 0
for S, T in mejores:
    r = nueva.camino(S, T, [LAND]); o = prev.camino(S, T, [LAND])
    pasos = [S] + r
    if not r or r[-1] != T or not all(paso_ok(pasos[i], pasos[i + 1]) for i in range(len(r))):
        malos.append((S, T, r[:8]))
    distintos += r != o
    check(f'camino a pie {S}->{T} sin bono, igual al anterior', nueva.camino(S, T) == prev.camino(S, T))
check(f'caminos a pie con "Landing": {len(mejores)} destinos, todos llegan con pasos válidos', not malos, malos[:3])
check(f'  y {distintos} difieren del anterior (desembarco en playa)', distintos > 0)

# ---------------------------------------------------------------- movimiento de la IA (0x4c4a10)
u = Maquina(NEW)
def st_mover(args):
    code, hit = u.script.pop(0) if u.script else (1, 0)
    u.w(LCHIT, '<B', hit); u.log.append(('mover', args[0] & 0xffff, code, hit)); return code
def st_grupo(args):
    lst = struct.unpack('<8h', u.rd(args[0], 16)); u.log.append(('grupo', lst))
    c = [a for a in lst if a]; u.w(GRP + 4, '<8h', *(c + [0] * (8 - len(c)))); u.w(GRP + 0x18, '<h', len(c))
    u.w(GRP, '<h', c[0] if c else 0); return 1
def st_marco(args):
    u.log.append(('marco', struct.unpack('<8h', u.rd(args[0], 16)))); return 0
u.stub(0x49c4b0, st_mover)
u.stub(0x4b91e0, lambda a: u.log.append(('destino', a[0] & 0xffff, a[1] & 0xffff, a[2] & 0xffff)) or 0)
u.stub(0x497240, st_grupo)
u.stub(0x497860, lambda a: u.log.append(('sync', a[0] & 0xffff)) or 0)
u.stub(0x4c4da0, st_marco)
u.stub(0x4411b0, lambda a: u.log.append(('cuenta', a[0], a[1])) or u.ocupa)
for va, r in ((0x420a70, P), (0x440be0, -1), (0x427520, 0), (0x4c4eb0, 0), (0x4b9020, 0), (0x48d020, 0),
              (0x410220, 0), (0x4deb20, 1), (0xdeb00000, 0)):
    u.stub(va, lambda a, r=r: r)
u.mu.mem_map(0xdeb00000, 0x1000); u.mu.mem_write(0xdeb00000, b'\xc3')
# lchit: de la instrucción de landcap que lo escribe (el salto en 0x49e4a7 lleva a landcap)
import capstone, re
cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
LC = int(next(cs.disasm(u.rd(0x49e4a7, 5), 0x49e4a7)).op_str, 16)
LCHIT = next(int(re.search(r'\[(0x[0-9a-f]+)\]', i.op_str).group(1), 16)
             for i in cs.disasm(u.rd(LC, 0x100), LC) if i.op_str.endswith('], al'))
check('0x4c4bce llama a ai_move', next(cs.disasm(u.rd(0x4c4bce, 5), 0x4c4bce)).op_str != '0x49c4b0')

GR = list(range(100, 108))
def arma(i, xy, emb, dueno=P, tarea=3, bits=0x400, dest=None, vivo=True):
    a = ARMY(i); u.w(a, '<hh', *xy); u.w(a + 4, '<hh', *(dest or xy))
    u.w(a + 0xc, '<H', (u.u16(a + 0xc) & ~0x1ff) | dueno << 5)
    u.w(a + 0x11, '<B', (u.rd(a + 0x11, 1)[0] & ~0x40) | (0x40 if vivo else 0))
    f = u.u16(a + 0x12); u.w(a + 0x12, '<H', (f | 8) if emb else (f & ~8))
    u.w(a + 0x15, '<B', tarea); u.w(a + 0x19, '<B', 0)
    u.w(a + 0x1a, '<H', (u.u16(a + 0x1a) & 0xc3ff) | bits)
def armar(bonos, xy, n=8, humano=False, emb=False, script=()):
    u.reset(bonos); u.w(0x537ce8, '<h', P); u.w(0x4fb0ec, '<h', P); u.w(0x4fb0f0, '<h', 0); u.call(0x4a4f90, [])
    u.w(0x5a9bec, '<I', 0xdeb00000); u.w(0x53c393, '<B', 0); u.w(SIDE + 10, '<h', -1 if humano else 0)
    u.w(SIDE, '<h', 8); u.ocupa = 0
    for i in range(10): u.w(AIREC(i), '<H', 0)
    for i in GR[:n]: arma(i, xy, emb)
    u.w(AIREC(0), '<H', 1); u.w(AIREC(0) + 0xc, '<8h', *(GR[:n] + [0] * (8 - n)))
    u.w(AIREC(1), '<H', 1); u.w(AIREC(1) + 0xc, '<8h', 120, 121, GR[n - 1], 0, 0, 0, 0, 0)
    u.w(GRP, '<hh', GR[0], 0); u.w(GRP + 4, '<8h', *(GR[:n] + [0] * (8 - n))); u.w(GRP + 0x18, '<h', n)
    f = u.u16(GRP + 0x1a); u.w(GRP + 0x1a, '<H', (f | 8) if emb else (f & ~8)); u.w(GRP + 0x1c, '<h', 0)
    u.script = list(script); u.log = []
def mover(dest):
    REGS = {UC_X86_REG_EBX: 0x1111, UC_X86_REG_ESI: 0x2222, UC_X86_REG_EDI: 0x3333, UC_X86_REG_EBP: 0x4444}
    r = u.call(0x4c4a10, [dest[0], dest[1], 0], REGS) & 0xffff
    ok = all(u.mu.reg_read(k) == v for k, v in REGS.items()) and u.mu.reg_read(UC_X86_REG_ESP) == 0x10080000 - 12   # quedan los 3 argumentos
    return r, ok
tierra = inicios[0]
OBJ = mejores[0][1]
def ev(tag): return [e for e in u.log if e[0] == tag]
def libre(i):
    a = ARMY(i)
    return u.u16(a + 0x1a) & 0x3c00 == 0 and u.rd(a + 0x15, 1)[0] == 0 and u.s16(a + 4) == -1 and u.s16(a + 6) == -1
def en_pila(i): return [k for k in range(10) if u.u16(AIREC(k)) & 1 and i in struct.unpack('<8h', u.rd(AIREC(k) + 0xc, 16))]

# 1) "Landing": 8 a pie; el barco no alcanza dos veces (5 y 4 no entran), entran 3. Después, código 2 (0x4c4da0).
armar([LAND], tierra, script=[(5, 1), (5, 1), (5, 1), (2, 0)])
r, regs = mover(OBJ)
grupos = [e[1] for e in ev('grupo')]
check('Landing: el grupo se parte 5, 4 y 3', grupos == [tuple(GR[:5] + [0] * 3), tuple(GR[:4] + [0] * 4),
                                                          tuple(GR[:3] + [0] * 5)], grupos)
check('  4 movimientos y una orden de destino nueva por cada parte',
      len(ev('mover')) == 4 and ev('destino')[1:] == [('destino', P, *OBJ)] * 3, u.log)
check('  0x4c4da0 recibe la lista del grupo final', ev('marco') == [('marco', tuple(GR[:3] + [0] * 5))], ev('marco'))
check('  los 3 primeros que bajan forman una pila nueva de la IA (slot 2, líder 105)',
      u.u16(AIREC(2)) & 1 and struct.unpack('<8h', u.rd(AIREC(2) + 0xc, 16)) == (105, 106, 107, 0, 0, 0, 0, 0)
      and all(u.u16(ARMY(i) + 0x1a) & 0x3c00 == 0x400 for i in (105, 106, 107)))
check('  103 y 104 quedan libres y fuera de las pilas', all(libre(i) and not en_pila(i) for i in (103, 104)),
      [(i, en_pila(i)) for i in (103, 104)])
check('  107 sale de la otra pila (salvo que sea líder)', struct.unpack('<8h', u.rd(AIREC(1) + 0xc, 16))[:3] == (120, 121, 0))
check('  pila 0: quedan 100..102', struct.unpack('<8h', u.rd(AIREC(0) + 0xc, 16)) == (100, 101, 102, 0, 0, 0, 0, 0))
tras = u.log[u.log.index(ev('mover')[0]):]   # los sync de antes son del propio 0x4c4a10
check('  los que bajan se sincronizan', sorted(e[1] for e in tras if e[0] == 'sync') == [103, 104, 105, 106, 107], tras)
check('  registros y pila intactos (el código llega a la tabla de saltos: el 2 lleva a 0x4c4da0, arriba)', regs, (r, regs))

# 2) "Landing" + "Carrier": tope 6; entra al segundo intento
armar([LAND, CARR], tierra, script=[(5, 1), (1, 0)])
mover(OBJ)
check('Landing+Carrier: primero se queda con 6', [e[1] for e in ev('grupo')] == [tuple(GR[:6] + [0, 0])], u.log)
check('  los 2 que bajan forman pila', struct.unpack('<8h', u.rd(AIREC(2) + 0xc, 16))[:3] == (106, 107, 0))

# 3) el barco nunca alcanza: baja hasta el líder solo y termina
armar([LAND], tierra, script=[(5, 1)] * 10)
r, regs = mover(OBJ)
check('nunca alcanza: 5, 4, 3, 2, 1 y termina', [len([a for a in e[1] if a]) for e in ev('grupo')] == [5, 4, 3, 2, 1]
      and len(ev('mover')) == 6 and regs, (r, u.log))

# controles: nada se parte
for tag, kw, script in (('humano', dict(humano=True), [(5, 1)]), ('lchit 2', {}, [(5, 2)]), ('código 1', {}, [(1, 1)]),
                        ('código 4', {}, [(4, 1)]), ('grupo de 1', dict(n=1), [(5, 1)])):
    armar([LAND], tierra, script=script, **kw)
    antes = [en_pila(i) for i in GR]
    r, regs = mover(OBJ)
    check(f'control {tag}: no se parte', not ev('grupo') and len(ev('mover')) == 1 and [en_pila(i) for i in GR] == antes
          and regs, (r, regs, u.log))

# ---------------------------------------------------------------- convoyes (ai_conv)
agua = [(x, y) for x in range(W) for y in range(H) if med(x, y) == 0x80
        and all(dentro(x + dx, y + dy) and med(x + dx, y + dy) == 0x80 for dx, dy in VEC)]
cerca = lambda t: any(dentro(t[0] + i, t[1] + j) and med(t[0] + i, t[1] + j) == 0xc0 for i in range(-2, 3) for j in range(-2, 3))
L = next(a for a in agua if not cerca(a)); N = (L[0] + VEC[0][0], L[1] + VEC[0][1])
TP = puertos[0]                                 # destino con puerto a mano
TL = next(a for a in agua if not cerca(a) and max(abs(a[0] - L[0]), abs(a[1] - L[1])) > 6)   # sin puerto cerca
OTROS = range(110, 114)
def conv(bonos, T, emb=True, modo=0, ocupa=4, d=None, oemb=True, odueno=P, ovivo=True, n=3, links=0):
    armar(bonos, L, n=n, emb=emb, script=[(1, 0), (1, 0)])
    u.w(GRP + 0x1c, '<h', modo); u.ocupa = ocupa
    for i in GR[:n]: u.w(ARMY(i) + 0x19, '<B', links)
    for i in OTROS: arma(i, N, oemb, dueno=odueno, dest=d or T, vivo=ovivo)
    mover(T)
    return [e for e in u.log if e[0] in ('destino', 'mover')]
ORDEN = lambda T: [('destino', P, *T), ('destino', P, *N), ('mover', P, 1, 0), ('destino', P, *T), ('mover', P, 1, 0)]
NADA = lambda T: [('destino', P, *T), ('mover', P, 1, 0)]
print('convoy: grupo en', L, 'vecina', N, 'destinos', TP, TL)
r = conv([CARR], TL, ocupa=6)
check('Carrier: 3 + 6 no entran (tope 8): orden de ir a la vecina y destino repuesto', r == ORDEN(TL), r)
r = conv([CARR], TL, ocupa=5)
check('control Carrier: 3 + 5 entran: nada', r == NADA(TL), r)
r = conv([LAND, CARR], TP, ocupa=4)
check('Landing+Carrier, puerto junto al destino: 3 + 4 no entran (tope 6): orden', r == ORDEN(TP), r)
for tag, kw, T in (('sin Carrier', dict(bonos=[LAND]), TL),
                   ('Landing+Carrier sin puerto cerca del destino', dict(bonos=[LAND, CARR]), TL),
                   ('grupo a pie', dict(emb=False), TL), ('grupo volando', dict(modo=2), TL),
                   ('los otros van lejos', dict(d=(TL[0] + 3, TL[1])), TL), ('los otros no embarcados', dict(oemb=False), TL),
                   ('los otros de otro jugador', dict(odueno=(P + 1) % 8), TL), ('los otros muertos', dict(ovivo=False), TL)):
    kw = {'bonos': [CARR], 'ocupa': 6, **kw}
    r = conv(T=T, **kw)
    check(f'control {tag}: nada', r == NADA(T), r)
# grupo que ya está en un convoy: enlace válido con un barco propio en la casilla opuesta a N
M = (L[0] - VEC[0][0], L[1] - VEC[0][1])
cod = lambda dx, dy: dx + 4 * dy + 5
armar([CARR], L, n=3, emb=True)
r = conv([CARR], TL, ocupa=6, links=0x80 | cod(M[0] - L[0], M[1] - L[1]))
arma(130, M, True); u.w(ARMY(130) + 0x19, '<B', 0x80 | cod(L[0] - M[0], L[1] - M[1]))
for i in GR[:3]: u.w(ARMY(i) + 0x19, '<B', 0x80 | cod(M[0] - L[0], M[1] - L[1]))
u.log = []; u.script = [(1, 0), (1, 0)]; mover(TL)
r = [e for e in u.log if e[0] in ('destino', 'mover')]
check('control grupo ya en un convoy: nada', r == NADA(TL), r)

print('\nTODO OK' if not fallas else f'\n{fallas} FALLAS')
sys.exit(1 if fallas else 0)
