# Visor de miniaturas de armas en Edit Side (pedido del usuario, 19/11/2026)

## Qué pidió

En la ventana **Edit Side** del juego (DarklordAV.exe, diálogo 86), en el ángulo superior **derecho**, hoy vacío,
un botón o casilla «ver unidades». Activado, abre arriba a la derecha de la pantalla una ventanita que muestra la
**imagen de la unidad tal como se ve en el mapa**, de la que se elija en las **listas de armas de Edit Side**
(confirmado por el usuario: las listas de Edit Side, no Army List). Hoy al elegir una unidad solo se ven algunos datos.

## Lo que ya se sabe (de build.py)

- Edit Side = diálogo 86 (emergente 81, lo abre 0x44d320); controles 1 a 74; el botón del Comparador es el 75
  (`DC_BTN`, arriba a la izquierda, 46,46, 51x51). El nuevo control sería el 76.
- Alta de los controles: 0x44dc00..0x44dd53 (`dc_init` muestra el botón con 0x4dcec0 + 0x4d7f60).
- Clics: 0x44d3a0, evento 3 en 0x44d3e7 (edx = control; fuera de 2..73 cae en 0x44db1c). `dc_click` es el modelo.
- Botón con dibujo propio: copia de Chat del diálogo 7 + hoja PCX en `SETS\Fantasy` (ver `DC_FILE`, líneas ~26577
  y ~26769 de build.py). El aro de «puntero encima» ya quedó resuelto (TAREAS 274/275).
- Retratos de unidad: imagen 46 de lightinf; el ariete orco agrega `ARMY\orcs_ram.pcx` en WAR3AV.RES (~6164, ~26655).

## Falta averiguar (en este orden)

1. Qué control de Edit Side es cada lista de armas y qué evento llega al elegir una fila (y de dónde sacar el
   índice de tipo de arma de la fila elegida).
2. Qué función dibuja la figura de mapa de un tipo de arma (la que usa el tablero o Army List) y con qué paleta.
3. Cómo dibujar la ventanita: un panel propio dentro del diálogo 86 (más simple; un control «Chat» más que se
   repinta) o una superficie aparte arriba a la derecha de la pantalla.
4. El botón/casilla «ver unidades» en el ángulo superior derecho (control 76), alterna mostrar/ocultar.

## Al terminar

Versión nueva de vista-aliada, fila en el Apéndice E del Manual y explicación en el capítulo del editor, prueba
en TAREAS.md.
