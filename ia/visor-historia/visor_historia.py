# Visor de historia: el "Events Report" de una partida guardada (.SAV), con el arte del juego, línea de tiempo por
# ronda, buscador y exportación a PDF o texto (PENDIENTE-visor-historia.md). Lee todo con ia\historia.py y toma el arte
# (fondo, escudos, texturas, fuentes) de la carpeta del juego donde está el .SAV. Se empaqueta con build.py.
import ctypes, os, sys, time
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import historia, tanda   # noqa: E402

VERSION = '1.0.0.0'
TITULO = f'VISOR DE HISTORIA — VERSIÓN {VERSION}'
FONDO = '#1b1b1b'
TEXTO, SOMBRA, RESALTE = '#f0e6c8', '#000000', '#ffd966'
COLOR = {'white': (250, 250, 250), 'yellow': (240, 220, 40), 'orange': (240, 140, 30), 'red': (220, 30, 30),
         'green': (40, 180, 40), 'blue': (40, 80, 230), 'cyan': (60, 210, 230), 'black': (40, 40, 40)}
NEUTRAL = (150, 150, 150)
# Cuadro DLG_BIG (620x460): título en la barra de arriba, minimapa a la izquierda y renglones a la derecha.
TIT_Y, SUB_Y = 28, 72
MINI = (28, 95, 200, 240)              # x, y, ancho y alto máximos del minimapa
ESC_Y = 350                            # fila de escudos para elegir el color del minimapa
REN_X, REN_Y, REN_ALTO = 245, 98, 20   # 16 renglones como máximo por ronda (2 por jugador)


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
        raiz.title(TITULO)
        raiz.configure(bg=FONDO)
        raiz.resizable(False, False)
        self.f_ren = tkfont.Font(family='Arial', size=11)
        fams = set(tkfont.families())
        self.f_tit = tkfont.Font(family='Uncial ATT' if 'Uncial ATT' in fams else 'Times New Roman', size=18)
        self.f_sub = tkfont.Font(family=self.f_tit.cget('family'), size=13)
        lbl = dict(bg=FONDO, fg='#e8e8e8', font=('Segoe UI', 10), anchor='w')

        # Panel superior
        sup = tk.Frame(raiz, bg=FONDO, padx=10, pady=8)
        sup.pack(fill='x')
        tk.Button(sup, text='Abrir…', width=10, command=self.abrir).grid(row=0, column=0, rowspan=3, padx=(0, 14))
        self.d_nombre = tk.Label(sup, **{**lbl, 'font': ('Segoe UI', 13, 'bold')})
        self.d_nombre.grid(row=0, column=1, columnspan=2, sticky='w')
        self.d_turnos, self.d_victoria = tk.Label(sup, **lbl), tk.Label(sup, **lbl)
        self.d_mapa, self.d_guardado = tk.Label(sup, **lbl), tk.Label(sup, **lbl)
        self.d_turnos.grid(row=1, column=1, sticky='w', padx=(0, 30))
        self.d_victoria.grid(row=1, column=2, sticky='w')
        self.d_mapa.grid(row=2, column=1, sticky='w', padx=(0, 30))
        self.d_guardado.grid(row=2, column=2, sticky='w')
        self.aviso = tk.Label(raiz, bg=FONDO, fg='#ff7070', font=('Segoe UI', 9), wraplength=620, justify='left')
        self.aviso.pack(fill='x', padx=10)

        # Buscador, separado del panel superior
        tk.Frame(raiz, bg='#444', height=1).pack(fill='x', padx=10, pady=(4, 6))
        bus = tk.Frame(raiz, bg=FONDO, padx=10)
        bus.pack(fill='x')
        tk.Label(bus, text='Buscar:', **{**lbl, 'anchor': 'e'}).pack(side='left')
        self.buscar = tk.StringVar()
        self.buscar.trace_add('write', lambda *_: self.al_buscar())
        e = tk.Entry(bus, textvariable=self.buscar, width=24, font=('Segoe UI', 10))
        e.pack(side='left', padx=6)
        e.bind('<Return>', lambda _: self.saltar(1))
        tk.Button(bus, text='◀', width=3, command=lambda: self.saltar(-1)).pack(side='left')
        tk.Button(bus, text='▶', width=3, command=lambda: self.saltar(1)).pack(side='left', padx=(2, 8))
        self.d_coinc = tk.Label(bus, **lbl, width=1)   # ancho fijo: no estira la ventana
        self.d_coinc.pack(side='left', fill='x', expand=True)

        # Panel principal: el cuadro y la línea de tiempo
        self.cv = tk.Canvas(raiz, width=620, height=460, bg=FONDO, highlightthickness=0)
        self.cv.pack(padx=10, pady=(8, 0))
        self.cv.bind('<Button-1>', self.clic_cuadro)
        self.barra = tk.Canvas(raiz, width=620, height=34, bg=FONDO, highlightthickness=0)
        self.barra.pack(padx=10, pady=(4, 0))
        self.barra.bind('<Button-1>', self.clic_barra)
        self.barra.bind('<B1-Motion>', self.clic_barra)
        raiz.bind('<Left>', lambda _: self.ir(self.ronda - 1))
        raiz.bind('<Right>', lambda _: self.ir(self.ronda + 1))

        # Panel inferior
        inf = tk.Frame(raiz, bg=FONDO, padx=10, pady=10)
        inf.pack(fill='x')
        tk.Button(inf, text='Limpiar búsqueda', command=lambda: self.buscar.set('')).pack(side='left')
        tk.Button(inf, text='Exportar texto…', command=self.exportar_texto).pack(side='right')
        tk.Button(inf, text='Exportar PDF…', command=self.exportar_pdf).pack(side='right', padx=6)
        self.dibujar()

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
        self.d_nombre['text'] = c['nombre']
        self.d_turnos['text'] = f"Turnos jugados: {c['ronda'] - 1}  (ronda {c['ronda']} en curso)"
        self.d_victoria['text'] = 'Victoria: ' + c['victoria'] + (f", límite {c['limite']}" if c['limite'] else '')
        self.d_mapa['text'] = 'Mapa: ' + ('aleatorio' if c['mapa'] == 'Random' else f"escenario «{c['mapa']}»") \
            + f"  ({c['set']})"
        self.d_guardado['text'] = 'Último guardado: ' + time.strftime('%d/%m/%Y %H:%M', time.localtime(os.path.getmtime(ruta)))
        self.aviso['text'] = ('Aviso: el historial guardado en esta partida es de otra partida (pasa con las guardadas '
                              'armadas a partir de otra). Los sucesos y nombres de ciudad no corresponden a este mapa.'
                              if p.ajena else '')
        self.al_buscar()
        self.ir(max([1] + [r for r, rs in self.rondas.items() if rs]))   # la última ronda con sucesos

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
        if not self.p:
            cv.create_text(310, 230, text='Abrí una partida guardada (.SAV) con «Abrir…»', fill='#aaa',
                           font=('Segoe UI', 12))
            self.dibujar_barra()
            return
        cv.create_image(0, 0, image=self.foto(self.fondo), anchor='nw')
        cv.create_text(310, TIT_Y, text='History of Events', font=self.f_tit, fill='#20203a')
        self.texto_sombra(REN_X + 175, SUB_Y, f'Events for turn {self.ronda}', self.f_sub, 'n')
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
        if not self.p:
            return
        n = self.p.cabecera['ronda']
        x = lambda r: 20 + (580 * (r - 1) / max(1, n - 1))
        b.create_line(20, 14, 600, 14, fill='#777', width=3)
        for r in sorted({r for r, _ in self.coinc}):
            b.create_line(x(r), 6, x(r), 22, fill=RESALTE, width=2)
        b.create_oval(x(self.ronda) - 7, 7, x(self.ronda) + 7, 21, fill='#c8a040', outline='#000')
        b.create_text(20, 30, text='1', fill='#aaa', font=('Segoe UI', 8))
        b.create_text(600, 30, text=str(n), fill='#aaa', font=('Segoe UI', 8))
        b.create_text(310, 30, text=f'Ronda {self.ronda} de {n}' + (' (en curso)' if self.ronda == n else ''),
                      fill='#ddd', font=('Segoe UI', 8))

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
        enc = [c['nombre'], self.d_turnos['text'], self.d_victoria['text'], self.d_mapa['text'],
               self.d_guardado['text']] + ([self.aviso['text']] if self.aviso['text'] else [])
        cuerpo = []
        for r in range(1, c['ronda'] + 1):
            cuerpo.append((r, [(self.p.jugador(j) if j < 8 else '', s) for j, s in self.rondas.get(r, [])]))
        return enc, cuerpo

    def destino(self, ext, tipo):
        if not self.p:
            return None
        return filedialog.asksaveasfilename(title='Exportar', defaultextension=ext,
                                            initialfile=self.p.cabecera['nombre'] + ext,
                                            filetypes=[(tipo, '*' + ext)])

    def exportar_texto(self):
        ruta = self.destino('.txt', 'Texto')
        if not ruta:
            return
        enc, cuerpo = self.renglones_export()
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write('\n'.join(enc) + '\n')
            for r, rs in cuerpo:
                f.write(f'\nEvents for turn {r}\n')
                for j, s in rs or [('', self.p.T[0][0])]:
                    f.write(f'  {j + ": " if j else ""}{s}\n')
        messagebox.showinfo(TITULO, f'Exportado:\n{ruta}')

    def exportar_pdf(self):
        ruta = self.destino('.pdf', 'PDF')
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
            pdf.set_font(tit, '', 12)
            pdf.cell(0, 7, f'Events for turn {r}', new_x='LMARGIN', new_y='NEXT')
            pdf.set_font('ui', '', 10)
            for j, s in rs or [('', self.p.T[0][0])]:
                pdf.cell(42, 5, j)
                pdf.cell(0, 5, s, new_x='LMARGIN', new_y='NEXT')
        pdf.output(ruta)
        messagebox.showinfo(TITULO, f'Exportado:\n{ruta}')


if __name__ == '__main__':
    fuente_privada(os.path.join(tanda.JUEGO, 'FONTS', 'UNCIAL.TTF'))
    raiz = tk.Tk()
    v = Visor(raiz)
    if len(sys.argv) > 1:
        v.abrir(sys.argv[1])
    raiz.mainloop()
