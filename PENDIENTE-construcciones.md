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
- **Próximo paso:** (1.0.111.0 publicada: flecha roja de mvarrow en el diálogo del camino; el «build» de la torre sigue sin ubicarse, tarea 92 pide captura) cuando termine la tanda de la tarea 87 y el juego esté cerrado, compilar en C:\Warlords3 y
  `tools\publicar-parche.ps1 vista-aliada`; luego tarea 88 del usuario. Después C.2 (montaña).
- **Hecho (3/11/2026):** publicada la 1.0.106.0; tarea 88 cumplida: los caminos se construyen y se ven bien.
  La versión vigente es la 1.0.108.0 (agrega solo registros de IA para el convoy).
- **Próximo paso: C.2** (paso de montaña), después el puente nuevo sobre agua y el puerto. El usuario dejó la tanda
  de la tarea 90 sin arrancar porque esto tiene prioridad: se puede compilar en C:\Warlords3. La tarea 90 tendrá que
  correrse con la versión que resulte (sigue trayendo los eventos 24 y 25).
  Frase para retomar: "Seguimos con PENDIENTE-construcciones.md, paso C.2".
- **C.2 implementado (3/11/2026) en vista-aliada 1.0.109.0** (sin publicar; se publicó como 1.0.110.0, que suma
  «Rebuild» en el botón de la torre). Si la casilla del líder no admite camino, una montaña vecina sin
  estructura sí (`bd_okm`, paso fijo `BD_MNT = 10`: precio = ciudad × 10 / 20). `bd_check` enciende el renglón si
  hay algún destino; el destino lo elige `bd_pick` **al hacer clic** (no al habilitar: 0x4b0660 se llama desde 8
  lugares, incluido el hover), rotando N, E, S, O si el líder no se movió, así «No» + otro clic pasa a la
  siguiente. Destino en `bd_vars` (BD_X, BD_Y, BD_DIR); el paquete y el costo usan BD_X/BD_Y (la trampa sigue con
  TR_X/TR_Y). Texto del diálogo con la dirección. `bd_recv` acepta tierra o montaña (`bd_any`).
  prueba_caminos.py: MAL 0; las demás pruebas dan igual que la 1.0.108.0.
- **Publicada la 1.0.110.0 (3/11/2026)**: C.2 + botón de la torre «Build» → «Rebuild» (diálogos 39 y 41,
  RES_TEXTS). Los «Darklords.exe» que parecían la tanda eran otro programa (cliente YIIOT): la serie no corría.
- **Próximo paso:** (1.0.111.0 publicada: flecha roja de mvarrow en el diálogo del camino; el «build» de la torre sigue sin ubicarse, tarea 92 pide captura) F (puentes largos en derribar/reconstruir) y el puente nuevo sobre agua (C, punto 8); luego G.
  Tarea 91 del usuario: paso de montaña.
- **F + puente nuevo implementados (3/11/2026) en vista-aliada 1.0.117.0.**
  - F: `br_comp`, `br_canon`, `br_name` y `br_rebapply` ya recorrían hasta 8 casillas (inundación por lados,
    `br_xy` de 8). Lo único que suponía puentes cortos era el dibujo de los restos: el tramo medio (3,4)/(3,5)
    dibujaba cabeceras en sus dos bordes. Ahora `br_vfill` marca en la celda (0x2000 / 0x4000) los bordes que dan a
    otra casilla derribada y `br_vdraw` no los dibuja: solo se ven las cabeceras de la costa. Pruebas en
    prueba_puentes.py (puentes de 6 y 8; derribar, reconstruir, marcas).
  - Puente nuevo: `bd_brscan` (de 1 a `BD_BRMAX` = 8 casillas de clase agua sin estructura, edificio ni puente
    derribado, desde la orilla —la casilla de atrás no es agua— hasta una casilla que no es agua), `bd_brapply`
    (punta + medios + punta con `bd_brtab`, y `bd_fix` en los caminos de las dos orillas). `bd_pick` rota ahora por
    5 destinos: la casilla del líder (camino) y N, E, S, O (montaña → camino; agua → puente). `BD_PW` = 0 camino,
    0x100 | dir puente; viaja en la palabra libre del paquete 0x2a4 (+0x12) y `bd_recv` vuelve a medir con
    `bd_brscan` antes de cobrar. Precio por casilla: `BD_BRW` = 3 veinteavos (15 %) agua, `BD_BRL` = 5 (25 %) lava (desde la 1.0.118.0: 6 y 12, 30 % y 60 %),
    entero o nada. Renglón del menú: «Road/Bridge»; diálogo «Building a bridge» con la flecha.
  - Caso no cubierto: un puente nuevo pegado de costado a otro puente se une con él para derribar (la inundación
    de `br_comp` va por los 4 lados). Raro; si molesta, limitar la inundación a la línea recta.
- **G: medición hecha (3/11/2026), ver la sección G al final.** Antes de probar, tarea 96 del usuario. Frase vieja:
  PENDIENTE-construcciones.md, paso G".

## G. Puerto — medición del 3/11/2026 (Darklord.exe y 40 .SAV de `C:\Warlords3\Saves`)

Herramientas: capstone sobre todo el código (accesos al registro de ciudad, grafo de llamadas); los .SAV se leen
con el mismo desplazamiento que `prueba_emulada.py` (el bloque 0x536b30, de 0x2d894 B, trae ciudades y sitios).

- **Registro de ciudad** (0x537e2c + i*0xde, contador 0x537e2a): x +0, y +2, nombre +4, **+0xa4 = nivel de
  defensa, 0 = arrasada** (no es un sí/no: valores 0-3), +0xa5 dueño (8 = nadie; las 12 arrasadas de los .SAV
  tienen 8). **+0xdd no lo lee ni escribe ninguna instrucción** del exe y vale 0 en las 4349 ciudades de los
  .SAV (también 0xdb/0xdc valen 0, pero esos sí se usan): es la **marca «convertida en puerto»**. Viaja sola en
  el .SAV y en la sincronización del Puente.
- **Arrasar** (0x4d5cb0(ciudad, jugador), la que aplica el paquete): 0x49f900(3, jugador, 0, 0), +0xa4 = 0,
  0x46a3a0(ciudad, 8) (dueño 8 en el registro y en las 4 casillas: palabra 0 bits 10-13, +8 bits 3-6, +8 & 0x80
  muerta, +8 bits 8-9 nivel; estructura 3), 0x441290, historia 0x4a0400 evento 0x13, 0x46a120(ciudad) (avisa a
  7 subsistemas, cachés de la IA incluidas), mensajes, redibujo, 0x4a4f20. La conversión hace lo mismo **sin los
  mensajes ni el evento de arrasar**, más la marca +0xdd y las casillas nuevas.
- **Quién usa una ciudad arrasada** (218 lecturas de +0xa4; las que siguen de largo cuando vale 0):
  - **0x440be0(x, y)**, ciudad en la casilla: recorre la tabla por coordenadas **sin mirar +0xa4**; 33 llamadas.
    → saltear las marcadas: así la ciudad oculta no existe para nadie que pregunte por casilla.
  - **0x41e290** (evaluador de la meta 9, en 0x41e30a): una muerta es candidata a reconstruir. → saltear las
    marcadas (ahí mismo engancha ya `ai_brrebev`, en 0x41e4eb).
  - Menú de reconstruir (0x4b0660, 0x4b0915): obtiene la ciudad solo si la casilla es estructura 3 (0x4b07c6) y
    con 0x440be0: con las casillas cambiadas y el gancho de arriba, no aparece. Nada más que hacer.
  - Los demás (0x412020/0x412580/0x4127f0/0x412bc0 dibujo de ruinas en el panel de una ciudad ya elegida;
    0x435fd0, 0x442470, 0x464ac0, 0x46db00, 0x498fd0, 0x4c57d0, 0x4c58e0, 0x43b6d0): tratan a la muerta como
    «sin dueño / no sirve». No hace falta tocarlos. 0x461a60 (misiones): una misión sobre esa ciudad queda como
    con una arrasada; aceptable.
- **Puerto en la casilla** (los 9 de Tanda_Kor): estructura 4 (palabra 1 = byte bajo | 0x1c00), **palabra 0 |
  0x4000** (punto de embarque) y dueño 8 (0x2000), +8 = **0xa0** (tipo de sitio 0 en los bits 0-2, bit 3
  arrasado, bits 4-7 dibujo 0xa). Registro de sitio (0x55acb6 + i*0x96): x, y, nombre +4 (16 B), descripción
  +0x14, **tipo +0x94 = 0 para puerto**, arrasado +0x95. La tabla de medios 0x582158 (0xc0 = embarque) no va en
  el .SAV: la rehace 0x4a4f20 a partir del bit 0x4000.
- **Casilla común** (11772 de Tanda_Kor): palabra 1 alta 0x18 (estructura 0), +8 = 0x92. En una casilla de ciudad
  el terreno de abajo queda en la palabra 0 (bits bajos) y la palabra 1 lleva 0x04 de byte bajo.
  **Abierto:** qué terreno (byte bajo de la palabra 1 / pieza de dibujo) se les pone a las 3 casillas que
  vuelven a ser comunes y a la del puerto. Se decide con una prueba de juguete en el juego (convertir y mirar),
  copiando lo que tiene una casilla de pasto vecina.

### Diseño de G (etapa 1, humanos)

1. `pt_hidden(i)`: `[0x537e2c + i*0xde + 0xdd] != 0`. Ganchos en 0x440be0 (saltear) y 0x41e30a (saltear).
2. Renglón **«Make Port»** en el menú de la ciudad propia (diálogo a ubicar, como se ubicó el 34): solo si la
   ciudad es del jugador, humano, viva, alguna de sus 4 casillas toca agua por un lado y la tabla de sitios
   tiene lugar (< 50). Confirmación con el diálogo de reconstruir («Make Bridge»-style: «Turn X into a port:
   N gold? The city is lost.»).
3. Paquete propio `PT_PKT = 0x2a5` (bando, ciudad, casilla del puerto); `pt_recv` repite las comprobaciones, cobra
   y aplica en todas las PC: lo de arrasar sin mensajes, +0xdd = 1, 3 casillas a comunes, la de la costa a
   puerto, sitio nuevo (nombre «Port <ciudad>», tipo 0), 0x46a120, 0x4a4f20, redibujo.
4. Precio: `PT_X` veces el costo de fundar ciudad del bando (el mismo de 0x4b65e0); valor inicial 2, a calibrar.
5. Miniatura propia (decisión 6): dibujo nuevo en la hoja de sitios, en un índice libre de los bits 4-7 de +8.
   Primero se publica con el dibujo de puerto común; el dibujo nuevo va después.
6. Prueba de juguete `prueba_puerto.py` (emulada, como prueba_caminos): conversión, marca, 0x440be0 devuelve -1 en
   las 4 casillas, la meta 9 no la ofrece, sitio nuevo y 0x582158 = 0xc0; control: una ciudad arrasada común
   sigue siendo reconstruible.

### G implementado (3/11/2026, vista-aliada 1.0.118.0)

Cambios respecto del diseño de arriba:
- **Sin diálogo ni paquete nuevos.** El menú de la ciudad es el mismo menú de órdenes del grupo (diálogo 34,
  donde está Raze). El renglón de construir pasó a llamarse **«Build»** y el puerto es el **destino 5** de la
  rotación de `bd_pick` (0 líder, 1-4 N/E/S/O, 5 puerto). Camino y puente siguen pidiendo un ejército con «build»
  (`BD_HASB`, que deja `bd_check`); el puerto no. Viaja en el paquete 0x2a4 con `BD_PW = 0x8000 | ciudad` y x, y
  de la casilla del puerto. Texto del diálogo: «City into a port».
- **Las 4 casillas de la ciudad vuelven a ser comunes y el puerto va en el agua**, como todos los puertos de los
  .SAV: la primera casilla libre del anillo de 8 vecinas (`pt_ring`) de clase agua/lava, sin estructura, edificio
  ni puente derribado (`pt_water`). Casilla del puerto: palabra 0 dueño 8 | 0x4000, estructura 4, +8 = 0x20. Las 4
  casillas: sin 0x4000, estructura 0, palabra 1 baja 0, +8 copiado de la primera casilla de tierra común del anillo
  (o 0). **Abierto:** cómo se ven en el juego (tarea 97).
- `pt_ok` exige además que el bando tenga **otra ciudad viva** (no se puede eliminar a sí mismo).
- Precio `PT_FRAC` = 40 veinteavos (el doble del costo de ciudad del bando, con su rebaja, vía `bd_price`).
- Miniatura propia (decisión 6) sin hacer: usa el dibujo del puerto común.
- Ganchos: 0x440c26 → `pt_cityat` (la marcada no está en ninguna casilla), 0x41e30a → `pt_ai9` (la meta 9 la
  saltea). `pt_apply` no manda mensajes ni evento de historia.
- Prueba: `prueba_puerto.py`, MAL 0 (menú, rotación, costo, texto, envío, conversión completa y 9 controles, más
  la arrasada común que sigue siendo reconstruible). prueba_caminos.py ajustada (BD_HASB y precios del puente).
- En la misma versión: puente nuevo a **30 % agua / 60 % lava** por casilla (`BD_BRW` 6, `BD_BRL` 12), pedido
  del usuario en la tarea 96.
- Pruebas que ya fallaban en la 1.0.117.0 (comprobado compilando HEAD aparte): prueba_iaalianzas.py (2 fallas del
  evento 12), prueba_ariete.py y prueba_botones.py (cuentan archivos de recursos).

### Corrección 1.0.119.0 (4/11/2026, resultado de la tarea 97)

- La ciudad marcada como puerto seguía contando como arrasada: calavera en el minimapa y, al tocarla, la pantalla
  de ciudad caía al respaldo original (ciudad propia más cercana → mejora de defensa, el +3 de la ciudad del sur).
  Ganchos: 0x404893 → `pt_scrn` (pantalla de ciudad), 0x412320/0x412809/0x412bde → `pt_mm1/2/3` (los tres lazos
  del minimapa) saltean la ciudad con `PT_HIDE`.
- Acerca de (diálogo 94 del RES): sin las líneas de memoria; muestra «Patch vista-aliada» versión y fecha
  (de parches.txt y de git) y créditos @elCoprofago / Anthropic Claude, 2026 (`about_fill` en 0x4a97b7).
- Prueba nueva en `prueba_puerto.py`. Retest del usuario: tarea 98.

### Corrección 1.0.120.0 (4/11/2026, resultado de la tarea 98)

- Quedaba la calavera en el minimapa de «City Improvements»: otros dos bucles de ciudades, 0x412580 y 0x413000
  (el de lo conocido por el jugador, tabla 0x4f9870). Ganchos 0x4125a2 → `pt_mm4`, 0x41303b → `pt_mm5`.
- Acerca de: los valores 8-10 (tipo 0x13) tenían +0x24 = 0 (oscuro); «Version 1.0.3» y las líneas de Broderbund
  tienen 1. Se puso 1.
- Trucos del chat (0x455240) desactivados: 0x4552cf salta siempre a la salida 0x456444.
- Retest del usuario: tarea 99.

**Próximo paso:** resultado de la tarea 99. Si las casillas liberadas o el puerto se ven mal, ajustar la plantilla
de `pt_apply`. Etapa 2 (la IA convierte ciudades) y miniatura propia, solo si el usuario lo pide. Frase para
retomar: "Seguimos con PENDIENTE-construcciones.md, paso G, resultado de la tarea 99".

## Pedido del 9/11/2026 (sin empezar)

1. **Revisar fallas reportadas por el usuario:**
   - Las trampas no se pueden sembrar sobre pozos ya detonados: quitar ese límite.
   - No se pueden poner dos trampas en la misma casilla: permitirlo.
   - En partida multijugador, las unidades con bono «build» no pueden construir caminos, puentes
     ni pasos de montaña, aun con el último vista-aliada y ARMY.zip actualizado (publicado el
     9/11/2026). Averiguar la causa (¿bono no leído en multijugador? ¿orden bloqueada por el
     Puente/sincronización? ¿ARMY local distinto?).
2. **Construcciones nuevas, misma lógica casilla por casilla que caminos/puentes:**
   - Murallas: (i) empalizada, defensa equivalente a tres grupos de infantería pesada por
     casilla; (ii) muro de piedra, impasable salvo atravesándolo con camino, que cuesta el doble
     que construir camino en montaña.
   - Torre de vigilancia: 1 casilla, hasta 8 unidades, +1 de defensa, +5 de visión.
   - Faro costero: igual que la torre, +6 de visión.
   - Gráficos a cargo de Claude: muros tomando cortes de ciudades; torres reciclando o
     modificando ruinas; faro propio.
3. **Limitar la pausa de la partida a 3 por jugador.**

Retomar con: *"Seguimos con PENDIENTE-construcciones.md, pedido del 9/11"*.

### Parte 1, 9/11/2026 (vista-aliada 1.0.146.0)
- Trampas sobre gastadas: hecho (ver parches/vista-aliada/PENDIENTE-pozos-y-trampas.md).
- Dos en la misma casilla: ya existía apilar (propia, activa, fuera de ciudad); se espera el caso concreto (tarea 136).
- «Build» en red: no es del parche. bd_check lee el bono del registro de armas de la partida (0x53c410), que se copia
  del .ARM al crear la partida. dia-noche3.SAV no tiene ninguna unidad con «build» (sí Archers, sin el bono). Hace
  falta partida nueva. goblins.ARM tiene «build» en la ranura de combate (+0xd6), no en las de movimiento (+0xb2).
- Próximo: parte 2 (murallas, torres, faros), después la 3 (pausas). Frase: "Seguimos con
  PENDIENTE-construcciones.md, pedido del 9/11, parte 2".

### Parte 2, diseño (9/11/2026)

**Tabla propia de obras** (`ob_*`, como la de pozos pero aparte: la de pozos tiene 64 lugares que ya se llenan con
trampas, y muchos consumidores de pozos suponen sus 4 tipos). Registro de 8 B: x, y, tipo, estado, dueño, libre.
`ob_map`: un byte por casilla (índice + 1). Tope 255. Va al .SAV detrás del bloque POZO ('OBRA' + cantidad + tabla;
un .SAV sin el bloque carga sin obras), viaja por red como bloque 10 al empezar y entra en la suma de sincronía.
Tipos: 1 torre, 2 faro, 3 empalizada, 4 muro de piedra.

**Etapa A: torre y faro** (constructor con «build», en la casilla del líder; tierra sin estructura de ciudad/sitio
ni otra obra; el faro, además, con agua en alguna de las 4 vecinas). Destinos nuevos de la rotación de `bd_pick`.
- Visión (gancho al final de 0x441540, que despeja la niebla con 0x441720(x, y, radio)): radio 5 la torre, 6 el
  faro, para el dueño y sus aliados con vista aliada. Sin niebla no hay nada que hacer.
- Defensa: +1 de fuerza a cada defensor de la batalla cuya casilla tiene la obra (en `bridgeab`, 0x467d0e;
  defensor = 5.º argumento de 0x467240 en 0).
- Dueño: el que construye; pasa al bando que entra en la casilla (gancho de paso, corre igual en todas las PC).
- 8 unidades: ya es el tope de una casilla; no hace falta nada.
- Dibujo: cuadro propio en la hoja del parche (torre a partir de una ruina; faro propio).

Hecha en vista-aliada 1.0.148.0 (9/11/2026): tipos 4 torre y 5 faro (tope 64 obras), precio 50 % de fundar una
ciudad (a confirmar, TAREAS 137); se construye en la casilla del líder y no sobre un camino. Prueba: `prueba_obras.py`.

**Etapa B: murallas.** Muro de piedra = intransitable en el grafo de pasos salvo con camino; camino sobre muro =
2 × montaña (10 veinteavos). Empalizada (respuesta del usuario, 9/11/2026): cada casilla de muralla construida tiene esas
defensas, como si la defendieran 3 grupos de infantería pesada que el atacante tiene que vencer; solo la construyen
unidades con «build»; cuesta el doble de un paso montañoso (2 × 5 veinteavos = 50 % de fundar una ciudad).
Orden pedido: primero el tope de pausas (hecho en 1.0.149.0, TAREAS 138), después las murallas.

**Diseño de la etapa B (9/11/2026, a implementar en este orden):**
1. *Muro de piedra* (tipo 7): obra de la tabla `ob_*`. En el grafo de pasos (0x4a4f20) la casilla es intransitable
   para todos salvo que tenga camino; poner camino sobre un muro cuesta 10 veinteavos (2 × montaña). Se construye
   como la torre (posición nueva de `bd_pick`), precio 10 veinteavos. Prueba: `prueba_murallas.py`.
   Hecho en vista-aliada 1.0.150.0 (posición 8 de `bd_pick`, `po_pf` lo bloquea, `bd_ok` admite camino encima a
   OB_MCAM; ni visión ni +1 de defensa). Arreglado de paso: `bd_check` probaba el faro en (0, y).
2. *Empalizada* (tipo 6): precio 10 veinteavos. Un bando que no es el dueño ni su aliado no entra caminando: tiene
   que atacarla. La batalla (0x469ed0 → 0x464ac0 arma la ficha) suma a los defensores 3 grupos del tipo de
   infantería pesada del bando dueño (unidades virtuales: no existen fuera de la batalla, no cobran mantenimiento),
   además de los ejércitos reales que haya. Si el atacante gana, la empalizada se destruye (sale de la tabla) y
   entra; si pierde, queda entera con sus 3 grupos para la próxima. Falta averiguar: dónde 0x464ac0 lee la lista
   de defensores (pila de la casilla) y cómo identificar «infantería pesada» en los tipos del bando (nombre en +0x90
   del registro de 0xfc bytes de 0x53c410).
   Averiguado (9/11/2026): 0x464ac0(atacante, x, y, ficha) arma la ficha: +0 bando, +1 terreno (palabra 0 de la
   casilla, bits 10-13), +2 ciudad o -1, +4/+6 x, y; los defensores salen de 0x4411b0(x, y, lista) (índices de
   ejércitos de la tabla 0x54fe50 en la casilla; con ciudad, sus 4 casillas). Camino elegido: antes de 0x4411b0,
   crear 3 ejércitos reales temporales del dueño en la casilla (con la función del juego que crea un ejército) y,
   al terminar 0x469ed0, borrar los que sobrevivan; así la batalla, la animación y las probabilidades los tratan
   como tropa común. Falta: la función de alta/baja de ejércitos y el tipo «infantería pesada» de cada bando.

## Pedido del 9/11/2026 (después de 1.0.150.0)

Hecho en 1.0.151.0: la puerta (camino sobre el muro) cuesta el 25 % de una ciudad (OB_MCAM = 5). Por la puerta pasan
solo el dueño y sus aliados (`po_pf`, con `fogally`). Probado en `prueba_obras.py`.

Hecho en 1.0.152.0 (9/11/2026):
- **Gráficos nuevos** (`parches\vista-aliada\obras_img.py`): render por vóxeles, de arriba y de frente como el
  juego, con sombra al sureste. Cada obra se dibuja en un lienzo de 3x3 casillas cortado en 9 piezas; `ob_draw`
  pinta en cada celda las piezas de la obra propia y de sus 8 vecinas (así la torre asoma sobre la casilla de arriba
  y los muros empalman sin cortes aunque el juego repinte solo algunas celdas). Las piezas van en las filas 1..4 de la
  hoja de `RUINS\pozos.pcx`. Muro de piedra con la piedra y las almenas de `RUINS
uin_lrg.PCX`; torre redonda con
  almenas; faro a franjas con linterna encendida. El tramo de piedra que corre de norte a sur es más ancho (pedido
  del usuario: de costado se veía muy fino).
- **Muro en 8 direcciones**: en `bd_pick` las posiciones 8..15 son el muro hacia N, NE, E, SE, S, SO, O, NO, con las
  flechas de `mvarrow.pcx` (`bd_arrows` 8..15). `BD_PW = 0x4000 | (d + 1) << 8 | OB_MURO`; `bv_ob` guarda d + 1 en el
  byte +5 del registro. Cada bloque se une con la dirección elegida, su opuesta y los vecinos de su mismo tipo
  (`ob_wmask`; la diagonal solo si ningún vecino ortogonal la cubre). Los muros viejos (sin dirección) se unen solo
  con sus vecinos. Probado en `prueba_obras.py`.
- La empalizada, sin cambios de reglas (también se dibuja con el gráfico nuevo y se une igual).
Prueba en el juego: tarea 141 de `TAREAS.md`.

## Botonera de construir (pedido del 9/11/2026, va DESPUÉS de los gráficos y el muro en 8 direcciones)

Hoy todo se construye con un solo comando que hay que apretar varias veces hasta llegar a la obra deseada (camino,
puente, torre, faro, muro): muy engorroso en plena batalla. El usuario pide:
- mover **construir** al botón de la torrecita (el de la almena, en la botonera del grupo, a la izquierda del de
  «pasar turno»; su función original casi nadie la usa);
- mover también **reconstruir** (rebuild) a ese mismo botón;
- que ese botón centralice todo lo de construir y reconstruir: elegir directamente la obra (camino, puente, torre,
  faro, muro de piedra, empalizada) en vez de recorrerlas de a una.
Antes de tocarlo: averiguar qué hace hoy ese botón (su manejador en el exe) y dónde dejarlo, si hace falta.
Captura del usuario: el botón señalado es el de la almena roja, arriba a la derecha de los de mover y acampar.

**Hecho en vista-aliada 1.0.153.0 (9/11/2026).** La torrecita (en las dos barras del grupo) abre el menú de órdenes en
modo construir (`bm_*` en `build.py`): Rebuild City/Site, Road, Bridge, Port, Watchtower, Lighthouse, Stone Wall y
Trap, cada renglón encendido solo si esa obra se puede hacer desde la casilla del líder. Otro clic en el mismo renglón
pasa a la siguiente casilla o dirección de ese tipo (`BD_CAT` filtra la rotación de `bd_pick`). «Build» y «Build
Trap» salieron del menú del clic derecho. Falta: la empalizada (espera la batalla, etapa B). Prueba: tarea 142.
Pendiente técnico: instalar en `C:\Warlords3`, correr todas las `prueba_*.py` y publicar (el juego estaba abierto).

**vista-aliada 1.0.154.0 (9/11/2026), pedido del usuario:** el muro de piedra se puede construir sobre un camino
(no puente), y queda hecho puerta (`ob_okt`). Gráfico: muro de 16 de ancho y 32 de alto (como el frente de la ruina
grande), almenas más grandes, y sin los píxeles casi blancos ni la hiedra verde de la textura (`_limpia` en
`obras_img.py`). Prueba: tarea 143.
vista-aliada 1.0.155.0: sin las rayas tipo «código de barras» (textura por la cara que se ve, hiladas
horizontales; arriba piedra lisa).
vista-aliada 1.0.156.0: la calzada de arriba del muro con la textura del camino de tierra (road0.PCX) en gris oscuro.

### 1.0.157.0 (9/11/2026)
Muro de piedra rehecho para parecerse a la ruina: hiladas de 4 px (junta oscura), ladrillos de 6 trabados, contados a lo
largo del muro (u = a) y desde la calzada hacia abajo, así siguen las diagonales; moldura clara y línea negra bajo la
calzada; parapeto de 3 en los bordes con almenas de 5 cada 8; en el centro solo pilares en las esquinas.

### 1.0.158.0 (9/11/2026)
Las puntas de los tramos mostraban rayas (el centro cuadrado usaba u = gx también en los costados). El centro del muro
de piedra pasa a ser una torre redonda (radio RT = 15, 4 más alta que el muro) con ladrillos contados alrededor
(u = ángulo × RT), luz según la normal y almenas en el borde.

### 1.0.159.0 (9/11/2026)
Quedaban rayas donde el tramo topa con la torre: los tramos ya no se dibujan dentro de la torre, y la cara del tramo junto
a la torre usa los ladrillos de la torre (u = ángulo × RT); la cara del extremo lejano los cuenta a lo ancho (u = w).

### 1.0.160.0 (9/11/2026)
El juego pinta las casillas de norte a sur: un tramo de la casilla de más al sur tapaba la torre de su vecina del norte
(calzada y almenas cortadas en los cruces). Cada tramo se dibuja ahora junto con las dos torres que une (_muro_piedra),
así lo de adelante tapa a lo de atrás en cualquier orden. prev2.py del scratchpad imita ese orden (od_ord).

### 1.0.161.0 (9/11/2026)
- Muros entrecortados: ob_wmask sumaba siempre el brazo de la dirección de construcción, aunque esa casilla estuviera
  vacía; desde 1.0.160 cada brazo trae la torre vecina, así que aparecían torres y tramos fantasma. En el muro de
  piedra solo cuentan los vecinos con muro; uno aislado es solo la torre.
- Gris del muro más claro (ladrillos 87..127, como las ciudades de cit_*.PCX: 63..159, mucho 103).
- «Build Trap» volvió al menú de órdenes (TR_HOT); la botonera de construir tiene 7 renglones.
- La botonera de construir abre su propio diálogo, BM_DLG = 133 (bm_open, copia de 0x4afc20): los controles del 34
  sobre SETS\Fantasy\dlg_bm.pcx (archivo 172), que es DLG_PU11 de 204 de alto en lugar de 284.
