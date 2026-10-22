# Prueba de juguete de war3ed_av.exe (editor_av.py), en unicorn.
# Uso: python prueba_editor.py [carpeta]   (por defecto C:\Warlords3; la que se le pasó a build.py)
# Las llamadas que llenaban los combos de bonos de Edit Army Data y Edit Hero Data se corren con un combo de mentira:
# 0x428d60 (llenar con los subtipos) y SendMessageA se reemplazan por versiones en Python sobre una lista.
# Esperado: movimiento sin bridge ni trap; combate sin landing, carrier, cabotage ni bridge (sin distinguir
# mayúsculas); el resto, incluidos trap en combate y landing en movimiento, queda. Control: los subtipos de Edit
# Terrain siguen llamando a 0x428d60 y la entrada 14 de habilidades dice "Bridge +N".
import os, sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

DIR = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3'
pe = pefile.PE(os.path.join(DIR, 'war3ed_av.exe'))
img = pe.get_memory_mapped_image()
SUBTIPOS = ['bridge', 'Cabotage', 'carrier', 'LANDING', 'trap', 'water', 'woods', 'bridges', 'fly']
COMBO, STUB, STACK, RET = 0x100000, 0x101000, 0x1f0000, 0x1e0000

def correr(site):
    destino = site + 5 + struct.unpack_from('<i', img, site - 0x400000 + 1)[0]
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(0x400000, (len(img) + 0xfff) & ~0xfff); mu.mem_write(0x400000, img)
    mu.mem_map(0x100000, 0x100000)
    mu.mem_write(COMBO + 0x1c, struct.pack('<I', 0x4242))
    mu.mem_write(0x48fad0, struct.pack('<I', STUB)); mu.mem_write(STUB, b'\xc2\x10\x00')    # ret 16
    mu.mem_write(0x428d60, b'\xc3')
    lista = []
    def gancho(mu, addr, size, _):
        sp = mu.reg_read(UC_X86_REG_ESP)
        if addr == 0x428d60:
            assert struct.unpack('<I', mu.mem_read(sp + 4, 4))[0] == COMBO
            lista[:] = SUBTIPOS; mu.reg_write(UC_X86_REG_EAX, len(lista))
        elif addr == STUB:
            h, msg, wp, lp = struct.unpack('<IIii', mu.mem_read(sp + 4, 16))
            assert h == 0x4242
            if msg == 0x158:
                nom = bytes(mu.mem_read(lp, 32)).split(b'\0')[0].decode().lower()
                r = next((i for i, n in enumerate(lista) if n.lower() == nom), -1)
            elif msg == 0x144:
                del lista[wp]; r = len(lista)
            else:
                raise AssertionError(hex(msg))
            mu.reg_write(UC_X86_REG_EAX, r & 0xffffffff)
    mu.hook_add(UC_HOOK_CODE, gancho, begin=0x428d60, end=0x428d60)
    mu.hook_add(UC_HOOK_CODE, gancho, begin=STUB, end=STUB)
    mu.mem_write(STACK, struct.pack('<II', RET, COMBO))
    for r, v in ((UC_X86_REG_ESP, STACK), (UC_X86_REG_ESI, 0x5151), (UC_X86_REG_EDI, 0x6161), (UC_X86_REG_EBX, 0x7171),
                 (UC_X86_REG_EBP, 0x8181)):
        mu.reg_write(r, v)
    mu.emu_start(destino, RET, count=20000)
    regs = tuple(mu.reg_read(r) for r in (UC_X86_REG_ESP, UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBX, UC_X86_REG_EBP))
    return lista, mu.reg_read(UC_X86_REG_EAX), regs == (STACK + 4, 0x5151, 0x6161, 0x7171, 0x8181)

MOV = [n for n in SUBTIPOS if n.lower() not in ('bridge', 'trap')]
COM = [n for n in SUBTIPOS if n.lower() not in ('landing', 'carrier', 'cabotage', 'bridge')]
SITIOS = {0x41453e: MOV, 0x41454f: MOV, 0x414560: MOV, 0x41456f: MOV, 0x414580: COM,
          0x41d3d8: MOV, 0x41d3e9: MOV, 0x41d3fa: MOV, 0x41d409: MOV, 0x41d41a: COM}
mal = 0
for site, esperado in SITIOS.items():
    lista, n, regs = correr(site)
    ok = lista == esperado and n == len(esperado) and regs
    mal += not ok
    print(f'{"OK " if ok else "MAL"} {site:#x}: {lista} (devuelve {n}, registros {"bien" if regs else "MAL"})')
ctl = [site + 5 + struct.unpack_from('<i', img, site - 0x400000 + 1)[0] for site in (0x43d9e7, 0x43d9f8, 0x43da07)]
ok = ctl == [0x428d60] * 3
mal += not ok
print(f'{"OK " if ok else "MAL"} control: Edit Terrain sigue con la lista completa')
raw = open(os.path.join(DIR, 'war3ed_av.exe'), 'rb').read()
ok = raw[0x9b6eb:0x9b6eb + 23] == b'X\x04\x03\x04\x0f\x00\x00\x00Bridge +N\x00\x00\x00\x00\x00\x00' and b'Giantslayer' in raw
mal += not ok
print(f'{"OK " if ok else "MAL"} habilidad 14 de Edit Army Data = "Bridge +N" (los héroes y objetos conservan Giantslayer)')
print('MAL:', mal)
sys.exit(1 if mal else 0)
