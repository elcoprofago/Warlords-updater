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

- Torre de vigía (indicación del 10/11/2026): alumbra 3 casillas (DN_TORRE). El +1 de fuerza al grupo que está en
  ella ya existía desde la etapa A (bridgeab: defensores que no son héroes).

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
    (ciudad, jugador, tipo). **Falta** ubicar la función que da de alta el registro (la que llama a 0x43b6d0 en
    la producción: 0x43aab4 / 0x43b24b / 0x43b437) para crear los arqueros virtuales.
- Orden de trabajo que sigue: no publicar el paso 1 solo (un muro vacío atacado sin defensores se perdería en una
  batalla sin defensa). Pasos 1 y 2 van juntos: código 2 ante muro enemigo + crdef con los arqueros virtuales +
  anotar muertos en +7 después de 0x465c80 y derribar el bloque con 24.
