# Prueba de hi_mover / hi_fin / hi_gofin / hi_govic / hi_auto (partidas terminadas a HISTORY\), con el código
# parcheado real emulado sobre una carpeta de juguete (PENDIENTE-partidas-terminadas.md).
# Uso: python prueba_historia.py C:\Warlords3\DarklordAV.exe   (las rutinas se ubican por los parches del exe)
# Las funciones de Windows y de la biblioteca de C (sprintf, CopyFileA, DeleteFileA, CreateDirectoryA, _stricmp) y el
# autoguardado 0x4397f0 se reemplazan por equivalentes en Python sobre una carpeta temporal.
import os, re, shutil, struct, sys, tempfile
import pefile
from unicorn import *
from unicorn.x86_const import *

EXE = sys.argv[1]
pe = pefile.PE(EXE); img = pe.get_memory_mapped_image()

mu = Uc(UC_ARCH_X86, UC_MODE_32)
mu.mem_map(0x400000, (len(img) + 0xfff) & ~0xfff); mu.mem_write(0x400000, img)
STK = 0x10000000; mu.mem_map(STK, 0x100000)
STUB = 0x20000000; mu.mem_map(STUB, 0x1000)
FIN = 0xdead0000; mu.mem_map(FIN, 0x1000)

def rd(a): return struct.unpack('<I', mu.mem_read(a, 4))[0]
def cstr(a):
    s = b''
    while (c := mu.mem_read(a + len(s), 1)) != b'\0': s += c
    return s.decode('latin1')
def arg(i): return rd(mu.reg_read(UC_X86_REG_ESP) + 4 + 4 * i)

def ruta(p): return os.path.join(JUEGO, p)
def f_sprintf():
    fmt = cstr(arg(1)); vals = []; k = 2
    for t in re.findall(r'%([sd])', fmt):
        vals.append(cstr(arg(k)) if t == 's' else struct.unpack('<i', struct.pack('<I', arg(k)))[0]); k += 1
    s = re.sub(r'%[sd]', '{}', fmt).format(*vals)
    mu.mem_write(arg(0), s.encode('latin1') + b'\0'); return len(s)
def f_copy():
    o, d = ruta(cstr(arg(0))), ruta(cstr(arg(1)))
    if not os.path.isfile(o) or not os.path.isdir(os.path.dirname(d)): return 0
    shutil.copyfile(o, d); return 1
def f_del():
    p = ruta(cstr(arg(0)))
    if not os.path.isfile(p): return 0
    os.remove(p); return 1
def f_mkdir():
    p = ruta(cstr(arg(0)))
    if os.path.isdir(p): return 0
    os.mkdir(p); return 1
def f_stricmp(): return int(cstr(arg(0)).lower() != cstr(arg(1)).lower())
def f_autoguardado():   # como 0x4397f0: NETSAVES\<nombre>_<turno>.SAV
    t = struct.unpack('<h', mu.mem_read(0x503328, 2))[0]
    open(ruta(f'NETSAVES\\{cstr(0x503da0)}_{t}.SAV'.replace('\\', os.sep)), 'w').write(f'turno {t}')
    return 0

# Cada función: un stub (ret o ret n) cuya ejecución llama a la versión en Python.
stubs = {}
def stub(iat, fn, pops):
    a = STUB + 16 * len(stubs)
    mu.mem_write(a, b'\xc3' if not pops else b'\xc2' + struct.pack('<H', pops))
    stubs[a] = fn
    if iat: mu.mem_write(iat, struct.pack('<I', a))
    return a
stub(0x5a9bec, f_sprintf, 0); stub(0x5a9844, f_copy, 12); stub(0x5a97c0, f_del, 4)
stub(0x5a9824, f_mkdir, 8); stub(0x5a9be0, f_stricmp, 0)
auto = stub(None, f_autoguardado, 0)
mu.mem_write(0x4397f0, b'\xe9' + struct.pack('<i', auto - 0x4397f5))
def al_ejecutar(uc, a, n, _):
    if a in stubs: uc.reg_write(UC_X86_REG_EAX, stubs[a]() & 0xffffffff)
mu.hook_add(UC_HOOK_CODE, al_ejecutar, begin=STUB, end=STUB + 0xfff)

# Direcciones de las rutinas: los parches del exe apuntan a ellas
def destino(va, op):   # destino de un call/jmp rel32 en va
    b = mu.mem_read(va, 5); assert b[0] == op, hex(va)
    return (va + 5 + struct.unpack('<i', bytes(b[1:]))[0]) & 0xffffffff
HI_GOFIN, HI_GOVIC, HI_AUTO = destino(0x482fd6, 0xe9), destino(0x482790, 0xe8), destino(0x4aa0a6, 0xe8)
HI_FIN = destino(HI_GOFIN, 0xe8); IA_FIN = destino(HI_GOFIN + 5, 0xe9)
# ia_fin/ia_vic (registros de tandas) no se prueban acá: se los corta en su entrada
IA_VIC = destino(HI_GOVIC + 0xe, 0xe9)

def correr(addr, stop=FIN):
    sp = STK + 0x80000 - 4; mu.mem_write(sp, struct.pack('<I', FIN))
    mu.reg_write(UC_X86_REG_ESP, sp); mu.reg_write(UC_X86_REG_EBP, STK + 0x90000)
    mu.emu_start(addr, stop, count=5_000_000)

ok = True
def check(c, msg):
    global ok; print('   ', 'OK   ' if c else 'FALLA', msg); ok &= bool(c)
def estado(tag):
    print(tag); print('    NETSAVES:', sorted(os.listdir(ruta('NETSAVES'))))
    print('    HISTORY :', sorted(os.listdir(ruta('HISTORY'))) if os.path.isdir(ruta('HISTORY')) else '(no existe)')
def poner(nombre, turno, victoria=0):
    mu.mem_write(0x503da0, nombre.encode() + b'\0'); mu.mem_write(0x503328, struct.pack('<h', turno))
    mu.mem_write(0x571760, bytes([victoria]))
def en(c, *a): return set(os.listdir(ruta(c))) >= set(a) if os.path.isdir(ruta(c)) else False
def no_en(c, *a): return not (set(os.listdir(ruta(c))) & set(a)) if os.path.isdir(ruta(c)) else True

JUEGO = tempfile.mkdtemp(prefix='prueba_historia_')
os.mkdir(ruta('NETSAVES'))
for t in (27, 28, 29): open(ruta(f'NETSAVES/NA_2_{t}.SAV'), 'w').write(f'turno {t}')
for t in (5, 6): open(ruta(f'NETSAVES/OTRA_{t}.SAV'), 'w').write('control')   # otra partida: tiene que quedar
open(ruta('NETSAVES/NA_2_X.SAV'), 'w').write('control')                       # mismo prefijo, no es un turno
open(ruta('HISTORY.DAT'), 'w').write('control')

print('1. Victoria aliada (cartel) en el turno 29 de NA_2, autoguardado del turno todavía no hecho')
poner('NA_2', 29, victoria=1)
correr(HI_GOVIC, IA_VIC)
estado('  después del cartel')
check(en('HISTORY', 'NA_2_27.SAV', 'NA_2_28.SAV', 'NA_2_29.SAV'), 'los tres turnos de NA_2 pasaron a HISTORY')
check(no_en('NETSAVES', 'NA_2_27.SAV', 'NA_2_28.SAV', 'NA_2_29.SAV'), 'y ya no están en NETSAVES')
check(en('NETSAVES', 'OTRA_5.SAV', 'OTRA_6.SAV', 'NA_2_X.SAV'), 'control: la otra partida y NA_2_X siguen en NETSAVES')
check(os.path.isfile(ruta('HISTORY.DAT')), 'control: HISTORY.DAT intacto')

print('2. Autoguardado del turno 29 después del cartel (mismo turno, el archivo ya estaba en HISTORY)')
correr(HI_AUTO)
estado('  después del autoguardado')
check(no_en('NETSAVES', 'NA_2_29.SAV') and en('HISTORY', 'NA_2_29.SAV'), 'el NA_2_29 nuevo pisó al de HISTORY y no quedó en NETSAVES')

print('3. La partida sigue tras la victoria aliada: autoguardado del turno 30')
poner('na_2', 30)   # el nombre se compara sin distinguir mayúsculas
correr(HI_AUTO)
check(no_en('NETSAVES', 'na_2_30.SAV') and en('HISTORY', 'na_2_30.SAV'), 'el turno 30 también va a HISTORY')

print('4. Control: autoguardado de otra partida (OTRA, turno 7) sin victoria')
poner('OTRA', 7)
correr(HI_AUTO)
check(en('NETSAVES', 'OTRA_5.SAV', 'OTRA_6.SAV', 'OTRA_7.SAV') and no_en('HISTORY', 'OTRA_7.SAV'), 'OTRA queda entera en NETSAVES')

print('5. Control: cartel sin victoria ([0x571760] = 0) no mueve nada')
correr(HI_GOVIC, IA_VIC)
check(en('NETSAVES', 'OTRA_5.SAV', 'OTRA_6.SAV', 'OTRA_7.SAV'), 'OTRA sigue en NETSAVES')

print('6. Game Over (podio) de OTRA en el turno 7')
poner('OTRA', 7)
correr(HI_GOFIN, IA_FIN)
estado('  después del podio')
check(en('HISTORY', 'OTRA_5.SAV', 'OTRA_6.SAV', 'OTRA_7.SAV') and no_en('NETSAVES', 'OTRA_5.SAV', 'OTRA_6.SAV', 'OTRA_7.SAV'),
      'OTRA pasó entera a HISTORY')
check(en('NETSAVES', 'NA_2_X.SAV'), 'control: NA_2_X sigue en NETSAVES')

shutil.rmtree(JUEGO)
print('RESULTADO:', 'TODO OK' if ok else 'HAY FALLAS')
sys.exit(0 if ok else 1)
