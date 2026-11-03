# PENDIENTE — Construcciones del jugador (puertos, puentes, caminos)

Diseño acordado con el usuario el 2-3/11/2026. Nada implementado todavía.

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
   Falta decidir si los puentes también los hace un constructor (lo natural) y si convertir
   una ciudad en puerto lo necesita (no parece hacer falta).

## Primer paso técnico (sin hacer)

- Ver si el campo de habilidades de las unidades tiene un bit libre para «build», o si hay que
  reutilizar uno que no se use. Nombre corto por el límite de letras: «build».
- Ver qué unidades de los ejércitos (army) llevarían el bono.
- La IA: en la primera etapa usa los caminos que encuentra pero no construye. Enseñarle a
  construir queda para otra tanda.

Medir en DarklordAV.exe:

- cómo se marca una casilla como camino o puente (se parte de lo que ya usan ai_brdefev y
  prueba_iareconstruye para derribar y reconstruir puentes);
- si una montaña admite camino y qué costo de movimiento queda;
- cómo se representa un puerto y si existe un estado de "ciudad desactivada";
- cómo se da la orden en la interfaz: un menú nuevo o reutilizar el botón de reconstruir.
