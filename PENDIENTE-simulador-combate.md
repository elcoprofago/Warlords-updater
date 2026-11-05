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
  +0x11 bit 0x40 viva; +0x12 banderas (bit 3 veterano, 0..2, 11, 12, 13, 15 van a la ficha).
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
- Próximo paso: etapa 2, ítems (después hechizos y terreno).

## Lo averiguado en la etapa 2 (datos)
- **El tipo en memoria es copia de los primeros 0xfc bytes del `.ARM`** (mismo orden de campos que lee DarkCompare:
  +0 nombre, +0x10 descripción, +0x90 archivo, +0x99 medalla, fuerza, mov, vidas, turnos, mantenimiento, vista;
  +0xb2 4 bonos de movimiento de 9 bytes; +0xd6 bono de combate y +0xdf su valor; +0xe2 costo; +0xe4 armado;
  +0xe6 poder, +0xe8 su valor). Solo +0xe0 es del juego (un contador): `cargar_arma` lo conserva.
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
- Ítems (para seguir): tabla 0x55cc22 + i*0xd8, cantidad en 0x55cb72; +0 héroe, +2 bits 0-1 = 1 lo lleva un héroe,
  +0xa y +0x1a dos habilidades (palabra id, palabra valor), nombre en +0x2c. 0x409fb0 los suma por habilidad (los
  «slayer» 0x2c..0x33 valen 2). Hechizos activos: 0x55f030 + i*0x36 (40), +2 unidad, +0x16 4 efectos (id, valor).
- Héroes (notas de antes): la unidad héroe es tipo 16 y +0x10 bits 8-13 apunta a un registro de 0xb8 en 0x556bb2
  (nombre en +2; ahí aparecen nombres de habilidades como «flight», «fortify» y de ítems). Los `.HER` del HERO  miden 1380 bytes (clase: nombres por nivel, tabla de experiencia, habilidades por nivel). Falta ver cómo arma el
  juego el registro de 0xb8 a partir de la clase y el nivel, y qué lee de él 0x467240.
