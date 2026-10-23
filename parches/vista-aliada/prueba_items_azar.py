# Prueba de ri_go (build.py): tras copiar el ITEM.DAT de un mapa al azar, rearma sus 32 primeros nombres con un
# sorteo entre todos los ITEMS\*.ITM. Corre el call parcheado de 0x4ca0b7 en unicorn, con las funciones de archivo
# (CopyFileA, CreateFileA, ReadFile, SetFilePointer, WriteFile, CloseHandle, _findfirst/_findnext/_findclose) sobre
# archivos en memoria y la tirada 0x4deb20 en Python.
# Uso: python prueba_items_azar.py [DarklordAV.exe]
import sys, struct, random, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

EXE = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe'
pe = pefile.PE(EXE); img = pe.get_memory_mapped_image()
def rva(va): return va - 0x400000
assert img[rva(0x4ca0b7)] == 0xe8 and img[rva(0x4ca0bc)] == 0x90, 'el CopyFileA de 0x4ca0b7 no está parcheado'
RI_GO = 0x4ca0bc + struct.unpack_from('<i', img, rva(0x4ca0b8))[0]
SENT, STACK, FRAME = 0xdead0000, 0x10080000, 0x10090000

def nombres(d): return [d[2 + 9 * i:11 + 9 * i].split(b'\0')[0].decode() for i in range(40)]
def correr(lista, dat, falla_find=False, seed=1):
    rnd = random.Random(seed)
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(0x400000, (len(img) + 0xfff) & ~0xfff); mu.mem_write(0x400000, img)
    mu.mem_map(0x10000000, 0x100000); mu.mem_map(SENT, 0x1000); mu.mem_map(0xdead1000, 0x10000)
    files, st = {'SRC': dat}, {'h': None, 'pos': 0, 'it': 0, 'tiradas': []}
    def cstr(a): return bytes(mu.mem_read(a, 260)).split(b'\0')[0].decode('latin1')
    def fd_name(fd, i): mu.mem_write(fd + 20, lista[i].encode() + b'.ITM\0')
    def copyf(a): files[cstr(a[1])] = files[cstr(a[0])]; return 1
    def findfirst(a):
        assert cstr(a[0]) == 'ITEMS\\*.ITM'
        if falla_find or not lista: return -1
        st['it'] = 0; fd_name(a[1], 0); return 0x77
    def findnext(a):
        assert a[0] == 0x77; st['it'] += 1
        if st['it'] >= len(lista): return -1
        fd_name(a[1], st['it']); return 0
    def createf(a): st['h'] = cstr(a[0]); st['pos'] = 0; assert st['h'] in files; return 0x55
    def readf(a):
        d = files[st['h']][st['pos']:st['pos'] + a[2]]; mu.mem_write(a[1], d); mu.mem_write(a[3], struct.pack('<I', len(d)))
        st['pos'] += len(d); return 1
    def setfp(a): st['pos'] = a[1]; return a[1]
    def writef(a):
        d = files[st['h']]; nuevo = bytes(mu.mem_read(a[1], a[2]))
        files[st['h']] = d[:st['pos']] + nuevo + d[st['pos'] + a[2]:]; mu.mem_write(a[3], struct.pack('<I', a[2])); return 1
    def stricmp(a):
        x, y = cstr(a[0]).lower(), cstr(a[1]).lower(); return (x > y) - (x < y)
    def tirada(a):
        n, caras, suma = a[0] & 0xffff, a[1] & 0xffff, a[2] & 0xffffffff
        assert n == 1 and suma == 0xffffffff and caras >= 1, (n, caras, suma)
        st['tiradas'].append(caras); return rnd.randrange(caras)
    stdcall = {'CopyFileA': (copyf, 3), 'CreateFileA': (createf, 7), 'ReadFile': (readf, 5),
               'SetFilePointer': (setfp, 4), 'WriteFile': (writef, 5), 'CloseHandle': (lambda a: 1, 1)}
    cdecl = {'_findfirst': findfirst, '_findnext': findnext, '_findclose': lambda a: 0, '_stricmp': stricmp}
    names, k = {}, 0
    for d in pe.DIRECTORY_ENTRY_IMPORT:
        for imp in d.imports:
            s = 0xdead1000 + 16 * k; k += 1
            mu.mem_write(imp.address, struct.pack('<I', s)); names[s] = (imp.name or b'?').decode()
    def llamada(m, fn, npop):
        sp = m.reg_read(UC_X86_REG_ESP)
        ret = struct.unpack('<I', m.mem_read(sp, 4))[0]; args = struct.unpack('<8I', m.mem_read(sp + 4, 32))
        m.reg_write(UC_X86_REG_EAX, fn(args) & 0xffffffff)
        m.reg_write(UC_X86_REG_ESP, sp + 4 + 4 * npop); m.reg_write(UC_X86_REG_EIP, ret)
    def imph(m, a, size, ud):
        n = names[a]
        if n in stdcall: llamada(m, stdcall[n][0], stdcall[n][1])
        elif n in cdecl: llamada(m, cdecl[n], 0)
        else: raise RuntimeError('importación inesperada ' + n)
    mu.hook_add(UC_HOOK_CODE, imph, begin=0xdead1000, end=0xdead1000 + 16 * k)
    mu.hook_add(UC_HOOK_CODE, lambda m, a, s, u: llamada(m, tirada, 0), begin=0x4deb20, end=0x4deb20)
    # marco de 0x4ca000: destino en [ebp - 0x60]; origen en otro búfer
    mu.mem_write(FRAME - 0x60, b'DST\0'); mu.mem_write(0x10010000, b'SRC\0')
    regs = {UC_X86_REG_EBX: 0x1111, UC_X86_REG_ESI: 0x2222, UC_X86_REG_EDI: 0x3333, UC_X86_REG_EBP: FRAME}
    for r, v in regs.items(): mu.reg_write(r, v)
    sp = STACK - 16; mu.mem_write(sp, struct.pack('<4I', SENT, 0x10010000, FRAME - 0x60, 0))
    mu.reg_write(UC_X86_REG_ESP, sp)
    mu.emu_start(RI_GO, SENT, count=2000000)
    for r, v in regs.items(): assert mu.reg_read(r) == v, 'registro no preservado'
    assert mu.reg_read(UC_X86_REG_ESP) == STACK, 'pila desbalanceada'
    return files['DST'], st['tiradas']

fallas = []
def caso(titulo, cond):
    print(('OK   ' if cond else 'FALLA'), titulo)
    if not cond: fallas.append(titulo)

orig = open(r'C:\Warlords3\RANDOM\Grass\Item2.dat', 'rb').read()      # con 8 especiales
largo = open(r'C:\Warlords3\RANDOM\Grass\Item1.dat', 'rb').read()     # 446 bytes: el resto se conserva
esp = [n for n in nombres(orig)[32:] if n]
todos = ['pers%03d' % i for i in range(300)] + ['BOOTSPEE', 'ringpowr'] + [e.upper() for e in esp]

out, tir = correr(todos, orig)
n = nombres(out)
caso('porcentaje 100', struct.unpack_from('<h', out)[0] == 100)
caso('32 nombres, todos de ITEMS', all(x in todos for x in n[:32]))
caso('sin repetidos', len({x.lower() for x in n[:32]}) == 32)
caso('ninguno repite un especial', not ({x.lower() for x in n[:32]} & {e.lower() for e in esp}))
caso('control: especiales intactos', out[2 + 32 * 9:] == orig[2 + 32 * 9:])
caso('sorteo sin reposición (tiradas n, n-1, ...)', tir[:3] == [len(todos), len(todos) - 1, len(todos) - 2])
caso('aparecen personalizados', any(x.startswith('pers') for x in n[:32]))
out2, _ = correr(todos, orig, seed=2)
caso('otra tirada, otra lista', nombres(out2)[:32] != n[:32])

out, _ = correr(['aa', 'bb', 'cc'], orig)
caso('pocos ítems: 3 nombres y el resto vacío', nombres(out)[:3] and set(nombres(out)[:3]) == {'aa', 'bb', 'cc'}
     and out[2 + 27:2 + 32 * 9] == bytes(29 * 9))
out, _ = correr(todos, largo)
caso('archivo de 446 bytes: cola intacta', out[362:] == largo[362:] and len(out) == len(largo))
out, _ = correr(todos, orig, falla_find=True)
caso('control: sin ITEMS, la copia queda como el original', out == orig)
out, _ = correr(['nombrelargo9', 'x'], orig)
caso('nombre de más de 8 letras se corta en 8', set(nombres(out)[:2]) == {'nombrela', 'x'})

print('TODO OK' if not fallas else '%d FALLAS' % len(fallas))
sys.exit(1 if fallas else 0)
