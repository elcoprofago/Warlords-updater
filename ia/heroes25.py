"""Héroes del 25th Anniversary Project en el banco de pruebas (ia\\PENDIENTE-ideas-moddb.md, Paso 2).

    python ia\\heroes25.py estado      qué héroes y hechizos hay en C:\\Warlords3
    python ia\\heroes25.py 25th        pone los 15 héroes del 25th y los hechizos propios que piden
    python ia\\heroes25.py original    vuelve a los héroes de HERO\\back y quita esos hechizos

Los héroes del 25th piden 42 hechizos que no existen en nuestro juego (25mason, 25pets...): sin ellos el héroe queda
con casilleros que apuntan a nada. Las tropas que esos hechizos invocan ya existen. HERO\\back es la copia que hizo el
usuario de los héroes originales: este script solo la lee. Solo se quitan los hechizos idénticos a los del 25th.
--juego <carpeta> cambia la carpeta (para la prueba en una carpeta de juguete).
"""
import os
import re
import shutil
import sys

MOD = r'F:\source\repos\Mods\25th Anniversary Project'
JUEGO = r'C:\Warlords3'


def leer(p):
    with open(p, 'rb') as f:
        return f.read()


def por_nombre(carpeta, ext):
    """{nombre en minúsculas: nombre real} de los archivos .ext de la carpeta."""
    return {f.lower(): f for f in os.listdir(carpeta) if f.lower().endswith(ext)}


def hechizos_pedidos(heroes_dir, nombres, mod_spl):
    """Hechizos del 25th que nombran los héroes (por sus textos de 3+ letras)."""
    pide = set()
    for h in nombres:
        for s in re.findall(rb'[ -~]{3,}', leer(os.path.join(heroes_dir, h))):
            k = s.decode().lower() + '.spl'
            if k in mod_spl:
                pide.add(k)
    return pide


def main(argv):
    juego = JUEGO
    if '--juego' in argv:
        i = argv.index('--juego'); juego = argv[i + 1]; del argv[i:i + 2]
    modo = argv[1] if len(argv) > 1 else 'estado'
    hero, back, spell = (os.path.join(juego, x) for x in ('HERO', os.path.join('HERO', 'back'), 'SPELL'))
    mh = por_nombre(os.path.join(MOD, 'HERO'), '.her')
    ms = por_nombre(os.path.join(MOD, 'SPELL'), '.spl')
    bk = por_nombre(back, '.her') if os.path.isdir(back) else {}
    faltan = sorted(set(mh) - set(bk))
    if faltan:
        sys.exit(f'HERO\\back no tiene el original de: {", ".join(faltan)}. No se toca nada.')
    pide = hechizos_pedidos(os.path.join(MOD, 'HERO'), mh.values(), ms)
    js = por_nombre(spell, '.spl')
    pisaria = [k for k in pide if k in js and leer(os.path.join(spell, js[k])) != leer(os.path.join(MOD, 'SPELL', ms[k]))]
    if pisaria:
        sys.exit(f'Ya hay hechizos distintos con el nombre de los del 25th: {", ".join(sorted(pisaria))}. No se toca nada.')

    if modo == '25th':
        for k, f in mh.items():
            shutil.copyfile(os.path.join(MOD, 'HERO', f), os.path.join(hero, f))
        for k in pide:
            shutil.copyfile(os.path.join(MOD, 'SPELL', ms[k]), os.path.join(spell, ms[k]))
    elif modo == 'original':
        for k, f in bk.items():
            if k in mh:
                shutil.copyfile(os.path.join(back, f), os.path.join(hero, f))
        for k in pide:
            if k in js:
                os.remove(os.path.join(spell, js[k]))
    elif modo != 'estado':
        sys.exit(__doc__)

    # Verificación: se mide lo que quedó en disco, no lo que se intentó.
    jh, js = por_nombre(hero, '.her'), por_nombre(spell, '.spl')
    es = lambda k, ref: k in jh and leer(os.path.join(hero, jh[k])) == leer(ref)
    n25 = sum(es(k, os.path.join(MOD, 'HERO', f)) for k, f in mh.items())
    nor = sum(es(k, os.path.join(back, bk[k])) for k in mh)
    nsp = sum(k in js for k in pide)
    print(f'{juego}: héroes del 25th {n25}/{len(mh)}, originales {nor}/{len(mh)}, hechizos del 25th {nsp}/{len(pide)}')
    bien = {'25th': n25 == len(mh) and nsp == len(pide), 'original': nor == len(mh) and nsp == 0}
    if modo in bien:
        print('OK' if bien[modo] else 'ERROR: no quedó como se pidió')
        return 0 if bien[modo] else 1
    estado = [m for m, ok in bien.items() if ok]
    print('Estado:', estado[0] if estado else 'MEZCLADO (correr 25th u original)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
