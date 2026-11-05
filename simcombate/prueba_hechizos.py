# Prueba de la etapa 2, hechizos, de PENDIENTE-simulador-combate.md.
# Uso: python prueba_hechizos.py [DarklordAV.exe] [partida.SAV]   (por defecto C:\Warlords3 y SAVES\Tanda_Kor.SAV)
# 1. Todos los .SPL se lanzan con la rutina del juego (0x48f300) sin fallar.
# 2. 0x409e40 del juego cuenta lo que dice el .SPL, por 1 en nivel 1-5, 2 en 6-8 y 3 en 9-10.
# 3. En batalla: cada hechizo con efectos de combate cambia el % del héroe solo; control: el mismo hechizo lanzado
#    por un héroe de otra pila (que no pelea) da lo mismo que sin hechizo.
import os, sys
from motor import Motor
from datos import hechizos, HABILIDADES
EXE = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe'
SAV = sys.argv[2] if len(sys.argv) > 2 else r'C:\Warlords3\SAVES\Tanda_Kor.SAV'
mal = 0
def ver(c, msg):
    global mal; mal += not c; print('OK  ' if c else 'MAL ', msg)

m = Motor(EXE, SAV)
hs = hechizos(os.path.join(os.path.dirname(EXE), 'SPELL'))
fallan = []
for s in hs:
    m.limpiar(); h = m.poner_heroe(0, 1, 1, [], 50, 40, 200)
    try: m.lanzar(h, s.registro)
    except RuntimeError as e: fallan.append((s.nombre, str(e)))
ver(not fallan, f'{len(hs)} hechizos lanzados, {len(fallan)} fallan {fallan[:3]}')

bp = next(s for s in hs if s.efectos and s.efectos[0][0] == 38 and any(e[0] == 8 for e in s.efectos))
for nivel, k in ((1, 1), (5, 1), (6, 2), (8, 2), (9, 3), (10, 3)):
    m.limpiar(); h = m.poner_heroe(0, 1, nivel, [], 50, 40, 200); m.lanzar(h, bp.registro)
    cuenta = [m.hechizo_suma(h, a) for a, v in bp.efectos]
    ver(cuenta == [v * k for a, v in bp.efectos], f'{bp.nombre} nivel {nivel}: el juego cuenta {cuenta} (archivo {bp.texto()} ×{k})')

AX, AY, DX, DY, OX, OY = 50, 40, 51, 40, 30, 30; N = 10000
def pct(spl=None, otro=False):
    m.limpiar(); m.vaciar((AX, AY), (DX, DY), (OX, OY))
    at = m.poner(0, [1] * 3, AX, AY, 200); h = m.poner_heroe(0, 1, 1, [], AX, AY, 200)
    if spl:
        lanza = m.poner_heroe(0, 1, 1, [], OX, OY, 202) if otro else h
        m.lanzar(lanza, spl.registro)
    m.poner(1, [1] * 3, DX, DY, 201)
    return 100 * m.probabilidad_motor(0, at + [h], DX, DY, 12345, N) / N

base = pct(); print(f'     héroe solo: {base:.2f} %')
vistos = set(); cambian = 0
for s in hs:
    clave = tuple(sorted(a for a, v in s.efectos if a not in (13, 16, 22, 25, 29, 35, 36, 58, 59, 60)))
    if not clave or clave in vistos: continue
    vistos.add(clave); p = pct(s); cambian += p != base
    print(f"     {s.nombre:18} {s.texto():60} {p:6.2f} %{'' if p != base else '   (igual)'}")
ver(cambian > 0, f'{cambian} de {len(vistos)} combinaciones de efectos cambian el combate')
fuerte = next(s for s in hs if s.efectos and s.efectos[0][0] == 8 and s.efectos[0][1] >= 3)   # Strength +3
p = pct(fuerte); ver(p != base, f'{fuerte.nombre} en el héroe que pelea: {p:.2f} %')
p = pct(fuerte, True); ver(p == base, f'control: {fuerte.nombre} en un héroe de otra pila da {p:.2f} % = héroe solo')
print('RESULTADO:', 'TODO OK' if not mal else f'{mal} FALLAS')
