# Prueba de juguete de la ventana de fin de partida (go_* de build.py) sobre el exe y el RES parcheados, en unicorn.
# Uso: python prueba_fin.py [carpeta]   (por defecto C:\Warlords3; armarla antes con build.py)
# Título: corre 0x482c1d -> 0x482c39 con GetModuleHandleA devolviendo una KERNEL32 de mentira (tabla de exportaciones
# armada a mano) y GetLocalTime simulada. Podio: corre la tabla desde 0x482fdc (después de hi_gofin) hasta 0x483264
# con un marco de 0x482d77 armado a mano y las llamadas de dibujo interceptadas.
# Controles: sin KERNEL32 o con GetLocalTime reenviada (va sin fecha), bando sin aliados, aliado eliminado, alianza de
# un solo lado, Diplomacia desactivada, ejércitos muertos o de otro color, partida sin nombre (sin pie) y el RES
# original (título en la fuente 2, sin la hoja de la alianza).
import os, sys, struct, pefile
from PIL import Image
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

DIR = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3'
pe = pefile.PE(os.path.join(DIR, 'DarklordAV.exe')); BASE = pe.OPTIONAL_HEADER.ImageBase
img = bytes(pe.get_memory_mapped_image())
SIZE = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
STACK, RET, STUBS, K32, FRAME = 0x1f0000, 0x100, 0x300000, 0x400000 - 0x10000, 0x1e0000
SPRINTF, STRNCMP, GETMOD = 0x5a9bec, 0x5a9bf0, 0x5a984c
DIPLO, DIPLO_OPT, PLAYERS, ARMIES, NAME = 0x55ee4c, 0x53c393, 0x536b30, 0x54fe50, 0x503da0
GO_IMG, GOLD = 207, 137

mal = 0
def ver(nombre, r, esperado):
    global mal
    ok = r == esperado
    mal += not ok
    print('OK ' if ok else 'MAL', nombre, '->', r)

def cstr(mu, a):
    s = bytes(mu.mem_read(a, 256)); return s[:s.index(b'\0')].decode('latin1')

def sprintf(mu, fmt, args):
    out, i, k = '', 0, 0
    while i < len(fmt):
        if fmt[i] == '%':
            j = i + 1
            while fmt[j] in 'l': j += 1
            c = fmt[j]
            v = args[k]; k += 1
            out += cstr(mu, v) if c == 's' else str(struct.unpack('<i', struct.pack('<I', v))[0])
            i = j + 1
        else:
            out += fmt[i]; i += 1
    return out

def maquina():
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(BASE, SIZE); mu.mem_write(BASE, img[:SIZE])
    mu.mem_map(0x100000, 0x100000)
    mu.mem_map(STUBS, 0x1000)
    mu.mem_map(K32, 0x10000)
    return mu

def interceptar(mu, addr, pop, fn, registro):
    def g(mu, a, size, _):
        sp = mu.reg_read(UC_X86_REG_ESP)
        ret, *args = struct.unpack('<9I', mu.mem_read(sp, 36))
        r = fn(mu, args)
        if r is not None and registro is not None: registro.append(r)
        mu.reg_write(UC_X86_REG_EAX, getattr(fn, 'eax', 0))
        mu.reg_write(UC_X86_REG_ESP, sp + 4 + pop); mu.reg_write(UC_X86_REG_EIP, ret)
    mu.hook_add(UC_HOOK_CODE, g, begin=addr, end=addr)

def importar(mu, iat, n, pop, fn, registro):
    stub = STUBS + 0x10 * n
    mu.mem_write(stub, b'\xc3'); mu.mem_write(iat, struct.pack('<I', stub))
    interceptar(mu, stub, pop, fn, registro)

def libc(mu):
    def spf(mu, a):
        s = sprintf(mu, cstr(mu, a[1]), a[2:]); mu.mem_write(a[0], s.encode('latin1') + b'\0')
    importar(mu, SPRINTF, 0, 0, spf, None)
    def sncmp(mu, a):
        x, y = bytes(mu.mem_read(a[0], a[2])), bytes(mu.mem_read(a[1], a[2]))
        x, y = x[:x.index(b'\0') + 1] if b'\0' in x else x, y[:y.index(b'\0') + 1] if b'\0' in y else y
        sncmp.eax = 0 if x == y else 1
    importar(mu, STRNCMP, 1, 0, sncmp, None)

# ---------------------------------------------------------------- título
def k32(mu, nombres, forward=False):
    """KERNEL32 de mentira en K32: cabecera PE mínima y tabla de exportaciones con esos nombres; cada función es un
    stub en STUBS + 0x100 + 0x10*i (RVA relativa a K32), o un texto de reenvío dentro de la tabla si forward."""
    exp = 0x200
    mu.mem_write(K32 + 0x3c, struct.pack('<I', 0x80))
    names_rva, ords_rva, funcs_rva, str_rva = exp + 0x40, exp + 0x80, exp + 0xc0, exp + 0x100
    fwd_rva = str_rva + 0x200
    mu.mem_write(K32 + 0x80 + 0x78, struct.pack('<II', exp, 0x400))
    mu.mem_write(K32 + exp + 0x14, struct.pack('<IIIII', len(nombres), len(nombres), funcs_rva, names_rva, ords_rva))
    p = str_rva
    for i, n in enumerate(nombres):
        mu.mem_write(K32 + p, n.encode() + b'\0')
        mu.mem_write(K32 + names_rva + 4 * i, struct.pack('<I', p)); p += len(n) + 1
        mu.mem_write(K32 + ords_rva + 2 * i, struct.pack('<H', i))
        f = fwd_rva if forward and n == 'GetLocalTime' else STUBS + 0x100 + 0x10 * i - K32
        mu.mem_write(K32 + funcs_rva + 4 * i, struct.pack('<I', f & 0xffffffff))
    mu.mem_write(K32 + fwd_rva, b'KERNELBASE.GetLocalTime\0')

def titulo(nombres=('GetDateFormatA', 'GetLocalTime', 'GetLongPathNameA'), modulo=True, forward=False,
           fecha=(2026, 11, 8)):
    mu = maquina(); out = []; libc(mu)
    mu.mem_write(0x57175c, b'\1')
    k32(mu, list(nombres), forward)
    def gm(mu, a):
        out.append(('modulo', cstr(mu, a[0]))); gm.eax = K32 if modulo else 0
    importar(mu, GETMOD, 2, 4, gm, None)
    for i, n in enumerate(nombres):
        def f(mu, a, n=n):
            if n == 'GetLocalTime':
                y, m, d = fecha; mu.mem_write(a[0], struct.pack('<8H', y, m, 0, d, 21, 30, 0, 0))
            return ('llamada', n)
        interceptar(mu, STUBS + 0x100 + 0x10 * i, 4, f, out)
    interceptar(mu, 0x4dd240, 0, lambda mu, a: ('texto', a[0], cstr(mu, a[1])), out)
    interceptar(mu, 0x4dd2b0, 0, lambda mu, a: ('color', a[0], a[1], a[2], a[3]), out)
    mu.reg_write(UC_X86_REG_ESP, STACK); mu.mem_write(STACK, struct.pack('<I', RET))
    mu.emu_start(0x482c1d, 0x482c39, count=100000)
    assert mu.reg_read(UC_X86_REG_EIP) == 0x482c39 and mu.reg_read(UC_X86_REG_ESP) == STACK
    return out
print('-- título')
_ok = [('modulo', 'KERNEL32.DLL'), ('llamada', 'GetLocalTime'), ('texto', 1, 'Partida finalizada 8/11/2026'),
       ('color', 1, GOLD, 0, 0)]
ver('con GetLocalTime: fecha d/m/aaaa, dorado', titulo(), _ok)
ver('otra fecha (un dígito y dos)', titulo(fecha=(2027, 1, 31))[2], ('texto', 1, 'Partida finalizada 31/1/2027'))
ver('control: GetLocalTime no exportada: sin fecha', titulo(nombres=('GetLocalTimeX', 'GetLocalTim')),
    [('modulo', 'KERNEL32.DLL'), ('texto', 1, 'Partida finalizada'), ('color', 1, GOLD, 0, 0)])
ver('control: sin KERNEL32: sin fecha', titulo(modulo=False),
    [('modulo', 'KERNEL32.DLL'), ('texto', 1, 'Partida finalizada'), ('color', 1, GOLD, 0, 0)])
ver('control: GetLocalTime reenviada: no la llama, sin fecha', titulo(forward=True),
    [('modulo', 'KERNEL32.DLL'), ('texto', 1, 'Partida finalizada'), ('color', 1, GOLD, 0, 0)])

# ---------------------------------------------------------------- podio
X0, Y0 = 52, 92
def podio(bandos, ejercitos, aliados, diplo=True, nombre='NA_052'):
    """bandos: [(color, puesto, pv, ciudades, oro, en_juego)] en orden; ejercitos: [(color, vivo)];
    aliados: pares (a, b) con a aliado de b (de un solo lado)."""
    mu = maquina(); out = []; libc(mu)
    mu.mem_write(DIPLO_OPT, bytes([8 if diplo else 0]))
    mu.mem_write(DIPLO, bytes([2] * 64 * 8))
    for a, b in aliados: mu.mem_write(DIPLO + a * 56 + b, b'\0')
    for p in range(8): mu.mem_write(PLAYERS + p * 0x1f8, b'\0\0')
    for c, *_r, juega in bandos:
        if juega: mu.mem_write(PLAYERS + c * 0x1f8, b'\1\1')
        mu.mem_write(PLAYERS + c * 0x1f8 + 4, f'Lord{c}\0'.encode())
    mu.mem_write(ARMIES, struct.pack('<h', len(ejercitos) + 1))
    for k, (c, vivo) in enumerate(ejercitos, 1):
        r = ARMIES + k * 0x1c
        mu.mem_write(r + 0xe, struct.pack('<H', (c << 5) | 0x13))
        mu.mem_write(r + 0x13, bytes([0x40 | 1 if vivo else 1]))
    mu.mem_write(NAME, nombre.encode() + b'\0')
    ebp = FRAME
    mu.mem_write(ebp + 8, struct.pack('<ii', X0, Y0))
    mu.mem_write(ebp - 0xe, struct.pack('<h', len(bandos)))
    for k, (c, pu, pv, ci, oro, _j) in enumerate(bandos):
        mu.mem_write(ebp - 0x24 + 2 * k, struct.pack('<h', c)); mu.mem_write(ebp - 0x5c + 2 * k, struct.pack('<h', pu))
        mu.mem_write(ebp - 0x3c + 2 * k, struct.pack('<h', pv)); mu.mem_write(ebp - 0x4c + 2 * k, struct.pack('<h', ci))
        mu.mem_write(ebp - 0x7c + 4 * k, struct.pack('<i', oro))
    texto = lambda tipo: (lambda mu, a: (tipo, a[0] - X0, a[1] - Y0, cstr(mu, a[2])))
    interceptar(mu, 0x4dd120, 0, texto('izq'), out)
    interceptar(mu, 0x4dd140, 0, texto('col'), out)
    interceptar(mu, 0x4dd080, 0, lambda mu, a: ('img', a[0], a[1] - X0, a[2] - Y0), out)
    interceptar(mu, 0x4dd0f0, 0, lambda mu, a: None, out)
    hdr = ['SIDE', 'VPs', 'CITIES', 'GOLD']
    def gs(mu, a):
        if a[0] == 0xd8: mu.mem_write(STUBS + 0x800, hdr[a[1]].encode() + b'\0')
        gs.eax = STUBS + 0x800
    interceptar(mu, 0x4def30, 8, gs, None)
    mu.reg_write(UC_X86_REG_EBP, ebp); mu.reg_write(UC_X86_REG_ESI, Y0)
    mu.reg_write(UC_X86_REG_ESP, STACK - 4); mu.mem_write(STACK - 4, struct.pack('<I', 1))
    mu.emu_start(0x482fdc, 0x483264, count=200000)
    assert mu.reg_read(UC_X86_REG_EIP) == 0x483264
    return out
print('-- podio')
_r = podio([(0, 1, 30, 5, 100, 1), (3, 2, 20, 4, 50, 1), (5, 3, 10, 1, 7, 1)],
           [(0, 1), (0, 1), (0, 0), (3, 1), (5, 1), (5, 1), (5, 1), (6, 1)], [(0, 3), (3, 0)])
ver('encabezado: Armas entre PV y Ciudades, columnas corridas', [x for x in _r if x[2] == 5],
    [('izq', 30, 5, 'SIDE'), ('col', 0x82, 5, 'VPs'), ('col', 0xce, 5, 'CITIES'), ('col', 0xf4, 5, 'GOLD'),
     ('col', 0xa8, 5, 'Armas')])
ver('armas: vivos de cada color (muertos y de otro color no)', [x[3] for x in _r if x[0] == 'col' and x[1] == 0xa8][1:],
    ['2', '1', '3'])
ver('valores en las columnas nuevas (fila 1)', [x for x in _r if x[2] == 0x23 and x[0] == 'col'],
    [('col', 10, 0x23, '1'), ('col', 0x82, 0x23, '30'), ('col', 0xce, 0x23, '5'), ('col', 0xa8, 0x23, '2'),
     ('col', 0xf4, 0x23, '100')])
ver('marca de alianza solo en los aliados mutuos en juego (0 y 3)', [x for x in _r if x[0] == 'img'],
    [('img', 0x69, 30, 0x23), ('img', GO_IMG, 38, 0x23 - 5), ('img', 0x69 + 3, 30, 0x41),
     ('img', GO_IMG, 38, 0x41 - 5), ('img', 0x69 + 5, 30, 0x5f)])
ver('pie centrado con el nombre de la partida', _r[-1], ('col', 123, 262, 'corresponde a la partida "NA_052"'))
_img = lambda r: [x[1] for x in r if x[0] == 'img']
_b = [(0, 1, 30, 5, 100, 1), (3, 2, 20, 4, 50, 1)]
ver('control: alianza de un solo lado: sin marca', _img(podio(_b, [], [(0, 3)])), [0x69, 0x69 + 3])
ver('control: aliado eliminado: sin marca', _img(podio(_b, [], [(0, 4), (4, 0)])), [0x69, 0x69 + 3])
ver('control: Diplomacia desactivada: sin marca', _img(podio(_b, [], [(0, 3), (3, 0)], diplo=False)), [0x69, 0x69 + 3])
ver('control: partida sin nombre: sin pie', [x for x in podio(_b, [], [], nombre='') if 'corresponde' in str(x)], [])

# ---------------------------------------------------------------- RES
def tablas(path):
    d = open(path, 'rb').read(); o = 8; t = {}; dl = {}
    while o + 20 <= len(d):
        h = struct.unpack_from('<5I', d, o)
        if h[1] == 0: t[h[0]] = (o, h)
        if h[0] == 7: dl[h[1]] = o
        o += 20 + h[4]
    return d, t, dl
def res_ver(path):
    d, t, dl = tablas(path)
    font = d[dl[46] + 20 + 0x20]
    o4, h4 = t[4]; o2, h2 = t[2]
    im = struct.unpack_from('<8i', d, o4 + 20 + GO_IMG * 32) if h4[2] > GO_IMG else None
    fi = d[o2 + 20 + 171 * 60 + 4:o2 + 20 + 171 * 60 + 36].split(b'\0')[0] if h2[2] > 171 else None
    return font, im, fi
print('-- RES')
ver('título en la fuente 1; imagen 207 = hoja 171 picts\\alianza 12x11', res_ver(os.path.join(DIR, 'DATA', 'WAR3AV.RES')),
    (1, (GO_IMG, 171, 1, 0, 0, 0, 12, 11), b'picts\\alianza'))
ver('control: RES original', res_ver(os.path.join(DIR, 'DATA', 'War3.RES')), (2, None, None))
_h = Image.open(os.path.join(DIR, 'PICTS', 'alianza.pcx'))
ver('hoja: 12x11 con transparente en las esquinas', (_h.size, _h.getpixel((0, 0)), _h.getpixel((11, 10))), ((12, 11), 11, 11))

print('MAL:', mal) if mal else print('todo OK')
sys.exit(1 if mal else 0)
