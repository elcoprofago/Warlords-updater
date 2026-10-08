# Prueba de juguete de los nombres de puentes (br_name) sobre el exe parcheado, en unicorn.
# Uso: python prueba_nombrepuente.py [DarklordAV.exe] [BRIDNAME.TXT]
#   (por defecto C:\Warlords3\DarklordAV.exe y C:\Warlords3\DATA\BRIDNAME.TXT; armarlos antes con build.py)
# Corre todo lo del juego: br_name, el generador de nombres 0x4374a0, su azar 0x4deb20 y los métodos de archivo
# (abrir, leer línea, rebobinar, cerrar). Solo se simulan las llamadas a Windows y a la biblioteca de C que hay
# debajo: CreateFileA, ReadFile, SetFilePointer, CloseHandle, sscanf y _stricmp, sobre archivos en memoria.
# Mapa de 40x40 de tierra con tres puentes: horizontal (5,5)-(6,5), vertical (12,8)-(12,9) y uno de cuatro
# casillas (20,30)-(23,30); el de (12,8) se prueba también derribado.
import sys, struct, re, pefile, capstone
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

pe = pefile.PE(sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe'); BASE = pe.OPTIONAL_HEADER.ImageBase
GRAMMAR = open(sys.argv[2] if len(sys.argv) > 2 else r'C:\Warlords3\DATA\BRIDNAME.TXT', 'rb').read()
img = bytes(pe.get_memory_mapped_image())
SIZE = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
IMPORTS = {i.name.decode(): i.address for e in pe.DIRECTORY_ENTRY_IMPORT for i in e.imports if i.name}
FNAME = 'DATA\\BRIDNAME.TXT'

# br_name: el primer call del texto del diálogo de arrasar (0x495530 salta a br_razetxt); br_xy: lo que copia al entrar.
_cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def ins(va, n=0x40): return list(_cs.disasm(img[va - BASE:va - BASE + n], va))
i0 = ins(0x495530)[0]; assert i0.mnemonic == 'jmp'
BR_NAME = next(int(i.op_str, 16) for i in ins(int(i0.op_str, 16)) if i.mnemonic == 'call')
BR_XY = next(int(i.op_str.split(', ')[1], 16) for i in ins(BR_NAME) if i.mnemonic == 'mov' and i.op_str.startswith('esi, 0x'))
def cstr_va(s): return BASE + img.index(s.encode('latin1') + b'\0')
THE_BRIDGE, THE_BRIDGE_U = cstr_va('the bridge'), cstr_va('The bridge')

W = H = 40; SHIFT = 8; WATER, LAND = 3, 2
BC = lambda x, y: 0x2000 + (y << 7) + x
STUB = 0x100000; STACK = 0x200000; END = 0x1fff00; TEB = 0x300000; GDT = 0x301000
BRIDGES = {'A': [(5, 5), (6, 5)], 'B': [(12, 8), (12, 9)], 'C': [(20, 30), (21, 30), (22, 30), (23, 30)]}
FNS = {'CreateFileA': 0x1c, 'ReadFile': 0x14, 'SetFilePointer': 0x10, 'CloseHandle': 4, 'sscanf': 0, '_stricmp': 0}

def tile_va(x, y): return ((y * 10) << SHIFT) + x * 10 + 0x503e58
def gdt_entry(base, limit, access, flags):
    e = limit & 0xffff | (base & 0xffffff) << 16 | (access & 0xff) << 40 | ((limit >> 16) & 0xf) << 48 \
        | (flags & 0xf) << 52 | ((base >> 24) & 0xff) << 56
    return struct.pack('<Q', e)

class Bench:
    def __init__(self, files=None, razed=(), rng=(0x1234, 1), bridges=BRIDGES):
        mu = self.mu = Uc(UC_ARCH_X86, UC_MODE_32)
        mu.mem_map(BASE, SIZE); mu.mem_write(BASE, img[:SIZE])
        mu.mem_map(STUB, 0x10000); mu.mem_map(STACK - 0x10000, 0x10000); mu.mem_map(TEB, 0x2000)
        # Segmentos: fs -> TEB (fs:[0] = cadena SEH); con la GDT cargada, ss/ds/es tienen que ser planos de 32 bits.
        mu.mem_write(GDT + 8 * 2, gdt_entry(0, 0xfffff, 0x92, 0xc))
        mu.mem_write(GDT + 8 * 3, gdt_entry(TEB, 0xfff, 0xf2, 0x4))
        mu.reg_write(UC_X86_REG_GDTR, (0, GDT, 0xfff, 0))
        for r in (UC_X86_REG_SS, UC_X86_REG_DS, UC_X86_REG_ES): mu.reg_write(r, 2 << 3)
        mu.reg_write(UC_X86_REG_FS, (3 << 3) | 3)
        mu.mem_write(TEB, struct.pack('<I', 0xffffffff))
        mu.mem_write(0x503e00, struct.pack('<HH', W, H)); mu.mem_write(0x503e06, bytes([SHIFT]))
        mu.mem_write(0x535f0c + WATER * 0x58, struct.pack('<H', 1))
        mu.mem_write(0x535f0c + LAND * 0x58, struct.pack('<H', 0))
        for y in range(H):
            for x in range(W): self.set_tile(x, y, LAND, 0, 0)
        for k, tiles in bridges.items():
            for x, y in tiles:
                if k in razed: self.set_tile(x, y, WATER, 0, 0x80)
                else: self.set_tile(x, y, WATER, 1, 0)
        mu.mem_write(0x500bf4, struct.pack('<II', *rng))
        mu.mem_write(BR_XY, bytes(range(0x40, 0x60)))                     # br_xy de quien llamó: debe volver
        self.files = {k.lower(): v for k, v in (files if files is not None else {FNAME: GRAMMAR}).items()}
        self.handles = {}; self.opened = []; self.next_h = 0x700
        self.stub_of = {}
        for k, (name, n) in enumerate(FNS.items()):
            va = STUB + 0x10 * k
            mu.mem_write(va, b'\xc2' + struct.pack('<H', n) if n else b'\xc3')
            mu.mem_write(IMPORTS[name], struct.pack('<I', va)); self.stub_of[va] = name
        mu.mem_write(END, b'\xf4')
        mu.hook_add(UC_HOOK_CODE, self.hook, begin=STUB, end=STUB + 0x10000)

    def set_tile(self, x, y, w0, struct_, b9):
        t = tile_va(x, y)
        self.mu.mem_write(t, struct.pack('<H', w0)); self.mu.mem_write(t + 3, bytes([struct_]))
        self.mu.mem_write(t + 9, bytes([b9]))

    def arg(self, k):
        return struct.unpack('<I', self.mu.mem_read(self.mu.reg_read(UC_X86_REG_ESP) + 4 + 4 * k, 4))[0]
    def cstr(self, p): return bytes(self.mu.mem_read(p, 0x100)).split(b'\0')[0].decode('latin1')

    def hook(self, uc, addr, size, _):
        name = self.stub_of.get(addr)
        if not name: return
        a = self.arg; ret = 0
        if name == 'CreateFileA':
            fn = self.cstr(a(0)); self.opened.append(fn)
            assert a(1) == 0x80000000 and a(4) == 3, 'se abre para leer un archivo existente'
            if fn.lower() in self.files:
                h = self.next_h; self.next_h += 4; self.handles[h] = [self.files[fn.lower()], 0]; ret = h
            else: ret = 0xffffffff
        elif name == 'ReadFile':
            f = self.handles[a(0)]; n = a(2)
            data = f[0][f[1]:f[1] + n]; f[1] += len(data)
            uc.mem_write(a(1), data); uc.mem_write(a(3), struct.pack('<I', len(data))); ret = 1
        elif name == 'SetFilePointer':
            f = self.handles[a(0)]; dist, method = struct.unpack('<i', struct.pack('<I', a(1)))[0], a(3)
            f[1] = {0: 0, 1: f[1], 2: len(f[0])}[method] + dist; ret = f[1]
        elif name == 'CloseHandle':
            del self.handles[a(0)]; ret = 1
        elif name == '_stricmp':
            x, y = self.cstr(a(0)).lower(), self.cstr(a(1)).lower(); ret = (x > y) - (x < y)
        elif name == 'sscanf':
            s, fmt = self.cstr(a(0)), self.cstr(a(1))
            assert fmt == '%d %s %s %s %s', fmt
            toks = s.split(); ret = 0
            m = re.match(r'\s*([+-]?\d+)', s)
            if not toks: ret = 0xffffffff
            elif m:
                uc.mem_write(a(2), struct.pack('<i', int(m.group(1)))); ret = 1
                for k, t in enumerate(s[m.end():].split()[:4]):
                    uc.mem_write(a(3 + k), t.encode('latin1') + b'\0'); ret += 1
        uc.reg_write(UC_X86_REG_EAX, ret & 0xffffffff)

    def name(self, code, cap=0):
        """Llama a br_name(código, mayúscula) cdecl; devuelve (texto, puntero, registros conservados)."""
        mu = self.mu; esp = STACK - 0x400
        mu.mem_write(esp, struct.pack('<III', END, code & 0xffffffff, cap) + bytes(0x40))
        regs = dict(ECX=0x22222222, EDX=0x33333333, EBX=0x44444444, ESI=0x55555555, EDI=0x66666666, EBP=0x77777777)
        for k, v in regs.items(): mu.reg_write(globals()['UC_X86_REG_' + k], v)
        mu.reg_write(UC_X86_REG_EAX, 0x11111111); mu.reg_write(UC_X86_REG_ESP, esp)
        mu.emu_start(BR_NAME, END, count=20000000)
        eax = mu.reg_read(UC_X86_REG_EAX)
        kept = all(mu.reg_read(globals()['UC_X86_REG_' + k]) == v for k, v in regs.items()) \
            and mu.reg_read(UC_X86_REG_ESP) == esp + 4 and mu.reg_read(UC_X86_REG_EIP) == END
        return self.cstr(eax), eax, kept

    def clean(self, rng=(0x1234, 1)):
        """El azar, br_xy y la cadena SEH como estaban, y ningún archivo abierto."""
        return struct.unpack('<II', self.mu.mem_read(0x500bf4, 8)) == rng and \
            bytes(self.mu.mem_read(BR_XY, 0x20)) == bytes(range(0x40, 0x60)) and \
            struct.unpack('<I', self.mu.mem_read(TEB, 4))[0] == 0xffffffff and not self.handles

res = []
def check(nombre, cond, detalle=''):
    res.append(cond); print(f'{"OK " if cond else "MAL"} {nombre}' + (f'   [{detalle}]' if not cond and detalle else ''))

# La gramática: cada nombre tiene que poder salir de sus reglas.
sec = {}; cur = None
for line in GRAMMAR.decode('ascii').split('\r\n'):
    if line.startswith('['): cur = line; sec[cur] = []
    elif line and cur: sec[cur].append(line)
alt = lambda k: '(?:' + '|'.join(re.escape(e) for e in sorted(set(sec[k]), key=len, reverse=True)) + ')'
GRAMMAR_RE = re.compile('^(?:' + '|'.join(''.join(alt(t) for t in r.split()[1:]) for r in sec['[RULES]']) + ')$')
check('gramática: CRLF, sin LF sueltos (0x4e00c0 solo corta en CR+LF)',
      GRAMMAR.count(b'\n') == GRAMMAR.count(b'\r\n') > 0 and GRAMMAR.endswith(b'\r\n'))

# ---- cada casilla del puente, entero o derribado, da el mismo nombre
names = {}
for k, tiles in BRIDGES.items():
    b = Bench(); got = [b.name(BC(x, y)) for x, y in tiles]
    names[k] = got[0][0]
    check(f'puente {k}: mismo nombre desde todas sus casillas ({names[k]!r})',
          all(g[0] == names[k] for g in got) and all(g[2] for g in got) and b.clean(), got)
    check(f'puente {k}: el nombre sale de la gramática', bool(GRAMMAR_RE.match(names[k])), names[k])
check('tres puentes, tres nombres distintos', len(set(names.values())) == 3, names)
b = Bench(razed='B'); got = [b.name(BC(x, y)) for x, y in BRIDGES['B']]
check('puente B derribado: el mismo nombre que entero', all(g[0] == names['B'] and g[2] for g in got) and b.clean(), got)
b = Bench(); n1 = b.name(BC(12, 9), cap=1)
check('mayúscula no cambia un nombre propio', n1[0] == names['B'] and n1[2], n1)

# ---- el nombre no depende del azar de la partida (igual en todas las máquinas) y lo deja como estaba
for rng in ((0xbeef, 0), (0, 1), (0xffff, 0)):
    b = Bench(rng=rng); got = b.name(BC(6, 5))
    check(f'azar previo {rng}: mismo nombre y el azar intacto', got[0] == names['A'] and got[2] and b.clean(rng), got)

# ---- se lee el archivo una vez por puente; cambiar de puente y volver da el nombre correcto
b = Bench()
seq = [b.name(BC(5, 5))[0], b.name(BC(6, 5))[0], b.name(BC(12, 8))[0], b.name(BC(5, 5))[0]]
check('nombres en sucesión A, A, B, A', seq == [names['A'], names['A'], names['B'], names['A']] and b.clean(), seq)
check('el archivo se abre solo cuando cambia el puente', b.opened == [FNAME] * 3, b.opened)

# ---- sin archivo, archivo roto o casilla que no es puente: "the bridge" / "The bridge"
b = Bench(files={})
g0, g1 = b.name(BC(5, 5)), b.name(BC(5, 5), cap=1)
check('sin archivo: "the bridge"', g0[:2] == ('the bridge', THE_BRIDGE) and g0[2] and b.clean(), g0)
check('sin archivo, con mayúscula: "The bridge"', g1[:2] == ('The bridge', THE_BRIDGE_U) and g1[2] and b.clean(), g1)
check('sin archivo: lo vuelve a buscar cada vez', b.opened == [FNAME] * 2, b.opened)
broken = b'[RULES]\r\n\r\n100 [SYL1] [NOPE]\r\n\r\n[SYL1]\r\nBel\r\n'
b = Bench(files={FNAME: broken}); g = b.name(BC(5, 5), cap=1)
check('gramática con una sección que falta: "The bridge" (no un nombre a medias)', g[0] == 'The bridge' and g[2] and b.clean(), g)
b = Bench(); g = b.name(BC(30, 30))
check('tierra: no es puente, "the bridge" sin abrir el archivo', g[0] == 'the bridge' and g[2] and b.clean() and not b.opened, g)

# ---- reparto: 120 puentes de una casilla en lugares distintos (de a uno, en un mapa sin otros puentes)
b = Bench(bridges={}); got = []
for k in range(120):
    x, y = k % W, 1 + k // W * 13
    b.set_tile(x, y, WATER, 1, 0); got.append(b.name(BC(x, y))[0]); b.set_tile(x, y, LAND, 0, 0)
bad = [g for g in got if not GRAMMAR_RE.match(g)]
check(f'120 puentes: todos de la gramática, {len(set(got))} nombres distintos', not bad and len(set(got)) >= 110 and b.clean(),
      (bad[:5], len(set(got))))
print('ejemplos:', ', '.join(got[:8]))

mal = res.count(False)
print('TODO OK' if not mal else f'{mal} MAL'); sys.exit(1 if mal else 0)
