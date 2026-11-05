# Motor del simulador de combate: corre el código real de DarklordAV.exe (unicorn) sobre el estado de una partida.
# 0x464ac0(atacante, x, y, ficha) arma la ficha; 0x466c90(ficha) la deja lista; 0x464ea0(ficha, resultado, modo) pelea.
# Resultado (0x40c bytes): +0 palabra 1 = gana el atacante; +6.. registro de eventos, un byte por evento.
import os, struct, pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_MEM_INVALID, UC_HOOK_CODE, UcError
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EAX

BASE = 0x400000
STK, RET, IMP = 0x10000000, 0xdead0000, 0xdeb00000   # IMP: una entrada por función importada
UNITS_N, UNIT0, UREC = 0x54fe50, 0x54fe52, 28     # unidad u (u >= 1) en UNIT0 + u*28
TIPOS, TREC = 0x53c410, 0xfc                        # tipo t del bando b en TIPOS + (b*16 + t)*TREC
SEL, SELSZ = 0x56ea90, 0x4f0                        # grupo elegido del jugador p (atacantes)
FICHA, FSZ = 0x569a80, 0x5cc
RES, RSZ = 0x56c8e0, 0x40c
SEED, SEEDT = 0x500bf4, 0x500bf8                    # estado del azar 0x4deb20; SEEDT != 0 lo siembra con time()
CIUDADES_N, CIUDAD0, CREC = 0x537e2a, 0x537e2c, 0xde   # ciudad c: +0xa4 viva (> 0), +0xa5 dueño
# Héroes: la unidad es tipo 16 y +0x10 bits 8-13 elige su registro en HEROE0 + h*HREC: +0 bits 6-7 clase (0..3 del
# bando), bit 5 sexo, bit 4 existe, bits 0-3 nivel - 1; +2 nombre; +0x12 experiencia; +0x14 10 casilleros de 16 bytes
# (palabra habilidad, palabra valor; 20 = hechizo, con su nombre en +6); +0xb4 puntos sin gastar.
# Clases: CLASE0 + (bando*4 + c)*CLREC es copia exacta del .HER (comprobado con las 32 de Tanda_Kor.SAV): +0 nombre,
# +0xdc fuerza, mov, vidas, vista; +0x3d0 10 umbrales de experiencia; +0x3e8 puntos que da cada subida de nivel;
# +0x3fc 10 elecciones de 16 bytes (habilidad, valor) y +0x49c su costo en puntos. 0x48efa0(unidad, elección) es la
# rutina del juego que aplica una elección (fuerza, vidas y movimiento van a la unidad; el resto, a un casillero).
HEROE0, HREC, HEROES = 0x556bb2, 0xb8, 64
CLASE0, CLREC = 0x5451d0, 1380
# [COMBAT] del .rul (el juego lo lee al arrancar; sin esto los topes quedan en 0 y anulan, p. ej., las defensas
# de la ciudad): clave -> (dirección, tipo) — 2 = par mín,máx de palabras, 0 = palabra, 1 = byte On/Off.
COMBATE = {'FinalBonusLimit': (0x56951a, 2), 'MoraleFearLimit': (0x56951e, 2), 'LeadershipChaosLimit': (0x569522, 2),
           'FortifySiegeLimit': (0x569526, 2), 'BaseDiseaseChance': (0x56952a, 0), 'BasePoisonChance': (0x56952c, 0),
           'BaseParalyzationChance': (0x56952e, 0), 'BaseCurseChance': (0x569530, 0),
           'BaseAssassinationChance': (0x569532, 0), 'BaseLightningChance': (0x569534, 0), 'BaseAcidChance': (0x569536, 0),
           'BaseMedalChance': (0x569538, 0), 'MedalsForRegulars': (0x56953a, 1), 'MedalsForMercs': (0x56953b, 1),
           'MedalsForAllies': (0x56953c, 1), 'MedalDice1': (0x56953e, 0), 'MedalDice2': (0x569540, 0),
           'MedalDice3': (0x569542, 0), 'MedalDice4': (0x569544, 0)}
REGIONES = ((0x503e00, 0x12), (0x503e58, 0x32000), (0x535ed0, 0xa96), (0x536b30, 0x2d894))

# Eventos del registro de 0x464ea0: 0 el defensor pierde una vida, 1 el atacante pierde una, 2/3 entra la siguiente
# unidad del atacante/defensor, 4/5 muere la del atacante/defensor, 6 gana el atacante, 7 gana el defensor; el resto
# son efectos especiales (0xc, 0xd, 0xf, 0x10, 0x11, 0x15, 0x17+) que la etapa 4 tendrá que identificar.
EVENTOS = {0: 'D-1', 1: 'A-1', 2: 'entra A', 3: 'entra D', 4: 'muere A', 5: 'muere D', 6: 'gana A', 7: 'gana D'}

def muertes(ev):
    """[('A', i) | ('D', i)]: qué unidad (por orden de pelea) muere, en orden."""
    r, na, nd = [], 0, 0
    for c in ev:
        if c == 4: r.append(('A', na)); na += 1
        elif c == 5: r.append(('D', nd)); nd += 1
    return r

class Motor:
    muertes = staticmethod(muertes)

    def __init__(self, exe, sav, rul=None):
        pe = pefile.PE(exe)
        img = pe.get_memory_mapped_image()
        mu = self.mu = Uc(UC_ARCH_X86, UC_MODE_32)
        size = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
        mu.mem_map(BASE, size); mu.mem_write(BASE, img)
        mu.mem_map(STK, 0x100000); mu.mem_map(RET, 0x1000)
        b = open(sav, 'rb').read(); off = 0x6d
        for va, n in REGIONES:
            mu.mem_write(va, b[off:off + n]); off += n
        mu.mem_write(SEEDT, bytes(4))
        self.reglas(rul or os.path.join(os.path.dirname(exe), 'Default.rul'))
        self.W, self.H = struct.unpack('<hh', mu.mem_read(0x503e00, 4))
        self.sh = mu.mem_read(0x503e06, 1)[0]
        self.n0 = self.w(UNITS_N)
        self.inicial = bytes(mu.mem_read(UNIT0, (self.n0 + 64) * UREC))
        self.heroes0 = bytes(mu.mem_read(HEROE0, HEROES * HREC))
        self.fallo = None
        def malo(m, acc, addr, sz, val, u):
            self.fallo = (acc, addr); return False
        mu.hook_add(UC_HOOK_MEM_INVALID, malo)
        # Importadas: cada entrada de la IAT apunta a IMP + 16*i; las de la biblioteca de C (cdecl) se hacen en Python.
        mu.mem_map(IMP, 0x10000); self.imp = {}
        k = 0
        for e in pe.DIRECTORY_ENTRY_IMPORT:
            for i in e.imports:
                mu.mem_write(i.address, struct.pack('<I', IMP + 16 * k))
                self.imp[IMP + 16 * k] = (i.name or b'?').decode(); k += 1
        mu.mem_write(IMP, bytes([0xc3]) * 0x10000)
        mu.hook_add(UC_HOOK_CODE, self._importada, begin=IMP, end=IMP + 0xffff)

    def reglas(self, rul):
        """Carga la sección [COMBAT] del .rul como lo hace el juego al arrancar (0x454700); falta una clave -> error."""
        sec, vals = None, {}
        for ln in open(rul, encoding='latin-1'):
            ln = ln.strip()
            if ln.startswith('['): sec = ln
            elif sec == '[COMBAT]' and '=' in ln: k, v = ln.split('=', 1); vals[k.strip()] = v.strip()
        for k, (a, t) in COMBATE.items():
            v = vals[k]
            if t == 2: self.mu.mem_write(a, struct.pack('<2h', *map(int, v.split(','))))
            elif t == 1: self.mu.mem_write(a, bytes([v.lower() in ('on', 'yes', '1')]))
            else: self.mu.mem_write(a, struct.pack('<h', int(v)))

    def cad(self, a): return bytes(self.mu.mem_read(a, 256)).split(bytes(1))[0]
    def _importada(self, mu, addr, size, u):
        n = self.imp.get(addr)
        sp = mu.reg_read(UC_X86_REG_ESP); a = struct.unpack('<4I', mu.mem_read(sp + 4, 16))
        if n == '_stricmp': x, y = self.cad(a[0]).lower(), self.cad(a[1]).lower(); v = (x > y) - (x < y)
        elif n == 'strcmp': x, y = self.cad(a[0]), self.cad(a[1]); v = (x > y) - (x < y)
        elif n == 'strlen': v = len(self.cad(a[0]))
        else:
            self.fallo = ('importada sin simular', n); mu.emu_stop(); return
        mu.reg_write(UC_X86_REG_EAX, v & 0xffffffff)

    def w(self, va): return struct.unpack('<h', self.mu.mem_read(va, 2))[0]
    def call(self, addr, args):
        sp = STK + 0x80000
        for a in reversed(args): sp -= 4; self.mu.mem_write(sp, struct.pack('<i', a))
        sp -= 4; self.mu.mem_write(sp, struct.pack('<I', RET))
        self.mu.reg_write(UC_X86_REG_ESP, sp)
        self.fallo = None
        try: self.mu.emu_start(addr, RET, count=20_000_000)
        except UcError as e: raise RuntimeError(f'{addr:#x}: {e} {self.fallo}')
        if self.fallo: raise RuntimeError(f'{addr:#x}: {self.fallo}')
        return self.mu.reg_read(UC_X86_REG_EAX)

    def casilla(self, x, y): return 0x503e58 + (((y * 10) << self.sh) + x * 10)
    def unidades(self):
        r = []
        for u in range(1, self.w(UNITS_N)):
            d = bytes(self.mu.mem_read(UNIT0 + u * UREC, UREC))
            x, y = struct.unpack_from('<hh', d); t = struct.unpack_from('<H', d, 0xc)[0]
            r.append(dict(u=u, x=x, y=y, activa=bool(d[0x11] & 0x40), tipo=t & 31, dueno=(t >> 5) & 15, raw=d))
        return r

    def tipo(self, dueno, t):
        r = bytes(self.mu.mem_read(TIPOS + (dueno * 16 + t) * TREC, TREC))
        return dict(corto=r[0x90:0x9a].split(bytes(1))[0].decode('latin-1'), fuerza=r[0x9a], mov=r[0x9b], vidas=r[0x9c])

    def cargar_arma(self, dueno, ranura, registro):
        """Pone un .ARM (sus primeros 0xfc bytes, datos.Arma.registro) en la ranura 0..15 del bando; conserva +0xe0
        (contador del juego, no viene del .ARM)."""
        a = TIPOS + (dueno * 16 + ranura) * TREC
        e0 = bytes(self.mu.mem_read(a + 0xe0, 2))
        self.mu.mem_write(a, bytes(registro[:TREC])); self.mu.mem_write(a + 0xe0, e0)

    def plantilla(self):
        for d in self.unidades():
            if d['activa'] and d['tipo'] < 16 and not d['raw'][0xb] & 2: return d['raw']
        raise RuntimeError('sin unidad común de plantilla')

    def poner(self, dueno, tipos, x, y, pila):
        """Agrega unidades sintéticas (tipos = ranuras 0..15 del bando) en (x, y). Devuelve sus índices."""
        tpl = bytearray(self.plantilla()); ids = []
        n = self.w(UNITS_N)
        for t in tipos:
            r = bytearray(tpl)
            struct.pack_into('<hh', r, 0, x, y)
            ti = self.tipo(dueno, t)   # palabra +0xc: tipo, dueño, fuerza (bits 9-12), vidas (13-15)
            struct.pack_into('<H', r, 0xc, t | dueno << 5 | (ti['fuerza'] & 15) << 9 | (ti['vidas'] & 7) << 13)
            struct.pack_into('<H', r, 0x12, 0)
            struct.pack_into('<H', r, 8, pila << 8 & 0xffff); struct.pack_into('<H', r, 0x14, pila)
            self.mu.mem_write(UNIT0 + n * UREC, bytes(r)); ids.append(n); n += 1
        self.mu.mem_write(UNITS_N, struct.pack('<h', n))
        return ids

    def limpiar(self):
        self.mu.mem_write(UNIT0, self.inicial); self.mu.mem_write(UNITS_N, struct.pack('<h', self.n0))
        self.mu.mem_write(HEROE0, self.heroes0)

    # --- héroes ---
    def cargar_clase(self, dueno, ranura, her):
        """Pone un .HER (sus 1380 bytes) en la ranura de clase 0..3 del bando."""
        if len(her) < CLREC: raise ValueError(f'.HER de {len(her)} bytes, se esperaban {CLREC}')
        self.mu.mem_write(CLASE0 + (dueno * 4 + ranura) * CLREC, bytes(her[:CLREC]))

    def clase(self, dueno, ranura):
        a = CLASE0 + (dueno * 4 + ranura) * CLREC; r = bytes(self.mu.mem_read(a, CLREC))
        el = []
        for i in range(10):
            hab, val = struct.unpack_from('<hh', r, 0x3fc + 16 * i)
            el.append(dict(hab=hab, valor=val, costo=struct.unpack_from('<h', r, 0x49c + 2 * i)[0],
                           hechizo=r[0x3fc + 16 * i + 6:0x3fc + 16 * i + 16].split(bytes(1))[0].decode('latin-1')
                           if hab == 20 else '', dir=a + 0x3fc + 16 * i))
        return dict(nombre=r[:16].split(bytes(1))[0].decode('latin-1'), fuerza=r[0xdc], mov=r[0xdd], vidas=r[0xde],
                    vista=r[0xdf], umbrales=struct.unpack_from('<10h', r, 0x3d0),
                    puntos=struct.unpack_from('<9h', r, 0x3e8), elecciones=el)

    def puntos_nivel(self, dueno, ranura, nivel):
        """Puntos que el héroe juntó al llegar a nivel (1..10): suma de lo que da cada subida (0x416c..)."""
        return sum(self.clase(dueno, ranura)['puntos'][:nivel - 1])

    def poner_heroe(self, dueno, ranura, nivel, elecciones, x, y, pila, sexo=0, nombre='Heroe'):
        """Agrega un héroe de la clase ranura (0..3 del bando), nivel 1..10, con las elecciones (índices 0..9 de la
        clase, repetibles) aplicadas por la rutina del juego. Los puntos gastados no pueden pasar de los del nivel.
        Devuelve el índice de la unidad."""
        c = self.clase(dueno, ranura)
        if not 1 <= nivel <= 10: raise ValueError('nivel 1..10')
        gasto, tiene = sum(c['elecciones'][i]['costo'] for i in elecciones), self.puntos_nivel(dueno, ranura, nivel)
        if gasto > tiene: raise ValueError(f'las elecciones cuestan {gasto} puntos y el nivel {nivel} da {tiene}')
        # 0x48efa0 suma sin tope y la unidad guarda la fuerza en 4 bits y las vidas en 3: 6 + 3*5 = 21 quedaría en 5.
        f = c['fuerza'] + sum(c['elecciones'][i]['valor'] for i in elecciones if c['elecciones'][i]['hab'] == 8)
        v = c['vidas'] + sum(c['elecciones'][i]['valor'] for i in elecciones if c['elecciones'][i]['hab'] == 14)
        if f > 15 or v > 7: raise ValueError(f'fuerza {f} (máximo 15) o vidas {v} (máximo 7): no entran en la unidad')
        usados = {(struct.unpack_from('<H', d['raw'], 0x10)[0] >> 8) & 63 for d in self.unidades()
                  if d['tipo'] == 16 and d['activa']}
        h = next(i for i in range(HEROES) if i not in usados)
        rec = bytearray(HREC)
        rec[0] = ranura << 6 | (sexo & 1) << 5 | 0x10 | (nivel - 1)
        n = nombre.encode('latin-1')[:15]; rec[2:2 + len(n)] = n
        struct.pack_into('<h', rec, 0x12, c['umbrales'][nivel - 1])
        struct.pack_into('<hh', rec, 0x14, 1, 1)            # Leadership 1, como lo crea el juego (0x43afd7)
        struct.pack_into('<h', rec, 0xb4, tiene - gasto)
        self.mu.mem_write(HEROE0 + h * HREC, bytes(rec))
        r = bytearray(self.plantilla())
        struct.pack_into('<hh', r, 0, x, y)
        struct.pack_into('<H', r, 0xc, 16 | dueno << 5 | (c['fuerza'] & 15) << 9 | (c['vidas'] & 7) << 13)
        struct.pack_into('<H', r, 0xe, (c['mov'] & 0x7f) << 8 | (c['vista'] & 7) << 1)
        struct.pack_into('<H', r, 0x10, (struct.unpack_from('<H', r, 0x10)[0] & 0xc080) | h << 8 | (c['mov'] & 0x7f))
        struct.pack_into('<H', r, 0x12, 0)
        struct.pack_into('<H', r, 8, pila << 8 & 0xffff); struct.pack_into('<H', r, 0x14, pila)
        u = self.w(UNITS_N)
        self.mu.mem_write(UNIT0 + u * UREC, bytes(r)); self.mu.mem_write(UNITS_N, struct.pack('<h', u + 1))
        for i in elecciones: self.call(0x48efa0, [u, c['elecciones'][i]['dir']])
        return u

    def heroe(self, u):
        """Lo que el juego ve del héroe u: fuerza, vidas, movimiento (+0x10, donde lo suma 0x48efa0), vista, nivel, clase y casilleros (habilidad, valor)."""
        d = bytes(self.mu.mem_read(UNIT0 + u * UREC, UREC)); w = struct.unpack_from('<H', d, 0xc)[0]
        h = (struct.unpack_from('<H', d, 0x10)[0] >> 8) & 63; rec = bytes(self.mu.mem_read(HEROE0 + h * HREC, HREC))
        cas = [struct.unpack_from('<hh', rec, 0x14 + 16 * i) for i in range(10)]
        return dict(h=h, fuerza=(w >> 9) & 15, vidas=w >> 13, mov=struct.unpack_from('<H', d, 0x10)[0] & 0x7f,
                    vista=(struct.unpack_from('<H', d, 0xe)[0] >> 1) & 7,
                    nivel=(rec[0] & 15) + 1, clase=rec[0] >> 6, casilleros=[c for c in cas if c[0]],
                    puntos=struct.unpack_from('<h', rec, 0xb4)[0])

    def vaciar(self, *casillas):
        for d in self.unidades():
            if (d['x'], d['y']) in casillas and d['activa']:
                a = UNIT0 + d['u'] * UREC + 0x11
                self.mu.mem_write(a, bytes([d['raw'][0x11] & ~0x40]))

    def batalla(self, p, atac, dx, dy, semilla, modo=0):
        """atac = índices de unidades del atacante p; defensores = lo que haya en (dx, dy)."""
        self.seleccionar(p, atac)
        self.mu.mem_write(SEED, struct.pack('<I', semilla & 0xffff))
        f = FICHA + p * FSZ; r = RES + p * RSZ
        if not self.call(0x464ac0, [p, dx, dy, f]) & 0xff: raise RuntimeError('0x464ac0 no armó la ficha')
        ficha = bytes(self.mu.mem_read(f, FSZ))
        self.call(0x466c90, [f])
        gana = self.call(0x464ea0, [f, r, modo]) & 0xff
        res = bytes(self.mu.mem_read(r, RSZ))
        ev = []
        for c in res[6:0x406]:
            ev.append(c)
            if c in (6, 7): break
        return dict(gana=bool(gana), eventos=ev, ficha=ficha, res=res)

    def seleccionar(self, p, atac):
        lst = (atac + [0] * 10)[:10]
        self.mu.mem_write(SEL + p * SELSZ, struct.pack('<hh', atac[0], 0) + struct.pack('<10h', *lst) + struct.pack('<h', len(atac)))

    def probabilidad_juego(self, p, atac, dx, dy, semilla):
        """0x464a10 del juego: arma una vez y pelea 10 veces (modo 1); devuelve las victorias del atacante."""
        self.seleccionar(p, atac); self.mu.mem_write(SEED, struct.pack('<I', semilla & 0xffff))
        return self.call(0x464a10, [p, dx, dy]) & 0xffff

    def probabilidad_motor(self, p, atac, dx, dy, semilla, n=10):
        """Lo mismo, con las rutinas sueltas del motor: arma (0x464ac0) y n veces copia, 0x466c90, 0x464ea0(modo 1)."""
        self.seleccionar(p, atac); self.mu.mem_write(SEED, struct.pack('<I', semilla & 0xffff))
        f = FICHA + p * FSZ; r = RES + p * RSZ; tmp = STK + 0x90000
        self.call(0x464ac0, [p, dx, dy, f]); ficha = bytes(self.mu.mem_read(f, FSZ)); g = 0
        for _ in range(n):
            self.mu.mem_write(tmp, ficha); self.call(0x466c90, [tmp])
            g += self.call(0x464ea0, [tmp, r, 1]) & 1
        return g

    def ciudades_de(self, dueno, n):
        """Deja n ciudades vivas al bando dueno (las primeras) y el resto neutrales; recuenta 0x536b20 (0x4407d0)."""
        k = 0
        for c in range(self.w(CIUDADES_N)):
            a = CIUDAD0 + c * CREC
            if self.mu.mem_read(a + 0xa4, 1)[0] == 0: continue
            self.mu.mem_write(a + 0xa5, bytes([dueno if k < n else 8])); k += 1
        self.call(0x4407d0, [])
        return struct.unpack('<8h', self.mu.mem_read(0x536b20, 16))
