# Prueba de la etapa 2, héroes, de PENDIENTE-simulador-combate.md.
# Uso: python prueba_heroes.py [DarklordAV.exe] [partida.SAV]   (por defecto C:\Warlords3 y SAVES\Tanda_Kor.SAV)
# 1. Las clases que la partida tiene cargadas son copia exacta de su .HER.
# 2. Un héroe nuevo de nivel 1 tiene la fuerza, vidas y movimiento de su clase; cada elección la aplica la rutina del
#    juego (0x48efa0) y cambia lo que dice el .HER; no se puede gastar más puntos que los del nivel.
# 3. Un héroe sintético pelea igual que un héroe real de la partida con el mismo registro (misma batalla, misma semilla).
# 4. En batalla: sumar un héroe al atacante sube su %; un héroe más fuerte lo sube más (control).
import os, sys, glob, struct
from motor import Motor, CLASE0, CLREC, HEROE0, HREC, UNIT0, UREC
from datos import HABILIDADES
EXE = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe'
SAV = sys.argv[2] if len(sys.argv) > 2 else r'C:\Warlords3\SAVES\Tanda_Kor.SAV'
HERO = os.path.join(os.path.dirname(EXE), 'HERO')
mal = 0
def ver(c, msg):
    global mal; mal += not c; print('OK  ' if c else 'MAL ', msg)

m = Motor(EXE, SAV)
her = {os.path.basename(f).lower(): open(f, 'rb').read() for f in glob.glob(os.path.join(HERO, '*.her'))}
iguales = 0
for k in range(32):
    r = bytes(m.mu.mem_read(CLASE0 + k * CLREC, CLREC))
    iguales += any(r == b[:CLREC] for b in her.values())
ver(iguales == 32, f'{iguales} de 32 clases en memoria son copia exacta de un .HER de {HERO} ({len(her)} archivos)')

# 2. Héroe nuevo y elecciones
AX, AY, DX, DY = 50, 40, 51, 40
for ranura in range(4):
    c = m.clase(0, ranura); m.limpiar()
    u = m.poner_heroe(0, ranura, 1, [], AX, AY, 200); h = m.heroe(u)
    ver((h['fuerza'], h['vidas'], h['mov'], h['nivel']) == (c['fuerza'], c['vidas'], c['mov'], 1),
        f"{c['nombre']} nivel 1: F{h['fuerza']} V{h['vidas']} M{h['mov']} (clase F{c['fuerza']} V{c['vidas']} M{c['mov']}),"
        f" puntos por nivel {c['puntos']}")
    for i, e in enumerate(c['elecciones']):
        if not e['hab'] or e['costo'] > m.puntos_nivel(0, ranura, 10): continue
        m.limpiar(); nivel = next(n for n in range(1, 11) if m.puntos_nivel(0, ranura, n) >= e['costo'])
        u = m.poner_heroe(0, ranura, nivel, [i], AX, AY, 200); h = m.heroe(u)
        nom = HABILIDADES.get(e['hab'], e['hab']); esperado = ok = None
        if e['hab'] == 8: ok = h['fuerza'] == c['fuerza'] + e['valor']
        elif e['hab'] == 14: ok = h['vidas'] == c['vidas'] + e['valor']
        elif e['hab'] == 7: ok = h['mov'] == c['mov'] + e['valor']
        elif e['hab'] == 23: ok = h['vista'] == min(7, c['vista'] + e['valor'])
        elif e['hab'] == 20: ok = (20, 0) in h['casilleros']
        elif e['hab'] in (9, 10, 13): continue                    # banderas del registro o del bando, no casilleros
        else: ok = any(a == e['hab'] for a, _ in h['casilleros'])
        ver(ok, f"   elección {i} {nom} {e['hechizo'] or '+' + str(e['valor'])} (costo {e['costo']}, nivel {nivel}):"
                f" F{h['fuerza']} V{h['vidas']} M{h['mov']} casilleros {h['casilleros']}")
m.limpiar()
try: m.poner_heroe(0, 1, 10, [0] * 4, AX, AY, 200); ver(False, 'fuerza 18 tendría que fallar')
except ValueError as e: ver(True, f'KBarbarian con 4 veces Strength +3: {e}')
try: m.poner_heroe(0, 1, 1, [0], AX, AY, 200); ver(False, 'gastar puntos en nivel 1 tendría que fallar')
except ValueError as e: ver(True, f'nivel 1 sin puntos: {e}')

# 3. Héroe real de la partida contra su copia sintética
N = 10000
def pct(at_fn, td=1):
    m.limpiar(); m.vaciar((AX, AY), (DX, DY))
    at = at_fn(); m.poner(1, [td] * 3, DX, DY, 201)
    return 100 * m.probabilidad_motor(0, at, DX, DY, 12345, N) / N
real = next(d for d in m.unidades() if d['tipo'] == 16 and d['activa'] and d['dueno'] == 3)   # Grak
hr = (struct.unpack_from('<H', real['raw'], 0x10)[0] >> 8) & 63
def con_real():
    a = UNIT0 + real['u'] * UREC; r = bytearray(real['raw'])
    struct.pack_into('<hh', r, 0, AX, AY); struct.pack_into('<H', r, 8, 200 << 8 & 0xffff); struct.pack_into('<H', r, 0x14, 200)
    w = struct.unpack_from('<H', r, 0xc)[0]; struct.pack_into('<H', r, 0xc, (w & ~0x1e0) | 0 << 5)   # pasa al bando 0
    m.mu.mem_write(a, bytes(r)); return m.poner(0, [1] * 3, AX, AY, 200) + [real['u']]
def con_copia():
    u = m.poner_heroe(0, 0, 1, [], AX, AY, 200); h = m.heroe(u)['h']
    m.mu.mem_write(HEROE0 + h * HREC, bytes(m.mu.mem_read(HEROE0 + hr * HREC, HREC)))
    r = bytearray(m.mu.mem_read(UNIT0 + u * UREC, UREC)); w = struct.unpack_from('<H', real['raw'], 0xc)[0]
    struct.pack_into('<H', r, 0xc, (w & ~0x1e0)); m.mu.mem_write(UNIT0 + u * UREC, bytes(r))
    return m.poner(0, [1] * 3, AX, AY, 200) + [u]
p1, p2 = pct(con_real), pct(con_copia)
ver(p1 == p2, f'Grak real {p1:.2f} %, Grak sintético {p2:.2f} %')

# 4. Efecto en batalla
base = pct(lambda: m.poner(0, [1] * 3, AX, AY, 200))
c = m.clase(0, 1)
debil = pct(lambda: m.poner(0, [1] * 3, AX, AY, 200) + [m.poner_heroe(0, 1, 1, [], AX, AY, 200)])
fuertes = [i for i, e in enumerate(c['elecciones']) if e['hab'] == 8]
el = []
for i in fuertes * 5:
    if (sum(c['elecciones'][j]['costo'] for j in el + [i]) <= m.puntos_nivel(0, 1, 10)
            and c['fuerza'] + sum(c['elecciones'][j]['valor'] for j in el + [i]) <= 15): el.append(i)
fuerte = pct(lambda: m.poner(0, [1] * 3, AX, AY, 200) + [m.poner_heroe(0, 1, 10, el, AX, AY, 200)])
m.limpiar(); hf = m.heroe(m.poner_heroe(0, 1, 10, el, AX, AY, 200))
ver(debil > base, f"3 gnollcav {base:.2f} %; con un {c['nombre']} de nivel 1 {debil:.2f} %")
ver(fuerte > debil, f"control, con un {c['nombre']} de nivel 10 y F{hf['fuerza']} V{hf['vidas']} (elecciones {el}): {fuerte:.2f} %")
print('RESULTADO:', 'TODO OK' if not mal else f'{mal} FALLAS')
