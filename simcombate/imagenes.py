"""Imágenes del Historial: la ficha de un combate y la torta de formaciones ganadoras, para ver y exportar (PNG o JPG).
Sin dependencias nuevas: solo PIL, que el simulador ya usa."""
import os
from PIL import Image, ImageDraw, ImageFont

AZUL, ROJO, GRIS, NEGRO = '#0050d0', '#c01818', '#808080', '#000000'
COLORES = ('#4e79a7', '#f28e2b', '#59a14f', '#e15759', '#76b7b2', '#edc948', '#b07aa1', '#ff9da7',
           '#9c755f', '#bab0ac', '#2f6f3e', '#8c2d5c')

def fuente(negrita=False, tam=15):
    for n in (('arialbd.ttf' if negrita else 'arial.ttf'), ('segoeuib.ttf' if negrita else 'segoeui.ttf')):
        try: return ImageFont.truetype(os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts', n), tam)
        except OSError: pass
    return ImageFont.load_default()

def ganador(f):
    """('ATACANTE'|'DEFENSOR', % del ganador)."""
    return ('ATACANTE', f['pct']) if f['pct'] >= 50 else ('DEFENSOR', 100 - f['pct'])

def partes_ficha(f):
    """La ficha como trozos (texto, marcas): 't' negrita, 'A'/'D' color del bando, 'gris'. La usan la ventana y la imagen."""
    p = []; w = lambda s, *tag: p.append((s, tag))
    w(f"COMBATE N.º {f['numero']:06d}", 't'); w(f"   {f['fecha']}\n"); w(f"Campo: {f['campo']}\n\n")
    for L, nom in (('A', 'ATACANTE'), ('D', 'DEFENSOR')):
        c = f[L]; w(nom, 't', L); w('\n')
        for a, n in c['tropas']: w(f'  {n} × {a}\n')
        if c['barco']: w(f"  Barco: {c['barco']}\n")
        if c['heroe']: w(f"  Héroe: {c['heroe']}\n")
        if not c['tropas'] and not c['heroe']: w('  (nadie)\n')
        w('\n')
    g, pg = ganador(f); p_, pp = ('defensor', 100 - pg) if g == 'ATACANTE' else ('atacante', 100 - pg)
    w('RESULTADO: ', 't'); w(g, 't', g[0]); w(f' con {pg:.2f} %', 't')
    w(f"  ({p_} gana el {pp:.2f} % en {f['n']} peleas)\n\n", 'gris')
    for a in f['avisos']: w(f'\nAviso: {a}')
    return p

def imagen_ficha(f, version=''):
    partes = partes_ficha(f) + ([(f'\n\nSimulador de combate — VERSIÓN {version}', ('gris',))] if version else [])
    fn, fb = fuente(False, 16), fuente(True, 16); alto = 24
    lineas = [[]]
    for s, tag in partes:
        for i, trozo in enumerate(s.split('\n')):
            if i: lineas.append([])
            if trozo: lineas[-1].append((trozo, tag))
    medir = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    ancho = max([sum(medir.textlength(s, font=fb if 't' in tag else fn) for s, tag in ln) for ln in lineas] + [300])
    im = Image.new('RGB', (int(ancho) + 40, len(lineas) * alto + 36), 'white'); d = ImageDraw.Draw(im)
    for k, ln in enumerate(lineas):
        x = 20
        for s, tag in ln:
            fo = fb if 't' in tag else fn
            col = AZUL if 'A' in tag else ROJO if 'D' in tag else GRIS if 'gris' in tag else NEGRO
            d.text((x, 18 + k * alto), s, font=fo, fill=col); x += d.textlength(s, font=fo)
    return im

def nombre_formacion(c):
    s = ' + '.join(f'{n} {a}' for a, n in c['tropas']) or '(sin tropas)'
    if c['barco']: s += f" · barco {c['barco']}"
    if c['heroe']: s += f" · héroe {c['heroe']}"
    return s

def formaciones(h):
    """Formaciones ganadoras de los combates del historial: [(nombre, victorias, % medio de victoria)], la mejor primero
    (más victorias; a igualdad, mayor % medio)."""
    t = {}
    for f in h:
        g, pg = ganador(f); n = nombre_formacion(f[g[0]])
        v, s = t.get(n, (0, 0.0)); t[n] = (v + 1, s + pg)
    return sorted(((n, v, s / v) for n, (v, s) in t.items()), key=lambda x: (-x[1], -x[2]))

def imagen_torta(h, version=''):
    fo = formaciones(h); total = sum(v for _, v, _ in fo)
    ft, fn, fb = fuente(True, 20), fuente(False, 14), fuente(True, 14)
    medir = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    ley = [f'{v * 100 / total:.1f} %  ({v} de {total}, gana con {p:.1f} % de media)  {n}' for n, v, p in fo] if total else []
    ancho_ley = max([medir.textlength(s, font=fb) for s in ley] + [300])
    D = 340; alto = max(D + 150, 110 + len(ley) * 26 + 60)
    im = Image.new('RGB', (int(D + 90 + ancho_ley + 40), alto), 'white'); d = ImageDraw.Draw(im)
    d.text((20, 16), f'Mejor formación — {total} combates del Historial', font=ft, fill=NEGRO)
    if not total:
        d.text((20, 60), 'Todavía no hay combates guardados.', font=fn, fill=GRIS); return im
    d.text((20, 46), f'La mejor: {fo[0][0]}', font=fb, fill=AZUL)
    x0, y0, a = 30, 90, -90.0
    for k, (n, v, _) in enumerate(fo):
        b = a + 360 * v / total; col = COLORES[k % len(COLORES)]
        if len(fo) == 1: d.ellipse((x0, y0, x0 + D, y0 + D), fill=col, outline='white', width=2)
        else: d.pieslice((x0, y0, x0 + D, y0 + D), a, b, fill=col, outline='white', width=2)
        a = b
    lx = x0 + D + 50
    for k, s in enumerate(ley):
        y = y0 + k * 26; d.rectangle((lx, y + 2, lx + 16, y + 18), fill=COLORES[k % len(COLORES)])
        d.text((lx + 26, y), s, font=fb if k == 0 else fn, fill=NEGRO)
    d.text((20, alto - 30), 'Cuenta, en cada combate, la formación del bando que gana la mayoría de las peleas.'
           + (f'   Simulador de combate — VERSIÓN {version}' if version else ''), font=fn, fill=GRIS)
    return im

def guardar(im, ruta):
    """PNG o JPG según la extensión (JPG sin transparencia)."""
    if ruta.lower().endswith(('.jpg', '.jpeg')): im.convert('RGB').save(ruta, quality=95)
    else: im.save(ruta)
