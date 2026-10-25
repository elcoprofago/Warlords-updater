# Tandas de partidas IA contra IA (specs\ia-destrezas-v1.md, base de pruebas).
#
# Cada partida: escribe DATA\IA.INI (qué colores juegan con la IA de prueba y qué partida guardada cargar), abre
# DarklordAV.exe, que carga sola SAVES\<partida>.SAV al llegar al menú principal (parche ia_menu), y espera:
#   - DATA\IA_FIN.CSV con el podio del cartel "Game Over" (parche ia_fin)  -> estado "ok";
#   - DATA\IA_VIC.CSV del cartel "An allied victory!" (parche ia_vic, solo aliados vivos: no hay Game Over ni podio,
#     el juego espera Aceptar)  -> estado "ok", podio armado con la regla del juego;
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
# Etapa 3 (alianzas, vista-aliada 1.0.33.0): diplomacia por turno y eventos (puentes, convoyes, refugios).
CSV_D, CSV_E, CSV_V = (os.path.join(DATA, n) for n in ('IA_DIP.CSV', 'IA_EVT.CSV', 'IA_VIC.CSV'))
# Empaquetado en Monitor-IA.exe (ia\monitor-ia), el exe queda en ia\: la base y la configuración van junto a él.
BASE = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))
DB = os.path.join(BASE, 'datos.db')
CONFIG = os.path.join(BASE, 'tanda.ini')

# Controles del Monitor de IA: sonido del juego y corte de la tanda en curso.
CONTROL = {'silenciar': True}
CORTAR = threading.Event()

# Nombre de cada color: índice del registro de jugador, el mismo orden que sus estandartes en el .SAV (Bwhite ...
# Bblack) y que "Scenario Sides" del editor (ia\PENDIENTE-entrenamiento-ia.md, 16/10/2026).
COLORES = ['blanco', 'amarillo', 'naranja', 'rojo', 'verde', 'azul', 'celeste', 'negro']

# Colores con la IA de prueba en la primera partida de cada par; la segunda usa el complemento.
PATRONES = [(1, 3, 5, 7), (0, 1, 2, 3), (0, 1, 4, 5), (0, 3, 5, 6)]

SLOTS = [f's{i}' for i in range(16)]
COL_T = ['turno', 'color', 'ia', 'vivo', 'control', 'oro', 'ciudades', 'ejercitos', 'heroes'] + SLOTS
COL_B = (['turno', 'atacante', 'defensor', 'x', 'y', 'ciudad', 'resultado', 'ia_a', 'ia_d', 'n_a', 'n_d',
          'vivos_a', 'vivos_d'] + [f'a{i}' for i in range(17)] + [f'd{i}' for i in range(17)] + ['colores_d'])
COL_F = ['turno', 'orden', 'puesto', 'color', 'ia', 'pv', 'ciudades', 'oro']
COL_V = ['turno', 'color', 'ia', 'pv', 'ciudades', 'oro']
# opciones: 1 ciudades compartidas, 2 Diplomacy, 4 Hidden Map, 8 vista aliada; d0..d7: 0 aliados, 1 paz, 2 guerra.
COL_D = ['turno', 'color', 'opciones'] + [f'd{i}' for i in range(8)]
COL_E = ['turno', 'color', 'ia', 'tipo', 'x', 'y', 'n']
# Tipos de evento (build.py, ia_evt).
EVENTOS = {1: 'puente derribado (criterio propio)', 2: 'convoy', 3: 'grupo partido al embarcar',
           4: 'puente reconstruido', 5: 'refugio en ciudad aliada', 6: 'puente derribado (misión)'}

ESQUEMA = f'''
create table if not exists tanda (id integer primary key, inicio text, plan text, terminada integer default 0,
    parche text, exe text, bandos text, alianzas text);
create table if not exists partida (id integer primary key, tanda integer, n integer, guardada text,
    asignacion text, perfiles text, inicio text, fin text, estado text, turnos integer);
create table if not exists turno (partida integer, {', '.join(c + ' integer' for c in COL_T)});
create table if not exists batalla (partida integer, {', '.join(c + ' integer' for c in COL_B)});
create table if not exists diplo (partida integer, {', '.join(c + ' integer' for c in COL_D)});
create table if not exists evento (partida integer, {', '.join(c + ' integer' for c in COL_E)});
create table if not exists resultado (partida integer, color integer, ia integer, orden integer, puesto integer,
    pv integer, ciudades integer, oro integer, eliminado_turno integer);
'''


# Versión del parche con que juega la IA de prueba. Una tanda se juega entera con el mismo DarklordAV.exe: el número
# de vista-aliada sale de parches\parches.txt del repo (build.py instala sin tocar C:\Warlords3\PARCHES), y la huella
# del exe distingue dos compilaciones con el mismo número.
PARCHES_TXT = os.path.join(os.path.dirname(BASE), 'parches', 'parches.txt')


def parche_actual():
    import hashlib
    with open(os.path.join(JUEGO, EXE), 'rb') as f:
        exe = hashlib.sha256(f.read()).hexdigest()[:8]
    ver = '?'
    if os.path.exists(PARCHES_TXT):
        for l in open(PARCHES_TXT, encoding='utf-8'):
            if l.startswith('vista-aliada|'):
                ver = l.split('|')[1]
    return ver, exe


# Bandos de cada color en el .SAV: 8 jugadores x 16 unidades de 0xfc bytes, el mismo registro que el exe tiene en
# 0x53c410; en los .SAV de 8 bandos empieza en 0x383f5 (hallado en las Tanda_*.SAV, contrastado con otras guardadas).
SAV_BANDOS, UNIDAD = 0x383f5, 0xfc


def bandos(guardada):
    """'común' si los 8 colores tienen las mismas 16 unidades, 'distintos' si no, '?' si el bloque no se reconoce."""
    with open(os.path.join(JUEGO, 'SAVES', guardada + '.SAV'), 'rb') as f:
        d = f.read()
    r = 16 * UNIDAD
    colores = [d[SAV_BANDOS + c * r:SAV_BANDOS + (c + 1) * r] for c in range(8)]
    # Los colores que no juegan (Hexagon: 2 y 6) traen un bloque vacío o el bando de fábrica: no cuentan.
    colores = [c for c in colores if c[:1].isalpha()]
    if len(colores) < 2 or len(colores[-1]) < r:
        return '?'
    return 'común' if all(c == colores[0] for c in colores) else 'distintos'


# Diplomacia y opciones en el .SAV: los bloques se cargan a partir de 0x6d en este orden de direcciones del exe
# (el mismo armado que parches\vista-aliada\prueba_iaregistro.py). DIPLO = 0x55ee4c + a*56 + b (0 aliados).
SAV_BLOQUES = ((0x503e00, 0x12), (0x503e58, 0x32000), (0x535ed0, 0xa96), (0x536b30, 0x2d894))


def alianzas(guardada):
    """Equipos de aliados y opciones de la guardada, p. ej. 'equipos 0135|2467; compartidas, diplomacia'."""
    with open(os.path.join(JUEGO, 'SAVES', guardada + '.SAV'), 'rb') as f:
        d = f.read()
    def rd(va, n):
        off = 0x6d
        for b, t in SAV_BLOQUES:
            if b <= va and va + n <= b + t:
                return d[off + va - b:off + va - b + n]
            off += t
    o = rd(0x53c38c, 0x2a)
    vivos = [c for c in range(8) if rd(0x536b30 + c * 0x1f8 + 1, 1)[0]]

    def equipos(tabla):   # tabla 0 = vigente (+0..7 de cada fila); 9 = propuestas (+9..16): el juego las vuelve
        out, vistos = [], set()   # vigentes al jugar cada color su turno (prueba del 16/10/2026)
        for c in vivos:
            if c in vistos:
                continue
            eq, pend = set(), [c]
            while pend:
                x = pend.pop()
                if x not in eq:
                    eq.add(x); pend += [y for y in vivos if y != x and rd(0x55ee4c + x * 56 + tabla + y, 1)[0] == 0
                                        and rd(0x55ee4c + y * 56 + tabla + x, 1)[0] == 0]
            vistos |= eq; out.append(''.join(map(str, sorted(eq))))
        return '|'.join(e for e in out if len(e) > 1)
    op = [n for n, v in (('compartidas', o[25] & 1), ('diplomacia', o[7] & 8)) if v]
    # Al guardar en el primer turno, los colores que todavía no jugaron tienen la alianza solo como propuesta
    # (Tanda_hex_alianzas del 21/10/2026: 013 vigente, 457 propuesta): se cuentan ambas.
    vig, prop = equipos(0), equipos(9)
    eqs = sorted({e for e in (vig + '|' + prop).split('|') if e}, key=lambda e: e[0])
    eqs = [e for e in eqs if not any(set(e) < set(o) for o in eqs)]
    eq = f'equipos {"|".join(eqs)}' if eqs else 'sin alianzas'
    return eq + ('; ' + ', '.join(op) if op else '')


def ahora():
    return time.strftime('%Y-%m-%d %H:%M:%S')


def leer(ruta, n):
    if not os.path.exists(ruta):
        return []
    with open(ruta, newline='') as f:
        return [[int(v) for v in r] for r in csv.reader(f) if len(r) == n]


def leer_batallas():
    """IA_BAT.CSV; el exe anterior a 1.0.33.0 no escribe colores_d (queda None)."""
    return leer(CSV_B, len(COL_B)) + [r + [None] for r in leer(CSV_B, len(COL_B) - 1)]


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
    t, f = leer(CSV_T, len(COL_T)), leer(CSV_F, len(COL_F))
    b = leer_batallas()
    db.executemany(f'insert into diplo values (?{", ?" * len(COL_D)})', [[pid] + r for r in leer(CSV_D, len(COL_D))])
    db.executemany(f'insert into evento values (?{", ?" * len(COL_E)})', [[pid] + r for r in leer(CSV_E, len(COL_E))])
    # ia_fin corre cada vez que se dibuja el cartel: vale el primer bloque (orden 1, 2, ...).
    corte = next((k for k, r in enumerate(f) if k and r[1] == 1), len(f)); f = f[:corte]
    v = leer(CSV_V, len(COL_V))
    if not f and v:   # victoria aliada: vale el primer cartel; orden y puestos como el podio (por PV)
        tabla = puestos([r for r in v if r[0] == v[0][0]], lambda r: r[3])
        f = [[r[0], k + 1, -1 if k and p == tabla[k - 1][0] else p] + r[1:] for k, (p, r) in enumerate(tabla)]
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
    for ruta in (CSV_T, CSV_B, CSV_F, CSV_D, CSV_E, CSV_V):
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
    c = configparser.ConfigParser(); c.read(CONFIG); c['Pantalla'] = {'preferida': ms[int(r) - 1][0]}
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


def devolver_sonido():
    """Windows recuerda el silencio de cada programa (Mezclador de volumen): si el juego queda silenciado al cerrarse,
    también arranca mudo en una partida normal (17/10/2026). El servicio de audio lo guarda en su memoria y lo vuelve
    a escribir en el registro al cerrarse el juego: borrarlo del registro no alcanza (medido el 17/10/2026). Solo
    sirve quitarlo con la sesión de audio viva, así que se abre el juego un momento, se le quita y se cierra.
    Se llama al terminar la tanda, después de escribir_ini sin [Tanda], para que el juego no cargue nada."""
    proc = None
    try:
        from pycaw.pycaw import AudioUtilities
        proc = subprocess.Popen([os.path.join(JUEGO, EXE)], cwd=JUEGO)
        # La sesión aparece recién cuando el juego abre el sonido, y Windows le aplica el silencio guardado un
        # momento después: se mira durante 8 s desde que aparece y se le quita cada vez que esté (medido el 17/10/2026).
        desde = None
        for _ in range(60):
            time.sleep(0.3)
            sesiones = [s for s in AudioUtilities.GetAllSessions() if s.ProcessId == proc.pid]
            if sesiones:
                desde = desde or time.time()
                if sesiones[0].SimpleAudioVolume.GetMute():
                    sesiones[0].SimpleAudioVolume.SetMute(0, None)
                if time.time() - desde > 8:
                    break
        if desde is None:
            print('  (no se pudo devolver el sonido del juego: no apareció su sesión de audio)', flush=True)
    except Exception as e:
        print(f'  (no se pudo devolver el sonido del juego: {e})', flush=True)
    finally:
        if proc and proc.poll() is None:
            proc.kill()
            proc.wait()


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


def equipos_de(texto):
    """Los equipos de un texto de alianzas(): 'equipos 0135|2467; ...' -> [{0, 1, 3, 5}, {2, 4, 6, 7}]."""
    if not texto or not texto.startswith('equipos '):
        return []
    return [set(map(int, e)) for e in texto.split()[1].rstrip(';').split('|')]


# Personalidades: 22 bits en +0xc0 del registro de jugador, uno por punto, en el orden del juego (Sagetext.tex);
# hallados con Tanda_hex_perfiles (TAREAS 38) y confirmados en el exe (ia\PENDIENTE-entrenamiento-ia.md, 25/10/2026).
PERFIL = 0xc0
PUNTOS = ['Strong', 'Very Strong', 'Herculean', 'Fast', 'Very Fast', 'Lightning', 'Informed', 'Farseeing', 'Heroic',
          'Legendary', 'Merchant', 'Famous', 'Renowned', 'Disciplined', 'Resolute', 'Immovable', 'Rich', 'Opulent',
          'Engineer', 'Artificer', 'Ceremonial', 'Devout']
# Guardada que arma cada partida con los perfiles rotados (sin "Tanda_": no aparece en la lista del Monitor).
ROTADA = 'IA_ROTADA'


def jugadores(d):
    """Offsets en el .SAV del registro de cada color que juega."""
    o = 0x6d + sum(t for _, t in SAV_BLOQUES[:3])
    return {c: o + c * 0x1f8 for c in range(8) if d[o + c * 0x1f8 + 1]}


def perfiles(guardada):
    """{color: bits de personalidad} de los colores que juegan."""
    with open(os.path.join(JUEGO, 'SAVES', guardada + '.SAV'), 'rb') as f:
        d = f.read()
    return {c: int.from_bytes(d[o + PERFIL:o + PERFIL + 3], 'little') for c, o in jugadores(d).items()}


def nombre_perfil(bits):
    return ' + '.join(n for i, n in enumerate(PUNTOS) if bits >> i & 1) or 'ninguno'


def escribir_rotada(guardada, origen):
    """SAVES\\IA_ROTADA.SAV: la guardada con el perfil de origen[c] en cada color c y sin alianzas."""
    with open(os.path.join(JUEGO, 'SAVES', guardada + '.SAV'), 'rb') as f:
        d = bytearray(f.read())
    pf = perfiles(guardada); js = jugadores(d)
    for c, o in js.items():
        d[o + PERFIL:o + PERFIL + 3] = pf[origen[c]].to_bytes(3, 'little')
    # Todos contra todos: la guardada puede traer alianzas de otra partida armada antes aunque la diplomacia esté
    # apagada (Tanda_hex_perfiles: 01457 aliados), y con eso el juego da victoria aliada al turno 3 (25/10/2026).
    # Se escribe guerra (1, como en Tanda_Kor) en las vigentes y en las propuestas.
    o = 0x6d + sum(t for _, t in SAV_BLOQUES[:3]) + 0x55ee4c - SAV_BLOQUES[3][0]
    for x in js:
        for y in js:
            if x != y:
                d[o + x * 56 + y] = d[o + x * 56 + 9 + y] = 1
    with open(os.path.join(JUEGO, 'SAVES', ROTADA + '.SAV'), 'wb') as f:
        f.write(d)


def plan(partidas, guardadas, alianzas_de=None):
    # Con equipos de aliados (specs\ia-alianzas-v1.md, req. 13) la IA se reparte por equipo: la primera partida de cada
    # par le da la IA de prueba a un equipo entero y la segunda al resto; de un par al siguiente de la misma guardada
    # cambia qué equipo va primero. Sin equipos, los PATRONES de siempre.
    # Guardada con perfiles distintos (ronda de personalidades): la misma IA (original) en todos, y en la partida i
    # cada color recibe el perfil del color que está i lugares después, así cada perfil pasa por cada ubicación.
    out = []
    if len(guardadas) == 1 and len(set((pf := perfiles(guardadas[0])).values())) > 1:
        cs = sorted(pf)
        return [{'guardada': guardadas[0], 'prueba': [],
                 'perfiles': {c: cs[(k + i) % len(cs)] for k, c in enumerate(cs)}} for i in range(partidas)]
    for i in range(partidas):
        par = i // 2
        g = guardadas[par % len(guardadas)]
        eqs = equipos_de((alianzas_de or {}).get(g))
        todos = set(range(8))
        if len(eqs) >= 2:
            pat = eqs[(par // len(guardadas)) % len(eqs)]
            todos = set().union(*eqs)   # en mapas de menos de 8 bandos (Hexagon) no nombrar colores que no juegan
        else:
            pat = set(PATRONES[(par // len(guardadas)) % len(PATRONES)])
        out.append({'guardada': g, 'prueba': sorted(pat if i % 2 == 0 else todos - pat)})
    return out


def jugar(db, tid, n, p, a):
    asign = ''.join('P' if c in p['prueba'] else 'O' for c in range(8))
    # perfiles: {color: color de la guardada cuyo perfil recibe}; el json vuelve con claves de texto
    origen = {int(c): o for c, o in p.get('perfiles', {}).items()}
    pid = db.execute('insert into partida (tanda, n, guardada, asignacion, perfiles, inicio, estado) '
                     'values (?,?,?,?,?,?,?)', (tid, n, p['guardada'], asign, json.dumps(origen) if origen else None,
                                               ahora(), 'jugando')).lastrowid
    db.commit()
    if origen:
        escribir_rotada(p['guardada'], origen)
        print(f'[{ahora()}] partida {n + 1}: {p["guardada"]}, perfiles ' +
              ', '.join(f'{COLORES[c]} <- {COLORES[o]}' for c, o in origen.items()), flush=True)
    else:
        print(f'[{ahora()}] partida {n + 1}: {p["guardada"]}, colores con IA de prueba {p["prueba"]} ({asign})',
              flush=True)
    escribir_ini(set(p['prueba']), ROTADA if origen else p['guardada'])
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
        if any(os.path.exists(r) and os.path.getsize(r) > 0 for r in (CSV_F, CSV_V)):
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
    if proc.poll() is None:
        silenciar(proc.pid, False)   # que no quede silenciado para una partida normal
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
        devolver_sonido()


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
    cols = [r[1] for r in db.execute('pragma table_info(tanda)')]
    for c in ('parche', 'exe', 'bandos', 'alianzas'):   # bases anteriores al registro de parche, bandos y alianzas
        if c not in cols:
            db.execute(f'alter table tanda add column {c} text')
    if 'perfiles' not in [r[1] for r in db.execute('pragma table_info(partida)')]:   # bases anteriores al 25/10/2026
        db.execute('alter table partida add column perfiles text')
    if 'colores_d' not in [r[1] for r in db.execute('pragma table_info(batalla)')]:   # bases anteriores a 1.0.33.0
        db.execute('alter table batalla add column colores_d integer')
    ver, exe = parche_actual()
    # Partida que quedó "jugando" porque se cerró la ventana de la tanda: sus registros son suyos y se retoma.
    for (pid,) in db.execute("select id from partida where estado='jugando'").fetchall():
        importar(db, pid, 'cortada')
        print(f'Partida {pid} había quedado a medias: guardada como "cortada", se vuelve a jugar al retomar.')
    if any(os.path.exists(r) for r in (CSV_T, CSV_B, CSV_F, CSV_D, CSV_E, CSV_V)):   # registros de una partida a mano: no se pierden
        pid = db.execute('insert into partida (guardada, inicio, estado) values (?,?,?)',
                         ('(a mano)', ahora(), 'suelta')).lastrowid
        importar(db, pid, 'suelta')
        print(f'Registros sueltos de una partida anterior guardados como partida {pid} (estado "suelta").')
    if a.accion == 'nueva':
        gs = a.guardadas.split(',')
        faltan = [g for g in gs if not os.path.exists(os.path.join(JUEGO, 'SAVES', g + '.SAV'))]
        if faltan:
            sys.exit(f'No existen en {JUEGO}\\SAVES: {", ".join(g + ".SAV" for g in faltan)}')
        bs = {g: bandos(g) for g in gs}
        print('Bandos: ' + ', '.join(f'{g.removeprefix("Tanda_")} {b}' for g, b in bs.items()), flush=True)
        al = {g: alianzas(g) for g in gs}
        print('Alianzas: ' + ', '.join(f'{g.removeprefix("Tanda_")} {v}' for g, v in al.items()), flush=True)
        tid = db.execute('insert into tanda (inicio, plan, parche, exe, bandos, alianzas) values (?,?,?,?,?,?)',
                         (ahora(), json.dumps(plan(a.partidas, gs, al)), ver, exe, json.dumps(bs),
                          json.dumps(al, ensure_ascii=False))).lastrowid
        db.commit()
    else:
        # Solo la última tanda: una vieja abandonada (por ejemplo, de pruebas) no se retoma por sorpresa.
        r = db.execute('select id, terminada, parche, exe from tanda order by id desc').fetchone()
        if not r or r[1]:
            sys.exit('La última tanda ya terminó: no hay nada que retomar.')
        if r[3] and r[3] != exe:
            sys.exit(f'La tanda {r[0]} se empezó con vista-aliada {r[2]} (exe {r[3]}) y ahora está instalado {ver} '
                     f'(exe {exe}): sus partidas no serían comparables. Empezá una tanda nueva.')
        tid = r[0]
    return db, tid


if __name__ == '__main__':
    main()
