# Prueba del motor (etapa 1 de PENDIENTE-simulador-combate.md).
# Uso: python prueba_motor.py [DarklordAV.exe] [partida.SAV]   (por defecto C:\Warlords3 y SAVES\Tanda_Kor.SAV)
# 1. Control contra el juego: 0x464a10 (probabilidades del propio exe) y el motor con las rutinas sueltas dan las mismas
#    victorias para cada semilla.
# 2. Cantidad de ciudades: la misma batalla 10 000 veces con el defensor dueño de todas las ciudades y de una sola
#    (y lo mismo con el atacante). Control: una unidad más del atacante tiene que mover el %.
import sys, time
from motor import Motor
EXE = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe'
SAV = sys.argv[2] if len(sys.argv) > 2 else r'C:\Warlords3\SAVES\Tanda_Kor.SAV'
m = Motor(EXE, SAV)
AX, AY, DX, DY = 50, 40, 51, 40
mal = 0
def ver(c, msg):
    global mal; mal += not c; print('OK  ' if c else 'MAL ', msg)

def armar(na=3, nd=3):
    m.limpiar(); m.vaciar((AX, AY), (DX, DY))
    a = m.poner(0, [1] * na, AX, AY, 200); m.poner(1, [1] * nd, DX, DY, 201)
    return a

a = armar()
dif = [(s, m.probabilidad_juego(0, a, DX, DY, s), m.probabilidad_motor(0, a, DX, DY, s)) for s in range(0, 65536, 331)]
ver(all(j == k for s, j, k in dif), f'0x464a10 == motor en {len(dif)} semillas (victorias de 10: '
    f'{sum(j for s, j, k in dif)} y {sum(k for s, j, k in dif)})')

N = 10000
def pct(na=3, nd=3, cd=None, ca=None):
    a = armar(na, nd)
    if cd is not None: ver(m.ciudades_de(1, cd)[1] == cd, f'  el defensor quedó con {cd} ciudades')
    if ca is not None: ver(m.ciudades_de(0, ca)[0] == ca, f'  el atacante quedó con {ca} ciudades')
    return 100 * m.probabilidad_motor(0, a, DX, DY, 12345, N) / N
t = time.time(); base = pct(); print(f'base: {base:.2f} % ({time.time() - t:.1f} s por {N})')
for nombre, kw in (('defensor 40 ciudades', dict(cd=40)), ('defensor 1 ciudad', dict(cd=1)),
                   ('atacante 40 ciudades', dict(ca=40)), ('atacante 1 ciudad', dict(ca=1))):
    v = pct(**kw); ver(v == base, f'{nombre}: {v:.2f} %')
v = pct(na=4); ver(v != base, f'control, una unidad más del atacante: {v:.2f} %')
# 2b. Lo mismo con el defensor dentro de una ciudad suya (la 0); el atacante, al lado
import struct
CX, CY = struct.unpack('<hh', m.mu.mem_read(0x537e2c, 4))
def pct_ciudad(cd):
    m.limpiar(); m.vaciar((CX - 1, CY), (CX, CY))
    a = m.poner(0, [1] * 4, CX - 1, CY, 200); m.poner(1, [1] * 3, CX, CY, 201)
    m.mu.mem_write(0x537e2c + 0xa5, bytes([1]))
    n = m.ciudades_de(1, cd)[1]; m.mu.mem_write(0x537e2c + 0xa5, bytes([1])); m.call(0x4407d0, [])
    r = m.batalla(0, a, CX, CY, 5)
    ver(r['ficha'][2] == 0, f'  la ficha marca la ciudad 0 ({CX}, {CY}); el defensor tiene {n} ciudades')
    return 100 * m.probabilidad_motor(0, a, CX, CY, 12345, N) / N
c40, c1 = pct_ciudad(40), pct_ciudad(1)
ver(c40 == c1, f'en ciudad: defensor con 40 ciudades {c40:.2f} %, con 1 {c1:.2f} %')

# 2c. Defensas de la ciudad (+0xa4): 3 contra 3, el defensor en su ciudad con nivel 1, 2 y 3; el atacante tiene que
# ganar menos que en campo abierto y menos cuanto más alto el nivel (tope FortifySiegeLimit del .rul)
def pct_defensa(nivel):
    m.limpiar(); m.vaciar((CX - 1, CY), (CX, CY))
    a = m.poner(0, [1] * 3, CX - 1, CY, 200); m.poner(1, [1] * 3, CX, CY, 201)
    m.mu.mem_write(0x537e2c + 0xa5, bytes([1])); m.mu.mem_write(0x537e2c + 0xa4, bytes([nivel])); m.call(0x4407d0, [])
    return 100 * m.probabilidad_motor(0, a, CX, CY, 12345, N) / N
niv = [pct_defensa(k) for k in (1, 2, 3)]
ver(base > niv[0] > niv[1] > niv[2], 'defensas: atacante gana ' + f'{base:.2f} % en campo, ' +
    ', '.join(f'{v:.2f} % contra nivel {k}' for k, v in zip((1, 2, 3), niv)))

# 3. Secuencia: una batalla con semilla fija, de punta a punta; las muertes alcanzan para dar el ganador
a = armar(); r = m.batalla(0, a, DX, DY, 777)
mu = m.muertes(r['eventos'])
print('eventos', r['eventos']); print('muertes', mu)
ver(r['gana'] == (sum(1 for l, i in mu if l == 'D') == 3), 'el ganador es el que no perdió todas sus unidades')
print('RESULTADO:', 'TODO OK' if not mal else f'{mal} FALLAS')
