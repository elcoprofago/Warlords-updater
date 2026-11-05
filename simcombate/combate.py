# Ventana de combate del simulador (etapas 4 y 5 de PENDIENTE-simulador-combate.md): repite la batalla de muestra del
# motor sobre el cuadro de combate del juego, con las imágenes de las unidades, tachando una por una según la secuencia
# de eventos, con los sonidos del juego, y al final muestra los resultados.
# Arte del juego (SETS\<set>\, por defecto Fantasy):
#   DLG_CMBT.PCX 624x464: el cuadro del dragón; banda de arriba (18-604, 85-170) y tres paneles: izquierdo (18-122),
#     central (132-492) y derecho (502-603), de y 183 a 431. Izquierdo = atacante, derecho = defensor (2x4 casilleros),
#     central = el duelo de las dos que pelean.
#   CMBTPICS.PCX: (0,0)-(48,48) el casillero de unidad.
#   Unidades: el ícono 48x48 de la hoja de cada arma (ARMY\<archivo>.PCX, (1,161)-(48,208)) y del héroe
#     (HERO\<.HER +0xc9>.PCX, misma hoja). El magenta es transparente en todos.
# Efectos y sonidos: copiados de la ventana de combate de DarklordAV.exe (leído en el exe el 5/11/2026):
#   0x405cd0 recorre los eventos y 0x406ed0(código) muestra cada uno: una animación de CMBTPICS (0x407e20, tabla en
#   ANIM) y un sonido (0x4465e0 -> recurso de WAR3AV.RES -> FX\ o SETS\Fantasy\). Ver EVENTO y elegir().
#   Cada golpe: las chispas sobre la tropa golpeada, con su sonido, una vez por vida que quita (0x16-0x18 / 0x19-0x1b
#   quitan 2, 3 o 4: tantas chispas seguidas). Se muestran todos los golpes (lo que el usuario ve en el juego). La muerte: la explosión, salvo la que causa
#   un poder: flechas (Missiles), daga con sangre (Assassin), relámpago (Lightning), roca que se deshace en polvo
#   (Trample), ácido (Acid), calavera (Dragonslayer). Lightning que no mata parte las vidas a la mitad (relámpago
#   corto); Acid que no mata parte la fuerza a la mitad. Las tropas no suenan con su ARMY\<archivo>00.wav en el combate.
# Eventos (motor.py): 0/1 pierde una vida el defensor/atacante, 2/3 entra la siguiente, 6/7 gana atacante/defensor;
# las muertes se marcan por la estructura (motor.muertes); el resto, en EVENTO.
import os
import tkinter as tk
from PIL import Image, ImageChops, ImageTk

try: import winsound
except ImportError: winsound = None

ICONO = (1, 161, 49, 209)
ESCALA = {'Normal': 1.0, 'Grande': 1.5}
SET = 'Fantasy'
ORO, TINTA, SOMBRA = '#e8c860', '#f4ecd0', '#000000'
VIVA, PERDIDA, MUERTA = '#30e030', '#e02020', '#503020'
# animaciones de 0x407e20: nombre -> (x del primer cuadro, y, ancho, alto, cuadros) en CMBTPICS
ANIM = {'chispas': (48, 0, 48, 48, 5), 'explosion': (0, 48, 49, 54, 12), 'flechas': (0, 102, 49, 54, 12),
        'daga': (0, 156, 49, 54, 12), 'relampago': (0, 210, 49, 54, 12), 'calavera': (0, 264, 49, 54, 12),
        'roca': (0, 318, 49, 54, 12), 'acido': (0, 426, 49, 54, 12), 'relampago_corto': (0, 210, 49, 48, 5)}
# código (ya convertido como en 0x406ed0) -> (lado que lo recibe, qué le pasa, animación, sonido)
#   qué le pasa: un número = vidas que pierde; 'mitad' = vidas a la mitad; 'fuerza' = fuerza a la mitad; 'muere'
EVENTO = {0: ('D', 1, 'chispas', 'DefHit'), 0x16: ('D', 2, 'chispas', 'DefHit'), 0x17: ('D', 3, 'chispas', 'DefHit'),
          0x18: ('D', 4, 'chispas', 'DefHit'), 0x13: ('D', 'mitad', 'relampago_corto', 'zzzt'),
          1: ('A', 1, 'chispas', 'AttHit'), 0x19: ('A', 2, 'chispas', 'AttHit'), 0x1a: ('A', 3, 'chispas', 'AttHit'),
          0x1b: ('A', 4, 'chispas', 'AttHit'), 0x12: ('A', 'mitad', 'relampago_corto', 'zzzt'),
          0xd: ('D', 'fuerza', 'acido', 'zzzt'), 0x10: ('A', 'fuerza', 'acido', 'zzzt'),
          5: ('D', 'muere', 'explosion', 'DefDead'), 4: ('A', 'muere', 'explosion', 'AttDead'),
          8: ('D', 'muere', 'flechas', 'arrows'), 9: ('A', 'muere', 'flechas', 'arrows'),
          0xa: ('D', 'muere', 'daga', 'aagh'), 0xb: ('A', 'muere', 'daga', 'aagh'),
          0xc: ('D', 'muere', 'relampago', 'zzzt'), 0xf: ('A', 'muere', 'relampago', 'zzzt'),
          0xe: ('D', 'muere', 'roca', 'DefDead'), 0x11: ('A', 'muere', 'roca', 'AttDead'),
          0x1c: ('D', 'muere', 'acido', 'zzzt'), 0x1d: ('A', 'muere', 'acido', 'zzzt'),
          0x14: ('D', 'muere', 'calavera', 'Slayer'), 0x15: ('A', 'muere', 'calavera', 'Slayer')}
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
        sets = os.path.join(juego, 'SETS', SET)
        self.fx = {**_indice(sets), **_indice(os.path.join(juego, 'FX'))}   # AAGH y ARROWS están en el set
        f = self.f = ESCALA.get(tamano, 1.0); z = self.z
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
        if picts is not None:      # al doble, como la tropa del duelo
            for k, (x0, y, w, h, n) in ANIM.items():
                self.tiras[k] = [ImageTk.PhotoImage(picts.crop((x0 + i * w, y, x0 + i * w + w, y + h)).resize((z(2 * w), z(2 * h)), Image.NEAREST))
                                 for i in range(n)]
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
                nv = max(1, ficha['vidas']); pw = min(z(9), (s - (nv - 1)) // nv)
                pips = [self.c.create_oval(x + i * (pw + 1), y + s + 1, x + i * (pw + 1) + pw, y + s + 1 + pw,
                                           fill=VIVA, outline='#000000') for i in range(ficha['vidas'])]
                self.u[lado].append(dict(x=x, y=y, marco=marco, pips=pips, vidas=ficha['vidas'], muerto=False, ficha=ficha,
                                         fuerza=ficha.get('fuerza_c', 2),
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
        self.vidas_duelo(lado)

    def vidas_duelo(self, lado):
        """Puntos grandes de vida debajo de la tropa que pelea: verdes las que le quedan, rojos las perdidas."""
        self.c.delete('vd' + lado)
        k = self.na if lado == 'A' else self.nd
        if k >= len(self.u[lado]) or self.terminado: return
        d = self.u[lado][k]; x, y = self.duelo[lado]; z = self.z
        n = d['ficha']['vidas']; t = z(14); x0 = x + z(48) - (n * (t + z(4)) - z(4)) / 2
        for i in range(n):
            xi = x0 + i * (t + z(4))
            self.c.create_oval(xi, y + z(102), xi + t, y + z(102) + t, fill=VIVA if i < d['vidas'] else (MUERTA if d['muerto'] else PERDIDA),
                               outline='#000000', width=2, tags=('vd' + lado, 'duelo'))

    def animar(self, tira, lado):
        cuadros = self.tiras.get(tira)
        if not self.efectos or self.rapido or not cuadros: return
        x, y = self.duelo[lado]; t = max(20, self.paso_ms // (len(cuadros) + 2))
        it = self.c.create_image(x + self.z(48), y + self.z(48), image=cuadros[0], anchor='center')
        def sig(i):
            if not self.winfo_exists(): return
            if i >= len(cuadros): self.c.delete(it); return
            self.c.itemconfigure(it, image=cuadros[i]); self.after(t, lambda: sig(i + 1))
        sig(1)

    # ---- sonido ----
    def sonar(self, nombre):
        if not (self.sonido_si and winsound) or self.rapido: return
        p = self.fx.get(nombre.lower() + '.wav')
        if p: self.sonar_ruta(p)

    def sonar_ruta(self, p):
        if not (self.sonido_si and winsound) or self.rapido: return
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
        for p in d['pips']: self.c.itemconfigure(p, fill=MUERTA)
        self.vidas_duelo(lado)

    def peleando(self, lado):
        """La tropa de ese lado que está peleando ahora, o None."""
        k = self.na if lado == 'A' else self.nd
        return self.u[lado][k] if k < len(self.u[lado]) else None

    def quitar_vidas(self, d, nuevas):
        d['vidas'] = max(0, nuevas)
        for i, p in enumerate(d['pips']): self.c.itemconfigure(p, fill=VIVA if i < d['vidas'] else PERDIDA)

    def elegir(self):
        """El próximo evento a mostrar, con los reemplazos de 0x405cd0; None si no quedan. Se muestran todos los golpes
        (cada uno con sus chispas y su sonido: así se ve en el juego, según el usuario, 6/11/2026); el marcador de
        Trample (0xe/0x11) no se muestra solo: pasa a ser la muerte que le sigue; Lightning o Acid sobre una tropa que
        ya no aguanta reemplazan a su muerte."""
        ev = self.ev
        while self.i < len(ev):
            c = ev[self.i]
            if c in (0xe, 0x11):
                if self.i + 1 < len(ev) and ev[self.i + 1] == (5 if c == 0xe else 4): self.i += 1; ev[self.i] = c; return c
                self.i += 1; continue
            dA, dD = self.peleando('A'), self.peleando('D')
            vA, vD = (dA['vidas'] if dA else 0), (dD['vidas'] if dD else 0)
            if c == 0xc and vD <= 1 and self.i + 1 < len(ev): self.i += 1; ev[self.i] = 0xc
            elif c == 0xf and vA <= 1 and self.i + 1 < len(ev): self.i += 1; ev[self.i] = 0xf
            c = ev[self.i]
            if c == 0xd and dD and dD['fuerza'] <= 1 and self.i + 1 < len(ev): self.i += 1; ev[self.i] = 0x1c
            elif c == 0x10 and dA and dA['fuerza'] <= 1 and self.i + 1 < len(ev): self.i += 1; ev[self.i] = 0x1d
            return self.cambiar(ev[self.i])
        return None

    def cambiar(self, c):
        """Conversiones de 0x406ed0: Lightning que no mata = vidas a la mitad; Acid sobre fuerza 1 = muerte."""
        dA, dD = self.peleando('A'), self.peleando('D')
        if c == 0xc and dD and dD['vidas'] > 1: return 0x13
        if c == 0xf and dA and dA['vidas'] > 1: return 0x12
        if c == 0xd and dD and dD['fuerza'] <= 1: return 0x1c
        if c == 0x10 and dA and dA['fuerza'] <= 1: return 0x1d
        return c

    def mostrar(self, c):
        """Un evento con su animación y su sonido del juego (0x406ed0)."""
        lado, que, anim, son = EVENTO[c]
        d = self.peleando(lado)
        if d is None: return
        if que == 'mitad': self.quitar_vidas(d, d['vidas'] // 2)
        elif que == 'fuerza': d['fuerza'] //= 2
        elif isinstance(que, int):     # un golpe de 2-4 vidas: tantas chispas seguidas, cada una con su sonido
            for k in range(que):
                self.after(k * self.paso_ms // que, lambda: self.winfo_exists() and (self.animar(anim, lado), self.sonar(son)))
            self.quitar_vidas(d, d['vidas'] - que); self.vidas_duelo(lado); return
        self.vidas_duelo(lado)
        self.animar(anim, lado); self.sonar(son)

    def decir(self, t):
        self.c.itemconfigure(self.leyenda, text=t)
        if self.leyenda_s: self.c.delete(self.leyenda_s)
        self.leyenda_s = self.c.create_text(self.z(312) + 2, self.z(395) + 2, text=t, fill=SOMBRA, font=self.f_tit, width=self.z(340))
        self.c.tag_raise(self.leyenda)

    # ---- repetición de eventos ----
    def paso(self):
        self.tarea = None
        c = self.elegir()
        if c is None: self.fin(); return
        self.i += 1
        if c == 2:
            if self.ea: self.matar('A', self.na); self.na += 1
            self.ea = True; self.activa('A', self.na)
        elif c == 3:
            if self.ed: self.matar('D', self.nd); self.nd += 1
            self.ed = True; self.activa('D', self.nd)
        elif c == 6: self.matar('D', self.nd); self.fin(); return
        elif c == 7: self.matar('A', self.na); self.fin(); return
        elif c in EVENTO: self.mostrar(c)   # las muertes se marcan por la estructura (motor.muertes); otro código:
                                            # 0x406ed0 no lo muestra
        if self.rapido: self.paso()
        else: self.tarea = self.after(self.paso_ms, self.paso)

    def saltar(self):
        if self.tarea: self.after_cancel(self.tarea); self.tarea = None
        self.rapido = True; self.paso()

    def fin(self):
        self.rapido = False; self.terminado = True; self.bsaltar.configure(state='disabled')
        self.c.delete('vdA'); self.c.delete('vdD')
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
