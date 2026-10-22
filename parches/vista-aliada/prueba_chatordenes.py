# Prueba de las órdenes por chat a un aliado de la computadora (barra «#n», paquete 0x2a2; ch_* y or_recv de build.py)
# sobre el exe parcheado, en unicorn, con la partida Tanda_Border_Alianzas.
# Uso: python prueba_chatordenes.py [DarklordAV.exe] [partida.SAV]
# Se llama a la barra de chat original (0x409170) con el texto, con stubs: 0x4dd3a0 (máquina de esta PC), 0x4dd3b0
# (difusión: se anota el paquete) y 0x4ba990 (chat nativo: se anota bando, máquinas destino y texto). La recepción se
# prueba entrando al despachador parcheado (el «ja» de 0x4b6a22) con un paquete armado, hasta 0x4b85bb.
import sys, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

EXE = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe'
sav = open(sys.argv[2] if len(sys.argv) > 2 else r'C:\Warlords3\SAVES\Tanda_Border_Alianzas.SAV', 'rb').read()
CITIES, DIPLO, SIDE = 0x537e2c, 0x55ee4c, 0x1f8
SIDE_ON, SIDE_HUMAN, SIDE_MACHINE, SIDE_NAME = 0x536b30, 0x536c12, 0x536b33, 0x536b34

pe = pefile.PE(EXE); img = pe.get_memory_mapped_image()
def rva(va): return va - 0x400000
# direcciones del parche: or_recv por el «ja» de 0x4b6a22, tl_recv por su «jne» (cmp eax, imm32 = 5 bytes; jne rel32),
# OR_TAB por ai_ord (call de 0x40edf1; su cmp byte ptr [eax*8 + OR_TAB + 1], 1 está en +16)
assert img[rva(0x4b6a22):rva(0x4b6a22) + 2] == b'\x0f\x87'
OR_RECV = 0x4b6a28 + struct.unpack_from('<i', img, rva(0x4b6a24))[0]
# desde 1.0.51.0 el «ja» va primero a tr_recv (cmp eax, 0x2ab / jne or_recv): se sigue la cadena
if img[rva(OR_RECV)] == 0x3d and struct.unpack_from('<I', img, rva(OR_RECV) + 1)[0] == 0x2ab:
    OR_RECV = OR_RECV + 11 + struct.unpack_from('<i', img, rva(OR_RECV) + 7)[0]
assert img[rva(OR_RECV) + 5:rva(OR_RECV) + 7] == b'\x0f\x85', 'or_recv no empieza con cmp eax / jne tl_recv'
TL_RECV = OR_RECV + 11 + struct.unpack_from('<i', img, rva(OR_RECV) + 7)[0]
AI_ORD = 0x40edf6 + struct.unpack_from('<i', img, rva(0x40edf2))[0]
OR_TAB = struct.unpack_from('<I', img, rva(AI_ORD) + 19)[0] - 1
assert img[rva(0x4091ea):rva(0x4091ea) + 2] == b'\x0f\x85', 'la barra no tiene el salto parcheado en 0x4091ea'

mu = Uc(UC_ARCH_X86, UC_MODE_32)
mu.mem_map(0x400000, (len(img) + 0xfff) & ~0xfff); mu.mem_write(0x400000, img)
mu.mem_map(0x10000000, 0x100000); mu.mem_map(0xdead0000, 0x1000); mu.mem_write(0xdead0000, b'\xc3' * 0x1000)
off = 0x6d
for va, n in ((0x503e00, 0x12), (0x503e58, 0x32000), (0x535ed0, 0xa96), (0x536b30, 0x2d894)):
    mu.mem_write(va, sav[off:off + n]); off += n
def rd(a, n): return bytes(mu.mem_read(a, n))
def cstr(a): return rd(a, 80).split(b'\0')[0]
def w(a, fmt, *v): mu.mem_write(a, struct.pack(fmt, *v))

state = {'machine': 0}
pkts, msgs = [], []
def stub(addr, fn):
    def h(m, a, size, ud):
        sp = m.reg_read(UC_X86_REG_ESP)
        ret = struct.unpack('<I', m.mem_read(sp, 4))[0]; args = struct.unpack('<6I', m.mem_read(sp + 4, 24))
        m.reg_write(UC_X86_REG_EAX, fn(args) & 0xffffffff)
        m.reg_write(UC_X86_REG_ESP, sp + 4); m.reg_write(UC_X86_REG_EIP, ret)
    mu.hook_add(UC_HOOK_CODE, h, begin=addr, end=addr)
stub(0x4dd3a0, lambda a: state['machine'])
stub(0x4dd3b0, lambda a: pkts.append((a[0], rd(a[1], a[2]))) or 1)
stub(0x4ba990, lambda a: msgs.append((a[0] & 0xff, tuple(i for i, b in enumerate(rd(a[1], 8)) if b), cstr(a[2]))) or 1)
# importaciones: _stricmp y sprintf (solo %s)
names, k = {}, 0
mu.mem_map(0xdead1000, 0x10000)
for d in pe.DIRECTORY_ENTRY_IMPORT:
    for imp in d.imports:
        st = 0xdead1000 + 16 * k; k += 1
        mu.mem_write(imp.address, struct.pack('<I', st)); names[st] = (imp.name or b'?').decode()
def imph(m, a, size, ud):
    n = names.get(a); sp = m.reg_read(UC_X86_REG_ESP)
    ret = struct.unpack('<I', m.mem_read(sp, 4))[0]; args = struct.unpack('<4I', m.mem_read(sp + 4, 16))
    if n == '_stricmp':
        x, y = cstr(args[0]).lower(), cstr(args[1]).lower(); r = (x > y) - (x < y)
    elif n == 'sprintf':
        s = cstr(args[1]).replace(b'%s', cstr(args[2])) + b'\0'; m.mem_write(args[0], s); r = len(s) - 1
    else: raise RuntimeError('importación no emulada: ' + n)
    m.reg_write(UC_X86_REG_EAX, r & 0xffffffff); m.reg_write(UC_X86_REG_ESP, sp + 4); m.reg_write(UC_X86_REG_EIP, ret)
mu.hook_add(UC_HOOK_CODE, imph, begin=0xdead1000, end=0xdead1000 + 16 * k)

def call(addr, args):
    sp = 0x10080000
    for a in reversed(args): sp -= 4; mu.mem_write(sp, struct.pack('<I', a))
    sp -= 4; mu.mem_write(sp, struct.pack('<I', 0xdead0000)); mu.reg_write(UC_X86_REG_ESP, sp)
    mu.emu_start(addr, 0xdead0000, count=10_000_000)

fallas = 0
def check(nombre, cond, detalle=''):
    global fallas
    print(('OK   ' if cond else 'FALLA'), nombre, '' if cond else detalle)
    fallas += not cond

# ---------------------------------------------------------------- escenario
# bando 0 humano en la máquina 0 (esta PC); 1 de la computadora, corre en la máquina 1; 2 humano en la máquina 1;
# 3 de la computadora en la máquina 0. Aliados 0-1-2; 3 en guerra con todos.
ON = (0, 1, 2, 3)
for p in range(8):
    b = SIDE_ON + p * SIDE
    w(b, '<B', p in ON); w(SIDE_HUMAN + p * SIDE, '<h', -1 if p in (0, 2) else 2)
    w(SIDE_MACHINE + p * SIDE, '<B', {0: 0, 1: 1, 2: 1, 3: 0}.get(p, 0))
for a in range(8):
    for b in range(8):
        w(DIPLO + a * 56 + b, '<B', 0 if a in (0, 1, 2) and b in (0, 1, 2) or a == b else 2)
w(0x537ce8, '<h', 0)
ncity = struct.unpack('<h', rd(0x537e2a, 2))[0]
C = next(i for i in range(5, ncity) if rd(CITIES + i * 0xde + 0xa4, 1)[0] and cstr(CITIES + i * 0xde + 4))
CNAME = cstr(CITIES + C * 0xde + 4)
NAME2 = b'Rojos'; mu.mem_write(SIDE_NAME + 2 * SIDE, NAME2 + b'\0')
print('ciudad', C, CNAME, '| bando 3 se llama', NAME2.decode())
TXT = 0x10090000

def barra(texto):
    pkts.clear(); msgs.clear(); state['machine'] = 0
    mu.mem_write(TXT, texto.encode('latin1') + b'\0')
    call(0x409170, [TXT])
def orden(): return [struct.unpack('<4h', p) for t, p in pkts if t == 0x2a2]
def eco_ok(texto): return msgs[:1] == [(0, (0,), texto[2:].encode('latin1'))]
AYUDA = b'Ordenes: ataca CIUDAD / ataca a BANDO / mandame refuerzos'

# ---------------------------------------------------------------- barra (PC del humano)
t = '#2 ataca ' + CNAME.decode('latin1') + '  '
barra(t)
check('«#2 ataca CIUDAD»: paquete 0x2a2 (0, 1, tipo 1, ciudad), eco propio y nada más', orden() == [(0, 1, 1, C)]
      and eco_ok(t) and len(msgs) == 1 and len(pkts) == 1, (pkts, msgs))
barra('#2 ATACA ' + CNAME.decode('latin1').upper())
check('mayúsculas: la misma orden', orden() == [(0, 1, 1, C)], pkts)
barra('#2 ataca a 3')
check('«#2 ataca a 3»: tipo 2, bando 2', orden() == [(0, 1, 2, 2)], (pkts, msgs))
barra('#2 atac\xe1 a rojos')
check('«#2 atacá a rojos» (nombre del bando, con tilde): tipo 2, bando 2', orden() == [(0, 1, 2, 2)], (pkts, msgs))
barra('#2 mandame refuerzos')
check('«#2 mandame refuerzos»: tipo 3, objetivo el bando que la da', orden() == [(0, 1, 3, 0)], (pkts, msgs))
barra('#2 hola')
check('orden desconocida: sin paquete, ayuda con el color del bando 1 solo en esta máquina', not orden()
      and msgs[1:] == [(1, (0,), AYUDA)], msgs)
barra('#2 ataca Ningunlado')
check('ciudad inexistente: ayuda', not orden() and msgs[1:] == [(1, (0,), AYUDA)], msgs)
barra('#2 ataca a 1')
check('atacar a uno mismo: ayuda', not orden() and msgs[1:] == [(1, (0,), AYUDA)], msgs)
barra('#2 ataca')
check('sin objetivo: ayuda', not orden() and msgs[1:] == [(1, (0,), AYUDA)], msgs)
barra('#4 ataca a 3')
check('a un bando de la computadora no aliado: «No somos aliados», sin paquete', not orden()
      and msgs[1:] == [(3, (0,), b'No somos aliados')], msgs)
barra('#3 hola')
check('control: a un humano sigue el chat nativo (0x4ba990 del bando 0 a las máquinas 0 y 1), sin 0x2a2',
      not orden() and msgs == [(0, (0, 1), b' hola')], (pkts, msgs))
barra('#6 hola')
check('control: a un bando inactivo, nada', not pkts and not msgs, (pkts, msgs))

# ---------------------------------------------------------------- recepción
PK = 0x10095000
def recibir(maquina, de, a, tipo, obj, desde=None, ptipo=0x2a2):
    msgs.clear(); state['machine'] = maquina
    mu.mem_write(OR_TAB, bytes(64))
    mu.mem_write(PK, struct.pack('<hhhhhh4h', 0, 0, ptipo, de if desde is None else desde, 0, 0, de, a, tipo, obj))
    mu.reg_write(UC_X86_REG_ESI, PK); mu.reg_write(UC_X86_REG_EAX, ptipo + 8)
    mu.reg_write(UC_X86_REG_ESP, 0x10080000)
    hit = []
    h = mu.hook_add(UC_HOOK_CODE, lambda m, ad, s, u: hit.append(1) or m.emu_stop(), begin=TL_RECV, end=TL_RECV)
    mu.emu_start(0x4b6a16, 0x4b85bb, count=1_000_000)
    mu.hook_del(h)
    return rd(OR_TAB, 64), bool(hit)
def fila(tab, p): return tab[p * 8], tab[p * 8 + 1], struct.unpack_from('<h', tab, p * 8 + 2)[0], tab[p * 8 + 4]
tab, _ = recibir(1, 0, 1, 1, C)
check('en la PC que corre el bando 1: OR_TAB[1] = (1, 3, ciudad, 0) y contesta «Ok, ataco CIUDAD» a la máquina 0',
      fila(tab, 1) == (1, 3, C, 0) and msgs == [(1, (0,), b'Ok, ataco ' + CNAME)], (fila(tab, 1), msgs))
tab, _ = recibir(0, 0, 1, 1, C)
check('en otra PC: llena OR_TAB igual y no contesta', fila(tab, 1) == (1, 3, C, 0) and not msgs, (fila(tab, 1), msgs))
tab, _ = recibir(1, 0, 1, 2, 2)
check('tipo 2: «Ok, ataco a Rojos»', fila(tab, 1) == (2, 3, 2, 0) and msgs == [(1, (0,), b'Ok, ataco a Rojos')], msgs)
tab, _ = recibir(1, 0, 1, 3, 0)
check('tipo 3: «Ok, te mando refuerzos»', fila(tab, 1) == (3, 3, 0, 0)
      and msgs == [(1, (0,), b'Ok, te mando refuerzos')], msgs)
for nombre, args in (('la máquina que lo manda no es la del bando que da la orden', (1, 0, 1, 1, C, 1)),
                     ('el destino es humano', (1, 0, 2, 1, C)),
                     ('no son aliados', (0, 0, 3, 1, C)),
                     ('el que la da es de la computadora', (1, 3, 1, 1, C)),
                     ('ciudad fuera de rango', (1, 0, 1, 1, ncity)),
                     ('refuerzos para otro bando', (1, 0, 1, 3, 2)),
                     ('tipo desconocido', (1, 0, 1, 4, 0))):
    tab, _ = recibir(*args)
    check('rechazado: ' + nombre, tab == bytes(64) and not msgs, (tab[:16], msgs))
tab, hit = recibir(1, 0, 1, 1, C, ptipo=0x2a1)
check('control: otro paquete (0x2a1) sigue a tl_recv sin tocar OR_TAB', hit and tab == bytes(64), (hit, tab[:16]))

print('TODO OK' if not fallas else f'{fallas} FALLA(S)')
sys.exit(1 if fallas else 0)
