# Visor de historia: el "Events Report" de una partida guardada (.SAV), con el arte del juego, línea de tiempo por
# ronda, buscador y exportación a PDF (PENDIENTE-visor-historia.md). Lee todo con ia\historia.py y toma el arte
# (fondo, escudos, texturas, fuentes) de la carpeta del juego donde está el .SAV. Se empaqueta con build.py y se
# publica con publicar.py; la ruedita (configuración) elige el fondo y busca actualizaciones, como en el Monitor de IA.
import configparser, ctypes, json, os, subprocess, sys, time, urllib.request
import tkinter as tk
import tkinter.font as tkfont
from tkinter import colorchooser, filedialog, messagebox
from PIL import Image, ImageTk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import historia, tanda   # noqa: E402

VERSION = '1.0.2.0'
TITULO = f'VISOR DE HISTORIA — VERSIÓN {VERSION}'
FONDO = '#1b1b1b'
TEXTO, SOMBRA, RESALTE = '#f0e6c8', '#000000', '#ffd966'
HOVER = '#ffd8a8'                      # naranja suave de los botones con el mouse encima
COLOR = {'white': (250, 250, 250), 'yellow': (240, 220, 40), 'orange': (240, 140, 30), 'red': (220, 30, 30),
         'green': (40, 180, 40), 'blue': (40, 80, 230), 'cyan': (60, 210, 230), 'black': (40, 40, 40)}
NEUTRAL = (150, 150, 150)
# Cuadro DLG_BIG (620x460): título en la barra de arriba, minimapa a la izquierda y renglones a la derecha.
TIT_Y, SUB_Y = 28, 72
MINI = (28, 95, 200, 240)              # x, y, ancho y alto máximos del minimapa
ESC_Y = 350                            # fila de escudos para elegir el color del minimapa
REN_X, REN_Y, REN_ALTO = 245, 98, 20   # 16 renglones como máximo por ronda (2 por jugador)
# Actualizaciones: Visor-Historia.exe y Visor-Historia.version (el número, en texto) en la release Actualizador.
RELEASE = 'https://api.github.com/repos/elcoprofago/Warlords-updater/releases/tags/Actualizador'
EXE, MARCA = 'Visor-Historia.exe', 'Visor-Historia.version'
CARPETA = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))
CONFIG = os.path.join(CARPETA, 'Visor-Historia.ini')
# La ruedita y las luces son las del Monitor de IA: en el .exe va adentro (build.py); desde el código se lee de monitor-ia\assets.
ASSETS = os.path.join(getattr(sys, '_MEIPASS', ''), 'assets') if getattr(sys, 'frozen', False) else \
    os.path.join(os.path.dirname(CARPETA), 'monitor-ia', 'assets')
DATOS = (('turnos', 'Turnos jugados:'), ('victoria', 'Victoria:'), ('mapa', 'Mapa:'), ('guardado', 'Último guardado:'))


def juego_de(sav):
    """Carpeta del juego: la de arriba de SAVES si tiene Sagetext.tex; si no, la de siempre."""
    j = os.path.dirname(os.path.dirname(os.path.abspath(sav)))
    return j if os.path.exists(os.path.join(j, 'Sagetext.tex')) else tanda.JUEGO


def pcx_rgba(ruta):
    """La imagen con el magenta (y el separador de las hojas de escudos, índice 101) transparentes."""
    im = Image.open(ruta)
    trans = {11, 101} if os.path.basename(os.path.dirname(ruta)).upper() == 'SHIELD' else set()
    rgba = im.convert('RGBA')
    px, ix = rgba.load(), im.load()
    for y in range(im.height):
        for x in range(im.width):
            if px[x, y][:3] == (255, 0, 255) or ix[x, y] in trans:
                px[x, y] = (0, 0, 0, 0)
    return rgba


def leer_config():
    c = configparser.ConfigParser(); c.read(CONFIG)
    return dict(c['Fondo']) if c.has_section('Fondo') else {}


def guardar_config(**valores):
    c = configparser.ConfigParser(); c['Fondo'] = valores
    with open(CONFIG, 'w') as f:
        c.write(f)


def version_tupla(v):
    return tuple(int(x) for x in v.split('.'))


def version_de(exe):
    """La versión que trae adentro un Visor-Historia.exe (se la pregunta con --version; lo usa también publicar.py)."""
    marca = exe + '.version'
    subprocess.run([exe, '--version', marca], timeout=120, creationflags=subprocess.CREATE_NO_WINDOW)
    with open(marca) as f:
        v = f.read().strip()
    os.remove(marca)
    return v


def boton(padre, **kw):
    """Botón con naranja suave mientras el mouse está encima."""
    b = tk.Button(padre, cursor='hand2', **kw)
    normal = b.cget('bg')
    b.bind('<Enter>', lambda e: b.configure(bg=HOVER, activebackground=HOVER), add='+')
    b.bind('<Leave>', lambda e: b.configure(bg=normal, activebackground=normal), add='+')
    return b


def fuente_privada(ruta):
    """Registra una TTF solo para este proceso, para que Tk la vea por su nombre."""
    try:
        ctypes.windll.gdi32.AddFontResourceExW(ruta, 0x10, 0)
    except Exception:
        pass


class Visor:
    def __init__(self, raiz):
        self.raiz, self.p, self.ronda, self.color = raiz, None, 1, 0
        self.coinc, self.imgs = [], []
        self.cajas, self.rotulos, self.fotos = [], [], {}
        self.mosaico, self.base, self.tinta = None, FONDO, self.tintas((27, 27, 27))
        raiz.title(TITULO)
        raiz.resizable(False, False)
        self.f_ren = tkfont.Font(family='Arial', size=11)
        fams = set(tkfont.families())
        self.f_tit = tkfont.Font(family='Uncial ATT' if 'Uncial ATT' in fams else 'Times New Roman', size=18)
        self.f_sub = tkfont.Font(family='Arial', size=14)   # la letra de los renglones, más grande y en mayúsculas
        self.fondo_v = tk.Label(raiz, bd=0)
        self.fondo_v.place(x=0, y=0, relwidth=1, relheight=1)

        # Panel superior: el nombre en un cuadro blanco; rótulos y datos en dos colores
        sup = self.caja(raiz)
        sup.configure(padx=10, pady=8)
        sup.pack(fill='x')
        boton(sup, text='Abrir…', width=10, command=self.abrir).grid(row=0, column=0, rowspan=3, padx=(0, 14))
        self.d_nombre = tk.Entry(sup, font=('Segoe UI', 13, 'bold'), readonlybackground='#ffffff', fg='#000000',
                                 relief='solid', bd=1, width=44, state='readonly')
        self.d_nombre.grid(row=0, column=1, columnspan=4, sticky='w', pady=(0, 4))
        # Luces «Single» y «Multi» a la derecha del nombre, según el modo guardado en la partida
        sup.columnconfigure(5, weight=1)
        luces = self.caja(sup)
        luces.grid(row=0, column=5, rowspan=2, sticky='ne')
        self.luces = {m: self.luz(luces, m) for m in ('Single', 'Multi')}
        self.datos = {}
        for i, (clave, rot) in enumerate(DATOS):
            f, c = 1 + i // 2, 1 + 2 * (i % 2)
            self.rotulo(sup, 'etiqueta', text=rot).grid(row=f, column=c, sticky='w', padx=(0 if c == 1 else 24, 4))
            self.datos[clave] = self.rotulo(sup, 'valor')
            self.datos[clave].grid(row=f, column=c + 1, sticky='w')
        self.aviso = self.rotulo(raiz, 'aviso', font=('Segoe UI', 9), wraplength=620, justify='left')
        self.aviso.pack(fill='x', padx=10)

        # Buscador, separado del panel superior
        tk.Frame(raiz, bg='#444', height=1).pack(fill='x', padx=10, pady=(4, 6))
        bus = self.caja(raiz)
        bus.configure(padx=10)
        bus.pack(fill='x')
        self.rotulo(bus, 'etiqueta', text='Buscar:').pack(side='left')
        self.buscar = tk.StringVar()
        self.buscar.trace_add('write', lambda *_: self.al_buscar())
        e = tk.Entry(bus, textvariable=self.buscar, width=24, font=('Segoe UI', 10))
        e.pack(side='left', padx=6)
        e.bind('<Return>', lambda _: self.saltar(1))
        boton(bus, text='◀', width=3, command=lambda: self.saltar(-1)).pack(side='left')
        boton(bus, text='▶', width=3, command=lambda: self.saltar(1)).pack(side='left', padx=(2, 8))
        self.d_coinc = self.rotulo(bus, 'valor', width=1)   # ancho fijo: no estira la ventana
        self.d_coinc.pack(side='left', fill='x', expand=True)

        # Panel principal: el cuadro y la línea de tiempo
        self.cv = tk.Canvas(raiz, width=620, height=460, bg=FONDO, highlightthickness=0)
        self.cv.pack(padx=10, pady=(8, 0))
        self.cv.bind('<Button-1>', self.clic_cuadro)
        self.barra = tk.Canvas(raiz, width=620, height=46, bg=FONDO, highlightthickness=0)
        self.barra.pack(padx=10, pady=(4, 0))
        self.barra.bind('<Button-1>', self.clic_barra)
        self.barra.bind('<B1-Motion>', self.clic_barra)
        raiz.bind('<Left>', lambda _: self.ir(self.ronda - 1))
        raiz.bind('<Right>', lambda _: self.ir(self.ronda + 1))

        # Panel inferior
        inf = self.caja(raiz)
        inf.configure(padx=10, pady=10)
        inf.pack(fill='x')
        boton(inf, text='Limpiar búsqueda', command=lambda: self.buscar.set('')).pack(side='left')
        self.armar_ruedita(inf)
        boton(inf, text='Exportar PDF…', command=self.exportar_pdf).pack(side='right', padx=6)
        self.aplicar_fondo()

    # ---- fondo: color liso o textura en mosaico, como en el Monitor de IA; se guarda en Visor-Historia.ini ----
    # Cada caja y cada rótulo lleva de imagen el recorte del mosaico que cae en su lugar: se ve continuo.
    def caja(self, padre):
        f = tk.Frame(padre, bd=0, highlightthickness=0)
        fondo = tk.Label(f, bd=0, highlightthickness=0)
        fondo.place(x=0, y=0, relwidth=1, relheight=1)
        self.cajas.append((f, fondo))
        return f

    def rotulo(self, padre, tipo, **kw):
        kw.setdefault('font', ('Segoe UI', 10, 'bold') if tipo == 'etiqueta' else ('Segoe UI', 10))
        l = tk.Label(padre, bd=0, highlightthickness=0, padx=0, pady=0, compound='center', anchor='w', **kw)
        l.tipo = tipo
        self.rotulos.append(l)
        return l

    @staticmethod
    def tintas(rgb):
        """Colores de rótulos, datos y avisos según el fondo sea claro u oscuro."""
        if 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2] > 140:
            return {'etiqueta': '#8a4b00', 'valor': '#0b3d91', 'aviso': '#b00000'}
        return {'etiqueta': '#f0b040', 'valor': '#9fd3ff', 'aviso': '#ff7070'}

    def aplicar_fondo(self):
        c = leer_config()
        tipo, color, ruta = c.get('tipo', 'color'), c.get('color', FONDO), c.get('textura', '')
        if tipo == 'textura' and os.path.exists(ruta):
            t = Image.open(ruta).convert('RGB')
            self.mosaico = Image.new('RGB', (1000, 1100))
            for x in range(0, 1000, t.width):
                for y in range(0, 1100, t.height):
                    self.mosaico.paste(t, (x, y))
            rgb = t.resize((1, 1), Image.BOX).getpixel((0, 0))   # color medio de la textura
        else:
            self.mosaico = None
            rgb = tuple(v // 257 for v in self.raiz.winfo_rgb(color))
        self.base, self.tinta = '#%02x%02x%02x' % rgb, self.tintas(rgb)
        self.raiz.after(30, self.repintar)

    def recorte(self, w, tam=None):
        """El pedazo de mosaico que queda detrás del widget w (None si no hay textura o w no está a la vista)."""
        if self.mosaico is None or not w.winfo_ismapped():
            return None
        x, y = w.winfo_rootx() - self.raiz.winfo_rootx(), w.winfo_rooty() - self.raiz.winfo_rooty()
        ancho, alto = tam or (w.winfo_width(), w.winfo_height())
        return None if ancho < 2 or alto < 2 else self.mosaico.crop((x, y, x + ancho, y + alto))

    def foto_de(self, w, img):
        self.fotos[w] = ImageTk.PhotoImage(img) if img is not None else ''
        return self.fotos[w]

    def repintar(self):
        self.raiz.update_idletasks()
        self.raiz.configure(bg=self.base)
        self.fondo_v.configure(bg=self.base, image=self.foto_de(self.fondo_v, self.recorte(self.fondo_v)))
        for f, fondo in self.cajas:
            f.configure(bg=self.base)
            fondo.configure(image=self.foto_de(fondo, self.recorte(f)), bg=self.base)
        for l in self.rotulos:
            l.configure(image=self.foto_de(l, self.recorte(l)), bg=self.base, fg=self.tinta[l.tipo])
        for cv in (self.cv, self.barra):
            cv.configure(bg=self.base)
        self.pintar_ruedita()
        self.pintar_luces()
        self.dibujar()

    def fondo_canvas(self, cv):
        """El mosaico detrás de un canvas, como primer dibujo."""
        r = self.recorte(cv, (int(cv['width']), int(cv['height'])))
        if r is not None:
            self.imgs.append(ImageTk.PhotoImage(r))
            cv.create_image(0, 0, image=self.imgs[-1], anchor='nw')

    # ---- luces: el círculo del semáforo del Monitor de IA (mismo tamaño, 26 px), en amarillo anaranjado ----
    def luz(self, padre, nombre):
        marco = Image.open(os.path.join(ASSETS, 'marco.png')).convert('RGBA')
        base = Image.open(os.path.join(ASSETS, 'circle_09.png')).convert('RGBA')
        h, s, v = base.convert('HSV').split()
        imgs = {}
        for estado, brillo in (('on', 1), ('off', 0.3)):   # apagada: la misma muy oscura, lámpara sin corriente
            c = Image.merge('HSV', (h.point(lambda x: 28), s, v.point(lambda x: x * brillo))).convert('RGBA')
            c.putalpha(base.getchannel('A'))
            c.alpha_composite(marco.resize(c.size))
            imgs[estado] = c.resize((26, 26), Image.LANCZOS)
        f = self.caja(padre)
        f.pack(side='left', padx=(10, 0))
        l = tk.Label(f, bd=0, highlightthickness=0)
        l.pack()
        l.imgs, l.estado = imgs, 'off'
        self.rotulo(f, 'etiqueta', text=nombre, font=('Segoe UI', 7, 'bold')).pack()
        return l

    def pintar_luces(self):
        modo = self.p.cabecera['modo'] if self.p else None
        for nombre, l in self.luces.items():
            l.estado = 'on' if (nombre == 'Single' and modo == 0) or (nombre == 'Multi' and modo in (1, 2)) else 'off'
            img = l.imgs[l.estado]
            base = self.recorte(l, img.size)
            base = base.convert('RGBA') if base is not None else Image.new('RGBA', img.size, self.base)
            base.alpha_composite(img)
            l.configure(image=self.foto_de(l, base), bg=self.base)

    # ---- ruedita: normal, hover con el mouse encima, active mientras se aprieta, disabled con la ventana abierta ----
    def armar_ruedita(self, padre):
        self.r_imgs = {e: Image.open(os.path.join(ASSETS, f'menu_settings_{e}.png')).convert('RGBA')
                       .resize((28, 28), Image.LANCZOS) for e in ('normal', 'hover', 'active', 'disabled')}
        self.r_estado, self.r_abierta = 'normal', False
        r = self.ruedita = tk.Label(padre, bd=0, highlightthickness=0, cursor='hand2')
        r.pack(side='right')

        def estado(e):
            if not self.r_abierta:
                self.r_estado = e
                self.pintar_ruedita()
        r.bind('<Enter>', lambda e: estado('hover'))
        r.bind('<Leave>', lambda e: estado('normal'))
        r.bind('<ButtonPress-1>', lambda e: estado('active'))
        r.bind('<ButtonRelease-1>', lambda e: (estado('hover'), self.r_abierta or self.configurar()))

    def pintar_ruedita(self):
        img = self.r_imgs[self.r_estado]
        base = self.recorte(self.ruedita, img.size)
        base = base.convert('RGBA') if base is not None else Image.new('RGBA', img.size, self.base)
        base.alpha_composite(img)
        self.ruedita.configure(image=self.foto_de(self.ruedita, base), bg=self.base)

    def configurar(self):
        c = leer_config()
        v = tk.Toplevel(self.raiz)
        v.title('Configuración'); v.transient(self.raiz); v.grab_set(); v.resizable(False, False)
        self.r_abierta, self.r_estado = True, 'disabled'
        self.ruedita['cursor'] = 'arrow'
        self.pintar_ruedita()

        def cerrada(e):
            if e.widget is v and self.ruedita.winfo_exists():
                self.r_abierta, self.r_estado = False, 'normal'
                self.ruedita['cursor'] = 'hand2'
                self.pintar_ruedita()
        v.bind('<Destroy>', cerrada)
        v.geometry(f'+{self.raiz.winfo_rootx() + self.raiz.winfo_width() - 400}+{self.raiz.winfo_rooty() + 380}')
        tipo = tk.StringVar(value=c.get('tipo', 'color'))
        color = tk.StringVar(value=c.get('color', FONDO))
        ruta = tk.StringVar(value=c.get('textura', ''))
        fr = tk.Frame(v, padx=12, pady=10)
        fr.pack(fill='both')
        tk.Label(fr, text='Fondo de la ventana:', font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, columnspan=3,
                                                                                    sticky='w')
        tk.Radiobutton(fr, text='Color liso', variable=tipo, value='color').grid(row=1, column=0, sticky='w')
        muestra = tk.Label(fr, width=4, bg=color.get(), relief='solid', bd=1)
        muestra.grid(row=2, column=0, sticky='w', padx=(22, 0))

        def elegir_color():
            r = colorchooser.askcolor(color.get(), parent=v)[1]
            if r:
                color.set(r); muestra['bg'] = r; tipo.set('color')
        boton(fr, text='Elegir color...', command=elegir_color).grid(row=2, column=1, sticky='w', padx=6)
        tk.Radiobutton(fr, text='Textura (imagen en mosaico)', variable=tipo, value='textura') \
            .grid(row=3, column=0, columnspan=3, sticky='w', pady=(8, 0))
        tk.Entry(fr, textvariable=ruta, width=34, state='readonly').grid(row=4, column=0, columnspan=2, sticky='w',
                                                                         padx=(22, 0))

        def examinar():
            r = filedialog.askopenfilename(parent=v, title='Imagen para la textura',
                                           filetypes=[('Imágenes', '*.png *.jpg *.jpeg *.bmp *.gif')])
            if r:
                ruta.set(os.path.normpath(r)); tipo.set('textura')
        boton(fr, text='Examinar...', command=examinar).grid(row=4, column=2, padx=6)

        def aceptar():
            if tipo.get() == 'textura' and not os.path.exists(ruta.get()):
                return messagebox.showwarning('Configuración', 'Elegí una imagen para la textura.', parent=v)
            guardar_config(tipo=tipo.get(), color=color.get(), textura=ruta.get())
            self.aplicar_fondo()
            v.destroy()
        tk.Label(fr, text='Actualización:', font=('Segoe UI', 10, 'bold')).grid(row=5, column=0, columnspan=3,
                                                                              sticky='w', pady=(12, 0))
        tk.Label(fr, text=f'Versión instalada: {VERSION}').grid(row=6, column=0, columnspan=2, sticky='w')
        boton(fr, text='Actualizar versión', command=lambda: self.actualizar(v)).grid(row=6, column=2, padx=6)
        bf = tk.Frame(fr)
        bf.grid(row=7, column=0, columnspan=3, sticky='e', pady=(12, 0))
        boton(bf, text='Aceptar', width=10, command=aceptar).pack(side='left', padx=4)
        boton(bf, text='Cancelar', width=10, command=v.destroy).pack(side='left')

    # ---- actualización desde la release Actualizador ----
    def actualizar(self, padre):
        if not getattr(sys, 'frozen', False):
            return messagebox.showinfo('Actualización', 'Corriendo desde el código: se actualiza con git.', parent=padre)
        try:
            with urllib.request.urlopen(RELEASE, timeout=15) as r:
                assets = {a['name']: a['browser_download_url'] for a in json.load(r)['assets']}
            if EXE not in assets or MARCA not in assets:
                raise RuntimeError(f'la release no trae {EXE} y {MARCA}')
            with urllib.request.urlopen(assets[MARCA], timeout=15) as r:
                nueva = r.read().decode().strip()
        except Exception as e:
            return messagebox.showerror('Actualización', f'No se pudo consultar GitHub:\n{e}', parent=padre)
        if version_tupla(nueva) <= version_tupla(VERSION):
            return messagebox.showinfo('Actualización', f'Ya tenés la última versión ({VERSION}).', parent=padre)
        if not messagebox.askyesno('Actualización', f'Hay una versión nueva: {nueva} (tenés {VERSION}).\n'
                                   '¿Bajarla e instalarla? El Visor se cierra y se vuelve a abrir.', parent=padre):
            return
        actual = sys.executable
        nuevo = actual[:-4] + '.nuevo.exe'
        try:
            urllib.request.urlretrieve(assets[EXE], nuevo)
            # Lo bajado tiene que ser lo que anuncia la marca: se le pregunta la versión al .exe.
            interna = version_de(nuevo)
            if interna != nueva:
                raise RuntimeError(f'se anunció la {nueva} y el .exe trae adentro la {interna}')
        except Exception as e:
            if os.path.exists(nuevo):
                os.remove(nuevo)
            return messagebox.showerror('Actualización', f'No se instaló la actualización:\n{e}', parent=padre)
        # Un .bat espera a que este proceso cierre, reemplaza el .exe, lo abre de nuevo y se borra.
        bat, pid = actual[:-4] + '.actualizar.bat', os.getpid()
        with open(bat, 'w', encoding='mbcs') as f:
            f.write('@echo off\n:espera\n'
                    f'tasklist /FI "PID eq {pid}" /NH | find "{pid}" >nul && (timeout /t 1 /nobreak >nul & goto espera)\n'
                    f'move /y "{nuevo}" "{actual}" >nul\nstart "" "{actual}"\ndel "%~f0"\n')
        subprocess.Popen(['cmd', '/c', bat], creationflags=subprocess.CREATE_NO_WINDOW)
        self.raiz.destroy()

    # ---- datos ----
    def abrir(self, ruta=None):
        if not ruta:
            ini = next((os.path.join(j, 'SAVES') for j in (tanda.JUEGO, r'C:\Warlords')
                        if os.path.isdir(os.path.join(j, 'SAVES'))), None)
            ruta = filedialog.askopenfilename(title='Abrir partida', initialdir=ini,
                                              filetypes=[('Partidas de Warlords', '*.SAV'), ('Todos', '*.*')])
            if not ruta:
                return
        try:
            with open(ruta, 'rb') as f:
                d = f.read()
            self.juego = juego_de(ruta)
            p = historia.Partida(d, self.juego)
            self.cargar_arte(p)
        except Exception as e:
            messagebox.showerror(TITULO, f'No se pudo leer la partida:\n{ruta}\n\n{e}')
            return
        self.p, self.ruta = p, ruta
        c = p.cabecera
        self.rondas = {}
        for ronda, j, r in historia.renglones(d):
            self.rondas.setdefault(ronda, []).append((j, p.texto(r)))
        self.rondas[c['ronda']] = [(j, p.texto(r)) for j, r in historia.en_curso(d)]
        self.duenos = historia.duenos(d)
        self.duenos[c['ronda']] = bytes(ci['dueño'] for ci in p.ciudades)
        self.color = next((k for k in range(8) if p.juega(k)), 0)
        self.d_nombre.configure(state='normal')
        self.d_nombre.delete(0, 'end')
        self.d_nombre.insert(0, c['nombre'])
        self.d_nombre.configure(state='readonly')
        self.datos['turnos']['text'] = f"{c['ronda'] - 1}  (ronda {c['ronda']} en curso)"
        self.datos['victoria']['text'] = c['victoria'] + (f", límite {c['limite']}" if c['limite'] else '')
        self.datos['mapa']['text'] = ('aleatorio' if c['mapa'] == 'Random' else f"escenario «{c['mapa']}»") \
            + f"  ({c['set']})"
        self.datos['guardado']['text'] = time.strftime('%d/%m/%Y %H:%M', time.localtime(os.path.getmtime(ruta)))
        self.aviso['text'] = ('Aviso: el historial guardado en esta partida es de otra partida (pasa con las guardadas '
                              'armadas a partir de otra). Los sucesos y nombres de ciudad no corresponden a este mapa.'
                              if p.ajena else '')
        self.buscar.set(self.buscar.get())   # recalcula las coincidencias
        self.ronda = max([1] + [r for r, rs in self.rondas.items() if rs])   # la última ronda con sucesos
        self.raiz.after(30, self.repintar)   # los rótulos cambiaron de tamaño: el recorte del mosaico también

    def cargar_arte(self, p):
        j, c = self.juego, p.cabecera
        self.fondo = pcx_rgba(os.path.join(j, 'SETS', c['set'], 'DLG_BIG.PCX'))
        self.escudos, self.colores = {}, {}
        for k in range(9):
            hojas = p.escudo(k) if k < 8 else []
            if not hojas:
                continue
            esc = Image.new('RGBA', (54, 38))
            for h in hojas:
                ruta = os.path.join(j, 'SHIELD', h + '.PCX')
                if os.path.exists(ruta):
                    esc.alpha_composite(pcx_rgba(ruta))
            self.escudos[k] = (esc.crop((33, 1, 44, 15)), esc.crop((1, 1, 32, 37)))   # 11x14 y 31x36
            self.colores[k] = COLOR.get(hojas[0][1:].lower(), NEUTRAL)
        # Color de cada terreno del mapa: el promedio de su textura (no es la paleta exacta del minimapa del juego)
        self.tcol = []
        for _, tex in historia.terrenos(p.d):
            ruta = os.path.join(j, 'TERRAIN', 'DATA', tex + '.PCX')
            try:
                im = Image.open(ruta).convert('RGB').resize((32, 32))
                self.tcol.append(tuple(sum(c[i] for c in im.getdata()) // 1024 for i in range(3)))
            except OSError:
                self.tcol.append((90, 90, 90))
        self.mapa, self.mini = historia.mapa(p.d), {}

    # ---- dibujo ----
    def foto(self, im):
        f = ImageTk.PhotoImage(im)
        self.imgs.append(f)
        return f

    def texto_sombra(self, x, y, s, fuente, anchor='nw'):
        self.cv.create_text(x + 1, y + 1, text=s, font=fuente, fill=SOMBRA, anchor=anchor)
        self.cv.create_text(x, y, text=s, font=fuente, fill=TEXTO, anchor=anchor)

    def dibujar(self):
        cv, self.imgs = self.cv, []
        cv.delete('all')
        self.fondo_canvas(cv)
        if not self.p:
            cv.create_text(310, 230, text='Abrí una partida guardada (.SAV) con «Abrir…»', fill=self.tinta['valor'],
                           font=('Segoe UI', 12))
            self.dibujar_barra()
            return
        cv.create_image(0, 0, image=self.foto(self.fondo), anchor='nw')
        cv.create_text(310, TIT_Y, text='History of Events', font=self.f_tit, fill='#20203a')
        self.texto_sombra(REN_X + 175, SUB_Y, f'EVENTS FOR TURN {self.ronda}', self.f_sub, 'n')
        self.dibujar_minimapa()
        clave = self.buscar.get().strip().lower()
        y = REN_Y
        for j, s in self.rondas.get(self.ronda, []):
            if j in self.escudos:
                cv.create_image(REN_X, y + 3, image=self.foto(self.escudos[j][0]), anchor='nw')
            x = REN_X + 18
            if clave:   # resalte leve detrás de cada aparición
                i = s.lower().find(clave)
                while i >= 0:
                    x0 = x + self.f_ren.measure(s[:i])
                    cv.create_rectangle(x0 - 1, y + 1, x0 + self.f_ren.measure(s[i:i + len(clave)]) + 1, y + 18,
                                        fill=RESALTE, outline='', stipple='gray50')
                    i = s.lower().find(clave, i + 1)
            self.texto_sombra(x, y + 1, s, self.f_ren)
            y += REN_ALTO
        if not self.rondas.get(self.ronda):
            self.texto_sombra(REN_X + 18, y + 1, self.p.T[0][0], self.f_ren)   # Nothing unusual happens
        self.dibujar_barra()

    def dibujar_minimapa(self):
        m, p = self.mapa, self.p
        h, w = len(m), len(m[0])
        bit = 1 << self.color
        esc = min(MINI[2] / w, MINI[3] / h)
        if self.color not in self.mini:   # lo no explorado por ese color, en negro
            im = Image.new('RGB', (w, h))
            px = im.load()
            for y in range(h):
                for x in range(w):
                    t, ex = m[y][x]
                    px[x, y] = (self.tcol[t] if t < len(self.tcol) else (90, 90, 90)) if ex & bit else (0, 0, 0)
            self.mini[self.color] = im.resize((round(w * esc), round(h * esc)), Image.NEAREST)
        im = self.mini[self.color]
        x0, y0 = MINI[0] + (MINI[2] - im.width) // 2, MINI[1]
        self.cv.create_rectangle(x0 - 2, y0 - 2, x0 + im.width + 1, y0 + im.height + 1, outline='#c8a040', width=2)
        self.cv.create_image(x0, y0, image=self.foto(im), anchor='nw')
        duenos = self.duenos.get(self.ronda, b'')
        for i, ci in enumerate(p.ciudades if not p.ajena else []):
            if i >= len(duenos) or not m[min(ci['y'], h - 1)][min(ci['x'], w - 1)][1] & bit:
                continue
            col = '#%02x%02x%02x' % self.colores.get(duenos[i], NEUTRAL)
            cx, cy = x0 + ci['x'] * esc, y0 + ci['y'] * esc   # las ciudades ocupan 2x2 casillas
            self.cv.create_rectangle(cx - 1, cy - 1, cx + 2 * esc + 1, cy + 2 * esc + 1, fill=col, outline='#000')
        # Escudos para elegir de qué color es la vista del minimapa
        self.zonas = []
        ks = [k for k in range(8) if p.juega(k) and k in self.escudos]
        x = MINI[0] + (MINI[2] - 25 * len(ks)) // 2
        for k in ks:
            g = self.escudos[k][1].resize((22, 26))
            self.cv.create_image(x, ESC_Y, image=self.foto(g), anchor='nw')
            if k == self.color:
                self.cv.create_rectangle(x - 2, ESC_Y - 2, x + 23, ESC_Y + 27, outline='#ffd966', width=2)
            self.zonas.append((x, x + 22, k))
            x += 25
        self.texto_sombra(MINI[0] + MINI[2] // 2, ESC_Y + 32, p.jugador(self.color), self.f_ren, 'n')

    def clic_cuadro(self, e):
        if self.p and ESC_Y <= e.y <= ESC_Y + 26:
            for a, b, k in self.zonas:
                if a <= e.x <= b:
                    self.color = k
                    self.dibujar()

    def dibujar_barra(self):
        b = self.barra
        b.delete('all')
        self.fondo_canvas(b)
        if not self.p:
            return
        n = self.p.cabecera['ronda']
        x = lambda r: 20 + (580 * (r - 1) / max(1, n - 1))
        b.create_line(20, 14, 600, 14, fill='#777', width=3)
        for r in sorted({r for r, _ in self.coinc}):
            b.create_line(x(r), 6, x(r), 22, fill=RESALTE, width=2)
        b.create_oval(x(self.ronda) - 7, 7, x(self.ronda) + 7, 21, fill='#c8a040', outline='#000')
        f = ('Segoe UI', 9)
        b.create_text(20, 34, text='1', fill=self.tinta['valor'], font=f)
        b.create_text(600, 34, text=str(n), fill=self.tinta['valor'], font=f)
        b.create_text(310, 34, text=f'Ronda {self.ronda} de {n}' + (' (en curso)' if self.ronda == n else ''),
                      fill=self.tinta['etiqueta'], font=f)

    def clic_barra(self, e):
        if self.p:
            n = self.p.cabecera['ronda']
            self.ir(round(1 + (e.x - 20) * (n - 1) / 580) if n > 1 else 1)

    def ir(self, r):
        if self.p:
            self.ronda = max(1, min(self.p.cabecera['ronda'], r))
        self.dibujar()

    # ---- búsqueda ----
    def al_buscar(self):
        clave = self.buscar.get().strip().lower()
        self.coinc = [] if not clave or not self.p else \
            [(r, s) for r in sorted(self.rondas) for _, s in self.rondas[r] if clave in s.lower()]
        rs = sorted({r for r, _ in self.coinc})
        self.d_coinc['text'] = '' if not clave else ('Sin coincidencias' if not rs else
                                                     f"{len(self.coinc)} sucesos en {len(rs)} rondas: "
                                                     + ', '.join(map(str, rs[:12])) + ('…' if len(rs) > 12 else ''))
        self.dibujar()

    def saltar(self, paso):
        rs = sorted({r for r, _ in self.coinc})
        if rs:
            sig = [r for r in rs if (r - self.ronda) * paso > 0]
            self.ir((sig[0] if paso > 0 else sig[-1]) if sig else (rs[0] if paso > 0 else rs[-1]))

    # ---- exportar ----
    def renglones_export(self):
        c = self.p.cabecera
        enc = [c['nombre']] + [f"{rot} {self.datos[k]['text']}" for k, rot in DATOS] \
            + ([self.aviso['text']] if self.aviso['text'] else [])
        cuerpo = []
        for r in range(1, c['ronda'] + 1):
            cuerpo.append((r, [(self.p.jugador(j) if j < 8 else '', s) for j, s in self.rondas.get(r, [])]))
        return enc, cuerpo

    def exportar_pdf(self):
        if not self.p:
            return
        ruta = filedialog.asksaveasfilename(title='Exportar', defaultextension='.pdf',
                                            initialfile=self.p.cabecera['nombre'] + '.pdf', filetypes=[('PDF', '*.pdf')])
        if not ruta:
            return
        from fpdf import FPDF
        enc, cuerpo = self.renglones_export()
        fuentes = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts')
        pdf = FPDF(format='A4')
        pdf.set_auto_page_break(True, 15)
        pdf.add_font('ui', '', os.path.join(fuentes, 'arial.ttf'))
        pdf.add_font('ui', 'B', os.path.join(fuentes, 'arialbd.ttf'))
        unc = os.path.join(self.juego, 'FONTS', 'UNCIAL.TTF')
        tit = 'unc' if os.path.exists(unc) else 'ui'
        if tit == 'unc':
            pdf.add_font('unc', '', unc)
        pdf.add_page()
        pdf.set_font(tit, '', 20)
        pdf.cell(0, 12, 'History of Events', new_x='LMARGIN', new_y='NEXT', align='C')
        pdf.set_font('ui', 'B', 13)
        pdf.cell(0, 8, enc[0], new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('ui', '', 10)
        for s in enc[1:]:
            pdf.multi_cell(0, 5, s, new_x='LMARGIN', new_y='NEXT')
        for r, rs in cuerpo:
            pdf.ln(3)
            pdf.set_font('ui', 'B', 12)
            pdf.cell(0, 7, f'EVENTS FOR TURN {r}', new_x='LMARGIN', new_y='NEXT')
            pdf.set_font('ui', '', 10)
            for j, s in rs or [('', self.p.T[0][0])]:
                pdf.cell(42, 5, j)
                pdf.cell(0, 5, s, new_x='LMARGIN', new_y='NEXT')
        pdf.output(ruta)
        messagebox.showinfo(TITULO, f'Exportado:\n{ruta}')


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--version':   # lo usa la actualización para verificar lo bajado
        with open(sys.argv[2], 'w') as f:
            f.write(VERSION)
        sys.exit()
    fuente_privada(os.path.join(tanda.JUEGO, 'FONTS', 'UNCIAL.TTF'))
    raiz = tk.Tk()
    v = Visor(raiz)
    if len(sys.argv) > 1:
        v.abrir(sys.argv[1])
    raiz.mainloop()
