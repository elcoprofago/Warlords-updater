# Prueba emulada de partners(i), la regla de ciudades compartidas: ejecuta la rutina parcheada real sobre el estado de
# una partida guardada y compara la máscara de socios de cada ciudad con un cálculo independiente en Python.
#   - mapa visible: socios = aliados mutuos vivos del dueño, sin exigir exploración (16/10/2026);
#   - Hidden Map: además, que el socio haya explorado por sí mismo las 4 casillas de la ciudad;
#   - sin la opción de ciudades compartidas, o sin Diplomacy: ninguna.
# Las alianzas vigentes se toman de la tabla de propuestas (+9..16 de cada fila de DIPLO) solo en la memoria emulada;
# el .SAV no se modifica.
# Uso: python prueba_compartidas.py <DarklordAV.exe> <partners hex> <partida.SAV> [...]
#   (la dirección la imprime build.py en la línea "caves"; requiere pefile y unicorn)
import pefile, struct, sys
from unicorn import *
from unicorn.x86_const import *

EXE, PARTNERS, SAVS = sys.argv[1], int(sys.argv[2], 16), sys.argv[3:]
DIPLO, OPT, SHOPT, DIPLO_OPT, CITIES = 0x55ee4c, 0x53c38e, 0x53c38c + 25, 0x53c393, 0x537e2c
img = pefile.PE(EXE).get_memory_mapped_image()


def load(sav):
    b = open(sav, 'rb').read(); m = {}; off = 0x6d
    for va, n in ((0x503e00, 0x12), (0x503e58, 0x32000), (0x535ed0, 0xa96), (0x536b30, 0x2d894)):
        m[va] = bytearray(b[off:off + n]); off += n
    return m


def ref(m, va):
    for b, d in m.items():
        if b <= va < b + len(d): return d, va - b


def rd(m, va, n=1):
    d, o = ref(m, va); return bytes(d[o:o + n])


def wr(m, va, v):
    d, o = ref(m, va); d[o] = v


def esperado(m, i, hidden):
    if not rd(m, SHOPT)[0] & 1 or not rd(m, DIPLO_OPT)[0] & 8: return 0
    c = CITIES + i * 0xde
    if rd(m, c + 0xa4)[0] == 0: return 0
    p = rd(m, c + 0xa5)[0]
    if p >= 8: return 0
    mask = 0
    for q in range(8):
        pr = rd(m, 0x536b30 + q * 0x1f8, 2)
        if q != p and pr[0] and pr[1] and rd(m, DIPLO + p * 56 + q)[0] == 0 and rd(m, DIPLO + q * 56 + p)[0] == 0:
            mask |= 1 << q
    if not hidden or not mask: return mask
    x, y = struct.unpack('<h', rd(m, c, 2))[0], struct.unpack('<h', rd(m, c + 2, 2))[0]
    sh = rd(m, 0x503e06)[0]; ex = 0xff
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        t = 0x503e58 + (((y + dy) * 10) << sh) + (x + dx) * 10
        ex &= rd(m, t + 4)[0] & ~rd(m, t + 5)[0]
    return ex & mask


def emular(m, i):
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(0x400000, (len(img) + 0xfff) & ~0xfff); mu.mem_write(0x400000, img)
    for va, d in m.items(): mu.mem_write(va, bytes(d))
    STK = 0x10000000; mu.mem_map(STK, 0x10000); mu.mem_map(0xdead0000, 0x1000)
    sp = STK + 0x8000
    mu.mem_write(sp, struct.pack('<II', 0xdead0000, i))
    regs = {r: 0x11110000 + k for k, r in enumerate((UC_X86_REG_EBX, UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP))}
    for r, v in regs.items(): mu.reg_write(r, v)
    mu.reg_write(UC_X86_REG_ESP, sp)
    mu.emu_start(PARTNERS, 0xdead0000, count=100000)
    pres = all(mu.reg_read(r) == v for r, v in regs.items()) and mu.reg_read(UC_X86_REG_ESP) == sp + 4
    return mu.reg_read(UC_X86_REG_EAX), pres


ok = True
def check(c, msg):
    global ok; print('   ', 'OK   ' if c else 'FALLA', msg); ok &= c

for sav in SAVS:
    print(sav)
    base = load(sav)
    for p in range(8):   # alianzas vigentes = propuestas (solo en memoria)
        for q in range(8): wr(base, DIPLO + p * 56 + q, rd(base, DIPLO + p * 56 + 9 + q)[0])
    nc = struct.unpack('<h', rd(base, 0x537e2a, 2))[0]
    for nombre, hidden, sh, dip in (('visible', 0, 1, 1), ('Hidden Map', 1, 1, 1), ('sin la opción', 0, 0, 1),
                                    ('sin Diplomacy', 0, 1, 0)):
        m = {va: bytearray(d) for va, d in base.items()}
        o = rd(m, OPT)[0]; wr(m, OPT, (o | 0x10) if hidden else (o & ~0x10))
        s = rd(m, SHOPT)[0]; wr(m, SHOPT, (s | 1) if sh else (s & ~1))
        d = rd(m, DIPLO_OPT)[0]; wr(m, DIPLO_OPT, (d | 8) if dip else (d & ~8))
        malos, con, todos_pres = [], 0, True
        for i in range(nc):
            got, pres = emular(m, i); exp = esperado(m, i, hidden)
            todos_pres &= pres; con += bool(exp)
            if got != exp: malos.append((i, hex(got), hex(exp)))
        check(not malos and todos_pres, f'{nombre}: {nc} ciudades, {con} compartidas, igual al cálculo propio'
              + (f'; distintas {malos[:5]}' if malos else '') + ('' if todos_pres else '; registros pisados'))
        if nombre == 'visible':
            check(con > 0, 'visible: hay ciudades compartidas (antes del cambio daba 0)')
        if nombre in ('sin la opción', 'sin Diplomacy'):
            check(con == 0, f'{nombre}: ninguna compartida')
    # control: un dueño sin aliados no comparte, aunque el resto sí
    m = {va: bytearray(d) for va, d in base.items()}
    o = rd(m, OPT)[0]; wr(m, OPT, o & ~0x10)
    for q in range(8): wr(m, DIPLO + 0 * 56 + q, 1); wr(m, DIPLO + q * 56 + 0, 1)
    blancas = [i for i in range(nc) if rd(m, CITIES + i * 0xde + 0xa5)[0] == 0]
    r = [emular(m, i)[0] for i in blancas]
    check(blancas and not any(r), f'control: blanco sin aliados, sus {len(blancas)} ciudades no se comparten')
print('TODO OK' if ok else 'HAY FALLAS'); sys.exit(0 if ok else 1)
