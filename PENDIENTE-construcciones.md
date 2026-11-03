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

Siguiente: medir en DarklordAV.exe:

- cómo se marca una casilla como camino o puente (se parte de lo que ya usan ai_brdefev y
  prueba_iareconstruye para derribar y reconstruir puentes);
- si una montaña admite camino y qué costo de movimiento queda;
- cómo se representa un puerto y si existe un estado de "ciudad desactivada";
- cómo se da la orden en la interfaz: un menú nuevo o reutilizar el botón de reconstruir.
