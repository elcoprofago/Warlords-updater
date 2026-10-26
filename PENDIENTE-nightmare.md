# Bono «nightmare» (pedido del usuario, 26/10/2026; sin empezar)

Texto del usuario: «Quiero que sumemos un nuevo bono, que permita a las unidades clase "monster" tener un plus de +2
durante la noche (+2 de strength, hits, vs city, o habilidades especiales: ej., trample +1 a trample +3). El tipo de
plus sería aleatorio. El bono se llamará "nightmare", que dependerá no solo de la clase "monster" y la noche, sino
además de que cada unidad lo tenga asignado por editor.»

## Lo que ya se sabe (de PENDIENTE-dia-noche.md, pasos 7 a 14)

- Noche: `DN_ON` (lo pone `dn_pre`) sirve para el dibujo; para el combate hace falta la condición sin depender del
  dibujo: opción (SHOPT & 2) y vuelta par ([0x5032f8 + 0x30]; la primera es la 1). Con o sin Hidden Map.
- Bonos por nombre: como «camo», un archivo `TERRAIN\SUBTYPE\<nombre>.STT` y la búsqueda en los Move Bonus del tipo
  (`cam_rec` = `boatbon_src(..., rec=True)`; tipos en 0x53c410 + (bando*16 + ranura)*0xfc, nombres en +0xb2, 4 de 9
  bytes). **Los nombres de bono tienen 8 letras como máximo** y «nightmare» tiene 9: hay que elegir otro nombre.
- Héroes (ranura >= 16) no se miran.

## Por averiguar / decidir

1. Nombre de 8 letras como máximo (consultado al usuario: «nightmar», «nocturno», «pesadilla» no entra).
2. Qué marca la clase «monster» en el registro del tipo de unidad (buscar en el editor, Edit Army Data).
3. Dónde se suman fuerza, hits, vs city y las habilidades (trample, etc.) en el armado del combate (0x464ac0 y
   vecinas; ver el convoy, build.py ~l.3620).
4. Aleatorio: propuesta, uno por unidad y por noche (fijo durante esa noche, para que no cambie entre combates de la
   misma vuelta), con el generador del juego (0x4deb20). Si la habilidad no la tiene, ¿se le da? (ej. trample +2
   a una unidad sin trample): consultar.
5. Prueba de juguete (unicorn) y tarea en TAREAS.md.
