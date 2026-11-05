# Tablero del simulador de combate (etapa 3 de PENDIENTE-simulador-combate.md): la ventana donde se arman las dos pilas.
# Dos paneles gemelos (atacante y defensor) con 8 casilleros numerados = fight order (arma y cantidad), barco
# del bando y héroe (subpanel: clase, nivel, elecciones, ítems y hechizos); subpanel de terreno y subpanel visual
# (se guarda para la ventana de combate, etapa 4). INICIAR COMBATE arma el escenario (escenario.py) y muestra el % de
# victorias y abre la ventana de combate (combate.py) con una batalla de muestra. Uso: python tablero.py
import configparser, os, struct, sys, threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from escenario import Simulador, Error, MAX_PILA   # noqa: E402
from datos import HABILIDADES, SIN_VALOR           # noqa: E402
from combate import VentanaCombate                 # noqa: E402

VERSION = '1.0.2.0'
TITULO = f'SIMULADOR DE COMBATE — VERSIÓN {VERSION}'
CARPETA = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))
CONFIG = os.path.join(CARPETA, 'Simulador-Combate.ini')
JUEGO0 = r'C:\Warlords3'
ESTRUCTURAS = (('Nada', 0), ('Camino / puente', 1), ('Ciudad', 3))

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

class RecuadroFactor(tk.Frame):
    """El Factor total de la pila: recuadro de fondo claro con borde dorado (como el reborde del Visor de historia),
    Arial Bold con sombra."""
    def __init__(self, padre):
        super().__init__(padre, bg='#c8a040', padx=3, pady=3)
        negro = tk.Frame(self, bg='#000000', padx=1, pady=1); negro.pack(fill='x')
        self.cv = tk.Canvas(negro, height=50, bg='#f4ecd0', highlightthickness=0); self.cv.pack(fill='x')
        self.cv.bind('<Configure>', lambda e: self.dibujar()); self.t = ('', '')
    def poner(self, grande, chico):
        self.t = (grande, chico); self.dibujar()
    def dibujar(self):
        cv = self.cv; cv.delete('all'); w = cv.winfo_width() // 2
        for dx, col in ((2, '#b0a080'), (0, '#5a3a10')):
            cv.create_text(w + dx, 18 + dx, text=self.t[0], font=('Arial', 15, 'bold'), fill=col)
        cv.create_text(w, 40, text=self.t[1], font=('Arial', 9, 'bold'), fill='#3a2a10')

class Panel(ttk.LabelFrame):
    """Un lado: 8 casilleros, barco, héroe y Factor total."""
    def __init__(self, app, padre, titulo):
        super().__init__(padre, text=titulo, padding=6)
        self.app = app; self.heroe = None
        ttk.Label(self, text='N.º').grid(row=0, column=0); ttk.Label(self, text='Arma').grid(row=0, column=1, sticky='w')
        ttk.Label(self, text='Cant.').grid(row=0, column=2)
        self.armas, self.cant = [], []
        for k in range(8):
            ttk.Label(self, text=f'{k + 1}').grid(row=k + 1, column=0)
            cb = ttk.Combobox(self, width=34, state='readonly'); cb.grid(row=k + 1, column=1, pady=1)
            sp = ttk.Spinbox(self, from_=0, to=MAX_PILA, width=4, command=self.recalcular); sp.set(0)
            sp.grid(row=k + 1, column=2, padx=4)
            cb.bind('<<ComboboxSelected>>', lambda e, s=sp: (s.get() == '0' and s.set(1), self.recalcular()))
            sp.bind('<KeyRelease>', lambda e: self.recalcular())
            self.armas.append(cb); self.cant.append(sp)
        f = ttk.Frame(self); f.grid(row=9, column=0, columnspan=3, sticky='we', pady=(6, 0))
        ttk.Label(f, text='Barco').grid(row=0, column=0, sticky='w')
        self.barco = ttk.Combobox(f, width=28, state='readonly'); self.barco.grid(row=0, column=1, sticky='w')
        self.con_heroe = tk.BooleanVar()
        ttk.Checkbutton(f, text='Héroe', variable=self.con_heroe, command=self.recalcular).grid(row=2, column=0, sticky='w')
        ttk.Button(f, text='Héroe…', command=self.editar_heroe).grid(row=2, column=1, sticky='w')
        self.txt_heroe = ttk.Label(f, text='(sin armar)'); self.txt_heroe.grid(row=3, column=0, columnspan=2, sticky='w')
        self.coef = RecuadroFactor(self); self.coef.grid(row=10, column=0, columnspan=3, sticky='we', pady=(8, 0))

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
        d = self.lado(); tot = n = 0
        for a, c in d['tropas']:
            if a and c > 0: tot += sim.armas[a].factor() * c; n += c
        h = d['heroe']
        det = (f'{n} unidad' if n == 1 else f'{n} unidades') + (' + héroe' if h else '') + (f'  ·  Factor medio {tot / n:.1f}' if n else '')
        if n + (1 if h else 0) > MAX_PILA: det += f'  ·  ¡MÁS DE {MAX_PILA}!'
        self.coef.poner(f'FACTOR TOTAL {tot:.0f}' if n else 'FACTOR TOTAL —', det)
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
        ttk.Button(b, text='Aceptar', command=self.aceptar).pack(side='left', padx=4)
        ttk.Button(b, text='Cancelar', command=self.destroy).pack(side='left', padx=4)

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
        self.cfg = configparser.ConfigParser(); self.cfg.read(CONFIG, encoding='utf-8')
        if 'tablero' not in self.cfg: self.cfg['tablero'] = {}
        c = self.cfg['tablero']
        top = ttk.Frame(self, padding=6); top.pack(fill='x')
        ttk.Label(top, text=TITULO, font=('Segoe UI', 12, 'bold')).pack(side='left')
        self.estado = ttk.Label(top, text=''); self.estado.pack(side='right')
        self.juego = tk.StringVar(value=c.get('juego', JUEGO0))
        self.sav = tk.StringVar(value=c.get('partida', os.path.join(JUEGO0, 'SAVES', 'Tanda_Kor.SAV')))
        fb = ttk.Frame(self, padding=(6, 0)); fb.pack(fill='x')
        self.por_nombre = tk.BooleanVar(value=c.getboolean('por_nombre', False))
        ttk.Checkbutton(fb, text='Ordenar las armas por NOMBRE COMÚN (si no, por nombre de archivo)', variable=self.por_nombre,
                        command=self.reordenar).pack(side='left')
        ttk.Button(fb, text='Carpeta del juego…', command=self.configurar).pack(side='right')
        mid = ttk.Frame(self, padding=6); mid.pack(fill='both')
        self.pa = Panel(self, mid, 'ATACANTE'); self.pa.grid(row=0, column=0, sticky='n', padx=4)
        self.pd = Panel(self, mid, 'DEFENSOR'); self.pd.grid(row=0, column=1, sticky='n', padx=4)
        der = ttk.Frame(mid); der.grid(row=0, column=2, sticky='n', padx=4)
        self.subpanel_terreno(der); self.subpanel_visual(der, c)
        bot = ttk.Frame(self, padding=6); bot.pack(fill='both', expand=True)
        fila = ttk.Frame(bot); fila.pack(fill='x')
        ttk.Label(fila, text='Peleas para el %').pack(side='left')
        self.n = ttk.Spinbox(fila, from_=10, to=100000, increment=500, width=8); self.n.set(c.get('peleas', '1000')); self.n.pack(side='left', padx=4)
        self.boton = ttk.Button(fila, text='INICIAR COMBATE', command=self.iniciar); self.boton.pack(side='left', padx=12)
        ttk.Button(fila, text='⇄ Invertir atacante y defensor', command=self.invertir).pack(side='left')
        self.salida = tk.Text(bot, height=12, width=120, wrap='word', state='disabled'); self.salida.pack(fill='both', expand=True, pady=(6, 0))
        self.protocol('WM_DELETE_WINDOW', self.cerrar)
        self.after(100, self.cargar)

    def subpanel_terreno(self, padre):
        f = ttk.LabelFrame(padre, text='TERRENO (casilla del defensor)', padding=6); f.pack(fill='x')
        ttk.Label(f, text='Tipo').grid(row=0, column=0, sticky='w')
        self.terreno = ttk.Combobox(f, width=18, state='readonly'); self.terreno.grid(row=0, column=1, sticky='w')
        self.lagua = ttk.Label(f, text=''); self.lagua.grid(row=1, column=1, sticky='w')
        self.terreno.bind('<<ComboboxSelected>>', lambda e: self.ver_agua())
        self.estructura = tk.IntVar(value=0)
        for i, (t, v) in enumerate(ESTRUCTURAS):
            ttk.Radiobutton(f, text=t, value=v, variable=self.estructura).grid(row=2 + i, column=0, columnspan=2, sticky='w')
        self.bosque = tk.BooleanVar(); ttk.Checkbutton(f, text='Bosque (woods)', variable=self.bosque).grid(row=5, column=0, columnspan=2, sticky='w')
        self.noche = tk.BooleanVar(); ttk.Checkbutton(f, text='Noche (opción Day/Night)', variable=self.noche).grid(row=6, column=0, columnspan=2, sticky='w')
        ttk.Label(f, text='Defensas (ciudad)').grid(row=7, column=0, sticky='w')
        self.defensas = ttk.Spinbox(f, from_=1, to=3, width=3); self.defensas.set(1); self.defensas.grid(row=7, column=1, sticky='w')

    def subpanel_visual(self, padre, c):
        f = ttk.LabelFrame(padre, text='VISUAL (ventana de combate)', padding=6); f.pack(fill='x', pady=(6, 0))
        ttk.Label(f, text='Velocidad').grid(row=0, column=0, sticky='w')
        self.velocidad = tk.IntVar(value=c.getint('velocidad', 5)); ttk.Scale(f, from_=1, to=10, variable=self.velocidad).grid(row=0, column=1, sticky='we')
        self.efectos = tk.BooleanVar(value=c.getboolean('efectos', True)); ttk.Checkbutton(f, text='Efectos', variable=self.efectos).grid(row=1, column=0, sticky='w')
        self.sonido = tk.BooleanVar(value=c.getboolean('sonido', True)); ttk.Checkbutton(f, text='Sonido', variable=self.sonido).grid(row=1, column=1, sticky='w')
        ttk.Label(f, text='Tamaño').grid(row=2, column=0, sticky='w')
        self.tamano = ttk.Combobox(f, values=['Normal', 'Grande'], width=10, state='readonly'); self.tamano.set(c.get('tamano', 'Normal'))
        self.tamano.grid(row=2, column=1, sticky='w')
        ttk.Label(f, text='Resultados').grid(row=3, column=0, sticky='w')
        self.resultados = tk.StringVar(value=c.get('resultados', 'todos'))
        ttk.Radiobutton(f, text='Sobrevivientes y muertos', value='todos', variable=self.resultados).grid(row=4, column=0, columnspan=2, sticky='w')
        ttk.Radiobutton(f, text='Solo sobrevivientes', value='vivos', variable=self.resultados).grid(row=5, column=0, columnspan=2, sticky='w')

    def configurar(self):
        """Carpeta del juego (de ahí salen armas, héroes, ítems, hechizos, imágenes y sonidos). El motor además necesita
        una partida (.SAV) de esa carpeta como base de la memoria del juego emulado; se toma sola y no cambia la pelea
        (las armas se cargan del ARMY, el terreno y la ciudad los pone el tablero)."""
        d = filedialog.askdirectory(initialdir=self.juego.get(), title='Carpeta del juego (la que tiene DarklordAV.exe)')
        if not d: return
        d = os.path.normpath(d); self.juego.set(d)
        saves = os.path.join(d, 'SAVES'); sav = os.path.join(saves, os.path.basename(self.sav.get()))
        if not os.path.exists(sav):
            hay = sorted(f for f in os.listdir(saves) if f.lower().endswith('.sav')) if os.path.isdir(saves) else []
            if not hay: messagebox.showerror(TITULO, f'No hay partidas (.SAV) en {saves}: el motor necesita una.'); return
            sav = os.path.join(saves, hay[0])
        self.sav.set(sav); self.cargar()

    def reordenar(self):
        if self.sim:
            for p in (self.pa, self.pd): p.cargar_listas(self.sim)

    def invertir(self):
        if not self.sim: return
        a, d = self.pa.estado(), self.pd.estado()
        self.pa.poner_estado(d); self.pd.poner_estado(a)

    def cargar(self):
        self.estado['text'] = 'Cargando el juego…'; self.boton.state(['disabled'])
        def tarea():
            try: sim, err = Simulador(self.juego.get(), self.sav.get()), None
            except Exception as e: sim, err = None, e
            self.after(0, lambda: self.cargado(sim, err))
        threading.Thread(target=tarea, daemon=True).start()

    def cargado(self, sim, err):
        if err:
            self.estado['text'] = 'No se pudo cargar'; messagebox.showerror(TITULO, f'No se pudo cargar el juego:\n{err}'); return
        self.sim = sim; self.boton.state(['!disabled'])
        self.estado['text'] = f'{len(sim.armas)} armas, {len(sim.barcos)} barcos, {len(sim.clases)} clases, {len(sim.items)} ítems, {len(sim.hechizos)} hechizos'
        self.terreno['values'] = list(sim.terrenos)
        if not self.terreno.get(): self.terreno.set('plains' if 'plains' in sim.terrenos else next(iter(sim.terrenos)))
        self.ver_agua()
        for p in (self.pa, self.pd): p.cargar_listas(sim)

    def ver_agua(self):
        if self.sim and self.terreno.get():
            self.lagua['text'] = 'agua: hace falta barco (o puente)' if self.sim.es_agua(self.terreno.get()) else 'tierra'

    def escenario(self):
        try: d = int(self.defensas.get())
        except ValueError: d = 1
        return {'A': self.pa.lado(), 'D': self.pd.lado(),
                'campo': dict(terreno=self.terreno.get(), estructura=self.estructura.get(), bosque=self.bosque.get(),
                              noche=self.noche.get(), defensas=d)}

    def iniciar(self):
        try: n = max(1, int(self.n.get()))
        except ValueError: n = 1000
        try: r = self.sim.simular(self.escenario(), n)
        except Error as e: messagebox.showerror(TITULO, str(e)); return
        except Exception as e: messagebox.showerror(TITULO, f'Falló el motor:\n{e}'); return
        self.mostrar(r)
        VentanaCombate(self, self.juego.get(), r, TITULO, velocidad=self.velocidad.get(), efectos=self.efectos.get(),
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

    def cerrar(self):
        c = self.cfg['tablero']
        c.update(juego=self.juego.get(), partida=self.sav.get(), por_nombre=str(self.por_nombre.get()), peleas=self.n.get(), velocidad=str(self.velocidad.get()),
                 efectos=str(self.efectos.get()), sonido=str(self.sonido.get()), tamano=self.tamano.get(),
                 resultados=self.resultados.get())
        try:
            with open(CONFIG, 'w', encoding='utf-8') as f: self.cfg.write(f)
        except OSError: pass
        self.destroy()

if __name__ == '__main__':
    App().mainloop()
