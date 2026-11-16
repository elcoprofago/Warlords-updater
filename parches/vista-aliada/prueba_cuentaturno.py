# Prueba de juguete de la cuenta regresiva del turno en el mapa (cr_tick de build.py) sobre el exe parcheado, en unicorn.
# Uso: python prueba_cuentaturno.py [carpeta]   (por defecto C:\Warlords3; armarla antes con build.py)
# Entra a 0x4c1074 (el control del reloj del mapa con ms que quedan en ecx) y anota los sonidos (0x4465e0) y los
# cursores (0x4ddfa0). Controles: con más de 5 s no suena; en otra PC (no es su turno) no suena; en pausa no suena;
# el número del cursor es el de los segundos; el original sigue en 0x4c1079 con esi = 1000.
import os, sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

DIR = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3'
pe = pefile.PE(os.path.join(DIR, 'DarklordAV.exe')); BASE = pe.OPTIONAL_HEADER.ImageBase
img = bytes(pe.get_memory_mapped_image())
SIZE = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
TEXT = b'Voting in progress: game paused\0'
PZ_ON = BASE + img.index(TEXT) + len(TEXT)
GETTICK = 0x5a97f8
STUB, STACK = 0x300000, 0x1f0000

mal = 0
def ver(nombre, r, esperado):
    global mal
    ok = r == esperado
    mal += not ok
    print('OK ' if ok else 'MAL', nombre, '->', r)

class PC:
    def __init__(self, turno=2, yo=2):
        mu = self.mu = Uc(UC_ARCH_X86, UC_MODE_32)
        mu.mem_map(BASE, SIZE); mu.mem_write(BASE, img[:SIZE])
        mu.mem_map(0x100000, 0x100000); mu.mem_map(STUB, 0x1000)
        mu.mem_write(STUB, b'\xc3'); mu.mem_write(GETTICK, struct.pack('<I', STUB))
        mu.mem_write(0x537ce8, struct.pack('<h', turno)); mu.mem_write(0x560b20, struct.pack('<h', yo))
        mu.mem_write(0x4fb6c4, b'\0'); mu.mem_write(0x589814, struct.pack('<I', 0x4242))
        self.t, self.sonidos, self.cursores, self.esi = 1000000, [], [], None
        mu.hook_add(UC_HOOK_CODE, self.gancho)

    def gancho(self, mu, a, size, _):
        sp = mu.reg_read(UC_X86_REG_ESP)
        r = lambda k: struct.unpack('<i', mu.mem_read(sp + 4 * k, 4))[0]
        if a == STUB:
            mu.reg_write(UC_X86_REG_EAX, self.t)
        elif a == 0x4465e0:
            self.sonidos.append(r(1)); mu.reg_write(UC_X86_REG_ESP, sp + 4); mu.reg_write(UC_X86_REG_EIP, r(0))
        elif a == 0x4ddfa0:
            assert mu.reg_read(UC_X86_REG_ECX) == 0x4242
            self.cursores.append(r(1)); mu.reg_write(UC_X86_REG_ESP, sp + 8); mu.reg_write(UC_X86_REG_EIP, r(0))
        elif a == 0x4c1079:
            self.esi = mu.reg_read(UC_X86_REG_ESI); mu.emu_stop()

    def tic(self, quedan, avanza=50):
        self.t += avanza
        self.mu.reg_write(UC_X86_REG_ESP, STACK); self.mu.reg_write(UC_X86_REG_ECX, quedan)
        self.mu.emu_start(0x4c1074, 0)

p = PC()
p.tic(9000); p.tic(5000)
ver('con 5 s o más no suena', (p.sonidos, p.cursores), ([], []))
ver('el original sigue con esi = 1000', p.esi, 1000)
for q in (4999, 4900, 3999, 2500, 1000, 999, 0):
    p.tic(q)
ver('suena una vez por segundo', p.sonidos, [0x14] * 5)
ver('cursor con el número', p.cursores, [0x15, 0x14, 0x13, 0x12, 0x11])
p.tic(500, avanza=300)
ver('repone el cursor cada 200 ms sin volver a sonar', (len(p.sonidos), p.cursores[-1]), (5, 0x11))

o = PC(turno=3, yo=2)
o.tic(3000)
ver('otra PC (no es su turno) no suena', (o.sonidos, o.cursores), ([], []))

z = PC(); z.mu.mem_write(PZ_ON, b'\2')
z.tic(3000)
ver('en pausa no suena', (z.sonidos, z.cursores), ([], []))

print('TODO OK' if not mal else f'{mal} MAL')
sys.exit(1 if mal else 0)
