# Prueba de la ventana de combate (etapa 4 de PENDIENTE-simulador-combate.md): hay ícono para cada arma, barco y
# clase de héroe; la repetición de la ventana tacha las mismas unidades, en el mismo orden, que motor.muertes; y
# deja con vida exactamente a las del lado ganador que no cayeron.
# Uso: python prueba_combate.py [carpeta del juego] [partida.SAV]   (por defecto C:\Warlords3 y SAVES\Tanda_Kor.SAV)
import os, sys, random
import tkinter as tk
from escenario import Simulador
from combate import VentanaCombate, icono
JUEGO = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3'
SAV = sys.argv[2] if len(sys.argv) > 2 else os.path.join(JUEGO, 'SAVES', 'Tanda_Kor.SAV')
s = Simulador(JUEGO, SAV); mal = 0
def ver(c, msg):
    global mal; mal += not c; print('OK  ' if c else 'MAL ', msg)

# 1. Íconos
sin = [a.archivo for a in list(s.armas.values()) + list(s.barcos.values())
       if icono(os.path.join(JUEGO, 'ARMY', a.archivo), 48) is None]
ver(not sin, f'ícono de {len(s.armas) + len(s.barcos) - len(sin)} de {len(s.armas) + len(s.barcos)} armas y barcos {sin[:10]}')
sinc = [os.path.basename(c.ruta) for c in s.clases.values() if icono(os.path.join(JUEGO, 'HERO', c.imagen), 48) is None]
ver(not sinc, f'ícono de {len(s.clases) - len(sinc)} de {len(s.clases)} clases {sinc}')
im = icono(os.path.join(JUEGO, 'ARMY', 'gnollcav'), 48)
ver(im.getpixel((0, 0))[3] == 0 and im.getchannel('A').getextrema()[1] == 255, 'gnollcav: fondo transparente y figura visible')

# 2. Repetición = motor, en batallas al azar (con héroe y pilas mezcladas)
root = tk.Tk(); root.withdraw()
armas = sorted(s.armas); rnd = random.Random(7); n = 0; bien = 0
for j in range(150):
    def lado():
        k = rnd.randint(1, 4); t = [(rnd.choice(armas), rnd.randint(1, 2)) for _ in range(k)] + [(None, 0)] * (8 - k)
        h = {'clase': 'kbarbar.her', 'nivel': rnd.randint(1, 10)} if rnd.random() < 0.3 else None
        return dict(tropas=t, heroe=h, barco=None)
    esc = {'A': lado(), 'D': lado(), 'campo': dict(terreno='plains', estructura=0, bosque=False, noche=False, defensas=1)}
    try: r = s.simular(esc, 1, semilla=j)
    except Exception: continue
    v = VentanaCombate(root, JUEGO, r, 'prueba', sonido=False); v.saltar(); n += 1
    vivos_g = [k for k in range(len(r['fichas_a' if r['gana'] else 'fichas_d']))
               if not v.u['A' if r['gana'] else 'D'][k]['muerto']]
    perd = v.u['D' if r['gana'] else 'A']
    if v.muertes == [tuple(m) for m in r['muertes']] and vivos_g and all(d['muerto'] for d in perd): bien += 1
    v.cerrar()
ver(n >= 100 and bien == n, f'repetición igual al motor en {bien} de {n} batallas (ganador con vivos, perdedor sin vivos)')

# 3. Cada poder muestra la animación que le da la ventana del juego (0x406ed0) y nada más (Lightning contra tropas
#    de más de una vida: el relámpago corto, que les parte las vidas a la mitad)
def anims(a, d):
    def lado(*t): return dict(tropas=list(t) + [(None, 0)] * (8 - len(t)), heroe=None, barco=None)
    r = s.simular({'A': lado(*a), 'D': lado(*d), 'campo': dict(terreno='plains', estructura=0, bosque=False, noche=False,
                                                                defensas=1)}, 1)
    v = VentanaCombate(root, JUEGO, r, 'prueba', sonido=False); vistas = set()
    v.animar = lambda tira, l: vistas.add(tira); v.saltar(); v.cerrar(); return vistas
for a, d, debe, no in (([('elephant.arm', 3)], [('gnolls.arm', 3)], 'roca', 'explosion'),
                       ([('assassin.arm', 3)], [('gnolls.arm', 3)], 'daga', None),
                       ([('moongard.arm', 3)], [('bats.arm', 3)], 'flechas', None),
                       ([('budragon.arm', 2)], [('gnolls.arm', 4)], 'relampago_corto', None),
                       ([('fu_fire.arm', 3)], [('gnolls.arm', 4)], 'acido', None),
                       ([('firedrag.arm', 1)], [('rddragon.arm', 1)], 'calavera', None),
                       ([('gnolls.arm', 3)], [('gnolls.arm', 3)], 'explosion', 'calavera')):
    try: vistas = anims(a, d)
    except Exception as e: ver(False, f'{a[0][0]}: {e}'); continue
    ver(debe in vistas and (no is None or no not in vistas), f'{a[0][0]} contra {d[0][0]}: {sorted(vistas)}')
root.destroy()
print('TODO OK' if not mal else f'{mal} MAL')
