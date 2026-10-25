# Mapa de pruebas («probeta») para tandas de IA (pedido del usuario, 25/10/2026)

## Objetivo
Un mapa donde todos los lugares de salida sean equivalentes, para que en una tanda la única diferencia entre los
colores sea lo que se quiere medir (personalidad, PGS, IA). Va a servir para todas las tandas futuras, no solo las de
personalidad. Primer uso: repetir la serie de personalidades (TAREAS 41) para confirmar la ventaja de Artificer +
Devout y separar los otros cinco perfiles.

## Por qué hace falta
En la serie de personalidades (tandas 65 a 69, 30 partidas, Tanda_hex_perfiles_SR) ganaron 29 de 30 los que
arrancaron en el lugar amarillo o en el blanco. Los lugares negro, rojo y verde no ganaron nunca (el verde quedó
eliminado 11 veces de 30). Con la rotación cada perfil pasa por todos los lugares, pero solo dos de ellos permiten
ganar, así que cada perfil tiene en la práctica 10 oportunidades, no 30. Detalle en PENDIENTE-entrenamiento-ia.md
(«Ronda nueva: personalidades»).
- El desnivel no viene del oro inicial: amarillo y blanco arrancan con el **menor** oro (64); rojo con 119; verde,
  azul y negro con 244. Viene de la geografía (ciudades cercanas, vecinos, caminos). Igualar el oro lo empeoraría.

## Lo que ya se sabe y sirve
- La guardada se edita desde código: tanda.SAV_BLOQUES traduce direcciones de memoria a posiciones del .SAV
  (ver offset() en sin_ruinas.py). Ruinas: tabla 0x558872/0x558874, registros de 0xb8. Jugadores: 0x536b30 +
  color*0x1f8 (personalidades en +0xc0..0xc2, diplomacia en +0xe2..).
- escribir_rotada (Monitor 1.0.15+) ya reescribe perfiles y diplomacia antes de cada partida: el mapa parejo puede
  armarse con el mismo mecanismo (una _SR nueva, sin tocar la original).
- Hexagon solo admite 6 colores (blanco, amarillo, rojo, verde, azul, negro); Scarpart, Borderlands y Kor admiten 8.

## Pasos (ninguno hecho todavía)
1. Ubicar en el .SAV/exe la tabla de ciudades (dueño, posición, producción, ingreso, defensa) y el terreno.
   Probarlo primero en un caso de juguete (cambiar el dueño de una ciudad y ver el resultado en el juego).
2. Medir el desnivel de Hexagon por lugar: ciudades e ingreso a 1, 2 y 3 turnos de marcha de cada capital.
3. Elegir el método para emparejar: lo más simple que alcance (por ejemplo, igualar el ingreso y la defensa de las
   ciudades por anillo alrededor de cada capital). Si no alcanza, armar un mapa simétrico.
4. Validar el mapa con una tanda de control: el mismo perfil en todos los colores, 30 partidas. Queda parejo si
   ningún lugar se aparta claramente del promedio (hoy: amarillo 28.3 PV, verde 2.9).
5. Recién entonces repetir la serie de personalidades sobre el mapa nuevo (tarea nueva en TAREAS.md).
