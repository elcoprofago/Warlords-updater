# Prueba de juguete del renglón de habilidades del Army List (armab, 0x4a2c24) sobre el exe parcheado, en unicorn.
# Uso: python prueba_armylist.py [DarklordAV.exe]   (por defecto C:\Warlords3\DarklordAV.exe; armarlo antes con build.py)
# Corre desde 0x4a2c1a (texto ya armado en el búfer del marco) hasta la entrada de armrow, y mira el texto que le llega.
# Controles: unidad sin bonos, renglón que no es unidad, nombre parecido ("Landings"), texto que no entra, y los bytes
# del marco que siguen al búfer, que no se tienen que tocar.
import sys, struct, pefile, capstone
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

pe = pefile.PE(sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe'); BASE = pe.OPTIONAL_HEADER.ImageBase
img = bytes(pe.get_memory_mapped_image())
SIZE = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
ins = next(cs.disasm(img[0x4a2c24 - BASE:0x4a2c24 - BASE + 5], 0x4a2c24)); assert ins.mnemonic == 'jmp'
ARMAB = int(ins.op_str, 16)
ARMAB_CODE = img[ARMAB - BASE:ARMAB - BASE + 0x100]
ARMROW = [i for i in cs.disasm(ARMAB_CODE, ARMAB) if i.mnemonic == 'jmp' and int(i.op_str, 16) > 0x600000
          and not (ARMAB <= int(i.op_str, 16) < ARMAB + 0x100)][0]
ARMROW = int(ARMROW.op_str, 16)
STACK = 0x1f0000
NOSPEC = 'No Special Abilities'

def caso(bonos, texto, habil=0, slot=3, jugador=2):
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(BASE, SIZE); mu.mem_write(BASE, img[:SIZE])
    mu.mem_map(0x100000, 0x100000)
    rec = 0x53c410 + (jugador * 16 + min(slot, 15)) * 0xfc
    mu.mem_write(rec + 0xb2, b''.join(t.encode().ljust(9, b'\0')[:9] for t in (list(bonos) + [''] * 4)[:4]))
    mu.mem_write(rec + 0xe6, struct.pack('<H', habil))
    mu.mem_write(0x5730dc, struct.pack('<h', jugador))
    mu.mem_write(0x5730b0 + 5 * 2, struct.pack('<h', slot))
    esp = STACK
    marco = bytes(range(0x80, 0x80 + 0x70))
    mu.mem_write(esp, marco)
    mu.mem_write(esp + 0x14, texto.encode() + b'\0')
    mu.mem_write(esp + 0x74, struct.pack('<I', 5))
    antes = bytes(mu.mem_read(esp + 0x64, 0x10))
    mu.reg_write(UC_X86_REG_ESP, esp); mu.reg_write(UC_X86_REG_EBX, 100); mu.reg_write(UC_X86_REG_EBP, 50)
    mu.reg_write(UC_X86_REG_ESI, 0x1234); mu.reg_write(UC_X86_REG_EDI, 0x5678)
    mu.emu_start(0x4a2c1a, ARMROW, count=5000)
    assert mu.reg_read(UC_X86_REG_EIP) == ARMROW
    esp2 = mu.reg_read(UC_X86_REG_ESP)
    assert esp2 == esp - 0xc, hex(esp2)
    x, y, buf = struct.unpack('<III', mu.mem_read(esp2, 12))
    assert (x, y, buf) == (50, 100 + 0x1a, esp + 0x14), (x, y, hex(buf))
    assert (mu.reg_read(UC_X86_REG_ESI), mu.reg_read(UC_X86_REG_EDI)) == (0x1234, 0x5678)
    assert bytes(mu.mem_read(esp + 0x64, 0x10)) == antes, 'tocó el marco después del búfer'
    return bytes(mu.mem_read(buf, 0x50)).split(b'\0')[0].decode()

LARGO = 'A' * 62
casos = [
    (dict(bonos=('Hills', 'Landing'), texto=NOSPEC), 'Landing'),
    (dict(bonos=('CARRIER',), texto=NOSPEC), 'Carrier'),
    (dict(bonos=('carrier', 'Ice', 'landing'), texto=NOSPEC), 'Landing, Carrier'),
    (dict(bonos=('Landing',), texto='Flying', habil=1), 'Flying, Landing'),
    (dict(bonos=('Landing', 'Carrier'), texto='A' * 61, habil=1), 'A' * 61 + ', Landing, Carrier'),
    (dict(bonos=('Landing', 'Carrier'), texto=LARGO, habil=1), LARGO),                       # control: no entra
    (dict(bonos=('Hills', 'Ice'), texto=NOSPEC), NOSPEC),                                       # control: sin bonos
    (dict(bonos=('Landings',), texto=NOSPEC), NOSPEC),                                          # control: nombre parecido
    (dict(bonos=('Landing',), texto=NOSPEC, slot=16), NOSPEC),                                  # control: no es unidad
    (dict(bonos=('Landing',), texto=NOSPEC, slot=15, jugador=7), 'Landing'),                    # barco, último bando
]
mal = 0
for kw, esperado in casos:
    r = caso(**kw)
    ok = r == esperado
    mal += not ok
    print('OK ' if ok else 'MAL', kw['bonos'], repr(kw['texto'][:24]), '->', repr(r))
print('MAL:', mal)
sys.exit(1 if mal else 0)
