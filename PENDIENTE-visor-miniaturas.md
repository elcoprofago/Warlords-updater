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

## Hecho (vista-aliada 1.0.277.0, 19/11/2026) — falta la prueba del usuario (TAREAS 276)

- Casilla **View units** = control 76 del diálogo 86 (copia de «Mercenaries», en 470,46). `dc_init` la muestra y le
  pone el valor de `vw_on`; el evento 10 (0x44da1c, salto en 0x44da29 a `vw_check`) guarda el valor nuevo.
- La lista no es de Edit Side sino del selector que abren los «Change» (0x4027b0, diálogo 0x52 = RES 87, «Select an
  Army»): nombre de archivo = registro [0x5016d4] + fila [0x5016d0] * 48; filas [0x5016e4]; clase [0x5016dc]
  (5 = héroes). Al cambiar de fila (0x402963) se repinta el diálogo.
- Dibujo: el 5.º callback del selector (0x402c40, un `ret`) pasa a `vw_paint` (empujado en 0x40285c). Carga
  `ARMY\<nombre>.PCX` en una hoja temporal (carpeta 2; la carga pone la clave de color en el índice 11), arma una hoja
  en blanco de 100x100 con Blt de DirectDraw (relleno 199 de marco, 0 adentro, la celda (1,161) 48x48 estirada a 96x96
  con clave de color) y la pasa a la pantalla con 0x4e3c10 en (ancho - 108, 8). Libera las dos hojas.
- Prueba de juguete: `parches/vista-aliada/prueba_visor.py` (más los cambios en `prueba_botones.py`).

## Queda abierto

1. Si la figura queda pegada en pantalla al cerrar el selector (no hay repintado propio de esa zona): ver en la
   prueba 276; si pasa, guardar lo que había debajo y reponerlo al cerrar.
2. Héroes: están en `HERO\` con variantes f/m (`Cavalief`/`Cavaliem`) y archivos `.HER`; no se muestran todavía.
