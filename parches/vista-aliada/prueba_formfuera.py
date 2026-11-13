# Prueba emulada del evento 39 (pilas con meta Form que terminan el turno fuera de ciudad; fm_end/fm_evt;
# ia\PENDIENTE-ia-economia.md, paso 4.14). Sobre partidas guardadas, por color:
#   1. con ME_TAB cargada a mano (Form de esta ronda, Form de la ronda anterior, otra meta, sin dato) y FM_DST con
#      ciudades propias vivas y ajenas, fm_end (en 0x40ea9a, con 0x40eab0 simulado) anota una línea 39 por casilla fuera
#      de ciudad con algún ejército Form de esta ronda, igual que un modelo en Python: x = ciudad (+1000 si no es viva
#      de p), y = distancia (0x4974a0, modelada), n = ejércitos de p en la casilla × 100000 + movimiento total
#      × 1000 + movimiento que le quedó, del de índice menor con Form;
#   2. controles: sin ia_on, con jugador >= 8 y con toda la Form de la ronda anterior no anota nada; los ejércitos Form
#      en casilla de ciudad no anotan; fm_end vuelve al llamador con la pila y ebx, esi, edi, ebp intactos;
#   3. me_set copia [esp+0x42] (ciudad de la Form) a FM_DST solo cuando la meta final es Form.
# Uso: python prueba_formfuera.py <DarklordAV.exe> <ia_on> <me_tab> <fm_dst> <fm_end> <me_set> <SAV>...
import math, pefile, struct, sys
from unicorn import *
from unicorn.x86_const import *

AV = sys.argv[1]
IA_ON, ME_TAB, FM_DST, FM_END, ME_SET = (int(a, 16) for a in sys.argv[2:7])
SAVS = sys.argv[7:]
img = pefile.PE(AV).get_memory_mapped_image()
IAT = {'fopen': 0x5a9bdc, 'fclose': 0x5a9be4, 'fprintf': 0x5a9bf4}
STUB, FIN = 0xdeac0000, 0xdead0000
RONDA = 9


def cstr(mu, a):
    s = b''
    while (c := mu.mem_read(a + len(s), 1)[0]): s += bytes([c])
    return s.decode('latin1')


def load(sav):
    b = open(sav, 'rb').read(); m = {}; off = 0x6d
    for va, n in ((0x503e00, 0x12), (0x503e58, 0x32000), (0x535ed0, 0xa96), (0x536b30, 0x2d894)):
        m[va] = bytearray(b[off:off + n]); off += n
    return m


def rd(m, va, n):
    for base, d in m.items():
        if base <= va < base + len(d): return bytes(d[va - base:va - base + n])
    raise KeyError(hex(va))


def h(m, va): return struct.unpack('<h', rd(m, va, 2))[0]


def ejercitos(m):
    # (índice, dueño, x, y, en casilla de ciudad, movimiento total, que le queda), como fm_same0
    for i in range(min(h(m, 0x54fe50), 4096)):
        e = 0x54fe50 + i * 0x1c
        if not rd(m, e + 0x13, 1)[0] & 0x40: continue
        o = (h(m, e + 0xe) & 0x1e0) >> 5
        x, y = h(m, e + 2), h(m, e + 4)
        if x < 0 or y < 0: continue
        t = ((y * 10) << rd(m, 0x503e06, 1)[0]) + x * 10 + 0x503e58
        ciudad = (h(m, t + 2) & 0x700) == 0x300 and rd(m, t + 9, 1)[0] & 3
        yield i, o, x, y, bool(ciudad), rd(m, e + 0x12, 1)[0] & 0x7f, rd(m, e + 0x11, 1)[0] & 0x7f


def ciudades(m):
    n = h(m, 0x537e2a)
    return [(c, h(m, 0x537e2c + c * 0xde), h(m, 0x537e2e + c * 0xde), rd(m, 0x537ed0 + c * 0xde, 1)[0],
             rd(m, 0x537ed1 + c * 0xde, 1)[0]) for c in range(n)]


def maquina(m):
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(0x400000, (len(img) + 0xfff) & ~0xfff); mu.mem_write(0x400000, img)
    mu.mem_map(0x10000000, 0x100000); mu.mem_map(STUB, 0x1000); mu.mem_map(FIN, 0x1000)
    for va, d in m.items(): mu.mem_write(va, bytes(d))
    mu.mem_write(0x503328, struct.pack('<h', RONDA))
    return mu


def distancia(ax, ay, cx, cy):
    # 0x4974a0 original: raíz de dx² + dy² con _ftol (trunca; la DLL de C no está en la emulación, se reemplaza)
    return int(math.sqrt((ax - cx) ** 2 + (ay - cy) ** 2))


def dist_hook(mu, addr, size, _):
    esp = mu.reg_read(UC_X86_REG_ESP)
    r, *a = struct.unpack('<Iiiii', mu.mem_read(esp, 20))
    a = [struct.unpack('<h', struct.pack('<H', v & 0xffff))[0] for v in a]
    mu.reg_write(UC_X86_REG_EAX, distancia(*a))
    mu.reg_write(UC_X86_REG_ECX, 0xbad0bad0); mu.reg_write(UC_X86_REG_EDX, 0xbad1bad1)   # cdecl: los pisa
    mu.reg_write(UC_X86_REG_ESP, esp + 4); mu.reg_write(UC_X86_REG_EIP, r)


def carga(m, p):
    # ME_TAB y FM_DST de prueba: según i % 5, Form de esta ronda (0, 1), Form de la anterior (2), meta 7 de esta
    # ronda (3), sin dato (4). Ciudad: alternando una viva de p, una ajena (o muerta) y -1.
    cs = ciudades(m)
    propias = [c[0] for c in cs if c[3] and c[4] == p] or [0]
    ajenas = [c[0] for c in cs if not (c[3] and c[4] == p)] or [0]
    me, fd = {}, {}
    for i, o, *_ in ejercitos(m):
        k = i % 5
        if k in (0, 1): me[i] = 2 | (RONDA << 8)
        elif k == 2: me[i] = 2 | ((RONDA - 1) << 8)
        elif k == 3: me[i] = 8 | (RONDA << 8)
        j = i // 5
        fd[i] = (propias[j % len(propias)], ajenas[j % len(ajenas)], -1)[j % 3]
    return me, fd


def modelo(m, p, me, fd):
    cs = {c[0]: c for c in ciudades(m)}
    ej = [e for e in ejercitos(m) if e[1] == p and not e[4]]
    out = []
    vistos = set()
    for i, o, x, y, _, tot, resto in ej:
        if me.get(i) != 2 | (RONDA << 8) or (x, y) in vistos: continue
        vistos.add((x, y))
        n = sum(1 for e in ej if (e[2], e[3]) == (x, y))
        c = fd[i]; d = -1
        if 0 <= c < len(cs):
            d = distancia(x, y, cs[c][1], cs[c][2])
            if not (cs[c][3] and cs[c][4] == p): c += 1000
        out.append([39, c, d, n * 100000 + tot * 1000 + resto])
    return out


def corrida(m, p, on, me, fd, jug=None):
    mu = maquina(m)
    mu.mem_write(IA_ON, bytes([on, 0, 0, 0]))
    mu.mem_write(0x4fb0ec, struct.pack('<h', p if jug is None else jug))
    for i, v in me.items(): mu.mem_write(ME_TAB + 2 * i, struct.pack('<H', v))
    for i, v in fd.items(): mu.mem_write(FM_DST + 2 * i, struct.pack('<h', v))
    names = list(IAT)
    for k, n in enumerate(names):
        mu.mem_write(IAT[n], struct.pack('<I', STUB + k * 16)); mu.mem_write(STUB + k * 16, b'\xc3')
    lines = []

    def arg(i): return struct.unpack('<I', mu.mem_read(mu.reg_read(UC_X86_REG_ESP) + 4 + 4 * i, 4))[0]

    def iat(mu, addr, size, _):
        n = names[(addr - STUB) // 16]; ret = 0
        if n == 'fopen': ret = 0x1000
        elif n == 'fprintf':
            fmt = cstr(mu, arg(1))
            lines.append([struct.unpack('<i', struct.pack('<I', arg(2 + i)))[0] for i in range(fmt.count('%d'))])
        mu.reg_write(UC_X86_REG_EAX, ret)
    mu.hook_add(UC_HOOK_CODE, iat, begin=STUB, end=STUB + 0xfff)
    jugo = []

    def sim(mu, addr, size, _):
        jugo.append(1)
        esp = mu.reg_read(UC_X86_REG_ESP); r = struct.unpack('<I', mu.mem_read(esp, 4))[0]
        mu.reg_write(UC_X86_REG_ESP, esp + 4); mu.reg_write(UC_X86_REG_EIP, r)
    mu.hook_add(UC_HOOK_CODE, sim, begin=0x40eab0, end=0x40eab0)
    mu.hook_add(UC_HOOK_CODE, dist_hook, begin=0x4974a0, end=0x4974a0)
    sp = 0x10080000; mu.mem_write(sp, struct.pack('<II', FIN, 0x5555))
    regs = {UC_X86_REG_EBX: 0x11110000, UC_X86_REG_ESI: 0x11110001, UC_X86_REG_EBP: 0x11110002,
            UC_X86_REG_EDI: 0x11110003}
    for r, v in regs.items(): mu.reg_write(r, v)
    mu.reg_write(UC_X86_REG_ESP, sp)
    mu.emu_start(FM_END, FIN, count=50_000_000)
    pres = (all(mu.reg_read(r) == v for r, v in regs.items()) and mu.reg_read(UC_X86_REG_ESP) == sp + 4
            and mu.mem_read(sp + 4, 4) == struct.pack('<I', 0x5555) and jugo == [1])
    return [l[3:] for l in lines], pres


ok = True; nctl = 0


def check(c, msg):
    global ok, nctl; nctl += 1
    if not c: print('    FALLA', msg)
    ok &= c


# el parche está en 0x40ea9a
check(img[0x40ea9a - 0x400000] == 0xe8 and
      0x40ea9f + struct.unpack('<i', img[0x40ea9b - 0x400000:0x40ea9f - 0x400000])[0] == FM_END,
      'call fm_end en 0x40ea9a')
for sav in SAVS:
    m = load(sav); ej = list(ejercitos(m))
    print(sav, f'({len(ej)} ejércitos vivos)')
    for p in range(8):
        me, fd = carga(m, p)
        esp = modelo(m, p, me, fd)
        l, pres = corrida(m, p, 1, me, fd)
        check(l == esp and pres, f'color {p}: evento 39 {l[:4]}... = modelo {esp[:4]}... ({len(l)} / {len(esp)})')
        if esp:
            print(f'  color {p}: {len(esp)} casillas Form fuera de ciudad; p. ej. {esp[0][1:]}')
        l, pres = corrida(m, p, 0, me, fd)
        check(l == [] and pres, f'color {p}, sin ia_on: nada anotado')
        l, pres = corrida(m, p, 1, me, fd, jug=8)
        check(l == [] and pres, f'color {p}, jugador 8: nada anotado')
        vieja = {i: (v & 0xff) | ((RONDA - 1) << 8) for i, v in me.items()}
        l, pres = corrida(m, p, 1, vieja, fd)
        check(l == [] and pres, f'color {p}, Form de la ronda anterior: nada anotado')
    # ejércitos Form en casilla de ciudad: ninguno anota
    for p in range(8):
        dentro = {e[0]: 2 | (RONDA << 8) for e in ej if e[1] == p and e[4]}
        if not dentro: continue
        l, pres = corrida(m, p, 1, dentro, {i: 0 for i in dentro})
        check(l == [] and pres, f'color {p}: {len(dentro)} ejércitos Form en ciudad, nada anotado')
# me_set: [esp+0x1e] del llamador = meta, [esp+0x22] = ciudad; pila falsa con ejércitos 3 y 17
for meta in (1, 3, 7):
    mu = maquina(load(SAVS[0]))
    mu.mem_write(IA_ON, bytes([1, 0, 0, 0])); mu.mem_write(0x4fb0ec, struct.pack('<h', 8))
    rec = 0x10040000; mu.mem_write(rec + 0xc, struct.pack('<8h', 3, 17, 0, 0, 0, 0, 0, 0))
    mu.mem_write(0x5020d4, struct.pack('<I', rec))
    sp = 0x10080000; fr = bytearray(0x40); struct.pack_into('<h', fr, 0x1e, meta); struct.pack_into('<h', fr, 0x22, 42)
    struct.pack_into('<I', fr, 0, FIN); mu.mem_write(sp, bytes(fr)); mu.reg_write(UC_X86_REG_ESP, sp)
    mu.emu_start(ME_SET, FIN, count=10000)
    d = struct.unpack('<4096h', mu.mem_read(FM_DST, 8192))
    want = 42 if meta == 1 else 0
    check(d[3] == want and d[17] == want and sum(1 for t in d if t) == (2 if want else 0),
          f'me_set meta {meta}: FM_DST {d[3]} {d[17]}')
print(f'{nctl} controles:', 'TODO OK' if ok else 'HAY FALLAS'); sys.exit(0 if ok else 1)
