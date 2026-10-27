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

## Paso 4: resultado (25/10/2026) — los perfiles no explican nada
Tandas 76 a 80 (Tanda_hex_control, Artificer + Devout en los seis): 25 partidas ok, 5 colgadas (76: 1, 79: 2, 80: 2).

| color    | serie 65-69: gana / PV / elim. | control 76-80: gana / PV / elim. |
|----------|--------------------------------|----------------------------------|
| blanco   | 11/30 · 22.9 · 0               | 8/25 · 23.8 · 0                  |
| amarillo | 18/30 · 28.3 · 0               | 17/25 · 30.8 · 0                 |
| rojo     | 0/30 · 3.9 · 6                 | 0/25 · 4.2 · 6                   |
| verde    | 0/30 · 2.9 · 11                | 0/25 · 1.7 · 12                  |
| azul     | 1/30 · 9.6 · 3                 | 0/25 · 9.6 · 0                   |
| negro    | 0/30 · 5.1 · 9                 | 0/25 · 6.1 · 5                   |

- Con el mismo perfil en todos, el reparto es casi idéntico al de la serie: 25 de 25 para blanco y amarillo. El
  desnivel no viene de los perfiles ni de su interacción: viene del lugar (vecinos, caminos) o del orden de turno.
- Consecuencia: la serie 65-69 no mide personalidades. Tanda_hex_control no sirve como «mapa parejo».

## Próximo paso
5'. Separar lugar de orden de turno sin tocar el arranque de turno (que no se puede rehacer, paso 2): en una copia de
   Tanda_hex_control, intercambiar con ciudades.dar() las 12 ciudades del amarillo con las del verde (y los ejércitos
   que estén en ellas), de modo que el amarillo juegue primero desde el lugar del verde. Probar primero en tope de
   2-3 turnos que carga y juega; después tanda de control de 30. Si el ganador sigue al color (amarillo), pesa el
   orden; si sigue al lugar, pesa la geografía/vecindad.

## Paso 5': preparado (25/10/2026)
- ia\intercambiar.py arma Tanda_hex_lugar_control (solo en SAVES del juego) = Tanda_hex_control con amarillo (1) y
  verde (4) intercambiados: dueño de sus ciudades (al empezar cada color tiene solo su capital; las demás son
  neutrales), capital del registro de jugador (+0xf2 y +0xf4, ambos = índice de la ciudad capital) y el ejército
  del amarillo (héroe + red_scav, registro 69) trasladado de (34,137) a (94,137). El verde no tenía ejércitos.
- Prueba (tanda 81, partida 495, de prueba, tope 3): carga y juega; los seis con héroe al turno 2; el verde ataca en
  el turno 3 en (44,128), junto a su capital nueva (Yellow Main, 33,137).
- Falta: que el usuario corra la tanda (TAREAS 44) y analizarla. Lectura: si el amarillo sigue ganando (~17/25) pesa
  el orden de turno; si gana el verde, pesa el lugar (abajo a la izquierda). Comparar con el control 76-80.

## Paso 5': resultado (26/10/2026) — el amarillo ganaba por el lugar
Tandas 82 a 86 (Tanda_hex_lugar_control): 30 partidas ok, ninguna colgada. Columnas: gana / PV / eliminado.

| color    | control 76-80 (25)  | amarillo y verde intercambiados (30) |
|----------|---------------------|--------------------------------------|
| blanco   | 8 · 23.8 · 0        | 17 · 24.5 · 0                        |
| amarillo | 17 · 30.8 · 0       | 1 · 7.0 · 6                          |
| rojo     | 0 · 4.2 · 6         | 0 · 3.6 · 9                          |
| verde    | 0 · 1.7 · 12        | 6 · 13.5 · 0                         |
| azul     | 0 · 9.6 · 0         | 5 · 12.4 · 0                         |
| negro    | 0 · 6.1 · 5         | 3 · 14.3 · 0                         |

- El amarillo, jugando segundo desde el lugar del verde, se hunde como el verde de antes (1 victoria, 6 veces
  eliminado). Su ventaja era el lugar, no el orden de turno.
- Pero el verde, desde el lugar del amarillo, no hereda toda la ventaja (6 de 30, no 17): el reparto se abrió (azul 5,
  negro 3) y el blanco se queda con más. El lugar pesa con quién tiene al lado: al dejar de estar fuerte abajo a la
  izquierda, los vecinos del amarillo (negro, rojo) cambian de suerte. Hipótesis sin verificar.
- El blanco sigue ganando con el amarillo fuera de juego. Falta saber si es su lugar o jugar primero.

## Paso 5'': blanco contra negro (preparado 26/10/2026)
- Tanda_hex_espejo_control = Tanda_hex_control con blanco (0) y negro (7) intercambiados (ia\intercambiar.py, sus
  lugares son espejo exacto). Prueba: tanda 87, partida 527, de prueba, tope 3: carga y juega; el negro ataca en el
  turno 3 en (109,76), junto a su capital nueva (White Main, 122,79).
- Falta: tanda del usuario (TAREAS 47). Si el blanco sigue ganando desde el lugar del negro, pesa jugar primero; si
  gana el negro, pesa el lugar. Después de esto, elegir cómo emparejar (paso 3) con los dos resultados.

## Paso 5'': resultado (27/10/2026) — manda el lugar del amarillo
Tandas 89 a 95 (Tanda_hex_espejo_control): 41 partidas ok (88 y la última de 90, cortadas). Gana / PV / eliminado.

| color    | control 76-80 (25)  | blanco y negro intercambiados (41) |
|----------|---------------------|------------------------------------|
| blanco   | 8 · 23.8 · 0        | 2 · 9.1 · 4                        |
| amarillo | 17 · 30.8 · 0       | 34 · 29.5 · 0                      |
| rojo     | 0 · 4.2 · 6         | 0 · 4.8 · 11                       |
| verde    | 0 · 1.7 · 12        | 1 · 8.1 · 1                        |
| azul     | 0 · 9.6 · 0         | 4 · 16.1 · 0                       |
| negro    | 0 · 6.1 · 5         | 0 · 9.9 · 3                        |

- Jugar primero no salva al blanco: desde el lugar del negro cae de 8 victorias a 2 y de 23.8 a 9.1 PV. Pesa el lugar.
- El negro, desde el lugar del blanco, sube de 6.1 a 9.9 PV pero no gana nunca: lo que el blanco perdió se lo llevó
  el amarillo (17/25 -> 34/41). El lugar del blanco solo valía como contrapeso del amarillo cuando lo ocupaba alguien
  que juega antes que él; jugando último (negro) ya no le alcanza. El orden pesa, pero menos que el lugar.
- Juntando 5' y 5'': el lugar de abajo a la izquierda (el del amarillo) es el fuerte; vale para quien lo ocupe si
  juega temprano (amarillo: 17/25 y 34/41; el verde, cuarto, solo 6/30). El rojo pierde siempre (vecino del
  amarillo, juega tercero).

## Próximo paso
3. Elegir cómo emparejar con estos resultados. El mapa es simétrico y los lugares no: la diferencia está en la
   vecindad y el orden de turno, que no se cambian editando ciudades. Opciones a evaluar: medir por qué el lugar del
   amarillo es fuerte (ciudades neutrales y caminos a 1-3 turnos, paso 2 original), o rotar los colores por lugar en
   cada partida para que cada perfil pase por todos los lugares y todos los órdenes.
Frase para retomar: "Seguimos con ia\PENDIENTE-mapa-pruebas.md, paso 3: elegir cómo emparejar".
