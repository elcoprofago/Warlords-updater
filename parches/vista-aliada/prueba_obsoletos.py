# Prueba de juguete del borrado de archivos obsoletos (ia_menu, llamada en 0x452c3b) sobre el exe parcheado, en unicorn.
# Uso: python prueba_obsoletos.py [DarklordAV.exe]   (por defecto C:\Warlords3\DarklordAV.exe; armarlo antes con build.py)
# DeleteFileA ([0x5a97c0]), el menú (0x4aab10) y GetPrivateProfileString (sin tanda: devuelve 0) son stubs que anotan
# lo que reciben. Tiene que borrar exactamente los tres obsoletos, antes del menú, con la pila y los registros intactos.
import sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

pe = pefile.PE(sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe'); BASE = pe.OPTIONAL_HEADER.ImageBase
img = bytes(pe.get_memory_mapped_image())
SIZE = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
assert img[0x452c3b - BASE] == 0xe8
IA_MENU = 0x452c40 + struct.unpack_from('<i', img, 0x452c3c - BASE)[0]
STACK = 0x200000; END = 0x1fff00; STUBS = 0x180000
DELETE, MENU, PROF = STUBS, STUBS + 0x10, STUBS + 0x20

mu = Uc(UC_ARCH_X86, UC_MODE_32)
mu.mem_map(BASE, SIZE); mu.mem_write(BASE, img[:SIZE])
mu.mem_map(STACK - 0x10000, 0x10000); mu.mem_map(STUBS, 0x1000)
mu.mem_write(DELETE, b'\x31\xc0\xc2\x04\x00')                # xor eax, eax; ret 4  (stdcall, falla: "no estaba")
mu.mem_write(MENU, b'\xc3')
mu.mem_write(PROF, b'\x31\xc0\xc2\x18\x00')                  # sin [Tanda]: 0
mu.mem_write(0x5a97c0, struct.pack('<I', DELETE))
calls = []
def code(mu, a, s, _):
    if a == END: mu.emu_stop()
    elif a == DELETE:
        p = struct.unpack('<I', mu.mem_read(mu.reg_read(UC_X86_REG_ESP) + 4, 4))[0]
        calls.append(bytes(mu.mem_read(p, 64)).split(b'\0')[0].decode('latin1'))
    elif a == MENU: calls.append('menú')
mu.hook_add(UC_HOOK_CODE, code)
# el menú original es 0x4aab10: se redirige al stub
mu.mem_write(0x4aab10, b'\xe9' + struct.pack('<i', MENU - 0x4aab15))
for imp in {struct.unpack_from('<I', img, o + 2)[0] for o in range(IA_MENU - BASE, IA_MENU - BASE + 0x200)
            if img[o:o + 2] == b'\xff\x15'} - {0x5a97c0}:
    mu.mem_write(imp, struct.pack('<I', PROF))

regs = {UC_X86_REG_EBX: 0x11, UC_X86_REG_ESI: 0x22, UC_X86_REG_EDI: 0x33, UC_X86_REG_EBP: 0x44}
for r, v in regs.items(): mu.reg_write(r, v)
sp = STACK - 0x100; mu.mem_write(sp, struct.pack('<I', END)); mu.reg_write(UC_X86_REG_ESP, sp)
mu.emu_start(IA_MENU, END, count=100000)

EXP = [r'TERRAIN\SUBTYPE\camo.STT', r'TERRAIN\SUBTYPE\nighmare.STT', r'TERRAIN\SUBTYPE\bridge.STT', 'menú']
print('llamadas:', calls)
assert calls == EXP, calls
assert mu.reg_read(UC_X86_REG_ESP) == sp + 4, 'pila desbalanceada'
assert all(mu.reg_read(r) == v for r, v in regs.items()), 'registros pisados'
assert r'TERRAIN\SUBTYPE\camouflg.STT' not in calls          # control: el bono actual no se borra
print('TODO OK')
