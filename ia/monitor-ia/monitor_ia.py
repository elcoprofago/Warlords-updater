# Monitor de IA: panel de control de las tandas de ia\tanda.py (ia\PENDIENTE-monitor-ia.md).
# Corre la tanda en un hilo propio (reemplaza tanda.bat y monitor.bat) y muestra en vivo la partida en curso, leyendo
# ia\datos.db y los CSV que escribe DarklordAV.exe. Se empaqueta con build.py como ia\Monitor-IA.exe.
import configparser, ctypes, io, json, os, queue, sqlite3, subprocess, sys, threading, time, urllib.request, winsound
import tkinter as tk
import psutil
from PIL import Image, ImageTk
from tkinter import messagebox, ttk
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import informe, tanda   # noqa: E402

VERSION = '1.0.7'                 # sube con cada release; publicar.py la exige igual a la etiqueta v<VERSION>
REPO = 'elcoprofago/Monitor-IA'   # repo pÃºblico donde se publican las releases del .exe
ALARMA = r'C:\Windows\Media\Alarm01.wav'
CUELGUE_MIN = 10           # minutos sin turnos nuevos para dar la partida por colgada (tanda.py --cuelgue)
AVISO_MIN = 5              # a partir de acÃ¡ se avisa de un posible cuelgue
IAS = {0: 'original', 1: 'prueba'}


def juego_abierto():
    r = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {tanda.EXE}', '/NH'], capture_output=True, text=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    return tanda.EXE.lower() in r.stdout.lower()


# CÃ­rculo de consumo (CPU o RAM de toda la PC), con las imÃ¡genes y los cortes de semÃ¡foro de USBagent
# (tools/usbagent-hub/Controls/PerfCircle.xaml.cs): <30 % / 30-69 % / >=70 %, tres imÃ¡genes por franja.
ASSETS = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))), 'assets')


class Medidor:
    TAM = 26   # como la ruedita

    def __init__(self, mon, padre, nombre):
        self.mon, self.nombre = mon, nombre
        marco = Image.open(os.path.join(ASSETS, 'marco.png')).convert('RGBA')
        self.imgs = []
        for i in range(1, 10):
            c = Image.open(os.path.join(ASSETS, f'circle_{i:02}.png')).convert('RGBA')
            c.alpha_composite(marco.resize(c.size))
            self.imgs.append(c.resize((self.TAM, self.TAM), Image.LANCZOS))
        self.caja = mon.caja(padre)
        self.l_img = mon.icono(self.caja, self.imgs[0]); self.l_img.pack()
        self.l_txt = mon.rotulo(self.caja, text=f'{nombre} 0%', font=('Segoe UI', 7)); self.l_txt.pack()

    def poner(self, pct):
        if pct < 30:
            banda, pos = 0, pct / 30
        elif pct < 70:
            banda, pos = 1, (pct - 30) / 40
        else:
            banda, pos = 2, (pct - 70) / 30
        i = banda * 3 + min(2, max(0, round(pos * 2)))
        self.mon.iconos[self.l_img] = self.imgs[i]; self.mon.pintar_icono(self.l_img)
        self.l_txt['text'] = f'{self.nombre} {pct:.0f}%'


def leer_config(seccion):
    c = configparser.ConfigParser(); c.read(tanda.CONFIG)
    return dict(c[seccion]) if c.has_section(seccion) else {}


def guardar_config(seccion, **valores):
    """Cambia una secciÃ³n de tanda.ini sin tocar las demÃ¡s (Pantalla la usa tambiÃ©n tanda.py)."""
    c = configparser.ConfigParser(); c.read(tanda.CONFIG)
    c[seccion] = valores
    with open(tanda.CONFIG, 'w') as f:
        c.write(f)


def version_tupla(v):
    return tuple(int(x) for x in v.split('.'))


def version_de(exe):
    """La versiÃ³n que trae adentro un Monitor-IA.exe (se la pregunta con --version; lo usa tambiÃ©n publicar.py)."""
    marca = exe + '.version'
    subprocess.run([exe, '--version', marca], timeout=120, creationflags=subprocess.CREATE_NO_WINDOW)
    with open(marca) as f:
        v = f.read().strip()
    os.remove(marca)
    return v


class Ayuda:
    """Cartelito que aparece al pasar el mouse sobre un widget."""
    def __init__(self, w, texto):
        self.w, self.texto, self.v = w, texto, None
        w.bind('<Enter>', self.mostrar, add='+'); w.bind('<Leave>', self.ocultar, add='+')

    def mostrar(self, e):
        self.v = tk.Toplevel(self.w); self.v.wm_overrideredirect(True)
        self.v.geometry(f'+{e.x_root + 12}+{e.y_root + 14}')
        tk.Label(self.v, text=self.texto, bg='#ffffe0', relief='solid', bd=1, font=('Segoe UI', 8),
                 padx=4).pack()

    def ocultar(self, e):
        if self.v:
            self.v.destroy(); self.v = None


class Salida(io.TextIOBase):
    """Lo que tanda.py imprime va a la bitÃ¡cora del panel."""
    def __init__(self, cola):
        self.cola = cola

    def write(self, s):
        self.cola.put(s)
        return len(s)


class Monitor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f'Banco de pruebas de la IA â€” Monitor {VERSION}')
        self.geometry('740x760')
        self.cola = queue.Queue()
        sys.stdout = sys.stderr = Salida(self.cola)
        self.hilo = None
        self.tid = None
        self.retomable = False
        self.progreso = [('tanda', None, 'â€”', False), ('partida', None, 'â€”', False)]
        self.externa = False   # tanda arrancada fuera del panel (python ia/tanda.py): solo se mira
        self.armar()
        self.aplicar_fondo()
        self.refrescar()

    # ---- interfaz ----
    # Los paneles son tk (no ttk) para poder mostrar la textura: cada caja y cada rÃ³tulo lleva de imagen el recorte
    # del mosaico que cae en su lugar de la ventana, asÃ­ se ve continua detrÃ¡s de todo (repintar).
    def caja(self, padre, titulo=None, borde=False):
        f = tk.Frame(padre, bd=0, highlightthickness=1 if borde else 0, highlightbackground='#8a8a8a')
        fondo = tk.Label(f, bd=0, highlightthickness=0); fondo.place(x=0, y=0, relwidth=1, relheight=1)
        self.cajas.append((f, fondo))
        if titulo:
            self.rotulo(f, text=titulo, font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=6, pady=(3, 0))
        return f

    def panel(self, padre, titulo):
        """Caja con tÃ­tulo y flechita â–¼/â–¶ para plegarla (como en GPUmon). Devuelve (recuadro, contenido)."""
        caja = self.caja(padre, borde=True)
        cab = self.caja(caja); cab.pack(fill='x', padx=6, pady=(3, 0))
        self.rotulo(cab, text=titulo, font=('Segoe UI', 10, 'bold')).pack(side='left')
        cuerpo = self.caja(caja)
        flecha = tk.Button(cab, text='â–¼', font=('Segoe UI', 7), width=2, padx=0, pady=0, relief='solid', bd=1,
                           cursor='hand2', takefocus=False, command=lambda: self.plegar(caja, cuerpo, flecha))
        flecha.pack(side='left', padx=(6, 0)); self.flechas.append(flecha)
        cuerpo.pack(fill='both', expand=True)
        pie = self.caja(caja); pie.configure(height=3); pie.pack(fill='x')   # aire bajo el tÃ­tulo plegado
        cuerpo.pie = pie
        return caja, cuerpo

    def plegar(self, caja, cuerpo, flecha):
        self.update_idletasks()
        antes = self.winfo_reqheight()
        plegar = bool(cuerpo.winfo_manager())
        if plegar:
            cuerpo.pack_forget()
        else:
            cuerpo.pack(fill='both', expand=True, before=cuerpo.pie)
        flecha['text'] = 'â–¶' if plegar else 'â–¼'
        if caja is self.p_bitacora:   # plegada, la bitÃ¡cora deja de absorber el alto sobrante
            caja.pack_configure(fill='x', expand=False) if plegar else caja.pack_configure(fill='both', expand=True)
        self.update_idletasks()
        alto = max(200, self.winfo_height() + self.winfo_reqheight() - antes)
        if plegar:   # si la ventana era mÃ¡s baja que lo pedido, restar la diferencia la achica de mÃ¡s y se solapan
            alto = max(alto, self.winfo_reqheight())
        self.geometry(f'{self.winfo_width()}x{alto}')

    def rotulo(self, padre, **kw):
        kw.setdefault('font', ('Segoe UI', 10))
        l = tk.Label(padre, bd=0, highlightthickness=0, padx=0, pady=0, compound='center', **kw)
        self.rotulos.append(l)
        return l

    def icono(self, padre, img, **kw):
        l = tk.Label(padre, bd=0, highlightthickness=0, padx=0, pady=0, **kw)
        self.iconos[l] = img
        return l

    def boton(self, padre, nombre, accion, tam=58):
        imgs = {e: Image.open(os.path.join(ASSETS, f'{nombre}_{e}.png')).convert('RGBA').resize((tam, tam), Image.LANCZOS)
                for e in ('on', 'off')}
        l = self.icono(padre, imgs['off'], cursor='hand2')
        l.imgs, l.activo = imgs, False

        def clic(e):
            if l.activo:
                accion()
        l.bind('<Button-1>', clic)
        return l

    def encender(self, l, si):
        """Enciende el botÃ³n cuadrado si se puede apretar ahora; apagado no responde al clic."""
        if l.activo != si:
            l.activo = si
            self.iconos[l] = l.imgs['on' if si else 'off']
            l['cursor'] = 'hand2' if si else 'arrow'
            self.pintar_icono(l)

    def check(self, padre, texto, var, command=None):
        f = self.caja(padre)
        c = tk.Checkbutton(f, variable=var, command=command, bd=0, highlightthickness=0, padx=0, pady=0)
        c.pack(side='left'); self.checks.append(c)
        r = self.rotulo(f, text=' ' + texto, cursor='hand2'); r.pack(side='left')
        r.bind('<Button-1>', lambda e: c.invoke())
        return f

    def armar(self):
        pad = dict(padx=8, pady=4)
        self.cajas, self.rotulos, self.iconos, self.checks, self.fotos, self.flechas = [], [], {}, [], {}, []
        self.mosaico, self.base, self.tinta = None, '#f0f0f0', '#000000'
        self.fondo = tk.Label(self, bd=0); self.fondo.place(x=0, y=0, relwidth=1, relheight=1)
        arriba = self.caja(self); arriba.pack(fill='x')
        tarjeta = self.caja(arriba, borde=True); tarjeta.pack(side='right', anchor='n', padx=(0, 8), pady=(10, 0))
        semaforos = self.caja(tarjeta); semaforos.pack(padx=(4, 30), pady=(4, 0))   # aire para la ruedita
        # Interruptor de suspensiÃ³n (la ficha on/off translÃºcida de MovilCode), a la izquierda de los semÃ¡foros:
        # encendido, la PC se suspende al terminar la tanda.
        fs = self.caja(semaforos); fs.pack(side='left', padx=(4, 8))
        self.suspender = leer_config('Suspension').get('activa') == 'si'
        self.imgs_susp = {e: Image.open(os.path.join(ASSETS, f'suspender_{e}.png')).convert('RGBA')
                          .resize((25, 39), Image.LANCZOS) for e in ('on', 'off')}
        self.b_susp = self.icono(fs, self.imgs_susp['on' if self.suspender else 'off'], cursor='hand2')
        self.b_susp.pack(); self.b_susp.bind('<Button-1>', lambda e: self.alternar_suspension())
        Ayuda(self.b_susp, 'modo sleep')
        self.medidores = [Medidor(self, semaforos, 'CPU'), Medidor(self, semaforos, 'RAM')]
        for m in self.medidores:
            m.caja.pack(side='left', padx=8)
        # Botones cuadrados iluminados (como los de USBagent): encendido = se puede apretar ahora.
        botonera = self.caja(tarjeta); botonera.pack(padx=4, pady=6)
        self.b_nueva = self.boton(botonera, 'nueva', lambda: self.arrancar('nueva'))
        self.b_seguir = self.boton(botonera, 'retomar', lambda: self.arrancar('seguir'))
        self.b_cortar = self.boton(botonera, 'cortar', self.cortar)
        for b in (self.b_nueva, self.b_seguir, self.b_cortar):
            b.pack(side='left', padx=2)
        # Progreso de la tanda y de la partida en curso, estilo terminal (fondo oscuro, barra con resto rayado).
        self.barras = tk.Canvas(tarjeta, width=190, height=50, bg='#0d1512', highlightthickness=1,
                                highlightbackground='#3f8f6a', bd=0)
        self.barras.pack(padx=6, pady=(0, 6))
        rueda = Image.open(os.path.join(ASSETS, 'rueda1.png')).convert('RGBA').resize((26, 25), Image.LANCZOS)
        # En el Ã¡ngulo superior derecho de la tarjeta, al costado de los cÃ­rculos.
        b = self.icono(tarjeta, rueda, cursor='hand2'); b.place(relx=1, x=-4, y=4, anchor='ne')
        b.bind('<Button-1>', lambda e: self.configurar())
        caja, f = self.panel(arriba, 'Tanda'); caja.pack(side='left', fill='x', expand=True, anchor='n', **pad)
        self.v_tanda = tk.StringVar(); self.v_tanda2 = tk.StringVar(); self.v_parche = tk.StringVar(); self.v_todas = tk.StringVar()
        self.rotulo(f, textvariable=self.v_tanda, font=('Segoe UI', 11, 'bold')).pack(anchor='w', padx=8, pady=(4, 0))
        self.rotulo(f, textvariable=self.v_tanda2).pack(anchor='w', padx=8, pady=(2, 0))
        fp = self.caja(f); fp.pack(anchor='w', padx=8, pady=(2, 0))
        for i, (txt, var) in enumerate((('Parche de esta tanda: ', self.v_parche), ('Todas las tandas: ', self.v_todas))):
            self.rotulo(fp, text=txt).grid(row=i, column=0, sticky='nw')
            self.rotulo(fp, textvariable=var, font=('Consolas', 9), justify='left', anchor='w',
                        wraplength=330).grid(row=i, column=1, sticky='w')
        fila = self.caja(f); fila.pack(anchor='w', **pad)
        self.rotulo(fila, text='Partidas:').grid(row=0, column=0, sticky='w')
        self.v_partidas = tk.IntVar(value=6)
        ttk.Spinbox(fila, from_=1, to=500, width=5, textvariable=self.v_partidas).grid(row=0, column=1, sticky='w',
                                                                                     padx=6, pady=2)
        self.rotulo(fila, text='Guardadas:').grid(row=1, column=0, sticky='w')
        # Todas las Tanda_*.SAV sin alianzas (las del rating), hasta que se elija otra cosa: las de alianzas (etapa 3)
        # se marcan a mano para no mezclarlas en un rating.
        self.guardadas = [g for g in self.disponibles() if not self.con_alianzas(g)]
        self.b_guardadas = ttk.Button(fila, width=34, command=self.elegir_guardadas)
        self.b_guardadas.grid(row=1, column=1, sticky='w', padx=6, pady=2); self.rotular_guardadas()
        self.rotulo(fila, text='EstadÃ­sticas:').grid(row=2, column=0, sticky='w')
        ttk.Button(fila, text='Exportar PDF de un mapaâ€¦', width=34,
                   command=self.exportar_pdf).grid(row=2, column=1, sticky='w', padx=6, pady=2)
        caja, c = self.panel(self, 'Controles'); caja.pack(fill='x', **pad)
        c = self.caja(c); c.pack(anchor='w')
        self.v_mudo = tk.BooleanVar(value=True)
        self.check(c, 'Sonido del juego desactivado', self.v_mudo,
                   lambda: tanda.CONTROL.update(silenciar=self.v_mudo.get())).grid(row=0, column=0, sticky='w', **pad)
        self.v_alarma = tk.BooleanVar(value=True)
        self.check(c, 'Alarma al terminar la tanda', self.v_alarma).grid(row=0, column=1, sticky='w', **pad)
        # Serie programada: al terminar una tanda arranca sola la siguiente, con las mismas guardadas y partidas,
        # hasta completar las de la serie (alarma y suspensiÃ³n, solo al final).
        self.v_auto = tk.BooleanVar(value=False)
        fa = self.caja(c); fa.grid(row=2, column=0, columnspan=2, sticky='w', **pad)
        self.check(fa, 'Tandas automatizadas', self.v_auto).pack(side='left')
        self.rotulo(fa, text='   serie de').pack(side='left')
        self.v_serie = tk.IntVar(value=3)
        ttk.Spinbox(fa, from_=2, to=50, width=4, textvariable=self.v_serie).pack(side='left', padx=4)
        self.rotulo(fa, text='tandas').pack(side='left')
        self.rotulo(c, text='Monitor del juego:').grid(row=1, column=0, sticky='w', **pad)
        self.mons = tanda.monitores()
        nombres = [f'{m[0]} ({m[3]}x{m[4]}){" principal" if m[5] else ""}' for m in self.mons]
        self.v_mon = tk.StringVar()
        cb = ttk.Combobox(c, state='readonly', width=30, values=nombres, textvariable=self.v_mon)
        pref = tanda.monitor_configurado()[0]
        cb.current(next((i for i, m in enumerate(self.mons) if m[0] == pref), 0))
        cb.bind('<<ComboboxSelected>>', lambda e: self.guardar_monitor(cb.current()))
        cb.grid(row=1, column=1, sticky='w', **pad)

        caja, p = self.panel(self, 'Partida en curso'); caja.pack(fill='x', **pad)
        self.info = tk.Text(p, height=5, font=('Segoe UI', 10), bg='#f4f8ff', relief='flat', wrap='word',
                            padx=8, pady=6, cursor='arrow')
        for tag, kw in (('titulo', dict(font=('Segoe UI', 13, 'bold'), foreground='#123c7a')),
                        ('b', dict(font=('Segoe UI', 10, 'bold'))),
                        ('prueba', dict(font=('Segoe UI', 10, 'bold'), foreground='#0b5ed7')),
                        ('original', dict(font=('Segoe UI', 10, 'bold'), foreground='#b35c00')),
                        ('gana', dict(font=('Segoe UI', 10, 'bold'), foreground='#1a7f37')),
                        ('pierde', dict(font=('Segoe UI', 10, 'bold'), foreground='#c62828')),
                        ('gris', dict(foreground='#666666'))):
            self.info.tag_configure(tag, **kw)
        self.info.pack(fill='x', **pad)
        self.l_cuelgue = tk.Label(p, foreground='white', background='#c62828', font=('Segoe UI', 10, 'bold'))
        cols = ('color', 'ia', 'estado', 'pv', 'ciudades', 'oro', 'ejercitos', 'heroes')
        self.tabla = ttk.Treeview(p, columns=cols, show='headings', height=8)
        for k, t in zip(cols, ('Color', 'IA', 'Estado', 'PV', 'Ciudades', 'Oro', 'EjÃ©rcitos', 'HÃ©roes')):
            self.tabla.heading(k, text=t); self.tabla.column(k, width=76, anchor='center')
        ttk.Style(self).configure('Treeview.Heading', font=('Segoe UI', 9, 'bold'))
        self.tabla.tag_configure('prueba', background='#dbe9ff', foreground='#0b3d91')
        self.tabla.tag_configure('original', background='#ffeedd', foreground='#7a3e00')
        self.tabla.tag_configure('eliminado', background='#eeeeee', foreground='#999999')
        self.tabla.pack(fill='x', **pad)

        self.p_bitacora, b = self.panel(self, 'BitÃ¡cora e informe')
        self.p_bitacora.pack(fill='both', expand=True, **pad)
        tf = tk.Frame(b); tf.pack(fill='both', expand=True, padx=8, pady=(4, 8))
        self.log = tk.Text(tf, height=12, font=('Consolas', 9), wrap='none')
        sb = ttk.Scrollbar(tf, command=self.log.yview); self.log['yscrollcommand'] = sb.set
        sb.pack(side='right', fill='y'); self.log.pack(fill='both', expand=True)
        self.protocol('WM_DELETE_WINDOW', self.salir)
        # Todo widget de la ventana principal lleva '.' en sus bindtags: cualquier cambio de tamaÃ±o o lugar repinta.
        self.pendiente = False
        self.bind('<Configure>', lambda e: self.programar_repintado())

    def alternar_suspension(self):
        self.suspender = not self.suspender
        guardar_config('Suspension', activa='si' if self.suspender else 'no')
        self.iconos[self.b_susp] = self.imgs_susp['on' if self.suspender else 'off']
        self.pintar_icono(self.b_susp)

    @staticmethod
    def con_alianzas(g):
        try:
            return tanda.alianzas(g).startswith('equipos')
        except (OSError, TypeError, IndexError):
            return False

    def disponibles(self):
        d = os.path.join(tanda.JUEGO, 'SAVES')
        if not os.path.isdir(d):
            return []
        return sorted(n[:-4] for n in os.listdir(d) if n.upper().startswith('TANDA_') and n.upper().endswith('.SAV'))

    def rotular_guardadas(self):
        n = len(self.guardadas)
        txt = self.guardadas[0] if n == 1 else f'{n} partidas guardadas' if n else '(ninguna elegida)'
        self.b_guardadas['text'] = txt + '  â–¾'

    def elegir_guardadas(self):
        """Lista desplegable para marcar las Tanda_*.SAV de la carpeta del juego que entran en la tanda."""
        todas = self.disponibles()
        v = tk.Toplevel(self); v.title('Partidas guardadas'); v.transient(self); v.grab_set()
        v.geometry(f'+{self.b_guardadas.winfo_rootx()}+{self.b_guardadas.winfo_rooty() + 30}')
        ttk.Label(v, text=f'MarcÃ¡ las partidas de la tanda ({len(todas)} disponibles):').pack(anchor='w', padx=8, pady=4)
        lf = ttk.Frame(v); lf.pack(fill='both', expand=True, padx=8)
        lb = tk.Listbox(lf, selectmode='multiple', height=min(15, max(5, len(todas))), width=40,
                        activestyle='none', selectbackground='#0b5ed7', exportselection=False)
        sb = ttk.Scrollbar(lf, command=lb.yview); lb['yscrollcommand'] = sb.set
        sb.pack(side='right', fill='y'); lb.pack(side='left', fill='both', expand=True)
        for i, g in enumerate(todas):
            lb.insert('end', g.removeprefix('Tanda_') + ('  (alianzas)' if self.con_alianzas(g) else ''))
            if g in self.guardadas:
                lb.selection_set(i)
        bf = ttk.Frame(v); bf.pack(fill='x', padx=8, pady=6)
        ttk.Button(bf, text='Todas', command=lambda: lb.selection_set(0, 'end')).pack(side='left')
        ttk.Button(bf, text='Ninguna', command=lambda: lb.selection_clear(0, 'end')).pack(side='left', padx=4)

        def aceptar():
            self.guardadas = [todas[i] for i in lb.curselection()]
            self.rotular_guardadas(); v.destroy()
        ttk.Button(bf, text='Aceptar', command=aceptar).pack(side='right')

    def exportar_pdf(self):
        """Cuadro de posiciones de un mapa (ia\\exportar.py), en PDF, para la pÃ¡gina del Clan."""
        from tkinter import filedialog
        import exportar
        try:
            with sqlite3.connect(tanda.DB) as db:
                mapas = exportar.mapas(db)
        except Exception as e:
            messagebox.showerror('Exportar', f'No se pudo leer datos.db:\n{e}', parent=self); return
        if not mapas:
            messagebox.showinfo('Exportar', 'TodavÃ­a no hay partidas con bando comÃºn para exportar.', parent=self); return
        v = tk.Toplevel(self); v.title('Exportar PDF'); v.transient(self); v.grab_set()
        ttk.Label(v, text='Mapa (partidas comparables):').pack(anchor='w', padx=8, pady=4)
        lb = tk.Listbox(v, height=min(15, len(mapas)), width=40, activestyle='none', exportselection=False)
        lb.pack(fill='both', expand=True, padx=8)
        for g, n in mapas:
            lb.insert('end', f'{g.removeprefix("Tanda_")}  ({n})')
        lb.selection_set(0)

        def aceptar():
            if not lb.curselection():
                return
            g = mapas[lb.curselection()[0]][0]; v.destroy()
            destino = filedialog.asksaveasfilename(parent=self, defaultextension='.pdf', filetypes=[('PDF', '*.pdf')],
                                                   initialfile=f'{g.removeprefix("Tanda_")} - posiciones.pdf')
            if not destino:
                return
            try:
                with sqlite3.connect(tanda.DB) as db:
                    exportar.exportar(g, destino, db)
            except Exception as e:
                messagebox.showerror('Exportar', f'No se pudo generar el PDF:\n{e}', parent=self); return
            os.startfile(destino)
        ttk.Button(v, text='Exportarâ€¦', command=aceptar).pack(anchor='e', padx=8, pady=6)
        lb.bind('<Double-Button-1>', lambda e: aceptar())

    def guardar_monitor(self, i):
        guardar_config('Pantalla', preferida=self.mons[i][0])
        print(f'Monitor del juego: {self.mons[i][0]} (el juego se pasa en unos segundos).')

    # ---- fondo (ruedita): color liso o textura en mosaico, como en USBagent; se guarda en tanda.ini ----
    def aplicar_fondo(self):
        c = leer_config('Fondo')
        tipo, color, ruta = c.get('tipo', 'color'), c.get('color', '#f0f0f0'), c.get('textura', '')
        if tipo == 'textura' and os.path.exists(ruta):
            t = Image.open(ruta).convert('RGB')
            self.mosaico = Image.new('RGB', (3840, 2160))
            for x in range(0, 3840, t.width):
                for y in range(0, 2160, t.height):
                    self.mosaico.paste(t, (x, y))
            rgb = t.resize((1, 1), Image.BOX).getpixel((0, 0))   # color medio de la textura
            self.img_fondo = ImageTk.PhotoImage(self.mosaico)
            self.fondo.configure(image=self.img_fondo)
        else:
            self.mosaico = self.img_fondo = None
            rgb = tuple(v // 257 for v in self.winfo_rgb(color))
            self.fondo.configure(image='')
        self.base = '#%02x%02x%02x' % rgb
        # Letra negra sobre fondos claros, blanca sobre oscuros.
        self.tinta = '#000000' if 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2] > 140 else '#ffffff'
        self.configure(bg=self.base); self.fondo.configure(bg=self.base)
        self.programar_repintado()

    def programar_repintado(self):
        if not self.pendiente:
            self.pendiente = True
            self.after(30, self.repintar)

    def recorte(self, w, tam=None):
        """El pedazo de mosaico que queda detrÃ¡s del widget w (None si no hay textura o w no estÃ¡ a la vista)."""
        if self.mosaico is None or not w.winfo_ismapped():
            return None
        x, y = w.winfo_rootx() - self.winfo_rootx(), w.winfo_rooty() - self.winfo_rooty()
        ancho, alto = tam or (w.winfo_width(), w.winfo_height())
        if ancho < 2 or alto < 2:
            return None
        return self.mosaico.crop((x, y, x + ancho, y + alto))

    def foto(self, w, img):
        self.fotos[w] = ImageTk.PhotoImage(img) if img is not None else ''
        return self.fotos[w]

    def pintar_icono(self, l):
        img = self.iconos[l]
        base = self.recorte(l, img.size)
        base = base.convert('RGBA') if base is not None else Image.new('RGBA', img.size, self.base)
        base.alpha_composite(img)
        l.configure(image=self.foto(l, base), bg=self.base)

    def repintar(self):
        self.pendiente = False
        for f, fondo in self.cajas:
            f.configure(bg=self.base)
            fondo.configure(image=self.foto(fondo, self.recorte(f)), bg=self.base)
        for l in self.rotulos:
            l.configure(image=self.foto(l, self.recorte(l)), bg=self.base, fg=self.tinta)
        for c in self.checks + self.flechas:
            c.configure(bg=self.base, activebackground=self.base)
        for c in self.flechas:
            c.configure(fg=self.tinta, activeforeground=self.tinta)
        for l in self.iconos:
            self.pintar_icono(l)

    def configurar(self):
        from tkinter import colorchooser, filedialog
        c = leer_config('Fondo')
        v = tk.Toplevel(self); v.title('ConfiguraciÃ³n'); v.transient(self); v.grab_set(); v.resizable(False, False)
        v.geometry(f'+{self.winfo_rootx() + self.winfo_width() - 380}+{self.winfo_rooty() + 90}')
        tipo = tk.StringVar(value=c.get('tipo', 'color'))
        color = tk.StringVar(value=c.get('color', '#f0f0f0'))
        ruta = tk.StringVar(value=c.get('textura', ''))
        fr = tk.Frame(v, padx=12, pady=10); fr.pack(fill='both')
        tk.Label(fr, text='Fondo de la ventana:', font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, columnspan=3,
                                                                                    sticky='w')
        tk.Radiobutton(fr, text='Color liso', variable=tipo, value='color').grid(row=1, column=0, sticky='w')
        muestra = tk.Label(fr, width=4, bg=color.get(), relief='solid', bd=1)
        muestra.grid(row=2, column=0, sticky='w', padx=(22, 0))

        def elegir_color():
            r = colorchooser.askcolor(color.get(), parent=v)[1]
            if r:
                color.set(r); muestra['bg'] = r; tipo.set('color')
        tk.Button(fr, text='Elegir color...', command=elegir_color).grid(row=2, column=1, sticky='w', padx=6)
        tk.Radiobutton(fr, text='Textura (imagen en mosaico)', variable=tipo, value='textura')             .grid(row=3, column=0, columnspan=3, sticky='w', pady=(8, 0))
        tk.Entry(fr, textvariable=ruta, width=34, state='readonly').grid(row=4, column=0, columnspan=2, sticky='w',
                                                                         padx=(22, 0))

        def examinar():
            r = filedialog.askopenfilename(parent=v, title='Imagen para la textura',
                                           filetypes=[('ImÃ¡genes', '*.png *.jpg *.jpeg *.bmp *.gif')])
            if r:
                ruta.set(os.path.normpath(r)); tipo.set('textura')
        tk.Button(fr, text='Examinar...', command=examinar).grid(row=4, column=2, padx=6)

        def aceptar():
            if tipo.get() == 'textura' and not os.path.exists(ruta.get()):
                return messagebox.showwarning('ConfiguraciÃ³n', 'ElegÃ­ una imagen para la textura.', parent=v)
            guardar_config('Fondo', tipo=tipo.get(), color=color.get(), textura=ruta.get())
            self.aplicar_fondo(); v.destroy()
        tk.Label(fr, text='ActualizaciÃ³n:', font=('Segoe UI', 10, 'bold')).grid(row=5, column=0, columnspan=3,
                                                                              sticky='w', pady=(12, 0))
        tk.Label(fr, text=f'VersiÃ³n instalada: {VERSION}').grid(row=6, column=0, columnspan=2, sticky='w')
        tk.Button(fr, text='Buscar actualizaciÃ³n', command=lambda: self.actualizar(v)).grid(row=6, column=2, padx=6)
        bf = tk.Frame(fr); bf.grid(row=7, column=0, columnspan=3, sticky='e', pady=(12, 0))
        tk.Button(bf, text='Aceptar', width=10, command=aceptar).pack(side='left', padx=4)
        tk.Button(bf, text='Cancelar', width=10, command=v.destroy).pack(side='left')

    # ---- actualizaciÃ³n desde las releases de REPO ----
    def actualizar(self, padre):
        if not getattr(sys, 'frozen', False):
            return messagebox.showinfo('ActualizaciÃ³n', 'Corriendo desde el cÃ³digo: se actualiza con git.', parent=padre)
        if self.corriendo():
            return messagebox.showwarning('ActualizaciÃ³n', 'Hay una tanda corriendo: actualizÃ¡ cuando termine.',
                                          parent=padre)
        try:
            with urllib.request.urlopen(f'https://api.github.com/repos/{REPO}/releases/latest', timeout=15) as r:
                rel = json.load(r)
        except Exception as e:
            return messagebox.showerror('ActualizaciÃ³n', f'No se pudo consultar GitHub:\n{e}', parent=padre)
        etiqueta = rel['tag_name'].lstrip('v')
        if version_tupla(etiqueta) <= version_tupla(VERSION):
            return messagebox.showinfo('ActualizaciÃ³n', f'Ya tenÃ©s la Ãºltima versiÃ³n ({VERSION}).', parent=padre)
        exe = next((a for a in rel['assets'] if a['name'] == 'Monitor-IA.exe'), None)
        if not exe:
            return messagebox.showerror('ActualizaciÃ³n', f'La release {etiqueta} no trae Monitor-IA.exe.', parent=padre)
        if not messagebox.askyesno('ActualizaciÃ³n', f'Hay una versiÃ³n nueva: {etiqueta} (tenÃ©s {VERSION}).\n'
                                   'Â¿Bajarla e instalarla? El Monitor se cierra y se vuelve a abrir.', parent=padre):
            return
        actual = sys.executable
        nuevo = actual[:-4] + '.nuevo.exe'
        try:
            urllib.request.urlretrieve(exe['browser_download_url'], nuevo)
            # La release tiene que ser lo que dice su etiqueta: se le pregunta la versiÃ³n al .exe bajado.
            interna = version_de(nuevo)
            if interna != etiqueta:
                raise RuntimeError(f'la release {etiqueta} trae adentro la versiÃ³n {interna}')
        except Exception as e:
            if os.path.exists(nuevo):
                os.remove(nuevo)
            return messagebox.showerror('ActualizaciÃ³n', f'No se instalÃ³ la actualizaciÃ³n:\n{e}', parent=padre)
        # Un .bat espera a que este proceso cierre, reemplaza el .exe, lo abre de nuevo y se borra.
        bat, pid = actual[:-4] + '.actualizar.bat', os.getpid()
        with open(bat, 'w', encoding='mbcs') as f:
            f.write('@echo off\n:espera\n'
                    f'tasklist /FI "PID eq {pid}" /NH | find "{pid}" >nul && (timeout /t 1 /nobreak >nul & goto espera)\n'
                    f'move /y "{nuevo}" "{actual}" >nul\nstart "" "{actual}"\ndel "%~f0"\n')
        subprocess.Popen(['cmd', '/c', bat], creationflags=subprocess.CREATE_NO_WINDOW)
        self.destroy()

    # ---- tanda ----
    def corriendo(self):
        return self.hilo is not None and self.hilo.is_alive()

    def arrancar(self, accion):
        if self.corriendo():
            return
        if accion == 'nueva' and not self.guardadas:
            return messagebox.showwarning('Nueva tanda', 'ElegÃ­ al menos una partida guardada.')
        a = SimpleNamespace(accion=accion, partidas=self.v_partidas.get(), guardadas=','.join(self.guardadas),
                            tope_turnos=0, cuelgue=CUELGUE_MIN)
        tanda.CORTAR.clear()
        tanda.CONTROL['silenciar'] = self.v_mudo.get()
        self.hilo = threading.Thread(target=self.trabajar, args=(a,), daemon=True)
        self.hilo.start()

    def trabajar(self, a):
        # Mantener la PC despierta mientras corre: si Windows suspende, la tanda se corta.
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)   # ES_CONTINUOUS | SYSTEM_REQUIRED
        try:
            serie = self.v_serie.get() if self.v_auto.get() else 1
            for i in range(serie):
                db, self.tid = tanda.preparar(a)
                tanda.correr(db, self.tid, a)
                terminada = db.execute('select terminada from tanda where id=?', (self.tid,)).fetchone()[0]
                print()
                informe.main(self.tid)
                # Sigue la serie solo si esta tanda terminÃ³ entera y no se tocÃ³ Cortar ni se destildÃ³ el check.
                if not terminada or tanda.CORTAR.is_set() or i == serie - 1 or not self.v_auto.get():
                    break
                print(f'\nSerie: tanda {i + 1} de {serie} terminada; arranca la siguiente.\n')
                a = SimpleNamespace(**{**vars(a), 'accion': 'nueva'})
            if terminada and self.suspender:
                print('Tanda terminada: la PC se suspende en 30 segundos (apagÃ¡ el interruptor para evitarlo).')
                for _ in range(30):
                    time.sleep(1)
                    if not self.suspender:
                        print('SuspensiÃ³n cancelada.'); break
                else:
                    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
                    ctypes.windll.powrprof.SetSuspendState(False, False, False)
            elif terminada and self.v_alarma.get():
                self.alarma()
        except SystemExit as e:
            print(e)
        except Exception as e:
            print(f'Error: {e!r}')
        finally:
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)

    def cortar(self):
        if self.corriendo() and messagebox.askyesno(
                'Cortar', 'Se cierra el juego y la partida en curso se vuelve a jugar al retomar. Â¿Cortar?'):
            tanda.CORTAR.set()
            print('Cortandoâ€¦')

    def alarma(self):
        threading.Thread(target=lambda: [winsound.PlaySound(ALARMA, winsound.SND_FILENAME) for _ in range(3)],
                         daemon=True).start()

    def salir(self):
        if not self.corriendo():
            return self.destroy()
        if messagebox.askyesno('Salir', 'Hay una tanda corriendo. Â¿Cortarla y salir? Se retoma con "Retomar".'):
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
            self.escribir((f'(no se pudo leer el estado: {e})', 'gris'))
        corre = self.corriendo() or self.externa
        self.encender(self.b_nueva, not corre)
        self.encender(self.b_seguir, not corre and self.retomable)
        self.encender(self.b_cortar, self.corriendo())
        self.dibujar_barras()
        self.medidores[0].poner(psutil.cpu_percent())
        self.medidores[1].poner(psutil.virtual_memory().percent)
        self.after(2000, self.refrescar)

    def dibujar_barras(self):
        c = self.barras; c.delete('all')
        mono, verde, naranja, gris = ('Consolas', 8), '#6fd39a', '#f0a070', '#9aa7a1'
        x0, x1 = 52, 136
        for i, (rot, frac, txt, lista) in enumerate(self.progreso):
            y = 9 + i * 18
            c.create_text(4, y, text=rot, anchor='w', font=mono, fill='#d8e4de')
            c.create_rectangle(x0, y - 5, x1, y + 5, fill='#1a2420', outline='')
            for xx in range(x0, x1, 2):   # resto rayado, como en la imagen de referencia
                for yy in range(y - 5 + (xx // 2) % 2, y + 5, 2):
                    c.create_rectangle(xx, yy, xx + 1, yy + 1, fill='#4a5550', outline='')
            if frac is not None:
                xf = x0 + (x1 - x0) * max(0.0, min(1.0, frac))
                c.create_rectangle(x0, y - 5, xf, y + 5, fill=verde if lista else naranja, outline='')
            c.create_text(x1 + 4, y, text=txt, anchor='w', font=mono, fill=verde if lista else naranja)
        c.create_text(4, 45, text='verde â†’ hecha  naranja â†’ en curso', anchor='w', font=('Consolas', 7), fill=gris)

    def escribir(self, *partes):
        """Reescribe el recuadro de la partida en curso: partes = (texto, estilo) o texto sin estilo."""
        self.info.configure(state='normal'); self.info.delete('1.0', 'end')
        for p in partes:
            self.info.insert('end', *((p,) if isinstance(p, str) else p))
        self.info.configure(state='disabled')

    @staticmethod
    def parches(db, tid):
        """Con quÃ© parche juega la tanda mostrada y con cuÃ¡l jugaron todas, agrupadas de corrido."""
        cols = [r[1] for r in db.execute('pragma table_info(tanda)')]
        if 'exe' not in cols:
            return 'sin registrar', ''
        def rotulo(ver, exe):
            return f'vista-aliada {ver} (exe {exe})' if exe else (f'vista-aliada {ver}' if ver else 'sin registrar')
        filas = db.execute('select id, parche, exe from tanda order by id').fetchall()
        actual = next((rotulo(v, e) for i, v, e in filas if i == tid), 'sin registrar')
        grupos = []
        for i, v, e in filas:
            if grupos and grupos[-1][2] == (v, e):
                grupos[-1][1] = i
            else:
                grupos.append([i, i, (v, e)])
        return actual, ' Â· '.join(f'{a}{"â€“" + str(b) if b != a else ""}: {rotulo(*ve)}' for a, b, ve in grupos)

    def mostrar(self):
        import sqlite3
        self.externa = False
        self.retomable = False
        self.progreso = [('tanda', None, 'â€”', False), ('partida', None, 'â€”', False)]
        if not os.path.exists(tanda.DB):
            self.v_tanda.set('Sin tandas todavÃ­a.'); self.v_tanda2.set(''); self.v_parche.set(''); self.v_todas.set(''); return
        db = sqlite3.connect(tanda.DB)
        # La tanda que se estÃ¡ jugando; si no hay ninguna, la que corriÃ³ este panel; si no, la Ãºltima.
        r = db.execute("select tanda from partida where estado='jugando' and tanda is not null "
                       "order by id desc").fetchone()
        ult = db.execute('select terminada from tanda order by id desc').fetchone()
        self.retomable = bool(ult) and not ult[0]   # tanda.preparar solo retoma la Ãºltima
        tid = r[0] if r else self.tid or db.execute('select max(id) from tanda').fetchone()[0]
        t = db.execute('select id, inicio, plan, terminada from tanda where id=?', (tid,)).fetchone()
        if not t:
            self.v_tanda.set('Sin tandas todavÃ­a.'); self.v_tanda2.set(''); self.v_parche.set(''); self.v_todas.set(''); return
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
        self.v_tanda.set(f'Tanda {tid} ({estado}) â€” desde {inicio}')
        txt = f'{len(hechas)} de {total} partidas terminadas'
        if en_curso:
            txt += f' â€” jugando la {en_curso[0] + 1}.Âª'
        dur = [time.mktime(time.strptime(p[4], '%Y-%m-%d %H:%M:%S')) -
               time.mktime(time.strptime(p[3], '%Y-%m-%d %H:%M:%S')) for p in hechas if p[3] and p[4]]
        if dur and not term:
            fin = time.time() + sum(dur) / len(dur) * (total - len(hechas))
            txt += f' â€” fin estimado {time.strftime("%H:%M", time.localtime(fin))}'
        self.v_tanda2.set(txt)
        self.progreso[0] = ('tanda', len(hechas) / total if total else 0, f'{len(hechas)}/{total}', bool(term))
        actual, todas = self.parches(db, tid); self.v_parche.set(actual); self.v_todas.set(todas)

        if not en_curso:
            self.escribir(('Ninguna partida en curso', 'titulo'), *(
                f'\n  {p[0] + 1}. {p[1].removeprefix("Tanda_")}: {p[5]}, {p[6] or 0} turnos' for p in hechas[-5:]))
            self.l_cuelgue.pack_forget()
            self.tabla.delete(*self.tabla.get_children())
            return
        n, guardada, asig, ini = en_curso[:4]
        filas = tanda.leer(tanda.CSV_T, len(tanda.COL_T))
        bats = tanda.leer_batallas()
        evs = {}
        for r in tanda.leer(tanda.CSV_E, len(tanda.COL_E)):
            evs[r[3]] = evs.get(r[3], 0) + 1
        turno = max((r[0] for r in filas), default=0)
        # Sin tope de turnos, el largo esperado sale del promedio de las partidas ya jugadas.
        largos = [p[0] for p in db.execute("select turnos from partida where turnos>0 and estado!='cortada'")]
        if largos:
            esperado = sum(largos) / len(largos)
            self.progreso[1] = ('partida', turno / esperado, f't{turno}/~{esperado:.0f}', False)
        else:
            self.progreso[1] = ('partida', None, f't{turno}', False)
        prueba = [c for c in range(8) if asig[c] == 'P']
        res = {ia: [0, 0] for ia in (0, 1)}
        for r in bats:
            res.setdefault(r[7], [0, 0])[0 if r[6] == 1 else 1] += 1
        bt = []
        for ia, (g, p) in res.items():
            bt += [('   IA ' + IAS.get(ia, str(ia)) + ': ', IAS.get(ia, 'b')), (f'{g} ganadas', 'gana'), ' / ',
                   (f'{p} perdidas', 'pierde')]
        self.escribir((f'Partida {n + 1} Â· {guardada.removeprefix("Tanda_")} Â· turno {turno}', 'titulo'),
                      (f'     empezÃ³ {ini[11:]}\n', 'gris'),
                      'Colores con la IA de prueba: ', (', '.join(tanda.COLORES[c] for c in prueba) + '\n', 'prueba'),
                      ('Batallas atacando: ', 'b'), (str(len(bats)), 'b'), *bt,
                      '\nEventos: ' +(', '.join(f'{tanda.EVENTOS.get(t, t)} {k}' for t, k in sorted(evs.items()))
                                        or 'ninguno todavÃ­a'))
        quieto = time.time() - os.path.getmtime(tanda.CSV_T) if os.path.exists(tanda.CSV_T) else \
            time.time() - time.mktime(time.strptime(ini, '%Y-%m-%d %H:%M:%S'))
        if quieto > AVISO_MIN * 60:
            self.l_cuelgue['text'] = (f'  Sin turnos nuevos hace {quieto / 60:.0f} min: posible cuelgue '
                                      f'(se corta sola a los {CUELGUE_MIN} min).  ')
            self.l_cuelgue.pack(anchor='w', padx=8, before=self.tabla)
        else:
            self.l_cuelgue.pack_forget()
        ultimo = {}
        for r in filas:
            ultimo[r[1]] = dict(zip(tanda.COL_T, r))
        self.tabla.delete(*self.tabla.get_children())
        for c in sorted(ultimo):
            u = ultimo[c]
            vivo = u['vivo'] and u['turno'] >= turno - 1
            self.tabla.insert('', 'end', tags=('eliminado' if not vivo else 'prueba' if u['ia'] == 1 else 'original',), values=(
                tanda.COLORES[c] if 0 <= c < 8 else c, IAS.get(u['ia'], u['ia']), 'vivo' if vivo else 'eliminado',
                tanda.pv_calc(u['ciudades'], u['heroes'], u['oro']) if vivo else 0,
                # de un eliminado, IA.CSV guarda lo que tenÃ­a en su Ãºltimo turno vivo: no vale mostrarlo
                *((u['ciudades'], u['oro'], u['ejercitos'], u['heroes']) if vivo else ('â€”',) * 4)))


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--version':
        with open(sys.argv[2], 'w') as f:
            f.write(VERSION)
        sys.exit(0)
    Monitor().mainloop()
