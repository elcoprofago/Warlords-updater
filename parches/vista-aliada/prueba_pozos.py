# Prueba de juguete de pozos, remolinos y trampas (po_* de build.py) sobre el exe parcheado y el original, en unicorn.
# Uso: python prueba_pozos.py [carpeta]   (por defecto C:\Warlords3; armarla antes con build.py)
# Parte 1, datos + SAV: guardar y cargar corren desde la última escritura y la última lectura del .SAV (0x439c84,
# 0x439fda) con el archivo de mentira (un dict).
# Controles: la tabla de la Votación sigue igual delante; un .SAV viejo (sin VOTA, o con VOTA y sin POZO), roto o con
# otra marca carga la tabla vacía; un registro fuera del mapa no se marca en po_map; el original carga el .SAV nuevo.
import os, sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

DIR = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3'
STACK, RET, FRAME, OPTS = 0x1f0000, 0x100, 0x1e0000, 0x4fae68
MAPW, MAPH, MAPSH = 0x503e00, 0x503e02, 0x503e06
PO_MAX, PO_REC, PO_MAPSZ, VT_MAX = 64, 8, 0x32000 // 10, 8

def cargar(nombre):
    pe = pefile.PE(os.path.join(DIR, nombre))
    return pe, pe.OPTIONAL_HEADER.ImageBase, bytes(pe.get_memory_mapped_image())
AV, ORIG = cargar('DarklordAV.exe'), cargar('Darklord.exe')
_, BASE, img = AV
# po_save: 'POZO' y la tabla en cero; vt_save: 'VOTA' y la suya
PO_SAVE = BASE + img.index(b'POZO' + bytes(4 + PO_MAX * PO_REC)); PO_N, PO_TAB = PO_SAVE + 4, PO_SAVE + 8
VT_N = BASE + img.index(b'VOTA' + bytes(4 + VT_MAX * 0x1c)) + 4
# po_map: lo primero que borra po_rebuild (pushad; mov edi, po_map)
k = img.index(b'\x60\xbf') ; PO_MAP = struct.unpack_from('<I', img, k + 2)[0]
while not (PO_MAP == PO_SAVE + 8 + PO_MAX * PO_REC + 4):
    k = img.index(b'\x60\xbf', k + 1); PO_MAP = struct.unpack_from('<I', img, k + 2)[0]

mal = 0
def ver(nombre, r, esperado):
    global mal
    ok = r == esperado
    mal += not ok
    print('OK ' if ok else 'MAL', nombre, '->', r)

class Juego:
    def __init__(self, exe=AV):
        pe, base, imagen = exe
        mu = self.mu = Uc(UC_ARCH_X86, UC_MODE_32)
        size = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
        mu.mem_map(base, size); mu.mem_write(base, imagen[:size])
        mu.mem_map(0, 0x1000); mu.mem_map(0x100000, 0x100000)
        self.fs, self.abiertos = {}, {}
        mu.mem_write(MAPW, struct.pack('<hh', 40, 30)); mu.mem_write(MAPSH, b'\6')   # 40 x 30, filas de 64
        self.interceptar(0x4dfd70, self.escribir, pop=8)
        self.interceptar(0x4dfd20, self.leer, pop=8)
        self.interceptar(0x4dfdc0, lambda a: self.abiertos.pop(self.mu.reg_read(UC_X86_REG_ECX), None) and 0)
    def interceptar(self, addr, fn, pop=0):
        def g(mu, a, size, _):
            sp = mu.reg_read(UC_X86_REG_ESP)
            ret, *args = struct.unpack('<5I', mu.mem_read(sp, 20))
            mu.reg_write(UC_X86_REG_EAX, (fn(args) or 0) & 0xffffffff)
            mu.reg_write(UC_X86_REG_ESP, sp + 4 + pop); mu.reg_write(UC_X86_REG_EIP, ret)
        self.mu.hook_add(UC_HOOK_CODE, g, begin=addr, end=addr)
    def escribir(self, a):
        f = self.abiertos[self.mu.reg_read(UC_X86_REG_ECX)]; d = self.fs[f[0]]
        d[f[1]:f[1] + a[1]] = bytes(self.mu.mem_read(a[0], a[1])); f[1] += a[1]; return a[1]
    def leer(self, a):
        f = self.abiertos[self.mu.reg_read(UC_X86_REG_ECX)]; d = self.fs[f[0]]
        b = bytes(d[f[1]:f[1] + a[1]]); self.mu.mem_write(a[0], b); f[1] += len(b); return len(b)
    def correr(self, start, stop, regs=()):
        mu = self.mu
        mu.mem_write(STACK, struct.pack('<I', RET)); mu.reg_write(UC_X86_REG_ESP, STACK)
        for r, v in regs: mu.reg_write(r, v)
        mu.emu_start(start, stop, count=2000000)
        assert mu.reg_read(UC_X86_REG_EIP) == stop, hex(mu.reg_read(UC_X86_REG_EIP))
    def poner(self, regs):
        self.mu.mem_write(PO_N, struct.pack('<i', len(regs)))
        for i, r in enumerate(regs): self.mu.mem_write(PO_TAB + PO_REC * i, struct.pack('<hhBBBB', *r))
    def tabla(self):
        n = struct.unpack('<i', self.mu.mem_read(PO_N, 4))[0]
        return [struct.unpack('<hhBBBB', self.mu.mem_read(PO_TAB + PO_REC * i, PO_REC)) for i in range(n)]
    def mapa(self):
        m = bytes(self.mu.mem_read(PO_MAP, PO_MAPSZ))
        return {(i & 63, i >> 6): v for i, v in enumerate(m) if v}

OPC = bytes(range(0x18))
def guardar(g):
    g.fs[b'P.SAV'] = bytearray(b'PRINCIPIO'); g.abiertos[FRAME - 0x12c] = [b'P.SAV', 9]
    g.mu.mem_write(FRAME - 0x12c + 0x108, struct.pack('<I', 1)); g.mu.mem_write(OPTS, OPC)
    g.correr(0x439c72, 0x439c8f, regs=[(UC_X86_REG_EBP, FRAME)])
    return bytes(g.fs[b'P.SAV'])
def cargar_sav(g, datos, basura=True):
    g.fs[b'P.SAV'] = bytearray(datos); g.abiertos[FRAME - 0x120] = [b'P.SAV', 9]
    g.mu.mem_write(FRAME - 0x120 + 0x108, struct.pack('<I', 1)); g.mu.mem_write(OPTS, bytes(0x18))
    if basura:                                           # lo de una partida anterior: tiene que quedar lo del archivo
        g.poner([(1, 1, 0, 0, 0, 0xff)] * 3); g.mu.mem_write(PO_MAP + 65, b'\3')
    g.correr(0x439fda, 0x43a010, regs=[(UC_X86_REG_EBP, FRAME)])
    return g.tabla(), g.mapa(), bytes(g.mu.mem_read(OPTS, 0x18)) == OPC

print('-- guardar y cargar')
REGS = [(5, 7, 0, 0, 0x01, 0xff), (39, 29, 1, 0, 0x05, 0xff), (0, 0, 2, 1, 0xff, 3)]
g = Juego(); g.poner(REGS); g.mu.mem_write(VT_N, struct.pack('<i', 1))
sav = guardar(g)
VT_FIN = 0x21 + 8 + VT_MAX * 0x1c
ver('guardado: lo del original, VOTA y después POZO, cantidad y tabla',
    (sav[:0x21] == b'PRINCIPIO' + OPC, sav[0x21:0x25], struct.unpack_from('<i', sav, 0x25)[0], sav[VT_FIN:VT_FIN + 4],
     struct.unpack_from('<i', sav, VT_FIN + 4)[0], len(sav) - VT_FIN - 8),
    (True, b'VOTA', 1, b'POZO', 3, PO_MAX * PO_REC))
ver('  el original no escribe nada más', len(guardar(Juego(ORIG))), 0x21)
MAPA = {(5, 7): 1, (39, 29): 2, (0, 0): 3}
ver('cargado: la tabla vuelve y po_map se rearma', cargar_sav(Juego(), sav), (REGS, MAPA, True))
ver('  la Votación también', (lambda g: (cargar_sav(g, sav), struct.unpack('<i', g.mu.mem_read(VT_N, 4))[0])[1])(Juego()), 1)
ver('control: .SAV viejo (sin VOTA): vacía', cargar_sav(Juego(), sav[:0x21]), ([], {}, True))
ver('control: .SAV con VOTA y sin POZO: vacía', cargar_sav(Juego(), sav[:VT_FIN]), ([], {}, True))
ver('control: otra marca: vacía', cargar_sav(Juego(), sav[:VT_FIN] + b'XOZO' + sav[VT_FIN + 4:]), ([], {}, True))
ver('control: tabla cortada: vacía', cargar_sav(Juego(), sav[:-1]), ([], {}, True))
ver('control: cantidad mayor que el tope: vacía',
    cargar_sav(Juego(), sav[:VT_FIN + 4] + struct.pack('<i', PO_MAX + 1) + sav[VT_FIN + 8:]), ([], {}, True))
ver('control: VOTA cortada: tampoco lee POZO', cargar_sav(Juego(), sav[:0x30] + sav[VT_FIN:])[:2], ([], {}))
FUERA = [(40, 0, 0, 0, 0, 0xff), (0, 30, 0, 0, 0, 0xff), (-1, 2, 0, 0, 0, 0xff), (3, 4, 1, 0, 0, 0xff)]
g = Juego(); g.poner(FUERA)
ver('control: fuera del mapa no se marca (sí el de dentro)', cargar_sav(Juego(), guardar(g))[:2], (FUERA, {(3, 4): 4}))
ver('control: el original carga el .SAV nuevo igual que uno viejo', (lambda g: (
    g.fs.__setitem__(b'P.SAV', bytearray(sav)), g.abiertos.__setitem__(FRAME - 0x120, [b'P.SAV', 9]),
    g.mu.mem_write(FRAME - 0x120 + 0x108, struct.pack('<I', 1)),
    g.correr(0x439fda, 0x43a010, regs=[(UC_X86_REG_EBP, FRAME)]),
    bytes(g.mu.mem_read(OPTS, 0x18)) == OPC)[-1])(Juego(ORIG)), True)
print('MAL:', mal)
sys.exit(1 if mal else 0)
