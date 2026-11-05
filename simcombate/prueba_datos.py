# Prueba de la etapa 2 (datos) de PENDIENTE-simulador-combate.md.
# Uso: python prueba_datos.py [DarklordAV.exe] [partida.SAV]   (por defecto C:\Warlords3 y SAVES\Tanda_Kor.SAV)
# 1. Todos los .ARM del ARMY se leen; los tipos que la partida ya tiene cargados coinciden campo a campo con su .ARM
#    (salvo los .ARM modificados después de grabarse la partida: la partida guarda su propia copia del tipo).
# 2. Un .ARM cargado en una ranura libre pelea igual que el mismo tipo ya cargado por el juego (control: un arma
#    más fuerte en esa ranura tiene que mover el %).
import os, sys, struct
from motor import Motor, TIPOS, TREC
from datos import armas, Arma
EXE = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe'
SAV = sys.argv[2] if len(sys.argv) > 2 else r'C:\Warlords3\SAVES\Tanda_Kor.SAV'
ARMY = os.path.join(os.path.dirname(EXE), 'ARMY')
mal = 0
def ver(c, msg):
    global mal; mal += not c; print('OK  ' if c else 'MAL ', msg)

A = armas(ARMY); por = {a.archivo.lower(): a for a in A}
ver(len(A) > 0, f'{len(A)} armas leídas de {ARMY} ({sum(a.barco for a in A)} barcos)')
m = Motor(EXE, SAV)
n = dif = 0; nuevos = set(); tsav = os.path.getmtime(SAV)
for s in range(8 * 16):
    r = bytes(m.mu.mem_read(TIPOS + s * TREC, TREC)); k = r[0x90:0x99].split(b'\0')[0].decode('latin-1').lower()
    if k not in por: continue
    a = por[k]; b = a.registro
    if os.path.getmtime(a.ruta) > tsav: nuevos.add(a.archivo); continue   # el .ARM cambió después de la partida
    n += 1
    campos = [(0x99, 0xa0), (0xd6, 0xd6 + len(a.bono_combate_nombre)), (0xdf, 0xe0), (0xe2, 0xe9)]
    if any(r[i:j] != b[i:j] for i, j in campos) or r[0:16].split(b'\0')[0] != b[0:16].split(b'\0')[0]: dif += 1
ver(n > 0 and dif == 0, f'{n} tipos cargados por la partida: nombre, medalla..vista, bonos, costo y poder iguales al .ARM'
    f' (sin comparar {len(nuevos)}, modificados después de la partida: {", ".join(sorted(nuevos))})')
for a in sorted(A, key=lambda a: -a.factor())[:5]: print(f'     Factor {a.factor():5.1f}  {a!r}  {a.poder_texto()}')

N = 10000; AX, AY, DX, DY = 50, 40, 51, 40
def pct(ta, td):
    m.limpiar(); m.vaciar((AX, AY), (DX, DY))
    at = m.poner(0, [ta] * 3, AX, AY, 200); m.poner(1, [td] * 3, DX, DY, 201)
    return 100 * m.probabilidad_motor(0, at, DX, DY, 12345, N) / N
base = pct(1, 1)
m.cargar_arma(0, 12, por['gnollcav'].registro); m.cargar_arma(1, 12, por['gnollcav'].registro)
v = pct(12, 12); ver(v == base, f'gnollcav del juego {base:.2f} %, gnollcav cargado del .ARM {v:.2f} %')
fuerte = max(A, key=lambda a: (a.fuerza, a.vidas) if not a.barco else (0, 0))
m.cargar_arma(0, 12, fuerte.registro)
v2 = pct(12, 12); ver(v2 > base, f'control, el atacante con {fuerte.archivo} (F{fuerte.fuerza} V{fuerte.vidas}): {v2:.2f} %')
print('RESULTADO:', 'TODO OK' if not mal else f'{mal} FALLAS')
