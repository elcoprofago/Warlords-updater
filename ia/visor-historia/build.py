# Empaqueta el Visor de historia en ia\Visor-Historia.exe. El arte y los textos los toma del juego al abrir un .SAV;
# la ruedita de configuración y las luces van adentro, tomada de ia\monitor-ia\assets.
# Uso: python ia\visor-historia\build.py
import os, subprocess, sys, tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
IA = os.path.dirname(AQUI)
tmp = tempfile.mkdtemp(prefix='visor-historia-')
r = subprocess.run([sys.executable, '-m', 'PyInstaller', '--onefile', '--windowed', '--noconfirm',
                    '--name', 'Visor-Historia', '--distpath', IA, '--workpath', tmp, '--specpath', tmp,
                    '--paths', IA, *[a for n in ('menu_settings_*.png', 'marco.png', 'circle_09.png') for a in
                      ('--add-data', os.path.join(IA, 'monitor-ia', 'assets', n) + os.pathsep + 'assets')],
                    os.path.join(AQUI, 'visor_historia.py')])
sys.exit(r.returncode)
