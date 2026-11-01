# Cuenta los puentes de una guardada (misma regla que br_kind de vista-aliada) y, para cada puente entero, la cuenta
# de ai_brs por color al empezar (x = la ciudad dueña lo descarta). Uso: python ia\puentes.py Tanda_Borderlands ...
# Aproxima la distancia del juego (0x4974a0) con max(|dx|, |dy|).
import os, struct, sys

import tanda


def rd(d, va, n):
    off = 0x6d
    for b, t in tanda.SAV_BLOQUES:
        if b <= va and va + n <= b + t:
            return d[off + va - b:off + va - b + n]
        off += t
for g in sys.argv[1:]:
    d = open(os.path.join(tanda.JUEGO, 'SAVES', g + '.SAV'), 'rb').read()
    w, h, sh = struct.unpack('<hhxxB', rd(d, 0x503e00, 7))
    ent, der = [], 0
    for x in range(w):
        for y in range(h):
            a = 0x503e58 + ((y * 10) << sh) + x * 10
            t = rd(d, a, 10)
            wd = int.from_bytes(t[:2], 'little')
            if wd & 0x4000: continue
            if int.from_bytes(rd(d, 0x535f0c + (wd & 0x1f) * 0x58, 2), 'little') != 1: continue
            s = t[3] & 7
            if s == 1: ent.append((x, y))
            elif s == 0 and t[9] & 0x80: der += 1
    print(g, f'{w}x{h}', 'enteros', len(ent), 'derribados', der, ent[:20])

    nc = int.from_bytes(rd(d, 0x537e2a, 2), 'little', signed=True)
    cs = []
    for i in range(nc):
        r = rd(d, 0x537ed0 + i * 0xde, 0x10)
        cs.append((r[0], r[1], int.from_bytes(rd(d, 0x537e2c + i*0xde, 2), 'little', signed=True), int.from_bytes(rd(d, 0x537e2e + i*0xde, 2), 'little', signed=True)))
    temp = [rd(d, 0x561ef9 + p * 0x49a, 1)[0] for p in range(8)]
    print('  temperamento', temp, 'ciudades', nc)
    dip = lambda a, b: rd(d, 0x55ee4c + a * 56 + b, 1)[0]
    for (bx, by) in ent:
        viv = [c for c in cs if c[0]]
        dueño = min(viv, key=lambda c: max(abs(c[2]-bx), abs(c[3]-by)))[1]
        fila = []
        for p in range(8):
            c = temp[p]; s = -2 if c == 0 else 0; s += 1
            if dueño != 8 and (dueño == p or dip(p, dueño) != 2): fila.append('x'); continue
            near = sorted((max(abs(cc[2]-bx), abs(cc[3]-by)), cc[1]) for cc in viv)[:12]
            for dist, ow in near:
                if dist == 0 or dist > 30: continue
                k = 2 if dist < 15 else 1
                if ow == p: s -= k
                elif ow != 8 and dip(p, ow) == 2: s += k
            n = sum(1 for cc in viv if cc[1] == p)
            s += (n > 5) + (n > 15)
            fila.append(c + s)
        print(f'  puente {bx},{by} dueño {dueño}:', fila)
