# Tablero del simulador de combate (etapa 3 de PENDIENTE-simulador-combate.md): la ventana donde se arman las dos pilas.
# Dos paneles gemelos (atacante y defensor) con 8 casilleros numerados = fight order (arma y cantidad), barco
# del bando y héroe (subpanel: clase, nivel, elecciones, ítems y hechizos); subpanel de terreno y subpanel visual
# (se guarda para la ventana de combate, etapa 4). INICIAR COMBATE arma el escenario (escenario.py) y muestra el % de
# victorias y abre la ventana de combate (combate.py) con una batalla de muestra. Uso: python tablero.py
import configparser, json, os, struct, subprocess, sys, threading, time, urllib.request, webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font as tkfont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from escenario import Simulador, Error, MAX_PILA, TOPE_CIUDAD   # noqa: E402
from datos import HABILIDADES, SIN_VALOR           # noqa: E402
from combate import VentanaCombate, pcx            # noqa: E402
import contador, historial, imagenes               # noqa: E402
from PIL import Image, ImageTk                     # noqa: E402

VERSION = '1.0.41.0'
TITULO = f'SIMULADOR DE COMBATE — VERSIÓN {VERSION}'
CARPETA = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))
CONFIG = os.path.join(CARPETA, 'Simulador-Combate.ini')
HISTORIAL = os.path.join(CARPETA, 'Simulador-Combate-historial.json')
REPO = 'elcoprofago/Simulador-Combate'   # repo público donde se publican las releases del .exe (el fuente vive acá)
EXE_REL = 'Simulador-Combate.exe'
# El ícono de configuración es el del Monitor de IA (ia\monitor-ia\assets); en el .exe va adentro (build.py).
ASSETS = os.path.join(getattr(sys, '_MEIPASS', ''), 'assets') if getattr(sys, 'frozen', False) else \
    os.path.join(os.path.dirname(CARPETA), 'ia', 'monitor-ia', 'assets')
CORREO = 'ra.alvarito@gmail.com'

def version_tupla(v):
    return tuple(int(x) for x in v.split('.'))

def version_de(exe):
    """La versión que trae adentro un Simulador-Combate.exe (se le pregunta con --version; lo usa publicar.py)."""
    marca = exe + '.version'
    subprocess.run([exe, '--version', marca], timeout=120, creationflags=subprocess.CREATE_NO_WINDOW)
    with open(marca) as f: v = f.read().strip()
    os.remove(marca)
    return v
JUEGO0 = r'C:\Warlords3'
# Bosques del desplegable de terreno: en los mapas un bosque es la capa «woods» sobre llanura o colinas (el terreno
# «forest» no aparece en ningún mapa y el motor no lo cuenta como bosque). Texto -> terreno real con capa de bosque.
BOSQUES = {'forest': 'plains', 'hills con bosque': 'hills'}
# Lo que hay en la casilla del defensor: (texto, clave, estructura de escenario.py, obra de vista-aliada)
SITIOS = (('Nada', 'nada', 0, None), ('Camino / puente', 'camino', 1, None), ('Ciudad', 'ciudad', 3, None),
          ('Faro', 'faro', 0, 'faro'), ('Torre de vigía', 'torre', 0, 'torre'), ('Muralla', 'muro', 0, 'muro'))
MURO_TXT = 'Missiles +3, Acid +3, Fortify +3'
# Defensas que ofrece el desplegable según el sitio: (texto, nivel de la ciudad, obra)
DEFENSAS = {'nada': [], 'camino': [],
            'ciudad': [(f'Nivel {n} (Life Ward +{n})', n, None) for n in (1, 2, 3)] +
                      [(f'Nivel {n} con muralla al lado (Life Ward +3, {MURO_TXT})', n, 'muro') for n in (1, 2, 3)],
            'faro': [('Life Ward +1, fuerza +1 (no héroes)', 1, 'faro')],
            'torre': [('Life Ward +2, fuerza +1 (no héroes)', 1, 'torre')],
            'muro': [(f'Life Ward +3, {MURO_TXT}', 1, 'muro')]}
ORO = '#c8a040'

# Colores de cada bando (pedido del usuario, 5/11/2026): atacante en azules, defensor en rojos.
BANDOS = {'ATACANTE': dict(oscuro='#001a66', medio='#0050d0', claro='#38a8ff', letra='#0a3c9c', suave='#a8d4ff', escudo='Cbludrag.PCX'),
          'DEFENSOR': dict(oscuro='#5a0000', medio='#c01818', claro='#ff6040', letra='#9c1010', suave='#ffb0a0', escudo='Creddrag.PCX')}

FUENTE_TITULO = ('Arial', 17, 'bold')

def letra_titulo(cv, cx, cy, texto, borde, recuadro=True, fondo='#ffffff'):
    """Título de panel: recuadro blanco con borde fino oscuro y, adentro, el texto en Arial bold blanco con borde
    del color pedido (negro en los bandos, verde en el terreno) y sombra. Devuelve el ancho del recuadro."""
    f = tkfont.Font(font=FUENTE_TITULO); w, h = f.measure(texto) + 20, f.metrics('linespace') + 6
    if recuadro: cv.create_rectangle(cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2, fill=fondo, outline='#202020', width=1)
    cv.create_text(cx + 2, cy + 2, text=texto, font=FUENTE_TITULO, fill='#9a9a9a')               # sombra
    for dx, dy in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)):
        cv.create_text(cx + dx, cy + dy, text=texto, font=FUENTE_TITULO, fill=borde)            # borde de la letra
    cv.create_text(cx, cy, text=texto, font=FUENTE_TITULO, fill='#ffffff')
    return w

def mezcla(a, b, t):
    a, b = [int(a[i:i + 2], 16) for i in (1, 3, 5)], [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02x%02x%02x' % tuple(round(x + (y - x) * t) for x, y in zip(a, b))

class Estandarte(tk.Canvas):
    """Encabezado de un panel: franja degradada del color del bando, el escudo del dragón del juego (SHIELD) a cada
    lado y el nombre del bando en blanco con sombra."""
    def __init__(self, padre, titulo, juego):
        super().__init__(padre, height=48, highlightthickness=0, bd=0, bg='#000000')
        self.titulo, self.c = titulo, BANDOS[titulo]; self.fotos = []
        try:
            from combate import pcx
            im = pcx(os.path.join(juego, 'SHIELD', self.c['escudo']))
            im = im.crop((1, 1, 32, 37)) if im is not None else None
        except Exception: im = None
        if im is not None:
            from PIL import ImageOps
            im = im.resize((im.width * 6 // 5, im.height * 6 // 5), Image.NEAREST)
            self.fotos = [ImageTk.PhotoImage(im), ImageTk.PhotoImage(ImageOps.mirror(im))]
        self.bind('<Configure>', lambda e: self.dibujar())
    def dibujar(self):
        self.delete('all'); w, h, c = self.winfo_width(), int(self['height']), self.c
        for x in range(0, w, 2):
            t = 1 - abs(x / max(w - 1, 1) - 0.5) * 2
            col = mezcla(c['oscuro'], c['medio'], min(t * 1.6, 1)) if t < 0.62 else mezcla(c['medio'], c['claro'], (t - 0.62) / 0.38)
            self.create_rectangle(x, 0, x + 2, h, fill=col, outline='')
        self.create_line(0, 1, w, 1, fill=ORO, width=2); self.create_line(0, h - 2, w, h - 2, fill=ORO, width=2)
        if self.fotos:
            self.create_image(8, h // 2, image=self.fotos[1], anchor='w'); self.create_image(w - 8, h // 2, image=self.fotos[0], anchor='e')
        letra_titulo(self, w // 2, h // 2, self.titulo, '#000000', recuadro=False)   # sin recuadro: sobre la franja

def titulo_verde(padre, texto, aclaracion=''):
    """Título de subpanel: mismo estilo que los estandartes (letra_titulo), con el borde de la letra verde."""
    fondo = ttk.Style(padre).lookup('TFrame', 'background') or '#f0f0f0'
    f = tk.Frame(padre, bg=fondo); fn = tkfont.Font(font=FUENTE_TITULO)
    w, h = fn.measure(texto) + 22, fn.metrics('linespace') + 8
    cv = tk.Canvas(f, width=w, height=h, bg=fondo, highlightthickness=0); cv.pack(side='left')
    letra_titulo(cv, w // 2, h // 2, texto, '#0a8a28', fondo='#d2b48c')   # recuadro marrón claro
    if aclaracion: tk.Label(f, text=aclaracion, bg=fondo).pack(side='left', padx=(2, 0), pady=(6, 0))
    return f

def reborde(padre, color='#000000'):
    """Reborde dorado como el de los cuadros de texto del Visor de historia: dorado ancho por fuera y una línea negra
    por dentro. Devuelve el marco interior (donde va el widget); el exterior, que se ubica, es su .master."""
    oro = tk.Frame(padre, bg=ORO, padx=3, pady=3)
    negro = tk.Frame(oro, bg=color, padx=1 if color == '#000000' else 3, pady=1 if color == '#000000' else 3)
    negro.pack(fill='both', expand=True)
    return negro

def plegable(app, partes, clave):
    """Una flecha ▲/▼ (en la esquina del último reborde) que contrae juntas todas las partes [(caja, contenido)]:
    queda solo el título de cada una. En pantallas bajas (notebook) el tablero entero no entra; lo plegado se
    recuerda en el .ini."""
    caja = partes[-1][0]; exterior = caja.master; datos = []
    for cj, contenido in partes:
        info = contenido.pack_info(); info.pop('in', None)
        datos.append((contenido, info, tk.Frame(cj, height=18, width=150, bg=cj['bg'])))   # un marco sin hijos no se achica en Tk
    f = tk.Label(exterior, bg=ORO, fg='#000000', font=('Segoe UI', 9, 'bold'), cursor='hand2', padx=3, pady=0, bd=1, relief='raised')
    def poner(plegado):
        for contenido, info, relleno in datos:
            if plegado: contenido.pack_forget(); relleno.pack(fill='x')
            else: relleno.pack_forget(); contenido.pack(**info)
        f['text'] = '▼' if plegado else '▲'; app.plegados[clave] = plegado; f.lift()
    f.bind('<Button-1>', lambda e: poner(not app.plegados[clave]))
    f.place(relx=1, x=0, y=0, anchor='ne')
    poner(app.cfg['tablero'].getboolean(f'plegado_{clave}', False))

def boton(padre, **kw):
    """Un botón con reborde dorado; devuelve el marco a ubicar (el botón queda en .boton)."""
    m = reborde(padre); b = ttk.Button(m, **kw); b.pack(fill='both', expand=True); m.master.boton = b
    return m.master

class BotonAzul(tk.Canvas):
    """Botón dibujado: fondo azul claro, letra blanca con sombra negra. Acepta .state(['disabled'/'!disabled'])
    como un ttk.Button."""
    AZUL, AZUL_SOBRE, AZUL_APAGADO = '#5aa8e6', '#7cbcf0', '#9db4c6'
    def __init__(self, padre, text, command, ancho=170, alto=30):
        super().__init__(padre, width=ancho, height=alto, highlightthickness=0, bd=0, cursor='hand2')
        self.texto, self.cmd, self.ancho, self.alto, self.activo, self.sobre = text, command, ancho, alto, True, False
        self.bind('<Enter>', lambda e: self.poner(sobre=True)); self.bind('<Leave>', lambda e: self.poner(sobre=False))
        self.bind('<ButtonRelease-1>', lambda e: self.activo and self.cmd())
        self.dibujar()
    def poner(self, sobre): self.sobre = sobre; self.dibujar()
    def state(self, estados):
        for e in estados:
            if e == 'disabled': self.activo = False
            elif e == '!disabled': self.activo = True
        self.configure(cursor='hand2' if self.activo else ''); self.dibujar()
    def dibujar(self):
        self.delete('all')
        # Degradé de izquierda a derecha como el escudo azul del juego: bordes oscuros, brillo a un tercio.
        pasos = [(0, (0x00, 0x2f, 0x9f)), (.12, (0x00, 0x6b, 0xe3)), (.33, (0x17, 0xa7, 0xf3)), (.55, (0x00, 0x77, 0xe7)),
                 (.75, (0x00, 0x6b, 0xe3)), (.9, (0x00, 0x43, 0xb7)), (1, (0x00, 0x2f, 0x9f))]
        for x in range(self.ancho):
            t = x / (self.ancho - 1)
            (t0, c0), (t1, c1) = next((pasos[i], pasos[i + 1]) for i in range(len(pasos) - 1) if t <= pasos[i + 1][0])
            k = (t - t0) / (t1 - t0); rgb = [a + (b - a) * k for a, b in zip(c0, c1)]
            if not self.activo: g = sum(rgb) / 3; rgb = [(v + g * 2) / 3 for v in rgb]
            elif self.sobre: rgb = [v + (255 - v) * .15 for v in rgb]
            self.create_line(x, 0, x, self.alto, fill='#%02x%02x%02x' % tuple(int(v) for v in rgb))
        f = ('Segoe UI', 10, 'bold'); x, y = self.ancho // 2, self.alto // 2
        self.create_text(x + 2, y + 2, text=self.texto, font=f, fill='#000000')
        self.create_text(x, y, text=self.texto, font=f, fill='#ffffff')

def elecciones(clase):
    """Las 10 elecciones de una clase (.HER) y los puntos por nivel: [(texto, costo)], [puntos de cada subida]."""
    r = clase.registro; out = []
    for i in range(10):
        hab, val = struct.unpack_from('<hh', r, 0x3fc + 16 * i); costo = struct.unpack_from('<h', r, 0x49c + 2 * i)[0]
        if not hab: out.append(('', 0)); continue
        n = HABILIDADES.get(hab, f'Ability_{hab}')
        if hab == 20: n = 'Spell ' + r[0x3fc + 16 * i + 6:0x3fc + 16 * i + 16].split(b'\0')[0].decode('latin-1')
        elif hab not in SIN_VALOR: n += f' +{val}'
        out.append((n, costo))
    return out, list(struct.unpack_from('<9h', r, 0x3e8))

class Deslizador(tk.Canvas):
    """Barra deslizante con la bola dorada de la barra de rondas del Visor de historia (riel gris, bola dorada con
    borde negro), en lugar del rectángulo azul de ttk.Scale."""
    def __init__(self, padre, variable, desde, hasta, ancho=130):
        fondo = ttk.Style(padre).lookup('TFrame', 'background') or '#f0f0f0'
        super().__init__(padre, width=ancho, height=22, bg=fondo, highlightthickness=0, cursor='hand2')
        self.var, self.desde, self.hasta, self.ancho = variable, desde, hasta, ancho
        self.bind('<Button-1>', self.clic); self.bind('<B1-Motion>', self.clic)
        variable.trace_add('write', lambda *a: self.dibujar()); self.dibujar()
    def x(self, v): return 9 + (self.ancho - 18) * (v - self.desde) / (self.hasta - self.desde)
    def clic(self, e):
        v = round(self.desde + (e.x - 9) * (self.hasta - self.desde) / (self.ancho - 18))
        self.var.set(max(self.desde, min(self.hasta, v)))
    def dibujar(self):
        self.delete('all'); x = self.x(self.var.get())
        self.create_line(9, 11, self.ancho - 9, 11, fill='#777', width=3)
        self.create_oval(x - 7, 4, x + 7, 18, fill=ORO, outline='#000')

class RecuadroFactor(tk.Frame):
    """El Factor total de la pila: fondo negro, letra blanca con sombra gris, borde dorado (pedido del usuario,
    5/11/2026: el fondo de la app irá pareciéndose al del juego)."""
    def __init__(self, padre, bando=None):
        super().__init__(padre, bg=BANDOS[bando]['medio'] if bando else ORO, padx=3, pady=3)
        self.claro = BANDOS[bando]['suave'] if bando else '#ffffff'
        negro = tk.Frame(self, bg='#000000', padx=1, pady=1); negro.pack(fill='x')
        self.cv = tk.Canvas(negro, height=50, bg='#000000', highlightthickness=0); self.cv.pack(fill='x')
        self.cv.bind('<Configure>', lambda e: self.dibujar()); self.t = ('', '')
    def poner(self, grande, chico):
        self.t = (grande, chico); self.dibujar()
    def dibujar(self):
        cv = self.cv; cv.delete('all'); w = cv.winfo_width() // 2
        # FACTOR y COSTO en dorado con borde verde, igual en los dos bandos (pedido del usuario, 5/11/2026)
        for dx, dy in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1), (2, 2)):
            cv.create_text(w + dx, 18 + dy, text=self.t[0], font=('Arial', 15, 'bold'), fill='#0a7a1e')
        cv.create_text(w, 18, text=self.t[0], font=('Arial', 15, 'bold'), fill='#ffd040')
        for dx, col in ((1, '#707070'), (0, '#ffffff')):
            cv.create_text(w + dx, 40 + dx, text=self.t[1], font=('Arial', 9, 'bold'), fill=col)

class LuzTope(ttk.Frame):
    """Luz roja «tope excedido»: la del Monitor de IA (circle_09.png del Monitor llevada a rojo, con marco.png, 26 px),
    que titila con un fundido lento (2 s por ciclo) mientras la pila pase su tope."""
    TAM, PASOS, CICLO_MS = 26, 16, 2000

    def __init__(self, padre):
        super().__init__(padre)
        bg = ttk.Style(self).lookup('TFrame', 'background') or '#f0f0f0'
        try:
            marco = Image.open(os.path.join(ASSETS, 'marco.png')).convert('RGBA')
            naranja = Image.open(os.path.join(ASSETS, 'circle_09.png')).convert('RGBA')
            h, sat, v = naranja.convert('HSV').split()
            def tono(f):
                im = Image.merge('HSV', (h.point(lambda x: 0), sat, v.point(f))).convert('RGBA')
                im.putalpha(naranja.getchannel('A')); im.alpha_composite(marco.resize(im.size))
                return im.resize((self.TAM, self.TAM), Image.LANCZOS)
            roja, apagada = tono(lambda x: x), tono(lambda x: x * 0.3)
            c = [Image.blend(apagada, roja, i / (self.PASOS - 1)) for i in range(self.PASOS)]
            self.cuadros = [ImageTk.PhotoImage(i) for i in c + c[-2:0:-1]]
        except OSError: self.cuadros = []
        self.l_img = tk.Label(self, bg=bg, bd=0)
        if self.cuadros: self.l_img.configure(image=self.cuadros[0])
        self.l_img.pack(side='left')
        self.l_txt = tk.Label(self, text='', bg=bg, fg='#606060', font=('Segoe UI', 8, 'bold'))
        self.l_txt.pack(side='left', padx=(4, 0))
        self.encendida, self.cuadro = False, 0

    def poner(self, si, cuenta=''):
        """cuenta = 'unidades / tope'; encendida: «tope excedido 9 / 8» en rojo; apagada: «8 / 8» en gris."""
        self.l_txt.configure(text=f'tope excedido  {cuenta}' if si else cuenta, fg='#b00000' if si else '#606060')
        if si and not self.encendida:
            self.encendida, self.cuadro = True, 0; self.titilar()
        elif not si and self.encendida:
            self.encendida = False
            if self.cuadros: self.l_img.configure(image=self.cuadros[0])

    def titilar(self):
        if not self.encendida or not self.cuadros: return
        self.l_img.configure(image=self.cuadros[self.cuadro % len(self.cuadros)]); self.cuadro += 1
        self.after(self.CICLO_MS // len(self.cuadros), self.titilar)

class Panel(ttk.Frame):
    """Un lado: 8 casilleros, barco, héroe y Factor total, con los colores de su bando."""
    def __init__(self, app, padre, titulo):
        super().__init__(padre, padding=6)
        self.app = app; self.heroe = None; b = BANDOS[titulo]
        st = ttk.Style(self); est = f'{titulo}.TLabel'
        st.configure(est, foreground=b['letra'], font=('Segoe UI', 9, 'bold'))
        ttk.Label(self, text='N.º', style=est).grid(row=0, column=0); ttk.Label(self, text='Arma', style=est).grid(row=0, column=1, sticky='w')
        ttk.Label(self, text='Cant.', style=est).grid(row=0, column=2)
        self.armas, self.cant = [], []
        self.arrastre = None
        for k in range(8):
            n = ttk.Label(self, text=f'☰ {k + 1}', cursor='fleur', style=est); n.grid(row=k + 1, column=0, padx=(0, 4))
            n.bind('<ButtonPress-1>', lambda e, k=k: self.tomar(k))
            n.bind('<B1-Motion>', self.mover)
            n.bind('<ButtonRelease-1>', self.soltar)
            cb = ttk.Combobox(self, width=34, state='readonly'); cb.grid(row=k + 1, column=1, pady=1)
            sp = ttk.Spinbox(self, from_=0, to=TOPE_CIUDAD, width=4, command=self.recalcular); sp.set(0)
            sp.grid(row=k + 1, column=2, padx=4)
            cb.bind('<<ComboboxSelected>>', lambda e, s=sp: (s.get() == '0' and s.set(1), self.recalcular()))
            sp.bind('<KeyRelease>', lambda e: self.recalcular())
            self.armas.append(cb); self.cant.append(sp)
        f = ttk.Frame(self); f.grid(row=9, column=0, columnspan=3, sticky='we', pady=(6, 0))
        ttk.Label(f, text='Barco', style=est).grid(row=0, column=0, sticky='w')
        self.barco = ttk.Combobox(f, width=28, state='readonly'); self.barco.grid(row=0, column=1, sticky='w')
        self.barco.bind('<<ComboboxSelected>>', lambda e: self.recalcular())
        self.con_heroe = tk.BooleanVar()
        ttk.Checkbutton(f, text='Héroe', variable=self.con_heroe, command=self.recalcular).grid(row=2, column=0, sticky='w', pady=(8, 0))
        fh = ttk.Frame(f); fh.grid(row=2, column=1, sticky='w', pady=(8, 0))
        boton(fh, text='Héroe…', command=self.editar_heroe).pack(side='left')
        self.luz = LuzTope(fh); self.luz.pack(side='left', padx=(10, 0))
        self.txt_heroe = ttk.Label(f, text='(sin armar)'); self.txt_heroe.grid(row=3, column=0, columnspan=2, sticky='w')
        self.coef = RecuadroFactor(self, titulo); self.coef.grid(row=10, column=0, columnspan=3, sticky='we', pady=(8, 0))

    def cargar_listas(self, sim):
        """Llena los desplegables, ordenados por nombre común o por archivo según el tablero; conserva lo elegido."""
        antes = self.estado() if hasattr(self, 'nombres') else None
        comun = self.app.por_nombre.get()
        def lista(tabla):
            if comun: it = sorted(tabla.items(), key=lambda x: (x[1].nombre.lower(), x[0]))
            else: it = sorted(tabla.items())
            return {(f'{a.nombre} — {a.archivo}' if comun else f'{a.archivo} — {a.nombre}'): k for k, a in it}
        self.nombres = lista(sim.armas); self.nbarcos = lista(sim.barcos)
        self.rotulo = {k: t for t, k in self.nombres.items()}; self.rotulo_b = {k: t for t, k in self.nbarcos.items()}
        for cb in self.armas: cb['values'] = [''] + list(self.nombres)
        self.barco['values'] = [''] + list(self.nbarcos)
        if antes: self.poner_estado(antes)
        self.recalcular()

    # ---- arrastrar una fila (☰ N) a otra posición del orden de pelea ----
    def fila_en(self, y_raiz):
        for k, cb in enumerate(self.armas):
            y0 = cb.winfo_rooty()
            if y_raiz < y0 + cb.winfo_height(): return k
        return len(self.armas) - 1

    def tomar(self, k):
        self.arrastre = k; self.configure(cursor='fleur')

    def mover(self, e):
        if self.arrastre is None: return
        j = self.fila_en(e.y_root)
        for i, cb in enumerate(self.armas): cb.state(['focus'] if i == j else ['!focus'])

    def soltar(self, e):
        k, self.arrastre = self.arrastre, None; self.configure(cursor='')
        for cb in self.armas: cb.state(['!focus'])
        if k is None: return
        self.mover_fila(k, self.fila_en(e.y_root))

    def mover_fila(self, k, j):
        """Lleva la fila k a la posición j; las del medio se corren un lugar."""
        if k == j: return
        filas = [(cb.get(), sp.get()) for cb, sp in zip(self.armas, self.cant)]
        filas.insert(j, filas.pop(k))
        for (t, n), cb, sp in zip(filas, self.armas, self.cant): cb.set(t); sp.set(n)
        self.recalcular()

    def estado(self):
        """Todo lo ingresado en este lado (para Invertir)."""
        return dict(lado=self.lado(), con_heroe=self.con_heroe.get(), heroe=self.heroe)

    def poner_estado(self, e):
        for (a, n), cb, sp in zip(e['lado']['tropas'], self.armas, self.cant):
            cb.set(self.rotulo.get(a, '') if a else ''); sp.set(n)
        b = e['lado']['barco']; self.barco.set(self.rotulo_b.get(b, '') if b else '')
        self.heroe = e['heroe']; self.con_heroe.set(e['con_heroe'])
        if not self.heroe: self.txt_heroe['text'] = '(sin armar)'
        self.recalcular()

    def lado(self):
        tropas = []
        for cb, sp in zip(self.armas, self.cant):
            try: n = int(sp.get())
            except ValueError: n = 0
            tropas.append((self.nombres.get(cb.get()), n))
        return dict(tropas=tropas, barco=self.nbarcos.get(self.barco.get()),
                    heroe=self.heroe if self.con_heroe.get() and self.heroe else None)

    def recalcular(self):
        sim = self.app.sim
        if not sim: return
        d = self.lado(); tot = n = costo = 0
        for a, c in d['tropas']:   # costo: el de comprar cada unidad (Arma.costo), no el de armar la producción
            if a and c > 0: tot += sim.armas[a].factor() * c; n += c; costo += sim.armas[a].costo * c
        h = d['heroe']
        det = f'Factor medio {tot / n:.1f}' if n else ''   # la cantidad va en la leyenda de la luz (n / tope)
        try:
            lado = 'A' if self is self.app.pa else 'D'
            tope, motivo = sim.tope(lado, d, self.app.escenario()['campo'])
        except Exception: tope, motivo = MAX_PILA, 'pila común'
        total = n + (1 if h else 0)
        self.luz.poner(total > tope, f'{total} / {tope}')
        if tope != MAX_PILA or total > tope: det += ('  ·  ' if det else '') + f'tope {tope}: {motivo}'
        self.coef.poner((f'FACTOR = {tot:.0f}     COSTO = $ {costo:,}'.replace(',', '.')) if n else 'FACTOR = —     COSTO = $ 0', det)
        if self.heroe:
            cl = sim.clases[self.heroe['clase']]; el, _ = elecciones(cl)
            suma = lambda p: sum(int(el[i][0].split('+')[1]) for i in self.heroe['elecciones'] if el[i][0].startswith(p))
            f, v, mv = cl.fuerza + suma('Strength +'), cl.vidas + suma('Hits +'), cl.mov + suma('Movement +')
            self.txt_heroe['text'] = (f'{cl.nombre}, nivel {self.heroe["nivel"]}: F{f} V{v} M{mv}, '
                                      f'{len(self.heroe["items"])} ítems, {len(self.heroe["hechizos"])} hechizos')

    def editar_heroe(self):
        if self.app.sim: SubpanelHeroe(self)

class SubpanelHeroe(tk.Toplevel):
    def __init__(self, panel):
        super().__init__(panel); self.panel = panel; sim = panel.app.sim
        self.title(f'Héroe del {panel["text"].lower()}'); self.transient(panel.winfo_toplevel()); self.grab_set()
        h = panel.heroe or dict(clase=next(iter(sim.clases)), nivel=1, elecciones=[], items=[], hechizos=[])
        self.cls = {f'{c.nombre} ({k})': k for k, c in sim.clases.items()}
        ttk.Label(self, text='Clase').grid(row=0, column=0, sticky='w', padx=6)
        self.clase = ttk.Combobox(self, values=list(self.cls), width=36, state='readonly'); self.clase.grid(row=0, column=1, sticky='w')
        self.clase.set(next(t for t, k in self.cls.items() if k == h['clase']))
        ttk.Label(self, text='Nivel').grid(row=1, column=0, sticky='w', padx=6)
        self.nivel = ttk.Spinbox(self, from_=1, to=10, width=4, command=self.puntos); self.nivel.set(h['nivel'])
        self.nivel.grid(row=1, column=1, sticky='w')
        self.fe = ttk.LabelFrame(self, text='Habilidades aprendidas (veces que se eligió cada una)', padding=4)
        self.fe.grid(row=2, column=0, columnspan=2, sticky='we', padx=6, pady=4)
        self.lpuntos = ttk.Label(self); self.lpuntos.grid(row=3, column=0, columnspan=2, sticky='w', padx=6)
        self.veces = []
        self.clase.bind('<<ComboboxSelected>>', lambda e: self.armar_elecciones([]))
        self.armar_elecciones(h['elecciones'])
        f = ttk.Frame(self); f.grid(row=4, column=0, columnspan=2, padx=6, pady=4)
        self.items = self.lista(f, 'Ítems (Ctrl+clic para varios)', sim.items, h['items'], 0)
        self.hech = self.lista(f, 'Magias del héroe (se lanzan antes de pelear)', sim.hechizos, h['hechizos'], 1)
        b = ttk.Frame(self); b.grid(row=5, column=0, columnspan=2, pady=6)
        boton(b, text='Aceptar', command=self.aceptar).pack(side='left', padx=4)
        boton(b, text='Cancelar', command=self.destroy).pack(side='left', padx=4)

    def lista(self, padre, titulo, tabla, sel, col):
        fr = ttk.LabelFrame(padre, text=titulo, padding=4); fr.grid(row=0, column=col, padx=4, sticky='n')
        lb = tk.Listbox(fr, selectmode='extended', width=44, height=12, exportselection=False)
        sb = ttk.Scrollbar(fr, command=lb.yview); lb['yscrollcommand'] = sb.set
        lb.pack(side='left'); sb.pack(side='left', fill='y')
        claves = list(tabla)
        for i, k in enumerate(claves):
            lb.insert('end', f'{tabla[k].nombre} — {tabla[k].texto()}')
            if k in sel: lb.selection_set(i)
        lb.claves = claves
        return lb

    def armar_elecciones(self, elegidas):
        for w in self.fe.winfo_children(): w.destroy()
        cl = self.panel.app.sim.clases[self.cls[self.clase.get()]]
        self.el, self.subidas = elecciones(cl); self.veces = []
        ttk.Label(self.fe, text=f'Base: F{cl.fuerza} V{cl.vidas} M{cl.mov} Vista {cl.vista}').grid(row=0, column=0, columnspan=3, sticky='w')
        for i, (t, costo) in enumerate(self.el):
            sp = ttk.Spinbox(self.fe, from_=0, to=10, width=3, command=self.puntos); sp.set(elegidas.count(i))
            if not t: sp.state(['disabled'])
            sp.grid(row=i + 1, column=0); sp.bind('<KeyRelease>', lambda e: self.puntos())
            ttk.Label(self.fe, text=t or '—').grid(row=i + 1, column=1, sticky='w', padx=4)
            ttk.Label(self.fe, text=f'{costo} pts' if t else '').grid(row=i + 1, column=2, sticky='e')
            self.veces.append(sp)
        self.puntos()

    def elegidas(self):
        r = []
        for i, sp in enumerate(self.veces):
            try: r += [i] * int(sp.get())
            except ValueError: pass
        return r

    def puntos(self):
        try: nivel = max(1, min(10, int(self.nivel.get())))
        except ValueError: nivel = 1
        tiene = sum(self.subidas[:nivel - 1]); gasta = sum(self.el[i][1] for i in self.elegidas())
        self.lpuntos['text'] = f'Puntos: gasta {gasta} de {tiene} que da el nivel {nivel}' + ('  ·  ¡DE MÁS!' if gasta > tiene else '')

    def aceptar(self):
        try: nivel = int(self.nivel.get()); assert 1 <= nivel <= 10
        except (ValueError, AssertionError): messagebox.showerror(TITULO, 'Nivel: 1 a 10', parent=self); return
        self.panel.heroe = dict(clase=self.cls[self.clase.get()], nivel=nivel, elecciones=self.elegidas(),
                                items=[self.items.claves[i] for i in self.items.curselection()],
                                hechizos=[self.hech.claves[i] for i in self.hech.curselection()])
        self.panel.con_heroe.set(True); self.panel.recalcular(); self.destroy()

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title(TITULO); self.sim = None
        try:   # el escudo con las espadas (icono.py); en el .exe va adentro, junto al ícono del archivo
            self.foto_icono = tk.PhotoImage(file=os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))), 'icono.png'))
            self.iconphoto(True, self.foto_icono)
        except tk.TclError: pass
        self.cfg = configparser.ConfigParser(); self.cfg.read(CONFIG, encoding='utf-8')
        if 'tablero' not in self.cfg: self.cfg['tablero'] = {}
        c = self.cfg['tablero']
        self.marmol = tk.Label(self, bd=0); self.marmol.place(x=0, y=0, relwidth=1, relheight=1); self.marmol.lower()
        self.juego = tk.StringVar(value=c.get('juego', JUEGO0))
        self.sav = tk.StringVar(value=c.get('partida', os.path.join(JUEGO0, 'SAVES', 'Tanda_Kor.SAV')))
        self.por_nombre = tk.BooleanVar(value=c.getboolean('por_nombre', False))
        self.marmol_im = None
        self.encabezado(c)
        # Los paneles van directo sobre la ventana, cada uno en su reborde dorado: entre ellos se ve el mármol.
        cajas = [reborde(self, BANDOS['ATACANTE']['medio']), reborde(self, BANDOS['DEFENSOR']['medio']), reborde(self)]
        for col, m in enumerate(cajas):
            m.master.grid(row=1, column=col, sticky='ns', padx=(10 if col == 0 else 4, 10 if col == 2 else 4), pady=4)
        for caja, t in ((cajas[0], 'ATACANTE'), (cajas[1], 'DEFENSOR')): Estandarte(caja, t, self.juego.get()).pack(fill='x')
        self.pa = Panel(self, cajas[0], 'ATACANTE'); self.pa.pack(fill='both')
        self.pd = Panel(self, cajas[1], 'DEFENSOR'); self.pd.pack(fill='both')
        der = ttk.Frame(cajas[2], padding=4); der.pack(fill='both', expand=True)
        self.subpanel_terreno(der); self.subpanel_visual(der, c)
        self.plegados = {}
        plegable(self, [(cajas[0], self.pa), (cajas[1], self.pd), (cajas[2], der)], 'tablero')
        caja = reborde(self); caja.master.grid(row=2, column=0, columnspan=3, sticky='w', padx=10, pady=4)
        fila = ttk.Frame(caja, padding=6); fila.pack(fill='x')
        ttk.Label(fila, text='Peleas para el %').pack(side='left')
        self.n = ttk.Spinbox(fila, from_=10, to=65536, increment=500, width=8); self.n.set(c.get('peleas', '1000')); self.n.pack(side='left', padx=4)
        m = reborde(fila); m.master.pack(side='left', padx=12)
        self.boton = BotonAzul(m, 'INICIAR COMBATE', self.iniciar); self.boton.pack()
        boton(fila, text='⇄ Invertir atacante y defensor', command=self.invertir).pack(side='left')
        boton(fila, text=f'Historial (últimos {historial.MAXIMO})…', command=self.ver_historial).pack(side='left', padx=(12, 0))
        caja = reborde(self); caja.master.grid(row=3, column=0, columnspan=3, sticky='nsew', padx=10, pady=(4, 10))
        self.salida = tk.Text(caja, height=12, width=60, wrap='word', state='disabled', bd=0); self.salida.pack(fill='both', expand=True)
        plegable(self, [(caja, self.salida)], 'resultado')
        self.rowconfigure(3, weight=1); self.columnconfigure(2, weight=1)
        self.poner_marmol()
        self.protocol('WM_DELETE_WINDOW', self.cerrar)
        self.after(100, self.cargar)

    def poner_marmol(self):
        """Fondo de la ventana: MARBLE.PCX del juego (EDPICTS) en mosaico; sin él queda el color de siempre."""
        t = pcx(os.path.join(self.juego.get(), 'EDPICTS', 'MARBLE.PCX'))
        if t is None: self.marmol_im = None; self.marmol.configure(image=''); self.pintar_encabezado(); return
        t = t.convert('RGB'); W, H = self.winfo_screenwidth(), self.winfo_screenheight()
        m = Image.new('RGB', (W, H))
        for y in range(0, H, t.height):
            for x in range(0, W, t.width): m.paste(t, (x, y))
        self.marmol_im = m
        self.foto_marmol = ImageTk.PhotoImage(m); self.marmol.configure(image=self.foto_marmol, anchor='nw')
        self.pintar_encabezado()

    # ---- encabezado: sobre el mármol, con título, estado, casilla de orden, carpeta y configuración ----
    def encabezado(self, c):
        caja = reborde(self); caja.master.grid(row=0, column=0, columnspan=3, sticky='we', padx=10, pady=(10, 4))
        cv = self.cab = tk.Canvas(caja, height=70, bg='#1b2a3a', highlightthickness=0); cv.pack(fill='x')
        self.estado_txt = ''
        self.b_carpeta = boton(cv, text='Carpeta del juego…', command=self.configurar)
        imgs = {}
        for e in ('normal', 'hover', 'active', 'disabled'):
            try: imgs[e] = ImageTk.PhotoImage(Image.open(os.path.join(ASSETS, f'menu_settings_{e}.png')).convert('RGBA').resize((28, 28), Image.LANCZOS))
            except OSError: pass
        self.icono_cfg, self.cfg_abierta = imgs if len(imgs) == 4 else {}, False
        cv.bind('<Configure>', lambda e: self.pintar_encabezado())

    def pintar_encabezado(self):
        cv = self.cab; cv.delete('all'); W = cv.winfo_width()
        if self.marmol_im is not None and W > 1:
            x0, y0 = cv.winfo_rootx() - self.winfo_rootx(), cv.winfo_rooty() - self.winfo_rooty()
            self.foto_cab = ImageTk.PhotoImage(self.marmol_im.crop((x0, y0, x0 + W, y0 + 70)))
            cv.create_image(0, 0, image=self.foto_cab, anchor='nw')
        def sombra(x, y, t, f, anchor='w', tag=()):
            cv.create_text(x + 1, y + 1, text=t, font=f, fill='#000000', anchor=anchor, tags=tag)
            cv.create_text(x, y, text=t, font=f, fill='#ffffff', anchor=anchor, tags=tag)
        sombra(10, 18, TITULO, ('Segoe UI', 12, 'bold'))
        # contador general de pruebas: a la derecha, a todo el alto del encabezado; leyenda a su izquierda
        self.foto_odo = ImageTk.PhotoImage(contador.odometro(self.pruebas(), alto=56))
        cv.create_image(W - 8, 35, image=self.foto_odo, anchor='e')
        der = W - 22 - self.foto_odo.width()
        per = self.cfg.get('contador', 'periodo', fallback='manual')
        ley = 'PRUEBAS' + ('' if per == 'manual' else f' ({contador.PERIODOS[per].lower()})')
        sombra(der, 50, ley, ('Segoe UI', 10, 'bold'), anchor='e')
        if self.icono_cfg:
            e = 'disabled' if self.cfg_abierta else 'normal'
            cv.create_image(der, 18, image=self.icono_cfg[e], anchor='e', tags='cfg'); der -= 38
            if not self.cfg_abierta:
                cv.tag_bind('cfg', '<Enter>', lambda e: (cv.itemconfigure('cfg', image=self.icono_cfg['hover']), cv.configure(cursor='hand2')))
                cv.tag_bind('cfg', '<Leave>', lambda e: (cv.itemconfigure('cfg', image=self.icono_cfg['normal']), cv.configure(cursor='')))
                cv.tag_bind('cfg', '<ButtonPress-1>', lambda e: cv.itemconfigure('cfg', image=self.icono_cfg['active']))
                cv.tag_bind('cfg', '<ButtonRelease-1>', lambda e: (cv.configure(cursor=''), self.configuracion()))
        sombra(der, 18, self.estado_txt, ('Segoe UI', 9), anchor='e')
        marca = '☑' if self.por_nombre.get() else '☐'
        sombra(10, 50, f'{marca} Ordenar las armas por NOMBRE COMÚN (si no, por nombre de archivo)', ('Segoe UI', 9), tag='orden')
        cv.tag_bind('orden', '<Button-1>', lambda e: (self.por_nombre.set(not self.por_nombre.get()), self.reordenar(), self.pintar_encabezado()))
        cv.tag_bind('orden', '<Enter>', lambda e: cv.configure(cursor='hand2')); cv.tag_bind('orden', '<Leave>', lambda e: cv.configure(cursor=''))
        x = cv.bbox('orden')[2] + 24 if cv.bbox('orden') else 420
        cv.create_window(x, 50, window=self.b_carpeta, anchor='w')

    # ---- contador general de pruebas (sección [contador] del .ini; se guarda en cada prueba) ----
    def _contador(self):
        if not self.cfg.has_section('contador'): self.cfg.add_section('contador')
        c = self.cfg['contador']; per = c.get('periodo', 'manual')
        if per not in contador.PERIODOS: per = c['periodo'] = 'manual'
        if per != 'manual' and c.get('clave', '') != contador.clave(per):   # empezó otro período: a cero
            c['valor'], c['clave'] = '0', contador.clave(per)
        return c

    def pruebas(self):
        try: return int(self._contador().get('valor', '0'))
        except ValueError: return 0

    def guardar_cfg(self):
        try:
            with open(CONFIG, 'w', encoding='utf-8') as f: self.cfg.write(f)
        except OSError: pass

    def contar_prueba(self, poner=None):
        c = self._contador(); c['valor'] = str(0 if poner == 0 else self.pruebas() + 1)
        self.guardar_cfg(); self.pintar_encabezado()

    def decir_estado(self, t):
        self.estado_txt = t; self.pintar_encabezado()

    # ---- configuración: actualización en línea y créditos (como el Monitor de IA y el Gestor de ventanas) ----
    def configuracion(self):
        if self.cfg_abierta: return
        v = tk.Toplevel(self); v.title(f'Configuración — VERSIÓN {VERSION}'); v.transient(self); v.resizable(False, False)
        self.cfg_abierta = True; self.pintar_encabezado()
        def cerrada(e):
            if e.widget is v:
                self.cfg_abierta = False
                try: self.pintar_encabezado()
                except tk.TclError: pass   # la ventana principal se está cerrando
        v.bind('<Destroy>', cerrada)
        v.geometry(f'+{self.winfo_rootx() + self.winfo_width() - 470}+{self.winfo_rooty() + 90}')
        fr = tk.Frame(v, padx=15, pady=12); fr.pack(fill='both')
        tk.Label(fr, text='Actualización en línea', font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        tk.Label(fr, text=f'Versión instalada: {VERSION}').pack(anchor='w', pady=(6, 0))
        estado = tk.Label(fr, text='', width=55, anchor='w', justify='left', wraplength=410)
        tk.Button(fr, text='Buscar actualización', width=20, command=lambda: self.actualizar(v, estado)).pack(anchor='w', pady=(8, 0))
        estado.pack(anchor='w', pady=(6, 0))
        estado.barra = ttk.Progressbar(fr, length=410, maximum=100)   # aparece solo mientras baja la versión nueva
        tk.Label(fr, text='Contador de pruebas', font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(14, 0))
        fc = tk.Frame(fr); fc.pack(anchor='w', pady=(6, 0))
        nombres = list(contador.PERIODOS.values()); clave_de = {t: k for k, t in contador.PERIODOS.items()}
        per = ttk.Combobox(fc, values=nombres, state='readonly', width=16)
        per.set(contador.PERIODOS[self._contador().get('periodo', 'manual')])
        def cambiar(e=None):
            c = self._contador(); c['periodo'] = clave_de[per.get()]; c['clave'] = contador.clave(c['periodo'])
            self.guardar_cfg(); self.pintar_encabezado()
        per.bind('<<ComboboxSelected>>', cambiar); per.pack(side='left')
        def cero():
            if messagebox.askyesno(TITULO, f'¿Poner en cero el contador de pruebas ({self.pruebas()})?', parent=v): self.contar_prueba(poner=0)
        tk.Button(fc, text='Poner en cero', width=14, command=cero).pack(side='left', padx=(10, 0))
        tk.Label(fr, text='RA Sistemas & Claude © 2026', fg='#696969').pack(anchor='w', pady=(14, 0))
        correo = tk.Label(fr, text=CORREO, fg='#0066cc', cursor='hand2', font=('Segoe UI', 9, 'underline')); correo.pack(anchor='w')
        correo.bind('<Button-1>', lambda e: webbrowser.open(f'mailto:{CORREO}'))
        tk.Button(fr, text='Cerrar', width=10, command=v.destroy).pack(anchor='e', pady=(10, 0))
        self.v_config = v

    def actualizar(self, padre, estado):
        """Baja la última release de REPO y reemplaza este .exe (como el Monitor de IA)."""
        def decir(t): estado['text'] = t; padre.update_idletasks()
        if not getattr(sys, 'frozen', False):
            return decir('Corriendo desde el código: se actualiza con git.')
        decir('Consultando GitHub…')
        try:
            with urllib.request.urlopen(f'https://api.github.com/repos/{REPO}/releases/latest', timeout=15) as r: rel = json.load(r)
        except Exception as e:
            return decir(f'No se pudo consultar GitHub: {e}')
        etiqueta = rel['tag_name'].lstrip('v')
        if version_tupla(etiqueta) <= version_tupla(VERSION):
            return decir(f'Ya tenés la última versión ({VERSION}).')
        exe = next((a for a in rel['assets'] if a['name'] == EXE_REL), None)
        if not exe: return decir(f'La release {etiqueta} no trae {EXE_REL}.')
        if not messagebox.askyesno(TITULO, f'Hay una versión nueva: {etiqueta} (tenés {VERSION}).\n'
                                   '¿Bajarla e instalarla? El simulador se cierra y se vuelve a abrir.', parent=padre):
            return decir('')
        actual = sys.executable; nuevo = actual[:-4] + '.nuevo.exe'
        barra = estado.barra; barra.pack(anchor='w', pady=(4, 0), before=estado); barra['value'] = 0
        decir(f'Descargando la versión {etiqueta}…')
        def avance(bloques, tam, total):
            hecho = bloques * tam; total = total if total > 0 else exe.get('size', 0)
            if total:
                pct = min(hecho * 100 / total, 100); barra['value'] = pct
                mb = lambda b: f'{b / 1048576:.1f}'.replace('.', ',')
                estado['text'] = f'Descargando la versión {etiqueta}: {mb(min(hecho, total))} de {mb(total)} MB ({pct:.0f} %)'
            padre.update()
        try:
            urllib.request.urlretrieve(exe['browser_download_url'], nuevo, avance)
            barra['value'] = 100; decir(f'Descarga completa. Verificando la versión {etiqueta}…')
            interna = version_de(nuevo)   # la release tiene que ser lo que dice su etiqueta
            if interna != etiqueta: raise RuntimeError(f'la release {etiqueta} trae adentro la versión {interna}')
        except Exception as e:
            if os.path.exists(nuevo): os.remove(nuevo)
            barra.pack_forget()
            return decir(f'No se instaló la actualización: {e}')
        # Un .bat espera a que este proceso cierre, reemplaza el .exe, lo abre de nuevo y se borra.
        bat, pid = actual[:-4] + '.actualizar.bat', os.getppid()   # el cargador de PyInstaller: sale último
        with open(bat, 'w', encoding='mbcs') as f:
            f.write('@echo off\n:espera\n'
                    f'tasklist /FI "PID eq {pid}" /NH | find "{pid}" >nul && (timeout /t 1 /nobreak >nul & goto espera)\n'
                    f'move /y "{nuevo}" "{actual}" >nul\nstart "" "{actual}"\ndel "%~f0"\n')
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith(('_PYI', '_MEI'))}
        env['PYINSTALLER_RESET_ENVIRONMENT'] = '1'
        decir(f'Instalando la versión {etiqueta}: el simulador se cierra y se vuelve a abrir…'); padre.after(1200)
        subprocess.Popen(['cmd', '/c', bat], creationflags=subprocess.CREATE_NO_WINDOW, env=env)
        self.cerrar()

    def subpanel_terreno(self, padre):
        f = ttk.LabelFrame(padre, labelwidget=titulo_verde(padre, 'TERRENO', '(casilla del defensor)'), padding=6); f.pack(fill='x')
        ttk.Label(f, text='Tipo').grid(row=0, column=0, sticky='w')
        self.terreno = ttk.Combobox(f, width=18, state='readonly'); self.terreno.grid(row=0, column=1, sticky='w')
        self.lagua = ttk.Label(f, text=''); self.lagua.grid(row=1, column=1, sticky='w')
        self.terreno.bind('<<ComboboxSelected>>', lambda e: self.ver_agua())
        self.sitio = tk.StringVar(value='nada')
        for i, (t, k, _, _) in enumerate(SITIOS):
            ttk.Radiobutton(f, text=t, value=k, variable=self.sitio, command=self.ver_defensas).grid(row=2 + i, column=0, columnspan=2, sticky='w')
        ttk.Label(f, text='Defensas').grid(row=8, column=0, columnspan=2, sticky='w')
        self.defensas = ttk.Combobox(f, width=34, state='readonly'); self.defensas.grid(row=9, column=0, columnspan=2, sticky='w')
        self.ver_defensas()

    def ver_defensas(self, texto=None):
        self.after_idle(self.recalcular_lados)
        """Llena el desplegable de defensas con las del sitio elegido (vacío y apagado si no tiene)."""
        ops = [t for t, _, _ in DEFENSAS[self.sitio.get()]]
        self.defensas['values'] = ops
        if not ops: self.defensas.set('(sin defensas)'); self.defensas.state(['disabled']); return
        self.defensas.state(['!disabled'])
        self.defensas.set(texto if texto in ops else (self.defensas.get() if self.defensas.get() in ops else ops[0]))

    def subpanel_visual(self, padre, c):
        f = ttk.LabelFrame(padre, text='VISUAL (ventana de combate)', padding=6); f.pack(fill='both', expand=True, pady=(6, 0))
        ttk.Label(f, text='Velocidad').grid(row=0, column=0, sticky='w')
        self.velocidad = tk.IntVar(value=c.getint('velocidad', 5)); Deslizador(f, self.velocidad, 1, 10).grid(row=0, column=1, sticky='w')
        self.efectos = tk.BooleanVar(value=c.getboolean('efectos', True)); ttk.Checkbutton(f, text='Efectos', variable=self.efectos).grid(row=1, column=0, sticky='w')
        self.sonido = tk.BooleanVar(value=c.getboolean('sonido', True)); ttk.Checkbutton(f, text='Sonido', variable=self.sonido).grid(row=1, column=1, sticky='w')
        ttk.Label(f, text='Tamaño').grid(row=2, column=0, sticky='w')
        self.tamano = ttk.Combobox(f, values=['Normal', 'Grande'], width=10, state='readonly'); self.tamano.set(c.get('tamano', 'Normal'))
        self.tamano.grid(row=2, column=1, sticky='w')
        ttk.Label(f, text='Resultados').grid(row=3, column=0, sticky='w')
        self.resultados = tk.StringVar(value=c.get('resultados', 'todos'))
        ttk.Radiobutton(f, text='Sobrevivientes y muertos', value='todos', variable=self.resultados).grid(row=4, column=0, columnspan=2, sticky='w')
        ttk.Radiobutton(f, text='Solo sobrevivientes', value='vivos', variable=self.resultados).grid(row=5, column=0, columnspan=2, sticky='w')
        # de noche algunas armas pelean más fuerte: va al escenario (campo['noche']) además de verse
        self.noche = tk.BooleanVar(); ttk.Checkbutton(f, text='Noche (opción Day/Night)', variable=self.noche).grid(row=6, column=0, columnspan=2, sticky='w')

    def configurar(self):
        """Carpeta del juego (de ahí salen armas, héroes, ítems, hechizos, imágenes y sonidos). El motor además necesita
        una partida (.SAV) de esa carpeta como base de la memoria del juego emulado; se toma sola y no cambia la pelea
        (las armas se cargan del ARMY, el terreno y la ciudad los pone el tablero)."""
        d = filedialog.askdirectory(initialdir=self.juego.get(), title='Carpeta del juego (la que tiene DarklordAV.exe)')
        if not d: return
        d = os.path.normpath(d); self.juego.set(d)
        self.sav.set(os.path.join(d, 'SAVES', os.path.basename(self.sav.get())))   # elegir_partida busca otra si falta
        self.poner_marmol(); self.cargar()

    def reordenar(self):
        if self.sim:
            for p in (self.pa, self.pd): p.cargar_listas(self.sim)

    def invertir(self):
        if not self.sim: return
        a, d = self.pa.estado(), self.pd.estado()
        self.pa.poner_estado(d); self.pd.poner_estado(a)

    def elegir_partida(self):
        """El motor sirve con cualquier partida (.SAV): si la recordada no existe, toma la más reciente de SAVES."""
        if os.path.isfile(self.sav.get()): return True
        saves = os.path.join(self.juego.get(), 'SAVES')
        hay = [os.path.join(saves, f) for f in os.listdir(saves) if f.lower().endswith('.sav')] if os.path.isdir(saves) else []
        if not hay:
            self.decir_estado('No se pudo cargar')
            messagebox.showerror(TITULO, f'No hay partidas (.SAV) en {saves}.\nEl motor necesita una cualquiera '
                                 '(guardá una partida en el juego) o elegí otra carpeta del juego.'); return False
        self.sav.set(max(hay, key=os.path.getmtime)); return True

    def cargar(self):
        if not os.path.isfile(os.path.join(self.juego.get(), 'DarklordAV.exe')):
            self.decir_estado('No se pudo cargar')
            messagebox.showerror(TITULO, f'No está DarklordAV.exe en {self.juego.get()}.\n'
                                 'Elegí la carpeta del juego con «Carpeta del juego…».'); return
        if not self.elegir_partida(): return
        self.decir_estado('Cargando el juego…'); self.boton.state(['disabled'])
        def tarea():
            try: sim, err = Simulador(self.juego.get(), self.sav.get()), None
            except Exception as e: sim, err = None, e
            self.after(0, lambda: self.cargado(sim, err))
        threading.Thread(target=tarea, daemon=True).start()

    def cargado(self, sim, err):
        if err:
            self.decir_estado('No se pudo cargar'); messagebox.showerror(TITULO, f'No se pudo cargar el juego:\n{err}'); return
        self.sim = sim; self.boton.state(['!disabled'])
        self.decir_estado(f'{len(sim.armas)} armas, {len(sim.barcos)} barcos, {len(sim.clases)} clases, {len(sim.items)} ítems, {len(sim.hechizos)} hechizos')
        ts = []
        for t in sim.terrenos:
            if t in BOSQUES and BOSQUES[t] not in sim.terrenos: continue
            ts.append(t)
            if t == 'hills' and 'hills con bosque' in BOSQUES: ts.append('hills con bosque')
        self.terreno['values'] = ts
        if not self.terreno.get(): self.terreno.set('plains' if 'plains' in sim.terrenos else next(iter(sim.terrenos)))
        self.ver_agua()
        for p in (self.pa, self.pd): p.cargar_listas(sim)
        if not getattr(self, 'restaurado', False): self.restaurado = True; self.restaurar()

    def restaurar(self):
        """Vuelve a poner las tropas, barcos, héroes y el terreno de la última vez (los guarda cerrar() en el .ini).
        Un arma o terreno que esta carpeta del juego no tiene queda vacío."""
        c = self.cfg['tablero']
        try:
            for clave, p in (('atacante', self.pa), ('defensor', self.pd)):
                if c.get(clave): p.poner_estado(json.loads(c[clave]))
            campo = json.loads(c.get('campo', '{}'))
        except (ValueError, KeyError, TypeError, IndexError): return
        t = campo.get('terreno')
        if campo.get('bosque'): t = next((k for k, v in BOSQUES.items() if v == t), t)
        if t in self.terreno['values']: self.terreno.set(t); self.ver_agua()
        self.noche.set(campo.get('noche', False))
        est, obra, niv = campo.get('estructura', 0), campo.get('obra'), campo.get('defensas', 1)
        sitio = next((k for _, k, e, o in SITIOS if e == est and (o == obra or est == 3)), 'nada')
        self.sitio.set(sitio)
        self.ver_defensas(next((t for t, n, o in DEFENSAS[sitio] if o == obra and (sitio != 'ciudad' or n == niv)), None))

    def recalcular_lados(self):
        for p in (getattr(self, 'pa', None), getattr(self, 'pd', None)):
            if p is not None and hasattr(p, 'nombres'): p.recalcular()

    def ver_agua(self):
        self.after_idle(self.recalcular_lados)
        if self.sim and self.terreno.get():
            self.lagua['text'] = 'agua: hace falta barco (o puente)' if self.sim.es_agua(self.terreno_real()[0]) else 'tierra'

    def terreno_real(self):
        """(terreno de la partida, capa de bosque) de lo elegido en el desplegable."""
        t = self.terreno.get()
        return (BOSQUES[t], True) if t in BOSQUES else (t, False)

    def escenario(self):
        k = self.sitio.get(); est = next(e for _, s, e, _ in SITIOS if s == k)
        d, obra = next(((n, o) for t, n, o in DEFENSAS[k] if t == self.defensas.get()), (1, None))
        return {'A': self.pa.lado(), 'D': self.pd.lado(),
                'campo': dict(terreno=self.terreno_real()[0], estructura=est, bosque=self.terreno_real()[1],
                              noche=self.noche.get(), defensas=d, obra=obra)}

    def iniciar(self):
        v = getattr(self, 'v_combate', None)   # una sola pelea a la vez: si ya hay una ventana, se la trae al frente
        if v is not None and v.winfo_exists(): v.lift(); v.focus_force(); return
        try: n = max(1, int(self.n.get()))
        except ValueError: n = 1000
        try: r = self.sim.simular(self.escenario(), n)
        except Error as e: messagebox.showerror(TITULO, str(e)); return
        except Exception as e: messagebox.showerror(TITULO, f'Falló el motor:\n{e}'); return
        self.mostrar(r); self.contar_prueba(); self.anotar_ficha(r)
        self.v_combate = VentanaCombate(self, self.juego.get(), r, TITULO, velocidad=self.velocidad.get(), efectos=self.efectos.get(),
                       sonido=self.sonido.get(), tamano=self.tamano.get(), resultados=self.resultados.get())

    def mostrar(self, r):
        muertos = {('A', i) for l, i in r['muertes'] if l == 'A'} | {('D', i) for l, i in r['muertes'] if l == 'D'}
        def fila(lado, nombres):
            out = []
            for i, nm in enumerate(nombres):
                muerto = (lado, i) in muertos
                if muerto and self.resultados.get() == 'vivos': continue
                out.append(f'{i + 1}. {nm}' + (' ✝' if muerto else ''))
            return '  '.join(out) or '(ninguno)'
        t = [f'El ATACANTE gana el {r["pct"]:.2f} % de {r["n"]} peleas (defensor: {100 - r["pct"]:.2f} %).', '',
             f'Batalla de muestra: gana el {"ATACANTE" if r["gana"] else "DEFENSOR"}.',
             f'  Atacante: {fila("A", r["orden_a"])}', f'  Defensor: {fila("D", r["orden_d"])}',
             '  Caídas en orden: ' + ', '.join(f'{"A" if l == "A" else "D"}{i + 1}' for l, i in r['muertes'])]
        if r['avisos']: t += [''] + ['Aviso: ' + a for a in r['avisos']]
        self.salida['state'] = 'normal'; self.salida.delete('1.0', 'end'); self.salida.insert('1.0', '\n'.join(t))
        self.salida['state'] = 'disabled'

    # ---- historial: ficha de cada combate, con el número del contador de pruebas ----
    def anotar_ficha(self, r):
        def comp(p):
            lado = p.lado(); h = lado['heroe']
            return dict(tropas=[(cb.get(), n) for (a, n), cb in zip(lado['tropas'], p.armas) if a and n > 0],
                        barco=p.barco.get() or None, heroe=f"{h['clase']} nivel {h['nivel']}" if h else None)
        k = self.sitio.get(); sitio = next(t for t, s, _, _ in SITIOS if s == k)
        campo = (f'{self.terreno.get()} · {sitio}' + (f' · {self.defensas.get()}' if self.defensas.get() else '')
                 + (' · noche' if self.noche.get() else ''))
        historial.guardar(HISTORIAL, dict(numero=self.pruebas(), fecha=time.strftime('%d/%m/%Y %H:%M:%S'), campo=campo,
            A=comp(self.pa), D=comp(self.pd), pct=r['pct'], n=r['n'], gana=bool(r['gana']), orden_a=list(r['orden_a']),
            orden_d=list(r['orden_d']), muertes=[list(m) for m in r['muertes']], avisos=list(r['avisos'])))

    def ver_historial(self):
        v = getattr(self, 'v_historial', None)
        if v is not None and v.winfo_exists(): v.destroy()
        h = historial.cargar(HISTORIAL)
        v = self.v_historial = tk.Toplevel(self); v.title(f'Historial de combates — VERSIÓN {VERSION}'); v.transient(self)
        fr = ttk.Frame(v, padding=10); fr.pack(fill='both', expand=True)
        ttk.Label(fr, text=f'Últimos {historial.MAXIMO} combates (doble clic o Enter para ver la ficha; los repetidos, del mismo color)').pack(anchor='w')
        # lista en un Text (no Treeview) para poder pintar ATACANTE y DEFENSOR cada uno con su color
        fl = ttk.Frame(fr); fl.pack(fill='both', expand=True, pady=6)
        t = self.t_historial = tk.Text(fl, width=50, height=11, wrap='none', cursor='arrow', font=('Segoe UI', 10),
                                       tabs=('70', '230'), bd=1, relief='solid', padx=6, pady=4)
        sb = ttk.Scrollbar(fl, orient='vertical', command=t.yview); t.configure(yscrollcommand=sb.set)
        t.pack(side='left', fill='both', expand=True); sb.pack(side='right', fill='y')
        neg = tkfont.Font(family='Segoe UI', size=10, weight='bold'); v.fuentes = (neg,)
        t.tag_configure('cab', font=neg)
        for L in ('ATACANTE', 'DEFENSOR'): t.tag_configure(L, foreground=BANDOS[L]['medio'], font=neg)
        # combates repetidos (mismo campo y mismos dos lados): sus filas comparten un color de fondo
        clave = lambda f: json.dumps([f.get('campo'), f.get('A'), f.get('D')], sort_keys=True)
        cuantos = {}
        for f in h: cuantos[clave(f)] = cuantos.get(clave(f), 0) + 1
        COLORES = ('#fff2b3', '#d4f5d4', '#ffd9b3', '#e6d9ff', '#ffd6e7', '#c9f0f0', '#e8f0c0', '#f0dcc8')
        grupo = {}
        for k in (clave(f) for f in h):
            if cuantos[k] > 1 and k not in grupo:
                grupo[k] = f'rep{len(grupo)}'; t.tag_configure(grupo[k], background=COLORES[len(grupo) % len(COLORES)])
        t.tag_configure('sel_fila', background='#cce4ff'); t.tag_raise('sel_fila')
        t.insert('end', 'N.º\tFecha y hora\tGanador\n', 'cab')
        for i, f in enumerate(h):
            gana, pct = ('ATACANTE', f['pct']) if f['pct'] >= 50 else ('DEFENSOR', 100 - f['pct'])
            fila = (f'f{i}',) + ((grupo[clave(f)],) if clave(f) in grupo else ())
            t.insert('end', f"{f['numero']:06d}\t{f['fecha']}\t", fila)
            t.insert('end', gana, fila + (gana,)); t.insert('end', f'  {pct:.2f} %\n', fila)
        if not h: t.insert('end', 'Todavía no hay combates guardados.')
        t['state'] = 'disabled'
        elegida = {'i': 0 if h else None}
        def marcar(i):
            t.tag_remove('sel_fila', '1.0', 'end')
            if i is None: return
            elegida['i'] = i; t.tag_add('sel_fila', f'{i + 2}.0', f'{i + 3}.0'); t.see(f'{i + 2}.0')
        def fila_en(e):
            n = int(t.index(f'@{e.x},{e.y}').split('.')[0]) - 2
            return n if 0 <= n < len(h) else None
        def clic(e):
            n = fila_en(e)
            if n is not None: marcar(n)
            return 'break'
        def abrir(e=None):
            if e is not None and getattr(e, 'type', None) == tk.EventType.ButtonPress: clic(e)
            if elegida['i'] is not None: self.ver_ficha(h[elegida['i']])
            return 'break'
        def mover(d):
            if elegida['i'] is not None: marcar(max(0, min(len(h) - 1, elegida['i'] + d)))
            return 'break'
        t.bind('<Button-1>', clic); t.bind('<Double-1>', abrir); t.bind('<Return>', abrir)
        t.bind('<Up>', lambda e: mover(-1)); t.bind('<Down>', lambda e: mover(1))
        marcar(elegida['i']); t.focus_set()
        fb = ttk.Frame(fr); fb.pack(fill='x')
        ttk.Button(fb, text='Ver ficha', command=abrir).pack(side='left')
        def exportar_ficha():
            if elegida['i'] is None: return messagebox.showinfo('Exportar ficha', 'No hay combates guardados.', parent=v)
            f = h[elegida['i']]
            self.exportar(imagenes.imagen_ficha(f, VERSION), f"Ficha-combate-{f['numero']:06d}", v)
        ttk.Button(fb, text='Stats', command=lambda: self.ver_stats(h)).pack(side='left', padx=(12, 0))
        ttk.Button(fb, text='Exportar ficha', command=exportar_ficha).pack(side='left', padx=(6, 0))
        ttk.Button(fb, text='Exportar gráfica', command=lambda: self.exportar(imagenes.imagen_torta(h, VERSION),
                   'Stats-formaciones', v)).pack(side='left', padx=(6, 0))
        ttk.Button(fb, text='Cerrar', command=v.destroy).pack(side='right')

    def exportar(self, im, nombre, padre):
        ruta = filedialog.asksaveasfilename(parent=padre, title='Exportar imagen', initialfile=nombre + '.png',
                                            defaultextension='.png', filetypes=[('PNG', '*.png'), ('JPG', '*.jpg *.jpeg')])
        if not ruta: return
        try: imagenes.guardar(im, ruta)
        except (OSError, ValueError) as e: return messagebox.showerror('Exportar imagen', f'No se pudo guardar:\n{e}', parent=padre)
        messagebox.showinfo('Exportar imagen', f'Guardada en:\n{ruta}', parent=padre)

    def ver_stats(self, h):
        v = tk.Toplevel(self); v.title(f'Stats: mejor formación — VERSIÓN {VERSION}'); v.transient(self)
        im = imagenes.imagen_torta(h, VERSION)
        esc = min(1.0, (self.winfo_screenwidth() - 80) / im.width, (self.winfo_screenheight() - 160) / im.height)
        vista = im.resize((int(im.width * esc), int(im.height * esc)), Image.LANCZOS) if esc < 1 else im
        v.foto = ImageTk.PhotoImage(vista); tk.Label(v, image=v.foto, bg='white').pack(padx=6, pady=6)
        fb = ttk.Frame(v, padding=(10, 0, 10, 10)); fb.pack(fill='x')
        ttk.Button(fb, text='Exportar gráfica', command=lambda: self.exportar(im, 'Stats-formaciones', v)).pack(side='left')
        ttk.Button(fb, text='Cerrar', command=v.destroy).pack(side='right')

    def ver_ficha(self, f):
        v = tk.Toplevel(self); v.title(f"Ficha del combate {f['numero']:06d} — VERSIÓN {VERSION}"); v.transient(self)
        tx = tk.Text(v, width=80, height=24, wrap='word', bd=0, padx=12, pady=10, font=('Segoe UI', 10))
        tx.pack(fill='both', expand=True)
        neg = tkfont.Font(family='Segoe UI', size=10, weight='bold'); tach = tkfont.Font(family='Segoe UI', size=10, overstrike=1)
        v.fuentes = (neg, tach)   # que no se las lleve el recolector
        tx.tag_configure('t', font=neg); tx.tag_configure('x', font=tach, foreground='#a00000')
        tx.tag_configure('A', foreground=BANDOS['ATACANTE']['medio']); tx.tag_configure('D', foreground=BANDOS['DEFENSOR']['medio'])
        tx.tag_configure('gris', foreground='#808080')
        for trozo, tag in imagenes.partes_ficha(f): tx.insert('end', trozo, tag)
        tx['state'] = 'disabled'
        ttk.Button(v, text='Cerrar', command=v.destroy).pack(anchor='e', padx=10, pady=(0, 10))

    def cerrar(self):
        c = self.cfg['tablero']
        c.update(juego=self.juego.get(), partida=self.sav.get(), por_nombre=str(self.por_nombre.get()), peleas=self.n.get(), velocidad=str(self.velocidad.get()),
                 efectos=str(self.efectos.get()), sonido=str(self.sonido.get()), tamano=self.tamano.get(),
                 resultados=self.resultados.get())
        c.update({f'plegado_{k}': str(v) for k, v in self.plegados.items()})
        if self.sim:   # la última pelea armada, para la próxima vez (restaurar)
            c.update(atacante=json.dumps(self.pa.estado()), defensor=json.dumps(self.pd.estado()),
                     campo=json.dumps(self.escenario()['campo']))
        self.guardar_cfg()
        self.destroy()

if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--version':
        with open(sys.argv[2], 'w') as f: f.write(VERSION)
        sys.exit(0)
    App().mainloop()
