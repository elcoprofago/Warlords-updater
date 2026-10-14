# Monitor de IA: panel de control de las tandas de ia\tanda.py (ia\PENDIENTE-monitor-ia.md).
# Corre la tanda en un hilo propio (reemplaza tanda.bat y monitor.bat) y muestra en vivo la partida en curso, leyendo
# ia\datos.db y los CSV que escribe DarklordAV.exe. Se empaqueta con build.py como ia\Monitor-IA.exe.
import ctypes, io, json, os, queue, subprocess, sys, threading, time, winsound
import tkinter as tk
from tkinter import messagebox, ttk
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import informe, tanda   # noqa: E402

ALARMA = r'C:\Windows\Media\Alarm01.wav'
CUELGUE_MIN = 10           # minutos sin turnos nuevos para dar la partida por colgada (tanda.py --cuelgue)
AVISO_MIN = 5              # a partir de acá se avisa de un posible cuelgue
IAS = {0: 'original', 1: 'prueba'}


def juego_abierto():
    r = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {tanda.EXE}', '/NH'], capture_output=True, text=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    return tanda.EXE.lower() in r.stdout.lower()


class Salida(io.TextIOBase):
    """Lo que tanda.py imprime va a la bitácora del panel."""
    def __init__(self, cola):
        self.cola = cola

    def write(self, s):
        self.cola.put(s)
        return len(s)


class Monitor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Monitor de IA')
        self.geometry('900x720')
        self.cola = queue.Queue()
        sys.stdout = sys.stderr = Salida(self.cola)
        self.hilo = None
        self.tid = None
        self.externa = False   # tanda arrancada fuera del panel (python ia	anda.py): solo se mira
        self.armar()
        self.refrescar()

    # ---- interfaz ----
    def armar(self):
        pad = dict(padx=8, pady=4)
        f = ttk.LabelFrame(self, text='Tanda'); f.pack(fill='x', **pad)
        self.v_tanda = tk.StringVar(); ttk.Label(f, textvariable=self.v_tanda, font=('Segoe UI', 11, 'bold')) \
            .grid(row=0, column=0, columnspan=8, sticky='w', **pad)
        ttk.Label(f, text='Partidas:').grid(row=1, column=0, sticky='e')
        self.v_partidas = tk.IntVar(value=6)
        ttk.Spinbox(f, from_=1, to=200, width=5, textvariable=self.v_partidas).grid(row=1, column=1, sticky='w')
        ttk.Label(f, text='Guardadas:').grid(row=1, column=2, sticky='e')
        self.v_guardadas = tk.StringVar(value='Tanda_Scarpart,Tanda_Borderlands,Tanda_Kor')
        ttk.Entry(f, width=42, textvariable=self.v_guardadas).grid(row=1, column=3, sticky='w')
        self.b_nueva = ttk.Button(f, text='Nueva tanda', command=lambda: self.arrancar('nueva'))
        self.b_seguir = ttk.Button(f, text='Retomar', command=lambda: self.arrancar('seguir'))
        self.b_cortar = ttk.Button(f, text='Cortar', command=self.cortar)
        for k, b in enumerate((self.b_nueva, self.b_seguir, self.b_cortar)):
            b.grid(row=1, column=4 + k, **pad)

        c = ttk.LabelFrame(self, text='Controles'); c.pack(fill='x', **pad)
        self.v_mudo = tk.BooleanVar(value=True)
        ttk.Checkbutton(c, text='Sonido del juego desactivado', variable=self.v_mudo,
                        command=lambda: tanda.CONTROL.update(silenciar=self.v_mudo.get())).grid(row=0, column=0, **pad)
        self.v_alarma = tk.BooleanVar(value=True)
        ttk.Checkbutton(c, text='Alarma al terminar la tanda', variable=self.v_alarma).grid(row=0, column=1, **pad)
        ttk.Button(c, text='Probar alarma', command=self.alarma).grid(row=0, column=2, **pad)
        ttk.Label(c, text='Monitor del juego:').grid(row=0, column=3, sticky='e')
        self.mons = tanda.monitores()
        nombres = [f'{m[0]} ({m[3]}x{m[4]}){" principal" if m[5] else ""}' for m in self.mons]
        self.v_mon = tk.StringVar()
        cb = ttk.Combobox(c, state='readonly', width=30, values=nombres, textvariable=self.v_mon)
        pref = tanda.monitor_configurado()[0]
        cb.current(next((i for i, m in enumerate(self.mons) if m[0] == pref), 0))
        cb.bind('<<ComboboxSelected>>', lambda e: self.guardar_monitor(cb.current()))
        cb.grid(row=0, column=4, **pad)

        p = ttk.LabelFrame(self, text='Partida en curso'); p.pack(fill='x', **pad)
        self.v_partida = tk.StringVar(); ttk.Label(p, textvariable=self.v_partida, justify='left') \
            .pack(anchor='w', **pad)
        self.l_cuelgue = ttk.Label(p, foreground='#b00000'); self.l_cuelgue.pack(anchor='w', padx=8)
        cols = ('color', 'ia', 'estado', 'pv', 'ciudades', 'oro', 'ejercitos', 'heroes')
        self.tabla = ttk.Treeview(p, columns=cols, show='headings', height=8)
        for k, t in zip(cols, ('Color', 'IA', 'Estado', 'PV', 'Ciudades', 'Oro', 'Ejércitos', 'Héroes')):
            self.tabla.heading(k, text=t); self.tabla.column(k, width=90, anchor='center')
        self.tabla.tag_configure('prueba', background='#e4f0ff')
        self.tabla.pack(fill='x', **pad)

        b = ttk.LabelFrame(self, text='Bitácora e informe'); b.pack(fill='both', expand=True, **pad)
        self.log = tk.Text(b, height=12, font=('Consolas', 9), wrap='none')
        sb = ttk.Scrollbar(b, command=self.log.yview); self.log['yscrollcommand'] = sb.set
        sb.pack(side='right', fill='y'); self.log.pack(fill='both', expand=True)
        self.protocol('WM_DELETE_WINDOW', self.salir)

    def guardar_monitor(self, i):
        import configparser
        c = configparser.ConfigParser(); c['Pantalla'] = {'preferida': self.mons[i][0]}
        with open(tanda.CONFIG, 'w') as f:
            c.write(f)
        print(f'Monitor del juego: {self.mons[i][0]} (vale desde la próxima vuelta de la espera).')

    # ---- tanda ----
    def corriendo(self):
        return self.hilo is not None and self.hilo.is_alive()

    def arrancar(self, accion):
        if self.corriendo():
            return
        a = SimpleNamespace(accion=accion, partidas=self.v_partidas.get(), guardadas=self.v_guardadas.get(),
                            tope_turnos=0, cuelgue=CUELGUE_MIN)
        tanda.CORTAR.clear()
        tanda.CONTROL['silenciar'] = self.v_mudo.get()
        self.hilo = threading.Thread(target=self.trabajar, args=(a,), daemon=True)
        self.hilo.start()

    def trabajar(self, a):
        # Mantener la PC despierta mientras corre: si Windows suspende, la tanda se corta.
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)   # ES_CONTINUOUS | SYSTEM_REQUIRED
        try:
            db, self.tid = tanda.preparar(a)
            tanda.correr(db, self.tid, a)
            terminada = db.execute('select terminada from tanda where id=?', (self.tid,)).fetchone()[0]
            print()
            informe.main(self.tid)
            if terminada and self.v_alarma.get():
                self.alarma()
        except SystemExit as e:
            print(e)
        except Exception as e:
            print(f'Error: {e!r}')
        finally:
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)

    def cortar(self):
        if self.corriendo() and messagebox.askyesno(
                'Cortar', 'Se cierra el juego y la partida en curso se vuelve a jugar al retomar. ¿Cortar?'):
            tanda.CORTAR.set()
            print('Cortando…')

    def alarma(self):
        threading.Thread(target=lambda: [winsound.PlaySound(ALARMA, winsound.SND_FILENAME) for _ in range(3)],
                         daemon=True).start()

    def salir(self):
        if not self.corriendo():
            return self.destroy()
        if messagebox.askyesno('Salir', 'Hay una tanda corriendo. ¿Cortarla y salir? Se retoma con "Retomar".'):
            tanda.CORTAR.set()
            self.after(500, self.esperar_y_salir)

    def esperar_y_salir(self):
        if self.corriendo():
            return self.after(500, self.esperar_y_salir)
        self.destroy()

    # ---- vista en vivo ----
    def refrescar(self):
        while not self.cola.empty():
            self.log.insert('end', self.cola.get()); self.log.see('end')
        try:
            self.mostrar()
        except Exception as e:   # el juego puede estar escribiendo los CSV justo ahora
            self.v_partida.set(f'(no se pudo leer el estado: {e})')
        corre = self.corriendo() or self.externa
        for b in (self.b_nueva, self.b_seguir):
            b.state(['disabled'] if corre else ['!disabled'])
        self.b_cortar.state(['!disabled'] if self.corriendo() else ['disabled'])
        self.after(2000, self.refrescar)

    def mostrar(self):
        import sqlite3
        self.externa = False
        if not os.path.exists(tanda.DB):
            self.v_tanda.set('Sin tandas todavía.'); return
        db = sqlite3.connect(tanda.DB)
        t = db.execute('select id, inicio, plan, terminada from tanda order by id desc limit 1').fetchone()
        if not t:
            self.v_tanda.set('Sin tandas todavía.'); return
        tid, inicio, plan, term = t
        total = len(json.loads(plan))
        parts = db.execute('select n, guardada, asignacion, inicio, fin, estado, turnos from partida where tanda=? '
                           'order by id', (tid,)).fetchall()
        validas = [p for p in parts if p[5] != 'cortada']
        en_curso = next((p for p in reversed(parts) if p[5] == 'jugando'), None)
        hechas = [p for p in validas if p[5] != 'jugando']
        self.externa = bool(en_curso) and not self.corriendo() and juego_abierto()
        estado = ('terminada' if term else 'corriendo' if self.corriendo() else
                  'corriendo fuera del Monitor' if self.externa else 'detenida')
        txt = f'Tanda {tid} ({estado}) — desde {inicio} — {len(hechas)} de {total} partidas terminadas'
        if en_curso:
            txt += f' — jugando la {en_curso[0] + 1}.ª'
        dur = [time.mktime(time.strptime(p[4], '%Y-%m-%d %H:%M:%S')) -
               time.mktime(time.strptime(p[3], '%Y-%m-%d %H:%M:%S')) for p in hechas if p[3] and p[4]]
        if dur and not term:
            fin = time.time() + sum(dur) / len(dur) * (total - len(hechas))
            txt += f' — fin estimado {time.strftime("%H:%M", time.localtime(fin))}'
        self.v_tanda.set(txt)

        if not en_curso:
            self.v_partida.set('Ninguna partida en curso.' + ''.join(
                f'\n  {p[0] + 1}. {p[1]}: {p[5]}, {p[6] or 0} turnos' for p in hechas[-5:]))
            self.l_cuelgue['text'] = ''
            self.tabla.delete(*self.tabla.get_children())
            return
        n, guardada, asig, ini = en_curso[:4]
        filas = tanda.leer(tanda.CSV_T, len(tanda.COL_T))
        bats = tanda.leer(tanda.CSV_B, len(tanda.COL_B))
        turno = max((r[0] for r in filas), default=0)
        prueba = [c for c in range(8) if asig[c] == 'P']
        res = {ia: [0, 0] for ia in (0, 1)}
        for r in bats:
            res.setdefault(r[7], [0, 0])[0 if r[6] == 1 else 1] += 1
        bt = '   '.join(f'IA {IAS.get(ia, ia)}: {g} ganadas / {p} perdidas' for ia, (g, p) in res.items())
        self.v_partida.set(f'Partida {n + 1}: {guardada.removeprefix("Tanda_")} — turno {turno} — empezó {ini[11:]}\n'
                           f'Colores con la IA de prueba: {", ".join(map(str, prueba))}\n'
                           f'Batallas atacando ({len(bats)}): {bt}')
        quieto = time.time() - os.path.getmtime(tanda.CSV_T) if os.path.exists(tanda.CSV_T) else \
            time.time() - time.mktime(time.strptime(ini, '%Y-%m-%d %H:%M:%S'))
        self.l_cuelgue['text'] = (f'Sin turnos nuevos hace {quieto / 60:.0f} min: posible cuelgue '
                                  f'(se corta sola a los {CUELGUE_MIN} min).') if quieto > AVISO_MIN * 60 else ''
        ultimo = {}
        for r in filas:
            ultimo[r[1]] = dict(zip(tanda.COL_T, r))
        self.tabla.delete(*self.tabla.get_children())
        for c in sorted(ultimo):
            u = ultimo[c]
            vivo = u['vivo'] and u['turno'] >= turno - 1
            self.tabla.insert('', 'end', tags=('prueba',) if u['ia'] == 1 else (), values=(
                c, IAS.get(u['ia'], u['ia']), 'vivo' if vivo else 'eliminado',
                tanda.pv_calc(u['ciudades'], u['heroes'], u['oro']) if vivo else 0,
                # de un eliminado, IA.CSV guarda lo que tenía en su último turno vivo: no vale mostrarlo
                *((u['ciudades'], u['oro'], u['ejercitos'], u['heroes']) if vivo else ('—',) * 4)))


if __name__ == '__main__':
    Monitor().mainloop()
