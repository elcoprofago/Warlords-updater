# Prueba de juguete: la IA derriba puentes por criterio propio (ai_brraze en 0x4c4d3a) y el caso "Raze Site" del
# evaluador de misiones lee bien la casilla de un puente (qb_ailoc3 en 0x435d53), en unicorn.
# Uso: python prueba_iarazea.py [DarklordAV.exe] [Darklord.exe] [casos al azar]
#      (por defecto C:\Warlords3\DarklordAV.exe y el original C:\Warlords3\Darklord.exe; armar antes con build.py)
# Mapa de 64x64 de tierra con el puente P (20,10)-(21,10). La pila del jugador 2 (computadora) termina un movimiento de
# 0x4c4a10 (se entra en 0x4c4d3a con el destino en [esp+0x38]/[esp+0x3c]) con el líder (ejército 1) donde diga el caso.
# La decisión se compara contra un modelo en Python de la cuenta de 0x41f4b0 llevada al puente (ver ai_brraze en
# build.py); la distancia (0x4974a0) y la hostilidad (0x49c1c0) corren de verdad. El azar (0x4deb20), el aviso a la
# misión (0x461a60), la orden de red (0x4b9550) y la pausa (0x4275b0) van guionados y se anotan.
import sys, math, random, struct, pefile
from unicorn import Uc, UcError, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_HOOK_MEM_READ_UNMAPPED
from unicorn.x86_const import *
from keystone import Ks, KS_ARCH_X86, KS_MODE_32

def load(path):
    pe = pefile.PE(path)
    return pe.OPTIONAL_HEADER.ImageBase, bytes(pe.get_memory_mapped_image()), (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
AV = load(sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe')
ORIG = load(sys.argv[2] if len(sys.argv) > 2 else r'C:\Warlords3\Darklord.exe')
NRAND = int(sys.argv[3]) if len(sys.argv) > 3 else 3000

W = H = 64; SHIFT = 8; LAND, WATER = 2, 3
AI, ENEMY, FRIEND = 2, 3, 4
HERO, OTHER = 1, 2
BC = lambda x, y: 0x2000 + (y << 7) + x
P = [(20, 10), (21, 10)]; PC = BC(20, 10)
HEADS = [(19, 9), (19, 10), (19, 11), (20, 9), (20, 11), (21, 9), (21, 11), (22, 9), (22, 10), (22, 11)]
STUB = 0x100000; STACK = 0x200000; END = 0x1fff00
STUBS = {0x4deb20: 'azar', 0x461a60: 'evento', 0x4b9550: 'orden', 0x4275b0: 'pausa', 0x4b9020: 'fin'}

FTOL = STUB + 0x100
FTOL_CODE = bytes(Ks(KS_ARCH_X86, KS_MODE_32).asm('''
    sub esp, 12
    fnstcw word ptr [esp + 8]
    mov ax, word ptr [esp + 8]
    or ax, 0xc00
    mov word ptr [esp + 10], ax
    fldcw word ptr [esp + 10]
    fistp qword ptr [esp]
    fldcw word ptr [esp + 8]
    mov eax, dword ptr [esp]
    mov edx, dword ptr [esp + 4]
    add esp, 12
    ret''', FTOL)[0])

def tile_va(x, y): return ((y * 10) << SHIFT) + x * 10 + 0x503e58

def caso(**kw):
    c = dict(cur=AI, human=False, raze=2, stack=True, alive=True, leader=(19, 10), dest=(5, 10), temp=3, flag=0, r=10,
             dip={}, cities=[], armies=[], razed=False)
    c.update(kw); return c

class Bench:
    def __init__(self, c, exe=AV):
        base, img, size = exe
        mu = self.mu = Uc(UC_ARCH_X86, UC_MODE_32)
        mu.mem_map(base, size); mu.mem_write(base, img[:size])
        mu.mem_map(STUB, 0x10000); mu.mem_map(STACK - 0x10000, 0x10000)
        mu.mem_write(0x503e00, struct.pack('<HH', W, H)); mu.mem_write(0x503e06, bytes([SHIFT]))
        for t, cls in ((LAND, 0), (WATER, 1)):
            mu.mem_write(0x535f0c + t * 0x58, struct.pack('<H', cls))
        for y in range(H):
            for x in range(W): self.set_tile(x, y, LAND, 0, 0x05)
        for x, y in P:
            if c['razed']: self.set_tile(x, y, WATER, 0, 0x85)
            else: self.set_tile(x, y, WATER, 1, 0x05)
        mu.mem_write(0x537ce8, struct.pack('<h', c['cur'])); mu.mem_write(0x4fb0ec, struct.pack('<h', AI))
        for p in range(8): mu.mem_write(0x536c12 + p * 0x1f8, struct.pack('<h', 0))
        if c['human']: mu.mem_write(0x536c12 + AI * 0x1f8, struct.pack('<h', -1))
        mu.mem_write(0x53c393, bytes([c['raze']]))
        mu.mem_write(0x560e52, struct.pack('<h', 0))
        for p in range(8): mu.mem_write(0x561ef9 + p * 0x49a, bytes([c['temp'] if p == AI else 0]))
        for q in range(9): mu.mem_write(0x55ee4c + AI * 56 + q, bytes([c['dip'].get(q, 2)]))
        # ciudades: (x, y, viva, dueño)
        mu.mem_write(0x537e2a, struct.pack('<h', len(c['cities'])))
        for i, (x, y, alive, owner) in enumerate(c['cities']):
            o = i * 0xde
            mu.mem_write(0x537e2c + o, struct.pack('<hh', x, y)); mu.mem_write(0x537e30 + o, b'Ciudad\0')
            mu.mem_write(0x537ed0 + o, bytes([alive, owner]))
        # ejércitos: el líder y los del caso ((x, y), dueño)
        arm = [(HERO, c['leader'], AI, c['alive'], c['flag'])] + \
              [(OTHER + i, xy, o, True, 0) for i, (xy, o) in enumerate(c['armies'])]
        mu.mem_write(0x54fe50, struct.pack('<h', 1 + max(a for a, *_ in arm)))
        for a, (x, y), owner, alive, flag in arm:
            r = a * 0x1c
            mu.mem_write(0x54fe52 + r, struct.pack('<hh', x, y))
            mu.mem_write(0x54fe5e + r, struct.pack('<H', owner << 5))
            mu.mem_write(0x54fe63 + r, bytes([0x40 if alive else 0]))
            mu.mem_write(0x54fe6c + r, struct.pack('<H', (flag << 10) | 0x8003))   # bits ajenos alrededor del grupo
        s = 0x56ea90 + AI * 0x4f0
        mu.mem_write(s, struct.pack('<hh', HERO if c['stack'] else 0, HERO if c['stack'] else 0))
        self.r = c['r']; self.calls = []
        for va in STUBS: mu.mem_write(va, b'\xc3')
        mu.mem_write(FTOL, FTOL_CODE); mu.mem_write(0x5a9ba8, struct.pack('<I', FTOL))
        mu.mem_write(END, b'\xf4')
        mu.hook_add(UC_HOOK_CODE, self.hook)

    def set_tile(self, x, y, w0, struct_, b9):
        t = tile_va(x, y)
        self.mu.mem_write(t, struct.pack('<H', w0)); self.mu.mem_write(t + 3, bytes([struct_]))
        self.mu.mem_write(t + 9, bytes([b9]))

    def arg(self, k):
        esp = self.mu.reg_read(UC_X86_REG_ESP)
        return struct.unpack('<i', self.mu.mem_read(esp + 4 + 4 * k, 4))[0]
    def sarg(self, k): return struct.unpack('<h', struct.pack('<H', self.arg(k) & 0xffff))[0]

    def hook(self, uc, addr, size, _):
        if addr in self.stops:
            self.end = addr; uc.emu_stop(); return
        if addr in STUBS:
            k = STUBS[addr]; s = self.sarg; ret = 0
            if k == 'azar': self.calls.append((k, s(0), s(1))); ret = self.r
            elif k == 'evento': self.calls.append((k,) + tuple(s(i) for i in range(6)))
            elif k == 'orden': self.calls.append((k, s(0), s(1)))
            else: self.calls.append(k)
            uc.reg_write(UC_X86_REG_EAX, ret)

    def run(self, start, frame, regs, stops):
        mu = self.mu
        esp = STACK - 0x400
        mu.mem_write(esp, frame + bytes(0x40))
        for k, v in regs.items(): mu.reg_write(globals()['UC_X86_REG_' + k], v)
        mu.reg_write(UC_X86_REG_ESP, esp)
        self.stops = set(stops) | {END}; self.end = None
        mu.emu_start(start, 0, count=20000000)
        self.esp0 = esp
        return self.end
    def reg(self, k): return self.mu.reg_read(globals()['UC_X86_REG_' + k])

REGS = dict(EAX=0x11111111, ECX=0x22222222, EDX=0x33333333, EBX=0x44444444, ESI=0x55555555, EDI=0x66666666,
            EBP=0x77777777)

def go(c, exe=AV):
    """Entra en 0x4c4d3a (fin de 0x4c4a10) y para en 0x4c4d58 (pila no vacía) o 0x4c4d68 (vacía)."""
    b = Bench(c, exe)
    frame = bytes(0x38) + struct.pack('<ii', *c['dest'])
    end = b.run(0x4c4d3a, frame, REGS, (0x4c4d58, 0x4c4d68))
    ok = (end == (0x4c4d58 if c['stack'] else 0x4c4d68) and b.reg('ESP') == b.esp0
          and all(b.reg(k) == REGS[k] for k in ('EBX', 'ESI', 'EDI', 'EBP'))
          and b.reg('EAX') == AI * 0x4f0 and b.reg('ECX') & 0xffff == AI)   # lo que deja el código original
    return dict(ok=ok, end=end, calls=b.calls, temp=b.mu.mem_read(0x561ef9 + AI * 0x49a, 1)[0])
RAZE = lambda code=PC: [('evento', 6, HERO, 0, 0, code, 1), ('orden', code, AI), 'pausa']
def razes(g): return [c for c in g['calls'] if c != ('azar', 1, 20)]

# ---- modelo
def kd(a, b): return max(abs(a[0] - b[0]), abs(a[1] - b[1]))
def edist(a, b): return int(math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2))
def hostile(q, dip): return q != AI and (q == 8 or dip.get(q, 2) == 2)
def model(c):
    if c['cur'] != AI or c['human'] or not (c['raze'] & 6) or not c['stack'] or not c['alive']: return False
    t, flag = c['temp'], c['flag']
    if t == 0 and flag == 0: return False
    if c['razed'] or c['leader'] in P or kd(c['leader'], P[0]) > 1 and kd(c['leader'], P[1]) > 1: return False
    if any(xy in P for xy, _ in c['armies']): return False
    sd = kd(c['leader'], c['dest'])
    for tl in P:
        if kd(tl, c['dest']) <= 1 or kd(tl, c['dest']) < sd: return False
    s = (-2 if t == 0 else 0) + 1
    live = [(i, ct) for i, ct in enumerate(c['cities']) if ct[2]]
    if live:
        owner = min(live, key=lambda ic: (kd(P[0], ic[1][:2]), ic[0]))[1][3]
        if owner != 8:
            if not hostile(owner, c['dip']): return False
            if flag: s += 1
    near = sorted(live, key=lambda ic: (edist(P[0], ic[1][:2]), ic[0]))[:12]
    for i, (x, y, _, o) in near:
        d = edist(P[0], (x, y))
        if d == 0 or d > 30: continue
        w = 2 if d < 15 else 1
        if o == AI: s -= w
        elif o != 8 and hostile(o, c['dip']): s += w
    k = sum(1 for _, ct in live if ct[3] == AI)
    s += (k > 5) + (k > 15)
    if c['r'] >= 19: return False
    return t + s >= 5

res = []
def check(nombre, cond, detalle=''):
    res.append(cond); print(f'{"OK " if cond else "MAL"} {nombre}' + (f'   [{detalle}]' if not cond and detalle else ''))

def named(nombre, esperado, **kw):
    c = caso(**kw); g = go(c)
    m = model(c)
    check(f'{nombre}: {"derriba" if esperado else "no derriba"}', g['ok'] and m == esperado
          and razes(g) == (RAZE() if esperado else []), f'modelo {m} {g}')
    return g

# Ciudad enemiga dueña del puente, cerca: (23,12) del jugador 3 (a 3 de distancia). temp 3 + 1 (sin producción)
# + 2 (enemiga a < 15) = 6 >= 5.
ENEMY_CITY = (23, 12, 1, ENEMY)
named('base: líder en la cabecera oeste, destino al oeste, ciudad enemiga cerca', True, cities=[ENEMY_CITY])
g = go(caso(cities=[ENEMY_CITY]), ORIG)
check('control: Darklord.exe original en el mismo caso no derriba nada', g['ok'] and g['calls'] == [], g)
for h in HEADS:
    dest = {9: (20, 0), 11: (20, 63)}.get(h[1], (60, 10) if h[0] == 22 else (5, 10))   # hacia afuera del puente
    c = caso(cities=[ENEMY_CITY], leader=h, dest=dest)
    g = go(c)
    check(f'cabecera {h}, destino {dest}: derriba', g['ok'] and razes(g) == RAZE() and model(c), g)
named('líder sobre el puente', False, cities=[ENEMY_CITY], leader=(20, 10))
named('líder lejos', False, cities=[ENEMY_CITY], leader=(10, 10))
named('puente ya derribado', False, cities=[ENEMY_CITY], razed=True)
named('turno de otro jugador', False, cities=[ENEMY_CITY], cur=ENEMY)
named('jugador humano', False, cities=[ENEMY_CITY], human=True)
named('opción de arrasar apagada', False, cities=[ENEMY_CITY], raze=0)
named('opción de arrasar = 4', True, cities=[ENEMY_CITY], raze=4)
named('sin pila', False, cities=[ENEMY_CITY], stack=False)
named('líder muerto', False, cities=[ENEMY_CITY], alive=False)
named('ejército enemigo sobre el puente', False, cities=[ENEMY_CITY], armies=[((21, 10), ENEMY)])
named('ejército propio sobre el puente', False, cities=[ENEMY_CITY], armies=[((20, 10), AI)])
named('ejércitos en otro lado (control)', True, cities=[ENEMY_CITY], armies=[((30, 30), ENEMY), ((19, 11), AI)])
# destino: por delante, hacia el puente, por detrás
named('destino del otro lado: el puente está por delante', False, cities=[ENEMY_CITY], dest=(40, 10))
named('destino en la cabecera de enfrente', False, cities=[ENEMY_CITY], dest=(22, 10))
named('destino en la misma cabecera (la misión de ai_brq)', False, cities=[ENEMY_CITY], dest=(19, 10))
named('destino a 2 del puente, por detrás', True, cities=[ENEMY_CITY], dest=(18, 10), leader=(19, 10))
named('destino a la misma distancia que la pila (empate: no está por delante)', True, cities=[ENEMY_CITY],
      leader=(19, 10), dest=(19, 25))
named('destino un paso más cerca del puente que de la pila', False, cities=[ENEMY_CITY], leader=(20, 9), dest=(20, 40))
# dueño del puente
named('ciudad dueña propia', False, cities=[(23, 12, 1, AI), (30, 10, 1, ENEMY)])
named('ciudad dueña aliada (diplomacia 0)', False, cities=[(23, 12, 1, FRIEND)], dip={FRIEND: 0})
named('ciudad dueña en paz (diplomacia 1)', False, cities=[(23, 12, 1, FRIEND)], dip={FRIEND: 1})
named('ciudad dueña neutral: no descarta, sin bono', True, cities=[(23, 12, 1, 8), (25, 12, 1, ENEMY)], temp=2)
named('ciudad dueña muerta: manda la viva siguiente (propia)', False, cities=[(21, 12, 0, ENEMY), (23, 12, 1, AI),
                                                                              (30, 10, 1, ENEMY)])
# temperamento y bandera
named('temperamento 0 sin bandera', False, cities=[ENEMY_CITY], temp=0)
named('temperamento 0 con bandera: -2 +1 +1 +2 = 2 < 5', False, cities=[ENEMY_CITY], temp=0, flag=3)
named('temperamento 0 con bandera y muchas enemigas cerca', True, temp=0, flag=1,
      cities=[ENEMY_CITY] + [(18 + i, 14, 1, ENEMY) for i in range(3)])
named('temperamento 1: 1 + 1 + 2 = 4', False, cities=[ENEMY_CITY], temp=1)
named('temperamento 1 con bandera: 5', True, cities=[ENEMY_CITY], temp=1, flag=15)
named('temperamento 2 + ciudad enemiga lejos (peso 1): 4', False, cities=[(36, 10, 1, ENEMY)], temp=2)
named('temperamento 2 + ciudad enemiga a 14 (peso 2): 5', True, cities=[(34, 10, 1, ENEMY)], temp=2)
named('temperamento 2 + ciudad enemiga a 31: no cuenta', False, cities=[(51, 10, 1, ENEMY)], temp=2)
named('temperamento 3 + propia cerca resta 2', False, cities=[ENEMY_CITY, (19, 13, 1, AI)], temp=3)
# azar
named('azar 18', True, cities=[ENEMY_CITY], r=18)
named('azar 19', False, cities=[ENEMY_CITY], r=19)
named('azar 20', False, cities=[ENEMY_CITY], r=20)
g = go(caso(cities=[ENEMY_CITY], r=1, temp=1, flag=1))
check('azar 1 no sube el temperamento', g['ok'] and razes(g) == RAZE() and g['temp'] == 1, g)
g = go(caso(cities=[ENEMY_CITY], leader=(10, 10)))
check('sin candidato no hay azar', g['calls'] == [], g)
# más de 5 / 15 ciudades propias lejos
far_own = lambda n: [(60 - (i % 8), 50 + i // 8, 1, AI) for i in range(n)]
named('5 propias lejos: no suma (temp 2 + 1 + 2 = 5 con enemiga)', True, cities=[ENEMY_CITY] + far_own(5), temp=2)
named('temp 1 + enemiga: 4; 6 propias lejos suman 1', True, cities=[ENEMY_CITY] + far_own(6), temp=1)
named('temp 0 + bandera + enemiga: 2; 16 propias lejos suman 2 -> 4', False, cities=[ENEMY_CITY] + far_own(16), temp=0,
      flag=1)
named('temp 0 + bandera + 2 enemigas: 4; 16 propias lejos suman 2 -> 6', True,
      cities=[ENEMY_CITY, (24, 12, 1, ENEMY)] + far_own(16), temp=0, flag=1)
# solo las 12 más cercanas
many = [(20 + dx, 13, 1, 8) for dx in range(-6, 6)] + [(20, 20, 1, ENEMY)]
named('12 neutrales más cerca tapan a la enemiga', False, cities=many, temp=2)
named('con 11 neutrales la enemiga entra', True, cities=many[1:], temp=2)

# ---- al azar contra el modelo
rng = random.Random(1)
bad = 0; cnt = {True: 0, False: 0}
for n in range(NRAND):
    nc = rng.randrange(0, 40)
    cities = []
    for _ in range(nc):
        x, y = rng.randrange(64), rng.randrange(64)
        if (x, y) in P: x = 40
        cities.append((x, y, rng.choice([0, 1, 1, 1]), rng.choice([AI, AI, ENEMY, FRIEND, 5, 6, 8])))
    c = caso(cur=rng.choice([AI] * 9 + [ENEMY]), human=rng.random() < .05, raze=rng.choice([2, 2, 4, 6, 0, 1]),
             stack=rng.random() > .05, alive=rng.random() > .05,
             leader=rng.choice(HEADS * 6 + [(20, 10), (21, 10), (10, 10), (18, 10)]),
             dest=(rng.randrange(64), rng.randrange(64)), temp=rng.choice([0, 0, 1, 2, 3, 4, 5]),
             flag=rng.choice([0, 0, 1, 7, 15]), r=rng.choice([1, 2, 10, 18, 19, 20]),
             dip={q: rng.choice([0, 1, 2, 2]) for q in range(8)}, cities=cities,
             armies=[(rng.choice(P + [(30, 30), (19, 11)]), rng.choice([AI, ENEMY])) for _ in range(rng.choice([0, 0, 0, 1]))],
             razed=rng.random() < .05)
    g = go(c); m = model(c); cnt[m] += 1
    if not (g['ok'] and razes(g) == (RAZE() if m else [])):
        bad += 1
        if bad <= 5: print('DIFIERE', m, g, c)
check(f'{NRAND} casos al azar iguales al modelo (derriba {cnt[True]}, no {cnt[False]})', bad == 0 and cnt[True] > 50,
      f'difieren {bad}')

# ---- instrumentos
b = Bench(caso())
d = []
for xyxy in ((19, 10, 19, 10), (19, 10, 20, 11), (19, 10, 22, 10), (0, 0, 3, 4), (20, 10, 34, 10), (20, 10, 30, 21)):
    b.run(0x4974a0, struct.pack('<I', END) + b''.join(struct.pack('<i', v) for v in xyxy), REGS, ())
    d.append(b.reg('EAX') & 0xffff)
check('instrumento: 0x4974a0 con _ftol suplido da 0, 1, 3, 5, 14, 14', d == [0, 1, 3, 5, 14, 14], d)
b = Bench(caso(dip={FRIEND: 0, 5: 1}))
h = []
for q in (AI, ENEMY, FRIEND, 5, 8):
    b.run(0x49c1c0, struct.pack('<Ii', END, q), REGS, ()); h.append(b.reg('EAX') & 0xffff)
check('instrumento: 0x49c1c0 da propio 0, guerra 1, aliado 0, paz 0, neutral 1', h == [0, 1, 0, 0, 1], h)

# ---- 0x435d53: "Raze Site" del evaluador de misiones
def site435(code, exe=AV, edi=6):
    b = Bench(caso(), exe)
    b.mu.mem_write(0x55acb4, struct.pack('<h', 1))
    b.mu.mem_write(0x55acb6, struct.pack('<hh', 30, 31) + b'SitioA\0')
    frame = bytearray(0x80); frame[0x20:0x22] = b'\x12\x34'
    frame[0x2e + edi:0x30 + edi] = struct.pack('<h', code)
    end = b.run(0x435d53, bytes(frame), dict(REGS, EDI=edi), (0x435d79,))
    esp = b.reg('ESP')
    return end, b.reg('EDX') & 0xffff, b.reg('EAX') & 0xffff, bytes(b.mu.mem_read(esp + 0x20, 2)), esp == b.esp0
r = site435(BC(21, 10))
check('0x435d53 con puente: dx = 21, ax = 10', r == (0x435d79, 21, 10, b'\xff\xff', True), r)
r = site435(BC(63, 127), edi=0)
check('0x435d53 con puente en (63,127)', r == (0x435d79, 63, 127, b'\xff\xff', True), r)
# El original multiplica el código por 150 (el registro de sitio): con un puente lee fuera de su imagen (termina en
# 0x6b0000). En el juego eso es basura o un acceso inválido; en el banco, memoria sin mapear.
b = Bench(caso(), ORIG); bad_reads = []
b.mu.hook_add(UC_HOOK_MEM_READ_UNMAPPED, lambda uc, acc, addr, size, val, _: bad_reads.append(addr) and False)
frame = bytearray(0x80); frame[0x34:0x36] = struct.pack('<h', BC(21, 10))
try: b.run(0x435d53, bytes(frame), dict(REGS, EDI=6), (0x435d79,))
except UcError: pass
check('control: el original con el código del puente lee fuera de su imagen (el defecto de 1.0.21/22)',
      bad_reads == [0x55acb6 + BC(21, 10) * 150], [hex(v) for v in bad_reads])
a, o = site435(0), site435(0, ORIG)
check('0x435d53 con sitio: igual al original (30, 31)', a == o and a[:3] == (0x435d79, 30, 31), f'{a} {o}')

print('TODO OK' if all(res) else f'FALLAN {res.count(False)} DE {len(res)}')
sys.exit(0 if all(res) else 1)
