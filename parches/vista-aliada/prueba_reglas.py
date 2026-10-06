# Prueba del chequeo del Army List contra DarklordsValidator real (reglas 1-25).
# Uso: python prueba_reglas.py [cantidad de casos sintéticos, 20000 por defecto] [carpeta ARMY, C:\Warlords3\ARMY]
#   Arma el parche en una carpeta temporal (build.py), emula su rutina armeval (unicorn) y la compara, unidad por
#   unidad, con RulesEngine.Validate del validador (..\..\..\DarklordsValidator, compilado acá con dotnet) y con
#   reglas_ref.validar. Primero sobre los .ARM reales, después sobre casos sintéticos con valores alrededor de cada
#   umbral y textos raros en Move Bonus y Combat Bonus (mayúsculas, espacios, bytes de control y > 0x7f).
#   Requiere pefile, unicorn, keystone, capstone y el SDK de .NET 8.
import os, sys, ast, glob, random, shutil, struct, subprocess, tempfile
import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EAX
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import reglas_ref as RR

N = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
ARMY = sys.argv[2] if len(sys.argv) > 2 else r'C:\Warlords3\ARMY'
VALIDADOR = os.path.normpath(os.path.join(AQUI, '..', '..', '..', 'DarklordsValidator', 'DarklordsValidator.csproj'))
TMP = tempfile.mkdtemp(prefix='prueba_reglas_')

def correr(args, **kw):
    r = subprocess.run(args, capture_output=True, text=True, **kw)
    if r.returncode: sys.exit(f'falló {args[:2]} (código {r.returncode}):\n{r.stdout}\n{r.stderr}')
    return r.stdout

try:
    # 1) el parche, armado desde el build.py actual
    os.makedirs(os.path.join(TMP, 'parche', 'DATA'))
    salida = correr([sys.executable, os.path.join(AQUI, 'build.py'), os.path.join(TMP, 'parche')], cwd=AQUI)
    caves = ast.literal_eval(next(l for l in salida.splitlines() if l.startswith('caves '))[6:])
    ARMEVAL = int(caves['armeval'], 16)
    pe = pefile.PE(os.path.join(TMP, 'parche', 'DarklordAV.exe')); img = pe.get_memory_mapped_image()
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(0x400000, (len(img) + 0xfff) & ~0xfff); mu.mem_write(0x400000, img)
    STK = 0x10000000; mu.mem_map(STK, 0x100000); mu.mem_map(0xdead0000, 0x1000)
    BUF = STK + 0x90000
    def armeval(rec, ship):
        mu.mem_write(BUF, rec)
        sp = STK + 0x80000
        for a in (ship, BUF):
            sp -= 4; mu.mem_write(sp, struct.pack('<I', a))
        sp -= 4; mu.mem_write(sp, struct.pack('<I', 0xdead0000))
        mu.reg_write(UC_X86_REG_ESP, sp)
        mu.emu_start(ARMEVAL, 0xdead0000, count=5_000_000)
        m = mu.reg_read(UC_X86_REG_EAX)
        return [i + 1 for i in range(32) if m >> i & 1]

    # 2) el validador real: un programa de consola que imprime, por .ARM, si es ship y las reglas que viola
    cmp_dir = os.path.join(TMP, 'comparador'); os.makedirs(cmp_dir)
    open(os.path.join(cmp_dir, 'Comparador.csproj'), 'w').write(f'''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net8.0-windows</TargetFramework>
    <UseWindowsForms>true</UseWindowsForms><Nullable>disable</Nullable></PropertyGroup>
  <ItemGroup><ProjectReference Include="{VALIDADOR}" /></ItemGroup>
</Project>''')
    open(os.path.join(cmp_dir, 'Program.cs'), 'w').write('''using System; using System.IO; using System.Linq;
using DarklordsValidator;
foreach (var f in Directory.GetFiles(args[0], "*.ARM").OrderBy(x => x, StringComparer.OrdinalIgnoreCase))
{
    var u = new Unit(f);
    var r = RulesEngine.Validate(u).Select(x => x.RuleNumber);
    Console.WriteLine($"{Path.GetFileName(f)}\\t{(u.IsAShip ? 1 : 0)}\\t{string.Join(",", r)}");
}''')
    correr(['dotnet', 'build', '-c', 'Release', '-o', os.path.join(cmp_dir, 'bin'), cmp_dir])
    COMP = os.path.join(cmp_dir, 'bin', 'Comparador.exe')

    def comparar(d, tag):
        dif = 0; cuenta = {}; total = 0
        for ln in correr([COMP, d]).splitlines():
            f, ship, r = ln.split('\t'); ship = int(ship)
            val = [int(x) for x in r.split(',')] if r else []
            rec = open(os.path.join(d, f), 'rb').read()[:0xfc].ljust(0xfc, b'\0')
            par, ref = armeval(rec, ship), RR.validar(RR.unit(rec, bool(ship)))
            total += 1
            for k in val: cuenta[k] = cuenta.get(k, 0) + 1
            if par != val or ref != val:
                dif += 1
                if dif <= 15: print(f'  DIFERENCIA {f} ship={ship} validador={val} parche={par} reglas_ref={ref}')
        print(f'{tag}: {total} unidades, {dif} diferencias')
        print('  unidades que violan cada regla:', ' '.join(f'{k}:{cuenta.get(k, 0)}' for k in range(1, 26)))
        return dif

    dif = comparar(ARMY, 'ARMY')

    # 3) casos de juguete: cada uno con su control en el límite. (nombre, ship, cambios, regla, ¿la viola?)
    def juguete(ship, **c):
        r = bytearray(0xfc)
        r[0x9a:0x9f] = bytes([1, 1, 1, 5, 50])                 # S M H T U: no viola nada
        struct.pack_into('<HH', r, 0xe2, 2000, 2000)
        for k, v in c.items():
            if k.startswith('mb'): r[0xb2 + 9 * int(k[2]):0xb2 + 9 * int(k[2]) + len(v)] = v
            else: r[dict(S=0x9a, M=0x9b, U=0x9e, PC=0xe6, PV=0xe8)[k]] = v
        return r, ship
    JUG = [
        ('L13', 1, dict(mb0=b'landing', M=13), 8, True), ('L12', 1, dict(mb0=b'landing', M=12), 8, False),
        ('L13b', 1, dict(mb3=b'LANDING', M=13), 8, True), ('L13t', 0, dict(mb1=b'landing', M=13), 8, False),
        ('LC999', 1, dict(mb2=b'Landing', M=12), 24, True), ('LC2000', 1, dict(mb2=b'Landing', U=17), 24, False),
        ('LU16', 1, dict(mb2=b'Landing', U=16), 24, True),
        ('C1199', 1, dict(mb2=b'CARRIER'), 25, True), ('C2000', 1, dict(mb2=b'CARRIER'), 25, False), ('U33', 1, dict(mb1=b'carrier', U=33), 25, True),
        ('U34', 1, dict(mb1=b'carrier', U=34), 25, False), ('Ct', 0, dict(mb1=b'carrier', U=33), 25, False),
        ('T21', 0, dict(mb3=b'Fly', PC=32, PV=1, M=21), 5, True), ('T20', 0, dict(mb3=b'Fly', PC=32, PV=1, M=20), 5, False),
        ('T21t', 0, dict(PC=32, PV=1, M=21), 5, False),
    ]
    jd = os.path.join(TMP, 'juguete'); os.makedirs(jd)
    for nombre, ship, c, regla, viola in JUG:
        r, s = juguete(ship, **c)
        if nombre == 'C1199': struct.pack_into('<H', r, 0xe2, 1199)
        if nombre == 'LC999': struct.pack_into('<H', r, 0xe2, 999)
        r[0x90:0x99] = nombre.encode().ljust(9, b'\0')
        open(os.path.join(jd, nombre + '.ARM'), 'wb').write(r)
        if s: open(os.path.join(jd, nombre + '.SHP'), 'wb').write(b'')
    dif += comparar(jd, 'juguete')
    for nombre, ship, c, regla, viola in JUG:
        rec = open(os.path.join(jd, nombre + '.ARM'), 'rb').read()
        ok = (regla in armeval(rec, ship)) == viola
        print(f'  {"OK   " if ok else "FALLA"} {nombre}: regla {regla} {"violada" if viola else "no violada"}')
        dif += not ok

    # 4) casos sintéticos
    rnd = random.Random(20261006)
    bases = [open(p, 'rb').read()[:0xfc].ljust(0xfc, b'\0') for p in glob.glob(os.path.join(ARMY, '*.ARM'))]
    CHICO = list(range(0, 27)) + [29, 30, 31, 33, 34, 35, 39, 40, 41, 255]
    WORD = [0, 1, 149, 150, 151, 299, 300, 301, 399, 400, 401, 499, 500, 501, 599, 600, 601, 799, 800, 801,
            999, 1000, 1001, 1199, 1200, 1201, 2000, 65535]
    MB = [b'', b'fly', b'FLY', b'Fly', b' fly', b'fly ', b'  fly  ', b'Fly\x01', b'f\x01ly', b'fl\x80y', b'fly2',
          b'fly\0xyz', b'flyy', b'fl', b'landing', b'LANDING', b'Landing', b' landing ', b'landing\x80',
          b'landing\x7f', b'landin', b'landingx', b'carrier', b'CARRIER', b'CaRRier', b'carrier  ', b'carrier\x01',
          b'carriers', b'carrie', b'none', b'None', b'hills', b'water', b'\x80\x80', b'\x7f', b'?', b'lan\0ding']
    CB = [b'', b'none', b'None', b'hills', b'City', b'n/a', b'-', b'a-b', b'x 3', b'None +0', b'\x80ab', b'hi\x7fll',
          b'+2', b'2', b'0', b'hills 0', b'-3', b'\x80', b'?']
    def casillero(b, n=9):
        b = b[:n]
        if len(b) < n:
            b = b + b'\0' + bytes(rnd.choice([0, 0, rnd.randrange(256)]) for _ in range(n - len(b) - 1))
        return b
    def basura(n): return bytes(rnd.randrange(256) for _ in range(rnd.randrange(n + 1)))
    fz = os.path.join(TMP, 'sinteticos'); os.makedirs(fz)
    for k in range(N):
        r = bytearray(rnd.choice(bases))
        nombre = f'Z{k:05d}'
        r[0x90:0x99] = nombre.encode().ljust(9, b'\0')
        for off in range(0x9a, 0x9f): r[off] = rnd.choice(CHICO)
        struct.pack_into('<HH', r, 0xe2, rnd.choice(WORD), rnd.choice(WORD))
        for i in range(4):
            r[0xb2 + 9 * i:0xbb + 9 * i] = casillero(rnd.choice(MB) if rnd.random() < .9 else basura(9))
        r[0xd6:0xdf] = casillero(rnd.choice(CB) if rnd.random() < .9 else basura(9))
        r[0xdf] = rnd.choice([0, 0, 1, 2, 3, 255])
        r[0xe6] = rnd.choice([0, 0, 5, 32, 13, 16, 44, 55, 57, 54, 30, rnd.randrange(256)])
        r[0xe8] = rnd.choice([0, 1, 2, 3, 4, 5, 6, 7, 9, 255])
        open(os.path.join(fz, nombre + '.ARM'), 'wb').write(r)
        if rnd.random() < .4: open(os.path.join(fz, nombre + '.SHP'), 'wb').write(b'x')
    dif += comparar(fz, 'sintéticos')
    print('RESULTADO:', 'TODO OK' if dif == 0 else 'HAY DIFERENCIAS')
    sys.exit(1 if dif else 0)
finally:
    shutil.rmtree(TMP, ignore_errors=True)
