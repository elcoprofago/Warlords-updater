# Empaqueta el Visor de historia en ia\Visor-Historia.exe. El arte y los textos los toma del juego al abrir un .SAV.
# Uso: python ia\visor-historia\build.py
import os, subprocess, sys, tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
IA = os.path.dirname(AQUI)
tmp = tempfile.mkdtemp(prefix='visor-historia-')
r = subprocess.run([sys.executable, '-m', 'PyInstaller', '--onefile', '--windowed', '--noconfirm',
                    '--name', 'Visor-Historia', '--distpath', IA, '--workpath', tmp, '--specpath', tmp,
                    '--paths', IA, os.path.join(AQUI, 'visor_historia.py')])
sys.exit(r.returncode)
