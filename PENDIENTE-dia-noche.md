# Modo día/noche (pedido del clan, 26/10/2026; sin empezar)

Texto del usuario: «que el juego tenga una nueva opción de juego (activable en inicio de partida) en modo día/noche:
una vuelta completa transcurre de día (interfaz actual) y la otra de noche, en ciclos regulares siempre (no
aleatorios). El efecto "noche" se lograría aprovechando lo que ya tiene el juego (mapa "explorado") oscureciendo lo
explorado aún más, de manera que lo "no explorado" sería realmente más oscuro, aunque no "negro" como el modo
"oculto". Es obvio que solo se podría jugar este modo sin la opción "hidden map" activada. Para reforzar este efecto
'noche' el halo de visión de las armas debería ser en gradiente, imitando un efecto luz. El mismo efecto halo deberían
tener las ciudades y demás sitios (ruinas, puentes, etc.). Esta modalidad incluso podría generar la necesidad de
nuevos sitios: faros costeros.»

Para trabajar en una sesión aparte. Primer paso: averiguar en el exe cómo se dibuja la niebla del Hidden Map
(0x441f30 despeja en cada paso; ver PENDIENTE-pozos-y-trampas.md, «Descubrir al pasar») y dónde agregar la opción en
el diálogo de inicio de partida.
