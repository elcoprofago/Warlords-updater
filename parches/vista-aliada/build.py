# Arma DarklordAV.exe y DATA\WAR3AV.RES a partir de los originales (que solo se leen).
# Vista aliada compartida: bit 0x80 de [0x53c38e] (opciones de partida).
# Uso: python build.py [carpeta_salida]   (por defecto C:\Warlords3; crea DATA\ si falta)
import struct, sys, os
import keystone, capstone

SRC_EXE = r'C:\Warlords3\Darklord.exe'
SRC_RES = r'C:\Warlords3\DATA\War3.RES'
OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3'
OUT_EXE = os.path.join(OUT_DIR, 'DarklordAV.exe')
OUT_RES = os.path.join(OUT_DIR, 'DATA', 'WAR3AV.RES')
RES_NAME = b'DATA\\WAR3AV.RES'

BASE = 0x400000
ks = keystone.Ks(keystone.KS_ARCH_X86, keystone.KS_MODE_32)
cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

def asm(src, addr):
    enc, _ = ks.asm(src, addr)
    return bytes(enc)

exe = bytearray(open(SRC_EXE, 'rb').read())
res = bytearray(open(SRC_RES, 'rb').read())

# ---------------------------------------------------------------- PE: sección nueva
e_lfanew = struct.unpack_from('<I', exe, 0x3c)[0]
fh = e_lfanew + 4
nsec = struct.unpack_from('<H', exe, fh + 2)[0]
opt = fh + 20
sizeopt = struct.unpack_from('<H', exe, fh + 16)[0]
sectab = opt + sizeopt
assert nsec == 6
last = sectab + 40 * (nsec - 1)
l_vsz, l_va, l_rsz, l_raw = struct.unpack_from('<IIII', exe, last + 8)
SECT_ALIGN, FILE_ALIGN = struct.unpack_from('<II', exe, opt + 32)
new_va = (l_va + l_vsz + SECT_ALIGN - 1) // SECT_ALIGN * SECT_ALIGN
new_raw = len(exe)
assert new_raw % FILE_ALIGN == 0 and new_raw == l_raw + l_rsz
hdr = sectab + 40 * nsec
assert exe[hdr:hdr + 40] == bytes(40), 'no hay lugar para otra cabecera de sección'
SIZEOFHEADERS = struct.unpack_from('<I', exe, opt + 60)[0]
assert hdr + 40 <= SIZEOFHEADERS
CAVE = BASE + new_va

# ---------------------------------------------------------------- código nuevo
OPT = 0x53c38e      # byte de opciones de vista: 0x10 Hidden Map, 0x80 vista aliada (nueva)
DIPLO_OPT = 0x53c393  # & 8 = Diplomacy activada
DIPLO = 0x55ee4c    # [DIPLO + a*56 + b]: 0 aliados, 1 paz, 2 guerra
REDRAW = 0x4a2170

# edx <- máscara de los aliados de ecx (sin ecx). Usa eax; preserva ecx, ebx, esi, edi, ebp.
ALLIES = f'''
    xor edx, edx
    cmp ecx, 8
    jae allies_end
    test byte ptr [{OPT:#x}], 0x80
    jz allies_end
    test byte ptr [{OPT:#x}], 0x10
    jz allies_end
    test byte ptr [{DIPLO_OPT:#x}], 8
    jz allies_end
    push edi
    imul edi, ecx, 56
    xor eax, eax
allies_loop:
    cmp eax, ecx
    je allies_next
    cmp byte ptr [edi + eax + {DIPLO:#x}], 0
    jne allies_next
    push eax
    imul eax, eax, 56
    cmp byte ptr [eax + ecx + {DIPLO:#x}], 0
    pop eax
    jne allies_next
    bts edx, eax
allies_next:
    inc eax
    cmp eax, 8
    jb allies_loop
    pop edi
allies_end:
'''

caves = {}
def place(name, src):
    addr = CAVE + sum(len(b) for b in caves.values())
    addr = (addr + 15) & ~15
    pad = addr - (CAVE + sum(len(b) for b in caves.values()))
    if pad and caves:
        k = list(caves)[-1]; caves[k] = caves[k] + b'\xcc' * pad
    code = asm(src, addr)
    caves[name] = code
    return addr

# Byte +5 de cada casilla (siempre 0 en el juego original, se guarda con la partida): bit p = el jugador p conoce
# la casilla solo porque se la pasó un aliado. Lo propio de p es entonces [casilla+4] & ~[casilla+5].

# 1) Revelado (reemplaza 0x441c9f..0x441cc9 de 0x441b30, caso de jugador >= 0).
#    esi = casilla, bl = "ya pedí redibujo", [esp+0x44] = jugador.
#    p la ve por sí mismo (deja de ser prestada); los aliados que no la tenían la reciben prestada.
reveal = place('reveal', f'''
    movzx ecx, byte ptr [esp + 0x44]
    {ALLIES.replace('allies_', 'rv_')}
    mov al, byte ptr [esi + 4]
    not al
    and al, dl
    or byte ptr [esi + 5], al
    mov al, 1
    shl al, cl
    not al
    and byte ptr [esi + 5], al
    bts edx, ecx
    mov al, byte ptr [esi + 4]
    and al, dl
    cmp al, dl
    je rv_set
    test bl, bl
    jne rv_set
    mov bl, 1
    push edx
    call {REDRAW:#x}
    pop edx
rv_set:
    or byte ptr [esi + 4], dl
    jmp 0x441cc9
''')

# 2) Inicio de turno: antes de 0x442470(jugador), se rehace lo que p conoce prestado: recibe lo propio de sus
#    aliados actuales y pierde lo que solo conocía por quien ya no es aliado.
turn = place('turn', f'''
    push ebx
    push esi
    push edi
    push ebp
    movzx ecx, byte ptr [esp + 0x14]
    cmp ecx, 8
    jae tn_out
    test byte ptr [{OPT:#x}], 0x80
    jz tn_out
    test byte ptr [{OPT:#x}], 0x10
    jz tn_out
    test byte ptr [{DIPLO_OPT:#x}], 8
    jz tn_out
    {ALLIES.replace('allies_', 'tn_')}
    mov ebx, 1
    shl ebx, cl
    mov bh, bl
    not bh
    xor ebp, ebp
tn_y:
    movsx eax, word ptr [0x503e02]
    cmp ebp, eax
    jge tn_redraw
    lea esi, [ebp + ebp*4]
    add esi, esi
    mov cl, byte ptr [0x503e06]
    shl esi, cl
    add esi, 0x503e58
    movsx edi, word ptr [0x503e00]
    test edi, edi
    jle tn_ynext
tn_x:
    mov al, byte ptr [esi + 4]
    mov ah, byte ptr [esi + 5]
    not ah
    and ah, al
    test ah, bl
    jnz tn_skip
    test ah, dl
    jz tn_drop
    or byte ptr [esi + 4], bl
    or byte ptr [esi + 5], bl
    jmp tn_skip
tn_drop:
    test byte ptr [esi + 5], bl
    jz tn_skip
    and byte ptr [esi + 4], bh
    and byte ptr [esi + 5], bh
tn_skip:
    add esi, 10
    dec edi
    jnz tn_x
tn_ynext:
    inc ebp
    jmp tn_y
tn_redraw:
    call {REDRAW:#x}
tn_out:
    pop ebp
    pop edi
    pop esi
    pop ebx
    jmp 0x442470
''')

# 2b) Inicio de partida (0x441933, borrado de lo explorado): borrar también lo prestado.
mapinit = place('mapinit', '''
    mov byte ptr [ebp + ecx*2 + 0x503e5c], bl
    mov byte ptr [ebp + ecx*2 + 0x503e5d], 0
    jmp 0x44193a
''')

# 2c) Revelado de un rectángulo para un jugador (0x41fb98, dl = bit del jugador): pasa a ser propio.
rect = place('rect', '''
    or byte ptr [ebp + eax*2 + 0x503e5c], dl
    not dl
    and byte ptr [ebp + eax*2 + 0x503e5d], dl
    not dl
    jmp 0x41fb9f
''')

# 3) Clic en la casilla nueva (id 59) del diálogo Customize Options. eax = id - 2.
NEWCHK = 59
click = place('click', f'''
    cmp eax, {NEWCHK - 2}
    jne 0x427d43
    mov eax, dword ptr [esi + 8]
    push 0
    shl al, 7
    xor al, byte ptr [0x503d02]
    and al, 0x80
    xor byte ptr [0x503d02], al
    call 0x428370
    add esp, 4
    mov ecx, 0x588bd0
    call 0x4d82a0
    xor ax, ax
    pop edi
    pop esi
    add esp, 0x60
    ret
''')

# 4) Refresco del diálogo: después de la casilla Fog (id 7), poner la nueva.
refresh = place('refresh', f'''
    push dword ptr [esp + 8]
    push dword ptr [esp + 8]
    call 0x4dd000
    add esp, 8
    xor eax, eax
    test byte ptr [0x503d02], 0x80
    setnz al
    push eax
    push {NEWCHK}
    call 0x4dd000
    add esp, 8
    ret
''')

# 5) Reporte View Game Options: después de Timed Vectoring (id 0x2f), el indicador nuevo.
NEWIND = 49
report = place('report', f'''
    push dword ptr [esp + 8]
    push dword ptr [esp + 8]
    call 0x4dd040
    add esp, 8
    mov eax, 0x1d
    test byte ptr [{OPT:#x}], 0x80
    jz rp_off
    mov eax, 0x1c
rp_off:
    push eax
    push {NEWIND}
    call 0x4dd040
    add esp, 8
    ret
''')

# 6) Alta del diálogo (0x427ea0): todos los controles nacen ocultos (estado 1 en [ctrl+0x2c]) y
#    la rutina habilita uno por uno con 0x4dcec0(id, 0). Junto con Fog (id 7), habilitar la nueva.
init = place('init', f'''
    push dword ptr [esp + 8]
    push dword ptr [esp + 8]
    call 0x4dcec0
    add esp, 8
    push 0
    push {NEWCHK}
    call 0x4dcec0
    add esp, 8
    ret
''')

blob = b''.join(caves.values())
raw_size = (len(blob) + FILE_ALIGN - 1) // FILE_ALIGN * FILE_ALIGN
exe += blob + b'\0' * (raw_size - len(blob))

struct.pack_into('<8sIIIIIIHHI', exe, hdr, b'.avis\0\0\0', len(blob), new_va, raw_size, new_raw,
                 0, 0, 0, 0, 0x60000020)
struct.pack_into('<H', exe, fh + 2, nsec + 1)
size_of_image = (new_va + len(blob) + SECT_ALIGN - 1) // SECT_ALIGN * SECT_ALIGN
struct.pack_into('<I', exe, opt + 56, size_of_image)
code_size = struct.unpack_from('<I', exe, opt + 4)[0]
struct.pack_into('<I', exe, opt + 4, code_size + raw_size)

# ---------------------------------------------------------------- parches en .text
def va2off(va):
    for k in range(nsec):
        s = sectab + 40 * k
        vsz, va_, rsz, raw = struct.unpack_from('<IIII', exe, s + 8)
        if BASE + va_ <= va < BASE + va_ + max(vsz, rsz):
            return raw + va - BASE - va_
    raise ValueError(hex(va))

def patch(va, expect, new):
    o = va2off(va)
    assert bytes(exe[o:o + len(expect)]) == expect, (hex(va), exe[o:o + len(expect)].hex(), expect.hex())
    assert len(new) <= len(expect)
    exe[o:o + len(new)] = new
    exe[o + len(new):o + len(expect)] = b'\x90' * (len(expect) - len(new))

def rel(va, n):  # bytes originales
    o = va2off(va); return bytes(exe[o:o + n])

patch(0x441c9f, rel(0x441c9f, 0x441cc9 - 0x441c9f), asm(f'jmp {reveal:#x}', 0x441c9f))
patch(0x4223ad, asm('call 0x442470', 0x4223ad), asm(f'call {turn:#x}', 0x4223ad))
patch(0x441933, bytes.fromhex('889c4d5c3e5000'), asm(f'jmp {mapinit:#x}', 0x441933))
patch(0x41fb98, bytes.fromhex('0894455c3e5000'), asm(f'jmp {rect:#x}', 0x41fb98))
patch(0x427877, asm('ja 0x427d43', 0x427877), asm(f'ja {click:#x}', 0x427877))
patch(0x428643, asm('call 0x4dd000', 0x428643), asm(f'call {refresh:#x}', 0x428643))
patch(0x43f40f, asm('call 0x4dd040', 0x43f40f), asm(f'call {report:#x}', 0x43f40f))
patch(0x428074, bytes.fromhex('6a006a07') + asm('call 0x4dcec0', 0x428078),
      bytes.fromhex('6a006a07') + asm(f'call {init:#x}', 0x428078))
patch(0x4fb70c, b'DATA\\WAR3.RES\0\0\0', RES_NAME + b'\0' * (16 - len(RES_NAME)))

# ---------------------------------------------------------------- War3.RES
SZ = {1: 0x80, 2: 0x9c, 3: 0x6c, 4: 0xac, 5: 0xa8, 6: 0xa0, 7: 0x1c, 8: 0x1c, 9: 0x1c, 0xa: 0x20,
      0xb: 0x64, 0xc: 0x64, 0xd: 0x3c, 0xe: 0x30, 0x11: 0x14, 0x12: 0x68, 0x13: 0x28, 0x14: 0x2c, 0x15: 0xac}

def find_dialog(d, did):
    o = 8
    while o + 20 <= len(d):
        h = struct.unpack_from('<5I', d, o)
        if h[0] == 7 and h[1] == did: return o, h
        o += 20 + h[4]
    raise KeyError(did)

def records(d, did):
    o, h = find_dialog(d, did); p = o + 20; out = {}
    for _ in range(h[2]):
        t, i = struct.unpack_from('<II', d, p)
        out[i] = (p, t)
        p += 4 + SZ[t]
    assert p == o + 20 + h[4]
    return out

def setstr(rec, off, size, s):
    b = s.encode('latin1'); assert len(b) < size
    rec[off:off + size] = b + b'\0' * (size - len(b))

def append(d, did, new):
    o, h = find_dialog(d, did)
    end = o + 20 + h[4]
    d[end:end] = new
    struct.pack_into('<III', d, o + 8, h[2] + len(new_list[did]), h[3] + len(new), h[4] + len(new))

new_list = {}

# Diálogo 9 (Customize Options): casilla nueva clonada de Fog of War (id 7), debajo de ella.
r9 = records(res, 9)
p, t = r9[7]; assert t == 5
chk = bytearray(res[p:p + 4 + SZ[5]])
struct.pack_into('<IIII', chk, 4, NEWCHK, 311, 162, 1)
struct.pack_into('<I', chk, 0x14, 85)
setstr(chk, 0x1c, 16, 'Allied View')
setstr(chk, 0x2c, 64, 'Allies share the explored map (Hidden Map)')
setstr(chk, 0x9c, 16, 'Allied View')
new_list[9] = [chk]

# Diálogo 115 (reporte View Game Options): fila nueva "Shared Allied View" debajo de Fog of War.
# Las dos columnas pasan de 25 a 21 píxeles entre filas para que entren 8.
r115 = records(res, 115)
col1 = [(9, 23), (10, 24), (11, 25), (12, 26), (13, 27), (14, 28), ('new', 'new'), (15, 29)]
col2 = [(16, 30), (17, 31), (18, 32), (19, 33), (20, 34), (21, 35), (22, 36)]
NEWLBL = 48
p, t = r115[14]; assert t == 0x12
lbl = bytearray(res[p:p + 4 + SZ[0x12]])
struct.pack_into('<I', lbl, 4, NEWLBL)
setstr(lbl, 0x2c, 64, 'Shared Allied View')
p, t = r115[28]; assert t == 0x11
ind = bytearray(res[p:p + 4 + SZ[0x11]])
struct.pack_into('<I', ind, 4, NEWIND)
for col in (col1, col2):
    for k, (li, ii) in enumerate(col):
        y = 130 + 21 * k
        if li == 'new':
            struct.pack_into('<I', lbl, 0xc, y); struct.pack_into('<I', ind, 0xc, y - 2)
        else:
            struct.pack_into('<I', res, r115[li][0] + 0xc, y)
            struct.pack_into('<I', res, r115[ii][0] + 0xc, y - 2)
new_list[115] = [lbl, ind]

for did in (115, 9):   # el 115 está después del 9: tocarlo primero no corre el offset del 9
    append(res, did, b''.join(new_list[did]))

# ---------------------------------------------------------------- escribir (solo archivos nuevos)
for path in (OUT_EXE, OUT_RES):
    assert os.path.abspath(path).lower() not in (os.path.abspath(SRC_EXE).lower(), os.path.abspath(SRC_RES).lower())
os.makedirs(os.path.dirname(OUT_RES), exist_ok=True)
open(OUT_EXE, 'wb').write(exe)
open(OUT_RES, 'wb').write(res)
print('caves', {k: hex(CAVE + sum(len(caves[j]) for j in list(caves)[:list(caves).index(k)])) for k in caves})
print('exe', OUT_EXE, len(exe), 'res', OUT_RES, len(res))
