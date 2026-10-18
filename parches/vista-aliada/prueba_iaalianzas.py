# Prueba de la destreza de alianzas de la IA de prueba (ai_ally, specs/ia-alianzas-v1.md) sobre el exe parcheado, en
# unicorn, con la partida Tanda_Border_Alianzas (equipos 0135 | 2467; la diplomacia se arma acá: aliados dentro del
# equipo, guerra entre equipos).
# Uso: python prueba_iaalianzas.py [DarklordAV.exe] [partida.SAV]
# ai_ally se llama como en 0x40edf1 (pila, 0), con stubs: 0x40c990 (la decisión original: se anota que se llamó) y
# 0x40d2b0 (mover la pila: se anota el destino). Los eventos se leen de lo que ia_evt manda a fprintf.
# Esperado: los casos del Definition of done del spec (refugio 1a/1b/1c, salidas 3a/3b, req. 4 y 5, refuerzo 6a/6b
# con y sin importancia 7a, casos límite) y los controles: con la IA original y sin IA.INI no cambia nada.
import sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

EXE = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe'
sav = open(sys.argv[2] if len(sys.argv) > 2 else r'C:\Warlords3\SAVES\Tanda_Border_Alianzas.SAV', 'rb').read()
CITIES, DIPLO = 0x537e2c, 0x55ee4c
EQ = ((0, 1, 3, 5), (2, 4, 6, 7))
P = 2                      # color con la IA de prueba (equipo 2467); su pila 0 tiene dos ejércitos
DATA = (0x4f9000, 0xb0000)

pe = pefile.PE(EXE); img = pe.get_memory_mapped_image()
def rva(va): return va - 0x400000
# direcciones del parche: ai_ally por el call de 0x40edf1; IA_ON e IA_MODE por sus primeras instrucciones
AI_ALLY = 0x40edf6 + struct.unpack_from('<i', img, rva(0x40edf2))[0]
assert img[rva(AI_ALLY):rva(AI_ALLY) + 2] == b'\x80\x3d', 'ai_ally no empieza con cmp byte ptr [ia_on]'
IA_ON = struct.unpack_from('<I', img, rva(AI_ALLY) + 2)[0]

class Maquina:
    def __init__(s):
        s.mu = mu = Uc(UC_ARCH_X86, UC_MODE_32)
        mu.mem_map(0x400000, (len(img) + 0xfff) & ~0xfff); mu.mem_write(0x400000, img)
        mu.mem_map(0x10000000, 0x100000); mu.mem_map(0xdead0000, 0x1000); mu.mem_write(0xdead0000, b'\xc3' * 0x1000)
        off = 0x6d
        for va, n in ((0x503e00, 0x12), (0x503e58, 0x32000), (0x535ed0, 0xa96), (0x536b30, 0x2d894)):
            mu.mem_write(va, sav[off:off + n]); off += n
        s.evts, s.orig, s.moves = [], 0, []
        s.imports()
        s.stub(0x40c990, s._orig)
        s.stub(0x40d2b0, s._move)
        # 0x497240 (formar el grupo) llama a rutinas de pantalla que acá no tienen sus objetos armados
        s.stub(0x486ab0, lambda a: 0); s.stub(0x4868d0, lambda a: 0)
        # 0x4974a0 (distancia euclídea) termina en _ftol de la FPU: se calcula acá igual que el juego
        lim = struct.unpack_from('<d', img, rva(0x4f5350))[0]
        def dist(a):
            q = (a[0] - a[2]) ** 2 + (a[1] - a[3]) ** 2
            return 0x2710 if q < lim else int(q ** 0.5)
        s.stub(0x4974a0, lambda a: dist([((v & 0xffff) ^ 0x8000) - 0x8000 for v in a[:4]]))
        s.call(0x4a4f90, [])
        s.data0 = s.rd(*DATA)
    def _orig(s, a): s.orig += 1; return 0
    def _move(s, a): s.moves.append((a[0] & 0xffff, a[1] & 0xffff)); return 1
    def imports(s):
        mu = s.mu; mu.mem_map(0xdead1000, 0x10000); mu.mem_map(0x30000000, 0x4000000)
        names, k = {}, 0
        for d in pe.DIRECTORY_ENTRY_IMPORT:
            for imp in d.imports:
                stub = 0xdead1000 + 16 * k; k += 1
                mu.mem_write(imp.address, struct.pack('<I', stub)); names[stub] = (imp.name or b'?').decode()
        ARGS = {'GlobalAlloc': 2, 'GlobalLock': 1, 'GlobalUnlock': 1, 'GlobalFree': 1, 'GlobalHandle': 1}
        s.heap = 0x30000000
        def h(m, a, size, ud):
            n = names.get(a); sp = m.reg_read(UC_X86_REG_ESP)
            ret = struct.unpack('<I', m.mem_read(sp, 4))[0]; args = struct.unpack('<10i', m.mem_read(sp + 4, 40))
            pop = ARGS.get(n, 0)
            if n == 'GlobalAlloc':
                sz = (args[1] + 15) & ~15; r = s.heap; s.heap += sz; m.mem_write(r, bytes(sz))
            elif n in ('GlobalLock', 'GlobalHandle'): r = args[0]
            elif n in ('GlobalUnlock', 'GlobalFree'): r = 0
            elif n == 'fopen': r = 0x7777
            elif n == 'fclose': r = 0
            elif n == 'fprintf':
                fmt = bytes(m.mem_read(args[1], 40)).split(b'\0')[0]
                if fmt == b'%d,%d,%d,%d,%d,%d,%d\n': s.evts.append(tuple(args[2:9]))
                r = 1
            else: raise RuntimeError('importación no emulada: ' + n)
            m.reg_write(UC_X86_REG_EAX, r & 0xffffffff); m.reg_write(UC_X86_REG_ESP, sp + 4 + 4 * pop)
            m.reg_write(UC_X86_REG_EIP, ret)
        mu.hook_add(UC_HOOK_CODE, h, begin=0xdead1000, end=0xdead1000 + 16 * k)
    def stub(s, addr, fn):
        def h(m, a, size, ud):
            sp = m.reg_read(UC_X86_REG_ESP)
            ret = struct.unpack('<I', m.mem_read(sp, 4))[0]; args = struct.unpack('<6i', m.mem_read(sp + 4, 24))
            m.reg_write(UC_X86_REG_EAX, fn(args) & 0xffffffff)
            m.reg_write(UC_X86_REG_ESP, sp + 4); m.reg_write(UC_X86_REG_EIP, ret)
        s.mu.hook_add(UC_HOOK_CODE, h, begin=addr, end=addr)
    def call(s, addr, args):
        mu = s.mu; sp = 0x10080000
        for a in reversed(args): sp -= 4; mu.mem_write(sp, struct.pack('<i', a))
        sp -= 4; mu.mem_write(sp, struct.pack('<I', 0xdead0000)); mu.reg_write(UC_X86_REG_ESP, sp)
        mu.emu_start(addr, 0xdead0000, count=100_000_000)
        return mu.reg_read(UC_X86_REG_EAX)
    def rd(s, a, n): return bytes(s.mu.mem_read(a, n))
    def u16(s, a): return struct.unpack('<H', s.rd(a, 2))[0]
    def s16(s, a): return struct.unpack('<h', s.rd(a, 2))[0]
    def w(s, a, fmt, *v): s.mu.mem_write(a, struct.pack(fmt, *v))

m = Maquina()
W, H = m.u16(0x503e00), m.u16(0x503e02)
NARM = m.s16(0x54fe50)
fallas = 0
def check(nombre, cond, detalle=''):
    global fallas
    print(('OK   ' if cond else 'FALLA'), nombre, '' if cond else detalle)
    fallas += not cond

# ---------------------------------------------------------------- preparación del escenario
def arm(i): return 0x54fe50 + i * 0x1c
def owner(i): return (m.u16(arm(i) + 0xe) >> 5) & 15
def alive(i): return m.rd(arm(i) + 0x13, 1)[0] & 0x40
def setfs(i, f, h):  # fuerza base y vida en la palabra +0xe
    v = m.u16(arm(i) + 0xe); m.w(arm(i) + 0xe, '<H', (v & 0x1ff) | (f << 9) | (h << 13))
def put(i, x, y): m.w(arm(i) + 2, '<hh', x, y)
def kill(i): m.w(arm(i) + 0x13, '<B', m.rd(arm(i) + 0x13, 1)[0] & ~0x40)
def revive(i): m.w(arm(i) + 0x13, '<B', m.rd(arm(i) + 0x13, 1)[0] | 0x40)
def city(i): return m.s16(CITIES + i * 0xde), m.s16(CITIES + i * 0xde + 2)
def cowner(i): return m.rd(CITIES + i * 0xde + 0xa5, 1)[0]
def tclass(x, y):
    sh = m.rd(0x503e06, 1)[0]
    t = m.u16(0x503e58 + ((y * 10) << sh) + x * 10) & 0x1f
    return m.u16(0x535f0c + t * 0x58)
for a in range(8):
    for b in range(8):
        m.w(DIPLO + a * 56 + b, '<B', 0 if (a in EQ[0]) == (b in EQ[0]) else 2)
for p in range(8): m.w(0x536b30 + p * 0x1f8 + 0xe2, '<h', 2)      # todos de la computadora
m.w(0x4fb0ec, '<h', P); m.w(0x537ce8, '<h', P)
REC = 0x561f00 + P * 0x49a
def setown(i, o): v = m.u16(arm(i) + 0xe); m.w(arm(i) + 0xe, '<H', (v & ~0x1e0) | (o << 5))
# en el SAV (turno 0) solo viven los héroes de cada color y 55 neutrales: la pila de prueba es el héroe de P más un
# neutral pasado a P; los enemigos, el aliado del dueño y el ejército propio suelto son neutrales pasados a esos colores
neut = [i for i in range(1, NARM) if alive(i) and owner(i) == 8]
LEAD = next(i for i in range(1, NARM) if alive(i) and owner(i) == P and (m.u16(arm(i) + 0xe) & 0x1f) == 0x10)
SEG = neut.pop(); setown(SEG, P)
m.w(REC + 0xc, '<8h', LEAD, SEG, 0, 0, 0, 0, 0, 0)
check('la pila 0 de P tiene dos ejércitos vivos', alive(LEAD) and alive(SEG), (LEAD, SEG))
enem = [neut.pop() for _ in range(3)]
for i in enem: setown(i, 0)
mios = [neut.pop()]; setown(mios[0], P)
ncity = m.s16(0x537e2a)
aliadas = [i for i in range(ncity) if cowner(i) in (4, 6, 7) and m.rd(CITIES + i * 0xde + 0xa4, 1)[0]]
check('hay enemigos y ciudades aliadas', len(enem) >= 3 and aliadas, (len(enem), aliadas))
C = aliadas[0]; CX, CY = city(C); OWN = cowner(C)
# casilla de tierra a 3 de la ciudad, para la pila
def tierra(x, y): return 0 <= x < W and 0 <= y < H and tclass(x, y) not in (1, 4)
T = next((CX + dx, CY + dy) for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-3, -3), (3, 3), (-3, 3), (3, -3))
         if tierra(CX + dx, CY + dy))
print('ciudad aliada', C, (CX, CY), 'dueño', OWN, 'pila en', T, 'líder', LEAD, SEG)
# a todos los demás ejércitos se los aleja (casilla 0,0) para que no interfieran; se guardan sus posiciones
for i in range(1, NARM):
    if alive(i) and i not in (LEAD, SEG): put(i, 0, 0)
base = m.rd(0x536b30, 0x2d894)
PDAT = 0x6c9000, 0x400000 + len(img) - 0x6c9000         # datos del parche (tablas de refugio y amenaza) a restaurar
pdat = m.rd(*PDAT)
AWAY = (0, 0)
def escenario(modo=1, on=1):
    m.mu.mem_write(0x536b30, base); m.mu.mem_write(PDAT[0], pdat)
    m.w(IA_ON, '<B', on)
    m.w(IA_MODE + P, '<B', modo)
    put(LEAD, *T); put(SEG, *T)
    m.w(0x56ea90 + P * 0x4f0 + 0x14, '<h', 30)
    m.evts.clear(); m.orig = 0; m.moves.clear()
# IA_MODE: los 8 bytes antes de IA_ON (place_data seguidos: ia_mode y después ia_on)
IA_MODE = IA_ON - 8
def jugar(stk=0):
    m.evts.clear(); m.orig = 0; m.moves.clear()
    m.call(AI_ALLY, [stk, 0])
    return [(e[3], e[4], e[5], e[6]) for e in m.evts]
def tipos(ev): return [e[0] for e in ev]
E1, E2, E3 = enem[:3]

# ---------------------------------------------------------------- refugio 1a
escenario(1)
setfs(E1, 15, 7); put(E1, T[0] + 4, T[1])          # 105 de fuerza a 4 casillas
ev = jugar()
r7 = [e for e in ev if e[0] == 7]
# elige la ciudad compartida más lejos de la amenaza: desde acá C es esa
cc = [i for i in range(ncity) if r7 and city(i) == r7[0][1:3]]
check('1a: refugio decidido (evento 7, motivo 1) en una ciudad de un aliado', cc and r7[0][3] == 1
      and cowner(cc[0]) in (4, 6, 7), ev)
check('1a: mueve la pila a esa ciudad', r7 and m.moves == [r7[0][1:3]], m.moves)
if cc: C = cc[0]; CX, CY = city(C); OWN = cowner(C)
print('ciudad de refugio', C, (CX, CY), 'dueño', OWN)
check('1a: no llama a la decisión original', m.orig == 0)
check('1a: anota la pila amenazada (evento 11)', 11 in tipos(ev), ev)
# el mismo caso con la IA original
escenario(0)
setfs(E1, 15, 7); put(E1, T[0] + 4, T[1])
d0 = m.rd(0x536b30, 0x2d894) + m.rd(0x503e00, 0x32058) + m.rd(0x5020d0, 8)
ev = jugar()
check('1a con IA original: el estado del juego no cambia (byte a byte)',
      m.rd(0x536b30, 0x2d894) + m.rd(0x503e00, 0x32058) + m.rd(0x5020d0, 8) == d0)
check('1a con IA original: solo el evento 11, sin mover, sigue la original', tipos(ev) == [11] and not m.moves
      and m.orig == 1, (ev, m.moves, m.orig))
# sin IA.INI
escenario(1, on=0)
setfs(E1, 15, 7); put(E1, T[0] + 4, T[1])
d0 = m.rd(0x536b30, 0x2d894)
ev = jugar()
check('sin IA.INI: nada (ni eventos ni movimiento), sigue la original', not ev and not m.moves and m.orig == 1)
check('sin IA.INI: el estado del juego no cambia', m.rd(0x536b30, 0x2d894) == d0)
# enemigo fuera de alcance: no hay amenaza
escenario(1)
setfs(E1, 15, 7); put(E1, T[0] + 20, T[1]) if T[0] + 20 < W else put(E1, T[0] - 20, T[1])
ev = jugar()
check('enemigo lejos: sin refugio, sigue la original', 7 not in tipos(ev) and m.orig == 1, ev)
# enemigo más débil al lado
escenario(1)
setfs(E1, 1, 1); put(E1, T[0] + 2, T[1])
ev = jugar()
check('enemigo más débil: sin refugio', 7 not in tipos(ev) and 11 not in tipos(ev), ev)

# ---------------------------------------------------------------- casos límite del refugio
escenario(1)
setfs(E1, 15, 7); put(E1, T[0] + 4, T[1])
m.w(0x56ea90 + P * 0x4f0 + 0x14, '<h', 0)
ev = jugar()
check('sin movimiento (ninguna ciudad al alcance): sigue la original', 7 not in tipos(ev) and m.orig == 1, ev)
escenario(1)
setfs(E1, 15, 7); put(E1, T[0] + 4, T[1])
llenos = neut[:32]
for k, i in enumerate(llenos): revive(i); put(i, CX + (k & 1), CY + ((k >> 1) & 1))
ev = jugar()
check('ciudad llena (32 ejércitos): no la elige', all(e[1:3] != (CX, CY) for e in ev if e[0] == 7), ev)
escenario(1)
setfs(E1, 15, 7); put(E1, T[0] + 4, T[1])
m.w(DIPLO + P * 56 + OWN, '<B', 1); m.w(DIPLO + OWN * 56 + P, '<B', 1)
ev = jugar()
check('sin alianza con el dueño: no es refugio', 7 not in tipos(ev) and m.orig == 1, ev)
m.w(DIPLO + P * 56 + OWN, '<B', 0); m.w(DIPLO + OWN * 56 + P, '<B', 0)

# ---------------------------------------------------------------- 1c: héroe enemigo que viene hacia la pila
escenario(1)
hero = next(i for i in range(1, NARM) if (m.u16(arm(i) + 0xe) & 0x1f) == 0x10 and owner(i) == 1)
revive(hero); setfs(hero, 1, 1); put(hero, T[0] + 3, T[1]); m.w(arm(hero) + 6, '<hh', T[0], T[1])
ev = jugar()
check('1c: héroe débil que viene: refugio motivo 3', (7, CX, CY, 3) in ev, ev)
escenario(1)
revive(hero); setfs(hero, 1, 1); put(hero, T[0] + 3, T[1]); m.w(arm(hero) + 6, '<hh', T[0] + 10, T[1] + 10)
ev = jugar()
check('1c control: héroe que va a otro lado: sin refugio', 7 not in tipos(ev), ev)

# ---------------------------------------------------------------- 1b: débil después de una batalla
escenario(1)
setfs(LEAD, 3, 3); setfs(SEG, 3, 3)
turno = m.s16(0x503328)
ev = jugar()                                       # anota la fuerza (18) en este turno
check('1b: primera decisión sin amenaza, original', 7 not in tipos(ev) and m.orig == 1, ev)
m.w(0x503328, '<h', turno + 1); kill(SEG); setfs(LEAD, 2, 3)   # 6 < 18 / 2
put(LEAD, *T)
ev = jugar()
check('1b: perdió más de la mitad: refugio motivo 2 en una ciudad de un aliado', any(e[0] == 7 and e[3] == 2 and any(
    city(i) == e[1:3] and cowner(i) in (4, 6, 7) for i in range(ncity)) for e in ev), ev)
m.w(0x503328, '<h', turno)

# ---------------------------------------------------------------- salidas y permanencia
def refugiar():
    escenario(1)
    setfs(LEAD, 3, 3); setfs(SEG, 3, 3)
    setfs(E1, 15, 7); put(E1, T[0] + 4, T[1])
    ev = jugar()
    assert (7, CX, CY, 1) in ev, ev
    put(LEAD, CX, CY); put(SEG, CX, CY); put(E1, *AWAY)   # llegó; el enemigo se fue
    m.w(0x503328, '<h', m.s16(0x503328) + 1)
refugiar()
ev = jugar()
check('refugiada, sin cambios: se queda (sin mover, sin la original)', not m.moves and m.orig == 0
      and 8 not in tipos(ev), (ev, m.moves, m.orig))
mio = neut[-1]; setown(mio, OWN)
revive(mio); setfs(mio, 4, 2); put(mio, CX + 1, CY + 1)
ev = jugar()
check('3a: el dueño juntó fuerza nueva: sale (evento 8, n = 1) y sigue la original', (8, CX, CY, 1) in ev
      and m.orig == 1, ev)
refugiar()
setfs(LEAD, 5, 6)                                    # 30 + 9 >= 18 + 9
ev = jugar()
check('3b: se reforzó: sale (evento 8, n = 2)', (8, CX, CY, 2) in ev and m.orig == 1, ev)
refugiar()
setfs(E2, 15, 7); put(E2, CX + 4, CY)
ev = jugar()
check('5: la ciudad amenazada: se queda a defenderla (evento 13)', 13 in tipos(ev) and m.orig == 0 and not m.moves, ev)
ev = jugar()
check('5: el evento 13 se anota una sola vez', 13 not in tipos(ev) and m.orig == 0, ev)
refugiar()
put(LEAD, CX + 5, CY)
ev = jugar()
check('refugiada fuera de la ciudad: vuelve a ella', m.moves == [(CX, CY)] and m.orig == 0, (ev, m.moves))
refugiar()
m.w(DIPLO + P * 56 + OWN, '<B', 2); m.w(DIPLO + OWN * 56 + P, '<B', 2)
ev = jugar()
check('alianza rota: deja el refugio (evento 8, n = 3)', (8, CX, CY, 3) in ev, ev)
m.w(DIPLO + P * 56 + OWN, '<B', 0); m.w(DIPLO + OWN * 56 + P, '<B', 0)
# req. 4: muy débil, sin oro y sin refuerzos cerca
refugiar()
kill(SEG); setfs(LEAD, 2, 2)                          # 4 <= 6
m.w(0x536b30 + P * 0x1f8 + 0xe4, '<h', 50)
ev = jugar()
check('4: muy débil y sin oro: se queda hasta el final (evento 9)', (9, CX, CY, 4) in ev and m.orig == 0, ev)
setfs(LEAD, 5, 6)
ev = jugar()
check('4: después no sale aunque se refuerce', 8 not in tipos(ev) and m.orig == 0, ev)
refugiar()
kill(SEG); setfs(LEAD, 2, 2); m.w(0x536b30 + P * 0x1f8 + 0xe4, '<h', 500)
ev = jugar()
check('4 control: con oro no se queda hasta el final', 9 not in tipos(ev), ev)
refugiar()
kill(SEG); setfs(LEAD, 2, 2); m.w(0x536b30 + P * 0x1f8 + 0xe4, '<h', 50)
revive(mios[0]); put(mios[0], CX + 3, CY)
ev = jugar()
check('4 control: con refuerzos propios cerca no se queda hasta el final', 9 not in tipos(ev), ev)

# ---------------------------------------------------------------- refuerzo
escenario(1)
setfs(E1, 15, 7); put(E1, CX + 5, CY)              # amenaza la ciudad (alcance 4 casillas desde E1... ver abajo)
reach = m.rd(arm(E1) + 0x12, 1)[0] // 2 + 1
put(E1, CX + reach, CY); put(LEAD, *T); put(SEG, *T)
dist_pila = max(abs(T[0] - (CX + reach)), abs(T[1] - CY))
if dist_pila <= m.rd(arm(E1) + 0x12, 1)[0] // 2 + 1:
    put(E1, CX - reach if T[0] > CX else CX + reach, CY)
ev = jugar()
r = [e for e in ev if e[0] == 10]
check('6a: ciudad aliada amenazada al alcance: refuerzo (evento 10, motivo 1)', r and r[0][1:3] == (CX, CY)
      and r[0][3] // 10 == 1 and m.moves == [(CX, CY)], (ev, m.moves))
escenario(1)
put(E1, *AWAY)
ev = jugar()
check('6 control: ciudad sin amenaza: sin refuerzo', 10 not in tipos(ev) and m.orig == 1, ev)
# 6b: la pila no llega este turno (movimiento 1); con importancia y sin ella
def caso6b(imp):
    escenario(1)
    setfs(LEAD, 9, 3); setfs(SEG, 9, 3)
    setfs(E1, 6, 3)
    put(E1, CX - reach if T[0] > CX else CX + reach, CY)
    m.w(0x56ea90 + P * 0x4f0 + 0x14, '<h', 1)
    # importancia 7a por una ciudad propia a 6 casillas: se le da o se le quita a P la más cercana
    cerca = [i for i in range(ncity) if i != C and max(abs(city(i)[0] - CX), abs(city(i)[1] - CY)) <= 6]
    lejos_o = [i for i in range(ncity) if cowner(i) == P]
    for i in lejos_o: m.w(CITIES + i * 0xde + 0xa5, '<B', 8)
    if imp and cerca: m.w(CITIES + cerca[0] * 0xde + 0xa5, '<B', P)
    return jugar(), bool(cerca)
ev, hay = caso6b(True)
r = [e for e in ev if e[0] == 10]
check('6b: no llega, importante (7a) y la suma vence: refuerzo motivo 2, criterio 1',
      hay and r and r[0][3] == 21, (ev, hay))
ev, _ = caso6b(False)
r = [e for e in ev if e[0] == 10]
check('6b control: no llega y no es importante: sin refuerzo (si las ruinas/neutrales no la hacen importante)',
      not r or r[0][3] % 10 == 1, ev)

# ---------------------------------------------------------------- al_surv: resultado de la pila amenazada

def al_surv_addr():
    # al_surv es lo que ia_turn llama justo después de ia_refug: se busca el call a una dirección > ai_ally
    for k in range(rva(AI_ALLY), len(img) - 5):
        if img[k] == 0xe8:
            t = 0x400000 + k + 5 + struct.unpack_from('<i', img, k + 1)[0]
            if AI_ALLY < t < AI_ALLY + 0x1000 and img[rva(t) - 1] in (0xcc, 0xc3, 0x90) and t != AI_ALLY:
                if k > rva(t): return t
AL_SURV = al_surv_addr()
print('al_surv', hex(AL_SURV))
for sobrevive in (True, False):
    escenario(1)
    setfs(E1, 15, 7); put(E1, T[0] + 4, T[1])
    jugar()
    m.w(0x503328, '<h', m.s16(0x503328) + 1)
    if not sobrevive: kill(LEAD)
    m.evts.clear()
    m.call(AL_SURV, [P])
    ev = [(e[3], e[4], e[5], e[6]) for e in m.evts]
    check(f'12: la pila amenazada {"sobrevivió" if sobrevive else "murió"} (evento 12, n = {int(sobrevive)})',
          [e for e in ev if e[0] == 12] == [(12, T[0], T[1], int(sobrevive))], ev)
    m.w(0x503328, '<h', m.s16(0x503328) - 1)
print('\nRESULTADO:', 'TODO OK' if not fallas else f'{fallas} FALLAS')
sys.exit(1 if fallas else 0)
