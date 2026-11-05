# Datos del simulador de combate (etapa 2 de PENDIENTE-simulador-combate.md): armas del ARMY activo y su Factor.
# El registro de tipo que usa el juego (0x53c410 + (bando*16 + t)*0xfc) es copia de los primeros 0xfc bytes del .ARM
# (comprobado con Tanda_Kor.SAV: solo difieren el texto de la descripción y +0xe0, un contador del juego), así que
# cualquier .ARM se puede poner en una ranura del bando con Motor.cargar_arma.
# Factor: el mismo cálculo que DarkCompare (StarChartForm.CalcularValores / Coeficiente); se reimplementa acá leyendo
# el .ARM, sin enlazar ese repo.
import os, glob

HABILIDADES = {1: 'Leadership', 2: 'Chaos', 3: 'Morale', 4: 'Fear', 5: 'Siege', 6: 'Fortify', 7: 'Movement',
    8: 'Strength', 9: 'Move Bonus', 10: 'Gold', 11: 'Gold per City', 12: 'Engineer', 13: 'Fly', 14: 'Hits',
    15: 'Speed', 16: 'Invisibility', 17: 'Group Movement', 18: 'Group Hits', 19: 'Port', 20: 'Spell',
    21: 'Production', 22: 'Summon Army', 23: 'View', 24: 'View (group)', 25: 'Bless', 26: 'Poison', 27: 'Disease',
    28: 'Assassin', 29: 'Reveal Map', 30: 'Missiles', 31: 'Medals', 32: 'Trample', 33: 'Curse', 34: 'Teleport',
    35: 'Summon Item', 36: 'xx', 37: 'Banding', 38: 'Acid', 39: 'Lightning', 40: 'Paralysis', 41: 'Warding',
    42: 'Acid (group)', 43: 'Lightning (group)', 44: 'Dragonslayer', 45: 'Demonslayer', 46: 'Deathslayer',
    47: 'Humanslayer', 48: 'bb', 49: 'Dwarfslayer', 50: 'Orcslayer', 51: 'Necromancy', 52: 'Warding (group)',
    53: 'Necromancy', 54: 'Life Drain', 55: 'Questing', 56: 'Mana Drain', 57: 'None'}
SIN_VALOR = {13, 16, 44, 45, 46, 47, 49, 50, 55, 57}
TREC = 0xfc

def _cad(b): return bytes(b).split(b'\0')[0].decode('latin-1').strip()

class Arma:
    def __init__(self, ruta):
        b = open(ruta, 'rb').read()
        if len(b) < TREC: raise ValueError(f'{ruta}: {len(b)} bytes, se esperaban {TREC}')
        self.ruta, self.registro = ruta, b[:TREC]
        self.nombre, self.archivo = _cad(b[0:16]), _cad(b[0x90:0x99])
        self.medalla, self.fuerza, self.mov, self.vidas, self.turnos, self.mant, self.vista = b[0x99:0xa0]
        self.bonos_mov = [m for m in (_cad(b[o:o + 9]) for o in (0xb2, 0xbb, 0xc4, 0xcd)) if m and m.lower() != 'none']
        cb = _cad(b[0xd6:0xdf])
        self.bono_combate = 0 if not cb or cb.lower() == 'none' else b[0xdf]
        self.bono_combate_nombre = '' if not self.bono_combate else cb
        self.costo, self.armado = int.from_bytes(b[0xe2:0xe4], 'little'), int.from_bytes(b[0xe4:0xe6], 'little')
        self.poder, self.poder_valor = b[0xe6], b[0xe8]
        self.barco = os.path.exists(os.path.join(os.path.dirname(ruta), self.archivo + '.SHP'))

    def poder_texto(self):
        n = HABILIDADES.get(self.poder, f'Ability_{self.poder}')
        if self.poder in SIN_VALOR: return n
        return '' if not self.poder or not self.poder_valor else f'{n} +{self.poder_valor}'

    def factor(self):
        """% del área de la estrella máxima de DarkCompare (9 ejes, mínimo visual 0,25)."""
        N = lambda v, mx: v / mx
        l30 = lambda v: 0.30 + v * 0.70; l40 = lambda v: 0.40 + v * 0.60
        p = self.poder_texto()
        pwr = bpwr = 0.0
        if '+' in p:
            v = self.poder_valor if 0 < self.poder_valor < 200 else 0
            pwr = l40(N(v, 7))
        elif p and p.lower() != 'none': bpwr = 0.80
        bcom = l40(N(self.bono_combate, 5)) if self.bono_combate > 0 else 0.0
        v = [l30(N(self.fuerza, 9)), l40(N(self.vidas, 4)), pwr, bcom, l40(N(self.mov, 40)), N(self.vista, 7),
             0.80 if self.bonos_mov else 0.0, bpwr, N(self.medalla, 90)]
        v = [max(x, 0.25) for x in v]
        return sum(v[i] * v[(i + 1) % 9] for i in range(9)) / 9 * 100

    def __repr__(self): return f'<Arma {self.archivo} {self.nombre!r} F{self.fuerza} V{self.vidas} M{self.mov}>'

def armas(carpeta):
    """Todas las armas del ARMY, en orden alfabético de archivo (sin distinguir mayúsculas)."""
    fs = sorted(glob.glob(os.path.join(carpeta, '*.ARM')), key=lambda f: os.path.basename(f).lower())
    return [Arma(f) for f in fs]
