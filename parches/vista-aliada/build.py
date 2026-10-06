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

# Ciudades compartidas: bit 0x01 del byte 25 del bloque de opciones (0x53c38c, 0x2a bytes). Ese byte no lo lee
# ningún código, vale 0 en los 28 .SAV y en todos los OPT*.DAT/OPTIONS.* de C:\Warlords3, y viaja con el bloque
# entero (diálogo 0x503d00, partida guardada, red 0x4b8f00). El bit 0x40 de OPT NO sirve: viene puesto en
# OPTIONS.NET, OPTIONSFILE y 14 de las 28 partidas.
SHOPT = 0x53c38c + 25
SHOPT_DLG = 0x503d00 + 25

# edx <- máscara de los aliados mutuos de ecx (sin ecx). Usa eax; preserva ecx, ebx, esi, edi, ebp.
ALLIES_CORE = '''
    xor edx, edx
    cmp ecx, 8
    jae allies_end
    push edi'''
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
    push edi'''
ALLIES_TAIL = f'''
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
ALLIES_CORE += ALLIES_TAIL
ALLIES += ALLIES_TAIL

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
sync = place('sync', f'''
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
    ret
''')

# 2a) Llamadores de sync(p). Inicio de turno: antes de 0x442470(p). Y la copia de trabajo 0x441cf0(p, f), que
#     pasa lo explorado de p (+4) a los bits 0x800/0x1000 de la palabra +2 (lo que se dibuja durante el turno y
#     0x441eb0 vuelve a sumar a +4 al terminarlo). El bucle de turnos la hace ANTES de 0x4221a0 (0x4c08d0,
#     0x4c0b21): sin este gancho la copia llevaba lo prestado ya caducado y el cierre del turno lo volvía propio.
turn = place('turn', f'''
    push dword ptr [esp + 4]
    call {sync:#x}
    add esp, 4
    jmp 0x442470
''')
vcopy = place('vcopy', f'''
    push dword ptr [esp + 4]
    call {sync:#x}
    add esp, 4
    sub esp, 8
    xor ecx, ecx
    jmp 0x441cf5
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

# ---- Ciudades compartidas por la alianza
# partners(i) -> eax = máscara de los socios de la ciudad i: aliados mutuos y vivos del dueño que exploraron
# por sí mismos ([casilla+4] & ~[casilla+5], no lo prestado por vista aliada) las 4 casillas de la ciudad.
# Requiere la opción, Hidden Map y Diplomacy; la ciudad viva y con dueño < 8. Preserva ebx, esi, edi, ebp.
CITIES = 0x537e2c
partners = place('partners', f'''
    push ebx
    push esi
    push edi
    push ebp
    test byte ptr [{SHOPT:#x}], 1
    jz pt_none
    test byte ptr [{OPT:#x}], 0x10
    jz pt_none
    test byte ptr [{DIPLO_OPT:#x}], 8
    jz pt_none
    mov esi, dword ptr [esp + 0x14]
    movsx eax, word ptr [0x537e2a]
    cmp esi, eax
    jae pt_none
    imul edi, esi, 0xde
    cmp byte ptr [edi + {CITIES + 0xa4:#x}], 0
    je pt_none
    movzx ecx, byte ptr [edi + {CITIES + 0xa5:#x}]
    {ALLIES_CORE.replace('allies_', 'pa_')}
    mov ebp, edx
    xor eax, eax
pt_alive:
    bt ebp, eax
    jnc pt_anext
    imul ebx, eax, 0x1f8
    cmp byte ptr [ebx + 0x536b30], 0
    je pt_dead
    cmp byte ptr [ebx + 0x536b31], 0
    jne pt_anext
pt_dead:
    btr ebp, eax
pt_anext:
    inc eax
    cmp eax, 8
    jb pt_alive
    test ebp, ebp
    jz pt_none
    movsx eax, word ptr [edi + {CITIES + 2:#x}]
    lea eax, [eax + eax*4]
    add eax, eax
    mov cl, byte ptr [0x503e06]
    shl eax, cl
    movsx ebx, word ptr [edi + {CITIES:#x}]
    lea ebx, [ebx + ebx*4]
    add ebx, ebx
    lea esi, [eax + ebx + 0x503e58]
    mov edx, 10
    shl edx, cl
    mov al, byte ptr [esi + 5]
    not al
    and al, byte ptr [esi + 4]
    mov bl, byte ptr [esi + 15]
    not bl
    and bl, byte ptr [esi + 14]
    and al, bl
    mov bl, byte ptr [esi + edx + 5]
    not bl
    and bl, byte ptr [esi + edx + 4]
    and al, bl
    mov bl, byte ptr [esi + edx + 15]
    not bl
    and bl, byte ptr [esi + edx + 14]
    and al, bl
    movzx eax, al
    and eax, ebp
    jmp pt_ret
pt_none:
    xor eax, eax
pt_ret:
    pop ebp
    pop edi
    pop esi
    pop ebx
    ret
''')

# Oro (0x43ff80, reemplaza 0x43ffdc..0x43ffec). ecx = dueño, edx = 0, si = índice, edi = índice*0xde.
# El ingreso se reparte en partes iguales entre dueño y socios; el resto de la división queda para el dueño.
# Tabla 0x5643f0 = ingreso del turno por jugador (word). Al salir: ecx = dueño, edx = 0 (los usa el original).
gold = place('gold', f'''
    push ecx
    movsx eax, si
    push eax
    call {partners:#x}
    add esp, 4
    pop ecx
    movzx ebx, byte ptr [edi + {CITIES + 0xa7:#x}]
    test eax, eax
    jz gd_owner
    push esi
    push ecx
    mov esi, eax
    mov ecx, 1
gd_cnt:
    test eax, eax
    jz gd_div
    lea edx, [eax - 1]
    and eax, edx
    inc ecx
    jmp gd_cnt
gd_div:
    mov eax, ebx
    xor edx, edx
    div ecx
    xor ecx, ecx
gd_loop:
    bt esi, ecx
    jnc gd_next
    add word ptr [ecx*2 + 0x5643f0], ax
gd_next:
    inc ecx
    cmp ecx, 8
    jb gd_loop
    lea ebx, [eax + edx]
    pop ecx
    pop esi
gd_owner:
    add word ptr [ecx*2 + 0x5643f0], bx
    xor edx, edx
    jmp 0x43ffec
''')

# Maná (0x4403f0, reemplaza 0x44045a..0x440492). al = dueño, dl = tipo de maná de la ciudad, bl = cantidad.
# Partes iguales entre dueño y socios (resto al dueño); cada uno la recibe solo si su maná es compatible
# (tipo propio > 0 y a distancia <= 1 del de la ciudad: la misma prueba que el original le hacía al dueño).
# Tabla 0x564d18 = maná del turno por jugador (word). edi no lo usa el original en este bucle.
mana = place('mana', f'''
    movzx ebp, al
    movzx edi, dl
    movzx ebx, bl
    push esi
    movsx eax, si
    push eax
    call {partners:#x}
    add esp, 4
    mov esi, eax
    mov ecx, 1
mn_cnt:
    test eax, eax
    jz mn_div
    lea edx, [eax - 1]
    and eax, edx
    inc ecx
    jmp mn_cnt
mn_div:
    mov eax, ebx
    xor edx, edx
    div ecx
    mov ebx, eax
    add eax, edx
    mov ecx, ebp
    call mn_give
    xor ecx, ecx
mn_loop:
    bt esi, ecx
    jnc mn_next
    mov eax, ebx
    call mn_give
mn_next:
    inc ecx
    cmp ecx, 8
    jb mn_loop
    pop esi
    jmp 0x440492
mn_give:
    test eax, eax
    jz mn_gret
    imul edx, ecx, 0x1f8
    movsx edx, word ptr [edx + 0x536c0c]
    test edx, edx
    jle mn_gret
    sub edx, edi
    cmp edx, 1
    jg mn_gret
    cmp edx, -1
    jl mn_gret
    add word ptr [ecx*2 + 0x564d18], ax
mn_gret:
    ret
''')

# Panel de la ciudad bajo el cursor (0x418680, bp = índice de ciudad).
# Escudo derecho (call 0x4dd080 en 0x418836, args imagen 0x69+dueño, x, y): el del primer socio.
shield2 = place('shield2', f'''
    push ecx
    push edx
    movsx eax, bp
    push eax
    call {partners:#x}
    add esp, 4
    pop edx
    pop ecx
    test eax, eax
    jz sh_go
    bsf eax, eax
    add eax, 0x69
    mov dword ptr [esp + 4], eax
sh_go:
    jmp 0x4dd080
''')
# Línea "Owner: %s" (call [0x5a9bec] = sprintf(buf, fmt, nombre) en 0x418871): agrega " + socio" por cada socio.
# El buffer del original tiene 80 bytes; se corta en 39 caracteres.
ownertxt = place('ownertxt', f'''
    push dword ptr [esp + 12]
    push dword ptr [esp + 12]
    push dword ptr [esp + 12]
    call dword ptr [0x5a9bec]
    add esp, 12
    push eax
    movsx eax, bp
    push eax
    call {partners:#x}
    add esp, 4
    test eax, eax
    jz ot_out
    push esi
    push edi
    push ebx
    mov esi, eax
    mov edi, dword ptr [esp + 20]
    lea edx, [edi + 39]
ot_end:
    cmp byte ptr [edi], 0
    je ot_names
    inc edi
    jmp ot_end
ot_names:
    xor ecx, ecx
ot_p:
    bt esi, ecx
    jnc ot_pn
    mov al, 0x20
    call ot_put
    mov al, 0x2b
    call ot_put
    mov al, 0x20
    call ot_put
    imul ebx, ecx, 0x1f8
    add ebx, 0x536b34
ot_n:
    mov al, byte ptr [ebx]
    test al, al
    jz ot_pn
    call ot_put
    inc ebx
    jmp ot_n
ot_pn:
    inc ecx
    cmp ecx, 8
    jb ot_p
    mov byte ptr [edi], 0
    pop ebx
    pop edi
    pop esi
ot_out:
    pop eax
    ret
ot_put:
    cmp edi, edx
    jae ot_pr
    mov byte ptr [edi], al
    inc edi
ot_pr:
    ret
''')

# 3) Clic en las casillas nuevas del diálogo Customize Options. eax = id - 2.
#    59 Allied View (bit 0x80 de [0x503d02]), 60 Shared Cities (bit 1 de [SHOPT_DLG]).
NEWCHK = 59
SHCHK = 60
click = place('click', f'''
    cmp eax, {SHCHK - 2}
    je ck_shared
    cmp eax, {NEWCHK - 2}
    jne 0x427d43
    mov eax, dword ptr [esi + 8]
    push 0
    shl al, 7
    xor al, byte ptr [0x503d02]
    and al, 0x80
    xor byte ptr [0x503d02], al
ck_done:
    call 0x428370
    add esp, 4
    mov ecx, 0x588bd0
    call 0x4d82a0
    xor ax, ax
    pop edi
    pop esi
    add esp, 0x60
    ret
ck_shared:
    mov eax, dword ptr [esi + 8]
    push 0
    xor al, byte ptr [{SHOPT_DLG:#x}]
    and al, 1
    xor byte ptr [{SHOPT_DLG:#x}], al
    jmp ck_done
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
    xor eax, eax
    test byte ptr [{SHOPT_DLG:#x}], 1
    setnz al
    push eax
    push {SHCHK}
    call 0x4dd000
    add esp, 8
    ret
''')

# 5) Reporte View Game Options: después de Timed Vectoring (id 0x2f), el indicador nuevo.
NEWIND = 49
SHIND = 51
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
    mov eax, 0x1d
    test byte ptr [{SHOPT:#x}], 1
    jz rp_off2
    mov eax, 0x1c
rp_off2:
    push eax
    push {SHIND}
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
    push 0
    push {SHCHK}
    call 0x4dcec0
    add esp, 8
    ret
''')

# ---- Etapa 3: refugio. Un socio de la ciudad (dueño o aliado que la comparte) entra en sus casillas vacías como
# en una propia; nadie que la comparta ataca a otro que la comparte dentro de ella.
# member(i, p) -> eax = 1 si la ciudad i está compartida (partners != 0) y p es su dueño o un socio.
# Preserva todo salvo eax.
member = place('member', f'''
    push ecx
    push edx
    mov eax, dword ptr [esp + 12]
    push eax
    call {partners:#x}
    add esp, 4
    test eax, eax
    jz mb_no
    mov ecx, dword ptr [esp + 12]
    imul ecx, ecx, 0xde
    movzx ecx, byte ptr [ecx + {CITIES + 0xa5:#x}]
    cmp ecx, 8
    jae mb_no
    bts eax, ecx
    mov ecx, dword ptr [esp + 16]
    cmp ecx, 8
    jae mb_no
    bt eax, ecx
    jnc mb_no
    mov eax, 1
    jmp mb_ret
mb_no:
    xor eax, eax
mb_ret:
    pop edx
    pop ecx
    ret
''')

# 3a) Decodificador de clic/cursor 0x4735c0, en 0x473c24 (hay grupo elegido; bx = dueño de la casilla, si = hay
#     ejército, bp = ciudad o -1). Casilla vacía de una ciudad compartida con el jugador -> mover (7, sin el ícono
#     del tratado). Ejército ajeno en ella: si es de otro socio, nada (0) al lado y "ver ciudad" (13) de lejos,
#     como el original; si no, solo el dueño de la ciudad puede
#     atacarlo (un socio que ganara ahí se quedaría con la ciudad: 0x465c80 captura al ganar en una ciudad).
decide = place('decide', f'''
    cmp word ptr [0x537ce8], bx
    je 0x473c49
    test bp, bp
    jl 0x473c2d
    push eax
    push ecx
    push edx
    movsx eax, word ptr [0x537ce8]
    push eax
    movsx eax, bp
    push eax
    call {member:#x}
    add esp, 8
    test eax, eax
    jz dc_orig
    test si, si
    jz dc_move
    movsx eax, bx
    push eax
    movsx eax, bp
    push eax
    call {member:#x}
    add esp, 8
    test eax, eax
    jnz dc_none
    movsx eax, bp
    imul eax, eax, 0xde
    movzx eax, byte ptr [eax + {CITIES + 0xa5:#x}]
    cmp ax, word ptr [0x537ce8]
    je dc_orig
dc_none:
    pop edx
    pop ecx
    pop eax
    cmp word ptr [esp + 0x22], 1
    jg 0x473d32
    cmp word ptr [esp + 0x24], 1
    jg 0x473d32
    jmp 0x473c50
dc_move:
    pop edx
    pop ecx
    pop eax
    jmp 0x473c49
dc_orig:
    pop edx
    pop ecx
    pop eax
    jmp 0x473c2d
''')

# 3b) Buscador de caminos, vecinos (0x4a5d6d): una casilla de ciudad viva solo se pisa si es del que mueve
#     ([0x58715c]). También se pisa si está vacía y su ciudad está compartida con él.
#     edi = índice de la grilla = x*160 + y; hay que preservar eax (al = bandera de la grilla), edi, esi, ebp.
pathf = place('pathf', f'''
    and cx, 0x3c00
    shr cx, 0xa
    movzx ebx, cx
    cmp ebx, edx
    je 0x4a5d81
    push eax
    push edx
    push ebp
    mov eax, edi
    xor edx, edx
    mov ecx, 160
    div ecx
    lea ebx, [edx + edx*4]
    add ebx, ebx
    mov cl, byte ptr [0x503e06]
    shl ebx, cl
    lea ecx, [eax + eax*4]
    test word ptr [ebx + ecx*2 + 0x503e58], 0x8000
    jnz pf_no
    push edx
    push eax
    call 0x440be0
    add esp, 8
    movsx eax, ax
    push dword ptr [esp + 4]
    push eax
    call {member:#x}
    add esp, 8
    test eax, eax
    jz pf_no
    pop ebp
    pop edx
    pop eax
    jmp 0x4a5d81
pf_no:
    pop ebp
    pop edx
    pop eax
    jmp 0x4a5e31
''')

# 3c) Paso a paso del movimiento (0x49e280, en 0x49e42a): una ciudad viva ajena detiene el avance (devuelve 3).
#     No la detiene si la casilla está vacía y la ciudad está compartida con el que mueve (ebp; si = x, di = y,
#     edx = casilla; hay que preservar ecx, edx).
stepc = place('stepc', f'''
    test byte ptr [edx + 8], 0x80
    jnz 0x49e434
    test word ptr [edx], 0x8000
    jnz 0x49e558
    push ecx
    push edx
    movsx eax, di
    push eax
    movsx eax, si
    push eax
    call 0x440be0
    add esp, 8
    movsx eax, ax
    push ebp
    push eax
    call {member:#x}
    add esp, 8
    pop edx
    pop ecx
    test eax, eax
    jnz 0x49e434
    jmp 0x49e558
''')

# 3d) Al irse un ejército de una casilla (0x49d450, en 0x49d48b): en una ciudad viva el original deja el dueño
#     que tenía la casilla, que era el del ejército. Con refugio ese ejército puede ser de un socio: se repone el
#     dueño de la ciudad, que la casilla guarda en [+8] bits 3-6. En el juego original son siempre iguales.
leave = place('leave', '''
    test byte ptr [esi + 8], 0x80
    jnz 0x49d491
    movzx eax, byte ptr [esi + 8]
    shr eax, 3
    and eax, 0xf
    shl eax, 10
    mov di, word ptr [esi]
    and di, 0xc3ff
    or di, ax
    mov word ptr [esi], di
    jmp 0x49d49e
''')

# 3e) Informe de combate (0x4764b0, una sola vez por batalla, al principio de 0x465c80): solo para el dueño de la
# casilla atacada ([batalla+1]) y contaba como suyas TODAS las bajas defensoras. Con refugio, en una ciudad compartida
# defienden ejércitos de dueños distintos. Defensores: batalla+0x12e + i*0x24, palabra +0 = índice de ejército
# (dueño = (palabra [0x54fe5e + e*0x1c] & 0x1e0) >> 5). kcount (en 0x476690): una baja cuenta solo si el ejército
# era de quien recibe el informe. reports (en 0x465ca5): informe original y luego uno por cada otro dueño de
# defensores (ni el atacante ni [batalla+1]), cambiando [batalla+1] durante la llamada.
kcount = place('kcount', '''
    movsx eax, cx
    shl eax, 2
    lea esi, [eax + eax*8]
    movsx eax, word ptr [esi + edx + 0x12e]
    test eax, eax
    jl kc_count
    imul eax, eax, 0x1c
    movzx eax, word ptr [eax + 0x54fe5e]
    and eax, 0x1e0
    shr eax, 5
    cmp al, byte ptr [esp + 0x16]
    jne 0x4766b4
kc_count:
    cmp byte ptr [esi + edx + 0x130], 0x10
    jl kc_reg
    mov byte ptr [esp + 0x1e], 1
    inc word ptr [esp + 0x38]
    jmp 0x4766b4
kc_reg:
    inc word ptr [esp + 0x36]
    jmp 0x4766b4
''')
reports = place('reports', '''
    push dword ptr [esp + 8]
    push dword ptr [esp + 8]
    call 0x4764b0
    add esp, 8
    push ebx
    push esi
    push edi
    mov esi, dword ptr [esp + 16]
    xor edi, edi
    movsx ecx, byte ptr [esi + 0xd]
rp_scan:
    dec ecx
    jl rp_scanned
    imul eax, ecx, 0x24
    movsx eax, word ptr [esi + eax + 0x12e]
    test eax, eax
    jl rp_scan
    imul eax, eax, 0x1c
    movzx eax, word ptr [eax + 0x54fe5e]
    and eax, 0x1e0
    shr eax, 5
    cmp eax, 8
    jae rp_scan
    bts edi, eax
    jmp rp_scan
rp_scanned:
    movzx eax, byte ptr [esi + 1]
    and eax, 0x1f
    btr edi, eax
    movzx eax, byte ptr [esi]
    and eax, 0x1f
    btr edi, eax
    mov bl, byte ptr [esi + 1]
rp_next:
    bsf eax, edi
    jz rp_end
    btr edi, eax
    mov byte ptr [esi + 1], al
    push dword ptr [esp + 20]
    push esi
    call 0x4764b0
    add esp, 8
    jmp rp_next
rp_end:
    mov byte ptr [esi + 1], bl
    pop edi
    pop esi
    pop ebx
    ret
''')

# ---- Niebla compartida (opción Fog of War, bit 0x20 de OPT). La niebla es una sola capa, la de quien mira:
# 0x441540(jugador) la pone en todo el mapa (bit 0x2000 de la palabra +2 de cada casilla) y la despeja alrededor de
# las ciudades y los ejércitos de ese jugador. Con vista aliada, también alrededor de los de sus aliados mutuos.
# Lo que se dibuja no cambia: un ejército invisible solo lo ve su dueño (0x414dbd), aliado o no.
# fogally: ZF=1 si ecx (dueño) es aliado mutuo de edx (quien mira) con vista aliada. Preserva todo menos flags.
fogally = place('fogally', f'''
    push eax
    push ecx
    push edx
    push ecx
    mov ecx, edx
    {ALLIES.replace('allies_', 'fa_')}
    pop eax
    cmp eax, 8
    jae fa_no
    bt edx, eax
    jnc fa_no
    xor eax, eax
    jmp fa_out
fa_no:
    mov eax, 1
    test eax, eax
fa_out:
    pop edx
    pop ecx
    pop eax
    ret
''')
# En 0x4415ed (ciudades): ecx = dueño de la ciudad, edx = quien mira; al = radio base, se usa en 0x4415f5.
fogcity = place('fogcity', f'''
    cmp ecx, edx
    je 0x4415f5
    call {fogally:#x}
    je 0x4415f5
    jmp 0x44168d
''')
# En 0x4416ef (ejércitos): ebp = dueño, eax = quien mira; ecx/edx = y/x del ejército, se usan en 0x441703.
fogarmy = place('fogarmy', f'''
    cmp ebp, eax
    je fg_mine
    push ecx
    push edx
    mov ecx, ebp
    mov edx, eax
    call {fogally:#x}
    pop edx
    pop ecx
    jne 0x44170d
fg_mine:
    mov ax, word ptr [edi + 0x54fe60]
    jmp 0x4416fa
''')

# ---- Nombre del juego: "Warlords III Era de Alianzas" (v.1.0.3). Solo textos visibles. Se dejan como están el
# "1.02" que se compara en red (0x4f90b4 -> 0x5016c0), el título y la clase de la ventana (0x4fd45c: Red Orb Zone
# busca la ventana con FindWindow por clase y título, MPlay los usa como nombre de la aplicación) y las líneas de
# marca registrada del producto original (grupo 0xec).
def place_data(name, data):
    addr = CAVE + sum(len(b) for b in caves.values())
    caves[name] = bytes(data)
    return addr
GAME = 'Warlords III Era de Alianzas'
VERSION = '1.0.3'
def cstr_(s): return s.encode('latin1') + b'\0'
TEXTS = [  # (grupo, índice, texto nuevo, texto original de Sagetext.tex)
    (0, 0, GAME, 'Warlords III'),                       # título del About
    (1, 0, 'Era de Alianzas', 'Darklords Rising'),       # subtítulo del menú principal (control 19)
    (0x147, 3, GAME + '?', 'Warlords III - Darklords Rising?'),
    (0x148, 3, GAME + '?', 'Warlords III - Darklords Rising?'),
    (0x14c, 1, GAME + ' will now exit!', 'Warlords III - Darklords Rising will now exit!'),
]
strs = {}
for g, i, s, _ in TEXTS:
    assert len(s) < 0x4f
    strs[(g, i)] = place_data(f'str_{g:x}_{i}', cstr_(s))
ver_str = place_data('str_version', cstr_(VERSION))
gtab = place_data('gname_tab', b''.join(struct.pack('<iiI', g, i, strs[(g, i)]) for g, i, _, _ in TEXTS)
                  + struct.pack('<i', -1))
# En 0x4def81 del lector de textos 0x4def30: edx = edi + índice*4 (edi = desplazamiento del grupo), ecx = base de
# la tabla, eax = ranura del búfer rotativo (se usa en 0x4def87); [esp+0x10] = grupo.
gname = place('gname', f'''
    add ecx, dword ptr [edx + ecx + 4]
    push eax
    push edx
    sub edx, edi
    sar edx, 2
    mov eax, dword ptr [esp + 0x18]
    push esi
    mov esi, {gtab:#x}
gn_loop:
    cmp dword ptr [esi], -1
    je gn_done
    cmp dword ptr [esi], eax
    jne gn_next
    cmp dword ptr [esi + 4], edx
    jne gn_next
    mov ecx, dword ptr [esi + 8]
    jmp gn_done
gn_next:
    add esi, 12
    jmp gn_loop
gn_done:
    pop esi
    pop edx
    pop eax
    push 0x4f
    jmp 0x4def87
''')


# ---------------------------------------------------------------- Army List: unidades no permitidas por el validador
# Reglas 1-25 del manifiesto del clan, copiadas de DarklordsValidator (RulesEngine.cs, Unit.cs, AbilityTable.cs,
# ParserUtils.cs; transcriptas en reglas_ref.py). Si el clan cambia las reglas, hay que volver a armar el parche.
import re as _re
import reglas_ref as RR

# Poder (código +0xe6, valor +0xe8) -> bits: 1 tiene poder, 2 contiene "trample", 4 empieza con "trample",
# 8 empieza con "siege", 16 valor > 2, 32 valor > 4. Tabla completa 256x256, sin suposiciones sobre los códigos.
ptab = bytearray(65536)
for code in range(256):
    nm = RR.getname(code)
    for v in range(256):
        pw = nm if code in RR.NOVALUE else ('' if code == 0 or v == 0 else f'{nm} +{v}')
        pw = RR.normalizar(pw); lo = pw.lower(); pv = RR.power_value(pw)
        ptab[code * 256 + v] = ((pw.strip() != '') | ('trample' in lo) << 1 | lo.startswith('trample') << 2
                                | lo.startswith('siege') << 3 | (pv > 2) << 4 | (pv > 4) << 5)
PTAB = place_data('al_ptab', ptab)
WTAB = place_data('al_wtab', bytes(1 if (chr(i).isascii() and (chr(i).isalnum() or chr(i) == '_')) else 0
                                   for i in range(256)))
# Bytes del registro que el juego cambia en memoria al empezar la partida (bonos del jugador, costo, upkeep,
# valor del poder, tipo de movimiento): no cuentan al comparar el .ARM del disco con lo cargado.
AL_SKIP = {0x9a, 0x9b, 0x9c, 0x9d, 0x9e, 0x9f, 0xe0, 0xe2, 0xe3, 0xe8}
SKIP = place_data('al_skip', bytes(1 if i in AL_SKIP else 0 for i in range(0xfc)))

# Banderas del texto del Combat Bonus (al_scan): 1 "none" (\bnone\b, \bn/a\b, \b-\b), 2 primer número válido
# y != 0, 4 habilidad no vacía, 16 hay número, 32 hay algún carácter que no es espacio.
# Átomos de las reglas en [ebp-0x10]. FLY, LAND y CARR: "fly", "landing" o "carrier" en alguno de los 4 casilleros
# de Move Bonus (0xb2, 0xbb, 0xc4, 0xcd), sin distinguir mayúsculas (Unit.TieneMoveBonus).
AT = dict(TERR=1, FLY=2, SHIP=4, HP=8, TRC=16, TRS=32, SGS=64, PV2=128, PV4=256, HC=512, LAND=1024, CARR=2048)
FLD = dict(S=('byte', 0x9a), M=('byte', 0x9b), H=('byte', 0x9c), T=('byte', 0x9d), U=('byte', 0x9e),
           C=('word', 0xe2), SE=('word', 0xe4))
RULES = [  # RulesEngine.cs, en orden (bit i = regla i+1): conjunción de cláusulas, cada cláusula es una disyunción
    [['TERR'], ['M>25']],                                   # 1
    [['TERR'], ['HP'], ['TRC'], ['M>15']],                  # 2
    [['TERR'], ['HP'], ['SGS'], ['PV2'], ['M>17']],         # 3
    [['FLY'], ['M>40']],                                    # 4
    [['FLY'], ['HP'], ['TRS'], ['M>20']],                   # 5
    [['FLY'], ['HP'], ['SGS'], ['PV2'], ['M>22']],          # 6
    [['SHIP'], ['M>30']],                                   # 7
    [['SHIP'], ['LAND'], ['M>12']],                         # 8
    [['FLY'], ['S>3', 'H>1'], ['SE<600', 'U<10', 'T<3']],   # 9
    [['FLY'], ['S>6', 'H>2'], ['SE<800', 'U<15', 'T<4']],   # 10
    [['FLY'], ['S>8', 'H>3'], ['SE<1000', 'U<20', 'T<5']],  # 11
    [['TERR'], ['S>3', 'H>1'], ['SE<300', 'U<5', 'T<2']],   # 12
    [['TERR'], ['S>6', 'H>2'], ['SE<400', 'U<10', 'T<3']],  # 13
    [['TERR'], ['S>8', 'H>3'], ['SE<500', 'U<15', 'T<4']],  # 14
    [['FLY'], ['HP', 'HC'], ['C<600', 'U<10']],             # 15
    [['FLY'], ['HP'], ['HC'], ['C<800', 'U<15']],           # 16
    [['FLY'], ['PV4'], ['C<1000', 'U<20']],                 # 17
    [['TERR'], ['HP', 'HC'], ['C<150', 'U<4']],             # 18
    [['TERR'], ['HP'], ['HC'], ['C<300', 'U<8']],           # 19
    [['TERR'], ['PV4'], ['C<500', 'U<12']],                 # 20
    [['SHIP'], ['HP', 'HC'], ['C<400', 'U<8']],             # 21
    [['SHIP'], ['HP'], ['HC'], ['C<600', 'U<12']],          # 22
    [['SHIP'], ['PV4'], ['C<800', 'U<18']],                 # 23
    [['SHIP'], ['LAND'], ['C<1000', 'U<17']],               # 24
    [['SHIP'], ['CARR'], ['C<1200', 'U<34']],               # 25
]
def rules_asm():
    out = []
    for i, clauses in enumerate(RULES):
        no = f'ru{i}_no'
        for j, cl in enumerate(clauses):
            ok = f'ru{i}_c{j}'
            for p in cl:
                if p in AT:
                    out += [f'test dword ptr [ebp - 0x10], {AT[p]}', f'jnz {ok}']
                else:
                    f, op, k = _re.fullmatch(r'(\w+?)([<>])(\d+)', p).groups()
                    sz, off = FLD[f]
                    out += [f'cmp {sz} ptr [ebx + {off:#x}], {k}', f'{"ja" if op == ">" else "jb"} {ok}']
            out += [f'jmp {no}', f'{ok}:']
        out += [f'or eax, {1 << i:#x}', f'{no}:']
    return '\n    '.join(out)

# armeval(buf 252 bytes, es_barco) -> eax = máscara de reglas violadas (bit i = regla i+1). cdecl.
# Marco: [ebp-0x240] centinela ' ' + texto filtrado en minúsculas; [ebp-0x130] habilidad; [ebp-0x10] átomos.
armeval = place('armeval', f'''
    push ebp
    mov ebp, esp
    sub esp, 0x240
    push ebx
    push esi
    push edi
    mov ebx, dword ptr [ebp + 8]
    lea esi, [ebx + 0xd6]
    call al_scan
    mov dword ptr [ebp - 8], eax
    xor edx, edx
    lea esi, [ebx + 0xb2]
mb_slot:
    lea edi, [ebp - 0x30]
    xor ecx, ecx
mb_cp:
    movzx eax, byte ptr [esi + ecx]
    test eax, eax
    jz mb_cpe
    inc ecx
    cmp eax, 0x20
    jb mb_nx
    cmp eax, 0x7e
    jbe mb_lo
    cmp eax, 0x7f
    je mb_nx
    mov eax, 0x3f
mb_lo:
    cmp eax, 0x41
    jb mb_put
    cmp eax, 0x5a
    ja mb_put
    or eax, 0x20
mb_put:
    mov byte ptr [edi], al
    inc edi
mb_nx:
    cmp ecx, 9
    jb mb_cp
mb_cpe:
    lea ecx, [ebp - 0x30]
mb_t1:
    cmp edi, ecx
    jbe mb_done
    cmp byte ptr [edi - 1], 0x20
    jne mb_t2
    dec edi
    jmp mb_t1
mb_t2:
    cmp byte ptr [ecx], 0x20
    jne mb_t3
    inc ecx
    jmp mb_t2
mb_t3:
    mov eax, edi
    sub eax, ecx
    cmp eax, 3
    jne mb_7
    cmp word ptr [ecx], 0x6c66
    jne mb_done
    cmp byte ptr [ecx + 2], 0x79
    jne mb_done
    or edx, {AT['FLY']}
    jmp mb_done
mb_7:
    cmp eax, 7
    jne mb_done
    cmp dword ptr [ecx], 0x646e616c
    jne mb_car
    cmp word ptr [ecx + 4], 0x6e69
    jne mb_done
    cmp byte ptr [ecx + 6], 0x67
    jne mb_done
    or edx, {AT['LAND']}
    jmp mb_done
mb_car:
    cmp dword ptr [ecx], 0x72726163
    jne mb_done
    cmp word ptr [ecx + 4], 0x6569
    jne mb_done
    cmp byte ptr [ecx + 6], 0x72
    jne mb_done
    or edx, {AT['CARR']}
mb_done:
    add esi, 9
    lea eax, [ebx + 0xd6]
    cmp esi, eax
    jb mb_slot
    cmp dword ptr [ebp + 0xc], 0
    je ae_noship
    or edx, {AT['SHIP']}
ae_noship:
    test edx, {AT['FLY'] | AT['SHIP']}
    jnz ae_noterr
    or edx, {AT['TERR']}
ae_noterr:
    mov eax, dword ptr [ebp - 8]
    test eax, 32
    jz ae_nohc
    test eax, 1
    jnz ae_nohc
    test eax, 4
    jnz ae_hc
    test eax, 16
    jz ae_cv
    test eax, 2
    jnz ae_hc
    jmp ae_nohc
ae_cv:
    cmp byte ptr [ebx + 0xdf], 0
    je ae_nohc
ae_hc:
    or edx, {AT['HC']}
ae_nohc:
    movzx eax, byte ptr [ebx + 0xe6]
    shl eax, 8
    mov al, byte ptr [ebx + 0xe8]
    movzx eax, byte ptr [eax + {PTAB:#x}]
    shl eax, 3
    or edx, eax
    mov dword ptr [ebp - 0x10], edx
    xor eax, eax
    {rules_asm()}
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

al_scan:
    lea edi, [ebp - 0x23f]
    mov byte ptr [edi - 1], 0x20
    lea edx, [ebx + 0xfc]
sc_cp:
    cmp esi, edx
    jae sc_cpe
    movzx eax, byte ptr [esi]
    inc esi
    test eax, eax
    jz sc_cpe
    cmp eax, 0x20
    jb sc_cp
    cmp eax, 0x7e
    jbe sc_asc
    cmp eax, 0x7f
    je sc_cp
    mov eax, 0x3f
    jmp sc_put
sc_asc:
    lea ecx, [eax - 0x41]
    cmp ecx, 25
    ja sc_put
    or eax, 0x20
sc_put:
    mov byte ptr [edi], al
    inc edi
    jmp sc_cp
sc_cpe:
    mov dword ptr [edi], 0
    mov dword ptr [edi + 4], 0
    xor edx, edx
    lea esi, [ebp - 0x23f]
    lea edi, [ebp - 0x130]
sc_lp:
    movzx eax, byte ptr [esi]
    test eax, eax
    jz sc_end
    cmp eax, 0x20
    je sc_n
    or edx, 32
sc_n:
    cmp eax, 0x6e
    jne sc_dash
    movzx ecx, byte ptr [esi - 1]
    cmp byte ptr [ecx + {WTAB:#x}], 0
    jne sc_keep
    cmp dword ptr [esi], 0x656e6f6e
    jne sc_na
    movzx ecx, byte ptr [esi + 4]
    cmp byte ptr [ecx + {WTAB:#x}], 0
    jne sc_na
    or edx, 1
sc_na:
    cmp word ptr [esi], 0x2f6e
    jne sc_keep
    cmp byte ptr [esi + 2], 0x61
    jne sc_keep
    movzx ecx, byte ptr [esi + 3]
    cmp byte ptr [ecx + {WTAB:#x}], 0
    jne sc_keep
    or edx, 1
    jmp sc_keep
sc_dash:
    cmp eax, 0x2d
    jne sc_dig
    movzx ecx, byte ptr [esi - 1]
    cmp byte ptr [ecx + {WTAB:#x}], 0
    je sc_dash2
    movzx ecx, byte ptr [esi + 1]
    cmp byte ptr [ecx + {WTAB:#x}], 0
    je sc_dash2
    or edx, 1
sc_dash2:
    movzx ecx, byte ptr [esi + 1]
    sub ecx, 0x30
    cmp ecx, 9
    jbe sc_next
    jmp sc_keep
sc_dig:
    lea ecx, [eax - 0x30]
    cmp ecx, 9
    ja sc_plus
    test edx, 16
    jnz sc_next
    or edx, 16
    call sc_num
    jmp sc_next
sc_plus:
    cmp eax, 0x2b
    je sc_next
sc_keep:
    mov byte ptr [edi], al
    inc edi
sc_next:
    inc esi
    jmp sc_lp
sc_end:
    lea esi, [ebp - 0x130]
sc_t1:
    cmp edi, esi
    jbe sc_ret
    cmp byte ptr [edi - 1], 0x20
    jne sc_t2
    dec edi
    jmp sc_t1
sc_t2:
    cmp byte ptr [esi], 0x20
    jne sc_t3
    inc esi
    jmp sc_t2
sc_t3:
    or edx, 4
sc_ret:
    mov eax, edx
    ret

sc_num:
    push esi
    push edi
    xor edi, edi
    xor ecx, ecx
sn_lp:
    movzx eax, byte ptr [esi]
    sub eax, 0x30
    cmp eax, 9
    ja sn_end
    inc esi
    test ecx, ecx
    jnz sn_lp
    cmp edi, 0x0ccccccc
    ja sn_ovf
    imul edi, edi, 10
    add edi, eax
    jmp sn_lp
sn_ovf:
    mov ecx, 1
    jmp sn_lp
sn_end:
    test ecx, ecx
    jnz sn_ret
    mov eax, 0x7fffffff
    mov ecx, dword ptr [esp + 4]
    cmp byte ptr [ecx - 1], 0x2d
    jne sn_b
    inc eax
sn_b:
    cmp edi, eax
    ja sn_ret
    test edi, edi
    jz sn_ret
    or edx, 2
sn_ret:
    pop edi
    pop esi
    ret
''')

# armcheck(registro en memoria, bando) -> eax = máscara de reglas violadas. cdecl.
# Evalúa ARMY\<nombre>.ARM del disco si coincide con lo cargado salvo los bytes de AL_SKIP; si no existe o no
# coincide (partida guardada con unidades que después cambiaron), evalúa lo cargado quitando los bonos del
# jugador de 0x433a60 (fuerza, movimiento, vida, turnos): aproximado, el resto de los cambios no se deshace.
# Barco = existe ARMY\<nombre>.SHP. Marco: [ebp-0x180] búfer, [ebp-0x80] ruta, [ebp-8] barco, [ebp-4] fd.
SPRINTF, OPEN, READ, CLOSE = 0x5a9bec, 0x5a9c08, 0x5a9c04, 0x5a9bfc
def fix(off, bit_vals, sign):
    # campo [ebp-0x180+off] -/+ suma de bonos según bits de eax; con piso 0 y techo 255
    s = ['xor ecx, ecx']
    for k, (bit, val) in enumerate(bit_vals):
        s += [f'test eax, {bit:#x}', f'jz fx{off:x}_{k}', f'add ecx, {val}', f'fx{off:x}_{k}:']
    s += [f'movzx edx, byte ptr [ebp - 0x180 + {off:#x}]', f'{"sub" if sign < 0 else "add"} edx, ecx',
          f'jns fx{off:x}_p', 'xor edx, edx', f'fx{off:x}_p:', 'cmp edx, 255', f'jbe fx{off:x}_q', 'mov edx, 255',
          f'fx{off:x}_q:', f'mov byte ptr [ebp - 0x180 + {off:#x}], dl']
    return '\n    '.join(s)
armcheck = place('armcheck', f'''
    push ebp
    mov ebp, esp
    sub esp, 0x180
    push ebx
    push esi
    push edi
    mov esi, dword ptr [ebp + 8]
    lea eax, [esi + 0x90]
    push eax
    push 0x4fb5e0
    lea eax, [ebp - 0x80]
    push eax
    call dword ptr [{SPRINTF:#x}]
    add esp, 12
    push 0x8000
    lea eax, [ebp - 0x80]
    push eax
    call dword ptr [{OPEN:#x}]
    add esp, 8
    xor ebx, ebx
    cmp eax, -1
    je ac_noshp
    push eax
    call dword ptr [{CLOSE:#x}]
    add esp, 4
    mov ebx, 1
ac_noshp:
    mov dword ptr [ebp - 8], ebx
    lea eax, [esi + 0x90]
    push eax
    push 0x4fb5c8
    lea eax, [ebp - 0x80]
    push eax
    call dword ptr [{SPRINTF:#x}]
    add esp, 12
    push 0x8000
    lea eax, [ebp - 0x80]
    push eax
    call dword ptr [{OPEN:#x}]
    add esp, 8
    cmp eax, -1
    je ac_mem
    mov dword ptr [ebp - 4], eax
    push 0xfc
    lea ecx, [ebp - 0x180]
    push ecx
    push eax
    call dword ptr [{READ:#x}]
    add esp, 12
    mov ebx, eax
    push dword ptr [ebp - 4]
    call dword ptr [{CLOSE:#x}]
    add esp, 4
    cmp ebx, 0xfc
    jne ac_mem
    xor ecx, ecx
ac_cmp:
    cmp byte ptr [ecx + {SKIP:#x}], 0
    jne ac_cnx
    mov al, byte ptr [esi + ecx]
    cmp al, byte ptr [ebp + ecx - 0x180]
    jne ac_mem
ac_cnx:
    inc ecx
    cmp ecx, 0xfc
    jb ac_cmp
    jmp ac_eval
ac_mem:
    lea edi, [ebp - 0x180]
    mov ecx, 63
    rep movsd dword ptr es:[edi], dword ptr [esi]
    mov eax, dword ptr [ebp + 0xc]
    imul eax, eax, 0x1f8
    mov eax, dword ptr [eax + 0x536bf0]
    {fix(0x9a, [(1, 1), (2, 2), (4, 3)], -1)}
    {fix(0x9b, [(8, 3), (0x10, 6), (0x20, 9)], -1)}
    {fix(0x9c, [(0x4000, 1), (0x8000, 2)], -1)}
    {fix(0x9d, [(0x2000, 1)], +1)}
ac_eval:
    push dword ptr [ebp - 8]
    lea eax, [ebp - 0x180]
    push eax
    call {armeval:#x}
    add esp, 8
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret
''')

# Icono "prohibido" 21x21 (aro y barra rojos, contorno negro), en tramos horizontales (dy, x0, x1, color), fin 0xff.
def _icon():
    N, c = 19, 9
    R = [[False] * (N + 2) for _ in range(N + 2)]
    for y in range(N):
        for x in range(N):
            dx, dy = x - c, y - c; d = (dx * dx + dy * dy) ** .5
            R[y + 1][x + 1] = 6.3 <= d <= 9.4 or (d < 7 and abs(dx - dy) / 2 ** .5 <= 1.6)
    def col(x, y):
        if R[y][x]: return 70
        if any(R[yy][xx] for yy in range(max(0, y - 1), min(N + 2, y + 2)) for xx in range(max(0, x - 1), min(N + 2, x + 2))):
            return 0
        return None
    runs = []
    for y in range(N + 2):
        x = 0
        while x < N + 2:
            k = col(x, y)
            if k is None: x += 1; continue
            x1 = x
            while x1 + 1 < N + 2 and col(x1 + 1, y) == k: x1 += 1
            runs.append(bytes([y, x, x1, k])); x = x1 + 1
    return b''.join(runs) + b'\xff'
ICON = place_data('al_icon', _icon())
AL_DX, AL_DY = 355, 13   # icono sobre el texto de habilidades (x 433..~512), centrado a ojo respecto del texto: 373
                         # (centro de la columna) se veía corrido a la derecha, 400 pisaba el texto, 421 el borde (fotos 5/10/2026)

# En 0x4a2c24 (última llamada del dibujo de una fila de la lista 21 de Army List, antes del epílogo común):
# dibuja la fila como siempre y, si es una unidad (casilla 0..15) que viola alguna regla, el icono a la derecha.
# [esp+0x6c] x, [esp+0x70] y, [esp+0x74] índice del renglón; +0x20 por el pushad.
armrow = place('armrow', f'''
    call 0x4dd120
    add esp, 0xc
    pushad
    mov eax, dword ptr [esp + 0x94]
    movsx edi, word ptr [eax*2 + 0x5730b0]
    cmp edi, 15
    ja ar_done
    movsx eax, word ptr [0x5730dc]
    cmp eax, 7
    ja ar_done
    push eax
    shl eax, 4
    add eax, edi
    imul eax, eax, 0xfc
    add eax, 0x53c410
    push eax
    call {armcheck:#x}
    add esp, 8
    test eax, eax
    jz ar_done
    mov esi, {ICON:#x}
    mov edi, dword ptr [esp + 0x8c]
    add edi, {AL_DX}
    mov ebx, dword ptr [esp + 0x90]
    add ebx, {AL_DY}
ar_lp:
    movzx eax, byte ptr [esi]
    cmp eax, 0xff
    je ar_done
    add eax, ebx
    movzx ecx, byte ptr [esi + 3]
    push ecx
    push eax
    movzx ecx, byte ptr [esi + 2]
    add ecx, edi
    push ecx
    push eax
    movzx ecx, byte ptr [esi + 1]
    add ecx, edi
    push ecx
    call 0x4e1a70
    add esp, 0x14
    add esi, 4
    jmp ar_lp
ar_done:
    popad
    jmp 0x4a2c2c
''')

# Título de Army List ("Army List for %s", Sagetext 0x129/0; reemplaza "call 0x4dd260" en 0x4a2cb6, cdecl
# (control 0x1b, formato, nombre)): agrega " [<archivo>.PGS]" con el nombre del bando del jugador mirado. El nombre
# está en la copia del PGS del registro del jugador (0x536b30 + p*0x1f8 + 0xe8, nombre en +0xe) y el juego arma el
# archivo con 0x43a680 (cambia . > < * ? , | \ / % ; : por _) y "PGS\%s.PGS". Solo si ese archivo existe: los
# bandos propios de un escenario (o sin nombre) dejan el título original. El control guarda 63 caracteres.
ALT_FMT = place_data('alt_fmt', cstr_(' [%s.PGS]'))
altitle = place('altitle', f'''
    push ebp
    mov ebp, esp
    sub esp, 0x100
    push ebx
    push esi
    push edi
    movsx eax, word ptr [0x5730dc]
    cmp eax, 7
    ja at_plain
    imul esi, eax, 0x1f8
    add esi, {0x536b30 + 0xe8 + 0xe:#x}
    cmp byte ptr [esi], 0
    je at_plain
    lea edi, [ebp - 0x100]
    mov ecx, 8
    rep movsd dword ptr es:[edi], dword ptr [esi]
    mov byte ptr [ebp - 0x100 + 31], 0
    lea eax, [ebp - 0x100]
    push eax
    call 0x43a680
    add esp, 4
    lea eax, [ebp - 0x100]
    push eax
    push 0x4fb574
    lea eax, [ebp - 0xc0]
    push eax
    call dword ptr [{SPRINTF:#x}]
    add esp, 12
    push 0x8000
    lea eax, [ebp - 0xc0]
    push eax
    call dword ptr [{OPEN:#x}]
    add esp, 8
    cmp eax, -1
    je at_plain
    push eax
    call dword ptr [{CLOSE:#x}]
    add esp, 4
    push dword ptr [ebp + 0x10]
    push dword ptr [ebp + 0xc]
    lea eax, [ebp - 0xc0]
    push eax
    call dword ptr [{SPRINTF:#x}]
    add esp, 12
    lea edx, [ebp - 0xc0]
    add edx, eax
    lea eax, [ebp - 0x100]
    push eax
    push {ALT_FMT:#x}
    push edx
    call dword ptr [{SPRINTF:#x}]
    add esp, 12
    push dword ptr [ebp + 8]
    mov ecx, 0x588bd0
    call 0x4d83d0
    test eax, eax
    jz at_done
    lea edx, [ebp - 0xc0]
    push edx
    mov ecx, eax
    call 0x4f0f40
    jmp at_done
at_plain:
    push dword ptr [ebp + 0x10]
    push dword ptr [ebp + 0xc]
    push dword ptr [ebp + 8]
    call 0x4dd260
    add esp, 12
at_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret
''')

# ---- Banderas de los socios en las ciudades compartidas (mapa principal)
# La ciudad ocupa 4x4 casillas de la vista alrededor de sus 2x2; la pieza t (0..15) es la casilla (t&3)-1, (t>>2)-1
# respecto de la esquina sup-izq. La bandera original (40x30, parte 9 de 0x45ba50) va en la torre inf-izq, en
# (-12, 72) px, repartida entre las piezas 8, 9, 12 y 13. Las de los socios van en las otras tres torres, en el
# orden de sus bits: 1º inf-der, 2º sup-izq, 3º sup-der (máximo 3 socios). Probado en los 9 estilos de CITY.
FLAG_W, FLAG_H = 40, 30
FLAG_AT = [(96, 72), (-12, -28), (96, -28)]          # esquina de cada socio, px respecto de la ciudad
fl_corner = [0xff] * 16
fl_piece = [0] * (16 * 6)
for k, (fx, fy) in enumerate(FLAG_AT):
    for t in range(16):
        tx, ty = 48 * ((t & 3) - 1), 48 * ((t >> 2) - 1)
        x0, y0 = max(fx, tx), max(fy, ty)
        x1, y1 = min(fx + FLAG_W, tx + 48), min(fy + FLAG_H, ty + 48)
        if x0 < x1 and y0 < y1:
            assert fl_corner[t] == 0xff and t not in (8, 9, 12, 13)
            fl_corner[t] = k
            fl_piece[6 * t:6 * t + 6] = [x0 - fx, y0 - fy, x0 - tx, y0 - ty, x1 - x0, y1 - y0]
FLCORNER = place_data('flcorner', fl_corner)
FLPIECE = place_data('flpiece', fl_piece + [0] * 0x10)

# flcolor(ecx = vista, edx = registro de casilla) -> eax = color del socio cuya bandera cae en esta pieza, o -1.
# Esquina sup-izq de la ciudad = semilla [reg+0x18], [reg+0x1a] menos el origen de la vista [+0x28], [+0x2a].
# Preserva ebx, esi, edi, ebp.
flcolor = place('flcolor', f'''
    push ebx
    push esi
    push edi
    mov esi, ecx
    mov edi, edx
    cmp byte ptr [edi + 0x10], 0
    je fc_none
    movzx ecx, word ptr [edi + 0x12]
    test ch, 3
    jz fc_none
    and ecx, 0xf
    movsx ebx, byte ptr [ecx + {FLCORNER:#x}]
    test ebx, ebx
    js fc_none
    movsx eax, word ptr [edi + 0x1a]
    movsx edx, word ptr [esi + 0x2a]
    sub eax, edx
    push eax
    movsx eax, word ptr [edi + 0x18]
    movsx edx, word ptr [esi + 0x28]
    sub eax, edx
    push eax
    call 0x440be0
    add esp, 8
    movsx eax, ax
    test eax, eax
    js fc_none
    push eax
    call {partners:#x}
    add esp, 4
    mov edx, eax
fc_bit:
    test edx, edx
    jz fc_none
    bsf eax, edx
    btr edx, eax
    sub ebx, 1
    jns fc_bit
    jmp fc_out
fc_none:
    or eax, -1
fc_out:
    pop edi
    pop esi
    pop ebx
    ret
''')

# Dibujo (reemplaza la llamada de la 2ª pasada 0x45a049 a 0x45aa80, thiscall, ret 0x18): la pieza original y
# encima, si corresponde, su parte de la bandera del socio con la misma semilla de animación que la del dueño.
fldraw = place('fldraw', f'''
    push ebx
    push esi
    push edi
    push ebp
    mov esi, ecx
    push dword ptr [esp + 0x28]
    push dword ptr [esp + 0x28]
    push dword ptr [esp + 0x28]
    push dword ptr [esp + 0x28]
    push dword ptr [esp + 0x28]
    push dword ptr [esp + 0x28]
    mov ecx, esi
    call 0x45aa80
    mov edi, dword ptr [esp + 0x24]
    lea edx, [edi - 0x12]
    mov ecx, esi
    call {flcolor:#x}
    test eax, eax
    js fd_out
    movzx ecx, word ptr [edi]
    and ecx, 0xf
    lea ebx, [ecx + ecx*2]
    lea ebx, [ebx*2 + {FLPIECE:#x}]
    movsx edx, word ptr [edi + 6]
    push edx
    push eax
    movzx edx, byte ptr [edi + 2]
    push edx
    movzx edx, byte ptr [ebx + 5]
    push edx
    movzx edx, byte ptr [ebx + 4]
    push edx
    movzx edx, byte ptr [ebx + 3]
    push edx
    movzx edx, byte ptr [ebx + 2]
    push edx
    movzx edx, byte ptr [ebx + 1]
    push edx
    movzx edx, byte ptr [ebx]
    push edx
    push 9
    push dword ptr [esp + 0x44]
    push dword ptr [esp + 0x44]
    push dword ptr [esp + 0x44]
    mov ecx, esi
    call 0x45ba50
fd_out:
    pop ebp
    pop edi
    pop esi
    pop ebx
    ret 0x18
''')

# Casillas sucias (0x457090, reemplaza "and dx, 0xf; cmp dx, 8" en 0x4571f8): además de las piezas de la bandera
# del dueño (8, 9, 12, 13), se redibujan en cada cuadro las que llevan bandera de socio, para que se animen
# enteras. ebp = registro, bx = contador de sucias, cl = byte +6, [esp+0x18] = vista.
# El byte +0x11 del registro (sin uso en el juego; se copia entero al cuadro anterior en [vista+0x1b0]) queda en 1
# si la pieza lleva bandera de socio: cuando deja de llevarla, la comparación con el cuadro anterior (0x4573f3)
# la marca sucia y se borra la bandera vieja.
fldirty = place('fldirty', f'''
    and dx, 0xf
    cmp dx, 8
    je fy_mark
    cmp dx, 9
    je fy_mark
    cmp dx, 0xc
    je fy_mark
    cmp dx, 0xd
    je fy_mark
    push eax
    push ecx
    push edx
    mov ecx, dword ptr [esp + 0x24]
    mov edx, ebp
    call {flcolor:#x}
    not eax
    shr eax, 31
    mov byte ptr [ebp + 0x11], al
    test eax, eax
    pop edx
    pop ecx
    pop eax
    jz fy_skip
fy_mark:
    jmp 0x457214
fy_skip:
    jmp 0x457231
''')

# ---------------------------------------------------------------- Tope de 6 para pilas con voladores
# Una pila que incluye al menos un volador (unidad con tipo +0xe0 == 4, o héroe que vuela por sí mismo o por un
# objeto: 0x48f9a0 != 0, el mismo criterio de la batalla 0x466cf0) admite 6 ejércitos en vez del tope del bando
# ([0x536c08 + p*0x1f8], 8). Se aplica donde una pila se forma: paso del movimiento (0x49e280, humanos e IA),
# reunión del grupo en una ciudad (0x4d3330), lugar para lo que se produce (0x43b510) y reagrupado de las 4 casillas
# de la ciudad (0x4ae450). Las pilas de más de 6 con voladores de partidas viejas no se parten: solo no crecen.
FLYCAP = 6

# eax = ejército -> eax 1 si vuela. Preserva todo lo demás.
isfly = place('isfly', '''
    push ecx
    push edx
    imul ecx, eax, 0x1c
    movzx edx, word ptr [ecx + 0x54fe5e]
    mov ecx, edx
    and ecx, 0x1f
    cmp ecx, 0x10
    jne if_unit
    push eax
    call 0x48f9a0
    add esp, 4
    movzx eax, ax
    neg eax
    sbb eax, eax
    neg eax
    jmp if_out
if_unit:
    shr edx, 5
    and edx, 0xf
    push edx
    push eax
    call 0x497010
    add esp, 8
if_out:
    pop edx
    pop ecx
    ret
''')

# esi = lista de ejércitos (palabras), ecx = cantidad -> eax 1 si alguno vuela. Preserva todo lo demás.
listfly = place('listfly', f'''
    push ecx
    push esi
lf_loop:
    test ecx, ecx
    jle lf_no
    movzx eax, word ptr [esi]
    call {isfly:#x}
    test eax, eax
    jnz lf_out
    add esi, 2
    dec ecx
    jmp lf_loop
lf_no:
    xor eax, eax
lf_out:
    pop esi
    pop ecx
    ret
''')

# cdecl (x, y) -> eax 1 si algún ejército vivo de la casilla vuela (mismo recorrido que 0x4411b0).
# Preserva todo menos eax.
tilefly = place('tilefly', f'''
    push ecx
    push edx
    mov ecx, 1
tf_loop:
    movsx eax, word ptr [0x54fe50]
    cmp ecx, eax
    jge tf_no
    imul edx, ecx, 0x1c
    test byte ptr [edx + 0x54fe63], 0x40
    jz tf_next
    mov ax, word ptr [esp + 12]
    cmp word ptr [edx + 0x54fe52], ax
    jne tf_next
    mov ax, word ptr [esp + 16]
    cmp word ptr [edx + 0x54fe54], ax
    jne tf_next
    mov eax, ecx
    call {isfly:#x}
    test eax, eax
    jnz tf_out
tf_next:
    inc ecx
    jmp tf_loop
tf_no:
    xor eax, eax
tf_out:
    pop edx
    pop ecx
    ret
''')

# eax = jugador -> eax 1 si algún ejército de su grupo en movimiento (0x56ea94 + p*0x4f0, cantidad en +0x14) vuela.
grpfly = place('grpfly', f'''
    push ecx
    push esi
    imul eax, eax, 0x4f0
    lea esi, [eax + 0x56ea94]
    movsx ecx, word ptr [eax + 0x56eaa8]
    call {listfly:#x}
    pop esi
    pop ecx
    ret
''')

# Paso del movimiento (0x49e280, en 0x49e48b): ecx = ejércitos en la casilla + los del grupo, ebp = jugador,
# si/di = casilla. Deja en edx el tope (6 si hay volador en el grupo o en la casilla). Preserva ecx, ebx, esi,
# edi, ebp.
stepcap = place('stepcap', f'''
    mov eax, ebp
    shl eax, 6
    sub eax, ebp
    movsx edx, word ptr [eax*8 + 0x536c08]
    cmp ecx, {FLYCAP}
    jle sp_out
    cmp edx, {FLYCAP}
    jle sp_out
    mov eax, ebp
    call {grpfly:#x}
    test eax, eax
    jnz sp_cap
    movsx eax, di
    push eax
    movsx eax, si
    push eax
    call {tilefly:#x}
    add esp, 8
    test eax, eax
    jz sp_out
sp_cap:
    mov edx, {FLYCAP}
sp_out:
    jmp 0x49e49a
''')

# Grupo reunido en una ciudad (0x4d3330, en 0x4d340a): ecx = ejércitos en la casilla + los del grupo,
# [esp+0x1c] = jugador, di/bx = casilla. Igual que stepcap.
gatecap = place('gatecap', f'''
    mov eax, dword ptr [esp + 0x1c]
    shl eax, 6
    sub eax, dword ptr [esp + 0x1c]
    movsx edx, word ptr [eax*8 + 0x536c08]
    cmp ecx, {FLYCAP}
    jle gc_out
    cmp edx, {FLYCAP}
    jle gc_out
    mov eax, dword ptr [esp + 0x1c]
    call {grpfly:#x}
    test eax, eax
    jnz gc_cap
    movsx eax, bx
    push eax
    movsx eax, di
    push eax
    call {tilefly:#x}
    add esp, 8
    test eax, eax
    jz gc_out
gc_cap:
    mov edx, {FLYCAP}
gc_out:
    jmp 0x4d341d
''')

# Lugar para un ejército nuevo (0x43b510, en 0x43b5a8): ax = ejércitos en la casilla, ebp = jugador,
# [esp+0x12] = x, si = y, byte [esp+0x34] = el nuevo vuela. La casilla sirve si cuenta < tope.
placecap = place('placecap', f'''
    mov ecx, ebp
    shl ecx, 6
    sub ecx, ebp
    movsx edx, word ptr [ecx*8 + 0x536c08]
    movsx ecx, ax
    cmp ecx, {FLYCAP}
    jl pc_cmp
    cmp edx, {FLYCAP}
    jle pc_cmp
    cmp byte ptr [esp + 0x34], 0
    jne pc_cap
    movsx eax, si
    push eax
    movsx eax, word ptr [esp + 0x16]
    push eax
    call {tilefly:#x}
    add esp, 8
    test eax, eax
    jz pc_cmp
pc_cap:
    mov edx, {FLYCAP}
pc_cmp:
    cmp edx, ecx
    jle 0x43b5bd
    jmp 0x43b5b9
''')

# cdecl (listas, cuentas, jugador): 4 listas de 8 palabras seguidas y sus 4 cuentas (palabras). Mientras una
# lista tenga más de 6 y un volador, pasa uno de sus ejércitos (del último al primero) a otra lista donde quepa sin
# romper ninguna de las dos reglas. Si no hay dónde, la deja como está.
rebal = place('rebal', f'''
    push ebx
    push esi
    push edi
    push ebp
    sub esp, 12
    mov eax, dword ptr [esp + 0x28]
    imul eax, eax, 0x1f8
    movsx ebp, word ptr [eax + 0x536c08]
    cmp ebp, {FLYCAP}
    jle rb_done
    mov dword ptr [esp], 0
rb_s:
    mov ebx, dword ptr [esp]
    cmp ebx, 4
    jae rb_done
    mov edx, dword ptr [esp + 0x24]
    movsx ecx, word ptr [edx + ebx*2]
    cmp ecx, {FLYCAP}
    jle rb_next_s
    mov esi, dword ptr [esp + 0x20]
    shl ebx, 4
    add esi, ebx
    call {listfly:#x}
    test eax, eax
    jz rb_next_s
    dec ecx
    mov dword ptr [esp + 4], ecx
rb_j:
    mov ecx, dword ptr [esp + 4]
    test ecx, ecx
    jl rb_next_s
    movzx edi, word ptr [esi + ecx*2]
    mov dword ptr [esp + 8], 0
rb_t:
    mov eax, dword ptr [esp + 8]
    cmp eax, 4
    jae rb_j_next
    cmp eax, dword ptr [esp]
    je rb_t_next
    mov edx, dword ptr [esp + 0x24]
    movsx ecx, word ptr [edx + eax*2]
    inc ecx
    cmp ecx, ebp
    jg rb_t_next
    cmp ecx, {FLYCAP}
    jle rb_move
    push eax
    mov eax, edi
    call {isfly:#x}
    mov ebx, eax
    pop eax
    test ebx, ebx
    jnz rb_t_next
    push esi
    push ecx
    mov esi, dword ptr [esp + 0x28]
    shl eax, 4
    add esi, eax
    dec ecx
    call {listfly:#x}
    pop ecx
    pop esi
    test eax, eax
    jnz rb_t_next
    mov eax, dword ptr [esp + 8]
rb_move:
    mov edx, dword ptr [esp + 0x24]
    movsx ecx, word ptr [edx + eax*2]
    inc word ptr [edx + eax*2]
    mov ebx, dword ptr [esp + 0x20]
    shl eax, 4
    add ebx, eax
    mov word ptr [ebx + ecx*2], di
    mov eax, dword ptr [esp]
    movsx ecx, word ptr [edx + eax*2]
    dec ecx
    mov word ptr [edx + eax*2], cx
    mov ebx, dword ptr [esp + 4]
    mov ax, word ptr [esi + ecx*2]
    mov word ptr [esi + ebx*2], ax
    jmp rb_s
rb_t_next:
    inc dword ptr [esp + 8]
    jmp rb_t
rb_j_next:
    dec dword ptr [esp + 4]
    jmp rb_j
rb_next_s:
    inc dword ptr [esp]
    jmp rb_s
rb_done:
    add esp, 12
    pop ebp
    pop edi
    pop esi
    pop ebx
    ret
''')

# Reagrupado de la ciudad (0x4ae450, en 0x4ae941, antes de escribir las posiciones): listas en [esp+0x1c]
# (x, y+1; cuenta en cx), [esp+0x2c] (x, y; [esp+0x14]), [esp+0x3c] (x+1, y; [esp+0x16]), [esp+0x4c]
# (x+1, y+1; [esp+0x18]); [esp+0x12] = dueño. Se repite lo reemplazado (xor dx, dx / cmp [esp+0x14], dx).
regroup = place('regroup', f'''
    sub esp, 8
    mov word ptr [esp], cx
    mov ax, word ptr [esp + 8 + 0x14]
    mov word ptr [esp + 2], ax
    mov ax, word ptr [esp + 8 + 0x16]
    mov word ptr [esp + 4], ax
    mov ax, word ptr [esp + 8 + 0x18]
    mov word ptr [esp + 6], ax
    movsx eax, word ptr [esp + 8 + 0x12]
    push eax
    lea eax, [esp + 4]
    push eax
    lea eax, [esp + 16 + 0x1c]
    push eax
    call {rebal:#x}
    add esp, 12
    movsx ecx, word ptr [esp]
    mov ax, word ptr [esp + 2]
    mov word ptr [esp + 8 + 0x14], ax
    mov ax, word ptr [esp + 4]
    mov word ptr [esp + 8 + 0x16], ax
    mov ax, word ptr [esp + 6]
    mov word ptr [esp + 8 + 0x18], ax
    add esp, 8
    xor dx, dx
    cmp word ptr [esp + 0x14], dx
    jmp 0x4ae949
''')

# ---------------------------------------------------------------- Puertos arrasados
# El grafo de pasos (0x4a4f90) marca agua+tierra (punto de embarque) toda casilla con el bit 0x4000 de la palabra 0,
# que es fijo del mapa: un puerto arrasado (sitio tipo 4, [casilla+8] & 8) seguía sirviendo. En 0x4a5147 se lo
# saltea. Arrasar ya invalida el grafo (0x4d5e30 -> 0x4a4f20); reconstruir (0x4b6610) no lo hacía: ahora sí, al
# final (salto a 0x4a4f20 en lugar del ret), para que el puerto reconstruido vuelva a servir.
portc = place('portc', '''
    test byte ptr [edi + 1], 0x40
    jz 0x4a5157
    push eax
    mov al, byte ptr [edi + 3]
    and al, 7
    cmp al, 4
    pop eax
    jne 0x4a514d
    test byte ptr [edi + 8], 8
    jnz 0x4a5157
    jmp 0x4a514d
''')

# ---------------------------------------------------------------- Desembarco libre (bono de movimiento "Landing")
# "Embarcado" es un estado del ejército (bit 8 de +0x12; el grupo lo refleja en +0x1a & 8) y el barco de cada bando es
# su tipo de arma de la ranura 15 (registro 0x53c410 + (p*16 + 15)*0xfc, el .ARM tal cual). El ejecutor del paso
# (0x49db70) y el costo del camino (0x4a61e0) ya desembarcan en cualquier paso de agua pura a tierra; lo único que lo
# impide es el grafo de enlaces, que solo une agua y tierra en los puntos de transbordo (puertos).
# Si el grupo del jugador que pide el camino ([0x58715c]) está embarcado y el barco de su bando tiene "Landing" en
# alguno de sus 4 bonos de movimiento (+0xb2 + k*9, 9 B c/u; el cargador 0x42f1b0 ignora los textos que no conoce y
# el editor los escribe en sus listas desplegables editables), el buscador (0x4a5c40, expansión, y su rastreo de
# vuelta en 0x4a600e) suma a los enlaces de una casilla de agua pura las direcciones hacia tierra, y a los de una
# casilla con tierra las direcciones hacia agua pura. Nunca hacia tierra intransitable: clase de terreno 4
# (montaña; 0x535f0c + tipo*0x58) sin camino ni puente (flags & 0x30), la misma regla del constructor (0x4a52c3).
# No toca los vuelos (otra rama) ni la tabla de enlaces.
LANDING = b'landing'    # se compara sin distinguir mayúsculas
landstr = place_data('landstr', LANDING + b'\0')
landchk = place('landchk', f'''
    pushad
    movsx eax, word ptr [0x58715c]
    cmp eax, 8
    jae landchk_no
    imul edx, eax, 0x4f0
    test byte ptr [edx + 0x56eaaa], 8
    jz landchk_no
    shl eax, 4
    add eax, 15
    imul esi, eax, 0xfc
    add esi, {0x53c410 + 0xb2:#x}
    mov edi, 4
landchk_slot:
    xor ecx, ecx
landchk_ch:
    mov al, byte ptr [esi + ecx]
    cmp al, 0x41
    jb landchk_nf
    cmp al, 0x5a
    ja landchk_nf
    or al, 0x20
landchk_nf:
    cmp al, byte ptr [ecx + {landstr:#x}]
    jne landchk_next
    test al, al
    jz landchk_yes
    inc ecx
    cmp ecx, 9
    jb landchk_ch
landchk_next:
    add esi, 9
    dec edi
    jnz landchk_slot
landchk_no:
    xor eax, eax
    popad
    ret
landchk_yes:
    test esp, esp
    popad
    ret
''')
# ZF=1 si la casilla (ebp = x, edi = y; índice del grafo en edx) es tierra intransitable sin camino ni puente.
# Usa ebp, edi; preserva el resto.
mtnchk = place('mtnchk', '''
    test byte ptr [edx + 0x57d158], 0x30
    jnz mtnchk_ok
    cmp byte ptr [0x4fe688], 0
    jne mtnchk_ok
    push ecx
    lea edi, [edi + edi*4]
    add edi, edi
    mov cl, byte ptr [0x503e06]
    shl edi, cl
    pop ecx
    lea ebp, [ebp + ebp*4]
    lea edi, [edi + ebp*2]
    movzx edi, word ptr [edi + 0x503e58]
    and edi, 0x1f
    imul edi, edi, 0x58
    cmp word ptr [edi + 0x535f0c], 4
    ret
mtnchk_ok:
    test esp, esp
    ret
''')
livexp = place('livexp', f'''
    shl eax, 5
    movsx ecx, word ptr [esp + 0x1c]
    add eax, ecx
    mov cl, byte ptr [eax + 0x573158]
    cmp byte ptr [eax + 0x582158], 0x80
    jne livexp_end
    call {landchk:#x}
    jz livexp_end
    push ebx
    push esi
    push edi
    push ebp
    mov bl, byte ptr [eax + 0x578158]
    xor esi, esi
livexp_loop:
    test byte ptr [esi + 0x4fe678], bl
    jz livexp_next
    movsx ebp, word ptr [esi*2 + 0x4fe640]
    movsx edi, word ptr [esi*2 + 0x4fe658]
    imul edx, ebp, 0xa0
    add edx, edi
    add edx, eax
    test byte ptr [edx + 0x582158], 0x40
    jz livexp_next
    movsx ecx, cl
    push ecx
    movsx ecx, word ptr [esp + 0x2c]
    add ebp, ecx
    movsx ecx, word ptr [esp + 0x30]
    add edi, ecx
    pop ecx
    call {mtnchk:#x}
    jz livexp_next
    or cl, byte ptr [esi + 0x4fe678]
livexp_next:
    inc esi
    cmp esi, 8
    jb livexp_loop
    pop ebp
    pop edi
    pop esi
    pop ebx
livexp_end:
    jmp 0x4a5c79
''')
livback = place('livback', f'''
    movsx ecx, word ptr [esp + 0x1e]
    lea ecx, [ecx + ecx*4]
    shl ecx, 5
    movsx edx, word ptr [esp + 0x20]
    lea esi, [ecx + edx]
    mov cl, byte ptr [esi + 0x573158]
    test byte ptr [esi + 0x582158], 0x40
    jz livback_end
    call {landchk:#x}
    jz livback_end
    push ebp
    movsx ebp, word ptr [esp + 0x22]
    movsx edi, word ptr [esp + 0x24]
    mov edx, esi
    call {mtnchk:#x}
    pop ebp
    jz livback_end
    push ebx
    push eax
    mov bl, byte ptr [esi + 0x578158]
    xor edi, edi
livback_loop:
    test byte ptr [edi + 0x4fe678], bl
    jz livback_next
    movsx eax, word ptr [edi*2 + 0x4fe640]
    imul eax, eax, 0xa0
    movsx edx, word ptr [edi*2 + 0x4fe658]
    add eax, edx
    cmp byte ptr [esi + eax + 0x582158], 0x80
    jne livback_next
    or cl, byte ptr [edi + 0x4fe678]
livback_next:
    inc edi
    cmp edi, 8
    jb livback_loop
    pop eax
    pop ebx
livback_end:
    jmp 0x4a6048
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
patch(0x441cf0, bytes.fromhex('83ec0833c9'), asm(f'jmp {vcopy:#x}', 0x441cf0))
patch(0x441933, bytes.fromhex('889c4d5c3e5000'), asm(f'jmp {mapinit:#x}', 0x441933))
patch(0x41fb98, bytes.fromhex('0894455c3e5000'), asm(f'jmp {rect:#x}', 0x41fb98))
patch(0x427877, asm('ja 0x427d43', 0x427877), asm(f'ja {click:#x}', 0x427877))
patch(0x428643, asm('call 0x4dd000', 0x428643), asm(f'call {refresh:#x}', 0x428643))
patch(0x43f40f, asm('call 0x4dd040', 0x43f40f), asm(f'call {report:#x}', 0x43f40f))
patch(0x428074, bytes.fromhex('6a006a07') + asm('call 0x4dcec0', 0x428078),
      bytes.fromhex('6a006a07') + asm(f'call {init:#x}', 0x428078))
patch(0x4fb70c, b'DATA\\WAR3.RES\0\0\0', RES_NAME + b'\0' * (16 - len(RES_NAME)))
patch(0x43ffdc, bytes.fromhex('660fb69fd37e5300') + bytes.fromhex('66011c4df0435600'), asm(f'jmp {gold:#x}', 0x43ffdc))
assert rel(0x44045a, 4) == bytes.fromhex('33c98ac8') and rel(0x440486, 12) == bytes.fromhex('660fb6c36601044d184d5600')
patch(0x44045a, rel(0x44045a, 0x440492 - 0x44045a), asm(f'jmp {mana:#x}', 0x44045a))
patch(0x418836, asm('call 0x4dd080', 0x418836), asm(f'call {shield2:#x}', 0x418836))
patch(0x418871, bytes.fromhex('ff15ec9b5a00'), asm(f'call {ownertxt:#x}', 0x418871))
patch(0x473c24, bytes.fromhex('66391de87c5300741c'), asm(f'jmp {decide:#x}', 0x473c24))
patch(0x4a5d6d, bytes.fromhex('6681e1003c66c1e90a0fb7d93bda0f85b0000000'), asm(f'jmp {pathf:#x}', 0x4a5d6d))
patch(0x49e42a, bytes.fromhex('f64208800f8424010000'), asm(f'jmp {stepc:#x}', 0x49e42a))
patch(0x49d48b, bytes.fromhex('f6460880740d'), asm(f'jmp {leave:#x}', 0x49d48b))
assert rel(0x476690, 4) == bytes.fromhex('0fbfc1c1') and rel(0x4766b4, 2) == bytes.fromhex('6641')
patch(0x476690, rel(0x476690, 0x4766b4 - 0x476690), asm(f'jmp {kcount:#x}', 0x476690))
patch(0x465ca5, asm('call 0x4764b0', 0x465ca5), asm(f'call {reports:#x}', 0x465ca5))
patch(0x4415ed, bytes.fromhex('3bca0f8598000000'), asm(f'jmp {fogcity:#x}', 0x4415ed))
assert rel(0x4416fa, 4) == bytes.fromhex('66250e00')
patch(0x4416ef, bytes.fromhex('3be8751a668b8760fe5400'), asm(f'jmp {fogarmy:#x}', 0x4416ef))
patch(0x4def81, bytes.fromhex('034c0a046a4f'), asm(f'jmp {gname:#x}', 0x4def81))
assert rel(0x4a2c24, 8) == asm('call 0x4dd120; add esp, 0xc', 0x4a2c24)
patch(0x4a2c24, rel(0x4a2c24, 8), asm(f'jmp {armrow:#x}', 0x4a2c24))
patch(0x45a049, asm('call 0x45aa80', 0x45a049), asm(f'call {fldraw:#x}', 0x45a049))
patch(0x4a2cb6, asm('call 0x4dd260', 0x4a2cb6), asm(f'call {altitle:#x}', 0x4a2cb6))
assert rel(0x457200, 2) == asm('je 0x457214', 0x457200)
patch(0x4571f8, bytes.fromhex('6683e20f6683fa08'), asm(f'jmp {fldirty:#x}', 0x4571f8))
for va in (0x4a979e, 0x4ab7c5):
    patch(va, asm('push 0x4f90b4', va), asm(f'push {ver_str:#x}', va))
patch(0x49e48b, rel(0x49e48b, 0x49e49a - 0x49e48b), asm(f'jmp {stepcap:#x}', 0x49e48b))
assert rel(0x49e49a, 2) == bytes.fromhex('3bca')
patch(0x4d340a, rel(0x4d340a, 0x4d341d - 0x4d340a), asm(f'jmp {gatecap:#x}', 0x4d340a))
assert rel(0x4d341d, 2) == bytes.fromhex('3bca')
assert rel(0x43b5b7, 2) == asm('jle 0x43b5bd', 0x43b5b7)
patch(0x43b5a8, rel(0x43b5a8, 0x43b5b9 - 0x43b5a8), asm(f'jmp {placecap:#x}', 0x43b5a8))
patch(0x4ae941, bytes.fromhex('6633d26639542414'), asm(f'jmp {regroup:#x}', 0x4ae941))
patch(0x4a5147, bytes.fromhex('f6470140740a'), asm(f'jmp {portc:#x}', 0x4a5147))
patch(0x4b6677, bytes.fromhex('c3cccccccc'), asm('jmp 0x4a4f20', 0x4b6677))
# Puentes solo de tierra: en 0x4a5135 una casilla de clase agua con camino (estructura 1 = puente) quedaba agua+tierra
# (punto de transbordo, y paso de barcos por debajo). Reordenado en el lugar: con camino se saltea el "agua".
patch(0x4a5135, rel(0x4a5135, 0x4a5147 - 0x4a5135),
      asm('cmp word ptr [esp + 0x12], 0; jne 0x4a5147; mov word ptr [esp + 0x18], 1; xor bp, bp', 0x4a5135))
patch(0x4a5c6a, rel(0x4a5c6a, 0x4a5c79 - 0x4a5c6a), asm(f'jmp {livexp:#x}', 0x4a5c6a))
patch(0x4a6031, rel(0x4a6031, 0x4a6048 - 0x4a6031), asm(f'jmp {livback:#x}', 0x4a6031))

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
chk2 = bytearray(chk)
struct.pack_into('<IIII', chk2, 4, SHCHK, 189, 162, 1)
setstr(chk2, 0x1c, 16, 'Shared Cities')
setstr(chk2, 0x2c, 64, 'Allies co-own cities both explored (Hidden Map)')
setstr(chk2, 0x9c, 16, 'Shared Cities')
new_list[9] = [chk, chk2]

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
# Fila "Shared Cities" como 8ª de la columna 2, clonada de su última fila (22 / 36).
SHLBL = 50
p, t = r115[22]; assert t == 0x12
lbl2 = bytearray(res[p:p + 4 + SZ[0x12]])
struct.pack_into('<I', lbl2, 4, SHLBL)
setstr(lbl2, 0x2c, 64, 'Shared Cities')
p, t = r115[36]; assert t == 0x11
ind2 = bytearray(res[p:p + 4 + SZ[0x11]])
struct.pack_into('<I', ind2, 4, SHIND)
y = 130 + 21 * len(col2)
struct.pack_into('<I', lbl2, 0xc, y); struct.pack_into('<I', ind2, 0xc, y - 2)
new_list[115] = [lbl, ind, lbl2, ind2]

for did in (115, 9):   # el 115 está después del 9: tocarlo primero no corre el offset del 9
    append(res, did, b''.join(new_list[did]))

# Nombre del juego en los textos de los diálogos (ayudas de botón: +0x40, 64 bytes; texto tipo 0x12: +0x2c, se
# rellena solo hasta 40 bytes). No se tocan los avisos del CD-Rom (diálogo 126, ids 4 y 5): nombran el disco original.
RES_TEXTS = [  # (diálogo, id, tipo, desplazamiento, tamaño, original, nuevo)
    (1, 5, 1, 0x40, 64, 'Play the Warlords III Tutorial', f'Play the {GAME} Tutorial'),
    (1, 7, 1, 0x40, 64, 'Exits Warlords III', f'Exits {GAME}'),
    (8, 12, 0x12, 0x2c, 40, 'of Warlords III', f'of {GAME}'),
    (8, 13, 0x12, 0x2c, 40, 'Verifying Warlords III', f'Verifying {GAME}'),
    (8, 35, 0x15, 0x40, 64, 'Begin playing Warlords 3', f'Begin playing {GAME}'),
    (54, 7, 0x15, 0x40, 64, 'Exit Warlords 3', f'Exit {GAME}'),
    (126, 3, 0x15, 0x40, 64, 'Quit from Warlords 3', f'Quit from {GAME}'),
]
for did, cid, typ, off, size, old, new in RES_TEXTS:
    p, t = records(res, did)[cid]
    assert t == typ, (did, cid, t)
    assert bytes(res[p + off:p + off + len(old) + 1]) == old.encode('latin1') + b'\0', (did, cid)
    setstr(res, p + off, size, new)

# ---------------------------------------------------------------- escribir (solo archivos nuevos)
for path in (OUT_EXE, OUT_RES):
    assert os.path.abspath(path).lower() not in (os.path.abspath(SRC_EXE).lower(), os.path.abspath(SRC_RES).lower())
os.makedirs(os.path.dirname(OUT_RES), exist_ok=True)
open(OUT_EXE, 'wb').write(exe)
open(OUT_RES, 'wb').write(res)
print('caves', {k: hex(CAVE + sum(len(caves[j]) for j in list(caves)[:list(caves).index(k)])) for k in caves})
print('exe', OUT_EXE, len(exe), 'res', OUT_RES, len(res))
