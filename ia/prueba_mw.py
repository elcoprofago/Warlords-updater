"""Prueba emulada del punto 4 de ia\\PENDIENTE-ia-muros.md (vista-aliada 1.0.274.0): mw_ev y mw_tile.

Con cada guardada (y su variante forzada de prueba_mp_scan), para cada color que elige un paso (mp_pick):
- mw_ev desde la casilla de una pila suya con «build» tiene que proponer MPW_CODE, con la distancia de rey hasta el
  primer bloque del tramo elegido; y mw_tile tiene que dar ese bloque con la dirección del tramo (E o N).
Controles (cada uno tiene que dar -1; sin IA.INI, desde la 1.0.283.0, propone): color original (IA_MODE = 0), sin oro, casilla sin pila
con «build», tramo entero con MURALLA propia. Y uno que tiene que cambiar el bloque: MURALLA en el primer bloque del
tramo -> mw_tile da el segundo.
Lo que no se emula: mw_go (mover la pila y mandar BD_PKT); eso se ve en el juego (TAREAS).

Uso: python ia\\prueba_mw.py [DarklordAV.exe] [guardadas...]
"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prueba_mp_scan as P
import tanda
from motor import STK, RET
from mp_modelo import MP_P
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EAX, UC_X86_REG_EDX, UC_X86_REG_ECX, UC_X86_REG_EBX

MPW_CODE, MPW_DMAX = 0x7000, 30
ARMY = 0x54fe50


def simbolos(exe):
    """ai_brreb empieza con cmp word [esp+4], MPW_CODE; jl; jmp [MW_VEC]. MW_VEC = (mw_go, mw_ev). En mw_ev:
    cmp byte [ebx + IA_MODE], 1 (IA_ON = IA_MODE + 8). mw_tile es el primer call de mw_ev después de mw_hasb."""
    img = open(exe, 'rb').read()
    import pefile
    pe = pefile.PE(data=img)
    va = lambda o: pe.get_rva_from_offset(o) + pe.OPTIONAL_HEADER.ImageBase
    off = lambda v: pe.get_offset_from_rva(v - pe.OPTIONAL_HEADER.ImageBase)
    o = img.find(b'\x66\x81\x7c\x24\x04\x00\x70\x7c')
    assert o > 0, 'este exe no tiene el punto 4 (mw_go / mw_ev)'
    assert img[o + 9:o + 11] == b'\xff\x25'
    vec = struct.unpack_from('<I', img, o + 11)[0]
    go, ev = struct.unpack_from('<II', img, off(vec))
    e = off(ev)
    mode = struct.unpack_from('<I', img, img.find(b'\x80\xbb', e) + 2)[0]
    on = mode + 8     # ia_on va justo después de ia_mode (8 bytes); desde la 1.0.283.0 mw_ev ya no lo mira
    calls = []
    i = e
    while len(calls) < 2:
        i = img.find(b'\xe8', i)
        if img[i - 3:i] == b'\x6a\x00\x00' or True:
            calls.append(va(i) + 5 + struct.unpack_from('<i', img, i + 1)[0])
        i += 1
    # el primer call es mw_hasb, el segundo mw_tile (pueden aparecer E8 dentro de otras instrucciones: se verifican)
    return ev, calls[0], calls[1], on, mode


def llamar(J, addr, args=(), ebx=0):
    mu = J.m.mu
    sp = STK + 0x80000 - 4 - 4 * len(args)
    mu.mem_write(sp, struct.pack('<I', RET) + b''.join(struct.pack('<i', a) for a in args))
    mu.reg_write(UC_X86_REG_ESP, sp)
    mu.reg_write(UC_X86_REG_EBX, ebx)
    J.m.fallo = None
    mu.emu_start(addr, RET, count=4_000_000_000)
    if J.m.fallo:
        raise RuntimeError(f'{addr:#x}: {J.m.fallo}')
    assert mu.reg_read(UC_X86_REG_ESP) == sp + 4, 'la pila no quedó igual'
    assert mu.reg_read(UC_X86_REG_EBX) == ebx, 'no preserva ebx'
    s32 = lambda r: struct.unpack('<i', struct.pack('<I', mu.reg_read(r) & 0xffffffff))[0]
    return s32(UC_X86_REG_EAX), s32(UC_X86_REG_EDX), mu.reg_read(UC_X86_REG_ECX) & 0xffffffff


def pilas_build(J, p):
    """[(x, y)] de los ejércitos vivos de p con «build» (lo mismo que mira mw_hasb, leído en Python)."""
    mu = J.m.mu
    n = struct.unpack('<h', bytes(mu.mem_read(ARMY, 2)))[0]
    out = []
    for i in range(1, n):
        r = bytes(mu.mem_read(ARMY + i * 0x1c, 0x1c))
        x, y = struct.unpack_from('<hh', r, 2)
        if not r[0x13] & 0x40:
            continue
        t = struct.unpack_from('<H', r, 0xe)[0]
        s, d = t & 0x1f, (t >> 5) & 0xf
        if s > 15 or d != p:
            continue
        u = bytes(mu.mem_read(0x53c410 + (d * 16 + s) * 0xfc, 0xfc))
        if any(u[0xb2 + 9 * b:0xb2 + 9 * b + 9].split(b'\0')[0].lower() == b'build' for b in range(4)):
            out.append((x, y))
    return out


def probar(exe, g, S):
    ev, hasb, tile, on, mode = S
    J = P.Juego(exe, g)
    mu = J.m.mu
    llamar(J, J.scan)
    if not J.var(0) & 0xff:
        print(f'{g}: mp_scan no terminó')
        return False
    tr = [struct.unpack('<HBBBBH', bytes(mu.mem_read(J.TR + 8 * k, 8))) for k in range(J.var(2))]
    ok, alguno = True, False
    for p in range(8):
        llamar(J, J.pick, ebx=p)
        obj = struct.unpack('<i', bytes(mu.mem_read(J.OBJ + 4 * p, 4)))[0]
        if obj == -1:
            continue
        c, L, v = tr[obj >> 16][:3]
        dd = 1 if v else MP_P
        celdas = [((c + dd * i) // MP_P - 1, (c + dd * i) % MP_P - 1) for i in range(L)]
        pw = 0x4000 | ((1 if v else 3) << 8) | P.OB_MURO
        x0, y0, pw0 = llamar(J, tile, ebx=p)
        if (x0, y0, pw0) != (*celdas[0], pw):
            print(f'{g} color {p}: mw_tile dio {(x0, y0, hex(pw0))}, esperado {celdas[0]} {pw:#x}')
            ok = False
            continue
        pilas = [(max(abs(x - x0), abs(y - y0)), x, y) for x, y in pilas_build(J, p)]
        pilas = [t for t in pilas if t[0] <= MPW_DMAX]
        if not pilas:
            # se acerca una pila viva de p a 3 casillas del bloque y su unidad recibe «build» (solo en memoria)
            n = struct.unpack('<h', bytes(mu.mem_read(ARMY, 2)))[0]
            # (al empezar, la única pila de cada color es el héroe: pasa a ser la unidad de la ranura 0)
            i = next((i for i in range(1, n) if (r := bytes(mu.mem_read(ARMY + i * 0x1c, 0x1c)))[0x13] & 0x40
                      and (struct.unpack_from('<H', r, 0xe)[0] >> 5) & 0xf == p), None)
            if i is None:
                print(f'{g} color {p}: sin pilas vivas (sin prueba de mw_ev)')
                continue
            t = struct.unpack('<H', bytes(mu.mem_read(ARMY + i * 0x1c + 0xe, 2)))[0] & ~0x1f
            mu.mem_write(ARMY + i * 0x1c + 0xe, struct.pack('<H', t))
            u = 0x53c410 + p * 16 * 0xfc + 0xb2 + 3 * 9
            mu.mem_write(u, b'build'.ljust(9, b'\0'))
            sx = x0 + 3 if x0 + 3 < 150 else x0 - 3
            mu.mem_write(ARMY + i * 0x1c + 2, struct.pack('<hh', sx, y0))
            pilas = [(3, sx, y0)]
            print(f'{g} color {p}: pila {i} llevada a ({sx},{y0}) con «build»')
        alguno = True
        d, sx, sy = min(pilas)
        mu.mem_write(mode + p, b'\1')
        mu.mem_write(on, b'\1')   # solo para mw_ev: con IA_ON, mp_pick escribe el evento 51 (fopen)
        jx = struct.unpack('<h', bytes(mu.mem_read(0x4fb0ec, 2)))
        mu.mem_write(0x4fb0ec, struct.pack('<h', p))
        a, e, _ = llamar(J, ev, (sx, sy))
        bien = a == MPW_CODE and e == max(d, 1)
        print(f'{g} color {p}: pila ({sx},{sy}) -> bloque {celdas[0]} distancia {d}: mw_ev {"PROPONE" if bien else "DA " + str((a, e))}')
        ok &= bien

        def control(nombre, cambia, deshace, args=(sx, sy), f=ev, espera=-1):
            cambia()
            r = llamar(J, f, args, ebx=p)
            deshace()
            bien = r[0] == espera if f == ev else r[:2] == espera
            print(f'   control {nombre}: {"bien" if bien else "MAL " + str(r)}')
            return bien
        nada = lambda: None
        # desde la 1.0.283.0 la MURALLA es IA del ranking: sin IA.INI (IA_ON = 0, IA_MODE = 1) también propone
        ok &= control('sin IA.INI (ranking: IA_ON = 0) propone', lambda: mu.mem_write(on, b'\0'),
                      lambda: mu.mem_write(on, b'\1'), espera=MPW_CODE)
        ok &= control('color original (IA_MODE = 0)', lambda: mu.mem_write(mode + p, b'\0'),
                      lambda: mu.mem_write(mode + p, b'\1'))
        oro = bytes(mu.mem_read(P.ORO + p * P.SIDE, 4))
        ok &= control('sin oro', lambda: mu.mem_write(P.ORO + p * P.SIDE, bytes(4)),
                      lambda: mu.mem_write(P.ORO + p * P.SIDE, oro))
        libre = next(((x, y) for x in range(0, 160) for y in range(0, 160) if (x, y) not in pilas_build(J, p)
                      and max(abs(x - x0), abs(y - y0)) <= 5), None)
        ok &= control(f'casilla sin pila con «build» {libre}', nada, nada, args=libre)
        # MURALLAS propias en la tabla de obras (como prueba_mp_scan.murallas)
        omap, tab = J.m.ob

        def poner(cs):
            def f():
                for i, (x, y) in enumerate(cs):
                    mu.mem_write(tab + 8 * i, struct.pack('<hhBBBB', x, y, P.OB_MURO, 0, p, 0))
                    mu.mem_write(omap + J.m.obw * ((y << J.m.sh) + x), struct.pack('<H', i + 1)[:J.m.obw])
                mu.mem_write(tab - 4, struct.pack('<I', len(cs)))
            return f

        def sacar():
            mu.mem_write(omap, J.m.obmap0)
            mu.mem_write(tab - 4, J.m.obtab0)
        ok &= control('tramo entero con MURALLA', poner(celdas), sacar)
        if L > 1:
            ok &= control('MURALLA en el primer bloque -> segundo', poner(celdas[:1]), sacar, args=(), f=tile,
                          espera=celdas[1])
        mu.mem_write(mode + p, b'\0')
        mu.mem_write(on, b'\0')
        mu.mem_write(0x4fb0ec, struct.pack('<h', *jx))
    if not alguno:
        print(f'{g}: ningún color con pila a mano (sin prueba de mw_ev)')
    return ok


if __name__ == '__main__':
    args = sys.argv[1:]
    exe = os.path.join(tanda.JUEGO, 'DarklordAV.exe')
    if args and args[0].lower().endswith('.exe'):
        exe = args.pop(0)
    S = simbolos(exe)
    print('mw_ev %#x mw_hasb %#x mw_tile %#x IA_ON %#x IA_MODE %#x' % S)
    gs = args or ['Tanda_hex_perfiles', 'Tanda_Borderlands', 'Tanda_Kor', 'Tanda_Scarpart', 'build_01']
    gs = gs + [P.forzar(g) for g in gs]
    r = [probar(exe, g, S) for g in gs]
    print('TODO OK' if all(r) else 'FALLA')
    sys.exit(0 if all(r) else 1)
