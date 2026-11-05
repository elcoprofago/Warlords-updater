# Ventana de combate del simulador (etapa 4 de PENDIENTE-simulador-combate.md): repite la batalla de muestra del motor
# con las imágenes de las unidades del juego, tachando una por una según la secuencia de eventos, con los sonidos del
# juego, y al final muestra los resultados.
# Imágenes: el ícono 48x48 de la hoja de cada arma (ARMY\<archivo>.PCX, (1,161)-(48,208); el magenta es transparente)
# y del héroe (HERO\<.HER +0xc9>.PCX, misma hoja). Sonidos: FX\AttHit, DefHit, AttDead, DefDead y Spell.wav (los
# nombres los tomo de los archivos; no está visto en el exe cuál usa el juego en cada golpe).
# Eventos (motor.py): 0/1 pierde una vida el defensor/atacante, 2/3 entra la siguiente, 6/7 gana atacante/defensor;
# las muertes se sacan de la estructura (motor.muertes); 0xc.. son efectos especiales sin identificar.
import os, sys
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageChops, ImageTk

try: import winsound
except ImportError: winsound = None

ICONO = (1, 161, 49, 209)
TAM = {'Normal': 48, 'Grande': 96}

def _indice(carpeta):
    try: return {f.lower(): os.path.join(carpeta, f) for f in os.listdir(carpeta)}
    except OSError: return {}

def icono(ruta, lado):
    """Ícono de la hoja PCX (o None si no está); ruta sin extensión, sin distinguir mayúsculas."""
    if not ruta: return None
    p = _indice(os.path.dirname(ruta)).get(os.path.basename(ruta).lower() + '.pcx')
    if not p: return None
    try: im = Image.open(p).convert('RGB').crop(ICONO)
    except OSError: return None
    r, g, b = ImageChops.difference(im, Image.new('RGB', im.size, (255, 0, 255))).split()
    im.putalpha(ImageChops.lighter(ImageChops.lighter(r, g), b).point(lambda v: 255 if v else 0))
    return im.resize((lado, lado), Image.NEAREST)

class VentanaCombate(tk.Toplevel):
    def __init__(self, padre, juego, r, titulo, velocidad=5, efectos=True, sonido=True, tamano='Normal',
                 resultados='todos'):
        super().__init__(padre); self.title(titulo); self.configure(bg='#1b1610')
        self.r, self.efectos, self.sonido_si, self.resultados = r, efectos, sonido, resultados
        self.paso_ms = max(60, int(1400 / max(1, velocidad)))
        self.fx = _indice(os.path.join(juego, 'FX'))
        s = self.s = TAM.get(tamano, 48); pad = 14; w = s + pad
        n = max(len(r['fichas_a']), len(r['fichas_d']), 1)
        ancho = max(n * w + 2 * pad + 120, 460); self.alto = 2 * (s + 44) + 110
        tk.Label(self, text=titulo, bg='#1b1610', fg='#e8d8a0', font=('Segoe UI', 11, 'bold')).pack(pady=(6, 0))
        self.c = tk.Canvas(self, width=ancho, height=self.alto, bg='#2a2218', highlightthickness=0); self.c.pack(padx=8, pady=6)
        self.fotos = []; self.u = {'A': [], 'D': []}
        for lado, y0, nombre in (('D', 30, 'DEFENSOR'), ('A', self.alto - s - 52, 'ATACANTE')):
            self.c.create_text(pad, y0 - 16, text=nombre, anchor='w', fill='#e8d8a0', font=('Segoe UI', 10, 'bold'))
            for k, f in enumerate(r['fichas_a' if lado == 'A' else 'fichas_d']):
                x = pad + 110 + k * w
                marco = self.c.create_rectangle(x - 3, y0 - 3, x + s + 3, y0 + s + 3, outline='#5a4a30', width=2)
                im = icono(f['imagen'], s)
                if im is not None:
                    ph = ImageTk.PhotoImage(im); self.fotos.append(ph); self.c.create_image(x, y0, image=ph, anchor='nw')
                else:
                    self.c.create_text(x + s / 2, y0 + s / 2, text=f['nombre'], fill='#e8d8a0', width=s)
                self.c.create_text(x + s / 2, y0 + s + 10, text=f'{k + 1}. {f["nombre"]}'[:12], fill='#c8b888', font=('Segoe UI', 7))
                pips = [self.c.create_rectangle(x + i * 7, y0 + s + 20, x + i * 7 + 5, y0 + s + 25, fill='#40c040', outline='')
                        for i in range(f['vidas'])]
                self.u[lado].append(dict(x=x, y=y0, marco=marco, pips=pips, vidas=f['vidas'], muerto=False))
        self.leyenda = self.c.create_text(ancho / 2, self.alto / 2, text='', fill='#ffe080', font=('Segoe UI', 12, 'bold'))
        fb = tk.Frame(self, bg='#1b1610'); fb.pack(fill='x', padx=8, pady=(0, 8))
        self.bsaltar = ttk.Button(fb, text='Saltar al final', command=self.saltar); self.bsaltar.pack(side='left')
        ttk.Button(fb, text='Cerrar', command=self.cerrar).pack(side='right')
        self.res = tk.Text(self, height=7, width=60, wrap='word', state='disabled', bg='#2a2218', fg='#e8d8a0')
        self.protocol('WM_DELETE_WINDOW', self.cerrar); self.bind('<Escape>', lambda e: self.cerrar())
        self.ev = list(r['eventos']); self.i = 0; self.na = self.nd = 0; self.ea = self.ed = False
        self.muertes = []; self.tarea = None; self.rapido = False
        self.tarea = self.after(400, self.paso)

    # ---- sonido y efectos ----
    def sonar(self, nombre):
        if not (self.sonido_si and winsound) or self.rapido: return
        p = self.fx.get(nombre.lower() + '.wav')
        if p:
            try: winsound.PlaySound(p, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
            except RuntimeError: pass

    def destello(self, lado, k, color):
        if not self.efectos or self.rapido or k >= len(self.u[lado]): return
        d = self.u[lado][k]
        r = self.c.create_rectangle(d['x'], d['y'], d['x'] + self.s, d['y'] + self.s, outline=color, width=4)
        self.after(max(40, self.paso_ms // 2), lambda: self.c.delete(r))

    def activa(self, lado, k):
        for j, d in enumerate(self.u[lado]):
            if not d['muerto']: self.c.itemconfigure(d['marco'], outline='#ffd040' if j == k else '#5a4a30')

    def matar(self, lado, k):
        if k >= len(self.u[lado]): return
        d = self.u[lado][k]; d['muerto'] = True; self.muertes.append((lado, k))
        x, y, s = d['x'], d['y'], self.s
        self.c.create_rectangle(x, y, x + s, y + s, fill='#000000', stipple='gray50', outline='')
        self.c.create_line(x, y, x + s, y + s, fill='#e02020', width=3)
        self.c.create_line(x + s, y, x, y + s, fill='#e02020', width=3)
        self.c.itemconfigure(d['marco'], outline='#802020')
        for p in d['pips']: self.c.itemconfigure(p, fill='#503020')
        self.sonar('AttDead' if lado == 'A' else 'DefDead')

    def golpe(self, lado, k):
        if k >= len(self.u[lado]): return
        d = self.u[lado][k]
        if d['vidas'] > 0:
            d['vidas'] -= 1; self.c.itemconfigure(d['pips'][d['vidas']], fill='#c03020')
        self.destello(lado, k, '#ff3030'); self.sonar('DefHit' if lado == 'D' else 'AttHit')

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
            self.c.itemconfigure(self.leyenda, text=f'efecto especial (código 0x{c:x})'); self.sonar('Spell')
            self.after(self.paso_ms, lambda: self.c.itemconfigure(self.leyenda, text=''))
        if self.rapido: self.paso()
        else: self.tarea = self.after(self.paso_ms, self.paso)

    def saltar(self):
        if self.tarea: self.after_cancel(self.tarea); self.tarea = None
        self.rapido = True; self.paso()

    def fin(self):
        self.rapido = False; self.bsaltar.state(['disabled'])
        r = self.r; gana = 'ATACANTE' if r['gana'] else 'DEFENSOR'
        self.c.itemconfigure(self.leyenda, text=f'¡Gana el {gana}!')
        if self.muertes != [tuple(m) for m in r['muertes']]:      # la repetición tiene que coincidir con el motor
            self.c.itemconfigure(self.leyenda, text=f'¡Gana el {gana}! (la repetición no coincide con el motor)')
        muertos = set(self.muertes)
        def fila(lado, fichas):
            out = []
            for k, f in enumerate(fichas):
                m = (lado, k) in muertos
                if m and self.resultados == 'vivos': continue
                out.append(f'{k + 1}. {f["nombre"]}' + (' ✝' if m else ''))
            return '  '.join(out) or '(ninguno)'
        t = [f'Gana el {gana}.  En {r["n"]} peleas el atacante gana el {r["pct"]:.2f} % (defensor: {100 - r["pct"]:.2f} %).', '',
             ('Sobrevivientes y muertos' if self.resultados == 'todos' else 'Sobrevivientes') + ':',
             f'  Atacante: {fila("A", r["fichas_a"])}', f'  Defensor: {fila("D", r["fichas_d"])}']
        self.res.pack(fill='both', padx=8, pady=(0, 8))
        self.res['state'] = 'normal'; self.res.insert('1.0', '\n'.join(t)); self.res['state'] = 'disabled'

    def cerrar(self):
        if self.tarea: self.after_cancel(self.tarea)
        if winsound:
            try: winsound.PlaySound(None, 0)
            except RuntimeError: pass
        self.destroy()
