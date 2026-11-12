# Prueba emulada del paso 4.8 (ia\PENDIENTE-ia-economia.md): or_run arma grupos de la IA con los huérfanos.
# Sobre partidas guardadas, por color:
#   1. modelo en Python: huérfano = ejército vivo de p, no héroe, fuera de una casilla de ciudad y en ningún grupo
#      activo de p (0x561f00 + 1178·p, 10 de 64 bytes, bit 0 = activo, lista de 8 en +0xc). Por orden de índice, cada
#      huérfano sin grupo arma uno con los huérfanos de su casilla (hasta 8, él de líder) mientras haya menos de
#      OR_MAX grupos activos; el grupo va al primer lugar libre.
#   2. corre or_run en el exe parcheado (ia_on, IA_MODE[p] = 1, [0x4fb0ec] = p, bando de la computadora) y compara
#      los grupos nuevos (lugar, activo, líder, lista), el bit 0x400 en +0x1a de cada miembro y el evento 35 con el
#      modelo; los grupos que ya existían y los de los otros colores quedan iguales.
#   3. controles sin cambio: sin ia_on, IA_MODE[p] = 0, jugador >= 8 y bando humano (0x536c12 = -1).
#   4. con OR_MAX - 1 grupos ocupados a mano: arma uno solo (llega a OR_MAX).
#   5. (paso 4.13) cada ejército agrupado queda en ME_TAB con RP_HU (15) y la ronda; el resto de ME_TAB, en 0.
# Uso: python prueba_huerfanos.py <DarklordAV.exe> <ia_on hex> <ia_mode hex> <or_run hex> <me_tab hex> <partida.SAV> [...]
import pefile, struct, sys
from unicorn import *
from unicorn.x86_const import *

AV, IA_ON, IA_MODE, OR_RUN = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3], 16), int(sys.argv[4], 16)
ME_TAB = int(sys.argv[5], 16)
SAVS = sys.argv[6:]
RONDA, RP_HU, ME_N = 12, 15, 4096
OR_MAX = 4
img = pefile.PE(AV).get_memory_mapped_image()
IAT = {'fopen': 0x5a9bdc, 'fclose': 0x5a9be4, 'fprintf': 0x5a9bf4, 'sprintf': 0x5a9bec, 'time': 0x5a9b88}
STUB, END = 0xdeac0000, 0xdead0000
G0 = 0x561f00


def load(sav):
    b = open(sav, 'rb').read(); m = {}; off = 0x6d
    for va, n in ((0x503e00, 0x12), (0x503e58, 0x32000), (0x535ed0, 0xa96), (0x536b30, 0x2d894)):
        m[va] = bytearray(b[off:off + n]); off += n
    return m


def rd(m, va, n):
    for base, d in m.items():
        if base <= va < base + len(d): return bytes(d[va - base:va - base + n])
    raise KeyError(hex(va))


def wr(m, va, data):
    for base, d in m.items():
        if base <= va < base + len(d): d[va - base:va - base + len(data)] = data; return
    raise KeyError(hex(va))


def h(m, va): return struct.unpack('<h', rd(m, va, 2))[0]


def grp(m, p, k): return G0 + 1178 * p + 64 * k


def activos(m, p): return [k for k in range(10) if h(m, grp(m, p, k)) & 1]


def en_grupo(m, p):
    g = set()
    for k in activos(m, p):
        g |= {struct.unpack('<H', rd(m, grp(m, p, k) + 0xc + 2 * j, 2))[0] for j in range(8)}
    return g


def casilla(m, i, p, g):
    e = 0x54fe50 + i * 0x1c
    if not rd(m, e + 0x13, 1)[0] & 0x40: return None
    t = h(m, e + 0xe)
    if t & 0x1f == 0x10 or (t & 0x1e0) >> 5 != p: return None
    x, y = h(m, e + 2), h(m, e + 4)
    if x < 0 or y < 0: return None
    c = ((y * 10) << rd(m, 0x503e06, 1)[0]) + x * 10 + 0x503e58
    if (h(m, c + 2) & 0x700) == 0x300 and rd(m, c + 9, 1)[0] & 3: return None
    if i in g: return None
    return (x, y)


def modelo(m, p):
    g = en_grupo(m, p); libres = [k for k in range(10) if k not in activos(m, p)]
    n_act = 10 - len(libres); hechos = []; quedan = 0
    nej = h(m, 0x54fe50)
    for i in range(nej):
        c = casilla(m, i, p, g)
        if c is None: continue
        if n_act >= OR_MAX or not libres: quedan += 1; continue
        lista = [i] + [j for j in range(i + 1, nej) if casilla(m, j, p, g) == c][:7]
        g |= set(lista); hechos.append((libres.pop(0), lista)); n_act += 1
    return hechos, quedan


def corrida(m, p, on=1, modo=1, jug=None, humano=False):
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(0x400000, (len(img) + 0xfff) & ~0xfff); mu.mem_write(0x400000, img)
    mu.mem_map(0x10000000, 0x100000); mu.mem_map(STUB, 0x1000); mu.mem_map(END, 0x1000)
    for va, d in m.items(): mu.mem_write(va, bytes(d))
    mu.mem_write(0x4fb0ec, struct.pack('<h', p if jug is None else jug))
    mu.mem_write(0x536c12 + p * 0x1f8, struct.pack('<h', -1 if humano else 2))
    mu.mem_write(IA_ON, bytes([on, 0, 0, 0])); mu.mem_write(IA_MODE, bytes([modo] * 8))
    mu.mem_write(0x503328, struct.pack('<h', RONDA))
    mu.mem_write(0x427520, b'\xc3')                       # registro del juego: no hace falta
    for a in range(0x5a9b00, 0x5a9d00, 4): mu.mem_write(a, struct.pack('<I', STUB + 0x800))   # resto de la CRT
    mu.mem_write(STUB + 0x800, bytes([0xc3]))
    names = list(IAT)
    for k, n in enumerate(names):
        mu.mem_write(IAT[n], struct.pack('<I', STUB + k * 16)); mu.mem_write(STUB + k * 16, b'\xc3')
    lines = []

    def arg(i): return struct.unpack('<I', mu.mem_read(mu.reg_read(UC_X86_REG_ESP) + 4 + 4 * i, 4))[0]

    def iat(mu, addr, size, _):
        n = names[(addr - STUB) // 16]; ret = 0
        if n == 'fopen': ret = 0x1000
        elif n == 'fprintf': lines.append([struct.unpack('<i', struct.pack('<I', arg(k)))[0] for k in range(2, 9)])
        mu.reg_write(UC_X86_REG_EAX, ret)
    mu.hook_add(UC_HOOK_CODE, iat, begin=STUB, end=STUB + 0x7ff)
    sp = 0x10080000
    mu.mem_write(sp, struct.pack('<I', END)); mu.reg_write(UC_X86_REG_ESP, sp)
    regs = [UC_X86_REG_EBX, UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP, UC_X86_REG_ECX, UC_X86_REG_EDX]
    for k, r in enumerate(regs): mu.reg_write(r, 0x11110000 + k)
    mu.emu_start(OR_RUN, END, count=20_000_000)
    intactos = all(mu.reg_read(r) == 0x11110000 + k for k, r in enumerate(regs)) and \
        mu.reg_read(UC_X86_REG_ESP) == sp + 4
    gm = bytes(mu.mem_read(G0, 0x5643c4 - G0))
    flags = {i: struct.unpack('<H', mu.mem_read(0x54fe50 + i * 0x1c + 0x1c, 2))[0] for i in range(h(m, 0x54fe50))}
    corrida.tab = struct.unpack(f'<{ME_N}H', mu.mem_read(ME_TAB, 2 * ME_N))
    return gm, flags, lines, intactos


fallas = ctl = 0


def ok(c, msg):
    global fallas, ctl
    ctl += 1
    if not c: fallas += 1; print('  FALLA', msg)


for sav in SAVS:
    m = load(sav); base = rd(m, G0, 0x5643c4 - G0)
    print(sav.split('\\')[-1].split('/')[-1])
    for p in range(8):
        hechos, quedan = modelo(m, p)
        gm, flags, lines, intactos = corrida(m, p)
        ok(intactos, f'p{p}: registros o pila cambiados')
        ok([l[1:] for l in lines] == [[p, 1, 35, len(hechos), sum(len(l) for _, l in hechos), quedan]],
           f'p{p}: evento 35 {lines} != {len(hechos)}, {quedan}')
        nuevos = {k for k, _ in hechos}
        for q in range(8):
            for k in range(10):
                a = G0 + 1178 * q + 64 * k - G0
                if q == p and k in nuevos: continue
                ok(gm[a:a + 64] == base[a:a + 64], f'p{p}: grupo {q}/{k} cambió')
        for k, lista in hechos:
            a = 1178 * p + 64 * k
            ok(gm[a] & 1 and not gm[a] & 0x10, f'p{p}: grupo {k} no activo o ya jugado')
            got = list(struct.unpack('<8H', gm[a + 0xc:a + 0x1c]))
            ok(got == lista + [0] * (8 - len(lista)), f'p{p}: grupo {k} {got} != {lista}')
            for i in lista[1:]: ok(flags[i] & 0x3c00 == 0x400, f'p{p}: ejército {i} sin bit de pila')
        marcados = {i for _, l in hechos for i in l if 0 < i < ME_N}
        tab = corrida.tab
        ok(all(tab[i] == (RP_HU | RONDA << 8 if i in marcados else 0) for i in range(ME_N)),
           f'p{p}: ME_TAB {[(i, hex(tab[i])) for i in range(ME_N) if tab[i]][:10]} != {sorted(marcados)[:10]}')
        if hechos:
            print(f'  color {p}: {len(hechos)} grupos, {sum(len(l) for _, l in hechos)} ejércitos, quedan {quedan}')
        for nombre, kw in (('sin ia_on', dict(on=0)), ('IA_MODE 0', dict(modo=0)), ('jugador 8', dict(jug=8)),
                           ('humano', dict(humano=True))):
            gm, _, lines, intactos = corrida(m, p, **kw)
            ok(not any(corrida.tab), f'p{p}: control {nombre} marcó ME_TAB')
            ok(gm == base and intactos and (lines == [] or nombre != 'sin ia_on') and
               all(l[3] != 35 for l in lines), f'p{p}: control {nombre} cambió algo {gm == base} {intactos} {lines}')
    # OR_MAX - 1 grupos ocupados a mano en el color con más huérfanos: solo uno nuevo
    p = max(range(8), key=lambda q: len(modelo(m, q)[0]))
    if modelo(m, p)[0]:
        m2 = {k: bytearray(v) for k, v in m.items()}
        libres = [k for k in range(10) if k not in activos(m2, p)]
        for k in libres[:max(0, OR_MAX - 1 - len(activos(m2, p)))]:
            a = grp(m2, p, k); wr(m2, a, struct.pack('<H', h(m2, a) | 1)); wr(m2, a + 0xc, bytes(16))
        hechos, quedan = modelo(m2, p)
        _, _, lines, _ = corrida(m2, p)
        ok(len(hechos) == 1 and lines[0][4] == 1, f'tope: {len(hechos)} grupos, evento {lines}')
print('controles', ctl, 'TODO OK' if not fallas else f'{fallas} FALLAS')
sys.exit(1 if fallas else 0)
