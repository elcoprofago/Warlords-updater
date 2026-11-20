# Army List marca en infracción armas que el Comparador aprueba (informe del usuario, 19/11/2026)

## Qué pasa

El reporte **Army List** (botón del libro, diálogo 111 de DarklordAV.exe) muestra algunas armas en infracción que el
**Comparador** (DarkCompare) da por aprobadas. Caso concreto: la **balsa** (Raft). Según el usuario, el que está
desactualizado es el juego, no el Comparador.

## Dónde mirar

- `parches/vista-aliada/build.py`, sección «Army List: unidades no permitidas por el validador» (~línea 1092): las
  reglas 1-25 están **copiadas** de DarklordsValidator a `parches/vista-aliada/reglas_ref.py` (poderes, habilidades,
  tablas `al_ptab`/`al_wtab`, `armcheck`). Si las reglas o la tabla de habilidades cambiaron después (por ejemplo, la
  habilidad nueva Raft/balsa), la copia quedó vieja.
- Comparar contra el código actual de DarklordsValidator / DarkCompare (RulesEngine.cs, Unit.cs, AbilityTable.cs,
  ParserUtils.cs) y ver qué regla dispara la balsa en el juego.

## Próximo paso

1. Sacar la lista de armas que Army List marca y DarkCompare aprueba (empezando por la balsa) y qué regla las marca.
2. Poner `reglas_ref.py` al día con el validador, recompilar, prueba de juguete, versión nueva, Manual, TAREAS.

## Resultado (19/11/2026): las reglas del juego están al día; la balsa marcada es la de la partida

- `prueba_reglas.py` (el `armeval` real del exe, emulado, contra `RulesEngine.Validate` de DarklordsValidator, que es
  el mismo motor que usa DarkCompare): **0 diferencias** en `E:\Warlords-TEST\Warlords3\ARMY` y en `C:\Warlords\ARMY`,
  más 2000 casos sintéticos. `reglas_ref.py` no quedó vieja; el validador no tiene regla propia para "Raft".
- La balsa del disco no viola nada: E: `raft`, Move 5, Cost 800, Upkeep 40; C: `raft`+`carrier`, Move 8, Cost 1200,
  Upkeep 40.
- Army List evalúa el `.ARM` del disco **solo si coincide con lo cargado**; si no, evalúa el registro que trae la
  partida (armcheck, `ac_mem`). `E:\...\SAVES\agua04.SAV` (19/11 19:10) lleva una balsa vieja: `raft`+`carrier`,
  Move 12, Cost 600, Upkeep 10 → viola la **regla 25** (carrier con Cost < 1200 o Upkeep < 34). Es la única copia
  de la balsa distinta del disco entre los 105 archivos de SAVES/NETSAVES de las dos carpetas.
- O sea: el Comparador juzga el `.ARM` actual; el juego juzga la balsa con la que se está jugando esa partida, que
  se armó antes de editar la balsa (14:37). Con una partida nueva, Army List ya no la marca.
- No hay nada que corregir en el parche. Queda cerrado.
