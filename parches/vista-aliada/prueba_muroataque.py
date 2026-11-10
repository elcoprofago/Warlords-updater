# Prueba de juguete del ataque al muro (wl_war, wv_step, wv_pre, wv_stat, wv_post de build.py; PENDIENTE-faros-muros,
# punto 2b), en unicorn. Uso: python prueba_muroataque.py [carpeta]   (por defecto C:\Warlords3)
# Reusa el banco de prueba_caminos.py. Cada función se corre sola, con las llamadas al juego interceptadas.
import os, sys
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prueba_caminos.py'), encoding='utf-8').read()
exec(_src[:_src.index("print('-- menú")])

_OB = b'OBRA' + bytes(4 + 64 * 8)
assert img.count(_OB) == 1
OB_N = BASE + img.index(_OB) + 4
OB_TAB = OB_N + 4
DIPLO = 0x55ee4c
WV_PRE, WV_POST, WV_STAT, WV_STEP = dest(0x469f35), dest(0x469f54), dest(0x4660d1), dest(0x49e434)
def llamadas(va, n):
    r, k = [], va - BASE
    while len(r) < n:
        if img[k] == 0xe8 and 0 <= k + 5 + struct.unpack_from('<i', img, k + 1)[0] < len(img):
            r.append(BASE + k + 5 + struct.unpack_from('<i', img, k + 1)[0]); k += 5
        else: k += 1
    return r
WL_WAR = llamadas(WV_STEP, 1)[0]
assert img[WV_PRE - BASE] == 0x60 and img[WV_PRE - BASE + 1:WV_PRE - BASE + 3] == b'\xc7\x05'
WV_REC = d32(WV_PRE + 3); WV_N = WV_REC + 4; WV_IDS = WV_REC + 8
OB_AT = llamadas(WL_WAR, 1)[0]
_k = img.index(bytes.fromhex('0fb682'), OB_AT - BASE); assert _k < OB_AT - BASE + 0x30
OB_MAP = d32(BASE + _k + 3)
IA_BAT, H470, OB_DEL, H4F20, OB_FOGME, H1290, REDRAW = llamadas(WV_POST, 7)
assert (H470, H4F20, H1290) == (0x46c470, 0x4a4f20, 0x441290)

def juego(dueño=2, muertos=0, tipo=7, guerra=True, x=5, y=7):
    g = Juego(); mu = g.mu
    mu.mem_write(OB_N, struct.pack('<I', 1))
    mu.mem_write(OB_TAB, struct.pack('<hhBBBB', x, y, tipo, 3, dueño, muertos))
    mu.mem_write(OB_MAP + (y << 6) + x, bytes([1]))
    for a in range(8):
        for b in range(8):
            mu.mem_write(DIPLO + a * 56 + b, bytes([2 if guerra and a != b else 0]))
    return g

print('-- wl_war')
def war(p, **kw):
    g = juego(**kw)
    g.correr(WL_WAR, RET, struct.pack('<I', RET), [(UC_X86_REG_EAX, 5), (UC_X86_REG_EDX, 7), (UC_X86_REG_ECX, p)])
    return g.mu.reg_read(UC_X86_REG_EAX)
ver('bando 5 en guerra con el dueño 2: el registro', war(5), OB_TAB)
ver('control: en paz', war(5, guerra=False), 0)
ver('control: el propio dueño', war(2), 0)
ver('control: 24 muertos (caído)', war(5, muertos=24), 0)
ver('23 muertos: todavía en pie', war(5, muertos=23), OB_TAB)
ver('control: torre (tipo 4)', war(5, tipo=4), 0)
ver('control: neutral (8)', war(8), 0)

print('-- wv_step')
W = 0x160000
def paso(p, palabra=0, **kw):
    g = juego(**kw); mu = g.mu
    mu.mem_write(W, struct.pack('<H', palabra))
    r = []
    for a, n in ((0x49e57d, 'ataque'), (0x49e467, 'libre'), (0x49e43d, 'ocupada')):
        mu.hook_add(UC_HOOK_CODE, lambda mu, *_, n=n: (r.append(n), mu.emu_stop()), begin=a, end=a)
    mu.reg_write(UC_X86_REG_EDX, W); mu.reg_write(UC_X86_REG_ESI, 5); mu.reg_write(UC_X86_REG_EDI, 7)
    mu.reg_write(UC_X86_REG_EBP, p); mu.reg_write(UC_X86_REG_ESP, STACK)
    mu.emu_start(0x49e434, 0, count=5000)
    return r[:1]
ver('casilla vacía con muro enemigo: ataque (código 2)', paso(5), ['ataque'])
ver('control: en paz: libre', paso(5, guerra=False), ['libre'])
ver('control: el dueño: libre', paso(2), ['libre'])
ver('control: ocupada: sigue el camino original', paso(5, palabra=0x8000), ['ocupada'])

print('-- wv_pre')
def pre(p=5, muertos=0, reales=0, ocup=None):
    g = juego(muertos=muertos); mu = g.mu
    if ocup is not None: mu.mem_write(casilla(5, 7), struct.pack('<H', ocup))
    nuevos = []
    def nuevo(a):
        i = 100 + len(nuevos); nuevos.append((a[0], i)); return 0x54fe52 + i * 0x1c
    g.interceptar(0x46c330, nuevo)
    g.interceptar(0x43b6d0, lambda a: 0)
    g.interceptar(0x4411b0, lambda a: reales)
    g.correr(WV_PRE, 0x464ac0, struct.pack('<IIIII', RET, p, 5, 7, 0))
    n = struct.unpack('<I', mu.mem_read(WV_N, 4))[0]
    ids = list(struct.unpack(f'<{n}h', mu.mem_read(WV_IDS, 2 * n))) if n else []
    pos = [struct.unpack('<hh', mu.mem_read(0x54fe52 + i * 0x1c, 4)) for i in ids[:1]]
    dueño = (struct.unpack('<H', mu.mem_read(casilla(5, 7), 2))[0] >> 10) & 0xf
    return n, len(set(o for o, _ in nuevos)) and nuevos[0][0], pos, dueño, struct.unpack('<I', mu.mem_read(WV_REC, 4))[0] == OB_TAB
ver('muro entero: 24 arqueros del dueño 2 en (5, 7), palabra del mapa con el dueño 2', pre(), (24, 2, [(5, 7)], 2, True))
ver('10 muertos: 14', pre(muertos=10)[0], 14)
ver('con 20 defensores reales: tope 32, 12', pre(reales=20)[0], 12)
ver('control: en paz (el dueño ataca): ninguno', pre(p=2)[:1], (0,))
ver('control: casilla ocupada por otro bando (3): ninguno', pre(ocup=0x8000 | 3 << 10)[0], 0)
ver('casilla ocupada por el dueño: 24', pre(ocup=0x8000 | 2 << 10)[0], 24)

print('-- wv_stat')
def stat(id_):
    g = juego(); mu = g.mu
    mu.mem_write(WV_N, struct.pack('<I', 2)); mu.mem_write(WV_IDS, struct.pack('<hh', 100, 101))
    S = 0x170000
    mu.mem_write(S + 0x12e, struct.pack('<h', id_))
    r = []
    for a, n in ((0x4661ba, 'sin estadística'), (0x4660d9, 'normal')):
        mu.hook_add(UC_HOOK_CODE, lambda mu, *_, n=n: (r.append(n), mu.emu_stop()), begin=a, end=a)
    mu.reg_write(UC_X86_REG_EDI, S); mu.reg_write(UC_X86_REG_ESP, STACK)
    mu.emu_start(WV_STAT, 0, count=100)
    return r[:1]
ver('arquero virtual 101', stat(101), ['sin estadística'])
ver('control: ejército real 7', stat(7), ['normal'])

print('-- wv_post')
def post(muertos=0, vivos=(), n=24):
    g = juego(muertos=muertos); mu = g.mu
    ids = list(range(100, 100 + n))
    for i in ids:
        mu.mem_write(0x54fe63 + i * 0x1c, bytes([0x40 if i in vivos else 0]))
    mu.mem_write(WV_REC, struct.pack('<II', OB_TAB, n)); mu.mem_write(WV_IDS, struct.pack(f'<{n}h', *ids))
    bajas = []
    g.interceptar(IA_BAT, lambda a: g.llamadas.append('ia_bat'))
    g.interceptar(0x46c470, lambda a: bajas.append(a[0]))
    for a, nom in ((0x4a4f20, 'grafo'), (OB_FOGME, 'niebla'), (0x441290, 'ocupación'), (REDRAW, 'redibujo')):
        g.interceptar(a, lambda _, nom=nom: g.llamadas.append(nom))
    g.correr(WV_POST, RET, struct.pack('<III', RET, 0, 0))
    obn = struct.unpack('<I', mu.mem_read(OB_N, 4))[0]
    return sorted(bajas), obn, mu.mem_read(OB_TAB + 7, 1)[0] if obn else None, g.llamadas, \
        struct.unpack('<II', mu.mem_read(WV_REC, 8))
ver('mueren 10 de 24: los 14 vivos de baja, +7 = 10', post(vivos=range(110, 124))[:3], (list(range(110, 124)), 1, 10))
ver('ya 20 muertos, mueren 4: cae el bloque', post(muertos=20, n=4)[1:4],
    (0, None, ['ia_bat', 'grafo', 'niebla', 'ocupación', 'redibujo']))
ver('ninguno muere: +7 sigue en 0, se limpia el estado', (lambda r: (r[0], r[2], r[4]))(post(vivos=range(100, 124))),
    (list(range(100, 124)), 0, (0, 0)))
def sin_muro():
    g = juego(); mu = g.mu
    g.interceptar(IA_BAT, lambda a: g.llamadas.append('ia_bat'))
    g.correr(WV_POST, RET, struct.pack('<III', RET, 0, 0))
    return g.llamadas
ver('control: batalla común (sin muro): solo ia_bat', sin_muro(), ['ia_bat'])

print('MAL:', mal)
sys.exit(1 if mal else 0)
