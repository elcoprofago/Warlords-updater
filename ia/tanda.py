# Tandas de partidas IA contra IA (specs\ia-destrezas-v1.md, base de pruebas).
#
# Cada partida: escribe DATA\IA.INI (qué colores juegan con la IA de prueba y qué partida guardada cargar), abre
# DarklordAV.exe, que carga sola SAVES\<partida>.SAV al llegar al menú principal (parche ia_menu), y espera:
#   - DATA\IA_FIN.CSV con el podio del cartel "Game Over" (parche ia_fin)  -> estado "ok";
#   - el tope de turnos (--tope-turnos)                                       -> estado "tope", PV calculados acá;
#   - IA.CSV sin crecer durante --cuelgue minutos, o el juego cerrado solo   -> estado "colgada" / "cerrada".
# Después cierra el juego, pasa IA.CSV, IA_BAT.CSV e IA_FIN.CSV a ia\datos.db y los borra.
#
# Rotación: las partidas van de a pares con asignaciones complementarias (los colores que en una juegan con la IA de
# prueba en la otra juegan con la original), así cada color ocupa cada IA la misma cantidad de veces en el total.
#
# Uso:
#   python ia\tanda.py nueva --partidas 6 --guardadas Tanda_Scarpart,Tanda_Borderlands,Tanda_Kor
#   python ia\tanda.py seguir            (retoma la última tanda sin terminar)
#   python ia\informe.py [tanda]          (informe de la tanda)
import argparse, csv, json, os, sqlite3, subprocess, sys, time

JUEGO = r'C:\Warlords3'
EXE = 'DarklordAV.exe'
DATA = os.path.join(JUEGO, 'DATA')
INI = os.path.join(DATA, 'IA.INI')
CSV_T, CSV_B, CSV_F = (os.path.join(DATA, n) for n in ('IA.CSV', 'IA_BAT.CSV', 'IA_FIN.CSV'))
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'datos.db')

# Colores con la IA de prueba en la primera partida de cada par; la segunda usa el complemento.
PATRONES = [(1, 3, 5, 7), (0, 1, 2, 3), (0, 1, 4, 5), (0, 3, 5, 6)]

SLOTS = [f's{i}' for i in range(16)]
COL_T = ['turno', 'color', 'ia', 'vivo', 'control', 'oro', 'ciudades', 'ejercitos', 'heroes'] + SLOTS
COL_B = (['turno', 'atacante', 'defensor', 'x', 'y', 'ciudad', 'resultado', 'ia_a', 'ia_d', 'n_a', 'n_d',
          'vivos_a', 'vivos_d'] + [f'a{i}' for i in range(17)] + [f'd{i}' for i in range(17)])
COL_F = ['turno', 'orden', 'puesto', 'color', 'ia', 'pv', 'ciudades', 'oro']

ESQUEMA = f'''
create table if not exists tanda (id integer primary key, inicio text, plan text, terminada integer default 0);
create table if not exists partida (id integer primary key, tanda integer, n integer, guardada text,
    asignacion text, inicio text, fin text, estado text, turnos integer);
create table if not exists turno (partida integer, {', '.join(c + ' integer' for c in COL_T)});
create table if not exists batalla (partida integer, {', '.join(c + ' integer' for c in COL_B)});
create table if not exists resultado (partida integer, color integer, ia integer, orden integer, puesto integer,
    pv integer, ciudades integer, oro integer, eliminado_turno integer);
'''


def ahora():
    return time.strftime('%Y-%m-%d %H:%M:%S')


def leer(ruta, n):
    if not os.path.exists(ruta):
        return []
    with open(ruta, newline='') as f:
        return [[int(v) for v in r] for r in csv.reader(f) if len(r) == n]


def pv_calc(ciudades, heroes, oro):
    """Fórmula del juego (ia/puntos-de-victoria.md), para partidas cortadas por el tope."""
    aj = oro if oro < 600 else 600 if oro <= 1000 else 600 + (oro - 1000) // 10
    return max(0, min(100, ciudades + heroes + aj // 100))


def puestos(filas, clave):
    """Puestos como los muestra el juego: empate con el anterior = mismo puesto; el siguiente salta."""
    filas = sorted(filas, key=lambda r: -clave(r))   # sort estable: a igual clave, color menor primero
    out, prev = [], None
    for k, r in enumerate(filas):
        p = out[-1][0] if prev is not None and clave(r) == prev else k + 1
        out.append((p, r)); prev = clave(r)
    return out


def importar(db, pid, estado):
    """Pasa los tres CSV a la base, completa el resultado y los borra. Devuelve la cantidad de turnos."""
    t, b, f = leer(CSV_T, len(COL_T)), leer(CSV_B, len(COL_B)), leer(CSV_F, len(COL_F))
    # ia_fin corre cada vez que se dibuja el cartel: vale el primer bloque (orden 1, 2, ...).
    corte = next((k for k, r in enumerate(f) if k and r[1] == 1), len(f)); f = f[:corte]
    db.executemany(f'insert into turno values (?{", ?" * len(COL_T)})', [[pid] + r for r in t])
    db.executemany(f'insert into batalla values (?{", ?" * len(COL_B)})', [[pid] + r for r in b])
    ultimo = {}
    for r in t:
        ultimo[r[1]] = dict(zip(COL_T, r))
    turnos = max((r[0] for r in t), default=0)
    if f:
        prev = None
        for r in f:
            d = dict(zip(COL_F, r))
            p = prev if d['puesto'] < 0 else d['puesto']; prev = p
            db.execute('insert into resultado values (?,?,?,?,?,?,?,?,null)',
                       (pid, d['color'], d['ia'], d['orden'], p, d['pv'], d['ciudades'], d['oro']))
        en_podio = {r[3] for r in f}
    else:
        vivos = [u for u in ultimo.values() if u['vivo'] and u['turno'] == turnos]
        tabla = puestos(vivos, lambda u: pv_calc(u['ciudades'], u['heroes'], u['oro']))
        for k, (p, u) in enumerate(tabla):
            db.execute('insert into resultado values (?,?,?,?,?,?,?,?,null)',
                       (pid, u['color'], u['ia'], k + 1, p, pv_calc(u['ciudades'], u['heroes'], u['oro']),
                        u['ciudades'], u['oro']))
        en_podio = {u['color'] for u in vivos}
    for c, u in ultimo.items():   # eliminados: su último turno registrado + 1
        if c not in en_podio:
            db.execute('insert into resultado values (?,?,?,null,null,0,0,0,?)', (pid, c, u['ia'], u['turno'] + 1))
    db.execute('update partida set fin=?, estado=?, turnos=? where id=?', (ahora(), estado, turnos, pid))
    db.commit()
    for ruta in (CSV_T, CSV_B, CSV_F):
        if os.path.exists(ruta):
            os.remove(ruta)
    return turnos


def escribir_ini(prueba, guardada):
    with open(INI, 'w', newline='\r\n') as f:
        f.write('[IA]\n')
        for c in range(8):
            f.write(f'Color{c}={"prueba" if c in prueba else "original"}\n')
        if guardada:
            f.write(f'[Tanda]\nPartida={guardada}\n')


def cerrar_juego():
    subprocess.run(['taskkill', '/F', '/IM', EXE], capture_output=True)


def plan(partidas, guardadas):
    out = []
    for i in range(partidas):
        par = i // 2
        g = guardadas[par % len(guardadas)]
        pat = set(PATRONES[(par // len(guardadas)) % len(PATRONES)])
        out.append({'guardada': g, 'prueba': sorted(pat if i % 2 == 0 else set(range(8)) - pat)})
    return out


def jugar(db, tid, n, p, a):
    asign = ''.join('P' if c in p['prueba'] else 'O' for c in range(8))
    pid = db.execute('insert into partida (tanda, n, guardada, asignacion, inicio, estado) values (?,?,?,?,?,?)',
                     (tid, n, p['guardada'], asign, ahora(), 'jugando')).lastrowid
    db.commit()
    print(f'[{ahora()}] partida {n + 1}: {p["guardada"]}, colores con IA de prueba {p["prueba"]} ({asign})', flush=True)
    escribir_ini(set(p['prueba']), p['guardada'])
    cerrar_juego()
    proc = subprocess.Popen([os.path.join(JUEGO, EXE)], cwd=JUEGO)
    t0 = ultimo_cambio = time.time(); tam = -1; estado = None
    while estado is None:
        time.sleep(5)
        if os.path.exists(CSV_F) and os.path.getsize(CSV_F) > 0:
            time.sleep(3); estado = 'ok'; break
        s = os.path.getsize(CSV_T) if os.path.exists(CSV_T) else 0
        if s != tam:
            tam, ultimo_cambio = s, time.time()
        if a.tope_turnos and leer(CSV_T, len(COL_T)) and max(r[0] for r in leer(CSV_T, len(COL_T))) > a.tope_turnos:
            estado = 'tope'
        elif proc.poll() is not None:
            estado = 'cerrada'
        elif time.time() - ultimo_cambio > a.cuelgue * 60:
            estado = 'colgada'
    cerrar_juego()
    time.sleep(2)
    turnos = importar(db, pid, estado)
    print(f'[{ahora()}]   -> {estado}, {turnos} turnos, {(time.time() - t0) / 60:.1f} min', flush=True)


def correr(db, tid, a):
    pl = json.loads(db.execute('select plan from tanda where id=?', (tid,)).fetchone()[0])
    hechas = db.execute('select count(*) from partida where tanda=?', (tid,)).fetchone()[0]
    try:
        for n in range(hechas, len(pl)):
            jugar(db, tid, n, pl[n], a)
        db.execute('update tanda set terminada=1 where id=?', (tid,)); db.commit()
        print(f'Tanda {tid} terminada. Informe: python ia\\informe.py {tid}')
    finally:
        escribir_ini(set(), None)   # sin [Tanda]: abrir el juego a mano ya no carga nada solo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('accion', choices=['nueva', 'seguir'])
    ap.add_argument('--partidas', type=int, default=6)
    ap.add_argument('--guardadas', default='Tanda_Scarpart,Tanda_Borderlands,Tanda_Kor')
    ap.add_argument('--tope-turnos', type=int, default=0, help='0 = hasta el Game Over del escenario')
    ap.add_argument('--cuelgue', type=float, default=10, help='minutos sin turnos nuevos = colgada')
    a = ap.parse_args()
    db = sqlite3.connect(DB); db.executescript(ESQUEMA)
    if any(os.path.exists(r) for r in (CSV_T, CSV_B, CSV_F)):   # registros de una partida a mano: no se pierden
        pid = db.execute('insert into partida (guardada, inicio, estado) values (?,?,?)',
                         ('(a mano)', ahora(), 'suelta')).lastrowid
        importar(db, pid, 'suelta')
        print(f'Registros sueltos de una partida anterior guardados como partida {pid} (estado "suelta").')
    if a.accion == 'nueva':
        gs = a.guardadas.split(',')
        faltan = [g for g in gs if not os.path.exists(os.path.join(JUEGO, 'SAVES', g + '.SAV'))]
        if faltan:
            sys.exit(f'No existen en {JUEGO}\\SAVES: {", ".join(g + ".SAV" for g in faltan)}')
        tid = db.execute('insert into tanda (inicio, plan) values (?,?)',
                         (ahora(), json.dumps(plan(a.partidas, gs)))).lastrowid
        db.commit()
    else:
        r = db.execute('select id from tanda where terminada=0 order by id desc').fetchone()
        if not r:
            sys.exit('No hay tandas sin terminar.')
        tid = r[0]
    correr(db, tid, a)


if __name__ == '__main__':
    main()
