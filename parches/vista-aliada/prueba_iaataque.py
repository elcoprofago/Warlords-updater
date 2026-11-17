# Prueba de juguete del corte de ataques perdidos (ap_gate de build.py, paso 6.2 de ia\PENDIENTE-ia-innovaciones.md),
# en unicorn. Uso: python prueba_iaataque.py [carpeta]   (por defecto E:\Warlords-TEST\Warlords3)
# ap_gate se encuentra por el call que lo reemplaza en 0x4c4de7. 0x440be0 (ciudad de la casilla), 0x4648d0 (la orden de
# atacar) e ia_evt se reemplazan por stubs que anotan si se llamaron.
# Casos que tienen que cortar (devuelve 0, evento 45, sin orden): grupo con menos de la mitad de la fuerza. Controles
# que tienen que dar la orden: mitad justa, ciudad, sin IA.INI, color en original, humano, defensores propios, muertos
# o en otra casilla.
import os as _os, sys as _sys; _sys.path.append(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..'))  # para encontrar juego_pruebas.py
from juego_pruebas import W3  # carpeta del juego de pruebas: se cambia solo ahi
import os, sys, struct, pefile, capstone
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

DIR = sys.argv[1] if len(sys.argv) > 1 else W3
EJ, NEJ, GRP, CTRL = 0x54fe00, 0x54fe50, 0x56ea94, 0x536c12
pe = pefile.PE(os.path.join(DIR, 'DarklordAV.exe'))
BASE, img = pe.OPTIONAL_HEADER.ImageBase, bytes(pe.get_memory_mapped_image())
c = img[0x4c4de7 - BASE:0x4c4de7 - BASE + 5]
assert c[0] == 0xe8, 'el call de 0x4c4de7 no está parcheado'
AP = 0x4c4dec + struct.unpack('<i', c[1:])[0]
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
ins = list(md.disasm(img[AP - BASE:AP - BASE + 0x200], AP))
cmps = [i.op_str for i in ins if i.mnemonic == 'cmp' and i.op_str.startswith('byte ptr [')]
IA_ON = int(cmps[0].split('[')[1].split(']')[0], 16)                             # cmp byte ptr [ia_on], 0
IA_MODE = int(cmps[1].split('+ ')[1].split(']')[0], 16)                          # cmp byte ptr [ebx + ia_mode], 1
pos = next(k for k, i in enumerate(ins) if i.mnemonic == 'push' and i.op_str == '0x2d')   # push 45 (AP_EVT)
EVT = int(ins[pos + 1].op_str, 16)                                               # call ia_evt
STK, RET = 0x150000, 0x100
P, X, Y = 2, 10, 10

mal = 0
def ver(nombre, r, esperado):
    global mal
    ok = r == esperado
    mal += not ok
    print('OK ' if ok else 'MAL', nombre, '->', r)

def ej(mu, e, dueno, fuerza, vida, x, y, vivo=True, ranura=0):
    mu.mem_write(EJ + e * 0x1c + 0x52, struct.pack('<hh', x, y))
    mu.mem_write(EJ + e * 0x1c + 0x5e, struct.pack('<H', ranura | dueno << 5 | fuerza << 9 | vida << 13))
    mu.mem_write(EJ + e * 0x1c + 0x63, bytes([0x40 if vivo else 0]))

def caso(grupo, defensores, ciudad=-1, ia_on=1, modo=1, control=0):
    # grupo: lista de (fuerza, vida, vivo) del bando P; defensores: (dueño, fuerza, vida, x, y, vivo)
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(0, 0x800000)
    mu.mem_write(BASE, img)
    mu.mem_write(IA_ON, bytes([ia_on])); mu.mem_write(IA_MODE + P, bytes([modo]))
    mu.mem_write(CTRL + P * 0x1f8, struct.pack('<h', control))
    mu.mem_write(0x440be0, b'\xb8' + struct.pack('<i', ciudad) + b'\xc3')       # mov eax, ciudad; ret
    mu.mem_write(0x4648d0, b'\xb8\x01\x00\x00\x00\xc3')                          # mov eax, 1; ret
    mu.mem_write(EVT, b'\xc3')
    e = 1
    lista = []
    for f, v, vivo in grupo:
        ej(mu, e, P, f, v, X - 1, Y, vivo); lista.append(e); e += 1
    for d, f, v, x, y, vivo in defensores:
        ej(mu, e, d, f, v, x, y, vivo); e += 1
    mu.mem_write(NEJ, struct.pack('<h', e))
    g = GRP + P * 0x4f0
    mu.mem_write(g, b''.join(struct.pack('<h', a) for a in lista)); mu.mem_write(g + 0x14, struct.pack('<h', len(lista)))
    llamadas = {'orden': 0, 'evt': None}
    def hook(mu, addr, size, _):
        if addr == 0x4648d0: llamadas['orden'] += 1
        if addr == EVT:
            sp = mu.reg_read(UC_X86_REG_ESP)
            llamadas['evt'] = struct.unpack('<5i', mu.mem_read(sp + 4, 20))
    mu.hook_add(UC_HOOK_CODE, hook, begin=0x4648d0, end=0x4648d0)
    mu.hook_add(UC_HOOK_CODE, hook, begin=EVT, end=EVT)
    sp = STK
    for v in (Y, X, P, RET):
        sp -= 4; mu.mem_write(sp, struct.pack('<I', v))
    mu.reg_write(UC_X86_REG_ESP, sp)
    mu.reg_write(UC_X86_REG_EBX, 0x1111); mu.reg_write(UC_X86_REG_ESI, 0x2222); mu.reg_write(UC_X86_REG_EDI, 0x3333)
    mu.reg_write(UC_X86_REG_EBP, 0x4444); mu.reg_write(UC_X86_REG_EAX, 0x5555)
    mu.emu_start(AP, RET, count=200000)
    assert (mu.reg_read(UC_X86_REG_EBX), mu.reg_read(UC_X86_REG_ESI), mu.reg_read(UC_X86_REG_EDI),
            mu.reg_read(UC_X86_REG_EBP)) == (0x1111, 0x2222, 0x3333, 0x4444), 'registros no preservados'
    assert mu.reg_read(UC_X86_REG_ESP) == sp + 4
    return 'orden' if llamadas['orden'] else ('corta', llamadas['evt'], mu.reg_read(UC_X86_REG_EAX))

G2 = [(3, 2, True)] * 2                      # 12
D3 = [(5, 5, 3, X, Y, True)] * 3             # 45
print('ap_gate en', hex(AP), 'ia_on', hex(IA_ON), 'ia_mode', hex(IA_MODE), 'ia_evt', hex(EVT))
ver('12 contra 45: corta', caso(G2, D3), ('corta', (45, P, X, Y, 12045), 0))
ver('control: 24 contra 45 (más de la mitad)', caso(G2 * 2, D3), 'orden')
ver('borde: 2 × 15 = 30 contra 30', caso([(5, 3, True)], [(5, 5, 3, X, Y, True)] * 2), 'orden')
ver('borde: 2 × 14 = 28 contra 30 corta', caso([(7, 2, True)], [(5, 5, 3, X, Y, True)] * 2),
    ('corta', (45, P, X, Y, 14030), 0))
ver('control: ciudad', caso(G2, D3, ciudad=3), 'orden')
ver('control: sin IA.INI', caso(G2, D3, ia_on=0), 'orden')
ver('control: color en original', caso(G2, D3, modo=0), 'orden')
ver('control: humano', caso(G2, D3, control=-1), 'orden')
ver('control: defensores propios no cuentan', caso(G2, [(P, 5, 3, X, Y, True)] * 3), 'orden')
ver('control: defensores muertos no cuentan', caso(G2, [(5, 5, 3, X, Y, False)] * 3), 'orden')
ver('control: defensores en otra casilla', caso(G2, [(5, 5, 3, X + 1, Y, True)] * 3), 'orden')
ver('muerto del grupo no suma: 6 contra 15', caso([(3, 2, True), (7, 7, False)], [(5, 5, 3, X, Y, True)]),
    ('corta', (45, P, X, Y, 6015), 0))
ver('control: el mismo vivo suma (55 contra 15)', caso([(3, 2, True), (7, 7, True)], [(5, 5, 3, X, Y, True)]), 'orden')
print('TODO OK' if not mal else f'{mal} MAL')
sys.exit(1 if mal else 0)
