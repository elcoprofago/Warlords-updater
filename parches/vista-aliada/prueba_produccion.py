# Prueba emulada del freno de producción (pr_ok, pr_unit; ia\PENDIENTE-ia-economia.md, paso 4.2): corre la función de
# producción real 0x43b930(p) sobre partidas guardadas, con todas las ciudades de p a punto de terminar su unidad
# (+0xd8 = 1), en el exe parcheado y en el original. Las creaciones (0x43b120 y 0x43b390, dirigida) y el reinicio de la
# cuenta (0x4ae250) se interceptan y se anotan. Regla: con ia_on, IA en prueba y bando de la computadora, una ciudad
# produce solo si mantenimiento + lo producido en el turno + tercio de la unidad nueva (truncado, mínimo 1; paso 4.3)
# <= ingreso;
# si no, no crea ni reinicia, deja la cuenta en 1 y anota el evento 32 (x = tipo, y = total, n = ingreso).
# Paso 4.15: además, si mantenimiento entero de los ejércitos de p (al primer intento del turno) + lo producido entero en
# el turno + la unidad nueva entera > ingreso + oro / 4 (oro negativo = 0), no sale y anota el evento 40 (mismos campos;
# n = ingreso + oro / 4). Los casos del tercio corren con oro 32000 para que la regla nueva no intervenga.
# Controles que deben seguir como el original: humano, IA original (ia_mode 0), ingreso holgado. Sin ia_on (sin
# IA.INI, partidas del ranking): decide como la de prueba y no escribe eventos.
# Uso: python prueba_produccion.py <DarklordAV.exe> <Darklord.exe> <ia_on hex> <ia_mode hex> <partida.SAV> [...]
import pefile, struct, sys
from unicorn import *
from unicorn.x86_const import *

AV, ORIG, IA_ON, IA_MODE = sys.argv[1], sys.argv[2], int(sys.argv[3], 16), int(sys.argv[4], 16)
SAVS = sys.argv[5:]
pes = {k: pefile.PE(f) for k, f in (('av', AV), ('orig', ORIG))}
imgs = {k: pe.get_memory_mapped_image() for k, pe in pes.items()}
IMPS = [i.address for e in pes['orig'].DIRECTORY_ENTRY_IMPORT for i in e.imports]   # el resto: vuelven sin hacer nada
IAT = {'fopen': 0x5a9bdc, 'fclose': 0x5a9be4, 'fprintf': 0x5a9bf4}
STUB, CALLER = 0xdeac0000, 0xdead0000
CITY, CSZ = 0x537e2c, 0xde

def cstr(mu, a):
    s = b''
    while (c := mu.mem_read(a + len(s), 1)[0]): s += bytes([c])
    return s.decode('latin1')

def load(sav):
    b = open(sav, 'rb').read(); m = {}; off = 0x6d
    for va, n in ((0x503e00, 0x12), (0x503e58, 0x32000), (0x535ed0, 0xa96), (0x536b30, 0x2d894)):
        m[va] = b[off:off + n]; off += n
    return m

def maquina(img, sav, p, ing, mant, humano, on, modo, turno=7, oro=32000):
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(0x400000, (len(img) + 0xfff) & ~0xfff); mu.mem_write(0x400000, img)
    mu.mem_map(0x10000000, 0x100000); mu.mem_map(STUB, 0x1000); mu.mem_map(CALLER, 0x1000)
    for va, d in load(sav).items(): mu.mem_write(va, d)
    ncity = struct.unpack('<h', mu.mem_read(0x537e2a, 2))[0]
    for i in range(ncity):   # todas las ciudades de p con la unidad lista, sin dirigir
        c = CITY + i * CSZ
        if mu.mem_read(c + 0xa5, 1)[0] == p:
            mu.mem_write(c + 0xd8, b'\x01'); mu.mem_write(c + 0xd9, b'\x00')
    mu.mem_write(0x536c12 + p * 0x1f8, struct.pack('<h', -1 if humano else 0))
    mu.mem_write(0x5643d8 + 2 * p, struct.pack('<h', mant)); mu.mem_write(0x5643f0 + 2 * p, struct.pack('<h', ing))
    mu.mem_write(0x503328, struct.pack('<h', turno))
    mu.mem_write(0x536c14 + p * 0x1f8, struct.pack('<h', oro))
    mu.mem_write(0x537ce8, struct.pack('<h', (p + 1) % 8))
    if img is imgs['av']: mu.mem_write(IA_ON, bytes([on, 0, 0, 0])); mu.mem_write(IA_MODE, bytes([modo] * 8))
    return mu, ncity

def corrida(mu, fn, args):
    names = list(IAT); lines, res = [], []
    for a in IMPS: mu.mem_write(a, struct.pack('<I', STUB + 0x800))
    mu.mem_write(STUB + 0x800, bytes([0xc3]))
    for k, n in enumerate(names):
        mu.mem_write(IAT[n], struct.pack('<I', STUB + k * 16)); mu.mem_write(STUB + k * 16, b'\xc3')
    def arg(i): return struct.unpack('<I', mu.mem_read(mu.reg_read(UC_X86_REG_ESP) + 4 + 4 * i, 4))[0]
    def iat(mu, addr, size, _):
        if addr >= STUB + 0x800: mu.reg_write(UC_X86_REG_EAX, 0); return
        n = names[(addr - STUB) // 16]; ret = 0
        if n == 'fopen': ret = 0x1000 if cstr(mu, arg(0)).endswith('IA_EVT.CSV') else 0
        elif n == 'fprintf':
            fmt = cstr(mu, arg(1))
            lines.append([struct.unpack('<i', struct.pack('<I', arg(2 + i)))[0] for i in range(fmt.count('%d'))])
        mu.reg_write(UC_X86_REG_EAX, ret)
    h = [mu.hook_add(UC_HOOK_CODE, iat, begin=STUB, end=STUB + 0xfff)]
    def ret0(mu, addr, size, _):
        esp = mu.reg_read(UC_X86_REG_ESP); r = struct.unpack('<I', mu.mem_read(esp, 4))[0]
        if addr in (0x43b120, 0x43b390, 0x4ae250): res.append((addr, arg(0) & 0xffff, arg(1) & 0xffff))
        mu.reg_write(UC_X86_REG_ESP, esp + 4); mu.reg_write(UC_X86_REG_EIP, r)
    for a in (0x43c1e0, 0x43b120, 0x43b390, 0x4ae250, 0x431e60, 0x4a2170):
        h.append(mu.hook_add(UC_HOOK_CODE, ret0, begin=a, end=a))
    mu.mem_write(CALLER, b'\xe8' + struct.pack('<I', (fn - (CALLER + 5)) & 0xffffffff))
    sp = 0x10000000 + 0x80000
    mu.mem_write(sp, b''.join(struct.pack('<I', a & 0xffffffff) for a in args))
    regs = {UC_X86_REG_EBX: 0x11110000, UC_X86_REG_ESI: 0x2222abcd, UC_X86_REG_EBP: 0x11110002, UC_X86_REG_EDI: 0x3333}
    for r, v in regs.items(): mu.reg_write(r, v)
    mu.reg_write(UC_X86_REG_ESP, sp)
    mu.emu_start(CALLER, CALLER + 5, count=50_000_000)
    pres = mu.reg_read(UC_X86_REG_EIP) == CALLER + 5 and all(mu.reg_read(r) == v for r, v in regs.items())
    for x in h: mu.hook_del(x)
    return lines, res, pres

def mant_unidad(sav, p, ciudad, tipo):   # salida[4] de 0x43b6d0 en el original, como la usa 0x43b120
    mu, _ = maquina(imgs['orig'], sav, p, 0, 0, False, 0, 0)
    mu.mem_map(0x20000000, 0x1000)
    corrida(mu, 0x43b6d0, (ciudad, p, tipo, 0x20000000))
    return mu.mem_read(0x20000000 + 4, 1)[0] & 0xf

ok = True; n = 0
def me_modelo(mu, p):   # pr_me: mantenimiento entero de los ejércitos vivos de p (como mt_evt, sin mirar la casilla)
    n = struct.unpack('<h', mu.mem_read(0x54fe50, 2))[0]; t = 0
    for i in range(n):
        a = 0x54fe50 + i * 0x1c; b = mu.mem_read(a, 0x1c)
        if not b[0x13] & 0x40: continue
        own = struct.unpack('<H', b[0xe:0x10])[0] & 0x1e0
        if own >= 0x100 or own >> 5 != p: continue
        if struct.unpack('<h', b[2:4])[0] < 0 or struct.unpack('<h', b[4:6])[0] < 0: continue
        m = (struct.unpack('<H', b[0x10:0x12])[0] & 0xf0) >> 4
        if b[0x14] & 8 and m <= 4: m = 4
        t += m
    return t

def me_al_producir(sav, p):   # me_modelo leído en el primer intento de producción (0x43bdf2): 0x43b930 toca
    mu, _ = maquina(imgs['av'], sav, p, 30000, 0, False, 1, 1)   # ejércitos antes de producir, y pr_me ve eso
    v = []
    def hk(mu, a, s, _):
        if not v: v.append(me_modelo(mu, p))
    mu.hook_add(UC_HOOK_CODE, hk, begin=0x43bdf2, end=0x43bdf2)
    corrida(mu, 0x43b930, (p,))
    return v[0]

def tercio(m):   # como 0x4406b0 en una casilla de ciudad
    return max(1, m // 3) if m > 0 else 0

def check(c, msg):
    global ok, n; n += 1
    if not c: print('    FALLA', msg)
    ok &= c

def cuenta(mu, ncity):
    return {i: mu.mem_read(CITY + i * CSZ + 0xd8, 1)[0] for i in range(ncity)}

for sav in SAVS:
    antes = n
    for p in range(8):
        mu0, ncity = maquina(imgs['orig'], sav, p, 0, 0, False, 0, 0)
        mias = [i for i in range(ncity) if mu0.mem_read(CITY + i * CSZ + 0xa5, 1)[0] == p
                and mu0.mem_read(CITY + i * CSZ + 0xa4, 1)[0] > 0]
        if not mias: continue
        tipos = {i: mu0.mem_read(CITY + i * CSZ + 0xd7, 1)[0] for i in mias}
        u = {i: tercio(mant_unidad(sav, p, i, tipos[i])) for i in mias}
        _, r0, _ = corrida(mu0, 0x43b930, (p,))
        hechas0 = [c for a, c, _ in r0 if a == 0x43b120]
        check(hechas0 == mias, f'{sav} c{p}: el original produce en {hechas0}, se esperaba {mias}')
        for mant in (0, 25):
            # ingresos: holgado (todas salen), justo para k unidades, justo uno menos, cero
            tot = [mant + sum(u[i] for i in mias[:k]) for k in range(len(mias) + 1)]
            casos = [(30000, len(mias)), (0, 0 if mant or u[mias[0]] else None)]
            for k in range(1, len(mias) + 1):
                ing = tot[k]   # el menor ingreso con total <= ingreso
                casos += [(ing, k), (ing - 1, k - 1)]
            for ing, k in casos:
                if k is None: continue
                # con ingreso fijo, las que salen son las primeras mientras entren; después de la primera frenada pueden
                # entrar otras más baratas: se calcula ciudad por ciudad
                acc, sale, frena = mant, [], []
                for i in mias:
                    if acc + u[i] <= ing: acc += u[i]; sale.append(i)
                    else: frena.append((i, acc + u[i]))
                mu, _ = maquina(imgs['av'], sav, p, ing, mant, False, 1, 1)
                l, r, pr = corrida(mu, 0x43b930, (p,))
                cre = [c for a, c, _ in r if a == 0x43b120]; rei = [c for a, c, _ in r if a == 0x4ae250]
                cu = cuenta(mu, ncity)
                ev = [x for x in l if x[3] == 32]
                check(pr and cre == sale and rei == sale, f'{sav} c{p} ing {ing} mant {mant}: sale {cre} / reinicia {rei}, se esperaba {sale}')
                check(all(cu[i] == 1 for i, _ in frena), f'{sav} c{p} ing {ing}: la cuenta de las frenadas no quedó en 1')
                check(ev == [[7, p, 1, 32, tipos[i], t, ing] for i, t in frena], f'{sav} c{p} ing {ing}: eventos {ev}')
                # misma corrida otra vez en el mismo turno: lo producido ya cuenta (no sale nada nuevo que no entre)
                if sale and frena:
                    for i in mias: mu.mem_write(CITY + i * CSZ + 0xd8, b'\x01')
                    _, r2, _ = corrida(mu, 0x43b930, (p,))
                    acc2, sale2 = acc, []
                    for i in mias:
                        if acc2 + u[i] <= ing: acc2 += u[i]; sale2.append(i)
                    check([c for a, c, _ in r2 if a == 0x43b120] == sale2, f'{sav} c{p} ing {ing}: 2.a pasada {r2} vs {sale2}')
                    # turno siguiente: se reinicia lo acumulado
                    mu.mem_write(0x503328, struct.pack('<h', 8))
                    for i in mias: mu.mem_write(CITY + i * CSZ + 0xd8, b'\x01')
                    _, r3, _ = corrida(mu, 0x43b930, (p,))
                    check([c for a, c, _ in r3 if a == 0x43b120] == sale, f'{sav} c{p} ing {ing}: turno siguiente {r3}')
            # paso 4.15: ingreso holgado para la regla del tercio; el oro decide con la regla del entero
            ent = {i: mant_unidad(sav, p, i, tipos[i]) for i in mias}
            me = me_al_producir(sav, p)
            ingE = 100
            for k in range(len(mias) + 1):
                lim = me + sum(ent[i] for i in mias[:k])   # el menor ingreso + oro/4 con el que salen las k primeras
                for oro in (4 * (lim - ingE), 4 * (lim - ingE) + 3, 4 * (lim - ingE) - 1):
                    if oro < 0: continue
                    L = ingE + oro // 4
                    acc, sale, frena = me, [], []
                    for i in mias:
                        if acc + ent[i] <= L: acc += ent[i]; sale.append(i)
                        else: frena.append((i, acc + ent[i]))
                    mu, _ = maquina(imgs['av'], sav, p, ingE, 0, False, 1, 1, oro=oro)
                    # la regla del tercio no debe frenar: ingreso de la regla 1 = ingE; se fuerza holgura con mant 0
                    # y se comprueba antes que el tercio entre
                    if sum(u[i] for i in mias) > ingE: continue
                    l, r, pr = corrida(mu, 0x43b930, (p,))
                    cre = [c for a, c, _ in r if a == 0x43b120]
                    ev = [x for x in l if x[3] in (32, 40)]
                    check(pr and cre == sale, f'{sav} c{p} 4.15 oro {oro}: sale {cre}, se esperaba {sale}')
                    check(ev == [[7, p, 1, 40, tipos[i], t, L] for i, t in frena], f'{sav} c{p} 4.15 oro {oro}: eventos {ev}, se esperaba {frena} L {L}')
                    check(all(cuenta(mu, ncity)[i] == 1 for i, _ in frena), f'{sav} c{p} 4.15: cuenta')
            # oro negativo cuenta 0
            mu, _ = maquina(imgs['av'], sav, p, 30000, 0, False, 1, 1, oro=-500)
            l, r, pr = corrida(mu, 0x43b930, (p,))
            check(pr and not any(x[3] == 40 for x in l), f'{sav} c{p} 4.15 oro negativo con ingreso holgado frenó')
            for desc, hum, on, modo in (('humano', True, 1, 1), ('IA original', False, 1, 0)):
                mu, _ = maquina(imgs['av'], sav, p, 0, mant, hum, on, modo)
                l, r, pr = corrida(mu, 0x43b930, (p,))
                mo, _ = maquina(imgs['orig'], sav, p, 0, mant, hum, on, modo)
                _, ro, _ = corrida(mo, 0x43b930, (p,))
                check(pr and r == ro and not any(x[3] == 32 for x in l), f'{sav} c{p} {desc}: {r} vs {ro}')
            # sin IA.INI (partidas del ranking, 1.0.218.0): decide igual que la de prueba, sin escribir eventos
            mu, _ = maquina(imgs['av'], sav, p, 0, mant, False, 1, 1)
            _, r1, _ = corrida(mu, 0x43b930, (p,))
            mu, _ = maquina(imgs['av'], sav, p, 0, mant, False, 0, 1)
            l, r, pr = corrida(mu, 0x43b930, (p,))
            check(pr and r == r1 and l == [], f'{sav} c{p} sin IA.INI: {r} vs prueba {r1}, eventos {l}')
    print(sav, n - antes, 'controles')
print(n, 'controles:', 'TODO OK' if ok else 'HAY FALLAS'); sys.exit(0 if ok else 1)
