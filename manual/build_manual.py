# Arma el Manual de uso en PDF: saca las ilustraciones de los archivos del juego y del repo, y convierte
# manual.html a Manual-Era-de-Alianzas.pdf con Edge sin ventana (--print-to-pdf).
# Uso: python manual\build_manual.py
import os, subprocess, sys
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(AQUI)
IMG = os.path.join(AQUI, 'img')
POZOS = r'C:\Warlords3\RUINS\pozos.pcx'
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
CUADRO = 48
REMO0 = 13   # PO_REMO0 de parches\vista-aliada\build.py: 4 fases x 9 piezas
os.makedirs(IMG, exist_ok=True)


def transparente(im):
    im = im.convert('RGBA')
    im.putdata([(0, 0, 0, 0) if p[:3] == (255, 0, 255) else p for p in im.getdata()])
    return im


def cuadro(hoja, n):
    return hoja.crop((n * CUADRO, 0, (n + 1) * CUADRO, CUADRO))


hoja = transparente(Image.open(POZOS))
for nombre, n in (('pozo', 0), ('mina', 5), ('humo', 6), ('tumba', 11), ('mina-agua', hoja.width // CUADRO - 1)):
    cuadro(hoja, n).resize((96, 96), Image.NEAREST).save(os.path.join(IMG, nombre + '.png'))
remo = Image.new('RGBA', (3 * CUADRO, 3 * CUADRO))
for k in range(9):
    remo.paste(cuadro(hoja, REMO0 + k), (k % 3 * CUADRO, k // 3 * CUADRO))
remo.resize((288, 288), Image.NEAREST).save(os.path.join(IMG, 'remolino.png'))
transparente(Image.open(os.path.join(REPO, 'parches', 'vista-aliada', 'titulo.pcx'))).save(os.path.join(IMG, 'titulo.png'))
for n in ('sorteo_icono', 'comparador_icono'):
    Image.open(os.path.join(REPO, 'parches', 'vista-aliada', n + '.png')).save(os.path.join(IMG, n + '.png'))

pdf = os.path.join(AQUI, 'Manual-Era-de-Alianzas.pdf')
html = 'file:///' + os.path.join(AQUI, 'manual.html').replace('\\', '/')
# Perfil propio: con Edge abierto, el modo sin ventana le pasa el pedido a esa instancia y no escribe el PDF.
perfil = os.path.join(os.environ['TEMP'], 'build_manual_edge')
antes = os.path.getmtime(pdf) if os.path.exists(pdf) else 0
r = subprocess.run([EDGE, '--headless', '--disable-gpu', '--no-pdf-header-footer', f'--user-data-dir={perfil}',
                    f'--print-to-pdf={pdf}', html], capture_output=True, text=True, timeout=120)
if r.returncode != 0 or not os.path.exists(pdf) or os.path.getmtime(pdf) <= antes:
    sys.exit(f'Edge no generó el PDF (código {r.returncode}): {r.stderr}')
print(pdf, os.path.getsize(pdf), 'bytes')
