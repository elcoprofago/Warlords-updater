# Prueba del terreno (etapa 2 de PENDIENTE-simulador-combate.md).
# Uso: python prueba_terreno.py [DarklordAV.exe] [partida.SAV]   (por defecto C:\Warlords3 y SAVES\Tanda_Kor.SAV)
# 3 armas con bono de combate contra 3 gnollcav, 10 000 peleas por caso: el % tiene que subir solo en el terreno de su
# bono (en la casilla del defensor, o en la del atacante si el juego mira esa) y quedar igual en los demás (control).
import os, sys
from motor import Motor
from datos import armas
EXE = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe'
SAV = sys.argv[2] if len(sys.argv) > 2 else r'C:\Warlords3\SAVES\Tanda_Kor.SAV'
A = [a for a in armas(os.path.join(os.path.dirname(EXE), 'ARMY')) if not a.barco]
m = Motor(EXE, SAV); N = 10000; AX, AY, DX, DY = 50, 40, 51, 40
mal = 0
def ver(c, msg):
    global mal; mal += not c; print('OK  ' if c else 'MAL ', msg)
T = {n: t for t, n in reversed(list(m.terrenos().items()))}   # nombre -> primer índice
print('terrenos:', m.terrenos())
CASOS = {'llanura': dict(terreno=T['plains']), 'colinas': dict(terreno=T['hills']), 'pantano': dict(terreno=T['marsh']),
         'desierto': dict(terreno=T['desert']), 'hielo': dict(terreno=T['ice']), 'terreno forest': dict(terreno=T['forest']),
         'bosque (capa)': dict(terreno=T['plains'], bosque=True), 'camino': dict(terreno=T['plains'], estructura=1)}
def pct(arma, donde, lado):
    m.limpiar(); m.vaciar((AX, AY), (DX, DY))
    for x, y in ((AX, AY), (DX, DY)): m.poner_terreno(x, y, T['plains'], 0, False)
    m.poner_terreno(*((DX, DY) if lado == 'D' else (AX, AY)), **CASOS[donde])
    m.cargar_arma(0, 12, arma.registro)
    at = m.poner(0, [12] * 3, AX, AY, 200); m.poner(1, [1] * 3, DX, DY, 201)
    return 100 * m.probabilidad_motor(0, at, DX, DY, 12345, N) / N
ESPERA = {'hills': {'colinas'}, 'marsh': {'pantano'}, 'desert': {'desierto'}, 'ice': {'hielo'},
          'woods': {'bosque (capa)'}, 'forest': {'bosque (capa)'}, 'plains': {'llanura', 'bosque (capa)', 'camino'},
          'field': {'llanura', 'colinas', 'pantano', 'desierto', 'hielo', 'terreno forest', 'camino'}}
ESPERA['open'] = ESPERA['field']
lados = {}
for nombre in ESPERA:
    a = next((a for a in A if a.bono_combate_nombre.lower() == nombre), None)
    if not a: print('     sin arma con bono', nombre); continue
    for lado in 'DA':
        r = {d: pct(a, d, lado) for d in CASOS}
        sube = {d for d in r if r[d] > min(r.values())}
        lados.setdefault(lado, []).append(bool(sube))
        if lado == 'A' and not sube: continue
        ver(sube == ESPERA[nombre], f'{a.archivo} ({nombre} +{a.bono_combate}), terreno del {lado}: sube en {sorted(sube)}  '
            + ', '.join(f'{d} {v:.2f}' for d, v in r.items()))
print('el juego mira la casilla del', ' y '.join(l for l, v in lados.items() if any(v)) or 'ninguno')
print('RESULTADO:', 'TODO OK' if not mal else f'{mal} FALLAS')
