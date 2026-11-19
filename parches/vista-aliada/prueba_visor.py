# Prueba de juguete del visor de miniaturas (vw_* de build.py) sobre el exe y el RES parcheados, en unicorn.
# Uso: python prueba_visor.py [carpeta]   (por defecto E:\Warlords-TEST\Warlords3; armarla antes con build.py)
# Casilla: el evento 10 de Edit Side (0x44da1c) con el control 76 guarda el valor en vw_on (tildada: dibuja el marco); las casillas 0x23/0x24
# siguen yendo a lo suyo. Pintado: el 5.º callback del selector (el que 0x402862 empuja) con las funciones de hojas y
# el Blt de DirectDraw interceptados: celda (1,161)-(49,209) de ARMY\<nombre> estirada a (2,2)-(98,98) con clave de
# color, marco 199 y fondo 0, y la hoja a la pantalla en (ancho - 108, 8). RES: el registro 76 del diálogo 86.
# Controles (no dibujan nada): casilla destildada, otro evento de pintado, héroes (clase 5), fila -1 y fila fuera de
# la lista; y el exe original no tiene nada de esto.
import os as _os, sys as _sys; _sys.path.append(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..'))
from juego_pruebas import W3
import os, sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

DIR = sys.argv[1] if len(sys.argv) > 1 else W3
pe = pefile.PE(os.path.join(DIR, 'DarklordAV.exe')); BASE = pe.OPTIONAL_HEADER.ImageBase
img = bytes(pe.get_memory_mapped_image())
SIZE = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
STACK, RET, VT, SURF = 0x1f0000, 0x100, 0x120000, 0x121000
LIST = 0x130000
VW_CHK = 76

mal = 0
def ver(nombre, r, esperado):
    global mal
    ok = r == esperado
    mal += not ok
    print('OK ' if ok else 'MAL', nombre, '->', r)

def u32(a): return struct.unpack_from('<I', img, a - BASE)[0]
VW_PAINT = u32(0x40285d)
ver('el selector empuja otro pintado', VW_PAINT != 0x402c40 and VW_PAINT > 0x600000, True)
cs = Cs(CS_ARCH_X86, CS_MODE_32)
ins = list(cs.disasm(img[VW_PAINT - BASE:VW_PAINT - BASE + 40], VW_PAINT))
VW_ON = int(ins[0].op_str.split('[')[1].split(']')[0], 16)   # cmp byte ptr [vw_on], 0

def maquina():
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(BASE, SIZE); mu.mem_write(BASE, img[:SIZE])
    mu.mem_map(0x100000, 0x100000)
    mu.mem_write(0x500be8, struct.pack('<H', 800))
    mu.mem_write(VT, struct.pack('<32I', *([0xdead0000] * 32)))
    mu.mem_write(VT + 0x14, struct.pack('<I', 0x110000))            # Blt
    mu.mem_write(SURF, struct.pack('<I', VT))
    names = [b'Archons', b'Dwarves', b'Elves']
    for i, n in enumerate(names): mu.mem_write(LIST + i * 48, n + b'\0')
    mu.mem_write(0x5016d4, struct.pack('<I', LIST))
    mu.mem_write(0x5016e4, struct.pack('<H', len(names)))
    return mu

def intercept(mu, addr, pop, fn):
    def g(mu, a, size, _):
        sp = mu.reg_read(UC_X86_REG_ESP)
        ret, *args = struct.unpack('<8I', mu.mem_read(sp, 32))
        fn(mu, args)
        mu.reg_write(UC_X86_REG_EAX, 0)
        mu.reg_write(UC_X86_REG_ESP, sp + 4 + pop); mu.reg_write(UC_X86_REG_EIP, ret)
    mu.hook_add(UC_HOOK_CODE, g, begin=addr, end=addr)

def rect(mu, a): return struct.unpack('<4i', mu.mem_read(a, 16)) if a else None

def pintar(evento=2, on=1, clase=1, fila=1):
    mu = maquina()
    mu.mem_write(VW_ON, bytes([on]))
    mu.mem_write(0x5016dc, struct.pack('<H', clase))
    mu.mem_write(0x5016d0, struct.pack('<h', fila))
    log = []
    def obj(mu): return mu.reg_read(UC_X86_REG_ECX)
    def ctor(mu, a): log.append(('ctor', obj(mu)))
    def init(mu, a):
        o = obj(mu); nm = bytes(mu.mem_read(a[1], 16)).split(b'\0')[0].decode()
        log.append(('init', nm, a[2], a[3], a[4], a[5]))
        mu.mem_write(o + 0x3c, struct.pack('<I', SURF if nm == '' else SURF + 0x100))
    def load(mu, a): log.append(('load',))
    def free(mu, a): log.append(('free',))
    def scr(mu, a): log.append(('pantalla', tuple(a[:6])))
    def blt(mu, a):
        this, dst, src, srect, flags, fx = a[:6]
        fill = struct.unpack('<I', mu.mem_read(fx + 0x50, 4))[0] if fx else None
        log.append(('blt', this == SURF, rect(mu, dst), src, rect(mu, srect), hex(flags), fill))
    intercept(mu, 0x4e3470, 0, ctor); intercept(mu, 0x4e34d0, 0x1c, init); intercept(mu, 0x4e3540, 4, load)
    intercept(mu, 0x4e34a0, 0, free); intercept(mu, 0x4e3c10, 0x18, scr); intercept(mu, 0x110000, 0x18, blt)
    mu.mem_write(STACK, struct.pack('<4I', RET, evento, 50, 60))
    regs = ((UC_X86_REG_EBX, 0x9abc), (UC_X86_REG_ESI, 0x1234), (UC_X86_REG_EDI, 0x5678), (UC_X86_REG_EBP, 0xdef0))
    for r, v in regs: mu.reg_write(r, v)
    mu.reg_write(UC_X86_REG_ESP, STACK)
    mu.emu_start(VW_PAINT, RET, count=100000)
    ok = mu.reg_read(UC_X86_REG_ESP) == STACK + 4 and all(mu.reg_read(r) == v for r, v in regs)
    return ok, log

ok, log = pintar()
ver('pintado: registros preservados', ok, True)
ver('pintado: hoja en blanco 100x100', log[2], ('init', '', 0, 0, 100, 100))
ver('pintado: hoja de la unidad', [x for x in log if x[0] == 'init'][1], ('init', 'Dwarves', 2, 1, 0, 0))
blts = [x for x in log if x[0] == 'blt']
ver('pintado: marco', blts[0], ('blt', True, (0, 0, 100, 100), 0, None, '0x1000400', 199))
ver('pintado: fondo oscuro', blts[1], ('blt', True, (2, 2, 98, 98), 0, None, '0x1000400', 0))
ver('pintado: figura al doble con clave de color', blts[2], ('blt', True, (2, 2, 98, 98), SURF + 0x100,
                                                             (1, 161, 49, 209), '0x1008000', None))
ver('pintado: a la pantalla arriba a la derecha', [x for x in log if x[0] == 'pantalla'],
    [('pantalla', (0, 0, 100, 100, 800 - 108, 8))])
ver('pintado: libera las dos hojas', log[-2:], [('free',), ('free',)])
for nombre, kw in (('casilla destildada', dict(on=0)), ('otro evento', dict(evento=3)),
                   ('casilla destildada, solo marco', dict(on=0, evento=1))):
    ok, log = pintar(**kw)
    ver(f'control {nombre}: nada', (ok, log), (True, []))
for nombre, kw in (('evento 1 (casilla tildada)', dict(evento=1)), ('héroes', dict(clase=5)),
                   ('fila -1', dict(fila=-1)), ('fila fuera de la lista', dict(fila=3))):
    ok, log = pintar(**kw)
    ver(f'{nombre}: solo el marco, sin figura', (ok, [x[0] for x in log], [x[-1] for x in log if x[0] == 'blt']),
        (True, ['ctor', 'ctor', 'init', 'load', 'blt', 'blt', 'pantalla', 'free', 'free'], [199, 0]))

# Tras el repintado al cambiar de fila (0x4029b1): pinta con evento 2 y sigue con el final original
hook = img[0x4029b1 - BASE:0x4029b6 - BASE]
ver('0x4029b1 salta al visor', hook[0] == 0xe9, True)
VW_AFTER = 0x4029b6 + struct.unpack('<i', hook[1:5])[0]
ain = list(cs.disasm(img[VW_AFTER - BASE:VW_AFTER - BASE + 30], VW_AFTER))
ver('visor tras el repintado', [(i.mnemonic, i.op_str) for i in ain[:2]] + [(i.mnemonic, i.op_str) for i in ain[3:8]],
    [('push', '2'), ('call', hex(VW_PAINT)), ('xor', 'ax, ax'), ('pop', 'edi'), ('pop', 'esi'),
     ('add', 'esp, 0x60'), ('ret', '')])

# Casilla: evento 10 de Edit Side
def casilla(ctrl, valor):
    mu = maquina()
    ev = 0x140000
    mu.mem_write(ev, struct.pack('<IIB', 10, ctrl, valor))
    mu.reg_write(UC_X86_REG_ESI, ev); mu.reg_write(UC_X86_REG_ESP, STACK)
    fin = []
    marco = []
    vf = [i for i in cs.disasm(bytes(mu.mem_read(u32(0x44da2a) + 0x44da2e, 40)), u32(0x44da2a) + 0x44da2e)
          if i.mnemonic == 'call']
    if vf:
        a = int(vf[0].op_str, 16)
        intercept(mu, a, 0, lambda mu, args: marco.append(1))
    for a in (0x44db1c, 0x44da2e, 0x44da3e):
        mu.hook_add(UC_HOOK_CODE, lambda mu, ad, s, _: (fin.append(ad), mu.emu_stop()), begin=a, end=a)
    mu.emu_start(0x44da1c, 0, count=100)
    return fin[0], mu.mem_read(VW_ON, 1)[0], len(marco)
ver('casilla 76 tildada: dibuja el marco', casilla(VW_CHK, 1), (0x44db1c, 1, 1))
ver('casilla 76 destildada', casilla(VW_CHK, 0), (0x44db1c, 0, 0))
ver('control casilla 0x23', casilla(0x23, 1), (0x44da2e, 0, 0))
ver('control casilla 0x24', casilla(0x24, 1), (0x44da3e, 0, 0))
ver('control otro control', casilla(40, 1), (0x44db1c, 0, 0))

# RES: registro 76 del diálogo 86
SZ = {1: 0x80, 2: 0x9c, 3: 0x6c, 4: 0xac, 5: 0xa8, 6: 0xa0, 7: 0x1c, 8: 0x1c, 9: 0x1c, 0xa: 0x20,
      0xb: 0x64, 0xc: 0x64, 0xd: 0x3c, 0xe: 0x30, 0x11: 0x14, 0x12: 0x68, 0x13: 0x28, 0x14: 0x2c, 0x15: 0xac}
def dlg(path, did):
    d = open(path, 'rb').read(); o = 8
    while True:
        h = struct.unpack_from('<5I', d, o)
        if h[0] == 7 and h[1] == did: break
        o += 20 + h[4]
    p, out = o + 20, {}
    for _ in range(h[2]):
        t, i = struct.unpack_from('<II', d, p); out[i] = (t, d[p:p + 4 + SZ[t]]); p += 4 + SZ[t]
    return out
r = dlg(os.path.join(DIR, 'DATA', 'WAR3AV.RES'), 86)
t, rec = r[VW_CHK]
ver('RES: casilla 76', (t, struct.unpack_from('<2I', rec, 8), rec[0x1c:0x26]), (5, (520, 62), b'View units'))
ver('control RES original sin el 76', VW_CHK in dlg(os.path.join(W3, 'DATA', 'War3.RES'), 86), False)
ver('control exe original', struct.unpack_from('<I', open(os.path.join(W3, 'Darklord.exe'), 'rb').read(),
                                                pefile.PE(os.path.join(W3, 'Darklord.exe')).get_offset_from_rva(0x285d))[0],
    0x402c40)
print('MAL:', mal)
sys.exit(1 if mal else 0)
