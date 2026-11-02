# Publica Visor-Historia.exe y Visor-Historia.version (el número de versión, en texto) en la release Actualizador
# de elcoprofago/Warlords-updater, de donde los baja el botón «Actualizar versión» de la configuración.
# Uso: python ia\visor-historia\publicar.py
# Se niega si: no se está en main, hay cambios sin commitear en ia\, la versión no es mayor que la publicada o el
# .exe compilado no dice adentro la misma versión. Verifica lo publicado bajándolo de nuevo (SHA-256).
import hashlib, os, subprocess, sys, tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
IA = os.path.dirname(AQUI)
sys.path.insert(0, AQUI); sys.path.insert(0, IA)
from visor_historia import EXE, MARCA, VERSION, version_de, version_tupla   # noqa: E402

REPO, TAG = 'elcoprofago/Warlords-updater', 'Actualizador'
RUTA_EXE = os.path.join(IA, EXE)


def correr(*cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def parar(msg):
    sys.exit(f'No se publica: {msg}')


def sha(ruta):
    with open(ruta, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


_, rama, _ = correr('git', '-C', IA, 'branch', '--show-current')
if rama != 'main':
    parar(f'hay que estar en main (estás en {rama}).')
_, sucio, _ = correr('git', '-C', IA, 'status', '--porcelain', '--', '.')
if sucio:
    parar(f'hay cambios sin commitear en ia\\:\n{sucio}')
tmp = tempfile.mkdtemp(prefix='visor-publicar-')
cod, _, _ = correr('gh', 'release', 'download', TAG, '-p', MARCA, '-D', tmp, '-R', REPO)
if not cod:
    with open(os.path.join(tmp, MARCA)) as f:
        ultima = f.read().strip()
    if version_tupla(VERSION) <= version_tupla(ultima):
        parar(f'VERSION {VERSION} no es mayor que la publicada ({ultima}): subí VERSION en visor_historia.py.')

if subprocess.run([sys.executable, os.path.join(AQUI, 'build.py')]).returncode:
    parar('falló la compilación.')
interna = version_de(RUTA_EXE)
if interna != VERSION:
    parar(f'el .exe compilado dice {interna}, no {VERSION}.')
marca = os.path.join(tmp, 'subir', MARCA)
os.makedirs(os.path.dirname(marca))
with open(marca, 'w') as f:
    f.write(VERSION)
# Primero el .exe y después la marca: si se corta en el medio, nadie ve anunciada una versión que no está.
for ruta in (RUTA_EXE, marca):
    cod, _, err = correr('gh', 'release', 'upload', TAG, ruta, '--clobber', '-R', REPO)
    if cod:
        parar(f'gh release upload {os.path.basename(ruta)} falló:\n{err}')
bajado = os.path.join(tmp, 'bajado')
cod, _, err = correr('gh', 'release', 'download', TAG, '-p', EXE, '-p', MARCA, '-D', bajado, '-R', REPO, '--clobber')
if cod:
    sys.exit(f'PUBLICADO A MEDIAS: no se pudo bajar para verificar:\n{err}')
for ruta in (RUTA_EXE, marca):
    if sha(ruta) != sha(os.path.join(bajado, os.path.basename(ruta))):
        sys.exit(f'PUBLICADO A MEDIAS: {os.path.basename(ruta)} publicado no es el armado.')
print(f'PUBLICADO: Visor de historia {VERSION} en la release {TAG} ({sha(RUTA_EXE)})')
