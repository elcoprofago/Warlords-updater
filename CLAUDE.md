# Reglas de este repo

## Cada cambio queda en los registros del repo y en el Manual del parche «Era de Alianzas»

Pedido del usuario (11/11/2026): *«cada cambio debe verse reflejado en los registros del repo y en el manual del
parche "Alianzas"»*, porque la actualización del Manual no puede depender de la memoria de nadie.

- **Registros del repo:** el commit (mensaje con versión y qué cambió), `TAREAS.md` si hay algo que probar, y el
  `PENDIENTE-*.md` del tema si lo hay.
- **Manual** (`manual/manual.html`, se compila a `manual/Manual-Era-de-Alianzas.pdf` con
  `python manual\build_manual.py`; el PDF va dentro del parche vista-aliada):
  - toda versión nueva de vista-aliada agrega su fila **arriba** en el Apéndice E «Historial de versiones»;
  - si el cambio se ve en el juego, se explica además en su capítulo (y en Novedades, Referencia rápida o el
    Apéndice C de estado si corresponde).
- **Blindado en `hooks/pre-commit` (punto 6):** un commit que sube la VERSION de vista-aliada en
  `parches/parches.txt` se bloquea si `manual/manual.html` no tiene esa versión en el Apéndice E o si el PDF no
  está regenerado en el mismo commit. Lo que el hook no puede verificar (que el capítulo explique bien el cambio)
  queda a cargo de quien hace el cambio.
