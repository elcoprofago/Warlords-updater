# Prueba del bono de movimiento "Cabotage" (cabgraph, cabfwd/cabbwd) y del desembarco "Landing" (livexp/livback) sobre
# el exe parcheado, en unicorn, con el buscador de caminos real (0x485e30) y la partida Aliados03 (jugador 2, ejército
# 17, como en las pruebas de Landing).
# Uso: python prueba_cabotaje.py [DarklordAV.exe] [Darklord.exe] [partida.SAV]
#      (por defecto los de C:\Warlords3 y Saves\Aliados03.SAV; armar antes con build.py)
# Esperado:
#  - la tabla de distancias a tierra (CABD) es la de un recorrido en anchura independiente, en todo el mapa, y el
#    armado del grafo (0x4a4f90) vuelve con los registros que preserva intactos;
#  - sin "Cabotage" en ningún barco (controles), los caminos son los del exe original;
#  - con "Cabotage" en el barco del jugador 2, para varios orígenes y todos los destinos de agua conocidos: hay camino
#    si y solo si el original lo encuentra y un modelo propio de la regla (no entrar en agua pura a más de 2 casillas
#    de tierra, salvo acercándose a la costa) lo alcanza; y cada paso del camino cumple la regla;
#  - el bono en otro bando, o mal escrito, no cambia nada; un grupo a pie que sube al barco en un puerto también
#    queda limitado;
#  - "Landing": desde agua se desembarca en un paso hacia la tierra vecina en las 8 direcciones (salvo montaña sin
#    camino), y solo hacia tierra.
import sys, struct, re, collections, pefile, capstone
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

NEW = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe'
OLD = sys.argv[2] if len(sys.argv) > 2 else r'C:\Warlords3\Darklord.exe'
sav = open(sys.argv[3] if len(sys.argv) > 3 else r'C:\Warlords3\Saves\Aliados03.SAV', 'rb').read()
P, STK = 2, 17
REC = lambda p: 0x53c410 + (p * 16 + 15) * 0xfc      # registro del barco (ranura 15) del bando p
GRP = 0x56ea90 + P * 0x4f0
ARMY = lambda i: 0x54fe52 + i * 0x1c
DATA = (0x4f9000, 0xb0000)                            # .data entera: se restaura entre casos

class Maquina:
    # El exe cargado una vez, con la partida encima; cada caso parte de la misma memoria de datos.
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
    def imports(s):
        # Cada importación va a un stub; se emulan las de memoria (GlobalAlloc y compañía), las demás no se esperan.
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
    def reset(s, bonos=()):
        s.mu.mem_write(DATA[0], s.data); s.heap = 0x30000000
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
    def w(s, a, fmt, *v): s.mu.mem_write(a, struct.pack(fmt, *v))
    def camino(s, ini, dest, embarcado=True, bonos=()):
        # Como en las pruebas de Landing: el ejército 17 del jugador 2 solo en ini, grupo de 1, 16 de 30 pasos.
        s.reset(bonos)
        s.w(0x537ce8, '<h', P); s.call(0x4a4f90, [])
        s.w(ARMY(STK), '<hh', *ini)
        f = s.u16(ARMY(STK) + 0x12); s.w(ARMY(STK) + 0x12, '<H', (f | 8) if embarcado else (f & ~8))
        s.w(GRP, '<h', STK); s.w(GRP + 4, '<h', STK)
        s.w(GRP + 0x14, '<hhh', 16, 30, 1)
        f = s.u16(GRP + 0x1a); s.w(GRP + 0x1a, '<H', (f | 8) if embarcado else (f & ~8))
        r = s.call(0x485e30, [P, dest[0], dest[1]]) & 0xffff
        out = []
        for k in range(60):
            x, y = struct.unpack('<hh', s.rd(GRP + 0x34 + k * 4, 4))
            if x <= 0 and y <= 0: break
            out.append((x, y))
        return r, out

nueva, orig = Maquina(NEW), Maquina(OLD)
m = nueva; m.reset(); m.call(0x4a4f90, [])
W, H = m.u16(0x503e00), m.u16(0x503e02)
med = lambda x, y: m.rd(0x582158 + x * 0xa0 + y, 1)[0]
conocida = lambda x, y: m.rd(0x503e5c + ((y * 10) << m.rd(0x503e06, 1)[0]) + x * 10, 1)[0] >> P & 1
D640 = struct.unpack('<8h', m.rd(0x4fe640, 16)); D658 = struct.unpack('<8h', m.rd(0x4fe658, 16))
VEC = [(D658[k], D640[k]) for k in range(8)]        # vecina k de (x, y): (x + D658[k], y + D640[k])

fallas = 0
def check(nombre, cond, detalle=''):
    global fallas
    print(('OK   ' if cond else 'FALLA'), nombre, detalle if not cond else '')
    fallas += not cond

# ---------------------------------------------------------------- tabla de distancias (CABD)
# Su dirección sale del primer "mov byte ptr [ecx + CABD], al" de cabgraph (destino del salto en 0x4a5328).
cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
salto = next(cs.disasm(m.rd(0x4a5328, 5), 0x4a5328))
check('0x4a5328 salta a cabgraph', salto.mnemonic == 'jmp', salto.mnemonic)
CG = int(salto.op_str, 16)
CABD = next(int(re.search(r'ecx \+ (0x[0-9a-f]+)', i.op_str).group(1), 16) for i in cs.disasm(m.rd(CG, 0x40), CG)
            if i.mnemonic == 'mov' and i.op_str.startswith('byte ptr [ecx +') and i.op_str.endswith('al'))
ref = [[254] * H for _ in range(W)]; q = collections.deque()
for x in range(W):
    for y in range(H):
        if med(x, y) & 0x40: ref[x][y] = 0; q.append((x, y))
while q:
    x, y = q.popleft()
    for dx, dy in VEC:
        nx, ny = x + dx, y + dy
        if 0 <= nx < W and 0 <= ny < H and ref[nx][ny] > ref[x][y] + 1: ref[nx][ny] = ref[x][y] + 1; q.append((nx, ny))
D = m.rd(CABD, 0x5000)
dif = [(x, y) for x in range(W) for y in range(H) if D[x * 0xa0 + y] != min(ref[x][y], 254)]
check('CABD = distancia a tierra de referencia en todo el mapa', not dif, dif[:5])
check('el mapa tiene agua a más de 2 casillas de tierra', any(ref[x][y] > 2 for x in range(W) for y in range(H)))
REGS = {UC_X86_REG_EBX: 0x1111, UC_X86_REG_ESI: 0x2222, UC_X86_REG_EDI: 0x3333, UC_X86_REG_EBP: 0x4444}
m.reset(); m.call(0x4a4f90, [], REGS)
check('0x4a4f90 preserva ebx, esi, edi, ebp y la pila',
      all(m.mu.reg_read(r) == v for r, v in REGS.items()) and m.mu.reg_read(UC_X86_REG_ESP) == 0x10080000)

# ---------------------------------------------------------------- caminos
def permitido(a, b):
    i, j = a[0] * 0xa0 + a[1], b[0] * 0xa0 + b[1]
    return not (med(*b) == 0x80 and D[j] > 2 and D[j] >= D[i])
def alcance(s, cab):
    # Sin filtrar por lo explorado: con [0x5878b4] = 0 el pathfinder atraviesa casillas desconocidas.
    vistos = {s}; q = collections.deque([s])
    while q:
        a = q.popleft(); L = m.rd(0x573158 + a[0] * 0xa0 + a[1], 1)[0]
        for k in range(8):
            n = (a[0] + VEC[k][0], a[1] + VEC[k][1])
            if L >> k & 1 and n not in vistos and (not cab or permitido(a, n)):
                vistos.add(n); q.append(n)
    return vistos
CAB = [(P, 1, b'Cabotage')]
agua = [(x, y) for x in range(W) for y in range(H) if med(x, y) == 0x80 and conocida(x, y)]
lejos = [a for a in agua if D[a[0] * 0xa0 + a[1]] > 2]
check(f'el jugador {P} conoce agua a más de 2 casillas de tierra', len(lejos) > 10, len(lejos))

# controles: sin el bono, lo mismo que el original
CTRL = [((18, 39), (25, 44)), ((44, 9), (45, 5)), ((45, 5), (44, 9)), ((44, 9), (56, 9)), ((18, 39), (17, 37))]
for ini, dest in CTRL:
    o = orig.camino(ini, dest)
    check(f'sin bono {ini}->{dest} = original', nueva.camino(ini, dest) == o, o)
    for bonos, tag in (([(0, 1, b'Cabotage')], 'bono en otro bando'), ([(P, 1, b'Cabotagex')], '"Cabotagex"'),
                       ([(P, 1, b'cabotag')], '"cabotag"')):
        check(f'{tag} {ini}->{dest} = original', nueva.camino(ini, dest, bonos=bonos) == o)

# masivo: cada origen contra todos los destinos de agua conocidos
for ini in ((18, 39), (44, 9), (45, 5), (47, 7), (58, 21)):
    R1 = alcance(ini, True); malos = []; n = {}
    for dest in agua:
        if dest == ini: continue
        o = orig.camino(ini, dest)[1]; r = nueva.camino(ini, dest, bonos=CAB)[1]
        pasos = [ini] + r
        bien = bool(r) == (bool(o) and dest in R1) and all(permitido(pasos[i], pasos[i + 1]) for i in range(len(r)))
        n[bool(o), bool(r)] = n.get((bool(o), bool(r)), 0) + 1
        if not bien: malos.append((dest, bool(o), dest in R1, r[:6]))
    check(f'Cabotage desde {ini} (D={D[ini[0] * 0xa0 + ini[1]]}): {len(agua) - 1} destinos, (original, cabotaje) = {n}',
          not malos, malos[:4])
    check(f'  y alguno queda cortado', n.get((True, False), 0) > 0 or ini == (18, 39))

# mayúsculas y ranura 4
for bonos in ([(P, 3, b'CABOTAGE')], [(P, 0, b'cabotage')]):
    r = nueva.camino((44, 9), (45, 5), bonos=bonos)
    check(f'{bonos[0][2]} en la ranura {bonos[0][1] + 1} corta (44,9)->(45,5)', r[1] == [], r)

# un grupo a pie que sube al barco en un puerto: el tramo de agua también queda limitado
puertos = [(x, y) for x in range(W) for y in range(H) if med(x, y) == 0xc0 and conocida(x, y)]
casos = 0
for px, py in puertos:
    tierra = [(px + dx, py + dy) for dx, dy in VEC if med(px + dx, py + dy) == 0x40 and conocida(px + dx, py + dy)]
    R = alcance((px, py), True)
    cerca = [a for a in agua if a in R and abs(a[0] - px) + abs(a[1] - py) < 8]
    mar = [a for a in lejos if a not in R and abs(a[0] - px) + abs(a[1] - py) < 12]
    if not tierra or not cerca or not mar: continue
    for dest, debe in ((cerca[-1], True), (mar[0], False)):
        o = orig.camino(tierra[0], dest, embarcado=False); r = nueva.camino(tierra[0], dest, embarcado=False, bonos=CAB)
        if not o[1]: continue
        casos += 1
        check(f'a pie {tierra[0]} por el puerto {(px, py)} a {dest}: {"llega" if debe else "no llega"}',
              bool(r[1]) == debe, (o, r))
check('hubo casos de grupo a pie por un puerto', casos >= 2, casos)

# ---------------------------------------------------------------- Landing en las 8 direcciones
def montana(x, y):
    sh = m.rd(0x503e06, 1)[0]
    t = struct.unpack('<H', m.rd(0x503e58 + ((y * 10) << sh) + x * 10, 2))[0] & 0x1f
    return m.u16(0x535f0c + t * 0x58) == 4 and not m.rd(0x57d158 + x * 0xa0 + y, 1)[0] & 0x30
LAND = [(P, 1, b'Landing')]
por_dir = collections.Counter(); malos = []
for x, y in agua:
    for k, (dx, dy) in enumerate(VEC):
        t = (x + dx, y + dy)
        if not (0 <= t[0] < W and 0 <= t[1] < H) or not conocida(*t): continue
        if med(*t) != 0x40 or montana(*t): continue
        if not m.rd(0x578158 + x * 0xa0 + y, 1)[0] >> k & 1: continue
        r = nueva.camino((x, y), t, bonos=LAND)
        if r[1] == [t]: por_dir[k] += 1
        else: malos.append(((x, y), t, r[1][:4]))
check(f'Landing: desembarco en 1 paso hacia tierra vecina, por dirección {dict(sorted(por_dir.items()))}',
      not malos and len(por_dir) == 8, malos[:5])
# y solo hacia tierra: un camino de agua a agua vecina no cambia con Landing
dif = [(a, t) for a in agua[::7] for t in [(a[0] + 1, a[1])] if t in agua
       and nueva.camino(a, t, bonos=LAND) != orig.camino(a, t)]
check('Landing: de agua a agua vecina, igual que el original', not dif, dif[:5])

print('\nTODO OK' if not fallas else f'\n{fallas} FALLAS')
sys.exit(1 if fallas else 0)
