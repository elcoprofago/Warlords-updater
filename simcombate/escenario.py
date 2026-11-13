# Escenario del simulador de combate (etapa 3 de PENDIENTE-simulador-combate.md): lo que arma el tablero, sin ventana.
# Un escenario es un dict:
#   {'A': lado, 'D': lado, 'campo': campo}
#   lado  = {'tropas': [(archivo .ARM o None, cantidad)] * 8   (casillero k = k-ésimo en pelear, el fight order),
#            'heroe': None | {'clase': archivo .HER, 'nivel': 1..10, 'elecciones': [índices 0..9, repetibles],
#                             'items': [archivos .ITM], 'hechizos': [archivos .SPL]},
#            'barco': archivo .ARM de barco o None,  'ciudades': None | cantidad de ciudades del bando}
#   campo = {'terreno': nombre, 'estructura': 0 nada | 1 camino o puente | 3 ciudad, 'bosque': bool,
#            'noche': bool, 'defensas': 1..3 (solo ciudad), 'obra': None | 'torre' | 'faro' | 'muro'}
#   La obra (vista-aliada) es del defensor y está en su casilla: torre Life Ward +2, faro +1 (y +1 de fuerza a los no
#   héroes); muro Life Ward +3, Missiles +3, Acid +3, Fortify +3 (sin Life Drain desde vista-aliada 1.0.204.0). Life Ward de la ciudad = su tamaño.
# El atacante es el bando 0 y el defensor el 1; el casillero k de cada lado carga su arma en la ranura k del bando y
# le da prioridad k en el fight order (Motor.orden), así que la pila pelea en el orden de la grilla. El héroe usa la
# ranura de clase 0. En agua las tropas van embarcadas (hace falta un barco); con puente, no.
import os, struct
import datos
from motor import Motor, CIUDAD0, OBRAS

MAX_PILA = 8          # tope común de una pila; los otros topes, en Simulador.tope
TOPE_CIUDAD = 32      # la ciudad defiende con sus 4 casillas de 8 (la ficha del defensor tiene 32 lugares; medido)
TOPE_LANDING, TOPE_LANDING_CARRIER = 5, 6     # pila en agua con barco "Landing" (LANDCAP del parche vista-aliada)
TOPE_CONVOY = 3       # el convoy ("Carrier"): hasta 3 pilas embarcadas vecinas defienden juntas (crlink del parche)
AX, AY, DX, DY = 50, 40, 51, 40      # casillas de campo abierto (Tanda_Kor: tierra, sin nada)
PILA_A, PILA_D = 200, 201

class Error(ValueError):
    pass

class Simulador:
    """Carga una vez el exe, la partida base y los datos del juego; arma y pelea escenarios."""
    def __init__(self, juego, sav, rul=None):
        self.juego = juego
        self.m = Motor(os.path.join(juego, 'DarklordAV.exe'), sav, rul)
        def idx(lista): return {os.path.basename(x.ruta).lower(): x for x in lista}
        todas = datos.armas(os.path.join(juego, 'ARMY'))
        self.armas = {os.path.basename(a.ruta).lower(): a for a in todas if not a.barco}
        self.barcos = {os.path.basename(a.ruta).lower(): a for a in todas if a.barco}
        self.clases = idx(datos.clases(os.path.join(juego, 'HERO')))
        self.items = idx(datos.items(os.path.join(juego, 'ITEMS')))
        self.hechizos = idx(datos.hechizos(os.path.join(juego, 'SPELL')))
        t = self.m.terrenos(); self.terrenos = {}
        for i, n in t.items(): self.terrenos.setdefault(n, i)      # nombre -> primer índice
        self.cx, self.cy = struct.unpack('<hh', self.m.mu.mem_read(CIUDAD0, 4))

    def es_agua(self, terreno):
        return self.m.w(0x535ef8 + self.terrenos[terreno] * 0x58 + 0x14) == 1

    def tope(self, lado, d, campo):
        """(unidades que entran, motivo) para el lado 'A' o 'D' con su barco d['barco'] en ese campo. La ficha de
        batalla tiene 8 lugares para el atacante y 32 para el defensor."""
        est = campo.get('estructura', 0)
        if lado == 'D' and est == 3: return TOPE_CIUDAD, 'ciudad: 4 casillas de 8'
        agua = campo.get('terreno') in self.terrenos and self.es_agua(campo['terreno']) and est != 1
        b = self.barcos.get((d.get('barco') or '').lower()) if agua else None
        bonos = {x.lower() for x in b.bonos_mov} if b else set()
        pila = (TOPE_LANDING_CARRIER if 'carrier' in bonos else TOPE_LANDING) if 'landing' in bonos else MAX_PILA
        if lado == 'D' and 'carrier' in bonos:
            return TOPE_CONVOY * pila, f'convoy «Carrier»: {TOPE_CONVOY} pilas de {pila}'
        if pila < MAX_PILA: return pila, 'barco «Landing»' + (' y «Carrier»' if 'carrier' in bonos else '')
        return MAX_PILA, 'pila común'

    def _busca(self, tabla, archivo, que):
        x = tabla.get((archivo or '').lower())
        if x is None: raise Error(f'{que} «{archivo}» no está en la carpeta del juego')
        return x

    def armar(self, esc):
        """Arma el escenario en el motor. Devuelve (unidades del atacante, (x, y) del defensor, avisos)."""
        m, c = self.m, esc['campo']; avisos = []
        if c['terreno'] not in self.terrenos: raise Error(f'terreno «{c["terreno"]}» desconocido')
        agua, est = self.es_agua(c['terreno']), c.get('estructura', 0)
        if agua and est == 3: raise Error('una ciudad no puede estar en el agua')
        m.limpiar(); m.dia_noche(bool(c.get('noche')))
        if est == 3:     # la ciudad 0 de la partida, del defensor; el atacante, al oeste
            dx, dy = self.cx, self.cy; ax, ay = dx - 1, dy
            m.vaciar((ax, ay), (dx, dy), (dx + 1, dy), (dx, dy + 1), (dx + 1, dy + 1))
        else:
            ax, ay, dx, dy = AX, AY, DX, DY
            m.vaciar((ax, ay), (dx, dy))
            for x, y in ((ax, ay), (dx, dy)): m.poner_terreno(x, y, self.terrenos[c['terreno']], est, bool(c.get('bosque')))
        if est == 3: m.poner_terreno(dx, dy, None, None, bool(c.get('bosque')))
        for b, lado in ((0, 'A'), (1, 'D')):
            n = esc[lado].get('ciudades')
            if n is not None: m.ciudades_de(b, n)
        if est == 3:
            nivel = c.get('defensas', 1)
            if not 1 <= nivel <= 3: raise Error('defensas de la ciudad: 1 a 3')
            m.mu.mem_write(CIUDAD0 + 0xa5, bytes([1])); m.mu.mem_write(CIUDAD0 + 0xa4, bytes([nivel])); m.call(0x4407d0, [])
        obra = c.get('obra')
        if obra:
            if obra not in OBRAS: raise Error(f'obra «{obra}» desconocida')
            if agua: raise Error('las obras van en tierra')
            if est == 3 and obra != 'muro': raise Error('la torre y el faro no van en una ciudad (el muro sí, al lado)')
            # en la casilla del defensor, de su bando: el muro vale igual sobre el bloque o a 1 casilla
            m.poner_obra(obra, dx, dy, 1)
        ids = {}; self.clase_de = {}
        for b, lado, (x, y), pila in ((0, 'A', (ax, ay), PILA_A), (1, 'D', (dx, dy), PILA_D)):
            ids[lado] = self._lado(b, lado, esc[lado], x, y, pila, agua and est != 1, avisos, self.tope(lado, esc[lado], c),
                                   [(dx + 1, dy), (dx, dy + 1), (dx + 1, dy + 1)] if lado == 'D' and est == 3 else [])
        if not ids['A']: raise Error('el atacante no tiene unidades')
        if not ids['D']: raise Error('el defensor no tiene unidades')
        self.ids = ids
        return ids['A'], (dx, dy), avisos

    def _lado(self, b, lado, d, x, y, pila, embarcadas, avisos, tope=(MAX_PILA, 'pila común'), otras=()):
        """otras: más casillas del lado (las de la ciudad), que se llenan de a MAX_PILA después de (x, y)."""
        m = self.m; nombre = 'atacante' if lado == 'A' else 'defensor'
        tropas = [(a, n) for a, n in d['tropas'] if a and n > 0]
        total = sum(n for _, n in tropas) + (1 if d.get('heroe') else 0)
        if total > tope[0]: raise Error(f'el {nombre} tiene {total} unidades; aquí entran {tope[0]} como máximo ({tope[1]})')
        ranuras, tipos = [], []
        for k, (a, n) in enumerate(d['tropas']):
            if not a or n <= 0: continue
            m.cargar_arma(b, k, self._busca(self.armas, a, 'el arma').registro)
            ranuras.append(k); tipos += [k] * n
        m.orden(b, ranuras)
        casillas = [(x, y)] + list(otras) if otras else [(x, y)]
        por = MAX_PILA if otras else max(len(tipos), 1)
        ids = []
        for i, (cx, cy) in enumerate(casillas):
            parte = tipos[i * por:(i + 1) * por]
            if parte: ids += m.poner(b, parte, cx, cy, pila + 10 * i)
        if d.get('heroe'):     # el héroe va en la primera casilla con lugar
            i = min(len(tipos) // por, len(casillas) - 1) if otras else 0
            x, y, pila = casillas[i][0], casillas[i][1], pila + 10 * i
        h = d.get('heroe')
        if h:
            cl = self._busca(self.clases, h['clase'], 'la clase'); self.clase_de[lado] = cl
            m.cargar_clase(b, 0, cl.registro)
            try: u = m.poner_heroe(b, 0, h.get('nivel', 1), h.get('elecciones', []), x, y, pila)
            except ValueError as e: raise Error(f'héroe del {nombre}: {e}')
            for it in h.get('items', []): m.dar_item(u, self._busca(self.items, it, 'el ítem').registro)
            for sp in h.get('hechizos', []):
                _, fuera = m.lanzar(u, self._busca(self.hechizos, sp, 'el hechizo').registro)
                if fuera: avisos.append(f'{sp} ({nombre}): sus efectos inmediatos (invocar, volar...) no se aplican; '
                                        'una invocación se representa poniendo las unidades invocadas')
            ids.append(u)
        if embarcadas and ids:
            if not d.get('barco'): raise Error(f'el {nombre} está en el agua sin barco')
            bar = self._busca(self.barcos, d['barco'], 'el barco')
            m.cargar_arma(b, 15, bar.registro)
            m.embarcar(ids)
            # el juego: embarcada, cada unidad pelea con min(su fuerza, la del barco) y min(sus vidas, las del barco)
            if not any(self.armas[a.lower()].fuerza > bar.fuerza or self.armas[a.lower()].vidas > bar.vidas for a, _ in tropas):
                avisos.append(f'{bar.archivo} ({nombre}): F{bar.fuerza} V{bar.vidas}, ninguna tropa lo supera, así que no '
                              'cambia nada (embarcada, cada unidad pelea con el menor entre su fuerza y vidas y las del barco)')
        elif d.get('barco') and ids:
            avisos.append(f'{d["barco"]} ({nombre}): el barco solo pelea en agua (sin puente); en esta casilla no cuenta')
        return ids

    def simular(self, esc, n=1000, semilla=12345):
        """% de victorias del atacante en n peleas y una batalla de muestra con su secuencia."""
        atac, (dx, dy), avisos = self.armar(esc)
        g = self.m.probabilidad_motor(0, atac, dx, dy, semilla, n)
        r = self.m.batalla(0, atac, dx, dy, semilla)
        f = r['ficha']; u = lambda i: self.m.unidades()[i - 1]
        def fichas(lado):
            out = []
            o = 0xe if lado == 'A' else 0x12e
            for k, i in enumerate(self.m.orden_ficha(f, lado)[:len(self.ids[lado])]):
                d = u(i); t = struct.unpack_from('<H', d['raw'], 0xc)[0]
                if d['tipo'] == 16:
                    cl = self.clase_de.get(lado); nm = 'Héroe'
                    img = os.path.join(self.juego, 'HERO', cl.imagen) if cl else None
                else:
                    nm = self.m.tipo(d['dueno'], d['tipo'])['corto']; img = os.path.join(self.juego, 'ARMY', nm)
                a = self.armas.get(nm.lower() + '.arm') if d['tipo'] != 16 else None
                out.append(dict(nombre=nm, imagen=img, vidas=(t >> 13) & 7, heroe=d['tipo'] == 16, poder=a.poder if a else 0,
                                # lo que muestra la ventana del juego (0x4071cb): fuerza +8 y vidas +9 del casillero de la ficha
                                fuerza_c=f[o + k * 0x24 + 8], vidas_c=f[o + k * 0x24 + 9]))
            return out
        fa, fd = fichas('A'), fichas('D')
        return dict(pct=100 * g / n, n=n, gana=r['gana'], eventos=r['eventos'], muertes=self.m.muertes(r['eventos']),
                    orden_a=[x['nombre'] for x in fa], orden_d=[x['nombre'] for x in fd], fichas_a=fa, fichas_d=fd,
                    avisos=avisos)
