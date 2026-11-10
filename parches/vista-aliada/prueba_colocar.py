# Prueba de juguete de colocar obras con vista previa (pv_* de build.py, pedido del 9/11/2026 en
# PENDIENTE-construcciones.md), en unicorn.
# Uso: python prueba_colocar.py [carpeta]   (por defecto C:\Warlords3; la que se le pasó a build.py)
# Reusa el banco de prueba_caminos.py (mapa: x >= 30 agua; columna x = 10 camino). Prueba pv_eval (alcance, tipos,
# precio, fantasma y redibujo), ob_at (el fantasma solo mientras se dibuja), pv_dec (cursor al pasar, paquete al hacer
# clic) y bm_norm (el clic derecho termina el modo), con sus controles.
import os, sys
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prueba_caminos.py'), encoding='utf-8').read()
exec(_src[:_src.index("print('-- menú")])

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
_cs = Cs(CS_ARCH_X86, CS_MODE_32)
def calls(va, n):      # destinos de los primeros n «call rel32» de la rutina en va
    r = []
    for i in _cs.disasm(img[va - BASE:va - BASE + 0x400], va):
        if i.mnemonic == 'call' and i.bytes[0] == 0xe8: r.append(int(i.op_str, 16))
        if len(r) == n: return r
    raise AssertionError(hex(va))
PV_DEC = dest(0x4737a8)
assert img[PV_DEC - BASE:PV_DEC - BASE + 2] == b'\x80\x3d'
PV_ON = d32(PV_DEC + 2)
PV_CAT, PV_SIDE, PV_IN, PV_OK, PV_PW = PV_ON + 1, PV_ON + 2, PV_ON + 4, PV_ON + 5, PV_ON + 6
PV_REC, PV_RX, PV_RN = PV_ON + 8, PV_ON + 16, PV_ON + 20
PV_EVAL = calls(PV_DEC, 1)[0]
PV_CHK, REDRAW = calls(PV_EVAL, 2)
OB_OKT = calls(PV_CHK, 1)[0]
OB_AT = calls(OB_OKT, 1)[0]
_k = img.index(b'\xff\x15', PV_EVAL - BASE)
TR_CHKP = d32(BASE + _k + 2)
BM_NORM = dest(0x4bf02d)
P, LIDER = 2, 5

def juego(lx, ly, cat, oro=1000, hasb=1, prep=None):
    g = Juego(); mu = g.mu
    mu.mem_write(0x200, b'\xc3'); mu.mem_write(TR_CHKP, struct.pack('<I', 0x200))   # tr_check: ya probado aparte
    mu.mem_write(BD_HASB, bytes([hasb]))
    mu.mem_write(0x537ce8, struct.pack('<h', P))
    mu.mem_write(P * 0x4f0 + 0x56ea90, struct.pack('<h', LIDER))
    mu.mem_write(0x54fe50 + LIDER * 0x1c + 2, struct.pack('<hh', lx, ly))
    mu.mem_write(0x536c14 + P * 0x1f8, struct.pack('<i', oro))
    mu.mem_write(PV_ON, bytes([1, cat])); mu.mem_write(PV_SIDE, struct.pack('<h', P))
    g.redib = 0
    def rd(a): g.redib += 1
    g.interceptar(REDRAW, rd)
    if prep: prep(g)
    return g
def evaluar(g, x, y):
    g.correr(PV_EVAL, RET, struct.pack('<I', RET), [(UC_X86_REG_EAX, x), (UC_X86_REG_EDX, y)])
    mu = g.mu
    ok = mu.mem_read(PV_OK, 1)[0]
    r = (ok, *struct.unpack('<hh', mu.mem_read(BD_X, 4)), struct.unpack('<H', mu.mem_read(PV_PW, 2))[0]) if ok else (0,)
    return r
def fantasma(g):
    mu = g.mu
    rec = bytes(mu.mem_read(PV_REC, 8)); rx, ry = struct.unpack('<hh', mu.mem_read(PV_RX, 4))
    rn, rd, rp = mu.mem_read(PV_RN, 3)
    return (struct.unpack('<hh', rec[:4]) + tuple(rec[4:7])) if rec[:4] != b'\xff\x7f\xff\x7f' else None, \
           (rx, ry, rn, rd, rp) if rn else None

print('-- pv_eval: camino')
g = juego(5, 7, 1)
ver('camino en la vecina diagonal (6, 8): sirve, paquete 0', evaluar(g, 6, 8), (1, 6, 8, 0))
ver('  fantasma de camino de 1 casilla, pieza E-O suelta (1); redibuja una vez', (fantasma(g), g.redib), ((None, (6, 8, 1, 0, 1)), 1))
evaluar(g, 6, 8)
ver('  el mismo lugar otra vez: no redibuja', g.redib, 1)
ver('en la casilla del líder (5, 7): sirve', evaluar(g, 5, 7), (1, 5, 7, 0))
ver('control: a 2 casillas (7, 7): no sirve, borra el fantasma y redibuja', (evaluar(g, 7, 7), fantasma(g), g.redib), ((0,), (None, None), 3))
ver('control: sobre el camino de x = 10', evaluar(juego(9, 7, 1), 10, 7), (0,))
ver('control: agua (30, 7)', evaluar(juego(29, 7, 1), 30, 7), (0,))
ver('control: sin constructor', evaluar(juego(5, 7, 1, hasb=0), 6, 7), (0,))
ver('control: oro 9 (cuesta 10)', evaluar(juego(5, 7, 1, oro=9), 6, 7), (0,))
ver('con oro 10: sirve', evaluar(juego(5, 7, 1, oro=10), 6, 7), (1, 6, 7, 0))

print('-- pv_eval: puente')
def isla(g):        # agua en x = 30..32 de la fila 7, tierra desde x = 33
    for x in range(33, 40): g.mu.mem_write(casilla(x, 7), struct.pack('<H', 0))
g = juego(29, 7, 2, prep=isla)
ver('puente hacia el este desde (29, 7): primera casilla (30, 7), paquete 0x101', evaluar(g, 30, 7), (1, 30, 7, 0x101))
ver('  fantasma: 3 casillas desde (30, 7) hacia el este, pieza recta E-O (1)', fantasma(g), (None, (30, 7, 3, 1, 1)))
ver('control: en diagonal (30, 8)', evaluar(g, 30, 8), (0,))
ver('control: la casilla del líder', evaluar(g, 29, 7), (0,))
ver('control: sin tierra enfrente (fila 8)', evaluar(juego(29, 8, 2, prep=isla), 30, 8), (0,))

print('-- pv_eval: obras')
g = juego(5, 7, 4)
ver('torre en la vecina (5, 6): paquete 0x4004', evaluar(g, 5, 6), (1, 5, 6, 0x4004))
ver('  fantasma de obra: (5, 6), tipo 4, dirección 0, dueño 2', fantasma(g), ((5, 6, 4, 0, P), None))
def ob_at(g, x, y, dibujando):
    g.mu.mem_write(PV_IN, bytes([dibujando]))
    g.correr(OB_AT, RET, struct.pack('<I', RET), [(UC_X86_REG_EAX, x), (UC_X86_REG_EDX, y)])
    return g.mu.reg_read(UC_X86_REG_EAX)
ver('  ob_at(5, 6) al dibujar da el fantasma; fuera del dibujo, nada; otra casilla, nada',
    (ob_at(g, 5, 6, 1) == PV_REC, ob_at(g, 5, 6, 0), ob_at(g, 5, 7, 1)), (True, 0, 0))
ver('faro a orillas del agua (29, 6)', evaluar(juego(29, 7, 5), 29, 6), (1, 29, 6, 0x4005))
ver('control: faro lejos del agua', evaluar(juego(5, 7, 5), 5, 6), (0,))
ver('muro de piedra (4, 8), sin dirección: se une solo con sus vecinos', evaluar(juego(5, 7, 6), 4, 8), (1, 4, 8, 0x4007))
ver('muro sobre el camino (10, 7): puerta', evaluar(juego(9, 7, 6), 10, 7), (1, 10, 7, 0x4007))
ver('control: torre sobre el camino', evaluar(juego(9, 7, 4), 10, 7), (0,))
ver('control: torre con oro 99 (cuesta 100)', evaluar(juego(5, 7, 4, oro=99), 5, 6), (0,))
ver('control: categoría 3 (puerto) no es de este modo', evaluar(juego(5, 7, 3), 5, 6), (0,))
g = juego(5, 7, 4)
g.mu.mem_write(0x537ce8, struct.pack('<h', 3))
ver('control: cambió el bando: termina el modo', (evaluar(g, 5, 6), g.mu.mem_read(PV_ON, 1)[0]), ((0,), 0))
g = juego(5, 7, 4)
g.mu.mem_write(P * 0x4f0 + 0x56ea90, struct.pack('<h', 0))
ver('control: sin grupo elegido: termina el modo', (evaluar(g, 5, 6), g.mu.mem_read(PV_ON, 1)[0]), ((0,), 0))

print('-- pv_dec: cursor y clic')
OUT = 0x150000
def dec(g, x, y, pasa, stop=RET):
    pila = bytearray(0x50)
    struct.pack_into('<hh', pila, 0x2c, x, y)
    struct.pack_into('<I', pila, 0x34, RET)
    struct.pack_into('<II', pila, 0x44, OUT, pasa)
    g.mu.mem_write(OUT, bytes(4))
    g.envios = []
    g.interceptar(0x4dd3b0, lambda a: g.envios.append((a[0], bytes(g.mu.mem_read(a[1], a[2])))))
    g.correr(PV_DEC, stop, bytes(pila))
    return g.mu.reg_read(UC_X86_REG_EAX) & 0xffff, struct.unpack('<hh', g.mu.mem_read(OUT, 4)), g.envios
ver('pasar por una casilla que sirve: cursor 7 (mover), con la casilla', dec(juego(5, 7, 4), 5, 6, 1), (7, (5, 6), []))
ver('pasar por una que no sirve: cursor 3 (flecha)', dec(juego(5, 7, 4), 8, 6, 1), (3, (8, 6), []))
ver('clic donde sirve: manda BD_PKT (bando 2, 5, 6, 0x4004) y devuelve 0', dec(juego(5, 7, 4), 5, 6, 0),
    (0, (0, 0), [(BD_PKT, struct.pack('<4h', P, 5, 6, 0x4004))]))
ver('control: clic donde no sirve: nada', dec(juego(5, 7, 4), 8, 6, 0), (0, (0, 0), []))
g = juego(5, 7, 4); g.mu.mem_write(PV_ON, b'\0')
ver('control: fuera del modo: sigue el código del juego (0x4737af)', dec(g, 5, 6, 0, stop=0x4737af)[2], [])
g = juego(5, 7, 4); g.mu.mem_write(0x537ce8, struct.pack('<h', 3))
ver('control: cambió el bando: sigue el código del juego', dec(g, 5, 6, 1, stop=0x4737af)[2], [])

print('-- clic derecho (bm_norm)')
g = juego(5, 7, 4); evaluar(g, 5, 6); n = g.redib
g.correr(BM_NORM, RET, struct.pack('<I', RET))
ver('en modo: lo termina, borra el fantasma y redibuja, sin abrir el menú', (g.mu.mem_read(PV_ON, 1)[0], fantasma(g), g.redib - n), (0, (None, None), 1))
g = juego(5, 7, 4); g.mu.mem_write(PV_ON, b'\0')
g.interceptar(0x4afc20, lambda a: g.llamadas.append('menú'))
g.correr(BM_NORM, RET, struct.pack('<I', RET))
ver('control: fuera del modo abre el menú de órdenes', g.llamadas, ['menú'])

print('MAL:', mal)
sys.exit(1 if mal else 0)
