# Arma DarklordAV.exe y DATA\WAR3AV.RES a partir de los originales (que solo se leen), los subtipos de terreno
# TERRAIN\SUBTYPE\landing.STT, carrier.STT, cabotage.STT y trap.STT, y el dibujo del botón de Sorteo
# SETS\Fantasy\sorteo.pcx, y el editor war3ed_av.exe (editor_av.py).
# Topes de un barco según sus bonos de movimiento: stack en agua de 5 con "Landing" y de 6 con "Landing" y "Carrier"
# (LANDCAP); pasos de 12, 20 y 24 con "Landing", "Landing" y "Carrier", y "Carrier" (MVCAP).
# Convoy: hasta tres barcos en fila de un bando con bono de movimiento "Carrier" forman uno de hasta 24 (crlink).
# Puentes: derribar (Raze, con la opción de arrasar sitios) y reconstruir (Build, al costo de una ciudad); el diálogo
# de derribar muestra el retrato del ariete orco.
# Habilidad especial "Bridge +N" (código 34, sin uso en el original): suma N a la fuerza cuando la batalla es en un
# puente en pie.
# Cabotaje: el barco de un bando con el bono de movimiento "Cabotage" no se aleja más de 2 casillas de la costa
# (salvo para acercarse); cruza ríos y lagos angostos.
# Vista aliada compartida: bit 0x80 de [0x53c38e] (opciones de partida).
# Botones de Votación ("Votacion" en el menú de partida) y Sorteo (ícono del programa en la preparación): el
# anfitrión abre Herramientas\votacion.exe / sorteo.exe en todas las PC y su estado viaja por red a los espectadores.
# Botón del Comparador (ícono de DarkCompare en Edit Side): cada PC abre su Herramientas\DarkCompare.exe; su dibujo es
# SETS\Fantasy\darkcomp.pcx.
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
# partners(i) -> eax = máscara de los socios de la ciudad i: aliados mutuos y vivos del dueño. Con Hidden Map, solo
# los que exploraron por sí mismos ([casilla+4] & ~[casilla+5], no lo prestado por vista aliada) las 4 casillas de
# la ciudad; con el mapa visible, todos (pedido del usuario, 16/10/2026: sin Hidden Map no había ciudad compartida
# nunca). Requiere la opción y Diplomacy; la ciudad viva y con dueño < 8. Preserva ebx, esi, edi, ebp.
CITIES = 0x537e2c
partners = place('partners', f'''
    push ebx
    push esi
    push edi
    push ebp
    test byte ptr [{SHOPT:#x}], 1
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
    mov eax, ebp
    test byte ptr [{OPT:#x}], 0x10
    jz pt_ret
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
#    59 Allied View (bit 0x80 de [0x503d02]), 60 Shared Cities (bit 1 de [SHOPT_DLG]),
#    61 Day/Night (bit 2 de [SHOPT_DLG]; se puede combinar con Hidden Map desde el 1.0.85.0).
NEWCHK = 59
SHCHK = 60
DNCHK = 61
click = place('click', f'''
    cmp eax, {SHCHK - 2}
    je ck_shared
    cmp eax, {DNCHK - 2}
    je ck_dn
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
ck_dn:
    mov eax, dword ptr [esi + 8]
    push 0
    and eax, 1
    shl al, 1
    xor al, byte ptr [{SHOPT_DLG:#x}]
    and al, 2
    xor byte ptr [{SHOPT_DLG:#x}], al
    jmp ck_done
''')

# 4) Refresco del diálogo: después de la casilla Fog (id 7), poner las nuevas.
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
    xor eax, eax
    test byte ptr [{SHOPT_DLG:#x}], 2
    setnz al
    push eax
    push {DNCHK}
    call 0x4dd000
    add esp, 8
    ret
''')

# 5) Reporte View Game Options: después de Timed Vectoring (id 0x2f), el indicador nuevo.
NEWIND = 49
SHIND = 51
DNIND = 53
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
    mov eax, 0x1d
    test byte ptr [{SHOPT:#x}], 2
    jz rp_off3
    mov eax, 0x1c
rp_off3:
    push eax
    push {DNIND}
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
    push 0
    push {DNCHK}
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
    # Habilidad 34 (sin uso en el original, textos de relleno): "Bridge +N", ver Habilidad "Bridge +N" más abajo.
    (0x18a, 0, 'Bridge +%d', 'XXXX +%d'),
    (0x18a, 1, 'brg +%d', 'xx +%d'),
    (0x18a, 2, 'Bridge', 'XXXX'),
    (0x18a, 3, 'Each point of Bridge adds 1 to the strength of ', 'XXXX '),
    (0x18a, 4, 'this army when the battle is on a bridge that ', 'XXXX '),
    (0x18a, 5, 'is still standing.', 'XXXX'),
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
# off y slots: dónde están los nombres de 9 bytes (bonos de movimiento: 0xb2, 4; bono de combate: 0xd6, 1).
def boatbon_src(lbl, straddr, rec=False, off=0xb2, slots=4):
    head = f'lea esi, [eax + {off:#x}]' if rec else f'''shl eax, 4
    add eax, 15
    imul esi, eax, 0xfc
    add esi, {0x53c410 + off:#x}'''
    straddr = 'edx' if rec else f'{straddr:#x}'
    return f'''
    push ecx
    push esi
    push edi
    {head}
    mov edi, {slots}
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
# Copia con [CRBLIT] (0x4dd530, o cam_blit del camuflaje cuando ese bloque lo pone), con los mismos argumentos.
CRBLIT = place_data('crblit', struct.pack('<I', 0x4dd530))
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
    jmp dword ptr [{CRBLIT:#x}]
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
# se encienden también con un puente vecino entero / derribado. Además anota en TR_FLAG si se puede construir una
# trampa en la casilla del líder (tr_check, más abajo con los pozos; se llama por TR_CHKP porque está después).
tr_vars = place_data('tr_vars', bytes(8))
TR_FLAG, TR_X, TR_Y, TR_CHKP = tr_vars, tr_vars + 2, tr_vars + 4, place_data('tr_chkp', bytes(4))
# Código de la trampa en el diálogo de reconstruir ([0x587e5c]): >= BR_CODE, así br_rebdraw no busca imagen y br_cost
# le pone el costo de fundar una ciudad; br_rebtxt le pone su texto y tr_send la manda por red.
TR_MARK = 0x7fff
tr_dlgtxt = place_data('tr_dlgtxt', cstr_('Building a trap'))
br_menu = place('br_menu', f'''
    mov byte ptr [{TR_FLAG:#x}], 0
    test bl, bl
    jnz brm_out
    test bp, bp
    jz brm_out
    movsx eax, bp
    imul eax, eax, 0x1c
    movsx edi, word ptr [eax + 0x54fe52]
    movsx ebp, word ptr [eax + 0x54fe54]
    call dword ptr [{TR_CHKP:#x}]
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
# Dibuja un cuadro del mapa (0x456ee0 sobre la vista 0x569588) solo si lo que está arriba es el mapa (0x4d7ed0 de
# 0x588bd0 == 0xa, la misma condición del bucle principal en 0x49d2f7). En una partida local, arrasar y reconstruir se
# aplican en el acto dentro del botón del diálogo, con el diálogo abierto: dibujar ahí dejaba la vista al día debajo
# del diálogo, y al cerrarse este reponía su fondo viejo sin que el mapa lo volviera a pintar (pedazos recortados
# hasta pasar el mouse). Con un diálogo arriba el bucle principal redibuja al volver al mapa. Usa eax, ecx, edx.
br_mapview = place('br_mapview', f'''
    mov ecx, 0x588bd0
    call 0x4d7ed0
    cmp eax, 0xa
    jne bmv_out
    mov ecx, 0x569588
    call 0x456ee0
bmv_out:
    ret
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
    call {br_mapview:#x}
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
# qb_line: la línea naranja del mapa hasta el objetivo de la misión (0x414090, caso del tipo 10 en 0x41424a) leía
# x, y en la tabla de sitios con el código del puente como índice, fuera de la tabla: el destino salía de basura
# que cambiaba de turno en turno (en el agua) o el juego se colgaba al aceptar la misión. Para un puente, su casilla.
qb_line = place('qb_line', f'''
    movsx eax, word ptr [edi + 6]
    push 0x48
    cmp eax, {BR_CODE:#x}
    jge qbl_bridge
    lea eax, [eax + eax*4]
    add eax, eax
    lea ecx, [eax + eax*2]
    mov di, word ptr [ecx + ecx*4 + 0x55acb6]
    lea eax, [ecx + ecx*4]
    mov ax, word ptr [eax + 0x55acb8]
    jmp 0x41426a
qbl_bridge:
    sub eax, {BR_CODE:#x}
    mov edi, eax
    and edi, 0x7f
    shr eax, 7
    jmp 0x41426a
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
# ---- IA: registro de eventos (ia\PENDIENTE-entrenamiento-ia.md, etapa 3). Solo con DATA\IA.INI (ia_on, ver "IA: base
# de pruebas"): una línea por evento en DATA\IA_EVT.CSV: turno, color, ia, tipo, x, y, n. Solo anota, no decide nada.
# Tipos: 1 puente derribado por criterio propio (ai_brraze; n = c + s), 2 convoy ordenado (ai_conv; x, y = casilla del
# barco al que se suma, n = ese ejército), 3 grupo partido al embarcar (ai_move; x, y = líder, n = soltados),
# 4 puente reconstruido (ai_brreb; n = costo), 5 refugio (ia_turn: al empezar el turno, pilas propias en una ciudad
# compartida de otro; x, y = ciudad, n = ejércitos), 6 puente derribado por misión (ai_brq).
# Alianzas (ai_ally; x, y = la ciudad salvo en 11 y 12): 7 refugio decidido (n = motivo 1/2/3 = req. 1a/b/c),
# 8 salida del refugio (n = 1 req. 3a, 2 req. 3b, 3 se perdió la ciudad o la alianza, 4 terminó la persecución del
# héroe), 9 (hasta 1.0.38.0) queda hasta el final (n = fuerza), 10 (hasta 1.0.37.0) refuerzo de ciudad aliada (n = 10 * motivo 6a/6b + criterio 7), 11 pila amenazada (x, y = líder,
# n = líder), 12 resultado de esa pila al turno siguiente (n = 1 sobrevivió, 0 no), 13 queda a defender la ciudad
# del refugio (req. 5; n = amenaza), 14 (solo 1.0.37.0) refuerzo que se queda, 15 va a defender una ciudad aliada
# amenazada (n = amenaza), 16 se queda en ella mientras dure la amenaza (n = amenaza).
# Órdenes del humano (ai_ord): 17 la pila cumple la orden (x, y = ciudad, n = tipo 1 ciudad, 2 color, 3 refuerzos).
# Pozos (po_fall): 18 cayó en un pozo, 19 en un remolino, 20 en una trampa (x, y = casilla, n = muertos + 100 si ya
# lo veía antes del paso: error evitable).
IA_A = place_data('ia_a', cstr_('a'))
IA_MODE = place_data('ia_mode', bytes(8))
IA_ON = place_data('ia_on', bytes(4))   # 1 si en el último turno existía DATA\IA.INI (activa los registros)
FOPEN, FCLOSE, FPRINTF, STRICMP = 0x5a9bdc, 0x5a9be4, 0x5a9bf4, 0x5a9be0
IA_ECSV = place_data('ia_ecsv', cstr_(r'.\DATA\IA_EVT.CSV'))
IA_EFMT = place_data('ia_efmt', cstr_('%d,%d,%d,%d,%d,%d,%d\n'))
# ia_evt(tipo, p, x, y, n) cdecl. Preserva todo.
ia_evt = place('ia_evt', f'''
    cmp byte ptr [{IA_ON:#x}], 0
    je ie_ret
    pushad
    push {IA_A:#x}
    push {IA_ECSV:#x}
    call dword ptr [{FOPEN:#x}]
    add esp, 8
    test eax, eax
    jz ie_out
    mov edi, eax
    mov ebx, dword ptr [esp + 0x28]
    push dword ptr [esp + 0x34]
    push dword ptr [esp + 0x34]
    push dword ptr [esp + 0x34]
    push dword ptr [esp + 0x30]
    mov eax, -1
    cmp ebx, 8
    jae ie_md
    movzx eax, byte ptr [ebx + {IA_MODE:#x}]
ie_md:
    push eax
    push ebx
    movsx eax, word ptr [0x503328]
    push eax
    push {IA_EFMT:#x}
    push edi
    call dword ptr [{FPRINTF:#x}]
    add esp, 0x24
    push edi
    call dword ptr [{FCLOSE:#x}]
    add esp, 4
ie_out:
    popad
ie_ret:
    ret
''')
# ia_evtb(tipo, p, código de puente, n) cdecl: ia_evt con x, y de la casilla del código. Preserva todo.
ia_evtb = place('ia_evtb', f'''
    push eax
    push edx
    mov eax, dword ptr [esp + 0x14]
    sub eax, {BR_CODE:#x}
    mov edx, eax
    shr edx, 7
    and eax, 0x7f
    push dword ptr [esp + 0x18]
    push edx
    push eax
    push dword ptr [esp + 0x1c]
    push dword ptr [esp + 0x1c]
    call {ia_evt:#x}
    add esp, 0x14
    pop edx
    pop eax
    ret
''')
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
    movsx eax, word ptr [0x537ce8]
    push 0
    movsx ecx, word ptr [esp + 0x28]
    push ecx
    push eax
    push 6
    call {ia_evtb:#x}
    add esp, 0x10
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
    push dword ptr [esp + {ABZ_S:#x}]
    push dword ptr [esp + {ABZ_CODE + 4:#x}]
    push dword ptr [esp + {ABZ_P + 8:#x}]
    push 1
    call {ia_evtb:#x}
    add esp, 0x10
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
    push esi
    push dword ptr [esp + {CV_NY + 4:#x}]
    push dword ptr [esp + {CV_NX + 8:#x}]
    push ebx
    push 2
    call {ia_evt:#x}
    add esp, 0x14
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
    mov ecx, dword ptr [esp + {AM_N:#x}]
    movsx eax, word ptr [esp + {AM_KEEP:#x}]
    imul eax, eax, 0x1c
    push ecx
    movsx edx, word ptr [eax + 0x54fe54]
    push edx
    movsx edx, word ptr [eax + 0x54fe52]
    push edx
    push dword ptr [esp + {AM_P + 12:#x}]
    push 3
    call {ia_evt:#x}
    add esp, 0x14
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
    push esi
    movsx eax, word ptr [esp + 0x18]
    push eax
    push ebx
    push 4
    call {ia_evtb:#x}
    add esp, 0x10
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
# Texto "Rebuilding %s" (0x4b64f0); la trampa, tr_dlgtxt como formato (0x4b6516 -> 0x4dd260(5, texto, 0)).
br_rebtxt = place('br_rebtxt', f'''
    movsx eax, word ptr [0x587e5c]
    cmp eax, {TR_MARK:#x}
    je brx_trap
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
brx_trap:
    push 0
    mov eax, {tr_dlgtxt:#x}
    jmp 0x4b6516
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
    call {br_mapview:#x}
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

# ---------------------------------------------------------------- Habilidad "Bridge +N"
# El bono de combate de cada unidad (nombre +0xd6, valor +0xdf del registro) se compara en 0x467b4a..0x467d09 con la
# casilla de la batalla (la del defensor, [esp+0x38]; vale para atacantes y defensores); si coincide, [esp+0x11] = 1
# y en 0x467d0e el valor ([esp+0x12]) pasa a [esp+0x16], lo que se suma a la fuerza. Ahí se suma además la habilidad
# 34 (palabra +0xe6, valor byte +0xe8; sin efecto en el original) si la casilla es un puente en pie: clase agua (di,
# palabra 0x535f0c del tipo, ya cargada) con estructura 1 ([+3] & 7, la misma definición que el constructor de
# caminos en 0x4a5135). Un puente derribado tiene estructura 0: no cuenta. No vale para héroes ([esp+0x26] = 0x10).
# Sin bono ni puente, registros y pila quedan como en el original. El nombre lo dan los textos 0x18a (TEXTS).
BRIDGE_AB = 34
bridgeab = place('bridgeab', f'''
    push ecx
    push edx
    xor ecx, ecx
    cmp byte ptr [esp + 0x19], 0
    je bab_chk
    mov cx, word ptr [esp + 0x1a]
bab_chk:
    cmp word ptr [esp + 0x2e], 0x10
    je bab_no
    cmp di, 1
    jne bab_no
    mov edx, dword ptr [esp + 0x40]
    mov dl, byte ptr [edx + 3]
    and dl, 7
    cmp dl, 1
    jne bab_no
    mov edx, dword ptr [esp + 0x38]
    cmp word ptr [edx + 0xe6], {BRIDGE_AB}
    jne bab_no
    movzx edx, byte ptr [edx + 0xe8]
    test edx, edx
    jz bab_no
    add ecx, edx
    jmp bab_put
bab_no:
    cmp byte ptr [esp + 0x19], 0
    je bab_out
bab_put:
    mov ax, cx
    mov word ptr [esp + 0x1e], ax
bab_out:
    pop edx
    pop ecx
    jmp 0x467d1f
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

# El aviso sobre un papiro (pedido del usuario, 30/10/2026: en amarillo pálido sobre el mapa no se veía). En las dos
# llamadas de 0x4c2810 a 0x4dd1c0 (surf, x del centro del texto, y, texto; ebx = renglón): si el renglón es el del
# aviso, antes del texto va
# la hoja PZ_FILE (RUINS\aviso.pcx, el papiro de los cuadros de info, DLG_HELP, de PZ_W x PZ_H) centrada en el texto, y
# el texto en marrón oscuro (PZ_INK) con sombra clara (PZ_SHADOW). Los otros renglones siguen igual.
PZ_FILE = RAM_FILE + 4       # después de pozos.pcx (ver table_add, más abajo)
PZ_W, PZ_H, PZ_INK, PZ_SHADOW = 340, 56, 128, 174
pz_scroll = place('pz_scroll', f'''
    call {pz_find:#x}
    cmp eax, ebx
    jne 0x4dd1c0
    pushad
    push {PZ_FILE}
    mov ecx, 0x58cf78
    call 0x4e4a90
    test eax, eax
    jz ps_ink
    cmp dword ptr [eax + 8], 0
    jne ps_blit
    push {PZ_FILE}
    call 0x4dd3f0
    add esp, 4
    test eax, eax
    jz ps_ink
ps_blit:
    mov eax, dword ptr [esp + 0x28]
    sub eax, {PZ_W // 2}
    jge ps_x
    xor eax, eax
ps_x:
    mov edx, dword ptr [esp + 0x2c]
    sub edx, {(PZ_H - 12) // 2}
    jge ps_y
    xor edx, edx
ps_y:
    push edx
    push eax
    push dword ptr [esp + 0x2c]
    push {PZ_H}
    push {PZ_W}
    push 0
    push 0
    push {PZ_FILE}
    call 0x4dd530
    add esp, 0x20
ps_ink:
    push {PZ_SHADOW}
    push 10
    push 10
    push {PZ_INK}
    push 3
    call 0x4dd0f0
    add esp, 0x14
    popad
    jmp 0x4dd1c0
''')

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

# ---- Pozos, remolinos y trampas (po_*; diseño en PENDIENTE-pozos-y-trampas.md). Tabla propia, fuera de la de ruinas
# y de la casilla: PO_MAX registros de 8 bytes (+0 x, +2 y, +4 tipo, +5 estado, +6 máscara de quién lo descubrió,
# +7 dueño; en pozo y remolino, +5 = cuál nombre, ver PO_NOMBRES). po_map: un byte por casilla (índice + 1, 0 = nada), rearmado desde la tabla; no se guarda.
# En el .SAV va detrás del bloque de la Votación: 'POZO', cantidad (dword) y la tabla entera.
PO_MAX, PO_REC = 64, 8
PO_POZO, PO_REMOLINO, PO_TRAMPA, PO_TUMBA = 0, 1, 2, 3   # tumba: +5 = cuál (tumba, lápida, cruz), vista por todos
# Trampa: +5 = explosiones que lleva en los bits 0-3 (pedido del usuario, 22/10/2026: explota TR_USOS veces). Activa
# mientras lleve menos de TR_USOS; gastada, no mata ni se descubre, y queda a la vista de todos como agujero con humo
# hasta el final (pedido del usuario, 22/10/2026). Bit 7 (TR_RECIEN): explotó y su jugador (bits 4-6) todavía no
# empezó otro turno; mientras tanto, quien la ve, ve el agujero con humo, y después de nuevo la mina (tr_turn).
# Un .SAV de antes trae 1 en las detonadas: les queda 1 uso. Desde 1.0.70.0 son 2 explosiones, no 3 (pedido del
# usuario, 24/10/2026: tres era excesivo); una trampa que ya llevaba 2 queda gastada.
TR_USOS, TR_CUENTA, TR_RECIEN = 2, 0x0f, 0x80
PO_MAPSZ = 0x32000 // 10                       # casillas del mapa 0x503e58 (10 bytes cada una)
po_save = place_data('po_save', b'POZO' + bytes(4 + PO_MAX * PO_REC))   # tal cual se escribe al final del .SAV
PO_SAVELEN = 8 + PO_MAX * PO_REC
PO_N, PO_TAB = po_save + 4, po_save + 8
po_magic = place_data('po_magic', bytes(4))
po_map = place_data('po_map', bytes(PO_MAPSZ))

# Rearma po_map desde la tabla. Un registro fuera del mapa no se marca. Preserva todo.
po_rebuild = place('po_rebuild', f'''
    pushad
    mov edi, {po_map:#x}
    mov ecx, {PO_MAPSZ // 4}
    xor eax, eax
    rep stosd
    xor ebx, ebx
por_loop:
    cmp ebx, dword ptr [{PO_N:#x}]
    jae por_end
    lea esi, [ebx*8 + {PO_TAB:#x}]
    movsx eax, word ptr [esi]
    movsx edx, word ptr [esi + 2]
    test eax, eax
    jl por_next
    test edx, edx
    jl por_next
    movsx ecx, word ptr [0x503e00]
    cmp eax, ecx
    jge por_next
    movsx ecx, word ptr [0x503e02]
    cmp edx, ecx
    jge por_next
    mov cl, byte ptr [0x503e06]
    shl edx, cl
    add edx, eax
    cmp edx, {PO_MAPSZ}
    jae por_next
    lea eax, [ebx + 1]
    mov byte ptr [edx + {po_map:#x}], al
por_next:
    inc ebx
    jmp por_loop
por_end:
    popad
    ret
''')

# Al cargar, detrás de la Votación (ebp = el marco de 0x439e..): la tabla, si está; si no, o rota, vacía.
po_loadf = place('po_loadf', f'''
    pushad
    mov dword ptr [{PO_N:#x}], 0
    mov dword ptr [{po_magic:#x}], 0
    push 4
    push {po_magic:#x}
    lea ecx, [ebp - 0x120]
    call 0x4dfd20
    cmp eax, 4
    jne pol_end
    cmp dword ptr [{po_magic:#x}], 0x4f5a4f50
    jne pol_end
    push {4 + PO_MAX * PO_REC}
    push {PO_N:#x}
    lea ecx, [ebp - 0x120]
    call 0x4dfd20
    cmp eax, {4 + PO_MAX * PO_REC}
    jne pol_bad
    cmp dword ptr [{PO_N:#x}], {PO_MAX}
    jbe pol_end
pol_bad:
    mov dword ptr [{PO_N:#x}], 0
pol_end:
    call {po_rebuild:#x}
    popad
    ret
''')

# Red (parte 6). Cada PC genera sus pozos al recibir la partida nueva (0x42ceb0 -> po_gen, po_start); después el
# anfitrión manda la partida en bloques (0x4aa0e0: 0x4aa2c0(id, cantidad, datos, largo), ids 0..8) y el receptor
# (0x4aa340) los copia encima de lo suyo, como hace con las ruinas. Se suma el bloque PO_BLOQUE con la tabla entera:
# el anfitrión lo manda detrás del 8 (aunque esté vacía: así el receptor vacía la suya), el receptor lo copia en
# PO_TAB con la cantidad en PO_N y rearma po_map, y la suma de sincronía (0x4aa520) incluye cantidad y tabla.
# Un id fuera de 0..8 el original lo pegaría detrás del bloque anterior: por eso hay que atenderlo antes.
PO_BLOQUE = 9
po_nsend = place('po_nsend', f'''
    mov eax, dword ptr [{PO_N:#x}]
    cmp eax, {PO_MAX}
    jbe pns_ok
    xor eax, eax
pns_ok:
    lea ecx, [eax*8]
    push ecx
    push {PO_TAB:#x}
    push eax
    push {PO_BLOQUE}
    call 0x4aa2c0
    add esp, 16
    jmp 0x4baf20
''')

# En 0x4aa361 (cx = id de un bloque que empieza; [esp+0x14] = cantidad).
po_nrecv = place('po_nrecv', f'''
    cmp cx, {PO_BLOQUE}
    jne pnr_orig
    movsx eax, word ptr [esp + 0x14]
    cmp eax, {PO_MAX}
    jbe pnr_ok
    xor eax, eax
pnr_ok:
    mov dword ptr [{PO_N:#x}], eax
    mov edx, {PO_TAB:#x}
    jmp 0x4aa3ed
pnr_orig:
    movsx eax, cx
    inc eax
    cmp eax, 9
    ja 0x4aa3e7
    jmp dword ptr [eax*4 + 0x4aa42c]
''')

# En 0x4aa421, después de copiar un paquete: si era de la tabla, rearma po_map.
po_nrecvd = place('po_nrecvd', f'''
    mov dword ptr [0x4ff03c], edx
    cmp word ptr [0x4ff030], {PO_BLOQUE}
    jne 0x4aa427
    call {po_rebuild:#x}
    jmp 0x4aa427
''')

# En 0x4aa6bf, al cerrar la suma ([esp+0x10]): cantidad y tabla con el mismo 0x4aa6d0 (xor de dwords).
po_nsum = place('po_nsum', f'''
    xor dword ptr [esp + 0x10], ebp
    mov eax, dword ptr [{PO_N:#x}]
    cmp eax, {PO_MAX}
    jbe pnm_ok
    xor eax, eax
pnm_ok:
    lea eax, [eax*8 + 4]
    push eax
    push {PO_N:#x}
    call 0x4aa6d0
    add esp, 8
    xor dword ptr [esp + 0x10], eax
    mov eax, dword ptr [esp + 0x10]
    jmp 0x4aa6c7
''')

# Generación (partida nueva): al terminar de ocultar ruinas (0x4a1961, corre en toda partida nueva) se vacía la tabla
# y, con Hidden Ruins, se reparten pozos y remolinos con el generador del juego (0x4deb20: n dados de 1..max + suma).
# Cantidad: pozos, 20 % de las ruinas, mínimo 1, como mucho PO_MAX/4; remolinos, el doble (pedido del usuario,
# 21/10/2026: por el agua se circula menos); PO_TRIES tiros por cada uno (si el mapa
# no tiene casillas válidas, quedan menos). Casilla válida: libre en po_map, sin edificio (palabra 0 & 0x4000), sin
# cosa (palabra +2 bits 8-10, el mismo campo que la «estructura» [+3] & 7: 1 camino o puente, 2 ruina, 3 ciudad, 4
# sitio). Trampa: cualquier casilla libre en po_map (pedido del usuario, 22/10/2026: también ciudad, ruina, sitio,
# camino, puente y agua). Pozo: clase de terreno
# (0x535f0c + tipo*0x58) ni agua (1) ni montaña (4), a más de 2 casillas (max |dx|,|dy|) de la capital de todo jugador
# activo. Remolino: clase agua, y agua todo alrededor hasta 2 casillas (po_mar). Tumba (po_grave): como el pozo, pero sin mirar las capitales. pg_ok: esi = x,
# edi = y, ebp = tipo -> ZF = 1 si sirve; preserva todo.
# Nombres de pozos y remolinos (pedido del usuario, 21/10/2026): como las ruinas, para los avisos («Your army fell
# into the Well of Souls!»). En +5 del registro (el estado solo lo usan las trampas): índice en la lista de su tipo,
# que po_gen reparte sin repetir (un comienzo al azar y después correlativos). Hay tantos nombres como el tope de cada
# tipo (16 pozos, 32 remolinos); un .SAV de antes trae 0 = el primero. La trampa y la tumba siguen con el aviso fijo.
PO_NOMBRES = (
    ('the Well of Souls', 'the Pit of Despair', 'the Abyss of Mor', 'the Chasm of Woe', 'the Maw of Darkness',
     'the Sinkhole of Ash', 'the Hollow of Bones', 'the Deep of Kragg', 'the Rift of Sorrows', 'the Gorge of Shadows',
     'the Pit of the Lost', 'the Throat of Stone', 'the Shaft of Doom', 'the Gulf of Night', 'the Grave of Giants',
     'the Void of Ulgar'),
    ('the Maelstrom of Kor', 'the Drowning Eye', 'the Whirl of Vash', "the Serpent's Coil", "the Sea's Maw",
     'the Black Vortex', 'the Spiral of Lost Ships', 'the Churn of Ymir', "the Widow's Whirl", 'the Eye of the Deep',
     'the Gyre of Thalos', 'the Sunken Mouth', 'the Grey Maelstrom', "the Kraken's Throat", 'the Whirl of Sorrow',
     "the Mariners' Doom", 'the Vortex of Azur', 'the Swirl of Bones', 'the Hungry Tide', 'the Coil of Nereth',
     'the Storm Eye', "the Drowned King's Gate", 'the Spinning Grave', 'the Whirl of Mists', 'the Maw of Leviathan',
     'the Abyssal Spiral', 'the Gyre of Salt', 'the Cauldron of Waves', "the Siren's Whirl", "the Wreckers' Pool",
     'the Weeping Vortex', "the Sea Wolf's Den"))
assert [len(n) for n in PO_NOMBRES] == [PO_MAX // 4, PO_MAX // 2] and all(len(set(n)) == len(n) for n in PO_NOMBRES)
po_nmt = place_data('po_nmt', struct.pack('<2I', *(place_data(f'po_nm{t}', struct.pack(f'<{len(ns)}I', *(
    place_data(f'str_po_nm{t}_{i}', cstr_(n)) for i, n in enumerate(ns)))) for t, ns in enumerate(PO_NOMBRES))))
po_nmask = place_data('po_nmask', struct.pack('<2I', len(PO_NOMBRES[0]) - 1, len(PO_NOMBRES[1]) - 1))
PO_FMT = (('Your army fell into %s!', 'Your army was swallowed by %s!'),
          ('You have discovered %s!', 'You have discovered %s!'))
assert all(len(f % n) < 64 for fs in PO_FMT for t, f in enumerate(fs) for n in PO_NOMBRES[t])   # renglón de 0x4c2790
po_fmtt = place_data('po_fmtt', struct.pack('<4I', *(place_data(f'str_po_fmt{i}', cstr_(f))
                                                     for i, f in enumerate(f for fs in PO_FMT for f in fs))))
po_nmi = place_data('po_nmi', bytes(4))
po_buf = place_data('po_buf', bytes(64))
PO_TRIES = 400
po_q = place_data('po_q', bytes(4))
po_k = place_data('po_k', bytes(4))
# po_mar: esi = x, edi = y -> ZF = 1 si toda casilla a 2 o menos (max |dx|,|dy|) está en el mapa y es agua sin
# edificio ni estructura (pedido del usuario, 22/10/2026: el remolino junto a la costa se ve entrecortado; así
# tampoco hay remolinos en ríos). Preserva todo.
po_mar = place('po_mar', f'''
    pushad
    mov ebx, -2
pmr_y:
    mov ebp, -2
pmr_x:
    lea eax, [esi + ebp]
    lea edx, [edi + ebx]
    test eax, eax
    jl pmr_no
    test edx, edx
    jl pmr_no
    cmp ax, word ptr [0x503e00]
    jge pmr_no
    cmp dx, word ptr [0x503e02]
    jge pmr_no
    mov cl, byte ptr [0x503e06]
    lea edx, [edx + edx*4]
    add edx, edx
    shl edx, cl
    lea eax, [eax + eax*4]
    lea edx, [edx + eax*2 + 0x503e58]
    test word ptr [edx], 0x4000
    jnz pmr_no
    test word ptr [edx + 2], 0x700
    jnz pmr_no
    movzx eax, word ptr [edx]
    and eax, 0x1f
    imul eax, eax, 0x58
    cmp word ptr [eax + 0x535f0c], 1
    jne pmr_no
    inc ebp
    cmp ebp, 2
    jle pmr_x
    inc ebx
    cmp ebx, 2
    jle pmr_y
    popad
    cmp eax, eax
    ret
pmr_no:
    popad
    test esp, esp
    ret
''')
# po_wet: eax = registro -> ZF = 1 si su casilla es agua sin puente (mina submarina, pedido del usuario, 22/10/2026).
# Preserva todo.
po_wet = place('po_wet', f'''
    pushad
    movsx esi, word ptr [eax]
    movsx edi, word ptr [eax + 2]
    mov cl, byte ptr [0x503e06]
    lea eax, [edi + edi*4]
    add eax, eax
    shl eax, cl
    lea edx, [esi + esi*4]
    lea eax, [eax + edx*2 + 0x503e58]
    movzx edx, word ptr [eax + 2]
    and edx, 0x700
    cmp edx, 0x100
    je pwt_no
    movzx edx, word ptr [eax]
    and edx, 0x1f
    imul edx, edx, 0x58
    cmp word ptr [edx + 0x535f0c], 1
    popad
    ret
pwt_no:
    test esp, esp
    popad
    ret
''')
pg_ok = place('pg_ok', f'''
    pushad
    test esi, esi
    jl pk_no
    test edi, edi
    jl pk_no
    cmp si, word ptr [0x503e00]
    jge pk_no
    cmp di, word ptr [0x503e02]
    jge pk_no
    mov cl, byte ptr [0x503e06]
    mov eax, edi
    shl eax, cl
    add eax, esi
    cmp eax, {PO_MAPSZ}
    jae pk_no
    cmp byte ptr [eax + {po_map:#x}], 0
    jne pk_no
    cmp ebp, {PO_TRAMPA}
    je pk_si
    lea eax, [edi + edi*4]
    add eax, eax
    shl eax, cl
    lea edx, [esi + esi*4]
    lea eax, [eax + edx*2 + 0x503e58]
    movzx edx, word ptr [eax]
    test dh, 0x40
    jnz pk_no
    movzx ecx, word ptr [eax + 2]
    and ecx, 0x700
    jnz pk_no
    and edx, 0x1f
    imul edx, edx, 0x58
    movsx edx, word ptr [edx + 0x535f0c]
    cmp ebp, {PO_REMOLINO}
    je pk_agua
    cmp edx, 1
    je pk_no
    cmp edx, 4
    je pk_no
    cmp ebp, {PO_TUMBA}
    je pk_si
    xor ebx, ebx
pk_cap:
    imul eax, ebx, 0x1f8
    cmp byte ptr [eax + 0x536b30], 0
    je pk_capn
    cmp byte ptr [eax + 0x536b31], 0
    je pk_capn
    movsx eax, word ptr [eax + 0x536c22]
    test eax, eax
    jl pk_capn
    cmp ax, word ptr [0x537e2a]
    jge pk_capn
    imul eax, eax, 0xde
    movsx ecx, word ptr [eax + 0x537e2c]
    sub ecx, esi
    cmp ecx, -2
    jl pk_capn
    cmp ecx, 2
    jg pk_capn
    movsx ecx, word ptr [eax + 0x537e2e]
    sub ecx, edi
    cmp ecx, -2
    jl pk_capn
    cmp ecx, 2
    jle pk_no
pk_capn:
    inc ebx
    cmp ebx, 8
    jl pk_cap
    jmp pk_si
pk_agua:
    cmp edx, 1
    jne pk_no
    call {po_mar:#x}
    jne pk_no
pk_si:
    popad
    cmp eax, eax
    ret
pk_no:
    popad
    or esp, esp
    ret
''')
po_gen = place('po_gen', f'''
    pushad
    mov dword ptr [{PO_N:#x}], 0
    test byte ptr [0x53c393], 0x10
    jz pg_end
    movsx eax, word ptr [0x558872]
    imul eax, eax, 20
    cdq
    mov ecx, 100
    idiv ecx
    test eax, eax
    jg pg_q1
    mov eax, 1
pg_q1:
    cmp eax, {PO_MAX // 4}
    jle pg_q2
    mov eax, {PO_MAX // 4}
pg_q2:
    mov dword ptr [{po_q:#x}], eax
    xor ebp, ebp
pg_tipo:
    mov ebx, dword ptr [{po_q:#x}]
    cmp ebp, {PO_REMOLINO}
    jne pg_cnt
    add ebx, ebx
pg_cnt:
    push -1
    mov eax, dword ptr [ebp*4 + {po_nmask:#x}]
    inc eax
    push eax
    push 1
    call 0x4deb20
    add esp, 12
    movzx eax, ax
    mov dword ptr [{po_nmi:#x}], eax
    mov dword ptr [{po_k:#x}], {PO_TRIES}
pg_try:
    test ebx, ebx
    jz pg_tnext
    dec dword ptr [{po_k:#x}]
    js pg_tnext
    push -1
    movsx eax, word ptr [0x503e00]
    push eax
    push 1
    call 0x4deb20
    add esp, 12
    movsx esi, ax
    push -1
    movsx eax, word ptr [0x503e02]
    push eax
    push 1
    call 0x4deb20
    add esp, 12
    movsx edi, ax
    call {pg_ok:#x}
    jnz pg_try
    mov eax, dword ptr [{PO_N:#x}]
    lea edx, [eax*8 + {PO_TAB:#x}]
    mov word ptr [edx], si
    mov word ptr [edx + 2], di
    mov ecx, ebp
    mov byte ptr [edx + 4], cl
    mov ecx, dword ptr [{po_nmi:#x}]
    and ecx, dword ptr [ebp*4 + {po_nmask:#x}]
    mov byte ptr [edx + 5], cl
    inc dword ptr [{po_nmi:#x}]
    mov byte ptr [edx + 6], 0
    mov byte ptr [edx + 7], 0xff
    inc eax
    mov dword ptr [{PO_N:#x}], eax
    call {po_rebuild:#x}
    dec ebx
    jmp pg_try
pg_tnext:
    inc ebp
    cmp ebp, {PO_REMOLINO}
    jle pg_tipo
pg_end:
    call {po_rebuild:#x}
    popad
    xor si, si
    cmp word ptr [0x558872], si
    jle 0x4a103c
    jmp 0x4a1971

''')

# Al empezar (0x42ddc1, antes de 0x4a1e20, que hace lo mismo con las ruinas): con Hidden Ruins, cada jugador activo
# descubre los de la región (byte bajo de la palabra +2 de la casilla, distinto de 0) de su capital.
po_start = place('po_start', f'''
    pushad
    test byte ptr [0x53c393], 0x10
    jz ps_end
    xor ebx, ebx
ps_pl:
    imul eax, ebx, 0x1f8
    cmp byte ptr [eax + 0x536b30], 0
    je ps_pln
    cmp byte ptr [eax + 0x536b31], 0
    je ps_pln
    movsx eax, word ptr [eax + 0x536c22]
    test eax, eax
    jl ps_pln
    cmp ax, word ptr [0x537e2a]
    jge ps_pln
    imul eax, eax, 0xde
    movsx esi, word ptr [eax + 0x537e2c]
    movsx edi, word ptr [eax + 0x537e2e]
    call ps_reg
    test eax, eax
    jz ps_pln
    mov ebp, eax
    xor edx, edx
ps_po:
    cmp edx, dword ptr [{PO_N:#x}]
    jae ps_pln
    movsx esi, word ptr [edx*8 + {PO_TAB:#x}]
    movsx edi, word ptr [edx*8 + {PO_TAB:#x} + 2]
    call ps_reg
    cmp eax, ebp
    jne ps_pon
    mov cl, bl
    mov al, 1
    shl al, cl
    or byte ptr [edx*8 + {PO_TAB:#x} + 6], al
ps_pon:
    inc edx
    jmp ps_po
ps_pln:
    inc ebx
    cmp ebx, 8
    jl ps_pl
ps_end:
    popad
    jmp 0x4a1e20

ps_reg:
    xor eax, eax
    test esi, esi
    jl pr_end
    test edi, edi
    jl pr_end
    cmp si, word ptr [0x503e00]
    jge pr_end
    cmp di, word ptr [0x503e02]
    jge pr_end
    push ecx
    push edx
    mov cl, byte ptr [0x503e06]
    lea eax, [edi + edi*4]
    add eax, eax
    shl eax, cl
    lea edx, [esi + esi*4]
    movzx eax, byte ptr [eax + edx*2 + 0x503e5a]
    pop edx
    pop ecx
pr_end:
    ret
''')

# Caer. El anfitrión arma cada tic un paso por jugador que se mueve (0x49e1a0 -> 0x49e280) y los manda juntos (orden
# 0x14d); todas las PC aplican el lote en 0x4b6e62: un 0x49c9f0 por paso y al final 0x49d1a0. En el paso normal
# (código 0), al descubrir ruinas (0x49ce08), po_step anota en po_pend[jugador] el registro de la casilla de llegada
# si está activo (pozo, remolino o trampa sin detonar). po_fall, antes de 0x49d1a0, mata en cada casilla anotada a
# los ejércitos vivos de ese jugador que no vuelan (héroes incluidos; en un remolino también lo embarcado) con
# 0x46c470(ejército, 0) en pozo y trampa o 0x46c470(ejército, 1) en remolino, como el disband. 0x46c470 suelta el
# grupo en movimiento (0x485c00): en el tic siguiente 0x49e280 devuelve -1 y el movimiento se corta; los voladores
# que sobrevivan quedan en la casilla. Si murió alguno: el registro queda descubierto para ese jugador (la trampa,
# con una explosión más, ver TR_USOS), 0x441290, el mapa y, en la PC de ese jugador ([0x560b20]), el aviso y el sonido de
# muerte de héroe (0x4465e0(7, g): RuinDie o RuinDie2; g al azar con rdtsc, que no toca el generador del juego). En
# una trampa suena además, a la vez, la explosión FX\Burst.wav (sonido PO_SND; pedido del usuario, 21/10/2026): con la
# misma condición que el 7 (bit 0x20 de [0x564d08]), 0x4eca00(id) busca el buffer en la lista 0x5a6f50 y 0x4e6fd0(0, 0)
# lo toca; DirectSound mezcla los dos.
PO_SND = 56                  # el sonido siguiente al último (Dispel, 55) de la tabla de sonidos del RES (ver más abajo)
# Descubrir al pasar (parte 4): po_step llama primero a 0x4a1ce0 (que avanza el contador de pasos [0x4fe5e8] y descubre
# ruinas) y después aplica la regla a la tabla: con Hidden Ruins y Discover Ruins, en 1 de cada 5 pasos (contador 0 o
# 5; pedido del usuario, 21/10/2026: las ruinas usan 1 de cada 10 con radio 1) y el grupo en movimiento (0x56ea94 + p*0x4f0) tiene alguno
# que no vuela (los voladores no caen, así que no descubren), el primer registro no visto por el jugador a
# |dx|+|dy| <= PO_RADIO (no el radio del grupo, que crece con "View" y para la computadora) queda descubierto para él, se redibuja y, en su PC, el aviso. Corre en todas las PC con los mismos datos, como las ruinas.
po_pend = place_data('po_pend', bytes(8))
# Registro de la IA (ia\PENDIENTE-ia-innovaciones.md, paso 1): po_step guarda en po_pvis[jugador] si el registro ya
# era visible para él antes del paso (antes de descubrir al pasar); po_fall cuenta en po_kill los muertos y anota
# ia_evt(18 + tipo, jugador, x, y, muertos + 100 si era visible): 18 pozo, 19 remolino, 20 trampa.
po_pvis = place_data('po_pvis', bytes(8))
po_kill = place_data('po_kill', bytes(4))
str_po_fell = [place_data(f'str_po_fell{i}', cstr_(s)) for i, s in enumerate((
    'Your army fell into a hidden pit!', 'Your army was swallowed by a whirlpool!', 'Your army fell into a trap!'))]
po_fellt = place_data('po_fellt', struct.pack('<3I', *str_po_fell))
str_po_disc = [place_data(f'str_po_disc{i}', cstr_(s)) for i, s in enumerate((
    'You have discovered a hidden pit!', 'You have discovered a hidden whirlpool!', 'You have discovered a hidden trap!'))]
po_disct = place_data('po_disct', struct.pack('<3I', *str_po_disc))
po_gent = place_data('po_gent', struct.pack('<6I', *str_po_fell, *str_po_disc))
# Nombre de la trampa (pedido del usuario, 21/10/2026): la ciudad más cercana y un número de dos cifras («Afland01»).
# No se guarda (el registro no tiene lugar libre): se calcula al dar el aviso. Ciudad: la más cercana de todas
# (distancia de rey; en empate, la primera), también las arrasadas, para que el nombre no cambie durante la partida.
# Número: 1 + las trampas anteriores en la tabla con la misma ciudad; los registros nunca se borran y la tabla es la
# misma en todas las PC, así que el número tampoco cambia. Sin ciudades, el aviso fijo de antes.
# tr_city: esi = registro -> eax = ciudad o -1; preserva el resto.
tr_city = place('tr_city', f'''
    push ebx
    push ecx
    push edx
    push edi
    push ebp
    or edi, -1
    mov ebp, 0x7fffffff
    xor ebx, ebx
tcy_loop:
    movsx eax, word ptr [0x537e2a]
    cmp ebx, eax
    jge tcy_out
    imul ecx, ebx, 0xde
    movsx eax, word ptr [ecx + 0x537e2e]
    movsx edx, word ptr [esi + 2]
    sub eax, edx
    cdq
    xor eax, edx
    sub eax, edx
    push eax
    movsx eax, word ptr [ecx + 0x537e2c]
    movsx edx, word ptr [esi]
    sub eax, edx
    cdq
    xor eax, edx
    sub eax, edx
    pop ecx
    cmp eax, ecx
    jge tcy_d
    mov eax, ecx
tcy_d:
    cmp eax, ebp
    jge tcy_next
    mov ebp, eax
    mov edi, ebx
tcy_next:
    inc ebx
    jmp tcy_loop
tcy_out:
    mov eax, edi
    pop ebp
    pop edi
    pop edx
    pop ecx
    pop ebx
    ret
''')
QT_TYPE = 13   # misión «escoltar al equipo que desarma la trampa» (qt_*, más abajo)
# tr_id: edx = registro de trampa -> eax = ciudad del nombre (o -1, sin ciudades), ecx = número; preserva el resto.
tr_id = place('tr_id', f'''
    push ebx
    push esi
    mov esi, edx
    call {tr_city:#x}
    test eax, eax
    jl ti_out
    mov ebx, eax
    mov ecx, 1
    mov esi, {PO_TAB:#x}
ti_loop:
    cmp esi, edx
    jae ti_end
    cmp byte ptr [esi + 4], {PO_TRAMPA}
    jne ti_next
    call {tr_city:#x}
    cmp eax, ebx
    jne ti_next
    inc ecx
ti_next:
    add esi, {PO_REC}
    jmp ti_loop
ti_end:
    mov eax, ebx
ti_out:
    pop esi
    pop ebx
    ret
''')
TR_FMT = ('Your army fell into the trap %.20s%02d!', 'You have discovered the trap %.20s%02d!')
assert all(len(f % ('x' * 20, 99)) < 64 for f in TR_FMT)   # renglón de 0x4c2790; el nombre de ciudad, a 20
tr_fmtt = place_data('tr_fmtt', struct.pack('<2I', *(place_data(f'str_tr_fmt{i}', cstr_(f)) for i, f in enumerate(TR_FMT))))
# Aviso: eax = tipo, edx = registro, ecx = 0 caer / 1 descubrir. Pozo y remolino con su nombre, trampa con el suyo;
# preserva todo.
po_msg = place('po_msg', f'''
    pushad
    cmp eax, {PO_TRAMPA}
    jbe pm_t
    xor eax, eax
pm_t:
    lea esi, [ecx + ecx*2]
    add esi, eax
    mov esi, dword ptr [esi*4 + {po_gent:#x}]
    cmp eax, {PO_TRAMPA}
    jne pm_pozo
    mov ebx, ecx
    call {tr_id:#x}
    xchg ebx, ecx
    test eax, eax
    jl pm_show
    push ebx
    imul eax, eax, 0xde
    add eax, 0x537e30
    push eax
    push dword ptr [ecx*4 + {tr_fmtt:#x}]
    push {po_buf:#x}
    call dword ptr [{SPRINTF:#x}]
    add esp, 16
    mov esi, {po_buf:#x}
    jmp pm_show
pm_pozo:
    cmp eax, {PO_REMOLINO}
    ja pm_show
    movzx edx, byte ptr [edx + 5]
    and edx, dword ptr [eax*4 + {po_nmask:#x}]
    mov edi, dword ptr [eax*4 + {po_nmt:#x}]
    push dword ptr [edi + edx*4]
    lea edi, [ecx*2 + eax]
    push dword ptr [edi*4 + {po_fmtt:#x}]
    push {po_buf:#x}
    call dword ptr [{SPRINTF:#x}]
    add esp, 12
    mov esi, {po_buf:#x}
pm_show:
    push 0x14
    push esi
    call 0x4c2790
    add esp, 8
    popad
    ret
''')
PO_RADIO = 1    # pedido del usuario (21/10/2026): se descubren a una casilla, no con el radio del grupo
po_step = place('po_step', f'''
    pushad
    movsx ebx, word ptr [esp + 0x24]
    movsx esi, word ptr [esp + 0x28]
    movsx edi, word ptr [esp + 0x2c]
    cmp ebx, 8
    jae pt_end
    test esi, esi
    jl pt_end
    test edi, edi
    jl pt_end
    cmp si, word ptr [0x503e00]
    jge pt_end
    cmp di, word ptr [0x503e02]
    jge pt_end
    mov cl, byte ptr [0x503e06]
    shl edi, cl
    add edi, esi
    cmp edi, {PO_MAPSZ}
    jae pt_end
    movzx eax, byte ptr [edi + {po_map:#x}]
    test eax, eax
    jz pt_end
    cmp byte ptr [eax*8 + {PO_TAB - 8 + 4:#x}], {PO_TUMBA}
    je pt_end
    cmp byte ptr [eax*8 + {PO_TAB - 8 + 4:#x}], {PO_TRAMPA}
    jne pt_mark
    mov cl, byte ptr [eax*8 + {PO_TAB - 8 + 5:#x}]
    and cl, {TR_CUENTA}
    cmp cl, {TR_USOS}
    jae pt_end
pt_mark:
    mov byte ptr [ebx + {po_pend:#x}], al
    movzx ecx, byte ptr [eax*8 + {PO_TAB - 8 + 6:#x}]
    bt ecx, ebx
    setc cl
    mov byte ptr [ebx + {po_pvis:#x}], cl
pt_end:
    popad
    push dword ptr [esp + 0x10]
    push dword ptr [esp + 0x10]
    push dword ptr [esp + 0x10]
    push dword ptr [esp + 0x10]
    call 0x4a1ce0
    add esp, 0x10
    pushad
    test byte ptr [0x53c393], 0x10
    jz pd_end
    test byte ptr [0x53c393], 0x20
    jz pd_end
    mov ebp, {PO_RADIO}
    movsx eax, word ptr [0x4fe5e8]
    cmp eax, 5
    jl pd_c5
    sub eax, 5
pd_c5:
    test eax, eax
    jnz pd_end
    movsx ebx, word ptr [esp + 0x24]
    cmp ebx, 8
    jae pd_end
    imul eax, ebx, 0x4f0
    lea esi, [eax + 0x56ea94]
    movsx ecx, word ptr [eax + 0x56eaa8]
pd_gr:
    dec ecx
    js pd_end
    movsx eax, word ptr [esi + ecx*2]
    call {isfly:#x}
    test eax, eax
    jnz pd_gr
    movsx esi, word ptr [esp + 0x28]
    movsx edi, word ptr [esp + 0x2c]
    xor edx, edx
pd_po:
    cmp edx, dword ptr [{PO_N:#x}]
    jae pd_end
    movzx eax, byte ptr [edx*8 + {PO_TAB + 6:#x}]
    bt eax, ebx
    jc pd_pon
    cmp byte ptr [edx*8 + {PO_TAB + 4:#x}], {PO_TRAMPA}
    jne pd_act
    mov cl, byte ptr [edx*8 + {PO_TAB + 5:#x}]
    and cl, {TR_CUENTA}
    cmp cl, {TR_USOS}
    jae pd_pon
pd_act:
    movsx ecx, word ptr [edx*8 + {PO_TAB:#x}]
    sub ecx, esi
    jge pd_dx
    neg ecx
pd_dx:
    movsx eax, word ptr [edx*8 + {PO_TAB + 2:#x}]
    sub eax, edi
    jge pd_dy
    neg eax
pd_dy:
    add ecx, eax
    cmp ecx, ebp
    jle pd_hit
pd_pon:
    inc edx
    jmp pd_po
pd_hit:
    mov cl, bl
    mov al, 1
    shl al, cl
    or byte ptr [edx*8 + {PO_TAB + 6:#x}], al
    push edx
    call {REDRAW:#x}
    pop edx
    cmp word ptr [0x560b20], bx
    jne pd_end
    lea edx, [edx*8 + {PO_TAB:#x}]
    movzx eax, byte ptr [edx + 4]
    mov ecx, 1
    call {po_msg:#x}
pd_end:
    popad
    ret
''')
# Tumba (pedido del usuario, 20/10/2026): cada vez que muere un grupo en un pozo, po_fall suma un registro PO_TUMBA en
# una casilla al azar a 2 o menos (max |dx|,|dy|) del pozo, nunca en él ni en otra tumba, pozo o trampa (pg_ok), con
# una de las tres imágenes al azar (+5) y vista por todos (+6 = 0xff). El azar sale de la tabla misma (x, y y
# cantidad de registros), no del generador del juego: po_fall corre en todas las PC y tienen que elegir lo mismo.
# PO_GTRIES tiros; si ninguno sirve o la tabla está llena, no hay tumba. ebp = el registro del pozo; preserva todo.
PO_GTRIES = 32
po_grave = place('po_grave', f'''
    pushad
    mov eax, dword ptr [{PO_N:#x}]
    cmp eax, {PO_MAX}
    jae pv_end
    movsx esi, word ptr [ebp]
    movsx edi, word ptr [ebp + 2]
    imul ebx, esi, 0x9e3779b1
    imul ecx, edi, 0x85ebca77
    add ebx, ecx
    imul ecx, eax, 0xc2b2ae3d
    add ebx, ecx
    mov ebp, {PO_TUMBA}
    mov ecx, {PO_GTRIES}
pv_try:
    imul ebx, ebx, 1103515245
    add ebx, 12345
    mov eax, ebx
    shr eax, 16
    xor edx, edx
    push ecx
    mov ecx, 25
    div ecx
    pop ecx
    cmp edx, 12
    je pv_next
    mov eax, edx
    xor edx, edx
    push ecx
    mov ecx, 5
    div ecx
    pop ecx
    lea eax, [eax + edi - 2]
    lea edx, [edx + esi - 2]
    push esi
    push edi
    mov esi, edx
    mov edi, eax
    call {pg_ok:#x}
    jz pv_ok
    pop edi
    pop esi
pv_next:
    dec ecx
    jnz pv_try
    jmp pv_end
pv_ok:
    mov eax, dword ptr [{PO_N:#x}]
    lea edx, [eax*8 + {PO_TAB:#x}]
    mov word ptr [edx], si
    mov word ptr [edx + 2], di
    mov byte ptr [edx + 4], {PO_TUMBA}
    push edx
    mov eax, ebx
    shr eax, 24
    xor edx, edx
    mov ecx, 3
    div ecx
    mov eax, edx
    pop edx
    mov byte ptr [edx + 5], al
    mov word ptr [edx + 6], 0xffff
    inc dword ptr [{PO_N:#x}]
    call {po_rebuild:#x}
    pop edi
    pop esi
pv_end:
    popad
    ret
''')
# Daño de la trampa en tierra (pedido del usuario, 26/10/2026): en cada explosión muere entre el 40 y el 80 % de los
# ejércitos que caen (no voladores; tr_pct al azar, redondeado) y los demás quedan paralizados como con la habilidad
# Paralysis (0x46b205..0x46b272): sin pasos este turno (+0x11 & 0x7f = 0) y, si su movimiento (+0x12 & 0x7f) es 9 o
# más y no lo estaban ya, 5 pasos menos y el bit 0x80 de +0x15; al empezar su turno siguiente el juego les devuelve
# los 5 y quita el bit (0x434f5a). Quién muere: selección al azar sin reemplazo (r = azar % los que faltan; muere si
# r < las muertes que faltan). El grupo se detiene (0x485c00). La mina submarina sigue hundiendo todo. El azar es un
# generador propio (tr_rand) sembrado con la casilla, las explosiones, el jugador y los ejércitos que caen, no el
# del juego: po_fall corre en todas las PC y tienen que elegir lo mismo (como po_grave).
TR_PMIN, TR_PMAX = 40, 80
tr_var = place_data('tr_var', bytes(16))      # +0 semilla, +4 los que faltan, +8 muertes que faltan, +0xc modo (1 = parcial)
TR_SEED, TR_N, TR_K, TR_MODO = tr_var, tr_var + 4, tr_var + 8, tr_var + 0xc
tr_rand = place('tr_rand', f'''
    imul eax, dword ptr [{TR_SEED:#x}], 1103515245
    add eax, 12345
    mov dword ptr [{TR_SEED:#x}], eax
    shr eax, 16
    and eax, 0x7fff
    ret
''')
po_fall = place('po_fall', f'''
    pushad
    xor ebx, ebx
pf_pl:
    movzx eax, byte ptr [ebx + {po_pend:#x}]
    test eax, eax
    jz pf_pln
    mov byte ptr [ebx + {po_pend:#x}], 0
    lea ebp, [eax*8 + {PO_TAB - 8:#x}]
    mov dword ptr [{TR_MODO:#x}], 0
    cmp byte ptr [ebp + 4], {PO_TRAMPA}
    jne pf_go
    mov eax, ebp
    call {po_wet:#x}
    je pf_go
    movzx eax, word ptr [ebp + 2]
    shl eax, 16
    mov ax, word ptr [ebp]
    movzx ecx, byte ptr [ebp + 5]
    and ecx, {TR_CUENTA}
    imul ecx, ecx, 0x1000193
    xor eax, ecx
    imul ecx, ebx, 0x9e3779b9
    xor eax, ecx
    mov dword ptr [{TR_SEED:#x}], eax
    xor edi, edi
    mov esi, 1
pf_cn:
    movsx eax, word ptr [0x54fe50]
    cmp esi, eax
    jge pf_cnf
    imul edx, esi, 0x1c
    test byte ptr [edx + 0x54fe63], 0x40
    jz pf_cnn
    mov eax, dword ptr [edx + 0x54fe52]
    cmp eax, dword ptr [ebp]
    jne pf_cnn
    movzx eax, word ptr [edx + 0x54fe5e]
    shr eax, 5
    and eax, 0xf
    cmp eax, ebx
    jne pf_cnn
    mov eax, esi
    call {isfly:#x}
    test eax, eax
    jnz pf_cnn
    inc edi
    imul eax, dword ptr [{TR_SEED:#x}], 33
    add eax, esi
    mov dword ptr [{TR_SEED:#x}], eax
pf_cnn:
    inc esi
    jmp pf_cn
pf_cnf:
    test edi, edi
    jz pf_go
    mov dword ptr [{TR_N:#x}], edi
    call {tr_rand:#x}
    xor edx, edx
    mov ecx, {TR_PMAX - TR_PMIN + 1}
    div ecx
    add edx, {TR_PMIN}
    mov eax, edx
    imul eax, edi
    add eax, 50
    mov ecx, 100
    xor edx, edx
    div ecx
    mov dword ptr [{TR_K:#x}], eax
    mov dword ptr [{TR_MODO:#x}], 1
pf_go:
    xor edi, edi
    mov dword ptr [{po_kill:#x}], edi
    mov esi, 1
pf_ej:
    movsx eax, word ptr [0x54fe50]
    cmp esi, eax
    jge pf_ejf
    imul edx, esi, 0x1c
    test byte ptr [edx + 0x54fe63], 0x40
    jz pf_ejn
    mov eax, dword ptr [edx + 0x54fe52]
    cmp eax, dword ptr [ebp]
    jne pf_ejn
    movzx eax, word ptr [edx + 0x54fe5e]
    shr eax, 5
    and eax, 0xf
    cmp eax, ebx
    jne pf_ejn
    mov eax, esi
    call {isfly:#x}
    test eax, eax
    jnz pf_ejn
    cmp dword ptr [{TR_MODO:#x}], 0
    je pf_todo
    call {tr_rand:#x}
    xor edx, edx
    div dword ptr [{TR_N:#x}]
    dec dword ptr [{TR_N:#x}]
    cmp edx, dword ptr [{TR_K:#x}]
    jae pf_para
    dec dword ptr [{TR_K:#x}]
    push 0
    jmp pf_kill
pf_para:
    imul edx, esi, 0x1c
    and word ptr [edx + 0x54fe60], 0x80ff
    inc edi
    test byte ptr [edx + 0x54fe65], 0x80
    jnz pf_ejn
    mov ax, word ptr [edx + 0x54fe62]
    mov cx, ax
    and cx, 0x7f
    cmp cx, 9
    jb pf_ejn
    sub ax, 5
    mov word ptr [edx + 0x54fe62], ax
    or byte ptr [edx + 0x54fe65], 0x80
    jmp pf_ejn
pf_todo:
    push 1
    cmp byte ptr [ebp + 4], {PO_REMOLINO}
    je pf_kill
    cmp byte ptr [ebp + 4], {PO_TRAMPA}
    jne pf_seco
    mov eax, ebp
    call {po_wet:#x}
    je pf_kill
pf_seco:
    mov dword ptr [esp], 0
pf_kill:
    push esi
    call 0x46c470
    add esp, 8
    inc edi
    inc dword ptr [{po_kill:#x}]
pf_ejn:
    inc esi
    jmp pf_ej
pf_ejf:
    cmp dword ptr [{TR_MODO:#x}], 0
    je pf_cuenta
    push ebx
    call 0x485c00
    add esp, 4
pf_cuenta:
    test edi, edi
    jz pf_pln
    movzx eax, byte ptr [ebx + {po_pvis:#x}]
    imul eax, eax, 100
    add eax, dword ptr [{po_kill:#x}]
    push eax
    movsx eax, word ptr [ebp + 2]
    push eax
    movsx eax, word ptr [ebp]
    push eax
    push ebx
    movzx eax, byte ptr [ebp + 4]
    add eax, 18
    push eax
    call {ia_evt:#x}
    add esp, 0x14
    mov cl, bl
    mov al, 1
    shl al, cl
    or byte ptr [ebp + 6], al
    cmp byte ptr [ebp + 4], {PO_POZO}
    jne pf_trap
    call {po_grave:#x}
pf_trap:
    cmp byte ptr [ebp + 4], {PO_TRAMPA}
    jne pf_vis
    mov al, byte ptr [ebp + 5]
    and al, {TR_CUENTA}
    inc al
    mov ah, bl
    shl ah, 4
    or al, ah
    or al, {TR_RECIEN}
    mov byte ptr [ebp + 5], al
    mov eax, ebx
    shl eax, 4
    cmp byte ptr [eax + 0x55edc4], 0
    je pf_vis
    cmp word ptr [eax + 0x55edc8], {QT_TYPE}
    jne pf_vis
    lea edx, [ebp - {PO_TAB:#x}]
    shr edx, 3
    cmp word ptr [eax + 0x55edca], dx
    jne pf_vis
    mov word ptr [eax + 0x55edce], 1
pf_vis:
    call 0x441290
    call {REDRAW:#x}
    cmp word ptr [0x560b20], bx
    jne pf_pln
    movzx eax, byte ptr [ebp + 4]
    mov edx, ebp
    xor ecx, ecx
    call {po_msg:#x}
    cmp byte ptr [ebp + 4], {PO_TRAMPA}
    jne pf_die
    test byte ptr [0x564d08], 0x20
    jz pf_die
    push {PO_SND}
    mov ecx, 0x5a6f50
    call 0x4eca00
    test eax, eax
    jz pf_die
    push 0
    mov ecx, eax
    push 0
    call 0x4e6fd0
pf_die:
    rdtsc
    shr eax, 8
    and eax, 1
    push eax
    push 7
    call 0x4465e0
    add esp, 8
pf_pln:
    inc ebx
    cmp ebx, 8
    jl pf_pl
    popad
    jmp 0x49d1a0
''')

# ---------------------------------------------------------------- Misión dura «escoltar al equipo que desarma una trampa»
# Tipo nuevo QT_TYPE (13); en el registro de la misión (0x55edc4 + jugador*16): +6 = índice de la trampa en PO_TAB,
# +8 = su dueño, +0xa = 1 cuando la detonó un ejército del jugador (po_fall; el generador lo deja en 0). Recorrido:
# - Generador 0x45ec40, dificultad Hard (0x45f4f6): qt_hard tira 0..6 en vez de 0..5 si hay alguna trampa candidata
#   (entera, descubierta por el jugador, de otro dueño que pase 0x461080, a distancia de rey 2..4Q+23 del héroe); el 6
#   es esta misión, con una de ellas al azar. Solo para humanos y si el tipo no está ya ofrecido; sin candidatas, la
#   tirada es la del original (0..5) y todo sigue igual.
# - Cumplida (evento 5, el héroe llegó a una casilla, 0x461fee): trampa detonada por el jugador (+0xa), el héroe a una
#   casilla o menos de la trampa, en tierra (no agua) y sin volar (isfly del héroe, grpfly del grupo que se mueve).
# - Fracasada (evento 0, cada turno, 0x461d0c): la trampa está detonada y no fue el jugador.
# - Textos: nombre del tipo (0x461163) «Escort trap-disarming team to Afland02» (ciudad y número como en po_msg; el
#   renglón más corto que lo recibe es de 0x40 bytes y esto llega a 52) y el objetivo (0x461432).
# - Premio: el switch de 0x46231d solo trata 7..11; el 13 toma el de por defecto, como los otros tipos. Los lectores
#   del tipo en la IA (0x40ee41, 0x41d084, 0x41d31e, 0x41dca8, 0x41df13, 0x435fd0, 0x436390) van por su default: la
#   IA no la recibe, y si toma un jugador que la tenía, la ignora.
QT_NAME = 'Escort trap-disarming team to %.20s%02d'
assert len(QT_NAME % ('x' * 20, 99)) < 0x40
str_qt_name = place_data('str_qt_name', cstr_(QT_NAME))
str_qt_name0 = place_data('str_qt_name0', cstr_('Escort trap-disarming team'))
str_qt_obj = place_data('str_qt_obj', cstr_('%s must escort a trap-disarming team to the trap %.20s%02d.'))
str_qt_obj0 = place_data('str_qt_obj0', cstr_('%s must escort a trap-disarming team to a trap.'))
# eax = jugador, ecx = x y edx = y del héroe, edi = cuál (-1: ninguna) -> ebp = candidatas contadas antes de la pedida
# (con -1, todas), esi = índice de la pedida o -1. Preserva ebx, edi.
qt_scan = place('qt_scan', f'''
    push ebx
    push edx
    push ecx
    push eax
    xor ebp, ebp
    or esi, -1
    xor ebx, ebx
qs_loop:
    cmp ebx, dword ptr [{PO_N:#x}]
    jge qs_end
    cmp ebx, {PO_MAX}
    jge qs_end
    lea edx, [ebx*8 + {PO_TAB:#x}]
    cmp byte ptr [edx + 4], {PO_TRAMPA}
    jne qs_next
    mov al, byte ptr [edx + 5]
    and al, {TR_CUENTA}
    cmp al, {TR_USOS}
    jae qs_next
    mov eax, edx
    call {po_wet:#x}
    je qs_next
    mov ecx, dword ptr [esp]
    movzx eax, byte ptr [edx + 6]
    bt eax, ecx
    jnc qs_next
    movzx eax, byte ptr [edx + 7]
    cmp eax, ecx
    je qs_next
    movsx eax, word ptr [edx]
    sub eax, dword ptr [esp + 4]
    cdq
    xor eax, edx
    sub eax, edx
    mov ecx, eax
    lea edx, [ebx*8 + {PO_TAB:#x}]
    movsx eax, word ptr [edx + 2]
    sub eax, dword ptr [esp + 8]
    cdq
    xor eax, edx
    sub eax, edx
    cmp eax, ecx
    jge qs_d
    mov eax, ecx
qs_d:
    cmp eax, 2
    jl qs_next
    movsx ecx, word ptr [0x56950a]
    lea ecx, [ecx*4 + 0x17]
    cmp eax, ecx
    jg qs_next
    movzx eax, byte ptr [ebx*8 + {PO_TAB + 7:#x}]
    push eax
    call 0x461080
    add esp, 4
    test al, al
    jz qs_next
    cmp ebp, edi
    je qs_found
    inc ebp
qs_next:
    inc ebx
    jmp qs_loop
qs_found:
    mov esi, ebx
qs_end:
    pop eax
    pop ecx
    pop edx
    pop ebx
    ret
''')
# Reemplaza 0x45f4f6..0x45f517 (la tirada 0..5 y el salto por la tabla 0x46101c). +0x10 por los cuatro push.
qt_hard = place('qt_hard', f'''
    push ebx
    push esi
    push edi
    push ebp
    xor ebp, ebp
    movsx eax, word ptr [esp + 0x26]
    imul edx, eax, 0x1f8
    cmp word ptr [edx + 0x536c12], -1
    jne qth_roll
    movsx ecx, word ptr [esp + 0x258]
    mov edx, dword ptr [esp + 0x254]
qth_used:
    dec ecx
    jl qth_count
    cmp word ptr [edx + ecx*2], {QT_TYPE}
    je qth_roll
    jmp qth_used
qth_count:
    movsx ecx, word ptr [esp + 0x2a]
    movsx edx, word ptr [esp + 0x28]
    or edi, -1
    call {qt_scan:#x}
qth_roll:
    xor eax, eax
    test ebp, ebp
    setnz al
    add eax, 6
    push -1
    push eax
    push 1
    call 0x4deb20
    add esp, 0xc
    movsx eax, ax
    cmp eax, 6
    je qth_trap
    pop ebp
    pop edi
    pop esi
    pop ebx
    cmp eax, 5
    ja 0x45fd6f
    jmp dword ptr [eax*4 + 0x46101c]
qth_trap:
    push -1
    push ebp
    push 1
    call 0x4deb20
    add esp, 0xc
    movsx edi, ax
    movsx eax, word ptr [esp + 0x26]
    movsx ecx, word ptr [esp + 0x2a]
    movsx edx, word ptr [esp + 0x28]
    call {qt_scan:#x}
    test esi, esi
    jl qth_out
    mov word ptr [esp + 0x34], {QT_TYPE}
    mov word ptr [esp + 0x36], si
    movzx eax, byte ptr [esi*8 + {PO_TAB + 7:#x}]
    mov word ptr [esp + 0x38], ax
    mov byte ptr [esp + 0x21], 1
qth_out:
    pop ebp
    pop edi
    pop esi
    pop ebx
    jmp 0x45fd6f
''')
# Nombre del tipo (0x461163; ebx = renglón, [esp+0x10] = misión).
qt_name = place('qt_name', f'''
    cmp eax, {QT_TYPE}
    je qtn
    dec eax
    cmp eax, 0xb
    ja 0x4613c8
    jmp dword ptr [eax*4 + 0x4613cc]
qtn:
    mov eax, dword ptr [esp + 0x10]
    movzx edx, word ptr [eax + 6]
    cmp edx, {PO_MAX}
    jae qtn0
    lea edx, [edx*8 + {PO_TAB:#x}]
    call {tr_id:#x}
    test eax, eax
    jl qtn0
    push ecx
    imul eax, eax, 0xde
    add eax, 0x537e30
    push eax
    push {str_qt_name:#x}
    push ebx
    call dword ptr [{SPRINTF:#x}]
    add esp, 16
    jmp 0x4613c8
qtn0:
    push {str_qt_name0:#x}
    push ebx
    call dword ptr [{SPRINTF:#x}]
    add esp, 8
    jmp 0x4613c8
''')
# Objetivo (0x461432; ebx = renglón, edi = misión; sale por el epílogo 0x461a20).
qt_text = place('qt_text', f'''
    movsx eax, word ptr [edi + 4]
    cmp eax, {QT_TYPE}
    je qtt
    dec eax
    cmp eax, 0xb
    ja 0x461a20
    jmp dword ptr [eax*4 + 0x461a28]
qtt:
    movsx eax, word ptr [edi + 2]
    imul eax, eax, 0x1c
    movzx eax, word ptr [eax + 0x54fe62]
    and eax, 0x3f00
    shr eax, 8
    imul esi, eax, 0xb8
    add esi, 0x556bb4
    movzx edx, word ptr [edi + 6]
    cmp edx, {PO_MAX}
    jae qtt0
    lea edx, [edx*8 + {PO_TAB:#x}]
    call {tr_id:#x}
    test eax, eax
    jl qtt0
    push ecx
    imul eax, eax, 0xde
    add eax, 0x537e30
    push eax
    push esi
    push {str_qt_obj:#x}
    push ebx
    call dword ptr [{SPRINTF:#x}]
    add esp, 0x14
    jmp 0x461a20
qtt0:
    push esi
    push {str_qt_obj0:#x}
    push ebx
    call dword ptr [{SPRINTF:#x}]
    add esp, 0xc
    jmp 0x461a20
''')
# Fracaso (0x461d0c; cx = tipo, esi = misión): detonada por otro.
qt_fail = place('qt_fail', f'''
    cmp cx, {QT_TYPE}
    je qtf
    cmp cx, 0xb
    jne 0x461d5d
    jmp 0x461d12
qtf:
    movzx eax, word ptr [esi + 6]
    cmp eax, {PO_MAX}
    jae 0x461d5d
    mov cl, byte ptr [eax*8 + {PO_TAB + 5:#x}]
    and cl, {TR_CUENTA}
    cmp cl, {TR_USOS}
    jb 0x461d5d
    cmp word ptr [esi + 0xa], 0
    jne 0x461d5d
    jmp 0x461d4d
''')
# Cumplida (0x461fee, evento 5; esi = misión, edi = jugador, x [esp+0x24], y [esp+0x28]; ebp libre).
qt_arrive = place('qt_arrive', f'''
    mov ax, word ptr [esi + 4]
    cmp ax, {QT_TYPE}
    je qta
    cmp ax, 1
    jne 0x462062
    jmp 0x461ff8
qta:
    cmp word ptr [esi + 0xa], 0
    je 0x462168
    movzx ebp, word ptr [esi + 6]
    cmp ebp, {PO_MAX}
    jae 0x462168
    lea ebp, [ebp*8 + {PO_TAB:#x}]
    movsx eax, word ptr [esp + 0x24]
    movsx ecx, word ptr [ebp]
    sub eax, ecx
    inc eax
    cmp eax, 2
    ja 0x462168
    movsx eax, word ptr [esp + 0x28]
    movsx ecx, word ptr [ebp + 2]
    sub eax, ecx
    inc eax
    cmp eax, 2
    ja 0x462168
    movsx eax, word ptr [esp + 0x28]
    imul eax, eax, 10
    mov cl, byte ptr [0x503e06]
    shl eax, cl
    movsx ecx, word ptr [esp + 0x24]
    imul ecx, ecx, 10
    movzx edx, word ptr [eax + ecx + 0x503e58]
    and edx, 0x1f
    imul edx, edx, 0x58
    cmp word ptr [edx + 0x535f0c], 1
    je 0x462168
    movsx eax, word ptr [esi + 2]
    call {isfly:#x}
    test eax, eax
    jnz 0x462168
    mov eax, edi
    call {grpfly:#x}
    test eax, eax
    jnz 0x462168
    jmp 0x462055
''')

# Dibujo. La vista del mapa (0x459790, ebp = la vista) recorre sus celdas en dos pasadas; la 1.ª pinta el terreno, la
# ruina (0x45c0e0) y el sitio, por debajo de los ejércitos. po_draw va entre la ruina y el sitio (reemplaza
# 0x459b95..0x459b9a; esi = celda, [esp+0x14] columna, [esp+0x16] fila, [esp+0x18] x y [esp+0x1a] y en pantalla; la
# casilla es (columna + [ebp+0x28], fila + [ebp+0x2a]), las mismas que 0x45857e copia a las celdas). Solo llegan las
# celdas visibles (Hidden Map). Se dibuja si quien mira ([0x560b20]) lo descubrió (bit en +6) o, si es una trampa, si
# es su dueño o un aliado mutuo con vista aliada (fogally); una trampa gastada, todos. Cuadro de 48x48 de la hoja PO_FILE (RUINS\pozos.pcx, el
# 11 es transparente): 0 pozo, 1..4 sin uso, 5 trampa (mina), 6..9 agujero con humo (trampa recién explotada o gastada, animado con la fase del agua), 10..12 tumba, lápida y cruz
# (+5 del registro), PO_REMO0.. remolino, PO_MINAGUA mina submarina (trampa en agua sin puente, po_wet: no deja
# rastro; recién explotada o gastada no se dibuja). El remolino se anima como el agua con la fase [ebp+0x3c] & 3
# que 0x456fdc avanza cada tic de la animación del mapa. El remolino ocupa 3x3 casillas (pedido del usuario,
# 22/10/2026; solo mata la del medio): cada celda de agua sin edificio ni estructura pinta, por cada remolino
# descubierto en ella o en una de sus 8 vecinas, la pieza (dy + 1) * 3 + (dx + 1) de esa fase, con (dx, dy) = celda -
# remolino; sobre tierra, costa o puente esa pieza no se pinta. Al descubrirlo se redibuja el mapa entero (REDRAW),
# así que las vecinas se actualizan. La hoja se carga (0x4dd3f0) la
# primera vez que hace falta, o de nuevo si el juego la descargó; si no se puede, no se insiste.
PO_FILE = RAM_FILE + 3       # después de sorteo.pcx y darkcomp.pcx (ver table_add, más abajo)
PO_REMO0 = 13                # remolino grande: 4 fases x 9 piezas (3x3), desde el cuadro 13
PO_MINAGUA = PO_REMO0 + 36   # mina submarina
PO_FRAMES = PO_MINAGUA + 1
# po_vecs[k]: (dy << 4) | (dx & 15) de la pieza k = (dy + 1) * 3 + (dx + 1), con (dx, dy) = celda - remolino
po_vecs = place_data('po_vecs', bytes(((k // 3 - 1) << 4 | (k % 3 - 1) & 15) & 0xff for k in range(9)))
po_nosheet = place_data('po_nosheet', bytes(4))
po_cx = place_data('po_cx', bytes(8))   # casilla (x, y) y lugar en pantalla (x, y) de la celda que se dibuja
# De noche (opción Day/Night, SHOPT & 2, vuelta par; pedido del usuario, 28/10/2026) el pozo y el remolino no se
# copian: 0x4ee3c0 recolorea el fondo con po_ntab usando su dibujo de máscara (como cam_blit), así queda solo una
# sombra de su forma (el fondo al 65 %), que la noche oscurece después como al resto. Trampas y tumbas, como siempre.
def po_ntable():
    pal = open(os.path.join(os.path.dirname(SRC_EXE), 'war3.pal'), 'rb').read()
    rgb = [tuple(pal[3 * i:3 * i + 3]) for i in range(256)]
    cand = [10] + [i for i in range(16, 245) if i != 187]
    out = bytearray(range(256))
    for i in range(256):
        if i == 11: continue
        t = tuple(c * 0.65 for c in rgb[i])
        out[i] = min(cand, key=lambda j: sum((a - c) ** 2 for a, c in zip(rgb[j], t)))
    return bytes(out)
PO_NTAB = po_ntable()
po_ntab = place_data('po_ntab', PO_NTAB)
# po_night: ZF = 0 de noche (Day/Night puesto y vuelta par). Solo toca eflags.
po_night = place('po_night', f'''
    test byte ptr [{SHOPT:#x}], 2
    jz pn_day
    test byte ptr [{0x5032f8 + 0x30:#x}], 1
    jnz pn_no
    test esp, esp
    ret
pn_no:
    cmp esp, esp
pn_day:
    ret
''')
# pw_put: edi = cuadro de la hoja, ebx = registro -> lo pinta en la celda; preserva ebp.
pw_put = place('pw_put', f'''
    cmp dword ptr [{po_nosheet:#x}], 0
    jne pp_end
    push {PO_FILE}
    mov ecx, 0x58cf78
    call 0x4e4a90
    test eax, eax
    jz pp_fail
    cmp dword ptr [eax + 8], 0
    jne pp_blit
    push {PO_FILE}
    call 0x4dd3f0
    add esp, 4
    test eax, eax
    jnz pp_blit
pp_fail:
    mov dword ptr [{po_nosheet:#x}], 1
    jmp pp_end
pp_blit:
    movsx eax, word ptr [{po_cx + 6:#x}]
    push eax
    movsx eax, word ptr [{po_cx + 4:#x}]
    push eax
    push 0x27
    push 48
    push 48
    push 0
    imul edi, edi, 48
    push edi
    push {PO_FILE}
    cmp byte ptr [ebx + 4], {PO_REMOLINO}
    ja pp_copy
    call {po_night:#x}
    jz pp_copy
    push {po_ntab:#x}
    push dword ptr [esp + 0x20]
    push dword ptr [esp + 0x20]
    push dword ptr [esp + 0x20]
    push dword ptr [esp + 0x20]
    push dword ptr [esp + 0x20]
    push dword ptr [esp + 0x20]
    push dword ptr [esp + 0x20]
    push dword ptr [esp + 0x20]
    call 0x4ee3c0
    add esp, 0x44
    jmp pp_end
pp_copy:
    call 0x4dd530
    add esp, 0x20
pp_end:
    ret
''')
po_draw = place('po_draw', f'''
    pushad
    movsx eax, word ptr [esp + 0x34]
    movsx ecx, word ptr [ebp + 0x28]
    add eax, ecx
    movsx edx, word ptr [esp + 0x36]
    movsx ecx, word ptr [ebp + 0x2a]
    add edx, ecx
    mov word ptr [{po_cx:#x}], ax
    mov word ptr [{po_cx + 2:#x}], dx
    mov cx, word ptr [esp + 0x38]
    mov word ptr [{po_cx + 4:#x}], cx
    mov cx, word ptr [esp + 0x3a]
    mov word ptr [{po_cx + 6:#x}], cx
    test eax, eax
    jl pw_end
    test edx, edx
    jl pw_end
    cmp ax, word ptr [0x503e00]
    jge pw_end
    cmp dx, word ptr [0x503e02]
    jge pw_end
    movsx ecx, word ptr [0x560b20]
    cmp ecx, 8
    jae pw_end
    mov cl, byte ptr [0x503e06]
    lea esi, [edx + edx*4]
    add esi, esi
    shl esi, cl
    lea edi, [eax + eax*4]
    lea esi, [esi + edi*2 + 0x503e58]
    movzx edi, word ptr [esi]
    test edi, 0x4000
    jnz pw_own
    test byte ptr [esi + 3], 7
    jnz pw_own
    and edi, 0x1f
    imul edi, edi, 0x58
    cmp word ptr [edi + 0x535f0c], 1
    jne pw_own
    mov esi, 8
pw_vec:
    movzx eax, byte ptr [esi + {po_vecs:#x}]
    movsx edi, al
    sar edi, 4
    shl eax, 28
    sar eax, 28
    movsx ecx, word ptr [{po_cx:#x}]
    sub ecx, eax
    jl pw_vnext
    cmp cx, word ptr [0x503e00]
    jge pw_vnext
    movsx edx, word ptr [{po_cx + 2:#x}]
    sub edx, edi
    jl pw_vnext
    cmp dx, word ptr [0x503e02]
    jge pw_vnext
    push ecx
    mov cl, byte ptr [0x503e06]
    shl edx, cl
    pop ecx
    add edx, ecx
    cmp edx, {PO_MAPSZ}
    jae pw_vnext
    movzx eax, byte ptr [edx + {po_map:#x}]
    test eax, eax
    jz pw_vnext
    lea ebx, [eax*8 + {PO_TAB - 8:#x}]
    cmp byte ptr [ebx + 4], {PO_REMOLINO}
    jne pw_vnext
    movzx eax, byte ptr [ebx + 6]
    movsx edx, word ptr [0x560b20]
    bt eax, edx
    jnc pw_vnext
    movzx edi, word ptr [ebp + 0x3c]
    and edi, 3
    imul edi, edi, 9
    lea edi, [edi + esi + {PO_REMO0}]
    call {pw_put:#x}
pw_vnext:
    dec esi
    jns pw_vec
pw_own:
    movsx eax, word ptr [{po_cx:#x}]
    movsx edx, word ptr [{po_cx + 2:#x}]
    mov cl, byte ptr [0x503e06]
    shl edx, cl
    add edx, eax
    cmp edx, {PO_MAPSZ}
    jae pw_end
    movzx eax, byte ptr [edx + {po_map:#x}]
    test eax, eax
    jz pw_end
    lea ebx, [eax*8 + {PO_TAB - 8:#x}]
    movsx edx, word ptr [0x560b20]
    movzx eax, byte ptr [ebx + 6]
    bt eax, edx
    jc pw_vis
    cmp byte ptr [ebx + 4], {PO_TRAMPA}
    jne pw_end
    mov al, byte ptr [ebx + 5]
    and al, {TR_CUENTA}
    cmp al, {TR_USOS}
    jae pw_vis
    movzx ecx, byte ptr [ebx + 7]
    cmp ecx, edx
    je pw_vis
    call {fogally:#x}
    jne pw_end
pw_vis:
    movzx eax, byte ptr [ebx + 4]
    xor edi, edi
    cmp eax, {PO_REMOLINO}
    je pw_end
    cmp eax, {PO_TRAMPA}
    jne pw_tumba
    mov eax, ebx
    call {po_wet:#x}
    jne pw_seca
    mov al, byte ptr [ebx + 5]
    test al, {TR_RECIEN}
    jnz pw_end
    and al, {TR_CUENTA}
    cmp al, {TR_USOS}
    jae pw_end
    mov edi, {PO_MINAGUA}
    jmp pw_sheet
pw_seca:
    mov edi, 5
    mov al, byte ptr [ebx + 5]
    test al, {TR_RECIEN}
    jnz pw_humo
    and al, {TR_CUENTA}
    cmp al, {TR_USOS}
    jb pw_sheet
pw_humo:
    movzx edi, word ptr [ebp + 0x3c]
    and edi, 3
    add edi, 6
    jmp pw_sheet
pw_tumba:
    cmp eax, {PO_TUMBA}
    jne pw_sheet
    movzx edi, byte ptr [ebx + 5]
    cmp edi, 2
    ja pw_end
    add edi, 10
pw_sheet:
    call {pw_put:#x}
pw_end:
    popad
    cmp byte ptr [esi + 0x10], 0
    je 0x459bb9
    jmp 0x459b9b
''')

# Lupa y botón derecho (pedido del usuario, 22/10/2026): como en ruinas y sitios. El decodificador de clic/cursor
# 0x4735c0, sin grupo elegido, devuelve 0x14 en una ruina descubierta (cursor 9, la lupa, por las tablas 0x4c00f8 /
# 0x4c00c0 de 0x4bf88d; acción 0x4741d9 de 0x473e80 = cuadro de ruinas 0x4a4980), 0x15 en un sitio (la misma lupa,
# 0x4287d0) y 3 si no hay nada (0x473dc8). Ahí, si quien mira ([0x560b20], el de po_draw) ve dibujado un pozo,
# remolino o trampa en la casilla, po_cur devuelve 0x14 y anota el registro en po_info_r; ciudad, ruina y sitio
# siguen primero. En la acción 0x14, po_info abre el cuadro de información del juego, 0x4c7a10(título, texto, x, y del
# mouse; el que usan los diálogos para el botón derecho): nombre y tipo; en la trampa, las explosiones que le quedan.
# Con un grupo elegido el decodificador da mover, como en las ruinas. Las tumbas no tienen cuadro. De noche
# (po_night) ni ruinas, ni pozos, remolinos o trampas dan lupa (ver po_curclr); ciudades y sitios sí.
# po_look: eax = x, edx = y -> eax = registro que quien mira ve dibujado en esa casilla, o 0 (misma regla que
# po_draw). po_find: además, el remolino de una casilla vecina de agua (su dibujo ocupa 3x3). Preservan el resto.
po_look = place('po_look', f'''
    push ebx
    push ecx
    push edx
    test eax, eax
    jl pl_no
    test edx, edx
    jl pl_no
    cmp ax, word ptr [0x503e00]
    jge pl_no
    cmp dx, word ptr [0x503e02]
    jge pl_no
    mov cl, byte ptr [0x503e06]
    shl edx, cl
    add edx, eax
    cmp edx, {PO_MAPSZ}
    jae pl_no
    movzx eax, byte ptr [edx + {po_map:#x}]
    test eax, eax
    jz pl_no
    lea ebx, [eax*8 + {PO_TAB - 8:#x}]
    movsx edx, word ptr [0x560b20]
    cmp edx, 8
    jae pl_no
    mov al, byte ptr [ebx + 4]
    cmp al, {PO_TRAMPA}
    ja pl_no
    movzx ecx, byte ptr [ebx + 6]
    bt ecx, edx
    jc pl_vis
    cmp al, {PO_TRAMPA}
    jne pl_no
    mov cl, byte ptr [ebx + 5]
    and cl, {TR_CUENTA}
    cmp cl, {TR_USOS}
    jae pl_vis
    movzx ecx, byte ptr [ebx + 7]
    cmp ecx, edx
    je pl_vis
    call {fogally:#x}
    jne pl_no
pl_vis:
    cmp byte ptr [ebx + 4], {PO_TRAMPA}
    jne pl_yes
    mov eax, ebx
    call {po_wet:#x}
    jne pl_yes
    mov al, byte ptr [ebx + 5]
    test al, {TR_RECIEN}
    jnz pl_no
    and al, {TR_CUENTA}
    cmp al, {TR_USOS}
    jae pl_no
pl_yes:
    mov eax, ebx
    jmp pl_out
pl_no:
    xor eax, eax
pl_out:
    pop edx
    pop ecx
    pop ebx
    ret
''')
po_fxy = place_data('po_fxy', bytes(4))   # casilla para po_wet (registro de mentira: x, y)
po_find = place('po_find', f'''
    push ebx
    push esi
    push edi
    mov ebx, eax
    mov edi, edx
    call {po_look:#x}
    test eax, eax
    jnz pf2_out
    mov word ptr [{po_fxy:#x}], bx
    mov word ptr [{po_fxy + 2:#x}], di
    mov eax, {po_fxy:#x}
    call {po_wet:#x}
    jne pf2_none
    mov esi, 8
pf2_vec:
    movzx eax, byte ptr [esi + {po_vecs:#x}]
    movsx edx, al
    sar edx, 4
    shl eax, 28
    sar eax, 28
    neg eax
    add eax, ebx
    neg edx
    add edx, edi
    call {po_look:#x}
    test eax, eax
    jz pf2_next
    cmp byte ptr [eax + 4], {PO_REMOLINO}
    je pf2_out
pf2_next:
    dec esi
    jns pf2_vec
pf2_none:
    xor eax, eax
pf2_out:
    pop edi
    pop esi
    pop ebx
    ret
''')
# La IA ante los pozos (ia\PENDIENTE-ia-innovaciones.md, paso 3; decisión del usuario del 19/10/2026): en el buscador
# de caminos (0x4a5c40, por cada casilla vecina, en 0x4a5d34: di = x, bx = y) un pozo, remolino o trampa activa que el
# jugador del camino ([0x58715c]) ve es intransitable: bit suyo en +6 o, en una trampa, ser su dueño o su aliado con
# vista aliada (lo mismo que po_look, sin la excepción de dibujo de TR_RECIEN: el que la conoce sabe que sigue
# armada). Las tumbas y las trampas gastadas no cuentan. Excepción: la ruta expresa de un humano (0x536c12 = -1) a esa
# misma casilla (el destino del camino, [0x5878d4] / [0x5878d8]) sí llega, y cae. La computadora no tiene esa
# excepción: nunca entra en uno que ve, tampoco por el ítem que dejó un caído. Lo usan también el mapa de distancias
# de la IA (0x497750 -> 0x4a53b0) y el camino del humano. Preserva ebx, esi, edi, ebp; eax, ecx, edx los rehace lo
# reemplazado (0x4a5d34..0x4a5d40).
po_pf = place('po_pf', f'''
    movsx eax, di
    movsx edx, bx
    test eax, eax
    jl ppf_go
    test edx, edx
    jl ppf_go
    cmp ax, word ptr [0x503e00]
    jge ppf_go
    cmp dx, word ptr [0x503e02]
    jge ppf_go
    mov cl, byte ptr [0x503e06]
    shl edx, cl
    add edx, eax
    cmp edx, {PO_MAPSZ}
    jae ppf_go
    movzx eax, byte ptr [edx + {po_map:#x}]
    test eax, eax
    jz ppf_go
    push ebx
    lea ebx, [eax*8 + {PO_TAB - 8:#x}]
    movsx edx, word ptr [0x58715c]
    cmp edx, 8
    jae ppf_pass
    mov al, byte ptr [ebx + 4]
    cmp al, {PO_TRAMPA}
    ja ppf_pass
    jne ppf_vis
    mov cl, byte ptr [ebx + 5]
    and cl, {TR_CUENTA}
    cmp cl, {TR_USOS}
    jae ppf_pass
ppf_vis:
    movzx ecx, byte ptr [ebx + 6]
    bt ecx, edx
    jc ppf_seen
    cmp al, {PO_TRAMPA}
    jne ppf_pass
    movzx ecx, byte ptr [ebx + 7]
    cmp ecx, edx
    je ppf_seen
    call {fogally:#x}
    jne ppf_pass
ppf_seen:
    pop ebx
    imul eax, edx, {SIDE:#x}
    cmp word ptr [eax + {SIDE_HUMAN:#x}], -1
    jne 0x4a5e31
    cmp di, word ptr [0x5878d4]
    jne 0x4a5e31
    cmp bx, word ptr [0x5878d8]
    jne 0x4a5e31
    jmp ppf_go
ppf_pass:
    pop ebx
ppf_go:
    movsx edx, di
    lea eax, [edx + edx*4]
    shl eax, 5
    movsx ecx, bx
    jmp 0x4a5d40
''')
po_info_r = place_data('po_info_r', bytes(4))
# En 0x473dc8 (lo que queda: código 3). [esp+0x2c] / [esp+0x2e] = casilla; 0x473d7e la escribe y devuelve 0x14.
po_cur = place('po_cur', f'''
    call {po_night:#x}
    jnz pc_none
    movsx eax, word ptr [esp + 0x2c]
    movsx edx, word ptr [esp + 0x2e]
    call {po_find:#x}
    mov dword ptr [{po_info_r:#x}], eax
    test eax, eax
    jnz 0x473d7e
pc_none:
    mov ax, word ptr [esp + 0x38]
    jmp 0x473dcd
''')
# En 0x473d32 (antes de ciudad, ruina y sitio): el 0x14 de una ruina de verdad no es nuestro. De noche (po_night)
# ruinas, pozos, remolinos y trampas no dan lupa (pedido del usuario, 28/10/2026): se salta la ruina y po_cur
# da 3. Ciudades (encendidas) y sitios (puertos, establos, altares...) siguen con la suya.
po_curclr = place('po_curclr', f'''
    mov dword ptr [{po_info_r:#x}], 0
    test bp, bp
    jge 0x473d37
    call {po_night:#x}
    jz 0x473d76
    jmp 0x473d9f
''')
PI_TXT = ('A hidden pit. Any army that steps into it dies; only flyers are safe.',
          'A whirlpool. Any ship that sails into its eye sinks with all aboard; only flyers are safe.')
PI_TRFMT = (f'A mine. Explosions left: %d of {TR_USOS}.', f'A sea mine. Explosions left: %d of {TR_USOS}.')
PI_SPENT = 'A spent mine: it will not explode again.'
PI_TRAP, PI_TRNM = 'Trap %.20s%02d', 'Trap'
assert len(PI_TRAP % ('x' * 20, 99)) < 64   # el título del cuadro se copia a 63 (0x4f0f40)
pi_txtt = place_data('pi_txtt', struct.pack('<2I', *(place_data(f'str_pi_txt{i}', cstr_(s)) for i, s in enumerate(PI_TXT))))
pi_trft = place_data('pi_trft', struct.pack('<2I', *(place_data(f'str_pi_trf{i}', cstr_(s)) for i, s in enumerate(PI_TRFMT))))
str_pi_spent = place_data('str_pi_spent', cstr_(PI_SPENT))
str_pi_trap = place_data('str_pi_trap', cstr_(PI_TRAP))
str_pi_trnm = place_data('str_pi_trnm', cstr_(PI_TRNM))
str_pi_s = place_data('str_pi_s', cstr_('%.63s'))
pi_tit = place_data('pi_tit', bytes(64))
pi_txt = place_data('pi_txt', bytes(64))
# En 0x4741d9 (acción 0x14; [esp+0x1c] / [esp+0x20] = x, y del mouse). Vuelve por 0x4741f3, que restaura todo.
po_info = place('po_info', f'''
    call 0x4a2170
    mov ebx, dword ptr [{po_info_r:#x}]
    test ebx, ebx
    jz 0x4741de
    mov dword ptr [{po_info_r:#x}], 0
    movzx ebp, byte ptr [ebx + 4]
    cmp ebp, {PO_TRAMPA}
    je pi_trap
    movzx edx, byte ptr [ebx + 5]
    and edx, dword ptr [ebp*4 + {po_nmask:#x}]
    mov edi, dword ptr [ebp*4 + {po_nmt:#x}]
    push dword ptr [edi + edx*4]
    push {str_pi_s:#x}
    push {pi_tit:#x}
    call dword ptr [{SPRINTF:#x}]
    add esp, 12
    mov al, byte ptr [{pi_tit:#x}]
    cmp al, 0x61
    jb pi_cap
    cmp al, 0x7a
    ja pi_cap
    sub byte ptr [{pi_tit:#x}], 0x20
pi_cap:
    mov esi, dword ptr [ebp*4 + {pi_txtt:#x}]
    jmp pi_show
pi_trap:
    mov edx, ebx
    call {tr_id:#x}
    test eax, eax
    jl pi_tnone
    push ecx
    imul eax, eax, 0xde
    add eax, 0x537e30
    push eax
    push {str_pi_trap:#x}
    push {pi_tit:#x}
    call dword ptr [{SPRINTF:#x}]
    add esp, 16
    jmp pi_tuse
pi_tnone:
    push {str_pi_trnm:#x}
    push {str_pi_s:#x}
    push {pi_tit:#x}
    call dword ptr [{SPRINTF:#x}]
    add esp, 12
pi_tuse:
    xor edi, edi
    mov eax, ebx
    call {po_wet:#x}
    setz al
    movzx edi, al
    movzx ecx, byte ptr [ebx + 5]
    and ecx, {TR_CUENTA}
    mov esi, {str_pi_spent:#x}
    cmp ecx, {TR_USOS}
    jae pi_show
    neg ecx
    add ecx, {TR_USOS}
    push ecx
    push dword ptr [edi*4 + {pi_trft:#x}]
    push {pi_txt:#x}
    call dword ptr [{SPRINTF:#x}]
    add esp, 12
    mov esi, {pi_txt:#x}
pi_show:
    push dword ptr [esp + 0x20]
    push dword ptr [esp + 0x20]
    push esi
    push {pi_tit:#x}
    call 0x4c7a10
    add esp, 16
    jmp 0x4741f3
''')

# Al guardar (0x439a00), antes de cerrar el archivo: la tabla al final.
vt_savef = place('vt_savef', f'''
    push ecx
    push {len(b'VOTA') + 4 + VT_MAX * 0x1c}
    push {vt_save:#x}
    call 0x4dfd70
    pop ecx
    push ecx
    push {PO_SAVELEN}
    push {po_save:#x}
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
    call {po_loadf:#x}
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

# ---------------------------------------------------------------- Botón del Comparador (dc_*)
# En Edit Side (diálogo 86: el emergente 81, que abre 0x44d320) un botón con el ícono de DarkCompare, arriba a la
# izquierda junto a "Armies", abre Herramientas\DarkCompare.exe con --juego (lee el ARMY\ de la carpeta del juego, que
# es la actual, y queda encima de la ventana del juego). Es local: cada PC abre su propia copia, sin red, en cualquier
# máquina; si ya está abierto, el propio programa trae su ventana al frente. Si no está, el aviso de las herramientas.
DC_BTN = 75                  # Edit Side tiene los controles 1 a 74
DC_FILE = SORTEO_FILE + 1    # hoja SETS\Fantasy\darkcomp.pcx con el dibujo del botón
DC_X, DC_Y, DC_W, DC_H = 40, 40, 64, 64   # entre el marco y "REGULARS" (y 107), a la izquierda de "Armies"
dc_exe = place_data('dc_exe', cstr_('Herramientas\\DarkCompare.exe'))
dc_cmd = place_data('dc_cmd', cstr_('"Herramientas\\DarkCompare.exe" --juego'))
dc_err = place_data('dc_err', cstr_('No se pudo abrir Herramientas\\DarkCompare.exe'))

# Alta de Edit Side (0x44dc00, fin en 0x44dd53): los controles nacen ocultos; mostrar el botón, habilitado.
dc_init = place('dc_init', f'''
    push 0
    push {DC_BTN}
    call 0x4dcec0
    add esp, 8
    mov ecx, 0x588bd0
    call 0x4d7f60
    jmp 0x44dd5d
''')

# Clic en Edit Side (0x44d3a0; evento 3 en 0x44d3e7, edx = control; los que no están entre 2 y 73 caen en
# "ja 0x44db1c", que devuelve 0 y deja el diálogo abierto).
dc_click = place('dc_click', f'''
    cmp edx, {DC_BTN}
    jne 0x44db1c
    push {tl_pi:#x}
    push {tl_si:#x}
    push 0
    push 0
    push 0
    push 0
    push 0
    push 0
    push {dc_cmd:#x}
    push {dc_exe:#x}
    call dword ptr [{CREATEPROC:#x}]
    test eax, eax
    jz dc_fail
    push dword ptr [{tl_pi:#x}]
    call dword ptr [{CLOSEH:#x}]
    push dword ptr [{tl_pi + 4:#x}]
    call dword ptr [{CLOSEH:#x}]
    jmp 0x44db1c
dc_fail:
    push 0
    push 0
    push {dc_err:#x}
    push {tl_warn:#x}
    push 0
    push 0
    call dword ptr [{CREATETH:#x}]
    test eax, eax
    jz 0x44db1c
    push eax
    call dword ptr [{CLOSEH:#x}]
    jmp 0x44db1c
''')

# ---------------------------------------------------------------- IA: base de pruebas (specs\ia-destrezas-v1.md)
# DATA\IA.INI, sección [IA], claves Color0..Color7 = original | prueba: qué IA maneja cada color. Sin el archivo el exe
# no hace nada distinto (ni lee ni escribe). Con el archivo, al empezar el turno de cada bando (antes de 0x442470(p),
# en 0x4223ad) se releen las claves a ia_mode (0 original, 1 prueba, 2 valor inválido: se juega con la original) y se
# agrega a DATA\IA.CSV la línea turno, color, ia, vivo, control, oro, ciudades, ejércitos, héroes, s0..s15:
#   turno = [0x5032f8 + 0x30] (0x420a80); vivo = +1 del registro del jugador (0x536b30 + p*0x1f8); control = +0xe2
#   (-1 humano); oro = +0xe4; ciudades: dueño +0xa5 de cada ciudad (0x537e2c + i*0xde, [0x537e2a] ciudades);
#   ejércitos vivos (+0x13 & 0x40) de 0x54fe50 + i*0x1c (1 <= i < [0x54fe50]) cuya palabra +0xe tiene dueño p en los
#   bits 5-8; los bits 0-4 son la ranura del bando (0..15 se cuentan en s0..s15; 0x10 es héroe).
# Las destrezas de la IA de prueba leen ia_mode[p] (todavía no hay ninguna: con "prueba" juega igual que la original).
IA_SEC = place_data('ia_sec', cstr_('IA'))
IA_PATH = place_data('ia_path', cstr_(r'.\DATA\IA.INI'))
IA_CSV = place_data('ia_csv', cstr_(r'.\DATA\IA.CSV'))
IA_R = place_data('ia_r', cstr_('r'))
IA_EMPTY = place_data('ia_empty', cstr_(''))
IA_ORIG = place_data('ia_orig', cstr_('original'))
IA_PRUEBA = place_data('ia_prueba', cstr_('prueba'))
IA_KEYS = [place_data(f'ia_key{c}', cstr_(f'Color{c}')) for c in range(8)]
IA_KEYTAB = place_data('ia_keytab', b''.join(a.to_bytes(4, 'little') for a in IA_KEYS))
IA_FMT = place_data('ia_fmt', cstr_('%d,%d,%d' + ',%d' * 22 + '\n'))
IA_VAL = place_data('ia_val', bytes(16))
IA_SNAP = place_data('ia_snapbuf', bytes(4 * 22))
IA_N = 22
GETPROF = 0x5a97e8

# ia_snap(p, buf) cdecl: buf = 22 dwords (vivo, control, oro, ciudades, ejércitos, héroes, s0..s15). Preserva todo
# menos eax.
ia_snap = place('ia_snap', f'''
    pushad
    mov ebx, dword ptr [esp + 0x24]
    mov edi, dword ptr [esp + 0x28]
    push edi
    xor eax, eax
    mov ecx, {IA_N}
    rep stosd
    pop edi
    imul esi, ebx, 0x1f8
    movzx eax, byte ptr [esi + 0x536b31]
    mov dword ptr [edi], eax
    movsx eax, word ptr [esi + 0x536c12]
    mov dword ptr [edi + 4], eax
    mov eax, dword ptr [esi + 0x536c14]
    mov dword ptr [edi + 8], eax
    movsx ecx, word ptr [0x537e2a]
    mov esi, {CITIES + 0xa5:#x}
is_city:
    test ecx, ecx
    jle is_arm0
    movzx eax, byte ptr [esi]
    cmp eax, ebx
    jne is_cnext
    inc dword ptr [edi + 12]
is_cnext:
    add esi, 0xde
    dec ecx
    jmp is_city
is_arm0:
    mov ecx, 1
is_arm:
    movsx eax, word ptr [0x54fe50]
    cmp ecx, eax
    jge is_out
    imul esi, ecx, 0x1c
    test byte ptr [esi + 0x54fe63], 0x40
    jz is_anext
    movzx eax, word ptr [esi + 0x54fe5e]
    mov edx, eax
    shr edx, 5
    and edx, 0xf
    cmp edx, ebx
    jne is_anext
    and eax, 0x1f
    cmp eax, 0x10
    jb is_slot
    inc dword ptr [edi + 20]
    jmp is_anext
is_slot:
    inc dword ptr [edi + 16]
    inc dword ptr [edi + eax*4 + 24]
is_anext:
    inc ecx
    jmp is_arm
is_out:
    popad
    ret
''')

# Etapa 3 (alianzas): ia_dip(p) agrega a DATA\IA_DIP.CSV turno, color, opciones, d0..d7, con d = [DIPLO + p*56 + b]
# (0 aliados, 1 paz, 2 guerra) y opciones = 1 ciudades compartidas (SHOPT) | 2 Diplomacy | 4 Hidden Map | 8 vista
# aliada. Preserva todo.
IA_DCSV = place_data('ia_dcsv', cstr_(r'.\DATA\IA_DIP.CSV'))
IA_DFMT = place_data('ia_dfmt', cstr_('%d' + ',%d' * 10 + '\n'))
ia_dip = place('ia_dip', f'''
    pushad
    mov ebx, dword ptr [esp + 0x24]
    cmp ebx, 8
    jae id_out
    push {IA_A:#x}
    push {IA_DCSV:#x}
    call dword ptr [{FOPEN:#x}]
    add esp, 8
    test eax, eax
    jz id_out
    mov edi, eax
    imul esi, ebx, 56
    mov ecx, 8
id_push:
    movzx eax, byte ptr [esi + ecx + {DIPLO - 1:#x}]
    push eax
    loop id_push
    xor eax, eax
    test byte ptr [{SHOPT:#x}], 1
    jz id_o1
    or eax, 1
id_o1:
    test byte ptr [{DIPLO_OPT:#x}], 8
    jz id_o2
    or eax, 2
id_o2:
    test byte ptr [{OPT:#x}], 0x10
    jz id_o3
    or eax, 4
id_o3:
    test byte ptr [{OPT:#x}], 0x80
    jz id_o4
    or eax, 8
id_o4:
    push eax
    push ebx
    movsx eax, word ptr [0x503328]
    push eax
    push {IA_DFMT:#x}
    push edi
    call dword ptr [{FPRINTF:#x}]
    add esp, 0x34
    push edi
    call dword ptr [{FCLOSE:#x}]
    add esp, 4
id_out:
    popad
    ret
''')

# ia_refug(p): al empezar el turno de p, por cada ciudad compartida de otro dueño (member) con ejércitos vivos de p en
# sus 4 casillas, ia_evt(5, p, x, y, ejércitos). Es donde p terminó su turno anterior. Preserva todo.
ia_refug = place('ia_refug', f'''
    pushad
    sub esp, 8
    mov ebx, dword ptr [esp + 0x2c]
    cmp ebx, 8
    jae rf_out
    xor esi, esi
rf_city:
    movsx eax, word ptr [0x537e2a]
    cmp esi, eax
    jge rf_out
    imul edi, esi, 0xde
    movzx eax, byte ptr [edi + {CITIES + 0xa5:#x}]
    cmp eax, ebx
    je rf_next
    push ebx
    push esi
    call {member:#x}
    add esp, 8
    test eax, eax
    jz rf_next
    movsx eax, word ptr [edi + {CITIES:#x}]
    mov dword ptr [esp], eax
    movsx eax, word ptr [edi + {CITIES + 2:#x}]
    mov dword ptr [esp + 4], eax
    xor ebp, ebp
    mov ecx, 1
rf_arm:
    movsx eax, word ptr [0x54fe50]
    cmp ecx, eax
    jge rf_cnt
    imul edx, ecx, 0x1c
    test byte ptr [edx + 0x54fe63], 0x40
    jz rf_anext
    movzx eax, word ptr [edx + 0x54fe5e]
    shr eax, 5
    and eax, 0xf
    cmp eax, ebx
    jne rf_anext
    movsx eax, word ptr [edx + 0x54fe52]
    sub eax, dword ptr [esp]
    cmp eax, 1
    ja rf_anext
    movsx eax, word ptr [edx + 0x54fe54]
    sub eax, dword ptr [esp + 4]
    cmp eax, 1
    ja rf_anext
    inc ebp
rf_anext:
    inc ecx
    jmp rf_arm
rf_cnt:
    test ebp, ebp
    jz rf_next
    push ebp
    push dword ptr [esp + 8]
    push dword ptr [esp + 8]
    push ebx
    push 5
    call {ia_evt:#x}
    add esp, 0x14
rf_next:
    inc esi
    jmp rf_city
rf_out:
    add esp, 8
    popad
    ret
''')

# ---- IA de prueba: alianzas (specs/ia-alianzas-v1.md, etapa 3 paso 3). Solo con DATA\IA.INI (ia_on).
# ai_ally reemplaza el call 0x40c990(pila, 0) de 0x40edf1, el que hace jugar cada pila de la IA en su turno (0x40eab0).
# Para todo bando de la computadora anota, por pila amenazada (1a), el evento 11 y el resultado al turno siguiente
# (12, al_surv desde ia_turn); eso no decide nada. Solo para ia_mode = prueba decide además:
# - Refugio (req. 1, 2): motivo 3 (regla táctica del héroe, 1.0.39.0) = al_hunt: un héroe enemigo con la misión
#   «Assassinating an Enemy» contra un héroe de la pila la alcanza el próximo turno y su pila es más fuerte; solo
#   sirven ciudades donde el dueño ya tiene más fuerza que la amenaza (a). Se mira primero; sin ciudad así, siguen
#   los otros motivos. Motivo 1 = la amenaza al alcance (al_thr en la casilla del líder) es mayor que la pila;
#   2 = perdió más de la mitad de su fuerza desde la decisión del turno anterior. Va a la ciudad compartida de otro
#   dueño (member) que alcanza este turno (costo del mapa de caminos 0x497750/0x4a65d0 <= movimiento del grupo, o ya
#   está adentro), con lugar para la pila (32 ejércitos en sus 4 casillas) y más lejos del enemigo más cercano. Sin
#   ninguna, sigue la original.
# - Refugiada: si la alianza o la ciudad se pierden, deja de estarlo (evento 8, n = 3). Si la ciudad está amenazada
#   se queda a defenderla (req. 5, evento 13 una vez). Motivo 3: se queda mientras al_hunt siga dando un perseguidor
#   y el dueño siga más fuerte que la amenaza en la ciudad; si no, sale (evento 8, n = 4). Motivos 1 y 2: sale
#   (evento 8) si el dueño juntó más fuerza en la ciudad que al entrar (n = 1, req. 3a) o si la pila creció la mitad
#   (al menos 2) desde que entró (n = 2, req. 3b). Mientras tanto vuelve a la ciudad si salió y no hace nada más.
#   «Quedarse hasta el final» (req. 4, evento 9) quitado en 1.0.39.0: lo reemplaza el motivo 3.
# - Refuerzo de ciudades aliadas (req. 6 y 7): quitado en 1.0.38.0 por pedido del usuario (decisión estratégica,
#   no táctica).
# - Defensa de ciudades aliadas (1.0.39.0, regla del usuario), si la pila no se refugia: si ninguna ciudad propia
#   tiene amenaza mayor que sus defensores, la pila que ya está en una ciudad aliada con amenaza se queda (evento 16)
#   y si no, va (evento 15) a la ciudad aliada que alcanza este turno, con lugar, cuya amenaza supera a defensores +
#   lo ya mandado este turno (AL_CT +8) por más; suma su fuerza a lo mandado. Amenaza = enemigos de p (al_thr): se
#   supone que el enemigo de p es también del aliado (equipos). Después, la original.
# Fuerza de un ejército = fuerza base * vida de su palabra +0xe (bits 9-12 y 13-15, como 0x467240); alcance de un
# ejército enemigo = su movimiento +0x12 / 2 + 1 casillas de rey (aproximado: no mira el terreno).
# La tabla AL_TAB (por jugador y pila, 16 bytes): +0 líder, +2 ciudad + 1, +4 motivo, +5 bits (1 hasta el final,
# 2 evento 13 anotado; el 1 ya no se usa), +6 fuerza al entrar, +8 fuerza del dueño en la ciudad al entrar, +0xa fuerza en la última
# decisión, +0xc su turno + 1 (0 = sin decisión). No se guarda con la partida: al cargar, las pilas vuelven a decidir desde cero.
AL_TAB = place_data('al_tab', bytes(80 * 16))
AL_THR = place_data('al_amen', bytes(80 * 8))     # líder, x, y, turno de la pila amenazada (req. 11)
AL_CT = place_data('al_ct', bytes(256 * 12))     # por ciudad: amenaza, defensores, ya mandado
AL_KEY = place_data('al_key', bytes(4))          # turno * 16 + jugador + 1 de AL_CT
# al_str: eax = ejército -> eax = fuerza * vida. Preserva todo lo demás.
al_str = place('al_str', '''
    push edx
    imul eax, eax, 0x1c
    movzx eax, word ptr [eax + 0x54fe5e]
    mov edx, eax
    shr eax, 9
    and eax, 15
    shr edx, 13
    and edx, 7
    imul eax, edx
    pop edx
    ret
''')
# al_sstr(registro de pila) cdecl -> eax = fuerza de sus ejércitos vivos, ecx = cuántos. Preserva ebx esi edi ebp.
al_sstr = place('al_sstr', f'''
    push ebx
    push esi
    push edi
    mov esi, dword ptr [esp + 0x10]
    xor edi, edi
    xor ecx, ecx
    xor ebx, ebx
ss_lp:
    movsx eax, word ptr [esi + ebx*2 + 0xc]
    test eax, eax
    jle ss_nx
    imul edx, eax, 0x1c
    test byte ptr [edx + 0x54fe63], 0x40
    jz ss_nx
    call {al_str:#x}
    add edi, eax
    inc ecx
ss_nx:
    inc ebx
    cmp ebx, 8
    jb ss_lp
    mov eax, edi
    pop edi
    pop esi
    pop ebx
    ret
''')
# al_thr(p, x, y) cdecl -> eax = fuerza de los ejércitos en guerra con p (DIPLO 2) que alcanzan (x, y) en su próximo
# turno, edx = 1 si entre ellos hay un héroe con destino a 2 casillas o menos de (x, y), ecx = el ejército en guerra
# más cercano (cualquier distancia; -1 ninguno). Preserva ebx esi edi ebp.
al_thr = place('al_thr', f'''
    push ebx
    push esi
    push edi
    push ebp
    sub esp, 16
    mov dword ptr [esp], 0
    mov dword ptr [esp + 4], 0
    mov dword ptr [esp + 8], -1
    mov dword ptr [esp + 0xc], 0x7fffffff
    mov ebx, dword ptr [esp + 0x24]
    mov esi, 1
th_lp:
    movsx eax, word ptr [0x54fe50]
    cmp esi, eax
    jge th_end
    imul edi, esi, 0x1c
    test byte ptr [edi + 0x54fe63], 0x40
    jz th_nx
    movzx eax, word ptr [edi + 0x54fe5e]
    shr eax, 5
    and eax, 15
    cmp eax, 8
    jae th_nx
    cmp eax, ebx
    je th_nx
    imul edx, ebx, 56
    cmp byte ptr [edx + eax + {DIPLO:#x}], 2
    jne th_nx
    movsx eax, word ptr [edi + 0x54fe52]
    sub eax, dword ptr [esp + 0x28]
    cdq
    xor eax, edx
    sub eax, edx
    mov ebp, eax
    movsx eax, word ptr [edi + 0x54fe54]
    sub eax, dword ptr [esp + 0x2c]
    cdq
    xor eax, edx
    sub eax, edx
    cmp eax, ebp
    jle th_k
    mov ebp, eax
th_k:
    cmp ebp, dword ptr [esp + 0xc]
    jge th_r
    mov dword ptr [esp + 0xc], ebp
    mov dword ptr [esp + 8], esi
th_r:
    movzx eax, byte ptr [edi + 0x54fe62]
    shr eax, 1
    inc eax
    cmp ebp, eax
    jg th_nx
    mov eax, esi
    call {al_str:#x}
    add dword ptr [esp], eax
    mov al, byte ptr [edi + 0x54fe5e]
    and al, 0x1f
    cmp al, 0x10
    jne th_nx
    movsx eax, word ptr [edi + 0x54fe56]
    sub eax, dword ptr [esp + 0x28]
    add eax, 2
    cmp eax, 4
    ja th_nx
    movsx eax, word ptr [edi + 0x54fe58]
    sub eax, dword ptr [esp + 0x2c]
    add eax, 2
    cmp eax, 4
    ja th_nx
    mov dword ptr [esp + 4], 1
th_nx:
    inc esi
    jmp th_lp
th_end:
    mov eax, dword ptr [esp]
    mov edx, dword ptr [esp + 4]
    mov ecx, dword ptr [esp + 8]
    add esp, 16
    pop ebp
    pop edi
    pop esi
    pop ebx
    ret
''')
# al_def(p, ciudad) cdecl -> eax = fuerza de p y sus aliados (DIPLO 0) en las 4 casillas de la ciudad, edx = la del
# dueño de la ciudad, ecx = ejércitos vivos de cualquiera en ellas. Preserva ebx esi edi ebp.
al_def = place('al_def', f'''
    push ebx
    push esi
    push edi
    push ebp
    sub esp, 16
    imul eax, dword ptr [esp + 0x28], 0xde
    movsx ebx, word ptr [eax + {CITIES:#x}]
    movsx ebp, word ptr [eax + {CITIES + 2:#x}]
    movzx eax, byte ptr [eax + {CITIES + 0xa5:#x}]
    mov dword ptr [esp + 0xc], eax
    mov dword ptr [esp], 0
    mov dword ptr [esp + 4], 0
    mov dword ptr [esp + 8], 0
    mov esi, 1
df_lp:
    movsx eax, word ptr [0x54fe50]
    cmp esi, eax
    jge df_end
    imul edi, esi, 0x1c
    test byte ptr [edi + 0x54fe63], 0x40
    jz df_nx
    movsx eax, word ptr [edi + 0x54fe52]
    sub eax, ebx
    cmp eax, 1
    ja df_nx
    movsx eax, word ptr [edi + 0x54fe54]
    sub eax, ebp
    cmp eax, 1
    ja df_nx
    inc dword ptr [esp + 8]
    movzx ecx, word ptr [edi + 0x54fe5e]
    shr ecx, 5
    and ecx, 15
    mov eax, esi
    call {al_str:#x}
    cmp ecx, dword ptr [esp + 0xc]
    jne df_o
    add dword ptr [esp + 4], eax
df_o:
    cmp ecx, 8
    jae df_nx
    cmp ecx, dword ptr [esp + 0x24]
    je df_f
    imul edx, dword ptr [esp + 0x24], 56
    cmp byte ptr [edx + ecx + {DIPLO:#x}], 0
    jne df_nx
df_f:
    add dword ptr [esp], eax
df_nx:
    inc esi
    jmp df_lp
df_end:
    mov eax, dword ptr [esp]
    mov edx, dword ptr [esp + 4]
    mov ecx, dword ptr [esp + 8]
    add esp, 16
    pop ebp
    pop edi
    pop esi
    pop ebx
    ret
''')
# al_cost(p, ciudad) cdecl -> eax = menor costo del mapa de caminos de p (0x4a65d0) a una de las 4 casillas de la
# ciudad, 0x7fffffff si ninguna lo tiene. Preserva ebx esi edi ebp.
al_cost = place('al_cost', f'''
    push ebx
    push esi
    push edi
    push ebp
    imul eax, dword ptr [esp + 0x18], 0xde
    movsx ebx, word ptr [eax + {CITIES:#x}]
    movsx ebp, word ptr [eax + {CITIES + 2:#x}]
    mov edi, 0x7fffffff
    xor esi, esi
ac_lp:
    mov eax, esi
    shr eax, 1
    add eax, ebp
    push eax
    mov eax, esi
    and eax, 1
    add eax, ebx
    push eax
    push dword ptr [esp + 0x1c]
    call 0x4a65d0
    add esp, 0xc
    movzx eax, ax
    test eax, eax
    jz ac_nx
    cmp eax, edi
    jge ac_nx
    mov edi, eax
ac_nx:
    inc esi
    cmp esi, 4
    jb ac_lp
    mov eax, edi
    pop ebp
    pop edi
    pop esi
    pop ebx
    ret
''')
# al_tabla(p) cdecl: llena AL_CT para p una vez por turno (amenaza y defensores de las ciudades compartidas con p y
# de las propias; las demás en 0; ya mandado en 0). Preserva todo.
al_tabla = place('al_tabla', f'''
    pushad
    mov ebx, dword ptr [esp + 0x24]
    movsx eax, word ptr [0x503328]
    shl eax, 4
    lea eax, [eax + ebx + 1]
    cmp eax, dword ptr [{AL_KEY:#x}]
    je tb_out
    mov dword ptr [{AL_KEY:#x}], eax
    xor esi, esi
tb_lp:
    movsx eax, word ptr [0x537e2a]
    cmp esi, eax
    jge tb_out
    cmp esi, 256
    jae tb_out
    imul edi, esi, 12
    mov dword ptr [edi + {AL_CT:#x}], 0
    mov dword ptr [edi + {AL_CT + 4:#x}], 0
    mov dword ptr [edi + {AL_CT + 8:#x}], 0
    imul ebp, esi, 0xde
    cmp byte ptr [ebp + {CITIES + 0xa4:#x}], 0
    je tb_nx
    movzx eax, byte ptr [ebp + {CITIES + 0xa5:#x}]
    cmp eax, ebx
    je tb_si
    push ebx
    push esi
    call {member:#x}
    add esp, 8
    test eax, eax
    jz tb_nx
tb_si:
    movsx eax, word ptr [ebp + {CITIES + 2:#x}]
    push eax
    movsx eax, word ptr [ebp + {CITIES:#x}]
    push eax
    push ebx
    call {al_thr:#x}
    add esp, 0xc
    mov dword ptr [edi + {AL_CT:#x}], eax
    push esi
    push ebx
    call {al_def:#x}
    add esp, 8
    mov dword ptr [edi + {AL_CT + 4:#x}], eax
tb_nx:
    inc esi
    jmp tb_lp
tb_out:
    popad
    ret
''')
# al_hunt(p, registro de pila) cdecl -> eax = el héroe enemigo que persigue a un héroe de la pila (0 = ninguno):
# un jugador en guerra con p (DIPLO 2) tiene la misión activa 11 «Assassinating an Enemy» (0x55edc4 + jugador * 16:
# +0 activa, +2 su héroe, +4 tipo, +6 el ejército objetivo, según el generador 0x45ec40) con objetivo en la pila, su
# héroe vive, alcanza al objetivo en su próximo turno (movimiento / 2 + 1 casillas de rey, como al_thr) y los
# ejércitos de su color en su casilla suman más fuerza que la pila (la pila es débil). Preserva ebx esi edi ebp.
al_hunt = place('al_hunt', f'''
    push ebx
    push esi
    push edi
    push ebp
    sub esp, 8
    push dword ptr [esp + 0x20]
    call {al_sstr:#x}
    add esp, 4
    mov dword ptr [esp], eax
    xor ebx, ebx
hu_q:
    cmp ebx, 8
    jae hu_none
    cmp ebx, dword ptr [esp + 0x1c]
    je hu_nx
    imul edx, dword ptr [esp + 0x1c], 56
    cmp byte ptr [edx + ebx + {DIPLO:#x}], 2
    jne hu_nx
    mov edi, ebx
    shl edi, 4
    cmp byte ptr [edi + 0x55edc4], 0
    je hu_nx
    cmp word ptr [edi + 0x55edc8], 11
    jne hu_nx
    movsx eax, word ptr [edi + 0x55edca]
    test eax, eax
    jle hu_nx
    mov dword ptr [esp + 4], eax
    mov ecx, dword ptr [esp + 0x20]
    xor edx, edx
hu_s:
    cmp ax, word ptr [ecx + edx*2 + 0xc]
    je hu_in
    inc edx
    cmp edx, 8
    jb hu_s
    jmp hu_nx
hu_in:
    movsx esi, word ptr [edi + 0x55edc6]
    test esi, esi
    jle hu_nx
    imul ebp, esi, 0x1c
    test byte ptr [ebp + 0x54fe63], 0x40
    jz hu_nx
    movzx eax, word ptr [ebp + 0x54fe5e]
    shr eax, 5
    and eax, 15
    cmp eax, ebx
    jne hu_nx
    imul ecx, dword ptr [esp + 4], 0x1c
    movsx eax, word ptr [ebp + 0x54fe52]
    movsx edx, word ptr [ecx + 0x54fe52]
    sub eax, edx
    cdq
    xor eax, edx
    sub eax, edx
    mov edi, eax
    movsx eax, word ptr [ebp + 0x54fe54]
    movsx edx, word ptr [ecx + 0x54fe54]
    sub eax, edx
    cdq
    xor eax, edx
    sub eax, edx
    cmp eax, edi
    jle hu_d
    mov edi, eax
hu_d:
    movzx eax, byte ptr [ebp + 0x54fe62]
    shr eax, 1
    inc eax
    cmp edi, eax
    jg hu_nx
    xor edi, edi
    mov ecx, 1
hu_g:
    movsx eax, word ptr [0x54fe50]
    cmp ecx, eax
    jge hu_gd
    imul edx, ecx, 0x1c
    test byte ptr [edx + 0x54fe63], 0x40
    jz hu_gn
    movzx eax, word ptr [edx + 0x54fe5e]
    shr eax, 5
    and eax, 15
    cmp eax, ebx
    jne hu_gn
    mov ax, word ptr [edx + 0x54fe52]
    cmp ax, word ptr [ebp + 0x54fe52]
    jne hu_gn
    mov ax, word ptr [edx + 0x54fe54]
    cmp ax, word ptr [ebp + 0x54fe54]
    jne hu_gn
    mov eax, ecx
    call {al_str:#x}
    add edi, eax
hu_gn:
    inc ecx
    jmp hu_g
hu_gd:
    cmp dword ptr [esp], edi
    jge hu_nx
    mov eax, esi
    jmp hu_out
hu_nx:
    inc ebx
    jmp hu_q
hu_none:
    xor eax, eax
hu_out:
    add esp, 8
    pop ebp
    pop edi
    pop esi
    pop ebx
    ret
''')
# ai_ally(pila, arg): en lugar de 0x40c990 en 0x40edf1. Locales [ebp - n].
L_P, L_S, L_REC, L_LEAD, L_STR, L_LX, L_LY, L_E, L_HUNT, L_NEAR, L_ENT, L_MAP, L_BEST, L_BSC, L_MOT, L_CNT, \
    L_CRIT, L_CX, L_CY, L_MOV, L_T1, L_T2, L_OWNT = (4 * (i + 1) for i in range(23))
L_SIZE = 0x60
def _al_go(lbl):
    # mueve la pila hacia la ciudad [ebp - L_BEST] (arma el grupo si hace falta)
    return f'''
    cmp dword ptr [ebp - {L_MAP}], 0
    jne {lbl}_g
    mov eax, dword ptr [ebp - {L_REC}]
    add eax, 0xc
    push eax
    call 0x497240
    add esp, 4
{lbl}_g:
    imul eax, dword ptr [ebp - {L_BEST}], 0xde
    movsx ecx, word ptr [eax + {CITIES + 2:#x}]
    push ecx
    movsx ecx, word ptr [eax + {CITIES:#x}]
    push ecx
    call 0x40d2b0
    add esp, 8'''
ai_ally = place('ai_ally', f'''
    cmp byte ptr [{IA_ON:#x}], 0
    je 0x40c990
    movsx eax, word ptr [0x4fb0ec]
    cmp eax, 8
    jae 0x40c990
    push ebp
    mov ebp, esp
    sub esp, {L_SIZE:#x}
    pushad
    mov dword ptr [ebp - {L_P}], eax
    movsx ecx, word ptr [ebp + 8]
    mov dword ptr [ebp - {L_S}], ecx
    imul edx, eax, 0x49a
    shl ecx, 6
    lea edx, [edx + ecx + 0x561f00]
    mov dword ptr [ebp - {L_REC}], edx
    mov dword ptr [ebp - {L_MAP}], 0
    movsx eax, word ptr [edx + 0xc]
    mov dword ptr [ebp - {L_LEAD}], eax
    test eax, eax
    jle al_orig
    imul ecx, eax, 0x1c
    test byte ptr [ecx + 0x54fe63], 0x40
    jz al_orig
    movsx eax, word ptr [ecx + 0x54fe52]
    mov dword ptr [ebp - {L_LX}], eax
    movsx eax, word ptr [ecx + 0x54fe54]
    mov dword ptr [ebp - {L_LY}], eax
    push edx
    call {al_sstr:#x}
    add esp, 4
    mov dword ptr [ebp - {L_STR}], eax
    mov dword ptr [ebp - {L_CNT}], ecx
    push dword ptr [ebp - {L_LY}]
    push dword ptr [ebp - {L_LX}]
    push dword ptr [ebp - {L_P}]
    call {al_thr:#x}
    add esp, 0xc
    mov dword ptr [ebp - {L_E}], eax
    mov dword ptr [ebp - {L_HUNT}], edx
    mov dword ptr [ebp - {L_NEAR}], ecx
    cmp eax, dword ptr [ebp - {L_STR}]
    jle al_mode
    push dword ptr [ebp - {L_LEAD}]
    push dword ptr [ebp - {L_LY}]
    push dword ptr [ebp - {L_LX}]
    push dword ptr [ebp - {L_P}]
    push 11
    call {ia_evt:#x}
    add esp, 0x14
    imul eax, dword ptr [ebp - {L_P}], 10
    add eax, dword ptr [ebp - {L_S}]
    lea eax, [eax*8 + {AL_THR:#x}]
    mov ecx, dword ptr [ebp - {L_LEAD}]
    mov word ptr [eax], cx
    mov ecx, dword ptr [ebp - {L_LX}]
    mov word ptr [eax + 2], cx
    mov ecx, dword ptr [ebp - {L_LY}]
    mov word ptr [eax + 4], cx
    mov cx, word ptr [0x503328]
    mov word ptr [eax + 6], cx
al_mode:
    mov eax, dword ptr [ebp - {L_P}]
    cmp byte ptr [eax + {IA_MODE:#x}], 1
    jne al_orig
    mov eax, dword ptr [ebp - {L_S}]
    mov ecx, dword ptr [ebp - {L_REC}]
    mov word ptr [0x5020d0], ax
    mov dword ptr [0x5020d4], ecx
    imul esi, dword ptr [ebp - {L_P}], 10
    add esi, eax
    shl esi, 4
    add esi, {AL_TAB:#x}
    mov dword ptr [ebp - {L_ENT}], esi
    movsx eax, word ptr [esi]
    cmp eax, dword ptr [ebp - {L_LEAD}]
    je al_same
    mov dword ptr [esi], 0
    mov dword ptr [esi + 4], 0
    mov dword ptr [esi + 8], 0
    mov dword ptr [esi + 0xc], 0
    mov eax, dword ptr [ebp - {L_LEAD}]
    mov word ptr [esi], ax
al_same:
    xor eax, eax
    mov dword ptr [ebp - {L_T1}], eax
    movsx ecx, word ptr [esi + 0xc]
    movsx edx, word ptr [0x503328]
    inc edx
    cmp ecx, edx
    je al_cur
    test ecx, ecx
    jz al_last
    movsx eax, word ptr [esi + 0xa]
    mov ecx, dword ptr [ebp - {L_STR}]
    add ecx, ecx
    cmp ecx, eax
    jge al_last
    mov dword ptr [ebp - {L_T1}], 1
al_last:
    mov eax, dword ptr [ebp - {L_STR}]
    mov word ptr [esi + 0xa], ax
    mov word ptr [esi + 0xc], dx
al_cur:
    push dword ptr [ebp - {L_P}]
    call {al_tabla:#x}
    add esp, 4
    movsx eax, word ptr [esi + 2]
    test eax, eax
    jz al_normal
    dec eax
    mov dword ptr [ebp - {L_BEST}], eax
    imul edi, eax, 0xde
    cmp byte ptr [edi + {CITIES + 0xa4:#x}], 0
    je al_lost
    movzx ecx, byte ptr [edi + {CITIES + 0xa5:#x}]
    cmp ecx, dword ptr [ebp - {L_P}]
    je al_lost
    push dword ptr [ebp - {L_P}]
    push eax
    call {member:#x}
    add esp, 8
    test eax, eax
    jz al_lost
    movsx eax, word ptr [edi + {CITIES:#x}]
    mov dword ptr [ebp - {L_CX}], eax
    movsx eax, word ptr [edi + {CITIES + 2:#x}]
    mov dword ptr [ebp - {L_CY}], eax
    imul eax, dword ptr [ebp - {L_BEST}], 12
    cmp dword ptr [eax + {AL_CT:#x}], 0
    je al_calm
    test byte ptr [esi + 5], 2
    jnz al_stay
    or byte ptr [esi + 5], 2
    push dword ptr [eax + {AL_CT:#x}]
    push dword ptr [ebp - {L_CY}]
    push dword ptr [ebp - {L_CX}]
    push dword ptr [ebp - {L_P}]
    push 13
    call {ia_evt:#x}
    add esp, 0x14
    jmp al_stay
al_calm:
    and byte ptr [esi + 5], 0xfd
    cmp byte ptr [esi + 4], 3
    jne al_exits
    mov dword ptr [ebp - {L_T2}], 4
    push dword ptr [ebp - {L_REC}]
    push dword ptr [ebp - {L_P}]
    call {al_hunt:#x}
    add esp, 8
    test eax, eax
    jz al_exit
    push dword ptr [ebp - {L_BEST}]
    push dword ptr [ebp - {L_P}]
    call {al_def:#x}
    add esp, 8
    imul eax, dword ptr [ebp - {L_BEST}], 12
    cmp edx, dword ptr [eax + {AL_CT:#x}]
    jle al_exit
    jmp al_stay
al_exits:
    push dword ptr [ebp - {L_BEST}]
    push dword ptr [ebp - {L_P}]
    call {al_def:#x}
    add esp, 8
    movsx eax, word ptr [esi + 8]
    cmp edx, eax
    jle al_ex2
    mov dword ptr [ebp - {L_T2}], 1
    jmp al_exit
al_ex2:
    movsx eax, word ptr [esi + 6]
    mov ecx, eax
    shr ecx, 1
    cmp ecx, 2
    jge al_ex3
    mov ecx, 2
al_ex3:
    add eax, ecx
    cmp dword ptr [ebp - {L_STR}], eax
    jl al_stay
    mov dword ptr [ebp - {L_T2}], 2
al_exit:
    push dword ptr [ebp - {L_T2}]
    push dword ptr [ebp - {L_CY}]
    push dword ptr [ebp - {L_CX}]
    push dword ptr [ebp - {L_P}]
    push 8
    call {ia_evt:#x}
    add esp, 0x14
    mov dword ptr [esi + 2], 0
    mov dword ptr [esi + 6], 0
    jmp al_orig
al_lost:
    imul edi, dword ptr [ebp - {L_BEST}], 0xde
    movsx eax, word ptr [edi + {CITIES + 2:#x}]
    movsx ecx, word ptr [edi + {CITIES:#x}]
    push 3
    push eax
    push ecx
    push dword ptr [ebp - {L_P}]
    push 8
    call {ia_evt:#x}
    add esp, 0x14
    mov dword ptr [esi + 2], 0
    mov dword ptr [esi + 6], 0
    jmp al_normal
al_stay:
    mov eax, dword ptr [ebp - {L_LX}]
    sub eax, dword ptr [ebp - {L_CX}]
    cmp eax, 1
    ja al_back
    mov eax, dword ptr [ebp - {L_LY}]
    sub eax, dword ptr [ebp - {L_CY}]
    cmp eax, 1
    jbe al_done
al_back:{_al_go('al_bk')}
    jmp al_done
al_normal:
    push dword ptr [ebp - {L_REC}]
    push dword ptr [ebp - {L_P}]
    call {al_hunt:#x}
    add esp, 8
    mov dword ptr [ebp - {L_HUNT}], eax
    mov dword ptr [ebp - {L_MOT}], 3
    test eax, eax
    jnz al_ref
al_n12:
    mov dword ptr [ebp - {L_MOT}], 1
    mov eax, dword ptr [ebp - {L_E}]
    cmp eax, dword ptr [ebp - {L_STR}]
    jg al_ref
    mov dword ptr [ebp - {L_MOT}], 2
    cmp dword ptr [ebp - {L_T1}], 0
    jne al_ref
    jmp al_dfn
al_ref:
    call al_map
    mov dword ptr [ebp - {L_BEST}], -1
    mov dword ptr [ebp - {L_BSC}], -1
    xor esi, esi
al_rc:
    movsx eax, word ptr [0x537e2a]
    cmp esi, eax
    jge al_rch
    imul edi, esi, 0xde
    cmp byte ptr [edi + {CITIES + 0xa4:#x}], 0
    je al_rcn
    movzx eax, byte ptr [edi + {CITIES + 0xa5:#x}]
    cmp eax, dword ptr [ebp - {L_P}]
    je al_rcn
    push dword ptr [ebp - {L_P}]
    push esi
    call {member:#x}
    add esp, 8
    test eax, eax
    jz al_rcn
    movsx eax, word ptr [edi + {CITIES:#x}]
    mov dword ptr [ebp - {L_CX}], eax
    movsx eax, word ptr [edi + {CITIES + 2:#x}]
    mov dword ptr [ebp - {L_CY}], eax
    mov eax, dword ptr [ebp - {L_LX}]
    sub eax, dword ptr [ebp - {L_CX}]
    cmp eax, 1
    ja al_rcc
    mov eax, dword ptr [ebp - {L_LY}]
    sub eax, dword ptr [ebp - {L_CY}]
    cmp eax, 1
    jbe al_rcin
al_rcc:
    push esi
    push dword ptr [ebp - {L_P}]
    call {al_def:#x}
    add esp, 8
    add ecx, dword ptr [ebp - {L_CNT}]
    cmp ecx, 32
    jg al_rcn
    push esi
    push dword ptr [ebp - {L_P}]
    call {al_cost:#x}
    add esp, 8
    cmp eax, dword ptr [ebp - {L_MOV}]
    jg al_rcn
al_rcin:
    cmp dword ptr [ebp - {L_MOT}], 3
    jne al_rcin2
    push esi
    push dword ptr [ebp - {L_P}]
    call {al_def:#x}
    add esp, 8
    imul eax, esi, 12
    cmp edx, dword ptr [eax + {AL_CT:#x}]
    jle al_rcn
al_rcin2:
    xor eax, eax
    mov ecx, dword ptr [ebp - {L_NEAR}]
    test ecx, ecx
    jl al_rcs
    imul ecx, ecx, 0x1c
    movsx eax, word ptr [ecx + 0x54fe52]
    sub eax, dword ptr [ebp - {L_CX}]
    cdq
    xor eax, edx
    sub eax, edx
    mov edx, eax
    movsx eax, word ptr [ecx + 0x54fe54]
    sub eax, dword ptr [ebp - {L_CY}]
    push edx
    cdq
    xor eax, edx
    sub eax, edx
    pop edx
    cmp eax, edx
    jge al_rcs
    mov eax, edx
al_rcs:
    cmp eax, dword ptr [ebp - {L_BSC}]
    jle al_rcn
    mov dword ptr [ebp - {L_BSC}], eax
    mov dword ptr [ebp - {L_BEST}], esi
al_rcn:
    inc esi
    jmp al_rc
al_rch:
    mov eax, dword ptr [ebp - {L_BEST}]
    test eax, eax
    jge al_rok
    cmp dword ptr [ebp - {L_MOT}], 3
    je al_n12
    jmp al_orig
al_rok:
    mov esi, dword ptr [ebp - {L_ENT}]
    inc eax
    mov word ptr [esi + 2], ax
    mov eax, dword ptr [ebp - {L_MOT}]
    mov byte ptr [esi + 4], al
    and byte ptr [esi + 5], 0xfc
    mov eax, dword ptr [ebp - {L_STR}]
    mov word ptr [esi + 6], ax
    push dword ptr [ebp - {L_BEST}]
    push dword ptr [ebp - {L_P}]
    call {al_def:#x}
    add esp, 8
    mov word ptr [esi + 8], dx
    imul edi, dword ptr [ebp - {L_BEST}], 0xde
    movsx eax, word ptr [edi + {CITIES + 2:#x}]
    movsx ecx, word ptr [edi + {CITIES:#x}]
    push dword ptr [ebp - {L_MOT}]
    push eax
    push ecx
    push dword ptr [ebp - {L_P}]
    push 7
    call {ia_evt:#x}
    add esp, 0x14
    mov dword ptr [ebp - {L_CX}], ecx
    mov dword ptr [ebp - {L_CY}], eax
    jmp al_stay
al_dfn:
    xor esi, esi
al_do:
    movsx eax, word ptr [0x537e2a]
    cmp esi, eax
    jge al_ds0
    cmp esi, 256
    jae al_ds0
    imul edi, esi, 0xde
    cmp byte ptr [edi + {CITIES + 0xa4:#x}], 0
    je al_don
    movzx eax, byte ptr [edi + {CITIES + 0xa5:#x}]
    cmp eax, dword ptr [ebp - {L_P}]
    jne al_don
    imul eax, esi, 12
    mov ecx, dword ptr [eax + {AL_CT:#x}]
    cmp ecx, dword ptr [eax + {AL_CT + 4:#x}]
    jg al_orig
al_don:
    inc esi
    jmp al_do
al_ds0:
    xor esi, esi
al_ds:
    movsx eax, word ptr [0x537e2a]
    cmp esi, eax
    jge al_dg0
    cmp esi, 256
    jae al_dg0
    imul edi, esi, 0xde
    cmp byte ptr [edi + {CITIES + 0xa4:#x}], 0
    je al_dsn
    movzx eax, byte ptr [edi + {CITIES + 0xa5:#x}]
    cmp eax, dword ptr [ebp - {L_P}]
    je al_dsn
    imul eax, esi, 12
    mov ecx, dword ptr [eax + {AL_CT:#x}]
    test ecx, ecx
    jz al_dsn
    movsx eax, word ptr [edi + {CITIES:#x}]
    movsx edx, word ptr [edi + {CITIES + 2:#x}]
    mov ebx, dword ptr [ebp - {L_LX}]
    sub ebx, eax
    cmp ebx, 1
    ja al_dsn
    mov ebx, dword ptr [ebp - {L_LY}]
    sub ebx, edx
    cmp ebx, 1
    ja al_dsn
    push ecx
    push edx
    push eax
    push dword ptr [ebp - {L_P}]
    push 16
    call {ia_evt:#x}
    add esp, 0x14
    jmp al_done
al_dsn:
    inc esi
    jmp al_ds
al_dg0:
    call al_map
    mov dword ptr [ebp - {L_BEST}], -1
    mov dword ptr [ebp - {L_BSC}], 0
    xor esi, esi
al_dg:
    movsx eax, word ptr [0x537e2a]
    cmp esi, eax
    jge al_dgh
    cmp esi, 256
    jae al_dgh
    imul edi, esi, 0xde
    cmp byte ptr [edi + {CITIES + 0xa4:#x}], 0
    je al_dgn
    movzx eax, byte ptr [edi + {CITIES + 0xa5:#x}]
    cmp eax, dword ptr [ebp - {L_P}]
    je al_dgn
    imul eax, esi, 12
    mov ecx, dword ptr [eax + {AL_CT:#x}]
    sub ecx, dword ptr [eax + {AL_CT + 4:#x}]
    sub ecx, dword ptr [eax + {AL_CT + 8:#x}]
    cmp ecx, dword ptr [ebp - {L_BSC}]
    jle al_dgn
    mov dword ptr [ebp - {L_T2}], ecx
    push esi
    push dword ptr [ebp - {L_P}]
    call {al_def:#x}
    add esp, 8
    add ecx, dword ptr [ebp - {L_CNT}]
    cmp ecx, 32
    jg al_dgn
    push esi
    push dword ptr [ebp - {L_P}]
    call {al_cost:#x}
    add esp, 8
    cmp eax, dword ptr [ebp - {L_MOV}]
    jg al_dgn
    mov eax, dword ptr [ebp - {L_T2}]
    mov dword ptr [ebp - {L_BSC}], eax
    mov dword ptr [ebp - {L_BEST}], esi
al_dgn:
    inc esi
    jmp al_dg
al_dgh:
    mov esi, dword ptr [ebp - {L_BEST}]
    test esi, esi
    jl al_orig
    imul eax, esi, 12
    mov ecx, dword ptr [ebp - {L_STR}]
    add dword ptr [eax + {AL_CT + 8:#x}], ecx
    imul edi, esi, 0xde
    push dword ptr [eax + {AL_CT:#x}]
    movsx eax, word ptr [edi + {CITIES + 2:#x}]
    push eax
    movsx eax, word ptr [edi + {CITIES:#x}]
    push eax
    push dword ptr [ebp - {L_P}]
    push 15
    call {ia_evt:#x}
    add esp, 0x14
{_al_go('al_dgo')}
    jmp al_done
al_map:
    cmp dword ptr [ebp - {L_MAP}], 0
    jne al_map_r
    mov dword ptr [ebp - {L_MAP}], 1
    mov eax, dword ptr [ebp - {L_REC}]
    add eax, 0xc
    push eax
    call 0x497240
    add esp, 4
    push 0x100
    call 0x497750
    add esp, 4
    imul eax, dword ptr [ebp - {L_P}], 0x4f0
    movsx eax, word ptr [eax + 0x56eaa4]
    mov dword ptr [ebp - {L_MOV}], eax
al_map_r:
    ret
al_done:
    popad
    leave
    ret
al_orig:
    popad
    leave
    jmp 0x40c990
''')
# ---- Órdenes del humano a un aliado de la computadora (ia\PENDIENTE-entrenamiento-ia.md, mensajes entre aliados).
# 0x40c990(pila, arg) con arg != 0 se saltea el planificador 0x41eda0: meta = arg / 1000, objetivo = arg % 1000
# (1 ir a la ciudad, 0x40db40; 7 atacar la ciudad enemiga, 0x40d9f0(c, 7)). ai_ord va antes que ai_ally (con o sin
# IA.INI, y antes del refugio y de la defensa de ciudades aliadas: manda el humano). Con una orden vigente para el
# bando, la cumple la pila que llega en 2 turnos o menos (costo del mapa de caminos <= 2 * movimiento: a la ciudad
# para ir, como al_cost; a una casilla de al lado para atacar, or_ring):
# - tipo 1, atacar la ciudad OR +2: meta 7. Si la ciudad ya es del bando o de un aliado, la orden se da por cumplida.
# - tipo 2, atacar al color OR +2: meta 7 a la ciudad de ese color más barata de alcanzar.
# - tipo 3, refuerzos al bando OR +4: meta 1 a la ciudad de ese bando más barata de alcanzar (o en la que ya está).
# La pila que no llega sigue con ai_ally. Evento 17 (x, y = ciudad, n = tipo) si hay IA.INI.
# OR_TAB, 8 bytes por bando: +0 tipo, +1 turnos que quedan + 1 (quien recibe la orden pone 3; ia_turn lo baja al
# empezar cada turno del bando, así vale en sus 2 turnos siguientes, sea antes o después del humano en la ronda),
# +2 objetivo (palabra), +4 bando que la dio. No se guarda con la partida.
OR_TAB = place_data('or_tab', bytes(8 * 8))
OR_P, OR_REC, OR_BEST, OR_BC, OR_REACH = 4, 8, 12, 16, 20
# or_ring(p, ciudad) cdecl -> eax = menor costo del mapa de caminos (ya armado) a una de las 12 casillas que rodean la
# ciudad (0x7fffffff ninguna): las casillas de una ciudad enemiga no tienen costo de paso; se ataca desde al lado,
# como la meta 7 (0x497830). Preserva ebx esi edi ebp.
or_ring = place('or_ring', f'''
    push ebx
    push esi
    push edi
    push ebp
    imul eax, dword ptr [esp + 0x18], 0xde
    movsx ebx, word ptr [eax + {CITIES:#x}]
    movsx ebp, word ptr [eax + {CITIES + 2:#x}]
    mov edi, 0x7fffffff
    mov esi, -1
rg_y:
    mov ecx, -1
rg_x:
    cmp ecx, 0
    jl rg_ok
    cmp ecx, 1
    jg rg_ok
    cmp esi, 0
    jl rg_ok
    cmp esi, 1
    jle rg_nx
rg_ok:
    lea eax, [ebx + ecx]
    cmp eax, 0
    jl rg_nx
    movsx edx, word ptr [0x503e00]
    cmp eax, edx
    jge rg_nx
    lea edx, [ebp + esi]
    cmp edx, 0
    jl rg_nx
    push ecx
    movsx ecx, word ptr [0x503e02]
    cmp edx, ecx
    pop ecx
    jge rg_nx
    push ecx
    push edx
    push eax
    push dword ptr [esp + 0x20]
    call 0x4a65d0
    add esp, 0xc
    pop ecx
    movzx eax, ax
    test eax, eax
    jz rg_nx
    cmp eax, edi
    jge rg_nx
    mov edi, eax
rg_nx:
    inc ecx
    cmp ecx, 2
    jle rg_x
    inc esi
    cmp esi, 2
    jle rg_y
    mov eax, edi
    pop ebp
    pop edi
    pop esi
    pop ebx
    ret
''')
ai_ord = place('ai_ord', f'''
    movsx eax, word ptr [0x4fb0ec]
    cmp eax, 8
    jae {ai_ally:#x}
    cmp byte ptr [eax*8 + {OR_TAB + 1:#x}], 1
    jbe {ai_ally:#x}
    push ebp
    mov ebp, esp
    sub esp, 0x18
    pushad
    mov dword ptr [ebp - {OR_P}], eax
    movsx ecx, word ptr [ebp + 8]
    imul edx, eax, 0x49a
    mov eax, ecx
    shl ecx, 6
    lea edx, [edx + ecx + 0x561f00]
    mov dword ptr [ebp - {OR_REC}], edx
    movsx ecx, word ptr [edx + 0xc]
    test ecx, ecx
    jle or_no
    imul ecx, ecx, 0x1c
    test byte ptr [ecx + 0x54fe63], 0x40
    jz or_no
    mov word ptr [0x5020d0], ax
    mov dword ptr [0x5020d4], edx
    add edx, 0xc
    push edx
    call 0x497240
    add esp, 4
    push 0x100
    call 0x497750
    add esp, 4
    mov ebx, dword ptr [ebp - {OR_P}]
    imul eax, ebx, 0x4f0
    movsx eax, word ptr [eax + 0x56eaa4]
    add eax, eax
    mov dword ptr [ebp - {OR_REACH}], eax
    mov dword ptr [ebp - {OR_BEST}], -1
    mov dword ptr [ebp - {OR_BC}], 0x7fffffff
    xor esi, esi
or_lp:
    movsx eax, word ptr [0x537e2a]
    cmp esi, eax
    jge or_end
    imul edi, esi, 0xde
    cmp byte ptr [edi + {CITIES + 0xa4:#x}], 0
    je or_nx
    movzx edx, byte ptr [edi + {CITIES + 0xa5:#x}]
    movzx eax, byte ptr [ebx*8 + {OR_TAB:#x}]
    cmp eax, 1
    jne or_t2
    cmp si, word ptr [ebx*8 + {OR_TAB + 2:#x}]
    jne or_nx
    cmp edx, ebx
    je or_done1
    cmp edx, 8
    jae or_ringc
    imul eax, ebx, 56
    cmp byte ptr [eax + edx + {DIPLO:#x}], 0
    jne or_ringc
or_done1:
    mov byte ptr [ebx*8 + {OR_TAB + 1:#x}], 0
    jmp or_no
or_t2:
    cmp eax, 2
    jne or_t3
    cmp edx, ebx
    je or_nx
    cmp dx, word ptr [ebx*8 + {OR_TAB + 2:#x}]
    jne or_nx
or_ringc:
    push esi
    push ebx
    call {or_ring:#x}
    add esp, 8
    jmp or_cmp
or_t3:
    cmp eax, 3
    jne or_no
    cmp dl, byte ptr [ebx*8 + {OR_TAB + 4:#x}]
    jne or_nx
    mov ecx, dword ptr [ebp - {OR_REC}]
    movsx ecx, word ptr [ecx + 0xc]
    imul ecx, ecx, 0x1c
    mov ax, word ptr [ecx + 0x54fe52]
    sub ax, word ptr [edi + {CITIES:#x}]
    cmp ax, 1
    ja or_cost
    mov ax, word ptr [ecx + 0x54fe54]
    sub ax, word ptr [edi + {CITIES + 2:#x}]
    cmp ax, 1
    ja or_cost
    xor eax, eax
    jmp or_cmp
or_cost:
    push esi
    push ebx
    call {al_cost:#x}
    add esp, 8
or_cmp:
    cmp eax, dword ptr [ebp - {OR_REACH}]
    jg or_nx
    cmp eax, dword ptr [ebp - {OR_BC}]
    jge or_nx
    mov dword ptr [ebp - {OR_BC}], eax
    mov dword ptr [ebp - {OR_BEST}], esi
or_nx:
    inc esi
    jmp or_lp
or_end:
    mov esi, dword ptr [ebp - {OR_BEST}]
    test esi, esi
    jl or_no
    movzx eax, byte ptr [ebx*8 + {OR_TAB:#x}]
    imul edi, esi, 0xde
    push eax
    movsx ecx, word ptr [edi + {CITIES + 2:#x}]
    push ecx
    movsx ecx, word ptr [edi + {CITIES:#x}]
    push ecx
    push ebx
    push 17
    call {ia_evt:#x}
    add esp, 0x14
    cmp eax, 3
    mov eax, 7000
    jne or_go
    mov eax, 1000
or_go:
    add eax, esi
    push eax
    push dword ptr [ebp + 8]
    call 0x40c990
    add esp, 8
    popad
    leave
    ret
or_no:
    popad
    leave
    jmp {ai_ally:#x}
''')
# ---- Paquete 0x2a2 y barra de chat «#n» (ia\PENDIENTE-entrenamiento-ia.md, mensajes entre aliados).
# La barra (0x409170) descarta «#n texto» si el bando n no es humano (salto en 0x4091ea). Ahí entra ch_ai: la PC del
# humano interpreta la orden y la manda como OR_PKT (bando que la da, bando que la recibe, tipo, objetivo; 4 palabras),
# que un Warlords sin parche descarta. Órdenes (sin distinguir mayúsculas; el verbo vale por sus 4 primeras letras,
# así «atacá» y «ataca» son lo mismo):
#   «#n ataca CIUDAD»      -> tipo 1, objetivo = la ciudad con ese nombre exacto;
#   «#n ataca a BANDO»     -> tipo 2, objetivo = el bando de ese número (1 a 8) o con ese nombre exacto;
#   «#n mandame refuerzos» -> tipo 3, objetivo = el bando que la da.
# La PC del humano se muestra su propio texto (eco) y, si no son aliados o no entiende la orden, una respuesta con el
# color del bando n solo en su pantalla (0x1ac con destino su máquina; nadie más lo ve).
# or_recv (en todas las PC, por la difusión de 0x4dd3b0 con eco): si el que la da es humano de la máquina que la
# mandó, el destino es de la computadora, son aliados y el objetivo es válido, llena OR_TAB con 3 (vale en los 2 turnos
# siguientes del bando). La PC que corre ese bando (0x536b33) le contesta al humano con un 0x1ac del bando: se ve
# con el chat nativo solo en la máquina del humano.
OR_PKT = 0x2a2
ch_buf = place_data('ch_buf', bytes(64))
ch_out = place_data('ch_out', bytes(64))
ch_k_atac = place_data('ch_k_atac', cstr_('atac'))
ch_k_mand = place_data('ch_k_mand', cstr_('mand'))
ch_t_help = place_data('ch_t_help', cstr_('Ordenes: ataca CIUDAD / ataca a BANDO / mandame refuerzos'))
ch_t_ally = place_data('ch_t_ally', cstr_('No somos aliados'))
ch_f = [place_data(f'ch_f{k}', cstr_(s)) for k, s in
        enumerate(('Ok, ataco %s', 'Ok, ataco a %s', 'Ok, te mando refuerzos%s'), 1)]
ch_ftab = place_data('ch_ftab', struct.pack('<3I', *ch_f))
ch_empty = place_data('ch_empty', b'\0')
# ch_msg(bando, texto) cdecl: 0x1ac del bando que solo se muestra en esta máquina.
ch_msg = place('ch_msg', f'''
    push ebp
    mov ebp, esp
    sub esp, 8
    mov dword ptr [ebp - 8], 0
    mov dword ptr [ebp - 4], 0
    call 0x4dd3a0
    movsx eax, ax
    mov byte ptr [ebp + eax - 8], 1
    push dword ptr [ebp + 0xc]
    lea eax, [ebp - 8]
    push eax
    push dword ptr [ebp + 8]
    call 0x4ba990
    add esp, 0xc
    leave
    ret
''')
# ch_pre(texto, clave) cdecl -> eax = 1 si el texto empieza con la clave (en minúsculas), sin distinguir mayúsculas.
ch_pre = place('ch_pre', f'''
    mov ecx, dword ptr [esp + 4]
    mov edx, dword ptr [esp + 8]
cp_lp:
    mov al, byte ptr [edx]
    test al, al
    jz cp_yes
    mov ah, byte ptr [ecx]
    or ah, 0x20
    cmp ah, al
    jne cp_no
    inc ecx
    inc edx
    jmp cp_lp
cp_yes:
    mov eax, 1
    ret
cp_no:
    xor eax, eax
    ret
''')
# ch_order(n, texto) cdecl: texto = lo que sigue a «#n». Preserva ebx esi edi ebp.
ch_order = place('ch_order', f'''
    push ebp
    mov ebp, esp
    sub esp, 8
    push ebx
    push esi
    push edi
    movsx ebx, word ptr [0x537ce8]
    mov edi, dword ptr [ebp + 8]
    push dword ptr [ebp + 0xc]
    push ebx
    call {ch_msg:#x}
    add esp, 8
    imul eax, ebx, 56
    cmp byte ptr [eax + edi + {DIPLO:#x}], 0
    jne co_notally
    mov esi, dword ptr [ebp + 0xc]
co_sk:
    cmp byte ptr [esi], 0x20
    jne co_skd
    inc esi
    jmp co_sk
co_skd:
    push {ch_k_atac:#x}
    push esi
    call {ch_pre:#x}
    add esp, 8
    test eax, eax
    jnz co_w
    push {ch_k_mand:#x}
    push esi
    call {ch_pre:#x}
    add esp, 8
    test eax, eax
    jz co_bad
    mov ecx, 3
    mov edx, ebx
    jmp co_send
co_w:
    mov al, byte ptr [esi]
    test al, al
    jz co_bad
    cmp al, 0x20
    je co_ws
    inc esi
    jmp co_w
co_ws:
    inc esi
    cmp byte ptr [esi], 0x20
    je co_ws
    xor ecx, ecx
co_cp:
    mov al, byte ptr [esi + ecx]
    mov byte ptr [ecx + {ch_buf:#x}], al
    test al, al
    jz co_tr
    inc ecx
    cmp ecx, 63
    jb co_cp
    mov byte ptr [ecx + {ch_buf:#x}], 0
co_tr:
    test ecx, ecx
    jz co_bad
    cmp byte ptr [ecx + {ch_buf - 1:#x}], 0x20
    jne co_city0
    dec ecx
    mov byte ptr [ecx + {ch_buf:#x}], 0
    jmp co_tr
co_city0:
    xor esi, esi
co_cl:
    movsx eax, word ptr [0x537e2a]
    cmp esi, eax
    jge co_side
    imul eax, esi, 0xde
    cmp byte ptr [eax + {CITIES + 0xa4:#x}], 0
    je co_cn
    add eax, {CITIES + 4:#x}
    push eax
    push {ch_buf:#x}
    call dword ptr [{STRICMP:#x}]
    add esp, 8
    test eax, eax
    jz co_city
co_cn:
    inc esi
    jmp co_cl
co_city:
    mov ecx, 1
    mov edx, esi
    jmp co_send
co_side:
    mov al, byte ptr [{ch_buf:#x}]
    or al, 0x20
    cmp al, 0x61
    jne co_bad
    cmp byte ptr [{ch_buf + 1:#x}], 0x20
    jne co_bad
    mov esi, {ch_buf + 2:#x}
co_ss:
    cmp byte ptr [esi], 0x20
    jne co_ssd
    inc esi
    jmp co_ss
co_ssd:
    movzx edx, byte ptr [esi]
    sub edx, 0x31
    cmp edx, 7
    ja co_sname
    cmp byte ptr [esi + 1], 0
    je co_sok
co_sname:
    xor edx, edx
co_sl:
    imul eax, edx, {SIDE:#x}
    cmp byte ptr [eax + {SIDE_ON:#x}], 0
    je co_sn
    add eax, 0x536b34
    push edx
    push eax
    push esi
    call dword ptr [{STRICMP:#x}]
    add esp, 8
    pop edx
    test eax, eax
    jz co_sok
co_sn:
    inc edx
    cmp edx, 8
    jb co_sl
    jmp co_bad
co_sok:
    imul eax, edx, {SIDE:#x}
    cmp byte ptr [eax + {SIDE_ON:#x}], 0
    je co_bad
    cmp edx, ebx
    je co_bad
    mov ecx, 2
co_send:
    mov word ptr [ebp - 8], bx
    mov word ptr [ebp - 6], di
    mov word ptr [ebp - 4], cx
    mov word ptr [ebp - 2], dx
    push 8
    lea eax, [ebp - 8]
    push eax
    push {OR_PKT:#x}
    call 0x4dd3b0
    add esp, 0xc
    jmp co_end
co_notally:
    push {ch_t_ally:#x}
    push edi
    call {ch_msg:#x}
    add esp, 8
    jmp co_end
co_bad:
    push {ch_t_help:#x}
    push edi
    call {ch_msg:#x}
    add esp, 8
co_end:
    pop edi
    pop esi
    pop ebx
    leave
    ret
''')
# Mapas al azar: el generador (0x4ca05a) copia a la carpeta de la partida uno de RANDOM\<set>\ITEM.DAT/ITEM0-2.DAT
# (tirada 0x4deb20(1, 4, -1) sobre la tabla 0x500228), listas fijas de ítems originales. Formato (0x4a0fb0, 362
# bytes): word porcentaje, 16 nombres de 9 bytes que se cargan siempre, 16 que se cargan si 1d100 <= porcentaje y 8
# especiales (ITEM.INI). La tabla de ítems de la partida (0x55cb74, 0xd8 c/u) tiene lugar para 40 y no se agranda.
# Tras la copia se rearman los 32 primeros con un sorteo sin repetición entre todos los ITEMS\*.ITM (originales y
# personalizados), porcentaje 100, sin repetir los especiales. Quedan afuera los que tienen «fly» en el nombre
# (ítems de vuelo: bootfly, potfly, FlyShoot...).
ri_names = place_data('ri_names', bytes(9 * 1024))
ri_fd = place_data('ri_fd', bytes(0x120))        # _finddata_t: nombre en +20
ri_buf = place_data('ri_buf', bytes(0x170))
ri_pat = place_data('ri_pat', b'ITEMS\\*.ITM\0')
ri_tmp = place_data('ri_tmp', bytes(4))
ri_go = place('ri_go', f'''
    pop eax
    mov dword ptr [{ri_tmp:#x}], eax
    call dword ptr [0x5a9844]
    push dword ptr [{ri_tmp:#x}]
    pushad
    push {ri_fd:#x}
    push {ri_pat:#x}
    call dword ptr [0x5a9b84]
    add esp, 8
    cmp eax, -1
    je ri_done
    mov esi, eax
    xor ebx, ebx
ri_nxt:
    cmp ebx, 1024
    jae ri_fin
    lea edi, [ebx + ebx*8 + {ri_names:#x}]
    xor ecx, ecx
ri_cp:
    mov al, byte ptr [ecx + {ri_fd + 20:#x}]
    cmp al, 0x2e
    je ri_z
    test al, al
    je ri_z
    cmp ecx, 8
    jae ri_z
    mov byte ptr [edi + ecx], al
    inc ecx
    jmp ri_cp
ri_z:
    cmp ecx, 9
    jae ri_ok
    mov byte ptr [edi + ecx], 0
    inc ecx
    jmp ri_z
ri_ok:
    xor ecx, ecx
ri_fly:
    mov al, byte ptr [edi + ecx]
    or al, 0x20
    cmp al, 0x66
    jne ri_fn
    mov al, byte ptr [edi + ecx + 1]
    or al, 0x20
    cmp al, 0x6c
    jne ri_fn
    mov al, byte ptr [edi + ecx + 2]
    or al, 0x20
    cmp al, 0x79
    je ri_skip
ri_fn:
    inc ecx
    cmp ecx, 6
    jbe ri_fly
    inc ebx
ri_skip:
    push {ri_fd:#x}
    push esi
    call dword ptr [0x5a9b80]
    add esp, 8
    test eax, eax
    je ri_nxt
ri_fin:
    push esi
    call dword ptr [0x5a9b7c]
    add esp, 4
    test ebx, ebx
    je ri_done
    lea eax, [ebp - 0x60]
    push 0
    push 0x80
    push 3
    push 0
    push 0
    push 0xc0000000
    push eax
    call dword ptr [0x5a9810]
    cmp eax, -1
    je ri_done
    mov esi, eax
    push 0
    push {ri_tmp:#x}
    push 0x16a
    push {ri_buf:#x}
    push esi
    call dword ptr [0x5a9814]
    test eax, eax
    je ri_close
    cmp dword ptr [{ri_tmp:#x}], 0x16a
    jne ri_close
    mov word ptr [{ri_buf:#x}], 100
    xor edi, edi
ri_slot:
    cmp edi, 32
    jae ri_write
    lea ebp, [edi + edi*8 + {ri_buf + 2:#x}]
ri_pick:
    test ebx, ebx
    je ri_clear
    push -1
    push ebx
    push 1
    call 0x4deb20
    add esp, 12
    movsx eax, ax
    dec ebx
    lea ecx, [eax + eax*8 + {ri_names:#x}]
    lea edx, [ebx + ebx*8 + {ri_names:#x}]
    mov eax, dword ptr [ecx]
    mov dword ptr [ebp], eax
    mov eax, dword ptr [ecx + 4]
    mov dword ptr [ebp + 4], eax
    mov al, byte ptr [ecx + 8]
    mov byte ptr [ebp + 8], al
    mov eax, dword ptr [edx]
    mov dword ptr [ecx], eax
    mov eax, dword ptr [edx + 4]
    mov dword ptr [ecx + 4], eax
    mov al, byte ptr [edx + 8]
    mov byte ptr [ecx + 8], al
    mov ecx, {ri_buf + 2 + 32 * 9:#x}
ri_esp:
    cmp byte ptr [ecx], 0
    je ri_esn
    push ecx
    push ecx
    push ebp
    call dword ptr [0x5a9be0]
    add esp, 8
    pop ecx
    test eax, eax
    je ri_pick
ri_esn:
    add ecx, 9
    cmp ecx, {ri_buf + 2 + 40 * 9:#x}
    jb ri_esp
    inc edi
    jmp ri_slot
ri_clear:
    mov dword ptr [ebp], 0
    mov dword ptr [ebp + 4], 0
    mov byte ptr [ebp + 8], 0
    inc edi
    jmp ri_slot
ri_write:
    push 0
    push 0
    push 0
    push esi
    call dword ptr [0x5a981c]
    push 0
    push {ri_tmp:#x}
    push 0x16a
    push {ri_buf:#x}
    push esi
    call dword ptr [0x5a9818]
ri_close:
    push esi
    call dword ptr [0x5a97d8]
ri_done:
    popad
    ret
''')
# La barra de chat acepta «.» además de «#» para dirigir el mensaje («.3 ataca X»): el punto se escribe sin AltGr
# en cualquier distribución de teclado. El resto del texto lo lee igual (desde [ebp + 1]).
ch_pfx = place('ch_pfx', '''
    cmp byte ptr [ebp], 0x23
    je 0x40918b
    cmp byte ptr [ebp], 0x2e
    je 0x40918b
    jmp 0x409302
''')
# Reemplaza «jne 0x409317» en 0x4091ea (ebp = «#n...», el bando n está activo y no es humano).
ch_ai = place('ch_ai', f'''
    pushad
    lea eax, [ebp + 2]
    push eax
    movzx eax, byte ptr [ebp + 1]
    sub eax, 0x31
    push eax
    call {ch_order:#x}
    add esp, 8
    popad
    jmp 0x409317
''')
# Recepción (reemplaza «ja 0x4b85bb» en 0x4b6a22, antes que tl_recv; eax = tipo + 8, esi = paquete: +6 máquina que
# lo mandó, +0xc carga).
or_recv = place('or_recv', f'''
    cmp eax, {OR_PKT + 8:#x}
    jne {tl_recv:#x}
    pushad
    movsx ebx, word ptr [esi + 0xc]
    movsx edi, word ptr [esi + 0xe]
    cmp ebx, 8
    jae orr_x
    cmp edi, 8
    jae orr_x
    imul eax, ebx, {SIDE:#x}
    cmp byte ptr [eax + {SIDE_ON:#x}], 0
    je orr_x
    cmp word ptr [eax + {SIDE_HUMAN:#x}], -1
    jne orr_x
    movzx ecx, byte ptr [eax + {SIDE_MACHINE:#x}]
    movsx edx, word ptr [esi + 6]
    cmp ecx, edx
    jne orr_x
    imul eax, edi, {SIDE:#x}
    cmp byte ptr [eax + {SIDE_ON:#x}], 0
    je orr_x
    cmp word ptr [eax + {SIDE_HUMAN:#x}], -1
    je orr_x
    imul eax, ebx, 56
    cmp byte ptr [eax + edi + {DIPLO:#x}], 0
    jne orr_x
    movzx ecx, word ptr [esi + 0x10]
    movsx edx, word ptr [esi + 0x12]
    cmp ecx, 1
    jne orr_2
    movsx eax, word ptr [0x537e2a]
    cmp edx, eax
    jae orr_x
    imul eax, edx, 0xde
    add eax, {CITIES + 4:#x}
    jmp orr_ok
orr_2:
    cmp ecx, 2
    jne orr_3
    cmp edx, 8
    jae orr_x
    imul eax, edx, {SIDE:#x}
    add eax, 0x536b34
    jmp orr_ok
orr_3:
    cmp ecx, 3
    jne orr_x
    cmp edx, ebx
    jne orr_x
    mov eax, {ch_empty:#x}
orr_ok:
    mov byte ptr [edi*8 + {OR_TAB:#x}], cl
    mov byte ptr [edi*8 + {OR_TAB + 1:#x}], 3
    mov word ptr [edi*8 + {OR_TAB + 2:#x}], dx
    mov byte ptr [edi*8 + {OR_TAB + 4:#x}], bl
    mov esi, eax
    mov ebp, ecx
    call 0x4dd3a0
    movsx eax, ax
    imul ecx, edi, {SIDE:#x}
    movzx ecx, byte ptr [ecx + {SIDE_MACHINE:#x}]
    cmp eax, ecx
    jne orr_x
    push esi
    push dword ptr [ebp*4 + {ch_ftab - 4:#x}]
    push {ch_out:#x}
    call dword ptr [{SPRINTF:#x}]
    add esp, 0xc
    sub esp, 8
    mov dword ptr [esp], 0
    mov dword ptr [esp + 4], 0
    imul eax, ebx, {SIDE:#x}
    movzx eax, byte ptr [eax + {SIDE_MACHINE:#x}]
    mov byte ptr [esp + eax], 1
    mov eax, esp
    push {ch_out:#x}
    push eax
    push edi
    call 0x4ba990
    add esp, 0x14
orr_x:
    popad
    jmp 0x4b85bb
''')
# ---- Construir trampas (PENDIENTE-pozos-y-trampas.md, parte 7). Un grupo con un ejército (no héroe) cuyo registro
# tiene el bono "Trap" construye, desde su menú de órdenes (diálogo 0x1f = RES 34, renglón nuevo TR_TXT / TR_HOT),
# una trampa oculta en la casilla del líder, al costo de fundar una ciudad. Casilla: la de una tumba (pg_ok
# PO_TRAMPA: cualquier casilla libre, también agua; ahí es mina submarina) y lugar en la tabla. Confirma con el
# diálogo de reconstruir (TR_MARK) y la orden viaja como TR_PKT (bando, x, y): en todas las PC tr_recv vuelve a
# comprobar todo, cobra y agrega {x, y, PO_TRAMPA, 0, bit del dueño, dueño}. La IA no la usa.
TRAP = b'trap'      # bono de combate (nombre +0xd6), no de movimiento
trapstr = place_data('trapstr', TRAP + b'\0')
reccomb = place('reccomb', boatbon_src('reccomb', None, rec=True, off=0xd6, slots=1))
TR_TXT, TR_HOT = 0x17, 0x18
TR_PKT = 0x2a3
tr_menutxt = place_data('tr_menutxt', cstr_('Build Trap'))
# Desde br_menu (edi = x, ebp = y del líder). Preserva todo.
tr_check = place('tr_check', f'''
    pushad
    mov word ptr [{TR_X:#x}], di
    mov word ptr [{TR_Y:#x}], bp
    cmp dword ptr [{PO_N:#x}], {PO_MAX}
    jae tk_out
    mov esi, edi
    mov edi, ebp
    mov ebp, {PO_TRAMPA}
    call {pg_ok:#x}
    jnz tk_out
    movsx ebx, word ptr [0x537ce8]
    cmp ebx, 8
    jae tk_out
    imul ebx, ebx, 0x4f0
    movsx ecx, word ptr [ebx + 0x56eaa8]
tk_army:
    dec ecx
    js tk_out
    movsx eax, word ptr [ebx + ecx*2 + 0x56ea94]
    imul eax, eax, 0x1c
    movzx eax, word ptr [eax + 0x54fe5e]
    mov edx, eax
    and edx, 0x1f
    cmp edx, 15
    ja tk_army
    shr eax, 5
    and eax, 0xf
    shl eax, 4
    add eax, edx
    imul eax, eax, 0xfc
    add eax, 0x53c410
    mov edx, {trapstr:#x}
    call {reccomb:#x}
    test eax, eax
    jz tk_army
    mov byte ptr [{TR_FLAG:#x}], 1
tk_out:
    popad
    ret
''')
caves['tr_chkp'] = struct.pack('<I', tr_check)
# Habilitación (en 0x4affc2 de 0x4afec0, al abrir el menú, después de 0x4b0660).
tr_init = place('tr_init', f'''
    cmp byte ptr [{TR_FLAG:#x}], 1
    sbb eax, eax
    and eax, 2
    push eax
    push {TR_HOT:#x}
    call 0x4dcec0
    add esp, 8
    mov ecx, 0x588bd0
    jmp 0x4affc7
''')
# Texto y color (en 0x4b0450 de 0x4b0130; esi = zona bajo el mouse, [esp + 0x1c] = 1 al crear).
tr_hover = place('tr_hover', f'''
    cmp dword ptr [esp + 0x1c], 0
    je th_col
    push {tr_menutxt:#x}
    push {TR_TXT:#x}
    call 0x4dd240
    add esp, 8
th_col:
    push 0
    push 0
    cmp esi, {TR_HOT:#x}
    jne th_en
    push 0xf
    jmp th_set
th_en:
    cmp byte ptr [{TR_FLAG:#x}], 0
    je th_dis
    push 0x5c
    jmp th_set
th_dis:
    push 0x56
th_set:
    push {TR_TXT:#x}
    call 0x4dd2b0
    add esp, 0x10
    mov ecx, 0x588bd0
    jmp 0x4b0455
''')
# Clic (en 0x4b0487 de 0x4b0460; eax = zona): cierra el menú y abre el diálogo de reconstruir con TR_MARK.
tr_click = place('tr_click', f'''
    cmp eax, {TR_HOT:#x}
    je tc_trap
    sub eax, 0xb
    cmp eax, 0xb
    ja 0x4b0496
    jmp 0x4b048f
tc_trap:
    cmp byte ptr [{TR_FLAG:#x}], 0
    je 0x4b0496
    mov ecx, 0x588bd0
    call 0x4d7d70
    mov word ptr [0x587e5c], {TR_MARK:#x}
    call 0x4b6180
    pop edi
    pop esi
    ret
''')
# OK del diálogo (reemplaza «call 0x4b9ce0(índice, costo, jugador)» en 0x4b6236).
tr_send = place('tr_send', f'''
    cmp word ptr [esp + 4], {TR_MARK:#x}
    jne 0x4b9ce0
    sub esp, 8
    mov ax, word ptr [esp + 0x14]
    mov word ptr [esp], ax
    mov ax, word ptr [{TR_X:#x}]
    mov word ptr [esp + 2], ax
    mov ax, word ptr [{TR_Y:#x}]
    mov word ptr [esp + 4], ax
    mov word ptr [esp + 6], 0
    mov eax, esp
    push 8
    push eax
    push {TR_PKT:#x}
    call 0x4dd3b0
    add esp, 0x14
    ret
''')
# Recepción (antes que or_recv; eax = tipo + 8, esi = paquete: +6 máquina que lo mandó, +0xc bando, x, y).
tr_recv = place('tr_recv', f'''
    cmp eax, {TR_PKT + 8:#x}
    jne {or_recv:#x}
    pushad
    movsx ebx, word ptr [esi + 0xc]
    cmp ebx, 8
    jae tv_x
    imul eax, ebx, {SIDE:#x}
    cmp byte ptr [eax + {SIDE_ON:#x}], 0
    je tv_x
    cmp word ptr [eax + {SIDE_HUMAN:#x}], -1
    jne tv_x
    movzx ecx, byte ptr [eax + {SIDE_MACHINE:#x}]
    movsx edx, word ptr [esi + 6]
    cmp ecx, edx
    jne tv_x
    cmp dword ptr [{PO_N:#x}], {PO_MAX}
    jae tv_x
    movsx edi, word ptr [esi + 0x10]
    movsx esi, word ptr [esi + 0xe]
    mov ebp, {PO_TRAMPA}
    call {pg_ok:#x}
    jnz tv_x
    push ebx
    push {TR_MARK:#x}
    call 0x4b65e0
    add esp, 8
    movsx ebp, ax
    imul eax, ebx, {SIDE:#x}
    cmp ebp, dword ptr [eax + 0x536c14]
    jg tv_x
    neg ebp
    push ebp
    push ebx
    call 0x43fd60
    add esp, 8
    mov eax, dword ptr [{PO_N:#x}]
    lea edx, [eax*8 + {PO_TAB:#x}]
    mov word ptr [edx], si
    mov word ptr [edx + 2], di
    mov byte ptr [edx + 4], {PO_TRAMPA}
    mov byte ptr [edx + 5], 0
    mov cl, bl
    mov al, 1
    shl al, cl
    mov byte ptr [edx + 6], al
    mov byte ptr [edx + 7], bl
    inc dword ptr [{PO_N:#x}]
    call {po_rebuild:#x}
    call {REDRAW:#x}
tv_x:
    popad
    jmp 0x4b85bb
''')
# al_surv(p) cdecl, desde ia_turn: por cada pila de p anotada como amenazada en un turno anterior, evento 12 con
# x, y donde estaba y n = 1 si su líder sigue vivo y es de p, 0 si no. Preserva todo.
al_surv = place('al_surv', f'''
    pushad
    mov ebx, dword ptr [esp + 0x24]
    cmp ebx, 8
    jae sv_out
    imul esi, ebx, 80
    add esi, {AL_THR:#x}
    mov edi, 10
sv_lp:
    movsx eax, word ptr [esi + 6]
    test eax, eax
    jz sv_nx
    cmp ax, word ptr [0x503328]
    jge sv_nx
    xor edx, edx
    movsx eax, word ptr [esi]
    imul ecx, eax, 0x1c
    test byte ptr [ecx + 0x54fe63], 0x40
    jz sv_log
    movzx eax, word ptr [ecx + 0x54fe5e]
    shr eax, 5
    and eax, 15
    cmp eax, ebx
    jne sv_log
    inc edx
sv_log:
    movsx eax, word ptr [esi + 4]
    movsx ecx, word ptr [esi + 2]
    push edx
    push eax
    push ecx
    push ebx
    push 12
    call {ia_evt:#x}
    add esp, 0x14
    mov dword ptr [esi], 0
    mov dword ptr [esi + 4], 0
sv_nx:
    add esi, 8
    dec edi
    jnz sv_lp
sv_out:
    popad
    ret
''')

# tr_turn: ebx = jugador que empieza su turno -> las trampas que explotó dejan de estar recién explotadas (TR_RECIEN):
# vuelve a verse la mina, o el humo si está gastada. Corre en todas las PC con los mismos datos. Preserva todo.
tr_turn = place('tr_turn', f'''
    pushad
    xor edx, edx
tt_loop:
    cmp edx, dword ptr [{PO_N:#x}]
    jae tt_end
    cmp edx, {PO_MAX}
    jae tt_end
    cmp byte ptr [edx*8 + {PO_TAB + 4:#x}], {PO_TRAMPA}
    jne tt_next
    movzx eax, byte ptr [edx*8 + {PO_TAB + 5:#x}]
    test al, {TR_RECIEN}
    jz tt_next
    mov ecx, eax
    shr ecx, 4
    and ecx, 7
    cmp ecx, ebx
    jne tt_next
    and al, {TR_CUENTA}
    mov byte ptr [edx*8 + {PO_TAB + 5:#x}], al
tt_next:
    inc edx
    jmp tt_loop
tt_end:
    popad
    ret
''')
# ia_turn(p) cdecl, en lugar de turn en 0x4223ad: registra y sigue con turn. Preserva lo que turn recibe.
ia_turn = place('ia_turn', f'''
    pushad
    movsx ebx, word ptr [esp + 0x24]
    cmp ebx, 8
    jae it_out
    call {tr_turn:#x}
    cmp byte ptr [ebx*8 + {OR_TAB + 1:#x}], 0
    je it_ord
    dec byte ptr [ebx*8 + {OR_TAB + 1:#x}]
it_ord:
    mov byte ptr [{IA_ON:#x}], 0
    push {IA_R:#x}
    push {IA_PATH:#x}
    call dword ptr [{FOPEN:#x}]
    add esp, 8
    test eax, eax
    jz it_out
    push eax
    call dword ptr [{FCLOSE:#x}]
    add esp, 4
    mov byte ptr [{IA_ON:#x}], 1
    xor esi, esi
it_key:
    push {IA_PATH:#x}
    push 16
    push {IA_VAL:#x}
    push {IA_EMPTY:#x}
    push dword ptr [esi*4 + {IA_KEYTAB:#x}]
    push {IA_SEC:#x}
    call dword ptr [{GETPROF:#x}]
    mov dl, 0
    test eax, eax
    jz it_set
    push {IA_ORIG:#x}
    push {IA_VAL:#x}
    call dword ptr [{STRICMP:#x}]
    add esp, 8
    mov dl, 0
    test eax, eax
    jz it_set
    push {IA_PRUEBA:#x}
    push {IA_VAL:#x}
    call dword ptr [{STRICMP:#x}]
    add esp, 8
    mov dl, 1
    test eax, eax
    jz it_set
    mov dl, 2
it_set:
    mov byte ptr [esi + {IA_MODE:#x}], dl
    inc esi
    cmp esi, 8
    jb it_key
    push {IA_SNAP:#x}
    push ebx
    call {ia_snap:#x}
    add esp, 8
    push {IA_A:#x}
    push {IA_CSV:#x}
    call dword ptr [{FOPEN:#x}]
    add esp, 8
    test eax, eax
    jz it_out
    mov edi, eax
    mov ecx, {IA_N}
it_push:
    push dword ptr [ecx*4 + {IA_SNAP - 4:#x}]
    loop it_push
    movzx eax, byte ptr [ebx + {IA_MODE:#x}]
    push eax
    push ebx
    movsx eax, word ptr [0x503328]
    push eax
    push {IA_FMT:#x}
    push edi
    call dword ptr [{FPRINTF:#x}]
    add esp, {4 * (IA_N + 5):#x}
    push edi
    call dword ptr [{FCLOSE:#x}]
    add esp, 4
    push ebx
    call {ia_dip:#x}
    call {ia_refug:#x}
    call {al_surv:#x}
    add esp, 4
it_out:
    popad
    jmp {turn:#x}
''')

# Batallas: 0x469ed0 arma la ficha (0x464ac0), pelea (0x464ea0) y en 0x469f54 llama a 0x465c80(ficha, resultado),
# que informa y aplica el resultado ([resultado] palabra: 1 = gana el atacante; 0x465cb9 elige al ganador así).
# Ficha: +0 atacante, +1 dueño de la casilla atacada, +2 ciudad (-1 ninguna), +4/+6 x/y, +0xc/+0xd cantidad de
# atacantes/defensores; atacantes en +0xe + i*0x24, defensores en +0x12e + i*0x24 (palabra +0 = ejército, < 1 vacío).
# ia_bat la reemplaza en 0x469f54, solo con DATA\IA.INI (ia_on): cuenta la composición por ranura antes (s0..s15,
# héroes en s16), llama a 0x465c80 y cuenta los sobrevivientes (ejército vivo y del mismo dueño), y agrega a
# DATA\IA_BAT.CSV: turno, atacante, defensor, x, y, ciudad, resultado, ia del atacante, ia del defensor (-1 sin dueño),
# atacantes, defensores, atacantes vivos, defensores vivos, A s0..s16, D s0..s16, colores de los defensores (máscara:
# bit c = había un ejército del color c entre los defensores; en una ciudad compartida pueden ser varios).
IA_BCSV = place_data('ia_bcsv', cstr_(r'.\DATA\IA_BAT.CSV'))
IA_BN = 13 + 2 * 17 + 1
IA_BFMT = place_data('ia_bfmt', cstr_('%d' + ',%d' * (IA_BN - 1) + '\n'))
IA_BBUF = place_data('ia_bbuf', bytes(4 * IA_BN))
IA_BOWN = place_data('ia_bown', bytes(4 * 40))    # dueño de cada ejército de la ficha antes de pelear (-1 vacío)

# ia_bside: esi = primera entrada, ecx = cantidad, edi = 17 contadores, ebp = su parte de IA_BOWN. Preserva todo.
ia_bside = place('ia_bside', f'''
    pushad
bs_loop:
    dec ecx
    jl bs_out
    imul edx, ecx, 0x24
    mov dword ptr [ebp + ecx*4], -1
    movsx eax, word ptr [esi + edx]
    test eax, eax
    jle bs_loop
    imul eax, eax, 0x1c
    movzx eax, word ptr [eax + 0x54fe5e]
    mov edx, eax
    shr edx, 5
    and edx, 0xf
    mov dword ptr [ebp + ecx*4], edx
    and eax, 0x1f
    cmp eax, 0x10
    jbe bs_cnt
    mov eax, 0x10
bs_cnt:
    inc dword ptr [edi + eax*4]
    jmp bs_loop
bs_out:
    popad
    ret
''')

# ia_balive: esi, ecx, ebp como ia_bside -> eax = cuántos siguen vivos con el mismo dueño. Preserva el resto.
ia_balive = place('ia_balive', f'''
    push ecx
    push edx
    push ebx
    xor ebx, ebx
ba_loop:
    dec ecx
    jl ba_out
    imul edx, ecx, 0x24
    movsx eax, word ptr [esi + edx]
    test eax, eax
    jle ba_loop
    imul eax, eax, 0x1c
    test byte ptr [eax + 0x54fe63], 0x40
    jz ba_loop
    movzx eax, word ptr [eax + 0x54fe5e]
    shr eax, 5
    and eax, 0xf
    cmp eax, dword ptr [ebp + ecx*4]
    jne ba_loop
    inc ebx
    jmp ba_loop
ba_out:
    mov eax, ebx
    pop ebx
    pop edx
    pop ecx
    ret
''')

# ia_bat(ficha, resultado) cdecl, en lugar de 0x465c80 en 0x469f54.
ia_bat = place('ia_bat', f'''
    cmp byte ptr [{IA_ON:#x}], 0
    je 0x465c80
    pushad
    mov ebx, dword ptr [esp + 0x24]
    mov edi, {IA_BBUF:#x}
    xor eax, eax
    mov ecx, {IA_BN}
    rep stosd
    mov edi, {IA_BBUF:#x}
    movsx eax, word ptr [0x503328]
    mov dword ptr [edi], eax
    movsx eax, byte ptr [ebx]
    mov dword ptr [edi + 4], eax
    cmp eax, 8
    jae ib_ma
    movzx eax, byte ptr [eax + {IA_MODE:#x}]
    mov dword ptr [edi + 28], eax
ib_ma:
    movsx eax, byte ptr [ebx + 1]
    mov dword ptr [edi + 8], eax
    mov dword ptr [edi + 32], -1
    cmp eax, 8
    jae ib_md
    movzx eax, byte ptr [eax + {IA_MODE:#x}]
    mov dword ptr [edi + 32], eax
ib_md:
    movsx eax, word ptr [ebx + 4]
    mov dword ptr [edi + 12], eax
    movsx eax, word ptr [ebx + 6]
    mov dword ptr [edi + 16], eax
    movsx eax, word ptr [ebx + 2]
    mov dword ptr [edi + 20], eax
    mov eax, dword ptr [esp + 0x28]
    movsx eax, word ptr [eax]
    mov dword ptr [edi + 24], eax
    movsx ecx, byte ptr [ebx + 0xc]
    mov dword ptr [edi + 36], ecx
    lea esi, [ebx + 0xe]
    mov ebp, {IA_BOWN:#x}
    add edi, 52
    call {ia_bside:#x}
    movsx ecx, byte ptr [ebx + 0xd]
    mov dword ptr [{IA_BBUF + 40:#x}], ecx
    lea esi, [ebx + 0x12e]
    mov ebp, {IA_BOWN + 32:#x}
    add edi, 68
    call {ia_bside:#x}
    movsx ecx, byte ptr [ebx + 0xd]
    xor edx, edx
ib_mk:
    dec ecx
    jl ib_mkd
    mov eax, dword ptr [ecx*4 + {IA_BOWN + 32:#x}]
    cmp eax, 8
    jae ib_mk
    bts edx, eax
    jmp ib_mk
ib_mkd:
    mov dword ptr [{IA_BBUF + 4 * (IA_BN - 1):#x}], edx
    popad
    push dword ptr [esp + 8]
    push dword ptr [esp + 8]
    call 0x465c80
    add esp, 8
    pushad
    mov ebx, dword ptr [esp + 0x24]
    movsx ecx, byte ptr [ebx + 0xc]
    lea esi, [ebx + 0xe]
    mov ebp, {IA_BOWN:#x}
    call {ia_balive:#x}
    mov dword ptr [{IA_BBUF + 44:#x}], eax
    movsx ecx, byte ptr [ebx + 0xd]
    lea esi, [ebx + 0x12e]
    mov ebp, {IA_BOWN + 32:#x}
    call {ia_balive:#x}
    mov dword ptr [{IA_BBUF + 48:#x}], eax
    push {IA_A:#x}
    push {IA_BCSV:#x}
    call dword ptr [{FOPEN:#x}]
    add esp, 8
    test eax, eax
    jz ib_out
    mov edi, eax
    mov ecx, {IA_BN}
ib_push:
    push dword ptr [ecx*4 + {IA_BBUF - 4:#x}]
    loop ib_push
    push {IA_BFMT:#x}
    push edi
    call dword ptr [{FPRINTF:#x}]
    add esp, {4 * (IA_BN + 2):#x}
    push edi
    call dword ptr [{FCLOSE:#x}]
    add esp, 4
ib_out:
    popad
    ret
''')


# Tandas (ia\tanda.py): con [Tanda] Partida=<nombre> en DATA\IA.INI, al mostrarse el menú principal por primera vez
# (llamada 0x452c3b a 0x4aab10, la del arranque; la de después del Game Over, 0x482322, no) se pide cargar
# SAVES\<nombre>.SAV con 0x4b9c10(nombre, 0), lo mismo que hace el diálogo Load Game (0x42c696).
# Antes abre la pantalla de un jugador (0x443980, lo que hace el botón Single Player en 0x4aae18): la carga la atiende
# esa pantalla; desde el menú principal el pedido quedaba esperando a que se apretara el botón.
IA_TSEC = place_data('ia_tsec', cstr_('Tanda'))
IA_TKEY = place_data('ia_tkey', cstr_('Partida'))
IA_TNAME = place_data('ia_tname', bytes(64))
# Archivos que instaló una versión anterior del parche y ya no van (un bono renombrado o quitado): en el arranque,
# antes del menú, DeleteFileA ([0x5a97c0]) los borra de C:\Warlords3, así todas las PC quedan con los mismos bonos
# en el editor aunque el Actualizador no borre nada. Si no están, DeleteFileA falla sin más.
OBSOLETOS = (r'TERRAIN\SUBTYPE\camo.STT', r'TERRAIN\SUBTYPE\nighmare.STT', r'TERRAIN\SUBTYPE\bridge.STT')
obs_strs = [place_data(f'obs{i}', cstr_(n)) for i, n in enumerate(OBSOLETOS)]
ia_menu = place('ia_menu', f'''
    pushad
''' + ''.join(f'''    push {a:#x}
    call dword ptr [0x5a97c0]
''' for a in obs_strs) + f'''    popad
    call 0x4aab10
    pushad
    push {IA_PATH:#x}
    push 64
    push {IA_TNAME:#x}
    push {IA_EMPTY:#x}
    push {IA_TKEY:#x}
    push {IA_TSEC:#x}
    call dword ptr [{GETPROF:#x}]
    test eax, eax
    jz im_out
    call 0x443980
    push 0
    push {IA_TNAME:#x}
    call 0x4b9c10
    add esp, 8
im_out:
    popad
    ret
''')

# Game Over (0x482d77): en 0x482fd6 ya están el orden y los puestos. [ebp-0xe] cantidad de bandos en juego; por
# puesto k: [ebp-0x24+2k] color, [ebp-0x5c+2k] puesto (-1 = empatado con el anterior), [ebp-0x3c+2k] PV,
# [ebp-0x4c+2k] ciudades, [ebp-0x7c+4k] oro (ia/puntos-de-victoria.md). Con IA.INI (ia_on) agrega a DATA\IA_FIN.CSV
# una línea por bando: turno, orden, puesto, color, ia, PV, ciudades, oro.
IA_FCSV = place_data('ia_fcsv', cstr_(r'.\DATA\IA_FIN.CSV'))
IA_FFMT = place_data('ia_ffmt', cstr_('%d,%d,%d,%d,%d,%d,%d,%d\n'))
# Tandas: con todos los bandos en Computadora el juego no deja guardar, así que la partida de la tanda se guarda con un
# bando en Humano. Si se cargó por [Tanda] (ia_tname no vacío), al elegir el bando del turno (0x42237a, después de
# contar los humanos en [esp+0x18]) todo bando humano pasa a Computadora (+0xe2 = 2, como el diálogo, 0x40a5df) y la
# cuenta queda en 0.
ia_compu = place('ia_compu', f'''
    cmp byte ptr [{IA_TNAME:#x}], 0
    je ic_back
    push eax
    mov eax, 0x536c12
ic_loop:
    cmp word ptr [eax], -1
    jne ic_next
    mov word ptr [eax], 2
ic_next:
    add eax, 0x1f8
    cmp eax, 0x536c12 + 8*0x1f8
    jb ic_loop
    pop eax
    mov word ptr [esp + 0x18], 0
ic_back:
    mov word ptr [0x537ce8], di
    jmp 0x422381
''')

# Tandas sin alianzas: con la diplomacia apagada, en el turno de cada bando de la computadora el juego llama a
# 0x49fec0 (en 0x4476d9), que propone guerra a los humanos (+0xe2 = -1) y alianza a todos los bandos de la computadora
# (+0xe2 = 2): la computadora se une contra el humano. En una tanda no queda ningún humano (ia_compu los pasa a 2), así
# que todos se aliaban en dos turnos y el juego daba victoria aliada al turno 3 (Tanda_hex_perfiles, 25/10/2026). Si
# la partida se cargó por [Tanda] (ia_tname no vacío) no se llama; en una partida normal sigue igual que el original.
ia_nodip = place('ia_nodip', f'''
    cmp byte ptr [{IA_TNAME:#x}], 0
    jne ind_skip
    jmp 0x49fec0
ind_skip:
    ret
''')

# Tandas en segundo plano: al perder el foco (CWnd::OnActivate, 0x4ed400, nState = WA_INACTIVE) el juego se pausa
# ([obj+0x13d] = 1 vía 0x4de090) hasta recuperarlo, así que una tanda se detenía apenas el usuario usaba otra ventana.
# Si la partida se cargó por [Tanda] (ia_tname no vacío) se saltea esa rama y el juego sigue jugando sin foco.
ia_bg = place('ia_bg', f'''
    test esi, esi
    jne 0x4ed477
    cmp byte ptr [{IA_TNAME:#x}], 0
    jne 0x4ed477
    cmp byte ptr [0x501280], 0
    jmp 0x4ed420
''')

# Tandas: la partida guardada queda en el turno del bando que se pasó a Humano para poder guardarla, y al cargarla el
# juego espera a ese humano (ia_compu recién actúa al elegir el bando siguiente). En el ciclo de espera (OnIdle,
# 0x4ecf10, después del tick 0x4dea40), una sola vez y si se cargó por [Tanda]: si el bando del turno ([0x537ce8]) está
# en Humano, todos los humanos pasan a Computadora y se termina el turno como lo hace el botón (0x415d84: 0x4d7d70 sobre
# 0x588bd0 y 0x4221a0(0)).
IA_TDONE = place_data('ia_tdone', bytes(1))
ia_tload = place('ia_tload', f'''
    call 0x4dea40
    cmp byte ptr [{IA_TNAME:#x}], 0
    je it_out
    cmp byte ptr [{IA_TDONE:#x}], 0
    jne it_out
    pushad
    movsx eax, word ptr [0x537ce8]
    cmp eax, 8
    jae it_pop
    imul eax, eax, 0x1f8
    cmp word ptr [eax + 0x536c12], -1
    jne it_pop
    mov byte ptr [{IA_TDONE:#x}], 1
    call 0x4c0ca0
it_pop:
    popad
it_out:
    ret
''')

ia_fin = place('ia_fin', f'''
    cmp byte ptr [{IA_ON:#x}], 0
    je if_back
    pushad
    push {IA_A:#x}
    push {IA_FCSV:#x}
    call dword ptr [{FOPEN:#x}]
    add esp, 8
    test eax, eax
    jz if_out
    mov edi, eax
    xor ebx, ebx
if_loop:
    cmp bx, word ptr [ebp - 0xe]
    jge if_close
    push dword ptr [ebp + ebx*4 - 0x7c]
    movsx eax, word ptr [ebp + ebx*2 - 0x4c]
    push eax
    movsx eax, word ptr [ebp + ebx*2 - 0x3c]
    push eax
    movsx ecx, word ptr [ebp + ebx*2 - 0x24]
    xor eax, eax
    cmp ecx, 8
    jae if_md
    movzx eax, byte ptr [ecx + {IA_MODE:#x}]
if_md:
    push eax
    push ecx
    movsx eax, word ptr [ebp + ebx*2 - 0x5c]
    push eax
    lea eax, [ebx + 1]
    push eax
    movsx eax, word ptr [0x503328]
    push eax
    push {IA_FFMT:#x}
    push edi
    call dword ptr [{FPRINTF:#x}]
    add esp, 0x28
    inc ebx
    jmp if_loop
if_close:
    push edi
    call dword ptr [{FCLOSE:#x}]
    add esp, 4
if_out:
    popad
if_back:
    mov si, word ptr [ebp + 0xc]
    push 1
    jmp 0x482fdc
''')

# Victoria sin Game Over (0x482570): cuando quedan solo aliados vivos, el juego abre el cartel "Victory! / An allied
# victory!" (textos 0xd3) en vez del podio, espera Aceptar y la partida sigue: ia_fin no corre nunca y la tanda la daba
# por colgada (partidas 126 y 134). En la apertura del cartel (call 0x482c10 en 0x482790), con IA.INI (ia_on),
# victoria ([0x571760]) y sin Game Over ([0x57175c] = 0), calcula los PV como el podio (0x440840) y agrega a
# DATA\IA_VIC.CSV una línea por bando en juego (+0 y +1 del registro distintos de 0, como 0x482da3): turno, color, ia,
# PV, ciudades, oro. El orden y los puestos los arma la tanda con la regla del podio.
IA_VCSV = place_data('ia_vcsv', cstr_(r'.\DATA\IA_VIC.CSV'))
IA_VFMT = place_data('ia_vfmt', cstr_('%d,%d,%d,%d,%d,%d\n'))
ia_vic = place('ia_vic', f'''
    cmp byte ptr [{IA_ON:#x}], 0
    je iv_back
    cmp byte ptr [0x571760], 0
    je iv_back
    cmp byte ptr [0x57175c], 0
    jne iv_back
    pushad
    call 0x440840
    push {IA_A:#x}
    push {IA_VCSV:#x}
    call dword ptr [{FOPEN:#x}]
    add esp, 8
    test eax, eax
    jz iv_out
    mov edi, eax
    xor ebx, ebx
iv_loop:
    imul esi, ebx, 0x1f8
    cmp byte ptr [esi + 0x536b30], 0
    je iv_next
    cmp byte ptr [esi + 0x536b31], 0
    je iv_next
    push dword ptr [esi + 0x536c14]
    movsx eax, word ptr [ebx*2 + 0x536b20]
    push eax
    movsx eax, word ptr [ebx*2 + 0x5643c8]
    push eax
    movzx eax, byte ptr [ebx + {IA_MODE:#x}]
    push eax
    push ebx
    movsx eax, word ptr [0x503328]
    push eax
    push {IA_VFMT:#x}
    push edi
    call dword ptr [{FPRINTF:#x}]
    add esp, 0x20
iv_next:
    inc ebx
    cmp ebx, 8
    jb iv_loop
    push edi
    call dword ptr [{FCLOSE:#x}]
    add esp, 4
iv_out:
    popad
iv_back:
    jmp 0x482c10
''')

# ---------------------------------------------------------------- Día/noche: pintado de la noche
# Con la opción (bit 2 de SHOPT), las vueltas pares ([0x5032f8 + 0x30]; la primera es la 1) son de
# noche: el mapa se oscurece con DN_N niveles, cada uno una pasada del recoloreo de la niebla (0x4ee3c0 con la tabla
# dn_tab en vez de 0x589608) con sus mismos bordes suaves (hoja 0x48, máscara de 8 vecinas -> 0x4fbfc8). El nivel de
# una casilla es DN_MIN más su distancia a la luz más cercana menos el radio de esa luz, entre DN_MIN y DN_N (la luz
# también se oscurece un poco). Luces: las ciudades (radio 1, distancia máx + mín / 2: halo cuadrado), y con halo
# redondo (distancia euclídea redondeada) los ejércitos de quien mira ([0x560b20], radio 1), ruinas, sitios y
# puentes en pie (0).
# dn_pre (al entrar a 0x459790, ecx = la vista) arma la grilla dn_d: la vista más un borde de 1 (para las vecinas),
# DN_G bytes por fila; de día, toda en 0. Como el mapa se repinta solo en las celdas sucias (+6 & 0x20) o enteras
# ([vista+0x1a5]), marca sucia toda celda cuya vecindad 3x3 cambió respecto de la grilla anterior (dn_old); así una
# celda nunca se oscurece dos veces ni queda con la oscuridad de antes. dn_post (en 0x45aa6e, después de la niebla)
# pinta los niveles en las mismas celdas que repintó el juego. Vistas de más de DN_MAX celdas por lado: lo que pasa
# de DN_MAX queda de día.
DN_N = 8
DN_MIN = 1
DN_MAX = 64
DN_G = DN_MAX + 2
DN_TURN = 0x5032f8 + 0x30

def dn_table():
    pal = open(os.path.join(os.path.dirname(SRC_EXE), 'war3.pal'), 'rb').read()
    rgb = [tuple(pal[3 * i:3 * i + 3]) for i in range(256)]
    cand = [10] + [i for i in range(16, 245) if i != 187]   # sin los colores de Windows, el 11 transparente ni el verde 187
    f = 0.82                                                  # por nivel: la luz ~82 %, 8 niveles ~20 %; tinte azul
    out = bytearray(range(256))
    for i in range(256):
        if i == 11: continue
        r, g, b = rgb[i]
        t = (r * f * 0.92, g * f * 0.96, b * f * 1.05)
        out[i] = min(cand, key=lambda j: sum((a - c) ** 2 for a, c in zip(rgb[j], t)))
    return bytes(out)
DN_TAB = dn_table()
dn_tab = place_data('dn_tab', DN_TAB)
dn_d = place_data('dn_d', bytes(DN_G * DN_G))
dn_old = place_data('dn_old', bytes(DN_G * DN_G))
dn_var = place_data('dn_var', bytes(4 * 20))   # on, gw, gh, gx0, gy0, sx, sy, r0, r, c, k, p, sh, base, str, last, mw, mh, row, lmin
(DN_ON, DN_GW, DN_GH, DN_GX0, DN_GY0, DN_SX, DN_SY, DN_R0, DN_R, DN_C, DN_K, DN_P, DN_SH,
 DN_BASE, DN_STR, DN_LAST, DN_MW, DN_MH, DN_ROW, DN_LMIN) = (dn_var + 4 * i for i in range(20))
DN_AMIN = 4    # nivel mínimo de la luz de los ejércitos: 0,82^4 ~45 % (pedido: no más del 50 %)
# Las 8 vecinas en el orden de 0x45c8f0 (N, NE, E, SE, S, SO, O, NO), como desplazamientos en la grilla.
dn_offs = place_data('dn_offs', struct.pack('<8i', *(dy * DN_G + dx for dx, dy in
                     zip((0, 1, 1, 1, 0, -1, -1, -1), (-1, -1, 0, 1, 1, 1, 0, -1)))))

# dn_stamp: eax = x, edx = y del mapa (grilla en [DN_BASE], [DN_STR] bytes por fila; origen GX0/GY0, tamaño GW x GH), cl = radio, ch = 1 halo redondo / 0 cuadrado, bits 16..23 = nivel mínimo (0: DN_MIN) -> baja el nivel de las casillas de la grilla a su alcance.
dn_stamp = place('dn_stamp', f'''
    pushad
    sub eax, dword ptr [{DN_GX0:#x}]
    sub edx, dword ptr [{DN_GY0:#x}]
    mov dword ptr [{DN_SX:#x}], eax
    mov dword ptr [{DN_SY:#x}], edx
    mov ebx, ecx
    shr ebx, 16
    and ebx, 0xff
    jnz ds_lm
    mov ebx, {DN_MIN}
ds_lm:
    mov dword ptr [{DN_LMIN:#x}], ebx
    movzx ebx, ch
    mov dword ptr [{DN_SH:#x}], ebx
    movzx ecx, cl
    mov dword ptr [{DN_R0:#x}], ecx
    lea ebx, [edx - {DN_N}]
    sub ebx, ecx
    jge ds_y0
    xor ebx, ebx
ds_y0:
    lea ebp, [edx + {DN_N}]
    add ebp, ecx
    cmp ebp, dword ptr [{DN_GH:#x}]
    jl ds_yrow
    mov ebp, dword ptr [{DN_GH:#x}]
    dec ebp
ds_yrow:
    cmp ebx, ebp
    jg ds_out
    mov esi, dword ptr [{DN_SX:#x}]
    sub esi, {DN_N}
    sub esi, dword ptr [{DN_R0:#x}]
    jge ds_x0
    xor esi, esi
ds_x0:
    mov edi, dword ptr [{DN_SX:#x}]
    add edi, {DN_N}
    add edi, dword ptr [{DN_R0:#x}]
    cmp edi, dword ptr [{DN_GW:#x}]
    jl ds_x
    mov edi, dword ptr [{DN_GW:#x}]
    dec edi
ds_x:
    cmp esi, edi
    jg ds_ynext
    mov eax, esi
    sub eax, dword ptr [{DN_SX:#x}]
    cdq
    xor eax, edx
    sub eax, edx
    mov ecx, eax
    mov eax, ebx
    sub eax, dword ptr [{DN_SY:#x}]
    cdq
    xor eax, edx
    sub eax, edx
    test byte ptr [{DN_SH:#x}], 1
    jz ds_oct
    imul eax, eax
    imul ecx, ecx
    add ecx, eax
    xor eax, eax
ds_circ:
    lea edx, [eax + 1]
    imul edx, eax
    cmp ecx, edx
    jbe ds_dist
    inc eax
    jmp ds_circ
ds_oct:
    cmp eax, ecx
    jge ds_mx
    xchg eax, ecx
ds_mx:
    shr ecx, 1
    add eax, ecx
ds_dist:
    sub eax, dword ptr [{DN_R0:#x}]
    jge ds_lev
    xor eax, eax
ds_lev:
    add eax, dword ptr [{DN_LMIN:#x}]
    cmp eax, {DN_N}
    jge ds_xnext
    mov edx, ebx
    imul edx, dword ptr [{DN_STR:#x}]
    add edx, esi
    add edx, dword ptr [{DN_BASE:#x}]
    cmp byte ptr [edx], al
    jbe ds_xnext
    mov byte ptr [edx], al
ds_xnext:
    inc esi
    jmp ds_x
ds_ynext:
    inc ebx
    jmp ds_yrow
ds_out:
    popad
    ret
''')

# dn_lights: estampa en la grilla todas las luces de [GX0 - DN_N - 1, GX0 + GW + DN_N + 1) x (lo mismo en y). Con
# Hidden Map, una ciudad, ruina, sitio o puente solo alumbra desde una casilla explorada por quien mira (bit 0x10 del
# byte +3): su halo no delata lo que está bajo el negro.
dn_lights = place('dn_lights', f'''
    pushad
    mov edi, dword ptr [{DN_GY0:#x}]
    sub edi, {DN_N + 1}
dl_sy:
    mov eax, dword ptr [{DN_GY0:#x}]
    add eax, dword ptr [{DN_GH:#x}]
    add eax, {DN_N + 1}
    cmp edi, eax
    jge dl_arm
    mov esi, dword ptr [{DN_GX0:#x}]
    sub esi, {DN_N + 1}
dl_sx:
    mov eax, dword ptr [{DN_GX0:#x}]
    add eax, dword ptr [{DN_GW:#x}]
    add eax, {DN_N + 1}
    cmp esi, eax
    jge dl_synext
    mov eax, esi
    mov edx, edi
    call {br_tile:#x}
    test eax, eax
    jz dl_sxnext
    test byte ptr [{OPT:#x}], 0x10
    jz dl_seen
    test byte ptr [eax + 3], 0x10
    jz dl_sxnext
dl_seen:
    movzx ecx, byte ptr [eax + 3]
    and ecx, 7
    cmp ecx, 3
    je dl_city
    cmp ecx, 2
    je dl_site
    cmp ecx, 4
    je dl_site
    cmp ecx, 1
    jne dl_sxnext
    call {br_kind:#x}
    cmp eax, 1
    jne dl_sxnext
dl_site:
    mov ecx, 0x100
    jmp dl_put
dl_city:
    mov ecx, 1
dl_put:
    mov eax, esi
    mov edx, edi
    call {dn_stamp:#x}
dl_sxnext:
    inc esi
    jmp dl_sx
dl_synext:
    inc edi
    jmp dl_sy
dl_arm:
    movsx ebx, word ptr [0x560b20]
    cmp ebx, 8
    jae dl_out
    mov esi, 1
dl_aloop:
    movsx eax, word ptr [0x54fe50]
    cmp esi, eax
    jge dl_out
    imul edi, esi, 0x1c
    test byte ptr [edi + 0x54fe63], 0x40
    jz dl_anext
    movzx eax, word ptr [edi + 0x54fe5e]
    shr eax, 5
    and eax, 0xf
    cmp eax, ebx
    jne dl_anext
    movsx eax, word ptr [edi + 0x54fe52]
    movsx edx, word ptr [edi + 0x54fe54]
    mov ecx, {DN_AMIN << 16 | 0x101:#x}
    call {dn_stamp:#x}
dl_anext:
    inc esi
    jmp dl_aloop
dl_out:
    popad
    ret
''')

dn_pre = place('dn_pre', f'''
    pushad
    mov ebp, ecx
    xor ebx, ebx
    test byte ptr [{SHOPT:#x}], 2
    jz dp_fill
    test byte ptr [{DN_TURN:#x}], 1
    jnz dp_fill
    mov bl, {DN_N}
dp_fill:
    mov dword ptr [{DN_ON:#x}], ebx
    cmp ebx, dword ptr [{DN_LAST:#x}]
    je dp_same
    mov dword ptr [{DN_LAST:#x}], ebx
    mov eax, dword ptr [0x57276c]
    test eax, eax
    jz dp_same
    mov dword ptr [eax + 0xc], 1
dp_same:
    mov dword ptr [{DN_BASE:#x}], {dn_d:#x}
    mov dword ptr [{DN_STR:#x}], {DN_G}
    mov edi, {dn_d:#x}
    mov ecx, {DN_G * DN_G}
    mov al, bl
    rep stosb
    movsx eax, word ptr [ebp + 0x20]
    cmp eax, {DN_MAX}
    jle dp_w
    mov eax, {DN_MAX}
dp_w:
    add eax, 2
    mov dword ptr [{DN_GW:#x}], eax
    movsx eax, word ptr [ebp + 0x22]
    cmp eax, {DN_MAX}
    jle dp_h
    mov eax, {DN_MAX}
dp_h:
    add eax, 2
    mov dword ptr [{DN_GH:#x}], eax
    movsx eax, word ptr [ebp + 0x28]
    dec eax
    mov dword ptr [{DN_GX0:#x}], eax
    movsx eax, word ptr [ebp + 0x2a]
    dec eax
    mov dword ptr [{DN_GY0:#x}], eax
    test ebx, ebx
    jz dp_cmp
    call {dn_lights:#x}
dp_cmp:
    xor ebx, ebx
dp_crow:
    mov eax, dword ptr [{DN_GH:#x}]
    sub eax, 2
    cmp ebx, eax
    jge dp_copy
    xor edi, edi
dp_ccol:
    mov eax, dword ptr [{DN_GW:#x}]
    sub eax, 2
    cmp edi, eax
    jge dp_crnext
    imul esi, ebx, {DN_G}
    add esi, edi
    mov eax, dword ptr [esi + {dn_d:#x}]
    xor eax, dword ptr [esi + {dn_old:#x}]
    and eax, 0xffffff
    jnz dp_dirty
    mov eax, dword ptr [esi + {dn_d + DN_G:#x}]
    xor eax, dword ptr [esi + {dn_old + DN_G:#x}]
    and eax, 0xffffff
    jnz dp_dirty
    mov eax, dword ptr [esi + {dn_d + 2 * DN_G:#x}]
    xor eax, dword ptr [esi + {dn_old + 2 * DN_G:#x}]
    and eax, 0xffffff
    jz dp_ccnext
dp_dirty:
    movsx eax, word ptr [ebp + 0x20]
    imul eax, ebx
    add eax, edi
    imul eax, eax, 0x1c
    add eax, dword ptr [ebp + 0x40]
    or byte ptr [eax + 6], 0x20
dp_ccnext:
    inc edi
    jmp dp_ccol
dp_crnext:
    inc ebx
    jmp dp_crow
dp_copy:
    mov esi, {dn_d:#x}
    mov edi, {dn_old:#x}
    mov ecx, {DN_G * DN_G}
    rep movsb
    popad
    sub esp, 0x14
    mov word ptr [esp + 6], 0
    jmp 0x45979a
''')

dn_post = place('dn_post', f'''
    cmp dword ptr [{DN_ON:#x}], 0
    je dq_ret
    pushad
    push 0x48
    mov ecx, 0x58cf78
    call 0x4e4a90
    test eax, eax
    jz dq_out
    cmp dword ptr [eax + 8], 0
    jne dq_sheet
    push 0x48
    call 0x4dd3f0
    add esp, 4
    test eax, eax
    jz dq_out
dq_sheet:
    mov dword ptr [{DN_R:#x}], 0
dq_row:
    mov eax, dword ptr [{DN_GH:#x}]
    sub eax, 2
    cmp dword ptr [{DN_R:#x}], eax
    jge dq_out
    mov dword ptr [{DN_C:#x}], 0
dq_col:
    mov eax, dword ptr [{DN_GW:#x}]
    sub eax, 2
    cmp dword ptr [{DN_C:#x}], eax
    jge dq_rnext
    movsx eax, word ptr [ebp + 0x20]
    imul eax, dword ptr [{DN_R:#x}]
    add eax, dword ptr [{DN_C:#x}]
    imul eax, eax, 0x1c
    add eax, dword ptr [ebp + 0x40]
    cmp byte ptr [ebp + 0x1a5], 0
    jne dq_go
    test byte ptr [eax + 6], 0x20
    jz dq_cnext
dq_go:
    mov cx, word ptr [eax + 8]
    and ch, 0xfe
    cmp ch, 0xe
    je dq_cnext
    mov eax, dword ptr [{DN_R:#x}]
    inc eax
    imul eax, eax, {DN_G}
    add eax, dword ptr [{DN_C:#x}]
    lea esi, [eax + {dn_d + 1:#x}]
    mov dword ptr [{DN_P:#x}], esi
    mov dword ptr [{DN_K:#x}], 1
dq_lev:
    mov esi, dword ptr [{DN_P:#x}]
    movzx eax, byte ptr [esi]
    cmp dword ptr [{DN_K:#x}], eax
    jg dq_cnext
    mov ecx, dword ptr [{DN_K:#x}]
    xor edx, edx
    xor edi, edi
dq_nb:
    mov eax, dword ptr [edi*4 + {dn_offs:#x}]
    movzx eax, byte ptr [esi + eax]
    cmp eax, ecx
    jl dq_nbnext
    bts edx, edi
dq_nbnext:
    inc edi
    cmp edi, 8
    jb dq_nb
    movsx eax, byte ptr [edx + 0x4fbfc8]
    test eax, eax
    jl dq_knext
    push {dn_tab:#x}
    imul ecx, dword ptr [{DN_R:#x}], 0x30
    push ecx
    imul ecx, dword ptr [{DN_C:#x}], 0x30
    push ecx
    push 0x27
    push 0x30
    push 0x30
    mov ecx, eax
    shr ecx, 3
    add ecx, 2
    imul ecx, ecx, 0x31
    push ecx
    and eax, 7
    imul eax, eax, 0x31
    push eax
    push 0x48
    call 0x4ee3c0
    add esp, 0x24
dq_knext:
    inc dword ptr [{DN_K:#x}]
    jmp dq_lev
dq_cnext:
    inc dword ptr [{DN_C:#x}]
    jmp dq_col
dq_rnext:
    inc dword ptr [{DN_R:#x}]
    jmp dq_row
dq_out:
    popad
dq_ret:
    pop ebp
    pop edi
    pop esi
    pop ebx
    add esp, 0x14
    ret
''')

# Minimapa de noche. El del juego ([0x57276c], clase 0x4f5028) se rearma en 0x4114d0: copia la imagen base (hoja
# 0x2d) a la hoja 0x28 y encima dibuja los íconos; después la 0x28 va a pantalla. dn_mini (en 0x4114ef, entre los
# dos pasos, esi = el minimapa) oscurece la 0x28 con los mismos niveles que la vista: arma una grilla del mapa entero
# (dn_m, DN_MG bytes por fila) con dn_lights y recolorea cada tramo de una fila de píxeles con igual nivel en una sola
# llamada a 0x4ede30 (recoloreo de un rectángulo) con la tabla compuesta del nivel (dn_mt: dn_tab aplicada L veces).
# Píxel -> casilla como 0x411370: x * ancho del mapa / ancho del minimapa. dn_pre marca el minimapa para rearmar
# ([+0xc] = 1) cuando cambia entre día y noche.
DN_MG = 256
def dn_mtables():
    out = bytearray()
    t = bytes(range(256))
    for _ in range(DN_N + 1):
        out += t
        t = bytes(DN_TAB[c] for c in t)
    return bytes(out)
dn_mt = place_data('dn_mt', dn_mtables())
dn_m = place_data('dn_m', bytes(DN_MG * DN_MG))

def dn_mlev(lab):   # eax = nivel de la casilla del píxel x = esi en la fila [DN_ROW]; usa edx
    return f'''
    movsx eax, word ptr [0x503e00]
    imul eax, esi
    cdq
    idiv dword ptr [{DN_MW:#x}]
    cmp eax, {DN_MG - 1}
    jbe {lab}
    mov eax, {DN_MG - 1}
{lab}:
    add eax, dword ptr [{DN_ROW:#x}]
    movzx eax, byte ptr [eax]'''

dn_mini = place('dn_mini', f'''
    mov cx, word ptr [esp + 0x2c]
    add esp, 0x20
    pushad
    test byte ptr [{SHOPT:#x}], 2
    jz dm_out
    test byte ptr [{DN_TURN:#x}], 1
    jnz dm_out
    movsx eax, word ptr [esi + 0x20]
    mov dword ptr [{DN_MW:#x}], eax
    movsx eax, word ptr [esi + 0x22]
    mov dword ptr [{DN_MH:#x}], eax
    push dword ptr [{DN_GX0:#x}]
    push dword ptr [{DN_GY0:#x}]
    push dword ptr [{DN_GW:#x}]
    push dword ptr [{DN_GH:#x}]
    push dword ptr [{DN_BASE:#x}]
    push dword ptr [{DN_STR:#x}]
    xor eax, eax
    mov dword ptr [{DN_GX0:#x}], eax
    mov dword ptr [{DN_GY0:#x}], eax
    movsx eax, word ptr [0x503e00]
    cmp eax, {DN_MG}
    jle dm_w
    mov eax, {DN_MG}
dm_w:
    mov dword ptr [{DN_GW:#x}], eax
    movsx eax, word ptr [0x503e02]
    cmp eax, {DN_MG}
    jle dm_h
    mov eax, {DN_MG}
dm_h:
    mov dword ptr [{DN_GH:#x}], eax
    mov dword ptr [{DN_BASE:#x}], {dn_m:#x}
    mov dword ptr [{DN_STR:#x}], {DN_MG}
    mov edi, {dn_m:#x}
    mov ecx, {DN_MG * DN_MG}
    mov al, {DN_N}
    rep stosb
    call {dn_lights:#x}
    pop dword ptr [{DN_STR:#x}]
    pop dword ptr [{DN_BASE:#x}]
    pop dword ptr [{DN_GH:#x}]
    pop dword ptr [{DN_GW:#x}]
    pop dword ptr [{DN_GY0:#x}]
    pop dword ptr [{DN_GX0:#x}]
    cmp dword ptr [{DN_MW:#x}], 0
    jle dm_out
    cmp dword ptr [{DN_MH:#x}], 0
    jle dm_out
    xor edi, edi
dm_row:
    cmp edi, dword ptr [{DN_MH:#x}]
    jge dm_out
    movsx eax, word ptr [0x503e02]
    imul eax, edi
    cdq
    idiv dword ptr [{DN_MH:#x}]
    cmp eax, {DN_MG - 1}
    jbe dm_ty
    mov eax, {DN_MG - 1}
dm_ty:
    imul eax, eax, {DN_MG}
    add eax, {dn_m:#x}
    mov dword ptr [{DN_ROW:#x}], eax
    xor esi, esi
dm_run:
    cmp esi, dword ptr [{DN_MW:#x}]
    jge dm_rnext
    mov ebp, esi{dn_mlev('dm_l1')}
    mov ebx, eax
dm_ext:
    inc esi
    cmp esi, dword ptr [{DN_MW:#x}]
    jge dm_paint{dn_mlev('dm_l2')}
    cmp eax, ebx
    je dm_ext
dm_paint:
    test ebx, ebx
    jz dm_run
    mov eax, ebx
    shl eax, 8
    add eax, {dn_mt:#x}
    push eax
    push 1
    mov eax, esi
    sub eax, ebp
    push eax
    push edi
    push ebp
    push 0x28
    call 0x4ede30
    add esp, 0x18
    jmp dm_run
dm_rnext:
    inc edi
    jmp dm_row
dm_out:
    popad
    jmp 0x4114f7
''')

# ---------------------------------------------------------------- Camuflaje (bono de movimiento "camouflg", de noche)
# De noche (DN_ON, ver dn_pre), el ejército quieto de una casilla se ve en gris apagado si todas las unidades de su
# bando en esa casilla tienen el bono de movimiento "camouflg" (TERRAIN\SUBTYPE\camouflg.STT; el nombre del bono tiene a lo
# sumo 8 letras). Un grupo con un héroe no se camufla, ni uno dentro de una ciudad (iluminada). Se copia el dibujo
# (0x4dd530) y 0x4ee3c0 lo recolorea con los
# mismos argumentos (el dibujo hace de máscara) con cam_tab: cada color pasado a un gris verdoso del tono del pasto
# (24, 28, 15; la paleta va de 0 a 63 por canal), entre el 80 % y el 120 % según su luminancia, al índice más
# parecido de la paleta (los índices impares, entre los verdes oscuros 48..53: la paleta no tiene gris verdoso y la
# mezcla de tonos de la figura lo da): poco contraste, se confunde con el terreno (el gris oscuro del 1.0.81.0 se notaba demasiado;
# el 1.0.80.0 y el 1.0.82.0 salían blancos por tomar la paleta como 0..255). Vale para todo lo que se dibuja
# del ejército: la figura (0x459d0d vía crdraw, y 0x45a14f/0x45a18e de la 3ª pasada), el globito del color del equipo
# (0x45a267), su barra (0x45a2ac) y los iconos de la hoja 0x38 (0x45a2cc, 0x45a34a, 0x45a3a5). El grupo que se está
# moviendo (0x459e15, 0x459eea) no. El Army Report (minimapa 0x414d50) no muestra esos ejércitos a los demás.
CAMO = b'camouflg'
camstr = place_data('camstr', CAMO + b'\0')
def cam_table():
    pal = open(os.path.join(os.path.dirname(SRC_EXE), 'war3.pal'), 'rb').read()
    rgb = [tuple(pal[3 * i:3 * i + 3]) for i in range(256)]
    cand = [10] + [i for i in range(16, 245) if i != 187]
    out = bytearray(range(256))
    for i in range(256):
        if i == 11: continue
        t = tuple(o * (0.8 + 0.4 * sum(w * c for w, c in zip((0.3, 0.59, 0.11), rgb[i])) / 63) for o in (24, 28, 15))
        pool = range(48, 54) if i % 2 else cand   # la mitad de los tonos a verde oscuro: sin gris verdoso en la paleta
        out[i] = min(pool, key=lambda j: sum((a - c) ** 2 for a, c in zip(rgb[j], t)))
    return bytes(out)
CAM_TAB = cam_table()
cam_tab = place_data('cam_tab', CAM_TAB)
cam_hit = place_data('cam_hit', bytes(4))
cam_rec = place('cam_rec', boatbon_src('cam_rec', camstr, rec=True))
# cam_stack: eax = x, edx = y, ecx = bando -> eax = 1 si hay unidades de ese bando en (x, y) y todas tienen "camouflg".
# En una casilla de ciudad, 0: la ciudad está iluminada (pedido del usuario, 26/10/2026).
cam_stack = place('cam_stack', f'''
    push ebx
    push esi
    push edi
    push ebp
    mov ebp, ecx
    xor ebx, ebx
    push eax
    call {br_tile:#x}
    mov esi, eax
    pop eax
    test esi, esi
    jz cs_end
    movzx esi, byte ptr [esi + 3]
    and esi, 7
    cmp esi, 3
    je cs_end
    mov esi, 1
cs_loop:
    movsx ecx, word ptr [0x54fe50]
    cmp esi, ecx
    jge cs_end
    imul edi, esi, 0x1c
    test byte ptr [edi + 0x54fe63], 0x40
    jz cs_next
    cmp word ptr [edi + 0x54fe52], ax
    jne cs_next
    cmp word ptr [edi + 0x54fe54], dx
    jne cs_next
    movzx ecx, word ptr [edi + 0x54fe5e]
    push ecx
    shr ecx, 5
    and ecx, 0xf
    cmp ecx, ebp
    pop ecx
    jne cs_next
    and ecx, 0x1f
    cmp ecx, 16
    jae cs_no
    push eax
    push edx
    mov eax, ebp
    shl eax, 4
    add eax, ecx
    imul eax, eax, 0xfc
    add eax, 0x53c410
    mov edx, {camstr:#x}
    call {cam_rec:#x}
    mov ecx, eax
    pop edx
    pop eax
    test ecx, ecx
    jz cs_no
    inc ebx
cs_next:
    inc esi
    jmp cs_loop
cs_no:
    xor ebx, ebx
cs_end:
    xor eax, eax
    test ebx, ebx
    setnz al
    pop ebp
    pop edi
    pop esi
    pop ebx
    ret
''')
# cam_blit(reg): en lugar de una llamada a 0x4dd530 (cdecl, 8 argumentos) del dibujo de una celda de la vista; reg =
# celda (esi en la 2ª pasada, edi en la 3ª), ebp = vista; columna y fila de la celda en [esp+0x38]/[esp+0x3a] (las del
# llamador 0x459790), origen de la vista en [ebp+0x28]/[ebp+0x2a].
def cam_blit_src(n, reg):
    return f'''
    cmp dword ptr [{DN_ON:#x}], 0
    jne {n}_go
    jmp 0x4dd530
{n}_go:
    pushad
    movsx eax, word ptr [esp + 0x58]
    movsx edx, word ptr [ebp + 0x28]
    add eax, edx
    movsx edx, word ptr [esp + 0x5a]
    movsx ecx, word ptr [ebp + 0x2a]
    add edx, ecx
    movzx ecx, word ptr [{reg} + 4]
    and ecx, 0xf
    call {cam_stack:#x}
    mov dword ptr [{cam_hit:#x}], eax
    popad
    cmp dword ptr [{cam_hit:#x}], 0
    jne {n}_ghost
    jmp 0x4dd530
{n}_ghost:
    push dword ptr [esp + 0x20]
    push dword ptr [esp + 0x20]
    push dword ptr [esp + 0x20]
    push dword ptr [esp + 0x20]
    push dword ptr [esp + 0x20]
    push dword ptr [esp + 0x20]
    push dword ptr [esp + 0x20]
    push dword ptr [esp + 0x20]
    call 0x4dd530
    add esp, 0x20
    push {cam_tab:#x}
    push dword ptr [esp + 0x24]
    push dword ptr [esp + 0x24]
    push dword ptr [esp + 0x24]
    push dword ptr [esp + 0x24]
    push dword ptr [esp + 0x24]
    push dword ptr [esp + 0x24]
    push dword ptr [esp + 0x24]
    push dword ptr [esp + 0x24]
    call 0x4ee3c0
    add esp, 0x24
    ret
'''
cam_blit = place('cam_blit', cam_blit_src('cb', 'esi'))
cam_blit3 = place('cam_blit3', cam_blit_src('cb3', 'edi'))
CAM_SITES = (0x45a14f, 0x45a18e, 0x45a267, 0x45a2ac, 0x45a2cc, 0x45a34a, 0x45a3a5)   # 3ª pasada, con cam_blit3
# Army Report: en 0x414e1a de 0x414d50 (ya pasados invisibilidad y niebla; bx = dueño << 5, dx = x, ax = y), de noche
# no se dibuja el ejército camuflado (cam_stack) salvo para su dueño o un aliado mutuo con vista aliada (fogally) de
# quien mira ([0x560b20]).
cam_rep = place('cam_rep', f'''
    cmp dword ptr [{DN_ON:#x}], 0
    je cr_show
    pushad
    movzx ecx, bx
    shr ecx, 5
    movsx edx, word ptr [0x560b20]
    cmp ecx, edx
    je cr_vis
    call {fogally:#x}
    je cr_vis
    movsx eax, word ptr [esp + 0x14]
    movsx edx, word ptr [esp + 0x1c]
    call {cam_stack:#x}
    test eax, eax
    jz cr_vis
    popad
    jmp 0x414e2b
cr_vis:
    popad
cr_show:
    shr bx, 5
    mov ecx, dword ptr [esp + 0x10]
    jmp 0x414e22
''')
caves['crblit'] = struct.pack('<I', cam_blit) + caves['crblit'][4:]   # conserva el relleno que le sumó place()

# ---------------------------------------------------------------- Efecto noche (monster, demon, undead)
# De noche (opción Day/Night, SHOPT & 2, vuelta par; con o sin Hidden Map), una unidad cuyo tipo tiene la clase
# "monster", "demon" o "undead" (Army Subtypes, uno de los dos nombres de 9 bytes en +0xa0 y +0xa9; sin bono que
# asignar en el editor, pedido del usuario 26/10/2026) suma +2 a una sola cosa, elegida por
# un sorteo por noche: fuerza, hits, su bono de combate (solo si tiene uno; suma cuando el juego lo aplica) o su habilidad
# especial (solo si tiene una con valor que cuente en combate). Un sorteo por noche: r = nm_draw, el mismo para todas
# las unidades; cada una toma su opción r mod n de la lista de lo que tiene (fuerza, hits, bono, habilidad).
# r sale de la vuelta y de los nombres de los 128 tipos de los bandos (+0x90, 10 bytes): igual en todas las PC de la
# partida, al recargarla y en todos los combates de esa noche, y distinto entre partidas con otros bandos.
# Dónde: el armado de cada unidad de la ficha de batalla 0x467240 (lo usan la batalla, 0x469ed0, y el cálculo de
# probabilidades, 0x464a30) toma el registro del tipo en 0x46787d ([esp+0x30], solo unidades que no son héroes);
# nm_unit suma ahí la fuerza (ficha +3) o los hits (+4), o cambia el puntero por una copia del registro con +2 en el
# valor del bono (+0xdf) o de la habilidad (+0xe8): así valen las habilidades por unidad (trample, poison, etc.),
# Banding, "Bridge +N" (bridgeab lee el mismo puntero) y el bono de combate. Las habilidades de grupo (leadership,
# fear, etc.) las lee 0x468440 en 0x46907c: nm_grp cambia ahí ecx por una copia con +2. El registro real no se toca.
nm_monstr = place_data('nm_monstr', b'monster\0')
nm_demstr = place_data('nm_demstr', b'demon\0')
nm_undstr = place_data('nm_undstr', b'undead\0')
nm_nonestr = place_data('nm_nonestr', b'none\0')
# Habilidades con valor que cuentan en combate: por unidad (0x467885..0x467958, Banding 0x4680d5, Bridge) y de grupo
# (tabla 0x469684 de 0x468440). Necromancy 51 no usa el valor; 53 sí.
NM_CODES = {1, 2, 3, 4, 5, 6, 26, 27, 28, 30, 32, 33, BRIDGE_AB, 37, 38, 39, 40, 41, 42, 43, 52, 53, 54}
nm_codes = place_data('nm_codes', bytes(1 if c in NM_CODES else 0 for c in range(64)))
nm_r1 = place_data('nm_r1', bytes(0xfc))
nm_r2 = place_data('nm_r2', bytes(0xfc))
nm_sub = place('nm_sub', boatbon_src('nm_sub', None, rec=True, off=0xa0, slots=2))
nm_cbn = place('nm_cbn', boatbon_src('nm_cbn', None, rec=True, off=0xd6, slots=1))
# nm_draw: eax = sorteo de la noche (FNV-1a de la vuelta y los nombres, con mezcla final). Preserva el resto.
nm_draw = place('nm_draw', f'''
    push ecx
    push edx
    push esi
    movzx eax, word ptr [{DN_TURN:#x}]
    imul eax, eax, -0x61c88647
    xor eax, 0x811c9dc5
    mov esi, {0x53c410 + 0x90:#x}
    mov ecx, 128
nd_rec:
    xor edx, edx
nd_ch:
    xor al, byte ptr [esi + edx]
    imul eax, eax, 0x01000193
    inc edx
    cmp edx, 10
    jb nd_ch
    add esi, 0xfc
    dec ecx
    jnz nd_rec
    mov edx, eax
    shr edx, 15
    xor eax, edx
    imul eax, eax, 0x2c1b3c6d
    mov edx, eax
    shr edx, 12
    xor eax, edx
    pop esi
    pop edx
    pop ecx
    ret
''')
# nm_kind: eax = registro -> eax = 0 nada, 1 fuerza, 2 hits, 3 bono de combate, 4 habilidad. Preserva el resto.
nm_kind = place('nm_kind', f'''
    push ebx
    push ecx
    push edx
    push esi
    push edi
    mov ebx, eax
    xor eax, eax
    test byte ptr [{SHOPT:#x}], 2
    jz nk_out
    test byte ptr [{DN_TURN:#x}], 1
    jnz nk_out
    mov eax, ebx
    mov edx, {nm_monstr:#x}
    call {nm_sub:#x}
    test eax, eax
    jnz nk_race
    mov eax, ebx
    mov edx, {nm_demstr:#x}
    call {nm_sub:#x}
    test eax, eax
    jnz nk_race
    mov eax, ebx
    mov edx, {nm_undstr:#x}
    call {nm_sub:#x}
    test eax, eax
    jz nk_out
nk_race:
    mov edi, 2
    xor esi, esi
    cmp byte ptr [ebx + 0xdf], 0
    je nk_nob
    cmp byte ptr [ebx + 0xd6], 0
    je nk_nob
    mov eax, ebx
    mov edx, {nm_nonestr:#x}
    call {nm_cbn:#x}
    test eax, eax
    jnz nk_nob
    or esi, 1
    inc edi
nk_nob:
    cmp word ptr [ebx + 0xe8], 0
    je nk_noa
    movzx eax, word ptr [ebx + 0xe6]
    cmp eax, 64
    jae nk_noa
    cmp byte ptr [eax + {nm_codes:#x}], 0
    je nk_noa
    or esi, 2
    inc edi
nk_noa:
    call {nm_draw:#x}
    xor edx, edx
    div edi
    lea eax, [edx + 1]
    cmp eax, 3
    jne nk_out
    test esi, 1
    jnz nk_out
    mov eax, 4
nk_out:
    pop edi
    pop esi
    pop edx
    pop ecx
    pop ebx
    ret
''')
# nm_unit: en lugar de "mov [esp+0x30], eax; mov ecx, [esp+0x30]" en 0x46787d (eax = registro, esi = ficha de la unidad).
nm_unit = place('nm_unit', f'''
    push eax
    call {nm_kind:#x}
    mov ecx, eax
    pop eax
    cmp ecx, 1
    jne nu_h
    add byte ptr [esi + 3], 2
    jmp nu_out
nu_h:
    cmp ecx, 2
    jne nu_c
    add byte ptr [esi + 4], 2
    jmp nu_out
nu_c:
    test ecx, ecx
    jz nu_out
    push esi
    push edi
    push ecx
    mov esi, eax
    mov edi, {nm_r1:#x}
    mov ecx, 63
    cld
    rep movsd dword ptr es:[edi], dword ptr [esi]
    pop ecx
    pop edi
    pop esi
    mov eax, {nm_r1:#x}
    cmp ecx, 3
    jne nu_a
    add byte ptr [eax + 0xdf], 2
    jmp nu_out
nu_a:
    add word ptr [eax + 0xe8], 2
nu_out:
    mov dword ptr [esp + 0x30], eax
    mov ecx, eax
    jmp 0x467885
''')
# nm_grp: en lugar de "movsx edx, word ptr [ecx+0xe6]" en 0x46907c (ecx = registro; se vuelve a cargar en cada vuelta).
nm_grp = place('nm_grp', f'''
    push eax
    mov eax, ecx
    call {nm_kind:#x}
    cmp eax, 4
    jne ng_out
    push esi
    push edi
    mov esi, ecx
    mov edi, {nm_r2:#x}
    mov ecx, 63
    cld
    rep movsd dword ptr es:[edi], dword ptr [esi]
    pop edi
    pop esi
    mov ecx, {nm_r2:#x}
    add word ptr [ecx + 0xe8], 2
ng_out:
    pop eax
    movsx edx, word ptr [ecx + 0xe6]
    jmp 0x469083
''')

# ---------------------------------------------------------------- ícono del exe: craneo.ico (64, 32 y 16)
# El original trae RT_GROUP_ICON 148 con dos RT_ICON de 32x32 (ids 5 y 6). .rsrc no tiene lugar libre y lo sigue
# .reloc, así que todo lo nuevo va en .avis: un subdirectorio RT_ICON con los tres tamaños (los offsets de
# directorio son relativos al comienzo de .rsrc y .avis está después, quedan positivos), sus imágenes y el grupo
# nuevo. En .rsrc solo cambian el offset del subdirectorio RT_ICON y la entrada de datos del grupo 148.
RSRC_RVA = 0x1ab000
def rsrc_off(rva):
    return 0x101a00 + rva - RSRC_RVA
assert struct.unpack_from('<II', exe, opt + 96 + 8 * 2) == (RSRC_RVA, 0xee6dc)
def rsrc_entries(dir_off):
    n_named, n_id = struct.unpack_from('<HH', exe, rsrc_off(RSRC_RVA + dir_off) + 12)
    return [(rsrc_off(RSRC_RVA + dir_off) + 16 + 8 * i,) + struct.unpack_from('<II', exe, rsrc_off(RSRC_RVA + dir_off) + 16 + 8 * i)
            for i in range(n_named + n_id)]
def rsrc_find(dir_off, ident):
    hit = [e for e in rsrc_entries(dir_off) if e[1] == ident]
    assert len(hit) == 1, ident
    return hit[0]
ico = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'craneo.ico'), 'rb').read()
assert struct.unpack_from('<HHH', ico) == (0, 1, 3)
ico_imgs = []   # (cabecera de 12 bytes del grupo, imagen)
for i in range(3):
    w, h, cc, r0, planes, bpp, size, off = struct.unpack_from('<BBBBHHII', ico, 6 + 16 * i)
    ico_imgs.append((struct.pack('<BBBBHHI', w, h, cc, r0, planes, bpp, size), ico[off:off + size]))
ICO_IDS = (5, 6, 7)
def place_rsrc(name, data):   # alineado a 4 (directorios y datos de recursos)
    addr = CAVE + sum(len(b) for b in caves.values())
    pad = -addr % 4
    if pad:
        k = list(caves)[-1]; caves[k] = caves[k] + b'\0' * pad
    return place_data(name, data)
img_va = [place_rsrc(f'ico_img{i}', img) for i, (_, img) in enumerate(ico_imgs)]
grp = struct.pack('<HHH', 0, 1, 3) + b''.join(hd + struct.pack('<H', ICO_IDS[i]) for i, (hd, _) in enumerate(ico_imgs))
grp_va = place_rsrc('ico_grp', grp)
# subdirectorio RT_ICON: directorio de ids, tres directorios de idioma, tres entradas de datos (16 bytes c/u)
dir_va = CAVE + sum(len(b) for b in caves.values()) + (-(CAVE + sum(len(b) for b in caves.values())) % 4)
lang_va = [dir_va + 16 + 8 * 3 + 24 * i for i in range(3)]
data_va = [dir_va + 16 + 8 * 3 + 24 * 3 + 16 * i for i in range(3)]
rel = lambda va: va - BASE - RSRC_RVA
d = struct.pack('<IIHHHH', 0, 0, 0, 0, 0, 3)
d += b''.join(struct.pack('<II', ICO_IDS[i], 0x80000000 | rel(lang_va[i])) for i in range(3))
d += b''.join(struct.pack('<IIHHHHII', 0, 0, 0, 0, 0, 1, 1033, rel(data_va[i])) for i in range(3))
d += b''.join(struct.pack('<IIII', img_va[i] - BASE, len(ico_imgs[i][1]), 0, 0) for i in range(3))
assert place_rsrc('ico_dir', d) == dir_va
t_icon = rsrc_find(0, 3)
assert t_icon[2] & 0x80000000 and [e[1] for e in rsrc_entries(t_icon[2] & 0x7fffffff)] == [5, 6]
struct.pack_into('<I', exe, t_icon[0] + 4, 0x80000000 | rel(dir_va))
t_grp = rsrc_find(0, 14)
g148 = rsrc_find(t_grp[2] & 0x7fffffff, 148)
g_lang = rsrc_entries(g148[2] & 0x7fffffff)
assert len(g_lang) == 1 and not g_lang[0][2] & 0x80000000
g_data = rsrc_off(RSRC_RVA + g_lang[0][2])
assert struct.unpack_from('<I', exe, g_data + 4)[0] == 34
struct.pack_into('<II', exe, g_data, grp_va - BASE, len(grp))

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
patch(0x4223ad, asm('call 0x442470', 0x4223ad), asm(f'call {ia_turn:#x}', 0x4223ad))
patch(0x40edf1, asm('call 0x40c990', 0x40edf1), asm(f'call {ai_ord:#x}', 0x40edf1))
assert rel(0x4091e2, 8) == bytes.fromhex('6683b8126c5300ff')
patch(0x4091ea, asm('jne 0x409317', 0x4091ea), asm(f'jne {ch_ai:#x}', 0x4091ea))
patch(0x4ca0b7, bytes.fromhex('ff1544985a00'), asm(f'call {ri_go:#x}', 0x4ca0b7) + b'\x90')   # CopyFileA del ITEM.DAT
patch(0x409181, rel(0x409181, 0x40918b - 0x409181), asm(f'jmp {ch_pfx:#x}', 0x409181))
patch(0x469f54, asm('call 0x465c80', 0x469f54), asm(f'call {ia_bat:#x}', 0x469f54))
patch(0x452c3b, asm('call 0x4aab10', 0x452c3b), asm(f'call {ia_menu:#x}', 0x452c3b))
patch(0x42237a, asm('mov word ptr [0x537ce8], di', 0x42237a), asm(f'jmp {ia_compu:#x}', 0x42237a))
patch(0x4ecf10, asm('call 0x4dea40', 0x4ecf10), asm(f'call {ia_tload:#x}', 0x4ecf10))
# OnIdle (0x4ecef0): sin el foco ([0x501280] = 0, lo pone OnActivate 0x4ed400) el original no llama al tick 0x4dea40,
# y con él se frenaban la red (0x4df3e0) y tl_idle: con la Votación o el Sorteo al frente, el anfitrión no levantaba
# el .op ni mandaba el estado, y el espectador no escribía el .ver (prueba real 30/10/2026). Ahora el tick corre
# siempre; el dibujo (0x4de480) y los timers siguen pausados sin foco, como en el original.
patch(0x4ecf01, asm('jne 0x4ecf0b', 0x4ecf01), asm('jmp 0x4ecf0b', 0x4ecf01))
patch(0x4ed415, asm('test esi, esi; jne 0x4ed477; cmp byte ptr [0x501280], 0', 0x4ed415), asm(f'jmp {ia_bg:#x}', 0x4ed415))
patch(0x4476d9, asm('call 0x49fec0', 0x4476d9), asm(f'call {ia_nodip:#x}', 0x4476d9))
# Espacio libre (0x4e0770): sectores por clúster × bytes por sector × clústeres libres en 32 bits; con discos de
# decenas de GB el producto se desborda y, según lo libre que haya, el juego avisa "You are low on disk space" al
# arrancar y espera un clic (una tanda quedaba ahí, sin ventana del juego). Si GetDiskFreeSpaceA respondió, informa
# 2 GB, lo máximo que entra.
patch(0x4e0799, rel(0x4e0799, 14), asm('mov esi, 0x7fffffff', 0x4e0799) + bytes([0x90]) * 9)
patch(0x482fd6, asm('mov si, word ptr [ebp + 0xc]; push 1', 0x482fd6), asm(f'jmp {ia_fin:#x}', 0x482fd6))
patch(0x482790, asm('call 0x482c10', 0x482790), asm(f'call {ia_vic:#x}', 0x482790))
patch(0x441cf0, bytes.fromhex('83ec0833c9'), asm(f'jmp {vcopy:#x}', 0x441cf0))
patch(0x459790, asm('sub esp, 0x14; mov word ptr [esp + 6], 0', 0x459790), asm(f'jmp {dn_pre:#x}', 0x459790) + bytes([0x90]) * 5)
patch(0x45aa6e, asm('pop ebp; pop edi; pop esi; pop ebx; add esp, 0x14; ret', 0x45aa6e), asm(f'jmp {dn_post:#x}', 0x45aa6e) + bytes([0xcc]) * 3)
patch(0x4114ef, asm('mov cx, word ptr [esp + 0x2c]; add esp, 0x20', 0x4114ef), asm(f'jmp {dn_mini:#x}', 0x4114ef) + bytes([0x90]) * 3)
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
patch(0x4a5d34, bytes.fromhex('0fbfd78d0492c1e0050fbfcb'), asm(f'jmp {po_pf:#x}', 0x4a5d34) + bytes.fromhex('90') * 7)
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
patch(0x46787d, asm('mov dword ptr [esp + 0x30], eax; mov ecx, dword ptr [esp + 0x30]', 0x46787d),
      asm(f'jmp {nm_unit:#x}', 0x46787d))
patch(0x46907c, asm('movsx edx, word ptr [ecx + 0xe6]', 0x46907c), asm(f'jmp {nm_grp:#x}', 0x46907c))
for va in CAM_SITES:
    patch(va, asm('call 0x4dd530', va), asm(f'call {cam_blit3:#x}', va))
patch(0x414e1a, asm('shr bx, 5; mov ecx, dword ptr [esp + 0x10]', 0x414e1a), asm(f'jmp {cam_rep:#x}', 0x414e1a) + bytes([0x90]) * 3)
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
patch(0x467d0e, asm('cmp byte ptr [esp + 0x11], 0; je 0x467d1f; mov ax, word ptr [esp + 0x12]; mov word ptr [esp + 0x16], ax', 0x467d0e),
      asm(f'jmp {bridgeab:#x}', 0x467d0e).ljust(17, b'\x90'))
# Misión "derribar un puente" (qb_*)
patch(0x460dfb, bytes.fromhex('6685ff0f8e9c010000'), asm(f'jmp {qb_gen:#x}', 0x460dfb))
patch(0x461336, bytes.fromhex('516a42b980985800e8eddb0700'), asm(f'jmp {qb_name:#x}', 0x461336))
patch(0x461876, bytes.fromhex('0fbf47068d048003c08d0c408d0489'), asm(f'jmp {qb_text:#x}', 0x461876))
patch(0x461c80, bytes.fromhex('0fbf46068d048003c08d144080bc924bad550000740d'), asm(f'jmp {qb_fail:#x}', 0x461c80))
patch(0x41424a, rel(0x41424a, 0x41426a - 0x41424a), asm(f'jmp {qb_line:#x}', 0x41424a))
# Misión «escoltar al equipo que desarma una trampa» (qt_*)
patch(0x45f4f6, bytes.fromhex('6aff6a066a01e81ff607000fbfc083c40c83f8050f875f080000ff24851c104600'),
      asm(f'jmp {qt_hard:#x}', 0x45f4f6))
patch(0x461163, bytes.fromhex('4883f80b0f875b020000'), asm(f'jmp {qt_name:#x}', 0x461163))
patch(0x461432, bytes.fromhex('0fbf47044883f80b0f87e0050000'), asm(f'jmp {qt_text:#x}', 0x461432))
patch(0x461d0c, bytes.fromhex('6683f90b754b'), asm(f'jmp {qt_fail:#x}', 0x461d0c))
patch(0x461fee, bytes.fromhex('668b4604663d0100756a'), asm(f'jmp {qt_arrive:#x}', 0x461fee))
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
patch(0x4b6a22, asm('ja 0x4b85bb', 0x4b6a22), asm(f'ja {tr_recv:#x}', 0x4b6a22))
# Construir trampas (tr_*)
patch(0x4affc2, asm('mov ecx, 0x588bd0', 0x4affc2), asm(f'jmp {tr_init:#x}', 0x4affc2))
patch(0x4b0450, asm('mov ecx, 0x588bd0', 0x4b0450), asm(f'jmp {tr_hover:#x}', 0x4b0450))
patch(0x4b0487, asm('sub eax, 0xb; cmp eax, 0xb; ja 0x4b0496', 0x4b0487),
      asm(f'jmp {tr_click:#x}', 0x4b0487))
patch(0x4b6236, asm('call 0x4b9ce0', 0x4b6236), asm(f'call {tr_send:#x}', 0x4b6236))
assert rel(0x4b85bb, 9) == bytes.fromhex('5f5e81c408010000c3')
patch(0x4dea40, asm('mov ecx, 0x5a6f50', 0x4dea40), asm(f'jmp {tl_idle:#x}', 0x4dea40))
assert rel(0x4dd3a0, 7) == bytes.fromhex('66a1fc995800c3')
# Botón del Comparador en Edit Side (dc_*)
patch(0x44dd53, asm('mov ecx, 0x588bd0; call 0x4d7f60', 0x44dd53), asm(f'jmp {dc_init:#x}', 0x44dd53))
assert rel(0x44dd5d, 2) == bytes.fromhex('5ec3')
assert rel(0x44d3e7, 9) == bytes.fromhex('8b56048d42fe83f847')
patch(0x44d3f0, asm('ja 0x44db1c', 0x44d3f0), asm(f'ja {dc_click:#x}', 0x44d3f0))
assert rel(0x44db1c, 3) == bytes.fromhex('6633c0')
assert rel(0x44d357, 7) == bytes.fromhex('6a51') + asm('call 0x4d7980', 0x44d359)
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
patch(0x4a1961, rel(0x4a1961, 0x4a1971 - 0x4a1961), asm(f'jmp {po_gen:#x}', 0x4a1961))
patch(0x42ddc1, asm('call 0x4a1e20', 0x42ddc1), asm(f'call {po_start:#x}', 0x42ddc1))
patch(0x4aa299, asm('call 0x4baf20', 0x4aa299), asm(f'call {po_nsend:#x}', 0x4aa299))
patch(0x4aa361, asm('movsx eax, cx; inc eax; cmp eax, 9; ja 0x4aa3e7', 0x4aa361), asm(f'jmp {po_nrecv:#x}', 0x4aa361))
patch(0x4aa421, asm('mov dword ptr [0x4ff03c], edx', 0x4aa421), asm(f'jmp {po_nrecvd:#x}', 0x4aa421))
patch(0x4aa6bf, asm('xor dword ptr [esp + 0x10], ebp; mov eax, dword ptr [esp + 0x10]', 0x4aa6bf),
      asm(f'jmp {po_nsum:#x}', 0x4aa6bf))
patch(0x49ce08, asm('call 0x4a1ce0', 0x49ce08), asm(f'call {po_step:#x}', 0x49ce08))
patch(0x4b6e9d, asm('call 0x49d1a0', 0x4b6e9d), asm(f'call {po_fall:#x}', 0x4b6e9d))
patch(0x459b95, bytes.fromhex('807e1000741e'), asm(f'jmp {po_draw:#x}', 0x459b95))
patch(0x473d32, asm('test bp, bp; jl 0x473d76', 0x473d32), asm(f'jmp {po_curclr:#x}', 0x473d32))
patch(0x473dc8, asm('mov ax, word ptr [esp + 0x38]', 0x473dc8), asm(f'jmp {po_cur:#x}', 0x473dc8))
patch(0x4741d9, asm('call 0x4a2170', 0x4741d9), asm(f'jmp {po_info:#x}', 0x4741d9))
for _a in (0x4c2880, 0x4c28d0):
    patch(_a, asm('call 0x4dd1c0', _a), asm(f'call {pz_scroll:#x}', _a))
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
setstr(chk2, 0x2c, 64, 'Allies co-own cities (with Hidden Map: both explored)')
setstr(chk2, 0x9c, 16, 'Shared Cities')
# Día/noche: en la columna de la derecha, debajo de Hidden Map; esa columna pasa a 5 filas de 15 píxeles (102 a 162).
chk3 = bytearray(chk)
struct.pack_into('<I', chk3, 4, DNCHK)
struct.pack_into('<I', chk3, 0x14, 70)
setstr(chk3, 0x1c, 16, 'Day/Night')
setstr(chk3, 0x2c, 64, 'Every other turn is night')
setstr(chk3, 0x9c, 16, 'Day/Night')
for k, rec in enumerate([3, 6, chk3, 7, chk]):
    y = 102 + 15 * k
    if isinstance(rec, int): struct.pack_into('<I', res, r9[rec][0] + 0xc, y)
    else: struct.pack_into('<I', rec, 0xc, y)
new_list[9] = [chk, chk2, chk3]

# Diálogo 115 (reporte View Game Options): fila nueva "Shared Allied View" debajo de Fog of War.
# Las dos columnas pasan de 25 a 19 píxeles entre filas para que entren 9 (130 a 282; Timed Vectoring está en 301).
r115 = records(res, 115)
col1 = [(9, 23), (10, 24), (11, 25), (12, 26), (13, 27), ('dn', 'dn'), (14, 28), ('new', 'new'), (15, 29)]
col2 = [(16, 30), (17, 31), (18, 32), (19, 33), (20, 34), (21, 35), (22, 36)]
NEWLBL = 48
p, t = r115[14]; assert t == 0x12
lbl = bytearray(res[p:p + 4 + SZ[0x12]])
struct.pack_into('<I', lbl, 4, NEWLBL)
setstr(lbl, 0x2c, 64, 'Shared Allied View')
p, t = r115[28]; assert t == 0x11
ind = bytearray(res[p:p + 4 + SZ[0x11]])
struct.pack_into('<I', ind, 4, NEWIND)
# Fila "Day/Night" debajo de Hidden Map, clonada de la nueva.
DNLBL = 52
lbl3 = bytearray(lbl); struct.pack_into('<I', lbl3, 4, DNLBL); setstr(lbl3, 0x2c, 64, 'Day/Night')
ind3 = bytearray(ind); struct.pack_into('<I', ind3, 4, DNIND)
for col in (col1, col2):
    for k, (li, ii) in enumerate(col):
        y = 130 + 19 * k
        if li in ('new', 'dn'):
            l_, i_ = (lbl, ind) if li == 'new' else (lbl3, ind3)
            struct.pack_into('<I', l_, 0xc, y); struct.pack_into('<I', i_, 0xc, y - 2)
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
y = 130 + 19 * len(col2)
struct.pack_into('<I', lbl2, 0xc, y); struct.pack_into('<I', ind2, 0xc, y - 2)
new_list[115] = [lbl, ind, lbl2, ind2, lbl3, ind3]

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

# Diálogo 34 (menú de órdenes del grupo, 0x1f en el código): renglón nuevo TR_TXT / TR_HOT (construir trampa) al final.
# Los 12 renglones pasan a 16 píxeles entre sí desde el primero (53); cada zona de clic, 2 píxeles por encima de su
# texto y de 16 de alto, conserva su x y su ancho.
r34 = records(res, 34)
ORD = [(0x15, 0x16)] + [(k, k + 10) for k in range(1, 11)] + [('new', 'new')]
assert sorted(i for pair in ORD if pair[0] != 'new' for i in pair) == sorted(r34)
p, t = r34[10]; assert t == 0x13
ttxt = bytearray(res[p:p + 4 + SZ[0x13]])
struct.pack_into('<I', ttxt, 4, TR_TXT)
p, t = r34[20]; assert t == 3
thot = bytearray(res[p:p + 4 + SZ[3]])
struct.pack_into('<I', thot, 4, TR_HOT)
for k, (ti, hi) in enumerate(ORD):
    y = 53 + 16 * k
    buf, o = (ttxt, 0) if ti == 'new' else (res, r34[ti][0])
    struct.pack_into('<I', buf, o + 0xc, y)
    buf, o = (thot, 0) if hi == 'new' else (res, r34[hi][0])
    struct.pack_into('<I', buf, o + 0xc, y - 2)
    struct.pack_into('<I', buf, o + 0x1c, 16)
new_list[34] = [ttxt, thot]

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

# Diálogo 86 (Edit Side): botón DC_BTN, otra copia de Chat del diálogo 7, en DC_X/Y y de DC_W x DC_H; su dibujo es el
# ícono de DarkCompare, en (0,0) de la hoja DC_FILE (más abajo).
r86 = records(res, 86)
assert sorted(r86) == list(range(1, DC_BTN))
p, t = r7[80]
dcb = bytearray(res[p:p + 4 + SZ[1]])
struct.pack_into('<IIII', dcb, 4, DC_BTN, DC_X, DC_Y, 1)
struct.pack_into('<5I', dcb, 0x18, DC_FILE, 0, 0, DC_W, DC_H)
setstr(dcb, 0x30, 16, 'Compare')
setstr(dcb, 0x40, 64, 'Compare army units (DarkCompare)')
new_list[86] = [dcb]

for did in (115, 86, 35, 34, 9, 7):   # de atrás para adelante: agregar a uno no corre el offset de los anteriores
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
import io
def hoja_boton(archivo, W, H):
    icono = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), archivo)).convert('RGBA')
    assert icono.size == (W - 2, H - 2)
    hoja = Image.new('P', (W, 4 * H), 11)
    hoja.putpalette(butt.getpalette())
    for fila, (dx, oscuro, aro) in enumerate(((1, False, False), (2, False, True), (1, True, False), (1, False, True))):
        y0 = fila * H
        lleno = set()
        for y in range(icono.height):
            for x in range(icono.width):
                r, g, b_, a_ = icono.getpixel((x, y))
                if a_ < 128 or not (0 <= x + dx < W and 0 <= y + dx < H): continue
                if oscuro: r, g, b_ = r * 3 // 10, g * 3 // 10, b_ * 3 // 10
                hoja.putpixel((x + dx, y0 + y + dx), cercano((r, g, b_))); lleno.add((x + dx, y + dx))
        if aro:
            for x, y in {(x + i, y + j) for x, y in lleno for i in (-1, 0, 1) for j in (-1, 0, 1)} - lleno:
                if 0 <= x < W and 0 <= y < H: hoja.putpixel((x, y0 + y), 71)
    pcx = io.BytesIO(); hoja.save(pcx, 'PCX')
    return pcx.getvalue()
SORTEO_PCX = hoja_boton('sorteo_icono.png', SORTEO_W, SORTEO_H)
o2, _ = table(res, 2)
butt_std = bytearray(res[o2 + 20 + 0x79 * 60:o2 + 20 + 0x7a * 60])
assert butt_std[4:13] == b'butt_std\0' and struct.unpack_from('<6I', butt_std, 36) == (16, 1, 0, 0, 0, 0)
struct.pack_into('<I', butt_std, 0, SORTEO_FILE)
setstr(butt_std, 4, 32, 'sorteo')
table_add(res, 2, SORTEO_FILE, bytes(butt_std))

# Hoja DC_FILE = SETS\Fantasy\darkcomp.pcx: el botón del Comparador en Edit Side, igual que el de Sorteo, con el ícono
# de DarkCompare (comparador_icono.png: el de 256x256 de su assets\strella.ico, reducido a 62x62). Edit Side (fondo
# DLG_BIG.PCX) tiene la misma paleta que BUTT_STD.
assert Image.open(r'C:\Warlords3\SETS\Fantasy\DLG_BIG.PCX').getpalette()[:768] == pal
DC_PCX = hoja_boton('comparador_icono.png', DC_W, DC_H)
struct.pack_into('<I', butt_std, 0, DC_FILE)
setstr(butt_std, 4, 32, 'darkcomp')
table_add(res, 2, DC_FILE, bytes(butt_std))

# Hoja PO_FILE = RUINS\pozos.pcx, con los campos de henge (0x51, el PCX de un tipo de ruina; el 10 es la carpeta
# RUINS): los cuadros de 48x48 de po_draw, uno al lado del otro, en la paleta de las ruinas (la del mapa; el 11 es
# transparente). Dibujos del usuario en picts\ del repo (20/10/2026): pozo = cuadro del medio de pozo.PCX (hoja con
# el formato de una ruina, fondo magenta y grilla violeta, con matices), tumba = primer cuadro de tumba.PCX, lápida = lapida.pcx; cruz = cruz.pcx
# recortada de su pasto (los dos palos y la sombra oscura que cae abajo a la derecha). Trampa detonada: un agujero
# irregular propio (radio con ruido fijo, achatado) con el humo del pozo humeante de TERRAIN\DATA\cit_anim.PCX
# (columna 4, sus 4 cuadros): lo que difiere de la columna 5 (el mismo pozo con lava) y es gris claro, llevado al
# centro del agujero. Sigue de prueba (recortada de las ruinas): trampa = puerta trampa. Remolino: más abajo.
assert PO_FILE == DC_FILE + 1
henge = bytearray(res[o2 + 20 + 0x51 * 60:o2 + 20 + 0x52 * 60])
assert henge[4:10] == b'henge\0' and struct.unpack_from('<6I', henge, 36) == (10, 1, 0, 0, 0, 2)
struct.pack_into('<I', henge, 0, PO_FILE)
setstr(henge, 4, 32, 'pozos')
table_add(res, 2, PO_FILE, bytes(henge))
# Hoja PZ_FILE = RUINS\aviso.pcx (pz_scroll), con los mismos campos: el papiro DLG_HELP (250x150, la misma paleta del
# mapa, 11 transparente) llevado a PZ_W x PZ_H. Los rollos de los costados (45 de ancho) se achican parejo; el centro
# se estira.
assert PZ_FILE == PO_FILE + 1
struct.pack_into('<I', henge, 0, PZ_FILE)
setstr(henge, 4, 32, 'aviso')
table_add(res, 2, PZ_FILE, bytes(henge))
_help = Image.open(r'C:\Warlords3\SETS\Fantasy\DLG_HELP.PCX')
assert _help.size == (250, 150) and _help.getpixel((0, 0)) == 11
assert _help.getpalette()[:768] == Image.open(r'C:\Warlords3\RUINS\henge.PCX').getpalette()[:768]
assert _help.getpalette()[3 * PZ_INK:3 * PZ_INK + 3] == [47, 27, 7] and _help.getpalette()[3 * PZ_SHADOW:3 * PZ_SHADOW + 3] == [239, 231, 171]
_e = round(45 * PZ_H / 150)
pz_hoja = Image.new('P', (PZ_W, PZ_H), 11); pz_hoja.putpalette(_help.getpalette())
pz_hoja.paste(_help.crop((0, 0, 45, 150)).resize((_e, PZ_H), Image.NEAREST), (0, 0))
pz_hoja.paste(_help.crop((45, 0, 205, 150)).resize((PZ_W - 2 * _e, PZ_H), Image.NEAREST), (_e, 0))
pz_hoja.paste(_help.crop((205, 0, 250, 150)).resize((_e, PZ_H), Image.NEAREST), (PZ_W - _e, 0))
pcx = io.BytesIO(); pz_hoja.save(pcx, 'PCX'); PZ_PCX = pcx.getvalue()
# Sonido PO_SND = FX\Burst.wav (sonidos\Burst.wav del repo, el que sumó el usuario), con los campos de Dispel (55; el 14 en +36
# es la carpeta FX). La tabla de sonidos (tipo 3, registros de 52) la carga entera 0x4ec490 al arrancar: cada registro
# es un buffer de la lista 0x5a6f50, buscado por el id (+0).
o3, h3 = table(res, 3)
assert h3[2] == PO_SND
dispel = bytearray(res[o3 + 20 + 55 * 52:o3 + 20 + 56 * 52])
assert struct.unpack_from('<I', dispel, 0)[0] == 55 and dispel[4:11] == b'Dispel\0' and struct.unpack_from('<I', dispel, 36)[0] == 14
struct.pack_into('<I', dispel, 0, PO_SND)
setstr(dispel, 4, 16, 'Burst')
table_add(res, 3, PO_SND, bytes(dispel))
BURST = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'sonidos', 'Burst.wav'), 'rb').read()
PICTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'picts')
po_pal = Image.open(r'C:\Warlords3\RUINS\cave.PCX').getpalette()[:768]
cit = Image.open(r'C:\Warlords3\TERRAIN\DATA\cit_anim.PCX')
assert cit.size == (384, 192) and cit.getpalette()[:768] == po_pal
po_usar = sorted(set(cit.tobytes()) | set(Image.open(r'C:\Warlords3\RUINS\cave.PCX').tobytes()) - {11, 101})
_po_memo = {}
def po_color(rgb):
    if rgb not in _po_memo:
        _po_memo[rgb] = min(po_usar, key=lambda i: sum((po_pal[3 * i + k] - rgb[k]) ** 2 for k in range(3)))
    return _po_memo[rgb]
def po_cuadro(im, pts):   # los puntos pts (x, y) de im (RGB), centrados en un cuadro de 48x48 y en la paleta
    px = im.load()
    cx = (min(p[0] for p in pts) + max(p[0] for p in pts) + 1) // 2
    cy = (min(p[1] for p in pts) + max(p[1] for p in pts) + 1) // 2
    assert max(p[0] for p in pts) - min(p[0] for p in pts) < 48 and max(p[1] for p in pts) - min(p[1] for p in pts) < 48
    out = Image.new('P', (48, 48), 11); out.putpalette(po_pal)
    for x, y in pts: out.putpixel((x - cx + 24, y - cy + 24), po_color(px[x, y][:3]))
    return out
def po_dibujo(nombre, caja=None, fondo=(11, 101)):   # fondo: índices transparentes (P) o, en RGB, fondo(color) -> bool
    im = Image.open(os.path.join(PICTS, nombre))
    if caja: im = im.crop(caja)
    if im.mode == 'P': pts = [(x, y) for x in range(im.width) for y in range(im.height) if im.getpixel((x, y)) not in fondo]
    else: pts = [(x, y) for x in range(im.width) for y in range(im.height) if not fondo(im.convert('RGB').getpixel((x, y)))]
    return po_cuadro(im.convert('RGB'), pts)
def cuadro_ruina(tipo, columna):
    im = Image.open(rf'C:\Warlords3\RUINS\{tipo}.PCX')
    x0 = 1 + columna * 0x57
    c = im.crop((x0, 1, x0 + 87, 89))
    return po_cuadro(c.convert('RGB'), [(x, y) for x in range(87) for y in range(88) if c.getpixel((x, y)) not in (11, 101)])
pozo = po_dibujo('pozo.PCX', (0x58, 1, 0x58 + 87, 89), fondo=lambda c: c[0] > 130 and c[1] < 40 and c[2] > 190)   # magenta y violeta
tumba = po_dibujo('tumba.PCX', (1, 1, 88, 89))
# Lápida (pedido del usuario, 22/10/2026; lapida.pcx era la tumba repetida): la cruz de cruz.pcx (18x22, sin
# montículo) con su sombra hacia abajo a la derecha, y tres ramos de flores acostados contra el pie.
_lc = Image.open(os.path.join(PICTS, 'cruz.pcx')).convert('RGB')
_lm = {(x, y) for x in range(21) for y in range(21) if 8 <= x <= 11 and 4 <= y <= 15 or 5 <= x <= 14 and 7 <= y <= 9}
_lp = Image.new('RGB', (48, 48)); _lpp = []
def _lput(q, c):
    if not (0 <= q[0] < 48 and 0 <= q[1] < 48): return
    _lp.putpixel(q, c)
    if q not in _lpp: _lpp.append(q)
_SOMB, _TALLO = (40, 30, 10), (40, 110, 30)
_lx, _ly = 15, 34   # pie de la cruz
_lcz = [(_lx - 9 + X, _ly - 21 + Y, _lc.getpixel((5 + X * 5 // 9, 4 + Y * 12 // 22))) for X in range(18) for Y in range(22)
        if (5 + X * 5 // 9, 4 + Y * 12 // 22) in _lm]
for x, y, _ in _lcz:   # sombra de la cruz al sureste, como la de la tumba, más clara que la de los ramos
    for d in (0, 1): _lput((x + int((_ly - y) * 0.45) + 2 + d, _ly + 1 + int((_ly - y) * 0.45)), (85, 75, 40))
for sx, sy, fl in [(13, 36, (200, 30, 30)), (18, 38, (235, 235, 235)), (9, 37, (230, 200, 40))]:
    for k in range(9):
        _lput((sx - k, sy + k // 2 + 1), _SOMB)
        _lput((sx - k, sy + k // 2), _TALLO)
    for fx in range(-2, 3):
        for fy in range(-2, 2):
            if abs(fx) + abs(fy) < 4: _lput((sx + 2 + fx, sy - 1 + fy), fl)
    for fx in range(-1, 5): _lput((sx + 2 + fx, sy + 2), _SOMB)
    cen = (250, 230, 90) if fl[1] < 200 else (200, 110, 20)
    _lput((sx + 2, sy - 2), cen); _lput((sx + 3, sy), cen)
for x, y, c in _lcz: _lput((x, y), c)
lapida = po_cuadro(_lp, _lpp)
cruz_im = Image.open(os.path.join(PICTS, 'cruz.pcx'))
assert cruz_im.size == (21, 21)
# Cruz (pedido del usuario, 22/10/2026: con el formato de la tumba): el montículo de la tumba sin su lápida (lo gris
# arriba a la derecha) y en su lugar los dos palos de cruz.pcx al doble, apoyados en el montículo.
_tc = Image.open(os.path.join(PICTS, 'tumba.PCX')).crop((1, 1, 88, 89)); _tr = _tc.convert('RGB')
_cr = cruz_im.convert('RGB')
_cz = Image.new('RGB', (87, 88)); _czp = []
for x in range(87):
    for y in range(88):
        p = _tr.getpixel((x, y))
        if _tc.getpixel((x, y)) in (11, 101) or x >= 38 and (y <= 41 or y <= 47 and max(p) - min(p) < 40): continue
        _cz.putpixel((x, y), p); _czp.append((x, y))
for x, y in [(x, y) for x in range(21) for y in range(21) if 8 <= x <= 11 and 4 <= y <= 15 or 5 <= x <= 14 and 7 <= y <= 9]:
    for a in range(2):
        for b in range(2):
            q = (44 + (x - 10) * 2 + a, 49 + (y - 15) * 2 + b)
            _cz.putpixel(q, _cr.getpixel((x, y)))
            if q not in _czp: _czp.append(q)
cruz = po_cuadro(_cz, _czp)
import math, random
_lum = lambda i: sum(po_pal[3 * i:3 * i + 3]) / 3
_gris = lambda i: max(po_pal[3 * i:3 * i + 3]) - min(po_pal[3 * i:3 * i + 3]) < 30
_ref = cit.crop((240, 0, 288, 48))
_osc = [(x, y) for y in range(48) for x in range(48) if _lum(cit.getpixel((192 + x, y))) < 40]
HX, HY = sum(p[0] for p in _osc) / len(_osc), sum(p[1] for p in _osc) / len(_osc)
_rnd = random.Random(7)
_amp = [_rnd.uniform(-0.22, 0.22) for _ in range(9)]; _fas = [_rnd.uniform(0, 6.28) for _ in range(9)]
RX, RY, CX, CY = 15, 10, 24, 28
agujero = Image.new('P', (48, 48), 11); agujero.putpalette(po_pal)
for y in range(48):
    for x in range(48):
        dx, dy = (x - CX) / RX, (y - CY) / RY
        d, r = math.hypot(dx, dy), 1 + sum(_amp[k] * math.sin((k + 2) * math.atan2(dy, dx) + _fas[k]) / (k + 1) ** 0.5 for k in range(9))
        if d < r * 0.78:     # fondo, más oscuro hacia el centro y abajo
            v = 12 + 34 * (d / r) ** 2 - 8 * dy
            agujero.putpixel((x, y), po_color((v, v * 0.9, v * 0.8)))
        elif d < r:          # borde de tierra removida
            v = _rnd.uniform(0.7, 1.15) * (1 if dy < 0 else 0.7)
            agujero.putpixel((x, y), po_color((120 * v, 85 * v, 45 * v)))
        elif d < r * 1.35 and _rnd.random() < 0.18 * (1.35 - d / r) / 0.35:   # cascotes
            v = _rnd.uniform(0.5, 1.0)
            agujero.putpixel((x, y), po_color((110 * v, 80 * v, 45 * v)))
detonada = []
for fr in range(4):
    c, f = cit.crop((192, fr * 48, 240, fr * 48 + 48)), agujero.copy()
    for y in range(48):
        for x in range(48):
            i = c.getpixel((x, y))
            nx, ny = round(x - HX + CX), round(y - HY + CY - 2)
            if i != _ref.getpixel((x, y)) and _lum(i) > 75 and _gris(i) and 0 <= nx < 48 and 0 <= ny < CY + 3:
                f.putpixel((nx, ny), i)
    detonada.append(f)
# Remolino (aprobado por el usuario, 22/10/2026, «un poco más grande», simétrico): 3x3 casillas, unas dos de ancho;
# solo mata la del medio. Espiral de dos brazos de espuma sobre un embudo que oscurece hacia el centro, girada 45° por
# fase (con dos brazos, 4 fases dan media vuelta y el ciclo empalma), en los azules del agua del mapa. Fondo
# transparente: alrededor se ve el agua (con su animación); el borde se deshilacha con un ruido fijo, igual en las 4
# fases. Cada fase se corta en 9 piezas de 48x48 (cuadros PO_REMO0 + fase * 9 + pieza, ver po_draw); los cuadros 1..4
# (el remolino chico de antes) quedan con la pieza del medio.
RE_AZUL = sorted([32, 33, 34, 35, 36, 37, 38, 42, 43, 46] + list(range(148, 160)), key=lambda i: sum(po_pal[3 * i:3 * i + 3]))
_rr = random.Random(11)
_ruido = [[_rr.random() for x in range(144)] for y in range(144)]
def remolino(fase):
    im = Image.new('P', (144, 144), 11); im.putpalette(po_pal)
    for y in range(144):
        for x in range(144):
            dx, dy = (x - 71.5) / 46, (y - 71.5) / 37
            r = math.hypot(dx, dy)
            if r >= 1 or r > 0.7 and _ruido[y][x] < (r - 0.7) / 0.3: continue
            a = math.atan2(dy, dx) + fase + 5.5 * math.log(r + 0.08)
            brazo = (math.cos(2 * a) + 1) / 2            # 1 en la cresta de espuma, 0 en el valle
            l = (0.15 + 0.85 * r ** 0.6) * (0.55 + 0.6 * brazo ** 3) + 0.08 * (_ruido[x][y] - 0.5)
            im.putpixel((x, y), RE_AZUL[max(0, min(len(RE_AZUL) - 1, int(l * len(RE_AZUL))))])
    return im
remolinos = [remolino(-k * math.pi / 4) for k in range(4)]
remo_piezas = [r.crop((48 * (k % 3), 48 * (k // 3), 48 * (k % 3) + 48, 48 * (k // 3) + 48)) for r in remolinos for k in range(9)]
# Trampa = mina (pedido del usuario, 22/10/2026): una bola de hierro chica con 8 puntas, iluminada desde arriba a la
# izquierda, con un brillo, sin sombra. Reemplaza a la puerta trampa de prueba (cuadro 5). La submarina
# (PO_MINAGUA) es la misma, en los azules del agua del mapa (RE_AZUL) según su brillo.
def mina(agua=False):
    im = Image.new('P', (48, 48), 11); im.putpalette(po_pal)
    MX, MY, R = 23.5, 23.5, 6.5
    def color(v, b):
        if agua: return RE_AZUL[max(0, min(len(RE_AZUL) - 1, int(v / 230 * len(RE_AZUL))))]
        return po_color((v, v, v * b))
    for y in range(48):                                                    # puntas: conos finos de R - 1 a R + 4
        for x in range(48):
            for k in range(8):
                a = k * math.pi / 4 + math.pi / 8
                u = (x - MX) * math.cos(a) + (y - MY) * math.sin(a)        # a lo largo de la punta
                w = -(x - MX) * math.sin(a) + (y - MY) * math.cos(a)       # de costado
                if R - 1 < u < R + 4 and abs(w) < 0.4 + 1.1 * (R + 4 - u) / 5:
                    v = 55 + 90 * (0.5 + 0.5 * (-math.cos(a) - math.sin(a)) / 1.42) - (25 if w > 0.3 else 0)
                    im.putpixel((x, y), color(v, 1.05))
    for y in range(48):
        for x in range(48):
            dx, dy = (x - MX) / R, (y - MY) / R
            if dx * dx + dy * dy >= 1: continue
            dz = math.sqrt(1 - dx * dx - dy * dy)
            luz = max(0, (-dx - dy + dz) / 1.73)
            v = 30 + 130 * luz + (70 if luz > 0.95 else 0)
            im.putpixel((x, y), color(v, 1.08))
    return im
po_hoja = Image.new('P', (48 * PO_FRAMES, 48), 11); po_hoja.putpalette(po_pal)
cuadros = ([pozo] + [remo_piezas[9 * k + 4] for k in range(4)] + [mina()] + detonada
           + [tumba, lapida, cruz] + remo_piezas + [mina(True)])
assert len(cuadros) == PO_FRAMES
for i, im in enumerate(cuadros):
    po_hoja.paste(im, (48 * i, 0))
pcx = io.BytesIO(); po_hoja.save(pcx, 'PCX'); PO_PCX = pcx.getvalue()

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
STTS = {os.path.join('TERRAIN', 'SUBTYPE', n + '.STT'): stt(n, l) for n, l in (('landing', 'Landing'), ('carrier', 'Carrier'), ('cabotage', 'Cabotage'), ('trap', 'Trap'), ('camouflg', 'Camouflage'))}
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
NUEVOS[os.path.join('SETS', 'Fantasy', 'darkcomp.pcx')] = DC_PCX
NUEVOS[os.path.join('RUINS', 'pozos.pcx')] = PO_PCX
NUEVOS[os.path.join('RUINS', 'aviso.pcx')] = PZ_PCX
NUEVOS[os.path.join('FX', 'Burst.wav')] = BURST
NUEVOS.update(NUEVOS_TIT)
# Listas de ítems de los mapas al azar (random\Grass del repo, editadas por el usuario el 23/10/2026: sin los ítems
# de vuelo). Con ri_go cuentan sobre todo sus 8 especiales; los 32 comunes valen en el Darklord.exe original.
for _f in ('ITEM.DAT', 'Item0.dat', 'Item1.dat', 'Item2.dat'):
    NUEVOS[os.path.join('RANDOM', 'Grass', _f)] = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'random', 'Grass', _f), 'rb').read()
# Manual de uso (manualuild_manual.py lo arma): va con el parche porque describe esta versión.
NUEVOS['Manual-Era-de-Alianzas.pdf'] = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'manual', 'Manual-Era-de-Alianzas.pdf'), 'rb').read()

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
# Editor de escenarios con las listas de bonos y la habilidad Bridge acordes al juego (editor_av.py).
import editor_av
OUT_ED = os.path.join(OUT_DIR, 'war3ed_av.exe')
assert os.path.abspath(OUT_ED).lower() != os.path.abspath(editor_av.SRC).lower()
print('editor', OUT_ED, editor_av.armar(OUT_ED))
