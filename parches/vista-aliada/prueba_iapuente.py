# Prueba de juguete: la IA cumple la misión "derribar un puente" (ai_brq en 0x40d450, ai_brname en 0x40d963), en unicorn.
# Uso: python prueba_iapuente.py [DarklordAV.exe] [Darklord.exe]
#      (por defecto C:\Warlords3\DarklordAV.exe y el original C:\Warlords3\Darklord.exe; armar antes con build.py)
# Mapa de 64x64 de tierra con el puente P (20,10)-(21,10). El héroe (ejército 1) es del jugador 2, de la computadora,
# con la misión tipo 10 sobre P. Lo que el original hace con un sitio se compara contra Darklord.exe: tiene que dar
# exactamente lo mismo. El movimiento (0x40d2b0), el ataque (0x40e400), la orden de red (0x4b9550), el cambio de
# grupo (0x40d230) y la pausa (0x4275b0) van guionados y se anotan; el aviso a la misión (0x461a60) corre de verdad.
import sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
from keystone import Ks, KS_ARCH_X86, KS_MODE_32

def load(path):
    pe = pefile.PE(path)
    return pe.OPTIONAL_HEADER.ImageBase, bytes(pe.get_memory_mapped_image()), (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
AV = load(sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe')
ORIG = load(sys.argv[2] if len(sys.argv) > 2 else r'C:\Warlords3\Darklord.exe')

W = H = 64; SHIFT = 8; LAND, WATER, MOUNT = 2, 3, 5
AI, ENEMY = 2, 3
HERO, FOE, OWN = 1, 2, 3                  # ejércitos: el héroe de AI, uno enemigo, otro de AI
BC = lambda x, y: 0x2000 + (y << 7) + x
P = [(20, 10), (21, 10)]; PC = BC(20, 10)
SITE = (30, 30)
STUB = 0x100000; STACK = 0x200000; END = 0x1fff00; PLAN = 0x101600; FMT = 0x101200; LOG = 0x101700
STUBS = {0x40d2b0: 'mover', 0x40e400: 'atacar', 0x4b9550: 'orden', 0x40d230: 'grupo', 0x4275b0: 'pausa',
         0x4973f0: 'destino', 0x427520: 'log', 0x4621d0: 'premio', 0x4def30: 'texto', 0x4deb20: 'azar',
         0x4374a0: 'nombre'}
BRIDGE_NAME = 'Belgor Bridge'             # lo que da el stub del generador de nombres (br_name)

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

class Bench:
    def __init__(self, exe=AV, hero=(19, 10), armies=(), tiles={}, roads=(), razed=False, target=PC, move=None,
                 attack=lambda *a: 1, alive=1, real_attack=False):
        base, img, size = exe
        mu = self.mu = Uc(UC_ARCH_X86, UC_MODE_32)
        mu.mem_map(base, size); mu.mem_write(base, img[:size])
        mu.mem_map(STUB, 0x10000); mu.mem_map(STACK - 0x10000, 0x10000)
        mu.mem_write(0x503e00, struct.pack('<HH', W, H)); mu.mem_write(0x503e06, bytes([SHIFT]))
        for t, cls in ((LAND, 0), (WATER, 1), (MOUNT, 4)):
            mu.mem_write(0x535f0c + t * 0x58, struct.pack('<H', cls))
        for y in range(H):
            for x in range(W): self.set_tile(x, y, LAND, 0, 0x05)
        for x, y in P:
            if razed: self.set_tile(x, y, WATER, 0, 0x85)
            else: self.set_tile(x, y, WATER, 1, 0x05)
        for (x, y), t in tiles.items(): self.set_tile(x, y, t, 0, 0x05)
        for x, y in roads: mu.mem_write(0x57d158 + x * 0xa0 + y, b'\x10')
        mu.mem_write(0x537ce8, struct.pack('<h', AI)); mu.mem_write(0x4fb0ec, struct.pack('<h', AI))
        for p in range(8): mu.mem_write(0x536c12 + p * 0x1f8, struct.pack('<h', 0))
        mu.mem_write(0x53c393, bytes([2]))
        mu.mem_write(0x55acb4, struct.pack('<h', 1))
        mu.mem_write(0x55acb6, struct.pack('<hh', *SITE) + b'SitioA\0')
        # ejércitos
        arm = [(HERO, hero, AI, 3)] + list(armies)
        mu.mem_write(0x54fe50, struct.pack('<h', 1 + max(a for a, *_ in arm)))
        for a, (x, y), owner, hidx in arm:
            r = a * 0x1c
            mu.mem_write(0x54fe52 + r, struct.pack('<hh', x, y))
            mu.mem_write(0x54fe5e + r, struct.pack('<H', (owner << 5) | (0x10 if hidx else 0)))
            mu.mem_write(0x54fe61 + r, bytes([alive]))
            mu.mem_write(0x54fe62 + r, struct.pack('<H', 0x4000 | (hidx << 8) if hidx else 0))
            mu.mem_write(0x54fe63 + r, bytes([0x40 | hidx]))
        mu.mem_write(0x556bb4 + 3 * 0xb8, b'Heroe IA\0')
        mu.mem_write(0x56ea92 + AI * 0x4f0, struct.pack('<h', HERO))
        mu.mem_write(PLAN, bytes(0x20)); mu.mem_write(PLAN + 0xc, struct.pack('<h', HERO))
        mu.mem_write(0x5020d4, struct.pack('<I', PLAN)); mu.mem_write(0x5020d0, struct.pack('<h', 0))
        mu.mem_write(0x55edc4 + AI * 16, struct.pack('<BBhhhhhhh', 1, 0, HERO, 10, target, 0, 0, 0, 1))
        self.move = move; self.attack = attack; self.calls = []
        self.stubs = {va: k for va, k in STUBS.items() if not (real_attack and k == 'atacar')}
        for va in self.stubs: mu.mem_write(va, b'\xc3')
        mu.mem_write(STUB, b'\xc3'); mu.mem_write(0x5a9bec, struct.pack('<I', STUB))   # sprintf
        mu.mem_write(FTOL, FTOL_CODE); mu.mem_write(0x5a9ba8, struct.pack('<I', FTOL))  # _ftol (trunca)
        mu.mem_write(FMT, b'%s\0')
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
    def cstr(self, p): return bytes(self.mu.mem_read(p, 80)).split(b'\0')[0].decode('latin1')
    def pos(self, a=HERO): return struct.unpack('<hh', self.mu.mem_read(0x54fe52 + a * 0x1c, 4))
    def setpos(self, xy, a=HERO): self.mu.mem_write(0x54fe52 + a * 0x1c, struct.pack('<hh', *xy))

    def hook(self, uc, addr, size, _):
        if addr in self.stops:
            self.end = addr; uc.emu_stop(); return
        s = self.sarg; ret = 0
        if addr in self.stubs:
            k = self.stubs[addr]
            if k == 'mover':
                self.calls.append((k, s(0), s(1)))
                r = self.move(s(0), s(1)) if self.move else (s(0), s(1))
                if r is None: ret = 0
                else: self.setpos(r); ret = 1
            elif k == 'atacar':
                self.calls.append((k, s(0), s(1), s(2), s(3))); ret = self.attack(s(0), s(1), s(2), s(3))
            elif k == 'orden': self.calls.append((k, s(0), s(1)))
            elif k == 'destino': self.calls.append((k, s(0), s(1), s(2), s(3)))
            elif k in ('grupo', 'pausa', 'premio'): self.calls.append(k)
            elif k == 'texto': ret = FMT
            elif k == 'nombre': uc.mem_write(self.arg(1), BRIDGE_NAME.encode() + b'\0'); ret = self.arg(1)
            uc.reg_write(UC_X86_REG_EAX, ret)
        elif addr == STUB:
            fmt = self.cstr(a := self.arg(1))
            args = [self.arg(2 + i) for i in range(fmt.count('%'))]
            out = fmt.replace('%d', '{}').replace('%s', '{}').format(
                *[self.cstr(v) if c == 's' else v for v, c in zip(args, [fmt[i + 1] for i in range(len(fmt)) if fmt[i] == '%'])])
            self.calls.append(('sprintf', out))

    def run(self, start, args=(), regs=None, stops=(), esp=None, frame=None):
        mu = self.mu
        esp = STACK - 0x400
        mu.mem_write(esp, (frame if frame is not None else struct.pack('<I', END) +
                           b''.join(struct.pack('<I', v & 0xffffffff) for v in args)) + bytes(0x40))
        base = dict(EAX=0x11111111, ECX=0x22222222, EDX=0x33333333, EBX=0x44444444, ESI=0x55555555,
                    EDI=0x66666666, EBP=0x77777777)
        base.update(regs or {})
        for k, v in base.items(): mu.reg_write(globals()['UC_X86_REG_' + k], v)
        mu.reg_write(UC_X86_REG_ESP, esp)
        self.stops = set(stops) | {END}; self.end = None
        mu.emu_start(start, 0, count=5000000)
        self.esp0 = esp; self.regs_in = base
        return self.end

    def r(self, k): return self.mu.reg_read(globals()['UC_X86_REG_' + k])
    def saved_ok(self):
        return all(self.r(k) == self.regs_in[k] for k in ('EBX', 'ESI', 'EDI', 'EBP')) and self.r('ESP') == self.esp0 + 4
    def status(self): return self.mu.mem_read(0x55ee44 + AI, 1)[0]
    def plan(self): return struct.unpack('<hh', self.mu.mem_read(PLAN + 6, 4))

res = []
def check(nombre, cond, detalle=''):
    res.append(cond); print(f'{"OK " if cond else "MAL"} {nombre}' + (f'   [{detalle}]' if not cond and detalle else ''))

def go(target=PC, mode=10, exe=AV, **kw):
    b = Bench(exe=exe, target=target, **kw)
    end = b.run(0x40d450, (target, mode))
    return dict(end=end, ok=end == END and b.saved_ok(), ax=b.r('EAX') & 0xffff, calls=b.calls, st=b.status(),
                plan=b.plan(), pos=b.pos())
def moved(g): return [c[1:] for c in g['calls'] if c[0] == 'mover']
def razed(g): return [c for c in g['calls'] if c[0] == 'orden']
DONE = ['pausa', 'grupo']

# ---- parado en una cabecera: lo derriba en el acto
for nombre, hero in [('al lado, de frente', (19, 10)), ('al lado, en diagonal', (22, 11)), ('al lado de las dos casillas', (20, 9))]:
    g = go(hero=hero)
    check(f'cabecera {nombre}: derriba, cumple la misión y termina', g['ok'] and g['ax'] == 1 and
          razed(g) == [('orden', PC, AI)] and g['st'] == 1 and not moved(g) and g['calls'][-2:] == DONE
          and g['plan'] == (0, 0), g)
g = go(hero=(19, 10), target=BC(21, 10))
check('el objetivo por la otra casilla también (orden con ese código)', g['ok'] and g['ax'] == 1 and
      razed(g) == [('orden', BC(21, 10), AI)], g)

# ---- lejos: va hacia la cabecera más cercana
g = go(hero=(5, 10), move=lambda x, y: (12, 10))
check('lejos: elige (19,9) y va hacia ella; no llega, no derriba', g['ok'] and g['ax'] == 0 and moved(g) == [(19, 9)]
      and ('destino', 7, 0, 19, 9) in g['calls'] and g['plan'] == (8, PC) and not razed(g) and g['st'] == 0, g)
g = go(hero=(5, 10))
check('lejos: llega en el mismo turno y lo derriba', g['ok'] and g['ax'] == 1 and moved(g) == [(19, 9)]
      and ('atacar', 19, 9, 19, 9) in g['calls'] and razed(g) == [('orden', PC, AI)] and g['st'] == 1, g)
g = go(hero=(5, 10), move=lambda x, y: None)
check('lejos: el héroe muere en el camino, no ataca ni derriba', g['ok'] and g['ax'] == 0 and
      not any(c[0] in ('atacar', 'orden') for c in g['calls']), g)
g = go(hero=(5, 10), attack=lambda *a: 0)
check('lejos: 0x40e400 dice que no, no derriba', g['ok'] and g['ax'] == 0 and not razed(g), g)
g = go(hero=(40, 10), move=lambda x, y: (30, 10))
check('lejos al este: elige (22,9)', g['ok'] and moved(g) == [(22, 9)], g)
g = go(hero=(20, 10), move=lambda x, y: (20, 10))
check('parado sobre el puente: se baja a una cabecera, no lo derriba desde ahí', g['ok'] and g['ax'] == 0
      and moved(g) == [(19, 9)] and not razed(g), g)

# ---- qué casillas sirven de cabecera
for nombre, kw, esperado in [
        ('montaña sin camino no sirve', dict(tiles={(22, 9): MOUNT}), (22, 10)),
        ('montaña con camino sí', dict(tiles={(22, 9): MOUNT}, roads=[(22, 9)]), (22, 9)),
        ('agua no sirve', dict(tiles={(22, 9): WATER, (22, 10): WATER}), (22, 11))]:
    g = go(hero=(40, 10), move=lambda x, y: (30, 10), **kw)
    check(f'cabecera: {nombre}', g['ok'] and moved(g) == [esperado], g)
water = {(x + dx, y + dy): WATER for x, y in P for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (x + dx, y + dy) not in P}
g = go(hero=(5, 10), tiles=water)
check('sin ninguna cabecera: no hace nada', g['ok'] and g['ax'] == 0 and g['calls'] == [], g)

# ---- ejércitos sobre el puente
g = go(hero=(20, 9), armies=[(FOE, (21, 10), ENEMY, 0)])
check('enemigo encima: lo ataca, no derriba', g['ok'] and g['ax'] == 0 and ('atacar', 20, 9, 21, 10) in g['calls']
      and not razed(g) and g['st'] == 0, g)
g = go(hero=(19, 10), armies=[(FOE, (21, 10), ENEMY, 0)])
check('enemigo encima pero no al lado: no lo ataca ni derriba (la casilla vacía de al lado: 0x40e400 no hace nada)',
      g['ok'] and g['ax'] == 0 and not razed(g) and [c for c in g['calls'] if c[0] == 'atacar'] == [('atacar', 19, 10, 20, 10)], g)
g = go(hero=(20, 9), armies=[(OWN, (21, 10), AI, 0)])
check('propio encima: espera (no lo ahoga), no ataca', g['ok'] and g['ax'] == 0
      and not any(c[0] in ('atacar', 'orden') for c in g['calls']), g)
g = go(hero=(20, 9), armies=[(FOE, (40, 40), ENEMY, 0), (OWN, (30, 30), AI, 0)])
check('ejércitos en otro lado: derriba (control)', g['ok'] and g['ax'] == 1 and razed(g) == [('orden', PC, AI)], g)

b = Bench()
d = [(b.run(0x4974a0, xyxy), b.r('EAX') & 0xffff)[1] for xyxy in ((19, 10, 19, 10), (19, 10, 20, 11), (19, 10, 22, 10), (0, 0, 3, 4))]
check('instrumento: la distancia del juego (0x4974a0 con _ftol suplido) da 0, 1, 3, 5', d == [0, 1, 3, 5], d)
b = Bench(hero=(19, 10), armies=[(FOE, (21, 10), ENEMY, 0)], real_attack=True)
end = b.run(0x40e400, (19, 10, 20, 10))
check('0x40e400 real contra la casilla vacía de al lado: devuelve 0 y no hace nada',
      end == END and b.saved_ok() and b.r('EAX') & 0xffff == 0 and b.calls == [], b.calls)

# ---- puente ya derribado o modo que no es misión
g = go(hero=(19, 10), razed=True)
check('ya derribado: no hace nada', g['ok'] and g['ax'] == 0 and g['calls'] == [], g)
g = go(hero=(19, 10), mode=0)
check('modo 0 (visitar): llega y termina sin derribar', g['ok'] and g['ax'] == 1 and not razed(g)
      and g['calls'] == DONE, g)

# ---- sitios: igual al original
for nombre, kw in [('sitio, parado encima, modo 10', dict(hero=SITE)),
                   ('sitio, lejos y llega', dict(hero=(5, 5))),
                   ('sitio, lejos y no llega', dict(hero=(5, 5), move=lambda x, y: (10, 10))),
                   ('sitio, muere en el camino', dict(hero=(5, 5), move=lambda x, y: None)),
                   ('sitio, modo 0', dict(hero=SITE, mode=0))]:
    a, o = go(target=0, **kw), go(target=0, exe=ORIG, **kw)
    check(f'igual al original: {nombre}', a['ok'] and o['ok'] and a == o, f'{a} {o}')

# ---- 0x40d963: el registro de la IA y la llamada a 0x40d450
def site963(target, exe=AV):
    b = Bench(exe=exe, target=target)
    # pila de 0x40d6d0 en 0x40d963: edi, esi, ebx guardados, 8 de locales ([esp+0x12] = objetivo), retorno
    frame = struct.pack('<III', 0x6666, 0x5555, 0x4444) + bytes(6) + struct.pack('<h', target) + struct.pack('<I', END)
    end = b.run(0x40d963, frame=frame, regs=dict(ESI=STUB, EDI=10), stops=(0x40d450,))
    return end, b.sarg(0), b.sarg(1), [c for c in b.calls if c[0] == 'sprintf']
r = site963(PC)
check('0x40d963 con puente: registra su nombre y llama a 0x40d450(código, 10)',
      r[0] == 0x40d450 and r[1:3] == (PC, 10) and r[3] == [('sprintf', f'*******Goto Site {BRIDGE_NAME} *******')], r)
a, o = site963(0), site963(0, ORIG)
check('0x40d963 con sitio: igual al original', a == o and a[0] == 0x40d450 and 'SitioA' in a[3][0][1], f'{a} {o}')

print('TODO OK' if all(res) else f'FALLAN {res.count(False)} DE {len(res)}')
sys.exit(0 if all(res) else 1)
