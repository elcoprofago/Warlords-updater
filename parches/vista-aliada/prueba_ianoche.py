# Prueba de juguete de la pila de noche que espera de día (nt_wait de build.py, paso 5.4 de
# ia\PENDIENTE-ia-innovaciones.md), en unicorn. Uso: python prueba_ianoche.py [carpeta]   (por defecto C:\Warlords3)
# nt_wait se encuentra desde ai_ally (el call en al_orig, entre el push del registro de la pila y el test eax, eax).
# Controles que tienen que dar «no espera»: sin Day/Night, de noche, sin amenaza, blanco débil (menos de la mitad),
# mitad justa de ejércitos de noche, ejércitos muertos que no cuentan, héroe (cuenta en el total, nunca de noche).
import os, sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import *

DIR = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3'
SHOPT, RONDA, TIPOS, EJ = 0x53c3a5, 0x503328, 0x53c410, 0x54fe00
pe = pefile.PE(os.path.join(DIR, 'DarklordAV.exe'))
BASE, img = pe.OPTIONAL_HEADER.ImageBase, bytes(pe.get_memory_mapped_image())
pat = bytes.fromhex('535657 31c0 f605') .replace(b' ', b'') + struct.pack('<I', SHOPT) + b'\x02'
NT_WAIT = BASE + img.index(pat)
assert img.count(pat) == 1, 'nt_wait no es única'
STK, PILA, RET = 0x150000, 0x160000, 0x100

mal = 0
def ver(nombre, r, esperado):
    global mal
    ok = r == esperado
    mal += not ok
    print('OK ' if ok else 'MAL', nombre, '->', r)

def caso(ejs, fuerza, amenaza, daynight=True, ronda=7):
    # ejs: lista de (clase1, clase2, héroe, vivo); el ejército i + 1 es del bando 2, ranura i
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(0, 0x800000)
    mu.mem_write(BASE, img)
    mu.mem_write(SHOPT, bytes([2 if daynight else 0]))
    mu.mem_write(RONDA, struct.pack('<H', ronda))
    rec = bytearray(0x40)
    for i, (c1, c2, heroe, vivo) in enumerate(ejs):
        e = i + 1
        struct.pack_into('<h', rec, 0xc + 2 * i, e)
        slot = 0x10 if heroe else i
        mu.mem_write(EJ + e * 0x1c + 0x5e, struct.pack('<H', (2 << 5) | slot))
        mu.mem_write(EJ + e * 0x1c + 0x63, bytes([0x40 if vivo else 0]))
        if not heroe:
            t = TIPOS + (2 * 16 + i) * 0xfc
            mu.mem_write(t + 0xa0, c1.encode().ljust(9, b'\0')[:9] + c2.encode().ljust(9, b'\0')[:9])
    for i in range(len(ejs), 8):
        struct.pack_into('<h', rec, 0xc + 2 * i, -1)
    mu.mem_write(PILA, bytes(rec))
    sp = STK
    for v in (amenaza, fuerza, PILA, RET):
        sp -= 4; mu.mem_write(sp, struct.pack('<I', v))
    mu.reg_write(UC_X86_REG_ESP, sp)
    mu.reg_write(UC_X86_REG_EBX, 0x1111); mu.reg_write(UC_X86_REG_ESI, 0x2222); mu.reg_write(UC_X86_REG_EDI, 0x3333)
    mu.emu_start(NT_WAIT, RET, count=100000)
    assert (mu.reg_read(UC_X86_REG_EBX), mu.reg_read(UC_X86_REG_ESI), mu.reg_read(UC_X86_REG_EDI)) == (0x1111, 0x2222, 0x3333)
    return mu.reg_read(UC_X86_REG_EAX)

U, H, N = ('undead', 'none', False, True), ('human', 'none', False, True), ('none', 'none', True, True)
print('nt_wait en', hex(NT_WAIT))
ver('3 undead de 4, de día, parejo: espera', caso([U, U, U, H], 20, 15), 1)
ver('clase en la segunda ranura (Demon, mayúscula)', caso([('elf', 'Demon', False, True)] * 3 + [H], 20, 15), 1)
ver('monster', caso([('monster', 'none', False, True)] * 2 + [H], 20, 15), 1)
ver('control: sin Day/Night', caso([U, U, U, H], 20, 15, daynight=False), 0)
ver('control: de noche (vuelta par)', caso([U, U, U, H], 20, 15, ronda=8), 0)
ver('control: sin amenaza', caso([U, U, U, H], 20, 0), 0)
ver('control: blanco débil (9 < 20/2)', caso([U, U, U, H], 20, 9), 0)
ver('borde: amenaza justo la mitad (10)', caso([U, U, U, H], 20, 10), 1)
ver('amenaza mayor que la pila', caso([U, U, U, H], 20, 60), 1)
ver('control: mitad justa (2 de 4)', caso([U, U, H, H], 20, 15), 0)
ver('control: undead muertos no cuentan', caso([U, ('undead', 'none', False, False), ('undead', 'none', False, False), H], 20, 15), 0)
ver('héroe cuenta en el total: 2 undead + héroe', caso([U, U, N], 20, 15), 1)
ver('control: 1 undead + héroe', caso([U, N], 20, 15), 0)
ver('control: "undeadx" no es undead', caso([('undeadx', 'none', False, True)] * 3, 20, 15), 0)
print('TODO OK' if not mal else f'{mal} MAL')
sys.exit(1 if mal else 0)
