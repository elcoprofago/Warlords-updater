# Prueba de los barcos (etapa 2 de PENDIENTE-simulador-combate.md).
# Uso: python prueba_barcos.py [DarklordAV.exe] [partida.SAV]   (por defecto C:\Warlords3 y SAVES\Tanda_Kor.SAV)
# 3 gnollcav contra 3 gnollcav embarcados en cada barco del ARMY (ranura 15 del bando), 4000 peleas: tiene que dar lo
# mismo que contra 3 gnollcav en tierra con fuerza min(5, barco) y vidas min(2, barco). Lo mismo con el atacante
# embarcado. Controles: en tierra sin embarcar, el barco no cambia nada; en un puente (agua con camino), tampoco.
import os, sys, struct
from motor import Motor
from datos import armas
EXE = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3\DarklordAV.exe'
SAV = sys.argv[2] if len(sys.argv) > 2 else r'C:\Warlords3\SAVES\Tanda_Kor.SAV'
A = armas(os.path.join(os.path.dirname(EXE), 'ARMY')); por = {a.archivo.lower(): a for a in A}
m = Motor(EXE, SAV); N = 4000; AX, AY, DX, DY = 50, 40, 51, 40
gnoll = por['gnollcav']
mal = 0
def ver(c, msg):
    global mal; mal += not c; print('OK  ' if c else 'MAL ', msg)

def pct(barco=None, lado='D', agua=True, emb=True, puente=False, rebaja=None):
    m.limpiar(); m.vaciar((AX, AY), (DX, DY))
    for x, y in ((AX, AY), (DX, DY)): m.poner_terreno(x, y, 0, 0, False)
    b = 1 if lado == 'D' else 0
    r = bytearray(gnoll.registro)
    if rebaja: r[0x9a], r[0x9c] = rebaja
    m.cargar_arma(0, 12, gnoll.registro); m.cargar_arma(1, 12, gnoll.registro); m.cargar_arma(b, 12, bytes(r))
    if barco: m.cargar_arma(b, 15, barco.registro)
    at = m.poner(0, [12] * 3, AX, AY, 200); de = m.poner(1, [12] * 3, DX, DY, 201)
    x, y = (DX, DY) if lado == 'D' else (AX, AY)
    if agua: m.poner_terreno(x, y, 1, 1 if puente else 0)
    if emb: m.embarcar(de if lado == 'D' else at)
    return 100 * m.probabilidad_motor(0, at, DX, DY, 12345, N) / N

base = pct(agua=False, emb=False)
print(f'base en tierra: {base:.2f} %')
for barco in (a for a in A if a.barco):
    f, v = min(gnoll.fuerza, barco.fuerza), min(gnoll.vidas, barco.vidas)
    for lado in 'DA':
        e, ref = pct(barco, lado), pct(lado=lado, agua=False, emb=False, rebaja=(f, v))
        ver(e == ref, f'{barco.archivo:9} F{barco.fuerza} V{barco.vidas} {barco.bono_combate_nombre or "-"}+{barco.bono_combate}'
            f' {lado} embarcado {e:6.2f} %  = en tierra con F{f} V{v} {ref:6.2f} %')
debil = min((a for a in A if a.barco), key=lambda a: a.fuerza)
ver(pct(debil, agua=False, emb=False) == base, f'control: con {debil.archivo} en la ranura 15 pero en tierra, {base:.2f} %')
v = pct(debil, puente=True, emb=False)
ver(v == base, f'control: en un puente sin embarcar, {v:.2f} %')
ver(pct(debil) != base, f'control: embarcados en {debil.archivo} el % cambia')
print('RESULTADO:', 'TODO OK' if not mal else f'{mal} FALLAS')
