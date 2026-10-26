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

## Averiguado para el diseño (19/10/2026, cuarta ronda)
- El campo "clase de cosa" de la casilla (palabra +2 bits 8-10) **no es una enumeración limpia**: las ruinas se sellan
  con `and 0xfaff / or ah,2` (borra solo 0x400, conserva 0x100) y los sitios con `and 0xfcff / or ah,4`. Valores en
  uso: 1 camino/puente, 2 ruina, 3 (ciudad; unas 15 comparaciones `cmp ah,3`), 4 sitio. 5..7 no aparecen en ninguna
  comparación, pero el 0x100 se combina con otros bits y hay unas 40 lecturas del campo: meter una clase nueva ahí
  obliga a revisarlas todas. **Descartado.**
- Precedente en el parche para datos propios en el SAV: la tabla de la Votación va **al final del .SAV** con firma
  ('VOTA', vt_savef / vt_loadf, build.py ~l.6700): el exe original ignora lo que sobra y un SAV viejo la carga vacía.
- Precedente para red: el paquete propio 0x2a2 (build.py ~l.8842).

## Diseño (19/10/2026)
### Datos: una tabla propia, fuera de la de ruinas y fuera de la casilla
- `pz_tab`: hasta **64** registros de 8 bytes: +0 x (word), +2 y (word), +4 tipo (0 pozo, 1 remolino, 2 trampa),
  +5 estado (0 intacto, 1 detonado: solo trampas), +6 **máscara de quién lo descubrió** (bit = jugador, como +0x9b de
  la ruina), +7 dueño (solo trampa; 0xff en pozos y remolinos). `pz_n` = cantidad.
- `pz_map`: un byte por casilla (índice + 1 en `pz_tab`, 0 = nada), para que el paso y el dibujo no recorran la tabla.
  No se guarda: se rearma desde `pz_tab` al empezar, al cargar y al recibir la partida por red.
- Ningún código del juego ve la tabla: búsqueda de héroes, IA "Goto Ruin", informes y el tope de 50 ruinas quedan
  intactos.
- **SAV:** bloque 'POZO' al final del .SAV, detrás del de la Votación, con la misma técnica (SAV viejo → tabla vacía;
  exe original → lo ignora).
- **Red:** el anfitrión genera los pozos y los manda en la transferencia inicial como un bloque más (después del bloque
  5, el de ruinas; emisor 0x4aa170, receptor 0x4aa390), y se suman a la comprobación de sincronía (0x4aa590). Las
  trampas nuevas viajan como orden propia por el paquete 0x2a2 y se aplican en todas las PC, como 0x1ca (disband).
  Descubrir y caer no necesitan red: ocurren dentro del paso, que ya corre igual en todas las PC (como las ruinas).

### Generación (mapas nuevos, prearmados o al azar)
- Solo con **Hidden Ruins** activa. Justo después de ocultar las ruinas (0x4a14f2..0x4a194c), con el mismo generador.
- Cantidad: **20 % de la cantidad de ruinas del mapa** para pozos y otro 20 % para remolinos (mínimo 1 de cada uno si
  el mapa tiene tierra y agua transitables). Es la proporción que el juego usa para ocultar ruinas.
- Pozo: casilla de tierra transitable sin ciudad, ruina, sitio, camino ni puente, a más de 2 casillas de toda capital.
  Remolino: casilla de agua abierta (no puente). Nunca dos en la misma casilla.
- Al empezar, como las ruinas (0x4a1e20): cada jugador descubre los de la región de su capital.

### Descubrir
- En el mismo paso y con la misma regla que las ruinas (0x4a1ce0 desde 0x49ce08): Hidden Ruins + Discover Ruins, el
  contador de 10 pasos, radio del grupo (0x486290), distancia |dx|+|dy| ≤ radio. Pone el bit del jugador en +6, da el
  aviso y redibuja.
- Trampa: siempre visible para el **dueño y sus aliados** (mismo criterio que la vista aliada); los demás la
  descubren como un pozo.

### Caer
- Al terminar cada paso (0x49ce08), si `pz_map` de la casilla ≠ 0 y el registro está activo (pozo, remolino, o trampa
  no detonada):
  - **Pozo / trampa:** 0x46c470(ejército, 0) a cada ejército **no volador** de la casilla (héroes incluidos), el aviso
    y 0x441290; los voladores siguen. Como br_drown, pero filtrando con isfly en vez de 0x43c240.
  - **Remolino:** como el disband: 0x46c470(ejército, 1) a todos los no voladores, **embarcados incluidos**.
  - Sonido: 0x4465e0(7, g) con g al azar (RuinDie / RuinDie2).
  - Queda descubierto para el que cayó. Trampa: pasa a **detonada** (ya no mata) y queda vista por todos.
  - El movimiento se corta ahí; si sobrevivieron voladores, se detienen en la casilla.

### Bono "trap" y construir la trampa
- Subtipo nuevo TERRAIN\SUBTYPE\trap.STT, como landing / carrier / cabotage; lo llevan las armas que se elijan en el
  editor (por ejemplo los zappers).
- Construir (corrección del usuario, 19/10): el Build de los puentes **no sirve de modelo**, porque solo aparece al pie
  de un puente derribado. La trampa va donde el jugador elija: el grupo camina hasta la casilla que quiera y ahí usa
  una opción nueva **"Trap"** del menú de órdenes del grupo (el mismo menú de Raze / Build, 0x4b0660, ver br_menu
  ~l.4089). Se enciende siempre que el grupo tenga un ejército "trap", sea su turno, la casilla esté libre (sin ciudad,
  ruina, sitio, puente ni otro pozo) y el oro alcance ([0x56950e], costo de una ciudad). Pide confirmación y la orden
  viaja por red. No cae al salir; sí si **vuelve** a pisarla.
- Tope: lo libre de los 64 registros; lleno → aviso y no se construye.

### Dibujos
- Hoja propia (como sorteo.pcx / darkcomp.pcx), no la 0x4f: sus 8 lugares de tipo de ruina están ocupados. Cuadros:
  pozo, remolino (4 de animación), trampa intacta, trampa detonada (con fogonazo). Para las pruebas, copiados del de
  una ruina, como decidió el usuario.
- Gancho después de 0x45c0e0 en sus dos llamadas (0x459b90 y 0x45a02d): si la casilla tiene registro en `pz_map` y el
  jugador que mira [0x560b20] lo ve (bit en +6, o dueño/aliado de la trampa), copia el cuadro con 0x4dd490. El
  remolino elige el cuadro por un contador de tiempo.
- Animación (dato del usuario, 19/10): en el mapa solo se animan el **agua**, la **lava** y algunos **sitios**; las
  ruinas no. El remolino va siempre sobre agua: **el modelo es la animación del agua** (cómo y cada cuánto repinta el
  juego esas casillas). Averiguarlo es el primer paso al programar el dibujo; si hace falta un segundo modelo, el de
  los sitios animados.

### IA
- No pisa a sabiendas un pozo, remolino o trampa que ve: en su búsqueda de camino esa casilla es intransitable para
  ese jugador. Usar el bono "trap" queda para una etapa posterior, como pidió el usuario.

### Pruebas (prueba_pozos.py, como las demás prueba_*.py)
- Generación: cantidad y casillas válidas en un mapa al azar y uno prearmado; nada sin Hidden Ruins.
- SAV: guardar y cargar conserva la tabla; un SAV viejo carga vacío; el exe original abre el SAV nuevo.
- Caer: tierra en pozo (mueren todos, sonido), grupo con voladores (siguen los voladores), barco cargado en remolino
  (se hunde con todo), trampa (mata una vez, después detonada), el dueño que vuelve a su trampa (cae).
- Descubrir: con y sin Discover Ruins; trampa visible para dueño y aliados, oculta para el resto.
- Red: dos PC con la misma tabla y la misma suma de sincronía.

## Decisión del usuario (19/10/2026): pozos ya descubiertos
- El **camino automático** los esquiva siempre que el jugador los vea (pozo, remolino o trampa no detonada, en la
  búsqueda de camino es intransitable para ese jugador).
- **Salvo la ruta expresa del jugador, larga o paso a paso:** si el jugador elige como destino la casilla del pozo, o
  lo pisa avanzando casilla por casilla, cae. (El camino largo esquiva los demás pozos que vea y termina en ese.)
- Lo mismo vale para la IA: no tiene "ruta expresa", así que nunca entra en uno que vea.

## Estado
Orden: datos + SAV → generación → caer → descubrir → dibujo → red → trampa → IA, cada parte con su prueba.
- Parte 1, datos + SAV: hecha (commit a1e07a8, 1.0.42.0). po_save/po_map, bloque POZO tras VOTA; prueba_pozos.py.
- Parte 2, generación: hecha (1.0.43.0). po_gen en 0x4a1961 (vacía la tabla en toda partida nueva; con Hidden Ruins
  reparte 20 % de las ruinas de cada uno, mínimo 1, tope 32, 400 tiros) y po_start en 0x42ddc1 (región de la capital).
  Falta la red (parte 6): hoy cada PC generaría lo suyo.
- Parte 3, caer: hecha (1.0.44.0). po_step en 0x49ce08 (paso normal, al descubrir ruinas) anota la casilla en
  po_pend[jugador]; po_fall en 0x4b6e9d (fin del lote de pasos 0x14d, antes de 0x49d1a0, en todas las PC) mata con
  0x46c470 (0 pozo/trampa, 1 remolino) a los no voladores de ese jugador en la casilla. 0x46c470 suelta el grupo
  (0x485c00) y el tic siguiente 0x49e280 devuelve -1: el movimiento se corta. Aviso (0x4c2790) y sonido 0x4465e0(7,
  rdtsc & 1) solo en la PC del que cayó. Probado en unicorn (prueba_pozos.py), no en el juego: la prueba en el juego va a TAREAS cuando haya dibujo (parte 5), porque hoy los pozos no se ven.
  Sin probar en el juego: qué hace 0x46c470 con un héroe (arg 0 vs 1) y si el sonido 7 suena.
- Parte 4, descubrir: hecha (1.0.45.0). po_step ya no salta a 0x4a1ce0: lo llama (avanza el contador y descubre
  ruinas) y después aplica la misma regla a la tabla: Hidden + Discover Ruins, contador < radio, el primer registro no
  visto por el jugador a |dx|+|dy| <= radio; pone su bit en +6, redibuja y da el aviso en su PC. Pozo y ruina pueden
  descubrirse en el mismo paso (cada uno el suyo). Sin Discover Ruins una trampa ajena solo se descubre al caer (el
  dueño y sus aliados la ven siempre: eso es del dibujo, parte 5). Probado en unicorn, no en el juego.
- Parte 5, dibujo: hecha (1.0.47.0). Averiguado: la vista del mapa (0x459790, ebp = vista) pinta en su 1.ª pasada,
  por debajo de los ejércitos, terreno, ruina (0x45c0e0) y sitio (0x45aa80); la casilla de cada celda es (columna +
  [vista+0x28], fila + [vista+0x2a]). Lo animado (agua 0x15 en 0x4598c5, sitios en 0x459b16) elige su cuadro con
  (... + [vista+0x3c] o [vista+0x3e]) & 3; 0x456fdc avanza esa fase (0..15) en cada tic de la animación del mapa.
  Copia con transparencia: 0x4dd530(hoja, x, y, ancho, alto, destino 0x27, x, y); hoja cargada = [objeto+8] ≠ 0
  (objeto = 0x4e4a90(id), ecx = 0x58cf78); cargar = 0x4dd3f0(id) (1 si cargó).
  Hecho: po_draw en 0x459b95 (entre ruina y sitio) dibuja de la hoja nueva RUINS\pozos.pcx (archivo 168 del .RES,
  campos de henge) un cuadro de 48x48: pozo, remolino (4 cuadros, 1 + fase & 3), trampa, trampa detonada. Se ve si
  quien mira lo descubrió, o si es trampa suya o de un aliado mutuo con vista aliada (fogally). Dibujos de prueba
  recortados de las ruinas (cueva; cueva girada para el remolino; puerta trampa cerrada / abierta). Probado en
  unicorn; la prueba en el juego quedó en TAREAS 24 (solo en esta PC: sin la parte 6 cada PC genera sus pozos).
- Dibujos del usuario y tumbas (20/10/2026, 1.0.48.0). Pedido: (1) pozo descubierto = su picts\pozo.PCX; (2) cada
  vez que muere un grupo en un pozo, una tumba, lápida o cruz al azar (picts	umba.PCX, lapida.pcx, cruz.pcx) a 2
  casillas o menos, nunca sobre el pozo, que sigue oculto para quien no lo descubrió; (3) trampa detonada animada: un
  agujero irregular del que sale humo, el humo sacado de TERRAIN\DATA\cit_anim.PCX. Hecho: tipo nuevo PO_TUMBA (3) en
  la misma tabla (+5 = cuál imagen, +6 = 0xff: vista por todos), así viaja en el SAV y, en la parte 6, por red;
  po_grave (desde po_fall, solo pozos: remolino y trampa no dejan tumba; las trampas pueden ir juntas, como barrera, y no dejarían lugar a las tumbas) elige la casilla con un azar sacado de la
  tabla (igual en todas las PC) y pg_ok sin mirar capitales; po_step no anota tumbas. Hoja de 13 cuadros: detonada =
  cuadros 6..9 con la fase del agua, tumbas 10..12. Dato: lapida.pcx y el cuadro de tumba.PCX son **el mismo dibujo**
  píxel por píxel (se avisó al usuario; si cambia lapida.pcx basta recompilar).
- Prueba del usuario en el juego (21/10/2026): pozos y tumbas funcionan. Pidió (1.0.49.0, hecho): remolinos = el
  doble que los pozos (por el agua se circula menos; no vio ninguno), tope 16 pozos y 32 remolinos; descubrir a
  **una casilla** (PO_RADIO = 1, no el radio del grupo); un grupo de solo voladores no descubre. Se mantuvo el
  contador de 10 pasos de las ruinas (con radio 1 descubre en 1 de cada 10 pasos): si el usuario los nota difíciles
  de descubrir, es eso. (1.0.50.0, pedido del usuario: 1 de cada 5 pasos, contador 0 o 5.) Trampas: no vio cómo construirlas, porque era la parte 7 (hecha después, ver abajo).
- Parte 7, construir trampas: hecha (21/10/2026, 1.0.51.0). Bono nuevo TERRAIN\SUBTYPE\trap.STT ("trap", sin
  distinguir mayúsculas, en cualquiera de los 4 bonos del registro; los héroes no cuentan). Menú de órdenes del grupo
  (diálogo 0x1f = RES 34): renglón nuevo «Build Trap» al final (texto 0x17, zona 0x18; los 12 renglones a 16 px desde
  y = 53). br_menu llama a tr_check (por el puntero TR_CHKP, porque está después en build.py), que deja TR_FLAG y la
  casilla del líder (TR_X, TR_Y): se enciende si es su turno, algún ejército del grupo tiene "trap", la casilla pasa
  pg_ok PO_TUMBA (tierra transitable, sin camino, ciudad, sitio, estructura ni otro registro) y hay lugar en la
  tabla. tr_init (0x4affc2) habilita la zona, tr_hover (0x4b0450) pone texto y color, tr_click (0x4b0487) cierra el
  menú y abre el diálogo de reconstruir con [0x587e5c] = TR_MARK (0x7fff): br_rebdraw no busca imagen, br_cost da
  el costo de una ciudad, br_rebtxt muestra «Building a trap» y el OK se apaga solo si no alcanza el oro. tr_send
  (0x4b6236) manda TR_PKT 0x2a3 (bando, x, y); tr_recv (antes que or_recv) en todas las PC exige humano de la
  máquina que lo mandó, vuelve a pasar pg_ok, tabla y oro, cobra (0x43fd60) y agrega {x, y, PO_TRAMPA, 0, bit del
  dueño, dueño}. Probado en unicorn (prueba_trampas.py), no en el juego (TAREAS 26).
  Diferencias con el diseño (§ Bono "trap"): con la tabla llena la opción queda apagada, sin aviso; sin oro la
  opción se enciende igual y el OK del diálogo queda apagado (así el jugador ve el costo). El Army List no nombra
  "Trap" (solo Landing, Carrier, Cabotage).
  No se armó en C:\Warlords3: había una tanda corriendo con DarklordAV.exe; se armó y probó en una carpeta aparte.
  Hay que volver a correr build.py sin argumentos cuando termine (queda en TAREAS 26 como condición).
- Próximo: parte 6, red (el anfitrión manda la tabla en la transferencia inicial, suma de sincronía). Sin ella, en
  red cada PC tiene sus propios pozos; las trampas construidas sí viajan, pero sobre tablas distintas.
Para retomar: "Seguimos con PENDIENTE-pozos-y-trampas.md, parte 6 (red)".

## Pedidos del 21/10/2026 (después de la parte 7)
- **Sonido de trampa: hecho (21/10/2026, 1.0.53.0).** Los sonidos son la tabla tipo 3 del RES (registros de 52: +0 id,
  +4 nombre, +36 carpeta, 14 = FX; +48 clase), que 0x4ec490 carga entera al arrancar como buffers de la lista
  0x5a6f50; 0x4eca00(id) busca por id y 0x4e6fd0 toca. Los ids que usa 0x4465e0 son los de esa tabla (0x1c ruindie,
  0x32 RuinDie2). Se agregó el sonido 56 «Burst» con los campos de Dispel; Burst.wav (el del usuario) está en
  sonidos\ del repo y el parche lo instala en FX\. po_fall, en una trampa, lo toca junto con el grito, con la misma
  condición de la opción de sonido (bit 0x20 de [0x564d08]). Suenan a la vez, sin temporizador; si el usuario
  prefiere el grito corrido, la salida es un TrapDie.wav ya mezclado. Probado en unicorn (prueba_pozos.py); en el
  juego va con la tarea 26. De paso: parches.txt seguía con un tabulador real en lugar de la barra y la t de trap.STT.
- **Nombres de pozos y remolinos: hecho (21/10/2026, 1.0.52.0).** 16 nombres de pozo y 32 de remolino (PO_NOMBRES,
  tantos como el tope de cada tipo), en +5 del registro (el estado solo lo usan las trampas), así van en el SAV sin
  cambiar el formato; un SAV anterior trae 0 = el primero. po_gen tira un comienzo al azar por tipo y después
  correlativos, sin repetir. Los avisos (po_msg, sprintf [0x5a9bec]): «Your army fell into the Well of Souls!»,
  «Your army was swallowed by the Maelstrom of Kor!», «You have discovered the Well of Souls!». El aviso del juego
  dice «Your army», no el nombre del héroe (como antes). Trampa y tumba siguen con su texto fijo. Probado en unicorn
  (prueba_pozos.py, 75 OK); no en el juego (va con la tarea 24). Viajan por red con la tabla cuando se haga la parte 6.
  De paso se corrigió la prueba: el puente del mapa de juguete estaba en el byte +4 y pg_ok lo mira en +3.
- **Nombres de trampas: hecho (21/10/2026, 1.0.54.0).** Ciudad más cercana + número de dos cifras («Afland01»). No se
  guarda: el registro de 8 bytes no tiene lugar libre (+5 estado, +6 máscara, +7 dueño). po_msg lo calcula al dar el
  aviso: tr_city = la ciudad más cercana de todas (distancia de rey, en empate la primera; **también las arrasadas**,
  para que el nombre no cambie en la partida); número = 1 + las trampas anteriores en la tabla con la misma ciudad
  (los registros nunca se borran y la tabla es la misma en todas las PC). Nombre de ciudad recortado a 20 letras
  (%.20s) por el renglón de 64 del aviso. Avisos: «Your army fell into the trap Afland01!», «You have discovered the
  trap Afland01!». Sin ciudades, el aviso fijo de antes. El diálogo «Building a trap» no lo muestra (se calcula
  cuando la trampa ya está en la tabla). Probado en unicorn (prueba_pozos.py, 83 OK); en el juego, tarea 26.
- **Misión dura «Escort trap-disarming team to Afland02»: hecho (22/10/2026, 1.0.55.0).** Tipo nuevo 13 (qt_* en
  build.py); en el registro de la misión, +6 = índice de la trampa en PO_TAB, +8 = su dueño, +0xa = 1 cuando la
  detonó un ejército del jugador (po_fall lo marca). Generador Hard (0x45f4f6): si hay trampas candidatas (enteras,
  descubiertas por el jugador, de otro dueño hostil según 0x461080, a distancia de rey 2..4Q+23 del héroe) la tirada
  es 0..6 en vez de 0..5 y el 6 da esta misión; sin candidatas, la tirada del original. Solo para humanos (la IA no
  sabría cumplirla; si toma un jugador que la tenía, la ignora sin riesgo: todos los lectores del tipo tienen default).
  Cumplida (evento 5, 0x461fee): +0xa = 1 y el héroe a una casilla o menos de la trampa, en tierra, sin volar él ni
  nadie del grupo que se mueve. Fracasada (evento 0, 0x461d0c): detonada sin que fuera el jugador. Nombre (0x461163)
  «Escort trap-disarming team to Afland02»; objetivo (0x461432) «Heroe must escort a trap-disarming team to the trap
  Afland02.»; sin ciudades, sin el nombre. El número sale de tr_id, que ahora comparte con po_msg. Premio: el de por
  defecto. Como la IA no construye trampas, en el juego solo aparece con dos humanos en la misma PC. Probado en unicorn
  (prueba_misiontrampa.py, 55 OK, con comparaciones contra el original donde no hay trampas que dar); en el juego,
  tarea 27.

## Dibujo propio del remolino: hecho (22/10/2026, 1.0.56.0)
- El usuario aprobó el dibujo generado por código (espiral de dos brazos de espuma, embudo oscuro, azules del agua
  del mapa, fondo transparente) y pidió **un poco más grande, simétrico**: ocupa 3x3 casillas (unas dos de ancho) y
  **solo mata la del medio** (decisión del usuario). Sobre tierra, costa o puente la pieza vecina no se pinta.
- build.py: `remolino(fase)` dibuja 144x144, se corta en 9 piezas por fase; hoja con PO_FRAMES = 13 + 36 (cuadros
  PO_REMO0 + fase*9 + pieza; los 1..4 quedan sin uso). po_draw recorre la celda y sus 8 vecinas (po_vecs) y pinta la
  pieza de cada remolino descubierto; pw_put es el blit común.
- Probado en unicorn: prueba_pozos.py (piezas, fases, controles de tierra, puente, no descubierto, borde del mapa,
  dos remolinos vecinos, pozo encima), prueba_trampas.py y prueba_misiontrampa.py, todo OK. En el juego: tarea 24.

## Pedidos del 22/10/2026 (después de 1.0.57.0): hechos (1.0.58.0)
1. **Mina:** cuadro 5 de pozos.pcx = `mina()` en build.py (bola de hierro iluminada arriba a la izquierda, 8 puntas
   finas, brillo y sombra). Reemplaza a la puerta trampa. Construir en el agua: no pedido todavía.
2. **Tres usos (TR_USOS = 3):** +5 de la trampa = explosiones que lleva; activa mientras +5 < 3, sin cambiar el SAV (un
   SAV de antes trae 1 en las detonadas: les quedan 2). po_fall suma 1 y pone solo el bit de quien cayó (antes
   0xff). Gastada: no mata (po_step), no se descubre (pd_po la salta), no se dibuja (po_draw), y el registro queda
   (los nombres Afland01.. dependen del orden de la tabla), así que en esa casilla no se puede volver a construir.
   Misión 13: candidata si le quedan usos (qt_scan); +0xa se marca
   en cualquier explosión del jugador; fracasa solo cuando la trampa se gasta sin que la haya detonado el jugador
   (qt_fail). La tumba no cambia: solo la dejan los pozos.
3. **Caminos:** dato averiguado: el byte +3 «estructura» de la casilla es el mismo campo que los bits 8-10 de la palabra
   +2 (1 camino o puente). pg_ok con ebp = PO_TRAMPA (tr_check y tr_recv, antes PO_TUMBA) acepta el valor 1; el
   puente queda fuera porque su terreno es agua. Pozos, remolinos y tumbas siguen sin ir sobre caminos.
- Pruebas en unicorn: prueba_pozos, prueba_trampas (camino sí; puente y ruina no) y prueba_misiontrampa (usos
  intermedios), todo OK. En el juego: tareas 26 y 27 (actualizadas).

## Correcciones del 22/10/2026 (después de 1.0.58.0): hechas (1.0.59.0)
1. **Humo después de cada explosión:** +5 de la trampa pasa a ser: bits 0-3 explosiones, bits 4-6 quién la hizo
   explotar la última vez, bit 7 (TR_RECIEN) recién explotada. po_fall lo arma; tr_turn (desde ia_turn, al empezar el
   turno de cada jugador, en todas las PC) borra el bit 7 de las trampas que explotó ese jugador. po_draw: recién
   explotada o gastada -> agujero con humo (cuadros 6..9, animado con la fase del agua); si no, la mina. La recién
   explotada la ve quien la ve siempre (quien la descubrió, el dueño, sus aliados con vista aliada); la gastada,
   todos, hasta el final. Todas las comparaciones con TR_USOS miran solo los bits 0-3 (po_step, pd_po, qt_scan,
   qt_fail, po_draw). SAV sin cambios.
2. **Puentes:** pg_ok, para PO_TRAMPA con estructura 1 (camino o puente), acepta sin mirar el terreno. El dibujo va
   en la misma pasada que sobre tierra.
- Pruebas en unicorn: prueba_pozos (humo por fase, gastada vista por todos, tr_turn), prueba_trampas (puente sí) y
  prueba_misiontrampa (bit 7 con usos y gastada), todo OK.

## Pedidos del 22/10/2026 (después de 1.0.59.0): hechos (1.0.60.0)
1. **Trampas en cualquier lugar:** pg_ok con PO_TRAMPA solo pide casilla libre en po_map (ciudad, ruina, sitio, camino,
   puente, agua y montaña sí). Las arman las mismas unidades (bono «Trap»), también embarcadas.
2. **Mina más chica y sin sombra** (`mina()`, R 6.5). **Mina submarina:** trampa en agua sin puente (po_wet; sobre un
   puente es terrestre). Cuadro PO_MINAGUA (el último de pozos.pcx), la misma mina en los azules del agua (RE_AZUL).
   Al explotar no deja rastro: recién explotada o gastada no se dibuja. Mata como el remolino (0x46c470(ej, 1), también
   lo embarcado). Tres usos, como la de tierra. No es candidata a la misión 13 (el héroe no puede llegar por tierra).
3. **Remolino lejos de la costa:** po_mar exige agua sin edificio ni estructura en toda casilla a 2 o menos (5x5), dentro
   del mapa. Así no hay remolinos en ríos (hacen falta 5 casillas de agua de ancho). Los de partidas ya empezadas quedan.
- Pruebas: prueba_pozos (submarina, puente, remolino en río), prueba_trampas (ciudad, ruina, agua) y prueba_misiontrampa
  (submarina fuera de las candidatas), todo OK.

## Pedido del 22/10/2026 (después de 1.0.64.0): lupa y botón derecho. Hecho en 1.0.65.0
Hoy los nombres de pozos, remolinos y trampas (1.0.52.0 y 1.0.54.0) **solo salen en los avisos** al caer en ellos o
al descubrirlos. El usuario quiere que se vean igual que en sitios, ruinas y ciudades:
- al pasar el mouse por encima, el cursor cambia a una lupa;
- con el botón derecho se abre un cuadro con la información: nombre, tipo y, en una trampa, quizá los usos que le
  quedan;
- solo para lo que ese jugador ya descubrió.

Primer paso: encontrar en DarklordAV.exe dónde elige el juego el cursor de lupa y dónde arma el cuadro del botón
derecho para ruinas y sitios. Después, sumar el caso de PO_TAB: el registro de esa casilla en po_map, con el bit de
descubierto en +6.
Para retomar: «Seguimos con PENDIENTE-pozos-y-trampas.md, lupa y botón derecho».
- **Hecho (1.0.65.0):** en el decodificador de clic/cursor 0x4735c0, donde da 3 (nada, 0x473dc8), po_cur busca en
  la casilla lo que quien mira ve dibujado (po_look, la regla de po_draw; po_find suma las 9 casillas del remolino) y
  devuelve 0x14, el código de ruina: lupa y, con el botón derecho, la acción 0x4741d9, donde po_info abre el cuadro
  de información 0x4c7a10 con nombre, tipo y explosiones que quedan. Ciudad, ruina y sitio siguen primero; las tumbas
  y las minas submarinas que no se dibujan no tienen cuadro. Prueba: prueba_lupa.py, todo OK (también pozos, trampas
  y misiontrampa). Falta la prueba en el juego: tarea 31.

### Premios de las ruinas (averiguado el 23/10/2026 en el exe original, 0x4a14f2..0x4a194c)
- El contenido (+0x96) se sortea al armar la partida, **en partes iguales** (0x4deb20) entre los tipos de premio que
  la ruina tiene permitidos (7 banderas en [ebp-0x146..-0x141] y [ebp-0x13c]; tabla de saltos 0x4a19d8). No hay pesos
  ni porcentajes por tipo.
- Ítem (contenido 3): se elige **en partes iguales** entre los ítems cargados (tabla [0x55cb72], registros de 0xd8,
  los mismos .ITM) que todavía no están en otra ruina ni en manos de nadie (0x4427c0 y la marca [ebp-0x120]): cada
  ítem sale **una sola vez** por partida. Si no queda ninguno, la ruina pasa a contenido 1.
- La lista de ítems de la partida sale del ITEM.DAT del escenario (o RANDOM\<set>\ITEM.DAT / Item0-2.dat): byte de
  cantidad + nombres en registros de 9 bytes. Los montos (oro, maná, aliados, gema del sabio) salen de Default.rul
  (RuinGoldNormal=3d500+500, ...AGrade, etc.).
- El juego no distingue ítems originales de personalizados: solo se diferencian por la fecha de los .ITM.

## Ítems de los mapas al azar (23/10/2026, 1.0.67.0)

El generador de mapas al azar (0x4ca05a) copiaba a la partida uno de `RANDOM\<set>\ITEM.DAT`/`ITEM0-2.DAT`,
cuatro listas fijas hechas solo con ítems originales: por eso nunca salían los personalizados. Formato (cargador
0x4a0fb0, 362 bytes): word porcentaje, 16 nombres que se cargan siempre, 16 que se cargan si 1d100 <= porcentaje y
8 especiales (ITEM.INI). La tabla de ítems de la partida (0x55cb74) tiene lugar para 40; no se agranda. Desde
1.0.67.0 (`ri_go`), después de la copia se reemplazan los 32 primeros por un sorteo sin repetición entre todos los
`ITEMS\*.ITM`, con porcentaje 100 y sin repetir los especiales. Prueba: `prueba_items_azar.py`.

## Dos explosiones en vez de tres (1.0.70.0, 24/10/2026)
Pedido del usuario: el clan consideró excesivas las tres detonaciones; pasan a dos, tanto la trampa de tierra como la
mina submarina. Solo cambia TR_USOS (3 → 2): todo lo demás lo usa. Una trampa de un .SAV anterior que ya llevaba 2
explosiones queda gastada. Pruebas: `prueba_misiontrampa.py` ajustada a 2 usos, `prueba_pozos.py` y
`prueba_trampas.py`: TODO OK. El Manual dice «explota dos veces».

## Daño parcial de la trampa (26/10/2026)
Pedido del usuario: en cada explosión, eliminar entre el 40 y el 80 % de la pila y paralizar al resto (como el bono
Paralysis de Scorpion.arm). Hecho en build.py (tr_rand, tr_var, po_fall; versión 1.0.72.0) y probado en
prueba_pozos.py («daño parcial») y prueba_misiontrampa.py. Solo en tierra: la mina submarina sigue hundiendo todo
(matar parte de lo embarcado dejaría ejércitos en el agua sin barco).
- Parálisis del juego (0x46b205..0x46b272, la del defensor; 0x46af27.. la del atacante): +0x10 &= 0x80ff (pasos que
  quedan = 0), y si no tiene el bit 0x80 de +0x15 y (+0x12 & 0x7f) >= 9: movimiento -5 y el bit. Al empezar su turno
  0x434f5a quita el bit y devuelve los 5. Chance en combate: BaseParalyzationChance [0x56952e] × el valor del bono.
- Azar propio y determinista (todas las PC eligen lo mismo), como po_grave.
- **Falta publicar:** el 26/10 el juego estaba abierto (tanda de la tarea 44) y build.py no pudo escribir
  C:\Warlords3\DarklordAV.exe; publicar-parche.ps1 exige que lo instalado sea idéntico a lo compilado. Con el juego
  cerrado: `python parches\vista-aliada\build.py` y `.\tools\publicar-parche.ps1 vista-aliada`. Tarea 45.
