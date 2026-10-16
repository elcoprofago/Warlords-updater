# Publica Monitor-IA.exe como release v<VERSION> en el repo público REPO (el fuente queda acá).
# Uso: python ia\monitor-ia\publicar.py
# Se niega si: no se está en main, hay cambios sin commitear en ia\, la etiqueta ya existe, la versión no es mayor
# que la última publicada, o el .exe compilado no dice adentro la misma versión.
import json, os, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
IA = os.path.dirname(AQUI)
sys.path.insert(0, AQUI); sys.path.insert(0, IA)
from monitor_ia import REPO, VERSION, version_de, version_tupla   # noqa: E402

EXE = os.path.join(IA, 'Monitor-IA.exe')


def correr(*cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def parar(msg):
    sys.exit(f'No se publica: {msg}')


_, rama, _ = correr('git', '-C', IA, 'branch', '--show-current')
if rama != 'main':
    parar(f'hay que estar en main (estás en {rama}).')
_, sucio, _ = correr('git', '-C', IA, 'status', '--porcelain', '--', '.')
if sucio:
    parar(f'hay cambios sin commitear en ia\\:\n{sucio}')
cod, salida, _ = correr('gh', 'release', 'list', '-R', REPO, '--json', 'tagName', '-L', '100')
if cod:
    parar(f'no se pudo leer las releases de {REPO}.')
etiquetas = [r['tagName'].lstrip('v') for r in json.loads(salida)]
if VERSION in etiquetas:
    parar(f'la etiqueta v{VERSION} ya existe: subí VERSION en monitor_ia.py.')
ultima = max(etiquetas, key=version_tupla, default='0')
if etiquetas and version_tupla(VERSION) <= version_tupla(ultima):
    parar(f'VERSION {VERSION} no es mayor que la última publicada ({ultima}).')

if subprocess.run([sys.executable, os.path.join(AQUI, 'build.py')]).returncode:
    parar('falló la compilación.')
interna = version_de(EXE)
if interna != VERSION:
    parar(f'el .exe compilado dice {interna}, no {VERSION}.')
_, commit, _ = correr('git', '-C', IA, 'rev-parse', '--short', 'HEAD')
cod, salida, err = correr('gh', 'release', 'create', f'v{VERSION}', EXE, '-R', REPO, '--title', f'Monitor de IA {VERSION}',
                          '--notes', f'Compilado desde Warlords-updater, commit {commit}.')
if cod:
    parar(f'gh release create falló:\n{err}')
print(f'Publicada v{VERSION}: {salida}')
