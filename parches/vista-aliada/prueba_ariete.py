# Prueba de juguete del retrato del ariete en el diálogo de arrasar un puente, sobre el exe y el RES parcheados, en
# unicorn.
# Uso: python prueba_ariete.py [carpeta]   (por defecto C:\Warlords3; armarla antes con build.py)
# Dibujo: corre 0x4954d0 (dibujo de los ítems del diálogo) con 0x4bbf20 interceptada y mira qué imagen pide.
# RES: corre el lector de registros del juego (0x4ed760) con la búsqueda (0x4dfdf0) y la lectura (0x4dfd20) del archivo
# sobre WAR3AV.RES, y mira el archivo y la imagen nuevos, los de siempre y los que no existen.
# Controles: ciudad, sitio, otro ítem del diálogo, registros vecinos sin cambios y el RES original (sin las entradas).
import os, sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

DIR = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3'
pe = pefile.PE(os.path.join(DIR, 'DarklordAV.exe')); BASE = pe.OPTIONAL_HEADER.ImageBase
img = bytes(pe.get_memory_mapped_image())
SIZE = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
STACK = 0x1f0000
BR_CODE, RAM_FILE, RAM_IMG = 0x2000, 165, 206

def maquina():
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(BASE, SIZE); mu.mem_write(BASE, img[:SIZE])
    mu.mem_map(0x100000, 0x100000)
    return mu

def dibujo(item, modo, indice):
    mu = maquina()
    mu.mem_write(0x572774, struct.pack('<h', modo)); mu.mem_write(0x572778, struct.pack('<h', indice))
    esp = STACK
    mu.mem_write(esp, struct.pack('<IIII', 0x100, item, 108, 87))
    for r, v in ((UC_X86_REG_ESI, 0x1234), (UC_X86_REG_EDI, 0x5678), (UC_X86_REG_EBX, 0x9abc), (UC_X86_REG_EBP, 0xdef0)):
        mu.reg_write(r, v)
    mu.reg_write(UC_X86_REG_ESP, esp)
    llamadas = []
    def gancho(mu, addr, size, _):
        sp = mu.reg_read(UC_X86_REG_ESP)
        ret, *a = struct.unpack('<4I', mu.mem_read(sp, 16))
        llamadas.append(tuple(a))
        mu.reg_write(UC_X86_REG_ESP, sp + 4); mu.reg_write(UC_X86_REG_EIP, ret)
    mu.hook_add(UC_HOOK_CODE, gancho, begin=0x4bbf20, end=0x4bbf20)
    mu.emu_start(0x4954d0, 0x100, count=2000)
    assert mu.reg_read(UC_X86_REG_ESP) == esp + 4
    for r, v in ((UC_X86_REG_ESI, 0x1234), (UC_X86_REG_EDI, 0x5678), (UC_X86_REG_EBX, 0x9abc), (UC_X86_REG_EBP, 0xdef0)):
        assert mu.reg_read(r) == v
    return llamadas

def registro(res, tipo, n, largo):
    """0x4ed760(tipo, 0, n, búfer) del juego sobre el archivo res; devuelve el registro o None."""
    data = open(res, 'rb').read()
    mu = maquina()
    OBJ, BUF = 0x5a6fc8, 0x150000
    mu.mem_write(OBJ + 0x130, struct.pack('<I', 1))
    pos = [0]
    def gancho(mu, addr, size, _):
        sp = mu.reg_read(UC_X86_REG_ESP)
        ret, a, b = struct.unpack('<III', mu.mem_read(sp, 12))
        assert mu.reg_read(UC_X86_REG_ECX) == OBJ + 0x28
        if addr == 0x4dfdf0:                                   # búsqueda (desplazamiento, 0 = inicio / 1 = actual)
            pos[0] = a if b == 0 else pos[0] + a; r = 0
        else:                                                  # lectura (búfer, cantidad)
            chunk = data[pos[0]:pos[0] + b]; mu.mem_write(a, chunk); pos[0] += len(chunk); r = len(chunk)
        mu.reg_write(UC_X86_REG_EAX, r)
        mu.reg_write(UC_X86_REG_ESP, sp + 12); mu.reg_write(UC_X86_REG_EIP, ret)
    for f in (0x4dfdf0, 0x4dfd20):
        mu.hook_add(UC_HOOK_CODE, gancho, begin=f, end=f)
    esp = STACK
    mu.mem_write(esp, struct.pack('<5I', 0x100, tipo, 0, n, BUF))
    mu.reg_write(UC_X86_REG_ESP, esp); mu.reg_write(UC_X86_REG_ECX, OBJ)
    mu.emu_start(0x4ed760, 0x100, count=200000)
    assert mu.reg_read(UC_X86_REG_ESP) == esp + 4 + 16
    return bytes(mu.mem_read(BUF, largo)) if mu.reg_read(UC_X86_REG_EAX) else None

mal = 0
def ver(nombre, r, esperado):
    global mal
    ok = r == esperado
    mal += not ok
    print('OK ' if ok else 'MAL', nombre, '->', r)

print('-- dibujo del diálogo de arrasar')
ver('puente', dibujo(2, 1, BR_CODE + (5 << 7) + 9), [(RAM_IMG, 108, 87)])
ver('puente, última fila', dibujo(2, 1, BR_CODE + (155 << 7) + 111), [(RAM_IMG, 108, 87)])
ver('control: ciudad', dibujo(2, 0, 3), [(0x99, 108, 87)])
ver('control: sitio', dibujo(2, 1, 40), [(0x99, 108, 87)])
ver('control: sitio alto', dibujo(2, 1, BR_CODE - 1), [(0x99, 108, 87)])
ver('control: otro ítem', dibujo(5, 1, BR_CODE + 9), [])

print('-- RES')
NUEVO = os.path.join(DIR, 'DATA', 'WAR3AV.RES')
ORIG = r'C:\Warlords3\DATA\War3.RES'
ver('el juego tiene ARMY\\orcs_ram.pcx', os.path.isfile(r'C:\Warlords3\ARMY\orcs_ram.pcx'), True)
def archivo(res, n):
    r = registro(res, 2, n, 60)
    return r and (struct.unpack_from('<I', r)[0], r[4:36].split(b'\0')[0].decode(), struct.unpack_from('<6I', r, 36))
def imagen(res, n):
    r = registro(res, 4, n, 32)
    return r and struct.unpack('<8i', r)
ver('archivo nuevo', archivo(NUEVO, RAM_FILE), (RAM_FILE, 'orcs_ram', (2, 1, 0, 0, 0, 6)))
ver('imagen nueva', imagen(NUEVO, RAM_IMG), (RAM_IMG, RAM_FILE, 0, 0, 0, 0, 128, 160))
ver('control: lightinf', archivo(NUEVO, 46), archivo(ORIG, 46))
ver('control: archivo 164', archivo(NUEVO, 164), archivo(ORIG, 164))
ver('control: imagen raze', imagen(NUEVO, 0x99), imagen(ORIG, 0x99))
ver('control: imagen 205', imagen(NUEVO, 205), imagen(ORIG, 205))
ver('control: tabla 3 (después de la 2)', registro(NUEVO, 3, 55, 52), registro(ORIG, 3, 55, 52))
ver('control: tabla 6 (después de la 4)', registro(NUEVO, 6, 132, 32), registro(ORIG, 6, 132, 32))
ver('control: archivo 166 no existe', archivo(NUEVO, RAM_FILE + 1), None)
ver('control: imagen 207 no existe', imagen(NUEVO, RAM_IMG + 1), None)
ver('control: el original no la tiene', imagen(ORIG, RAM_IMG), None)
print('MAL:', mal)
sys.exit(1 if mal else 0)
