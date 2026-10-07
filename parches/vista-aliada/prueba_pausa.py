# Prueba de juguete de la pausa mientras se vota (pz_* de build.py) sobre el exe parcheado, en unicorn.
# Uso: python prueba_pausa.py [carpeta]   (por defecto C:\Warlords3; armarla antes con build.py)
# Una línea de tiempo simulada (GetTickCount y timeGetTime dan el mismo reloj): empieza un turno con límite de 1 minuto
# (0x4c0f70), y cada segundo corre la función ociosa (0x4dea40) y el control del reloj del bucle principal (0x4c0fe0),
# con lo que este llama al vencer interceptado. Los paquetes de red entran por la recepción real (0x4b6a16).
# Controles: sin votación el turno vence como en el original; abrir Sorteo no pausa; un estado sin orden de abrir no
# pausa; otro remitente; sin pausa el despacho deja pasar los clics; un mensaje del juego en pantalla no se toca.
import os, sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

DIR = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3'
pe = pefile.PE(os.path.join(DIR, 'DarklordAV.exe')); BASE = pe.OPTIONAL_HEADER.ImageBase
img = bytes(pe.get_memory_mapped_image())
SIZE = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
STACK, RET, STUBS, PKT, MSG = 0x1f0000, 0x100, 0x300000, 0x150000, 0x160000
MACHINE, LIMIT, TURN_END, GRACE_END, GAMECLK = 0x5899fc, 0x53c38f, 0x4ff7a8, 0x5885cc, 0x5032f8
MSG_TXT, MSG_END = 0x5885e8, 0x5885d8
TEXT = b'Votacion en curso: partida en pausa\0'
PZ_VARS = BASE + img.index(TEXT) + len(TEXT)
PZ_ON, PZ_ARM = PZ_VARS, PZ_VARS + 1
CLOSEPKT = img[PZ_VARS + 12 - BASE:PZ_VARS + 12 - BASE + 31]
PZ_DPTR = struct.unpack_from('<I', img, 0x4dea0e - BASE)[0]
IMPORTS = {}
for e in pe.DIRECTORY_ENTRY_IMPORT:
    for i in e.imports:
        if i.name: IMPORTS[i.name.decode()] = i.address

mal = 0
def ver(nombre, r, esperado):
    global mal
    ok = r == esperado
    mal += not ok
    print('OK ' if ok else 'MAL', nombre, '->', r)

def cstr(mu, a):
    s = bytes(mu.mem_read(a, 512)); return s[:s.index(b'\0')]
def rd(mu, a): return struct.unpack('<i', mu.mem_read(a, 4))[0]
def wr(mu, a, v): mu.mem_write(a, struct.pack('<i', v))

class Juego:
    """Una PC con el exe parcheado, un reloj que se adelanta a mano y Windows simulado."""
    def __init__(self, machine=0, proceso_ok=True, limite=2):
        mu = self.mu = Uc(UC_ARCH_X86, UC_MODE_32)
        mu.mem_map(BASE, SIZE); mu.mem_write(BASE, img[:SIZE])
        mu.mem_map(0x100000, 0x100000)
        mu.mem_map(STUBS, 0x1000)
        mu.mem_write(MACHINE, struct.pack('<H', machine))
        mu.mem_write(LIMIT, bytes([limite << 3]))
        self.t, self.ok, self.log, self.fs = 1000000, proceso_ok, [], {}
        api = {'GetTickCount': (0, lambda a: self.t), 'timeGetTime': (0, lambda a: self.t),
               'DeleteFileA': (1, lambda a: 0), 'MoveFileA': (2, lambda a: 0), 'CreateFileA': (7, lambda a: -1),
               'CloseHandle': (1, lambda a: 1), 'CreateProcessA': (10, self.proceso),
               'CreateThread': (6, lambda a: 0x601), 'DispatchMessageA': (1, self.despachar)}
        for k, (nombre, (n, fn)) in enumerate(api.items()):
            stub = STUBS + 0x10 * k
            mu.mem_write(IMPORTS[nombre], struct.pack('<I', stub))
            def g(mu, a, size, _, n=n, fn=fn):
                sp = mu.reg_read(UC_X86_REG_ESP)
                ret, *args = struct.unpack('<11I', mu.mem_read(sp, 44))
                mu.reg_write(UC_X86_REG_EAX, fn(args) & 0xffffffff)
                mu.reg_write(UC_X86_REG_ESP, sp + 4 + 4 * n); mu.reg_write(UC_X86_REG_EIP, ret)
            mu.hook_add(UC_HOOK_CODE, g, begin=stub, end=stub)
        # lo que llaman la función ociosa original y el control del reloj
        self.interceptar(0x4ec800, lambda a: None)
        self.interceptar(0x4df3e0, lambda a: None)
        self.interceptar(0x4dd390, lambda a: 1)                                    # una sola PC
        self.interceptar(0x421310, lambda a: 0)
        self.interceptar(0x4465e0, lambda a: 0)
        self.interceptar(0x4c0c00, lambda a: self.log.append(('fin de turno', (self.t - 1000000) // 1000)))
        self.interceptar(0x4e33f0, lambda a: self.log.append(('quedan', a[0])), pop=8)   # ret 8
        self.interceptar(0x4dd3b0, lambda a: self.log.append(('red', a[0], bytes(mu.mem_read(a[1], a[2])))))
    def interceptar(self, addr, fn, pop=0):
        def g(mu, a, size, _):
            sp = mu.reg_read(UC_X86_REG_ESP)
            ret, *args = struct.unpack('<5I', mu.mem_read(sp, 20))
            r = fn(args)
            mu.reg_write(UC_X86_REG_EAX, (r or 0) & 0xffffffff)
            mu.reg_write(UC_X86_REG_ESP, sp + 4 + pop); mu.reg_write(UC_X86_REG_EIP, ret)
        self.mu.hook_add(UC_HOOK_CODE, g, begin=addr, end=addr)
    def proceso(self, a):
        self.log.append(('proceso',))
        if not self.ok: return 0
        self.mu.mem_write(a[9], struct.pack('<II', 0x501, 0x502)); return 1
    def despachar(self, a):
        m = struct.unpack('<I', self.mu.mem_read(a[0] + 4, 4))[0]
        self.log.append(('despacho', hex(m))); return 7
    def correr(self, start, args=()):
        mu = self.mu
        mu.mem_write(STACK, struct.pack('<I', RET) + b''.join(struct.pack('<I', x) for x in args))
        regs = ((UC_X86_REG_EBX, 0x9abc), (UC_X86_REG_EDI, 0x5678), (UC_X86_REG_EBP, 0xdef0), (UC_X86_REG_ESI, 0x1234))
        for r, v in regs: mu.reg_write(r, v)
        mu.reg_write(UC_X86_REG_ESP, STACK)
        mu.emu_start(start, RET, count=200000)
        assert mu.reg_read(UC_X86_REG_EIP) == RET, hex(mu.reg_read(UC_X86_REG_EIP))
        for r, v in regs: assert mu.reg_read(r) == v, (start, r)
        return mu.reg_read(UC_X86_REG_EAX)
    def paquete(self, tipo, carga, remitente=0):
        mu = self.mu
        mu.mem_write(PKT, struct.pack('<IhhI', 0, tipo, remitente, 7) + carga)
        mu.reg_write(UC_X86_REG_ESP, STACK); mu.reg_write(UC_X86_REG_ESI, PKT)
        mu.emu_start(0x4b6a16, 0x4b85bb, count=5000)
        assert mu.reg_read(UC_X86_REG_EIP) == 0x4b85bb
    def abrir(self, t=0, remitente=0): self.paquete(0x2a0, struct.pack('<I', t), remitente)
    def estado(self, texto, t=0, remitente=0): self.paquete(0x2a1, struct.pack('<I', t) + texto + b'\0', remitente)
    def turno(self): self.correr(0x4c0f70)
    def segundo(self, dt=1000):
        self.t += dt
        self.correr(0x4dea40)
        self.correr(0x4c0fe0, [1])
    def pausa(self): return self.mu.mem_read(PZ_ON, 1)[0]
    def vencio(self): return [x[1] for x in self.log if x[0] == 'fin de turno'][:1]   # el primero (acá el turno no termina)
    def renglones(self):
        return [(cstr(self.mu, MSG_TXT + 64 * i).decode(), rd(self.mu, MSG_END + 4 * i) - self.t) for i in range(4)
                if self.mu.mem_read(MSG_TXT + 64 * i, 1)[0]]

VOT = lambda fase: f'VOT ab12cd34 {fase} 0 0 s-n-----'.encode()

# ---------------------------------------------------------------- el reloj del turno
print('-- reloj del turno (límite 1 minuto)')
g = Juego(); g.turno()
for s in range(70): g.segundo()
ver('control: sin votación vence al segundo 61, como en el original', g.vencio(), [61])

g = Juego(); g.turno()
for s in range(1, 200):
    g.segundo()
    if s == 10: g.abrir()
    if 10 < s < 100 and s % 3 == 0: g.estado(VOT('libre' if s < 50 else 'auto'))
    if s == 100: g.estado(VOT('cerrado'))
ver('votación de 90 s (segundos 10 a 100): vence al 151 (le quedaban 50)', g.vencio(), [151])
q = [x[1] for x in g.log if x[0] == 'quedan']
ver('  el reloj en pantalla se queda en 50 durante la votación', sorted(set(q[10:99])), [50])
ver('  y sigue bajando después', q[100:103], [49, 48, 47])

g = Juego(); g.turno()
for s in range(1, 200):
    g.segundo()
    if s == 10: g.abrir()
ver('sin estados (programa colgado): se reanuda a los 60 s y vence al 121', g.vencio(), [121])

g = Juego(); g.turno()
for s in range(1, 100):
    g.segundo()
    if s == 10: g.abrir(1)
ver('control: abrir Sorteo no pausa', g.vencio(), [61])

g = Juego(); g.turno()
for s in range(1, 100):
    g.segundo()
    if s % 3 == 0: g.estado(VOT('libre'))
ver('control: estado sin orden de abrir (un .op viejo) no pausa', (g.vencio(), g.pausa()), ([61], 0))

g = Juego(); g.turno()
for s in range(1, 100):
    g.segundo()
    if s == 10: g.abrir(0, remitente=2)
ver('control: orden de abrir de otra PC no pausa', g.vencio(), [61])

g = Juego(); g.turno()
for s in range(1, 330):
    g.segundo()
    if s == 10: g.abrir()
    if 10 < s < 199 and s % 3 == 0: g.estado(VOT('libre'))
    if s == 40: g.estado(b'XYZ basura')
ver('estado que no es VOT: se ignora; último estado al 198, reanuda al 258, vence al 309', g.vencio(), [309])

# ---------------------------------------------------------------- otros relojes
print('-- otros relojes y controles del reloj en diálogos')
g = Juego(); g.turno(); mu = g.mu
wr(mu, GRACE_END, g.t + 20000); wr(mu, GAMECLK + 0x4c, g.t + 600000); wr(mu, GAMECLK + 0x50, g.t)
antes = [rd(mu, a) for a in (TURN_END, GRACE_END, GAMECLK + 0x4c)]
g.segundo(); g.abrir()
for s in range(30): g.segundo()
despues = [rd(mu, a) for a in (TURN_END, GRACE_END, GAMECLK + 0x4c)]
ver('30 s de pausa: turno, gracia y fin de partida corridos 30 s', [b - a for a, b in zip(antes, despues)], [30000] * 3)
g.t += 5000; g.correr(0x4c10c0)
ver('  al entrar a 0x4c10c0 (sin pasar por la ociosa) se corre lo que faltaba', rd(mu, TURN_END) - despues[0], 5000)
g.t += 4000; g.correr(0x4c1250)
ver('  y al entrar a 0x4c1250', rd(mu, TURN_END) - despues[0], 9000)
g.estado(VOT('cerrado')); g.t += 7000; g.correr(0x4c1250)
ver('  después de "cerrado" ya no se corre', rd(mu, TURN_END) - despues[0], 9000)
g = Juego(); g.turno(); mu = g.mu
wr(mu, GAMECLK + 0x4c, -1); wr(mu, GAMECLK + 0x50, g.t)
g.abrir()
for s in range(10): g.segundo()
ver('control: partida sin límite de minutos (-1) queda en -1', rd(mu, GAMECLK + 0x4c), -1)

# ---------------------------------------------------------------- aviso en pantalla
print('-- aviso en pantalla')
g = Juego(); g.turno(); mu = g.mu
mu.mem_write(MSG_TXT, b'Your turn has ended\0'); wr(mu, MSG_END, g.t + 2000)
g.abrir(); g.segundo()
ver('en pausa: el aviso en el renglón libre, el del juego intacto', g.renglones(),
    [('Your turn has ended', 1000), ('Votacion en curso: partida en pausa', 5000)])
for s in range(20): g.segundo()
ver('  20 s después sigue uno solo, con el vencimiento estirado', [r for r in g.renglones() if r[0].startswith('Vot')],
    [('Votacion en curso: partida en pausa', 5000)])
g.estado(VOT('cerrado')); g.segundo()
ver('  "cerrado": el aviso vence ya', [r for r in g.renglones() if r[0].startswith('Vot')],
    [('Votacion en curso: partida en pausa', 0)])

# ---------------------------------------------------------------- teclado y mouse
print('-- despacho de mensajes')
def despacho(g, msgs):
    g.log.clear()
    for m in msgs:
        g.mu.mem_write(MSG, struct.pack('<IIII', 0x777, m, 0, 0))
        g.correr(struct.unpack('<I', g.mu.mem_read(PZ_DPTR, 4))[0], [MSG])
    return [x[1] for x in g.log if x[0] == 'despacho']
MSGS = [0xf, 0x100, 0x102, 0x104, 0x109, 0x10a, 0x200, 0x201, 0x202, 0x204, 0x20a, 0x20e, 0x20f, 0x113]
g = Juego(); g.abrir()
ver('en pausa: pasan pintar, mover el mouse, temporizador; no teclas ni botones', despacho(g, MSGS),
    ['0xf', '0x10a', '0x200', '0x20f', '0x113'])
g.estado(VOT('cerrado'))
ver('control: después de "cerrado" pasa todo', despacho(g, MSGS), [hex(m) for m in MSGS])
ver('control: sin votación pasa todo', despacho(Juego(), MSGS), [hex(m) for m in MSGS])
sitios = [(0x417652, 'ff15'), (0x417847, 'ff15'), (0x4790c9, '8b1d'), (0x4de957, '8b3d'), (0x4dea0c, 'ff15'), (0x4e5db8, '8b1d')]
ver('los 6 bucles de mensajes despachan por el filtro', [img[a - BASE:a - BASE + 6].hex() for a, _ in sitios],
    [op + struct.pack('<I', PZ_DPTR).hex() for _, op in sitios])
ver('control: ningún otro lugar llama a DispatchMessageA directo', img.count(struct.pack('<I', IMPORTS['DispatchMessageA'])), 1)

# ---------------------------------------------------------------- sin el programa
print('-- sin el programa de Votación')
g = Juego(proceso_ok=False); g.abrir(); g.segundo()
red = [x for x in g.log if x[0] == 'red']
ver('el anfitrión manda "cerrado" para que nadie quede en pausa', red, [('red', 0x2a1, CLOSEPKT)])
g.estado(CLOSEPKT[4:-1])
ver('  y al recibirlo se reanuda', g.pausa(), 0)
g = Juego(machine=2, proceso_ok=False); g.abrir(); g.segundo()
ver('control: otra PC sin el programa no manda nada', [x for x in g.log if x[0] == 'red'], [])
g = Juego(proceso_ok=False); g.abrir(1); g.segundo()
ver('control: sin el programa de Sorteo no manda nada', [x for x in g.log if x[0] == 'red'], [])
print('MAL:', mal)
sys.exit(1 if mal else 0)
