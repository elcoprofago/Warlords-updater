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
- Próximo: parte 2, generación (y vaciar la tabla al empezar partida nueva, que hoy no se hace).
Para retomar: "Seguimos con PENDIENTE-pozos-y-trampas.md, programación".
