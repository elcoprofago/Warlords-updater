# Prueba del escenario (etapa 3 de PENDIENTE-simulador-combate.md): lo que arma el tablero da lo mismo que las pruebas
# de las etapas 1 y 2, la grilla manda el orden de pelea, y la noche cambia la pelea solo a monster/demon/undead.
# Uso: python prueba_escenario.py [carpeta del juego] [partida.SAV]   (por defecto C:\Warlords3 y SAVES\Tanda_Kor.SAV)
import os, sys
from escenario import Simulador, Error
JUEGO = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3'
SAV = sys.argv[2] if len(sys.argv) > 2 else os.path.join(JUEGO, 'SAVES', 'Tanda_Kor.SAV')
s = Simulador(JUEGO, SAV); N = 10000
mal = 0
def ver(c, msg):
    global mal; mal += not c; print('OK  ' if c else 'MAL ', msg)
def lado(*tropas, heroe=None, barco=None):
    t = list(tropas) + [(None, 0)] * (8 - len(tropas)); return dict(tropas=t, heroe=heroe, barco=barco)
def esc(a, d, **campo):
    c = dict(terreno='plains', estructura=0, bosque=False, noche=False, defensas=1); c.update(campo)
    return {'A': a, 'D': d, 'campo': c}
G3 = lado(('gnollcav.arm', 3))

# 1. Ciudad y defensas: los mismos % de prueba_motor.py 2c (ciudad 0 del defensor, 3 contra 3 gnollcav)
esp = {1: 38.99, 2: 30.17, 3: 21.64}
for k, v in esp.items():
    r = s.simular(esc(G3, G3, estructura=3, defensas=k), N)
    ver(abs(r['pct'] - v) < 0.005, f'ciudad con defensas {k}: {r["pct"]:.2f} % (prueba_motor: {v} %)')
base = s.simular(esc(G3, G3), N)['pct']; print(f'campo abierto (plains): {base:.2f} %')

# 2. La grilla manda el orden de pelea, de los dos lados
for t in ((('moongard.arm', 1), ('gnollcav.arm', 1), ('Zappers.arm', 1)),
          (('Zappers.arm', 1), ('moongard.arm', 1), ('gnollcav.arm', 1))):
    r = s.simular(esc(lado(*t), lado(*t)), 10)
    q = [a.split('.')[0].lower() for a, _ in t]
    ver([x.lower() for x in r['orden_a']] == q and [x.lower() for x in r['orden_d']] == q,
        f'orden {q}: atacante {r["orden_a"]}, defensor {r["orden_d"]}')

# 3. Noche: archons (monster) cambia; gnollcav no (control)
dia = s.simular(esc(lado(('archons.arm', 3)), G3), N)['pct']; noche = s.simular(esc(lado(('archons.arm', 3)), G3, noche=True), N)['pct']
ver(noche != dia, f'archons: de día {dia:.2f} %, de noche {noche:.2f} %')
n2 = s.simular(esc(G3, G3, noche=True), N)['pct']
ver(n2 == base, f'control, gnollcav de noche: {n2:.2f} % (de día {base:.2f} %)')

# 4. Héroe con ítem y hechizo sube el %; elecciones de más se rechazan
h = dict(clase='KBARBAR.HER', nivel=1, elecciones=[], items=[], hechizos=[])
c = [k for k in s.clases if 'barb' in k]; h['clase'] = c[0]
con = s.simular(esc(lado(('gnollcav.arm', 3), heroe=h), G3), N)['pct']
ver(con > base, f'héroe {c[0]} nivel 1: {con:.2f} % (sin héroe {base:.2f} %)')
try: s.simular(esc(lado(('gnollcav.arm', 3), heroe=dict(h, elecciones=[0] * 30)), G3), 10); ver(False, 'elecciones de más aceptadas')
except Error as e: ver(True, f'elecciones de más: {e}')
try: s.simular(esc(lado(('gnollcav.arm', 8), heroe=h), G3), 10); ver(False, '9 unidades aceptadas')
except Error as e: ver(True, f'pila de 9: {e}')

# 5. Agua: sin barco, error; con barco, pelea (con barco y en puente)
agua = next(t for t in s.terrenos if s.es_agua(t))
try: s.simular(esc(G3, G3, terreno=agua), 10); ver(False, 'agua sin barco aceptada')
except Error as e: ver(True, f'agua sin barco: {e}')
b = next(iter(s.barcos))
r = s.simular(esc(lado(('gnollcav.arm', 3), barco=b), lado(('gnollcav.arm', 3), barco=b), terreno=agua), N)
ver(0 < r['pct'] < 100, f'agua con {b}: {r["pct"]:.2f} %')
r = s.simular(esc(G3, G3, terreno=agua, estructura=1), N)
ver(0 < r['pct'] < 100, f'puente sin barco: {r["pct"]:.2f} %')
# 6. Secuencia: en 300 semillas, con asesinos (gnollcav, Assassin +4) y sin ellos, gana quien no perdió todas sus unidades
from motor import muertes
ok = 0
for t in ('gnollcav.arm', 'moongard.arm', 'archons.arm', 'elephant.arm', 'Zappers.arm'):
    L = lado((t, 3)); s.armar(esc(L, L)); at = s.ids['A']
    for sem in range(300):
        r = s.m.batalla(0, at, 51, 40, sem); mu = muertes(r['eventos'])
        ok += r['gana'] == (sum(1 for l, _ in mu if l == 'D') == 3) and r['gana'] != (sum(1 for l, _ in mu if l == 'A') == 3)
ver(ok == 1500, f'secuencia de muertes coherente con el ganador en {ok} de 1500 batallas')
print("muestra:", [muertes(r["eventos"])], "gana", "A" if r["gana"] else "D")
# 7. Edificios del defensor (vista-aliada): faro, torre y muralla lo ayudan, la muralla más; el muro rechaza agua
#    y la torre una ciudad. Control: sin obra, el mismo % que antes.
G1 = lado(('gnollcav.arm', 3))
po = {o: s.simular(esc(G1, G1, obra=o), N)['pct'] for o in (None, 'faro', 'torre', 'muro')}
print('obras:', po)
ver(po[None] == base, f'sin obra: {po[None]:.2f} % (campo abierto {base:.2f} %)')
ver(po['faro'] < base and po['torre'] < base, f'faro {po["faro"]:.2f} %, torre {po["torre"]:.2f} % < {base:.2f} %')
ver(po['muro'] < min(po['faro'], po['torre']), f'muralla {po["muro"]:.2f} % < faro y torre')
for kw, que in ((dict(obra='torre', estructura=3), 'torre en ciudad'), (dict(obra='muro', terreno=agua, estructura=1), 'muro en agua')):
    try: s.simular(esc(G1, G1, **kw), 10); ver(False, f'{que} aceptado')
    except Error as e: ver(True, f'{que}: {e}')
r = s.simular(esc(G1, G1, estructura=3, defensas=2, obra='muro'), N)['pct']
ver(r < esp[2], f'ciudad nivel 2 con muralla al lado: {r:.2f} % < {esp[2]} %')
print('RESULTADO:', 'TODO OK' if not mal else f'{mal} FALLAS')
