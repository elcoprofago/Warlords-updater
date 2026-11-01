# Visor de historia de partidas (.SAV)

Pedido del usuario (1/11/2026): una app que abra una partida guardada y muestre su "Events Report" tal como lo
muestra el juego, con línea de tiempo deslizante, búsqueda y exportación a PDF/texto con el nombre de la partida.

## Lo averiguado (por lectura del código ya documentado; nada probado todavía sobre un .SAV real)

Fuente: `parches\vista-aliada\PENDIENTE-mision-puentes-y-botones.md`, parte E, y `parches\vista-aliada\build.py`
(bloque `vt_*`, ~línea 6860).

- El .SAV lleva adentro una copia de `HISTORY.DAT` y la tabla de la ronda en curso (lo escribe 0x439a00 del Darklord.exe).
- `HISTORY.DAT`: un bloque por ronda. Cabecera de 0x48 (+0 tamaño del bloque, +0x44 cantidad de renglones), los
  dueños de las ciudades en esa ronda y los renglones.
- Renglón de 0x1c: +0 tipo (también es la prioridad, 0..0x12; 0x13 = votación de vista-aliada), +2 jugador,
  +4 parámetro, +6 nombre[16], +0x16/+0x18/+0x1a tres words.
- Ronda en curso: tabla 0x572788 (8 jugadores x 2 renglones). Con vista-aliada, al final del .SAV va además
  'VOTA', cantidad, tabla.
- El informe lo arma 0x499450 y lo dibuja 0x4b3ec0 (hasta 11 renglones por ronda; la ronda 1, nada). El texto de
  cada renglón sale de 0x4b4110: escudo del jugador y un `switch` por tipo.
- Límite del juego: por ronda quedan solo los 2 sucesos de mayor tipo por jugador. La app no puede mostrar más que eso.
- Tabla de ciudades del .SAV: `ia\ciudades.py` (sirve para los nombres de ciudad y para el mapa por ronda).
- Lectura de offsets del .SAV: `ia\sin_ruinas.py` (`offset`).

## Lo que pidió que muestre la app

a) Panel superior: botón "Abrir", nombre de la partida, turnos jugados, condición de victoria, tipo de mapa
   (aleatorio, "Crusade", etc.), fecha de inicio y fecha de finalización.
b) Panel principal: el cuadro de eventos igual que en el juego (estilo, colores, marcos, letras, escudos), con la
   barra deslizante por ronda al pie, y más renglones que los 11 del juego si se puede.
c) Buscador, entre el panel superior y el principal (separado del superior): con pocas letras encuentra el evento;
   la palabra aparece con un resalte leve en todos los lugares donde figura (por ejemplo, el nombre de un héroe).
d) Panel inferior: botones "Limpiar búsqueda" y "Exportar" (PDF, y también texto).
- Versión visible en el título (regla global 19).

## Por averiguar (en este orden)

1. Ubicar `HISTORY.DAT` dentro de un .SAV real de `C:\Warlords3\SAVES` y recorrer sus bloques. Controlar que la
   cantidad de renglones de cada cabecera cuadre con el tamaño.
2. Texto de los 19 tipos: sacar del `switch` de 0x4b4110 las cadenas y qué campo va en cada hueco. Compararlo contra
   el Events Report del juego en la misma partida.
3. Arte del cuadro: el marco, la fuente y los escudos están en los recursos del juego. Ver de dónde los toma 0x4b3ec0.
4. Datos del panel superior: hay que ubicarlos en el .SAV (nombre, turno, condición de victoria, tipo de mapa).
   Las fechas de inicio y fin pueden no estar guardadas. Si no están, se dice y se propone una alternativa
   (por ejemplo, la fecha del archivo como fecha del último guardado). No se inventan.
5. Recién entonces: la app (dónde vive en el repo, lenguaje, empaquetado) y su publicación.

## Punto 1, resuelto (1/11/2026, medido sobre los 30 .SAV de `C:\Warlords3\SAVES`)

- `HISTORY.DAT` empieza siempre en el offset **0x60427** del .SAV, precedido por un dword con su largo
  (en 0x60423). En los 30 .SAV la cadena de bloques cierra exacto en 0x60427 + largo.
- Cabecera de bloque (0x48): +0 word tamaño del bloque, **+2 word número de ronda** (1, 2, 3… correlativo;
  sirve de control), +0x44 word cantidad de renglones. Después, un byte por ciudad (dueño; 73 en IA_ROTADA,
  40 en los mapas hex) y los renglones de 0x1c al final del bloque: tamaño = 0x48 + ciudades + n·0x1c, sin
  excepción en los 30 .SAV ni en el `C:\Warlords3\HISTORY.DAT` suelto (26 rondas).
- Renglones: 2.424 leídos, todos con tipo 1..0x11, jugador 0..8 y nombre ASCII. Tipos vistos: 1–15 y 17
  (el 0x10, 0x12 y 0x13 no aparecieron en estas partidas). El tipo 0 no aparece: es "casilla vacía".
- Detrás de HISTORY.DAT: la tabla de la ronda en curso, 16 renglones de 0x1c (jugador k en las casillas 2k y
  2k+1; tipo 0 = vacía); después los 0x18 bytes de 0x4fae68 y, con vista-aliada, 'VOTA', cantidad (dword) y tabla.
- Partidas en ronda 1 traen un solo bloque (largo 0x96…0x139).
- Pendiente de punto 2: qué significan parámetro y las tres words según el tipo (ej. tipo 0xe: parámetro =
  0x3c5e, w1 = jugador, w2/w3 quizá coordenadas, sin comprobar; el nombre es una ciudad).

## Próximo paso

Punto 2.
