# Arma el anexo «Cómo juega la computadora» en PDF: convierte anexo.html a manual\Anexo-IA.pdf con Edge sin ventana.
# Usa manual\img\titulo.png, que genera manual\build_manual.py.
# Uso: python manual\anexo-ia\build.py
import os, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
MANUAL = os.path.dirname(AQUI)
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'

if not os.path.exists(os.path.join(MANUAL, 'img', 'titulo.png')):
    sys.exit('Falta manual\\img\\titulo.png: correr antes python manual\\build_manual.py')
pdf = os.path.join(MANUAL, 'Anexo-IA.pdf')
html = 'file:///' + os.path.join(AQUI, 'anexo.html').replace('\\', '/')
r = subprocess.run([EDGE, '--headless', '--disable-gpu', '--no-pdf-header-footer', f'--print-to-pdf={pdf}', html],
                   capture_output=True, text=True, timeout=120)
if r.returncode != 0 or not os.path.exists(pdf):
    sys.exit(f'Edge no generó el PDF (código {r.returncode}): {r.stderr}')
print(pdf, os.path.getsize(pdf), 'bytes')
