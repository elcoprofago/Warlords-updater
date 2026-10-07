# Prueba de juguete de derribar y reconstruir puentes sobre el exe parcheado, en unicorn.
# Uso: python prueba_puentes.py [DarklordAV.exe]   (por defecto C:\Warlords3\DarklordAV.exe; armarlo antes con build.py)
# Mapa de 20x20 de tierra con un puente horizontal (5,5)-(6,5), otro vertical (12,8)-(12,9) y, como controles, una
# casilla de agua con edificio y estructura 1 (no es puente) en (15,15) y agua sin puente en (16,15).
# Las funciones del juego que se llaman (avisos, oro, ahogar, redibujar) son stubs que anotan sus argumentos.
import sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

pe = pefile.PE(sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe'); BASE = pe.OPTIONAL_HEADER.ImageBase
img = bytes(pe.get_memory_mapped_image())
SIZE = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff

def cstr_va(s):
    return BASE + img.index(s.encode('latin1') + b'\0')
THE_BRIDGE, THE_BRIDGE_U = cstr_va('the bridge'), cstr_va('The bridge')
ENEMY1, ENEMY2 = cstr_va('Enemies hold the bridge!'), cstr_va('Attack them first.')
def call_target(va):
    assert img[va - BASE] == 0xe8
    return va + 5 + struct.unpack_from('<i', img, va - BASE + 1)[0]
RAZELK, REBUILDLK = call_target(0x4205c1), call_target(0x42053f)
assert all(call_target(v) == RAZELK for v in (0x41c98c, 0x44c2d7, 0x4b05d1)) and call_target(0x41caab) == REBUILDLK

W = H = 20; SHIFT = 8; WATER, LAND = 3, 2
UI = 1                       # jugador de la interfaz, humano
BC = lambda x, y: 0x2000 + (y << 7) + x
SITE_NAME = lambda i: 0x55acba + i * 0x96
STUB = 0x100000; STACK = 0x200000; END = 0x1fff00
FMT_RUINS = 0x100800         # lo que devuelve el stub de textos (0x4def30)

def tile_va(x, y):
    return ((y * 10) << SHIFT) + x * 10 + 0x503e58

class Bench:
    def __init__(self, armies=(), opt=2, extra=None):
        mu = self.mu = Uc(UC_ARCH_X86, UC_MODE_32)
        mu.mem_map(BASE, SIZE); mu.mem_write(BASE, img[:SIZE])
        mu.mem_map(STUB, 0x10000); mu.mem_map(STACK - 0x10000, 0x10000)
        mu.mem_write(0x503e00, struct.pack('<HH', W, H)); mu.mem_write(0x503e06, bytes([SHIFT]))
        mu.mem_write(0x535f0c + WATER * 0x58, struct.pack('<H', 1))
        mu.mem_write(0x535f0c + LAND * 0x58, struct.pack('<H', 0))
        for y in range(H):
            for x in range(W):
                self.set_tile(x, y, LAND, 0, 0x05)            # byte +9 = 0x05: bits ajenos que deben sobrevivir
        for x, y in ((5, 5), (6, 5), (12, 8), (12, 9)):
            self.set_tile(x, y, WATER, 1, 0x05)
        self.set_tile(15, 15, WATER | 0x4000, 1, 0)
        self.set_tile(16, 15, WATER, 0, 0)
        mu.mem_write(0x53c393, bytes([opt]))
        mu.mem_write(0x537ce8, struct.pack('<h', UI))
        for p in range(8):
            mu.mem_write(0x536c12 + p * 0x1f8, struct.pack('<h', -1 if p == UI else 0))
        mu.mem_write(0x56950e, struct.pack('<HH', 1000, 300))     # BuildCity, BuildSite
        # ejércitos: índice 0 sin usar; (x, y, dueño, vivo)
        mu.mem_write(0x54fe50, struct.pack('<h', len(armies) + 1))
        for i, (x, y, owner, alive) in enumerate(armies, 1):
            r = i * 0x1c
            mu.mem_write(0x54fe52 + r, struct.pack('<hh', x, y))
            mu.mem_write(0x54fe5e + r, struct.pack('<H', owner << 5))
            mu.mem_write(0x54fe63 + r, bytes([0x40 if alive else 0]))
        self.calls = []
        self.fliers = set()
        self.stub_at = {}
        stubs = {0x4a2170: 0, 0x456ee0: 0, 0x4a4f20: 0, 0x43fd60: 0, 0x485610: 0, 0x43c240: 0, 0x4c2790: 0,
                 0x4b9550: 0, 0x4955d0: 0, 0x4d82a0: 0, 0x4d7f60: 0, 0x4a0400: 0, 0x49f900: 0, 0x43ff80: 0,
                 0x4def30: 8, 0x440b30: 0}
        for va, n in stubs.items():
            mu.mem_write(va, b'\xc2' + struct.pack('<H', n) if n else b'\xc3')
        self.site = -1
        mu.mem_write(STUB, b'\xc3'); mu.mem_write(0x5a9bec, struct.pack('<I', STUB))   # sprintf
        mu.mem_write(FMT_RUINS, b'%s is in ruins!\0')
        mu.mem_write(END, b'\xf4')
        if extra: extra(self)
        mu.hook_add(UC_HOOK_CODE, self.hook)

    def set_tile(self, x, y, w0, struct_, b9):
        t = tile_va(x, y)
        self.mu.mem_write(t, struct.pack('<H', w0)); self.mu.mem_write(t + 3, bytes([struct_]))
        self.mu.mem_write(t + 9, bytes([b9]))

    def tile(self, x, y):
        t = tile_va(x, y); b = self.mu.mem_read(t, 10)
        return b[3], b[9]

    def arg(self, k):
        esp = self.mu.reg_read(UC_X86_REG_ESP)
        return struct.unpack('<i', self.mu.mem_read(esp + 4 + 4 * k, 4))[0]

    def hook(self, uc, addr, size, _):
        if addr in self.stops:
            self.end = addr; uc.emu_stop(); return
        a = self.arg
        if addr == 0x440b30:
            uc.reg_write(UC_X86_REG_EAX, self.site & 0xffffffff); self.calls.append(('site', a(0) & 0xffff, a(1) & 0xffff))
        elif addr == 0x43c240:
            army = a(1) & 0xffff
            uc.reg_write(UC_X86_REG_EAX, 0 if army in self.fliers else 1); self.calls.append(('candrown', a(0) & 0xffff, army))
        elif addr == 0x485610:
            self.calls.append(('drown',) + tuple(a(k) & 0xffff for k in range(6)))
        elif addr == 0x43fd60:
            self.calls.append(('gold', a(0) & 0xffff, struct.unpack('<h', struct.pack('<H', a(1) & 0xffff))[0]))
        elif addr == 0x4c2790:
            p = a(0); s = bytes(uc.mem_read(p, 64)).split(b'\0')[0].decode('latin1')
            self.calls.append(('msg', s, a(1)))
        elif addr == 0x4def30:
            self.calls.append(('text', a(0))); uc.reg_write(UC_X86_REG_EAX, FMT_RUINS)
        elif addr == STUB:
            fmt = bytes(uc.mem_read(a(1), 64)).split(b'\0')[0].decode('latin1')
            name = bytes(uc.mem_read(a(2), 64)).split(b'\0')[0].decode('latin1')
            out = (fmt % name).encode('latin1') + b'\0'
            uc.mem_write(a(0), out); self.calls.append(('sprintf', fmt % name))
        elif addr == 0x4b9550:
            self.calls.append(('order', a(0) & 0xffff, a(1) & 0xffff))
        elif addr == 0x4955d0:
            self.calls.append(('siteraze', a(0) & 0xffff))
        elif addr in (0x4a4f20, 0x456ee0, 0x4a0400, 0x49f900):
            self.calls.append({0x4a4f20: 'graph', 0x456ee0: 'view', 0x4a0400: 'history', 0x49f900: 'history'}[addr])

    def run(self, start, stops, args=(), regs=None, stack_words=None):
        """Llama a start con args cdecl (vuelve a END), o arranca en medio de una función con la pila dada."""
        mu = self.mu
        esp = STACK - 0x100
        if stack_words is None:
            stack = struct.pack('<I', END) + b''.join(struct.pack('<I', v & 0xffffffff) for v in args)
        else:
            stack = b''.join(struct.pack('<I', v & 0xffffffff) for v in stack_words)
        mu.mem_write(esp, stack + bytes(0x40))
        base = dict(EAX=0x11111111, ECX=0x22222222, EDX=0x33333333, EBX=0x44444444, ESI=0x55555555,
                    EDI=0x66666666, EBP=0x77777777)
        base.update(regs or {})
        for k, v in base.items(): mu.reg_write(globals()['UC_X86_REG_' + k], v)
        mu.reg_write(UC_X86_REG_ESP, esp)
        self.stops = set(stops) | {END}; self.end = None
        mu.emu_start(start, 0, count=200000)
        self.esp0 = esp
        self.regs_in = base
        return self.end

    def r(self, k): return self.mu.reg_read(globals()['UC_X86_REG_' + k])
    def saved_ok(self, esp_delta):
        return all(self.r(k) == self.regs_in[k] for k in ('EBX', 'ESI', 'EDI', 'EBP')) and \
            self.r('ESP') == self.esp0 + esp_delta

res = []
def check(nombre, cond, detalle=''):
    res.append(cond); print(f'{"OK " if cond else "MAL"} {nombre}' + (f'   [{detalle}]' if not cond and detalle else ''))

ax = lambda b: struct.unpack('<h', struct.pack('<H', b.r('EAX') & 0xffff))[0]

# ---- búsqueda de Raze (en lugar de 0x440b30)
for nombre, leader, site, opt, esperado in [
        ('raze: líder al oeste del puente',   (4, 5), -1, 2, BC(5, 5)),
        ('raze: líder en diagonal',           (7, 4), -1, 2, BC(6, 5)),
        ('raze: líder al sur del vertical',   (12, 10), -1, 2, BC(12, 9)),
        ('raze: líder encima del puente',     (5, 5), -1, 2, -1),
        ('raze: lejos de todo',               (10, 15), -1, 2, -1),
        ('raze: agua con edificio no es puente', (14, 15), -1, 2, -1),
        ('raze: sin la opción de arrasar',    (4, 5), -1, 0, -1),
        ('raze: opción 4 también vale',       (4, 5), -1, 4, BC(5, 5)),
        ('raze: el sitio manda (control)',    (4, 5), 7, 2, 7),
        ('raze: esquina del mapa',            (0, 0), -1, 2, -1)]:
    b = Bench(opt=opt); b.site = site
    end = b.run(RAZELK, (), args=(0xbeef0000 | leader[0], 0xcafe0000 | leader[1]))
    check(nombre, end == END and ax(b) == esperado and b.saved_ok(4) and b.calls[0] == ('site',) + leader,
          f'ax={ax(b):#x} calls={b.calls}')
# ---- búsqueda de Build
for nombre, leader, site, prep, esperado in [
        ('build: puente entero no se reconstruye', (4, 5), -1, None, -1),
        ('build: puente derribado vecino',         (4, 5), -1, 'razed', BC(5, 5)),
        ('build: derribado y sin opción de arrasar', (4, 5), -1, 'razed0', BC(5, 5)),
        ('build: encima del derribado (agua)',     (5, 5), -1, 'razed', BC(6, 5)),
        ('build: el sitio manda (control)',        (4, 5), 3, 'razed', 3)]:
    def ext(bb, prep=prep):
        if prep: bb.set_tile(5, 5, WATER, 0, 0x85); bb.set_tile(6, 5, WATER, 0, 0x85)
    b = Bench(opt=0 if prep == 'razed0' else 2, extra=ext); b.site = site
    end = b.run(REBUILDLK, (), args=(leader[0], leader[1]))
    check(nombre, end == END and ax(b) == esperado and b.saved_ok(4), f'ax={ax(b):#x}')

# ---- habilitación del menú (salidas 0x4b0a1c / 0x4b0a28)
BUF = 0x100400
for nombre, start, leader, bl, opt, prep, esp8, espc in [
        ('menú: puente vecino enciende Raze',    0x4b0a1c, (4, 5), 0, 2, None, 1, 0),
        ('menú: también por la otra salida',     0x4b0a28, (4, 5), 0, 2, None, 1, 0),
        ('menú: sin opción no enciende',         0x4b0a1c, (4, 5), 0, 0, None, 0, 0),
        ('menú: no es su turno (bl)',            0x4b0a1c, (4, 5), 1, 2, None, 0, 0),
        ('menú: sin líder',                      0x4b0a1c, None, 0, 2, None, 0, 0),
        ('menú: derribado enciende Build',       0x4b0a1c, (4, 5), 0, 2, 'razed', 0, 1),
        ('menú: lejos, nada',                    0x4b0a1c, (10, 15), 0, 2, None, 0, 0)]:
    def ext(bb, prep=prep):
        if prep: bb.set_tile(5, 5, WATER, 0, 0x85); bb.set_tile(6, 5, WATER, 0, 0x85)
    arm = [(leader[0], leader[1], UI, True)] if leader else []
    b = Bench(armies=arm, opt=opt, extra=ext)
    b.mu.mem_write(BUF, bytes(0x20))
    # pila: ebp, edi, esi, ebx guardados, 0x14 de locales, retorno
    words = [0xa0a0a0a0, 0xb0b0b0b0, 0xc0c0c0c0, 0xd0d0d0d0] + [0] * 5 + [END]
    end = b.run(start, (), regs=dict(ESI=BUF, EBX=0x1200 | bl, EBP=1 if leader else 0), stack_words=words)
    got = bytes(b.mu.mem_read(BUF, 0x20))
    ok_regs = (b.r('EBP'), b.r('EDI'), b.r('ESI'), b.r('EBX')) == (0xa0a0a0a0, 0xb0b0b0b0, 0xc0c0c0c0, 0xd0d0d0d0) \
        and b.r('ESP') == b.esp0 + 4 * 10
    others = got[:8] + got[9:0xc] + got[0xd:]
    check(nombre, end == END and got[8] == esp8 and got[0xc] == espc and others == bytes(len(others)) and ok_regs,
          f'buf={got.hex()} regs_ok={ok_regs}')

# ---- texto del diálogo de arrasar (0x495530)
for nombre, eax, esperado in [('texto raze: puente', BC(5, 5), THE_BRIDGE), ('texto raze: sitio 2 (control)', 2, SITE_NAME(2))]:
    b = Bench()
    end = b.run(0x495530, (0x495541,), regs=dict(EAX=eax), stack_words=[0] * 4)
    top = struct.unpack('<I', b.mu.mem_read(b.r('ESP'), 4))[0]
    check(nombre, end == 0x495541 and top == esperado and b.r('ESP') == b.esp0 - 4, f'top={top:#x}')

# ---- botón del diálogo de arrasar (0x495288 -> 0x495294): un puente va por 0x4955d0 con su código canónico
for nombre, code, armies, esperado in [
        ('botón: puente vacío manda la orden', BC(5, 5), [(4, 5, UI, True)], [('siteraze', BC(5, 5))]),
        ('botón: otra casilla -> código canónico', BC(6, 5), [(4, 5, UI, True)], [('siteraze', BC(5, 5))]),
        ('botón: propio encima también',       BC(5, 5), [(5, 5, UI, True)], [('siteraze', BC(5, 5))]),
        ('botón: enemigo encima -> atacar',    BC(5, 5), [(6, 5, 3, True)],
         [('msg', 'Enemies hold the bridge!', 0x19), ('msg', 'Attack them first.', 0x1e)]),
        ('botón: enemigo muerto no cuenta',    BC(5, 5), [(6, 5, 3, False)], [('siteraze', BC(5, 5))]),
        ('botón: enemigo al lado no cuenta',   BC(5, 5), [(7, 5, 3, True)], [('siteraze', BC(5, 5))]),
        ('botón: sitio 4 (control)',           4, [], [('siteraze', 4)])]:
    b = Bench(armies=armies)
    b.mu.mem_write(0x572778, struct.pack('<h', code))
    end = b.run(0x495288, (0x495294,), stack_words=[0] * 4)
    check(nombre, end == 0x495294 and b.calls == esperado and b.saved_ok(-4), f'calls={b.calls}')

# ---- aplicación de arrasar (0x4d5e30(código, jugador))
def razed(b, *xy): return all(b.tile(x, y) == (0, 0x85) for x, y in xy)
def intact(b, *xy): return all(b.tile(x, y) == (1, 0x05) for x, y in xy)
for nombre, code, player, armies, fliers, cond in [
        ('arrasar: puente vacío, humano', BC(5, 5), UI, [(4, 5, UI, True)], (),
         lambda b: razed(b, (5, 5), (6, 5)) and intact(b, (12, 8), (12, 9)) and b.calls == [
             'view', ('text', 0x8d), ('sprintf', 'The bridge is in ruins!'), ('text', 0x8c),
             ('msg', '%s is in ruins!', 0x19), ('msg', 'The bridge is in ruins!', 0x23), 'graph']),
        ('arrasar: desde la otra punta', BC(6, 5), UI, [], (), lambda b: razed(b, (5, 5), (6, 5))),
        ('arrasar: el vertical', BC(12, 9), UI, [], (), lambda b: razed(b, (12, 8), (12, 9)) and intact(b, (5, 5), (6, 5))),
        ('arrasar: propio encima cae al agua', BC(5, 5), UI, [(4, 5, UI, True), (6, 5, UI, True)], (),
         lambda b: razed(b, (5, 5), (6, 5)) and ('candrown', UI, 2) in b.calls and ('drown', UI, 2, 1, 0, 1, 0) in b.calls
         and ('candrown', UI, 1) not in b.calls),
        ('arrasar: el que vuela no cae', BC(5, 5), UI, [(5, 5, UI, True)], {1},
         lambda b: razed(b, (5, 5), (6, 5)) and ('candrown', UI, 1) in b.calls
         and not any(isinstance(c, tuple) and c[0] == 'drown' for c in b.calls)),
        ('arrasar: enemigo encima no hace nada', BC(5, 5), UI, [(5, 5, 3, True)], (),
         lambda b: intact(b, (5, 5), (6, 5)) and b.calls == ['graph']),
        ('arrasar: computadora, sin aviso', BC(5, 5), 2, [], (),
         lambda b: razed(b, (5, 5), (6, 5)) and b.calls == ['view', 'graph']),
        ('arrasar: ya derribado no hace nada', BC(16, 15), UI, [], (),
         lambda b: b.tile(16, 15) == (0, 0) and b.calls == ['graph']),
        ('arrasar: agua con edificio no', BC(15, 15), UI, [], (),
         lambda b: b.tile(15, 15) == (1, 0) and b.calls == ['graph'])]:
    b = Bench(armies=armies); b.fliers = set(fliers)
    end = b.run(0x4d5e30, (), args=(code, player))
    check(nombre, end == END and cond(b) and b.saved_ok(4), f'calls={b.calls} t55={b.tile(5,5)} t65={b.tile(6,5)}')
b = Bench()
end = b.run(0x4d5e30, (0x4d5e35,), args=(3, UI))
check('arrasar: sitio 3 sigue el camino original (control)', end == 0x4d5e35 and b.r('ESP') == b.esp0 - 0x58
      and b.r('ESI') == 0x55555555)

# ---- diálogo de reconstruir (0x4b6160)
def raze_ext(bb):
    bb.set_tile(5, 5, WATER, 0, 0x85); bb.set_tile(6, 5, WATER, 0, 0x85)
for nombre, code, armies, ext, esperado, msgs in [
        ('reconstruir: derribado vacío abre el diálogo', BC(5, 5), [(4, 5, UI, True)], raze_ext, 0x4b6180, []),
        ('reconstruir: con un ejército encima, aviso', BC(6, 5), [(5, 5, UI, True)], raze_ext, END, [('text', 0x72)]),
        ('reconstruir: enemigo encima, aviso', BC(6, 5), [(6, 5, 3, True)], raze_ext, END, [('text', 0x72)]),
        ('reconstruir: puente entero, nada', BC(5, 5), [], None, END, []),
        ('reconstruir: sitio 2 (control)', 2, [], None, 0x4b6165, [])]:
    b = Bench(armies=armies, extra=ext)
    b.mu.mem_write(0x587e5c, struct.pack('<h', -7))
    end = b.run(0x4b6160, (0x4b6180, 0x4b6165), args=(0xffff0000 | code,))
    sel = struct.unpack('<h', b.mu.mem_read(0x587e5c, 2))[0]
    texts = [c for c in b.calls if isinstance(c, tuple) and c[0] == 'text']
    good = end == esperado and texts == msgs
    if esperado == 0x4b6180: good = good and sel == BC(5, 5) and b.r('ESP') == b.esp0
    elif esperado == 0x4b6165: good = good and b.r('EAX') & 0xffff == 2 and sel == -7
    else: good = good and sel == -7 and b.r('ESP') == b.esp0 + 4 and (not msgs or b.calls[-1][0] == 'msg' and b.calls[-1][2] == 0x14)
    check(nombre, good and all(b.r(k) == b.regs_in[k] for k in ('EBX', 'ESI', 'EDI', 'EBP')), f'end={end} calls={b.calls}')

# ---- dibujo del diálogo (0x4b64a0)
for nombre, sel, ev, esperado in [('dibujo: puente no dibuja', BC(5, 5), 4, 0x4b64e3), ('dibujo: sitio (control)', 2, 4, 0x4b64a7),
                                  ('dibujo: otro evento', 2, 3, 0x4b64e3)]:
    b = Bench(); b.mu.mem_write(0x587e5c, struct.pack('<h', sel))
    end = b.run(0x4b64a0, (0x4b64a7, 0x4b64e3), args=(ev, 0, 0))
    check(nombre, end == esperado and b.r('ESP') == b.esp0)

# ---- texto "Rebuilding %s" (0x4b64f0)
for nombre, sel, esperado in [('texto build: puente', BC(5, 5), THE_BRIDGE), ('texto build: sitio 5 (control)', 5, SITE_NAME(5))]:
    b = Bench(); b.mu.mem_write(0x587e5c, struct.pack('<h', sel))
    end = b.run(0x4b64f0, (0x4b650c,), stack_words=[0] * 4)
    check(nombre, end == 0x4b650c and b.r('EAX') == esperado and b.r('ECX') == 0x589880 and b.r('ESP') == b.esp0)

# ---- costo (0x4b65e0 -> si en 0x4b65ec)
for nombre, code, esperado in [('costo: puente = fundar ciudad', BC(5, 5), 1000), ('costo: sitio = reconstruir sitio', 2, 300)]:
    b = Bench()
    end = b.run(0x4b65e0, (0x4b65ec,), args=(code, UI))
    check(nombre, end == 0x4b65ec and b.r('ESI') & 0xffff == esperado and b.r('EAX') == UI and b.r('ESP') == b.esp0 - 4)

# ---- aplicación de reconstruir (0x4b6610(código, costo, jugador))
for nombre, code, armies, ext, cond in [
        ('reconstruir: repone y cobra', BC(6, 5), [(4, 5, UI, True)], raze_ext,
         lambda b: intact(b, (5, 5), (6, 5)) and b.calls == [('gold', UI, -1000), 'graph', 'view']),
        ('reconstruir: ocupado no hace nada', BC(6, 5), [(6, 5, 3, True)], raze_ext,
         lambda b: razed(b, (5, 5), (6, 5)) and b.calls == []),
        ('reconstruir: entero no cobra', BC(5, 5), [], None, lambda b: intact(b, (5, 5), (6, 5)) and b.calls == [])]:
    b = Bench(armies=armies, extra=ext)
    end = b.run(0x4b6610, (), args=(code, 1000, UI))
    check(nombre, end == END and cond(b) and b.saved_ok(4), f'calls={b.calls} t55={b.tile(5,5)}')
b = Bench()
end = b.run(0x4b6610, (0x4b6616,), args=(2, 300, UI))
check('reconstruir: sitio 2 sigue el camino original (control)', end == 0x4b6616 and b.r('ESP') == b.esp0 - 4
      and b.calls == [])

mal = res.count(False)
print('TODO OK' if not mal else f'{mal} MAL'); sys.exit(1 if mal else 0)
