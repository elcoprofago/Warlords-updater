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

VERSION = '1.0.18.0'
TITULO = f'VISOR DE HISTORIA — VERSIÓN {VERSION}'
FONDO = '#1b1b1b'
TEXTO, SOMBRA, RESALTE = '#f0e6c8', '#000000', '#ffd966'
HOVER = '#ffd8a8'                      # naranja suave de los botones con el mouse encima
COLOR = {'white': (250, 250, 250), 'yellow': (240, 220, 40), 'orange': (240, 140, 30), 'red': (220, 30, 30),
         'green': (40, 180, 40), 'blue': (40, 80, 230), 'cyan': (60, 210, 230), 'black': (40, 40, 40)}
NEUTRAL = (150, 150, 150)
# Cuadro DLG_BIG (620x460): título en la barra de arriba, minimapa a la izquierda y renglones a la derecha.
TIT_Y, SUB_Y = 28, 72
# Colores de terreno del minimapa, tomados del mapa estratégico del juego (STRAT_L.BMP); el primero que coincide
TERRENO_COL = (('water', (8, 140, 232)), ('forest', (0, 128, 16)), ('mount', (110, 110, 110)), ('hill', (156, 156, 156)),
               ('marsh', (76, 112, 72)), ('desert', (212, 196, 124)), ('sand', (212, 196, 124)), ('ice', (230, 240, 250)),
               ('snow', (230, 240, 250)), ('road', (148, 92, 0)), ('plain', (136, 136, 44)))
BOSQUE = (0, 128, 16)                   # árboles dibujados sobre el llano (byte +6 de la casilla: historia.mapa)
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
ICONO = getattr(sys, '_MEIPASS', '') if getattr(sys, 'frozen', False) else CARPETA
DATOS = (('turnos', 'Turnos jugados:'), ('victoria', 'Victoria:'), ('mapa', 'Mapa:'), ('guardado', 'Último guardado:'),
         ('explorado', 'Explorado:'))   # este, solo con Hidden Map


def juego_de(sav):
    """Carpeta del juego: la de arriba de SAVES si tiene Sagetext.tex; si no, la de siempre."""
    j = os.path.dirname(os.path.dirname(os.path.abspath(sav)))
    return j if os.path.exists(os.path.join(j, 'Sagetext.tex')) else tanda.JUEGO


def leer_fin(sav):
    """Cómo terminó la partida: HISTORY\\<nombre>.FIN que deja el parche al lado de los <nombre>_<turno>.SAV
    (PENDIENTE-partidas-terminadas.md, B2). None si no hay."""
    base = os.path.splitext(os.path.basename(sav))[0]
    partes = base.rsplit('_', 1)
    nombres = [partes[0], base] if len(partes) == 2 and partes[1].isdigit() else [base]
    for n in nombres:
        ruta = os.path.join(os.path.dirname(sav), n + '.FIN')
        if os.path.exists(ruta):
            break
    else:
        return None
    fin = {'cierre': '', 'turno': '', 'bandos': [], 'texto': ''}
    with open(ruta, encoding='mbcs', errors='replace') as f:
        for renglon in f:
            clave, _, valor = renglon.rstrip('\n').partition('=')
            if clave == 'bando':
                try:
                    fin['bandos'].append(tuple(int(x) for x in valor.split(',')))
                except ValueError:
                    pass
            elif clave in fin:
                fin[clave] = valor
    return fin


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


def guardar_config(seccion='Fondo', **valores):
    c = configparser.ConfigParser(); c.read(CONFIG); c[seccion] = valores   # las otras secciones quedan
    with open(CONFIG, 'w') as f:
        c.write(f)


def carpeta_abrir():
    """Dónde arranca «Abrir…»: la última carpeta usada; si no, HISTORY (las partidas terminadas); si no, SAVES."""
    c = configparser.ConfigParser(); c.read(CONFIG)
    ultima = c.get('Abrir', 'carpeta', fallback='')
    if os.path.isdir(ultima):
        return ultima
    return next((os.path.join(j, d) for d in ('HISTORY', 'SAVES') for j in (tanda.JUEGO, r'C:\Warlords')
                 if os.path.isdir(os.path.join(j, d))), None)


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



def reborde(padre):
    """Reborde de los cuadros de texto como el del minimapa: dorado ancho por fuera y una línea negra por dentro.
    Devuelve el marco interior (donde va el cuadro); el exterior, que se ubica, es su .master."""
    oro = tk.Frame(padre, bg='#c8a040', padx=3, pady=3)
    negro = tk.Frame(oro, bg='#000000', padx=1, pady=1)
    negro.pack()
    return negro

class Visor:
    def __init__(self, raiz):
        self.raiz, self.p, self.ronda, self.color = raiz, None, 1, 0
        self.coinc, self.imgs = [], []
        self.cajas, self.rotulos, self.fotos = [], [], {}
        self.mosaico, self.base, self.tinta = None, FONDO, self.tintas((27, 27, 27))
        raiz.title(TITULO)
        # Ícono de la aplicación: la medalla de cinta roja de ICONS.PCX del juego (medalla.png; en el .exe va adentro y
        # además es su ícono, medalla.ico: build.py). Vale para todas las ventanas.
        self.icono = ImageTk.PhotoImage(Image.open(os.path.join(ICONO, 'medalla.png')))
        raiz.iconphoto(True, self.icono)
        raiz.resizable(False, False)
        self.f_ren = tkfont.Font(family='Arial', size=11)
        fams = set(tkfont.families())
        self.f_tit = tkfont.Font(family='Uncial ATT' if 'Uncial ATT' in fams else 'Times New Roman', size=18)
        self.f_sub = tkfont.Font(family='Arial', size=10, weight='bold')   # la letra de los renglones, en mayúsculas
        self.fondo_v = tk.Label(raiz, bd=0)
        self.fondo_v.place(x=0, y=0, relwidth=1, relheight=1)

        # Panel superior: el nombre en un cuadro blanco; rótulos y datos en dos colores
        sup = self.caja(raiz)
        sup.configure(padx=10, pady=8)
        sup.pack(fill='x')
        boton(sup, text='Abrir…', width=10, command=self.abrir).grid(row=0, column=0, sticky='w', padx=(0, 14), pady=(0, 4))
        marco = reborde(sup)
        marco.master.grid(row=0, column=1, sticky='w', pady=(0, 4))
        self.d_nombre = tk.Entry(marco, font=('Segoe UI', 13, 'bold'), readonlybackground='#ffffff', fg='#000000',
                                 relief='flat', bd=0, width=26, state='readonly')
        self.d_nombre.pack()
        # Luces «Single» y «Multi» a la derecha del nombre, según el modo guardado en la partida
        # (en la misma fila del nombre, que es corto: no ensanchan la ventana más allá del cuadro del medio)
        sup.columnconfigure(3, weight=1)
        self.b_fin = boton(sup, text='Resultado', command=self.ver_fin, state='disabled')
        self.b_fin.grid(row=0, column=2, sticky='e', padx=(10, 0), pady=(0, 4))
        luces = self.caja(sup)
        luces.grid(row=0, column=3, sticky='e')
        self.luces = {m: self.luz(luces, m) for m in ('Single', 'Multi')}
        self.datos = {}
        # Los datos en una grilla propia, a lo ancho del panel: así «Victoria:» queda cerca del medio
        dat = self.caja(sup)
        dat.grid(row=1, column=0, columnspan=4, sticky='we')
        dat.columnconfigure(1, minsize=190)
        for i, (clave, rot) in enumerate(DATOS):
            f, c = 1 + i // 2, 2 * (i % 2)   # rótulos al margen izquierdo, los dos primeros debajo de «Abrir…»
            self.rotulo(dat, 'etiqueta', text=rot, font=('Segoe UI', 9, 'bold')).grid(
                row=f, column=c, sticky='w', padx=(0 if c == 0 else 16, 4), pady=(8 if f == 1 else 0, 0))
            self.datos[clave] = self.rotulo(dat, 'valor', wraplength=165, justify='left', font=('Segoe UI', 9))
            self.datos[clave].grid(row=f, column=c + 1, sticky='w', pady=(8 if f == 1 else 0, 0))
            self.datos[clave].rot = self.rotulos[-2] if len(self.rotulos) > 1 else None
        self.aviso = self.rotulo(raiz, 'aviso', font=('Segoe UI', 9), wraplength=620, justify='left')
        # (solo ocupa lugar cuando hay aviso: ver abrir)

        # Coincidencias de la búsqueda (el buscador está en el panel inferior)
        self.raya = tk.Frame(raiz, bg='#444', height=1)
        self.raya.pack(fill='x', padx=10, pady=(0, 4))
        bus = self.caja(raiz)
        bus.configure(padx=10)
        bus.pack(fill='x')
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
        self.rotulo(inf, 'etiqueta', text='Buscar:').pack(side='left')
        self.buscar = tk.StringVar()
        self.buscar.trace_add('write', lambda *_: self.al_buscar())
        marco = reborde(inf)
        marco.master.pack(side='left', padx=6)
        e = tk.Entry(marco, textvariable=self.buscar, width=18, font=('Segoe UI', 10), relief='flat', bd=0)
        e.pack()
        e.bind('<Return>', lambda _: self.saltar(1))
        boton(inf, text='◀', width=3, command=lambda: self.saltar(-1)).pack(side='left')
        boton(inf, text='▶', width=3, command=lambda: self.saltar(1)).pack(side='left', padx=(2, 6))
        boton(inf, text='Limpiar', command=lambda: self.buscar.set('')).pack(side='left')
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
        return {'etiqueta': '#f5ecd0', 'valor': '#9fd3ff', 'aviso': '#ff7070'}

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
        for estado, brillo in (('on', 1.3), ('off', 0.4)):   # encendida brillante; apagada: la misma oscura
            c = Image.merge('HSV', (h.point(lambda x: 0), s.point(lambda x: x * 0.8), v.point(lambda x: min(255, x * brillo)))).convert('RGBA')
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
        bat, pid = actual[:-4] + '.actualizar.bat', os.getppid()   # el cargador de PyInstaller: sale último
        with open(bat, 'w', encoding='mbcs') as f:
            f.write('@echo off\n:espera\n'
                    f'tasklist /FI "PID eq {pid}" /NH | find "{pid}" >nul && (timeout /t 1 /nobreak >nul & goto espera)\n'
                    f'move /y "{nuevo}" "{actual}" >nul\nstart "" "{actual}"\ndel "%~f0"\n')
        # El .exe nuevo tiene la misma ruta que este: si heredara las variables de PyInstaller se creería hijo de
        # este proceso y usaría su carpeta _MEI, que se borra al cerrar («Failed to remove temporary directory»).
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith(('_PYI', '_MEI'))}
        env['PYINSTALLER_RESET_ENVIRONMENT'] = '1'
        subprocess.Popen(['cmd', '/c', bat], creationflags=subprocess.CREATE_NO_WINDOW, env=env)
        self.raiz.destroy()

    # ---- datos ----
    def abrir(self, ruta=None):
        if not ruta:
            ruta = filedialog.askopenfilename(title='Abrir partida', initialdir=carpeta_abrir(),
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
        guardar_config('Abrir', carpeta=os.path.dirname(os.path.abspath(ruta)))
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
        if p.ajena:
            self.aviso.pack(fill='x', padx=10, before=self.raya)
        else:
            self.aviso.pack_forget()
        for w in (self.datos['explorado'], self.datos['explorado'].rot):   # solo en partidas con mapa oculto
            if w is not None:
                (w.grid if c['oculto'] else w.grid_remove)()
        self.fin = leer_fin(ruta)
        self.b_fin.configure(state='normal' if self.fin else 'disabled')
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
        # Color de cada terreno del mapa: el del mapa estratégico del juego (STRAT_L.BMP) según el nombre del terreno;
        # los que no están ahí, el promedio de su textura
        self.tcol = []
        for nombre, tex in historia.terrenos(p.d):
            col = next((c for k, c in TERRENO_COL if k in nombre.lower()), None)
            if col:
                self.tcol.append(col)
                continue
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

    def texto_sombra(self, x, y, s, fuente, anchor='nw', color=TEXTO):
        self.cv.create_text(x + 1, y + 1, text=s, font=fuente, fill=SOMBRA, anchor=anchor)
        self.cv.create_text(x, y, text=s, font=fuente, fill=color, anchor=anchor)

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
        self.texto_sombra(REN_X + 175, SUB_Y, f'EVENTS FOR TURN {self.ronda}', self.f_sub, 'n', '#8b6914')
        self.dibujar_minimapa()
        self.datos['explorado']['text'] = f"{historia.explorado(self.mapa, self.color):.0f} %" if self.p.cabecera['oculto'] else ''
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
                    t, ex, adorno = m[y][x]
                    col = BOSQUE if adorno in (72, 96) else self.tcol[t] if t < len(self.tcol) else (90, 90, 90)
                    px[x, y] = col if ex & bit else (0, 0, 0)
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

    # ---- resultado: el cartel del fin con el arte del set (DLG_MED, escudos, pvictory.pcx), en inglés como el juego ----
    def ver_fin(self):
        """Como el cartel del juego al terminar (captura del 2/11/2026): título en la barra, una línea debajo, columnas
        SIDE / VPs / CITIES / GOLD, escudo chico y nombre en el color del bando. La victoria sin Game Over, como el juego:
        «Total victory!» (un solo bando en pie) o «An allied victory!» y la imagen pvictory.pcx enmarcada."""
        fin, p = self.fin, self.p
        if not fin or not p:
            return
        sets = os.path.join(self.juego, 'SETS', p.cabecera['set'])
        v = tk.Toplevel(self.raiz)
        v.title('Final por acuerdo' if fin['cierre'] == 'acuerdo' else 'Resultado'); v.transient(self.raiz); v.resizable(False, False)
        cv = tk.Canvas(v, width=520, height=376, highlightthickness=0, bg='#000')
        cv.pack()
        cv.imgs = []

        def img(im, x, y, anchor='nw'):
            cv.imgs.append(ImageTk.PhotoImage(im))
            cv.create_image(x, y, image=cv.imgs[-1], anchor=anchor)

        def txt(x, y, s, fuente, anchor='nw', fill='#ffffff', **kw):
            cv.create_text(x + 1, y + 1, text=s, font=fuente, fill=SOMBRA, anchor=anchor, **kw)
            cv.create_text(x, y, text=s, font=fuente, fill=fill, anchor=anchor, **kw)
        img(pcx_rgba(os.path.join(sets, 'DLG_MED.PCX')).crop((0, 0, 520, 376)), 0, 0)   # el cuadro; el resto del PCX es blanco
        cierre = fin['cierre']
        limite = ''.join(c for c in str(p.cabecera['limite'] or '') if c.isdigit())   # viene como «35 turnos»
        titulo = {'podio': 'Game Over!', 'aliada': 'Victory!', 'acuerdo': 'Peace Agreement'}.get(cierre, cierre)
        cv.create_text(258, 25, text=titulo, font=self.f_tit if cierre == 'acuerdo' else ('Times New Roman', 18, 'bold'),
                       fill='#20206a')
        linea = {'podio': f'{limite} turns have passed!' if limite else f"Turn {fin['turno']}",
                 'aliada': 'Total victory!' if len(fin['bandos']) == 1 else 'An allied victory!', 'acuerdo': f"Terminada por acuerdo/votación al {fin['turno']}.º turno"}
        if cierre == 'acuerdo':   # la letra de los sucesos, más chica, en bermellón
            txt(260, 60, linea[cierre], ('Arial', 10), 'n', fill='#e34234')
        else:
            txt(260, 58, linea.get(cierre, ''), ('Segoe UI', 12), 'n')
        if cierre == 'acuerdo':
            # el papiro del juego (DLG_HELP.PCX, 250x150) agrandado, con el texto en letra manuscrita, negro y a la izquierda
            pap = os.path.join(sets, 'DLG_HELP.PCX')
            if os.path.exists(pap):
                img(pcx_rgba(pap).resize((440, 260), Image.LANCZOS), 260, 88, 'n')
            else:
                cv.create_rectangle(50, 92, 470, 315, fill='#e8d8a8', outline='#c8a040', width=4)
            cv.create_text(140, 125, text=fin['texto'] or '(sin texto)', width=255, anchor='nw', justify='left',
                           font=('Segoe Print', 13), fill='#000000')
        elif cierre == 'aliada':
            pv = os.path.join(sets, 'pvictory.pcx')
            if os.path.exists(pv):
                cv.create_rectangle(155, 89, 365, 341, outline='#c8a040', width=4)
                cv.create_rectangle(160, 94, 360, 336, outline='#8080c0', width=1)
                img(Image.open(pv).convert('RGB').resize((198, 240)), 161, 95)
        else:
            f = ('Segoe UI', 10)
            col = (95, 145, 330, 390, 455)   # puesto, escudo + SIDE, VPs, CITIES, GOLD (estas tres centradas)
            y = 88
            for x, rot in zip(col[1:], ('SIDE', 'VPs', 'CITIES', 'GOLD')):
                txt(x, y, rot, f, 'nw' if rot == 'SIDE' else 'n')
            y += 30
            puesto = 0
            for pu, k, puntos, ciudades, oro in fin['bandos'][:8]:
                if pu > 0:
                    puesto = pu
                if cierre == 'podio':
                    txt(col[0], y, str(puesto), f, 'n')
                if k in self.escudos:
                    img(self.escudos[k][0], col[1], y + 2)
                txt(col[1] + 20, y, p.jugador(k) if 0 <= k < 8 else '?', f,
                    fill='#%02x%02x%02x' % (c if sum(c := self.colores.get(k, NEUTRAL)) > 200 else (120, 120, 120)))   # negro → gris
                for x, n in zip(col[2:], (puntos, ciudades, oro)):
                    txt(x, y, str(n), f, 'n')
                y += 26
        v.bind('<Escape>', lambda e: v.destroy())
        v.bind('<Return>', lambda e: v.destroy())

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
        enc = [c['nombre']] + [f"{rot} {self.datos[k]['text']}" for k, rot in DATOS if k != 'explorado'] \
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
        if self.p.cabecera['oculto']:   # mapa oculto: lo explorado por cada bando, como lo revela el minimapa
            pdf.ln(3)
            pdf.set_font('ui', 'B', 10)
            pdf.cell(60, 6, 'SIDE', border=1)
            pdf.cell(45, 6, 'Explorado', border=1, align='C', new_x='LMARGIN', new_y='NEXT')
            pdf.set_font('ui', '', 10)
            for k in range(8):
                if self.p.juega(k):
                    pdf.cell(60, 6, self.p.jugador(k), border=1)
                    pdf.cell(45, 6, f'{historia.explorado(self.mapa, k):.0f} %', border=1, align='C',
                             new_x='LMARGIN', new_y='NEXT')
            pdf.set_font('ui', '', 8)
            pdf.cell(0, 5, 'Al último guardado: el .SAV no registra la exploración turno a turno.',
                     new_x='LMARGIN', new_y='NEXT')
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
