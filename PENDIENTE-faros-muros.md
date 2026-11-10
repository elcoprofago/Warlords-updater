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
- Interpretación tomada: «3 grupos de arqueros» = 3 unidades de arquero por bloque (las que se ven caer una a una);
  los arqueros que quedan vivos se guardan en el byte +7 del registro de la obra (persisten entre ataques).

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
