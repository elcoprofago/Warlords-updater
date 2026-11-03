# PENDIENTE — Construcciones del jugador (puertos, puentes, caminos)

Diseño acordado con el usuario el 2-3/11/2026. Nada implementado todavía; mediciones terminadas, diseño de la implementación al final.

## Descartado

- Fundar ciudades en cualquier lugar del mapa: cambia la naturaleza del juego, la IA no lo
  aprovecharía y obliga a tocar la tabla de ciudades, las partidas guardadas y la sincronización
  del Puente.

## Acordado

1. **Convertir una ciudad propia costera en puerto.** Es caro y además se pierde la ciudad: sus
   ingresos, su producción y sus defensas. A cambio, se gana la salida al mar.
2. **Puente nuevo** sobre una casilla de agua elegida por el jugador. Cuesta el triple de una
   ciudad, porque la ubicación es estratégica.
3. **Camino.** Cada casilla cuesta en oro en proporción a lo que cuesta transitar ese terreno:
   la casilla más cara es la de montaña.

4. **Quién construye.** Solo construyen las unidades que tienen un bono nuevo de movimiento,
   «build». Lo tienen pocas unidades, los constructores. El constructor coloca el camino casilla
   por casilla y cada casilla se paga en el momento. Se construye hasta donde alcance el oro.
   Los puentes también necesitan un constructor: el bando que no tiene ninguno no puede
   construir nada. Convertir una ciudad en puerto no lo necesita, porque no es construir desde
   cero.
5. **Etapas.** Primero, construir queda reservado a los jugadores humanos; la IA usa los caminos
   y puentes que encuentra, pero no construye. Enseñarle a construir se verá más adelante.

## Decisiones del 3/11/2026

6. **Puerto nuevo: una sola casilla**, como los puertos actuales, con miniatura propia rediseñada
   (los dibujos de puerto tradicionales no muestran que ahí hubo una ciudad). Las otras tres
   casillas de la ciudad vuelven a ser terreno común. Motivo: reusa la lógica y el código de los
   puertos que ya existen, y no abre una ciudad-puerto de 4 casillas vulnerable.
7. **Orden de construir: un comando nuevo**, aparte de «rebuild» (reconstruir ya existe y
   mezclarlos se prestaría a confusión), siguiendo el precedente de «trap». Un solo renglón en el
   menú de órdenes de la unidad con el bono «build»: sobre tierra pone **road**, sobre agua
   **bridge**; el juego decide por la casilla elegida.

## Primer paso técnico (sin hacer)

- ~~Bit libre para «build»~~ **Medido el 3/11/2026: no hace falta ningún bit.** Los bonos de
  movimiento no son bits sino **nombres de 9 bytes en 4 ranuras** (registro de unidad +0xb2,
  igual en el .ARM y en memoria, 0x53c410 + (bando*16 + ranura)*0xfc). «build» entra como un
  bono más, igual que «camouflg», «carrier», «cabotage», «landing» y «trap»: un
  `TERRAIN\SUBTYPE\build.STT` (sumarlo a `STTS` en build.py, para que war3ed_ssg lo ofrezca) y
  la comprobación por nombre con `Unit.TieneMoveBonus`. No existe hoy ningún `build.STT`.
- Ranuras libres (379 .ARM de `C:\Warlords3\ARMY`): solo 5 unidades tienen las 4 ranuras
  ocupadas (FU_gob, goblins, half_bra, half_thi, MC_NazKl); ninguna es candidata.
- Unidades que llevarían el bono (candidatas por nombre, todas con ranuras libres):
  **Dwarf Sappers** (`Dwarfsap.ARM`, hoy «hills») y **Peasants** (`peasants.ARM`, sin bonos)
  como constructores; posibles también Siege Engines (`siegeeng`, `FU_siege`) y Gnomes
  (`SH_Gnome`, `FU_gnome`). Propuesta: Dwarf Sappers y Peasants, para que sean pocas.
- Hallazgo al pasar: `Zappers.ARM` todavía tiene el nombre viejo «camo» (ya contemplado en
  build.py, ver CAMO).

8. **Puente nuevo: se paga por casilla, como el camino** (3/11/2026; reemplaza el «triple de una
   ciudad» del punto 2 y el «lava = triple que agua», que salía 9 veces una ciudad: inviable).
   Reconstruir un puente derribado sigue siendo en bloque, a precio fijo; un puente nuevo es una
   tira de casillas, de **hasta 8**, y cada una se paga según su terreno (fácil, mediano o
   difícil), con la misma regla que el camino. La lava, más difícil que el agua, cuesta más por
   casilla. Se distingue por el tipo de terreno (`lava`, tipo 10 en Tanda_Kor; clase 1, igual que
   el agua). Así se pueden cruzar lagos y brazos de mar, no solo ríos angostos.

## Mediciones en Darklord.exe (3/11/2026)

- **Camino y puente son lo mismo en la casilla:** estructura 1 (`[+3] & 7`; registro de 10 B,
  grilla 0x503e58). Sobre tierra es camino; sobre clase agua sin edificio (`palabra 0 & 0x4000`)
  es puente. Poner uno = estructura 1 + elegir la pieza de dibujo (`[+8]`: hoja `0x21 + (&0xf)`,
  pieza `(>>5) & 0x1f`) + `0x4a4f20` (rehace el grafo) + refrescar la vista; es lo que ya hace
  `br_rebapply` en build.py al reconstruir un puente.
- **Montaña con camino: transitable, costo 1.** El grafo de pasos (0x4a4f90) pone costo 1 a
  toda casilla con estructura 1, sea cual sea el terreno (0x4a50b3), y la clase 4 (montaña)
  solo se corta si no hay camino (0x4a52c3). Costo de paso de cada terreno: palabra +0x12 de
  la tabla de terrenos (0x535ef8 + tipo*0x58); clase en +0x14. En Tanda_Kor: plains 2,
  hills 5, marsh 5, desert 2, ice 3, lava 9, road 1; mntns **0 = intransitable** (clase 4).
  Para el precio del camino la montaña no tiene costo de paso que sirva de base: hay que
  fijarle uno (el más caro, como se acordó). La tabla viene del juego de terrenos del mapa,
  así que el precio se calcula de la tabla en ejecución, no con números fijos.
- **Puerto:** es un *sitio* (tipo 4, estructura 4), no un bit suelto. Tabla de sitios en
  0x55acb6, registros de 0x96 B (x +0, y +2, nombre +4, tipo +0x94, arrasado +0x95), contador
  en 0x55acb4, **tope 50** (el editor compara con 0x32; la tabla termina en 0x55ca02). La
  grilla 0x582158 marca el punto de embarque con 0xc0. Un puerto nuevo = un sitio nuevo:
  falta medir cuántos sitios usan los mapas del clan, para saber cuánto margen queda.
- **«Ciudad desactivada» ya existe:** ciudad arrasada = estructura 3 con `[+8] & 0x80`
  (ciudad muerta, reconstruible). Para el puerto no sirve tal cual: la ciudad tiene que
  desaparecer (3 de sus 4 casillas vuelven a terreno común, decisión 6).
- **Orden en la interfaz:** hay precedente exacto. «Build Trap» es un renglón nuevo del
  diálogo 34 (menú de órdenes del grupo, 0x1f en el código; build.py `TR_TXT`/`TR_HOT`,
  `tr_check` desde `br_menu`), confirma con el diálogo de reconstruir y viaja por red como
  paquete propio (`TR_PKT`). «Build» sería un renglón más igual a ese, con su paquete.

- **Puentes largos (punto 8), a medir:** el código de derribar/reconstruir supone puentes de
  1 o 2 casillas (`br_comp`, `br_xy`, y las piezas de dibujo: mitades izquierda/derecha y
  arriba/abajo, y la de una casilla). Uno de 3 a 8 necesita una pieza de tramo medio y que
  derribar/reconstruir recorra la tira entera. **El juego ya trae la pieza de medio y también
  curvas** (dato del usuario, 3/11/2026: las vio en las herramientas y materiales del editor de
  escenarios). **Medido el 3/11/2026** en las 4 hojas de caminos (`TERRAIN\DATA\road0`, `road1`,
  `o_road`, `x_road`, 8×4 piezas de 48; todas con las piezas de puente en el mismo lugar) y en
  los .SAV: pieza = `(fila, columna)` con fila `([+8] >> 8) & 3`, columna `([+8] >> 5) & 7`.
  - horizontal: punta izquierda (1,6), **tramo medio (3,4)**, punta derecha (1,7);
  - vertical: punta de arriba (2,7), **tramo medio (3,5)**, punta de abajo (2,6).
  Prueba: Tanda_Kor tiene dos puentes verticales de 3 casillas armados (2,7)-(3,5)-(2,6). La
  pieza que build.py llama «de una casilla» (`br_stubtab` 3*8+4 y 3*8+5) es en realidad el
  tramo medio. Un puente de 8 = punta + 6 medios + punta.
  **Curvas de puente no hay** en esas hojas: las curvas (los anillos de las filas 1 y 2) y los
  cruces son de camino. Un puente nuevo va en línea recta, horizontal o vertical. Hay puentes
  de mapa que usan piezas de camino sobre el agua (Scarpart (43,15): (1,0)-(1,6)-(1,7)), hechos
  a mano en el editor; no hace falta imitarlos.

- **Sitios usados (3/11/2026, .SAV de `C:\Warlords3\Saves`; la tabla se halló por su
  contador + registros de 0x96 válidos):** Kor 16, Borderlands 20, hex 44, Scarpart 46,
  Scar_Alianzas 48. **Margen en los mapas grandes: 2 a 6 lugares.** Con la tabla del juego, en
  Scar_Alianzas solo entrarían 2 puertos nuevos. Opciones: negar la conversión con un aviso
  cuando la tabla está llena, o llevar los puertos nuevos en una tabla propia del parche (como
  los pozos y trampas), que no tenga ese tope. A decidir al diseñar el puerto.

- **Renglón «Build» en el menú de órdenes: entra.** Medido el 3/11/2026 en War3.RES: el
  diálogo 34 original tiene su último renglón en y=235 (separación 18-19); el parche lo dejó en
  12 renglones a 16 px (último, «Build Trap», en 229). Con 13 renglones a **15 px** desde 53 el
  último queda en 233, dentro de lo que el original ya ocupaba: no hace falta agrandar la
  ventana (su tamaño no está en el .RES; lo lee 0x4dd900 → 0x4ed760(6, …), sin ubicar). Texto
  de 10 px de alto: sin superposición.

Mediciones del exe: **terminadas**.

## Diseño de la implementación, etapa 1 (humanos) — 3/11/2026

Sigue punto por punto el precedente de la trampa (build.py, «Construir trampas»): renglón del
diálogo 34, confirmación con el diálogo de reconstruir, paquete de red propio que cada PC vuelve a
comprobar antes de cobrar y aplicar. La IA no construye (punto 5).

**A. Bono «build».** `('build', 'Build')` en `STTS`. Rutina `hasbuild` (como `reccomb`, pero sobre
los bonos de movimiento: `off=0xb2`, `slots=4`): ¿algún ejército del grupo, no héroe, lo tiene?
El parche no edita .ARM: el bono se asigna a Dwarf Sappers y Peasants con war3ed_ssg (va a
TAREAS.md cuando esté publicado).

**B. Renglón «Build».** `BD_TXT, BD_HOT = 0x19, 0x1a`, renglón 13 del diálogo 34; los 13 renglones
pasan a 15 px desde y=53 (medido: entra). `bd_check` desde `br_menu`, como `tr_check`: lo habilita
si el grupo tiene `hasbuild`, el bando es humano y hay algún candidato (C). Paquete
`BD_PKT = 0x2a4` (libre: los usados son 0x2a2 y 0x2a3): bando, x, y, clase (camino/puente),
dirección, largo. `bd_recv` repite todas las comprobaciones, cobra y aplica.

**C. Qué se construye y dónde.** Un constructor no puede pararse en montaña ni en agua, así que la
orden no actúa solo sobre su casilla:
1. su casilla, si es tierra sin estructura → **camino** ahí;
2. si no, las 4 vecinas en orden N, E, S, O: una **montaña** sin camino → camino en esa vecina
   (así se abre un paso: camino, avanzar, camino…); un **agua/lava** desde la orilla → **puente**
   en línea recta en esa dirección, de 1 a 8 casillas de clase agua sin estructura, que termine
   en tierra (si no llega a tierra en 8, no es candidato).
Con varios candidatos se ofrecen uno por uno con el diálogo de confirmar («Road north: 40 gold?»,
«Bridge east, 3 tiles: 270 gold?»); «No» pasa al siguiente. Un solo renglón, como pide el punto 7.

**D. Precio.** Una constante `BD_UNIT` (oro por punto de paso) y el costo de paso de la tabla de
terrenos en ejecución (palabra +0x12): camino = paso × `BD_UNIT`; montaña, que tiene 0, usa un paso
fijo `BD_MNT = 10` (la más cara, punto 3); puente = paso del agua/lava por casilla × `BD_UNIT` ×
`BD_BRX` (agua toma paso fijo 9, como la lava, si la tabla da 0; la lava × 1,5 encima). El puente se
cobra **entero o nada** (medio puente no sirve); el camino, casilla por casilla hasta donde alcance
el oro (punto 4). Valores iniciales a calibrar contra el costo de reconstruir (0x4b65e0) al probar.

**E. Aplicar.** Lo mismo que `br_rebapply`: estructura 1, pieza de dibujo, 0x4a4f20, refrescar.
Camino: pieza recta según la vecindad (se recalculan también las 4 vecinas con camino, para que
empalmen). Puente: punta + medios (3,4)/(3,5) + punta. Se guarda solo: vive en la grilla del mapa,
que ya va en el .SAV y en la sincronización del Puente.

**F. Puentes largos en derribar/reconstruir.** `br_comp` y `br_xy` pasan a recorrer la tira recta
hasta 8 casillas (hoy 1-2), y `br_stubtab` se renombra como tramo medio. Hace falta para que los
puentes nuevos se derriben y reconstruyan enteros, y para la IA (meta 9, `ai_brrebev`).

**G. Puerto (última fase, falta una medición).** Sin constructor; renglón en el menú de la ciudad
propia costera. Va a la tabla de sitios del juego (compatible con editor y .SAV) y, si está llena
(tope 50), se niega con aviso: el margen de 2-6 alcanza para algo caro y raro, y una tabla propia
obligaría a reescribir todo lo que lee sitios. **Falta medir** cómo hacer desaparecer una ciudad sin
borrar su registro (los índices de ciudad se usan en todos lados): candidata, ciudad arrasada
(`[+8] & 0x80`) + una marca propia que la oculte y impida reconstruirla, y las 3 casillas sobrantes
a estructura 0.

**Orden de trabajo:** A+B+C.1 (camino en la propia casilla, se prueba en red) → C.2 montaña → F →
puente → G.


## Estado — 3/11/2026

- **A+B+C.1 implementado** en vista-aliada 1.0.106.0 (sin publicar): bono `build`, renglón «Build Road» en el
  menú de órdenes (13 renglones a 15 px), paquete 0x2a4, camino en la casilla del líder con piezas según vecinos.
  Prueba de juguete: `parches/vista-aliada/prueba_caminos.py` (MAL: 0). Todas las demás pruebas dan igual que
  la versión anterior (se ajustó el seguimiento de la cadena de recepción en prueba_trampas y prueba_chatordenes).
- **Próximo paso:** cuando termine la tanda de la tarea 87 y el juego esté cerrado, compilar en C:\Warlords3 y
  `tools\publicar-parche.ps1 vista-aliada`; luego tarea 88 del usuario. Después C.2 (montaña).
- **Hecho (3/11/2026):** publicada la 1.0.106.0; tarea 88 cumplida: los caminos se construyen y se ven bien.
  La versión vigente es la 1.0.108.0 (agrega solo registros de IA para el convoy).
- **Próximo paso: C.2** (paso de montaña), después el puente nuevo sobre agua y el puerto. Ojo: si la tanda de la
  tarea 90 está corriendo, no compilar en C:\Warlords3 (build.py escribe ahí) hasta que termine.
  Frase para retomar: "Seguimos con PENDIENTE-construcciones.md, paso C.2".
