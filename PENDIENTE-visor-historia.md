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

## Punto 2, resuelto en el código (1/11/2026); falta compararlo con el juego (TAREAS 80)

Decodificador: `ia\historia.py` (`Partida.texto`). Corrido sobre los 30 .SAV: 2.424 renglones, ninguno falla.

- Textos: `Sagetext.tex` (dword largo; después tabla de grupos, y por grupo word cantidad + dwords a las cadenas).
  Tipo t usa el grupo **0xb2 + t** (0x4def30 sobre 0x589880, variante 0 o 1). En inglés, como el juego.
- Qué va en cada hueco (`nom` = nombre[16] de +6, `par` = parámetro de +4, `p` = jugador de +2):

  | tipo | texto (variante) | huecos |
  |---|---|---|
  | 0 | Nothing unusual happens | — |
  | 1 | The enemy are vanquished in %s / A victory for %s in %s (si hay `nom`) | comarca `par` |
  | 2 | The Battle of %s is won / %s captures %s (si hay `nom`) | ciudad `par` |
  | 3 | %s receives a quest in %s | `nom`, ciudad `par` |
  | 4 | %s completes a quest! | `nom` |
  | 5 | %s finds %d mana crystal(s) (0 si `par`==1) | `nom`, `par` |
  | 6 | %s discovers %s | `nom`, oro: MISC.DAT antes/después ([0x56075f]/[0x560765]) + `par`, ej. «1567gp» |
  | 7 | %s meets a sage | `nom` |
  | 8 | %s enlists %d ally/allies (0 si `par`==1) | `nom`, `par` |
  | 9 | %s uncovers the %s | `nom`, ítem `par` (tabla 0x55cb74, 0xd8). Sale «the The Elven Ring», igual que el juego |
  | 0xa | %s rises to level %d | `nom`, `par`+1 |
  | 0xb/0xc/0xd | Peace negotiated / War declared / Alliance formed with %s | jugador `par` (0x536b34, 0x1f8) |
  | 0xe | A hero, %s, emerges / %s emerges in %s | ciudad en (w +0x16, w +0x18) o una casilla antes en x/y (0x440be0); si no hay, la variante 0 |
  | 0xf | %s is slain! (las dos variantes iguales) | `nom` |
  | 0x10 | %s is disbanded! | `nom` |
  | 0x11 | Utter defeat for %s | jugador `p` (el del renglón) |
  | 0x12 | %s for %s! | `nom`, jugador `p` |

- Comarcas (tipo 1): el juego las lee de `AREA.DAT` del disco (0x4410a0, registros de 0x22). El .SAV la lleva
  embebida solo si la partida tiene comarcas (0x43a850, bandera [0x560774]): detrás de la tabla de la ronda en curso
  va un dword y luego el largo + AREA.DAT. La reconoce `historia.areas` porque el largo es múltiplo de 0x22 (en las
  18 partidas con comarcas; las 12 de tandas no tienen). Sin comarcas, el texto del grupo 0xa («Wilderness»).
  **Suposición sin comprobar:** que al cargar una partida sin comarcas el juego no lea un AREA.DAT viejo del disco.
- **Historial ajeno:** en 11 guardadas de tandas (Tanda_Borderlands, Tanda_Kor, Tanda_hex_*…) el HISTORY.DAT
  embebido es de otro mapa: los bloques traen 74 o 40 dueños de ciudad y el mapa tiene 50 o 73. Pasa porque las
  guardadas de tandas se arman a partir de otras. `Partida.ajena` lo detecta; la app tiene que avisarlo en vez de
  mostrar nombres de ciudad equivocados.
- Jugadores sin nombre: en mapas de 6 bandos los registros 2 y 6 están vacíos y aun así aparecen en «War declared
  with » (Tanda_hex_alianzas). Es lo que guarda el juego, no un error de lectura.
- El tipo 0x13 (votación de vista-aliada) no está en el `switch` original: lo dibuja el parche (build.py ~7110).
  No apareció en estas partidas; queda «(tipo 19)» hasta que haga falta.

## Comparación con el juego (1/11/2026, capturas del usuario de dia-noche4, rondas 1, 3, 8 y 10)

- Los 26 renglones de esas rondas coinciden letra por letra con `ia\historia.py` (incluido el doble espacio de
  «finds 4  mana crystals» y el apóstrofo de «Horn of Jahve'»). Punto 2 confirmado.
- **Corrección:** la ronda 1 sí se muestra (11 renglones). Lo de «la ronda 1, nada» de arriba era un error de lectura
  del código. El tope de 11 sí se ve: el renglón 12 de la ronda 1 (Peldor finds 2 mana crystals) queda afuera.
- La lista de sucesos es la misma para todos los colores; el título es «History of Events», «Events for turn N».
- **Minimapa:** el juego muestra uno a la izquierda, del color que consulta. En las 4 capturas el terreno visible es
  el mismo y solo cambian los escudos de las ciudades: el terreno sería lo explorado **hoy** por ese color (sin
  comprobar en el código) y los dueños de ciudad salen del bloque de la ronda (un byte por ciudad, ya leído).
  Pedido del usuario: el visor tiene que poder mostrar el minimapa de cada color; si es muy complejo, se saca.
  Para hacerlo falta ubicar en el .SAV el terreno y lo explorado por cada color (nuevo punto 3b).

## Próximo paso

Punto 3 (arte del cuadro) y 3b (minimapa por color: terreno y exploración de cada color en el .SAV).
