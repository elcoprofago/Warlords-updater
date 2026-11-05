# Ventana de combate del simulador (etapas 4 y 5 de PENDIENTE-simulador-combate.md): repite la batalla de muestra del
# motor sobre el cuadro de combate del juego, con las imágenes de las unidades, tachando una por una según la secuencia
# de eventos, con los sonidos del juego, y al final muestra los resultados.
# Arte del juego (SETS\<set>\, por defecto Fantasy):
#   DLG_CMBT.PCX 624x464: el cuadro del dragón; banda de arriba (18-604, 85-170) y tres paneles: izquierdo (18-122),
#     central (132-492) y derecho (502-603), de y 183 a 431. Izquierdo = atacante, derecho = defensor (2x4 casilleros),
#     central = el duelo de las dos que pelean.
#   CMBTPICS.PCX: (0,0)-(48,48) el casillero de unidad; tiras de 12 cuadros de 49 de ancho: espada con sangre (y 154,
#     golpe), relámpago (y 210, efecto especial) y calavera que estalla (y 264, muerte). Cuál usa el juego en cada caso
#     no está visto en el exe.
#   Unidades: el ícono 48x48 de la hoja de cada arma (ARMY\<archivo>.PCX, (1,161)-(48,208)) y del héroe
#     (HERO\<.HER +0xc9>.PCX, misma hoja). El magenta es transparente en todos.
# Sonidos: FX\AttHit, DefHit, AttDead, DefDead y Spell.wav (nombres tomados de los archivos; sin ver en el exe).
# Eventos (motor.py): 0/1 pierde una vida el defensor/atacante, 2/3 entra la siguiente, 6/7 gana atacante/defensor;
# las muertes se sacan de la estructura (motor.muertes); 0xc.. son efectos especiales sin identificar.
import os
import tkinter as tk
from PIL import Image, ImageChops, ImageTk

try: import winsound
except ImportError: winsound = None

ICONO = (1, 161, 49, 209)
ESCALA = {'Normal': 1.0, 'Grande': 1.5}
SET = 'Fantasy'
ORO, TINTA, SOMBRA = '#e8c860', '#f4ecd0', '#000000'
TIRAS = {'golpe': 154, 'efecto': 210, 'muerte': 264}

def _indice(carpeta):
    try: return {f.lower(): os.path.join(carpeta, f) for f in os.listdir(carpeta)}
    except OSError: return {}

def _transparente(im):
    """RGB -> RGBA con el magenta transparente."""
    im = im.convert('RGB')
    r, g, b = ImageChops.difference(im, Image.new('RGB', im.size, (255, 0, 255))).split()
    im.putalpha(ImageChops.lighter(ImageChops.lighter(r, g), b).point(lambda v: 255 if v else 0))
    return im

def pcx(ruta):
    """Un PCX del juego sin distinguir mayúsculas (ruta con extensión), RGBA; None si no está."""
    p = _indice(os.path.dirname(ruta)).get(os.path.basename(ruta).lower())
    if not p: return None
    try: return _transparente(Image.open(p))
    except OSError: return None

def icono(ruta, lado):
    """Ícono de la hoja PCX de un arma o héroe (ruta sin extensión), o None si no está."""
    if not ruta: return None
    im = pcx(ruta + '.pcx')
    return None if im is None else im.crop(ICONO).resize((lado, lado), Image.NEAREST)

class VentanaCombate(tk.Toplevel):
    def __init__(self, padre, juego, r, titulo, velocidad=5, efectos=True, sonido=True, tamano='Normal',
                 resultados='todos'):
        super().__init__(padre); self.title(titulo); self.configure(bg='#000000'); self.resizable(False, False)
        self.r, self.efectos, self.sonido_si, self.resultados = r, efectos, sonido, resultados
        self.paso_ms = max(60, int(1400 / max(1, velocidad)))
        self.fx = _indice(os.path.join(juego, 'FX'))
        f = self.f = ESCALA.get(tamano, 1.0); z = self.z
        sets = os.path.join(juego, 'SETS', SET)
        self.fotos = []
        fondo = pcx(os.path.join(sets, 'DLG_CMBT.PCX'))
        picts = pcx(os.path.join(sets, 'CMBTPICS.PCX'))
        W, H = z(624), z(464)
        self.c = tk.Canvas(self, width=W, height=H, bg='#000000', highlightthickness=0); self.c.pack()
        if fondo is not None: self.imagen(fondo.resize((W, H), Image.LANCZOS), 0, 0)
        else: self.c.create_rectangle(z(18), z(85), z(604), z(431), fill='#203048', outline=ORO, width=3)
        s = self.s = z(48)
        casillero = picts.crop((0, 0, 48, 48)).resize((s, s), Image.NEAREST) if picts is not None else None
        self.tiras = {}
        if picts is not None:
            for k, y in TIRAS.items():
                self.tiras[k] = [ImageTk.PhotoImage(picts.crop((i * 49, y, i * 49 + 49, y + 52)).resize((z(98), z(104)), Image.NEAREST))
                                 for i in range(12)]
        self.f_tit = ('Arial', max(9, z(13)), 'bold'); self.f_txt = ('Arial', max(8, z(10)), 'bold')
        self.f_chi = ('Arial', max(7, z(8)), 'bold')
        self.sombra(z(130), z(112), 'ATACANTE', self.f_tit, ORO); self.sombra(z(494), z(112), 'DEFENSOR', self.f_tit, ORO)
        pct = r['pct']
        self.sombra(z(130), z(138), f'gana el {pct:.1f} %', self.f_txt); self.sombra(z(494), z(138), f'gana el {100 - pct:.1f} %', self.f_txt)
        # casilleros: 2x4 en los paneles de los costados, en el orden de pelea
        self.u = {'A': [], 'D': []}; self.grande = {}
        for lado, x0 in (('A', 21), ('D', 505)):
            for k, ficha in enumerate(r['fichas_a' if lado == 'A' else 'fichas_d']):
                x, y = z(x0 + (k % 2) * 50), z(190 + (k // 2) * 60)
                if casillero is not None: self.imagen(casillero, x, y)
                im = icono(ficha['imagen'], s)
                if im is not None: self.imagen(im, x, y)
                else: self.c.create_text(x + s / 2, y + s / 2, text=ficha['nombre'], fill=TINTA, width=s, font=self.f_chi)
                marco = self.c.create_rectangle(x - 1, y - 1, x + s + 1, y + s + 1, outline='', width=2)
                self.c.create_text(x + 3, y + 2, text=str(k + 1), anchor='nw', fill=ORO, font=self.f_chi)
                pw = max(4, z(5)); pips = [self.c.create_rectangle(x + i * (pw + 2), y + s + 2, x + i * (pw + 2) + pw, y + s + 2 + pw,
                                                                  fill='#40c040', outline='#000000') for i in range(ficha['vidas'])]
                self.u[lado].append(dict(x=x, y=y, marco=marco, pips=pips, vidas=ficha['vidas'], muerto=False, ficha=ficha,
                                         foto=ImageTk.PhotoImage(icono(ficha['imagen'], z(96))) if im is not None else None))
        # duelo en el panel central
        self.duelo = {'A': (z(175), z(250)), 'D': (z(353), z(250))}
        self.id_duelo = {}
        self.sombra(z(312), z(300), 'VS', self.f_tit, ORO, tag='duelo')
        self.leyenda = self.c.create_text(z(312), z(395), text='', fill=ORO, font=self.f_tit, width=z(340))
        self.leyenda_s = None
        # botones dentro del cuadro, abajo
        self.bsaltar = self.boton(z(145), z(440), 'Saltar al final', self.saltar)
        self.boton(z(480), z(440), 'Cerrar', self.cerrar, 'ne')
        self.protocol('WM_DELETE_WINDOW', self.cerrar); self.bind('<Escape>', lambda e: self.cerrar())
        self.ev = list(r['eventos']); self.i = 0; self.na = self.nd = 0; self.ea = self.ed = False
        self.muertes = []; self.tarea = None; self.rapido = False; self.terminado = False
        self.tarea = self.after(400, self.paso)

    # ---- dibujo ----
    def z(self, v): return int(round(v * self.f))

    def imagen(self, im, x, y, anchor='nw', tag=()):
        ph = im if isinstance(im, ImageTk.PhotoImage) else ImageTk.PhotoImage(im)
        self.fotos.append(ph); return self.c.create_image(x, y, image=ph, anchor=anchor, tags=tag)

    def sombra(self, x, y, t, fuente, color=TINTA, anchor='center', tag=(), width=0):
        a = self.c.create_text(x + 2, y + 2, text=t, font=fuente, fill=SOMBRA, anchor=anchor, tags=tag, width=width)
        b = self.c.create_text(x, y, text=t, font=fuente, fill=color, anchor=anchor, tags=tag, width=width)
        return a, b

    def boton(self, x, y, texto, cmd, anchor='nw'):
        b = tk.Button(self.c, text=texto, command=cmd, font=self.f_txt, bg='#2a2218', fg=ORO, activebackground='#ffd8a8',
                      relief='flat', bd=0, highlightthickness=2, highlightbackground='#c8a040', cursor='hand2', padx=8)
        self.c.create_window(x, y, window=b, anchor=anchor); return b

    def poner_duelo(self, lado, k):
        if lado in self.id_duelo: self.c.delete(self.id_duelo[lado])
        if k >= len(self.u[lado]): return
        d = self.u[lado][k]; x, y = self.duelo[lado]
        if d['foto'] is not None: self.id_duelo[lado] = self.imagen(d['foto'], x, y)
        else: self.id_duelo[lado] = self.c.create_text(x + self.z(48), y + self.z(48), text=d['ficha']['nombre'], fill=TINTA, font=self.f_tit)

    def animar(self, tira, lado):
        cuadros = self.tiras.get(tira)
        if not self.efectos or self.rapido or not cuadros: return
        x, y = self.duelo[lado]; t = max(20, self.paso_ms // (len(cuadros) + 2))
        it = self.c.create_image(x, y, image=cuadros[0], anchor='nw')
        def sig(i):
            if not self.winfo_exists(): return
            if i >= len(cuadros): self.c.delete(it); return
            self.c.itemconfigure(it, image=cuadros[i]); self.after(t, lambda: sig(i + 1))
        sig(1)

    # ---- sonido ----
    def sonar(self, nombre):
        if not (self.sonido_si and winsound) or self.rapido: return
        p = self.fx.get(nombre.lower() + '.wav')
        if p:
            try: winsound.PlaySound(p, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
            except RuntimeError: pass

    # ---- estado de las unidades ----
    def activa(self, lado, k):
        for j, d in enumerate(self.u[lado]):
            if not d['muerto']: self.c.itemconfigure(d['marco'], outline='#ffd040' if j == k else '')
        self.poner_duelo(lado, k)

    def matar(self, lado, k):
        if k >= len(self.u[lado]): return
        d = self.u[lado][k]; d['muerto'] = True; self.muertes.append((lado, k))
        x, y, s = d['x'], d['y'], self.s
        self.c.create_rectangle(x, y, x + s, y + s, fill='#000000', stipple='gray50', outline='')
        self.c.create_line(x + 3, y + 3, x + s - 3, y + s - 3, fill='#e02020', width=3)
        self.c.create_line(x + s - 3, y + 3, x + 3, y + s - 3, fill='#e02020', width=3)
        self.c.itemconfigure(d['marco'], outline='#802020')
        for p in d['pips']: self.c.itemconfigure(p, fill='#503020')
        self.animar('muerte', lado); self.sonar('AttDead' if lado == 'A' else 'DefDead')

    def golpe(self, lado, k):
        if k >= len(self.u[lado]): return
        d = self.u[lado][k]
        if d['vidas'] > 0:
            d['vidas'] -= 1; self.c.itemconfigure(d['pips'][d['vidas']], fill='#c03020')
        self.animar('golpe', lado); self.sonar('DefHit' if lado == 'D' else 'AttHit')

    def decir(self, t):
        self.c.itemconfigure(self.leyenda, text=t)
        if self.leyenda_s: self.c.delete(self.leyenda_s)
        self.leyenda_s = self.c.create_text(self.z(312) + 2, self.z(395) + 2, text=t, fill=SOMBRA, font=self.f_tit, width=self.z(340))
        self.c.tag_raise(self.leyenda)

    # ---- repetición de eventos ----
    def paso(self):
        self.tarea = None
        if self.i >= len(self.ev): self.fin(); return
        c = self.ev[self.i]; self.i += 1
        if c == 0: self.golpe('D', self.nd)
        elif c == 1: self.golpe('A', self.na)
        elif c == 2:
            if self.ea: self.matar('A', self.na); self.na += 1
            self.ea = True; self.activa('A', self.na)
        elif c == 3:
            if self.ed: self.matar('D', self.nd); self.nd += 1
            self.ed = True; self.activa('D', self.nd)
        elif c == 6: self.matar('D', self.nd); self.fin(); return
        elif c == 7: self.matar('A', self.na); self.fin(); return
        elif c in (4, 5, 8, 9, 10, 11): pass     # códigos de muerte: la muerte se marca por la estructura (motor.muertes)
        elif self.efectos and not self.rapido:
            self.decir(f'efecto especial (código 0x{c:x})'); self.sonar('Spell')
            self.animar('efecto', 'A'); self.animar('efecto', 'D')
            self.after(self.paso_ms, lambda: self.winfo_exists() and not self.terminado and self.decir(''))
        if self.rapido: self.paso()
        else: self.tarea = self.after(self.paso_ms, self.paso)

    def saltar(self):
        if self.tarea: self.after_cancel(self.tarea); self.tarea = None
        self.rapido = True; self.paso()

    def fin(self):
        self.rapido = False; self.terminado = True; self.bsaltar.configure(state='disabled')
        r = self.r; gana = 'ATACANTE' if r['gana'] else 'DEFENSOR'
        coincide = self.muertes == [tuple(m) for m in r['muertes']]    # la repetición tiene que coincidir con el motor
        self.decir(f'¡Gana el {gana}!' + ('' if coincide else ' (la repetición no coincide con el motor)'))
        muertos = set(self.muertes)
        def fila(lado, fichas):
            out = []
            for k, f in enumerate(fichas):
                m = (lado, k) in muertos
                if m and self.resultados == 'vivos': continue
                out.append(f'{k + 1}. {f["nombre"]}' + (' ✝' if m else ''))
            return '   '.join(out) or '(ninguno)'
        self.c.delete('duelo')
        for i in list(self.id_duelo.values()): self.c.delete(i)
        self.id_duelo = {}
        z = self.z
        self.c.create_rectangle(z(140), z(215), z(484), z(370), fill='#e8d8a8', outline='#c8a040', width=3)
        t = ('SOBREVIVIENTES Y MUERTOS' if self.resultados == 'todos' else 'SOBREVIVIENTES')
        self.c.create_text(z(312), z(228), text=t, font=self.f_txt, fill='#5a3a10')
        for j, (nom, lado, fichas) in enumerate((('Atacante', 'A', r['fichas_a']), ('Defensor', 'D', r['fichas_d']))):
            self.c.create_text(z(150), z(250 + j * 58), text=f'{nom}:', anchor='nw', font=self.f_txt, fill='#000000')
            self.c.create_text(z(150), z(266 + j * 58), text=fila(lado, fichas), anchor='nw', font=self.f_chi,
                               fill='#000000', width=z(325))

    def cerrar(self):
        if self.tarea: self.after_cancel(self.tarea)
        if winsound:
            try: winsound.PlaySound(None, 0)
            except RuntimeError: pass
        self.destroy()
