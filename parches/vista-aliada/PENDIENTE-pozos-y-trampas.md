# Pozos y remolinos ocultos, y el bono "trap" (idea del usuario, 19/10/2026)

No es una destreza de la IA, pero la IA tiene que conocerlo (no meterse a sabiendas en un pozo descubierto, y
usar el bono "trap" en una etapa posterior).

## Lo que pidió el usuario
1. Sumar al mapa, con la misma lógica de las ruinas ocultas, **pozos** ocultos (accidentes del terreno, en tierra)
   y **remolinos** ocultos (en el agua).
2. Se descubren igual que las ruinas ocultas, con el mismo rango de casillas (el usuario no sabe cuál es: hay que
   averiguarlo en el exe).
3. Efecto: el grupo que pasa sobre un pozo o remolino oculto muere de inmediato, **salvo los voladores**.
4. Cantidad: un porcentaje parecido al de las ruinas ocultas.
5. Al caer (terrestres al pozo, barcos al remolino) suena, al azar, el sonido de muerte de héroe o de heroína.
6. Dibujos nuevos: el pozo, y el remolino **animado**. Una vez descubiertos quedan visibles el resto de la
   partida, como las ruinas ocultas.
7. Bono **"trap"**: solo algunas armas (por ejemplo los actuales "zappers") pueden construir en el mapa, donde el
   jugador elija, un pozo-trampa oculto con el mismo efecto. Cuesta lo mismo que una ciudad. Siempre visible para
   su creador, con la misma lógica interna que las unidades con bono de invisibilidad.

## A averiguar en el exe (antes de diseñar)
- Cómo se generan y guardan las ruinas ocultas (opción de partida, porcentaje, estructura de la ruina, bandera de
  "oculta") y en qué rutina y con qué rango se descubren.
- Dónde se valida cada paso de un grupo (para el efecto de caer) y cómo se mata un grupo entero (sin batalla).
- Los sonidos de muerte de héroe y heroína (archivos y la rutina que los dispara).
- Cómo se dibujan las ruinas en el mapa y si hay casillas animadas que sirvan de modelo para el remolino (agua).
- Cómo funciona el bono de invisibilidad (visible para el dueño, oculto para los demás) y la lista de bonos de las
  armas (dónde sumar "trap", como ya se sumaron landing, carrier y cabotaje).
- "Costo de una ciudad": qué valor del juego es (¿construir una ciudad? averiguar si existe y cuánto vale).
- Qué viaja por red y qué se guarda con la partida: pozos y trampas tienen que estar en el SAV y ser iguales en
  todas las PC.

## Respuestas del usuario (19/10/2026)
1. **A quién afecta:** pozos, remolinos y trampas matan a cualquiera, incluso al creador de la trampa. Lo que cambia
   es la **visibilidad**: el creador y sus aliados ven la trampa aunque esté oculta para el resto.
2. **Héroes:** "unidad" incluye a los héroes. Caen como cualquiera (solo se salvan los voladores).
3. **Mapas:** pozos y remolinos van en cualquier mapa, prearmado o al azar. Si en los prearmados no se puede sin
   reeditarlos, solo en los mapas al azar.
4. **Trampa descubierta:** mata **una única vez**. Dos dibujos, con la lógica de las ruinas exploradas:
   - trampa descubierta al paso, sin activar;
   - trampa detonada (el mismo dibujo con un fogonazo); ya no mata.

## Averiguado en el exe (19/10/2026)
### Opciones de partida
- **Hidden Ruins** ("Not all ruins visible at start") = bit 0x10 de [0x53c393]. **Discover Ruins** ("Discover hidden
  ruins as you pass", diálogo Viewing Options, control 5) = bit 0x20 de [0x53c393] (copia del diálogo: 0x503d07).
  Hidden Map = 0x10 de [0x53c38e]. Pozos y remolinos pueden seguir las mismas dos opciones (propuesta).

### Ruinas: tabla y banderas
- Cantidad word [0x558872]; registro de 0xb8 bytes desde 0x558874: +0 x, +2 y, +4 nombre, +0x94 tipo de dibujo
  (0..6, nombres en 0x55ac64: cave, henge, ... = RUINS\*.RUI), +0x95 explorada, +0x96 contenido, +0x98 guardián,
  **+0x9a oculta**, **+0x9b máscara de jugadores que la descubrieron** (bit = jugador), +0x9c parámetro.
- Se arman en 0x4a14f2..0x4a194c (corre en toda partida, mapa prearmado o al azar): **20 %** de las ruinas quedan
  ocultas (rand(1..100) < 20), algunas siempre. **Porcentaje para pozos/remolinos: 20 %** (a definir sobre qué base,
  ver diseño).
- Al empezar (0x4a1e20, llamada en 0x42ddc1): cada jugador descubre las ocultas de la región de su capital
  (mapa de regiones = byte bajo de la palabra +2 de cada casilla, 0x503e5a).
- La casilla del mapa (10 bytes en 0x503e58, fila = y·10 << [0x503e06]) lleva en su byte +8 la máscara de quién ve la
  ruina; 0x441290 la recalcula desde +0x9b y el dibujo la consulta.

### Descubrir al pasar (el "rango")
- 0x4a1ce0(jugador, x, y, radio), llamada en cada paso desde 0x49ce08. Si Hidden Ruins y Discover Ruins: un
  contador global [0x4fe5e8] gira 0..9 y **solo descubre en radio de cada 10 pasos**; descubre la primera ruina
  oculta no vista a **distancia (|dx|+|dy|) ≤ radio**. Llama 0x4a1c10(jugador, ruina, 2, texto) (pone el bit,
  0x441290, mensaje) y 0x4a2170 (redibujar).
- **radio = word [0x56eaae + p·0x4f0]** (+0x1e del grupo en movimiento): es el **mismo radio de visión** que despeja el
  Hidden Map en ese paso (0x441f30 en 0x49cd80). Viene en el paquete de movimiento (copia en 0x4b7d6e → 0x497930).
  El valor numérico concreto (depende de las unidades) no lo calculé; no hace falta: el pozo usa el mismo campo.

### Caer: matar sin batalla y sonido
- **0x485610(jugador, ejército, 1, 0, 1, 0)** ahoga a todos los de una casilla y da el aviso: es lo que ya usa el
  parche al derribar un puente (br_drown, build.py ~l.3992). 0x43c240 filtra quién puede ahogarse (deja fuera a
  voladores y embarcados). Para el remolino hay que ver cómo se hunde el barco **con** su carga.
- Voladores: el parche ya tiene isfly / listfly / grpfly (build.py ~l.1816).
- Sonido: 0x4465e0(7, g): g = 0 → FX\RuinDie.wav (sonido 0x1c), g ≠ 0 → FX\RuinDie2.wav (0x32). Son las muertes de
  héroe en ruina; "al azar" = g aleatorio. (Ningún llamado directo con 7 en el exe original.)

### Dibujos
- PICTS\RUINS.PCX (700×268): 3 filas × 8 cuadros; fila 1 cerrada, fila 2 abierta (explorada), fila 3 un aro. Es el
  modelo para "sin activar / detonada". Falta confirmar qué rutina dibuja las ruinas en el mapa principal y con qué
  hoja/cuadro según el tipo +0x94 (la del diálogo de ruina es el dibujo 0x51 / la hoja 0x4f).
- Animación en agua para el remolino: falta buscar un modelo (TERRAIN\DATA\*anim*.PCX, cit_anim, dnganim).

### Ya resuelto por el parche (sirve tal cual)
- Bonos de movimiento nuevos como TERRAIN\SUBTYPE\*.STT (landing, carrier, cabotage): "trap" se suma igual.
- Costo de una ciudad: [0x56950e] (lo que cuesta reconstruir un puente).
- Invisibles: solo los ve su dueño (0x414dbd); para la trampa hay que sumar a los aliados (como la vista aliada).

## Falta averiguar
- Rutina de dibujo de ruinas en el mapa principal y su hoja.
- Hundir un barco con carga (remolino) sin batalla.
- Dónde guardar pozos/remolinos/trampas para que viajen en el SAV y por red (¿registros extra de la tabla de ruinas
  con un tipo nuevo? la tabla tiene tope: ver cuántas entradas admite).

## Estado
Averiguado lo de arriba; nada programado. Para retomar: "Seguimos con PENDIENTE-pozos-y-trampas.md, falta averiguar".
