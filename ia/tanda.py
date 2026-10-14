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
import argparse, configparser, csv, ctypes, json, os, sqlite3, subprocess, sys, threading, time
from ctypes import wintypes

JUEGO = r'C:\Warlords3'
EXE = 'DarklordAV.exe'
DATA = os.path.join(JUEGO, 'DATA')
INI = os.path.join(DATA, 'IA.INI')
CSV_T, CSV_B, CSV_F = (os.path.join(DATA, n) for n in ('IA.CSV', 'IA_BAT.CSV', 'IA_FIN.CSV'))
# Empaquetado en Monitor-IA.exe (ia\monitor-ia), el exe queda en ia\: la base y la configuración van junto a él.
BASE = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))
DB = os.path.join(BASE, 'datos.db')
CONFIG = os.path.join(BASE, 'tanda.ini')

# Controles del Monitor de IA: sonido del juego y corte de la tanda en curso.
CONTROL = {'silenciar': True}
CORTAR = threading.Event()

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


# Monitor del juego: misma lógica que Votación (lista de monitores, el elegido se guarda por nombre, y si ya no está
# conectado se usa el principal). El juego corre en ventana (GOG dxcfg, presentation=windowed), así que se centra su
# ventana en ese monitor; se vuelve a comprobar en cada vuelta de la espera por si el juego la recrea.
user32 = ctypes.windll.user32
user32.SetProcessDPIAware()


class _MonInfo(ctypes.Structure):
    _fields_ = [('cbSize', wintypes.DWORD), ('rcMonitor', wintypes.RECT), ('rcWork', wintypes.RECT),
                ('dwFlags', wintypes.DWORD), ('szDevice', wintypes.WCHAR * 32)]


def monitores():
    """[(nombre, x, y, ancho, alto, principal)], el principal primero."""
    out = []

    def cb(h, dc, r, l):
        m = _MonInfo(); m.cbSize = ctypes.sizeof(_MonInfo); user32.GetMonitorInfoW(h, ctypes.byref(m))
        r = m.rcMonitor
        out.append((m.szDevice, r.left, r.top, r.right - r.left, r.bottom - r.top, bool(m.dwFlags & 1)))
        return True
    proto = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(wintypes.RECT),
                               wintypes.LPARAM)
    user32.EnumDisplayMonitors(None, None, proto(cb), 0)
    return sorted(out, key=lambda m: not m[5])


def monitor_preferido():
    c = configparser.ConfigParser(); c.read(CONFIG)
    return c.get('Pantalla', 'preferida', fallback=None)


def elegir_monitor():
    ms = monitores()
    pref = monitor_preferido()
    print('Monitores:')
    for i, (nombre, x, y, an, al, princ) in enumerate(ms):
        marca = ' <- elegido' if nombre == pref else ''
        print(f'  {i + 1}. {nombre} ({an}x{al} @ {x},{y}){" principal" if princ else ""}{marca}')
    while True:
        r = input(f'Número del monitor para el juego (1-{len(ms)}): ').strip()
        if r.isdigit() and 1 <= int(r) <= len(ms):
            break
    c = configparser.ConfigParser(); c['Pantalla'] = {'preferida': ms[int(r) - 1][0]}
    with open(CONFIG, 'w') as f:
        c.write(f)
    print(f'Guardado: el juego se abre en {ms[int(r) - 1][0]}.')


def monitor_configurado():
    ms = monitores()
    pref = monitor_preferido()
    return next((m for m in ms if m[0] == pref), ms[0])


def ventana_del_juego(pid):
    """La ventana visible más grande del proceso del juego, o None."""
    hallada = []

    def cb(h, l):
        p = wintypes.DWORD(); user32.GetWindowThreadProcessId(h, ctypes.byref(p))
        if p.value == pid and user32.IsWindowVisible(h):
            r = wintypes.RECT(); user32.GetWindowRect(h, ctypes.byref(r))
            hallada.append(((r.right - r.left) * (r.bottom - r.top), h, r))
        return True
    user32.EnumWindows(ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(cb), 0)
    return max(hallada, key=lambda v: v[0])[1:] if hallada else None


def llevar_al_monitor(pid, m):
    v = ventana_del_juego(pid)
    if not v:
        return
    h, r = v
    _, x, y, an, al, _ = m
    cx, cy = (r.left + r.right) // 2, (r.top + r.bottom) // 2
    if x <= cx < x + an and y <= cy < y + al and r.right - r.left <= an and r.bottom - r.top <= al:
        return
    w, hh = r.right - r.left, r.bottom - r.top
    if w > an or hh > al:   # la ventana de juego toma el tamaño del monitor donde arrancó: se le da el del elegido
        user32.SetWindowPos(h, None, x, y, an, al, 0x0004 | 0x0010)   # SWP_NOZORDER | SWP_NOACTIVATE
    else:
        user32.SetWindowPos(h, None, x + (an - w) // 2, y + (al - hh) // 2, 0, 0, 0x0001 | 0x0004 | 0x0010)


def silenciar(pid, mudo=True):
    """Silencia (o devuelve) el sonido del juego (solo su sesión de audio, no el resto de la PC). La sesión aparece recién
    cuando el juego empieza a sonar, por eso se llama en cada vuelta. Requiere pycaw (pip install pycaw)."""
    try:
        from pycaw.pycaw import AudioUtilities
        for s in AudioUtilities.GetAllSessions():
            if s.ProcessId == pid and bool(s.SimpleAudioVolume.GetMute()) != mudo:
                s.SimpleAudioVolume.SetMute(int(mudo), None)
    except Exception as e:
        if not getattr(silenciar, 'avisado', False):
            silenciar.avisado = True
            print(f'  (no se pudo silenciar el juego: {e})', flush=True)


def apretar_un_jugador(pid):
    """Aprieta "Single Player" en el lanzador del juego (botón 1001), si está a la vista. El parche ia_menu de
    vista-aliada 1.0.31.0 debía hacerlo solo y en vivo no lo hace (14/10/2026: 90 s quieto en el lanzador)."""
    # Un WM_COMMAND directo deja la ventana del juego en blanco y sin jugar (14/10/2026): el botón tiene que recibir
    # el clic. Se le manda apretar y soltar el botón izquierdo, sin mover el mouse del usuario ni quitarle el foco.
    v = ventana_del_juego(pid)
    b = v and user32.GetDlgItem(v[0], 1001)
    if b:
        user32.PostMessageW(b, 0x0201, 1, 0x000a000a)   # WM_LBUTTONDOWN en (10, 10) del botón
        time.sleep(0.1)
        user32.PostMessageW(b, 0x0202, 0, 0x000a000a)   # WM_LBUTTONUP
        return True
    return False


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
    mon = monitor_configurado()
    for _ in range(30):   # la ventana tarda en aparecer: hasta 15 s
        time.sleep(0.5)
        if ventana_del_juego(proc.pid):
            break
    apretar_un_jugador(proc.pid)
    llevar_al_monitor(proc.pid, mon)
    t0 = ultimo_cambio = time.time(); tam = -1; estado = None
    while estado is None:
        time.sleep(5)
        llevar_al_monitor(proc.pid, monitor_configurado())   # el Monitor de IA puede cambiarlo en marcha
        silenciar(proc.pid, CONTROL['silenciar'])
        if CORTAR.is_set():
            estado = 'cortada'; break
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
    # Una partida cortada a mano queda registrada, pero al retomar se vuelve a jugar.
    hechas = db.execute("select count(*) from partida where tanda=? and estado!='cortada'", (tid,)).fetchone()[0]
    try:
        for n in range(hechas, len(pl)):
            if CORTAR.is_set():
                print(f'[{ahora()}] Tanda {tid} cortada. Se retoma con "Retomar".', flush=True)
                return
            jugar(db, tid, n, pl[n], a)
        db.execute('update tanda set terminada=1 where id=?', (tid,)); db.commit()
        print(f'Tanda {tid} terminada. Informe: python ia\\informe.py {tid}')
    finally:
        escribir_ini(set(), None)   # sin [Tanda]: abrir el juego a mano ya no carga nada solo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('accion', choices=['nueva', 'seguir', 'monitor'])
    ap.add_argument('--partidas', type=int, default=6)
    ap.add_argument('--guardadas', default='Tanda_Scarpart,Tanda_Borderlands,Tanda_Kor')
    ap.add_argument('--tope-turnos', type=int, default=0, help='0 = hasta el Game Over del escenario')
    ap.add_argument('--cuelgue', type=float, default=10, help='minutos sin turnos nuevos = colgada')
    a = ap.parse_args()
    if a.accion == 'monitor':
        return elegir_monitor()
    if not monitor_preferido() and len(monitores()) > 1:
        elegir_monitor()
    db, tid = preparar(a)
    correr(db, tid, a)


def preparar(a):
    """Abre la base, guarda registros sueltos y crea la tanda nueva o busca la última sin terminar."""
    db = sqlite3.connect(DB, check_same_thread=False); db.executescript(ESQUEMA)
    # Partida que quedó "jugando" porque se cerró la ventana de la tanda: sus registros son suyos y se retoma.
    for (pid,) in db.execute("select id from partida where estado='jugando'").fetchall():
        importar(db, pid, 'cortada')
        print(f'Partida {pid} había quedado a medias: guardada como "cortada", se vuelve a jugar al retomar.')
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
    return db, tid


if __name__ == '__main__':
    main()
