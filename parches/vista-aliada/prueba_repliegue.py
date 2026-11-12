# Prueba emulada del repliegue por quiebra (me_set, paso 4.12 de ia\PENDIENTE-ia-economia.md).
# Sobre partidas guardadas, para cada color con ciudades propias y un ejército no héroe fuera de toda ciudad:
#   - con ia_on, IA_MODE 1, bando de la computadora, mantenimiento > ingreso y oro < RP_TURNS × déficit, las metas
#     2, 3, 4 y 6 pasan a 1 (Form) con destino la ciudad propia viva más cercana al líder (0x4974a0 se reemplaza
#     en la emulación por su equivalente en Python, raíz truncada, porque usa _ftol de la DLL de C; en empate, la
#     primera); evento 37 = (meta original, ciudad, oro);
#     ME_TAB anota la meta nueva; eax = meta nueva, [esp+0x10] = 0, ebx y esp como el original;
#   - controles (meta y destino intactos, sin evento 37): metas 0, 1, 5, 7, 8, 9; oro justo en el límite; sin
#     déficit; IA_MODE 0; sin ia_on; jugador 8; bando humano; líder héroe; color sin ciudades propias.
# Uso: python prueba_repliegue.py <DarklordAV.exe> <Darklord.exe> <ia_on> <ia_mode> <me_tab> <me_set> <SAV>...
import math, pefile, struct, sys
from unicorn import *
from unicorn.x86_const import *

AV, ORIG = sys.argv[1], sys.argv[2]
IA_ON, IA_MODE, ME_TAB, ME_SET = (int(a, 16) for a in sys.argv[3:7])
SAVS = sys.argv[7:]
RP_TURNS = 8
imgs = {k: pefile.PE(f).get_memory_mapped_image() for k, f in (('av', AV), ('orig', ORIG))}
IAT = {'fopen': 0x5a9bdc, 'fclose': 0x5a9be4, 'fprintf': 0x5a9bf4}
STUB, END = 0xdeac0000, 0xdead0000


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


def maquina(img, m):
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(0x400000, (len(img) + 0xfff) & ~0xfff); mu.mem_write(0x400000, img)
    mu.mem_map(0x10000000, 0x100000); mu.mem_map(STUB, 0x1000); mu.mem_map(END, 0x1000)
    for va, d in m.items(): mu.mem_write(va, bytes(d))
    return mu


def dist(m, x1, y1, x2, y2):
    # 0x4974a0 original: raíz de dx² + dy² con _ftol (trunca; la DLL de C no está en la emulación). El caso «menor
    # que [0x4f5350] = 0,0 → 10000» no se da nunca con una suma de cuadrados.
    return int(math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2))


def dist_hook(mu, addr, size, _):
    esp = mu.reg_read(UC_X86_REG_ESP)
    a = struct.unpack('<Iiiii', mu.mem_read(esp, 20))
    s = lambda v: struct.unpack('<h', struct.pack('<H', v & 0xffff))[0]
    mu.reg_write(UC_X86_REG_EAX, dist(None, s(a[1]), s(a[2]), s(a[3]), s(a[4])))
    mu.reg_write(UC_X86_REG_ESP, esp + 4); mu.reg_write(UC_X86_REG_EIP, a[0])


def ciudades(m):
    for c in range(h(m, 0x537e2a)):
        b = c * 0xde
        yield c, rd(m, 0x537ed0 + b, 1)[0], rd(m, 0x537ed1 + b, 1)[0], h(m, 0x537e2c + b), h(m, 0x537e2e + b)


def modelo_ciudad(m, p, x, y):
    best, bd = -1, 0x7fffffff
    for c, viva, o, cx, cy in ciudades(m):
        if not viva or o != p: continue
        d = dist(m, x, y, cx, cy)
        if d < bd: best, bd = c, d
    return best


def corrida(m, p, lider, meta, mant, ing, oro, on=1, mode=1, jug=None, humano=False):
    mu = maquina(imgs['av'], m)
    mu.mem_write(IA_ON, bytes([on, 0, 0, 0])); mu.mem_write(IA_MODE, bytes([mode] * 8))
    mu.mem_write(0x4fb0ec, struct.pack('<h', p if jug is None else jug))
    mu.mem_write(0x503328, struct.pack('<h', 12))
    mu.mem_write(0x5643d8 + 2 * p, struct.pack('<h', mant)); mu.mem_write(0x5643f0 + 2 * p, struct.pack('<h', ing))
    mu.mem_write(0x536c14 + p * 0x1f8, struct.pack('<h', oro))
    mu.mem_write(0x536c12 + p * 0x1f8, struct.pack('<h', -1 if humano else 0))
    rec = 0x10040000; mu.mem_write(rec + 0xc, struct.pack('<8h', lider, 0, 0, 0, 0, 0, 0, 0))
    mu.mem_write(0x5020d4, struct.pack('<I', rec))
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
    mu.hook_add(UC_HOOK_CODE, dist_hook, begin=0x4974a0, end=0x4974a0)
    sp = 0x10080000; fr = bytearray(0x40)
    struct.pack_into('<h', fr, 0x1e, meta); struct.pack_into('<h', fr, 0x22, 777); struct.pack_into('<H', fr, 0x14, 0xbeef)
    mu.mem_write(sp, bytes(fr)); mu.mem_write(sp, struct.pack('<I', END))
    mu.reg_write(UC_X86_REG_ESP, sp); mu.reg_write(UC_X86_REG_EBX, 0x1234)
    mu.emu_start(ME_SET, END, count=200000)
    nm, dest = struct.unpack('<hh', mu.mem_read(sp + 0x1e, 4) + b'')[0], struct.unpack('<h', mu.mem_read(sp + 0x22, 2))[0]
    tab = struct.unpack('<H', mu.mem_read(ME_TAB + 2 * lider, 2))[0]
    orig_ok = (mu.reg_read(UC_X86_REG_EAX) == nm and struct.unpack('<H', mu.mem_read(sp + 0x14, 2))[0] == 0
               and mu.reg_read(UC_X86_REG_EBX) == 0x1234 and mu.reg_read(UC_X86_REG_ESP) == sp + 4)
    ev = [l[3:] for l in lines if len(l) > 3 and l[3] == 37]
    return nm, dest, tab, orig_ok, ev, lines


ok = True; nctl = 0


def check(c, msg):
    global ok, nctl; nctl += 1
    if not c: print('    FALLA', msg)
    ok &= c


probados = 0
for sav in SAVS:
    m = load(sav)
    print(sav)
    for p in range(8):
        propias = [c for c, viva, o, *_ in ciudades(m) if viva and o == p]
        ej = []; heroes = []
        for i in range(1, h(m, 0x54fe50)):
            e = 0x54fe50 + i * 0x1c
            if not rd(m, e + 0x13, 1)[0] & 0x40: continue
            t = h(m, e + 0xe)
            if (t & 0x1e0) >> 5 != p or h(m, e + 2) < 0 or h(m, e + 4) < 0: continue
            (heroes if t & 0x1f == 0x10 else ej).append(i)
        if heroes:
            nm, dest, tab, oo, ev, _ = corrida(m, p, heroes[0], 3, 150, 100, 0)
            check(nm == 3 and dest == 777 and not ev and oo, f'color {p} líder héroe: no cambia')
        if not ej: continue
        lider = ej[len(ej) // 2]; e = 0x54fe50 + lider * 0x1c; x, y = h(m, e + 2), h(m, e + 4)
        mant, ing = 150, 100; lim = RP_TURNS * (mant - ing)
        if not propias:
            nm, dest, tab, oo, ev, _ = corrida(m, p, lider, 3, mant, ing, 0)
            check(nm == 3 and dest == 777 and not ev and oo, f'color {p} sin ciudades: no cambia')
            continue
        want = modelo_ciudad(m, p, x, y); probados += 1
        for meta in range(0, 10):
            nm, dest, tab, oo, ev, _ = corrida(m, p, lider, meta, mant, ing, lim - 1)
            if meta in (2, 3, 4, 6):
                check(nm == 1 and dest == want and ev == [[37, meta, want, lim - 1]] and tab == (2 | 12 << 8) and oo,
                      f'color {p} meta {meta}: {nm} -> ciudad {dest} (modelo {want}), evento {ev}, tabla {tab:#x}')
            else:
                check(nm == meta and dest == 777 and not ev and tab == ((meta + 1) | 12 << 8) and oo,
                      f'color {p} meta {meta}: no cambia ({nm}, {dest}, {ev})')
        controles = {
            'oro en el límite': dict(oro=lim), 'sin déficit': dict(mant=100, oro=0),
            'IA_MODE 0': dict(mode=0, oro=0), 'jugador 8': dict(jug=8, oro=0), 'humano': dict(humano=True, oro=0)}
        for nombre, kw in controles.items():
            a = dict(mant=mant, ing=ing, oro=0); a.update(kw)
            nm, dest, tab, oo, ev, _ = corrida(m, p, lider, 3, a.pop('mant'), a.pop('ing'), a.pop('oro'), **a)
            check(nm == 3 and dest == 777 and not ev and oo, f'color {p} {nombre}: no cambia ({nm}, {dest}, {ev})')
        nm, dest, tab, oo, ev, lines = corrida(m, p, lider, 3, mant, ing, 0, on=0)
        check(nm == 3 and dest == 777 and not lines and tab == 0 and oo, f'color {p} sin ia_on: nada')
        print(f'  color {p}: líder {lider} en ({x},{y}), {len(propias)} ciudades propias, va a la {want}')
check(probados > 0, f'algún color probado ({probados})')
print(f'{nctl} controles:', 'TODO OK' if ok else 'HAY FALLAS'); sys.exit(0 if ok else 1)
