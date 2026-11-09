# Prueba de juguete de torres y faros (ob_* de build.py, etapa A de PENDIENTE-construcciones.md), en unicorn.
# Uso: python prueba_obras.py [carpeta]   (por defecto C:\Warlords3; la que se le pasó a build.py)
# Reusa el banco de prueba_caminos.py (mapa: x >= 30 agua; columna x = 10 camino). Prueba bd_pick (posiciones 6 y 7),
# el precio (br_cost con 0x4000), bd_recv (cobra y anota el registro) y sus controles.
import os, sys
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prueba_caminos.py'), encoding='utf-8').read()
exec(_src[:_src.index("print('-- menú")])
_a = _src.index('PKT = 0x150000'); exec(_src[_a:_src.index('g, c = recibir()', _a)])   # recibir()

_OB = b'OBRA' + bytes(4 + 64 * 8)
assert img.count(_OB) == 1, 'falta la tabla de obras (ob_save)'
OB_N = BASE + img.index(_OB) + 4
OB_TAB = OB_N + 4
TORRE, FARO = 0x4004, 0x4005

print('-- bd_pick con constructor')
def picks(x, y, n, prep=None):
    g = Juego(); mu = g.mu
    if prep: prep(g)
    mu.mem_write(BD_HASB, b'\1'); mu.mem_write(TR_X, struct.pack('<hh', x, y))
    r = []
    for _ in range(n):
        g.correr(BD_PICK, RET, struct.pack('<I', RET))
        ok = mu.reg_read(UC_X86_REG_EAX)
        r.append((*struct.unpack('<hh', mu.mem_read(BD_X, 4)), struct.unpack('<H', mu.mem_read(BD_PW, 2))[0]) if ok else (0,))
    return r
ver('llanura lejos del agua: camino, torre, camino', picks(5, 7, 3), [(5, 7, 0), (5, 7, TORRE), (5, 7, 0)])
ver('a orillas del agua (x = 29): camino, torre, faro, camino', picks(29, 7, 4), [(29, 7, 0), (29, 7, TORRE), (29, 7, FARO), (29, 7, 0)])
ver('control: tabla llena: solo camino', picks(5, 7, 2, lambda g: g.mu.mem_write(OB_N, struct.pack('<I', 64))), [(5, 7, 0)] * 2)

print('-- precio')
def precio(pw):
    g = Juego(); mu = g.mu
    mu.mem_write(BD_X, struct.pack('<hh', 5, 7)); mu.mem_write(BD_PW, struct.pack('<H', pw))
    g.correr(0x4b65e0, RET, struct.pack('<III', RET, BD_MARK, 0))
    return mu.reg_read(UC_X86_REG_EAX) & 0xffff
ver('torre: 50 % de 200 = 100', precio(TORRE), 100)
ver('faro: 100', precio(FARO), 100)

print('-- red: bd_recv')
def obra(x=5, y=7, pw=TORRE, oro=100, p=2, prep=None):
    def pr(g):
        g.interceptar(0x441540, lambda a: g.llamadas.append('niebla'))
        if prep: prep(g)
    g, c = recibir(p=p, x=x, y=y, pw=pw, oro=oro, prep=pr)
    n = struct.unpack('<I', g.mu.mem_read(OB_N, 4))[0]
    return c, n, bytes(g.mu.mem_read(OB_TAB, 8 * max(n, 1)))
ver('torre en (5, 7) del bando 2: cobra 100 y anota x, y, tipo 4, dueño 2', obra(),
    ([(2, -100)], 1, struct.pack('<hhBBBB', 5, 7, 4, 0, 2, 0)))
ver('faro en la orilla (29, 7), bando 5', obra(x=29, pw=FARO, p=5)[1:], (1, struct.pack('<hhBBBB', 29, 7, 5, 0, 5, 0)))
ver('control: oro 99', obra(oro=99)[:2], ([], 0))
ver('control: faro lejos del agua', obra(pw=FARO)[:2], ([], 0))
ver('control: tipo 6 inexistente', obra(pw=0x4006)[:2], ([], 0))
ver('control: agua', obra(x=33)[:2], ([], 0))
ver('control: sobre camino', obra(x=10)[:2], ([], 0))
ver('control: tabla llena', obra(prep=lambda g: g.mu.mem_write(OB_N, struct.pack('<I', 64)))[:2], ([], 64))

print('-- tope de 3 pausas manuales por jugador (pp_recv)')
PP_RECV = dest(0x4b6a22, 2)
_k = img.index(b'\x80\x0d', PP_RECV - BASE); PZ_ON = d32(BASE + _k + 2)
PP_CNT = OB_TAB + 64 * 8
def pausas(cargas, prep=None):
    g = Juego(); mu = g.mu
    if prep: prep(g)
    r = []
    for c in cargas:
        mu.mem_write(PZ_ON, b'\0'); mu.mem_write(PKT + 0xc, struct.pack('<I', c))
        g.correr(PP_RECV, 0x4b85bb, struct.pack('<I', RET), [(UC_X86_REG_EAX, 0x2a5 + 8), (UC_X86_REG_ESI, PKT)])
        r.append(mu.mem_read(PZ_ON, 1)[0] & 2)
    return r, bytes(mu.mem_read(PP_CNT, 8))
ver('jugador 2 pausa 4 veces: las 3 primeras pausan, la cuarta no', pausas([0x201] * 4), ([2, 2, 2, 0], bytes([0, 0, 3, 0, 0, 0, 0, 0])))
ver('  cada jugador tiene las suyas', pausas([0x201] * 3 + [0x501, 0x201]), ([2, 2, 2, 2, 0], bytes([0, 0, 3, 0, 0, 1, 0, 0])))
ver('control: reanudar (0) siempre vale y no cuenta', pausas([0, 0, 0, 0], lambda g: g.mu.mem_write(PP_CNT + 2, b'\3'))[1][2], 3)

print('MAL:', mal)
sys.exit(1 if mal else 0)
