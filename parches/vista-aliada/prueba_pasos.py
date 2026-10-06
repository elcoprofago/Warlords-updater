# Prueba de juguete del tope de pasos del barco (bmvcap) sobre el exe parcheado, en unicorn.
# Uso: python prueba_pasos.py [DarklordAV.exe] [Darklord.exe]   (por defecto los de C:\Warlords3; armar antes con build.py)
# Cada lectura parcheada se corre en el exe nuevo con los pasos del registro tal cual, y la instrucción original en
# Darklord.exe con los pasos ya topeados a mano: los registros, los flags y la pila tienen que quedar iguales.
import sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import *

def load(path):
    pe = pefile.PE(path); base = pe.OPTIONAL_HEADER.ImageBase
    return base, bytes(pe.get_memory_mapped_image()), (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
NEW = load(sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe')
OLD = load(sys.argv[2] if len(sys.argv) > 2 else r'C:\Warlords3\Darklord.exe')

CAP = {(): None, ('LANDING',): 12, ('LANDING', 'CARRIER'): 20, ('CARRIER',): 24}
REGS = ('EAX', 'EBX', 'ECX', 'EDX', 'ESI', 'EDI', 'EBP', 'ESP', 'EFLAGS')
rec = lambda p, k: 0x53c410 + (p * 16 + k) * 0xfc

# (va, largo de la instrucción original, registro índice -> valor según (p, k), registros que valen 0 antes)
BOAT = lambda p, k: p * 0xfc0
OFF = lambda p, k: (p * 16 + k) * 0xfc
SITES = [
    (0x422b61, 8, 'EDI', BOAT, ()), (0x466463, 6, 'EDX', BOAT, ('ECX',)), (0x4667cb, 6, 'EDX', BOAT, ('EBX',)),
    (0x466976, 6, 'EBX', BOAT, ('EAX',)), (0x49dc8b, 8, 'EAX', BOAT, ()), (0x49de3e, 8, 'EAX', BOAT, ()),
    (0x4a62c1, 8, 'EAX', BOAT, ()), (0x4d34e0, 8, 'EAX', BOAT, ()),
    (0x43b773, 6, 'EAX', rec, ()), (0x455a25, 8, 'ESI', OFF, ()), (0x477d0d, 8, 'EDI', OFF, ()),
    (0x4781f6, 8, 'ECX', OFF, ()), (0x48a793, 8, 'EDX', OFF, ()),
    (0x4a2a7c, 7, 'ECX', lambda p, k: (p * 16 + k) * 63, ('EAX',)),
]
GENERIC = {0x43b773, 0x455a25, 0x477d0d, 0x4781f6, 0x48a793, 0x4a2a7c}

def run(exe, va, n, idxreg, idxval, zero, p, k, moves, bonos, flags):
    base, img, size = exe
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(base, size); mu.mem_write(base, img[:size])
    mu.mem_map(0x100000, 0x10000)
    r = rec(p, k)
    mu.mem_write(r + 0x9b, bytes([moves]))
    boat = rec(p, 15) + 0xb2
    mu.mem_write(boat, b''.join(b.encode() + b'\0' * (9 - len(b)) for b in ('Ice',) + bonos).ljust(36, b'\0'))
    esp = 0x108000
    mu.mem_write(esp - 0x40, bytes(range(0x80)))
    regs = dict(EAX=0x11223344, EBX=0x55667788, ECX=0x99aabbcc, EDX=0xddeeff01, ESI=0x02030405, EDI=0x06070809,
                EBP=0x0a0b0c0d, ESP=esp, EFLAGS=flags)
    for z in zero: regs[z] = 0
    regs[idxreg] = idxval
    for k_, v in regs.items(): mu.reg_write(globals()['UC_X86_REG_' + k_], v)
    mu.emu_start(va, va + n, count=5000)
    assert mu.reg_read(UC_X86_REG_EIP) == va + n, hex(mu.reg_read(UC_X86_REG_EIP))
    return {k_: mu.reg_read(globals()["UC_X86_REG_" + k_]) for k_ in REGS}, bytes(mu.mem_read(esp, 0x40))  # bajo esp es basura

casos = []   # (p, k, pasos, bonos, pasos esperados)
for bonos, cap in CAP.items():
    for moves in (30, 12, 24, 20, 255, 0):
        casos.append((1, 15, moves, bonos, moves if cap is None else min(moves, cap)))
casos += [(7, 15, 30, ('LANDING',), 12), (0, 15, 26, ('LANDING', 'CARRIER'), 20),     # bandos de los extremos
          (2, 15, 30, ('CARRIER', 'LANDING'), 20),                                     # orden de los bonos
          (2, 15, 30, ('carrier',), 24)]                                               # minúsculas
generic = [(1, 3, 30, ('LANDING', 'CARRIER'), 30), (1, 0, 30, ('LANDING',), 30),       # otra ranura: no cambia
           (1, 14, 30, ('CARRIER',), 30), (8, 15, 30, ('LANDING',), 30)]                # fuera de los bandos 0..7

mal = total = 0
for va, n, idxreg, idxf, zero in SITES:
    for p, k, moves, bonos, exp in casos + (generic if va in GENERIC else []):
        for flags in (0x2, 0x8d7):
            total += 1
            got = run(NEW, va, n, idxreg, idxf(p, k), zero, p, k, moves, bonos, flags)
            ref = run(OLD, va, n, idxreg, idxf(p, k), zero, p, k, exp, bonos, flags)
            if got != ref:
                mal += 1
                diff = {r: (hex(got[0][r]), hex(ref[0][r])) for r in REGS if got[0][r] != ref[0][r]}
                print(f'MAL {va:#x} p={p} k={k} pasos={moves} {"+".join(bonos) or "sin bonos"} -> esperado {exp}; '
                      f'{diff or "pila distinta"}')
# Control: el exe original tiene que dar distinto en un caso con tope (si no, la prueba no mide nada).
ctl = run(OLD, 0x49dc8b, 8, 'EAX', BOAT(1, 15), (), 1, 15, 30, ('LANDING',), 2)
ctl_ref = run(OLD, 0x49dc8b, 8, 'EAX', BOAT(1, 15), (), 1, 15, 12, ('LANDING',), 2)
ctl_ok = ctl != ctl_ref and (ctl[0]['EAX'] & 0xffff) == 30
print(f'control (original sin tope lee 30): {"ok" if ctl_ok else "MAL"}')
print(f'{total} corridas, ' + ('TODO OK' if not mal and ctl_ok else f'{mal} MAL'))
sys.exit(1 if mal or not ctl_ok else 0)
