# Prueba de juguete del transporte doble ("Carrier") sobre el exe parcheado, en unicorn: formar (crlink, 0x49d05d),
# seguir (crfollow, 0x49cdc7), defensa conjunta (crdef, 0x464c3d) y "Landing" anulado en una mitad (landchk).
# Uso: python prueba_carrier.py [DarklordAV.exe]   (por defecto C:\Warlords3\DarklordAV.exe; armarlo antes con build.py)
# Corre el código real del juego salvo 0x485e30, 0x49c960 y 0x49d450, que se reemplazan por un ret que anota la
# llamada. Cada caso lleva controles que no se tienen que tocar: un ejército propio lejos y uno ajeno al lado.
import sys, struct, pefile, capstone
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

pe = pefile.PE(sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe'); BASE = pe.OPTIONAL_HEADER.ImageBase
img = bytes(pe.get_memory_mapped_image())
SIZE = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

def jmp_target(va):
    ins = next(cs.disasm(img[va - BASE:va - BASE + 5], va)); assert ins.mnemonic == 'jmp', hex(va)
    return int(ins.op_str, 16)
def first_call(va):
    for ins in cs.disasm(img[va - BASE:va - BASE + 0x100], va):
        if ins.mnemonic == 'call': return int(ins.op_str, 16)
LANDCHK = first_call(jmp_target(0x4a5c6a))   # livexp -> landchk
SENT = 0x1ff000
P = 1
REG = ('EAX', 'EBX', 'ECX', 'EDX', 'ESI', 'EDI', 'EBP')

class Mundo:
    def __init__(s, bonos=('Ice', 'Carrier')):
        s.mu = mu = Uc(UC_ARCH_X86, UC_MODE_32)
        mu.mem_map(BASE, SIZE); mu.mem_write(BASE, img[:SIZE])
        mu.mem_map(0x100000, 0x100000)
        s.llamadas = []
        for va in (0x485e30, 0x49c960, 0x49d450):
            mu.mem_write(va, b'\xc3')
        for q in range(8):
            boat = 0x53c410 + (q * 16 + 15) * 0xfc + 0xb2
            mu.mem_write(boat, b''.join(t.encode().ljust(9, b'\0') for t in (list(bonos) + [''] * 4)[:4]))
        s.n = 0
        s.mu.mem_write(0x54fe50, struct.pack('<h', 1))

    def army(s, x, y, owner=P, emb=True, link=0, moves=10, alive=True, dest=(-1, -1)):
        s.n += 1; i = s.n; b = i * 0x1c
        s.mu.mem_write(b + 0x54fe52, struct.pack('<hhhh', x, y, *dest))
        s.mu.mem_write(b + 0x54fe5e, struct.pack('<HH', owner << 5, moves << 8))
        s.mu.mem_write(b + 0x54fe62, bytes([0, 0x40 if alive else 0, 8 if emb else 0]))
        s.mu.mem_write(b + 0x54fe6b, bytes([link]))
        s.mu.mem_write(0x54fe50, struct.pack('<h', i + 1))
        return i

    def get(s, i):
        b = i * 0x1c
        x, y, dx, dy = struct.unpack('<hhhh', s.mu.mem_read(b + 0x54fe52, 8))
        moves = (struct.unpack('<H', s.mu.mem_read(b + 0x54fe60, 2))[0] >> 8) & 0x7f
        return dict(x=x, y=y, dest=(dx, dy), moves=moves, link=s.mu.mem_read(b + 0x54fe6b, 1)[0])

    def group(s, ids, emb=True, p=P):
        g = p * 0x4f0
        s.mu.mem_write(g + 0x56ea90, struct.pack('<h', ids[0]))
        s.mu.mem_write(g + 0x56ea94, struct.pack('<8h', *(list(ids) + [0] * 8)[:8]))
        s.mu.mem_write(g + 0x56eaa8, struct.pack('<hBB', len(ids), 8 if emb else 0, 0))

    def run(s, start, end, regs, stack=b''):
        mu = s.mu
        esp = 0x180000
        mu.mem_write(esp, stack + struct.pack('<I', SENT))
        regs = dict(regs, ESP=esp)
        for k, v in regs.items(): mu.reg_write(globals()['UC_X86_REG_' + k], v)
        fin = {}
        def hook(uc, addr, size, _):
            if addr in (0x485e30, 0x49c960, 0x49d450):
                sp = uc.reg_read(UC_X86_REG_ESP)
                a = struct.unpack('<iii', uc.mem_read(sp + 4, 12))
                s.llamadas.append((addr, tuple(((v & 0xffff) ^ 0x8000) - 0x8000 for v in a[:3 if addr == 0x485e30 else 2])))
            if addr in (end, SENT):
                fin['at'] = addr; uc.emu_stop()
        mu.hook_add(UC_HOOK_CODE, hook)
        mu.emu_start(start, 0, count=2_000_000)
        out = {k: mu.reg_read(globals()['UC_X86_REG_' + k]) for k in REG + ('ESP', 'EFLAGS')}
        return fin.get('at'), out, esp

mal = 0
def check(nombre, cond, detalle=''):
    global mal
    mal += not cond
    print(f'{"OK " if cond else "MAL"} {nombre}' + ('' if cond else f'   {detalle}'))

def enc(dx, dy): return dx + 4 * dy + 5

# ---------------------------------------------------------------- formar (crlink)
def formar(code=4, bonos=('Ice', 'Carrier'), gemb=True, dest=(11, 10), t_emb=True, t_owner=P, na=5, nt=6):
    w = Mundo(bonos)
    A = [w.army(10, 10, dest=dest) for _ in range(na)]
    T = [w.army(11, 10, owner=t_owner, emb=t_emb, dest=(30, 30)) for _ in range(nt)]
    if dest != (11, 10) and dest[0] >= 0:
        T += [w.army(*dest, dest=(30, 30)) for _ in range(nt)]
    lejos = w.army(40, 40, link=0); ajeno = w.army(12, 10, owner=2)
    w.group(A, emb=gemb)
    entry = 0x150000
    w.mu.mem_write(entry, struct.pack('<hbbhh', code, P, 1, 0, 0))
    regs = dict(EAX=0x11, EBX=0x1234, ECX=0x22, EDX=0x33, ESI=entry, EDI=0x5678, EBP=0x9abc)
    at, out, esp = w.run(0x49d05d, None, regs, stack=struct.pack('<III', 0x5678, entry, 0x1234))
    ctl = w.get(lejos)['link'] == 0 and w.get(ajeno)['link'] == 0 and w.get(lejos)['dest'] == (-1, -1)
    ok_regs = at == SENT and out['ESP'] == esp + 16 and out['ESI'] == entry and out['EDI'] == 0x5678 and out['EBX'] == 0x1234
    return w, A, T, ctl and ok_regs

def formo(w, A, T, ea):
    return (all(w.get(i)['link'] == 0x80 | ea for i in A) and all(w.get(i)['link'] == 0x80 | (10 - ea) for i in T)
            and all(w.get(i)['dest'] == (-1, -1) for i in T)
            and w.llamadas == [(0x485e30, (P, -1, -1)), (0x49c960, (P, 1))])
def no_formo(w, A, T):
    return (all(w.get(i)['link'] == 0 for i in A + T) and all(w.get(i)['dest'] == (30, 30) for i in T)
            and w.llamadas == [(0x49c960, (P, 5))])

w, A, T, ok = formar(); check('formar: barco lleno al lado (este)', ok and formo(w, A, T, enc(1, 0)), (w.llamadas, [w.get(i) for i in A + T]))
w, A, T, ok = formar(dest=(11, 11)); check('formar: en diagonal', ok and all(w.get(i)['link'] == 0x80 | enc(1, 1) for i in A)
                                         and all(w.get(i)['link'] == 0x80 | enc(-1, -1) for i in T if w.get(i)['x'] == 11 and w.get(i)['y'] == 11), w.llamadas)
w, A, T, ok = formar(bonos=('', '', '', 'CARRIER')); check('formar: "CARRIER" en el 4o casillero', ok and formo(w, A, T, enc(1, 0)))
for nombre, kw in [('codigo 3', dict(code=3)), ('codigo 7', dict(code=7)), ('sin Carrier', dict(bonos=('Landing',))),
                   ('grupo no embarcado', dict(gemb=False)), ('destino a 2 casillas', dict(dest=(12, 10))),
                   ('destino sin barco embarcado', dict(t_emb=False)), ('destino de otro jugador', dict(t_owner=3)),
                   ('sin destino', dict(dest=(-1, -1)))]:
    w, A, T, ok = formar(**kw)
    check(f'no forma: {nombre}', ok and no_formo(w, A, T), (w.llamadas, [w.get(i) for i in A + T]))

# ---------------------------------------------------------------- seguir (crfollow)
# Proa: grupo que estaba en A = (10,10) y ya está en N. Popa en P = (11,10), apuntando a A.
def seguir(N=(9, 10), cost=2, bonos=('Carrier',), gemb=True, popa_link=None, queda=False, sin_enlace=False,
           popa_moves=10, muerto=False):
    w = Mundo(bonos)
    Ax, Ay = 10, 10
    G = [w.army(*N, link=0 if sin_enlace else 0x80 | enc(1, 0)) for _ in range(5)]
    Pp = [w.army(11, 10, link=0x80 | enc(-1, 0) if popa_link is None else popa_link, moves=popa_moves, dest=(30, 30))
          for _ in range(6)]
    dead = w.army(11, 10, link=0x80 | enc(-1, 0), alive=False) if muerto else None
    resto = w.army(10, 10, link=0x80 | enc(1, 0)) if queda else None
    lejos = w.army(40, 40); ajeno = w.army(12, 10, owner=2)
    w.group(G, emb=gemb)
    w.mu.mem_write(0x572990, struct.pack('<h', Ax)); w.mu.mem_write(0x572994, struct.pack('<h', Ay))
    w.mu.mem_write(0x4fe5f8, b'\x01')
    entry = 0x150000
    w.mu.mem_write(entry, struct.pack('<hbbhhhh', 0, P, cost, N[0], N[1], 0, 1))
    regs = dict(EAX=0x11, EBX=0x1234, ECX=0x22, EDX=0x33, ESI=entry, EDI=entry + 4, EBP=0x9abc)
    at, out, esp = w.run(0x49cdc7, 0x49cdce, regs, stack=bytes(0x14))
    ok_regs = (at == 0x49cdce and out['ESP'] == esp + 0x14 and out['ECX'] & 0xffff == N[1]
               and all(out[k] == regs[k] for k in ('EAX', 'EBX', 'EDX', 'ESI', 'EDI', 'EBP'))
               and (out['ECX'] & ~0xffff) == (0x22 & ~0xffff))
    ctl = w.get(lejos) == dict(x=40, y=40, dest=(-1, -1), moves=10, link=0) and w.get(ajeno)['x'] == 12
    if dead: ctl = ctl and w.get(dead)['x'] == 11
    return w, G, Pp, resto, ctl and ok_regs

def siguio(w, G, Pp, N, moves):
    en = enc(N[0] - 10, N[1] - 10)
    return (all(w.get(i) == dict(x=10, y=10, dest=(-1, -1), moves=moves, link=0x80 | en) for i in Pp)
            and all(w.get(i)['link'] == 0x80 | (10 - en) for i in G)
            and w.llamadas == [(0x49d450, (10, 10)), (0x49d450, (11, 10))] and w.mu.mem_read(0x4fe5f8, 1)[0] == 0)
def no_siguio(w, G, Pp, grupo_link=0):
    return (all(w.get(i)['x'] == 11 and w.get(i)['moves'] == 10 and w.get(i)['dest'] == (30, 30) for i in Pp)
            and all(w.get(i)['link'] == grupo_link for i in G) and w.llamadas == [] and w.mu.mem_read(0x4fe5f8, 1)[0] == 1)

w, G, Pp, _, ok = seguir(); check('sigue: proa al oeste', ok and siguio(w, G, Pp, (9, 10), 8), [w.get(i) for i in G + Pp] + [w.llamadas])
w, G, Pp, _, ok = seguir(N=(9, 9)); check('sigue: proa en diagonal', ok and siguio(w, G, Pp, (9, 9), 8))
w, G, Pp, _, ok = seguir(N=(10, 11)); check('sigue: proa al sur (de costado)', ok and siguio(w, G, Pp, (10, 11), 8))
w, G, Pp, _, ok = seguir(cost=3, popa_moves=1); check('sigue: movimientos de la popa no bajan de 0', ok and siguio(w, G, Pp, (9, 10), 0))
w, G, Pp, _, ok = seguir(muerto=True); check('sigue: un muerto en P no se mueve', ok and siguio(w, G, Pp, (9, 10), 8))
w, G, Pp, resto, ok = seguir(queda=True)
check('no sigue: queda parte en A (el resto conserva el enlace)', ok and no_siguio(w, G, Pp) and w.get(resto)['link'] == 0x80 | enc(1, 0))
w, G, Pp, _, ok = seguir(N=(11, 10)); check('no sigue: la proa entra en la popa', ok and no_siguio(w, G, Pp))
w, G, Pp, _, ok = seguir(bonos=('Landing',)); check('no sigue: sin Carrier', ok and no_siguio(w, G, Pp))
w, G, Pp, _, ok = seguir(gemb=False); check('no sigue: desembarcó', ok and no_siguio(w, G, Pp))
w, G, Pp, _, ok = seguir(popa_link=0); check('no sigue: la popa no está enlazada', ok and no_siguio(w, G, Pp))
w, G, Pp, _, ok = seguir(popa_link=0x80 | enc(0, -1)); check('no sigue: la popa apunta a otra casilla', ok and no_siguio(w, G, Pp))
w, G, Pp, _, ok = seguir(sin_enlace=True); check('nada: grupo sin enlace', ok and no_siguio(w, G, Pp))

# ---------------------------------------------------------------- defensa conjunta (crdef)
def defensa(nd=6, np_=5, bonos=('Carrier',), back=True, linked=True, emb=True):
    w = Mundo(bonos)
    D = [w.army(20, 20, owner=3, emb=emb, link=(0x80 | enc(0, 1)) if linked else 0) for _ in range(nd)]
    Q = [w.army(20, 21, owner=3, emb=emb, link=(0x80 | enc(0, -1)) if back else 0x80 | enc(1, 0)) for _ in range(np_)]
    w.army(40, 40, owner=3); w.army(21, 20, owner=2)
    frame = bytearray(0x30 + 64 + 8)
    frame[0x12:0x14] = struct.pack('<h', 0x7777)
    regs = dict(EAX=0x11, EBX=0x1234, ECX=0x22, EDX=0x33, ESI=0xabcd0000 | 20, EDI=0xdcba0000 | 20, EBP=0x9abc)
    at, out, esp = w.run(0x464c3d, 0x464c51, regs, stack=bytes(frame))
    n = struct.unpack('<h', w.mu.mem_read(esp + 0x12, 2))[0]
    buf = list(struct.unpack('<32h', w.mu.mem_read(esp + 0x30, 64)))
    # eax, ecx y edx ya los pisa el original (0x4411b0); el resto se conserva
    ok_regs = at == 0x464c51 and out['ESP'] == esp and all(out[k] == regs[k] for k in ('EBX', 'ESI', 'EDI', 'EBP'))
    return n, buf, D, Q, ok_regs

n, buf, D, Q, ok = defensa(); check('defensa: 6 + 5 de la otra mitad', ok and n == 11 and buf[:11] == D + Q and buf[11:] == [0] * 21, (n, buf))
n, buf, D, Q, ok = defensa(nd=8, np_=8); check('defensa: 8 + 8', ok and n == 16 and buf[:16] == D + Q, (n, buf))
for nombre, kw in [('sin Carrier', dict(bonos=('Landing',))), ('la otra no apunta de vuelta', dict(back=False)),
                   ('casilla sin enlace', dict(linked=False)), ('no embarcados', dict(emb=False))]:
    n, buf, D, Q, ok = defensa(**kw)
    check(f'defensa sola: {nombre}', ok and n == 6 and buf[:8] == D + [0, 0], (n, buf))
n, buf, D, Q, ok = defensa(nd=0); check('defensa: casilla vacía', ok and n == 0, (n, buf))

# ---------------------------------------------------------------- "Landing" en una mitad (landchk)
def landing(link=True, back=True, bonos=('Landing', 'Carrier'), emb=True):
    w = Mundo(bonos)
    G = [w.army(10, 10, link=(0x80 | enc(1, 0)) if link else 0) for _ in range(3)]
    w.army(11, 10, link=(0x80 | enc(-1, 0)) if back else 0)
    w.group(G, emb=emb)
    w.mu.mem_write(0x58715c, struct.pack('<h', P))
    regs = dict(EAX=0x11, EBX=0x1234, ECX=0x22, EDX=0x33, ESI=0x44, EDI=0x55, EBP=0x9abc)
    at, out, esp = w.run(LANDCHK, None, regs)
    ok_regs = at == SENT and out['ESP'] == esp + 4 and all(out[k] == regs[k] for k in REG)
    return ('SI' if not out['EFLAGS'] & 0x40 else 'NO'), ok_regs

for nombre, kw, esp_ in [('barco suelto', dict(link=False), 'SI'), ('mitad enlazada', dict(), 'NO'),
                         ('bit suelto (la otra mitad se fue)', dict(back=False), 'SI'),
                         ('bit con barco sin Carrier', dict(bonos=('Landing',)), 'SI'),
                         ('sin Landing', dict(link=False, bonos=('Carrier',)), 'NO'),
                         ('no embarcado', dict(link=False, emb=False), 'NO')]:
    r, ok = landing(**kw)
    check(f'Landing: {nombre} -> {esp_}', ok and r == esp_, (r, ok))

print('TODO OK' if not mal else f'{mal} MAL'); sys.exit(1 if mal else 0)
