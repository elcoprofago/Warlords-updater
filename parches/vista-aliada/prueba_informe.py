# Prueba de juguete del +1 de la torre o el faro en el informe de la unidad (ui_tower de build.py, en 0x45e77b del
# caso de la fuerza violeta 0x45e771), en unicorn. Uso: python prueba_informe.py [carpeta]   (por defecto C:\Warlords3)
import os, sys
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prueba_caminos.py'), encoding='utf-8').read()
exec(_src[:_src.index("print('-- menú")])

_OB = b'OBRA' + bytes(4 + 64 * 8)
assert img.count(_OB) == 1
OB_N = BASE + img.index(_OB) + 4
OB_TAB = OB_N + 4
UI = dest(0x45e77b)
def llamadas(va, n):
    r, k = [], va - BASE
    while len(r) < n:
        if img[k] == 0xe8: r.append(BASE + k + 5 + struct.unpack_from('<i', img, k + 1)[0]); k += 5
        else: k += 1
    return r
OB_AT = llamadas(UI, 1)[0]
_k = img.index(bytes.fromhex('0fb682'), OB_AT - BASE); assert _k < OB_AT - BASE + 0x30
OB_MAP = d32(BASE + _k + 3)

def informe(obra=4, fuerza=1, base=1, heroe=False, x=5, y=7):
    g = Juego(); mu = g.mu
    if obra:
        mu.mem_write(OB_N, struct.pack('<I', 1))
        mu.mem_write(OB_TAB, struct.pack('<hhBBBB', x, y, obra, 0, 2, 0))
        mu.mem_write(OB_MAP + (y << 6) + x, bytes([1]))
    A = 3
    mu.mem_write(0x54fe52 + A * 0x1c, struct.pack('<hh', x, y))
    mu.mem_write(0x54fe5e + A * 0x1c, struct.pack('<H', (fuerza << 9) | (0x10 if heroe else 0)))
    mu.mem_write(STACK, bytes(0x40))
    mu.mem_write(STACK + 7, bytes([base]))
    r = []
    def h(mu, *_):
        sp = mu.reg_read(UC_X86_REG_ESP)
        a = struct.unpack('<6I', mu.mem_read(sp + 4, 24)); r.append((a[2] & 0xffff, a[5] & 0xff)); mu.emu_stop()
    mu.hook_add(UC_HOOK_CODE, h, begin=0x4c25d0, end=0x4c25d0)
    mu.reg_write(UC_X86_REG_ESI, A); mu.reg_write(UC_X86_REG_ESP, STACK)
    mu.emu_start(0x45e771, 0, count=5000)
    return r[0] if r else None

print('-- informe: fuerza violeta (valor, se muestra)')
ver('en la torre: 2, se muestra', informe(), (2, 1))
ver('en el faro: 2', informe(obra=5), (2, 1))
ver('control: terreno llano: 1, no se muestra', informe(obra=0), (1, 0))
ver('control: en un muro: 1', informe(obra=7), (1, 0))
ver('control: héroe en la torre: sin +1', informe(heroe=True), (1, 0))
ver('con otro bono (base 3) en la torre: 4', informe(fuerza=1, base=3), (4, 1))
print('MAL:', mal)
sys.exit(1 if mal else 0)
