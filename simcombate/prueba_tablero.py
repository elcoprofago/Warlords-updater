# Prueba del tablero: «Invertir» cambia de lado todo lo ingresado y «Ordenar por NOMBRE COMÚN» reordena las listas
# conservando lo elegido; arrastrar una fila la lleva a otra posición. Uso: python prueba_tablero.py (abre la ventana unos segundos; usa C:\Warlords3)
import os, tempfile
import tablero
tablero.CONFIG = os.path.join(tempfile.gettempdir(), 'prueba-simcombate.ini')   # no tocar el .ini real
app = tablero.App()
res = []
def armar():
    if not app.sim: app.after(500, armar); return
    pa, pd = app.pa, app.pd
    pa.armas[0].set(pa.rotulo['gnollcav.arm']); pa.cant[0].set(3)
    pa.armas[1].set(pa.rotulo['archons.arm']); pa.cant[1].set(2); pa.recalcular()
    pd.armas[0].set(pd.rotulo['amewyrm.arm']); pd.cant[0].set(1); pd.recalcular()
    antes = (pa.lado(), pd.lado())
    app.invertir()
    res.append(pa.lado() == antes[1] and pd.lado() == antes[0])
    app.por_nombre.set(True); app.reordenar()
    res.append(pd.lado() == antes[0] and pd.armas[0].get().startswith(app.sim.armas['gnollcav.arm'].nombre))
    vals = list(pd.armas[0]['values'])[1:]
    res.append(vals == sorted(vals, key=lambda t: (app.sim.armas[pd.nombres[t]].nombre.lower(), pd.nombres[t])))
    t = pd.lado()['tropas']; pd.mover_fila(1, 0)       # arrastrar la fila 2 arriba de la 1
    t2 = pd.lado()['tropas']; pd.mover_fila(0, 2)       # y la 1 a la 3: las del medio se corren
    res.append(t2[:2] == [t[1], t[0]] and pd.lado()['tropas'][:3] == [t2[1], t2[2], t2[0]])
    for ok, m in zip(res, ('Invertir cambia los dos lados', 'reordenar conserva lo elegido', 'orden por nombre común',
                           'arrastrar filas cambia el orden')):
        print('OK  ' if ok else 'MAL ', m)
    print('TODO OK' if all(res) else 'HAY MAL')
    app.destroy()
app.after(500, armar); app.mainloop()
