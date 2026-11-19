# Prueba de juguete del tope de la balsa (rf_turn y boatcarr de build.py, 1.0.266.0; pedido del usuario, 19/11/2026):
# un grupo con "Raft" no puede estar más de 2 vueltas en el agua; al empezar la tercera sin haber desembarcado se hunde
# (0x485610(jugador, ejército, 1, 0, 1, 0)) y en la PC de su jugador suena "splash" (0x4465e0(0x18, -1)).
# Corre rf_turn del DarklordAV.exe armado en unicorn, con 0x43c240 (¿se ahoga?), 0x485610 y 0x4465e0 interceptados.
# Controles que deben sobrevivir: bando sin "Raft" (con "Carrier"), ejército de otro jugador, ejército en tierra,
# ejército embarcado que no se ahoga (volador), ejército con enlace de convoy (bit 0x80), ejército muerto.
# Uso: python prueba_balsatope.py [carpeta]   (por defecto la del juego de pruebas; armar antes con build.py)
import os as _os, sys as _sys; _sys.path.append(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..'))
from juego_pruebas import W3
import os, sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EIP, UC_X86_REG_EAX, UC_X86_REG_EBX

DIR = sys.argv[1] if len(sys.argv) > 1 else W3
STACK, RET = 0x1f0000, 0x100
pe = pefile.PE(os.path.join(DIR, 'DarklordAV.exe'))
BASE, img = pe.OPTIONAL_HEADER.ImageBase, bytes(pe.get_memory_mapped_image())
def d32(va): return struct.unpack_from('<I', img, va - BASE)[0]
def dest(va): return va + 5 + struct.unpack_from('<i', img, va + 1 - BASE)[0]   # destino de un call en va
assert img[0x4223ad - BASE] == 0xe8
IA_TURN = dest(0x4223ad)
calls = [IA_TURN + k for k in range(0x40) if img[IA_TURN + k - BASE] == 0xe8]
RF_TURN = dest(calls[2])                         # dc_close, tr_turn, rf_turn
assert img[RF_TURN - BASE:RF_TURN - BASE + 3] == b'\x60\x89\xd8', img[RF_TURN - BASE:RF_TURN - BASE + 4].hex()
BOATRAFT = dest(RF_TURN + 3)
# boatcarr: push eax; call boatraft; test eax, eax; pop eax; jz boatcarr0
k = next(k for k in range(len(img) - 16) if img[k] == 0x50 and img[k + 1] == 0xe8 and img[k + 6:k + 9] == b'\x85\xc0\x58'
         and dest(BASE + k + 1) == BOATRAFT)
BOATCARR = BASE + k
REC = lambda p: 0x53c410 + (p * 16 + 15) * 0xfc
ARM = lambda i: 0x54fe50 + i * 0x1c

mal = 0
def ver(nombre, r, esperado):
    global mal
    ok = r == esperado; mal += not ok
    print('OK ' if ok else 'MAL', nombre, '->', r)

class Juego:
    def __init__(s, bonos, ejercitos, local=0, voladores=()):
        mu = s.mu = Uc(UC_ARCH_X86, UC_MODE_32)
        size = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
        mu.mem_map(BASE, size); mu.mem_write(BASE, img[:size])
        mu.mem_map(0, 0x1000); mu.mem_map(0x100000, 0x100000)
        for q in range(8): mu.mem_write(REC(q) + 0xb2, bytes(36))
        for q, txts in bonos.items():
            for r, t in enumerate(txts): mu.mem_write(REC(q) + 0xb2 + r * 9, t.ljust(9, b'\0'))
        mu.mem_write(0x560b20, struct.pack('<h', local))
        mu.mem_write(0x54fe50, struct.pack('<h', len(ejercitos) + 1))
        for i, (p, x, y, vivo, emb, byte) in enumerate(ejercitos, 1):
            mu.mem_write(ARM(i) + 2, struct.pack('<hh', x, y))
            mu.mem_write(ARM(i) + 0xe, struct.pack('<H', p << 5))
            mu.mem_write(ARM(i) + 0x13, bytes([0x40 if vivo else 0, 8 if emb else 0]))
            mu.mem_write(ARM(i) + 0x1b, bytes([byte]))
        s.hundidos, s.sonidos, s.voladores = [], [], set(voladores)
        # como el 0x43c240 real: "no" a todo embarcado (bit 8 de +0x14, 0x43c2aa) y a los voladores. Hasta 1.0.275.0 la
        # prueba decía "sí" al embarcado y no vio que rf_turn nunca sumaba (TAREA 269).
        s.hook(0x43c240, lambda a: 0 if (s.mu.mem_read(ARM(a[1] & 0xffff) + 0x14, 1)[0] & 8) or a[1] in s.voladores
               else 1)
        s.hook(0x485610, s.hundir)
        s.hook(0x4465e0, lambda a: s.sonidos.append((a[0], struct.unpack('<i', struct.pack('<I', a[1]))[0])))
    def hook(s, addr, fn):
        def g(mu, a, size, _):
            sp = mu.reg_read(UC_X86_REG_ESP); ret, *args = struct.unpack('<7I', mu.mem_read(sp, 28))
            mu.reg_write(UC_X86_REG_EAX, (fn(args) or 0) & 0xffffffff)
            mu.reg_write(UC_X86_REG_ESP, sp + 4); mu.reg_write(UC_X86_REG_EIP, ret)
        s.mu.hook_add(UC_HOOK_CODE, g, begin=addr, end=addr)
    def hundir(s, a):   # ahoga a todos los de la casilla, como el original
        s.hundidos.append(tuple(a[:6]))
        xy = s.mu.mem_read(ARM(a[1]) + 2, 4); n = struct.unpack('<h', s.mu.mem_read(0x54fe50, 2))[0]
        for i in range(1, n):
            if s.mu.mem_read(ARM(i) + 2, 4) == xy: s.mu.mem_write(ARM(i) + 0x13, b'\0')
    def turno(s, p):
        mu = s.mu; mu.mem_write(STACK, struct.pack('<I', RET)); mu.reg_write(UC_X86_REG_ESP, STACK)
        mu.reg_write(UC_X86_REG_EBX, p); mu.emu_start(RF_TURN, RET, count=2000000)
        assert mu.reg_read(UC_X86_REG_EBX) == p
    def byte(s, i): return s.mu.mem_read(ARM(i) + 0x1b, 1)[0]
    def emb(s, i, e): s.mu.mem_write(ARM(i) + 0x14, bytes([8 if e else 0]))
    def vivo(s, i): return bool(s.mu.mem_read(ARM(i) + 0x13, 1)[0] & 0x40)
    def carr(s, p):
        mu = s.mu; mu.mem_write(STACK, struct.pack('<I', RET)); mu.reg_write(UC_X86_REG_ESP, STACK)
        mu.reg_write(UC_X86_REG_EAX, p); mu.emu_start(BOATCARR, RET, count=200000)
        return mu.reg_read(UC_X86_REG_EAX) != 0

RAFT, CARR = b'Raft', b'Carrier'
# 1 balsa de 0 en el agua; 2 otro ejército de 0 en la misma balsa; 3 de 0 en tierra; 4 de 0 volador sobre el agua;
# 5 de 0 con enlace de convoy; 6 de 0 muerto en el agua; 7 de 1 en el agua (sin "Raft"); 8 de 2 en el agua (con "Carrier")
EJ = [(0, 5, 5, 1, 1, 0), (0, 5, 5, 1, 1, 0), (0, 9, 9, 1, 0, 0), (0, 12, 3, 1, 1, 0), (0, 14, 3, 1, 1, 0x85),
      (0, 16, 3, 0, 1, 0), (1, 20, 20, 1, 1, 0), (2, 22, 22, 1, 1, 0)]
g = Juego({0: [RAFT], 2: [CARR]}, EJ, local=0, voladores={4})
g.turno(0)
ver('vuelta 2: la balsa sigue a flote y cuenta 1', (g.vivo(1), g.byte(1), g.byte(2), g.hundidos, g.sonidos), (True, 0x41, 0x41, [], []))
ver('vuelta 2: controles intactos', [g.byte(i) for i in (3, 4, 5, 6)], [0, 0, 0x85, 0])
for p in (1, 2): g.turno(p)
ver('otros bandos sin "Raft": nada', ([g.byte(i) for i in (7, 8)], g.hundidos), ([0, 0], []))
g.turno(0)
ver('vuelta 3: se hunde con todo lo embarcado y suena splash', (g.vivo(1), g.vivo(2), g.hundidos, g.sonidos),
    (False, False, [(0, 1, 1, 0, 1, 0)], [(0x18, -1)]))
ver('vuelta 3: sobreviven tierra, volador y convoy', [g.vivo(i) for i in (3, 4, 5)], [True, True, True])
for _ in range(3):
    for p in (1, 2): g.turno(p)
ver('bandos sin "Raft": nunca se hunden', (g.vivo(7), g.vivo(8), [h for h in g.hundidos if h[0]]), (True, True, []))

g = Juego({0: [RAFT]}, EJ[:1], local=3)
g.turno(0); g.turno(0)
ver('hundida en otra PC: sin sonido', (g.vivo(1), len(g.hundidos), g.sonidos), (False, 1, []))

g = Juego({0: [RAFT]}, EJ[:1])
g.turno(0); g.emb(1, False); g.turno(0)
ver('volvió a tierra: la cuenta vuelve a 0', (g.vivo(1), g.byte(1)), (True, 0))
g.emb(1, True); g.turno(0)
ver('zarpa de nuevo: cuenta 1, a flote', (g.vivo(1), g.byte(1)), (True, 0x41))
g.turno(0)
ver('y al empezar la tercera se hunde', g.vivo(1), False)

g = Juego({0: [CARR], 1: [RAFT, CARR], 2: [b'carrier', b'raft']}, [])
ver('boatcarr: "Carrier" solo, sí; con "Raft", no', [g.carr(p) for p in (0, 1, 2, 3)], [True, False, False, False])
print('TODO OK' if not mal else f'{mal} MAL'); sys.exit(1 if mal else 0)
