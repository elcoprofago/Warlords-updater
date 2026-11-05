# Prueba emulada del evento 29 (saldo del turno, ec_evt; ia\PENDIENTE-ia-economia.md, paso 2): ejecuta 0x42244b..0x42249b
# (quiebra y saldo al empezar el turno) en el exe parcheado y en el original, sobre partidas guardadas, con ingreso y
# mantenimiento puestos a mano, y compara: la línea anotada (x = ingreso, y = mantenimiento, n = oro) y que la quiebra
# (0x415a00) y el saldo que recibe 0x4b9390 sean iguales a los del original. Control: sin ia_on no se anota nada.
# Uso: python prueba_saldo.py <DarklordAV.exe> <Darklord.exe> <ia_on hex> <ia_mode hex> <partida.SAV> [...]
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
        m[va] = b[off:off + n]; off += n
    return m

def corrida(img, sav, p, ing, man, on, oro=None):
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(0x400000, (len(img) + 0xfff) & ~0xfff); mu.mem_write(0x400000, img)
    STK = 0x10000000; mu.mem_map(STK, 0x100000); mu.mem_map(STUB, 0x1000)
    for va, d in load(sav).items(): mu.mem_write(va, d)
    if oro is not None: mu.mem_write(0x536c14 + p * 0x1f8, struct.pack('<i', oro))
    mu.mem_write(0x503328, struct.pack('<h', 7))
    mu.mem_write(0x5643f0 + 2 * p, struct.pack('<h', ing)); mu.mem_write(0x5643d8 + 2 * p, struct.pack('<h', man))
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
    def sim(mu, addr, size, _):
        calls.append((hex(addr), arg(0), arg(1) & 0xffff))
        esp = mu.reg_read(UC_X86_REG_ESP); r = struct.unpack('<I', mu.mem_read(esp, 4))[0]
        mu.reg_write(UC_X86_REG_ESP, esp + 4); mu.reg_write(UC_X86_REG_EIP, r)
    for a in (0x415a00, 0x4b9390): mu.hook_add(UC_HOOK_CODE, sim, begin=a, end=a)
    sp = STK + 0x80000
    frame = bytearray(0x40); struct.pack_into('<I', frame, 0x14, p); struct.pack_into('<I', frame, 0x1c, p * 0x1f8)
    mu.mem_write(sp, bytes(frame))
    regs = {UC_X86_REG_EBX: 0x11110000, UC_X86_REG_ESI: 0x11110001, UC_X86_REG_EBP: 0x11110002, UC_X86_REG_EDI: p}
    for r, v in regs.items(): mu.reg_write(r, v)
    mu.reg_write(UC_X86_REG_ESP, sp)
    mu.emu_start(0x42244b, RET, count=100_000)
    pres = all(mu.reg_read(r) == v for r, v in regs.items()) and mu.reg_read(UC_X86_REG_ESP) == sp - 8   # se detiene antes de "add esp, 8"
    return lines, calls, pres, mu.reg_read(UC_X86_REG_EDX)

ok = True
def check(c, msg):
    global ok; print('   ', 'OK   ' if c else 'FALLA', msg); ok &= c

for sav in SAVS:
    print(sav)
    for p in range(8):
        for ing, man, oro in ((120, 40, None), (30, 200, 50), (0, 0, 0), (5, 300, 100)):
            l1, c1, p1, d1 = corrida(imgs['av'], sav, p, ing, man, 1, oro)
            l0, c0, p0, d0 = corrida(imgs['orig'], sav, p, ing, man, 1, oro)
            o = struct.unpack('<i', load(sav)[0x536b30][(0x536c14 + p * 0x1f8 - 0x536b30):][:4])[0] if oro is None else oro
            check(l1 == [[7, p, 1, 29, ing, man, o]] and c1 == c0 and p1 and p0 and d1 == d0,
                  f'color {p}, ingreso {ing}, mantenimiento {man}, oro {o}: anotado {l1}, llamadas {c1} = original')
        l1, c1, p1, _ = corrida(imgs['av'], sav, p, 120, 40, 0)
        check(l1 == [] and p1, f'color {p}, sin ia_on: nada anotado')
print('TODO OK' if ok else 'HAY FALLAS'); sys.exit(0 if ok else 1)
