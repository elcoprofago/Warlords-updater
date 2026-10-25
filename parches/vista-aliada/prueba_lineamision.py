# Prueba de juguete de qb_line: la línea naranja del mapa hasta el objetivo de una misión (0x414090, caso del tipo 10
# en 0x41424a) con un puente como objetivo, en unicorn.
# Uso: python prueba_lineamision.py [DarklordAV.exe] [Darklord.exe]
#      (por defecto C:\Warlords3\DarklordAV.exe y el original C:\Warlords3\Darklord.exe; armar antes con build.py)
# Corre desde 0x41424a hasta 0x41426a, donde la función ya tiene en di la x y en ax la y del destino y apiló 0x48.
# Puente: la casilla de su código (0x2000 + y*128 + x), sin leer la tabla de sitios. Sitio: igual al original.
import sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_MEM_READ
from unicorn.x86_const import *

def load(path):
    pe = pefile.PE(path)
    return pe.OPTIONAL_HEADER.ImageBase, bytes(pe.get_memory_mapped_image()), (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
AV = load(sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe')
ORIG = load(sys.argv[2] if len(sys.argv) > 2 else r'C:\Warlords3\Darklord.exe')
QUEST, STACK, END = 0x100000, 0x200000, 0x41426a
SITES = [(12, 34), (40, 7), (63, 63)]

def run(exe, target):
    base, img, size = exe
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(base, size); mu.mem_write(base, img)
    mu.mem_map(QUEST, 0x1000); mu.mem_map(STACK - 0x10000, 0x10000)
    mu.mem_write(QUEST, struct.pack('<hhhh', 1, 1, 10, target))
    mu.mem_write(0x55acb4, struct.pack('<h', len(SITES)))
    for i, (x, y) in enumerate(SITES): mu.mem_write(0x55acb6 + i * 150, struct.pack('<hh', x, y))
    reads = []
    mu.hook_add(UC_HOOK_MEM_READ, lambda u, a, addr, n, v, d: reads.append(addr)
                if 0x55acb6 <= addr < 0x55acb6 + 0x2000 * 150 and addr >= 0x55acb6 + len(SITES) * 150 else None)
    mu.reg_write(UC_X86_REG_EDI, QUEST); mu.reg_write(UC_X86_REG_ESP, STACK - 0x100)
    mu.emu_start(0x41424a, END, count=200)
    esp = mu.reg_read(UC_X86_REG_ESP)
    return (mu.reg_read(UC_X86_REG_EIP), mu.reg_read(UC_X86_REG_EDI) & 0xffff, mu.reg_read(UC_X86_REG_EAX) & 0xffff,
            struct.unpack('<I', mu.mem_read(esp, 4))[0], esp, reads)

bad = 0
def check(nombre, ok, info=''):
    global bad
    print(('OK  ' if ok else 'MAL ') + nombre + ('' if ok else f'   [{info}]'))
    bad += not ok

for x, y in [(25, 30), (0, 0), (127, 5), (3, 120)]:
    r = run(AV, 0x2000 + (y << 7) + x)
    check(f'puente ({x},{y}): destino en su casilla, apila 0x48, sin leer fuera de la tabla de sitios',
          r[0] == END and (r[1], r[2], r[3]) == (x, y, 0x48) and r[4] == STACK - 0x104 and not r[5], r)
for i, (x, y) in enumerate(SITES):
    a, o = run(AV, i), run(ORIG, i)
    check(f'control: sitio {i}: igual al original ({x},{y})', a[:5] == o[:5] and a[1:3] == (x, y), (a, o))
print('TODO OK' if not bad else f'FALLAN {bad}')
