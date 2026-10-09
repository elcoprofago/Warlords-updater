# Arma Herramientas\votacion.exe y Herramientas\sorteo.exe, los programas que abren los botones "Votacion" y
# "Draw Lots" de vista-aliada (DarklordAV.exe los lanza desde C:\Warlords3 con --operador / --espectador).
# No los compila: copia el dist\<programa>.exe de los repos Votacion y Sorteo (hermanos de este repo), y se niega si
#   - la VERSION del programa no es la que fija PROGRAMAS: una version nueva de un programa obliga a cambiar este
#     archivo, y hooks\pre-commit obliga entonces a subir la VERSION de herramientas en parches.txt (si no, los
#     jugadores que ya lo tienen nunca verian la actualizacion);
#   - el repo del programa tiene cambios sin commitear: lo publicado tiene que salir de un commit;
#   - el .exe es anterior al ultimo commit que toco el programa: se commiteo algo que no se compilo (compilar.ps1).
# votacion.ini (la pantalla elegida en cada PC) no va: el programa usa la principal si falta, y asi el actualizador
# no pisa la de nadie.
# Uso: python build.py [carpeta_salida]   (por defecto C:\Warlords3; W3_REPOS cambia la carpeta de los repos, para
#      probar)
import os, re, shutil, subprocess, sys
from datetime import datetime

# programa: (repo, fuente con VERSION, version que se publica, lo que cuenta como "el programa" en git)
PROGRAMAS = {
    'votacion': ('Votacion', 'votacion.py', '1.1.2', ['votacion.py', 'assets', 'votacion.spec']),
    'sorteo': ('Sorteo', 'sorteo.py', '1.1.1', ['sorteo.py', 'assets', 'sorteo.spec']),
}

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else r'C:\Warlords3'
if OUT_DIR.startswith('-'):
    sys.exit('Uso: python build.py [carpeta_salida]   (por defecto C:\\Warlords3)')
REPOS = os.environ.get('W3_REPOS') or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))


def git(repo, *args):
    r = subprocess.run(['git', '-C', repo, *args], capture_output=True, text=True, encoding='utf-8')
    if r.returncode:
        sys.exit(f'git {" ".join(args)} en {repo} fallo: {r.stderr.strip()}')
    return r.stdout.strip()


fallas = []
copias = []
for nombre, (carpeta, fuente, version, rutas) in PROGRAMAS.items():
    repo = os.path.join(REPOS, carpeta)
    exe = os.path.join(repo, 'dist', nombre + '.exe')
    if not os.path.isdir(repo):
        fallas.append(f'{carpeta}: no esta el repo en {repo}')
        continue
    m = re.search(r'^VERSION = "(.+)"', open(os.path.join(repo, fuente), encoding='utf-8').read(), re.M)
    if not m:
        fallas.append(f'{carpeta}: no encuentro VERSION = "..." en {fuente}')
        continue
    if m.group(1) != version:
        fallas.append(f'{carpeta}: {fuente} dice VERSION {m.group(1)} y este build.py publica {version}. '
                      f'Cambia PROGRAMAS aca y subi la VERSION de herramientas en parches.txt.')
    if git(repo, 'status', '--porcelain'):
        fallas.append(f'{carpeta}: tiene cambios sin commitear')
    if not os.path.isfile(exe):
        fallas.append(f'{carpeta}: no esta {exe} (correr compilar.ps1)')
        continue
    ultimo = git(repo, 'log', '-1', '--format=%cI', '--', *rutas)
    if ultimo and os.path.getmtime(exe) < datetime.fromisoformat(ultimo).timestamp():
        fallas.append(f'{carpeta}: {exe} es anterior al ultimo commit del programa ({ultimo}); correr compilar.ps1')
    copias.append((exe, os.path.join(OUT_DIR, 'Herramientas', nombre + '.exe'), f'{nombre} v{version}'))

if fallas:
    sys.exit('No se arma herramientas:\n  ' + '\n  '.join(fallas))
for origen, destino, etiqueta in copias:
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    shutil.copyfile(origen, destino)
    print(f'{etiqueta}: {destino}')
