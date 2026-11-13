"""Prueba del Historial (40 combates) y de las imágenes de Stats y ficha: python prueba_imagenes.py"""
import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import imagenes, historial, tempfile, os.path
out = tempfile.mkdtemp()
L = lambda x, n=3, heroe=None: dict(tropas=[[x, n]], barco=None, heroe=heroe)
mk = lambda k, a, d, pct: dict(numero=k, fecha='13/11/2026 10:00:00', campo='hills · Nada', A=a, D=d, pct=pct, n=1000, gana=pct>=50, orden_a=[], orden_d=[], muertes=[], avisos=[])
h = [mk(1, L('Elves'), L('Orcs'), 80), mk(2, L('Elves'), L('Orcs'), 70), mk(3, L('Dwarves'), L('Orcs', 5, 'Warrior nivel 3'), 20), mk(4, L('Elves'), L('Wolves'), 60)]
fo = imagenes.formaciones(h); print(fo)
assert fo[0][:2] == ('3 Elves', 3) and fo[1][1] == 1
imagenes.guardar(imagenes.imagen_torta(h, 'X'), out + '/torta.png')
imagenes.guardar(imagenes.imagen_ficha(h[2], 'X'), out + '/ficha.jpg')
imagenes.imagen_torta([], 'X').save(out + '/vacia.png')
r = os.path.join(tempfile.mkdtemp(), 'h.json')
for i in range(50): historial.guardar(r, mk(i, L('A'), L('B'), 60))
hh = historial.cargar(r); assert len(hh) == 40 and hh[0]['numero'] == 49, len(hh)
print('TODO OK')
