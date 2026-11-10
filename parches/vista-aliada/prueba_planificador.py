# Prueba emulada del paso 4.10 (ia\PENDIENTE-ia-economia.md): evento 36, grupos del planificador.
#   1. pl_run (al empezar el turno de un bando de la computadora): anota el evento 36 con x = PL_N[p], y = PL_E[p],
#      n = grupos activos de p, y pone en 0 los contadores de p; los de los otros colores, los grupos y los registros
#      quedan iguales. Sin ia_on no anota (pero igual pone en 0); con jugador 8 no hace nada.
#   2. pl_mk (en lugar del call 0x40f1a0 de 0x40d434): deja los grupos igual que el 0x40f1a0 original con los mismos
#      argumentos y suma 1 a PL_N[p] solo si se creó el grupo (ax != -1; con los 10 lugares ocupados, no).
#   3. pl_es (en lugar del call 0x4a66a0 de 0x40cfd5): pasa los 3 argumentos, devuelve el eax de 0x4a66a0 y suma 1 a
#      PL_E[p].
# Uso: python prueba_planificador.py <DarklordAV.exe> <ia_on> <ia_mode> <pl_n> <pl_e> <pl_mk> <pl_es> <pl_run> <SAV>...
import pefile, struct, sys
from unicorn import *
from unicorn.x86_const import *

AV = sys.argv[1]
IA_ON, IA_MODE, PL_N, PL_E, PL_MK, PL_ES, PL_RUN = (int(a, 16) for a in sys.argv[2:9])
SAVS = sys.argv[9:]
img = pefile.PE(AV).get_memory_mapped_image()
IAT = {'fopen': 0x5a9bdc, 'fclose': 0x5a9be4, 'fprintf': 0x5a9bf4, 'sprintf': 0x5a9bec, 'time': 0x5a9b88}
STUB, END = 0xdeac0000, 0xdead0000
G0, GEND = 0x561f00, 0x5643c4


def load(sav):
    b = open(sav, 'rb').read(); m = {}; off = 0x6d
    for va, n in ((0x503e00, 0x12), (0x503e58, 0x32000), (0x535ed0, 0xa96), (0x536b30, 0x2d894)):
        m[va] = bytearray(b[off:off + n]); off += n
    return m


def activos(gm, p): return sum(1 for k in range(10) if gm[1178 * p + 64 * k] & 1)


def emu(m, p, entry, args=(), on=1, cont=None, stub_es=False, llenar=False):
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(0x400000, (len(img) + 0xfff) & ~0xfff); mu.mem_write(0x400000, img)
    mu.mem_map(0x10000000, 0x100000); mu.mem_map(STUB, 0x1000); mu.mem_map(END, 0x1000)
    for va, d in m.items(): mu.mem_write(va, bytes(d))
    mu.mem_write(0x4fb0ec, struct.pack('<h', p))
    mu.mem_write(IA_ON, bytes([on, 0, 0, 0])); mu.mem_write(IA_MODE, bytes([1] * 8))
    mu.mem_write(0x427520, b'\xc3')
    if stub_es:   # 0x4a66a0 de prueba: eax = a0 + 2*a1 + 3*a2
        mu.mem_write(0x4a66a0, bytes.fromhex('8b442404' + '03442408' * 2 + '0344240c' * 3 + 'c3'))
    if llenar:
        for q in range(8):
            for k in range(10):
                a = G0 + 1178 * q + 64 * k
                mu.mem_write(a, bytes([mu.mem_read(a, 1)[0] | 1]))
    if cont:
        mu.mem_write(PL_N, struct.pack('<8I', *cont[0])); mu.mem_write(PL_E, struct.pack('<8I', *cont[1]))
    for a in range(0x5a9b00, 0x5a9d00, 4): mu.mem_write(a, struct.pack('<I', STUB + 0x800))
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
    mu.mem_write(sp, struct.pack('<I', END) + b''.join(struct.pack('<I', a) for a in args))
    mu.reg_write(UC_X86_REG_ESP, sp)
    regs = [UC_X86_REG_EBX, UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP, UC_X86_REG_ECX, UC_X86_REG_EDX]
    for k, r in enumerate(regs): mu.reg_write(r, 0x11110000 + k)
    mu.emu_start(entry, END, count=20_000_000)
    intactos = [k for k, r in enumerate(regs) if mu.reg_read(r) != 0x11110000 + k]
    return dict(gm=bytes(mu.mem_read(G0, GEND - G0)), eax=mu.reg_read(UC_X86_REG_EAX), lines=lines,
                regs=intactos, esp=mu.reg_read(UC_X86_REG_ESP) == sp + 4,
                n=struct.unpack('<8I', mu.mem_read(PL_N, 32)), e=struct.unpack('<8I', mu.mem_read(PL_E, 32)),
                army=bytes(mu.mem_read(0x54fe50, 0x1c * 1200)))


fallas = ctl = 0


def ok(c, msg):
    global fallas, ctl
    ctl += 1
    if not c: fallas += 1; print('  FALLA', msg)


def huerfano(m, p):   # un ejército vivo de p, no héroe, para líder de prueba
    for i in range(struct.unpack('<h', m[0x536b30][0x54fe50 - 0x536b30:][:2])[0]):
        e = 0x54fe50 + i * 0x1c - 0x536b30
        t = struct.unpack('<h', m[0x536b30][e + 0xe:e + 0x10])[0]
        if m[0x536b30][e + 0x13] & 0x40 and t & 0x1f != 0x10 and (t & 0x1e0) >> 5 == p: return i
    return None


N0, E0 = tuple(3 * q + 1 for q in range(8)), tuple(5 * q + 2 for q in range(8))
for sav in SAVS:
    m = load(sav); base = bytes(m[0x536b30][G0 - 0x536b30:GEND - 0x536b30])
    print(sav.split('\\')[-1].split('/')[-1])
    for p in range(8):
        r = emu(m, p, PL_RUN, cont=(N0, E0))
        ok(not r['regs'] and r['esp'], f'p{p}: pl_run cambió registros {r["regs"]}')
        ok(r['gm'] == base, f'p{p}: pl_run cambió grupos')
        ok([l[1:] for l in r['lines']] == [[p, 1, 36, N0[p], E0[p], activos(base, p)]], f'p{p}: evento {r["lines"]}')
        ok(r['n'] == tuple(0 if q == p else N0[q] for q in range(8)) and
           r['e'] == tuple(0 if q == p else E0[q] for q in range(8)), f'p{p}: contadores {r["n"]} {r["e"]}')
        r = emu(m, p, PL_RUN, on=0, cont=(N0, E0))
        ok(r['lines'] == [] and r['n'][p] == 0 and r['e'][p] == 0, f'p{p}: sin ia_on {r["lines"]}')
        # pl_mk contra 0x40f1a0 original
        i = huerfano(m, p)
        if i is not None:
            for llenar in (False, True):
                a = emu(m, p, PL_MK, args=(i, 0), cont=(N0, E0), llenar=llenar)
                b = emu(m, p, 0x40f1a0, args=(i, 0), cont=(N0, E0), llenar=llenar)
                ok(a['gm'] == b['gm'] and a['army'] == b['army'] and a['eax'] & 0xffff == b['eax'] & 0xffff,
                   f'p{p}: pl_mk distinto de 0x40f1a0 (llenos {llenar})')
                creado = b['eax'] & 0xffff != 0xffff
                ok(creado != llenar, f'p{p}: 0x40f1a0 creó {creado} con llenos {llenar}')
                ok(a['n'] == tuple(N0[q] + (1 if q == p and creado else 0) for q in range(8)) and a['e'] == E0,
                   f'p{p}: pl_mk contadores {a["n"]}')
                ok(not a['regs'] or a['regs'] == b['regs'], f'p{p}: pl_mk registros {a["regs"]} {b["regs"]}')
        # pl_es con 0x4a66a0 de prueba
        r = emu(m, p, PL_ES, args=(7, 11, 13), cont=(N0, E0), stub_es=True)
        ok(r['eax'] == 7 + 2 * 11 + 3 * 13, f'p{p}: pl_es eax {r["eax"]}')
        ok(r['e'] == tuple(E0[q] + (q == p) for q in range(8)) and r['n'] == N0, f'p{p}: pl_es contadores {r["e"]}')
        ok(r['esp'] and r['regs'] in ([], [5]), f'p{p}: pl_es registros {r["regs"]}')
    r = emu(m, 8, PL_RUN, cont=(N0, E0))
    ok(r['lines'] == [] and r['n'] == N0 and r['e'] == E0, f'jugador 8: {r["lines"]}')
print('controles', ctl, 'TODO OK' if not fallas else f'{fallas} FALLAS')
sys.exit(1 if fallas else 0)
