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

## Paso 1 — cómo dibuja el juego la niebla (26/10/2026, leído en Darklord.exe original)

**Bits de la casilla** (10 bytes en 0x503e58, palabra +2 = 0x503e5a):
- 0x2000: Fog of War (niebla de quien mira; la pone/despeja 0x441540).
- 0x800 / 0x1000: copia de trabajo de lo explorado por quien juega el turno (0x441cf0 la arma desde el byte +4;
  0x441eb0 la devuelve). El dibujo mira 0x1000 (byte +3 & 0x10).

**Armado del cuadro visible** (0x4584d0, una entrada de 0x1c bytes por casilla en pantalla, tabla [esi+0x40]):
- Con Fog (OPT & 0x20) y la casilla con 0x2000: 0x45c8f0 da la máscara de las 8 vecinas con niebla, la tabla
  0x4fbfc8 la pasa a un número de borde, y queda en la palabra +8: bit 0 = hay niebla, bits 1..7 = borde.
- Con Hidden Map (OPT & 0x10) y la casilla sin 0x1000: 0x45c980(x, y, 1) da la máscara de vecinas no exploradas,
  0x4fbfc8 → borde, y queda en +8: bit 8 = no explorada, bits 9..15 = borde.

**Pintado** (0x45a960..0x45aa6e, por casilla de 48x48, hoja de dibujos 0x48):
- Niebla (bit 0): **0x4eddf0** → 0x4ee3c0 con la tabla **0x589608**: no tapa, **recolorea** cada píxel de la pantalla
  con una tabla de 256 colores (oscurecer), solo donde el dibujo de la hoja 0x48 marca (píxel ≠ 0x0b).
  Hay una segunda tabla igual en **0x589708** (usada por 0x4edcc4/0x4edd74/0x4eddb4, a ver para qué).
- No explorado (bit 8): **0x4dd530** = copia opaca del dibujo de la hoja 0x48 (el negro del Hidden Map).

**Consecuencia para la noche:** el juego ya tiene un "oscurecer con tabla de colores, con bordes suaves" (el de la
niebla). La noche puede salir de ahí sin dibujos nuevos para lo básico:
- noche sobre lo explorado = pasar el recoloreo de la niebla a todas las casillas fuera del halo;
- lo no explorado = el mismo recoloreo con una tabla más oscura (o dos pasadas), en vez del negro opaco;
- halo en gradiente = varias tablas (menos oscuras cerca de la fuente de luz), eligiendo por distancia.

**Falta averiguar:**
1. Quién llena las tablas 0x589608 y 0x589708 (no hay escrituras directas a esas direcciones: buscar quién recibe
   su puntero, 0x4edc74 y vecinas) y cómo armar tablas más oscuras con la paleta del juego.
2. Dónde se cuenta la vuelta (número de turno global) para alternar día/noche.
3. La opción: el diálogo 9 (Customize Options) ya tiene casillas clonadas por el parche (build.py, «Diálogo 9»,
   ~l.12296, y refresh/init/report ~l.571-640); la de día/noche va igual, deshabilitada si Hidden Map está puesto.
   Falta elegir el bit (el byte 25 del bloque de opciones, SHOPT, tiene libres los bits 0x02 en adelante).
