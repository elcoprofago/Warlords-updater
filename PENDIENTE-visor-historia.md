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

## Punto 3, arte del cuadro (1/11/2026)

- Fondo: `C:\Warlords3\SETS\Fantasy\DLG_BIG.PCX` (620×460; el magenta es transparente).
- Marco del minimapa: probablemente `FRAME200.PCX` o `FRAME128.PCX` del mismo set (sin comprobar cuál).
- Escudo de cada renglón (ícono 0x69 + jugador, 0x4dd080): fondo `C:\Warlords3\SHIELD\B<color>.PCX` con la figura
  `O<nombre>.PCX` encima (magenta transparente). Los nombres están en el registro del jugador del .SAV:
  +0xa0 fondo (ej. «bwhite»), +0xa9 figura (ej. «oredcros»). Probado: da la cruz roja de las capturas. Cada hoja
  trae 5 tamaños (54×38 el mayor); el renglón usa uno chico (falta medir cuál).
- Letra: el renglón llama a 0x4dd0f0(1, 0x90, 10, 10, 1) → fuente 1. Tabla de fuentes en `DATA\War3.RES` desde
  0x48 (entradas de 0x28: número, nombre, tamaño): 1 Arial 11, 2 Uncial ATT 20, 3 Uncial ATT 16, 4 Arial 9,
  5 Uncial ATT 12, 6 Uncial ATT 48, 7 Arial 14. Se crean con CreateFontA (alto negativo). Los otros argumentos
  (0x90, 10, 10, 1) quedan en +0x20a…+0x210 de 0x58d0e8; serían color y sombra (sin comprobar).
- Títulos («History of Events», «Events for turn N»): por la apariencia de las capturas, Uncial ATT (sin ubicar
  en el código qué número usa).

## Punto 3b, minimapa por color (1/11/2026, medido en dia-noche4)

- El mapa entero va en el .SAV (bloque 0x503e58, 0x32000 bytes): ancho/alto en 0x503e00/0x503e02 (80×100 en
  dia-noche4), desplazamiento de fila en el byte 0x503e06 (casilla (x, y) = 0x503e58 + ((y·10) << sh) + x·10).
- Terreno: byte +0 & 0x1f. Valores vistos: 0 agua, 1 llano, 3, 4, 5 (bosque, colinas, montaña; falta asignar cuál
  es cuál y los colores exactos del minimapa del juego, que arma su imagen base en la hoja 0x2d).
- **Explorado: byte +4, un bit por jugador** (bit p = jugador p). En dia-noche4: Crusaders 2.942 casillas, Dark Elves
  1.931, Dwarfs y Goblins 1.463, Gnoll King 951, Magelords 785, los 2 colores ausentes 0. El dibujo de prueba da un
  mapa coherente y la zona explorada de Crusaders es una región continua alrededor de su arranque.
- Lo explorado es el de hoy (al guardar), no el de cada ronda: el .SAV no guarda su historia. Coincide con las
  capturas (terreno igual en las 4 rondas; solo cambian los escudos, que salen del bloque de cada ronda).
- Código: `historia.mapa(d)` devuelve filas de (terreno, explorados).
- Conclusión: el minimapa por color es factible; no hace falta sacarlo.

## Punto 4, panel superior (1/11/2026, leído en el código de guardado 0x439a00 y medido en los 30 .SAV)

Código: `historia.cabecera(d)` (también en `Partida.cabecera`).

- **Nombre:** bytes 0..0x1f (el que muestra el juego; puede diferir del archivo: IA_ROTADA.SAV se llama
  «hex_pozos_control»). 0x20..0x3f: nombre de archivo al guardar.
- **Ronda en curso:** word en 0x603d9 (objeto 0x5032f8 +0x30, serializado por 0x420850). ABN_000_29 da 29.
  Control: los bloques de HISTORY.DAT son siempre las rondas 1..ronda−1 (la ronda en curso va en la tabla aparte).
  Turnos jugados = ronda − 1 completas, más la que está en curso.
- **Condición de victoria:** word [0x560e52] (dentro del .SAV), 0..6 = textos 0x1bf de Sagetext: Last Warlord
  Standing, Most Cities, Most Victory Points, Most Money, King of the Hill, Capture the Flag, Fortress.
  Límite: word [0x560e50] (0 = sin límite). Con límite en turnos, el juego lo copia al tope 0x603e5 (+0x54 del
  objeto de turno, 0x420760); si no coincide, el límite sería en minutos (textos 0x1c0) — ningún .SAV lo tiene,
  sin comprobar.
- **Tipo de mapa:** 0x61..0x6c: «Random» (mapa aleatorio) o el nombre de archivo del escenario («kor», «border»,
  «Scarpart», «Hexagon»). El set (0x58, «Fantasy») va al lado.
- **Fechas: el .SAV no guarda ninguna.** El dword +0x4c de la cabecera parecía candidato y no lo es: es un número
  al azar 1..10000 (0x42d33e, `0x4deb20(1, 10000)`) que identifica la partida al cargarla (0x439e15). El dword
  +0x50 del objeto de turno es el reloj del límite en minutos (0x4e33c0), tampoco una fecha. Alternativa honesta
  para la app: «Último guardado: <fecha del archivo>» y, como inicio, nada (o «sin dato»). No se inventa.
- **Historial ajeno, ampliado:** `Partida.ajena` ahora también salta cuando las rondas de los bloques no son
  1..ronda−1. Aparecieron 4 casos que el control por cantidad de ciudades no veía (IA_ROTADA, Tanda_Scarpart,
  Tanda_hex_pozos_control y _PV_control: ronda 1 con 30 bloques de otra partida del mismo mapa). Total: 15 de 30.
- Límite conocido: si la partida es en red (word [0x503de8] = 3) el juego mete 0x8e5 bytes más antes del set y todos
  los offsets fijos se corren. Ninguna de las 30 lo es.

## Punto 5: la app (1/11/2026, hecho)

- Fuente: `ia/visor-historia/visor_historia.py` (VERSION en el propio archivo, a la vista en el título). Lee con
  `ia/historia.py` (`Partida`, `cabecera`, `escudo`, `juega`).
- Compilar: `python ia/visor-historia/build.py` → `ia/Visor-Historia.exe` (PyInstaller --onefile, ~43 MB, no va a git).
- Panel superior con «Último guardado» = fecha del archivo; el inicio no se muestra (decisión del usuario).
- Búsqueda con marcas doradas en la barra de rondas, exportación a PDF (fpdf) y texto, aviso rojo si el historial
  es de otra partida. Acepta un .SAV como argumento.
- Probado: dia-noche4, ABN_000_29, IA_ROTADA (el .exe compilado). Prueba del usuario: tarea 82.

## 1.0.1.0: observaciones del usuario (1/11/2026)

- Rótulos al pie de la barra ya no se cortan (barra de 46 px). Subtítulo «EVENTS FOR TURN n» en Arial 14, la letra
  de los renglones, en mayúsculas (también en el PDF).
- Sin «Exportar texto»: en su lugar la ruedita del Monitor de IA (imágenes de `ia/monitor-ia/assets`, empaquetadas):
  fondo color liso o textura en mosaico (`Visor-Historia.ini` junto al .exe) y «Actualizar versión».
- Actualización: lee `Visor-Historia.version` de la release Actualizador de Warlords-updater, baja
  `Visor-Historia.exe` y le pregunta la versión (`--version`) antes de reemplazarse. Se publica con
  `python ia/visor-historia/publicar.py` (todavía no publicado).
- Nombre de la partida en un cuadro blanco; rótulos en dorado/marrón y datos en celeste/azul según el fondo.
- Botones con naranja suave al pasar el mouse.

## Un jugador o multijugador (1/11/2026)

El byte **0x48** del .SAV es el modo de la partida ([0x503de8], lo fija 0x42d323 al empezar):
0 = un jugador (guarda en SAVES), 1 = por correo (EMAIL\*.EML), 2 = en red (NETSAVES), 3 = sin identificar (se fija
si [0x4fb698] ≠ 0; guarda en SAVES). Medido en C:\Warlords y C:\Warlords3: todos los de NETSAVES dicen 2 y todos los
de SAVES dicen 0, salvo ABN_000_29 y ABN_001-FIN (ranking, en SAVES) que dicen 0. El byte 0x54 ([0x503df4]) es otra
cosa: cuántos turnos viejos conserva NETSAVES. Todavía no se muestra en el Visor.

## Próximo paso

Según la tarea 82. Sin decidir: distribuirlo (por ejemplo como opción del Actualizador). Pendientes menores: del 3, tamaño del escudo chico y posiciones (medir sobre las capturas);
del 3b, colores del minimapa por tipo de terreno.

## 1.0.2.0 — luces Single / Multi

A la derecha del nombre, dos luces del semáforo del Monitor de IA (circle_09 + marco, 26 px, tono amarillo anaranjado;
apagada = brillo × 0,3). Se encienden según el byte 0x48 del .SAV: 0 → Single; 1 (correo) o 2 (red) → Multi; 3 (sin
identificar) → ninguna. Las partidas de ranking guardadas en SAVES (ABN_*) dicen 0 y encienden Single.
