# Prueba emulada del evento 50 (rfsail, paso 5.6 de ia\PENDIENTE-ia-innovaciones): en el paso que embarca (0x49cdc7),
# un grupo de la computadora con "Raft" que quedó embarcado viniendo de tierra anota de dónde zarpó: 0 costa
# cualquiera, 1 ciudad, 2 punto de transbordo. Controles: sin IA.INI, humano, sin "Raft", grupo no embarcado, salida
# desde el agua (ya navegaba). En todos los casos el paso sigue a crfollow y sale en 0x49cdce con los registros intactos.
# Uso: python prueba_balsazarpa.py [DarklordAV.exe]
import os as _os, sys as _sys; _sys.path.append(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..'))
from juego_pruebas import W3
import sys, struct, pefile, capstone
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

pe = pefile.PE(sys.argv[1] if len(sys.argv) > 1 else W3 + r'\DarklordAV.exe'); BASE = pe.OPTIONAL_HEADER.ImageBase
img = bytes(pe.get_memory_mapped_image())
SIZE = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
ins = list(cs.disasm(img[0x49cdc7 - BASE:0x49cdc7 - BASE + 5], 0x49cdc7)); assert ins[0].mnemonic == 'jmp'
RFSAIL = int(ins[0].op_str, 16)
body = list(cs.disasm(img[RFSAIL - BASE:RFSAIL - BASE + 0x200], RFSAIL))
assert body[0].mnemonic in ('pushad', 'pushal') and body[1].mnemonic == 'cmp', 'rfsail no está en 0x49cdc7'
IA_ON = int(body[1].op_str.split('[')[1].split(']')[0], 16)
fin_rf = next(k for k, i in enumerate(body) if i.mnemonic == 'jmp' and i.op_str.startswith('0x')
              and not BASE <= int(i.op_str, 16) - RFSAIL + BASE < BASE + 0x100)   # el jmp final a crfollow
calls = [int(i.op_str, 16) for i in body[:fin_rf] if i.mnemonic == 'call']
IA_EVT = [c for c in calls if c not in (0x440be0, 0x4a6610)][-1]
SENT, P, SIDE_HUMAN = 0x1ff000, 1, 0x536c12
REG = ('EAX', 'EBX', 'ECX', 'EDX', 'ESI', 'EDI', 'EBP')

def caso(bono='Raft', ia=1, humano=False, emb=True, A_agua=False, ciudad=False, transb=False):
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(BASE, SIZE); mu.mem_write(BASE, img[:SIZE]); mu.mem_map(0x100000, 0x100000)
    for q in range(8):
        mu.mem_write(0x53c410 + (q * 16 + 15) * 0xfc + 0xb2, bono.encode().ljust(9, b'\0') + bytes(27))
        mu.mem_write(SIDE_HUMAN + q * 0x1f8, struct.pack('<h', -1 if humano and q == P else 0))
    mu.mem_write(IA_ON, bytes([ia]))
    mu.mem_write(0x440be0, b'\xb8' + struct.pack('<i', 3 if ciudad else -1) + b'\xc3')   # ciudad en A o no
    mu.mem_write(0x4a6610, b'\xb8' + struct.pack('<i', 1 if transb else 0) + b'\xc3')
    mu.mem_write(IA_EVT, b'\xc3')   # se registra en el hook, sin abrir IA_EVT.CSV
    mu.mem_write(0x503e06, b'\x08')
    mu.mem_write(0x535f0c, struct.pack('<h', 0)); mu.mem_write(0x535f0c + 0x58, struct.pack('<h', 1))
    Ax, Ay = 10, 10
    mu.mem_write(0x503e58 + ((Ay * 10) << 8) + Ax * 10, struct.pack('<H', 1 if A_agua else 0))
    mu.mem_write(0x572990, struct.pack('<h', Ax)); mu.mem_write(0x572994, struct.pack('<h', Ay))
    g = P * 0x4f0   # grupo de 2 ejércitos sin enlace de convoy (crfollow sale enseguida)
    for i in (1, 2): mu.mem_write(i * 0x1c + 0x54fe52, struct.pack('<hh', 11, 10))
    mu.mem_write(g + 0x56ea94, struct.pack('<8h', 1, 2, 0, 0, 0, 0, 0, 0))
    mu.mem_write(g + 0x56eaa8, struct.pack('<hBB', 2, 8 if emb else 0, 0))
    entry = 0x150000
    mu.mem_write(entry, struct.pack('<hbbhhhh', 0, P, 2, 11, 10, 0, 1))
    esp = 0x180000; mu.mem_write(esp, bytes(0x14) + struct.pack('<I', SENT))
    regs = dict(EAX=0x11, EBX=0x1234, ECX=0x22, EDX=0x33, ESI=entry, EDI=entry + 4, EBP=0x9abc)
    for k, v in dict(regs, ESP=esp).items(): mu.reg_write(globals()['UC_X86_REG_' + k], v)
    ev, fin = [], {}
    def hook(uc, addr, size, _):
        if addr == IA_EVT:
            sp = uc.reg_read(UC_X86_REG_ESP); ev.append(struct.unpack('<5i', uc.mem_read(sp + 4, 20)))
        if addr in (0x49cdce, SENT): fin['at'] = addr; uc.emu_stop()
    mu.hook_add(UC_HOOK_CODE, hook)
    mu.emu_start(0x49cdc7, 0, count=2_000_000)
    out = {k: mu.reg_read(globals()['UC_X86_REG_' + k]) for k in REG + ('ESP',)}
    ok = (fin.get('at') == 0x49cdce and out['ESP'] == esp + 0x14 and out['ECX'] & 0xffff == 10
          and all(out[k] == regs[k] for k in ('EAX', 'EBX', 'EDX', 'ESI', 'EDI', 'EBP')))
    return ev, ok

mal = 0
def check(nombre, kw, esperado):
    global mal
    ev, ok = caso(**kw)
    bien = ok and ev == esperado
    mal += not bien
    print(f'{"OK " if bien else "MAL"} {nombre}' + ('' if bien else f'   {ev} {ok}'))

check('zarpa de una costa cualquiera -> 50, n = 0', {}, [(50, P, 10, 10, 0)])
check('zarpa de una ciudad -> 50, n = 1', dict(ciudad=True), [(50, P, 10, 10, 1)])
check('zarpa de un punto de transbordo -> 50, n = 2', dict(transb=True), [(50, P, 10, 10, 2)])
check('control: sin IA.INI', dict(ia=0), [])
check('control: bando humano', dict(humano=True), [])
check('control: barco sin "Raft" (Landing)', dict(bono='Landing'), [])
check('control: grupo no embarcado (desembarcó)', dict(emb=False), [])
check('control: ya navegaba (sale del agua)', dict(A_agua=True), [])
print('TODO OK' if not mal else f'{mal} MAL'); sys.exit(1 if mal else 0)
