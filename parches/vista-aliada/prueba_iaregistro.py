# Prueba emulada del registro de la IA (ia_turn / ia_snap): ejecuta el código parcheado real sobre el estado de
# partidas guardadas, con fopen/fclose/fprintf/GetPrivateProfileStringA/_stricmp simulados, y compara cada línea con
# un conteo independiente hecho en Python sobre el mismo .SAV.
# Uso: python prueba_iaregistro.py <DarklordAV.exe> <ia_turn hex> <turn hex> <partida.SAV> [...]
#   (las direcciones las imprime build.py en la línea "caves"; requiere pefile y unicorn)
import pefile, struct, sys
from unicorn import *
from unicorn.x86_const import *

EXE, IA_TURN, TURN = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3], 16)
pe = pefile.PE(EXE); img = pe.get_memory_mapped_image()
IAT = {'fopen': 0x5a9bdc, 'fclose': 0x5a9be4, 'fprintf': 0x5a9bf4, '_stricmp': 0x5a9be0, 'GetPrivateProfileStringA': 0x5a97e8}
STUB = 0xdeac0000

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

def cuenta(m, p):   # independiente del parche
    n = struct.unpack('<h', rd(m, 0x54fe50, 2))[0]; nc = struct.unpack('<h', rd(m, 0x537e2a, 2))[0]
    pr = rd(m, 0x536b30 + p * 0x1f8, 0x1f8); slots = [0] * 17
    for i in range(1, n):
        r = rd(m, 0x54fe50 + i * 0x1c, 0x1c); w = struct.unpack_from('<H', r, 0xe)[0]
        if r[0x13] & 0x40 and (w >> 5) & 0xf == p: slots[min(w & 0x1f, 16)] += 1
    ci = sum(1 for k in range(nc) if rd(m, 0x537e2c + k * 0xde + 0xa5, 1)[0] == p)
    return [pr[1], struct.unpack_from('<h', pr, 0xe2)[0], struct.unpack_from('<i', pr, 0xe4)[0], ci,
            sum(slots[:16]), slots[16]] + slots[:16]

def corrida(sav, ini, turno, p):
    """ini: None = no hay IA.INI; si no, dict ColorN -> valor. Devuelve (líneas escritas, ia_mode, llamadas)."""
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(0x400000, (len(img) + 0xfff) & ~0xfff); mu.mem_write(0x400000, img)
    STK = 0x10000000; mu.mem_map(STK, 0x100000); mu.mem_map(STUB, 0x1000); mu.mem_map(0xdead0000, 0x1000)
    for va, d in load(sav).items(): mu.mem_write(va, d)
    mu.mem_write(0x503328, struct.pack('<h', turno))
    names = list(IAT)
    for k, n in enumerate(names):
        mu.mem_write(IAT[n], struct.pack('<I', STUB + k * 16)); mu.mem_write(STUB + k * 16, b'\xc3')
    out, calls = [], []
    def arg(i): return struct.unpack('<I', mu.mem_read(mu.reg_read(UC_X86_REG_ESP) + 4 + 4 * i, 4))[0]
    def hook(mu, addr, size, _):
        k = (addr - STUB) // 16; n = names[k]; calls.append(n); ret = 0
        if n == 'fopen':
            path, mode = cstr(mu, arg(0)), cstr(mu, arg(1))
            ret = 0 if (path.endswith('IA.INI') and ini is None) else 0x1000 + len(calls)
            calls[-1] += f'({path},{mode})'
        elif n == 'fprintf':
            fmt = cstr(mu, arg(1)); nargs = fmt.count('%d')
            vals = [struct.unpack('<i', struct.pack('<I', arg(2 + i)))[0] for i in range(nargs)]
            out.append(vals)
        elif n == '_stricmp':
            ret = 0 if cstr(mu, arg(0)).lower() == cstr(mu, arg(1)).lower() else 1
        elif n == 'GetPrivateProfileStringA':
            sec, key, dflt, buf, size = cstr(mu, arg(0)), cstr(mu, arg(1)), cstr(mu, arg(2)), arg(3), arg(4)
            v = (ini or {}).get(key, dflt)[:size - 1]
            mu.mem_write(buf, v.encode('latin1') + b'\0'); ret = len(v)
            mu.reg_write(UC_X86_REG_EAX, ret)
            esp = mu.reg_read(UC_X86_REG_ESP); r = struct.unpack('<I', mu.mem_read(esp, 4))[0]
            mu.reg_write(UC_X86_REG_ESP, esp + 4 + 24); mu.reg_write(UC_X86_REG_EIP, r)   # stdcall
            return
        mu.reg_write(UC_X86_REG_EAX, ret)
    mu.hook_add(UC_HOOK_CODE, hook, begin=STUB, end=STUB + 0xfff)
    sp = STK + 0x80000 - 64
    mu.mem_write(sp, struct.pack('<II', 0xdead0000, p))
    regs = {r: 0x11110000 + k for k, r in enumerate((UC_X86_REG_EBX, UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP))}
    for r, v in regs.items(): mu.reg_write(r, v)
    mu.reg_write(UC_X86_REG_ESP, sp)
    mu.emu_start(IA_TURN, TURN, count=5_000_000)
    assert mu.reg_read(UC_X86_REG_EIP) == TURN, 'no llegó a turn'
    pres = all(mu.reg_read(r) == v for r, v in regs.items()) and mu.reg_read(UC_X86_REG_ESP) == sp
    mode = list(mu.mem_read(0x400000 + 0, 0) or b'')
    return out, calls, pres

ok = True
def check(c, msg):
    global ok; print('   ', 'OK   ' if c else 'FALLA', msg); ok &= c

for sav in sys.argv[4:]:
    m = load(sav); print(sav)
    o, c, pres = corrida(sav, None, 7, 3)
    check(o == [] and c == ['fopen(.\\DATA\\IA.INI,r)'] and pres, 'sin IA.INI: solo intenta abrirlo, no escribe nada, registros intactos')
    ini = {f'Color{k}': ('prueba' if k % 2 else 'Original') for k in range(8)}
    for p in range(8):
        o, c, pres = corrida(sav, ini, 12, p)
        exp = [12, p, p % 2] + cuenta(m, p)
        check(o == [exp] and pres, f'color {p}: {o[0][:9] if o else o}... = conteo propio')
    ini['Color5'] = 'pruebas'; ini.pop('Color6')
    o5, _, _ = corrida(sav, ini, 1, 5); o6, _, _ = corrida(sav, ini, 1, 6)
    check(o5[0][2] == 2 and o6[0][2] == 0, f'valor inválido -> ia 2 ({o5[0][2]}); clave ausente -> original ({o6[0][2]})')
print('RESULTADO:', 'TODO OK' if ok else 'HAY FALLAS')
