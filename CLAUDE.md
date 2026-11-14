# Reglas de este repo

## Cada cambio queda en los registros del repo y en el Manual del parche «Era de Alianzas»

Pedido del usuario (11/11/2026): *«cada cambio debe verse reflejado en los registros del repo y en el manual del
parche "Alianzas"»*, porque la actualización del Manual no puede depender de la memoria de nadie.

- **Registros del repo** (confirmado por el usuario el 11/11/2026): el commit (mensaje con versión y qué cambió),
  el `PENDIENTE-*.md` del tema, la hoja de ruta (roadmap) si la hay, `TAREAS.md` si hay algo que probar, y toda
  otra anotación del repo que hable de lo que cambió: se actualiza en el mismo commit, no después.
- **Manual** (`manual/manual.html`, se compila a `manual/Manual-Era-de-Alianzas.pdf` con
  `python manual\build_manual.py`; el PDF va dentro del parche vista-aliada):
  - toda versión nueva de vista-aliada agrega su fila **arriba** en el Apéndice E «Historial de versiones»;
  - si el cambio se ve en el juego, se explica además en su capítulo (y en Novedades, Referencia rápida o el
    Apéndice C de estado si corresponde).
- **Blindado en `hooks/pre-commit` (punto 6):** un commit que sube la VERSION de vista-aliada en
  `parches/parches.txt` se bloquea si `manual/manual.html` no tiene esa versión en el Apéndice E o si el PDF no
  está regenerado en el mismo commit. Lo que el hook no puede verificar (que el capítulo explique bien el cambio)
  queda a cargo de quien hace el cambio.

## Todo avance genuino de la IA pasa enseguida a las partidas del ranking

Pedido del usuario (13/11/2026): *«cada avance genuino que logremos con la IA inmediatamente sea incorporado a la ia
del ranking multijugador, salvo que sea imprescindible hacer más tandas de pruebas en el banco.»*

- Sin `DATA\IA.INI` (las partidas reales, en `C:\Warlords`), los bandos de la computadora juegan con la IA de prueba,
  no con la original. `IA.INI` solo decide qué colores son original o prueba durante una tanda y activa los registros
  (IA.CSV, eventos, IA_FIN.CSV).
- Cuando una tanda confirma una mejora, queda activa también sin IA.INI en la misma versión o en la siguiente. Una
  destreza que todavía necesita tandas (o que empeoró algo) queda solo para los colores en prueba, y su
  `PENDIENTE-*.md` dice por qué.
- Recordar en `TAREAS.md` actualizar `C:\Warlords` cuando el cambio tiene que llegar a las partidas del ranking.
