# PENDIENTE — Construcciones del jugador (puertos, puentes, caminos)

Diseño acordado con el usuario el 2-3/11/2026. Nada implementado todavía; medido el formato del bono (ver abajo).

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
  derribar/reconstruir recorra la tira entera. Hay que buscar si el juego de terrenos ya trae
  la pieza de medio.

Siguiente: contar los sitios de los mapas del clan (margen hasta 50) y medir si el diálogo 34
admite un renglón más sin agrandar la ventana.
