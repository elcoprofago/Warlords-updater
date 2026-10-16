"""Cuadro de posiciones de un mapa, en PDF, para la sección de estadísticas del Clan.

Solo cuenta partidas comparables: estado 'ok', tanda con bando común en ese mapa y un mismo exe del parche.
"""
import json, math, os, sqlite3, sys
from datetime import date
from fpdf import FPDF

BASE = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))
DB = os.path.join(BASE, 'datos.db')
POSICIONES = os.path.join(BASE, 'posiciones.json')
COLORES = ['blanco', 'amarillo', 'naranja', 'rojo', 'verde', 'azul', 'celeste', 'negro']
FUENTES = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts')


def wilson(k, n, z=1.96):
    if not n:
        return 0.0, 0.0
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - m), min(1.0, c + m)


def marcas(n):
    return ','.join('?' * n)


def tandas_comparables(db, guardada):
    """{exe: [(id, parche)]} de las tandas donde el mapa se jugó con bando común."""
    grupos = {}
    for tid, parche, exe, bandos in db.execute('select id, parche, exe, bandos from tanda order by id'):
        try:
            b = json.loads(bandos or '{}')
        except ValueError:
            continue
        if b.get(guardada) == 'común' and exe:
            grupos.setdefault(exe, []).append((tid, parche))
    return grupos


def partidas_de(db, guardada, ids):
    return [r[0] for r in db.execute(f"select id from partida where estado='ok' and guardada=? and tanda in "
                                     f"({marcas(len(ids))}) order by id", [guardada, *ids])]


def medir(db, guardada):
    grupos = tandas_comparables(db, guardada)
    if not grupos:
        return None
    # Un solo exe por cuadro: el que más partidas tiene de ese mapa.
    exe = max(grupos, key=lambda e: len(partidas_de(db, guardada, [t for t, _ in grupos[e]])))
    ids = [t for t, _ in grupos[exe]]
    partidas = partidas_de(db, guardada, ids)
    if not partidas:
        return None
    q = marcas(len(partidas))
    turnos = [r[0] for r in db.execute(f'select distinct turnos from partida where id in ({q}) order by 1', partidas)]
    tandas = [r[0] for r in db.execute(f'select distinct tanda from partida where id in ({q}) order by 1', partidas)]
    filas = []
    for c in range(8):
        rs = db.execute(f'select puesto, pv, ciudades, eliminado_turno from resultado where color=? and partida in ({q})',
                        [c, *partidas]).fetchall()
        n = len(rs)
        if not n:
            continue
        gana = sum(1 for r in rs if r[0] == 1)
        vive = sum(1 for r in rs if r[3] is None)
        filas.append(dict(nombre=COLORES[c], n=n, gana=gana, vive=vive,
                          ic_gana=wilson(gana, n), ic_vive=wilson(vive, n),
                          podio=sum(1 for r in rs if r[0] is not None and r[0] <= 3),
                          pv=sum(r[1] or 0 for r in rs) / n, ciudades=sum(r[2] or 0 for r in rs) / n))
    parches = sorted({p for t, p in grupos[exe] if p and t in tandas})
    return dict(guardada=guardada, exe=exe, parches=parches, tandas=tandas, partidas=len(partidas),
                turnos=turnos, filas=filas)


def mapas(db):
    """[(guardada, partidas comparables)] de los mapas que tienen alguna."""
    salida = []
    for (g,) in db.execute("select distinct guardada from partida where estado='ok' order by guardada"):
        d = medir(db, g)
        if d:
            salida.append((g, d['partidas']))
    return salida


def rango(ts):
    """[6,7,8,10] -> '6–8, 10'"""
    out, i = [], 0
    while i < len(ts):
        j = i
        while j + 1 < len(ts) and ts[j + 1] == ts[j] + 1:
            j += 1
        out.append(str(ts[i]) if i == j else f'{ts[i]}–{ts[j]}'); i = j + 1
    return ', '.join(out)


def pct(x):
    return f'{round(100 * x)} %'


def exportar(guardada, destino, db=None):
    db = db or sqlite3.connect(DB)
    d = medir(db, guardada)
    if not d:
        raise ValueError(f'No hay partidas comparables de {guardada}.')
    try:
        with open(POSICIONES, encoding='utf-8') as f:
            pos = json.load(f).get(guardada, {})
    except (OSError, ValueError):
        pos = {}
    mapa = guardada[6:] if guardada.startswith('Tanda_') else guardada

    pdf = FPDF(orientation='L', format='A4')
    pdf.add_font('ui', '', os.path.join(FUENTES, 'segoeui.ttf'))
    pdf.add_font('ui', 'B', os.path.join(FUENTES, 'segoeuib.ttf'))
    pdf.set_margins(14, 12, 14); pdf.set_auto_page_break(True, 12)
    pdf.add_page()
    pdf.set_font('ui', 'B', 18)
    pdf.cell(0, 10, f'Warlords III — {mapa}: rating de posiciones', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('ui', '', 10)
    turnos = ' o '.join(str(t) for t in d['turnos'])
    pdf.multi_cell(0, 5,
        f"{d['partidas']} partidas de {turnos} turnos, ocho colores manejados por la computadora, todos con el mismo "
        f"bando (el mismo ejército): las diferencias vienen de la posición de arranque. "
        f"Medido con el parche vista-aliada {', '.join(d['parches'])} (exe {d['exe']}), tandas {rango(d['tandas'])}. "
        f"Generado el {date.today():%d/%m/%Y}.", new_x='LMARGIN', new_y='NEXT')
    pdf.ln(3)
    cols = [('#', 8), ('Color', 22), ('Posición de arranque', 70), ('Partidas', 18), ('Gana', 16),
            ('Gana (IC 95 %)', 30), ('Sobrevive', 20), ('Sobrevive (IC 95 %)', 34), ('Podio', 16),
            ('PV prom.', 18), ('Ciudades', 18)]

    def tabla(titulo, clave):
        pdf.set_font('ui', 'B', 12); pdf.cell(0, 7, titulo, new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('ui', 'B', 9); pdf.set_fill_color(225, 225, 225)
        for t, w in cols:
            pdf.cell(w, 6, t, border=1, fill=True, align='C')
        pdf.ln(); pdf.set_font('ui', '', 9)
        orden = sorted(d['filas'], key=lambda f: (-f[clave] / f['n'], -f['pv']))
        for i, f in enumerate(orden, 1):
            ig, iv, n = f['ic_gana'], f['ic_vive'], f['n']
            vals = [str(i), f['nombre'], pos.get(f['nombre'], ''), str(n), pct(f['gana'] / n),
                    f'{pct(ig[0])} – {pct(ig[1])}', pct(f['vive'] / n), f'{pct(iv[0])} – {pct(iv[1])}',
                    pct(f['podio'] / n), f"{f['pv']:.1f}", f"{f['ciudades']:.1f}"]
            for (t, w), v in zip(cols, vals):
                pdf.cell(w, 6, v, border=1, align='L' if t in ('Color', 'Posición de arranque') else 'C')
            pdf.ln()
        pdf.ln(3)

    tabla('Para ganar', 'gana')
    tabla('Para sobrevivir', 'vive')
    pdf.set_font('ui', '', 8.5)
    pdf.multi_cell(0, 4.3,
        "Cómo leerlo. Gana: partidas terminadas en primer puesto (un empate en el primero cuenta como victoria). "
        "Sobrevive: sigue en juego al último turno. Podio: puestos 1 a 3. PV: puntos de victoria al final. "
        "IC 95 %: entre qué valores está el porcentaje real con un 95 % de confianza (intervalo de Wilson); "
        "si los intervalos de dos colores se superponen mucho, la diferencia entre ellos puede ser azar. "
        "Son partidas de computadora contra computadora: muestran qué posición aprovecha mejor la IA del juego, "
        "que puede no coincidir con lo que haría un jugador humano.", new_x='LMARGIN', new_y='NEXT')
    pdf.output(destino)
    return d


if __name__ == '__main__':
    g = sys.argv[1] if len(sys.argv) > 1 else 'Tanda_Scarpart'
    print(exportar(g, sys.argv[2] if len(sys.argv) > 2 else f'{g}.pdf'))
