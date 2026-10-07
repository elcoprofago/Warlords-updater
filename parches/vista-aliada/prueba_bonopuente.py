# Prueba de juguete del Combat Bonus "Bridge" (gancho bridgecb) sobre el exe parcheado, en unicorn.
# Uso: python prueba_bonopuente.py [DarklordAV.exe] [Darklord.exe] [partida.SAV]
#      (por defecto los de C:\Warlords3 y Saves\Aliados03.SAV; armar antes con build.py)
# Se corre el comparador de terreno del bono (0x467b33 .. 0x467d1f) con casillas reales de la partida (tabla de
# terrenos incluida) y el bono de la unidad en un registro armado a mano. Esperado: un bono "bridge" (con cualquier
# mayúscula) suma solo en un puente en pie; cualquier otro nombre da lo mismo que el exe original, registros y pila
# incluidos.
import sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

def load(path):
    pe = pefile.PE(path); base = pe.OPTIONAL_HEADER.ImageBase
    return base, bytes(pe.get_memory_mapped_image()), (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
NEW = load(sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe')
OLD = load(sys.argv[2] if len(sys.argv) > 2 else r'C:\Warlords3\Darklord.exe')
sav = open(sys.argv[3] if len(sys.argv) > 3 else r'C:\Warlords3\Saves\Aliados03.SAV', 'rb').read()

TERR = sav[0x320a7:0x320a7 + 32 * 0x58]     # tabla de terrenos (0x535ef8; las capas 0x536790 son la 25 en adelante)
assert TERR[:7] == b'plains\0' and TERR[0x58:0x58 + 6] == b'water\0', 'la tabla de terrenos no está donde se espera'
SH = sav[0x73]
def tile(x, y):
    o = 0x7f + ((y * 10) << SH) + x * 10
    return bytearray(sav[o:o + 10])
def buscar(ok):
    return next((x, y) for y in range(100) for x in range(80) if ok(tile(x, y)))
clase = lambda b: struct.unpack_from('<H', TERR, (b[0] & 0x1f) * 0x58 + 0x14)[0]
estructura = lambda b: b[3] & 7

puente = tile(27, 40)
assert clase(puente) == 1 and estructura(puente) == 1, 'Aliados03 (27,40) no es un puente'
derribado = bytearray(puente); derribado[3] &= ~7; derribado[9] |= 0x80
CASILLAS = {
    'puente (27,40)': puente,
    'puente (27,41)': tile(27, 41),
    'puente derribado': derribado,
    'agua': tile(*buscar(lambda b: clase(b) == 1 and estructura(b) == 0)),
    'camino en tierra': tile(*buscar(lambda b: clase(b) != 1 and estructura(b) == 1)),
    'ciudad': tile(*buscar(lambda b: estructura(b) == 3)),
    'llanura': tile(*buscar(lambda b: b[0] & 0x1f == 0 and estructura(b) == 0 and not b[3] & 0x40)),
    'bosque (capa)': tile(*buscar(lambda b: b[3] & 0x40)),
    'colinas': tile(*buscar(lambda b: b[0] & 0x1f == 3 and estructura(b) == 0)),
}
NOMBRES = ['bridge', 'Bridge', 'BRIDGE', 'bridges', 'bridg', 'water', 'city', 'open', 'field', 'woods', 'forest',
           'plains', 'hills', 'landing', '']
ES_PUENTE = lambda n: n.lower() == 'bridge'

STUB, REC, TILE, ESP = 0x100000, 0x101000, 0x102000, 0x108000
REGS = ('EAX', 'EBX', 'ECX', 'EDX', 'ESI', 'EDI', 'EBP', 'ESP')

def run(exe, nombre, valor, casilla):
    base, img, size = exe
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(base, size); mu.mem_write(base, img[:size])
    mu.mem_map(0x100000, 0x10000)
    mu.mem_write(0x535ef8, TERR)
    mu.mem_write(0x5a9be0, struct.pack('<I', STUB)); mu.mem_write(STUB, b'\xc3')
    def stricmp(mu, addr, size, _):     # _stricmp de msvcrt: solo eax
        sp = mu.reg_read(UC_X86_REG_ESP)
        a, b = struct.unpack('<II', mu.mem_read(sp + 4, 8))
        cad = lambda p: bytes(mu.mem_read(p, 64)).split(b'\0')[0].lower()
        x, y = cad(a), cad(b)
        mu.reg_write(UC_X86_REG_EAX, 0 if x == y else (0xffffffff if x < y else 1))
    mu.hook_add(UC_HOOK_CODE, stricmp, begin=STUB, end=STUB)
    rec = bytearray(0xfc)
    rec[0xd6:0xd6 + 9] = nombre.encode().ljust(9, b'\0'); rec[0xdf] = valor
    mu.mem_write(REC, bytes(rec)); mu.mem_write(TILE, bytes(casilla))
    marco = bytearray(range(0xc0))
    struct.pack_into('<I', marco, 0x30, REC); struct.pack_into('<I', marco, 0x38, TILE)
    marco[0x11] = 0; struct.pack_into('<H', marco, 0x16, 0x7777); struct.pack_into('<H', marco, 0x26, 0)
    mu.mem_write(ESP, bytes(marco))
    for k, v in dict(EAX=0x11223344, EBX=0x55667788, ECX=0x99aabbcc, EDX=0xddeeff01, ESI=0x02030405,
                     EDI=0x06070809, EBP=0x0a0b0c0d, ESP=ESP).items():
        mu.reg_write(globals()['UC_X86_REG_' + k], v)
    mu.emu_start(0x467b33, 0x467d1f, count=5000)
    assert mu.reg_read(UC_X86_REG_EIP) == 0x467d1f, hex(mu.reg_read(UC_X86_REG_EIP))
    pila = bytes(mu.mem_read(ESP, 0xc0))
    bono = struct.unpack_from('<H', pila, 0x16)[0]
    return (0 if bono == 0x7777 else bono), {k: mu.reg_read(globals()['UC_X86_REG_' + k]) for k in REGS}, pila

mal = total = 0
for cnom, cas in CASILLAS.items():
    for nombre in NOMBRES:
        for valor in (2, 0):
            total += 1
            got, regs, pila = run(NEW, nombre, valor, cas)
            ref, regs_o, pila_o = run(OLD, nombre, valor, cas)
            if ES_PUENTE(nombre):
                exp = valor if cnom.startswith('puente (') else 0
                ok = got == exp
            else:
                exp = ref
                ok = (got, regs, pila) == (ref, regs_o, pila_o)
            if not ok:
                mal += 1
                print(f'MAL {cnom:16} "{nombre}" +{valor}: da {got}, esperado {exp}')
            elif valor and (got or ES_PUENTE(nombre)):
                print(f'ok  {cnom:16} "{nombre}" +{valor}: {got}')
# Control: el exe original no da bono "bridge" en el puente (si lo diera, la prueba no mide el gancho), y el bono
# "water" sí suma en el puente (la casilla de la prueba se lee bien).
ctl = run(OLD, 'bridge', 2, puente)[0] == 0 and run(OLD, 'water', 2, puente)[0] == 2 and \
      run(OLD, 'city', 3, CASILLAS['ciudad'])[0] == 3
print(f'control (original: bridge 0, water 2 y city 3 donde corresponde): {"ok" if ctl else "MAL"}')
print(f'{total} casos, ' + ('TODO OK' if not mal and ctl else f'{mal} MAL'))
sys.exit(1 if mal or not ctl else 0)
