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
