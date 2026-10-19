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
- **radio = word [0x56eaae + p·0x4f0]** (+0x1e del grupo en movimiento), el mismo que despeja el Hidden Map en ese
  paso (0x441f30 en 0x49cd80). **Corrección (19/10, a pedido del usuario):** no es un "rango visual" amplio. Lo calcula
  0x486290 (0x486b71..0x487185): el mayor de ((word +0xe del ejército) & 0xe) >> 1 entre los del grupo, más las
  habilidades "View" (0x17) y "View (group)" (0x18), **+2 solo si el jugador es la computadora** ([0x536c12] ≠ -1), con
  tope **entre 1 y 7**. Para un humano sin "View" queda en 1 o poco más: coincide con lo que el usuario ve en el juego
  ("casi tropezando, uno o dos casilleros"). No leí el valor base de cada tipo de unidad.
  **Decisión: el pozo usa el mismo campo y la misma regla (radio y chance radio/10 por paso).**

### Caer: matar sin batalla y sonido
- **0x485610(jugador, ejército, 1, 0, 1, 0)** ahoga a todos los de una casilla y da el aviso: es lo que ya usa el
  parche al derribar un puente (br_drown, build.py ~l.3992). 0x43c240 filtra quién puede ahogarse (deja fuera a
  voladores y embarcados). Para el remolino hay que ver cómo se hunde el barco **con** su carga.
- Voladores: el parche ya tiene isfly / listfly / grpfly (build.py ~l.1816).
- Sonido: 0x4465e0(7, g): g = 0 → FX\RuinDie.wav (sonido 0x1c), g ≠ 0 → FX\RuinDie2.wav (0x32). Son las muertes de
  héroe en ruina; "al azar" = g aleatorio. (Ningún llamado directo con 7 en el exe original.)

### Dibujos
- **Corrección (19/10, tercera ronda):** PICTS\RUINS.PCX no es el dibujo de las ruinas: es solo la base de la hoja 0x4f
  ("picts\ruins" en mpwar3.res), que el juego **rearma en memoria** al cargar. Ver "Dibujo de ruinas en el mapa" abajo.
- Animación en agua para el remolino: falta buscar un modelo (TERRAIN\DATA\*anim*.PCX, cit_anim, dnganim).

### Ya resuelto por el parche (sirve tal cual)
- Bonos de movimiento nuevos como TERRAIN\SUBTYPE\*.STT (landing, carrier, cabotage): "trap" se suma igual.
- Costo de una ciudad: [0x56950e] (lo que cuesta reconstruir un puente).
- Invisibles: solo los ve su dueño (0x414dbd); para la trampa hay que sumar a los aliados (como la vista aliada).

## Decisiones del usuario (19/10/2026, segunda ronda)
- Opciones de partida: las mismas Hidden Ruins / Discover Ruins. Sonido: RuinDie/RuinDie2 al azar.
- Dibujos: para las pruebas, el de la ruina (PICTS\RUINS.PCX); el dibujo propio se edita después.
- Costo de la trampa: el de una ciudad ([0x56950e]); menos haría el escenario intransitable.
- **Remolino: el barco se hunde igual que con el comando "disband"** (con lo que lleve encima). Falta ubicar la rutina.
- Guardado en el SAV y por red: decisión técnica mía.

## Averiguado en el exe (19/10/2026, tercera ronda)
### Dibujo de ruinas en el mapa
- **Tipos de ruina = archivos RUINS\<tipo>.RUI** (10 bytes: nombre de 9 + 1 bandera). 0x42fab0 lee **hasta 8** (bucle
  `di < 8`) y guarda los nombres en 0x55ac64 (10 bytes cada uno; la bandera queda en +9 = 0x55ac6d). Hoy hay 8: cave,
  henge, monolith, ruin_lrg, ruin_sml, tomb, tower, trapdoor → **no queda lugar libre para un tipo nuevo**.
- Cada RUINS\<tipo>.PCX (262×250) trae arriba tres cuadros de 87×88 (en x = 1, 0x58, 0xaf: intacta, ?, explorada; en
  trapdoor, puerta cerrada / abierta) y abajo la lámina del diálogo de exploración.
- 0x42fbf0 arma la hoja 0x4f: por cada tipo i copia con 0x4dd490 (hoja 0x51 = el PCX del tipo) esos tres cuadros a
  la columna x = i·87+1, filas y = 1, 0x5a, 0xb3.
- Al armar el mapa (0x431c85) cada ruina se **sella en la casilla** (10 bytes en 0x503e58): palabra +2 bits 8-10 =
  clase de cosa (**2 = ruina**, 4 = sitio; 0x436f73 también distingue 3); palabra +8 = byte bajo máscara de quién la
  descubrió, bit 0x100 explorada, **bits 9-11 tipo (3 bits → 8 tipos)**. Los sitios (0x55acb4) usan la misma casilla.
- El dibujo no lee la tabla: 0x4593f0 copia la casilla a celdas de vista de 0x1c bytes (+0 clase en bits 0x1c00,
  8 = ruina; +0xe máscara, se compara con el bit del jugador que mira [0x560b20]; +0x16 "hay ruina", +0x17 byte
  empaquetado) y **0x45c0e0** (llamada desde 0x459b90 y 0x45a02d) la dibuja de la hoja 0x4f con el byte empaquetado:
  bits 5-7 tipo (x = tipo·0x57), bit 0x10 explorada (fila y = 1 o 0x5a), nibble bajo = qué cuarto del ícono va en esa
  casilla (0..8; el ícono ocupa unas 2×2 casillas de 48).
- Bandera +9 del .RUI (0x45a012): si no es 0, la ruina **explorada no se dibuja** (monolith la tiene en 1). Sirve de
  modelo para "detonada" si se quiere que desaparezca, aunque el usuario pidió dibujo con fogonazo.
- Consecuencia para el diseño: el pozo/remolino/trampa **no entra como un 9.º tipo de ruina** sin ensanchar el campo
  de 3 bits (y la hoja 0x4f de 700 px de ancho ya está llena con 8 columnas de 87). Alternativas: otra clase de cosa
  en la palabra +2 de la casilla (ver qué valores libres hay: 0, 1, 3, 5..7) con su propio dibujo, o reutilizar uno de
  los 8 tipos. Decisión técnica pendiente al diseñar.

### Disband (para el remolino)
- Tecla BACKSPACE ("Disband Group", acción 19 de keys.w3); textos Sagetext grupo 0xfb (pregunta) y 0xfc (aviso).
- Confirmado en 0x46cf80: copia los ejércitos del grupo seleccionado (0x56ea94 + p·0x4f0, cantidad 0x56eaa8), manda la
  orden **0x146** (0x4b9020, vacía la pila) y por cada ejército la orden **0x199** (0x4ba530). Todo va por red.
- El anfitrión recibe 0x199 (0x4b780d; los demás la ignoran por 0x4dd3a0) y la reenvía a todos como **0x1ca**
  (0x4ba560); cada PC la aplica en 0x4b7e62 → **0x46d050(ejército)**: si es héroe (tipo & 0x1f == 0x10) marca
  [0x536bf4 + jugador·0x1f8], luego **0x46c470(ejército, 1)** y 0x441290.
- Ahogar (0x485610, puentes) usa la misma 0x46c470 pero con **0** y filtra con 0x43c240 (deja fuera voladores y
  embarcados). El 2.º argumento solo cambia la rama de los **héroes** (0x46c54c); no la descifré (probablemente qué pasa
  con sus objetos). Para el remolino: matar con 0x46c470 a todos los no voladores de la casilla, **embarcados
  incluidos** (sin el filtro 0x43c240); con 1 imita al disband.
- Despachador de órdenes: 0x4b69e0, tabla de bytes 0x4b892c (índice tipo+8) → tabla de saltos 0x4b85c4.

### SAV y red
- **SAV**: 0x439940 escribe bloques fijos con 0x4dfd70; entre ellos **0x536b30, 0x2d894 bytes** (hasta 0x5643c4),
  que contiene la cantidad de ruinas (0x558872) y la tabla entera. Además el mapa 0x503e58 (0x32000 bytes), así que lo
  sellado en la casilla también se guarda.
- **Red**: al empezar, el anfitrión manda la partida en bloques (0x4aa170.., paquetes de 0x100 bytes con 0x4aa2c0); la
  tabla de ruinas es el bloque 5 (cantidad·0xb8 bytes) y el receptor la guarda en 0x4aa3b5. 0x4aa590 la suma a la
  comprobación de sincronía.
- **Tope de la tabla: 50 ruinas** (0x558874 a 0x55ac64 = 0x23f0 = 50 × 0xb8, justo antes de los nombres de tipos).
- Consecuencia: registros extra en la tabla de ruinas viajan solos en el SAV y por red, pero comparten el tope de 50
  con las ruinas del mapa, y todo el código que recorre la tabla (búsqueda de héroes, IA "Goto Ruin", informes) los
  vería como ruinas: habría que filtrarlos en cada lugar. Una tabla propia evita eso pero hay que sumarla a mano al
  SAV (0x439940 y su lector), al envío inicial (0x4aa170 / 0x4aa390) y a la suma de sincronía. Las trampas creadas
  durante la partida, además, necesitan una orden de red propia (como 0x2a2). Decisión técnica pendiente al diseñar.

## Estado
Averiguado todo lo que estaba pendiente; nada programado. Próximo paso: diseñar (dónde viven los datos, clase de casilla
y dibujo). Para retomar: "Seguimos con PENDIENTE-pozos-y-trampas.md, diseño".
