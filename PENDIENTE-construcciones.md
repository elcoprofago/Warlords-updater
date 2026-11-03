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

## Primer paso técnico (sin hacer)

Medir en DarklordAV.exe:

- cómo se marca una casilla como camino o puente (se parte de lo que ya usan ai_brdefev y
  prueba_iareconstruye para derribar y reconstruir puentes);
- si una montaña admite camino y qué costo de movimiento queda;
- cómo se representa un puerto y si existe un estado de "ciudad desactivada";
- cómo se da la orden en la interfaz: un menú nuevo o reutilizar el botón de reconstruir.
