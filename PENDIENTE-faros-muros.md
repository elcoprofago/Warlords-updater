# Pendiente: luz de los faros y destrucción de muros (pedido del 10/11/2026)

Pedido completo:
1. Los faros iluminan 6 casillas, en mapas con niebla y de noche, con el mismo degradé que las ciudades.
2. Los muros se pueden destruir: a) por el dueño, seleccionando un bloque y usando "Raze"; b) por un enemigo,
   atacando la muralla.
3. Cada casilla de muro suma, en este orden: +3 Assassin, +5 Missiles, +5 Acid, +7 Fortify, +5 Life Drain, al poder
   de cada pila alojada en la muralla.
4. Imagen del bloque de muro roto, con el humo de las trampas detonadas.

## Hecho (1.0.170.0, commit de esta fecha; falta instalar y publicar: el juego estaba abierto en C:\Warlords3)
- Punto 1: `dn_lights` recorre OB_TAB y estampa cada faro (OB_FARO) con radio 6, cuadrado como ciudad
  (DN_FARO = OB_VISTA[OB_FARO]); con Hidden Map, solo si la casilla está explorada. Prueba: prueba_dianoche.py.
- Punto 2a: `wl_razelk` (menú 0x4b05d1 y tecla 0x44c2d7; la IA sigue con br_razelk), `wl_find`, `wl_text`, `ob_del`,
  `wl_apply` (código WL_CODE=0x7000+índice por la orden de arrasar de siempre). Prueba: prueba_obras.py (sección
  «derribar muros»).

## Próximo paso
- Cerrar el juego, `python parchesista-aliadauild.py` (instala en C:\Warlords3), correr las prueba_*.py sin
  argumentos y `tools\publicar-parche.ps1 vista-aliada`.
- Puntos 2b y 3 (ataque enemigo al muro con los bonos): falta decidir qué defiende un bloque sin pila encima y qué
  pilas cuentan como «alojadas» (¿las del dueño sobre las puertas?). Ingeniería inversa: batalla 0x469ed0,
  defensores 0x4411b0, habilidad única por unidad (+0xe6 código, +0xe8 valor; 6 Fortify, 28 Assassin, 30 Missiles,
  38 Acid, 54 Life Drain) — una unidad tiene una sola habilidad, así que 5 bonos exigen otro mecanismo.
- Punto 4: imagen del bloque roto en obras_img.py / RUINS\pozos.pcx.
