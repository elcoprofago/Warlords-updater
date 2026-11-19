# Prueba de juguete del marcador en el mapa (F12: ov_key, ov_calc y ov_draw de build.py) sobre el exe parcheado, en unicorn.
# Uso: python prueba_marcador.py [carpeta]   (por defecto E:\Warlords-TEST\Warlords3; armarla antes con build.py)
# Arma 8 bandos a mano (vivos y muertos, oro, ciudades, Winning, ejércitos) y comprueba: F12 va pasando Winning, Armies,
# Cities, Gold y apagado; SHIFT+F12 pasa por nombres/escudos con barras/números; estrella del bando con hechizos; la repetición de la tecla y otras teclas no hacen nada; los
# 4 primeros vivos van de mayor a menor con barras escaladas al primero; un muerto no aparece aunque tenga más; sin
# cambios no se pide redibujo y con cambios sí; lo que se dibuja (título, nombres, colores, posiciones).
import os as _os, sys as _sys; _sys.path.append(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..'))  # para encontrar juego_pruebas.py
from juego_pruebas import W3  # carpeta del juego de pruebas: se cambia solo ahi
import os, sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

DIR = sys.argv[1] if len(sys.argv) > 1 else W3
pe = pefile.PE(os.path.join(DIR, 'DarklordAV.exe')); BASE = pe.OPTIONAL_HEADER.ImageBase
img = bytes(pe.get_memory_mapped_image())
SIZE = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
T0 = BASE + img.index(b'%d\0Winning\0Armies\0Cities\0Gold\0') + 3
OV_FMT = T0 - 3; OV_BAR = OV_FMT - 128; OV_VAL = OV_BAR - 32; OV_OLD = OV_VAL - 40; OV_CUR = OV_OLD - 40
OV_MODE = OV_CUR - 4
OV_RX = T0 + len(b'Winning\0Armies\0Cities\0Gold\0') + 16
def tras(a):   # rutina siguiente: después del «popad; ret» que cierra la anterior, alineada a 16
    i = img.index(b'\x61\xc3', a - BASE) + BASE + 2
    return (i + 15) & ~15
OV_SHXY = OV_RX + 12
OV_CALC = (OV_SHXY + 64 + 15) & ~15
OV_KEY = tras(OV_CALC)
OV_POLL = (img.index(struct.pack('<IIII', 0, 0x100, 0x7b, 1)) + BASE + 16 + 15) & ~15   # ov_poll va detrás de ov_fake
OV_PIC = tras(OV_POLL)                 # ov_pic: carga la hoja y sigue a 0x4dd530
OV_STAR = tras(OV_PIC)                 # ov_star (estrella con rectangulos), despues ov_w (medida del texto)
OV_W = tras(OV_STAR)
OV_DRAW = (img.index(b'\x5a\x59\xc3', OV_W - BASE) + BASE + 3 + 15) & ~15
PK_GAK = BASE + img.index(b'GetAsyncKeyState\0') + 17
SPRINTF = 0x5a9bec
REPAINT = 0x569588 + 0x1a4
STUB, STACK, MSG, FIN = 0x300000, 0x1f0000, 0x200000, 0x300100

mal = 0
def ver(nombre, r, esperado):
    global mal
    ok = r == esperado
    mal += not ok
    print('OK ' if ok else 'MAL', nombre, '->', r)

class Juego:
    def __init__(self):
        mu = self.mu = Uc(UC_ARCH_X86, UC_MODE_32)
        mu.mem_map(BASE, SIZE); mu.mem_write(BASE, img[:SIZE])
        mu.mem_map(0x100000, 0x200000); mu.mem_map(STUB, 0x1000)
        mu.mem_write(STUB, b'\xc3'); mu.mem_write(FIN, b'\xc3')
        mu.mem_write(PK_GAK, struct.pack('<I', STUB)); mu.mem_write(SPRINTF, struct.pack('<I', STUB + 0x10))
        mu.mem_write(STUB + 0x10, b'\xc3')
        self.shift, self.f12, self.calls, self.calc = False, False, [], 0
        for p in range(8):
            r = 0x536b30 + p * 0x1f8
            mu.mem_write(r, b'\0\0'); mu.mem_write(r + 4, f'Lado{p}\0'.encode())
            mu.mem_write(r + 0xee, struct.pack('<HH', 100 + p, 200 + p))
        mu.mem_write(0x54fe50, struct.pack('<h', 1))
        mu.hook_add(UC_HOOK_CODE, self.gancho)

    def lado(self, p, vivo=True, oro=0, ciudades=0, winning=0):
        r = 0x536b30 + p * 0x1f8
        self.mu.mem_write(r, b'\1\1' if vivo else b'\1\0')
        self.mu.mem_write(r + 0xe4, struct.pack('<i', oro))
        self.mu.mem_write(0x536b20 + 2 * p, struct.pack('<h', ciudades))
        self.mu.mem_write(0x5643c8 + 2 * p, struct.pack('<h', winning))

    def ejercitos(self, duenos):   # lista de colores, uno por ejército vivo (el 0 de la tabla no cuenta)
        self.mu.mem_write(0x54fe50, struct.pack('<h', len(duenos) + 1))
        for i, c in enumerate(duenos, 1):
            e = 0x54fe50 + i * 0x1c
            self.mu.mem_write(e + 0xe, struct.pack('<H', c << 5)); self.mu.mem_write(e + 0x13, b'\x40')

    def s(self, a):
        b = bytes(self.mu.mem_read(a, 64)); return b[:b.index(0)].decode()

    def gancho(self, mu, a, size, _):
        sp = mu.reg_read(UC_X86_REG_ESP)
        r = lambda k: struct.unpack('<i', mu.mem_read(sp + 4 * k, 4))[0]
        ret = lambda n=0: (mu.reg_write(UC_X86_REG_ESP, sp + 4 + n), mu.reg_write(UC_X86_REG_EIP, r(0)))
        if a == STUB:   # GetAsyncKeyState (stdcall, 1 argumento)
            k = r(1)
            mu.reg_write(UC_X86_REG_EAX, 0x8000 if (k == 0x10 and self.shift) or (k == 0x7b and self.f12) else 0); ret(4)
        elif a == STUB + 0x10:   # sprintf(buf, "%d", n)
            mu.mem_write(r(1), b'%d\0' % r(3)); ret()
        elif a == 0x440840:
            self.calc += 1; ret()
        elif a == 0x4dd0f0:
            self.calls.append(('estilo', r(1), r(2), r(3))); ret()
        elif a in (0x4dd200, 0x4dd180):
            self.calls.append(('der' if a == 0x4dd200 else 'izq', r(1), r(2), r(3), self.s(r(4)))); ret()
        elif a == 0x4ede30:   # recoloreo de un rectángulo (superficie, x, y, ancho, alto, tabla): el color de la tabla
            t = bytes(mu.mem_read(r(6), 256))
            self.calls.append(('rect', r(1), r(2), r(3), r(4), r(5), t[0] if t == t[:1] * 256 else None)); ret()
        elif a == 0x4e5930:   # ancho del texto (thiscall, cadena, fuente): 5 px por letra
            mu.reg_write(UC_X86_REG_EAX, 5 * len(self.s(r(1)))); ret(8)
        elif a == 0x4e4a90:   # busqueda de la hoja (thiscall, 1 argumento): ya cargada
            mu.mem_write(STUB + 0x80, struct.pack('<III', 0, 0, 1)); mu.reg_write(UC_X86_REG_EAX, STUB + 0x80); ret(4)
        elif a == 0x4dd530:   # pegar (archivo, sx, sy, w, h, superficie, dx, dy)
            self.calls.append(('pic',) + tuple(r(k) for k in range(1, 9))); ret()

    def corre(self, a, *args):
        sp = STACK - 4 * len(args)
        self.mu.mem_write(sp - 4, struct.pack('<I', FIN) + b''.join(struct.pack('<I', x) for x in args))
        self.mu.reg_write(UC_X86_REG_ESP, sp - 4)
        self.mu.emu_start(a, FIN)

    def tecla(self, vk=0x7b, repetida=False, shift=False):
        self.shift = shift
        self.mu.mem_write(MSG, struct.pack('<IIII', 0, 0x100, vk, (1 << 30) if repetida else 1))
        self.corre(OV_KEY, 0, MSG)   # como desde pz_disp: [esp + 4] es la vuelta de pz_disp, el MSG va en [esp + 8]
        return self.mu.reg_read(UC_X86_REG_EAX)

    def modo(self): return tuple(self.mu.mem_read(OV_MODE, 2))
    def tabla(self):
        c = bytes(self.mu.mem_read(OV_CUR, 40)); n = c[2]
        idx = struct.unpack('<4i', c[4:20])[:n]; val = struct.unpack('<4i', c[20:36])[:n]
        return [(i, v, self.s(OV_BAR + 32 * k)) for k, (i, v) in enumerate(zip(idx, val))]
    def repinta(self):
        v = self.mu.mem_read(REPAINT, 1)[0]; self.mu.mem_write(REPAINT, b'\0'); return v

j = Juego()
j.lado(0, oro=900, ciudades=3, winning=10)
j.lado(1, oro=100, ciudades=9, winning=40)
j.lado(2, vivo=False, oro=9999, ciudades=20, winning=90)
j.lado(3, oro=450, ciudades=1, winning=20)
j.lado(5, oro=300, ciudades=5, winning=5)
j.lado(6, oro=0, ciudades=0, winning=0)
j.ejercitos([1, 1, 3, 5, 5, 5, 2, 2, 2, 2])

j.corre(OV_CALC)
ver('apagado: no calcula ni pide redibujo', (j.calc, j.repinta()), (0, 0))
ver('otra tecla (F2) sigue hacia el juego', j.tecla(0x71), 0)
ver('y no cambia nada', j.modo(), (0, 0))
ver('F12 no sigue hacia el juego', j.tecla(), 1)
ver('F12: Winning', j.modo(), (1, 0))
ver('pide redibujo', j.repinta(), 1)
ver('Winning: 4 primeros vivos, de mayor a menor, barras escaladas al primero', j.tabla(),
    [(1, 40, '|' * 20), (3, 20, '|' * 10), (0, 10, '|' * 5), (5, 5, '|' * 2)])
j.corre(OV_CALC)
ver('sin cambios no pide redibujo', j.repinta(), 0)
j.lado(0, oro=900, ciudades=3, winning=11)
j.corre(OV_CALC)
ver('con un cambio sí', j.repinta(), 1)
ver('la repetición tampoco sigue hacia el juego', j.tecla(repetida=True), 1)
ver('la repetición de la tecla no avanza', j.modo(), (1, 0))
j.tecla()
ver('Armies (cuenta por dueño, sin el muerto)', j.tabla(),
    [(5, 3, '|' * 20), (1, 2, '|' * 13), (3, 1, '|' * 6), (0, 0, '')])
j.tecla(shift=True)
ver('SHIFT+F12: números, mismo informe', (j.modo(), j.tabla()[0]), ((2, 1), (5, 3, '3')))
j.tecla()
ver('Cities con números', j.tabla(), [(1, 9, '9'), (5, 5, '5'), (0, 3, '3'), (3, 1, '1')])
j.tecla(shift=True)
ver('SHIFT+F12 otra vez: escudos y barras', j.modo()[1], 2)
j.tecla()
ver('Gold con barras', j.tabla(), [(0, 900, '|' * 20), (3, 450, '|' * 10), (5, 300, '|' * 6), (1, 100, '|' * 2)])

j.tecla(shift=True)
ver('SHIFT+F12 otra vez: escudos y numeros', j.modo()[1], 3)
j.tecla(shift=True)
ver('SHIFT+F12 al cuarto toque vuelve a nombres y barras', j.modo(), (4, 0))
HE = 0x55f030
j.mu.mem_write(HE + 5 * 0x56, struct.pack('<BBh', 1, 0, 3))     # hechizo vivo del heroe 3 (ejercito del bando 3)
j.mu.mem_write(HE + 6 * 0x56, struct.pack('<BBh', 0, 0, 7))     # control: muerto, del heroe 7 (bando 2)
j.corre(OV_CALC)
ver('mascara de hechizos: solo el bando 3', (struct.unpack('<I', j.mu.mem_read(OV_CUR + 36, 4))[0], j.repinta()), (8, 1))
j.calls = []
j.mu.mem_write(0x4ff7a4, b'\1')
j.mu.reg_write(UC_X86_REG_ESI, 0x1234); j.mu.reg_write(UC_X86_REG_EBX, 1000); j.mu.reg_write(UC_X86_REG_EBP, 50)
j.corre(OV_DRAW)
R = 1000 + 0x21c; Y = 50 + 0x56; TG = 3
STAR = [(102, [(0, 5, 1, 1), (10, 5, 1, 1)]),
        (103, [(5, 0, 1, 1), (4, 1, 1, 1), (6, 1, 1, 1), (1, 4, 1, 1), (9, 4, 1, 1), (1, 6, 1, 1), (9, 6, 1, 1), (4, 9, 1, 1), (6, 9, 1, 1), (5, 10, 1, 1)]),
        (104, [(5, 1, 1, 1), (4, 2, 1, 1), (5, 2, 1, 1), (6, 2, 1, 1), (4, 3, 1, 1), (6, 3, 1, 1), (2, 4, 1, 1), (8, 4, 1, 1), (1, 5, 1, 1), (2, 5, 1, 1), (8, 5, 1, 1), (9, 5, 1, 1), (2, 6, 1, 1), (3, 6, 1, 1), (7, 6, 1, 1), (8, 6, 1, 1), (4, 7, 1, 1), (6, 7, 1, 1), (4, 8, 1, 1), (5, 8, 1, 1), (6, 8, 1, 1), (5, 9, 1, 1)]),
        (105, [(5, 3, 1, 1), (3, 4, 1, 1), (4, 4, 1, 1), (5, 4, 1, 1), (6, 4, 1, 1), (7, 4, 1, 1), (3, 5, 1, 1), (4, 5, 1, 1), (6, 5, 1, 1), (7, 5, 1, 1), (4, 6, 1, 1), (5, 6, 1, 1), (6, 6, 1, 1), (5, 7, 1, 1)]),
        (106, [(5, 5, 1, 1)])]   # estrella de la esfera de mana, PICTS.PCX (1.0.265.0)
NSTAR = sum(len(rr) for _, rr in STAR)
def estrella(x, y): return [('rect', 0x1234, x + dx, y + dy, w, h, c) for c, rr in STAR for dx, dy, w, h in rr]
def barra(x, y, n, color): return [('rect', 0x1234, x + 3 * k, y, 2, 5, color) for k in range(n)]
# nombres y barras: lo mas largo a la derecha, 20 barras (64 px); a la izquierda 'Lado3' (25 px, 5 por letra) + estrella (13)
X = R - 64 - 3; YR = Y + TG + 12
ver('dibujo: pegado al margen (3 px), titulo centrado sobre los renglones, estrella chica a la izquierda del nombre',
    j.calls[:5 + 40 + 2 + NSTAR], [
    ('estilo', 4, 0, 0), ('estilo', 8, 137, 0xa), ('der', 0x1234, X + (64 - 38 + 20) // 2, Y, 'Gold'),
    ('estilo', 4, 100, 200), ('der', 0x1234, X, YR, 'Lado0')]
    + barra(X + 5, YR + 4, 20, 200) + barra(X + 4, YR + 3, 20, 100)
    + [('estilo', 4, 103, 203), ('der', 0x1234, X, YR + 12, 'Lado3')] + estrella(X - 38, YR + 12))
ver('cuatro renglones y una estrella', len(j.calls), 3 + 2 * 4 + 2 * (20 + 10 + 6 + 2) + NSTAR)
ver('ov_draw preserva los registros', (j.mu.reg_read(UC_X86_REG_ESI), j.mu.reg_read(UC_X86_REG_EBX),
                                       j.mu.reg_read(UC_X86_REG_EBP)), (0x1234, 1000, 50))
j.tecla(shift=True); j.tecla(shift=True); j.tecla(shift=True)
j.calls = []
j.corre(OV_DRAW)
# escudos y numeros: a la derecha '900' (15 + 4); a la izquierda escudo (11) + estrella (13)
X = R - 19 - 3; YS = Y + TG + 15
ver('escudos y numeros: pegado al margen, titulo centrado, escudo a la izquierda de X, renglon de 15, estrella, numero',
    j.calls[:3 + 3 + 2 + NSTAR + 1], [
    ('estilo', 4, 0, 0), ('estilo', 8, 137, 0xa), ('der', 0x1234, X + (19 - 24 + 20) // 2, Y, 'Gold'),
    ('estilo', 4, 100, 200), ('pic', 7, 33, 1, 11, 14, 0x1234, X - 11, YS - 2), ('izq', 0x1234, X + 4, YS, '900'),
    ('estilo', 4, 103, 203), ('pic', 7, 33, 38, 11, 14, 0x1234, X - 11, YS + 15 - 2)]
    + estrella(X - 24, YS + 15) + [('izq', 0x1234, X + 4, YS + 15, '450')])
j.tecla()
j.calls = []
j.corre(OV_DRAW)
ver('apagado: no dibuja y pide redibujo para borrar', (j.modo()[0], j.calls, j.repinta()), (0, [], 1))

p = Juego()
def poll(abajo):
    p.f12 = abajo; p.corre(OV_POLL)
poll(False); ver('ov_poll: sin F12 no cambia nada', p.modo(), (0, 0))
poll(True); ver('ov_poll: al bajar F12, Winning', p.modo(), (1, 0))
poll(True); poll(True); ver('ov_poll: mientras sigue apretada no avanza', p.modo(), (1, 0))
poll(False); poll(True); ver('ov_poll: soltar y volver a apretar, Armies', p.modo(), (2, 0))

k = Juego()
k.lado(4, oro=10); k.lado(7, oro=20)
k.tecla(); k.tecla(); k.tecla(); k.tecla()
ver('con 2 bandos vivos, 2 renglones', k.tabla(), [(7, 20, '|' * 20), (4, 10, '|' * 10)])

print('TODO OK' if not mal else f'{mal} MAL')
sys.exit(1 if mal else 0)
