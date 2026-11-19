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

## Antes de subir la versión de un parche, mirar si otra sesión ya la subió

Puede haber varias sesiones trabajando a la vez en este repo y en el mismo parche. Antes de subir la VERSION en
`parches/parches.txt`, releer ese archivo y `git log -3`: si otra sesión ya subió la versión, tomar la siguiente
libre (y lo mismo para la fila del Apéndice E del Manual). Si `DarklordAV.exe` u otro archivo instalado en
`E:\Warlords-TEST\Warlords3` aparece bloqueado sin que el juego esté abierto, lo más probable es que otra sesión
esté compilando: esperar a que termine, no forzar.

Caso que lo originó (19/11/2026): la estrella del marcador se iba a publicar como 1.0.266.0 mientras otra sesión
publicaba 1.0.266.0 (balsas) y 1.0.267.0 (montañas); el ejecutable estuvo bloqueado por esa compilación. Se
publicó como 1.0.268.0. Pedido del usuario: «Sí, agregá la regla».

## Vocabulario: MURALLA y MURO (definido por el usuario, 19/11/2026)

- **MURALLA:** la construcción del parche (obra OB_MURO, la que levanta una unidad con «build»). Solo la atraviesan
  las unidades terrestres del dueño y sus aliados (por la puerta) y **todos los voladores**.
- **MURO:** el terreno del escenario que no atraviesa nadie, ni por aire (terreno «Walls», clase 5; lo tiene Hexagon
  alrededor de los núcleos y en el borde, y quizás otros escenarios editados). Igual que las montañas altas.
- No mezclarlos: en notas, código y chat, «muralla» es lo que se construye y «muro» lo del escenario.
