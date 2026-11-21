# Punto 5 de ia\PENDIENTE-ia-muros.md: ¿la IA eligió bien dónde levantar MURALLA?
# Por cada paso que un color empezó a cerrar en una tanda (evento 52) mide, desde el turno del primer bloque:
#  - bloques levantados y si completó el tramo (los de pasos\<mapa>.json);
#  - el lado protegido (el que tiene más ciudades del color en ese turno, reconstruyendo los dueños con las batallas
#    ganadas sobre ciudades) y cuántas de sus ciudades ahí;
#  - ataques enemigos a esas ciudades después del primer bloque y después de completarlo (con el tramo cerrado,
#    un ataque en tierra solo llega rodeando: por agua, por aire o por otro paso), ciudades perdidas ahí;
#  - ataques a las casillas del tramo (a la MURALLA).
# Control: el mismo paso elegido (evento 51) por un color original, que elige pero no construye; se mide igual
# desde su primer turno de elección.
# Uso: python ia\murallas_tanda.py 189 [Tanda_hex_perfiles]   (el segundo, el .json de pasos del mapa)
#      python ia\murallas_tanda.py 195 Tanda_Kor_BDA --v2   (pasos v2 como los arma el juego: cortes y corredores,
#      con sus lados, calculados de esa guardada con mp_modelo.detectar_v2)
import json, os, sqlite3, sys
from collections import defaultdict

import ciudades, mp_modelo, tanda

AQUI = os.path.dirname(os.path.abspath(__file__))


def pasos_v2(guardada):
    d = open(os.path.join(tanda.JUEGO, 'SAVES', guardada + '.SAV'), 'rb').read()
    _, _, G, C, pas, _ = mp_modelo.detectar_v2(d)
    cs = ciudades.leer(d)
    out = []
    for p in pas:
        seg = p['tramos'][p['principal']][1]
        if 'corredor' in p:
            zs = [set(z) for _, _, z in mp_modelo.lados_corredor(G, C, seg, p['corredor'])]
        else:
            (_, _, z0), _ = mp_modelo.separa(G, C, seg)
            z0 = set(z0)
            # el otro lado: lo alcanzable desde el tramo sin pasar por z0
            vis, q = set(seg) | z0, [j for s in seg for dv in mp_modelo.DV for j in [s + dv] if G[j] & 1 and j not in z0 and j not in seg]
            vis |= set(q); k = 0
            while k < len(q):
                i = q[k]; k += 1
                for dv in mp_modelo.DV:
                    j = i + dv
                    if G[j] & 1 and j not in vis:
                        vis.add(j); q.append(j)
            zs = [z0, set(q)]
        lados = []
        for z in zs:
            zc = {mp_modelo.xy(i) for i in z}
            lados.append({'casillas': len(z), 'ciudades': [n for n, c in enumerate(cs) if c.get('tam', 1) and
                                                          any(t in zc for t in ((c['x'] + a, c['y'] + b) for a in (0, 1) for b in (0, 1)))]})
        out.append({'tramo': [list(mp_modelo.xy(i)) for i in seg], 'lados': lados, 'corredor': 'corredor' in p})
    return out


def main(t, mapa, v2=False):
    db = sqlite3.connect(os.path.join(AQUI, 'datos.db'))
    pasos = pasos_v2(mapa) if v2 else json.load(open(os.path.join(AQUI, 'pasos', mapa + '.json')))
    de_casilla = {tuple(c): k for k, p in enumerate(pasos) for c in p['tramo']}
    guard = {}
    filas = {'P': [], 'O': []}
    for pid, g, turnos in db.execute("select id, guardada, turnos from partida where tanda=? and estado='ok'", (t,)):
        if g not in guard:
            with open(os.path.join(tanda.JUEGO, 'SAVES', g + '.SAV'), 'rb') as f:
                guard[g] = ciudades.leer(f.read())
        cs = guard[g]
        bat = db.execute('select turno, atacante, defensor, x, y, ciudad, resultado from batalla where partida=? '
                         'order by rowid', (pid,)).fetchall()

        def dueños(hasta):
            d = [c['dueño'] for c in cs]
            for tu, a, _, _, _, ci, r in bat:
                if tu >= hasta:
                    break
                if ci >= 0 and r == 1:
                    d[ci] = a
            return d

        bloques = defaultdict(list)
        for tu, col, x, y in db.execute('select turno, color, x, y from evento where partida=? and tipo=52', (pid,)):
            if (x, y) in de_casilla:
                bloques[(col, de_casilla[(x, y)])].append(tu)
        elegidos = {}
        for tu, col, ia, x, y in db.execute('select turno, color, ia, x, y from evento where partida=? and tipo=51 '
                                            'order by turno', (pid,)):
            if ia == 0 and (x, y) in de_casilla:
                elegidos.setdefault((col, de_casilla[(x, y)]), tu)
        casos = [('P', k, min(v), v) for k, v in bloques.items()] + [('O', k, v, []) for k, v in elegidos.items()]
        for tipo, (col, k), t0, bs in casos:
            p = pasos[k]
            d0 = dueños(t0)
            lado = max(p['lados'], key=lambda l: sum(d0[i] == col for i in l['ciudades']))
            mias = {i for i in lado['ciudades'] if d0[i] == col}
            if not mias:
                continue
            completo = len(set(bs)) and len(bs) >= len(p['tramo'])
            tc = sorted(bs)[len(p['tramo']) - 1] if completo else None
            at = at_c = perd = muro = perd_tot = 0
            for tu, a, de, x, y, ci, r in bat:
                if tu < t0 or a == col:
                    continue
                if ci >= 0 and de == col and r == 1:
                    perd_tot += 1
                if ci in mias and de == col:
                    at += 1
                    if tc is not None and tu > tc:
                        at_c += 1
                    if r == 1:
                        perd += 1
                if (x, y) in {tuple(c) for c in p['tramo']}:
                    muro += 1
            filas[tipo].append(dict(partida=pid, color=col, paso=k + 1, t0=t0, turnos=turnos, bloques=len(bs),
                                    largo=len(p['tramo']), completo=bool(completo), ciudades=len(mias),
                                    chico=lado is min(p['lados'], key=lambda l: l['casillas']),
                                    ataques=at, ataques_cerrado=at_c, perdidas=perd, perdidas_total=perd_tot, al_muro=muro))
    for tipo, nom in (('P', 'PRUEBA (levanta MURALLA)'), ('O', 'ORIGINAL (elige, no construye: control)')):
        fs = filas[tipo]
        print(f'\n== {nom}: {len(fs)} casos (color, paso, partida)')
        if not fs:
            continue
        n = len(fs)
        tr = sum(f['turnos'] - f['t0'] for f in fs) or 1
        print(f"  completos {sum(f['completo'] for f in fs)}/{n}; ciudades protegidas {sum(f['ciudades'] for f in fs)}; "
              f"lado chico del paso {sum(f['chico'] for f in fs)}")
        print(f"  ataques a esas ciudades {sum(f['ataques'] for f in fs)} ({100 * sum(f['ataques'] for f in fs) / tr:.1f}"
              f" por 100 turnos), perdidas {sum(f['perdidas'] for f in fs)}, con el tramo cerrado "
              f"{sum(f['ataques_cerrado'] for f in fs)}, contra la MURALLA {sum(f['al_muro'] for f in fs)}")
        print(f"  ciudades que el color perdió en todo el mapa desde ese turno: {sum(f['perdidas_total'] for f in fs)}"
              f" (del lado protegido: {sum(f['perdidas'] for f in fs)}); casos sin ningún ataque del lado protegido: "
              f"{sum(f['ataques'] == 0 for f in fs)}/{n}; turno medio del primer bloque/elección "
              f"{sum(f['t0'] for f in fs) / n:.1f} de {sum(f['turnos'] for f in fs) / n:.1f}")
        por = defaultdict(list)
        for f in fs:
            por[f['paso']].append(f)
        for k in sorted(por):
            g = por[k]
            print(f"  paso {k:2}{' C' if pasos[k - 1].get('corredor') else '  '} ({pasos[k - 1]['tramo'][0]}, {len(pasos[k - 1]['tramo'])} bl): {len(g)} casos, "
                  f"completos {sum(f['completo'] for f in g)}, ciudades {sum(f['ciudades'] for f in g)}, "
                  f"ataques {sum(f['ataques'] for f in g)}, perdidas {sum(f['perdidas'] for f in g)}, "
                  f"cerrado {sum(f['ataques_cerrado'] for f in g)}, al muro {sum(f['al_muro'] for f in g)}, "
                  f"t0 medio {sum(f['t0'] for f in g) / len(g):.1f}")


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if x != '--v2']
    main(int(a[0]), a[1] if len(a) > 1 else 'Tanda_hex_perfiles', '--v2' in sys.argv)
