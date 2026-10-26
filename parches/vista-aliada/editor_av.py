# Arma war3ed_av.exe (editor de escenarios) a partir de war3ed_ssg.exe, que solo se lee. Lo llama build.py.
# - Bonos de movimiento (Edit Army Data, diálogo 148, y Edit Hero Data, 154): no ofrece "bridge" ni "trap".
# - Bono de combate (los mismos diálogos): no ofrece "landing", "carrier", "cabotage", "bridge" ni "camo"; "trap" sí.
#   Las dos listas las llena 0x428d60(combo) con todos los TERRAIN\SUBTYPE\*.STT (sin la extensión); las envolturas
#   stt_move / stt_comb la llaman y después borran los nombres que no van (CB_FINDSTRINGEXACT, sin distinguir
#   mayúsculas, y CB_DELETESTRING). Miembros de los combos: 0x110, 0xd4, 0x98, 0x5c movimiento; 0x14c combate
#   (DDX en 0x413840 y 0x41b3e0). Los subtipos de Edit Terrain (0x43d9e7..) siguen con la lista completa.
# - Habilidad especial de Edit Army Data: "Giantslayer +N" (código 34, sin efecto en el juego original) pasa a
#   llamarse "Bridge +N", la habilidad que DarklordAV.exe suma en un puente en pie.
# El código va en el sobrante de .text (0x46ce8d..0x46d000, ceros en el archivo); se agranda su VirtualSize.
import struct, keystone

SRC = r'C:\Warlords3\war3ed_ssg.exe'
BASE = 0x400000
SEND = 0x48fad0      # SendMessageA (importación)
FILL = 0x428d60      # llena el combo con los subtipos; cdecl, devuelve la cantidad
CB_DELETESTRING, CB_FINDSTRINGEXACT = 0x144, 0x158
MOVE_NO = ('bridge', 'trap')
COMB_NO = ('landing', 'carrier', 'cabotage', 'bridge', 'camo')
CALLS = {0x41453e: 'move', 0x41454f: 'move', 0x414560: 'move', 0x41456f: 'move', 0x414580: 'comb',   # 148
         0x41d3d8: 'move', 0x41d3e9: 'move', 0x41d3fa: 'move', 0x41d409: 'move', 0x41d41a: 'comb'}   # 154
GIANT = 0x9b6eb      # entrada de DLGINIT 148 (combo 0x458, CB_ADDSTRING) del índice 14 = código 34

def armar(out_path):
    exe = bytearray(open(SRC, 'rb').read())
    ks = keystone.Ks(keystone.KS_ARCH_X86, keystone.KS_MODE_32)
    e_lfanew = struct.unpack_from('<I', exe, 0x3c)[0]
    opt = e_lfanew + 24
    sectab = opt + struct.unpack_from('<H', exe, e_lfanew + 20)[0]
    name, vsz, va, rsz, raw = struct.unpack_from('<8sIIII', exe, sectab)
    assert name.rstrip(b'\0') == b'.text' and (vsz, va, rsz, raw) == (0x6be8d, 0x1000, 0x6c000, 0x400)
    assert struct.unpack_from('<H', exe, opt + 70)[0] & 0x40 == 0     # sin ASLR: las direcciones son fijas
    cave = BASE + va + vsz
    cave = (cave + 15) & ~15
    end = BASE + va + rsz
    off = lambda a: a - BASE - va + raw

    # Datos: listas de nombres separados por NUL, terminadas en un NUL extra.
    lists = {k: b''.join(n.encode() + b'\0' for n in v) + b'\0' for k, v in (('move', MOVE_NO), ('comb', COMB_NO))}
    code_va = cave
    src = f'''
    stt_move:
        mov edx, MOVE_LIST
        jmp stt_go
    stt_comb:
        mov edx, COMB_LIST
    stt_go:
        push esi
        push edi
        push ebx
        mov esi, dword ptr [esp + 0x10]
        mov edi, edx
        push esi
        call {FILL:#x}
        add esp, 4
        mov ebx, eax
        test esi, esi
        je stt_out
    stt_name:
        cmp byte ptr [edi], 0
        je stt_out
        push edi
        push -1
        push {CB_FINDSTRINGEXACT:#x}
        push dword ptr [esi + 0x1c]
        call dword ptr [{SEND:#x}]
        cmp eax, -1
        je stt_skip
        push 0
        push eax
        push {CB_DELETESTRING:#x}
        push dword ptr [esi + 0x1c]
        call dword ptr [{SEND:#x}]
        dec ebx
    stt_skip:
        inc edi
        cmp byte ptr [edi - 1], 0
        jne stt_skip
        jmp stt_name
    stt_out:
        mov eax, ebx
        pop ebx
        pop edi
        pop esi
        ret
    '''
    # Dos pasadas: la primera mide el código para ubicar las listas detrás.
    probe = bytes(ks.asm(src.replace('MOVE_LIST', hex(cave)).replace('COMB_LIST', hex(cave)), code_va)[0])
    move_va = code_va + len(probe)
    comb_va = move_va + len(lists['move'])
    enc, _ = ks.asm(src.replace('MOVE_LIST', hex(move_va)).replace('COMB_LIST', hex(comb_va)), code_va)
    code = bytes(enc)
    assert len(code) == len(probe)
    blob = code + lists['move'] + lists['comb']
    assert code_va + len(blob) <= end, 'no entra en el sobrante de .text'
    assert exe[off(code_va):off(code_va) + len(blob)] == bytes(len(blob))
    exe[off(code_va):off(code_va) + len(blob)] = blob
    stt_move = code_va
    assert code.startswith(b'\xba' + struct.pack('<I', move_va))
    k = code.index(b'\xba' + struct.pack('<I', comb_va))     # mov edx, COMB_LIST: entrada de stt_comb
    assert k < 16
    stt_comb = code_va + k
    struct.pack_into('<I', exe, sectab + 8, code_va + len(blob) - BASE - va)

    for site, kind in CALLS.items():
        o = off(site)
        assert exe[o] == 0xe8 and site + 5 + struct.unpack_from('<i', exe, o + 1)[0] == FILL, hex(site)
        dest = stt_move if kind == 'move' else stt_comb
        struct.pack_into('<i', exe, o + 1, dest - site - 5)

    old = b'X\x04\x03\x04\x0f\x00\x00\x00Giantslayer +N\x00'
    assert exe[GIANT:GIANT + len(old)] == old
    exe[GIANT + 8:GIANT + len(old)] = b'Bridge +N'.ljust(15, b'\0')

    assert struct.unpack_from('<I', exe, opt + 64)[0] == 0      # sin CheckSum que corregir
    open(out_path, 'wb').write(exe)
    return {'stt_move': hex(stt_move), 'stt_comb': hex(stt_comb), 'bytes': len(blob)}
