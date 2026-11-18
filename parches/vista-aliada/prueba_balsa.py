# Prueba del bono de movimiento "Raft" (balsa: livexp/livback con raftchk, cabfilt con RAFT_N, landchk) sobre el exe
# parcheado, en unicorn, con el buscador de caminos real (0x485e30) y una partida con agua.
# Uso: python prueba_balsa.py [DarklordAV.exe] [Darklord.exe] [partida.SAV] [jugador] [ejército]
#      (por defecto los de E:\Warlords-TEST\Warlords3, Saves\agua03.SAV y el jugador 0; armar antes con build.py)
# Esperado:
#  - controles: sin "Raft", con "Raft" en otro bando o mal escrito, nadie zarpa en un paso desde la costa;
#  - zarpar: desde cada casilla de tierra no montañosa (ni puerto) junto a agua pura, un grupo a pie llega a la casilla
#    de agua vecina en un solo paso, en las 8 direcciones; desde montaña sin camino, no (salvo grupo que cruza montañas);
#  - desembarcar: desde agua pura se llega a la tierra vecina en un paso (como con "Landing");
#  - distancia: ningún camino con "Raft" pasa por agua pura a más de 1 casilla de tierra, salvo acercándose; y hay
#    destinos que el original alcanzaba y la balsa no;
#  - "Raft" manda sobre "Cabotage" escrito en el mismo barco (tope 1, no 2).
import os as _os, sys as _sys; _sys.path.append(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..'))  # para encontrar juego_pruebas.py
from juego_pruebas import W3  # carpeta del juego de pruebas: se cambia solo ahi
import sys, struct, collections, random, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

NEW = sys.argv[1] if len(sys.argv) > 1 else W3 + r'\DarklordAV.exe'
OLD = sys.argv[2] if len(sys.argv) > 2 else W3 + r'\Darklord.exe'
sav = open(sys.argv[3] if len(sys.argv) > 3 else W3 + r'\Saves\agua03.SAV', 'rb').read()
P = int(sys.argv[4]) if len(sys.argv) > 4 else 0
REC = lambda p: 0x53c410 + (p * 16 + 15) * 0xfc
GRP = 0x56ea90 + P * 0x4f0
ARMY = lambda i: 0x54fe52 + i * 0x1c
DATA = (0x4f9000, 0xb0000)

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
    def reset(s, bonos=()):
        s.mu.mem_write(DATA[0], s.data); s.heap = 0x30000000
        for q in range(8):                                  # barcos sin bonos de movimiento: solo los del caso
            s.mu.mem_write(REC(q) + 0xb2, bytes(36))
        for q, ranura, txt in bonos:
            s.mu.mem_write(REC(q) + 0xb2 + ranura * 9, txt.ljust(9, b'\0'))
    def call(s, addr, args):
        mu = s.mu; sp = 0x10080000
        for a in reversed(args): sp -= 4; mu.mem_write(sp, struct.pack('<i', a))
        sp -= 4; mu.mem_write(sp, struct.pack('<I', 0xdead0000)); mu.reg_write(UC_X86_REG_ESP, sp)
        mu.emu_start(addr, 0xdead0000, count=50_000_000)
        return mu.reg_read(UC_X86_REG_EAX)
    def rd(s, a, n): return bytes(s.mu.mem_read(a, n))
    def u16(s, a): return struct.unpack('<H', s.rd(a, 2))[0]
    def w(s, a, fmt, *v): s.mu.mem_write(a, struct.pack(fmt, *v))
    def camino(s, ini, dest, embarcado, bonos=()):
        s.reset(bonos)
        s.w(0x537ce8, '<h', P); s.call(0x4a4f90, [])
        s.w(0x5878b4, '<h', 0)
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
m = nueva; m.reset()
STK = int(sys.argv[5]) if len(sys.argv) > 5 else 1
m.call(0x4a4f90, [])
W, H = m.u16(0x503e00), m.u16(0x503e02)
med = lambda x, y: m.rd(0x582158 + x * 0xa0 + y, 1)[0]
vale = lambda x, y, k: m.rd(0x578158 + x * 0xa0 + y, 1)[0] >> k & 1
D640 = struct.unpack('<8h', m.rd(0x4fe640, 16)); D658 = struct.unpack('<8h', m.rd(0x4fe658, 16))
VEC = [(D658[k], D640[k]) for k in range(8)]
def montana(x, y):
    sh = m.rd(0x503e06, 1)[0]
    t = struct.unpack('<H', m.rd(0x503e58 + ((y * 10) << sh) + x * 10, 2))[0] & 0x1f
    return m.u16(0x535f0c + t * 0x58) == 4 and not m.rd(0x57d158 + x * 0xa0 + y, 1)[0] & 0x30
dist = [[254] * H for _ in range(W)]; q = collections.deque()
for x in range(W):
    for y in range(H):
        if med(x, y) & 0x40: dist[x][y] = 0; q.append((x, y))
while q:
    x, y = q.popleft()
    for dx, dy in VEC:
        nx, ny = x + dx, y + dy
        if 0 <= nx < W and 0 <= ny < H and dist[nx][ny] > dist[x][y] + 1: dist[nx][ny] = dist[x][y] + 1; q.append((nx, ny))

fallas = 0
def check(nombre, cond, detalle=''):
    global fallas
    print(('OK   ' if cond else 'FALLA'), nombre, detalle if not cond else '')
    fallas += not cond

print(f'mapa {W}x{H}, jugador {P}, ejército {STK}')
RAFT = [(P, 2, b'Raft')]
agua = [(x, y) for x in range(W) for y in range(H) if med(x, y) == 0x80]
costa = []      # (tierra, k, agua vecina)
for x in range(W):
    for y in range(H):
        if med(x, y) != 0x40: continue
        for k, (dx, dy) in enumerate(VEC):
            t = (x + dx, y + dy)
            if 0 <= t[0] < W and 0 <= t[1] < H and vale(x, y, k) and med(*t) == 0x80: costa.append(((x, y), k, t))
check('el mapa tiene costa y agua a más de 1 casilla de tierra',
      len(costa) > 20 and any(dist[x][y] > 1 for x, y in agua), (len(costa), len(agua)))
random.seed(7)

# ---------------------------------------------------------------- controles
muestra = random.sample(costa, min(25, len(costa)))
for bonos, tag in (((), 'sin bono'), ([(P ^ 1, 2, b'Raft')], 'bono en otro bando'), ([(P, 2, b'Raftx')], '"Raftx"'),
                   ([(P, 2, b'raf')], '"raf"')):
    dif = [(a, t) for a, k, t in muestra if nueva.camino(a, t, False, bonos)[1] == [t]]
    check(f'control {tag}: no zarpa en 1 paso desde la costa', not dif, dif[:3])

# ---------------------------------------------------------------- zarpar en las 8 direcciones
por_dir = collections.Counter(); malos = []; mont = []
sel = [c for k in range(8) for c in random.sample([c for c in costa if c[1] == k], min(15, sum(c[1] == k for c in costa)))]
sel += [c for c in costa if montana(*c[0]) and not m.rd(0x57d158 + c[2][0] * 0xa0 + c[2][1], 1)[0]][:40]   # agua sin camino
for a, k, t in sel:
    r = nueva.camino(a, t, False, RAFT)
    if montana(*a) and not nueva.rd(0x4fe688, 1)[0]:     # 0x4fe688: el grupo cruza montañas
        mont.append((a, t, r[1][:1]))
        continue
    if r[1] == [t]: por_dir[k] += 1
    else: malos.append((a, t, r[1][:4]))
check(f'zarpa en 1 paso desde {sum(por_dir.values())} costas, por dirección {dict(sorted(por_dir.items()))}',
      not malos and len(por_dir) == 8, malos[:5])
mont = [(a, t, r) for a, t, r in mont if orig.camino(a, t, False)[1] != [t]]   # agua con camino (puente): ya en el original
check(f'desde montaña sin camino no zarpa en 1 paso ({len(mont)} casos)', all(r != [t] for a, t, r in mont), mont[:3])
for bonos, tag in (([(P, 0, b'RAFT')], 'RAFT en la ranura 1'), ([(P, 3, b'raft')], 'raft en la ranura 4')):
    a, k, t = muestra[0]
    check(f'{tag}: zarpa', nueva.camino(a, t, False, bonos)[1] == [t])

# ---------------------------------------------------------------- desembarcar
malos = []; n = 0
for a, k, t in random.sample(costa, min(60, len(costa))):
    if montana(*a): continue
    n += 1
    r = nueva.camino(t, a, True, RAFT)
    if r[1] != [a]: malos.append((t, a, r[1][:4]))
check(f'desembarca en 1 paso ({n} casos)', not malos, malos[:5])

# ---------------------------------------------------------------- distancia a tierra
def permitido(a, b, N):
    return not (med(*b) == 0x80 and dist[b[0]][b[1]] > N and dist[b[0]][b[1]] >= dist[a[0]][a[1]])
for bonos, tag in ((RAFT, 'Raft'), ([(P, 0, b'Cabotage'), (P, 2, b'Raft')], 'Raft + Cabotage')):
    malos = []; cortados = 0; n = 0
    for a, k, t in random.sample(costa, min(5, len(costa))):
        if montana(*a): continue
        for dest in random.sample(agua, min(20, len(agua))):
            r = nueva.camino(a, dest, False, bonos)[1]; o = orig.camino(a, dest, False)[1]
            pasos = [a] + r; n += 1
            if r and not all(permitido(pasos[i], pasos[i + 1], 1) for i in range(len(r))): malos.append((a, dest, r[:8]))
            # (un destino lejano o inalcanzable da un camino parcial: el juego lo corta; no es falla)
            if o and not r: cortados += 1
            if dist[dest[0]][dest[1]] > 1 and r: malos.append((a, dest, 'llega lejos de la costa'))
    check(f'{tag}: {n} caminos, ninguno se aleja más de 1 casilla de tierra', not malos, malos[:4])
    check(f'{tag}: hay destinos que el original alcanza y la balsa no ({cortados})', cortados > 0)

print('\nTODO OK' if not fallas else f'\n{fallas} FALLAS')
sys.exit(1 if fallas else 0)
