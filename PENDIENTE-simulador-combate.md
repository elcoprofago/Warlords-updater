# Simulador de combate

Pedido del usuario (5/11/2026): un programa aparte que enfrenta dos pilas (atacante y defensor) y muestra la batalla
animada como el juego, para ver quién gana.

## Decisión central: el combate lo resuelve el propio exe, emulado

No se reescribe la fórmula de combate a mano (sería una aproximación y se desactualiza con cada parche). Se ejecuta
el código real de `DarklordAV.exe` con unicorn, como ya hacen `prueba_emulada.py` y `prueba_ia*.py`:

- `0x464ac0` arma la ficha de batalla (unidades, fight order, terreno, ciudad, puente, héroes; llama a `0x467240`
  por unidad y `0x468440` por grupo: habilidades, bono de combate, noche/nightmare, Bridge, Banding).
- `0x464ea0` pelea (llama 19 veces a `0x4deb20`, el dado) y deja el resultado; `0x469ed0` es el armado+pelea real.
- `0x464a30` es el cálculo de probabilidades del propio juego (arma + pelea varias veces): sirve de control.

Ventajas: el resultado es el del juego, incluidas las reglas de vista-aliada, y una pelea emulada tarda
milisegundos, así que se pueden correr 1000 batallas y mostrar el % de victoria además de una batalla animada.

Base del estado: una partida guardada (`.SAV`) cualquiera; el simulador escribe en memoria las dos pilas, el
terreno de la casilla, la ciudad (defensas), día/noche y la cantidad de ciudades de cada bando, y llama a las rutinas.

## Pregunta del usuario: ¿un imperio con pocas ciudades pelea peor?

**Respondida (5/11/2026): no.** Medido con `simcombate/prueba_motor.py`: la misma batalla (3 contra 3 gnollcav,
10 000 peleas, misma semilla) da 50,48 % con el defensor dueño de las 40 ciudades, de 1, y con el atacante dueño de
40 o de 1; en una ciudad del defensor, 70,75 % con 40 y con 1. Se cambió el dueño real de las ciudades (+0xa5) y el
recuento del juego (0x4407d0 → 0x536b20), verificado. Control: una unidad más del atacante pasa de 50,48 % a 70,75 %.
Lo único del combate que mira la cantidad de ciudades es el botín: al ganar en una ciudad, el atacante se lleva
oro del defensor / max(2, ciudades del defensor) (0x465c30).

Notas de antes: Ni la pelea ni el armado leen a simple vista una tabla de ciudades, pero leen campos del
registro de cada bando (`0x55cb72`, `0x55cc22..0x55cc2e`, `0x55f030..0x55f048`) que hay que identificar.
Método (regla 4 y 5): misma batalla emulada 10 000 veces con el bando dueño de 40 ciudades y de 2; si el % no cambia,
no hay tal factor. Control: cambiar algo que sí cuenta (una unidad más) tiene que mover el %.

## Pregunta del usuario: ¿la ciudad y sus defensas ayudan al defensor?

**Respondida (5/11/2026): sí.** 3 contra 3 gnollcav, 10 000 peleas: el atacante gana 50,70 % en campo abierto,
38,99 % contra una ciudad de nivel 1, 30,17 % contra nivel 2 y 21,64 % contra nivel 3 (`prueba_motor.py`, 2c).
El nivel es +0xa4 de la ciudad (1-3; BuildLevel2/3 del .rul es su costo); entra al bono del grupo defensor en 0x468440
con tope `FortifySiegeLimit` del .rul. Una primera medición había dado «no cambia nada»: era un error del motor, que no
cargaba el .rul y dejaba esos topes en 0. Ahora `Motor` carga [COMBAT] de `Default.rul` (o el que se le pase).

## Etapas
1. **Motor**: `simcombate/motor.py` — carga exe + .SAV, arma dos pilas sintéticas, llama a `0x464ac0`/`0x464ea0`,
   devuelve la secuencia de muertes. Prueba: coincidir con `0x464a30` y con una batalla real del registro de IA.
   Medir el efecto de cantidad de ciudades (pregunta de arriba).
2. **Datos**: armas del `ARMY\*.ARM` activo (orden alfabético), héroes, ítems, hechizos por héroe, barcos, terrenos;
   coeficiente de cada arma tomado de DarkCompare (mismo cálculo; DarkCompare es otro repo: se lee el `.ARM`, no se
   lo enlaza). Coeficiente de héroe: nivel, fuerza, hits, movimiento, ítems + plus fijo si tiene magias.
3. **Tablero** (ventana de comandos): dos paneles gemelos atacante/defensor con check de héroe y cantidad, grilla
   de 8 casilleros numerados (= fight order) con desplegables, desplegable de barco, visor del coeficiente,
   subpanel de héroe (nivel 1-10, habilidades aprendidas, magias del héroe, ítems), subpanel de terreno
   (agua/tierra, tipo, camino/puente/ciudad, día/noche, defensas 1-3, ciudades del bando), subpanel visual
   (velocidad, efectos, sonido, tamaño, resultados: sobrevivientes y muertos / solo sobrevivientes) y botón
   INICIAR COMBATE. Título con «VERSIÓN x.y.z.w» (regla 19).
4. **Ventana de combate**: las dos filas de unidades con sus imágenes del juego, tachando una por una según la
   secuencia del motor, con los sonidos del juego; luego la ventana de resultados.
5. **Aspecto del juego**: fondos, marcos, botones y fuentes sacados de los recursos del juego (PCX/FNT).
6. Publicar como herramienta del Actualizador (como el Visor de historia).

## Lo averiguado en la etapa 1 (motor)
- `simcombate/motor.py`: carga el exe y el .SAV en unicorn, simula las importadas de la biblioteca de C que hagan
  falta (hoy `_stricmp`, `strcmp`, `strlen`; otra cualquiera corta con su nombre), agrega unidades sintéticas y pelea.
- Unidades: tabla en 0x54fe50 (cantidad) y 0x54fe52 + u*28 (u >= 1): +0 x, +2 y, +0xb bit 2 especial (tabla
  0x568448), +0xc palabra = tipo (bits 0-4, 16 = héroe), dueño (5-8), **fuerza (9-12), vidas (13-15)** — la unidad
  lleva su fuerza y vidas, no las lee del tipo; +0x10 bits 8-13 índice de héroe (0x556bb2, registros de 0xb8);
  +0x11 bit 0x40 viva; +0x12 banderas (bit 3 = embarcada, lo pone el juego al entrar al agua en 0x466949; 0..2, 11, 12, 13, 15 van a la ficha).
- Tipos: 0x53c410 + (bando*16 + t)*0xfc: +0x90 nombre corto, +0x9a fuerza, +0x9b movimiento, +0x9c vidas,
  +0xa0 subtipo, +0xdf bono, +0xe6/+0xe8 habilidad y valor.
- Atacantes: grupo elegido del jugador p en 0x56ea90 + p*0x4f0 (+0 primera unidad, +4 hasta 10 unidades, +0x18
  cantidad). Defensores: todo lo vivo en la casilla (0x4411b0; en ciudad, sus 4 casillas).
- Ficha 0x569a80 + p*0x5cc; resultado 0x56c8e0 + p*0x40c (+0 1 = gana el atacante, +6 registro de eventos:
  0/1 pierde una vida el defensor/atacante, 2/3 entra la siguiente, 4/5 muere, 6/7 gana atacante/defensor; 0xc,
  0xd, 0xf, 0x10, 0x11, 0x15, 0x17+ son efectos especiales sin identificar).
- Azar: 0x500bf4 (16 bits), puro; 0x500bf8 en 0 para que no se siembre con time(). La batalla real (0x469ed0)
  siembra con [0x4fc798 + p*4].
- Ciudades: 0x537e2a cantidad, 0x537e2c + c*0xde: +0 x, +2 y, +4 nombre, +0xa4 viva (> 0), +0xa5 dueño.
- Probabilidades del juego: la rutina empieza en **0x464a10** (no 0x464a30): (p, x, y), 10 peleas en modo 1.

## Estado
- 5/11/2026: plan escrito; ubicadas las rutinas.
- 5/11/2026: **etapa 1 hecha.** `python simcombate\prueba_motor.py` → TODO OK: el motor da las mismas victorias que
  0x464a10 en 198 semillas; 10 000 batallas en ~2 s; pregunta de las ciudades respondida (arriba).
  Sin hacer: comparar con una batalla real del registro de IA (IA_BAT.CSV no guarda la semilla ni el estado previo,
  así que solo se podría comparar en promedio).
  Defensas 1-3 de la ciudad: ubicadas y medidas (arriba). Ojo en la etapa 2: el .rul del escenario puede cambiar los
  topes de [COMBAT]; usar el que use la partida. Héroes, barcos y terreno aún no probados en el motor.
- 5/11/2026: **etapa 2, armas hechas.** `simcombate/datos.py` lee todos los `.ARM` del ARMY (orden alfabético; 379,
  14 barcos) con fuerza, vidas, movimiento, vista, medalla, bonos, poder, costo y Factor (cuenta de DarkCompare,
  reimplementada sin enlazar ese repo; falta confirmarla contra DarkCompare: TAREAS 111).
  `Motor.cargar_arma(bando, ranura, Arma.registro)` pone cualquier `.ARM` en una ranura 0..15 del bando.
  `python simcombate\prueba_datos.py` → TODO OK: gnollcav cargado del `.ARM` en la ranura 12 da el mismo 50,70 % que el
  gnollcav que trae la partida; control: elephant en el atacante sube a 92,16 %.
- 5/11/2026: **etapa 2, héroes hechos.** `Motor.poner_heroe(bando, clase 0..3, nivel 1..10, elecciones, x, y, pila)`
  arma el héroe como el juego (fuerza, vidas, movimiento y vista de la clase; registro con nivel, experiencia y
  Leadership 1) y aplica cada elección con la rutina del propio juego (0x48efa0); rechaza gastar más puntos que los del
  nivel y una fuerza > 15 o vidas > 7. `Motor.cargar_clase` pone cualquier `.HER` en una ranura de clase;
  `datos.clases` lee los 66 `.HER`. `python simcombate\prueba_heroes.py` → TODO OK: las 32 clases de la partida son
  copia exacta de su `.HER`; cada elección de las 4 clases cambia lo que dice el `.HER`; Grak real y Grak sintético dan
  el mismo 99,82 %; 3 gnollcav 50,70 % → con un KBarbarian nivel 1 88,66 % → nivel 10 con F15 94,73 % (control).
- 5/11/2026: **etapa 2, ítems hechos.** `Motor.dar_item(héroe, registro)` le da al héroe cualquier `.ITM`
  (`datos.items` lee los 328 del ITEMS); `Motor.item_suma(héroe, habilidad)` devuelve lo que cuenta el juego (0x409fb0).
  `python simcombate\prueba_items.py` → TODO OK: el juego cuenta +3 Gold per City en Grak (Ring of Grak) y lo que dice
  el `.ITM` dado; KBarbarian nivel 1 con 3 gnollcav 88,66 %; 34 de 45 habilidades de ítem lo cambian (The Yellow Cross
  100 %, Beowulfs Fire 98,62 %, Illearth Stone 87,53 %); no lo cambian View, Fly, Movement, Gold per City ni los
  «slayer» que no tocan a gnolls (control); el mismo ítem en el suelo da 88,66 % (control).
- 5/11/2026: **etapa 2, hechizos hechos.** `Motor.lanzar(héroe, registro)` lanza cualquier `.SPL` con la rutina del
  juego (0x48f300, sin cobrar maná); `Motor.hechizo_suma(héroe, habilidad)` devuelve lo que cuenta el juego (0x409e40);
  `datos.hechizos` lee los 200 del SPELL. `python simcombate\prueba_hechizos.py` → TODO OK (~3 min): los 200 se lanzan
  sin fallar; el juego multiplica los valores ×1 en nivel 1-5, ×2 en 6-8 y ×3 en 9-10 (Black Dragon); 81 de 95
  combinaciones de efectos cambian el 88,66 % del héroe solo (Battle Rune 99,29 %, Blood Feast 98,56 %; Cursing +8
  lo baja a 87,68 %); no lo cambian Fly, Invisibility, Movement, View, Engineer, Mana Drain ni los «slayer» que no
  tocan a gnolls; control: Focus' lanzado por un héroe de otra pila da el mismo 88,66 %.
  Sin hacer: los efectos inmediatos (invocar 22, volar 13, etc.) no se aplican en el motor (tocan mapa y pantalla);
  `lanzar` los devuelve aparte: en el tablero, una invocación se representa poniendo las unidades invocadas.
- 5/11/2026: **etapa 2, terreno hecho.** `Motor.poner_terreno(x, y, terreno, estructura, bosque)`, `Motor.terreno`,
  `Motor.terrenos` (`limpiar` ahora también restaura el mapa). `python simcombate\prueba_terreno.py` → TODO OK (~4 min):
  cada bono de combate sube el % solo en su terreno (AmeWyrm hills 77,49 → 89,71 %, bluemage ice 3,25 → 33,42 %,
  bladem woods 44,28 → 58,50 %); el juego mira solo la casilla del defensor (cambiar la del atacante no mueve nada).
  Hallazgo: **el terreno «forest» no cuenta para los bonos WOODS/FOREST**: solo la capa de bosque (+3 bit 0x40).
  OPEN/FIELD vale en todo lo que no sea ciudad, agua ni bosque; CITY en estructura 3; si no, el nombre del terreno.
- 5/11/2026: **etapa 2, barcos hechos.** `Motor.embarcar(unidades)` (bit 3 de +0x12) + el barco en la ranura 15 del
  bando (`cargar_arma(bando, 15, ...)`). `python simcombate\prueba_barcos.py` → TODO OK: con los 14 barcos, de los dos
  lados, **la unidad embarcada pelea con min(su fuerza, la del barco) y min(sus vidas, las del barco)**, exactamente
  igual que en tierra con esos valores; el barco nunca la mejora y sus bonos (water, City, Field) y poderes no cuentan.
  Controles: el barco en la ranura sin embarcar, y en un puente, no cambian nada.
- 5/11/2026: **día/noche medido: sí cambia la pelea.** El efecto noche del parche (monster, demon, undead: +2 a una
  cosa sorteada por noche) está en 0x467240, que el motor ejecuta; `Motor.dia_noche(noche)` pone la opción (SHOPT bit 2)
  y la vuelta par. 3 contra 3 gnollcav, 5000 peleas: archons 75,72 → 90,92 % de noche, bees 0,92 → 13,84 %; según la
  noche el sorteo puede caer en algo que no cuenta (cavewyrm: 90,02 una noche, 85,38 otra = de día). Controles: sin la
  opción o en vuelta impar no cambia; un arma sin esas clases (airship, gnollcav) no cambia.
- 5/11/2026: **etapa 3, tablero hecho.** `simcombate/escenario.py` (Simulador: arma un escenario descrito en un dict,
  sin ventana) y `simcombate/tablero.py` (la ventana, VERSIÓN 1.0.0.0). `python simcombate\prueba_escenario.py` →
  TODO OK: las defensas de ciudad dan los mismos 38,99/30,17/21,64 % de la etapa 1; la grilla manda el orden de pelea
  de los dos lados; la noche cambia archons y no gnollcav; héroe, pila de 9, agua sin barco, barco y puente;
  y en 1500 batallas la secuencia de muertes coincide con el ganador. Probado en la ventana real (captura): dos pilas,
  héroe con elecciones e ítem, INICIAR COMBATE muestra % y batalla de muestra.
  Hallazgos: el **fight order** está en 0x536cfa + bando*0x1f8 (palabra por ranura; pelea primero el menor; 0x441520);
  la ficha guarda las unidades ordenadas en +0xe + k*0x24 (atacante) y +0x12e + k*0x24 (defensor). Hay **más eventos de
  muerte** que 4/5: 10/11 (Assassin) y 8/9 (vistos con moongard); `muertes` ahora se saca de los «entra» y del ganador.
  Decisiones: casillero k → ranura k del bando con prioridad k; héroe en la clase 0; ciudad = la ciudad 0 de la
  partida (del defensor, atacante al oeste); en agua sin puente, todos embarcados en el barco elegido. El
  «coeficiente» de la pila es el Factor medio y total (el del héroe no tiene fórmula definida: se muestran F/V/M,
  ítems y hechizos). El subpanel visual se guarda en `Simulador-Combate.ini` para la etapa 4.
  Probar en manos del usuario: TAREAS 112.
- 5/11/2026: **etapa 4, ventana de combate hecha.** `simcombate/combate.py` (VentanaCombate); el tablero (VERSIÓN
  1.0.1.0) la abre con INICIAR COMBATE y le pasa el subpanel visual (velocidad, efectos, sonido, tamaño 48/96,
  resultados). Repite los eventos de la batalla de muestra: marco dorado en la que pelea, una vida roja por golpe (0/1),
  tachada al caer (por la estructura, como `motor.muertes`), y al final ganador, % y sobrevivientes/muertos.
  `python simcombate\prueba_combate.py` → TODO OK: ícono para las 379 armas y barcos y las 66 clases; en 147 batallas
  al azar la repetición tacha lo mismo y en el mismo orden que el motor. Captura revisada.
  Imágenes: la hoja PCX de cada arma/clase es 521x246: retrato (0,0)-(127,159), ícono 48x48 en (1,161) (y en (50,161)
  el mismo con contorno verde = elegido), grilla de 8x5 animaciones desde x=128 en celdas de 49; magenta = transparente.
  El héroe usa `HERO\<.HER +0xc9>.PCX` (+0xd2 la mujer). `escenario.simular` devuelve ahora `fichas_a`/`fichas_d`
  (nombre, imagen, vidas de la unidad).
  Sin verificar: qué sonido usa el juego en cada golpe. Se usan `FX\DefHit`/`AttHit` (golpe al defensor/atacante),
  `DefDead`/`AttDead` y `Spell` para los eventos 0xc.. (esos nombres solo están en `DATA\*.RES`, no en el exe). Los
  `ARMY\<arma>00/01.wav` no se usan todavía. Las vidas mostradas son las de la unidad (bits 13-15), sin bonos de pelea.
  Probar en manos del usuario: TAREAS 113.
- 5/11/2026: **etapa 5 empezada (ventana de combate) y pedidos del usuario sobre el tablero** (tablero 1.0.2.0).
  La ventana de combate se dibuja sobre `SETS\Fantasy\DLG_CMBT.PCX` (el cuadro del dragón, 624x464; ×1,5 en «Grande»):
  atacante en el panel izquierdo y defensor en el derecho (casilleros 2x4 con el fondo de casillero de CMBTPICS),
  el duelo de las dos que pelean en el panel central, con las animaciones de CMBTPICS (espada con sangre = golpe,
  calavera que estalla = muerte, relámpago = efecto especial), textos en Arial Bold con sombra, y los resultados en un
  recuadro claro de borde dorado dentro del panel central. Coordenadas en el encabezado de `combate.py`.
  Tablero: botón «Invertir atacante y defensor» (armas, cantidades, barco y héroe); check «Ordenar las armas por NOMBRE
  COMÚN» (se guarda en el .ini; conserva lo elegido); el Factor total en un recuadro claro con borde dorado, Arial Bold
  con sombra; se quitó «Ciudades del bando» (medido sin efecto en la pelea, ver arriba) y la fila de carpeta/partida:
  queda el botón «Carpeta del juego…», que toma sola una partida de SAVES (el motor la necesita como memoria base; no
  cambia la pelea). `python simcombate\prueba_tablero.py` y `prueba_combate.py` → TODO OK. Capturas revisadas.
  Probar en manos del usuario: TAREAS 114.
- 5/11/2026 (tablero 1.0.3.0): **efectos por poder, vidas a la vista y arrastre de filas**. Medido con el motor
  (una tropa de cada poder contra gnolls, de atacante y de defensor): los códigos especiales son de poderes —
  0xc/0xf Lightning, 0xd/0x10 Acid, 0xe/0x11 Trample (del atacante/defensor), 0x14/0x15 Dragonslayer, 0x16/0x19 vistos
  con chariot (sin identificar); 8/9 = cae D/A por Missiles (Moonguard contra murciélagos, sin golpes antes). El byte
  +0xf6 del .ARM NO es el efecto: es un sonido (0x4469ac: sonido 0x22 + valor). CMBTPICS tiene 9 tiras (fuego 50,
  flecha 103, espada 154, relámpago 210, calavera 264, roca 318, polvo 373, ácido 426; chispas en la fila 0). La
  ventana usa la tira del poder de la tropa que pega (golpes, muertes y códigos especiales) y su ARMY\<archivo>00.wav.
  No se encontró la rutina de dibujo del exe: el par poder-tira sale del dibujo de cada tira. El Red Dragons de
  C:\Warlords3 (rddragon) tiene Chaos, no Acid; los dragones con Acid son p. ej. bkdragon.
  Vidas: puntos más grandes en los casilleros y puntos grandes debajo de cada tropa del duelo. Arrastre: «☰ N» de cada
  fila del tablero se arrastra a otra posición (la grilla es el fight order). prueba_tablero y prueba_combate → TODO OK.
  Probar en manos del usuario: TAREAS 115.
- 5/11/2026 (tablero 1.0.4.0): **efectos copiados de la ventana de combate del juego** (corrige la entrada anterior:
  el par poder-tira «por el dibujo» era invento). Leído en DarklordAV.exe: 0x405cd0 recorre los eventos (salta la
  racha de golpes que termina en Trample 0xe+5 o en 0x16-0x18; no muestra el golpe a una tropa con 1 vida ni el
  marcador 0xe/0x11 suelto; Lightning/Acid sobre una tropa que no aguanta reemplazan a su muerte por 0xc/0xf/0x1c/0x1d);
  0x406ed0(código) convierte (0xc con vidas>1 -> 0x13 = vidas a la mitad; 0xd con fuerza>1 = fuerza a la mitad) y
  dibuja con 0x407e20 (13 animaciones de CMBTPICS: 0 chispas, 1 explosión y 48, 2 flechas 102, 3 daga con sangre 156,
  4 calavera 264, 5 relámpago 210, 6 roca que se deshace en polvo 318, 8/12 ácido 426, 10 relámpago corto) y suena
  con 0x4465e0 (recurso de WAR3AV.RES: 2 AttHit, 3 DefHit, 4 AttDead, 5 DefDead, 0x2e arrows, 0x2f aagh, 0x30 zzzt,
  0x34 Slayer; arrows y aagh están en SETS\Fantasy). Por evento: golpe = chispas (1 por evento; 0x16-0x18 quitan 2-4
  vidas), muerte común = explosión, Missiles 8/9 = flechas, Assassin 0xa/0xb = daga, Lightning = relámpago, Trample
  0xe/0x11 = roca, Acid = ácido, Dragonslayer 0x14/0x15 = calavera. La fila del polvo (y 372) no la usa el combate.
  Las tropas NO suenan con su ARMY\<archivo>00.wav en el combate. Tabla en `combate.py` (ANIM, EVENTO, elegir).
  La ficha del simulador trae fuerza_c y vidas_c (casillero +8/+9, lo que lee 0x4071cb). prueba_combate suma una
  prueba por poder; TODO OK (147/147). Probar: TAREAS 116.
- 5/11/2026 (tablero 1.0.5.0): se muestran todos los golpes, con chispas y sonido, y tantas chispas como vidas
  quite el golpe (lo que el usuario ve en el juego). Recuadro del Factor: fondo negro, letra arena, sombra gris.
  Sin verificar: Poison, Paralysis, Disease y Curse no dan eventos en el combate del motor; su marca y su zzzt
  salen de otra parte (quizá las banderas de dibujo de la ficha, +0x2c..0x31), sin investigar. Lightning: el exe
  le da el sonido «zzzt» (FX\ZZZT.WAV); no hay otro archivo de trueno en FX ni en SETS\Fantasy.
- Próximo paso: seguir la etapa 5 en el tablero (fondos y marcos del juego en vez de los controles de Windows: p. ej.
  DLG_BIG/ARMYBG, BUT_MED para los botones). Pendiente aparte: identificar los eventos 0xc..

## Lo averiguado en la etapa 2 (datos)
- **El tipo en memoria es copia de los primeros 0xfc bytes del `.ARM`** (mismo orden de campos que lee DarkCompare:
  +0 nombre, +0x10 descripción, +0x90 archivo, +0x99 medalla, fuerza, mov, vidas, turnos, mantenimiento, vista;
  +0xb2 4 bonos de movimiento de 9 bytes; +0xd6 bono de combate y +0xdf su valor; +0xe2 costo; +0xe4 armado;
  +0xe6 poder, +0xe8 su valor). Solo +0xe0 es del juego: los bonos de movimiento en bits (hills 1, forest 2, fly 4); `cargar_arma` lo calcula.
- **La partida guarda su propia copia de los tipos**: si un `.ARM` cambió después de grabarla (pasa con Zappers,
  barcaza, orcs_ram y Tanda_Kor.SAV), la partida pelea con el viejo. El simulador carga siempre el `.ARM` del ARMY.
- Ranuras: la 15 es el barco del bando; en Tanda_Kor las 12-14 están vacías. Cada lado usa su propio bando, así que
  hay 16 ranuras por lado para los hasta 8 tipos del tablero.
- **Héroes, resuelto** (detalle en el encabezado de `motor.py`): clases en 0x5451d0 + (bando*4 + c)*1380 = el `.HER`
  (+0xdc fuerza, mov, vidas, vista; +0x3d0 umbrales de experiencia; +0x3e8 puntos por subida; +0x3fc 10 elecciones
  (habilidad, valor) y +0x49c su costo). Registro del héroe (0xb8): +0 clase/sexo/nivel, +0x12 experiencia, +0x14 10
  casilleros (habilidad, valor; 20 = hechizo con nombre en +6), +0xb4 puntos sin gastar. Subir de nivel (0x416c..)
  suma puntos; elegir (0x40c7c0) los gasta y llama a 0x48efa0. El movimiento máximo va en la unidad +0x10 bits 0-6, la
  vista en +0xe bits 1-3. El nivel no lo lee la pelea: solo cuentan los casilleros, fuerza y vidas.
  **0x48efa0 no pone tope**: una fuerza de 21 queda en 5 (4 bits). Sin ver si la pantalla de subir de nivel del juego
  lo impide; el simulador lo rechaza.
- **Ítems, resuelto**: el juego lee el `.ITM` entero (0xd8 bytes; algunos traen 2 de más) a 0x55cb74 + i*0xd8
  (cargador 0x433e7c), cantidad en 0x55cb72, hasta 40. +0 nombre, +0xae héroe, +0xb0 bits 0-1 (1 lo lleva un héroe,
  3 en el suelo), +0xb8 y +0xc8 dos habilidades (palabra id, palabra valor). 0x409fb0 los suma por habilidad (los
  «slayer» 0x2c..0x33 valen 2). Los ítems del escenario de la partida no son `.ITM`. Hechizos activos: ver abajo.
- **Hechizos, resuelto**: activos en 0x55f030 + i*0x56 (40; la nota anterior decía 0x36, mal): +0 vivo, +2 unidad
  del héroe, +4, +6 nombre, +0x16 4 efectos de 16 bytes (id, valor). El `.SPL` (210 bytes): +0 nombre, +0x10
  descripción, +0x90 palabra, +0x92 4 efectos; en memoria el juego lo usa sin la descripción. 0x409bd0 cobra el
  maná (0x43fe20) y llama a 0x48f300(unidad, hechizo), que multiplica según el nivel y deja activos todos los efectos
  salvo 13, 16, 22, 25, 29, 35, 36, 54, 58-60 (inmediatos). 0x409e40(unidad, x, y, hab) da el mayor activo.
- Héroes (notas de antes): la unidad héroe es tipo 16 y +0x10 bits 8-13 apunta a un registro de 0xb8 en 0x556bb2
  (nombre en +2; ahí aparecen nombres de habilidades como «flight», «fortify» y de ítems). Los `.HER` del HERO  miden 1380 bytes (clase: nombres por nivel, tabla de experiencia, habilidades por nivel). Falta ver cómo arma el
  juego el registro de 0xb8 a partir de la clase y el nivel, y qué lee de él 0x467240.

## Cerrado: el terreno «forest» no cuenta como bosque
Hallado el 5/11/2026 en `prueba_terreno.py`. En 0x467b33 (código original, igual en `Darklord.exe`) los bonos de
combate WOODS y FOREST tienen una rama propia que mira solo la capa de bosque (+3 bit 0x40); nunca comparan con el
nombre del terreno, así que el terreno 3 «forest» (clase 4, la de las montañas) no da esos bonos.
Efecto: en Tanda_Kor hay 585 casillas de terreno «forest» y unas 70 con capa de bosque; las 47 armas con bono
«woods» solo lo reciben en estas últimas. Ninguna arma del ARMY usa «forest».
Visto (5/11/2026): el terreno 3 es **bosque de verdad**. Su ficha (`TERRAIN\DATA\o_forest.TER`) lo llama «Forest» en
pantalla y lo dibuja con `o_forest.PCX`: arboleda tupida que cubre toda la casilla (la capa «woods», `o_woods.PCX`,
son los mismos árboles sueltos sobre otro terreno). Para el jugador se ve como bosque y no da el bono de bosque.
Decidido por el usuario (6/11/2026): es el bosque denso e intransitable (visto en Scarpart); **no cuenta como bosque**
para bonos de combate ni de movimiento y sigue intransitable. Nada que cambiar: su clase de terreno es 4, la de las
montañas (0x535f0c + t*0x58), así que el juego ya lo trata como montaña, y «build» también (bd_ok lo rechaza, bd_okm
lo acepta como paso de montaña al 25 %). Cerrado.
- 5/11/2026 (tablero 1.0.6.0): fondo de la ventana con EDPICTS\MARBLE.PCX del juego en mosaico; paneles, botones y
  cuadro de resultados con el reborde dorado del Visor de historia (dorado ancho + línea negra); letras del Factor en
  blanco; «Carpeta del juego…» junto a la casilla de ordenar, ventana más angosta (1186 px).
- 5/11/2026 (tablero 1.0.7.0): barra de Velocidad con la bola dorada del Visor (dibujada, no es imagen del juego); encabezado sobre el mármol; engranaje de configuración del Monitor de IA con créditos y actualización en línea desde el repo público elcoprofago/Simulador-Combate (build.py y publicar.py, como el Monitor). El relámpago suena con FX\Lightning.wav (en el parche: RES de sonido 57, en lugar del zzzt en 0x446bff/0x446c33/0x446d03/0x446d37).
- 5/11/2026 (1.0.10.0): el .exe se cerraba en la primera pelea (0xC0000409): el cargador de PyInstaller trae Control Flow Guard y unicorn ejecuta código generado en memoria. build.py apaga el bit GUARD_CF del .exe (python.exe no lo trae).
- 13/11/2026 (1.0.26.0): pedido del usuario: los barcos «no parecen tener efecto» y el tope de 8 no debería ser fijo.
  Barcos: el motor ya corría el combate del juego, que da a la unidad embarcada min(fuerza, barco) y min(vidas, barco)
  (prueba_barcos.py); casi todos los barcos tienen F7-9 y V3-4, así que con tropas comunes no cambian nada, y en tierra
  no cuentan. Ahora el simulador lo avisa en el resultado. Medido: 3 gnollcav en warship contra 3 en lancha (F1 V2), 97,8 %.
  Topes (`Simulador.tope`): la ficha de batalla tiene 8 lugares para el atacante y 32 para el defensor (+0x12e +
  k*0x24 hasta 0x5cc). Ciudad: el defensor, hasta 32, repartido en las 4 casillas de 8 (con 25+ en una sola casilla
  0x464ac0 se cae). Barco «Landing»: 5 (6 con «Carrier»), LANDCAP del parche. Barco «Carrier» del defensor: convoy de
  3 pilas (24, crlink). `python simcombate\prueba_topes.py` → TODO OK (incluye: 8/9/17/32 defensores en la ciudad
  llegan enteros a la ficha; 94,75 → 31,5 → 0 % con 4, 8 y 16 defensores).
- 13/11/2026 (1.0.27.0): voladores, pedido del usuario: tienen su propio tope de 6 (FLYCAP del parche: pila con
  algún volador). En campo y en agua el tope es 6 si hay un volador (y no más que el del barco); en la ciudad, los
  voladores van en casillas de 6 y el resto en casillas de 8 (6 voladores + 24 = 30). El héroe cuenta como no volador.
  Corregido de paso: +0xe0 del tipo no es un contador, es lo que el juego arma con los bonos de movimiento (bit 0
  hills, 1 forest, 2 fly; visto en las 6 partidas de SAVES). `cargar_arma` conservaba el de la ranura, así que un
  volador cargado no llevaba el bit 4; ahora lo calcula. prueba_topes.py → TODO OK; escenario, barcos y combate, OK.
- 13/11/2026 (1.0.28.0): pedido del usuario: luz roja «tope excedido» en cada panel, junto al botón Héroe (bajado 8 px
  del desplegable de barcos). Es la luz del Monitor de IA (circle_09.png llevada a rojo con marco.png, 26 px; los
  assets ya van en el .exe), con fundido lento de 2 s por ciclo mientras el lado pase su tope (`LuzTope`, se enciende
  desde Panel.recalcular). Probado en la ventana (captura): 9 en campo la enciende, 8 la apaga.
- 13/11/2026 (1.0.29.0): pedido del usuario: la aclaración bajo FACTOR y COSTO quedaba cortada. Sale la cantidad de
  unidades; queda «Factor medio X · tope N: motivo» (el tope solo si no es 8 o si se pasa). La cantidad va como
  contador «unidades / tope» en la leyenda de la luz: gris apagada, roja «tope excedido 9 / 8» encendida. Captura OK.
- 13/11/2026 (1.0.30.0): pedido del usuario: contador general de pruebas, retro de tambores (contador.odometro, PIL),
  a la derecha del encabezado con la leyenda «PRUEBAS» a su izquierda. Se guarda en el .ini ([contador] n, periodo,
  clave); no se borra al reiniciar. Configuración: periodo (manual, día, semana, mes, año; se resetea al cambiar la
  clave del periodo) y «Poner en cero». Probado: 3 pruebas = 3, cambio de mes = 0, reset manual = 0. Captura OK.
- 13/11/2026 (1.0.31.0): pedido del usuario: botón «Historial (últimos 20)…» junto a Invertir. Lista por número del
  contador (6 cifras), fecha y hora y resultado; doble clic o Enter abre la ficha en texto: campo, composición de los
  dos lados (tropas, barco, héroe), porcentaje y batalla de muestra con las caídas tachadas. Se guarda en
  Simulador-Combate-historial.json junto al .ini (historial.py, MAXIMO = 20). Probado con 3 combates; capturas OK.
- 13/11/2026 (1.0.32.0): reporte del usuario: la lista del historial decía «Atacante gana X %» aunque ganara el
  defensor (X bajo). Ahora dice quién gana («Gana el DEFENSOR: 93.50 % de 200»). Además, barra de desplazamiento
  vertical (10 filas a la vista). Probado con 12 combates ganados por el defensor; captura OK.
- 13/11/2026 (1.0.33.0): pedido del usuario: la lista pasa a columna «Ganador» con ATACANTE/DEFENSOR en su color
  y el porcentaje (lista en un tk.Text, porque el Treeview no colorea celdas; clic, flechas, doble clic y Enter).
  La ficha empieza el resultado por el ganador («RESULTADO: DEFENSOR con 93.50 %») y en gris lo del perdedor
  («(atacante gana el 6.50 % en 200 peleas)»). Capturas OK.
- 13/11/2026 (1.0.34.0): pedido del usuario: la ficha ya no muestra la «batalla de muestra» (confundía: podía ganarla
  el que pierde en el porcentaje). Queda composición, campo, resultado y avisos. Captura OK.
- 13/11/2026 (1.0.35.0): reporte del usuario: en los combates 18 y 19 «ganó el defensor» pero el historial decía
  atacante. El historial estaba bien (atacante 80 %; 400 batallas sueltas: 82 %): la ventana de combate muestra una
  sola batalla con semilla fija (12345) y esa caía en el 20 % del defensor. Ahora Simulador.simular busca, desde esa
  semilla, la primera batalla que gana el ganador de la mayoría (hasta 200 intentos). Mismo caso: muestra gana A.
  Pruebas escenario, combate, barcos, topes y tablero: TODO OK.
- 13/11/2026 (1.0.36.0): **revisión de la confiabilidad del %** (pedido del usuario: «revisa absolutamente todo»).
  1. El % nunca salió de la batalla de muestra: sale de las n peleas (probabilidad_motor).
  2. **Hallazgo: el azar del juego tiene 65 536 estados y, encadenado pelea tras pelea, cae en un ciclo de ~2 234
     peleas** (medido con 2 semillas: período 2234). De 6000 peleas solo ~2234 eran distintas y el % quedaba fijado
     por el ciclo, igual con cualquier semilla. Ahora cada pelea arranca de un estado distinto (semilla + i·40503,
     impar: con 65 536 peleas se recorren todos y el % es el exacto del juego). Sesgo medido del método viejo:
     caso 18/19 de día 80,05 contra 80,36 exacto; ciudad nivel 2, 30,17 contra 29,10 exacto.
  3. **Hallazgo: de noche se usaba siempre la vuelta 6**, y el bono de monster/demon/undead se sortea por vuelta.
     Caso 18/19 de noche: 80,1 % en las vueltas 2-16, 67,6 % en las 18-22 y 28-30. Ahora reparte las peleas entre
     20 noches (vueltas 2…40) y da el promedio (≈77 %).
  4. Lo demás, ya medido antes y vuelto a correr: las 11 pruebas TODO OK (prueba_escenario comparaba contra valores
     del método viejo con tolerancia 0; ahora contra el exacto con margen de 4 desvíos, y suma la prueba de las
     65 536 semillas con su control). Cantidad de ciudades: descartada antes (no cambia la pelea).
  Spinbox de peleas: tope 65 536 (más no agrega nada).
- 13/11/2026 (1.0.37.0): Historial: los combates repetidos (mismo campo y mismos dos lados) comparten un color de fondo,
  uno por grupo; los que no se repiten quedan en blanco. Probado con un historial de 2 pares + 1 control: OK.
- 13/11/2026 (1.0.38.0): títulos de los paneles (pedido del usuario): Arial bold 17, letra blanca con borde negro
  (verde en TERRENO) y sombra, en un recuadro blanco con borde fino oscuro (letra_titulo en tablero.py).
- 13/11/2026 (1.0.39.0): ATACANTE y DEFENSOR sin el recuadro blanco detrás del título (pedido del usuario); TERRENO lo conserva.
- 13/11/2026 (1.0.40.0): recuadro del título TERRENO en marrón claro (#d2b48c), pedido del usuario.
- 13/11/2026 (1.0.41.0): Historial de 40 combates (antes 20). Botones nuevos en el Historial: Stats (torta de
  formaciones ganadoras: en cada combate, la del bando que gana la mayoría; la mejor = más victorias, a igualdad
  mayor % medio), Exportar ficha y Exportar gráfica (PNG o JPG, según la extensión). Módulo nuevo imagenes.py
  (solo PIL); la ficha en pantalla y la exportada salen de los mismos trozos. Prueba: prueba_imagenes.py, TODO OK.
- 13/11/2026 (1.0.42.0): botones modernizados (pedido del usuario) con BotonAzul(fondo=...) y boton_color: fondos
  tomados de la fila del medio de 5 escudos que pasó el usuario (FONDOS en tablero.py). Carpeta negro, INICIAR cyan,
  Invertir naranja, Historial verde, Héroe blanco; en fondos claros, la letra con borde negro fino.
- 13/11/2026 (1.0.43.0): leyenda de Stats sin nombres de archivo. El archivo no lleva extensión, así que el nombre
  se toma de la tabla del juego cargado (nombres_del_juego); medido: 379 armas y barcos, 0 mal, en los dos órdenes.
- 13/11/2026: el Manual suma la captura de la ventana del Simulador 1.0.43.0 (img/capturas/simulador-combate.png),
  al final del consejo «Probar antes de pelear»; antes no tenía ninguna. Si la ventana cambia, se vuelve a capturar.
  La captura muestra el combate 18/19 (5 Sparks + 1 Sun Priests contra Moonguard, Esfinge, Bannerman y Devourers,
  hills, de noche, 6000 peleas: atacante 76,85 %), simulado sin sumar al contador ni al Historial.
- 13/11/2026 (1.0.44.0): degradé de los botones pixelado (pedido del usuario): la paleta de los escudos viene en
  escalones de 2-3 píxeles; ahora se suaviza con un promedio gaussiano (suavizar) antes de estirarla. Captura del Manual rehecha.
