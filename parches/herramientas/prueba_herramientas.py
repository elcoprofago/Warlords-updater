# Prueba build.py de herramientas con repos de juguete (W3_REPOS): arma solo cuando los dos programas estan en la
# version fijada, commiteados y compilados despues de su ultimo commit; si no, no escribe nada.
# Controles: un commit que no toca el programa (README) no exige recompilar, y un votacion.ini ya presente en la
# carpeta de salida queda intacto.
# Uso: python prueba_herramientas.py
import os, re, shutil, subprocess, sys, tempfile, time

AQUI = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(AQUI, 'build.py')
fuente_build = open(BUILD, encoding='utf-8').read()
PIN = dict(re.findall(r"'(\w+)': \('\w+', '\w+\.py', '([\d.]+)'", fuente_build))
assert set(PIN) == {'votacion', 'sorteo'}, PIN
REPO = {'votacion': 'Votacion', 'sorteo': 'Sorteo'}
mal = 0


def git(repo, *args, fecha=None):
    env = dict(os.environ)
    if fecha:
        env['GIT_COMMITTER_DATE'] = env['GIT_AUTHOR_DATE'] = fecha
    subprocess.run(['git', '-C', repo, '-c', 'user.name=p', '-c', 'user.email=p@p', '-c', 'core.hooksPath=/dev/null',
                    *args], check=True, capture_output=True, env=env)


def armar(raiz, versiones=None):
    """Repos de juguete: commit del programa hace 1 h, exe compilado ahora."""
    for prog, carpeta in REPO.items():
        repo = os.path.join(raiz, carpeta)
        os.makedirs(os.path.join(repo, 'dist'))
        os.makedirs(os.path.join(repo, 'assets'))
        git(repo, 'init', '-q')
        ver = (versiones or {}).get(prog, PIN[prog])
        open(os.path.join(repo, prog + '.py'), 'w').write(f'VERSION = "{ver}"\n')
        open(os.path.join(repo, 'assets', 'a.png'), 'w').write('x')
        open(os.path.join(repo, '.gitignore'), 'w').write('dist/\n')
        git(repo, 'add', '-A')
        git(repo, 'commit', '-q', '-m', 'programa', fecha=time.strftime('%Y-%m-%dT%H:%M:%S%z', time.localtime(time.time() - 3600)))
        open(os.path.join(repo, 'dist', prog + '.exe'), 'wb').write(os.urandom(1000))
    return {p: os.path.join(raiz, c) for p, c in REPO.items()}


def correr(raiz, salida):
    env = dict(os.environ, W3_REPOS=raiz)
    r = subprocess.run([sys.executable, BUILD, salida], capture_output=True, text=True, env=env)
    return r.returncode, r.stdout + r.stderr


def caso(nombre, preparar, espera_ok, espera_texto=None):
    global mal
    raiz = tempfile.mkdtemp(prefix='herr-')
    try:
        repos = armar(raiz)
        salida = os.path.join(raiz, 'juego')
        ini = os.path.join(salida, 'Herramientas', 'votacion.ini')
        os.makedirs(os.path.dirname(ini))
        open(ini, 'w').write('[Pantalla]\npreferida = \\\\.\\DISPLAY6\n')
        antes_ini = open(ini, 'rb').read()
        preparar(repos)
        codigo, texto = correr(raiz, salida)
        problemas = []
        if (codigo == 0) != espera_ok:
            problemas.append(f'codigo {codigo}')
        if espera_texto and espera_texto not in texto:
            problemas.append(f'falta "{espera_texto}"')
        for prog, repo in repos.items():
            dest = os.path.join(salida, 'Herramientas', prog + '.exe')
            if espera_ok:
                if not os.path.isfile(dest) or open(dest, 'rb').read() != open(os.path.join(repo, 'dist', prog + '.exe'), 'rb').read():
                    problemas.append(f'{prog}.exe no copiado igual')
            elif os.path.exists(dest):
                problemas.append(f'{prog}.exe escrito pese a la falla')
        if open(ini, 'rb').read() != antes_ini:
            problemas.append('votacion.ini cambio (control)')
        print(('ok  ' if not problemas else 'MAL ') + nombre + ('' if not problemas else ': ' + ', '.join(problemas)))
        if problemas:
            print('    ' + texto.strip().replace('\n', '\n    '))
            mal += 1
    finally:
        shutil.rmtree(raiz, ignore_errors=True)


def version_otra(repos):
    open(os.path.join(repos['sorteo'], 'sorteo.py'), 'w').write('VERSION = "9.9.9"\n')
    git(repos['sorteo'], 'commit', '-q', '-am', 'v')
    os.utime(os.path.join(repos['sorteo'], 'dist', 'sorteo.exe'))


def sucio(repos):
    open(os.path.join(repos['votacion'], 'votacion.py'), 'a').write('# cambio\n')


def exe_viejo(repos):
    exe = os.path.join(repos['votacion'], 'dist', 'votacion.exe')
    open(os.path.join(repos['votacion'], 'assets', 'a.png'), 'w').write('y')
    git(repos['votacion'], 'commit', '-q', '-am', 'asset')          # commit ahora
    t = time.time() - 600
    os.utime(exe, (t, t))                                           # exe compilado hace 10 min


def readme_nuevo(repos):                                            # control: no es el programa
    exe = os.path.join(repos['votacion'], 'dist', 'votacion.exe')
    open(os.path.join(repos['votacion'], 'README.md'), 'w').write('x')
    git(repos['votacion'], 'add', 'README.md')
    git(repos['votacion'], 'commit', '-q', '-m', 'readme')
    t = time.time() - 600
    os.utime(exe, (t, t))


def sin_exe(repos):
    os.remove(os.path.join(repos['sorteo'], 'dist', 'sorteo.exe'))


caso('todo en orden: copia los dos', lambda r: None, True, 'votacion v' + PIN['votacion'])
caso('VERSION distinta de la fijada', version_otra, False, 'VERSION 9.9.9')
caso('cambios sin commitear', sucio, False, 'sin commitear')
caso('exe anterior al ultimo commit del programa', exe_viejo, False, 'correr compilar.ps1')
caso('control: commit que no toca el programa', readme_nuevo, True)
caso('falta el exe', sin_exe, False, 'no esta')
print('TODO OK' if not mal else f'{mal} MAL')
sys.exit(1 if mal else 0)
