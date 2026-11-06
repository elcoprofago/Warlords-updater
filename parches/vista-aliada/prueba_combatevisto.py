# Prueba de juguete del combate visto por el atacado (cv_chk de build.py) sobre el exe parcheado, en unicorn.
# Uso: python prueba_combatevisto.py [carpeta]   (por defecto C:\Warlords3; armarla antes con build.py)
# Corre desde 0x469f5c (después de la batalla) hasta la rama del atacante (0x469f65) o la del que no ataca (0x469fa9),
# con la ventana de combate (0x405a10) interceptada: anota sus argumentos y gasta azar del juego.
# Casos: el atacado en su PC ve la ventana con los mismos argumentos que el original le pasa al atacante y el azar queda
# como estaba; controles: el atacante sigue por su rama sin cambios; una sola PC; defensor de la computadora; defensor
# humano de otra PC; defensor que no es el jugador de esta PC; registros intactos al seguir.
import os, sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

DIR = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3'
pe = pefile.PE(os.path.join(DIR, 'DarklordAV.exe')); BASE = pe.OPTIONAL_HEADER.ImageBase
img = bytes(pe.get_memory_mapped_image())
SIZE = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
STACK, FICHA, RES = 0x1f0000, 0x150000, 0x160000
LOCAL, MACHINES, MACHINE, SEED, RESEED = 0x537ce8, 0x5899fa, 0x5899fc, 0x500bf4, 0x500bf8
SIDE, SIDE_HUMAN, SIDE_MACHINE = 0x1f8, 0x536c12, 0x536b33
ATK_BRANCH, OTHER_BRANCH = 0x469f65, 0x469fa9

mal = 0
def ver(nombre, r, esperado):
    global mal
    ok = r == esperado
    mal += not ok
    print('OK ' if ok else 'MAL', nombre, '->', r)

def correr(atacante=1, defensor=2, local=2, maquinas=2, maquina=1, def_humano=True, def_maquina=1):
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(BASE, SIZE); mu.mem_write(BASE, img[:SIZE])
    mu.mem_map(0x100000, 0x100000)
    mu.mem_write(LOCAL, struct.pack('<h', local))
    mu.mem_write(MACHINES, struct.pack('<h', maquinas))
    mu.mem_write(MACHINE, struct.pack('<h', maquina))
    mu.mem_write(SIDE_HUMAN + defensor * SIDE, struct.pack('<h', -1 if def_humano else 0))
    mu.mem_write(SIDE_MACHINE + defensor * SIDE, bytes([def_maquina]))
    mu.mem_write(SEED, struct.pack('<I', 0x1234)); mu.mem_write(RESEED, struct.pack('<I', 0))
    mu.mem_write(FICHA, bytes([atacante, defensor]))
    llamadas = []
    def ventana(mu, a, size, _):
        sp = mu.reg_read(UC_X86_REG_ESP)
        ret, *args = struct.unpack('<7I', mu.mem_read(sp, 28))
        llamadas.append(tuple(args))
        mu.mem_write(SEED, struct.pack('<I', 0x9999)); mu.mem_write(RESEED, struct.pack('<I', 1))   # gasta azar
        mu.reg_write(UC_X86_REG_ESP, sp + 4); mu.reg_write(UC_X86_REG_EIP, ret)
    mu.hook_add(UC_HOOK_CODE, ventana, begin=0x405a10, end=0x405a10)
    regs = {UC_X86_REG_ESI: atacante, UC_X86_REG_EDI: atacante, UC_X86_REG_EBX: FICHA, UC_X86_REG_EBP: RES,
            UC_X86_REG_ESP: STACK, UC_X86_REG_ECX: 0x11, UC_X86_REG_EDX: 0x22, UC_X86_REG_EAX: 0x33}
    for r, v in regs.items(): mu.reg_write(r, v)
    fin = []
    def parar(mu, a, size, _): fin.append(a); mu.emu_stop()
    mu.hook_add(UC_HOOK_CODE, parar, begin=ATK_BRANCH, end=ATK_BRANCH)
    mu.hook_add(UC_HOOK_CODE, parar, begin=OTHER_BRANCH, end=OTHER_BRANCH)
    mu.emu_start(0x469f5c, 0, count=2000)
    intactos = all(mu.reg_read(r) == v for r, v in regs.items())
    azar = struct.unpack('<II', mu.mem_read(SEED, 4) + mu.mem_read(RESEED, 4))
    return fin[0] if fin else None, llamadas, azar, intactos

a = 1
esperado = (a, FICHA, RES, 0x569910 + 23 * a, 0x5699c8 + 23 * a, 0x56e988 + 31 * a)
ver('atacado en su PC: ventana, sigue por la rama del que no ataca, azar intacto, registros intactos',
    correr(), (OTHER_BRANCH, [esperado], (0x1234, 0), True))
ver('control: el atacante sigue por su rama original, sin ventana extra',
    correr(local=1)[:2], (ATK_BRANCH, []))
ver('control: una sola PC (un jugador o turnos alternados en la misma PC)', correr(maquinas=1)[:2], (OTHER_BRANCH, []))
ver('control: defensor de la computadora', correr(def_humano=False)[:2], (OTHER_BRANCH, []))
ver('control: defensor humano de otra PC', correr(def_maquina=0)[:2], (OTHER_BRANCH, []))
ver('control: el defensor no es el jugador de esta PC', correr(local=3)[:2], (OTHER_BRANCH, []))
ver('control: casilla sin dueño (defensor -1)', correr(defensor=0xff)[:2], (OTHER_BRANCH, []))
print('MAL:', mal)
sys.exit(1 if mal else 0)
