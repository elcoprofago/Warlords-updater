# Prueba emulada del evento 28 (deserción por falta de oro, ds_evt; ia\PENDIENTE-ia-economia.md, paso 1): ejecuta
# 0x415910(p) del exe parcheado sobre el estado de partidas guardadas, con el azar (0x4deb20) forzado, y compara las
# líneas de IA_EVT.CSV con un conteo independiente hecho en Python sobre el mismo .SAV.
# Controles: con azar > 20 no deserta nadie ni se anota nada; sin ia_on desertan igual pero no se anota; los ejércitos
# de los otros colores y los héroes nunca aparecen; el contador del juego [0x4f9894] coincide con las líneas.
# Uso: python prueba_desbande.py <DarklordAV.exe> <ia_on hex> <ia_mode hex> <partida.SAV> [...]
#   (las direcciones las imprime build.py en la línea "caves"; requiere pefile y unicorn)
import pefile, struct, sys
from unicorn import *
from unicorn.x86_const import *

EXE, IA_ON, IA_MODE = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3], 16)
SAVS = sys.argv[4:]
img = pefile.PE(EXE).get_memory_mapped_image()
IAT = {'fopen': 0x5a9bdc, 'fclose': 0x5a9be4, 'fprintf': 0x5a9bf4}
STUB, RET = 0xdeac0000, 0xdead0000
# rutinas del juego simuladas: (dirección, bytes que saca del stack al volver)
SIM = {0x4deb20: 0, 0x4b9e20: 0, 0x4e3130: 0xc, 0x441290: 0}

def cstr(mu, a):
    s = b''
    while (c := mu.mem_read(a + len(s), 1)[0]): s += bytes([c])
    return s.decode('latin1')

def load(sav):
    b = open(sav, 'rb').read(); m = {}; off = 0x6d
    for va, n in ((0x503e00, 0x12), (0x503e58, 0x32000), (0x535ed0, 0xa96), (0x536b30, 0x2d894)):
        m[va] = b[off:off + n]; off += n
    return m

def rd(m, va, n):
    for b, d in m.items():
        if b <= va and va + n <= b + len(d): return d[va - b:va - b + n]

def esperado(m, p):   # independiente del parche: ejércitos vivos de p, no héroes, con algún bit 0xf0 en +0x10
    n = struct.unpack('<h', rd(m, 0x54fe50, 2))[0]; r = []
    oro = struct.unpack('<i', rd(m, 0x536c14 + p * 0x1f8, 4))[0]
    for i in range(1, n):
        a = rd(m, 0x54fe50 + i * 0x1c, 0x1c); w = struct.unpack_from('<H', a, 0xe)[0]
        if a[0x13] & 0x40 and (w >> 5) & 0xf == p and w & 0x1f != 0x10 and struct.unpack_from('<H', a, 0x10)[0] & 0xf0:
            x, y = struct.unpack_from('<hh', a, 2); r.append((i, [9, p, 1, 28, x, y, oro]))
    return r

def corrida(sav, p, azar, on):
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(0x400000, (len(img) + 0xfff) & ~0xfff); mu.mem_write(0x400000, img)
    STK = 0x10000000; mu.mem_map(STK, 0x100000); mu.mem_map(STUB, 0x1000); mu.mem_map(RET, 0x1000)
    for va, d in load(sav).items(): mu.mem_write(va, d)
    mu.mem_write(0x503328, struct.pack('<h', 9))
    mu.mem_write(IA_ON, bytes([on, 0, 0, 0])); mu.mem_write(IA_MODE, bytes([1] * 8))
    names = list(IAT)
    for k, n in enumerate(names):
        mu.mem_write(IAT[n], struct.pack('<I', STUB + k * 16)); mu.mem_write(STUB + k * 16, b'\xc3')
    lines, killed = [], []
    def arg(i): return struct.unpack('<I', mu.mem_read(mu.reg_read(UC_X86_REG_ESP) + 4 + 4 * i, 4))[0]
    def iat(mu, addr, size, _):
        n = names[(addr - STUB) // 16]; ret = 0
        if n == 'fopen': ret = 0x1000 if cstr(mu, arg(0)).endswith('IA_EVT.CSV') else 0
        elif n == 'fprintf':
            fmt = cstr(mu, arg(1))
            lines.append([struct.unpack('<i', struct.pack('<I', arg(2 + i)))[0] for i in range(fmt.count('%d'))])
        mu.reg_write(UC_X86_REG_EAX, ret)
    mu.hook_add(UC_HOOK_CODE, iat, begin=STUB, end=STUB + 0xfff)
    def sim(mu, addr, size, _):
        if addr not in SIM: return
        if addr == 0x4deb20: mu.reg_write(UC_X86_REG_EAX, azar)
        if addr == 0x4b9e20: killed.append(struct.unpack('<h', struct.pack('<I', arg(0))[:2])[0])
        esp = mu.reg_read(UC_X86_REG_ESP); r = struct.unpack('<I', mu.mem_read(esp, 4))[0]
        mu.reg_write(UC_X86_REG_ESP, esp + 4 + SIM[addr]); mu.reg_write(UC_X86_REG_EIP, r)
    for a in SIM: mu.hook_add(UC_HOOK_CODE, sim, begin=a, end=a)
    sp = STK + 0x80000 - 64
    mu.mem_write(sp, struct.pack('<II', RET, p))
    regs = {r: 0x11110000 + k for k, r in enumerate((UC_X86_REG_EBX, UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP))}
    for r, v in regs.items(): mu.reg_write(r, v)
    mu.reg_write(UC_X86_REG_ESP, sp)
    mu.emu_start(0x415910, RET, count=5_000_000)
    pres = all(mu.reg_read(r) == v for r, v in regs.items()) and mu.reg_read(UC_X86_REG_ESP) == sp + 4
    cont = struct.unpack('<h', mu.mem_read(0x4f9894, 2))[0]
    return lines, killed, cont, pres

ok = True
def check(c, msg):
    global ok; print('   ', 'OK   ' if c else 'FALLA', msg); ok &= c

total = 0
for sav in SAVS:
    m = load(sav); print(sav)
    for p in range(8):
        e = esperado(m, p)
        lines, killed, cont, pres = corrida(sav, p, 20, 1)
        total += len(lines)
        check(killed == [i for i, _ in e] and lines == [l for _, l in e] and cont == len(e) and pres,
              f'color {p}, azar 20: {len(lines)} desertores anotados = conteo propio ({len(e)}), contador del juego {cont}')
        lines, killed, cont, pres = corrida(sav, p, 21, 1)
        check(lines == [] and killed == [] and cont == 0 and pres, f'color {p}, azar 21: nadie deserta, nada anotado')
        lines, killed, cont, pres = corrida(sav, p, 1, 0)
        check(lines == [] and len(killed) == len(e) and pres, f'color {p}, sin ia_on: desertan {len(killed)} y no se anota')
print('desertores anotados en total:', total)
print('TODO OK' if ok else 'HAY FALLAS'); sys.exit(0 if ok else 1)
