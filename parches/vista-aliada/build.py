# Arma DarklordAV.exe y DATA\WAR3AV.RES a partir de los originales (que solo se leen), los subtipos de terreno
# TERRAIN\SUBTYPE\landing.STT, carrier.STT, bridge.STT y cabotage.STT, y el dibujo del botón de Sorteo
# SETS\Fantasy\sorteo.pcx.
# Topes de un barco según sus bonos de movimiento: stack en agua de 5 con "Landing" y de 6 con "Landing" y "Carrier"
# (LANDCAP); pasos de 12, 20 y 24 con "Landing", "Landing" y "Carrier", y "Carrier" (MVCAP).
# Convoy: hasta tres barcos en fila de un bando con bono de movimiento "Carrier" forman uno de hasta 24 (crlink).
# Puentes: derribar (Raze, con la opción de arrasar sitios) y reconstruir (Build, al costo de una ciudad); el diálogo
# de derribar muestra el retrato del ariete orco.
# Combat Bonus "Bridge": el bono suma cuando la batalla es en un puente en pie (subtipo TERRAIN\SUBTYPE\bridge.STT).
# Cabotaje: el barco de un bando con el bono de movimiento "Cabotage" no se aleja más de 2 casillas de la costa
# (salvo para acercarse); cruza ríos y lagos angostos.
# Vista aliada compartida: bit 0x80 de [0x53c38e] (opciones de partida).
# Botones de Votación ("Votacion" en el menú de partida) y Sorteo (ícono del programa en la preparación): el
# anfitrión abre Herramientas\votacion.exe / sorteo.exe en todas las PC y su estado viaja por red a los espectadores.
# Uso: python build.py [carpeta_salida]   (por defecto C:\Warlords3; crea DATA\ si falta)
import struct, sys, os
import keystone, capstone

SRC_EXE = r'C:\Warlords3\Darklord.exe'
SRC_RES = r'C:\Warlords3\DATA\War3.RES'
OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3'
if OUT_DIR.startswith('-'):
    sys.exit('Uso: python build.py [carpeta_salida]   (por defecto C:\\Warlords3)')
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
    (1, 0, '', 'Darklords Rising'),       # subtítulo del menú principal (control 19): va la imagen titulo.pcx
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
# Si el barco del bando del jugador que pide el camino ([0x58715c]) tiene "Landing" en alguno de sus 4 bonos de
# movimiento (+0xb2 + k*9, 9 B c/u; el cargador 0x42f1b0 ignora los textos que no conoce y el editor los escribe en
# sus listas desplegables editables), el buscador (0x4a5c40, expansión, y su rastreo de vuelta en 0x4a600e) suma a
# los enlaces de una casilla de agua pura las direcciones hacia tierra, y a los de una casilla con tierra las
# direcciones hacia agua pura, salvo que el líder esté en un convoy (crconv): esos atracan solo en puertos.
# Vale también para un grupo que todavía está en tierra (1.0.25.0; antes solo embarcado): el camino sube al barco en
# un puerto, como siempre (no hay enlace nuevo de tierra a agua), y baja en cualquier costa. Así la IA, cuyo mapa de
# distancias (0x497750 -> 0x4a53b0) y cuyos caminos usan este mismo buscador, planea desembarcos en playa desde
# tierra; el humano recibe las mismas rutas al ordenar un movimiento. Nunca hacia tierra intransitable: clase de terreno 4
# (montaña; 0x535f0c + tipo*0x58) sin camino ni puente (flags & 0x30), la misma regla del constructor (0x4a52c3).
# No toca los vuelos (otra rama) ni la tabla de enlaces.
LANDING = b'landing'    # se compara sin distinguir mayúsculas
landstr = place_data('landstr', LANDING + b'\0')
# eax = jugador (0..7) -> eax = 1 si el barco de su bando tiene "Landing", 0 si no. Preserva el resto.
# Con rec=True: eax = registro de unidad y edx = texto en minúsculas (para cualquier unidad, no solo el barco).
def boatbon_src(lbl, straddr, rec=False):
    head = 'lea esi, [eax + 0xb2]' if rec else f'''shl eax, 4
    add eax, 15
    imul esi, eax, 0xfc
    add esi, {0x53c410 + 0xb2:#x}'''
    straddr = 'edx' if rec else f'{straddr:#x}'
    return f'''
    push ecx
    push esi
    push edi
    {head}
    mov edi, 4
{lbl}_slot:
    xor ecx, ecx
{lbl}_ch:
    mov al, byte ptr [esi + ecx]
    cmp al, 0x41
    jb {lbl}_nf
    cmp al, 0x5a
    ja {lbl}_nf
    or al, 0x20
{lbl}_nf:
    cmp al, byte ptr [ecx + {straddr}]
    jne {lbl}_next
    test al, al
    jz {lbl}_yes
    inc ecx
    cmp ecx, 9
    jb {lbl}_ch
{lbl}_next:
    add esi, 9
    dec edi
    jnz {lbl}_slot
    xor eax, eax
    jmp {lbl}_out
{lbl}_yes:
    mov eax, 1
{lbl}_out:
    pop edi
    pop esi
    pop ecx
    ret
'''
boatland = place('boatland', boatbon_src('boatland', landstr))

# ---------------------------------------------------------------- Convoy (bono de movimiento "Carrier")
# Hasta tres stacks embarcados de un bando cuyo barco (ranura 15) tiene "Carrier", en una cadena de casillas vecinas,
# forman un solo barco de hasta 24: cada casilla conserva su tope, se mueven juntos (el stack que se mueve arrastra a
# los demás en fila: cada uno pasa a la casilla que dejó el de adelante), atacan solo con el grupo que ataca y
# defienden con todas las casillas. Atracan solo en puertos: a una casilla del convoy no se le aplica "Landing".
# Enlace: byte +0x1b del ejército (0x54fe6b; en 1821 ejércitos vivos de 12 partidas siempre vale 0, ningún código lo
# lee y se guarda con la partida). Bit 0x80 = enlazado; bits 0-3 = cod de la primera casilla vecina enlazada
# (bits 0-1 = dx+1 y bits 2-3 = dy+1: cod = dx + 4*dy + 5, el opuesto es 10 - cod); bits 4-6 = k, la segunda
# vecina enlazada está k pasos más allá de la primera en la rosa de direcciones CR_RING (0 = no hay segunda). Un
# enlace de T hacia T + d vale si el barco de q tiene "Carrier" y en T + d hay un ejército vivo y embarcado de q
# con la dirección -d en su byte. Los enlaces sueltos (la otra casilla se fue o murió) no valen nada. Los transportes
# dobles de 1.0.7 y 1.0.8 (k = 0) son convoyes de 2 casillas con el mismo byte.
# Formar: ordenar a un stack embarcado ir a una casilla vecina con un barco propio cuando la suma no entra (el paso
# devuelve 4, "stack lleno"). Se ejecuta en todas las máquinas (comando de red 0x14d -> 0x49c9f0) y usa el destino
# del líder, que viaja por red (el camino no).
CARRIER = b'carrier'
carrstr = place_data('carrstr', CARRIER + b'\0')
boatcarr = place('boatcarr', boatbon_src('boatcarr', carrstr))
CABOTAGE = b'cabotage'
cabstr = place_data('cabstr', CABOTAGE + b'\0')
boatcab = place('boatcab', boatbon_src('boatcab', cabstr))   # ver Cabotaje, más abajo

# Army List: el renglón de habilidades de una unidad (texto en [esp+8] al llegar a 0x4a2c24, búfer de 0x50 bytes del
# marco de 0x4a2560) nombra también los bonos de movimiento "Landing", "Carrier" y "Cabotage" de su registro: reemplazan
# "No Special Abilities" (palabra de habilidades +0xe6 en 0) o se agregan con ", " si entran en el búfer. Después sigue armrow.
recbon = place('recbon', boatbon_src('recbon', None, rec=True))
AB_NAMES = ('Landing', 'Carrier', 'Cabotage')   # bits 0, 1 y 2 del índice en AB_TAB
AB_TXT = [place_data(f'ab_txt{k}', cstr_(', '.join(n for b, n in enumerate(AB_NAMES) if k >> b & 1))) for k in range(1, 8)]
AB_TAB = place_data('ab_tab', b''.join(a.to_bytes(4, 'little') for a in [0] + AB_TXT))
AB_SEP = place_data('ab_sep', cstr_(', '))
# Largo máximo del texto previo para que entren ', ' + AB_TXT[k] y el 0 final (por índice, para no cortar de más).
AB_LIM = place_data('ab_lim', bytes([0] + [0x50 - 1 - len(', ' + ', '.join(n for b, n in enumerate(AB_NAMES) if k >> b & 1))
                                        for k in range(1, 8)]))
armab = place('armab', f'''
    pushad
    mov eax, dword ptr [esp + 0xa0]
    movsx edi, word ptr [eax*2 + 0x5730b0]
    cmp edi, 15
    ja ab_out
    movsx eax, word ptr [0x5730dc]
    cmp eax, 7
    ja ab_out
    shl eax, 4
    add eax, edi
    imul ebx, eax, 0xfc
    add ebx, 0x53c410
    mov eax, ebx
    mov edx, {landstr:#x}
    call {recbon:#x}
    mov ebp, eax
    mov eax, ebx
    mov edx, {carrstr:#x}
    call {recbon:#x}
    lea ebp, [ebp + eax*2]
    mov eax, ebx
    mov edx, {cabstr:#x}
    call {recbon:#x}
    lea ebp, [ebp + eax*4]
    test ebp, ebp
    jz ab_out
    mov edi, dword ptr [esp + 0x28]
    cmp word ptr [ebx + 0xe6], 0
    jne ab_app
    mov byte ptr [edi], 0
    jmp ab_cat
ab_app:
    xor ecx, ecx
ab_len:
    cmp byte ptr [edi + ecx], 0
    je ab_lend
    inc ecx
    cmp ecx, 0x50
    jb ab_len
    jmp ab_out
ab_lend:
    movzx eax, byte ptr [ebp + {AB_LIM:#x}]
    cmp ecx, eax
    ja ab_out
    add edi, ecx
    mov esi, {AB_SEP:#x}
ab_sep:
    lodsb
    stosb
    test al, al
    jnz ab_sep
    dec edi
ab_cat:
    mov esi, dword ptr [ebp*4 + {AB_TAB:#x}]
ab_cp:
    lodsb
    stosb
    test al, al
    jnz ab_cp
ab_out:
    popad
    jmp {armrow:#x}
''')
# Rosa de direcciones (cod de N, NE, E, SE, S, SO, O, NO) y su inversa (cod -> índice, 0xff si el cod no es dirección).
CR_RING = [1, 2, 6, 10, 9, 8, 4, 0]
CR_E2R = place_data('cr_e2r', bytes(CR_RING.index(e) if e in CR_RING else 0xff for e in range(16)))
CR_R2E = place_data('cr_r2e', bytes(CR_RING))
CRLK = place_data('crlk', b'\xff' * 12)     # crlinks: jugador, cod 1, cod 2 (-1 si no hay)
CRCV = place_data('crcv', bytes(16))        # crconv: las otras casillas del convoy, 2 x (x, y)
# eax = byte de enlace -> eax = cod 1, edx = cod 2 (-1 si no hay); los dos -1 si no está enlazado o el cod 1 no es
# una dirección. Preserva el resto.
crdec = place('crdec', f'''
    push ecx
    movzx ecx, al
    test cl, 0x80
    jz crd_none
    mov eax, ecx
    and eax, 0xf
    movzx edx, byte ptr [eax + {CR_E2R:#x}]
    cmp edx, 8
    jae crd_none
    shr ecx, 4
    and ecx, 7
    jz crd_one
    add edx, ecx
    and edx, 7
    movzx edx, byte ptr [edx + {CR_R2E:#x}]
    pop ecx
    ret
crd_one:
    or edx, -1
    pop ecx
    ret
crd_none:
    or eax, -1
    or edx, -1
    pop ecx
    ret
''')
# eax = cod 1, edx = cod 2 o -1 -> eax = byte de enlace. Preserva el resto.
crenc = place('crenc', f'''
    test edx, edx
    js cre_one
    push ecx
    movzx ecx, byte ptr [edx + {CR_E2R:#x}]
    sub cl, byte ptr [eax + {CR_E2R:#x}]
    and ecx, 7
    shl ecx, 4
    or eax, ecx
    pop ecx
cre_one:
    or eax, 0x80
    ret
''')
# eax = cod, esi = x, edi = y -> eax, edx = la casilla vecina en esa dirección. Preserva el resto.
crxy = place('crxy', '''
    mov edx, eax
    shr edx, 2
    lea edx, [edi + edx - 1]
    and eax, 3
    lea eax, [esi + eax - 1]
    ret
''')
# eax = dx, edx = dy -> eax = max(|dx|, |dy|). Preserva el resto (salvo edx).
crcheb = place('crcheb', '''
    push ecx
    mov ecx, eax
    sar ecx, 31
    xor eax, ecx
    sub eax, ecx
    mov ecx, edx
    sar ecx, 31
    xor edx, ecx
    sub edx, ecx
    cmp eax, edx
    jge crc_out
    mov eax, edx
crc_out:
    pop ecx
    ret
''')
# eax = x, edx = y, ebp = jugador, ecx = operación -> eax = cuántos ejércitos vivos del jugador en la casilla pasan los
# filtros. Operación: 0x200 solo embarcados, 0x1000 solo con la dirección cl en el byte de enlace, 0x400 solo con byte
# de enlace == cl, 0x800 escribe cl en el byte de enlace, 0x100 borra el destino. Preserva el resto (salvo edx).
crscan = place('crscan', f'''
    push ebx
    push esi
    push edi
    mov esi, eax
    mov edi, edx
    xor eax, eax
    mov ebx, 1
crs_loop:
    movsx edx, word ptr [0x54fe50]
    cmp ebx, edx
    jge crs_end
    imul edx, ebx, 0x1c
    test byte ptr [edx + 0x54fe63], 0x40
    jz crs_next
    cmp word ptr [edx + 0x54fe52], si
    jne crs_next
    cmp word ptr [edx + 0x54fe54], di
    jne crs_next
    push eax
    movzx eax, word ptr [edx + 0x54fe5e]
    shr eax, 5
    and eax, 0xf
    cmp eax, ebp
    pop eax
    jne crs_next
    test ch, 2
    jz crs_f0
    test byte ptr [edx + 0x54fe64], 8
    jz crs_next
crs_f0:
    test ch, 0x10
    jz crs_f1
    push eax
    push edx
    movzx eax, byte ptr [edx + 0x54fe6b]
    call {crdec:#x}
    cmp al, cl
    je crs_f0b
    cmp dl, cl
crs_f0b:
    pop edx
    pop eax
    jne crs_next
crs_f1:
    test ch, 4
    jz crs_f2
    cmp byte ptr [edx + 0x54fe6b], cl
    jne crs_next
crs_f2:
    test ch, 8
    jz crs_f3
    mov byte ptr [edx + 0x54fe6b], cl
crs_f3:
    test ch, 1
    jz crs_f4
    mov dword ptr [edx + 0x54fe56], 0xffffffff
crs_f4:
    inc eax
crs_next:
    inc ebx
    jmp crs_loop
crs_end:
    pop edi
    pop esi
    pop ebx
    ret
''')
# esi = x, edi = y, ebp = jugador, eax = cod -> eax = cuántos ejércitos vivos y embarcados del jugador en la casilla
# vecina en esa dirección apuntan de vuelta. Preserva el resto (salvo edx).
crback = place('crback', f'''
    push ecx
    mov ecx, 0x120a
    sub ecx, eax
    call {crxy:#x}
    call {crscan:#x}
    pop ecx
    ret
''')
# esi = x, edi = y -> eax = cuántos enlaces de la casilla valen (0..2): los del primer ejército vivo y embarcado con
# alguno que valga. En CRLK: jugador, cod 1, cod 2 (-1 los que no hay). Preserva el resto.
crlinks = place('crlinks', f'''
    push ebx
    push ecx
    push edx
    push ebp
    mov ebx, 1
crk_loop:
    movsx eax, word ptr [0x54fe50]
    cmp ebx, eax
    jge crk_no
    imul eax, ebx, 0x1c
    test byte ptr [eax + 0x54fe63], 0x40
    jz crk_next
    test byte ptr [eax + 0x54fe64], 8
    jz crk_next
    cmp word ptr [eax + 0x54fe52], si
    jne crk_next
    cmp word ptr [eax + 0x54fe54], di
    jne crk_next
    movzx ebp, word ptr [eax + 0x54fe5e]
    shr ebp, 5
    and ebp, 0xf
    cmp ebp, 8
    jae crk_next
    movzx eax, byte ptr [eax + 0x54fe6b]
    call {crdec:#x}
    test eax, eax
    js crk_next
    mov dword ptr [{CRLK + 4:#x}], eax
    mov dword ptr [{CRLK + 8:#x}], edx
    mov eax, ebp
    call {boatcarr:#x}
    test eax, eax
    jz crk_next
    xor ecx, ecx
    mov eax, dword ptr [{CRLK + 4:#x}]
    call {crback:#x}
    test eax, eax
    jz crk_2
    inc ecx
crk_2:
    mov eax, dword ptr [{CRLK + 8:#x}]
    test eax, eax
    js crk_end
    call {crback:#x}
    test eax, eax
    jz crk_end
    mov eax, dword ptr [{CRLK + 8:#x}]
    mov dword ptr [ecx*4 + {CRLK + 4:#x}], eax
    inc ecx
crk_end:
    test ecx, ecx
    jz crk_next
    mov dword ptr [{CRLK:#x}], ebp
    mov eax, ecx
    cmp eax, 2
    je crk_out
    mov dword ptr [{CRLK + 8:#x}], -1
crk_out:
    pop ebp
    pop edx
    pop ecx
    pop ebx
    ret
crk_next:
    inc ebx
    jmp crk_loop
crk_no:
    or eax, -1
    mov dword ptr [{CRLK:#x}], eax
    mov dword ptr [{CRLK + 4:#x}], eax
    mov dword ptr [{CRLK + 8:#x}], eax
    xor eax, eax
    jmp crk_out
''')
# esi = x, edi = y -> eax = cuántas otras casillas tiene el convoy de la casilla (0..2), en CRCV como (x, y): sigue
# los enlaces que valen hasta 2 pasos. Preserva el resto.
crconv = place('crconv', f'''
    push ebx
    push ecx
    push edx
    push esi
    push edi
    call {crlinks:#x}
    test eax, eax
    jz crv_out
    mov ecx, eax
    mov eax, dword ptr [{CRLK + 4:#x}]
    call {crxy:#x}
    mov dword ptr [{CRCV:#x}], eax
    mov dword ptr [{CRCV + 4:#x}], edx
    cmp ecx, 2
    jne crv_far
    mov eax, dword ptr [{CRLK + 8:#x}]
    call {crxy:#x}
    jmp crv_third
crv_far:
    mov ebx, esi
    mov ecx, edi
    mov esi, eax
    mov edi, edx
    call {crlinks:#x}
    test eax, eax
    jz crv_one
    mov eax, dword ptr [{CRLK + 4:#x}]
    call {crxy:#x}
    cmp eax, ebx
    jne crv_third
    cmp edx, ecx
    jne crv_third
    mov eax, dword ptr [{CRLK + 8:#x}]
    test eax, eax
    js crv_one
    call {crxy:#x}
crv_third:
    mov dword ptr [{CRCV + 8:#x}], eax
    mov dword ptr [{CRCV + 0xc:#x}], edx
    mov eax, 2
    jmp crv_out
crv_one:
    mov eax, 1
crv_out:
    pop edi
    pop esi
    pop edx
    pop ecx
    pop ebx
    ret
''')
landchk = place('landchk', f'''
    pushad
    movsx eax, word ptr [0x58715c]
    cmp eax, 8
    jae landchk_no
    imul edx, eax, 0x4f0
    call {boatland:#x}
    test eax, eax
    jz landchk_no
    movsx eax, word ptr [edx + 0x56ea90]
    imul eax, eax, 0x1c
    test byte ptr [eax + 0x54fe6b], 0x80
    jz landchk_yes
    movsx esi, word ptr [eax + 0x54fe52]
    movsx edi, word ptr [eax + 0x54fe54]
    call {crconv:#x}
    test eax, eax
    jnz landchk_no
landchk_yes:
    or eax, 1
    popad
    ret
landchk_no:
    xor eax, eax
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
# ---------------------------------------------------------------- Cabotaje (bono de movimiento "Cabotage")
# El barco de un bando (ranura 15) con "Cabotage" navega pegado a la costa: no entra en una casilla de agua pura
# (medio 0x80) a más de CAB_N casillas de tierra, salvo que se acerque a la costa (para que un barco que ya está mar
# adentro pueda volver). Alcanza para cruzar ríos y lagos angostos. La distancia a tierra (en pasos, también en
# diagonal) de cada casilla se calcula en CABD cada vez que se arma el grafo de caminos (0x4a4f90, el único que
# escribe la tabla de medios 0x582158), en dos pasadas: hacia adelante mirando (x-1, y-1), (x-1, y), (x-1, y+1) y
# (x, y-1); hacia atrás, los opuestos. Tierra (medio con 0x40, puertos incluidos) = 0. El buscador (expansión y
# rastreo de vuelta, los mismos ganchos que Landing) quita los enlaces hacia esas casillas; vale para cualquier grupo
# del bando que no vuele, embarcado o no, porque uno a pie solo pisa agua subiendo al barco en un puerto.
CAB_N = 2
CABD = place_data('cabd', bytes(0x80 * 0xa0))
# Fin de 0x4a4f90 (reemplaza su único epílogo, 0x4a5328).
cabgraph = place('cabgraph', f'''
    pushad
    xor ecx, ecx
cabg_init:
    xor eax, eax
    test byte ptr [ecx + 0x582158], 0x40
    jnz cabg_land
    mov al, 254
cabg_land:
    mov byte ptr [ecx + {CABD:#x}], al
    inc ecx
    cmp ecx, {0x80 * 0xa0:#x}
    jb cabg_init
    movsx ebp, word ptr [0x503e00]
    movsx esi, word ptr [0x503e02]
    xor ecx, ecx
cabg_1x:
    cmp ecx, ebp
    jge cabg_1end
    imul ebx, ecx, 0xa0
    xor edi, edi
cabg_1y:
    cmp edi, esi
    jge cabg_1nx
    movzx eax, byte ptr [ebx + {CABD:#x}]
    test eax, eax
    jz cabg_1st
    test ecx, ecx
    jz cabg_1a
    movzx edx, byte ptr [ebx + {CABD + (-0xa0):#x}]
    inc edx
    cmp edx, eax
    jae cabg_1r1
    mov eax, edx
cabg_1r1:
    test edi, edi
    jz cabg_1b
    movzx edx, byte ptr [ebx + {CABD + (-0xa1):#x}]
    inc edx
    cmp edx, eax
    jae cabg_1r2
    mov eax, edx
cabg_1r2:
cabg_1b:
    lea edx, [edi + 1]
    cmp edx, esi
    jge cabg_1a
    movzx edx, byte ptr [ebx + {CABD + (-0x9f):#x}]
    inc edx
    cmp edx, eax
    jae cabg_1r3
    mov eax, edx
cabg_1r3:
cabg_1a:
    test edi, edi
    jz cabg_1st
    movzx edx, byte ptr [ebx + {CABD + (-0x1):#x}]
    inc edx
    cmp edx, eax
    jae cabg_1r4
    mov eax, edx
cabg_1r4:
cabg_1st:
    mov byte ptr [ebx + {CABD:#x}], al
    inc ebx
    inc edi
    jmp cabg_1y
cabg_1nx:
    inc ecx
    jmp cabg_1x
cabg_1end:
    lea ecx, [ebp - 1]
cabg_2x:
    test ecx, ecx
    jl cabg_2end
    imul ebx, ecx, 0xa0
    lea edi, [esi - 1]
    add ebx, edi
cabg_2y:
    test edi, edi
    jl cabg_2nx
    movzx eax, byte ptr [ebx + {CABD:#x}]
    test eax, eax
    jz cabg_2st
    lea edx, [ecx + 1]
    cmp edx, ebp
    jge cabg_2a
    movzx edx, byte ptr [ebx + {CABD + (+0xa0):#x}]
    inc edx
    cmp edx, eax
    jae cabg_2r1
    mov eax, edx
cabg_2r1:
    lea edx, [edi + 1]
    cmp edx, esi
    jge cabg_2b
    movzx edx, byte ptr [ebx + {CABD + (+0xa1):#x}]
    inc edx
    cmp edx, eax
    jae cabg_2r2
    mov eax, edx
cabg_2r2:
cabg_2b:
    test edi, edi
    jz cabg_2a
    movzx edx, byte ptr [ebx + {CABD + (+0x9f):#x}]
    inc edx
    cmp edx, eax
    jae cabg_2r3
    mov eax, edx
cabg_2r3:
cabg_2a:
    lea edx, [edi + 1]
    cmp edx, esi
    jge cabg_2st
    movzx edx, byte ptr [ebx + {CABD + (+0x1):#x}]
    inc edx
    cmp edx, eax
    jae cabg_2r4
    mov eax, edx
cabg_2r4:
cabg_2st:
    mov byte ptr [ebx + {CABD:#x}], al
    dec ebx
    dec edi
    jmp cabg_2y
cabg_2nx:
    dec ecx
    jmp cabg_2x
cabg_2end:
    popad
    pop ebp
    pop edi
    pop esi
    pop ebx
    add esp, 0x14
    ret
''')
# Filtro de enlaces: eax = índice del grafo (x*0xa0 + y) de la casilla, cl = sus direcciones (bits de 0x4fe678; la
# vecina k es (x + [0x4fe658 + 2k], y + [0x4fe640 + 2k])). cabfwd: la casilla es el origen (expansión); cabbwd: es el
# destino y las vecinas los orígenes (rastreo de vuelta). Quita las direcciones prohibidas; preserva el resto.
# Entra después de pushad, con ebp = 0 (cabfwd) o 1 (cabbwd).
cabfilt = place('cabfilt', f'''
    mov esi, eax
    mov bl, cl
    cmp word ptr [0x5878b0], 0
    jne cabf_out
    movsx eax, word ptr [0x58715c]
    cmp eax, 8
    jae cabf_out
    call {boatcab:#x}
    test eax, eax
    jz cabf_out
    xor edi, edi
cabf_loop:
    test byte ptr [edi + 0x4fe678], bl
    jz cabf_next
    movsx eax, word ptr [edi*2 + 0x4fe658]
    imul eax, eax, 0xa0
    movsx edx, word ptr [edi*2 + 0x4fe640]
    add eax, edx
    add eax, esi
    mov edx, esi
    test ebp, ebp
    jnz cabf_dir
    xchg eax, edx
cabf_dir:
    cmp byte ptr [edx + 0x582158], 0x80
    jne cabf_next
    mov cl, byte ptr [edx + {CABD:#x}]
    cmp cl, {CAB_N}
    jbe cabf_next
    cmp cl, byte ptr [eax + {CABD:#x}]
    jb cabf_next
    mov al, byte ptr [edi + 0x4fe678]
    not al
    and bl, al
cabf_next:
    inc edi
    cmp edi, 8
    jb cabf_loop
    mov byte ptr [esp + 0x18], bl
cabf_out:
    popad
    ret
''')
cabfwd = place('cabfwd', f'''
    pushad
    xor ebp, ebp
    jmp {cabfilt:#x}
''')
cabbwd = place('cabbwd', f'''
    pushad
    mov ebp, 1
    jmp {cabfilt:#x}
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
    movsx ebp, word ptr [esi*2 + 0x4fe658]
    movsx edi, word ptr [esi*2 + 0x4fe640]
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
    call {cabfwd:#x}
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
    movsx eax, word ptr [edi*2 + 0x4fe658]
    imul eax, eax, 0xa0
    movsx edx, word ptr [edi*2 + 0x4fe640]
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
    push eax
    mov eax, esi
    call {cabbwd:#x}
    pop eax
    jmp 0x4a6048
''')

# Tope de stack en barco "Landing". El paso del movimiento (0x49e280) solo mira el tope del bando cuando la casilla de
# destino ya tiene ejércitos propios (0x49e467); una casilla vacía no tiene control. Este se engancha en 0x49e4a7, por
# donde pasa todo destino que el control original dejó pasar, y vale si el grupo no vuela (+0x1c != 2), el barco del
# bando tiene "Landing" y el destino es agua pura con la misma cuenta del ejecutor (0x49db70): sin edificio (& 0x4000),
# sin estructura 1 (puente) y clase 1, y no es punto de transbordo (0x4a6610). Cuenta grupo + ejércitos en la
# casilla (0x4411b0) y solo cuando el stack embarcado crece: el grupo se embarca ahora (no embarcado y con alguien que
# se embarca, 0x56eab0[i] == 0) o se suma a ejércitos propios en el agua. Un stack que ya navega con más de 5 (de antes
# del parche) sigue moviéndose; solo no crece, como el tope de voladores. Si pasa del tope, devuelve 4 (stack lleno):
# LANDCAP con "Landing" solo, LANDCAP_LC si el barco tiene también "Carrier" (con "Carrier" solo rige el del bando).
# Al bloquear deja en lchit 1 si el grupo se embarcaba (estaba en tierra) o 2 si se sumaba a barcos propios en el agua;
# nadie más lo escribe salvo ai_move, que lo pone en 0 antes de mover: así distingue este 4 del tope del bando.
LANDCAP = 5
LANDCAP_LC = 6
assert LANDCAP_LC == LANDCAP + 1     # el código suma boatcarr (0 o 1) a LANDCAP
lchit = place_data('lchit', bytes(4))
landcap = place('landcap', f'''
    pushad
    movsx esi, si
    movsx edi, di
    cmp word ptr [ebx + 0x56eaac], 2
    je lc_pass
    mov eax, ebp
    call {boatland:#x}
    test eax, eax
    jz lc_pass
    lea eax, [edi + edi*4]
    add eax, eax
    mov cl, byte ptr [0x503e06]
    shl eax, cl
    lea ecx, [esi + esi*4]
    lea eax, [eax + ecx*2 + 0x503e58]
    movzx ecx, word ptr [eax]
    test ch, 0x40
    jnz lc_pass
    mov dl, byte ptr [eax + 3]
    and dl, 7
    cmp dl, 1
    je lc_pass
    and ecx, 0x1f
    imul ecx, ecx, 0x58
    cmp word ptr [ecx + 0x535f0c], 1
    jne lc_pass
    push edi
    push esi
    call 0x4a6610
    add esp, 8
    test ax, ax
    jnz lc_pass
    push 0
    push edi
    push esi
    call 0x4411b0
    add esp, 12
    movsx ecx, ax
    movsx edx, word ptr [ebx + 0x56eaa8]
    test byte ptr [ebx + 0x56eaaa], 8
    jnz lc_emb
    xor eax, eax
lc_scan:
    cmp eax, edx
    jge lc_pass
    cmp byte ptr [ebx + eax + 0x56eab0], 0
    je lc_count
    inc eax
    jmp lc_scan
lc_emb:
    test ecx, ecx
    jz lc_pass
lc_count:
    add ecx, edx
    mov eax, ebp
    call {boatcarr:#x}
    add eax, {LANDCAP}
    cmp ecx, eax
    jle lc_pass
    mov al, 1
    test byte ptr [ebx + 0x56eaaa], 8
    jz lc_hit
    inc eax
lc_hit:
    mov byte ptr [{lchit:#x}], al
    popad
    mov word ptr [esp + 0x16], 4
    jmp 0x49e4dd
lc_pass:
    popad
    push edi
    push esi
    call 0x49e770
    jmp 0x49e4ae
''')

# Tope de pasos del barco según sus bonos de movimiento: el barco usa los pasos de su registro (+0x9b) pero nunca más
# que MVCAP ("Landing" solo, "Landing" y "Carrier", "Carrier" solo; sin ninguno de los dos, sin tope). Un barco más
# lento que el tope no se acelera. Se aplica al leer, no se escribe: el ajuste de partida 0x433b40 (que suma a los
# pasos de las 16 ranuras y los guarda) sigue igual y el tope rige sobre su resultado.
# Lecturas del barco (ranura 15, registro 0x53d2d4 + p*0xfc0): reinicio de pasos al empezar el turno (0x422b61),
# 0x466463, 0x4667cb, 0x466976, 0x49dc8b, 0x49de3e, costo del camino (0x4a62c1) y 0x4d34e0. Lecturas de cualquier
# ranura (solo cambian si es la 15): 0x43b773, 0x455a25, 0x477d0d, 0x4781f6, 0x48a793 y la columna de pasos de Army
# List (0x4a2a7c).
MVCAP = {'landing': 12, 'landing+carrier': 20, 'carrier': 24}
mvcaptab = place_data('mvcaptab', bytes([255, MVCAP['landing'], MVCAP['carrier'], MVCAP['landing+carrier']]))
# eax = pasos leídos (0..255), ecx = registro de unidad -> eax = con el tope si es el barco (ranura 15) de un bando
# 0..7. Preserva el resto y los flags.
bmvcap = place('bmvcap', f'''
    pushfd
    push ecx
    push edx
    push ebx
    mov ebx, eax
    lea eax, [ecx - 0x53c410]
    cmp eax, {8 * 0xfc0:#x}
    jae bmc_out
    xor edx, edx
    mov ecx, 0xfc
    div ecx
    test edx, edx
    jnz bmc_out
    mov ecx, eax
    and ecx, 15
    cmp ecx, 15
    jne bmc_out
    shr eax, 4
    mov ecx, eax
    call {boatland:#x}
    mov edx, eax
    mov eax, ecx
    call {boatcarr:#x}
    lea eax, [edx + eax*2]
    movzx eax, byte ptr [eax + {mvcaptab:#x}]
    cmp ebx, eax
    jbe bmc_out
    mov ebx, eax
bmc_out:
    mov eax, ebx
    pop ebx
    pop edx
    pop ecx
    popfd
    ret
''')
# Un enganche por lectura (call al stub + nops sobre la instrucción original). Ninguno toca los flags.
MV_SITES = [
    # (va, instrucción original, stub)
    (0x422b61, 'movzx di, byte ptr [edi + 0x53d36f]', '''push eax; push ecx; lea ecx, [edi + 0x53d2d4];
        movzx eax, byte ptr [ecx + 0x9b]; call BMV; mov di, ax; pop ecx; pop eax; ret'''),
    (0x466463, 'mov cl, byte ptr [edx + 0x53d36f]', '''push eax; lea ecx, [edx + 0x53d2d4];
        movzx eax, byte ptr [ecx + 0x9b]; call BMV; mov ecx, eax; pop eax; ret'''),          # ecx en 0 antes
    (0x4667cb, 'mov bl, byte ptr [edx + 0x53d36f]', '''push eax; push ecx; lea ecx, [edx + 0x53d2d4];
        movzx eax, byte ptr [ecx + 0x9b]; call BMV; mov bl, al; pop ecx; pop eax; ret'''),
    (0x466976, 'mov al, byte ptr [ebx + 0x53d36f]', '''push ecx; lea ecx, [ebx + 0x53d2d4];
        movzx eax, byte ptr [ecx + 0x9b]; call BMV; pop ecx; ret'''),                        # eax en 0 antes
    *[(va, 'movzx ax, byte ptr [eax + 0x53d36f]', '''push ecx; push eax; lea ecx, [eax + 0x53d2d4];
        movzx eax, byte ptr [ecx + 0x9b]; call BMV; mov word ptr [esp], ax; pop eax; pop ecx; ret''')
      for va in (0x49dc8b, 0x49de3e, 0x4a62c1, 0x4d34e0)],
    (0x43b773, 'mov dl, byte ptr [eax + 0x9b]', '''push eax; push ecx; mov ecx, eax;
        movzx eax, byte ptr [ecx + 0x9b]; call BMV; mov dl, al; pop ecx; pop eax; ret'''),
    (0x455a25, 'movzx di, byte ptr [esi + 0x53c4ab]', '''push eax; push ecx; lea ecx, [esi + 0x53c410];
        movzx eax, byte ptr [ecx + 0x9b]; call BMV; mov di, ax; pop ecx; pop eax; ret'''),
    (0x477d0d, 'movzx ax, byte ptr [edi + 0x53c4ab]', '''push ecx; push eax; lea ecx, [edi + 0x53c410];
        movzx eax, byte ptr [ecx + 0x9b]; call BMV; mov word ptr [esp], ax; pop eax; pop ecx; ret'''),
    (0x4781f6, 'movzx bx, byte ptr [ecx + 0x53c4ab]', '''push eax; push ecx; lea ecx, [ecx + 0x53c410];
        movzx eax, byte ptr [ecx + 0x9b]; call BMV; mov bx, ax; pop ecx; pop eax; ret'''),
    (0x48a793, 'movzx cx, byte ptr [edx + 0x53c4ab]', '''push eax; push ecx; lea ecx, [edx + 0x53c410];
        movzx eax, byte ptr [ecx + 0x9b]; call BMV; pop ecx; mov cx, ax; pop eax; ret'''),
    (0x4a2a7c, 'mov al, byte ptr [ecx*4 + 0x53c4ab]', '''push ecx; lea ecx, [ecx*4 + 0x53c410];
        movzx eax, byte ptr [ecx + 0x9b]; call BMV; pop ecx; ret'''),                        # eax en 0 antes
]
mv_stubs = [(va, orig, place(f'bmv_{va:x}', stub.replace('BMV', f'{bmvcap:#x}').replace('\n', ';')))
            for va, orig, stub in MV_SITES]

# Convoy: formar. Enganche en 0x49d05d (códigos 3, 4 y 7 del paso, "parar": 0x49c960(p, 5)). Con el código 4, barco
# del bando con "Carrier", grupo embarcado y destino D del líder en una casilla vecina con ejércitos propios
# embarcados: si D ya es del convoy del grupo, no cambia nada; si los dos convoyes (la casilla S del grupo y D, con lo
# que tengan enlazado) suman hasta 3 casillas, enlaza S con D sumando el enlace al que ya tenga cada una (S y D son
# puntas: un convoy de 2 casillas solo tiene puntas) y borra los destinos de D. Las dos cosas terminan como el código
# 1 (llegó: 0x485e30(p, -1, -1) y 0x49c960(p, 1)), sin el aviso de stack lleno. Si suman más, el aviso de siempre.
crlink = place('crlink', f'''
    cmp word ptr [esi], 4
    jne crl_orig
    pushad
    movsx ebp, byte ptr [esi + 2]
    cmp ebp, 8
    jae crl_no
    mov eax, ebp
    call {boatcarr:#x}
    test eax, eax
    jz crl_no
    imul ebx, ebp, 0x4f0
    test byte ptr [ebx + 0x56eaaa], 8
    jz crl_no
    movsx eax, word ptr [ebx + 0x56ea90]
    imul eax, eax, 0x1c
    movsx esi, word ptr [eax + 0x54fe52]
    movsx edi, word ptr [eax + 0x54fe54]
    movsx ecx, word ptr [eax + 0x54fe56]
    movsx edx, word ptr [eax + 0x54fe58]
    sub ecx, esi
    sub edx, edi
    lea eax, [ecx + 1]
    cmp eax, 2
    ja crl_no
    lea eax, [edx + 1]
    cmp eax, 2
    ja crl_no
    lea ebx, [edx*4 + 5]
    add ebx, ecx
    cmp ebx, 5
    je crl_no
    lea eax, [esi + ecx]
    lea edx, [edi + edx]
    push eax
    push edx
    mov ecx, 0x200
    call {crscan:#x}
    test eax, eax
    jz crl_no2
    call {crconv:#x}
    mov ecx, eax
    test eax, eax
    jz crl_d
    mov eax, dword ptr [esp + 4]
    mov edx, dword ptr [esp]
    cmp eax, dword ptr [{CRCV:#x}]
    jne crl_c2
    cmp edx, dword ptr [{CRCV + 4:#x}]
    je crl_done
crl_c2:
    cmp ecx, 2
    jb crl_d
    cmp eax, dword ptr [{CRCV + 8:#x}]
    jne crl_d
    cmp edx, dword ptr [{CRCV + 0xc:#x}]
    je crl_done
crl_d:
    push esi
    push edi
    mov esi, dword ptr [esp + 0xc]
    mov edi, dword ptr [esp + 8]
    call {crconv:#x}
    pop edi
    pop esi
    add ecx, eax
    cmp ecx, 1
    ja crl_no2
    call {crlinks:#x}
    mov edx, dword ptr [{CRLK + 4:#x}]
    mov eax, ebx
    call {crenc:#x}
    lea ecx, [eax + 0x800]
    mov eax, esi
    mov edx, edi
    call {crscan:#x}
    mov esi, dword ptr [esp + 4]
    mov edi, dword ptr [esp]
    call {crlinks:#x}
    mov edx, dword ptr [{CRLK + 4:#x}]
    mov eax, 10
    sub eax, ebx
    call {crenc:#x}
    lea ecx, [eax + 0x900]
    mov eax, esi
    mov edx, edi
    call {crscan:#x}
crl_done:
    add esp, 8
    popad
    movsx ax, byte ptr [esi + 2]
    push -1
    push -1
    push eax
    call 0x485e30
    add esp, 12
    movsx ax, byte ptr [esi + 2]
    push 1
    push eax
    call 0x49c960
    add esp, 8
    pop edi
    pop esi
    pop ebx
    ret
crl_no2:
    add esp, 8
crl_no:
    popad
crl_orig:
    movsx ax, byte ptr [esi + 2]
    jmp 0x49d062
''')
# eax = x, edx = y -> (esi, edi): mueve los ejércitos vivos del jugador ebp de la casilla, restando ecx (el costo del
# paso) a sus movimientos sin bajar de 0, y borra sus destinos. Preserva todo.
crmove = place('crmove', '''
    push ebx
    push ecx
    mov ebx, 1
crm_loop:
    push eax
    movsx eax, word ptr [0x54fe50]
    cmp ebx, eax
    pop eax
    jge crm_end
    imul ecx, ebx, 0x1c
    test byte ptr [ecx + 0x54fe63], 0x40
    jz crm_next
    cmp word ptr [ecx + 0x54fe52], ax
    jne crm_next
    cmp word ptr [ecx + 0x54fe54], dx
    jne crm_next
    push edx
    movzx edx, word ptr [ecx + 0x54fe5e]
    shr edx, 5
    and edx, 0xf
    cmp edx, ebp
    pop edx
    jne crm_next
    mov word ptr [ecx + 0x54fe52], si
    mov word ptr [ecx + 0x54fe54], di
    mov dword ptr [ecx + 0x54fe56], 0xffffffff
    push edx
    movzx edx, byte ptr [ecx + 0x54fe61]
    and edx, 0x7f
    sub edx, dword ptr [esp + 4]
    jns crm_pos
    xor edx, edx
crm_pos:
    cmp edx, 0x7f
    jbe crm_set
    mov edx, 0x7f
crm_set:
    and byte ptr [ecx + 0x54fe61], 0x80
    or byte ptr [ecx + 0x54fe61], dl
    pop edx
crm_next:
    inc ebx
    jmp crm_loop
crm_end:
    pop ecx
    pop ebx
    ret
''')
# Convoy: seguir. Enganche en 0x49cdc7, en el paso (código 0) después de embarcar/desembarcar (0x49db70), en todas
# las máquinas. A = de donde salió el grupo ([0x572990], [0x572994]), N = adonde llegó. Si algún ejército del grupo
# está enlazado, el bando tiene "Carrier", el grupo sigue embarcado, N es vecina de A, A quedó vacía y alguno de los
# enlaces de A vale (la casilla vecina apunta de vuelta):
#  - A era punta, enlazada con P (y P quizá con Q): lo de P pasa a A y lo de Q a P, en fila;
#  - A era el medio, enlazada con P y P': lo de la más lejana de N (P si empatan) pasa a A; la otra queda y sigue
#    enlazada con A;
# siempre que N no sea una casilla del convoy. Lo que se mueve resta el costo del paso a sus movimientos (sin bajar
# de 0) y pierde el destino; los enlaces quedan N - A - (P o P'). Si no, el grupo se desenlaza (salió del convoy una
# parte, o desembarcó). Ocupación de las casillas tocadas con 0x49d450; mapa con 0x4a2170.
# Anota en crface[jugador] la casilla A (x, y) y la dirección del paso P -> A, y en crface2[jugador] P y la dirección
# Q -> P (x = 0x7fff si no hubo), para dibujar esas casillas mirando hacia donde avanzaron (crdraw). Direcciones del
# juego (0x49cbf1..0x49ccfb): índice (dx + 1) + 3*(dy + 1).
# Marco: [esp] A, [+8] N, [+0x10] costo, [+0x14] cod de A a P, [+0x18] el otro enlace que le queda a A (o -1),
# [+0x1c] 1 si A era el medio, [+0x20] P, [+0x28] Q o P' (x = 0x7fff: no hay), [+0x30] cod de A a N.
CR_FTAB = place_data('cr_ftab', bytes([7, 0, 1, 6, 4, 2, 5, 4, 3]))
CRFACE = place_data('crface', b'\xff\x7f' * 64)    # 2 x 8 x (x, y, dirección, -); x = 0x7fff: nada anotado
crfollow = place('crfollow', f'''
    add esp, 0x14
    pushad
    sub esp, 0x40
    movsx ebp, byte ptr [esi + 2]
    cmp ebp, 8
    jae cf_out
    imul ebx, ebp, 0x4f0
    movsx ecx, word ptr [ebx + 0x56eaa8]
    xor edx, edx
cf_find:
    cmp edx, ecx
    jge cf_out
    movsx eax, word ptr [ebx + edx*2 + 0x56ea94]
    imul eax, eax, 0x1c
    movzx edi, byte ptr [eax + 0x54fe6b]
    test edi, 0x80
    jnz cf_found
    inc edx
    jmp cf_find
cf_found:
    mov eax, ebp
    call {boatcarr:#x}
    test eax, eax
    jz cf_clear
    test byte ptr [ebx + 0x56eaaa], 8
    jz cf_clear
    movsx eax, word ptr [esi + 4]
    mov dword ptr [esp + 8], eax
    movsx eax, word ptr [esi + 6]
    mov dword ptr [esp + 0xc], eax
    movsx eax, byte ptr [esi + 3]
    mov dword ptr [esp + 0x10], eax
    mov eax, edi
    call {crdec:#x}
    test eax, eax
    js cf_clear
    mov dword ptr [esp + 0x14], eax
    mov dword ptr [esp + 0x18], edx
    movsx esi, word ptr [0x572990]
    movsx edi, word ptr [0x572994]
    mov dword ptr [esp], esi
    mov dword ptr [esp + 4], edi
    mov eax, dword ptr [esp + 8]
    sub eax, esi
    lea ecx, [eax + 1]
    cmp ecx, 2
    ja cf_clear
    mov edx, dword ptr [esp + 0xc]
    sub edx, edi
    lea ecx, [edx + 1]
    cmp ecx, 2
    ja cf_clear
    lea ecx, [edx*4 + 5]
    add ecx, eax
    cmp ecx, 5
    je cf_clear
    mov dword ptr [esp + 0x30], ecx
    push 0
    push edi
    push esi
    call 0x4411b0
    add esp, 12
    test ax, ax
    jnz cf_clear
    xor ecx, ecx
    mov eax, dword ptr [esp + 0x14]
    call {crback:#x}
    test eax, eax
    jz cf_l2
    inc ecx
cf_l2:
    mov eax, dword ptr [esp + 0x18]
    test eax, eax
    js cf_l3
    call {crback:#x}
    test eax, eax
    jz cf_l3
    mov eax, dword ptr [esp + 0x18]
    mov dword ptr [esp + ecx*4 + 0x14], eax
    inc ecx
cf_l3:
    test ecx, ecx
    jz cf_clear
    mov dword ptr [esp + 0x1c], 0
    mov dword ptr [esp + 0x28], 0x7fff
    mov eax, dword ptr [esp + 0x14]
    call {crxy:#x}
    mov dword ptr [esp + 0x20], eax
    mov dword ptr [esp + 0x24], edx
    cmp ecx, 2
    je cf_mid
    mov dword ptr [esp + 0x18], -1
    mov esi, eax
    mov edi, edx
    call {crlinks:#x}
    test eax, eax
    jz cf_chk
    mov eax, dword ptr [{CRLK + 4:#x}]
    call {crxy:#x}
    mov dword ptr [esp + 0x28], eax
    mov dword ptr [esp + 0x2c], edx
    mov eax, dword ptr [esp + 0x14]
    mov dword ptr [esp + 0x18], eax
    jmp cf_chk
cf_mid:
    mov dword ptr [esp + 0x1c], 1
    mov eax, dword ptr [esp + 0x18]
    call {crxy:#x}
    mov dword ptr [esp + 0x28], eax
    mov dword ptr [esp + 0x2c], edx
    mov eax, dword ptr [esp + 0x20]
    sub eax, dword ptr [esp + 8]
    mov edx, dword ptr [esp + 0x24]
    sub edx, dword ptr [esp + 0xc]
    call {crcheb:#x}
    mov ecx, eax
    mov eax, dword ptr [esp + 0x28]
    sub eax, dword ptr [esp + 8]
    mov edx, dword ptr [esp + 0x2c]
    sub edx, dword ptr [esp + 0xc]
    call {crcheb:#x}
    cmp eax, ecx
    jle cf_chk
    mov eax, dword ptr [esp + 0x14]
    mov edx, dword ptr [esp + 0x18]
    mov dword ptr [esp + 0x14], edx
    mov dword ptr [esp + 0x18], eax
    mov eax, dword ptr [esp + 0x20]
    mov edx, dword ptr [esp + 0x28]
    mov dword ptr [esp + 0x20], edx
    mov dword ptr [esp + 0x28], eax
    mov eax, dword ptr [esp + 0x24]
    mov edx, dword ptr [esp + 0x2c]
    mov dword ptr [esp + 0x24], edx
    mov dword ptr [esp + 0x2c], eax
cf_chk:
    mov eax, dword ptr [esp + 8]
    mov edx, dword ptr [esp + 0xc]
    cmp eax, dword ptr [esp + 0x20]
    jne cf_c2
    cmp edx, dword ptr [esp + 0x24]
    je cf_clear
cf_c2:
    cmp eax, dword ptr [esp + 0x28]
    jne cf_go
    cmp edx, dword ptr [esp + 0x2c]
    je cf_clear
cf_go:
    cmp dword ptr [esp + 0x1c], 0
    je cf_mv
    mov dword ptr [esp + 0x28], 0x7fff
cf_mv:
    mov eax, dword ptr [esp + 0x20]
    mov edx, dword ptr [esp + 0x24]
    mov esi, dword ptr [esp]
    mov edi, dword ptr [esp + 4]
    mov ecx, dword ptr [esp + 0x10]
    call {crmove:#x}
    sub esi, eax
    sub edi, edx
    lea edx, [edi + edi*2 + 4]
    add edx, esi
    mov al, byte ptr [edx + {CR_FTAB:#x}]
    mov byte ptr [ebp*8 + {CRFACE + 4:#x}], al
    mov eax, dword ptr [esp]
    mov word ptr [ebp*8 + {CRFACE:#x}], ax
    mov eax, dword ptr [esp + 4]
    mov word ptr [ebp*8 + {CRFACE + 2:#x}], ax
    mov word ptr [ebp*8 + {CRFACE + 0x40:#x}], 0x7fff
    cmp dword ptr [esp + 0x28], 0x7fff
    je cf_lk
    mov eax, dword ptr [esp + 0x28]
    mov edx, dword ptr [esp + 0x2c]
    mov esi, dword ptr [esp + 0x20]
    mov edi, dword ptr [esp + 0x24]
    mov ecx, dword ptr [esp + 0x10]
    call {crmove:#x}
    mov word ptr [ebp*8 + {CRFACE + 0x40:#x}], si
    mov word ptr [ebp*8 + {CRFACE + 0x42:#x}], di
    sub esi, eax
    sub edi, edx
    lea edx, [edi + edi*2 + 4]
    add edx, esi
    mov al, byte ptr [edx + {CR_FTAB:#x}]
    mov byte ptr [ebp*8 + {CRFACE + 0x44:#x}], al
    mov eax, dword ptr [esp + 0x20]
    mov edx, dword ptr [esp + 0x24]
    mov ecx, 0x88a
    sub ecx, dword ptr [esp + 0x14]
    call {crscan:#x}
cf_lk:
    mov eax, dword ptr [esp + 0x30]
    mov edx, dword ptr [esp + 0x18]
    call {crenc:#x}
    lea ecx, [eax + 0x800]
    mov eax, dword ptr [esp]
    mov edx, dword ptr [esp + 4]
    call {crscan:#x}
    mov eax, dword ptr [esp + 8]
    mov edx, dword ptr [esp + 0xc]
    mov ecx, 0x88a
    sub ecx, dword ptr [esp + 0x30]
    call {crscan:#x}
    push dword ptr [esp + 4]
    push dword ptr [esp + 4]
    call 0x49d450
    add esp, 8
    push dword ptr [esp + 0x24]
    push dword ptr [esp + 0x24]
    call 0x49d450
    add esp, 8
    cmp dword ptr [esp + 0x28], 0x7fff
    je cf_draw
    push dword ptr [esp + 0x2c]
    push dword ptr [esp + 0x2c]
    call 0x49d450
    add esp, 8
cf_draw:
    call {REDRAW:#x}
    jmp cf_out
cf_clear:
    movsx ecx, word ptr [ebx + 0x56eaa8]
    xor edx, edx
cf_cl:
    cmp edx, ecx
    jge cf_out
    movsx eax, word ptr [ebx + edx*2 + 0x56ea94]
    imul eax, eax, 0x1c
    mov byte ptr [eax + 0x54fe6b], 0
    inc edx
    jmp cf_cl
cf_out:
    add esp, 0x40
    popad
    mov cx, word ptr [esi + 6]
    jmp 0x49cdce
''')
# Convoy: defensa conjunta. Reemplaza 0x464c3d..0x464c51 de 0x464ac0 (armado del combate, casilla sin ciudad;
# si = x, di = y, defensores en [esp+0x30], hasta 32 como en una ciudad de 4 casillas; cuenta en [esp+0x12]). Si la
# casilla atacada es de un convoy, suma los ejércitos de las otras casillas (hasta 3 x 8 = 24). Lo que muere se limpia
# después en la reconstrucción de ocupación (0x441290) que hace el combate.
crdef = place('crdef', f'''
    lea eax, [esp + 0x30]
    push eax
    push edi
    push esi
    call 0x4411b0
    mov word ptr [esp + 0x1e], ax
    add esp, 0xc
    pushad
    movsx esi, si
    movsx edi, di
    call {crconv:#x}
    mov ebx, eax
    xor ebp, ebp
cd_loop:
    cmp ebp, ebx
    jge cd_out
    movsx eax, word ptr [esp + 0x32]
    cmp eax, 24
    ja cd_out
    lea eax, [esp + eax*2 + 0x50]
    push eax
    push dword ptr [ebp*8 + {CRCV + 4:#x}]
    push dword ptr [ebp*8 + {CRCV:#x}]
    call 0x4411b0
    add esp, 12
    add word ptr [esp + 0x32], ax
    inc ebp
    jmp cd_loop
cd_out:
    popad
    jmp 0x464c51
''')
# Convoy: dibujo. Reemplaza "call 0x4dd530" en 0x459d0d de 0x459790 (ejército quieto de una celda de la vista: un solo
# cuadro por tipo, sin dirección; esi = celda, ebp = vista, columna y fila en [esp+0x14]/[esp+0x16] del llamador,
# origen de la vista en [ebp+0x28]/[ebp+0x2a]; dueño en [esi+4] & 0xf, como lo carga 0x457909). Si la casilla es una
# casilla quieta del convoy cuyo grupo activo es el del dueño (estructura de sprite ebp + 0x2c*p, armada por
# 0x457cd0), la dibuja como 0x459e4f dibuja ese grupo: su hoja animada [+0x60], columna de la dirección
# (dir*0x31 + 0x81) y el mismo cuadro. Dirección: la anotada por crfollow si es esta casilla (crface o crface2); si
# no, la del grupo [+0x50]. Sin animaciones ([0x560758]) o con la imagen 0xa4 queda el dibujo original.
crdraw = place('crdraw', f'''
    cmp dword ptr [esp + 4], 0xa4
    je cw_go
    cmp byte ptr [0x560758], 0
    jne cw_go
    pushad
    sub esp, 0x10
    movzx ebx, word ptr [esi + 4]
    and ebx, 0xf
    cmp ebx, 8
    jae cw_out
    imul ecx, ebx, 0x4f0
    cmp word ptr [ecx + 0x56eaa8], 0
    jle cw_out
    test byte ptr [ecx + 0x56eaaa], 8
    jz cw_out
    movsx eax, word ptr [ecx + 0x56ea90]
    test eax, eax
    jle cw_out
    imul eax, eax, 0x1c
    movsx edx, word ptr [eax + 0x54fe52]
    mov dword ptr [esp + 8], edx
    movsx edx, word ptr [eax + 0x54fe54]
    mov dword ptr [esp + 0xc], edx
    movsx eax, word ptr [esp + 0x68]
    movsx edx, word ptr [ebp + 0x28]
    add eax, edx
    mov dword ptr [esp], eax
    movsx eax, word ptr [esp + 0x6a]
    movsx edx, word ptr [ebp + 0x2a]
    add eax, edx
    mov dword ptr [esp + 4], eax
    mov eax, dword ptr [esp + 8]
    sub eax, dword ptr [esp]
    add eax, 2
    cmp eax, 4
    ja cw_out
    mov edx, dword ptr [esp + 0xc]
    sub edx, dword ptr [esp + 4]
    add edx, 2
    cmp edx, 4
    ja cw_out
    lea eax, [eax + edx*8]
    cmp eax, 18
    je cw_out
    imul edi, ebx, 0x2c
    add edi, ebp
    cmp byte ptr [edi + 0x44], 0
    je cw_out
    cmp byte ptr [edi + 0x59], 0
    jne cw_out
    cmp byte ptr [edi + 0x5b], 0
    jne cw_out
    push edi
    mov esi, dword ptr [esp + 4]
    mov edi, dword ptr [esp + 8]
    call {crconv:#x}
    pop edi
    test eax, eax
    jz cw_out
    mov ecx, dword ptr [esp + 8]
    mov edx, dword ptr [esp + 0xc]
    cmp ecx, dword ptr [{CRCV:#x}]
    jne cw_c2
    cmp edx, dword ptr [{CRCV + 4:#x}]
    je cw_in
cw_c2:
    cmp eax, 2
    jb cw_out
    cmp ecx, dword ptr [{CRCV + 8:#x}]
    jne cw_out
    cmp edx, dword ptr [{CRCV + 0xc:#x}]
    jne cw_out
cw_in:
    movzx eax, word ptr [edi + 0x50]
    movsx ecx, word ptr [ebx*8 + {CRFACE:#x}]
    cmp ecx, dword ptr [esp]
    jne cw_f2
    movsx ecx, word ptr [ebx*8 + {CRFACE + 2:#x}]
    cmp ecx, dword ptr [esp + 4]
    jne cw_f2
    movzx eax, byte ptr [ebx*8 + {CRFACE + 4:#x}]
    jmp cw_dir
cw_f2:
    movsx ecx, word ptr [ebx*8 + {CRFACE + 0x40:#x}]
    cmp ecx, dword ptr [esp]
    jne cw_dir
    movsx ecx, word ptr [ebx*8 + {CRFACE + 0x42:#x}]
    cmp ecx, dword ptr [esp + 4]
    jne cw_dir
    movzx eax, byte ptr [ebx*8 + {CRFACE + 0x44:#x}]
cw_dir:
    and eax, 7
    imul eax, eax, 0x31
    add eax, 0x81
    mov dword ptr [esp + 0x38], eax
    cmp byte ptr [ebx + 0x4fe110], 0
    jne cw_mov
    cmp word ptr [0x560b20], bx
    jne cw_mov
    mov eax, 0x94
    test byte ptr [ebp + 0x3c], 4
    jz cw_fr
    mov eax, 0xc5
    jmp cw_fr
cw_mov:
    movsx eax, word ptr [edi + 0x4e]
    cdq
    xor eax, edx
    sub eax, edx
    and eax, 3
    xor eax, edx
    sub eax, edx
    imul eax, eax, 0x31
    inc eax
cw_fr:
    mov dword ptr [esp + 0x3c], eax
    mov eax, dword ptr [edi + 0x60]
    mov dword ptr [esp + 0x34], eax
cw_out:
    add esp, 0x10
    popad
cw_go:
    jmp 0x4dd530
''')

# ---------------------------------------------------------------- Puentes: derribar y reconstruir
# Un puente es una casilla de clase agua sin edificio (palabra 0 & 0x4000) con estructura 1 ([+3] & 7); en los mapas
# vienen de a 2 casillas unidas por un lado (102 de 102 en las partidas). Derribado: estructura 0 y bit 0x80 de [+9]
# (nadie más lo usa: el byte +8/+9 solo se lee enmascarado a 0xff, en 0x412ac5). Los demás bits de +8/+9 se dejan:
# reconstruir solo vuelve a poner la estructura 1. Con estructura 0 la casilla es agua: el grafo de pasos (0x4a4f90)
# la deja navegable para los barcos y cortada para los de tierra.
# El juego arrasa y reconstruye "sitios" por índice (word) en todo el recorrido: menú, diálogo, red (0x18d/0x1cf y
# 0x18e/0x1c9) y aplicación. Un puente viaja por ese mismo camino con el código BR_CODE + (y << 7) + x (la grilla
# 0x582158 es x*160 + y en 0x5000 bytes: x < 128, y < 160; el máximo 0x6fff sigue positivo para los "jl" del juego, y
# los sitios son muchos menos que 0x2000).
# Arrasar un puente: la opción de arrasar sitios ([0x53c393] & 6 >= 2), el líder en una casilla vecina (no encima) y
# ningún ejército ajeno sobre el puente: si lo hay, el diálogo avisa que primero hay que atacarlo (el combate normal
# del juego). Los ejércitos propios que quedan encima caen al agua como en el desbande (0x485610, con su aviso);
# 0x43c240 deja fuera a los que vuelan y a los embarcados. Reconstruir cuesta lo de fundar una ciudad ([0x56950e]),
# con el descuento del jugador como el de los sitios (0x4b65e0), y exige el puente vacío (aviso 0x72).
BR_CODE = 0x2000
BR_KIND_INTACT, BR_KIND_RAZED = 1, 2
br_xy = place_data('br_xy', bytes(4 * 8))               # componente: (x | y << 16) por casilla, hasta 8
br_d8 = place_data('br_d8', struct.pack('<8h8h', -1, 0, 1, -1, 1, -1, 0, 1, -1, -1, -1, 0, 0, 1, 1, 1))
br_d4 = place_data('br_d4', struct.pack('<4h4h', 0, -1, 1, 0, -1, 0, 0, 1))
str_the_bridge = place_data('str_the_bridge', cstr_('the bridge'))
str_The_bridge = place_data('str_The_bridge', cstr_('The bridge'))
br_namebuf = place_data('br_namebuf', bytes(0x140))
br_namecode = place_data('br_namecode', struct.pack('<i', -1))
str_brname_file = place_data('str_brname_file', cstr_('DATA\\BRIDNAME.TXT'))
str_br_enemy1 = place_data('str_br_enemy1', cstr_('Enemies hold the bridge!'))
str_br_enemy2 = place_data('str_br_enemy2', cstr_('Attack them first.'))
# eax = x, edx = y -> eax = casilla, o 0 si cae fuera del mapa. Preserva el resto.
br_tile = place('br_tile', '''
    test eax, eax
    jl brt_no
    test edx, edx
    jl brt_no
    push ecx
    movsx ecx, word ptr [0x503e00]
    cmp eax, ecx
    jge brt_nopop
    movsx ecx, word ptr [0x503e02]
    cmp edx, ecx
    jge brt_nopop
    push edx
    lea edx, [edx + edx*4]
    add edx, edx
    mov cl, byte ptr [0x503e06]
    shl edx, cl
    lea eax, [eax + eax*4]
    lea eax, [edx + eax*2 + 0x503e58]
    pop edx
    pop ecx
    ret
brt_nopop:
    pop ecx
brt_no:
    xor eax, eax
    ret
''')
# eax = casilla -> eax = 1 puente entero, 2 puente derribado, 0 otra cosa. Preserva el resto.
br_kind = place('br_kind', '''
    push ecx
    push edx
    mov edx, eax
    movzx ecx, word ptr [edx]
    test ch, 0x40
    jnz brk_no
    and ecx, 0x1f
    imul ecx, ecx, 0x58
    cmp word ptr [ecx + 0x535f0c], 1
    jne brk_no
    mov cl, byte ptr [edx + 3]
    and cl, 7
    cmp cl, 1
    je brk_intact
    test cl, cl
    jnz brk_no
    test byte ptr [edx + 9], 0x80
    jz brk_no
    mov eax, 2
    jmp brk_out
brk_intact:
    mov eax, 1
    jmp brk_out
brk_no:
    xor eax, eax
brk_out:
    pop edx
    pop ecx
    ret
''')
# br_find(x, y, tipo) cdecl -> eax = código de la primera casilla vecina (8 direcciones) de ese tipo, o -1.
# Para arrasar (tipo 1), -1 también si el propio (x, y) es un puente entero: no se derriba el puente que se pisa.
br_find = place('br_find', f'''
    push ebx
    push esi
    push edi
    push ebp
    movsx esi, word ptr [esp + 0x14]
    movsx edi, word ptr [esp + 0x18]
    mov ebp, dword ptr [esp + 0x1c]
    cmp ebp, {BR_KIND_INTACT}
    jne brf_scan
    mov eax, esi
    mov edx, edi
    call {br_tile:#x}
    test eax, eax
    jz brf_none
    call {br_kind:#x}
    cmp eax, {BR_KIND_INTACT}
    je brf_none
brf_scan:
    xor ebx, ebx
brf_loop:
    movsx eax, word ptr [ebx*2 + {br_d8:#x}]
    add eax, esi
    movsx edx, word ptr [ebx*2 + {br_d8 + 16:#x}]
    add edx, edi
    push eax
    call {br_tile:#x}
    test eax, eax
    jz brf_next
    call {br_kind:#x}
    cmp eax, ebp
    jne brf_next
    pop eax
    shl edx, 7
    lea eax, [eax + edx + {BR_CODE:#x}]
    jmp brf_out
brf_next:
    pop eax
    inc ebx
    cmp ebx, 8
    jb brf_loop
brf_none:
    or eax, -1
brf_out:
    pop ebp
    pop edi
    pop esi
    pop ebx
    ret
''')
# br_comp(código, tipo) cdecl -> eax = casillas del puente (unidas por un lado, del mismo tipo, hasta 8) en br_xy;
# 0 si el código no es de un puente de ese tipo.
br_comp = place('br_comp', f'''
    push ebx
    push esi
    push edi
    push ebp
    movsx eax, word ptr [esp + 0x14]
    sub eax, {BR_CODE:#x}
    jl brc_zero
    mov edx, eax
    shr edx, 7
    and eax, 0x7f
    mov word ptr [{br_xy:#x}], ax
    mov word ptr [{br_xy + 2:#x}], dx
    call {br_tile:#x}
    test eax, eax
    jz brc_zero
    call {br_kind:#x}
    cmp eax, dword ptr [esp + 0x18]
    jne brc_zero
    mov ebp, 1
    xor esi, esi
brc_outer:
    xor ebx, ebx
brc_dir:
    movsx eax, word ptr [esi*4 + {br_xy:#x}]
    movsx ecx, word ptr [ebx*2 + {br_d4:#x}]
    add eax, ecx
    movsx edx, word ptr [esi*4 + {br_xy + 2:#x}]
    movsx ecx, word ptr [ebx*2 + {br_d4 + 8:#x}]
    add edx, ecx
    mov edi, eax
    call {br_tile:#x}
    test eax, eax
    jz brc_next
    call {br_kind:#x}
    cmp eax, dword ptr [esp + 0x18]
    jne brc_next
    shl edx, 16
    or edx, edi
    xor ecx, ecx
brc_dup:
    cmp edx, dword ptr [ecx*4 + {br_xy:#x}]
    je brc_next
    inc ecx
    cmp ecx, ebp
    jb brc_dup
    cmp ebp, 8
    jae brc_next
    mov dword ptr [ebp*4 + {br_xy:#x}], edx
    inc ebp
brc_next:
    inc ebx
    cmp ebx, 4
    jb brc_dir
    inc esi
    cmp esi, ebp
    jb brc_outer
    mov eax, ebp
    jmp brc_out
brc_zero:
    xor eax, eax
brc_out:
    pop ebp
    pop edi
    pop esi
    pop ebx
    ret
''')
# br_armies(n, jugador) cdecl, sobre las n casillas de br_xy -> eax = ejércitos vivos de otro dueño, edx = todos.
br_armies = place('br_armies', f'''
    push ebx
    push esi
    push edi
    push ebp
    xor esi, esi
    xor edi, edi
    xor ebx, ebx
bra_loop:
    movsx eax, word ptr [0x54fe50]
    cmp ebx, eax
    jge bra_end
    imul eax, ebx, 0x1c
    test byte ptr [eax + 0x54fe63], 0x40
    jz bra_next
    mov edx, dword ptr [eax + 0x54fe52]
    mov ecx, dword ptr [esp + 0x14]
bra_j:
    dec ecx
    js bra_next
    cmp edx, dword ptr [ecx*4 + {br_xy:#x}]
    jne bra_j
    inc edi
    movzx edx, word ptr [eax + 0x54fe5e]
    and edx, 0x1e0
    shr edx, 5
    movsx ecx, word ptr [esp + 0x18]
    cmp edx, ecx
    je bra_next
    inc esi
bra_next:
    inc ebx
    jmp bra_loop
bra_end:
    mov eax, esi
    mov edx, edi
    pop ebp
    pop edi
    pop esi
    pop ebx
    ret
''')
# br_drown(n, jugador) cdecl: los ejércitos del jugador sobre las n casillas de br_xy que pueden ahogarse (0x43c240)
# caen al agua con 0x485610(jugador, ejército, 1, 0, 1, 0), que ahoga a todos los de esa casilla y da el aviso.
br_drown = place('br_drown', f'''
    push ebx
    push esi
    push edi
    push ebp
    xor ebx, ebx
brd_loop:
    movsx eax, word ptr [0x54fe50]
    cmp ebx, eax
    jge brd_end
    imul esi, ebx, 0x1c
    test byte ptr [esi + 0x54fe63], 0x40
    jz brd_next
    movzx eax, word ptr [esi + 0x54fe5e]
    and eax, 0x1e0
    shr eax, 5
    movsx ecx, word ptr [esp + 0x18]
    cmp eax, ecx
    jne brd_next
    mov edx, dword ptr [esi + 0x54fe52]
    mov ecx, dword ptr [esp + 0x14]
brd_j:
    dec ecx
    js brd_next
    cmp edx, dword ptr [ecx*4 + {br_xy:#x}]
    jne brd_j
    movsx eax, word ptr [esp + 0x18]
    push ebx
    push eax
    call 0x43c240
    add esp, 8
    test al, al
    jz brd_next
    movsx eax, word ptr [esp + 0x18]
    push 0
    push 1
    push 0
    push 1
    push ebx
    push eax
    call 0x485610
    add esp, 0x18
brd_next:
    inc ebx
    jmp brd_loop
brd_end:
    pop ebp
    pop edi
    pop esi
    pop ebx
    ret
''')
# Búsquedas del menú y las teclas: en lugar de 0x440b30(x, y) (sitio en la casilla del líder). Si no hay sitio,
# el puente vecino. Arrasar: 0x4205c1, 0x41c98c, 0x44c2d7, 0x4b05d1. Reconstruir: 0x42053f, 0x41caab.
br_razelk = place('br_razelk', f'''
    mov eax, dword ptr [esp + 8]
    push eax
    mov eax, dword ptr [esp + 8]
    push eax
    call 0x440b30
    add esp, 8
    test ax, ax
    jge brz_out
    mov al, byte ptr [0x53c393]
    and al, 6
    cmp al, 2
    jb brz_none
    push {BR_KIND_INTACT}
    push dword ptr [esp + 0xc]
    push dword ptr [esp + 0xc]
    call {br_find:#x}
    add esp, 0xc
    ret
brz_none:
    or eax, -1
brz_out:
    ret
''')
br_rebuildlk = place('br_rebuildlk', f'''
    mov eax, dword ptr [esp + 8]
    push eax
    mov eax, dword ptr [esp + 8]
    push eax
    call 0x440b30
    add esp, 8
    test ax, ax
    jge brb_out
    push {BR_KIND_RAZED}
    push dword ptr [esp + 0xc]
    push dword ptr [esp + 0xc]
    call {br_find:#x}
    add esp, 0xc
brb_out:
    ret
''')
# Habilitación del menú (salidas de 0x4b0660, esi = búfer, bl = no es su turno, bp = líder). Raze (+8) y Build (+0xc)
# se encienden también con un puente vecino entero / derribado.
br_menu = place('br_menu', f'''
    test bl, bl
    jnz brm_out
    test bp, bp
    jz brm_out
    movsx eax, bp
    imul eax, eax, 0x1c
    movsx edi, word ptr [eax + 0x54fe52]
    movsx ebp, word ptr [eax + 0x54fe54]
    cmp byte ptr [esi + 8], 0
    jne brm_reb
    mov al, byte ptr [0x53c393]
    and al, 6
    cmp al, 2
    jb brm_reb
    push {BR_KIND_INTACT}
    push ebp
    push edi
    call {br_find:#x}
    add esp, 0xc
    test ax, ax
    jl brm_reb
    mov byte ptr [esi + 8], 1
brm_reb:
    cmp byte ptr [esi + 0xc], 0
    jne brm_out
    push {BR_KIND_RAZED}
    push ebp
    push edi
    call {br_find:#x}
    add esp, 0xc
    test ax, ax
    jl brm_out
    mov byte ptr [esi + 0xc], 1
brm_out:
    pop ebp
    pop edi
    pop esi
    pop ebx
    add esp, 0x14
    ret
''')
# br_canon(código) cdecl -> eax = código canónico del puente entero que incluye esa casilla (el menor de sus
# casillas), o -1 si no es un puente entero. Una misión guarda este código: se derriba desde cualquier punta.
br_canon = place('br_canon', f'''
    push {BR_KIND_INTACT}
    push dword ptr [esp + 8]
    call {br_comp:#x}
    add esp, 8
    test eax, eax
    jz brn_none
    push ebx
    mov ecx, eax
    or eax, -1
brn_loop:
    movzx edx, word ptr [ecx*4 + {br_xy - 2:#x}]
    shl edx, 7
    movzx ebx, word ptr [ecx*4 + {br_xy - 4:#x}]
    add edx, ebx
    cmp edx, eax
    jae brn_next
    mov eax, edx
brn_next:
    dec ecx
    jnz brn_loop
    add eax, {BR_CODE:#x}
    pop ebx
    ret
brn_none:
    or eax, -1
    ret
''')
# br_city(código) cdecl -> eax = la ciudad dueña del puente con la misma regla que 0x440f60 para un sitio: la viva
# más cercana (distancia de rey; en empate, la primera) de la misma región que la casilla (byte +2), si hay; si no,
# la viva más cercana de todas; -1 si no queda ninguna viva. Da el dueño del puente al elegir la misión y el nombre
# del lugar en su texto.
br_city = place('br_city', f'''
    push ebx
    push esi
    push edi
    push ebp
    sub esp, 0x14
    movsx eax, word ptr [esp + 0x28]
    sub eax, {BR_CODE:#x}
    mov esi, eax
    and esi, 0x7f
    shr eax, 7
    mov edi, eax
    mov cl, byte ptr [0x503e06]
    lea eax, [edi + edi*4]
    add eax, eax
    shl eax, cl
    lea edx, [esi + esi*4]
    movzx eax, byte ptr [eax + edx*2 + 0x503e5a]
    mov dword ptr [esp], eax
    mov dword ptr [esp + 4], 0x3e8
    mov dword ptr [esp + 8], -1
    mov dword ptr [esp + 0xc], 0x3e8
    mov dword ptr [esp + 0x10], -1
    xor ebp, ebp
brcy_loop:
    movsx eax, word ptr [0x537e2a]
    cmp ebp, eax
    jge brcy_out
    imul ebx, ebp, 0xde
    cmp byte ptr [ebx + 0x537ed0], 0
    je brcy_next
    movsx eax, word ptr [ebx + 0x537e2e]
    sub eax, edi
    cdq
    xor eax, edx
    sub eax, edx
    mov ecx, eax
    movsx eax, word ptr [ebx + 0x537e2c]
    sub eax, esi
    cdq
    xor eax, edx
    sub eax, edx
    cmp ecx, eax
    jge brcy_d
    mov ecx, eax
brcy_d:
    cmp dword ptr [esp + 4], ecx
    jle brcy_reg
    mov dword ptr [esp + 4], ecx
    mov dword ptr [esp + 8], ebp
brcy_reg:
    push ecx
    mov cl, byte ptr [0x503e06]
    movsx eax, word ptr [ebx + 0x537e2e]
    lea eax, [eax + eax*4]
    add eax, eax
    shl eax, cl
    movsx edx, word ptr [ebx + 0x537e2c]
    lea edx, [edx + edx*4]
    movzx eax, byte ptr [eax + edx*2 + 0x503e5a]
    pop ecx
    cmp eax, dword ptr [esp]
    jne brcy_next
    cmp dword ptr [esp + 0xc], ecx
    jle brcy_next
    mov dword ptr [esp + 0xc], ecx
    mov dword ptr [esp + 0x10], ebp
brcy_next:
    inc ebp
    jmp brcy_loop
brcy_out:
    mov eax, dword ptr [esp + 0x10]
    test eax, eax
    jge brcy_ret
    mov eax, dword ptr [esp + 8]
brcy_ret:
    add esp, 0x14
    pop ebp
    pop edi
    pop esi
    pop ebx
    ret
''')
# br_name(código, mayúscula) cdecl -> eax = el nombre propio del puente que incluye esa casilla, entero o derribado
# ("Belgor Bridge"). Lo arma el generador de nombres del juego (0x4374a0, el de las ciudades y ruinas del mapa al
# azar) con la gramática DATA\BRIDNAME.TXT y una semilla fija sacada de la casilla menor del puente: el mismo
# puente da el mismo nombre desde cualquier casilla, en cualquier momento y en todas las máquinas. El estado del
# azar ([0x500bf4], [0x500bf8]) se guarda y se repone, así la partida sigue igual que sin nombres. Sin el archivo,
# o si no es un puente: "the bridge" / "The bridge" (mayúscula != 0). Preserva todos los registros salvo eax y
# también br_xy. El último nombre queda en br_namebuf (br_namecode = su casilla), para no releer el archivo.
br_name = place('br_name', f'''
    push ecx
    push edx
    push ebx
    push esi
    push edi
    push ebp
    sub esp, 0x20
    mov esi, {br_xy:#x}
    mov edi, esp
    mov ecx, 8
    rep movsd dword ptr es:[edi], dword ptr [esi]
    movsx ebx, word ptr [esp + 0x3c]
    push {BR_KIND_INTACT}
    push ebx
    call {br_comp:#x}
    add esp, 8
    test eax, eax
    jnz brnm_have
    push {BR_KIND_RAZED}
    push ebx
    call {br_comp:#x}
    add esp, 8
    test eax, eax
    jz brnm_fallback
brnm_have:
    mov ecx, eax
    or ebx, -1
brnm_min:
    movzx edx, word ptr [ecx*4 + {br_xy - 2:#x}]
    shl edx, 7
    movzx eax, word ptr [ecx*4 + {br_xy - 4:#x}]
    add edx, eax
    cmp edx, ebx
    jae brnm_next
    mov ebx, edx
brnm_next:
    dec ecx
    jnz brnm_min
    cmp ebx, dword ptr [{br_namecode:#x}]
    je brnm_buf
    mov dword ptr [{br_namecode:#x}], -1
    imul eax, ebx, 0x2f1d
    xor eax, 0x5a5a
    and eax, 0xffff
    push dword ptr [0x500bf4]
    push dword ptr [0x500bf8]
    mov dword ptr [0x500bf4], eax
    mov dword ptr [0x500bf8], 0
    push {br_namebuf:#x}
    push {str_brname_file:#x}
    call 0x4374a0
    add esp, 8
    pop dword ptr [0x500bf8]
    pop dword ptr [0x500bf4]
    test eax, eax
    jz brnm_fallback
    cmp byte ptr [{br_namebuf:#x}], 0
    je brnm_fallback
    mov dword ptr [{br_namecode:#x}], ebx
brnm_buf:
    mov eax, {br_namebuf:#x}
    jmp brnm_out
brnm_fallback:
    mov eax, {str_the_bridge:#x}
    cmp dword ptr [esp + 0x40], 0
    je brnm_out
    mov eax, {str_The_bridge:#x}
brnm_out:
    mov esi, esp
    mov edi, {br_xy:#x}
    mov ecx, 8
    rep movsd dword ptr es:[edi], dword ptr [esi]
    add esp, 0x20
    pop ebp
    pop edi
    pop esi
    pop ebx
    pop edx
    pop ecx
    ret
''')
# Diálogo de arrasar (0x4951b0, modo 1 = sitio): el nombre en "Are you sure you want to raze %s?" (0x495530,
# eax = índice) y el botón (0x495288): para un puente, si hay ejércitos ajenos encima se avisa; si no, va por el
# mismo 0x4955d0 que un sitio, con el código canónico: avisa la destrucción a la misión del héroe (0x461a60, evento 6)
# y manda la orden 0x4b9550(código, jugador).
br_razetxt = place('br_razetxt', f'''
    cmp eax, {BR_CODE:#x}
    jl brt2_site
    push 0
    push eax
    call {br_name:#x}
    add esp, 8
    push eax
    jmp 0x495541
brt2_site:
    lea eax, [eax + eax*4]
    add eax, eax
    lea ecx, [eax + eax*2]
    lea eax, [ecx + ecx*4]
    add eax, 0x55acba
    push eax
    jmp 0x495541
''')
# Imagen del diálogo de arrasar (0x4954d0 dibuja la 153, "raze", en el marco de 142x168 con 0x4bbf20): para un
# puente, el retrato del ariete orco (imagen RAM_IMG, que WAR3AV.RES agrega sobre ARMY\orcs_ram.pcx).
RAM_FILE, RAM_IMG = 165, 206
br_razepic = place('br_razepic', f'''
    movsx edx, word ptr [0x572778]
    cmp edx, {BR_CODE:#x}
    jl brp_site
    push {RAM_IMG}
    jmp 0x4954e6
brp_site:
    push 0x99
    jmp 0x4954e6
''')
br_razebtn = place('br_razebtn', f'''
    movsx eax, word ptr [0x572778]
    cmp eax, {BR_CODE:#x}
    jge brb2_bridge
    push eax
    call 0x4955d0
    jmp 0x495294
brb2_bridge:
    push {BR_KIND_INTACT}
    push eax
    call {br_comp:#x}
    add esp, 8
    test eax, eax
    jz brb2_done
    movsx ecx, word ptr [0x537ce8]
    push ecx
    push eax
    call {br_armies:#x}
    add esp, 8
    test eax, eax
    jnz brb2_enemy
    movsx eax, word ptr [0x572778]
    push eax
    call {br_canon:#x}
    mov dword ptr [esp], eax
    call 0x4955d0
    add esp, 4
    jmp brb2_done
brb2_enemy:
    push 0x19
    push {str_br_enemy1:#x}
    call 0x4c2790
    add esp, 8
    push 0x1e
    push {str_br_enemy2:#x}
    call 0x4c2790
    add esp, 8
brb2_done:
    push eax
    jmp 0x495294
''')
# Aplicación de arrasar (0x4d5e30(código, jugador), en todas las máquinas de la partida). Para un puente: vuelve a
# comprobar que está entero y sin ejércitos ajenos (si no, no hace nada), lo derriba, ahoga a los propios de encima,
# refresca la vista y da el aviso "Razed!" / "<nombre> is in ruins!" del original al jugador humano que arrasó.
# Sin historia (0x4a0400 / 0x49f900 son de sitios). 0x4d5f3a invalida el grafo de pasos (0x4a4f20) y sale.
br_razeapply = place('br_razeapply', f'''
    cmp word ptr [esp + 4], {BR_CODE:#x}
    jge bra2_bridge
    sub esp, 0x50
    push esi
    push edi
    jmp 0x4d5e35
bra2_bridge:
    sub esp, 0x50
    push esi
    push edi
    call 0x4a2170
    push ebx
    push ebp
    movsx ebx, word ptr [esp + 0x64]
    movsx ebp, word ptr [esp + 0x68]
    push {BR_KIND_INTACT}
    push ebx
    call {br_comp:#x}
    add esp, 8
    test eax, eax
    jz bra2_quit
    mov esi, eax
    push ebp
    push esi
    call {br_armies:#x}
    add esp, 8
    test eax, eax
    jnz bra2_quit
    xor edi, edi
bra2_tile:
    movzx eax, word ptr [edi*4 + {br_xy:#x}]
    movzx edx, word ptr [edi*4 + {br_xy + 2:#x}]
    call {br_tile:#x}
    and byte ptr [eax + 3], 0xf8
    or byte ptr [eax + 9], 0x80
    inc edi
    cmp edi, esi
    jb bra2_tile
    push ebp
    push esi
    call {br_drown:#x}
    add esp, 8
    mov ecx, 0x569588
    call 0x456ee0
    pop ebp
    pop ebx
    mov di, word ptr [esp + 0x60]
    cmp word ptr [0x537ce8], di
    jne 0x4d5f3a
    movsx eax, di
    mov ecx, eax
    shl eax, 6
    sub eax, ecx
    cmp word ptr [eax*8 + 0x536c12], -1
    jne 0x4d5f3a
    movsx eax, word ptr [esp + 0x5c]
    push 1
    push eax
    call {br_name:#x}
    add esp, 8
    mov esi, eax
    jmp 0x4d5eda
bra2_quit:
    pop ebp
    pop ebx
    jmp 0x4d5f3a
''')
# ---------------------------------------------------------------- Misión de héroe "derribar un puente"
# Es el tipo 10 ("Destroying an Enemy Site") con objetivo = código canónico del puente (br_canon) en vez del índice
# de un sitio. La misión activa vive en 0x55edc4 + jugador*16 (+2 héroe, +4 tipo, +6 objetivo), dentro del bloque
# que guarda el SAV. Recorrido:
# - Generador 0x45ec40, dificultad Average (la única con el tipo 10): después de juntar los sitios candidatos
#   ([esp+0x34], di de ellos), qb_gen suma los puentes enteros con la misma distancia de rey al héroe
#   (3Q+14 .. 4Q+34, Q = [0x56950a]) y dueño enemigo o nadie: la ciudad dueña sale de br_city (la misma regla
#   que 0x440f60 para un sitio) y se filtra con el mismo 0x461080; si no queda ciudad viva, es de nadie. Vale
#   para todos los jugadores: la IA también los toma (ai_brq).
# - Cumplida: el botón de arrasar puente pasa por 0x4955d0 (br_razebtn), que llama a 0x461a60(6, ejército
#   seleccionado, 0, 0, código): el original compara el objetivo con el código y premia igual que un sitio.
# - Fracasada: el chequeo de cada turno (0x461a60 evento 0) mira si el sitio está arrasado (0x461c80); para un
#   puente, si ya no está entero (qb_fail).
# - Textos: el nombre del tipo (0x461130 -> 0x461336) y el objetivo (0x461400 -> 0x461876).
# - La IA lee el lugar del objetivo en 0x435fd0 (0x436178) y 0x436390 (0x436442): para un puente, su casilla, para
#   no leer la tabla de sitios fuera de rango.
# - La IA la cumple: su meta 6 (misión, 0x40d6d0) manda el tipo 10 a 0x40d963, que escribe en el registro de la IA el
#   nombre del sitio (ai_brname: el del puente, br_name) y llama a 0x40d450(objetivo, 10), el "ir al sitio y arrasarlo".
#   Para un puente, ai_brq: elige la cabecera más cercana al héroe (distancia de rey; una casilla vecina de una del
#   puente que no sea puente, ni agua, ni montaña sin camino), va hacia ella como 0x40d450 va al sitio (0x4973f0,
#   0x40d2b0, 0x40e400) y, parado ahí, lo derriba con el mismo 0x4955d0 del botón (evento 6 de la misión + orden
#   0x4b9550). Con ejércitos ajenos sobre el puente no lo derriba: ataca como 0x40e400 ataca al que ocupa un sitio;
#   con ejércitos propios encima espera, para no ahogarlos.
str_qb_name = place_data('str_qb_name', cstr_('Destroying a Bridge'))
str_qb_obj = place_data('str_qb_obj', cstr_('%s must destroy %s, near %s.'))
str_qb_obj0 = place_data('str_qb_obj0', cstr_('%s must destroy %s.'))
QB_MAXCAND = 0x100                                       # la lista [esp+0x34] del generador llega a [esp+0x233]
qb_gen = place('qb_gen', f'''
    push ebx
    push esi
    push ebp
    xor esi, esi
qbg_y:
    movsx eax, word ptr [0x503e02]
    cmp esi, eax
    jge qbg_end
    xor ebx, ebx
qbg_x:
    movsx eax, word ptr [0x503e00]
    cmp ebx, eax
    jge qbg_nexty
    mov eax, ebx
    mov edx, esi
    call {br_tile:#x}
    test eax, eax
    jz qbg_next
    call {br_kind:#x}
    cmp eax, {BR_KIND_INTACT}
    jne qbg_next
    mov ebp, esi
    shl ebp, 7
    lea ebp, [ebp + ebx + {BR_CODE:#x}]
    push ebp
    call {br_canon:#x}
    add esp, 4
    cmp eax, ebp
    jne qbg_next
    movsx eax, word ptr [esp + 0x26]
    sub eax, ebx
    jge qbg_p1
    neg eax
qbg_p1:
    mov ecx, eax
    movsx eax, word ptr [esp + 0x24]
    sub eax, esi
    jge qbg_p2
    neg eax
qbg_p2:
    cmp ecx, eax
    jge qbg_d
    mov ecx, eax
qbg_d:
    movsx edx, word ptr [0x56950a]
    lea eax, [edx + edx*2 + 0xe]
    cmp eax, ecx
    jg qbg_next
    lea eax, [edx*4 + 0x22]
    cmp eax, ecx
    jl qbg_next
    push ebp
    call {br_city:#x}
    add esp, 4
    test eax, eax
    jl qbg_add
    imul eax, eax, 0xde
    movzx eax, byte ptr [eax + 0x537ed1]
    push eax
    call 0x461080
    add esp, 4
    test al, al
    jz qbg_next
qbg_add:
    movsx eax, di
    cmp eax, {QB_MAXCAND}
    jge qbg_next
    inc edi
    mov word ptr [esp + eax*2 + 0x40], bp
qbg_next:
    inc ebx
    jmp qbg_x
qbg_nexty:
    inc esi
    jmp qbg_y
qbg_end:
    pop ebp
    pop esi
    pop ebx
    test di, di
    jle 0x460fa0
    jmp 0x460e04
''')
qb_name = place('qb_name', f'''
    mov eax, dword ptr [esp + 0x10]
    cmp word ptr [eax + 6], {BR_CODE:#x}
    jge qbn_bridge
    push ecx
    push 0x42
    mov ecx, 0x589880
    call 0x4def30
    jmp 0x461343
qbn_bridge:
    mov eax, {str_qb_name:#x}
    jmp 0x461343
''')
qb_text = place('qb_text', f'''
    movsx eax, word ptr [edi + 6]
    cmp eax, {BR_CODE:#x}
    jge qbt_bridge
    lea eax, [eax + eax*4]
    add eax, eax
    lea ecx, [eax + eax*2]
    lea eax, [ecx + ecx*4]
    jmp 0x461885
qbt_bridge:
    push esi
    push 0
    push eax
    call {br_name:#x}
    add esp, 8
    mov esi, eax
    movsx eax, word ptr [edi + 6]
    push eax
    call {br_city:#x}
    add esp, 4
    mov ecx, {str_qb_obj0:#x}
    test eax, eax
    jl qbt_go
    imul eax, eax, 0xde
    add eax, 0x537e30
    mov ecx, {str_qb_obj:#x}
qbt_go:
    push eax
    push esi
    movsx eax, word ptr [edi + 2]
    imul eax, eax, 0x1c
    movzx eax, word ptr [eax + 0x54fe62]
    and eax, 0x3f00
    shr eax, 8
    imul eax, eax, 0xb8
    add eax, 0x556bb4
    push eax
    push ecx
    push ebx
    call dword ptr [0x5a9bec]
    add esp, 0x14
    pop esi
    jmp 0x4618d3
''')
qb_fail = place('qb_fail', f'''
    movsx eax, word ptr [esi + 6]
    cmp eax, {BR_CODE:#x}
    jge qbf_bridge
    lea eax, [eax + eax*4]
    add eax, eax
    lea edx, [eax + eax*2]
    cmp byte ptr [edx + edx*4 + 0x55ad4b], 0
    je 0x461ca3
    jmp 0x461c96
qbf_bridge:
    push ecx
    push {BR_KIND_INTACT}
    push eax
    call {br_comp:#x}
    add esp, 8
    pop ecx
    test eax, eax
    jnz 0x461ca3
    jmp 0x461c96
''')
qb_ailoc1 = place('qb_ailoc1', f'''
    movsx eax, di
    mov bp, 1
    cmp eax, {BR_CODE:#x}
    jge qba1_bridge
    lea eax, [eax + eax*4]
    add eax, eax
    lea ecx, [eax + eax*2]
    mov dx, word ptr [ecx + ecx*4 + 0x55acb6]
    lea eax, [ecx + ecx*4]
    mov ax, word ptr [eax + 0x55acb8]
    jmp 0x436199
qba1_bridge:
    sub eax, {BR_CODE:#x}
    mov edx, eax
    and edx, 0x7f
    shr eax, 7
    jmp 0x436199
''')
qb_ailoc2 = place('qb_ailoc2', f'''
    mov word ptr [ebx], cx
    movsx ecx, cx
    cmp ecx, {BR_CODE:#x}
    jge qba2_bridge
    lea ecx, [ecx + ecx*4]
    add ecx, ecx
    lea ebx, [ecx + ecx*2]
    mov di, word ptr [ebx + ebx*4 + 0x55acb6]
    lea ecx, [ebx + ebx*4]
    mov word ptr [esi], di
    mov cx, word ptr [ecx + 0x55acb8]
    jmp qba2_out
qba2_bridge:
    sub ecx, {BR_CODE:#x}
    mov edi, ecx
    and edi, 0x7f
    mov word ptr [esi], di
    shr ecx, 7
qba2_out:
    pop edi
    pop esi
    mov word ptr [edx], cx
    pop ebx
    ret
''')
ai_brname = place('ai_brname', f'''
    movsx eax, word ptr [esp + 0x12]
    cmp eax, {BR_CODE:#x}
    jge aibn_bridge
    lea eax, [eax + eax*4]
    add eax, eax
    lea ecx, [eax + eax*2]
    lea eax, [ecx + ecx*4]
    add eax, 0x55acba
    jmp 0x40d978
aibn_bridge:
    push 0
    push eax
    call {br_name:#x}
    add esp, 8
    jmp 0x40d978
''')
# ai_brq(código, modo): 0x40d450 para un puente. Devuelve ax = 1 hecho, 0 todavía no (como el original).
# Locales: [esp] x, [esp+4] y de la cabecera, [esp+8] su distancia, [esp+0xc] casillas*8; edi = registro del grupo.
# El líder de la pila se guarda al entrar (ai_brlead), como el original en [esp+0x12]: al terminar de mover, 0x4c4a10
# manda la orden 0x146 (0x4b9020), que se aplica en el acto (0x4df400) y vacía la pila (0x485c70 pone 0x56ea90/92 en 0);
# por eso el derribo no pasa por 0x4955d0, que lee el líder recién ahí.
ai_brlead = place_data('ai_brlead', bytes(4))
ai_brq = place('ai_brq', f'''
    cmp word ptr [esp + 4], {BR_CODE:#x}
    jge aib_bridge
    sub esp, 4
    mov eax, dword ptr [0x5020d4]
    jmp 0x40d458
aib_bridge:
    movsx eax, word ptr [0x537ce8]
    imul eax, eax, 0x4f0
    movsx eax, word ptr [eax + 0x56ea92]
    mov dword ptr [{ai_brlead:#x}], eax
    push ebx
    push esi
    push edi
    push ebp
    sub esp, 0x10
    mov eax, dword ptr [0x5020d4]
    movsx edi, word ptr [eax + 0xc]
    imul edi, edi, 0x1c
    push {BR_KIND_INTACT}
    push dword ptr [esp + 0x28]
    call {br_comp:#x}
    add esp, 8
    test eax, eax
    jz aib_ret0
    shl eax, 3
    mov dword ptr [esp + 0xc], eax
    mov dword ptr [esp + 8], 0x3e8
    movsx ebx, word ptr [edi + 0x54fe52]
    movsx ebp, word ptr [edi + 0x54fe54]
    xor esi, esi
aib_cand:
    mov ecx, esi
    shr ecx, 3
    mov edx, esi
    and edx, 7
    movsx eax, word ptr [edx*2 + {br_d8:#x}]
    push eax
    movsx eax, word ptr [edx*2 + {br_d8 + 16:#x}]
    movsx edx, word ptr [ecx*4 + {br_xy + 2:#x}]
    add edx, eax
    pop eax
    movsx ecx, word ptr [ecx*4 + {br_xy:#x}]
    add eax, ecx
    push eax
    push edx
    call {br_tile:#x}
    test eax, eax
    jz aib_skip
    mov ecx, eax
    call {br_kind:#x}
    test eax, eax
    jnz aib_skip
    movzx eax, word ptr [ecx]
    and eax, 0x1f
    imul eax, eax, 0x58
    movsx eax, word ptr [eax + 0x535f0c]
    cmp eax, 1
    je aib_skip
    cmp eax, 4
    jne aib_dist
    cmp byte ptr [0x4fe688], 0
    jne aib_dist
    imul eax, dword ptr [esp + 4], 0xa0
    add eax, dword ptr [esp]
    test byte ptr [eax + 0x57d158], 0x30
    jz aib_skip
aib_dist:
    mov eax, dword ptr [esp + 4]
    sub eax, ebx
    cdq
    xor eax, edx
    sub eax, edx
    mov ecx, eax
    mov eax, dword ptr [esp]
    sub eax, ebp
    cdq
    xor eax, edx
    sub eax, edx
    cmp ecx, eax
    jge aib_d
    mov ecx, eax
aib_d:
    cmp ecx, dword ptr [esp + 0x10]
    jge aib_skip
    mov dword ptr [esp + 0x10], ecx
    mov eax, dword ptr [esp + 4]
    mov dword ptr [esp + 8], eax
    mov eax, dword ptr [esp]
    mov dword ptr [esp + 0xc], eax
aib_skip:
    add esp, 8
    inc esi
    cmp esi, dword ptr [esp + 0xc]
    jb aib_cand
    mov ecx, dword ptr [esp + 8]
    cmp ecx, 0x3e8
    je aib_ret0
    test ecx, ecx
    jz aib_here
    push dword ptr [esp + 4]
    push dword ptr [esp + 4]
    push 0
    push 7
    call 0x4973f0
    add esp, 0x10
    mov eax, dword ptr [0x5020d4]
    mov word ptr [eax + 6], 8
    mov cx, word ptr [esp + 0x24]
    mov word ptr [eax + 8], cx
    push dword ptr [esp + 4]
    push dword ptr [esp + 4]
    call 0x40d2b0
    add esp, 8
    test ax, ax
    jz aib_ret0
    test byte ptr [edi + 0x54fe61], 0x7f
    jz aib_ret0
    push dword ptr [esp + 4]
    push dword ptr [esp + 4]
    movsx eax, word ptr [edi + 0x54fe54]
    push eax
    movsx eax, word ptr [edi + 0x54fe52]
    push eax
    call 0x40e400
    add esp, 0x10
    test ax, ax
    jz aib_ret0
    mov ax, word ptr [edi + 0x54fe52]
    cmp ax, word ptr [esp]
    jne aib_ret0
    mov ax, word ptr [edi + 0x54fe54]
    cmp ax, word ptr [esp + 4]
    jne aib_ret0
aib_here:
    cmp word ptr [esp + 0x28], 10
    jne aib_done
    push {BR_KIND_INTACT}
    push dword ptr [esp + 0x28]
    call {br_comp:#x}
    add esp, 8
    test eax, eax
    jz aib_ret0
    mov esi, eax
    movsx ecx, word ptr [0x537ce8]
    push ecx
    push eax
    call {br_armies:#x}
    add esp, 8
    test eax, eax
    jnz aib_held
    test edx, edx
    jnz aib_ret0
    push 1
    movsx eax, word ptr [esp + 0x28]
    push eax
    push 0
    push 0
    push dword ptr [{ai_brlead:#x}]
    push 6
    call 0x461a60
    add esp, 0x18
    movsx eax, word ptr [0x537ce8]
    push eax
    movsx eax, word ptr [esp + 0x28]
    push eax
    call 0x4b9550
    add esp, 8
aib_done:
    push 0x7d0
    call 0x4275b0
    add esp, 4
    mov eax, dword ptr [0x5020d4]
    xor ecx, ecx
    mov word ptr [eax + 6], cx
    mov word ptr [eax + 8], cx
    call 0x40d230
    mov ax, 1
    jmp aib_out
aib_held:
    movsx ebx, word ptr [edi + 0x54fe52]
    movsx ebp, word ptr [edi + 0x54fe54]
aib_hl:
    dec esi
    js aib_ret0
    movsx eax, word ptr [esi*4 + {br_xy:#x}]
    movsx edx, word ptr [esi*4 + {br_xy + 2:#x}]
    mov ecx, eax
    sub ecx, ebx
    inc ecx
    cmp ecx, 2
    ja aib_hl
    mov ecx, edx
    sub ecx, ebp
    inc ecx
    cmp ecx, 2
    ja aib_hl
    push edx
    push eax
    push ebp
    push ebx
    call 0x40e400
    add esp, 0x10
    test ax, ax
    jz aib_hl
aib_ret0:
    xor eax, eax
aib_out:
    add esp, 0x10
    pop ebp
    pop edi
    pop esi
    pop ebx
    ret
''')
# qb_ailoc3: el caso "Raze Site" del evaluador de misiones de la IA (0x4358e0, tabla 0x435f94, caso 0x435d53) leía
# x/y de la tabla de sitios con el código del puente; deja dx = x, ax = y de la casilla del código.
qb_ailoc3 = place('qb_ailoc3', f'''
    movsx eax, word ptr [esp + edi + 0x2e]
    mov word ptr [esp + 0x20], 0xffff
    cmp eax, {BR_CODE:#x}
    jge qba3_bridge
    lea eax, [eax + eax*4]
    add eax, eax
    lea ecx, [eax + eax*2]
    mov dx, word ptr [ecx + ecx*4 + 0x55acb6]
    lea eax, [ecx + ecx*4]
    mov ax, word ptr [eax + 0x55acb8]
    jmp 0x435d79
qba3_bridge:
    sub eax, {BR_CODE:#x}
    mov edx, eax
    and edx, 0x7f
    shr eax, 7
    jmp 0x435d79
''')
# br_kd: eax = distancia de rey entre (eax, edx) y (esi, ebp). Preserva todo salvo eax y edx.
br_kd = place('br_kd', '''
    push ecx
    mov ecx, edx
    sub eax, esi
    cdq
    xor eax, edx
    sub eax, edx
    xchg eax, ecx
    sub eax, ebp
    cdq
    xor eax, edx
    sub eax, edx
    cmp eax, ecx
    jge brkd_out
    mov eax, ecx
brkd_out:
    pop ecx
    ret
''')
# ai_brraze: la IA derriba un puente por criterio propio, con la misma cuenta con que arrasa una ciudad (0x41f4b0).
# Corre al final de cada movimiento de una pila de la IA (0x4c4a10, en 0x4c4d3a: antes de la orden 0x146 que vacía la
# pila), si el líder quedó junto a un puente entero (br_find). Descarta el puente si:
# - la ciudad dueña (br_city) es propia o de un jugador no hostil (0x49c1c0 = 0); las neutrales no lo descartan;
# - hay cualquier ejército encima (no se ahoga a nadie);
# - el destino del movimiento (argumentos de 0x4c4a10) está a 1 casilla o menos del puente (va hacia él: la misión
#   de ai_brq o cruzarlo) o el puente le queda más cerca al destino que la pila (está por delante en el camino).
# Cuenta de 0x41f4b0, con el puente en lugar de la ciudad:
#   c = temperamento [0x561ef9 + p*0x49a]; flag = grupo de la IA del líder ([+0x1a] & 0x3c00) >> 10.
#   c = 0 y flag = 0: no. s = -2 si c = 0. +1 si flag y la ciudad dueña no es neutral. +1 siempre (un puente no
#   produce: valor < 150). Las 12 ciudades vivas más cercanas (0x4974a0 desde la casilla del código), a distancia
#   1..30, pesan 2 si están a menos de 15 y 1 si no: las propias restan, las hostiles (0x49c1c0) suman. +1 si tiene
#   más de 5 ciudades, +1 más si más de 15. Azar r = 0x4deb20(1, 20): r >= 19, no. Derriba si c + s >= 5.
#   El original sube el temperamento con r = 1; acá no (es la decisión de arrasar ciudades la que lo hace).
# El derribo es el de la misión: 0x4955d0(código) (evento 6 con el líder y la orden de red 0x18d) y la pausa 0x4275b0.
# La cuenta (salvo el azar) es ai_brs, que comparte con la reconstrucción (ai_brrebev): no se repone lo que se derribaría.
# ai_brs(código, jugador, flag) cdecl -> eax = c + s, o 0x80000000 si la ciudad dueña lo descarta (nunca lo derriba).
# Locales: [esp + 4*i] distancia a la ciudad i (hasta 80), después BS_*.
BS_S, BS_NC, BS_RND, BS_P, BS_BX, BS_BY, BS_C, BS_FLAG = (0x140 + 4 * i for i in range(8))
BS_LOC = 0x140 + 4 * 8
BS_ARG = BS_LOC + 0x14
ai_brs = place('ai_brs', f'''
    push ebx
    push esi
    push edi
    push ebp
    sub esp, {BS_LOC:#x}
    movsx ebx, word ptr [esp + {BS_ARG + 4:#x}]
    mov dword ptr [esp + {BS_P:#x}], ebx
    mov eax, dword ptr [esp + {BS_ARG + 8:#x}]
    mov dword ptr [esp + {BS_FLAG:#x}], eax
    imul ecx, ebx, 0x49a
    movzx ecx, byte ptr [ecx + 0x561ef9]
    mov dword ptr [esp + {BS_C:#x}], ecx
    movsx eax, word ptr [esp + {BS_ARG:#x}]
    sub eax, {BR_CODE:#x}
    mov edx, eax
    and edx, 0x7f
    mov dword ptr [esp + {BS_BX:#x}], edx
    shr eax, 7
    mov dword ptr [esp + {BS_BY:#x}], eax
    xor eax, eax
    cmp dword ptr [esp + {BS_C:#x}], 0
    jne bs_s0
    mov eax, -2
bs_s0:
    inc eax
    mov dword ptr [esp + {BS_S:#x}], eax
    push dword ptr [esp + {BS_ARG:#x}]
    call {br_city:#x}
    add esp, 4
    test eax, eax
    jl bs_near
    imul eax, eax, 0xde
    movzx eax, byte ptr [eax + 0x537ed1]
    cmp eax, 8
    je bs_near
    push eax
    call 0x49c1c0
    add esp, 4
    test ax, ax
    jz bs_never
    cmp dword ptr [esp + {BS_FLAG:#x}], 0
    je bs_near
    inc dword ptr [esp + {BS_S:#x}]
bs_near:
    xor ebp, ebp
bs_dist:
    movsx eax, word ptr [0x537e2a]
    cmp ebp, eax
    jge bs_distend
    cmp ebp, 80
    jge bs_distend
    mov dword ptr [esp + ebp*4], 0x7fffffff
    imul ebx, ebp, 0xde
    cmp byte ptr [ebx + 0x537ed0], 0
    je bs_distnext
    movsx eax, word ptr [ebx + 0x537e2e]
    push eax
    movsx eax, word ptr [ebx + 0x537e2c]
    push eax
    push dword ptr [esp + {BS_BY + 8:#x}]
    push dword ptr [esp + {BS_BX + 12:#x}]
    call 0x4974a0
    add esp, 0x10
    movsx eax, ax
    mov dword ptr [esp + ebp*4], eax
bs_distnext:
    inc ebp
    jmp bs_dist
bs_distend:
    mov dword ptr [esp + {BS_NC:#x}], ebp
    mov dword ptr [esp + {BS_RND:#x}], 12
bs_sel:
    or esi, -1
    mov edi, 0x7fffffff
    xor ebp, ebp
bs_sell:
    cmp ebp, dword ptr [esp + {BS_NC:#x}]
    jge bs_selend
    mov eax, dword ptr [esp + ebp*4]
    cmp eax, edi
    jge bs_selnext
    mov edi, eax
    mov esi, ebp
bs_selnext:
    inc ebp
    jmp bs_sell
bs_selend:
    test esi, esi
    jl bs_count
    mov dword ptr [esp + esi*4], 0x7fffffff
    test edi, edi
    jz bs_next
    cmp edi, 30
    jg bs_next
    mov ecx, 1
    cmp edi, 15
    jge bs_w
    mov ecx, 2
bs_w:
    imul ebx, esi, 0xde
    movzx eax, byte ptr [ebx + 0x537ed1]
    cmp eax, dword ptr [esp + {BS_P:#x}]
    jne bs_foreign
    sub dword ptr [esp + {BS_S:#x}], ecx
    jmp bs_next
bs_foreign:
    cmp eax, 8
    je bs_next
    push ecx
    push eax
    call 0x49c1c0
    add esp, 4
    pop ecx
    test ax, ax
    jz bs_next
    add dword ptr [esp + {BS_S:#x}], ecx
bs_next:
    dec dword ptr [esp + {BS_RND:#x}]
    jnz bs_sel
bs_count:
    xor ecx, ecx
    xor ebp, ebp
bs_cl:
    movsx eax, word ptr [0x537e2a]
    cmp ebp, eax
    jge bs_cend
    imul ebx, ebp, 0xde
    cmp byte ptr [ebx + 0x537ed0], 0
    je bs_cnext
    movzx eax, byte ptr [ebx + 0x537ed1]
    cmp eax, dword ptr [esp + {BS_P:#x}]
    jne bs_cnext
    inc ecx
bs_cnext:
    inc ebp
    jmp bs_cl
bs_cend:
    cmp ecx, 5
    jle bs_sum
    inc dword ptr [esp + {BS_S:#x}]
    cmp ecx, 15
    jle bs_sum
    inc dword ptr [esp + {BS_S:#x}]
bs_sum:
    mov eax, dword ptr [esp + {BS_C:#x}]
    add eax, dword ptr [esp + {BS_S:#x}]
    jmp bs_out
bs_never:
    mov eax, 0x80000000
bs_out:
    add esp, {BS_LOC:#x}
    pop ebp
    pop edi
    pop esi
    pop ebx
    ret
''')
# Locales de ai_brraze: ABZ_*.
ABZ_CODE, ABZ_S, ABZ_P, ABZ_FLAG, ABZ_C, ABZ_N, ABZ_SD = (4 * i for i in range(7))
ABZ_LOC = 4 * 7
ABZ_X, ABZ_Y = ABZ_LOC + 0x20 + 4 + 0x38, ABZ_LOC + 0x20 + 4 + 0x3c
ai_brraze = place('ai_brraze', f'''
    pushad
    sub esp, {ABZ_LOC:#x}
    movsx ebx, word ptr [0x4fb0ec]
    cmp bx, word ptr [0x537ce8]
    jne abz_out
    mov dword ptr [esp + {ABZ_P:#x}], ebx
    imul eax, ebx, 0x1f8
    cmp word ptr [eax + 0x536c12], -1
    je abz_out
    test byte ptr [0x53c393], 6
    jz abz_out
    imul esi, ebx, 0x4f0
    cmp word ptr [esi + 0x56ea90], 0
    je abz_out
    movsx edi, word ptr [esi + 0x56ea92]
    imul edi, edi, 0x1c
    test byte ptr [edi + 0x54fe63], 0x40
    jz abz_out
    movzx eax, word ptr [edi + 0x54fe6c]
    and eax, 0x3c00
    shr eax, 10
    mov dword ptr [esp + {ABZ_FLAG:#x}], eax
    imul ecx, ebx, 0x49a
    movzx ecx, byte ptr [ecx + 0x561ef9]
    mov dword ptr [esp + {ABZ_C:#x}], ecx
    or eax, ecx
    jz abz_out
    push {BR_KIND_INTACT}
    movsx eax, word ptr [edi + 0x54fe54]
    push eax
    movsx eax, word ptr [edi + 0x54fe52]
    push eax
    call {br_find:#x}
    add esp, 0xc
    test eax, eax
    jl abz_out
    push eax
    call {br_canon:#x}
    add esp, 4
    test eax, eax
    jl abz_out
    mov dword ptr [esp + {ABZ_CODE:#x}], eax
    push {BR_KIND_INTACT}
    push dword ptr [esp + {ABZ_CODE + 4:#x}]
    call {br_comp:#x}
    add esp, 8
    test eax, eax
    jz abz_out
    mov dword ptr [esp + {ABZ_N:#x}], eax
    push ebx
    push eax
    call {br_armies:#x}
    add esp, 8
    test edx, edx
    jnz abz_out
    movsx esi, word ptr [esp + {ABZ_X:#x}]
    movsx ebp, word ptr [esp + {ABZ_Y:#x}]
    movsx eax, word ptr [edi + 0x54fe52]
    movsx edx, word ptr [edi + 0x54fe54]
    call {br_kd:#x}
    mov dword ptr [esp + {ABZ_SD:#x}], eax
    mov ecx, dword ptr [esp + {ABZ_N:#x}]
abz_tile:
    dec ecx
    js abz_owner
    movsx eax, word ptr [ecx*4 + {br_xy:#x}]
    movsx edx, word ptr [ecx*4 + {br_xy + 2:#x}]
    call {br_kd:#x}
    cmp eax, 1
    jle abz_out
    cmp eax, dword ptr [esp + {ABZ_SD:#x}]
    jl abz_out
    jmp abz_tile
abz_owner:
    push dword ptr [esp + {ABZ_FLAG:#x}]
    push dword ptr [esp + {ABZ_P + 4:#x}]
    push dword ptr [esp + {ABZ_CODE + 8:#x}]
    call {ai_brs:#x}
    add esp, 0xc
    cmp eax, 0x80000000
    je abz_out
    mov dword ptr [esp + {ABZ_S:#x}], eax
    push 0
    push 20
    push 1
    call 0x4deb20
    add esp, 0xc
    cmp ax, 19
    jge abz_out
    mov eax, dword ptr [esp + {ABZ_S:#x}]
    cmp eax, 5
    jl abz_out
    push dword ptr [esp + {ABZ_CODE:#x}]
    call 0x4955d0
    add esp, 4
    push 0x7d0
    call 0x4275b0
    add esp, 4
abz_out:
    add esp, {ABZ_LOC:#x}
    popad
    movsx eax, word ptr [0x4fb0ec]
    ret
''')
# ---- La IA usa los barcos con "Landing" y "Carrier" (1.0.25.0).
# El juego ya planea con ellos: su mapa de distancias (0x497750 -> 0x4a53b0) y sus caminos (0x485e30) usan el buscador
# con los enlaces de Landing (landchk, también desde tierra) y de Cabotage (cabfilt), porque los dos miran el jugador
# del camino [0x58715c]. Faltan dos cosas que el juego no sabe hacer:
# - Partir el grupo cuando no entra en el barco. Con "Landing" el stack embarcado tiene tope LANDCAP (landcap) y el
#   paso que embarca de más devuelve "stack lleno": el movimiento termina con el código 5 (0x49d05d -> 0x49c960(p, 5))
#   y la IA original no hace nada con él (0x4c4d84, caso 5), así que el grupo quedaría en el muelle todos los turnos.
# - Formar convoyes: la orden explícita de mover un stack embarcado a la casilla de otro propio cuando la suma no entra
#   (crlink), que la IA nunca da.
# ai_move reemplaza el call 0x49c4b0 de 0x4c4a10 (en 0x4c4bce, ya dada la orden de destino 0x4b91e0(p, x, y)), solo
# para bandos de la computadora (0x536c12 != -1):
# 1. ai_conv: si el grupo navega con "Carrier", no está en un convoy y en una casilla vecina de agua pura hay ejércitos
#    propios embarcados que van a menos de 2 casillas del mismo destino y la suma no entra en un stack, ordena ir a esa
#    casilla (crlink los enlaza, o no pasa nada si el convoy pasaría de 3 casillas) y vuelve a dar la orden de destino.
#    Con "Landing" solo si hay un puerto (0xc0 en 0x582158) a 2 casillas o menos del destino: un convoy atraca solo en
#    puertos.
# 2. Mueve (0x49c4b0). Si termina en 5 y landcap dejó lchit = 1 (el grupo se embarcaba desde tierra), se queda con el
#    líder y los primeros del grupo hasta el tope (LANDCAP + "Carrier", y uno menos en cada reintento, por si el barco
#    ya tenía gente), suelta al resto (ai_free; si son 2 o más, forman una pila nueva de la IA con 0x40f1a0, como hace
#    0x40d380 al reagrupar), rearma el grupo (0x497240), copia la lista nueva en la del marco de 0x4c4a10 (la usa el
#    caso 2, 0x4c4da0), vuelve a dar la orden de destino y reintenta.
# Devuelve el código del último movimiento, como 0x49c4b0.
# ai_free: eax = ejército, ebx = jugador. Lo saca de las pilas de la IA del jugador (0x561f00 + p*0x49a, 10 de 0x40,
# activas con +0 & 1, lista de 8 en +0xc; nunca la entrada 0, el líder) y lo deja libre como los que junta 0x40e020:
# sin bits de pila (& 0xc3ff en +0x1a), tarea +0x15 = 0 y sin destino; lo sincroniza con 0x497860. Preserva todo.
ai_free = place('ai_free', '''
    pushad
    mov edi, eax
    imul esi, ebx, 0x49a
    add esi, 0x561f00
    mov ecx, 10
af_rec:
    test byte ptr [esi], 1
    jz af_rnext
    mov edx, 1
af_ent:
    cmp word ptr [esi + edx*2 + 0xc], di
    jne af_enext
    mov word ptr [esi + edx*2 + 0xc], 0
af_enext:
    inc edx
    cmp edx, 8
    jb af_ent
af_rnext:
    add esi, 0x40
    dec ecx
    jnz af_rec
    imul eax, edi, 0x1c
    and word ptr [eax + 0x54fe6c], 0xc3ff
    mov byte ptr [eax + 0x54fe67], 0
    mov dword ptr [eax + 0x54fe56], -1
    push edi
    call 0x497860
    add esp, 4
    popad
    ret
''')
# eax = x, edx = y -> eax = medio de la casilla (0x582158 + x*0xa0 + y) & 0xc0: 0x80 agua, 0x40 tierra, 0xc0
# transbordo; 0 fuera del mapa. Preserva el resto.
aimed = place('aimed', '''
    test eax, eax
    js aim_out
    test edx, edx
    js aim_out
    cmp ax, word ptr [0x503e00]
    jge aim_out
    cmp dx, word ptr [0x503e02]
    jge aim_out
    imul eax, eax, 0xa0
    movzx eax, byte ptr [eax + edx + 0x582158]
    and eax, 0xc0
    ret
aim_out:
    xor eax, eax
    ret
''')
# ai_conv: ebx = jugador, esi = x, edi = y (destino del grupo). Preserva todo. Locales: CV_*.
CV_X, CV_Y, CV_LX, CV_LY, CV_NEED, CV_K, CV_NX, CV_NY = (4 * i for i in range(8))
CV_LOC = 4 * 8
ai_conv = place('ai_conv', f'''
    pushad
    sub esp, {CV_LOC:#x}
    mov dword ptr [esp + {CV_X:#x}], esi
    mov dword ptr [esp + {CV_Y:#x}], edi
    mov eax, ebx
    call {boatcarr:#x}
    test eax, eax
    jz cv_out
    imul ebp, ebx, 0x4f0
    test byte ptr [ebp + 0x56eaaa], 8
    jz cv_out
    cmp word ptr [ebp + 0x56eaac], 2
    je cv_out
    movsx eax, word ptr [ebp + 0x56ea90]
    test eax, eax
    jz cv_out
    imul eax, eax, 0x1c
    movsx esi, word ptr [eax + 0x54fe52]
    movsx edi, word ptr [eax + 0x54fe54]
    mov dword ptr [esp + {CV_LX:#x}], esi
    mov dword ptr [esp + {CV_LY:#x}], edi
    call {crconv:#x}
    test eax, eax
    jnz cv_out
    imul eax, ebx, 0x1f8
    movsx ecx, word ptr [eax + 0x536c08]
    mov eax, ebx
    call {boatland:#x}
    test eax, eax
    jz cv_need
    cmp ecx, {LANDCAP + 1}
    jle cv_port
    mov ecx, {LANDCAP + 1}
cv_port:
    mov esi, -2
cv_px:
    mov edi, -2
cv_py:
    mov eax, dword ptr [esp + {CV_X:#x}]
    add eax, esi
    mov edx, dword ptr [esp + {CV_Y:#x}]
    add edx, edi
    call {aimed:#x}
    cmp eax, 0xc0
    je cv_need
    inc edi
    cmp edi, 2
    jle cv_py
    inc esi
    cmp esi, 2
    jle cv_px
    jmp cv_out
cv_need:
    movsx eax, word ptr [ebp + 0x56eaa8]
    sub ecx, eax
    mov dword ptr [esp + {CV_NEED:#x}], ecx
    mov dword ptr [esp + {CV_K:#x}], 0
cv_nb:
    mov eax, dword ptr [esp + {CV_K:#x}]
    movsx edx, word ptr [eax*2 + 0x4fe640]
    add edx, dword ptr [esp + {CV_LY:#x}]
    movsx eax, word ptr [eax*2 + 0x4fe658]
    add eax, dword ptr [esp + {CV_LX:#x}]
    mov dword ptr [esp + {CV_NX:#x}], eax
    mov dword ptr [esp + {CV_NY:#x}], edx
    call {aimed:#x}
    cmp eax, 0x80
    jne cv_nbnext
    mov esi, 1
cv_ar:
    movsx eax, word ptr [0x54fe50]
    cmp esi, eax
    jge cv_nbnext
    imul edi, esi, 0x1c
    test byte ptr [edi + 0x54fe63], 0x40
    jz cv_arnext
    test byte ptr [edi + 0x54fe64], 8
    jz cv_arnext
    movzx eax, word ptr [edi + 0x54fe5e]
    shr eax, 5
    and eax, 0xf
    cmp eax, ebx
    jne cv_arnext
    movsx eax, word ptr [edi + 0x54fe52]
    cmp eax, dword ptr [esp + {CV_NX:#x}]
    jne cv_arnext
    movsx eax, word ptr [edi + 0x54fe54]
    cmp eax, dword ptr [esp + {CV_NY:#x}]
    jne cv_arnext
    movsx eax, word ptr [edi + 0x54fe56]
    test eax, eax
    js cv_arnext
    movsx edx, word ptr [edi + 0x54fe58]
    test edx, edx
    js cv_arnext
    sub eax, dword ptr [esp + {CV_X:#x}]
    sub edx, dword ptr [esp + {CV_Y:#x}]
    call {crcheb:#x}
    cmp eax, 2
    jle cv_found
cv_arnext:
    inc esi
    jmp cv_ar
cv_found:
    push 0
    push dword ptr [esp + {CV_NY + 4:#x}]
    push dword ptr [esp + {CV_NX + 8:#x}]
    call 0x4411b0
    add esp, 0xc
    movsx eax, ax
    cmp eax, dword ptr [esp + {CV_NEED:#x}]
    jle cv_nbnext
    push dword ptr [esp + {CV_NY:#x}]
    push dword ptr [esp + {CV_NX + 4:#x}]
    push ebx
    call 0x4b91e0
    add esp, 0xc
    push ebx
    call 0x49c4b0
    add esp, 4
    push dword ptr [esp + {CV_Y:#x}]
    push dword ptr [esp + {CV_X + 4:#x}]
    push ebx
    call 0x4b91e0
    add esp, 0xc
    jmp cv_out
cv_nbnext:
    inc dword ptr [esp + {CV_K:#x}]
    cmp dword ptr [esp + {CV_K:#x}], 8
    jb cv_nb
cv_out:
    add esp, {CV_LOC:#x}
    popad
    ret
''')
# ai_move(p) cdecl, en lugar de 0x49c4b0(p) en 0x4c4bce. Al entrar: si = x, di = y (destino), la lista del marco de
# 0x4c4a10 en [esp + 0x2c]. Locales: AM_*; AM_KEEP y AM_DROP, listas de 8 palabras.
AM_P, AM_X, AM_Y, AM_ALLOW, AM_CODE, AM_N = (4 * i for i in range(6))
AM_KEEP, AM_DROP = 0x18, 0x28
AM_LOC = 0x38
AM_ARG, AM_EAX, AM_FRAME = AM_LOC + 0x24, AM_LOC + 0x1c, AM_LOC + 0x20 + 0x2c
ai_move = place('ai_move', f'''
    pushad
    sub esp, {AM_LOC:#x}
    movsx ebx, word ptr [esp + {AM_ARG:#x}]
    cmp ebx, 8
    jae am_orig
    imul eax, ebx, 0x1f8
    cmp word ptr [eax + 0x536c12], -1
    je am_orig
    mov dword ptr [esp + {AM_P:#x}], ebx
    movsx esi, si
    movsx edi, di
    mov dword ptr [esp + {AM_X:#x}], esi
    mov dword ptr [esp + {AM_Y:#x}], edi
    call {ai_conv:#x}
    mov dword ptr [esp + {AM_ALLOW:#x}], 0
am_try:
    mov byte ptr [{lchit:#x}], 0
    push dword ptr [esp + {AM_P:#x}]
    call 0x49c4b0
    add esp, 4
    movsx eax, ax
    mov dword ptr [esp + {AM_CODE:#x}], eax
    cmp eax, 5
    jne am_done
    cmp byte ptr [{lchit:#x}], 1
    jne am_done
    mov ebx, dword ptr [esp + {AM_P:#x}]
    imul ebp, ebx, 0x4f0
    movsx ecx, word ptr [ebp + 0x56eaa8]
    mov eax, dword ptr [esp + {AM_ALLOW:#x}]
    test eax, eax
    jnz am_dec
    mov eax, ebx
    call {boatcarr:#x}
    add eax, {LANDCAP}
    jmp am_clamp
am_dec:
    dec eax
am_clamp:
    dec ecx
    cmp eax, ecx
    jle am_c1
    mov eax, ecx
am_c1:
    test eax, eax
    jle am_done
    mov dword ptr [esp + {AM_ALLOW:#x}], eax
    xor eax, eax
    mov ecx, 8
am_zero:
    mov dword ptr [esp + ecx*4 + {AM_KEEP - 4:#x}], eax
    loop am_zero
    mov ax, word ptr [ebp + 0x56ea90]
    mov word ptr [esp + {AM_KEEP:#x}], ax
    mov edx, 1
    xor ecx, ecx
    xor esi, esi
am_split:
    movsx eax, word ptr [ebp + esi*2 + 0x56ea94]
    test eax, eax
    jz am_snext
    cmp ax, word ptr [esp + {AM_KEEP:#x}]
    je am_snext
    cmp edx, dword ptr [esp + {AM_ALLOW:#x}]
    jge am_drop
    mov word ptr [esp + edx*2 + {AM_KEEP:#x}], ax
    inc edx
    jmp am_snext
am_drop:
    mov word ptr [esp + ecx*2 + {AM_DROP:#x}], ax
    inc ecx
am_snext:
    inc esi
    cmp esi, 8
    jb am_split
    test ecx, ecx
    jz am_done
    mov dword ptr [esp + {AM_N:#x}], ecx
    xor esi, esi
am_free:
    movsx eax, word ptr [esp + esi*2 + {AM_DROP:#x}]
    call {ai_free:#x}
    inc esi
    cmp esi, dword ptr [esp + {AM_N:#x}]
    jb am_free
    cmp dword ptr [esp + {AM_N:#x}], 2
    jb am_group
    lea eax, [esp + {AM_DROP:#x}]
    push eax
    movsx eax, word ptr [esp + {AM_DROP + 4:#x}]
    push eax
    call 0x40f1a0
    add esp, 8
am_group:
    lea eax, [esp + {AM_KEEP:#x}]
    push eax
    call 0x497240
    add esp, 4
    xor ecx, ecx
am_frame:
    mov eax, dword ptr [esp + ecx*4 + {AM_KEEP:#x}]
    mov dword ptr [esp + ecx*4 + {AM_FRAME:#x}], eax
    inc ecx
    cmp ecx, 4
    jb am_frame
    push dword ptr [esp + {AM_Y:#x}]
    push dword ptr [esp + {AM_X + 4:#x}]
    push dword ptr [esp + {AM_P + 8:#x}]
    call 0x4b91e0
    add esp, 0xc
    jmp am_try
am_done:
    mov eax, dword ptr [esp + {AM_CODE:#x}]
    mov dword ptr [esp + {AM_EAX:#x}], eax
    add esp, {AM_LOC:#x}
    popad
    ret
am_orig:
    add esp, {AM_LOC:#x}
    popad
    jmp 0x49c4b0
''')
# ---- La IA reconstruye puentes: la meta 9 del juego (reconstruir una ciudad muerta), con el código del puente.
# br_head(n, x, y) cdecl, sobre las n casillas de br_xy: la cabecera del puente más a mano desde (x, y) para el jugador
# [0x4fb0ec]. Cabecera = casilla vecina (8 direcciones) que no es puente ni agua, ni montaña sin camino si las
# montañas no se pisan (lo mismo que ai_brq). eax = 0 si es (x, y); si no, su costo en el mapa de caminos de la IA
# (0x4a65d0, el que usa 0x41e290 para las ciudades) si lo tiene, o 0x10000 + distancia de rey si no; 0x7fffffff si
# no hay cabecera. La elegida queda en br_hxy (x | y << 16).
br_hxy = place_data('br_hxy', bytes(4))
br_head = place('br_head', f'''
    push ebx
    push esi
    push edi
    push ebp
    mov edi, 0x7fffffff
    xor esi, esi
brh_loop:
    mov ecx, esi
    shr ecx, 3
    cmp ecx, dword ptr [esp + 0x14]
    jae brh_end
    mov edx, esi
    and edx, 7
    movsx eax, word ptr [ecx*4 + {br_xy:#x}]
    movsx ebx, word ptr [edx*2 + {br_d8:#x}]
    add ebx, eax
    movsx ebp, word ptr [ecx*4 + {br_xy + 2:#x}]
    movsx eax, word ptr [edx*2 + {br_d8 + 16:#x}]
    add ebp, eax
    mov eax, ebx
    mov edx, ebp
    call {br_tile:#x}
    test eax, eax
    jz brh_next
    mov ecx, eax
    call {br_kind:#x}
    test eax, eax
    jnz brh_next
    movzx eax, word ptr [ecx]
    and eax, 0x1f
    imul eax, eax, 0x58
    movsx eax, word ptr [eax + 0x535f0c]
    cmp eax, 1
    je brh_next
    cmp eax, 4
    jne brh_cost
    cmp byte ptr [0x4fe688], 0
    jne brh_cost
    imul eax, ebx, 0xa0
    add eax, ebp
    test byte ptr [eax + 0x57d158], 0x30
    jz brh_next
brh_cost:
    xor eax, eax
    cmp ebx, dword ptr [esp + 0x18]
    jne brh_path
    cmp ebp, dword ptr [esp + 0x1c]
    je brh_key
brh_path:
    push ebp
    push ebx
    movsx eax, word ptr [0x4fb0ec]
    push eax
    call 0x4a65d0
    add esp, 0xc
    test eax, eax
    jnz brh_key
    mov eax, ebx
    sub eax, dword ptr [esp + 0x18]
    cdq
    xor eax, edx
    sub eax, edx
    mov ecx, eax
    mov eax, ebp
    sub eax, dword ptr [esp + 0x1c]
    cdq
    xor eax, edx
    sub eax, edx
    cmp eax, ecx
    jge brh_kd
    mov eax, ecx
brh_kd:
    add eax, 0x10000
brh_key:
    cmp eax, edi
    jge brh_next
    mov edi, eax
    shl ebp, 16
    movzx ebx, bx
    or ebp, ebx
    mov dword ptr [{br_hxy:#x}], ebp
brh_next:
    inc esi
    jmp brh_loop
brh_end:
    mov eax, edi
    pop ebp
    pop edi
    pop esi
    pop ebx
    ret
''')
# ai_brrebev: candidatos de puente para la meta 9, al final del evaluador de ciudades muertas (0x41e290, en 0x41e4eb,
# con su marco: [+0x12] límite, [+0x14] mejor valor, [+0x18] su costo, [+0x1c] su ciudad; x, y de la pila en
# [+0x2c], [+0x30]). Recorre los puentes derribados (cada uno una vez, desde su casilla menor) con la misma cuenta que
# las ciudades:
# - vacío (br_armies; reponerlo lo exige) y el oro alcanza para el costo de reconstruirlo (0x4b65e0, como br_cost);
# - cabecera alcanzable (br_head con costo de camino; la casilla de la pila cuenta 1): ese es el costo;
# - ningún ejército hostil visible más cerca que el límite (0x497a90 desde el puente; 15 si temperamento 0, si no 30);
# - no lo derribaría (ai_brs con flag 1, el peor caso: c + s < 5), para no ir y venir;
# - hay algo que ganar cruzándolo: 0x41d640 + 0x41ec20 (ruinas sin explorar y ciudades neutrales cerca, el paso
#   hacia el objetivo) > 0. Una ciudad muerta vale por sí misma; un puente, solo por lo que abre.
# Valor = max(0, 50 - costo) + 2 * oportunidades + 0x4deb20(1, 6), como el de una ciudad. Si el mejor es un puente,
# se guarda con su código en la tabla de candidatos ([0x5032e6]) y se salta el final del original, que lo nombraría
# como ciudad.
EV_X, EV_Y, EV_N, EV_D, EV_SX, EV_SY, EV_P, EV_DI, EV_V, EV_E = (4 * i for i in range(10))
EV_LOC = 4 * 10
EVF = EV_LOC + 0x20
ai_brrebev = place('ai_brrebev', f'''
    pushad
    sub esp, {EV_LOC:#x}
    movsx eax, word ptr [0x4fb0ec]
    mov dword ptr [esp + {EV_P:#x}], eax
    movsx eax, word ptr [esp + {EVF + 0x2c:#x}]
    mov dword ptr [esp + {EV_SX:#x}], eax
    movsx eax, word ptr [esp + {EVF + 0x30:#x}]
    mov dword ptr [esp + {EV_SY:#x}], eax
    mov dword ptr [esp + {EV_Y:#x}], 0
rbe_row:
    movsx eax, word ptr [0x503e02]
    cmp dword ptr [esp + {EV_Y:#x}], eax
    jge rbe_end
    cmp dword ptr [esp + {EV_Y:#x}], 160
    jge rbe_end
    mov dword ptr [esp + {EV_X:#x}], 0
rbe_col:
    movsx eax, word ptr [0x503e00]
    cmp dword ptr [esp + {EV_X:#x}], eax
    jge rbe_rownext
    cmp dword ptr [esp + {EV_X:#x}], 128
    jge rbe_rownext
    mov eax, dword ptr [esp + {EV_X:#x}]
    mov edx, dword ptr [esp + {EV_Y:#x}]
    call {br_tile:#x}
    test eax, eax
    jz rbe_next
    call {br_kind:#x}
    cmp eax, {BR_KIND_RAZED}
    jne rbe_next
    mov ebx, dword ptr [esp + {EV_Y:#x}]
    shl ebx, 7
    add ebx, dword ptr [esp + {EV_X:#x}]
    push {BR_KIND_RAZED}
    lea eax, [ebx + {BR_CODE:#x}]
    push eax
    call {br_comp:#x}
    add esp, 8
    test eax, eax
    jz rbe_next
    mov dword ptr [esp + {EV_N:#x}], eax
    mov ecx, eax
rbe_canon:
    dec ecx
    js rbe_free
    movsx eax, word ptr [ecx*4 + {br_xy + 2:#x}]
    shl eax, 7
    movsx edx, word ptr [ecx*4 + {br_xy:#x}]
    add eax, edx
    cmp eax, ebx
    jl rbe_next
    jmp rbe_canon
rbe_free:
    push -1
    push dword ptr [esp + {EV_N + 4:#x}]
    call {br_armies:#x}
    add esp, 8
    test edx, edx
    jnz rbe_next
    push dword ptr [esp + {EV_P:#x}]
    lea eax, [ebx + {BR_CODE:#x}]
    push eax
    call 0x4b65e0
    add esp, 8
    movsx eax, ax
    imul ecx, dword ptr [esp + {EV_P:#x}], 0x1f8
    cmp eax, dword ptr [ecx + 0x536c14]
    jg rbe_next
    push dword ptr [esp + {EV_SY:#x}]
    push dword ptr [esp + {EV_SX + 4:#x}]
    push dword ptr [esp + {EV_N + 8:#x}]
    call {br_head:#x}
    add esp, 0xc
    cmp eax, 0x10000
    jge rbe_next
    test eax, eax
    jnz rbe_d
    inc eax
rbe_d:
    mov dword ptr [esp + {EV_D:#x}], eax
    push 0
    push dword ptr [esp + {EV_Y + 4:#x}]
    push dword ptr [esp + {EV_X + 8:#x}]
    call 0x497a90
    add esp, 0xc
    movsx eax, ax
    mov dword ptr [esp + {EV_E:#x}], eax
    movsx ecx, word ptr [esp + {EVF + 0x12:#x}]
    cmp ecx, eax
    jg rbe_next
    push 1
    push dword ptr [esp + {EV_P + 4:#x}]
    lea eax, [ebx + {BR_CODE:#x}]
    push eax
    call {ai_brs:#x}
    add esp, 0xc
    cmp eax, 5
    jge rbe_next
    push dword ptr [esp + {EV_Y:#x}]
    push dword ptr [esp + {EV_X + 4:#x}]
    call 0x41d640
    add esp, 8
    movsx esi, ax
    push dword ptr [esp + {EV_Y:#x}]
    push dword ptr [esp + {EV_X + 4:#x}]
    call 0x41ec20
    add esp, 8
    movsx eax, ax
    add esi, eax
    test esi, esi
    jle rbe_next
    mov dword ptr [esp + {EV_DI:#x}], esi
    mov edi, 50
    sub edi, dword ptr [esp + {EV_D:#x}]
    jg rbe_pos
    xor edi, edi
rbe_pos:
    lea edi, [edi + esi*2]
    push 0
    push 6
    push 1
    call 0x4deb20
    add esp, 0xc
    movsx eax, ax
    add edi, eax
    mov dword ptr [esp + {EV_V:#x}], edi
    push 0
    lea eax, [ebx + {BR_CODE:#x}]
    push eax
    call {br_name:#x}
    add esp, 8
    push eax
    push dword ptr [esp + {EV_E + 4:#x}]
    push dword ptr [esp + {EV_DI + 8:#x}]
    push dword ptr [esp + {EV_D + 0xc:#x}]
    push dword ptr [esp + {EV_V + 0x10:#x}]
    push 0x4f9edc
    push 0x564d90
    call dword ptr [0x5a9bec]
    add esp, 0x1c
    mov ax, word ptr [0x564e48]
    mov cx, ax
    inc ax
    mov word ptr [0x564e48], ax
    push 0x564d90
    push ecx
    call 0x427520
    add esp, 8
    mov eax, dword ptr [esp + {EV_V:#x}]
    cmp ax, word ptr [esp + {EVF + 0x14:#x}]
    jle rbe_next
    mov word ptr [esp + {EVF + 0x14:#x}], ax
    mov eax, dword ptr [esp + {EV_D:#x}]
    mov word ptr [esp + {EVF + 0x18:#x}], ax
    lea eax, [ebx + {BR_CODE:#x}]
    mov word ptr [esp + {EVF + 0x1c:#x}], ax
rbe_next:
    inc dword ptr [esp + {EV_X:#x}]
    jmp rbe_col
rbe_rownext:
    inc dword ptr [esp + {EV_Y:#x}]
    jmp rbe_row
rbe_end:
    movsx eax, word ptr [esp + {EVF + 0x1c:#x}]
    cmp eax, {BR_CODE:#x}
    jl rbe_city
    mov word ptr [0x5032e6], ax
    mov cx, word ptr [esp + {EVF + 0x18:#x}]
    mov word ptr [0x5032e8], cx
    mov word ptr [0x5032ea], 1
    push 0
    push eax
    call {br_name:#x}
    add esp, 8
    push eax
    movsx ecx, word ptr [esp + {EVF + 0x18 + 4:#x}]
    push ecx
    push 1
    push 0x4f9e7c
    push 0x564d90
    call dword ptr [0x5a9bec]
    add esp, 0x14
    mov ax, word ptr [0x564e48]
    mov cx, ax
    inc ax
    mov word ptr [0x564e48], ax
    push 0x564d90
    push ecx
    call 0x427520
    add esp, 8
    add esp, {EV_LOC:#x}
    popad
    jmp 0x41e563
rbe_city:
    add esp, {EV_LOC:#x}
    popad
    cmp word ptr [esp + 0x1c], -1
    je 0x41e563
    jmp 0x41e4f3
''')
# ai_brreb: la meta 9 (0x40dbf0(índice)) para un puente. Como la del original con una ciudad: va a la cabecera
# (br_head; 0x4973f0(7, 0, x, y) y 0x40d2b0(x, y), como ai_brq) y, si el líder llega vivo, lo repone con la orden de
# red de un humano (0x4b9ce0(código, costo, jugador) = 0x18e, que aplica br_rebapply en todas las máquinas), después
# de volver a mirar que siga derribado, vacío y que el oro alcance. Pausa 0x4275b0 y fin de la pila (0x40d230), como
# el original. Devuelve 0 siempre, como el original.
ai_brreb = place('ai_brreb', f'''
    cmp word ptr [esp + 4], {BR_CODE:#x}
    jge arb_bridge
    sub esp, 4
    mov eax, dword ptr [0x5020d4]
    jmp 0x40dbf8
arb_bridge:
    push ebx
    push esi
    push edi
    push ebp
    mov eax, dword ptr [0x5020d4]
    movsx edi, word ptr [eax + 0xc]
    imul edi, edi, 0x1c
    movsx eax, word ptr [esp + 0x14]
    push {BR_KIND_RAZED}
    push eax
    call {br_comp:#x}
    add esp, 8
    test eax, eax
    jz arb_ret0
    movsx ecx, word ptr [edi + 0x54fe54]
    push ecx
    movsx ecx, word ptr [edi + 0x54fe52]
    push ecx
    push eax
    call {br_head:#x}
    add esp, 0xc
    cmp eax, 0x7fffffff
    je arb_ret0
    test eax, eax
    jz arb_here
    movsx esi, word ptr [{br_hxy:#x}]
    movsx ebx, word ptr [{br_hxy + 2:#x}]
    push ebx
    push esi
    push 0
    push 7
    call 0x4973f0
    add esp, 0x10
    mov eax, dword ptr [0x5020d4]
    mov word ptr [eax + 6], 9
    mov word ptr [eax + 8], 0
    push ebx
    push esi
    call 0x40d2b0
    add esp, 8
    test ax, ax
    jz arb_ret0
    test byte ptr [edi + 0x54fe63], 0x40
    jz arb_ret0
    cmp word ptr [edi + 0x54fe52], si
    jne arb_ret0
    cmp word ptr [edi + 0x54fe54], bx
    jne arb_ret0
arb_here:
    movsx eax, word ptr [esp + 0x14]
    push {BR_KIND_RAZED}
    push eax
    call {br_comp:#x}
    add esp, 8
    test eax, eax
    jz arb_ret0
    push -1
    push eax
    call {br_armies:#x}
    add esp, 8
    test edx, edx
    jnz arb_ret0
    movsx ebx, word ptr [0x4fb0ec]
    push ebx
    movsx eax, word ptr [esp + 0x18]
    push eax
    call 0x4b65e0
    add esp, 8
    movsx esi, ax
    imul eax, ebx, 0x1f8
    cmp esi, dword ptr [eax + 0x536c14]
    jg arb_ret0
    push ebx
    push esi
    movsx eax, word ptr [esp + 0x1c]
    push eax
    call 0x4b9ce0
    add esp, 0xc
    push 0x7d0
    call 0x4275b0
    add esp, 4
    mov eax, dword ptr [0x5020d4]
    xor ecx, ecx
    mov word ptr [eax + 6], cx
    mov word ptr [eax + 8], cx
    call 0x40d230
arb_ret0:
    xor eax, eax
    pop ebp
    pop edi
    pop esi
    pop ebx
    ret
''')
# Nombres en los textos de depuración de la meta 9 (se arman también sin depurar): "Ctd - Rebuild %s" (0x40ce24) y
# "Evaluate rebuild %s" (0x41f30c) leían el nombre de la tabla de ciudades con el código del puente.
ai_brname9 = place('ai_brname9', f'''
    movsx eax, word ptr [esp + 0x1e]
    cmp eax, {BR_CODE:#x}
    jge aib9_bridge
    lea edx, [eax + eax*8]
    lea eax, [eax + edx*4]
    lea ecx, [eax + eax*2]
    lea edx, [ecx*2 + 0x537e30]
    jmp 0x40ce39
aib9_bridge:
    push 0
    push eax
    call {br_name:#x}
    add esp, 8
    mov edx, eax
    jmp 0x40ce39
''')
ai_brname9s = place('ai_brname9s', f'''
    mov si, word ptr [0x5032e6]
    movsx eax, si
    cmp eax, {BR_CODE:#x}
    jge aib9s_bridge
    lea edx, [eax + eax*8]
    lea eax, [eax + edx*4]
    lea ecx, [eax + eax*2]
    lea edx, [ecx*2 + 0x537e30]
    jmp 0x41f326
aib9s_bridge:
    push 0
    push eax
    call {br_name:#x}
    add esp, 8
    mov edx, eax
    jmp 0x41f326
''')
# Diálogo de reconstruir (0x4b6160(índice)): para un puente, derribado y vacío (si no, el aviso 0x72 "Cannot rebuild!
# Other armies are here..."); el índice queda en [0x587e5c] como el de un sitio.
br_rebdlg = place('br_rebdlg', f'''
    mov ax, word ptr [esp + 4]
    cmp ax, {BR_CODE:#x}
    jge brd2_bridge
    jmp 0x4b6165
brd2_bridge:
    movsx eax, ax
    push {BR_KIND_RAZED}
    push eax
    call {br_comp:#x}
    add esp, 8
    test eax, eax
    jz brd2_ret
    push -1
    push eax
    call {br_armies:#x}
    add esp, 8
    test edx, edx
    jnz brd2_busy
    mov ax, word ptr [esp + 4]
    mov word ptr [0x587e5c], ax
    jmp 0x4b6180
brd2_busy:
    push 0x14
    mov ecx, 0x589880
    push 0
    push 0x72
    call 0x4def30
    push eax
    call 0x4c2790
    add esp, 8
brd2_ret:
    ret
''')
# Dibujo del diálogo (0x4b64a0, evento 4): la imagen es la del tipo de sitio ([0x55ad4a + i*0x96]); un puente no
# tiene, y su código leería fuera de la tabla.
br_rebdraw = place('br_rebdraw', f'''
    cmp dword ptr [esp + 4], 4
    jne 0x4b64e3
    cmp word ptr [0x587e5c], {BR_CODE:#x}
    jge 0x4b64e3
    jmp 0x4b64a7
''')
# Texto "Rebuilding %s" (0x4b64f0).
br_rebtxt = place('br_rebtxt', f'''
    movsx eax, word ptr [0x587e5c]
    cmp eax, {BR_CODE:#x}
    jl brx_site
    push 0
    push eax
    call {br_name:#x}
    add esp, 8
    jmp brx_go
brx_site:
    lea eax, [eax + eax*4]
    add eax, eax
    lea ecx, [eax + eax*2]
    lea eax, [ecx + ecx*4]
    add eax, 0x55acba
brx_go:
    mov ecx, 0x589880
    jmp 0x4b650c
''')
# Costo (0x4b65e0(índice, jugador), en 0x4b65e5 tras el push esi): el de fundar una ciudad para un puente.
br_cost = place('br_cost', f'''
    mov si, word ptr [0x569510]
    cmp word ptr [esp + 8], {BR_CODE:#x}
    jl 0x4b65ec
    mov si, word ptr [0x56950e]
    jmp 0x4b65ec
''')
# Aplicación de reconstruir (0x4b6610(índice, costo, jugador), en todas las máquinas). Para un puente: vuelve a
# comprobar que está derribado y vacío, cobra (0x43fd60(jugador, -costo)), lo repone y refresca grafo y vista.
br_rebapply = place('br_rebapply', f'''
    cmp word ptr [esp + 4], {BR_CODE:#x}
    jge brp_bridge
    push esi
    call 0x4a2170
    jmp 0x4b6616
brp_bridge:
    push ebx
    push esi
    push edi
    call 0x4a2170
    movsx eax, word ptr [esp + 0x10]
    push {BR_KIND_RAZED}
    push eax
    call {br_comp:#x}
    add esp, 8
    test eax, eax
    jz brp_out
    mov esi, eax
    push -1
    push esi
    call {br_armies:#x}
    add esp, 8
    test edx, edx
    jnz brp_out
    movsx eax, word ptr [esp + 0x14]
    neg eax
    push eax
    movsx eax, word ptr [esp + 0x1c]
    push eax
    call 0x43fd60
    add esp, 8
    xor edi, edi
brp_tile:
    movzx eax, word ptr [edi*4 + {br_xy:#x}]
    movzx edx, word ptr [edi*4 + {br_xy + 2:#x}]
    call {br_tile:#x}
    mov cl, byte ptr [eax + 3]
    and cl, 0xf8
    or cl, 1
    mov byte ptr [eax + 3], cl
    and byte ptr [eax + 9], 0x7f
    inc edi
    cmp edi, esi
    jb brp_tile
    call 0x4a4f20
    mov ecx, 0x569588
    call 0x456ee0
brp_out:
    pop edi
    pop esi
    pop ebx
    ret
''')
# Restos del puente derribado: en el mapa se dibuja la cabecera de cada pieza del lado de la costa, para que se vea
# dónde reconstruirlo. La vista copia la casilla a su celda en 0x4583b0: estructura en bits 10-12 de la palabra 0 y,
# si hay estructura, [+8] en [celda+0xe]; el dibujo (0x459a9f) pone el camino con estructura 1 (clase 4): hoja
# 0x21 + ([+0xe] & 0xf), pieza ([+0xe] >> 5) & 0x1f = fila*8 + columna de 48x48. Un puente derribado (estructura 0)
# lleva ahora [+8] en [celda+0xe] con el bit 0x8000 (el de derribado); en el resto de las celdas sin estructura ese
# bit se borra, porque [celda+0xe] queda de lo que mostraba antes la celda.
BR_STUB = 18
br_stubtab = bytearray(32 * 8)                          # por pieza, hasta 2 rectángulos (dx, dy, ancho, alto)
for piece, rects in {1 * 8 + 6: [(0, 0, BR_STUB, 48)],                         # horizontal, mitad izquierda
                     1 * 8 + 7: [(48 - BR_STUB, 0, BR_STUB, 48)],              # horizontal, mitad derecha
                     2 * 8 + 7: [(0, 0, 48, BR_STUB)],                         # vertical, mitad de arriba
                     2 * 8 + 6: [(0, 48 - BR_STUB, 48, BR_STUB)],              # vertical, mitad de abajo
                     3 * 8 + 4: [(0, 0, BR_STUB, 48), (48 - BR_STUB, 0, BR_STUB, 48)],   # de una casilla
                     3 * 8 + 5: [(0, 0, 48, BR_STUB), (0, 48 - BR_STUB, 48, BR_STUB)]}.items():
    for k, r in enumerate(rects):
        struct.pack_into('<bbBB', br_stubtab, piece * 8 + k * 4, *r)
br_stubtab = place_data('br_stubtab', bytes(br_stubtab))
# Copia a la celda (reemplaza 0x45846d..0x45847f; ecx = casilla, edi = celda, bp = palabra 0 nueva).
br_vfill = place('br_vfill', f'''
    mov word ptr [edi], bp
    test bp, 0x1c00
    jz bvf_none
    mov ax, word ptr [ecx + 8]
    mov word ptr [edi + 0xe], ax
    jmp 0x45847f
bvf_none:
    and word ptr [edi + 0xe], 0x7fff
    test byte ptr [ecx + 9], 0x80
    jz 0x45847f
    mov eax, ecx
    call {br_kind:#x}
    cmp eax, {BR_KIND_RAZED}
    jne 0x45847f
    mov ax, word ptr [ecx + 8]
    mov word ptr [edi + 0xe], ax
    jmp 0x45847f
''')
# Dibujo (reemplaza 0x459a9f..0x459aaa; esi = celda, edi = x en pantalla, [esp+0x1c] = y). Camino: sigue el del juego.
br_vdraw = place('br_vdraw', f'''
    mov ax, word ptr [esi]
    and ah, 0x1c
    cmp ah, 4
    je 0x459aaa
    test ah, ah
    jnz 0x459af5
    movzx ecx, word ptr [esi + 0xe]
    test ch, 0x80
    jz 0x459af5
    pushad
    mov ebx, ecx
    shr ecx, 5
    and ecx, 0x1f
    lea ebp, [ecx*8 + {br_stubtab:#x}]
    xor esi, esi
bvd_loop:
    movzx eax, byte ptr [ebp + esi*4 + 2]
    test eax, eax
    jz bvd_next
    movsx ecx, byte ptr [ebp + esi*4 + 1]
    add ecx, dword ptr [esp + 0x3c]
    push ecx
    movsx ecx, byte ptr [ebp + esi*4]
    add ecx, edi
    push ecx
    push 0x27
    movzx ecx, byte ptr [ebp + esi*4 + 3]
    push ecx
    push eax
    mov eax, ebx
    shr eax, 8
    and eax, 3
    imul eax, eax, 0x30
    movsx ecx, byte ptr [ebp + esi*4 + 1]
    add eax, ecx
    push eax
    mov eax, ebx
    shr eax, 5
    and eax, 7
    imul eax, eax, 0x30
    movsx ecx, byte ptr [ebp + esi*4]
    add eax, ecx
    push eax
    mov eax, ebx
    and eax, 0xf
    add eax, 0x21
    push eax
    call 0x4dd530
    add esp, 0x20
bvd_next:
    inc esi
    cmp esi, 2
    jb bvd_loop
    popad
    jmp 0x459af5
''')

# ---------------------------------------------------------------- Combat Bonus "Bridge"
# El bono de combate de cada unidad (nombre +0xd6, valor +0xdf del registro) se compara en 0x467b4a..0x467d09 con la
# casilla de la batalla (la del defensor, [esp+0x38]; vale para atacantes y defensores): "OPEN"/"FIELD", "CITY",
# "WOODS"/"FOREST" o el nombre del terreno; si coincide, [esp+0x11] = 1 y el valor se suma a la fuerza. Se agrega
# "BRIDGE" (sin distinguir mayúsculas): coincide si la casilla es un puente en pie, clase agua (di, palabra 0x535f0c
# del tipo, ya cargada) con estructura 1 ([+3] & 7, la misma definición que el constructor de caminos en 0x4a5135).
# Un puente derribado tiene estructura 0: no cuenta. El texto "+N ..." lo arma 0x46a6e0 con bridge.STT.
bridgestr = place_data('bridgestr', b'BRIDGE\0')
bridgecb = place('bridgecb', f'''
    lea eax, [esp + 0x4c]
    push {bridgestr:#x}
    push eax
    call dword ptr [0x5a9be0]
    add esp, 8
    test eax, eax
    jnz bcb_other
    mov edx, dword ptr [esp + 0x38]
    mov al, byte ptr [edx + 3]
    and al, 7
    cmp al, 1
    jne 0x467d0e
    cmp di, 1
    jne 0x467d0e
    jmp 0x467d09
bcb_other:
    lea eax, [esp + 0x4c]
    push 0x4fc808
    jmp 0x467bac
''')

# ---------------------------------------------------------------- Botones de Votación y Sorteo
# El anfitrión (máquina 0) abre las herramientas: Votación desde el menú de partida (línea nueva "Votacion", diálogo
# 35) y Sorteo desde la pantalla de preparación (botón con su ícono junto a Chat, diálogo 7). La orden viaja por red (TL_OPEN) y cada
# PC abre su propia copia: el anfitrión como operador, los demás como espectadores con sus bandos marcados. El estado
# va y viene por archivos en Herramientas\ y por red (TL_STATE), fuera de la simulación: no puede desincronizar turnos.
#   operador:    <tool>.op   (lo escribe el programa del anfitrión) -> se renombra a .env, se lee y se manda.
#   espectador:  <tool>.ver  (lo escribe el juego al recibir TL_STATE; se arma en .vtmp y se renombra).
# Un Warlords sin el parche descarta los dos tipos (el despachador de 0x4b69e0 ignora los mayores que 0x209).
TOOLS = ('votacion', 'sorteo')
TL_OPEN, TL_STATE = 0x2a0, 0x2a1   # carga: herramienta (dword) | herramienta (dword) + texto con NUL (hasta 256)
VOTE_TXT, VOTE_HOT, COIN = 0x19, 0x1a, 97
SORTEO_FILE = RAM_FILE + 1   # hoja SETS\Fantasy\sorteo.pcx con el dibujo del botón de Sorteo
SORTEO_X, SORTEO_Y, SORTEO_W, SORTEO_H = 567, 409, 64, 60   # abajo a la derecha, en el cielo junto al murciélago
GETTICK, CREATEPROC, CLOSEH, MOVEF, DELF = 0x5a97f8, 0x5a97d0, 0x5a97d8, 0x5a97e4, 0x5a97c0
CREATEF, READF, WRITEF, CREATETH, MSGBOX, STRLEN = 0x5a9810, 0x5a9814, 0x5a9818, 0x5a97ec, 0x5a9c30, 0x5a9b98
SIDE, SIDE_ON, SIDE_HUMAN, SIDE_MACHINE = 0x1f8, 0x536b30, 0x536c12, 0x536b33
tl_voting = place_data('tl_voting', cstr_('Votacion'))
tl_caption = place_data('tl_caption', cstr_(GAME))
tl_vars = place_data('tl_vars', bytes(16))   # +0 tick, +4 ocupado, +8 abrir[2], +0xc estado[2]
TL_TICK, TL_BUSY, TL_PEND_OPEN, TL_PEND_STATE = tl_vars, tl_vars + 4, tl_vars + 8, tl_vars + 0xc
tl_n = place_data('tl_n', bytes(4))
tl_openpkt = place_data('tl_openpkt', bytes(4))
tl_pkt = place_data('tl_pkt', bytes(4 + 256))
tl_buf = place_data('tl_buf', bytes(256 * len(TOOLS)))   # último estado recibido, por herramienta
tl_si = place_data('tl_si', struct.pack('<I', 68) + bytes(64))   # STARTUPINFOA
tl_pi = place_data('tl_pi', bytes(16))                           # PROCESS_INFORMATION
tl_path = {}
for t, n in enumerate(TOOLS):
    for ext in ('ver', 'vtmp', 'op', 'env'):
        tl_path[t, ext] = place_data(f'tl_{n}_{ext}', cstr_(f'Herramientas\\{n}.{ext}'))
    tl_path[t, 'exe'] = place_data(f'tl_{n}_exe', cstr_(f'Herramientas\\{n}.exe'))
    tl_path[t, 'op_cmd'] = place_data(f'tl_{n}_opcmd', cstr_(f'"Herramientas\\{n}.exe" --operador'))
    sp = cstr_(f'"Herramientas\\{n}.exe" --espectador 00000000')
    tl_path[t, 'sp_cmd'] = place_data(f'tl_{n}_spcmd', sp)
    tl_path[t, 'mask'] = tl_path[t, 'sp_cmd'] + len(sp) - 9   # carácter s: '1' si el bando s es humano de esta PC
    tl_path[t, 'err'] = place_data(f'tl_{n}_err', cstr_(f'No se pudo abrir Herramientas\\{n}.exe'))

# ---- Pausa mientras se vota (pz_*). Cada PC lleva su propia cuenta regresiva del turno (vence en [0x4ff7a8], con el
# timeGetTime de esa PC; al vencer, la PC del jugador de turno manda el fin de turno), así que la pausa se arma en cada
# PC con lo que ya viaja por red: la orden de abrir la Votación (TL_OPEN 0) pausa, y el estado que manda el anfitrión
# (TL_STATE 0, "VOT <sesión> <fase> ...") la mantiene hasta que dice "cerrado". Si el estado deja de llegar 60 s (el
# programa se colgó o se mató), se reanuda sola. Nada de esto se guarda ni viaja como estado de la partida.
# En pausa: se corren hacia adelante el vencimiento del turno, el de los 20 s de gracia ([0x5885cc]) y el fin de la
# partida por minutos ([0x5032f8+0x4c], -1 si no hay); el despacho de mensajes descarta teclas y botones del mouse
# (no se deshabilita la ventana: al cerrarse la Votación, Windows no le devolvería el foco a una ventana deshabilitada);
# y se mantiene un aviso en pantalla con 0x4c2790 (4 renglones de 64 bytes en 0x5885e8, vencimiento en 0x5885d8).
PZ_TEXT = 'Votacion en curso: partida en pausa'
PZ_WATCH = 60000
TURN_END, GRACE_END, GAMECLK, MSG_TXT, MSG_END = 0x4ff7a8, 0x5885cc, 0x5032f8, 0x5885e8, 0x5885d8
DISPATCH = 0x5a9c5c   # DispatchMessageA
pz_text = place_data('pz_text', cstr_(PZ_TEXT))
pz_vars = place_data('pz_vars', bytes(12))   # +0 en pausa, +1 votación abierta, +4 último tick, +8 último estado
PZ_ON, PZ_ARM, PZ_LAST, PZ_SEEN = pz_vars, pz_vars + 1, pz_vars + 4, pz_vars + 8
pz_closepkt_data = struct.pack('<I', 0) + cstr_('VOT - cerrado 0 0 --------')
pz_closepkt = place_data('pz_closepkt', pz_closepkt_data)

# Correr los vencimientos lo que pasó desde la última vez (se llama a cada vuelta de la función ociosa y al entrar a los
# controles del reloj 0x4c0fe0, 0x4c10c0 y 0x4c1250). Conserva todos los registros.
pz_tick = place('pz_tick', f'''
    pushad
    call dword ptr [{GETTICK:#x}]
    mov edx, eax
    xchg edx, dword ptr [{PZ_LAST:#x}]
    cmp byte ptr [{PZ_ON:#x}], 0
    je pk_end
    sub eax, edx
    add dword ptr [{TURN_END:#x}], eax
    add dword ptr [{GRACE_END:#x}], eax
    cmp dword ptr [{GAMECLK + 0x4c:#x}], -1
    je pk_end
    cmp dword ptr [{GAMECLK + 0x50:#x}], -1
    je pk_end
    add dword ptr [{GAMECLK + 0x4c:#x}], eax
pk_end:
    popad
    ret
''')

# Llegó la orden de abrir la Votación.
pz_open = place('pz_open', f'''
    pushad
    call dword ptr [{GETTICK:#x}]
    mov dword ptr [{PZ_SEEN:#x}], eax
    mov byte ptr [{PZ_ARM:#x}], 1
    cmp byte ptr [{PZ_ON:#x}], 0
    jne po_end
    mov dword ptr [{PZ_LAST:#x}], eax
    mov byte ptr [{PZ_ON:#x}], 1
po_end:
    popad
    ret
''')

# Llegó un estado de la Votación (edi = texto). Solo cuenta después de una orden de abrir: un .op viejo que quedó de
# otra partida no pausa.
pz_state = place('pz_state', f'''
    pushad
    cmp byte ptr [{PZ_ARM:#x}], 0
    je pst_end
    cmp dword ptr [edi], 0x20544f56
    jne pst_end
    call dword ptr [{GETTICK:#x}]
    mov dword ptr [{PZ_SEEN:#x}], eax
    lea esi, [edi + 4]
pst_skip:
    mov cl, byte ptr [esi]
    test cl, cl
    jz pst_end
    inc esi
    cmp cl, 0x20
    jne pst_skip
    cmp dword ptr [esi], 0x72726563
    jne pst_on
    cmp dword ptr [esi + 4], 0x206f6461
    jne pst_on
    mov byte ptr [{PZ_ARM:#x}], 0
    mov byte ptr [{PZ_ON:#x}], 0
    jmp pst_end
pst_on:
    cmp byte ptr [{PZ_ON:#x}], 0
    jne pst_end
    mov dword ptr [{PZ_LAST:#x}], eax
    mov byte ptr [{PZ_ON:#x}], 1
pst_end:
    popad
    ret
''')

# Renglón del aviso en pantalla: eax = 0..3, o -1 si no está.
pz_find = place('pz_find', f'''
    push ecx
    push esi
    push edi
    xor ecx, ecx
pf_slot:
    mov esi, ecx
    shl esi, 6
    add esi, {MSG_TXT:#x}
    mov edi, {pz_text:#x}
pf_cmp:
    mov al, byte ptr [esi]
    cmp al, byte ptr [edi]
    jne pf_next
    test al, al
    jz pf_found
    inc esi
    inc edi
    jmp pf_cmp
pf_next:
    inc ecx
    cmp ecx, 4
    jb pf_slot
    or ecx, -1
pf_found:
    mov eax, ecx
    pop edi
    pop esi
    pop ecx
    ret
''')

# Cada ~250 ms (desde tl_idle): vigilancia de los 60 s y el aviso (se pone si no está, se le estira el vencimiento si
# está; al reanudar se lo deja vencer ya).
PZ_SLOW = f'''
    cmp byte ptr [{PZ_ON:#x}], 0
    je pw_off
    call dword ptr [{GETTICK:#x}]
    mov ebx, eax
    sub eax, dword ptr [{PZ_SEEN:#x}]
    cmp eax, {PZ_WATCH}
    jb pw_show
    mov byte ptr [{PZ_ON:#x}], 0
    jmp pw_off
pw_show:
    call {pz_find:#x}
    test eax, eax
    js pw_post
    add ebx, 5000
    mov dword ptr [eax * 4 + {MSG_END:#x}], ebx
    jmp pw_end
pw_post:
    push 50
    push {pz_text:#x}
    call 0x4c2790
    add esp, 8
    jmp pw_end
pw_off:
    call {pz_find:#x}
    test eax, eax
    js pw_end
    mov ebx, eax
    call dword ptr [{GETTICK:#x}]
    mov dword ptr [ebx * 4 + {MSG_END:#x}], eax
pw_end:
'''

# DispatchMessageA de los 6 bucles de mensajes del juego: en pausa no pasan teclas (0x100..0x109) ni botones y rueda
# del mouse (0x201..0x20e). El movimiento del mouse sí.
pz_disp = place('pz_disp', f'''
    cmp byte ptr [{PZ_ON:#x}], 0
    je pd_pass
    mov eax, dword ptr [esp + 4]
    mov eax, dword ptr [eax + 4]
    cmp eax, 0x100
    jb pd_pass
    cmp eax, 0x109
    jbe pd_drop
    cmp eax, 0x201
    jb pd_pass
    cmp eax, 0x20e
    ja pd_pass
pd_drop:
    xor eax, eax
    ret 4
pd_pass:
    jmp dword ptr [{DISPATCH:#x}]
''')
pz_dptr = place_data('pz_dptr', struct.pack('<I', pz_disp))

# Entradas de los controles del reloj del turno: primero correr los vencimientos.
pz_chk = {va: place(f'pz_chk_{va:x}', f'''
    call {pz_tick:#x}
    {insn}
    jmp {va + 7:#x}
''') for va, insn in ((0x4c0fe0, 'test byte ptr [0x53c38f], 0xf8'),
                      (0x4c10c0, 'cmp byte ptr [0x4ff7a0], 0'),
                      (0x4c1250, 'cmp byte ptr [0x4ff7a0], 0'))}

# ---- Resultado de la votación en el Events Report (vt_*). Los sucesos de la ronda en curso viven en 0x572788 (8
# jugadores x 2 renglones de 0x1c: +0 tipo, que es también la prioridad, +2 jugador, +4 parámetro, +6 nombre[16],
# +0x16/+0x18/+0x1a tres words). Al terminar la ronda, 0x4989d0 agrega un bloque a HISTORY.DAT (cabecera de 0x48 con
# el tamaño en +0 y la cantidad de renglones en +0x44, las ciudades y los renglones) y vacía la tabla con 0x4988d0; el
# informe (0x499450) arma las rondas pasadas desde HISTORY.DAT y la actual desde la tabla.
# Como en las partidas en red están los 8 bandos activos, no hay renglones libres en esa tabla: los resultados van en
# una aparte (vt_tab, hasta VT_MAX por ronda), con tipo 0x13 (nuevo), jugador = el bando que abrió la Votación (o 8, sin escudo), SI en +0x16 y NO en +0x18. Se
# escriben en HISTORY.DAT antes que los sucesos de la ronda (el informe muestra 11 renglones por ronda), se suman a la
# ronda en curso del informe y se guardan al final del .SAV ('VOTA', cantidad, tabla; el ejecutable original ignora lo
# que sobra después del final y un .SAV viejo carga la tabla vacía).
# Cuándo se anota una votación (con al menos un voto): cuando se reinicia (cambia el número de reinicios del estado) o
# cuando el programa se cierra ("cerrado"). Si el programa muere sin cerrar, o el cierre es el de emergencia (sesión
# "-"), no se anota nada.
VT_MAX = 8
VT_TYPE, VT_NOBODY = 0x13, 8
vt_save = place_data('vt_save', b'VOTA' + bytes(4 + VT_MAX * 0x1c))   # tal cual se escribe al final del .SAV
VT_N, VT_TAB = vt_save + 4, vt_save + 8
vt_vars = place_data('vt_vars', bytes(0x20))   # +0 pendiente, +4 reinicios, +8 SI, +0xa NO, +0xc 'VOTA' leído, +0x10 sesión
VT_HAVE, VT_RES, VT_SI, VT_NO, VT_MAGIC, VT_SES = (vt_vars + o for o in (0, 4, 8, 0xa, 0xc, 0x10))
vt_fmt = place_data('vt_fmt', cstr_('Resultados votacion: %d por el SI, %d por el NO'))
vt_owner = place_data('vt_owner', struct.pack('<I', VT_NOBODY))   # el bando que abrió la Votación en curso

# Llegó la orden de abrir la Votación: la abre el anfitrión (máquina 0), así que el bando que la pidió es el primero
# humano de la máquina 0 (cada PC lo calcula igual: los bandos son los mismos en todas). Ninguno: VT_NOBODY. Conserva
# todos los registros.
vt_open = place('vt_open', f'''
    pushad
    xor ecx, ecx
vo_loop:
    imul edx, ecx, {SIDE:#x}
    cmp byte ptr [edx + {SIDE_ON:#x}], 0
    je vo_next
    cmp word ptr [edx + {SIDE_HUMAN:#x}], -1
    jne vo_next
    cmp byte ptr [edx + {SIDE_MACHINE:#x}], 0
    je vo_set
vo_next:
    inc ecx
    cmp ecx, 8
    jb vo_loop
vo_set:
    mov dword ptr [{vt_owner:#x}], ecx
    popad
    ret
''')

# Anotar el resultado pendiente, si lo hay. Conserva todos los registros.
vt_commit = place('vt_commit', f'''
    pushad
    cmp byte ptr [{VT_HAVE:#x}], 0
    je vc_end
    mov byte ptr [{VT_HAVE:#x}], 0
    mov eax, dword ptr [{VT_N:#x}]
    cmp eax, {VT_MAX}
    jae vc_end
    inc dword ptr [{VT_N:#x}]
    imul edi, eax, 0x1c
    add edi, {VT_TAB:#x}
    mov ebx, edi
    xor eax, eax
    mov ecx, 7
    rep stosd
    mov word ptr [ebx], {VT_TYPE:#x}
    mov ax, word ptr [{vt_owner:#x}]
    mov word ptr [ebx + 2], ax
    mov ax, word ptr [{VT_SI:#x}]
    mov word ptr [ebx + 0x16], ax
    mov ax, word ptr [{VT_NO:#x}]
    mov word ptr [ebx + 0x18], ax
vc_end:
    popad
    ret
''')

# Llegó un estado de la Votación (edi = texto "VOT <sesión> <fase> <automáticas> <reinicios> <8 marcas s/n/->").
# Se llama antes que pz_state, que en "cerrado" baja la orden de abrir.
VT_SKIP = lambda l: f'''
{l}:
    mov al, byte ptr [esi]
    test al, al
    jz vs_end
    inc esi
    cmp al, 0x20
    jne {l}
'''
vt_state = place('vt_state', f'''
    pushad
    cmp byte ptr [{PZ_ARM:#x}], 0
    je vs_end
    cmp dword ptr [edi], 0x20544f56
    jne vs_end
    lea esi, [edi + 4]
    mov ebx, {VT_SES:#x}
    xor ecx, ecx
    xor edx, edx
vs_ses:
    mov al, byte ptr [esi]
    test al, al
    jz vs_end
    inc esi
    cmp al, 0x20
    je vs_sesend
    cmp edx, 15
    jae vs_ses
    cmp al, byte ptr [ebx + edx]
    je vs_seseq
    mov byte ptr [ebx + edx], al
    mov cl, 1
vs_seseq:
    inc edx
    jmp vs_ses
vs_sesend:
    cmp byte ptr [ebx + edx], 0
    je vs_ses0
    mov byte ptr [ebx + edx], 0
    mov cl, 1
vs_ses0:
    test cl, cl
    jz vs_phase
    mov byte ptr [{VT_HAVE:#x}], 0
vs_phase:
    xor ebp, ebp
    cmp dword ptr [esi], 0x72726563
    jne vs_ph1
    cmp dword ptr [esi + 4], 0x206f6461
    jne vs_ph1
    inc ebp
{VT_SKIP('vs_ph1')}
{VT_SKIP('vs_auto')}
    xor edx, edx
vs_num:
    movzx eax, byte ptr [esi]
    test eax, eax
    jz vs_end
    inc esi
    cmp al, 0x20
    je vs_numend
    sub eax, 0x30
    imul edx, edx, 10
    add edx, eax
    jmp vs_num
vs_numend:
    cmp edx, dword ptr [{VT_RES:#x}]
    je vs_marks
    mov dword ptr [{VT_RES:#x}], edx
    call {vt_commit:#x}
vs_marks:
    xor ecx, ecx
    xor edx, edx
vs_mk:
    mov al, byte ptr [esi]
    inc esi
    cmp al, 0x73
    jne vs_mkn
    inc ecx
    jmp vs_mk
vs_mkn:
    cmp al, 0x6e
    jne vs_mkx
    inc edx
    jmp vs_mk
vs_mkx:
    cmp al, 0x2d
    je vs_mk
    mov eax, ecx
    or eax, edx
    jz vs_close
    mov word ptr [{VT_SI:#x}], cx
    mov word ptr [{VT_NO:#x}], dx
    mov byte ptr [{VT_HAVE:#x}], 1
vs_close:
    test ebp, ebp
    jz vs_end
    call {vt_commit:#x}
vs_end:
    popad
    ret
''')

# Vaciado de la tabla de sucesos (0x4988d0: partida nueva y fin de ronda): también la de votaciones.
vt_clear = place('vt_clear', f'''
    mov dword ptr [{VT_N:#x}], 0
    push ebx
    push esi
    xor si, si
    jmp 0x4988d5
''')

# Fin de ronda, 0x4989d0 (bx = renglones de la ronda): la cabecera cuenta también las votaciones...
vt_wcount = place('vt_wcount', f'''
    add bx, word ptr [{VT_N:#x}]
    mov ax, bx
    push 0
    mov word ptr [ebp - 0x14], bx
    jmp 0x498b4a
''')

# ... que se escriben antes que los sucesos.
vt_wrecs = place('vt_wrecs', f'''
    movsx eax, word ptr [{VT_N:#x}]
    test eax, eax
    jz vw_rest
    imul eax, eax, 0x1c
    push eax
    push {VT_TAB:#x}
    lea ecx, [ebp - 0x1b8]
    call 0x4dfd70
vw_rest:
    movsx eax, bx
    movsx ecx, word ptr [{VT_N:#x}]
    sub eax, ecx
    imul eax, eax, 0x1c
    lea ecx, [ebp - 0x378]
    push eax
    push ecx
    lea ecx, [ebp - 0x1b8]
    call 0x4dfd70
    jmp 0x498c0d
''')

# Informe, 0x499450: la ronda en curso mide también las votaciones (si = renglones de la tabla de sucesos)...
vt_rsize = place('vt_rsize', f'''
    add si, word ptr [{VT_N:#x}]
    imul si, si, 0x1c
    add si, 6
    jmp 0x499542
''')

# ... y las lleva primero (ebx = destino, edx = cantidad de la ronda, [ebp-0x14] = su tamaño).
vt_rfill = place('vt_rfill', f'''
    add ebx, 6
    movsx ecx, word ptr [{VT_N:#x}]
    test ecx, ecx
    jz vr_end
    add word ptr [edx], cx
    imul eax, ecx, 0x1c
    mov esi, dword ptr [ebp - 0x14]
    add word ptr [esi], ax
    imul ecx, ecx, 7
    mov esi, {VT_TAB:#x}
    mov edi, ebx
    rep movsd dword ptr es:[edi], dword ptr [esi]
    mov ebx, edi
vr_end:
    mov word ptr [ebp - 0xe], 0
    jmp 0x499641
''')

# Renglón del informe, 0x4b4110 (ebx = suceso, di = x, esi = y, texto en esp+0xc): el de la votación lleva el escudo
# del bando que la abrió, como los demás sucesos (0x4dd080(0x69 + bando, x, y)); sin bando (VT_NOBODY), solo el texto.
vt_line = place('vt_line', f'''
    cmp word ptr [ebx], {VT_TYPE:#x}
    je vl_vote
    movsx eax, di
    push esi
    push eax
    jmp 0x4b4147
vl_vote:
    movsx eax, word ptr [ebx + 2]
    cmp eax, 8
    jae vl_text
    add eax, 0x69
    movsx ecx, di
    push esi
    push ecx
    push eax
    call 0x4dd080
    add esp, 0xc
vl_text:
    movsx eax, word ptr [ebx + 0x18]
    push eax
    movsx eax, word ptr [ebx + 0x16]
    push eax
    push {vt_fmt:#x}
    lea eax, [esp + 0x18]
    push eax
    call dword ptr [0x5a9bec]
    add esp, 0x10
    movsx eax, di
    add eax, 0x14
    lea ecx, [esp + 0xc]
    push ecx
    push esi
    push eax
    call 0x4dd120
    add esp, 0xc
    jmp 0x4b41a0
''')

# Al guardar (0x439a00), antes de cerrar el archivo: la tabla al final.
vt_savef = place('vt_savef', f'''
    push ecx
    push {len(b'VOTA') + 4 + VT_MAX * 0x1c}
    push {vt_save:#x}
    call 0x4dfd70
    pop ecx
    jmp 0x4dfdc0
''')

# Al cargar (0x439e..), después de lo último que lee el original: la tabla, si está.
vt_loadf = place('vt_loadf', f'''
    mov dword ptr [{VT_N:#x}], 0
    push 4
    push {VT_MAGIC:#x}
    lea ecx, [ebp - 0x120]
    call 0x4dfd20
    cmp eax, 4
    jne vl_end
    cmp dword ptr [{VT_MAGIC:#x}], 0x41544f56
    jne vl_end
    push {4 + VT_MAX * 0x1c}
    push {VT_N:#x}
    lea ecx, [ebp - 0x120]
    call 0x4dfd20
    cmp eax, {4 + VT_MAX * 0x1c}
    jne vl_bad
    cmp dword ptr [{VT_N:#x}], {VT_MAX}
    jbe vl_end
vl_bad:
    mov dword ptr [{VT_N:#x}], 0
vl_end:
    push 0x564d08
    jmp 0x43a010
''')

# Aviso sin bloquear el juego (un MessageBox modal en el bucle principal frenaría la red): en un hilo aparte.
tl_warn = place('tl_warn', f'''
    mov eax, dword ptr [esp + 4]
    push 0x41030
    push {tl_caption:#x}
    push eax
    push 0
    call dword ptr [{MSGBOX:#x}]
    xor eax, eax
    ret 4
''')

# Mandar la orden de abrir (arg: herramienta). Solo el anfitrión; la copia local llega por el eco de 0x4dd3b0.
tl_sendopen = place('tl_sendopen', f'''
    call 0x4dd3a0
    test ax, ax
    jnz tso_end
    mov eax, dword ptr [esp + 4]
    mov dword ptr [{tl_openpkt:#x}], eax
    push 4
    push {tl_openpkt:#x}
    push {TL_OPEN:#x}
    call 0x4dd3b0
    add esp, 0xc
tso_end:
    ret
''')

# Recepción (reemplaza "ja 0x4b85bb" en 0x4b6a22; eax = tipo + 8, esi = paquete). Solo vale lo que manda la máquina 0.
tl_recv = place('tl_recv', f'''
    cmp eax, {TL_OPEN + 8:#x}
    je tr_open
    cmp eax, {TL_STATE + 8:#x}
    jne 0x4b85bb
    cmp word ptr [esi + 6], 0
    jne 0x4b85bb
    mov eax, dword ptr [esi + 0xc]
    cmp eax, {len(TOOLS)}
    jae 0x4b85bb
    mov byte ptr [eax + {TL_PEND_STATE:#x}], 1
    shl eax, 8
    lea edi, [eax + {tl_buf:#x}]
    xor edx, edx
tr_copy:
    mov al, byte ptr [esi + edx + 0x10]
    mov byte ptr [edi + edx], al
    test al, al
    jz tr_done
    inc edx
    cmp edx, 255
    jb tr_copy
    mov byte ptr [edi + edx], 0
tr_done:
    cmp edi, {tl_buf:#x}
    jne 0x4b85bb
    call {vt_state:#x}
    call {pz_state:#x}
    jmp 0x4b85bb
tr_open:
    cmp word ptr [esi + 6], 0
    jne 0x4b85bb
    mov eax, dword ptr [esi + 0xc]
    cmp eax, {len(TOOLS)}
    jae 0x4b85bb
    mov byte ptr [eax + {TL_PEND_OPEN:#x}], 1
    test eax, eax
    jnz 0x4b85bb
    call {vt_open:#x}
    call {pz_open:#x}
    jmp 0x4b85bb
''')

def tl_tool(t):
    p = lambda k: f'{tl_path[t, k]:#x}'
    fail_close = '' if t else f'''
    test ebx, ebx
    jnz to{t}_noclose
    push {len(pz_closepkt_data)}
    push {pz_closepkt:#x}
    push {TL_STATE:#x}
    call 0x4dd3b0
    add esp, 0xc
to{t}_noclose:'''
    return f'''
    cmp byte ptr [{TL_PEND_OPEN + t:#x}], 0
    je to{t}_end
    mov byte ptr [{TL_PEND_OPEN + t:#x}], 0
    push {p('ver')}
    call dword ptr [{DELF:#x}]
    push {p('op')}
    call dword ptr [{DELF:#x}]
    push {p('env')}
    call dword ptr [{DELF:#x}]
    call 0x4dd3a0
    movzx ebx, ax
    mov esi, {p('op_cmd')}
    test ebx, ebx
    jz to{t}_run
    mov esi, {p('sp_cmd')}
    xor ecx, ecx
to{t}_mask:
    imul edx, ecx, {SIDE:#x}
    mov al, 0x30
    cmp byte ptr [edx + {SIDE_ON:#x}], 0
    je to{t}_put
    cmp word ptr [edx + {SIDE_HUMAN:#x}], -1
    jne to{t}_put
    movzx edi, byte ptr [edx + {SIDE_MACHINE:#x}]
    cmp edi, ebx
    jne to{t}_put
    mov al, 0x31
to{t}_put:
    mov byte ptr [ecx + {p('mask')}], al
    inc ecx
    cmp ecx, 8
    jb to{t}_mask
to{t}_run:
    push {tl_pi:#x}
    push {tl_si:#x}
    push 0
    push 0
    push 0
    push 0
    push 0
    push 0
    push esi
    push {p('exe')}
    call dword ptr [{CREATEPROC:#x}]
    test eax, eax
    jz to{t}_fail
    push dword ptr [{tl_pi:#x}]
    call dword ptr [{CLOSEH:#x}]
    push dword ptr [{tl_pi + 4:#x}]
    call dword ptr [{CLOSEH:#x}]
    jmp to{t}_end
to{t}_fail:
    {fail_close}
    push 0
    push 0
    push {p('err')}
    push {tl_warn:#x}
    push 0
    push 0
    call dword ptr [{CREATETH:#x}]
    test eax, eax
    jz to{t}_end
    push eax
    call dword ptr [{CLOSEH:#x}]
to{t}_end:

    call 0x4dd3a0
    test ax, ax
    jnz tf{t}_end
    push {p('env')}
    call dword ptr [{DELF:#x}]
    push {p('env')}
    push {p('op')}
    call dword ptr [{MOVEF:#x}]
    test eax, eax
    jz tf{t}_end
    push 0
    push 0
    push 3
    push 0
    push 1
    push 0x80000000
    push {p('env')}
    call dword ptr [{CREATEF:#x}]
    cmp eax, -1
    je tf{t}_del
    mov esi, eax
    mov dword ptr [{tl_n:#x}], 0
    push 0
    push {tl_n:#x}
    push 255
    push {tl_pkt + 4:#x}
    push esi
    call dword ptr [{READF:#x}]
    push esi
    call dword ptr [{CLOSEH:#x}]
    mov eax, dword ptr [{tl_n:#x}]
    cmp eax, 255
    jbe tf{t}_len
    mov eax, 255
tf{t}_len:
    mov byte ptr [eax + {tl_pkt + 4:#x}], 0
    mov dword ptr [{tl_pkt:#x}], {t}
    push 260
    push {tl_pkt:#x}
    push {TL_STATE:#x}
    call 0x4dd3b0
    add esp, 0xc
tf{t}_del:
    push {p('env')}
    call dword ptr [{DELF:#x}]
tf{t}_end:

    cmp byte ptr [{TL_PEND_STATE + t:#x}], 0
    je ts{t}_end
    push 0
    push 0x80
    push 2
    push 0
    push 0
    push 0x40000000
    push {p('vtmp')}
    call dword ptr [{CREATEF:#x}]
    cmp eax, -1
    je ts{t}_end
    mov esi, eax
    push {tl_buf + 256 * t:#x}
    call dword ptr [{STRLEN:#x}]
    add esp, 4
    push 0
    push {tl_n:#x}
    push eax
    push {tl_buf + 256 * t:#x}
    push esi
    call dword ptr [{WRITEF:#x}]
    push esi
    call dword ptr [{CLOSEH:#x}]
    push {p('ver')}
    call dword ptr [{DELF:#x}]
    push {p('ver')}
    push {p('vtmp')}
    call dword ptr [{MOVEF:#x}]
    test eax, eax
    jz ts{t}_end
    mov byte ptr [{TL_PEND_STATE + t:#x}], 0
ts{t}_end:
'''

# Cada ~250 ms, en la función ociosa 0x4dea40 (la llaman el bucle principal y los bucles de los diálogos): abrir lo
# pedido, mandar el estado del operador (anfitrión) y dejar el recibido para el espectador. Si el .ver está abierto
# por el programa y no se puede reemplazar, se reintenta en la vuelta siguiente.
tl_idle = place('tl_idle', f'''
    pushad
    call {pz_tick:#x}
    cmp byte ptr [{TL_BUSY:#x}], 0
    jne ti_done
    call dword ptr [{GETTICK:#x}]
    mov edx, eax
    sub eax, dword ptr [{TL_TICK:#x}]
    cmp eax, 250
    jb ti_done
    mov dword ptr [{TL_TICK:#x}], edx
    mov byte ptr [{TL_BUSY:#x}], 1
    {''.join(tl_tool(t) for t in range(len(TOOLS)))}
    {PZ_SLOW}
    mov byte ptr [{TL_BUSY:#x}], 0
ti_done:
    popad
    mov ecx, 0x5a6f50
    jmp 0x4dea45
''')

# Menú de partida, al abrirse (0x4bce20, que habilita o deshabilita cada línea con 0x4dcec0): la zona de "Votacion"
# también. Sin esto el control queda como sin mostrar y la búsqueda de 0x4d95d0 no lo encuentra: ni se resalta ni
# responde al clic. Habilitada en el anfitrión, deshabilitada en las demás PC.
tl_menuinit = place('tl_menuinit', f'''
    call 0x4dd3a0
    xor ecx, ecx
    test ax, ax
    jz tmi_set
    mov ecx, 2
tmi_set:
    push ecx
    push {VOTE_HOT:#x}
    call 0x4dcec0
    add esp, 8
    push ebx
    mov ecx, 0x5032f8
    jmp 0x4bce26
''')

# Menú de partida (0x4bd180, fin en 0x4bd512): texto y color de "Votacion". esi = control bajo el puntero;
# [esp + 0xc] = escribir los textos. Gris (0x56) fuera del anfitrión.
tl_menu = place('tl_menu', f'''
    cmp dword ptr [esp + 0xc], 0
    je tm_col
    push {tl_voting:#x}
    push {VOTE_TXT:#x}
    call 0x4dd240
    add esp, 8
tm_col:
    push 0
    push 0
    call 0x4dd3a0
    mov ecx, 0x56
    test ax, ax
    jnz tm_set
    mov ecx, 0x5c
    cmp esi, {VOTE_HOT:#x}
    jne tm_set
    mov ecx, 0xf
tm_set:
    push ecx
    push {VOTE_TXT:#x}
    call 0x4dd2b0
    add esp, 0x10
    mov ecx, 0x588bd0
    call 0x4d7f60
    jmp 0x4bd51c
''')

# Despachador del menú (0x4bd520, eax = control).
tl_disp = place('tl_disp', f'''
    cmp eax, {VOTE_HOT:#x}
    je td_vote
    sub eax, 0xb
    cmp eax, 0xd
    ja 0x4bd533
    jmp 0x4bd52c
td_vote:
    mov ecx, 0x588bd0
    call 0x4d7d70
    push 0
    call {tl_sendopen:#x}
    add esp, 4
    ret
''')

# Pantalla de preparación (diálogo 7): el botón de Sorteo se muestra al iniciarla, deshabilitada fuera del anfitrión, y el
# clic (ebp = control; los mayores que 96 caen en "ja 0x46ed83") manda abrir el Sorteo.
tl_setinit = place('tl_setinit', f'''
    call 0x4dd3a0
    xor ecx, ecx
    test ax, ax
    jz tsi_show
    mov ecx, 2
tsi_show:
    push ecx
    push {COIN}
    call 0x4dcec0
    add esp, 8
    mov ecx, 0x588bd0
    call 0x4d7f60
    jmp 0x46f34b
''')
tl_setclick = place('tl_setclick', f'''
    cmp ebp, {COIN}
    jne 0x46ed83
    push 1
    call {tl_sendopen:#x}
    add esp, 4
    jmp 0x46ed83
''')

blob = b''.join(caves.values())
raw_size = (len(blob) + FILE_ALIGN - 1) // FILE_ALIGN * FILE_ALIGN
exe += blob + b'\0' * (raw_size - len(blob))

struct.pack_into('<8sIIIIIIHHI', exe, hdr, b'.avis\0\0\0', len(blob), new_va, raw_size, new_raw,
                 0, 0, 0, 0, 0xE0000020)   # código + lectura + escritura (br_xy)
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
patch(0x4a2c24, rel(0x4a2c24, 8), asm(f'jmp {armab:#x}', 0x4a2c24))
patch(0x45a049, asm('call 0x45aa80', 0x45a049), asm(f'call {fldraw:#x}', 0x45a049))
patch(0x4a2cb6, asm('call 0x4dd260', 0x4a2cb6), asm(f'call {altitle:#x}', 0x4a2cb6))
assert rel(0x457200, 2) == asm('je 0x457214', 0x457200)
patch(0x4571f8, bytes.fromhex('6683e20f6683fa08'), asm(f'jmp {fldirty:#x}', 0x4571f8))
for va in (0x4a979e, 0x4ab7c5):
    patch(va, asm('push 0x4f90b4', va), asm(f'push {ver_str:#x}', va))
patch(0x49e48b, rel(0x49e48b, 0x49e49a - 0x49e48b), asm(f'jmp {stepcap:#x}', 0x49e48b))
assert rel(0x49e49a, 2) == bytes.fromhex('3bca')
assert rel(0x49e4a7, 7) == bytes.fromhex('5756e8c2020000')
patch(0x49e4a7, rel(0x49e4a7, 7), asm(f'jmp {landcap:#x}', 0x49e4a7))
for va, orig, stub in mv_stubs:     # tope de pasos del barco (ver bmvcap)
    patch(va, asm(orig, va), asm(f'call {stub:#x}', va))
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
patch(0x4a5328, bytes.fromhex('5d5f5e5b83c414c3'), asm(f'jmp {cabgraph:#x}', 0x4a5328))
# Convoy (ver crlink, crfollow, crdef, crdraw).
assert rel(0x49d062, 2) == bytes.fromhex('6a05')
patch(0x49d05d, asm('movsx ax, byte ptr [esi + 2]', 0x49d05d), asm(f'jmp {crlink:#x}', 0x49d05d))
assert rel(0x49cdc2, 5) == asm('call 0x49db70', 0x49cdc2)
patch(0x49cdc7, bytes.fromhex('83c414') + asm('mov cx, word ptr [esi + 6]', 0x49cdca), asm(f'jmp {crfollow:#x}', 0x49cdc7))
assert rel(0x464c3d, 0x464c51 - 0x464c3d) == asm('lea eax, [esp + 0x30]; push eax; push edi; push esi; call 0x4411b0; '
                                                 'mov word ptr [esp + 0x1e], ax; add esp, 0xc', 0x464c3d)
patch(0x464c3d, rel(0x464c3d, 0x464c51 - 0x464c3d), asm(f'jmp {crdef:#x}', 0x464c3d))
patch(0x459d0d, asm('call 0x4dd530', 0x459d0d), asm(f'call {crdraw:#x}', 0x459d0d))
# Puentes: derribar y reconstruir (ver br_* arriba).
for va in (0x4205c1, 0x41c98c, 0x44c2d7, 0x4b05d1):
    patch(va, asm('call 0x440b30', va), asm(f'call {br_razelk:#x}', va))
for va in (0x42053f, 0x41caab):
    patch(va, asm('call 0x440b30', va), asm(f'call {br_rebuildlk:#x}', va))
for va in (0x4b0a1c, 0x4b0a28):
    patch(va, bytes.fromhex('5d5f5e5b83c414c3'), asm(f'jmp {br_menu:#x}', va))
assert rel(0x495540, 1) == b'\x50' and rel(0x495541, 2) == bytes.fromhex('6a00')
patch(0x495530, rel(0x495530, 0x495541 - 0x495530), asm(f'jmp {br_razetxt:#x}', 0x495530))
patch(0x4954e1, asm('push 0x99', 0x4954e1), asm(f'jmp {br_razepic:#x}', 0x4954e1))
patch(0x495288, bytes.fromhex('66a178275700') + b'\x50' + asm('call 0x4955d0', 0x49528f),
      asm(f'jmp {br_razebtn:#x}', 0x495288))
patch(0x4d5e30, bytes.fromhex('83ec505657'), asm(f'jmp {br_razeapply:#x}', 0x4d5e30))
assert rel(0x4d5eda, 5) == bytes.fromhex('b980985800') and rel(0x4d5f3a, 5) == asm('call 0x4a4f20', 0x4d5f3a)
patch(0x4b6160, bytes.fromhex('668b442404'), asm(f'jmp {br_rebdlg:#x}', 0x4b6160))
assert rel(0x4b6180, 2) == bytes.fromhex('6a00')
patch(0x4b64a0, bytes.fromhex('837c240404'), asm(f'jmp {br_rebdraw:#x}', 0x4b64a0))
assert rel(0x4b64a7, 4) == bytes.fromhex('8b44240c') and rel(0x4b64e3, 1) == b'\xc3'
patch(0x4b64f0, rel(0x4b64f0, 0x4b650c - 0x4b64f0), asm(f'jmp {br_rebtxt:#x}', 0x4b64f0))
assert rel(0x4b650c, 1) == b'\x50'
patch(0x4b65e5, bytes.fromhex('668b3510955600'), asm(f'jmp {br_cost:#x}', 0x4b65e5))
patch(0x4b6610, b'\x56' + asm('call 0x4a2170', 0x4b6611), asm(f'jmp {br_rebapply:#x}', 0x4b6610))
patch(0x45846d, bytes.fromhex('66f7c5001c66892f7408668b41086689470e'),
      asm(f'jmp {br_vfill:#x}', 0x45846d))
patch(0x459a9f, bytes.fromhex('668b0680e41c80fc04754b'), asm(f'jmp {br_vdraw:#x}', 0x459a9f))
patch(0x467ba3, asm('lea eax, [esp + 0x4c]; push 0x4fc808', 0x467ba3), asm(f'jmp {bridgecb:#x}', 0x467ba3))
# Misión "derribar un puente" (qb_*)
patch(0x460dfb, bytes.fromhex('6685ff0f8e9c010000'), asm(f'jmp {qb_gen:#x}', 0x460dfb))
patch(0x461336, bytes.fromhex('516a42b980985800e8eddb0700'), asm(f'jmp {qb_name:#x}', 0x461336))
patch(0x461876, bytes.fromhex('0fbf47068d048003c08d0c408d0489'), asm(f'jmp {qb_text:#x}', 0x461876))
patch(0x461c80, bytes.fromhex('0fbf46068d048003c08d144080bc924bad550000740d'), asm(f'jmp {qb_fail:#x}', 0x461c80))
patch(0x436178, bytes.fromhex('0fbfc766bd01008d048003c08d0c40668b9489b6ac55008d0489668b80b8ac5500'),
      asm(f'jmp {qb_ailoc1:#x}', 0x436178))
patch(0x436442, bytes.fromhex('66890b0fbfc98d0c8903c98d1c49668bbc9bb6ac55008d0c9b66893e5f668b89b8ac55005e66890a5bc3'),
      asm(f'jmp {qb_ailoc2:#x}', 0x436442))
patch(0x40d963, bytes.fromhex('0fbf4424128d048003c08d0c408d048905baac5500'), asm(f'jmp {ai_brname:#x}', 0x40d963))
patch(0x40d450, bytes.fromhex('83ec04a1d4205000'), asm(f'jmp {ai_brq:#x}', 0x40d450))
assert rel(0x435d79, 7) == asm('mov cx, word ptr [0x4fb0ec]', 0x435d79)
patch(0x435d53, rel(0x435d53, 0x435d79 - 0x435d53), asm(f'jmp {qb_ailoc3:#x}', 0x435d53))
assert rel(0x4c4d41, 2) == bytes.fromhex('8bc8')   # mov ecx, eax
patch(0x4c4d3a, asm('movsx eax, word ptr [0x4fb0ec]', 0x4c4d3a), asm(f'call {ai_brraze:#x}', 0x4c4d3a))
patch(0x4c4bce, asm('call 0x49c4b0', 0x4c4bce), asm(f'call {ai_move:#x}', 0x4c4bce))
# La IA reconstruye puentes (meta 9: ai_brrebev, ai_brreb, ai_brname9*)
patch(0x41e4eb, asm('cmp word ptr [esp + 0x1c], -1; je 0x41e563', 0x41e4eb), asm(f'jmp {ai_brrebev:#x}', 0x41e4eb))
patch(0x40dbf0, bytes.fromhex('83ec04a1d4205000'), asm(f'jmp {ai_brreb:#x}', 0x40dbf0))
patch(0x40ce24, asm('movsx eax, word ptr [esp + 0x1e]; lea edx, [eax + eax*8]; lea eax, [eax + edx*4];'
                    'lea ecx, [eax + eax*2]; lea edx, [ecx*2 + 0x537e30]', 0x40ce24),
      asm(f'jmp {ai_brname9:#x}', 0x40ce24))
patch(0x41f30c, asm('mov si, word ptr [0x5032e6]; movsx eax, si; lea edx, [eax + eax*8]; lea eax, [eax + edx*4];'
                    'lea ecx, [eax + eax*2]; lea edx, [ecx*2 + 0x537e30]', 0x41f30c),
      asm(f'jmp {ai_brname9s:#x}', 0x41f30c))
# Botones de Votación y Sorteo (tl_*)
patch(0x4bce20, asm('push ebx; mov ecx, 0x5032f8', 0x4bce20), asm(f'jmp {tl_menuinit:#x}', 0x4bce20))
patch(0x4bd512, asm('mov ecx, 0x588bd0; call 0x4d7f60', 0x4bd512), asm(f'jmp {tl_menu:#x}', 0x4bd512))
assert rel(0x4bd51c, 3) == bytes.fromhex('5e5bc3') and rel(0x4bd520, 4) == bytes.fromhex('8b442404')
patch(0x4bd524, asm('sub eax, 0xb; cmp eax, 0xd; ja 0x4bd533', 0x4bd524), asm(f'jmp {tl_disp:#x}', 0x4bd524))
patch(0x46f341, asm('mov ecx, 0x588bd0; call 0x4d7f60', 0x46f341), asm(f'jmp {tl_setinit:#x}', 0x46f341))
assert rel(0x46f34b, 4) == bytes.fromhex('5d5f5e5b')
assert rel(0x46e889, 9) == bytes.fromhex('8b6e048d45ff83f85f')
patch(0x46e892, asm('ja 0x46ed83', 0x46e892), asm(f'ja {tl_setclick:#x}', 0x46e892))
assert rel(0x46ed83, 7) == bytes.fromhex('6633c05d5f5e5b')
assert rel(0x4b6a16, 12) == bytes.fromhex('0fbf460483c0083d11020000')
patch(0x4b6a22, asm('ja 0x4b85bb', 0x4b6a22), asm(f'ja {tl_recv:#x}', 0x4b6a22))
assert rel(0x4b85bb, 9) == bytes.fromhex('5f5e81c408010000c3')
patch(0x4dea40, asm('mov ecx, 0x5a6f50', 0x4dea40), asm(f'jmp {tl_idle:#x}', 0x4dea40))
assert rel(0x4dd3a0, 7) == bytes.fromhex('66a1fc995800c3')
# Pausa mientras se vota (pz_*)
for va, op in ((0x417652, 'ff15'), (0x417847, 'ff15'), (0x4790c9, '8b1d'), (0x4de957, '8b3d'), (0x4dea0c, 'ff15'),
               (0x4e5db8, '8b1d')):
    patch(va, bytes.fromhex(op) + struct.pack('<I', DISPATCH), bytes.fromhex(op) + struct.pack('<I', pz_dptr))
patch(0x4c0fe0, bytes.fromhex('f6058fc35300f8'), asm(f'jmp {pz_chk[0x4c0fe0]:#x}', 0x4c0fe0))
patch(0x4c10c0, bytes.fromhex('803da0f74f0000'), asm(f'jmp {pz_chk[0x4c10c0]:#x}', 0x4c10c0))
patch(0x4c1250, bytes.fromhex('803da0f74f0000'), asm(f'jmp {pz_chk[0x4c1250]:#x}', 0x4c1250))
assert rel(0x4c2790, 7) == bytes.fromhex('5333c05633d257') and rel(0x4e33c0, 2) == bytes.fromhex('ff25')
# Resultado de la votación en el Events Report (vt_*)
patch(0x4988d0, bytes.fromhex('53566633f6'), asm(f'jmp {vt_clear:#x}', 0x4988d0))
patch(0x498b41, bytes.fromhex('668bc36a0066895dec'), asm(f'jmp {vt_wcount:#x}', 0x498b41))
patch(0x498bed, bytes.fromhex('0fbfc38bc8c1e0032bc18d8d88fcffffc1e00250518d8d48feffff') + asm('call 0x4dfd70', 0x498c08),
      asm(f'jmp {vt_wrecs:#x}', 0x498bed))
assert rel(0x498c0d, 0x10) == asm('lea ecx, [ebp - 0x1b8]; call 0x4dfdc0; call 0x4988d0', 0x498c0d)
patch(0x49953a, asm('imul si, si, 0x1c; add si, 6', 0x49953a), asm(f'jmp {vt_rsize:#x}', 0x49953a))
patch(0x499638, asm('add ebx, 6; mov word ptr [ebp - 0xe], 0', 0x499638), asm(f'jmp {vt_rfill:#x}', 0x499638))
patch(0x4b4142, asm('movsx eax, di; push esi; push eax', 0x4b4142), asm(f'jmp {vt_line:#x}', 0x4b4142))
assert rel(0x4b415e, 9) == asm('cmp eax, 0x12; ja 0x4b4790', 0x4b415e) and rel(0x4b41a0, 7) == bytes.fromhex('5f5e5b83c474c3')
assert rel(0x439c84, 6) == asm('lea ecx, [ebp - 0x12c]', 0x439c84)
patch(0x439c8a, asm('call 0x4dfdc0', 0x439c8a), asm(f'call {vt_savef:#x}', 0x439c8a))
assert rel(0x439fdc, 6) == asm('lea ecx, [ebp - 0x120]', 0x439fdc)
patch(0x43a00b, asm('push 0x564d08', 0x43a00b), asm(f'jmp {vt_loadf:#x}', 0x43a00b))
assert rel(0x43a010, 5) == asm('call 0x446060', 0x43a010)

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

# Diálogo 35 (menú de partida): línea nueva "Votacion" (texto VOTE_TXT, zona VOTE_HOT) debajo de Chat Mode. Las 13
# líneas pasan a 16 píxeles entre sí (de 46 a 238; el marco deja libre de 40 a 262); cada zona de clic, 4 píxeles
# por encima de su texto y de 16 de alto, conserva su x y su ancho.
r35 = records(res, 35)
MENU = [(1, 0xb), (2, 0xc), ('new', 'new'), (0x15, 0x16), (3, 0xd), (4, 0xe), (5, 0xf), (6, 0x10), (7, 0x11),
        (8, 0x12), (9, 0x13), (0x17, 0x18), (10, 0x14)]
assert sorted(i for pair in MENU if pair[0] != 'new' for i in pair) == sorted(r35)
p, t = r35[2]; assert t == 0x13
vtxt = bytearray(res[p:p + 4 + SZ[0x13]])
struct.pack_into('<I', vtxt, 4, VOTE_TXT)
p, t = r35[0xc]; assert t == 3
vhot = bytearray(res[p:p + 4 + SZ[3]])
struct.pack_into('<I', vhot, 4, VOTE_HOT)
for k, (ti, hi) in enumerate(MENU):
    y = 46 + 16 * k
    buf, o = (vtxt, 0) if ti == 'new' else (res, r35[ti][0])
    struct.pack_into('<I', buf, o + 0xc, y)
    buf, o = (vhot, 0) if hi == 'new' else (res, r35[hi][0])
    struct.pack_into('<I', buf, o + 0xc, y - 4)
    struct.pack_into('<I', buf, o + 0x1c, 16)
new_list[35] = [vtxt, vhot]

# Diálogo 7 (preparación): botón COIN clonado de Chat (id 80, butt_std en (436,80)), en SORTEO_X/Y y de
# SORTEO_W x SORTEO_H; su dibujo es el ícono de Sorteo, en (0,0) de la hoja SORTEO_FILE (más abajo).
r7 = records(res, 7)
assert max(r7) == COIN - 1
p, t = r7[80]; assert t == 1
coin = bytearray(res[p:p + 4 + SZ[1]])
assert struct.unpack_from('<11I', coin, 0) == (1, 80, 6, 453, 1, 1, 0x79, 436, 80, 20, 20)
struct.pack_into('<IIII', coin, 4, COIN, SORTEO_X, SORTEO_Y, 1)
struct.pack_into('<5I', coin, 0x18, SORTEO_FILE, 0, 0, SORTEO_W, SORTEO_H)
setstr(coin, 0x30, 16, 'Draw Lots')
setstr(coin, 0x40, 64, 'Draw lots for the starting order')
new_list[7] = [coin]

for did in (115, 35, 9, 7):   # de atrás para adelante: agregar a uno no corre el offset de los anteriores
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

# Tablas de archivos (tipo 2, registros de 60 bytes) y de imágenes (tipo 4, de 32): el juego las carga enteras al
# arrancar (0x4e4910 y 0x4eeb50), del registro 1 hasta la cantidad del encabezado, leyendo cada uno por su posición.
# Se agrega el archivo RAM_FILE = ARMY\orcs_ram.pcx, con los campos de lightinf (46, el retrato de unidad), y la imagen
# RAM_IMG = su retrato de 128x160 en (0,0), como la 63 sobre lightinf. Los ids son la posición: van al final.
def table(d, typ):
    o = 8
    while o + 20 <= len(d):
        h = struct.unpack_from('<5I', d, o)
        if h[0] == typ and h[1] == 0: return o, h
        o += 20 + h[4]
    raise KeyError(typ)

def table_add(d, typ, rid, rec):
    o, h = table(d, typ)
    assert h[2] == rid and h[3] == len(rec) and h[4] == h[2] * h[3], (typ, h)
    d[o + 20 + h[4]:o + 20 + h[4]] = rec
    struct.pack_into('<III', d, o + 8, h[2] + 1, h[3], h[4] + len(rec))

o2, _ = table(res, 2)
lightinf = bytes(res[o2 + 20 + 46 * 60:o2 + 20 + 47 * 60])
assert lightinf[4:13] == b'lightinf\0' and struct.unpack_from('<6I', lightinf, 36) == (2, 1, 0, 0, 0, 6)
o4, _ = table(res, 4)
assert struct.unpack_from('<8i', res, o4 + 20 + 63 * 32) == (63, 46, 0, 0, 0, 0, 128, 160)
assert struct.unpack_from('<8i', res, o4 + 20 + 0x99 * 32)[6:] == (128, 160)
ram = bytearray(lightinf)
struct.pack_into('<I', ram, 0, RAM_FILE)
setstr(ram, 4, 32, 'orcs_ram')
table_add(res, 4, RAM_IMG, struct.pack('<8i', RAM_IMG, RAM_FILE, 0, 0, 0, 0, 128, 160))   # la 4 va después de la 2
table_add(res, 2, RAM_FILE, bytes(ram))

# Hoja SORTEO_FILE = SETS\Fantasy\sorteo.pcx, con los campos de butt_std (0x79; el 16 es la carpeta del set): el
# dibujo del botón de Sorteo, de SORTEO_W x SORTEO_H. Un botón usa cuatro cuadros de su tamaño, uno debajo del otro:
# normal, apretado, deshabilitado y con el puntero encima (así están también los de 32x33 de BUTT_STD.PCX). El índice
# 11 (magenta) es transparente: el fondo de esos botones. Cada cuadro lleva el ícono del programa Sorteo
# (sorteo_icono.png: el de 64x64 de su assets\icono.ico, recortado a lo dibujado) a 1 píxel del borde: apretado,
# corrido un píxel abajo a la derecha y con contorno naranja (71, el aro de los botones apretados de BUTT_STD); con el
# puntero encima, con el contorno; deshabilitado, oscurecido. Los colores salen de la paleta de BUTT_STD.PCX (la misma
# de la pantalla de preparación), solo entre los que ya usan BUTT_STD y SetupScr.
from PIL import Image, ImageFilter
SRC_BUTT = r'C:\Warlords3\SETS\Fantasy\BUTT_STD.PCX'
butt = Image.open(SRC_BUTT)
assert butt.mode == 'P' and butt.size == (472, 224)
pal = butt.getpalette()[:768]
assert Image.open(r'C:\Warlords3\PICTS\SetupScr.pcx').getpalette()[:768] == pal
assert butt.getpixel((272, 0)) == 11 and pal[33:36] == [255, 0, 255]   # fondo transparente de los botones 32x33
assert butt.getpixel((436 + 8, 20 + 3)) == 71                          # el aro naranja de la moneda apretada
usables = sorted((set(butt.getdata()) | set(Image.open(r'C:\Warlords3\PICTS\SetupScr.pcx').getdata())) - {11})
def cercano(rgb, _memo={}):
    if rgb not in _memo:
        _memo[rgb] = min(usables, key=lambda i: sum((pal[3 * i + k] - rgb[k]) ** 2 for k in range(3)))
    return _memo[rgb]
icono = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sorteo_icono.png')).convert('RGBA')
assert icono.size == (SORTEO_W - 2, SORTEO_H - 2)
hoja = Image.new('P', (SORTEO_W, 4 * SORTEO_H), 11)
hoja.putpalette(butt.getpalette())
for fila, (dx, oscuro, aro) in enumerate(((1, False, False), (2, False, True), (1, True, False), (1, False, True))):
    y0 = fila * SORTEO_H
    lleno = set()
    for y in range(icono.height):
        for x in range(icono.width):
            r, g, b_, a_ = icono.getpixel((x, y))
            if a_ < 128 or not (0 <= x + dx < SORTEO_W and 0 <= y + dx < SORTEO_H): continue
            if oscuro: r, g, b_ = r * 3 // 10, g * 3 // 10, b_ * 3 // 10
            hoja.putpixel((x + dx, y0 + y + dx), cercano((r, g, b_))); lleno.add((x + dx, y + dx))
    if aro:
        for x, y in {(x + i, y + j) for x, y in lleno for i in (-1, 0, 1) for j in (-1, 0, 1)} - lleno:
            if 0 <= x < SORTEO_W and 0 <= y < SORTEO_H: hoja.putpixel((x, y0 + y), 71)
import io
pcx = io.BytesIO(); hoja.save(pcx, 'PCX'); SORTEO_PCX = pcx.getvalue()
o2, _ = table(res, 2)
butt_std = bytearray(res[o2 + 20 + 0x79 * 60:o2 + 20 + 0x7a * 60])
assert butt_std[4:13] == b'butt_std\0' and struct.unpack_from('<6I', butt_std, 36) == (16, 1, 0, 0, 0, 0)
struct.pack_into('<I', butt_std, 0, SORTEO_FILE)
setstr(butt_std, 4, 32, 'sorteo')
table_add(res, 2, SORTEO_FILE, bytes(butt_std))

# Título del menú principal: la imagen titulo.pcx ("Era de Alianzas" dorado sobre blanco) va pintada en el fondo, en
# lugar del texto del control 19 (que queda vacío). El fondo es el archivo 1 (picts\startup, 640x480, por la pantalla
# 1 de la tabla tipo 5) o, a 800x600 y 1024x768, el 138 o el 139 (0x4aab9a), con el diálogo corrido (80,60) o
# (192,144); el marco es el mismo en los tres, en esa posición. Las tres copias nuevas (picts\startav*) llevan el
# título centrado sobre el marco (x 322 del diálogo) y arriba (y 3), donde iba el texto, de 60 de alto (el marco
# empieza en y 67). El dorado es un degradé vertical (amarillo pálido arriba, naranja abajo) sobre blanco (254): el
# color lleno de cada fila es la mediana del interior de las letras (erosionado 5x5), interpolada entre filas; la
# transparencia de un píxel es cuánto avanza de blanco hacia ese color, y su color, despejado de la mezcla con
# blanco. Se mezcla con el fondo y se lleva al color más cercano entre los que ya usan los tres fondos (comparten
# paleta).
TITULO = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'titulo.pcx')).convert('RGB')
TIT_H, TIT_X, TIT_Y, TIT_W = 60, 322, 3, (254, 254, 254)
STARTUP = [(1, 'startup', 'startav', (0, 0)), (138, 'startup1', 'startav1', (80, 60)), (139, 'startup2', 'startav2', (192, 144))]
fondos = {n: Image.open(os.path.join(r'C:\Warlords3\PICTS', n + '.pcx')) for _, n, _, _ in STARTUP}
st_pal = fondos['startup'].getpalette()[:768]
assert all(f.mode == 'P' and f.getpalette()[:768] == st_pal for f in fondos.values())
def st_difs(n, ox, oy):   # píxeles del marco de 640 que difieren en el fondo n corrido (ox,oy)
    return sum(x != y for x, y in zip(fondos['startup'].crop((175, 67, 469, 467)).tobytes(), fondos[n].crop((ox + 175, oy + 67, ox + 469, oy + 467)).tobytes()))
for _, n, _, (ox, oy) in STARTUP[1:]:   # el marco, en el mismo lugar del diálogo en los tres (no idéntico: ~8% difiere)
    assert st_difs(n, ox, oy) * 4 < min(st_difs(n, ox + dx, oy + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
st_usables = sorted(set().union(*(set(f.get_flattened_data()) for f in fondos.values())))
_st_memo = {}
def st_cercano(rgb):
    if rgb not in _st_memo:
        _st_memo[rgb] = min(st_usables, key=lambda i: sum((st_pal[3 * i + k] - rgb[k]) ** 2 for k in range(3)))
    return _st_memo[rgb]
tit = TITULO
assert all(tit.getpixel(p) == TIT_W for p in ((0, 0), (tit.width - 1, 0), (0, tit.height - 1), (tit.width - 1, tit.height - 1)))
tit_tinta = Image.new('L', tit.size)
tit_tinta.putdata([255 if min(c) < 230 else 0 for c in tit.get_flattened_data()])
tit_int = tit_tinta.filter(ImageFilter.MinFilter(5))
tit_fila = {}
for y in range(tit.height):
    cs = [tit.getpixel((x, y)) for x in range(tit.width) if tit_int.getpixel((x, y))]
    if len(cs) >= 3: tit_fila[y] = tuple(sorted(c[k] for c in cs)[len(cs) // 2] for k in range(3))
tit_ys = sorted(tit_fila)
assert len(tit_ys) > tit.height // 2
def tit_color(y):
    if y <= tit_ys[0]: return tit_fila[tit_ys[0]]
    if y >= tit_ys[-1]: return tit_fila[tit_ys[-1]]
    a_, b_ = max(k for k in tit_ys if k <= y), min(k for k in tit_ys if k >= y)
    t = (y - a_) / (b_ - a_) if b_ > a_ else 0
    return tuple(tit_fila[a_][k] + (tit_fila[b_][k] - tit_fila[a_][k]) * t for k in range(3))
tit_a = Image.new('RGBA', tit.size)
for y in range(tit.height):
    d = [TIT_W[k] - v for k, v in enumerate(tit_color(y))]; dd = sum(v * v for v in d)
    for x in range(tit.width):
        p_ = tit.getpixel((x, y))
        a_ = max(0.0, min(1.0, sum((TIT_W[k] - p_[k]) * d[k] for k in range(3)) / dd))
        if a_ < 0.03: continue
        c_ = p_ if a_ > 0.97 else tuple(max(0, min(255, round((p_[k] - (1 - a_) * TIT_W[k]) / a_))) for k in range(3))
        tit_a.putpixel((x, y), c_ + (round(a_ * 255),))
tit_a = tit_a.crop(tit_a.getbbox())
tit_a = tit_a.resize((round(tit_a.width * TIT_H / tit_a.height), TIT_H), Image.LANCZOS)
assert TIT_Y + TIT_H < 67
NUEVOS_TIT = {}
o2, _ = table(res, 2)
for fid, viejo, nuevo, (ox, oy) in STARTUP:
    p = o2 + 20 + fid * 60
    assert struct.unpack_from('<I', res, p)[0] == fid and res[p + 4:p + 36].split(b'\0')[0] == b'picts\\' + viejo.encode()
    setstr(res, p + 4, 32, 'picts\\' + nuevo)
    f = fondos[viejo].copy(); rgb = f.convert('RGB')
    x0, y0 = ox + TIT_X - tit_a.width // 2, oy + TIT_Y
    for y in range(tit_a.height):
        for x in range(tit_a.width):
            r, g, b_, a_ = tit_a.getpixel((x, y))
            if a_:
                fr = rgb.getpixel((x0 + x, y0 + y))
                f.putpixel((x0 + x, y0 + y), st_cercano(tuple(round((v * a_ + w * (255 - a_)) / 255) for v, w in zip((r, g, b_), fr))))
    pcx = io.BytesIO(); f.save(pcx, 'PCX')
    NUEVOS_TIT[os.path.join('PICTS', nuevo + '.pcx')] = pcx.getvalue()

# ---------------------------------------------------------------- subtipos de terreno "landing" y "carrier"
# Para que war3ed_ssg los ofrezca en las listas de Move Bonus: arma esas listas con FindFirst sobre
# TERRAIN\SUBTYPE\*.STT (0x428d60). El juego solo abre un .STT por nombre (0x46a6f0), para el texto de un Combat
# Bonus, y lee el nombre largo (9) y el corto (25). Formato de 41 bytes: nombre (9 bytes), nombre largo (16), nombre
# corto (7) y el resto como water.STT. El dword de 32 en 0 hace de terminador del nombre corto, que ocupa los 7
# bytes (igual que lthills.STT); el editor tampoco lo respeta (escribe hasta 8 caracteres ahí).
def stt(nombre, largo):
    b = nombre.encode().ljust(9, b'\0') + largo.encode().ljust(16, b'\0') + nombre.encode()[:7].ljust(7, b'\0')
    b += struct.pack('<IIB', 0, 1, 0x34)
    assert len(b) == 0x29
    return b
STTS = {os.path.join('TERRAIN', 'SUBTYPE', n + '.STT'): stt(n, l) for n, l in (('landing', 'Landing'), ('carrier', 'Carrier'), ('bridge', 'Bridge'), ('cabotage', 'Cabotage'))}
# DATA\BRIDNAME.TXT: gramática de los nombres de puentes (br_name), en el formato de RANDOM\<set>\cityname.txt que
# lee 0x4374a0: en [RULES], "porcentaje [A] [B] [C] [D]" (toma la primera regla cuyo porcentaje supera la tirada de
# 1 a 100) y cada [SECCIÓN] da una entrada al azar; se pegan tal cual, con sus espacios. Sílabas de cityname.txt.
BRIDNAME = """[RULES]

40 [SYL1] [SYL2] [TITLE]
75 [SYL1] [SYL3] [TITLE]
100 [SYL1] [SYL3] [SYL2] [TITLE]

[TITLE]
 Bridge
 Bridge
 Bridge
 Bridge
 Bridge
 Crossing
 Span

[SYL1]
Aern
Gal
Fer
Bel
Mel
Bal
Xal
Xaj
Zan
Zar
Zhul
Yor
Nar
Gon
Trel
Grul
Pret
Ban
Mor
Tan
Ten
Tul
Gol
Ghul
Dar
Dran
Drak
Dral
Del
Drel
Dul
Drul
Dhul
Dhol
Eral
Elan
Hrul
Han
Hol
Hop
Jus
Kil
Khaz
Khur
Zen

[SYL2]
ton
rak
rik
thas
thor
gor
dros
heim
dor
doria
kith
kin
ing
gon
tor
torin
berg
ville
side
shand
lay
dalf

[SYL3]
an
a
or
o
in
il
al
onga
orcha
""".replace('\n', '\r\n').encode('ascii')
NUEVOS = dict(STTS)
NUEVOS[os.path.join('DATA', 'BRIDNAME.TXT')] = BRIDNAME
NUEVOS[os.path.join('SETS', 'Fantasy', 'sorteo.pcx')] = SORTEO_PCX
NUEVOS.update(NUEVOS_TIT)

# ---------------------------------------------------------------- escribir (solo archivos nuevos)
for path in (OUT_EXE, OUT_RES):
    assert os.path.abspath(path).lower() not in (os.path.abspath(SRC_EXE).lower(), os.path.abspath(SRC_RES).lower())
# Un .STT distinto ya presente lo hizo otro (con el editor): no se pisa. sorteo.pcx es del parche, como el exe y el
# RES: se reescribe.
for rel_, data in STTS.items():
    path = os.path.join(OUT_DIR, rel_)
    if os.path.exists(path) and open(path, 'rb').read() != data:
        sys.exit(f'{path} ya existe con otro contenido; no lo piso. Renombralo o borralo y volve a armar.')
os.makedirs(os.path.dirname(OUT_RES), exist_ok=True)
open(OUT_EXE, 'wb').write(exe)
open(OUT_RES, 'wb').write(res)
for rel_, data in NUEVOS.items():
    path = os.path.join(OUT_DIR, rel_)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'wb').write(data)
print('caves', {k: hex(CAVE + sum(len(caves[j]) for j in list(caves)[:list(caves).index(k)])) for k in caves})
print('exe', OUT_EXE, len(exe), 'res', OUT_RES, len(res), 'nuevos', ', '.join(NUEVOS))
