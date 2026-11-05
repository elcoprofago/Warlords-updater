# Empaqueta el Simulador de combate en simcombate\Simulador-Combate.exe (el .ini lo guarda junto a sí).
# Uso: python simcombate\build.py
import os, subprocess, sys, tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(AQUI), 'ia', 'monitor-ia', 'assets')   # ícono de configuración del Monitor de IA
tmp = tempfile.mkdtemp(prefix='simcombate-')
r = subprocess.run([sys.executable, '-m', 'PyInstaller', '--onefile', '--windowed', '--noconfirm',
                    '--name', 'Simulador-Combate', '--distpath', AQUI, '--workpath', tmp, '--specpath', tmp,
                    '--paths', AQUI, '--add-data', ASSETS + os.pathsep + 'assets', '--collect-all', 'unicorn',
                    os.path.join(AQUI, 'tablero.py')])
sys.exit(r.returncode)
