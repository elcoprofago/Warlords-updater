# Prueba de la etapa 2, ítems, de PENDIENTE-simulador-combate.md.
# Uso: python prueba_items.py [DarklordAV.exe] [partida.SAV]   (por defecto C:\Warlords3 y SAVES\Tanda_Kor.SAV)
# 1. Los ítems de la partida están donde dice motor.ITEM0: 0x409fb0 del juego cuenta +3 Gold per City en Grak.
# 2. Un ítem dado con Motor.dar_item lo cuenta el juego igual.
# 3. En batalla: cada ítem con una habilidad de combate cambia el % del héroe solo; control: el mismo ítem en el suelo
#    (estado 3) da lo mismo que sin ítem.
import os, sys
from motor import Motor, ITEM0, IREC
from datos import items, HABILIDADES
EXE = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe'
SAV = sys.argv[2] if len(sys.argv) > 2 else r'C:\Warlords3\SAVES\Tanda_Kor.SAV'
mal = 0
def ver(c, msg):
    global mal; mal += not c; print('OK  ' if c else 'MAL ', msg)

m = Motor(EXE, SAV)
grak = next(d for d in m.unidades() if d['tipo'] == 16 and d['activa'] and d['dueno'] == 3)
ver(m.item_suma(grak['u'], 11) == 3, f"Grak: Gold per City en sus ítems = {m.item_suma(grak['u'], 11)} (Ring of Grak +3)")

its = items(os.path.join(os.path.dirname(EXE), 'ITEMS'))
AX, AY, DX, DY = 50, 40, 51, 40; N = 10000
def pct(item=None, estado=1):
    m.limpiar(); m.vaciar((AX, AY), (DX, DY))
    at = m.poner(0, [1] * 3, AX, AY, 200); h = m.poner_heroe(0, 1, 1, [], AX, AY, 200)
    if item:
        i = m.dar_item(h, item.registro)
        if estado != 1: a = ITEM0 + i * IREC + 0xb0; b = m.mu.mem_read(a, 1)[0]; m.mu.mem_write(a, bytes([b & ~3 | estado]))
    m.poner(1, [1] * 3, DX, DY, 201)
    return 100 * m.probabilidad_motor(0, at + [h], DX, DY, 12345, N) / N

m.limpiar(); h = m.poner_heroe(0, 1, 1, [], AX, AY, 200)
ej = next(t for t in its if t.habilidades and t.habilidades[0][0] not in (13, 16) and t.habilidades[0][1] > 0)
m.dar_item(h, ej.registro); a, v = ej.habilidades[0]
ver(m.item_suma(h, a) == v, f'{ej.nombre}: el juego cuenta {HABILIDADES.get(a)} {m.item_suma(h, a)} (archivo +{v})')

base = pct(); print(f'     héroe solo: {base:.2f} %')
vistos = set(); cambian = 0
for t in its:
    if not t.habilidades or t.habilidades[0][0] in vistos: continue
    vistos.add(t.habilidades[0][0]); p = pct(t)
    cambian += p != base
    print(f"     {t.nombre:32} {t.texto():40} {p:6.2f} %{'' if p != base else '   (igual)'}")
ver(cambian > 0, f'{cambian} de {len(vistos)} habilidades cambian el combate')
fuerte = next(t for t in its if t.habilidades and t.habilidades[0][0] == 1)   # Leadership
ver(pct(fuerte, 3) == base, f'control: {fuerte.nombre} en el suelo da {pct(fuerte, 3):.2f} % = héroe solo')
print('RESULTADO:', 'TODO OK' if not mal else f'{mal} FALLAS')
