# Empaqueta el Monitor de IA en ia\Monitor-IA.exe (junto a datos.db y tanda.ini, que busca en su propia carpeta).
# Uso: python ia\monitor-ia\build.py
import os, subprocess, sys, tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
IA = os.path.dirname(AQUI)
tmp = tempfile.mkdtemp(prefix='monitor-ia-')
r = subprocess.run([sys.executable, '-m', 'PyInstaller', '--onefile', '--windowed', '--noconfirm',
                    '--name', 'Monitor-IA', '--distpath', IA, '--workpath', tmp, '--specpath', tmp,
                    '--paths', IA, '--add-data', os.path.join(AQUI, 'assets') + os.pathsep + 'assets', '--hidden-import', 'pycaw.pycaw', '--collect-submodules', 'comtypes',
                    os.path.join(AQUI, 'monitor_ia.py')])
sys.exit(r.returncode)
