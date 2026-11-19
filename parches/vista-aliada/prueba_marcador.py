# Prueba de juguete del marcador en el mapa (F3: ov_key, ov_calc y ov_draw de build.py) sobre el exe parcheado, en unicorn.
# Uso: python prueba_marcador.py [carpeta]   (por defecto E:\Warlords-TEST\Warlords3; armarla antes con build.py)
# Arma 8 bandos a mano (vivos y muertos, oro, ciudades, Winning, ejércitos) y comprueba: F3 va pasando Winning, Armies,
# Cities, Gold y apagado; SHIFT+F3 cambia barras por números; la repetición de la tecla y otras teclas no hacen nada; los
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
OV_FMT = T0 - 3; OV_BAR = OV_FMT - 128; OV_VAL = OV_BAR - 32; OV_OLD = OV_VAL - 36; OV_CUR = OV_OLD - 36
OV_MODE = OV_CUR - 4
OV_RX = T0 + len(b'Winning\0Armies\0Cities\0Gold\0') + 16
def tras(a):   # rutina siguiente: después del «popad; ret» que cierra la anterior, alineada a 16
    i = img.index(b'\x61\xc3', a - BASE) + BASE + 2
    return (i + 15) & ~15
OV_CALC = (OV_RX + 12 + 15) & ~15
OV_KEY = tras(OV_CALC); OV_DRAW = tras(OV_KEY)
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
        self.shift, self.calls, self.calc = False, [], 0
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
            mu.reg_write(UC_X86_REG_EAX, 0x8000 if self.shift and r(1) == 0x10 else 0); ret(4)
        elif a == STUB + 0x10:   # sprintf(buf, "%d", n)
            mu.mem_write(r(1), b'%d\0' % r(3)); ret()
        elif a == 0x440840:
            self.calc += 1; ret()
        elif a == 0x4dd0f0:
            self.calls.append(('estilo', r(1), r(2), r(3))); ret()
        elif a in (0x4dd200, 0x4dd180):
            self.calls.append(('der' if a == 0x4dd200 else 'izq', r(1), r(2), r(3), self.s(r(4)))); ret()

    def corre(self, a, *args):
        sp = STACK - 4 * len(args)
        self.mu.mem_write(sp - 4, struct.pack('<I', FIN) + b''.join(struct.pack('<I', x) for x in args))
        self.mu.reg_write(UC_X86_REG_ESP, sp - 4)
        self.mu.emu_start(a, FIN)

    def tecla(self, vk=0x72, repetida=False, shift=False):
        self.shift = shift
        self.mu.mem_write(MSG, struct.pack('<IIII', 0, 0x100, vk, (1 << 30) if repetida else 1))
        self.corre(OV_KEY, MSG)

    def modo(self): return tuple(self.mu.mem_read(OV_MODE, 2))
    def tabla(self):
        c = bytes(self.mu.mem_read(OV_CUR, 36)); n = c[2]
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
j.tecla(0x71)
ver('otra tecla (F2) no cambia nada', j.modo(), (0, 0))
j.tecla()
ver('F3: Winning', j.modo(), (1, 0))
ver('pide redibujo', j.repinta(), 1)
ver('Winning: 4 primeros vivos, de mayor a menor, barras escaladas al primero', j.tabla(),
    [(1, 40, '|' * 20), (3, 20, '|' * 10), (0, 10, '|' * 5), (5, 5, '|' * 2)])
j.corre(OV_CALC)
ver('sin cambios no pide redibujo', j.repinta(), 0)
j.lado(0, oro=900, ciudades=3, winning=11)
j.corre(OV_CALC)
ver('con un cambio sí', j.repinta(), 1)
j.tecla(repetida=True)
ver('la repetición de la tecla no avanza', j.modo(), (1, 0))
j.tecla()
ver('Armies (cuenta por dueño, sin el muerto)', j.tabla(),
    [(5, 3, '|' * 20), (1, 2, '|' * 13), (3, 1, '|' * 6), (0, 0, '')])
j.tecla(shift=True)
ver('SHIFT+F3: números, mismo informe', (j.modo(), j.tabla()[0]), ((2, 1), (5, 3, '3')))
j.tecla()
ver('Cities con números', j.tabla(), [(1, 9, '9'), (5, 5, '5'), (0, 3, '3'), (3, 1, '1')])
j.tecla(shift=True)
j.tecla()
ver('Gold con barras', j.tabla(), [(0, 900, '|' * 20), (3, 450, '|' * 10), (5, 300, '|' * 6), (1, 100, '|' * 2)])

j.calls = []
j.mu.mem_write(0x4ff7a4, b'\1')
j.mu.reg_write(UC_X86_REG_ESI, 0x1234); j.mu.reg_write(UC_X86_REG_EBX, 1000); j.mu.reg_write(UC_X86_REG_EBP, 50)
j.corre(OV_DRAW)
X = 1000 + 0x21c - 74; Y = 50 + 0x58
ver('dibujo: título en dorado, nombres a la derecha de X, barras desde X + 4, en sus colores', j.calls[:7], [
    ('estilo', 1, 137, 0xa), ('der', 0x1234, X, Y, 'Gold'),
    ('estilo', 1, 100, 200), ('der', 0x1234, X, Y + 14, 'Lado0'), ('izq', 0x1234, X + 4, Y + 14, '|' * 20),
    ('estilo', 1, 103, 203), ('der', 0x1234, X, Y + 28, 'Lado3')])
ver('cuatro renglones', len(j.calls), 2 + 4 * 3)
ver('ov_draw preserva los registros', (j.mu.reg_read(UC_X86_REG_ESI), j.mu.reg_read(UC_X86_REG_EBX),
                                       j.mu.reg_read(UC_X86_REG_EBP)), (0x1234, 1000, 50))
j.tecla()
j.calls = []
j.corre(OV_DRAW)
ver('apagado: no dibuja y pide redibujo para borrar', (j.modo()[0], j.calls, j.repinta()), (0, [], 1))

k = Juego()
k.lado(4, oro=10); k.lado(7, oro=20)
k.tecla(); k.tecla(); k.tecla(); k.tecla()
ver('con 2 bandos vivos, 2 renglones', k.tabla(), [(7, 20, '|' * 20), (4, 10, '|' * 10)])

print('TODO OK' if not mal else f'{mal} MAL')
sys.exit(1 if mal else 0)
