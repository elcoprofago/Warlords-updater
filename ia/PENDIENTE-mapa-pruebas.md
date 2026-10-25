# Mapa de pruebas («probeta») para tandas de IA (pedido del usuario, 25/10/2026)

## Objetivo
Un mapa donde todos los lugares de salida sean equivalentes, para que en una tanda la única diferencia entre los
colores sea lo que se quiere medir (personalidad, PGS, IA). Va a servir para todas las tandas futuras, no solo las de
personalidad. Primer uso: repetir la serie de personalidades (TAREAS 41) para confirmar la ventaja de Artificer +
Devout y separar los otros cinco perfiles.

## Por qué hace falta
En la serie de personalidades (tandas 65 a 69, 30 partidas, Tanda_hex_perfiles_SR) ganaron 29 de 30 los que
arrancaron en el lugar amarillo o en el blanco. Los lugares negro, rojo y verde no ganaron nunca (el verde quedó
eliminado 11 veces de 30). Con la rotación cada perfil pasa por todos los lugares, pero solo dos de ellos permiten
ganar, así que cada perfil tiene en la práctica 10 oportunidades, no 30. Detalle en PENDIENTE-entrenamiento-ia.md
(«Ronda nueva: personalidades»).
- El desnivel no viene del oro inicial: amarillo y blanco arrancan con el **menor** oro (64); rojo con 119; verde,
  azul y negro con 244. ~~Viene de la geografía~~: el paso 1 mostró que el mapa es simétrico (ver abajo); la
  diferencia está en el estado en que quedó guardada la partida.

## Lo que ya se sabe y sirve
- La guardada se edita desde código: tanda.SAV_BLOQUES traduce direcciones de memoria a posiciones del .SAV
  (ver offset() en sin_ruinas.py). Ruinas: tabla 0x558872/0x558874, registros de 0xb8. Jugadores: 0x536b30 +
  color*0x1f8 (personalidades en +0xc0..0xc2, diplomacia en +0xe2..).
- escribir_rotada (Monitor 1.0.15+) ya reescribe perfiles y diplomacia antes de cada partida: el mapa parejo puede
  armarse con el mismo mecanismo (una _SR nueva, sin tocar la original).
- Hexagon solo admite 6 colores (blanco, amarillo, rojo, verde, azul, negro); Scarpart, Borderlands y Kor admiten 8.

## Pasos
1. **Hecho (25/10/2026, ver «Paso 1: resultado»).** Ubicar en el .SAV/exe la tabla de ciudades (dueño, posición, producción, ingreso, defensa) y el terreno.
   Probarlo primero en un caso de juguete (cambiar el dueño de una ciudad y ver el resultado en el juego).
2. Medir el desnivel de Hexagon por lugar: ciudades e ingreso a 1, 2 y 3 turnos de marcha de cada capital.
3. Elegir el método para emparejar: lo más simple que alcance (por ejemplo, igualar el ingreso y la defensa de las
   ciudades por anillo alrededor de cada capital). Si no alcanza, armar un mapa simétrico.
4. Validar el mapa con una tanda de control: el mismo perfil en todos los colores, 30 partidas. Queda parejo si
   ningún lugar se aparta claramente del promedio (hoy: amarillo 28.3 PV, verde 2.9).
5. Recién entonces repetir la serie de personalidades sobre el mapa nuevo (tarea nueva en TAREAS.md).

## Paso 1: resultado (25/10/2026)
- Tabla de ciudades: ia\ciudades.py (lee la tabla de una guardada y `dar()` cambia el dueño). Registro 0x537e2c +
  i*0xde, cantidad [0x537e2a]: +0 x, +2 y, +4 nombre, +0xa4 tamaño, +0xa5 dueño (8 neutral), +0xa7 ingreso,
  +0xaa cuatro tropas producibles (9 letras cada una). Sin identificar: +0xa6, +0xa8, +0xa9, +0xce..+0xdd.
- Terreno: bloque 0x503e58 del .SAV (0x32000 bytes) = 128 x 160 casillas de 10 bytes. Dibujado con el byte +1 se
  ve el hexágono con simetría izquierda-derecha y arriba-abajo. Significado de cada byte sin averiguar (no hizo falta).
- Prueba de juguete (tanda 70, partida 448, de prueba): Tanda_juguete.SAV = Tanda_hex_perfiles_SR con Green Secret,
  Shopping y Door del verde. En el juego el verde arrancó con 4 ciudades y azul y negro (control) con 1. Editar la
  tabla funciona.
- **Hexagon ya es parejo de diseño**: cada color tiene las mismas 12 ciudades (Main, Secret, Door, Shopping, Haven,
  Chest, Outpost, Hole, Corner, Gate, Ambassy, Center) con el mismo tamaño, ingreso y tropas, en lugares simétricos.
  Blanco (122,79) y negro (4,79) son espejo exacto, y blanco ganó casi siempre y negro nunca.
- Lo que sí distingue a los lugares, en la guardada:
  - Se guardó **a mitad del turno 1**, con el rojo jugando ([0x537ce8] = 3): blanco y amarillo ya jugaron su turno 1
    (tienen héroe y compraron la tropa red_scav, de ahí el oro 64), rojo compró bladerun (119) y verde, azul y negro
    todavía no jugaron (244, sin ejércitos). Lo confirmó la prueba: en el turno 1 solo registran verde, azul y negro.
  - El orden de turno es fijo por color (blanco, amarillo, rojo, verde, azul, negro).
  - Green Main tiene +0xa6 = 1; las otras capitales, 3 (campo sin identificar).
  Sin verificar cuál de estas causas pesa. Hipótesis principal: la tropa red_scav ya comprada y el arranque antes que
  los demás.

## Próximo paso del paso 1 (superado: ver «Paso 2: resultado»)
2. Armar la guardada pareja desde Tanda_hex_perfiles_SR: dejar las seis capitales iguales (mismas tropas, +0xa6 y
   +0xce..+0xdd, sin red_scav ni bladerun), el oro en 244 y, si se puede, la partida al principio del turno 1 sin
   que nadie haya jugado. Si esto último no se logra editando, guardar una partida nueva de Hexagon antes de mover.
3. Con eso, el paso 4 (tanda de control) dice si alcanza; el orden de turno no se puede igualar y ahí se mide cuánto
   pesa.
## Paso 2: resultado (25/10/2026) — la guardada no se puede emparejar editándola, y no hace falta
Tandas de prueba 71 a 75 (partidas 449 a 463, de juguete, tope 1-3 turnos; no cuentan para ningún análisis). Script
de prueba descartado (no quedó en el repo); las guardadas de prueba se borraron.
- Lo que se probó, un cambio por guardada (bisección contra Tanda_hex_perfiles_SR):
  - capitales copiadas de la del negro (+0xa6..+0xdd): carga y juega;
  - oro de todos en 244: carga y juega;
  - quitar los 3 ejércitos de jugadores (registros 68-70 de 0x54fe52 + i*0x1c, cantidad [0x54fe50] 71 -> 68; +9 =
    0xff en los de jugador, dueño en los bits 5-8 de la palabra +0xc, 0x10 = héroe): carga y juega;
  - cambiar [0x537ce8] (3 -> 0) o el control del rojo (+0xe2, 0xffff -> 2): **se cuelga al cargar**, cada uno solo.
    Moviendo los dos juntos (control 0xffff al color de [0x537ce8]) carga.
- **El rojo es el humano**: control 0xffff y [0x537ce8] = 3 en todas las guardadas de tanda (Tanda_Kor, Scarpart y
  hasta 0001). El usuario arma las guardadas jugando con el rojo; blanco y amarillo (computadora) ya jugaron su turno 1
  al guardar. La tanda pasa el rojo a la IA al cargar.
- Con todo junto (y también con el turno de la cabecera, +0x50, en 0 y el negro como color en juego) el juego retoma
  el turno 1 **después del rojo**: verde, azul y negro arrancan su turno (héroe, compra); blanco, amarillo y rojo no
  vuelven a tener arranque de turno 1, quedan sin héroe 2-3 turnos y juntan oro sin comprar. Quedó **más** desparejo.
  El arranque de turno no se puede rehacer editando.
- Y la guardada original ya era pareja en lo que importa: en la partida 448 los seis colores salen del turno 1 con un
  héroe y una compra (oro al empezar el turno 2: blanco 64, amarillo 64, rojo 119, verde 69/144, azul 114, negro 64).
  Lo de «blanco y amarillo ya jugaron» no es ventaja: los demás juegan el mismo turno 1 enseguida.
- Conclusión: ni el mapa (paso 1) ni el estado de la guardada explican que blanco y amarillo ganen 29 de 30. Queda el
  orden de turno, el azar de cada partida y la interacción con los perfiles.

## Próximo paso (reemplaza al anterior)
4. Tanda de control directamente sobre Tanda_hex_perfiles_SR: **el mismo perfil en los seis colores**, 30 partidas.
   Hace falta una opción en tanda.py para escribir un solo perfil en todos (hoy escribir_rotada solo rota). Si la
   ventaja de blanco y amarillo sigue, viene del orden de turno o de la IA, no de los perfiles; si desaparece, el
   desnivel de la serie 65-69 es interacción entre perfiles vecinos.

## Paso 4: preparado (25/10/2026)
- Guardada **Tanda_hex_control** (solo en SAVES del juego, como las demás): Tanda_hex_perfiles_SR con Artificer +
  Devout (el perfil del negro) en los seis colores; nada más cambiado.
- tanda.py: una guardada con «_control» en el nombre (es_control) juega sola con la IA original en todos, cada color
  con su propio perfil, y escribir_rotada solo quita las alianzas. Probado: plan de 30, IA_ROTADA con los seis
  perfiles iguales y «sin alianzas»; la de perfiles sigue rotando. Monitor de IA 1.0.17 la marca «(control)».
- Falta: que el usuario corra la tanda (TAREAS 43) y analizarla: victorias y PV promedio por color contra la serie
  65-69 (amarillo 28.3 PV, verde 2.9).
Frase para retomar: "Seguimos con ia\PENDIENTE-mapa-pruebas.md, paso 4: analizar la tanda de control".
