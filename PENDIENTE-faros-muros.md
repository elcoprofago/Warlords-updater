# Pendiente: luz de los faros y destrucción de muros (pedido del 10/11/2026)

Pedido completo:
1. Los faros iluminan 6 casillas, en mapas con niebla y de noche, con el mismo degradé que las ciudades.
2. Los muros se pueden destruir: a) por el dueño, seleccionando un bloque y usando "Raze"; b) por un enemigo,
   atacando la muralla.
3. Cada casilla de muro suma, en este orden: +3 Assassin, +5 Missiles, +5 Acid, +7 Fortify, +5 Life Drain, al poder
   de cada pila alojada en la muralla.
4. Imagen del bloque de muro roto, con el humo de las trampas detonadas.

## Hecho (1.0.170.0 y 1.0.171.0, commit de esta fecha; falta instalar y publicar: el juego estaba abierto en C:\Warlords3)
- Punto 1: `dn_lights` recorre OB_TAB y estampa cada faro (OB_FARO) con radio 6, cuadrado como ciudad
  (DN_FARO = OB_VISTA[OB_FARO]); con Hidden Map, solo si la casilla está explorada. Prueba: prueba_dianoche.py.
- Punto 2a: `wl_razelk` (menú 0x4b05d1 y tecla 0x44c2d7; la IA sigue con br_razelk), `wl_find`, `wl_text`, `ob_del`,
  `wl_apply` (código WL_CODE=0x7000+índice por la orden de arrasar de siempre). Prueba: prueba_obras.py (sección
  «derribar muros»).

- Luz del faro (cambio del 10/11/2026, 1.0.172.0): se proyecta hacia el mar. `fr_stamp` alumbra con degradé 5
  casillas sobre agua (`aimed` & 0x80) y 1 sobre tierra (distancia max + min // 2, niveles FR_TAB 1,2,3,4,5,7).
  Prueba: prueba_dianoche.py (faro en la costa; tierra a 3 casillas queda oscura).
- Torre de vigía (indicación del 10/11/2026): alumbra 3 casillas (DN_TORRE). El +1 de fuerza al grupo que está en
  ella ya existía desde la etapa A (bridgeab: defensores que no son héroes).

## Estado al 11/11/2026 (para retomar en sesión nueva)
- Hecho y aprobado por el usuario: ataque al muro, caída del bloque al morir los 24 arqueros, daño progresivo con
  copias dañadas de las capas (od_put, 3 niveles), humo nuboso animado (dm_put), muralla gris azulado suave
  (vista-aliada 1.0.192.0, tarea 167 cumplida).
- **Hecho: los bonos (vista-aliada 1.0.193.0, 11/11/2026).** Valores fijados por el usuario: **+5 Missiles, +5 Acid,
  +5 Fortify, +5 Life Drain** (reemplaza el +7 Fortify anterior; Assassin afuera). Ver «Hecho: bonos del muro».
  Prueba en el juego: TAREAS 168.
- **Próximo paso:** la IA que repara sus muros (decidir junto con los bonos; TAREAS 159 es la prueba de Repair).

## Hecho: bonos del muro (1.0.193.0, 11/11/2026)
- Quién: los **defensores** de una casilla que es un bloque de muro de piedra en pie (OB_MURO, +7 < 24) de su mismo
  bando, o que está a 1 casilla (también en diagonal) de uno (`wb_near`). Incluye los arqueros virtuales y las pilas
  alojadas. El atacante nunca los recibe. Valen también en las probabilidades previas al ataque (0x464a30 usa 0x464ac0).
- Por unidad (`wb_unit`, en 0x4679e3 del armado 0x467240, solo con el argumento atacante = 0): ficha +0x16 (Missiles,
  la que el juego llena desde la habilidad 30) y +0x1a (Acid, habilidad 38), +5 cada una, sumadas.
- De grupo (`wb_grp`, en lugar de la llamada a 0x468440 del defensor en 0x464df2): grupo +4 (Fortify, código 6) y
  +0x16 (Life Drain, código 54), +5 cada uno, sumados al máximo del bando.
- Qué hace cada uno (desensamblado, 11/11/2026): **Fortify +N** = +N de fuerza a cada unidad del grupo durante la
  batalla, menos el **Siege** del enemigo (código 5, su contrario; par «FortifySiegeLimit» del juego), dentro del tope
  general de bonos (0x56951c, «FinalBonusLimit»); se calcula en 0x4696c0 y se aplica en 0x4698b0. **Life Drain +N** =
  cada unidad enemiga pierde N hits al empezar (mínimo 1, tope 4). Missiles y Acid son chances por unidad
  (BaseAcidChance, etc. en la configuración del juego).
- Corrección a «Averiguado»: Missiles va a la ficha +0x16 y Assassin a +0x17 (no +0x18 / +0x17 como decía).
- Prueba: prueba_muroataque.py, sección «bonos del muro» (con controles: a 2 casillas, atacante, otro bando, bloque
  caído, torre, neutral).

## Diseño del ataque al muro (indicaciones del usuario, 10/11/2026)
- Cada bloque sin grupo encima se defiende como si tuviera 3 arqueros comunes virtuales ("unidades fantasma", como
  la fuerza de una ciudad): no se ven en el mapa, no salen ni huyen; en la pantalla de combate se ven caer uno a uno.
  Caídos los 3 de un bloque, el bloque cae y el enemigo puede pasar (imagen de muro roto con humo, punto 4).
- Bonos de esos arqueros: +5 Missiles, +5 Acid, +7 Fortify, +5 Life Drain. (El pedido anterior decía también
  +3 Assassin; la indicación nueva no lo nombra: se toma la nueva.)
- Grupos alojados: los que están sobre casillas del muro o a 1 casilla de él; reciben esos bonos sumados a lo suyo.
- Confirmado por el usuario (10/11/2026): cada bloque tiene **3 pilas de 8 arqueros (24 arqueros)**, no 3 arqueros.
  Los que van muriendo se anotan en el bloque: un ataque posterior encuentra menos defensa. Assassin queda afuera.
  Ojo: la ficha admite hasta 32 defensores (0x464ac0, como una ciudad de 4 casillas): 24 virtuales + 8 de una pila
  alojada llenan el tope; con más pilas alojadas hay que decidir el reparto (técnico: mío). Byte +7 del registro =
  arqueros **muertos** (0..24): los muros ya construidos tienen 0 y quedan con los 24; con 24 el bloque cae.

## Indicaciones del usuario (10/11/2026, después del tipo y la baja)
- **Estadísticas:** los arqueros virtuales son puntos de defensa de la muralla, no ejército: no cuentan en las
  estadísticas de armas. Técnico: en 0x465c80, para las ranuras virtuales saltear 0x4039a0 (y el aviso 0x461a60);
  revisar también que no entren en conteos del atacante (bajas enemigas causadas) ni en el historial/IA (ia_bat).
- **Reparar:** el dueño de un bloque con arqueros muertos (byte +7 > 0) puede repararlo pagando el costo
  proporcional: precio del bloque (OB_FRAC, el mismo que construirlo) * muertos / 24. Va en la botonera de «Build»
  como orden nueva «Repair» (reparar, no reconstruir: el bloque sigue en pie y vuelve a 0 muertos). Sobre un bloque
  caído (24) no aplica: ese se construye de nuevo. Mismo camino que las demás órdenes de obra (bd_pick / bd_ok /
  bd_apply, código por red como wl_apply). Se programa después del ataque (sin daño no hay qué reparar ni cómo
  probarlo en el juego); la IA: que repare sus muros si le alcanza el oro (decidir junto con el ataque).

## Hecho: orden «Repair Wall» (1.0.179.0, 10/11/2026)

- Renglón 8 de la botonera «Build»: encendido si hay un bloque de muro de piedra propio dañado (+7 entre 1 y 23) en la casilla del líder o en una vecina y el oro alcanza; no pide constructor. Cada clic ofrece el siguiente bloque (wr_scan, wr_vars).
- Precio bd_price(OB_FRAC) * muertos / 24 (wr_price); viaja como BD_PKT con BD_PW = 0x4000 | OB_REP (0x10); bd_recv vuelve a comprobar, cobra y pone +7 = 0. Texto «Repairing a stone wall».
- Falta: la IA no repara (decidir junto con los bonos). Tarea 159.

## Hecho: Longbows, portón oscuro, banderas en caminos y reintegro del 75 % (1.0.178.0, 10/11/2026)

- wv_type: Longbows del bando si los tiene (nombre «longbow»), si no Archers, si no el primer tipo con Missiles. Un bando sin Longbows en su set no puede tenerlos: el juego solo crea ejércitos de los 15 tipos del bando.
- Hueco del portón abierto en negro (obras_img.py, `_arco`).
- Banderas solo en bloques con camino (ob_road en fl_has y en la pasada de puertas de ob_draw); el arco y el portón siguen en todo bloque.
- wl_apply: muro y empalizada devuelven al dueño el 75 % de bd_price(OB_FRAC) con 0x43fd60; torre y faro, nada. Tarea 158.

## Hecho: puerta en todo bloque y Raze de torres y faros (1.0.177.0, 10/11/2026)
- Informe del usuario: «desaparecieron las puertas y las banderitas». No faltaba nada: od_gate, od_dg y ob_near
  dibujaban la puerta solo sobre un camino, y en build_02.SAV ningún bloque de muro estaba sobre camino. Como desde
  la 1.0.175 todo bloque se atraviesa, ahora todo bloque de muro de piedra es puerta (arco, portón y banderas), con
  o sin camino. Los tramos diagonales llevan arco en cada bloque (od_dg), sin torre. Prueba: prueba_obras.py.
- Raze de torre de vigía y faro propios: wl_find y wl_apply aceptan OB_TORRE..OB_MURO; wl_text tiene 9 textos por
  tipo («the watchtower …», «the lighthouse …»). Pruebas: prueba_obras.py; prueba_puentes.py, que había quedado
  vieja desde la 1.0.176.

## Hecho: Raze desde la barra e informe de la torre (1.0.176.0, 10/11/2026)
- Causa de «Raze encendido que no hace nada» (usuario: no aparecía ninguna ventana): el botón Raze de las dos barras
  del grupo (0x4205c1, 0x41c98c) llamaba a br_razelk (sitios y puentes), no a wl_razelk. Ahora las cuatro entradas
  (barras, menú, tecla) usan wl_razelk. Prueba: prueba_obras.py.
- Faro a 6: confirmado por el usuario en el juego.
- `ui_tower` (0x45e77b, caso de la fuerza violeta del informe 0x45e580): +1 en torre o faro para quien no es héroe,
  como bridgeab, siempre (no solo en batalla). Prueba: prueba_informe.py. En batalla el +1 sigue siendo solo del
  defensor (bridgeab).

## Hecho: muros transitables y faro a 6 (1.0.175.0, 10/11/2026)
- Informe del usuario sobre la 1.0.174.0: los ejércitos no entraban a ningún muro y Raze «no hace nada».
- `po_pf`: el dueño y sus aliados pasan y se alojan en un bloque de muro con o sin puerta; el enemigo no (salvo
  como destino de ataque, wl_war). prueba_obras actualizada (dueño y aliado sin puerta: pasa; enemigo: cerrado).
- Faro: DN_FAGUA = 6 (luz sobre el mar), FR_TAB hasta 7; prueba_dianoche OK.
- Raze: no reproducido. La cadena completa (wl_find, wl_razelk, diálogo 0x4951b0, botón código 0x7000, paquete
  0x18d, wl_apply, ob_del) funciona en emulación. Prueba en el juego con los pasos exactos: TAREAS 155.

## Hecho: ataque al muro, pasos 1 y 2 (1.0.174.0, 10/11/2026)
- `po_pf`: un bloque en pie de un bando en guerra con el que mueve (`wl_war`: OB_MURO, +7 < WV_MAX = 24, DIPLO = 2)
  puede ser destino del camino; no se atraviesa.
- `wv_step` (0x49e434): casilla vacía con ese bloque -> código 2 (ataque).
- `wv_pre` (en lugar de 0x464ac0, en 0x469f35): pone el dueño del muro en la palabra +0 de la casilla y crea
  min(24 - muertos, 32 - defensores reales) arqueros (`wv_type`: «archers» del dueño, si no el primero con Missiles)
  con `wv_new` (0x46c330 + 0x43b6d0, ciudad -1). No crea si la casilla está ocupada por otro bando.
- `wv_stat` (0x4660d1): un arquero virtual muerto se da de baja sin estadísticas ni aviso.
- `wv_post` (en lugar de ia_bat, en 0x469f54): llama ia_bat, cuenta muertos, da de baja a los vivos, suma al +7 y
  con 24 derriba el bloque (ob_del, 0x4a4f20, ob_fogme); rehace la ocupación (0x441290) y redibuja.
- Pruebas: prueba_muroataque.py (wl_war, wv_step, wv_pre, wv_stat, wv_post, con controles) y prueba_obras.py
  (po_pf: el muro enemigo como destino).
- Sin verificar en el juego: si el atacante entra a la casilla cuando cae el muro; si el informe de la batalla
  (0x405a10) lee bien los registros dados de baja; que ia_bat (registro de batallas de la IA) cuenta a los arqueros
  virtuales como defensores (queda así por ahora). Prueba en el juego: TAREAS 154.
- Fallas previas, no de este cambio (iguales con la 1.0.173.0): prueba_botones (controles 138),
  prueba_iaalianzas (evento 12), prueba_obsoletos.
- Sigue: paso 3 (bonos), orden Repair, IA que repara, imagen del bloque roto (punto 4).

## Plan técnico (sin empezar)
1. Movimiento: hoy po_pf cierra el muro al enemigo; hay que convertir «entrar a un muro enemigo» en ataque
   (como a una casilla con ejércitos enemigos) en lugar de camino cerrado.
2. Batalla: 0x469ed0 -> ficha 0x464ac0 (defensores en +0x12e + i*0x24, palabra +0 = ejército). Los arqueros virtuales
   tienen que ser ejércitos reales temporales del dueño del muro (ranuras libres), creados al armar la ficha y
   borrados después de 0x465c80, anotando cuántos murieron en el byte +7.
3. Bonos múltiples: una unidad tiene una sola habilidad (+0xe6/+0xe8). Hay que aplicar los efectos de Missiles (30),
   Acid (38), Fortify (6) y Life Drain (54) leyendo cómo los usa 0x467885..0x467958 y 0x468440, y sumarlos aparte
   para los arqueros virtuales y los grupos alojados (copias del registro como nm_unit, una por habilidad, no alcanza).

- Cerrar el juego, `python parches\vista-aliada\build.py` (instala en C:\Warlords3), correr las prueba_*.py sin
  argumentos y `tools\publicar-parche.ps1 vista-aliada`.
- Puntos 2b y 3 (ataque enemigo al muro con los bonos): falta decidir qué defiende un bloque sin pila encima y qué
  pilas cuentan como «alojadas» (¿las del dueño sobre las puertas?). Ingeniería inversa: batalla 0x469ed0,
  defensores 0x4411b0, habilidad única por unidad (+0xe6 código, +0xe8 valor; 6 Fortify, 28 Assassin, 30 Missiles,
  38 Acid, 54 Life Drain) — una unidad tiene una sola habilidad, así que 5 bonos exigen otro mecanismo.
- Punto 4: imagen del bloque roto en obras_img.py / RUINS\pozos.pcx.

## Averiguado (ingeniería inversa, 10/11/2026)
- Habilidades por unidad (0x467885..0x4679e3, unidad de la ficha en [esp+0xb4]): Missiles 30 (0x1e) -> unidad +0x18,
  Acid 38 (0x26) -> +0x1a, Assassin 28 (0x1c) -> +0x17 (también 26 -> +0x14, 27 -> +0x13, 40 -> +0x1c, 33 -> +0x1b,
  32 -> +0x16? ver el orden de los mov en 0x46799e..0x4679e3, 39 -> +0x19, 41 -> +0x1d). Sumar varias a la vez es
  escribir esos bytes después de 0x4679e3 para los arqueros virtuales y los alojados.
- Habilidades de grupo (0x468440, tabla 0x469684 / saltos 0x469634, registro en ecx desde 0x46907c): se guarda el
  máximo del bando en la estructura esi: Fortify 6 -> [esi+4], Life Drain 54 -> [esi+0x16]. Para el bando del muro:
  poner max(actual, 7) y max(actual, 5) al final de ese armado (falta ubicar el final de 0x468440 y quién es esi).
- Cadena del ataque (10/11/2026, desensamblado del original):
  - Paso 0x49e280(p, &x, &y, &mov, &n) recorre el camino del grupo; por casilla lee la palabra del mapa
    (0x503e58: bit 0x8000 ocupada, dueño = (w & 0x3c00) >> 10). Ocupada por otro y diplomacia
    [0x55ee4c + p*56 + dueño] == 2 (guerra) -> devuelve **2** con x, y de la casilla (0x49e57d). Con otro estado,
    código 7 (entrar). Se engancha ahí: casilla con muro enemigo en pie y en guerra -> código 2 aunque esté vacía.
  - Código 2 en 0x49c9f0 (tabla 0x49d174, entrada 2 = 0x49d029): guarda el blanco en 0x572998[p] / 0x5729a8[p]
    (lector 0x49c300) y para con 0x49c960(p, 2). El humano confirma en 0x4c4da0 (0x4648d0(p, x, y): rechaza si
    0x49e770(x, y) está en la lista 0x5729b8 de 40 casillas o si no le queda movimiento; si no, 0x4b9330 manda la
    batalla por red y espera). Código 6 (0x49d0a1) / 0x49d151 -> 0x469ed0(p, x, y) en todas las PC.
  - 0x469ed0: 0x4debd0(semilla) -> 0x464ac0(p, x, y, ficha) -> 0x466c90 -> 0x464ea0 (pelea) -> 0x465c80 (resultado).
  - 0x464ac0: ficha [+0] atacante, [+1] defensor = dueño de la palabra del mapa (casilla vacía: el que diga la
    palabra; hay que forzar el dueño del muro), +4/+6 x, y; defensores en [esp+0x30] por 0x4411b0(x, y, lista)
    (sin ciudad: 0x464c3d..0x464c51, ya enganchado por crdef del convoy, que suma casillas con 0x4411b0 hasta 24);
    cuenta [esp+0x12] -> [+0xd]; cada defensor 0x467240(ejército, x, y, ficha+0x12e+i*0x24, 0); habilidades de
    grupo 0x468440(n, lista, x, y, 0x5699c8 + p*0x17).
  - Ejércitos: registro 0x1c bytes desde 0x54fe50 (+2 x, +4 y, +6/+8 destino, +0xe palabra con dueño
    (& 0x1e0) >> 5, +0x12 bit 0x4000 = vivo); cantidad en [0x54fe50]. 0x43b510 busca lugar para uno nuevo
    alrededor de una casilla (25 vecinos, tabla 0x4fabc0/0x4fabf8); 0x43b6d0 calcula las cifras de uno nuevo
    (ciudad, jugador, tipo). Alta: **0x46c330(dueño)** busca la primera ranura sin el bit vivo (1..999), sube
    [0x54fe50] si hace falta, la limpia (0x46c3c0), pone el dueño y los bits vivo; devuelve eax = puntero al
    registro (base 0x54fe52 + e*0x1c: +0 x, +2 y, +4/+6 destino, +0xc dueño & 0x1e0, +0x10 bit 0x4000 vivo) o 0.
    Ejemplo de relleno completo después del alta: 0x43ace9..0x43ae40 (x, y, destino -1, palabra del mapa con
    0x8000 y el dueño, cifras desde el registro del tipo).
  - **Tipo** (10/11/2026): palabra +0xe del registro (base 0x54fe50; +0xc desde el puntero de 0x46c330), bits 0..4 =
    tipo dentro de la tabla del dueño; 0x10 = héroe (0x4057f7, 0x4408e2). Registro del tipo = 0x53c410 +
    (dueño * 16 + tipo) * 0xfc (0x40e138, 0x410454, 0x41ceb9). Resto de la misma palabra: bits 5..8 dueño, 9..12 y
    13..15 cifras (0x43ad68..0x43adba). Palabra +0x10 (puntero +0xe): bits 8..14 movimiento máximo; +0x12 (puntero
    +0x10): bits 0..6 movimiento actual. Para los arqueros virtuales falta ubicar «Archers» en la tabla del dueño
    (los 16 tipos de 0x53c410 + dueño * 16 * 0xfc; buscar el offset del nombre en el registro del tipo).
  - **Baja**: 0x46c470(ejército, 0) (cdecl, add esp 8). Lo saca de los grupos seleccionados (0x561e2c, 8x10) y de
    las listas del bando (0x56ea94, 0x485c00); si no es héroe salta a 0x46c967: limpia el registro (0x46c3c0), apaga
    vivo (+0x12 & 0xbfff), x = y = -1 y dueño 8 (+0xe & 0xff1f | 0x100). **No toca la palabra del mapa** (bit 0x8000
    / dueño): los arqueros virtuales no deben marcarla, o hay que restaurarla. [0x54fe50] no baja.
  - Resultado de la batalla 0x465c80, defensores (0x4660b8..0x4661ee): ranura i de la ficha +0x12e + i*0x24 =
    ejército, +0x130 tipo (0x10 héroe; 8..0xb otra clase), +0x133 marca, **+0x134 = vivo**. Muerto: 0x4039a0
    (estadísticas del bando, por clase) y 0x461a60 (aviso), después 0x46c470(e, 0). Vivo: palabra +0x14 & 0xbfff.
    Para el muro: después de 0x465c80, contar las ranuras virtuales con +0x134 = 0 (sumarlas al byte +7 del bloque)
    y dar de baja con 0x46c470 a las que sobrevivieron. Ojo: los muertos virtuales entran en las estadísticas del
    dueño del muro (0x4039a0); decidir si se descuentan.
- Orden de trabajo que sigue: no publicar el paso 1 solo (un muro vacío atacado sin defensores se perdería en una
  batalla sin defensa). Pasos 1 y 2 van juntos: código 2 ante muro enemigo + crdef con los arqueros virtuales +
  anotar muertos en +7 después de 0x465c80 y derribar el bloque con 24.
