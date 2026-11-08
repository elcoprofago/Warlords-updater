# Prueba emulada del evento 33 (mantenimiento fuera de ciudad, mt_evt; ia\PENDIENTE-ia-economia.md, paso 4.4).
# Sobre partidas guardadas, por color:
#   1. corre el 0x4406b0 original y comprueba que un modelo en Python del mismo recorrido da el mismo mantenimiento
#      (así el modelo de «dentro / fuera de ciudad» es el del juego);
#   2. corre 0x42244b..0x42249b en el exe parcheado y compara la línea del evento 33 con el modelo
#      (x = lo que pagan enteros los de fuera, y = el tercio que pagarían en una ciudad, n = cuántos son);
#   3. con un ejército movido a mano a una ciudad y fuera de toda ciudad; control sin ia_on: nada anotado.
# Uso: python prueba_mantenimiento.py <DarklordAV.exe> <Darklord.exe> <ia_on hex> <ia_mode hex> <partida.SAV> [...]
import pefile, struct, sys
from unicorn import *
from unicorn.x86_const import *

AV, ORIG, IA_ON, IA_MODE = sys.argv[1], sys.argv[2], int(sys.argv[3], 16), int(sys.argv[4], 16)
SAVS = sys.argv[5:]
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
    return [l[3:] for l in lines if l[3] == 33], pres


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
        l, pres = corrida(m, p, 1)
        check(l == [[33] + esp] and pres, f'color {p}: evento 33 {l} = modelo {esp}')
        print(f'  color {p}: mantenimiento {orig[p]}; fuera de ciudad {esp[2]} ejércitos que pagan {esp[0]} '
              f'(en una ciudad pagarían {esp[1]})')
        l, pres = corrida(m, p, 0)
        check(l == [] and pres, f'color {p}, sin ia_on: nada anotado')
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
            tot, esp = modelo(m2, o); l, pres = corrida(m2, o, 1)
            check(tot == original_4406b0(m2)[o] and l == [[33] + esp] and pres,
                  f'ejército {i} (color {o}, mantenimiento {mt}) {destino}: {l} = modelo {esp}')
print(f'{nctl} controles:', 'TODO OK' if ok else 'HAY FALLAS'); sys.exit(0 if ok else 1)
