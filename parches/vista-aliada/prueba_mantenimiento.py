# Prueba emulada del evento 33 (mantenimiento fuera de ciudad, mt_evt; ia\PENDIENTE-ia-economia.md, paso 4.4).
# Sobre partidas guardadas, por color:
#   1. corre el 0x4406b0 original y comprueba que un modelo en Python del mismo recorrido da el mismo mantenimiento
#      (así el modelo de «dentro / fuera de ciudad» es el del juego);
#   2. corre 0x42244b..0x42249b en el exe parcheado y compara la línea del evento 33 con el modelo
#      (x = lo que pagan enteros los de fuera, y = el tercio que pagarían en una ciudad, n = cuántos son);
#   3. con un ejército movido a mano a una ciudad y fuera de toda ciudad; control sin ia_on: nada anotado.
#   4. evento 34 (paso 4.5): con ME_TAB cargada a mano (meta de la ronda, de la anterior, vieja o sin dato), el ahorro
#      (entero − tercio) por meta de los de fuera coincide con el modelo; y me_set (en 0x40cc3f) anota meta + 1 y la
#      ronda para los ejércitos de la pila y deja eax y [esp+0x10] como el original; sin ia_on también (1.0.218.0).
#   5. paso 4.6: el 34 también separa 11 (jugó sin meta) y 12 (lo decidió ai_ally); me_pre (en 0x40edf1) marca 11 con
#      la ronda en los ejércitos de la pila del jugador [0x4fb0ec] y sigue a ai_ord con la pila intacta; con jugador
#      >= 8 no marca; sin ia_on sí (1.0.218.0: ME_TAB la usa el repliegue en las partidas del ranking).
# Uso: python prueba_mantenimiento.py <DarklordAV.exe> <Darklord.exe> <ia_on hex> <ia_mode hex> <me_tab hex> <me_set hex>
#      <me_pre hex> <ai_ord hex> <partida.SAV> [...]
import pefile, struct, sys
from unicorn import *
from unicorn.x86_const import *

AV, ORIG, IA_ON, IA_MODE = sys.argv[1], sys.argv[2], int(sys.argv[3], 16), int(sys.argv[4], 16)
ME_TAB, ME_SET = int(sys.argv[5], 16), int(sys.argv[6], 16)
ME_PRE, AI_ORD = int(sys.argv[7], 16), int(sys.argv[8], 16)
SAVS = sys.argv[9:]
imgs = {k: pefile.PE(f).get_memory_mapped_image() for k, f in (('av', AV), ('orig', ORIG))}
IAT = {'fopen': 0x5a9bdc, 'fclose': 0x5a9be4, 'fprintf': 0x5a9bf4}
STUB, RET = 0xdeac0000, 0x42249b


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


def wr(m, va, data):
    for base, d in m.items():
        if base <= va < base + len(d): d[va - base:va - base + len(data)] = data; return
    raise KeyError(hex(va))


def h(m, va): return struct.unpack('<h', rd(m, va, 2))[0]


def ejercitos(m):
    for i in range(h(m, 0x54fe50)):
        e = 0x54fe50 + i * 0x1c
        if not rd(m, e + 0x13, 1)[0] & 0x40: continue
        o = h(m, e + 0xe) & 0x1e0
        if o >= 0x100: continue
        x, y = h(m, e + 2), h(m, e + 4)
        if x < 0 or y < 0: continue
        mt = (h(m, e + 0x10) & 0xf0) >> 4
        if rd(m, e + 0x14, 1)[0] & 8 and mt <= 4: mt = 4
        t = ((y * 10) << rd(m, 0x503e06, 1)[0]) + x * 10 + 0x503e58
        ciudad = (h(m, t + 2) & 0x700) == 0x300 and rd(m, t + 9, 1)[0] & 3
        yield i, o >> 5, mt, bool(ciudad), bool(rd(m, e + 0xd, 1)[0] & 1)


def modelo(m, p):
    total = fx = fy = fn = 0
    for _, o, mt, ciudad, b0 in ejercitos(m):
        if o != p: continue
        total += max(1, mt // 3) if ciudad and mt > 0 and not b0 else mt
        if mt > 0 and not ciudad: fx += mt; fy += max(1, mt // 3); fn += 1
    return total, [fx, fy, fn]


def me_de(i):
    # (meta, ronda) cargada en ME_TAB para el ejército i, o None
    k = i % 4
    return None if k == 0 else (i % 13, {1: 7, 2: 6, 3: 5}[k])


def grupos(m, p):
    # ejércitos en los grupos activos de la IA del color p (0x561f00 + 1178·p, 10 de 64 bytes, bit 0 = activo)
    g = set()
    for k in range(10):
        b = 0x561f00 + 1178 * p + 64 * k
        if h(m, b) & 1: g |= {struct.unpack('<H', rd(m, b + 0xc + 2 * j, 2))[0] for j in range(8)}
    return g


def modelo34(m, p):
    r = {}
    for i, o, mt, ciudad, _ in ejercitos(m):
        if o != p or mt == 0 or ciudad: continue
        d = me_de(i); c = d[0] if d and d[1] in (6, 7) else 10
        if not (d and d[1] in (6, 7)) and i not in grupos(m, p): c = 13
        a = r.setdefault(c, [0, 0]); a[0] += mt - max(1, mt // 3); a[1] += 1
    return [[34, c] + r[c] for c in sorted(r)]


def maquina(img, m):
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(0x400000, (len(img) + 0xfff) & ~0xfff); mu.mem_write(0x400000, img)
    mu.mem_map(0x10000000, 0x100000); mu.mem_map(STUB, 0x1000)
    for va, d in m.items(): mu.mem_write(va, bytes(d))
    return mu


def original_4406b0(m):
    mu = maquina(imgs['orig'], m); sp = 0x10080000
    mu.mem_map(0xdead0000, 0x1000)
    mu.mem_write(sp, struct.pack('<I', 0xdead0000)); mu.reg_write(UC_X86_REG_ESP, sp)
    mu.emu_start(0x4406b0, 0xdead0000, count=2_000_000)
    return [struct.unpack('<h', mu.mem_read(0x5643d8 + 2 * p, 2))[0] for p in range(8)]


def corrida(m, p, on):
    mu = maquina(imgs['av'], m)
    mu.mem_write(0x503328, struct.pack('<h', 7))
    mu.mem_write(0x5643f0 + 2 * p, struct.pack('<h', 100)); mu.mem_write(0x5643d8 + 2 * p, struct.pack('<h', 20))
    mu.mem_write(IA_ON, bytes([on, 0, 0, 0])); mu.mem_write(IA_MODE, bytes([1] * 8))
    for i in range(h(m, 0x54fe50)):
        d = me_de(i)
        if d: mu.mem_write(ME_TAB + 2 * i, bytes([d[0] + 1, d[1]]))
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

    def sim(mu, addr, size, _):
        esp = mu.reg_read(UC_X86_REG_ESP); r = struct.unpack('<I', mu.mem_read(esp, 4))[0]
        mu.reg_write(UC_X86_REG_ESP, esp + 4); mu.reg_write(UC_X86_REG_EIP, r)
    for a in (0x415a00, 0x4b9390): mu.hook_add(UC_HOOK_CODE, sim, begin=a, end=a)
    sp = 0x10080000
    frame = bytearray(0x40); struct.pack_into('<I', frame, 0x14, p); struct.pack_into('<I', frame, 0x1c, p * 0x1f8)
    mu.mem_write(sp, bytes(frame))
    regs = {UC_X86_REG_EBX: 0x11110000, UC_X86_REG_ESI: 0x11110001, UC_X86_REG_EBP: 0x11110002, UC_X86_REG_EDI: p}
    for r, v in regs.items(): mu.reg_write(r, v)
    mu.reg_write(UC_X86_REG_ESP, sp)
    mu.emu_start(0x42244b, RET, count=2_000_000)
    pres = all(mu.reg_read(r) == v for r, v in regs.items()) and mu.reg_read(UC_X86_REG_ESP) == sp - 8
    return [l[3:] for l in lines if l[3] == 33], pres, [l[3:] for l in lines if l[3] == 34]


ok = True; nctl = 0


def check(c, msg):
    global ok, nctl; nctl += 1
    if not c: print('    FALLA', msg)
    ok &= c


for sav in SAVS:
    m = load(sav); ej = list(ejercitos(m))
    print(sav, f'({len(ej)} ejércitos vivos, {sum(1 for e in ej if e[3])} en casilla de ciudad)')
    orig = original_4406b0(m)
    for p in range(8):
        tot, esp = modelo(m, p)
        check(tot == orig[p], f'color {p}: modelo {tot} = 0x4406b0 original {orig[p]}')
        l, pres, l34 = corrida(m, p, 1)
        check(l == [[33] + esp] and pres, f'color {p}: evento 33 {l} = modelo {esp}')
        e34 = [[a[0], a[1], a[2], a[3]] for a in modelo34(m, p)]
        check(l34 == e34, f'color {p}: evento 34 {l34} = modelo {e34}')
        check(sum(a[2] for a in l34) == esp[0] - esp[1] and sum(a[3] for a in l34) == esp[2],
              f'color {p}: el 34 suma lo mismo que el 33')
        print(f'  color {p}: mantenimiento {orig[p]}; fuera de ciudad {esp[2]} ejércitos que pagan {esp[0]} '
              f'(en una ciudad pagarían {esp[1]})')
        l, pres, *_ = corrida(m, p, 0)
        check(l == [] and pres, f'color {p}, sin ia_on: nada anotado')
    # paso 4.7: un huérfano (13) puesto a mano en un grupo activo (el 10.º del color) pasa a 10
    for p in range(8):
        hu = [i for i, o, mt, c, _ in ej if o == p and mt and not c and i not in grupos(m, p)
              and not (me_de(i) and me_de(i)[1] in (6, 7))][:1]
        if not hu: continue
        m2 = {k: bytearray(v) for k, v in m.items()}; b = 0x561f00 + 1178 * p + 64 * 9
        wr(m2, b, struct.pack('<H', h(m2, b) | 1)); wr(m2, b + 0xc, struct.pack('<8h', hu[0], 0, 0, 0, 0, 0, 0, 0))
        _, _, l34 = corrida(m2, p, 1); e34 = modelo34(m2, p)
        check(l34 == e34 and hu[0] in grupos(m2, p) and e34 != modelo34(m, p),
              f'color {p}: ejército {hu[0]} metido en un grupo deja de ser 13: {l34} = modelo {e34}')
    # un ejército movido a mano: a la casilla de un ejército que está en ciudad, y a una casilla fuera de toda ciudad
    en_ciudad = [e for e in ej if e[3]]
    fuera = [e for e in ej if not e[3]]
    cand = [e for e in ej if e[2] >= 3 and not e[4]][:4]
    for i, o, mt, _, _ in cand:
        e = 0x54fe50 + i * 0x1c
        for destino, ref in (('ciudad', en_ciudad), ('fuera', fuera)):
            if not ref: continue
            r = 0x54fe50 + ref[0][0] * 0x1c
            m2 = {k: bytearray(v) for k, v in m.items()}
            wr(m2, e + 2, rd(m, r + 2, 4))
            dentro = [x for x in ejercitos(m2) if x[0] == i][0][3]
            check((destino == 'ciudad') == dentro, f'ejército {i} quedó {"en" if dentro else "fuera de"} ciudad')
            tot, esp = modelo(m2, o); l, pres, *_ = corrida(m2, o, 1)
            check(tot == original_4406b0(m2)[o] and l == [[33] + esp] and pres,
                  f'ejército {i} (color {o}, mantenimiento {mt}) {destino}: {l} = modelo {esp}')
# me_set: pila falsa con ejércitos 3, 0 (vacío), -1, 5000 (fuera de tabla), 17; meta 7 en [esp+0x1a] del llamador
for on in (1, 0):
    for meta in (0, 1, 7, 9):
        mu = maquina(imgs['av'], load(SAVS[0]))
        mu.mem_write(IA_ON, bytes([on, 0, 0, 0])); mu.mem_write(0x503328, struct.pack('<h', 12))
        rec = 0x10040000; mu.mem_write(rec + 0xc, struct.pack('<8h', 3, 0, -1, 5000, 17, 0, 0, 0))
        mu.mem_write(0x5020d4, struct.pack('<I', rec))
        sp = 0x10080000; fr = bytearray(0x40); struct.pack_into('<h', fr, 0x1e, meta); struct.pack_into('<H', fr, 0x14, 0xbeef)
        mu.mem_write(sp, bytes(fr)); mu.mem_write(sp, struct.pack('<I', 0xdead0000)); mu.mem_map(0xdead0000, 0x1000)
        mu.reg_write(UC_X86_REG_ESP, sp); mu.reg_write(UC_X86_REG_EBX, 0x1234)
        mu.emu_start(ME_SET, 0xdead0000, count=10000)
        tab = struct.unpack('<4096H', mu.mem_read(ME_TAB, 8192))
        want = (meta + 1) | (12 << 8)   # también sin ia_on desde 1.0.218.0: ME_TAB la usa el repliegue del ranking
        check(tab[3] == want and tab[17] == want and sum(1 for t in tab if t) == 2,
              f'me_set ia_on={on} meta {meta}: tabla {tab[3]:#x} {tab[17]:#x}')
        check(mu.reg_read(UC_X86_REG_EAX) == meta and struct.unpack('<H', mu.mem_read(sp + 0x14, 2))[0] == 0
              and mu.reg_read(UC_X86_REG_EBX) == 0x1234 and mu.reg_read(UC_X86_REG_ESP) == sp + 4,
              f'me_set ia_on={on} meta {meta}: eax y [esp+0x10] como el original')
# me_pre: jugador 3, pila 2 con ejércitos 4, 0, -2, 5000, 21; luego va a ai_ord con la pila igual
for on, jug in ((1, 3), (0, 3), (1, 8)):
    mu = maquina(imgs['av'], load(SAVS[0]))
    mu.mem_write(IA_ON, bytes([on, 0, 0, 0])); mu.mem_write(0x503328, struct.pack('<h', 9))
    mu.mem_write(0x4fb0ec, struct.pack('<h', jug))
    rec = 0x561f00 + 3 * 0x49a + 2 * 0x40; mu.mem_write(rec + 0xc, struct.pack('<8h', 4, 0, -2, 5000, 21, 0, 0, 0))
    mu.mem_write(ME_TAB, bytes(8192))
    sp = 0x10080000; mu.mem_write(sp, struct.pack('<III', 0xdead0000, 2, 0))
    mu.reg_write(UC_X86_REG_ESP, sp); mu.reg_write(UC_X86_REG_EBX, 0x1234)
    mu.emu_start(ME_PRE, AI_ORD, count=10000)
    tab = struct.unpack('<4096H', mu.mem_read(ME_TAB, 8192))
    want = 12 | (9 << 8) if jug < 8 else 0   # también sin ia_on desde 1.0.218.0
    check(mu.reg_read(UC_X86_REG_EIP) == AI_ORD and mu.reg_read(UC_X86_REG_ESP) == sp
          and mu.mem_read(sp, 12) == struct.pack('<III', 0xdead0000, 2, 0) and mu.reg_read(UC_X86_REG_EBX) == 0x1234,
          f'me_pre ia_on={on} jugador {jug}: sigue a ai_ord con la pila intacta')
    check(tab[4] == want and tab[21] == want and sum(1 for t in tab if t) == (2 if want else 0),
          f'me_pre ia_on={on} jugador {jug}: tabla {tab[4]:#x} {tab[21]:#x}')
print(f'{nctl} controles:', 'TODO OK' if ok else 'HAY FALLAS'); sys.exit(0 if ok else 1)
