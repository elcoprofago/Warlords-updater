# Prueba de juguete de la parte 6 de pozos (red): la tabla de pozos viaja en la transferencia inicial y entra en la
# suma de sincronía (po_nsend, po_nrecv, po_nrecvd, po_nsum de build.py), en unicorn, sobre el exe parcheado y el
# original.
# Uso: python prueba_pozosred.py [carpeta]   (por defecto C:\Warlords3; armarla antes con build.py)
# Envío: desde 0x4aa299 (detrás del bloque 8) con 0x4aa2c0 y 0x4baf20 de mentira: sale el bloque 9 con la tabla.
# Recepción: el 0x4aa340 real con los paquetes que armaría 0x4aa2c0 (de a 0x100 bytes): la tabla llega entera en dos
# paquetes y po_map queda rearmado. Controles: los bloques 5 (ruinas) y 8 siguen yendo a su lugar, antes y después;
# el original pega un bloque 9 detrás del anterior (por eso hacía falta atenderlo).
# Suma: 0x4aa520 con la tabla vacía da lo mismo que el original; cambiar un byte de la tabla o la cantidad la cambia.
import os, sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

DIR = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3'
STACK, RET = 0x1f0000, 0x100
MAPW, MAPH, MAPSH = 0x503e00, 0x503e02, 0x503e06
PO_MAX, PO_REC, PO_MAPSZ = 64, 8, 0x32000 // 10

def cargar(nombre):
    ruta = os.path.join(DIR, nombre)
    pe = pefile.PE(ruta if os.path.exists(ruta) else os.path.join(r'C:\Warlords3', nombre))
    return pe, pe.OPTIONAL_HEADER.ImageBase, bytes(pe.get_memory_mapped_image())
AV, ORIG = cargar('DarklordAV.exe'), cargar('Darklord.exe')
_, BASE, img = AV
PO_SAVE = BASE + img.index(b'POZO' + bytes(4 + PO_MAX * PO_REC)); PO_N, PO_TAB = PO_SAVE + 4, PO_SAVE + 8
PO_MAP = PO_SAVE + 8 + PO_MAX * PO_REC + 4

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
        mu.mem_write(MAPW, struct.pack('<hh', 40, 30)); mu.mem_write(MAPSH, b'\6')
        self.ganchos = {}
        mu.hook_add(UC_HOOK_CODE, self.gancho)
    def interceptar(self, va, fn, pop=0):
        self.ganchos[va] = (fn, pop)
    def gancho(self, mu, addr, size, _):
        if addr in self.ganchos:
            fn, pop = self.ganchos[addr]
            esp = mu.reg_read(UC_X86_REG_ESP)
            args = struct.unpack('<8I', mu.mem_read(esp + 4, 32))
            r = fn(args)
            ret = struct.unpack('<I', mu.mem_read(esp, 4))[0]
            mu.reg_write(UC_X86_REG_EAX, (r or 0) & 0xffffffff)
            mu.reg_write(UC_X86_REG_ESP, esp + 4 + pop); mu.reg_write(UC_X86_REG_EIP, ret)
    def llamar(self, va, *args):
        mu = self.mu
        esp = STACK - 0x100 - 4 * len(args)
        mu.mem_write(esp, struct.pack('<I', RET) + b''.join(struct.pack('<I', a & 0xffffffff) for a in args))
        mu.reg_write(UC_X86_REG_ESP, esp)
        mu.emu_start(va, RET, count=2000000)
        return mu.reg_read(UC_X86_REG_EAX)
    def correr(self, desde, hasta):
        self.mu.reg_write(UC_X86_REG_ESP, STACK - 0x100)
        self.mu.emu_start(desde, hasta, count=2000000)
    def rd(self, a, n): return bytes(self.mu.mem_read(a, n))
    def wr(self, a, b): self.mu.mem_write(a, b)
    def n(self): return struct.unpack('<i', self.rd(PO_N, 4))[0]

def tabla(k):   # k registros de juguete dentro del mapa de 40 x 30
    return b''.join(struct.pack('<hhBBBB', i % 40, i // 40 + 1, i % 4, i & 3, 1 << (i % 8), i % 8) for i in range(k))

# ---------------------------------------------------------------- envío
def envio(n, k=None):
    g = Juego()
    enviados = []
    g.interceptar(0x4aa2c0, lambda a: enviados.append((a[0], a[1] & 0xffff, a[2], a[3])))
    g.interceptar(0x4baf20, lambda a: enviados.append('fin'))
    g.wr(PO_N, struct.pack('<i', n)); g.wr(PO_TAB, tabla(k if k is not None else min(n, PO_MAX)))
    g.correr(0x4aa299, 0x4aa29e)
    return enviados
ver('envío: bloque 9 con 3 registros, después 0x4baf20', envio(3), [(9, 3, PO_TAB, 24), 'fin'])
ver('envío: tabla vacía igual sale (el receptor vacía la suya)', envio(0), [(9, 0, PO_TAB, 0), 'fin'])
ver('envío: tabla llena', envio(PO_MAX), [(9, PO_MAX, PO_TAB, PO_MAX * 8), 'fin'])
ver('envío: cantidad rota sale vacía', envio(500, 0), [(9, 0, PO_TAB, 0), 'fin'])

# ---------------------------------------------------------------- recepción
BUF = 0x180000
def recibir(g, bid, cant, datos):
    # lo que hace 0x4aa2c0: paquetes de hasta 0x100 bytes, cada uno con id, largo, cantidad y datos
    i = 0
    while True:
        trozo = datos[i:i + 0x100]
        g.wr(BUF, trozo + b'\0')
        g.llamar(0x4aa340, bid, len(trozo), cant, BUF)
        i += len(trozo)
        if i >= len(datos): break

def nueva(exe=AV):
    g = Juego(exe)
    g.wr(0x4ff02c, b'\1'); g.wr(0x4ff030, struct.pack('<h', -1)); g.wr(0x4ff03c, bytes(4))
    return g

ruinas, ult = bytes(i % 251 + 1 for i in range(0xb8 * 2)), bytes([0x5a]) * 0xd70
t40 = tabla(40)
g = nueva()
g.wr(PO_N, struct.pack('<i', 7)); g.wr(PO_TAB, tabla(7)); g.wr(PO_MAP, b'\x07' * 16)   # lo generado en esta PC
recibir(g, 5, 2, ruinas)
recibir(g, 8, 0x28, ult)
recibir(g, 9, 40, t40)
ver('recepción: cantidad', g.n(), 40)
ver('recepción: tabla (2 paquetes)', g.rd(PO_TAB, 40 * 8) == t40, True)
esperado = bytearray(PO_MAPSZ)
for i in range(40):
    esperado[((i // 40 + 1) << 6) + i % 40] = i + 1
ver('recepción: po_map rearmado', g.rd(PO_MAP, PO_MAPSZ) == bytes(esperado), True)
ver('control: ruinas en su lugar', (struct.unpack('<h', g.rd(0x558872, 2))[0], g.rd(0x558874, 0xb8 * 2) == ruinas), (2, True))
ver('control: bloque 8 en su lugar', g.rd(0x55f030, 0xd70) == ult, True)
recibir(g, 5, 1, ruinas[:0xb8])
ver('control: un bloque después del 9 va a su lugar', (struct.unpack('<h', g.rd(0x558872, 2))[0], g.n()), (1, 40))
g = nueva()
g.wr(PO_N, struct.pack('<i', 7)); g.wr(PO_TAB, tabla(7))
recibir(g, 9, 0, b'')
ver('recepción: tabla vacía vacía la de esta PC', (g.n(), g.rd(PO_MAP, PO_MAPSZ) == bytes(PO_MAPSZ)), (0, True))
g = nueva(ORIG)
recibir(g, 8, 0x28, ult)
recibir(g, 9, 3, tabla(3))
ver('original: el bloque 9 se pega detrás del 8', g.rd(0x55f030 + 0xd70, 24) == tabla(3), True)

# ---------------------------------------------------------------- suma de sincronía
def suma(exe=AV, n=0, t=b''):
    g = Juego(exe)
    if exe is AV: g.wr(PO_N, struct.pack('<i', n)); g.wr(PO_TAB, t)
    return g.llamar(0x4aa520)
base = suma(ORIG)
ver('suma: tabla vacía = original', suma(), base)
s3 = suma(n=3, t=tabla(3))
ver('suma: con tabla cambia', s3 != base, True)
t = bytearray(tabla(3)); t[14] ^= 0x40
ver('suma: un bit de la tabla la cambia', suma(n=3, t=bytes(t)) != s3, True)
ver('suma: la cantidad la cambia', suma(n=4, t=tabla(3) + bytes(8)) != s3, True)
ver('suma: lo de más allá de la cantidad no cuenta', suma(n=3, t=tabla(3) + b'\x77' * 8), s3)

print('TODO BIEN' if not mal else f'{mal} MAL')
sys.exit(1 if mal else 0)
