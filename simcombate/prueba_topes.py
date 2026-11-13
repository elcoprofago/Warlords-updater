# Prueba de los topes de pila del simulador (escenario.Simulador.tope).
# Uso: python prueba_topes.py [carpeta del juego] [partida.SAV]   (por defecto C:\Warlords3 y SAVES\Tanda_Kor.SAV)
# Ciudad: el defensor entra con 32 (4 casillas de 8) y la ficha del juego los lleva a los 32; el atacante, 8.
# Barco "Landing": 5 (6 con "Carrier"); barco "Carrier" de defensor: convoy de 3 pilas (24). Campo abierto: 8.
# Controles: 9 en campo abierto se rechaza; 33 en la ciudad se rechaza; más defensores en la ciudad bajan el %.
import os, sys, struct
from escenario import Simulador, Error
J = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3'
S = Simulador(J, sys.argv[2] if len(sys.argv) > 2 else os.path.join(J, 'SAVES', 'Tanda_Kor.SAV'))
mal = 0
def ver(c, msg):
    global mal; mal += not c; print('OK  ' if c else 'MAL ', msg)
lado = lambda n, barco=None: {'tropas': [('gnollcav.arm', n)] + [(None, 0)] * 7, 'barco': barco}
tierra = next(t for t in S.terrenos if not S.es_agua(t)); agua = next(t for t in S.terrenos if S.es_agua(t))
def esc(na, nd, est=0, ter=tierra, ba=None, bd=None):
    return {'A': lado(na, ba), 'D': lado(nd, bd), 'campo': {'terreno': ter, 'estructura': est}}
def rechaza(e):
    try: S.armar(e); return False
    except Error: return True
def en_ficha(e):
    at, (dx, dy), _ = S.armar(e); f = S.m.batalla(0, at, dx, dy, 1)['ficha']
    return next((k for k in range(32) if struct.unpack_from('<h', f, 0x12e + k * 0x24)[0] <= 0), 32)
ver(rechaza(esc(8, 9)), 'campo abierto: 9 defensores se rechazan')
ver(rechaza(esc(9, 8, 3)), 'ciudad: 9 atacantes se rechazan')
ver(rechaza(esc(8, 33, 3)), 'ciudad: 33 defensores se rechazan')
for n in (8, 9, 17, 32): ver(en_ficha(esc(8, n, 3)) == n, f'ciudad: {n} defensores, {n} en la ficha del juego')
p = [S.simular(esc(8, n, 3), 400)['pct'] for n in (4, 8, 16)]
ver(p[0] > p[1] > p[2] or p[2] == 0, f'ciudad: más defensores, menos % del atacante {p}')
bon = lambda b: {x.lower() for x in b.bonos_mov}
for k, b in sorted(S.barcos.items()):
    t, mot = S.tope('D', {'barco': k}, {'terreno': agua, 'estructura': 0})
    ta, _ = S.tope('A', {'barco': k}, {'terreno': agua, 'estructura': 0})
    pila = (6 if 'carrier' in bon(b) else 5) if 'landing' in bon(b) else 8
    ok = ta == pila and t == (3 * pila if 'carrier' in bon(b) else pila)
    ver(ok, f'{k:13} {sorted(bon(b))}: atacante {ta}, defensor {t} ({mot})')
ver(S.tope('D', {'barco': next(iter(S.barcos))}, {'terreno': tierra, 'estructura': 0})[0] == 8, 'control: barco en tierra, 8')
print('RESULTADO:', 'TODO OK' if not mal else f'{mal} FALLAS')
