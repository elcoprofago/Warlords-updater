# Prueba emulada de la reserva de oro (rs_ok, rs_unit, rs_grow; ia\PENDIENTE-ia-economia.md, paso 4): llama a
# 0x48ba50 (comprar un tipo de unidad para una ciudad) y a 0x405310 (agrandar una ciudad) sobre partidas guardadas,
# en el exe parcheado y en el original, y mira si la compra sigue (llega al cobro, 0x43fd60, con el mismo costo que el
# original; en 0x405310, a la instrucción que sigue a la entrada) o se frena (vuelve sin cobrar, con el evento 31 y
# los registros intactos). Piso = 2 x mantenimiento, nunca menos de 50.
# Controles que deben seguir como el original: humano, IA original (ia_mode 0), sin ia_on, ciudad de otro, costo 0.
# Ahorro con destino (11/11/2026): con RS_GOAL[p] = costo de un puente y RS_GOALT[p] = turno + 1 de este turno o del
# anterior, el piso suma ese costo y el evento 31 lleva x = tipo + 10; vencido (2 turnos) o sin anotar, no cuenta.
# Uso: python prueba_reserva.py <DarklordAV.exe> <Darklord.exe> <ia_on hex> <ia_mode hex> <rs_goal hex> <rs_goalt hex>
#      <partida.SAV> [...]
import pefile, struct, sys
from unicorn import *
from unicorn.x86_const import *

AV, ORIG, IA_ON, IA_MODE = sys.argv[1], sys.argv[2], int(sys.argv[3], 16), int(sys.argv[4], 16)
RS_GOAL, RS_GOALT = int(sys.argv[5], 16), int(sys.argv[6], 16)
SAVS = sys.argv[7:]
TURNO = 7
imgs = {k: pefile.PE(f).get_memory_mapped_image() for k, f in (('av', AV), ('orig', ORIG))}
IAT = {'fopen': 0x5a9bdc, 'fclose': 0x5a9be4, 'fprintf': 0x5a9bf4}
STUB, CALLER = 0xdeac0000, 0xdead0000
SIGUE = 'sigue'

def cstr(mu, a):
    s = b''
    while (c := mu.mem_read(a + len(s), 1)[0]): s += bytes([c])
    return s.decode('latin1')

def load(sav):
    b = open(sav, 'rb').read(); m = {}; off = 0x6d
    for va, n in ((0x503e00, 0x12), (0x503e58, 0x32000), (0x535ed0, 0xa96), (0x536b30, 0x2d894)):
        m[va] = b[off:off + n]; off += n
    return m

def i16(v): return struct.unpack('<h', struct.pack('<H', v & 0xffff))[0]

def corrida(img, sav, fn, args, p, oro, mant, humano, on, modo, meta=None):
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(0x400000, (len(img) + 0xfff) & ~0xfff); mu.mem_write(0x400000, img)
    STK = 0x10000000; mu.mem_map(STK, 0x100000); mu.mem_map(STUB, 0x1000); mu.mem_map(CALLER, 0x1000)
    for va, d in load(sav).items(): mu.mem_write(va, d)
    mu.mem_write(0x536c14 + p * 0x1f8, struct.pack('<h', oro))
    mu.mem_write(0x536c12 + p * 0x1f8, struct.pack('<h', -1 if humano else 0))
    mu.mem_write(0x5643d8 + 2 * p, struct.pack('<h', mant))
    mu.mem_write(0x503328, struct.pack('<h', TURNO))
    if img is imgs['av']:
        mu.mem_write(IA_ON, bytes([on, 0, 0, 0])); mu.mem_write(IA_MODE, bytes([modo] * 8))
        if meta: mu.mem_write(RS_GOAL + 4 * p, struct.pack('<i', meta[0])); mu.mem_write(RS_GOALT + 4 * p, struct.pack('<i', meta[1]))
    names = list(IAT)
    for k, n in enumerate(names):
        mu.mem_write(IAT[n], struct.pack('<I', STUB + k * 16)); mu.mem_write(STUB + k * 16, b'\xc3')
    lines, res = [], []
    def arg(i): return struct.unpack('<I', mu.mem_read(mu.reg_read(UC_X86_REG_ESP) + 4 + 4 * i, 4))[0]
    def iat(mu, addr, size, _):
        n = names[(addr - STUB) // 16]; ret = 0
        if n == 'fopen': ret = 0x1000 if cstr(mu, arg(0)).endswith('IA_EVT.CSV') else 0
        elif n == 'fprintf':
            fmt = cstr(mu, arg(1))
            lines.append([struct.unpack('<i', struct.pack('<I', arg(2 + i)))[0] for i in range(fmt.count('%d'))])
        mu.reg_write(UC_X86_REG_EAX, ret)
    mu.hook_add(UC_HOOK_CODE, iat, begin=STUB, end=STUB + 0xfff)
    def ret0(mu, addr, size, _):   # funciones del original que no hacen falta: vuelven sin hacer nada
        esp = mu.reg_read(UC_X86_REG_ESP); r = struct.unpack('<I', mu.mem_read(esp, 4))[0]
        mu.reg_write(UC_X86_REG_ESP, esp + 4); mu.reg_write(UC_X86_REG_EIP, r)
    for a in (0x431e60, 0x4ae250, 0x4a2170): mu.hook_add(UC_HOOK_CODE, ret0, begin=a, end=a)
    def cobro(mu, addr, size, _):
        res.append(('cobra', arg(0) & 0xffff, i16(arg(1)))); mu.emu_stop()
    mu.hook_add(UC_HOOK_CODE, cobro, begin=0x43fd60, end=0x43fd60)
    if fn == 0x405310:   # agrandar: basta con ver que pasa la entrada
        def sigue(mu, addr, size, _): res.append(SIGUE); mu.emu_stop()
        mu.hook_add(UC_HOOK_CODE, sigue, begin=0x405317, end=0x405317)
    mu.mem_write(CALLER, b'\xe8' + struct.pack('<I', (fn - (CALLER + 5)) & 0xffffffff))
    sp = STK + 0x80000
    mu.mem_write(sp, b''.join(struct.pack('<I', a & 0xffffffff) for a in args))
    regs = {UC_X86_REG_EBX: 0x11110000, UC_X86_REG_ESI: 0x2222abcd, UC_X86_REG_EBP: 0x11110002, UC_X86_REG_EDI: 0x3333}
    for r, v in regs.items(): mu.reg_write(r, v)
    mu.reg_write(UC_X86_REG_ESP, sp)
    mu.emu_start(CALLER, CALLER + 5, count=200_000)
    volvio = mu.reg_read(UC_X86_REG_EIP) == CALLER + 5
    pres = volvio and all(mu.reg_read(r) == v for r, v in regs.items()) and mu.reg_read(UC_X86_REG_ESP) == sp
    return lines, res, pres

ok = True; n = 0
def check(c, msg):
    global ok, n; n += 1
    if not c: print('    FALLA', msg)
    ok &= c

def costo_unidad(m, p, t, aj):
    c = struct.unpack_from('<h', m[0x536b30], 0x53c4f2 + (16 * p + t) * 0xfc - 0x536b30)[0]
    q = abs(c * aj) // 10 * (1 if c * aj >= 0 else -1)   # idiv trunca hacia 0
    return i16(c - q)

for sav in SAVS:
    m = load(sav); antes = n
    ncity = struct.unpack_from('<h', m[0x536b30], 0x537e2a - 0x536b30)[0]
    dueño = {i: m[0x536b30][0x537ed1 + i * 0xde - 0x536b30] for i in range(ncity)}
    for p in range(8):
        mias = [i for i, d in dueño.items() if d == p]; otra = next(i for i, d in dueño.items() if d != p)
        for mant in (10, 40):
            piso = max(50, 2 * mant)
            # comprar tipo de unidad
            for ciudad in mias[:1]:
                for t, aj in ((0, 0), (1, 2), (2, -3), (3, 0)):
                    cost = costo_unidad(m, p, t, aj)
                    args = (ciudad, p, t, 0, aj)
                    _, r0, _ = corrida(imgs['orig'], sav, 0x48ba50, args, p, piso + cost, mant, False, 1, 1)
                    check(r0 == [('cobra', p, -cost)], f'original cobra {cost}: {r0}')
                    for oro, frena in ((piso + cost, False), (piso + cost - 1, True)):
                        l, r, pr = corrida(imgs['av'], sav, 0x48ba50, args, p, oro, mant, False, 1, 1)
                        if frena:
                            check(r == [] and pr and l == [[7, p, 1, 31, 1, cost, oro]],
                                  f'{sav} c{p} unidad t{t} aj{aj} oro {oro} piso {piso}: debe frenar {l} {r} {pr}')
                        else:
                            check(r == r0 and l == [[7, p, 1, 30, 0x48baea - (1 << 32), -cost, oro]] or
                                  r == r0 and r0 and l == [],
                                  f'{sav} c{p} unidad t{t} oro {oro}: debe seguir {l} {r}')
                    for desc, hum, on, modo in (('humano', True, 1, 1), ('IA original', False, 1, 0),
                                                ('sin ia_on', False, 0, 1)):
                        l, r, _ = corrida(imgs['av'], sav, 0x48ba50, args, p, 0, mant, hum, on, modo)
                        _, r0, _ = corrida(imgs['orig'], sav, 0x48ba50, args, p, 0, mant, hum, on, modo)
                        check(r == r0 and not any(x[3] == 31 for x in l), f'{sav} c{p} unidad {desc}: {l} {r} {r0}')
            # ciudad de otro: el original no hace nada; el parche tampoco ni anota
            l, r, pr = corrida(imgs['av'], sav, 0x48ba50, (otra, p, 0, 0, 0), p, 0, mant, False, 1, 1)
            _, r0, _ = corrida(imgs['orig'], sav, 0x48ba50, (otra, p, 0, 0, 0), p, 0, mant, False, 1, 1)
            check(r == r0 == [] and l == [] and pr, f'{sav} c{p} unidad en ciudad ajena: {l} {r}')
            # agrandar ciudad (costo 100, 300, 400 de la tanda)
            for ciudad in mias[:1]:
                for cost in (100, 300, 400):
                    args = (ciudad, 2, cost)
                    for oro, frena in ((piso + cost, False), (piso + cost - 1, True)):
                        l, r, pr = corrida(imgs['av'], sav, 0x405310, args, p, oro, mant, False, 1, 1)
                        if frena:
                            check(r == [] and pr and l == [[7, p, 1, 31, 2, cost, oro]],
                                  f'{sav} c{p} agrandar {cost} oro {oro}: debe frenar {l} {r} {pr}')
                        else:
                            check(r == [SIGUE] and l == [], f'{sav} c{p} agrandar {cost} oro {oro}: debe seguir {l} {r}')
                    for desc, hum, on, modo in (('humano', True, 1, 1), ('IA original', False, 1, 0),
                                                ('sin ia_on', False, 0, 1)):
                        l, r, _ = corrida(imgs['av'], sav, 0x405310, args, p, 0, mant, hum, on, modo)
                        check(r == [SIGUE] and l == [], f'{sav} c{p} agrandar {desc}: {l} {r}')
                l, r, _ = corrida(imgs['av'], sav, 0x405310, (ciudad, 2, 0), p, 0, mant, False, 1, 1)
                check(r == [SIGUE] and l == [], f'{sav} c{p} agrandar gratis: {l} {r}')
            # ahorro con destino: (costo, turno + 1 anotado, cuenta)
            for meta, cuenta in (((800, TURNO + 1), True), ((800, TURNO), True), ((800, TURNO - 1), False),
                                 ((800, 0), False), ((0, TURNO + 1), True)):
                extra = meta[0] if cuenta else 0; xg = 10 if cuenta else 0
                for ciudad in mias[:1]:
                    t, aj = 1, 2; cost = costo_unidad(m, p, t, aj); args = (ciudad, p, t, 0, aj)
                    _, r0, _ = corrida(imgs['orig'], sav, 0x48ba50, args, p, piso + extra + cost, mant, False, 1, 1)
                    for oro, frena in ((piso + extra + cost, False), (piso + extra + cost - 1, True)):
                        l, r, pr = corrida(imgs['av'], sav, 0x48ba50, args, p, oro, mant, False, 1, 1, meta)
                        if frena:
                            check(r == [] and pr and l == [[7, p, 1, 31, 1 + xg, cost, oro]],
                                  f'{sav} c{p} meta {meta} unidad oro {oro}: debe frenar {l} {r} {pr}')
                        else:
                            check(r == r0 and r0 and all(x[3] != 31 for x in l), f'{sav} c{p} meta {meta} unidad oro {oro}: debe seguir {l} {r}')
                    for oro, frena in ((piso + extra + 300, False), (piso + extra + 299, True)):
                        l, r, pr = corrida(imgs['av'], sav, 0x405310, (ciudad, 2, 300), p, oro, mant, False, 1, 1, meta)
                        if frena:
                            check(r == [] and pr and l == [[7, p, 1, 31, 2 + xg, 300, oro]],
                                  f'{sav} c{p} meta {meta} agrandar oro {oro}: debe frenar {l} {r} {pr}')
                        else:
                            check(r == [SIGUE] and l == [], f'{sav} c{p} meta {meta} agrandar oro {oro}: debe seguir {l} {r}')
                    for desc, hum, on, modo in (('humano', True, 1, 1), ('IA original', False, 1, 0), ('sin ia_on', False, 0, 1)):
                        l, r, _ = corrida(imgs['av'], sav, 0x48ba50, args, p, piso + cost, mant, hum, on, modo, meta)
                        _, r0, _ = corrida(imgs['orig'], sav, 0x48ba50, args, p, piso + cost, mant, hum, on, modo)
                        check(r == r0 and not any(x[3] == 31 for x in l), f'{sav} c{p} meta {meta} {desc}: {l} {r} {r0}')
    print(sav, n - antes, 'controles')
print(n, 'controles:', 'TODO OK' if ok else 'HAY FALLAS'); sys.exit(0 if ok else 1)
