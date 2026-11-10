import re
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
MURO = 0x4007
MUROS = [MURO | (d + 1) << 8 for d in range(8)]      # muro en 8 direcciones (N..NO), dirección + 1 en el byte alto
ver('llanura lejos del agua: camino, torre, muro x 8 direcciones, camino', picks(5, 7, 11),
    [(5, 7, 0), (5, 7, TORRE)] + [(5, 7, m) for m in MUROS] + [(5, 7, 0)])
ver('a orillas del agua (x = 29): camino, torre, faro, muro x 8, camino', picks(29, 7, 12),
    [(29, 7, 0), (29, 7, TORRE), (29, 7, FARO)] + [(29, 7, m) for m in MUROS] + [(29, 7, 0)])
ver('control: tabla llena: solo camino', picks(5, 7, 2, lambda g: g.mu.mem_write(OB_N, struct.pack('<I', 64))), [(5, 7, 0)] * 2)

print('-- botonera de la torre: bd_pick filtrado por tipo (BD_CAT)')
BD_CAT = BD_X + 13
def cat(c):
    return lambda g: g.mu.mem_write(BD_CAT, bytes([c]))
ver('camino: solo camino', picks(29, 7, 3, cat(1)), [(29, 7, 0)] * 3)
ver('torre: solo torre', picks(29, 7, 2, cat(4)), [(29, 7, TORRE)] * 2)
ver('faro a orillas del agua: solo faro', picks(29, 7, 2, cat(5)), [(29, 7, FARO)] * 2)
ver('muro: las 8 direcciones y vuelve a la primera', picks(29, 7, 9, cat(6)), [(29, 7, m) for m in MUROS + MUROS[:1]])
ver('control: faro lejos del agua: nada', picks(5, 7, 2, cat(5)), [(0,)] * 2)
ver('control: puerto sin ciudad: nada', picks(5, 7, 1, cat(3)), [(0,)])
ver('control: sin filtro (0): rotación completa', picks(5, 7, 3, cat(0)), [(5, 7, 0), (5, 7, TORRE), (5, 7, MUROS[0])])
# bm_calc: tr_init (0x4affc2) empieza con «cmp byte [BM_ON], 0; jne bm_init» y bm_init con «call bm_calc».
TR_INIT = dest(0x4affc2)
assert img[TR_INIT - BASE:TR_INIT - BASE + 2] == b'\x80\x3d'
BM_ON = d32(TR_INIT + 2); BM_EN = BM_ON + 1
BM_INIT = dest(TR_INIT + 7, 2)
BM_CALC = dest(BM_INIT)
def renglones(x, y, flag=1, trap=0):
    g = Juego(); mu = g.mu
    mu.mem_write(0x537ce8, struct.pack('<h', 2)); mu.mem_write(0x536c14 + 2 * 0x1f8, struct.pack('<i', 1000))
    mu.mem_write(BD_HASB, bytes([flag])); mu.mem_write(TR_X, struct.pack('<hh', x, y))
    mu.mem_write(BD_FLAG, bytes([flag])); mu.mem_write(TR_FLAG, bytes([trap]))
    mu.mem_write(BD_X, bytes(range(1, 13)))          # rotación guardada: tiene que quedar igual
    g.correr(BM_CALC, RET, struct.pack('<I', RET))
    return list(mu.mem_read(BM_EN, 13)), bytes(mu.mem_read(BD_X, 12)) == bytes(range(1, 13))
#              reconstruir camino puente puerto torre faro muro trampa, 5 vacíos
ver('orilla (29, 7): camino, torre, faro, muro; la rotación queda como estaba', renglones(29, 7),
    ([0, 1, 0, 0, 1, 1, 1, 0] + [0] * 5, True))
ver('con trampa posible: la trampa ya no está en este menú (volvió al de órdenes)', renglones(5, 7, trap=1),
    ([0, 1, 0, 0, 1, 0, 1, 0] + [0] * 5, True))
ver('control: BD_FLAG = BD_HASB = 0 (no es su turno): nada', renglones(29, 7, flag=0),
    ([0] * 13, True))

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

print('-- muro de piedra')
def muro_y_camino(oro=1000, x=5):
    g, c = recibir(pw=MURO, oro=oro, x=x)
    mu = g.mu; c1 = list(c)
    mu.mem_write(PKT + 0xc, struct.pack('<4h', 2, x, 7, 0))
    g.correr(BD_RECV, 0x4b85bb, struct.pack('<I', RET), [(UC_X86_REG_EAX, BD_PKT + 8), (UC_X86_REG_ESI, PKT)])
    n = struct.unpack('<I', mu.mem_read(OB_N, 4))[0]
    return c1, n, c[len(c1):], g.tile(x, 7)[3] & 7
ver('muro en (5, 7): cobra 100; después una puerta (camino encima) cobra 50 (25 % de ciudad) y pone la estructura 1',
    muro_y_camino(), ([(2, -100)], 1, [(2, -50)], 1))
def torre_sobre_muro():
    g, c = recibir(pw=MURO, oro=1000)
    mu = g.mu; n0 = len(c)
    mu.mem_write(PKT + 0xc, struct.pack('<4h', 2, 5, 7, TORRE))
    g.correr(BD_RECV, 0x4b85bb, struct.pack('<I', RET), [(UC_X86_REG_EAX, BD_PKT + 8), (UC_X86_REG_ESI, PKT)])
    return c[n0:], struct.unpack('<I', mu.mem_read(OB_N, 4))[0]
ver('control: torre sobre el muro no (ni cobra ni anota)', torre_sobre_muro(), ([], 1))
ver('muro sobre un camino (x = 10): se puede, cobra 100, y el camino queda (puerta)',
    (obra(x=10, pw=MURO, oro=1000)[:2], recibir(pw=MURO, oro=1000, x=10)[0].tile(10, 7)[3] & 7), (([(2, -100)], 1), 1))
ver('control: torre sobre camino sigue sin poder', obra(x=10, oro=1000)[:2], ([], 0))
def muro_dir(pw):
    g, c = recibir(pw=pw, oro=1000)
    return c, bytes(g.mu.mem_read(OB_TAB, 8))[4:6]
ver('muro hacia el este (dirección 2): cobra 100 y guarda tipo 7, dirección + 1 = 3', muro_dir(MUROS[2]), ([(2, -100)], bytes([7, 3])))
ver('control: muro sin dirección (viejo) guarda 0', muro_dir(MURO), ([(2, -100)], bytes([7, 0])))

print('-- muro: solo pasan el dueño y sus aliados, con puerta o sin ella (po_pf)')
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ
PO_PF = dest(0x4a5d34, 1)
_calls = []
_k = PO_PF - BASE
while len(_calls) < 4:
    if img[_k] == 0xe8: _calls.append(BASE + _k + 5 + struct.unpack('<i', img[_k + 1:_k + 5])[0]); _k += 5
    else: _k += 1
FOGALLY = _calls[3]
def puerta(quien, aliado=False, camino=True, destino=None, guerra=False):
    g, c = recibir(pw=MURO, oro=1000)
    mu = g.mu
    if camino:
        mu.mem_write(PKT + 0xc, struct.pack('<4h', 2, 5, 7, 0))
        g.correr(BD_RECV, 0x4b85bb, struct.pack('<I', RET), [(UC_X86_REG_EAX, BD_PKT + 8), (UC_X86_REG_ESI, PKT)])
    r = []
    def fa(mu, a, size, _):
        fl = mu.reg_read(UC_X86_REG_EFLAGS)
        mu.reg_write(UC_X86_REG_EFLAGS, (fl | 0x40) if aliado else (fl & ~0x40))
        sp = mu.reg_read(UC_X86_REG_ESP)
        mu.reg_write(UC_X86_REG_EIP, struct.unpack('<I', mu.mem_read(sp, 4))[0]); mu.reg_write(UC_X86_REG_ESP, sp + 4)
    def fin(nombre):
        def h(mu, a, size, _): r.append(nombre); mu.emu_stop()
        return h
    mu.hook_add(UC_HOOK_CODE, fa, begin=FOGALLY, end=FOGALLY)
    mu.hook_add(UC_HOOK_CODE, fin('cerrado'), begin=0x4a5e31, end=0x4a5e31)
    mu.hook_add(UC_HOOK_MEM_READ, lambda mu, ac, a, sz, v, _: (r.append('pasa'), mu.emu_stop()), begin=0x503e00, end=0x503e01)
    mu.mem_write(0x58715c, struct.pack('<h', quien))
    if destino: mu.mem_write(0x5878d4, struct.pack('<h', destino[0])); mu.mem_write(0x5878d8, struct.pack('<h', destino[1]))
    if guerra: mu.mem_write(0x55ee4c + quien * 56 + 2, bytes([2]))
    mu.mem_write(STACK, struct.pack('<I', RET)); mu.reg_write(UC_X86_REG_ESP, STACK)
    mu.reg_write(UC_X86_REG_EDI, 5); mu.reg_write(UC_X86_REG_EBX, 7)
    mu.emu_start(0x4a5d34, 0, count=5000)
    return r[:1]
ver('el dueño (2) pasa por su puerta', puerta(2), ['pasa'])
ver('un aliado (5) pasa', puerta(5, aliado=True), ['pasa'])
ver('un enemigo (5) no', puerta(5), ['cerrado'])
ver('neutral (8) no', puerta(8), ['cerrado'])
ver('muro sin puerta: el dueño entra (se aloja)', puerta(2, camino=False), ['pasa'])
ver('muro sin puerta: un aliado entra', puerta(5, aliado=True, camino=False), ['pasa'])
ver('control: muro sin puerta, un enemigo no', puerta(5, camino=False), ['cerrado'])
ver('ataque al muro: enemigo en guerra (5), el muro es el destino: llega', puerta(5, camino=False, destino=(5, 7), guerra=True), ['pasa'])
ver('ídem con puerta', puerta(5, destino=(5, 7), guerra=True), ['pasa'])
ver('control: en guerra pero el muro no es el destino', puerta(5, camino=False, destino=(6, 7), guerra=True), ['cerrado'])
ver('control: destino pero sin guerra', puerta(5, camino=False, destino=(5, 7)), ['cerrado'])
ver('el dueño, destino su muro sin puerta: entra', puerta(2, camino=False, destino=(5, 7), guerra=True), ['pasa'])

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

print('-- derribar muros propios con «Raze» (wl_razelk, wl_apply)')
import capstone
_cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def llamadas(va, n=400):
    return [int(i.op_str, 16) for i in _cs.disasm(img[va - BASE:va - BASE + n], va) if i.mnemonic == 'call' and i.op_str.startswith('0x')]
WL_RAZELK = dest(0x44c2d7)
def _calls(va, n):
    r, k = [], va - BASE
    while len(r) < n:
        if img[k] == 0xe8: r.append(BASE + k + 5 + struct.unpack_from('<i', img, k + 1)[0]); k += 5
        else: k += 1
    return r
BR_RAZELK = _calls(WL_RAZELK, 3)[2]     # 0x440b30, wl_find, br_razelk
assert BR_RAZELK != WL_RAZELK
print('-- botones de las barras (0x4205c1, 0x41c98c): también wl_razelk')
ver('las dos barras, el menú y la tecla llaman a wl_razelk', {dest(v) for v in (0x4205c1, 0x41c98c, 0x4b05d1)}, {WL_RAZELK})
BR_RAZEAPPLY = dest(0x4d5e30)
_j = list(_cs.disasm(img[BR_RAZEAPPLY - BASE:BR_RAZEAPPLY - BASE + 16], BR_RAZEAPPLY))[1]
assert _j.mnemonic == 'jge'
WL_APPLY = int(_j.op_str, 16)
_wa0 = llamadas(WL_APPLY, 160)
BD_PRICE = _wa0[0]
assert _wa0[1] == 0x43fd60, [hex(v) for v in _wa0]
_wa = _wa0[2:7]   # ob_del, REDRAW, 0x4a4f20, br_mapview, ob_fogme
assert _wa[2] == 0x4a4f20, [hex(v) for v in _wa]
PAGOS = []
def stub(mu, va, eax=None):
    def h(mu, a, size, _):
        if eax is not None: mu.reg_write(UC_X86_REG_EAX, eax)
        sp = mu.reg_read(UC_X86_REG_ESP)
        mu.reg_write(UC_X86_REG_EIP, struct.unpack('<I', mu.mem_read(sp, 4))[0]); mu.reg_write(UC_X86_REG_ESP, sp + 4)
    mu.hook_add(UC_HOOK_CODE, h, begin=va, end=va)
def muros(recs, yo=2):
    g = Juego(); mu = g.mu
    mu.mem_write(OB_N, struct.pack('<I', len(recs)))
    mu.mem_write(OB_TAB, b''.join(struct.pack('<hhBBBB', x, y, t, 0, d, 0) for x, y, t, d in recs))
    mu.mem_write(0x537ce8, struct.pack('<h', yo))
    stub(mu, 0x440b30, 0xffffffff); stub(mu, BR_RAZELK, 0xffffffff)
    for va in _wa[1:]: stub(mu, va)
    stub(mu, BD_PRICE, 101)   # precio de la obra para cualquier bando
    def pago(mu, a, size, _):
        sp = mu.reg_read(UC_X86_REG_ESP)
        PAGOS.append(struct.unpack('<ii', bytes(mu.mem_read(sp + 4, 8))))
    mu.hook_add(UC_HOOK_CODE, pago, begin=0x43fd60, end=0x43fd60)
    stub(mu, 0x43fd60)
    return g
def razes(g, x, y, n):
    r = []
    for _ in range(n):
        g.correr(WL_RAZELK, RET, struct.pack('<Iii', RET, x, y))
        v = struct.unpack('<h', struct.pack('<H', g.mu.reg_read(UC_X86_REG_EAX) & 0xffff))[0]
        r.append(v - 0x7000 if v >= 0x7000 else -1)
    return r
def tabla(g):
    n = struct.unpack('<I', g.mu.mem_read(OB_N, 4))[0]
    return [struct.unpack('<hhBBBB', bytes(g.mu.mem_read(OB_TAB + 8 * i, 8)))[:3] for i in range(n)]
REC = [(5, 7, 7, 2), (6, 8, 7, 2), (20, 20, 7, 2), (4, 6, 6, 3), (5, 6, 4, 2), (30, 30, 5, 2)]   # torre (4) en (5, 6); faro lejos
ver('líder en (5, 7): rota entre las obras propias al alcance (muros 0, 1, torre 4) y vuelve a empezar', razes(muros(REC), 5, 7, 4), [0, 1, 4, 0])
ver('faro propio: dentro', razes(muros(REC), 30, 30, 2), [5, 5])
ver('faro propio: al lado', razes(muros(REC), 31, 29, 1), [5])
ver('control: lejos (12, 12): nada', razes(muros(REC), 12, 12, 2), [-1, -1])
ver('control: empalizada ajena (dueño 3) solo para el jugador 3', razes(muros(REC, yo=3), 5, 7, 2), [3, 3])
def aplicar(g, idx, quien):
    g.correr(0x4d5e30, RET, struct.pack('<III', RET, 0x7000 + idx, quien))
    return tabla(g)
ver('derribar el bloque 1 del jugador 2: se va y los de atrás corren', aplicar(muros(REC), 1, 2),
    [(5, 7, 7), (20, 20, 7), (4, 6, 6), (5, 6, 4), (30, 30, 5)])
ver('control: el jugador 3 no derriba un muro del 2', aplicar(muros(REC), 1, 3), [r[:3] for r in REC])
ver('la torre propia se derriba', aplicar(muros(REC), 4, 2), [r[:3] for r in REC[:4] + REC[5:]])
ver('el faro propio se derriba', aplicar(muros(REC), 5, 2), [r[:3] for r in REC[:5]])
ver('control: el jugador 3 no derriba la torre del 2', aplicar(muros(REC), 4, 3), [r[:3] for r in REC])
ver('control: índice fuera de la tabla', aplicar(muros(REC), 9, 2), [r[:3] for r in REC])
def pagos(idx, quien):
    PAGOS.clear(); aplicar(muros(REC), idx, quien); return list(PAGOS)
print('-- reintegro del 75 % al derribar (precio 101 -> 75)')
ver('muro de piedra propio: 75 al dueño', pagos(1, 2), [(2, 75)])
ver('empalizada propia: 75 al dueño', pagos(3, 3), [(3, 75)])
ver('control: torre propia, sin reintegro', pagos(4, 2), [])
ver('control: faro propio, sin reintegro', pagos(5, 2), [])
ver('control: muro ajeno, ni derribo ni pago', pagos(1, 3), [])

def texto(idx, lx, ly):
    g = muros(REC); mu = g.mu
    g.correr(WL_RAZELK, RET, struct.pack('<Iii', RET, lx, ly))
    g.correr(WL_TEXT_VA, RET, struct.pack('<I', RET), [(UC_X86_REG_EAX, 0x7000 + idx)])
    return bytes(mu.mem_read(g.mu.reg_read(UC_X86_REG_EAX), 40)).split(bytes(1))[0].decode()
_k = img.index(bytes.fromhex('51522d00700000'), WL_RAZELK - BASE)   # push ecx; push edx; sub eax, WL_CODE
assert _k < WL_RAZELK - BASE + 0x200
WL_TEXT_VA = BASE + _k
print('-- textos (wl_text)')
ver('torre en (5, 6) desde (5, 7)', texto(4, 5, 7), 'the watchtower to the north')
ver('faro en su casilla', texto(5, 30, 30), 'the lighthouse here')
ver('muro en (6, 8) desde (5, 7)', texto(1, 5, 7), 'the stone wall to the south-east')
print('-- puerta en todo bloque de muro (od_gate), con o sin camino')
_pat = re.compile(re.escape(bytes.fromhex('60c605')) + b'(....)' + re.escape(bytes.fromhex('00807b0407')), re.S)
_k = [m.start() for m in _pat.finditer(img)]
assert len(_k) == 1, _k
OD_GATE = BASE + _k[0]; OD_CAPA = struct.unpack_from('<I', img, _k[0] + 3)[0]
def capa(tipo, mask_vecinos=()):
    g = muros([(5, 7, tipo, 2)] + [(5 + dx, 7 + dy, 7, 2) for dx, dy in mask_vecinos]); mu = g.mu
    mu.mem_write(0x54fe50, struct.pack('<h', 0))
    g.correr(OD_GATE, RET, struct.pack('<I', RET), [(UC_X86_REG_EBX, OB_TAB), (UC_X86_REG_EAX, 5), (UC_X86_REG_EDX, 7)])
    return mu.mem_read(OD_CAPA, 1)[0]
ver('muro sin camino ni ejércitos: portón cerrado (20)', capa(7), 20)
ver('control: torre de vigía: sin puerta (0)', capa(4), 0)
print('-- reparar el muro (bd_recv con 0x4000 | OB_REP)')
REP = 0x4010
def reparar(muertos, quien=2, oro=1000, x=5, dueno_otro=False):
    g, c = recibir(pw=MURO, oro=1000, x=x)
    mu = g.mu
    mu.mem_write(OB_TAB + 7, bytes([muertos]))
    if dueno_otro: mu.mem_write(OB_TAB + 6, bytes([3]))
    mu.mem_write(0x536c14 + quien * 0x1f8, struct.pack('<i', oro))
    s = 0x536b30 + quien * 0x1f8
    mu.mem_write(s, b'\1'); mu.mem_write(s + 3, bytes([1])); mu.mem_write(0x536c12 + quien * 0x1f8, struct.pack('<h', -1))
    n0 = len(c)
    mu.mem_write(PKT + 0xc, struct.pack('<4h', quien, x, 7, REP))
    g.correr(BD_RECV, 0x4b85bb, struct.pack('<I', RET), [(UC_X86_REG_EAX, BD_PKT + 8), (UC_X86_REG_ESI, PKT)])
    return c[n0:], mu.mem_read(OB_TAB + 7, 1)[0]
ver('12 de 24 muertos: cobra 50 (la mitad de 100) y vuelve a 0', reparar(12), ([(2, -50)], 0))
ver('1 muerto: cobra 4 (100 / 24)', reparar(1), ([(2, -4)], 0))
ver('23 muertos: cobra 95', reparar(23), ([(2, -95)], 0))
ver('control: sin daño, nada', reparar(0), ([], 0))
ver('control: caído (24), nada', reparar(24), ([], 24))
ver('control: oro que no alcanza (49 para 50), nada', reparar(12, oro=49), ([], 12))
ver('control: muro de otro bando, nada', reparar(12, dueno_otro=True), ([], 12))
print('MAL:', mal)
sys.exit(1 if mal else 0)
