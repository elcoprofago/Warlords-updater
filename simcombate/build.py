# Empaqueta el Simulador de combate en simcombate\Simulador-Combate.exe (el .ini lo guarda junto a sí).
# Uso: python simcombate\build.py
import os, subprocess, sys, tempfile
import pefile

AQUI = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(AQUI), 'ia', 'monitor-ia', 'assets')   # ícono de configuración del Monitor de IA
EXE = os.path.join(AQUI, 'Simulador-Combate.exe')


def sin_cfg(exe):
    """Apaga Control Flow Guard en el cargador de PyInstaller. Unicorn ejecuta código que genera en memoria; con CFG
    Windows corta el proceso (0xC0000409) en la primera pelea. python.exe no trae CFG, por eso desde el código anda."""
    pe = pefile.PE(exe)
    pe.OPTIONAL_HEADER.DllCharacteristics &= ~0x4000   # IMAGE_DLLCHARACTERISTICS_GUARD_CF
    pe.OPTIONAL_HEADER.CheckSum = pe.generate_checksum()
    datos = pe.write(); pe.close()                       # incluye el archivo de PyInstaller pegado al final
    with open(exe, 'wb') as f: f.write(datos)


def tiene_cfg(exe):
    pe = pefile.PE(exe, fast_load=True); v = bool(pe.OPTIONAL_HEADER.DllCharacteristics & 0x4000); pe.close()
    return v


if __name__ == '__main__':
    tmp = tempfile.mkdtemp(prefix='simcombate-')
    r = subprocess.run([sys.executable, '-m', 'PyInstaller', '--onefile', '--windowed', '--noconfirm',
                        '--name', 'Simulador-Combate', '--distpath', AQUI, '--workpath', tmp, '--specpath', tmp,
                        '--paths', AQUI, '--add-data', ASSETS + os.pathsep + 'assets', '--collect-all', 'unicorn',
                        '--icon', os.path.join(AQUI, 'icono.ico'), '--add-data', os.path.join(AQUI, 'icono.png') + os.pathsep + '.',
                        os.path.join(AQUI, 'tablero.py')])
    if r.returncode: sys.exit(r.returncode)
    sin_cfg(EXE)
    if tiene_cfg(EXE): sys.exit('No se pudo apagar CFG en el .exe: el motor no funcionaría.')
    print('CFG apagado en', EXE)
