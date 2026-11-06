# Prueba emulada del evento 30 (cambio de oro, gl_evt; ia\PENDIENTE-ia-economia.md, paso 4): llama a
# 0x43fd60(jugador, cantidad) desde una dirección de retorno conocida, en el exe parcheado y en el original, sobre
# partidas guardadas, y compara: la línea anotada (x = quien llamó, y = cantidad, n = oro antes), el oro que queda
# (con los topes 0 y 32000 del juego), lo que recibe el libro 0x41bee0 y los registros que preserva. Control: sin
# ia_on no se anota nada.
# Uso: python prueba_oro.py <DarklordAV.exe> <Darklord.exe> <ia_on hex> <ia_mode hex> <partida.SAV> [...]
import pefile, struct, sys
from unicorn import *
from unicorn.x86_const import *

AV, ORIG, IA_ON, IA_MODE = sys.argv[1], sys.argv[2], int(sys.argv[3], 16), int(sys.argv[4], 16)
SAVS = sys.argv[5:]
imgs = {k: pefile.PE(f).get_memory_mapped_image() for k, f in (('av', AV), ('orig', ORIG))}
IAT = {'fopen': 0x5a9bdc, 'fclose': 0x5a9be4, 'fprintf': 0x5a9bf4}
STUB, CALLER = 0xdeac0000, 0xdead0000   # CALLER: "call 0x43fd60" puesto a mano; vuelve a CALLER + 5

def cstr(mu, a):
    s = b''
    while (c := mu.mem_read(a + len(s), 1)[0]): s += bytes([c])
    return s.decode('latin1')

def load(sav):
    b = open(sav, 'rb').read(); m = {}; off = 0x6d
    for va, n in ((0x503e00, 0x12), (0x503e58, 0x32000), (0x535ed0, 0xa96), (0x536b30, 0x2d894)):
        m[va] = b[off:off + n]; off += n
    return m

def corrida(img, sav, p, cant, on, oro):
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(0x400000, (len(img) + 0xfff) & ~0xfff); mu.mem_write(0x400000, img)
    STK = 0x10000000; mu.mem_map(STK, 0x100000); mu.mem_map(STUB, 0x1000); mu.mem_map(CALLER, 0x1000)
    for va, d in load(sav).items(): mu.mem_write(va, d)
    mu.mem_write(0x536c14 + p * 0x1f8, struct.pack('<i', oro))
    mu.mem_write(0x503328, struct.pack('<h', 7))
    mu.mem_write(0x537ce8, struct.pack('<h', -1))   # nadie mira: no refresca la pantalla
    if img is imgs['av']: mu.mem_write(IA_ON, bytes([on, 0, 0, 0])); mu.mem_write(IA_MODE, bytes([1] * 8))
    names = list(IAT)
    for k, n in enumerate(names):
        mu.mem_write(IAT[n], struct.pack('<I', STUB + k * 16)); mu.mem_write(STUB + k * 16, b'\xc3')
    lines, calls = [], []
    def arg(i): return struct.unpack('<I', mu.mem_read(mu.reg_read(UC_X86_REG_ESP) + 4 + 4 * i, 4))[0]
    def iat(mu, addr, size, _):
        n = names[(addr - STUB) // 16]; ret = 0
        if n == 'fopen': ret = 0x1000 if cstr(mu, arg(0)).endswith('IA_EVT.CSV') else 0
        elif n == 'fprintf':
            fmt = cstr(mu, arg(1))
            lines.append([struct.unpack('<i', struct.pack('<I', arg(2 + i)))[0] for i in range(fmt.count('%d'))])
        mu.reg_write(UC_X86_REG_EAX, ret)
    mu.hook_add(UC_HOOK_CODE, iat, begin=STUB, end=STUB + 0xfff)
    def sim(mu, addr, size, _):   # 0x41bee0 es thiscall (ecx) con 3 argumentos; 0x4835d0 sin argumentos
        if addr == 0x41bee0:
            calls.append((arg(0) & 0xffff, arg(1), arg(2) & 0xffff))
        esp = mu.reg_read(UC_X86_REG_ESP); r = struct.unpack('<I', mu.mem_read(esp, 4))[0]
        mu.reg_write(UC_X86_REG_ESP, esp + 4 + (12 if addr == 0x41bee0 else 0)); mu.reg_write(UC_X86_REG_EIP, r)
    for a in (0x41bee0, 0x4835d0): mu.hook_add(UC_HOOK_CODE, sim, begin=a, end=a)
    mu.mem_write(CALLER, b'\xe8' + struct.pack('<I', (0x43fd60 - (CALLER + 5)) & 0xffffffff) + b'\x90')
    sp = STK + 0x80000
    mu.mem_write(sp, struct.pack('<II', p, cant & 0xffffffff))
    regs = {UC_X86_REG_EBX: 0x11110000, UC_X86_REG_ESI: 0x2222abcd, UC_X86_REG_EBP: 0x11110002, UC_X86_REG_EDI: 0x3333}
    for r, v in regs.items(): mu.reg_write(r, v)
    mu.reg_write(UC_X86_REG_ESP, sp)
    mu.emu_start(CALLER, CALLER + 5, count=100_000)
    pres = all(mu.reg_read(r) == v for r, v in regs.items()) and mu.reg_read(UC_X86_REG_ESP) == sp
    final = struct.unpack('<i', mu.mem_read(0x536c14 + p * 0x1f8, 4))[0]
    return lines, calls, pres, final

ok = True
def check(c, msg):
    global ok; print('   ', 'OK   ' if c else 'FALLA', msg); ok &= c

for sav in SAVS:
    print(sav)
    vivos = [p for p in range(8) if load(sav)[0x536b30][p * 0x1f8 + 1] and load(sav)[0x536b30][p * 0x1f8]]
    for p in range(8):
        for cant, oro in ((-150, 400), (250, 100), (-500, 120), (2000, 31000), (0, 77)):
            l1, c1, p1, f1 = corrida(imgs['av'], sav, p, cant, 1, oro)
            l0, c0, p0, f0 = corrida(imgs['orig'], sav, p, cant, 1, oro)
            check(l1 == [[7, p, 1, 30, CALLER + 5 - (1 << 32), cant, oro]] and c1 == c0 and f1 == f0 and p1 and p0,
                  f'color {p}{"" if p in vivos else " (no juega)"}, {cant:+} con oro {oro}: anotado {l1}, '
                  f'oro final {f1} = original {f0}, libro {c1}')
        l1, c1, p1, f1 = corrida(imgs['av'], sav, p, -150, 0, 400)
        l0, c0, p0, f0 = corrida(imgs['orig'], sav, p, -150, 0, 400)
        check(l1 == [] and p1 and f1 == f0 and c1 == c0, f'color {p}, sin ia_on: nada anotado, oro {f1} = original')
print('TODO OK' if ok else 'HAY FALLAS'); sys.exit(0 if ok else 1)
