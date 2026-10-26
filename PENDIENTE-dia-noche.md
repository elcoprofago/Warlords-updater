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

## Paso 2 — las tablas de oscurecer y el contador de vueltas (26/10/2026, Darklord.exe original)

**Tablas 0x589608 / 0x589708:** son parte del objeto paleta en **0x589308** (RGB 256x3 en +0, tablas en +0x300 y
+0x400). No las arma el código: las **lee del archivo `war3.pal`** (1280 bytes = 0x300 RGB + 0x100 + 0x100), en
0x4e94d0 (llamado desde 0x4de81d). Si el archivo es más corto, las llena con 0x0a y 0x0f.
- 0x589608 (+0x300) = **oscurecer**: en `war3.pal` deja cada color en ~50 % de su brillo (mín. 0, máx. 86 %).
- 0x589708 (+0x400) = **aclarar**: ~1,8x (1,0 a 4,8x). La usan 0x45ccc9 y 0x45d0b8 (dibujos de 48x48 en modo 1;
  el modo 0 de esos mismos lugares oscurece con 0x589608) y 0x4942eb.
- La paleta es VGA de 6 bits (componentes 0..63).

**Consecuencia:** las tablas nuevas (noche más oscura, escalones del halo) se pueden calcular en el parche al
cargar la paleta, a partir del RGB de 0x589308: para cada color, el índice de la paleta más parecido a ese color
multiplicado por un factor (p. ej. 0,35 / 0,5 / 0,7 / 0,85). Cuatro o cinco tablas de 256 bytes, en datos del parche;
no hace falta tocar `war3.pal`. Para "lo no explorado" de noche, la tabla más oscura (o la de 0x589608 dos veces).

**Contador de vueltas:** objeto de juego **0x5032f8**: palabra **+0x30 = número de vuelta** (lectura 0x420a80;
ya usado en build.py, «turno = [0x5032f8 + 0x30]»), +0x2a = bando del turno (0x420a70). Sube en **0x4212dd**
(`inc word [esi+0x30]`, dentro de 0x4212b0, solo cuando el indicador +0x32 de "vuelta completa" está puesto;
después llama a 0x43c620). Regla día/noche: día si la vuelta es impar, noche si es par (o al revés): falta
confirmar con qué valor arranca (1 en la primera vuelta, se ve en el juego).

## Paso 3 — la opción en Customize Options (26/10/2026, hecho en build.py; sin probar en el juego)

- Bit **0x02 de SHOPT** (byte 25 del bloque de opciones; 0x01 es Shared Cities). Viaja con el bloque: partida
  guardada y red.
- Casilla **id 61 «Day/Night»** (DNCHK), clonada de Fog of War, en la columna derecha de Viewing Options, debajo de
  Hidden Map. Esa columna pasa a 5 filas de 15 píxeles (y = 102..162): See in Cities, Hidden Map, Day/Night, Fog of
  War, Allied View.
- **Excluyente con Hidden Map** (en vez de deshabilitarla, que el diálogo no sabe hacer sin más trabajo): marcar
  Day/Night desmarca Hidden Map (click, `ck_dn`); marcar Hidden Map desmarca Day/Night (refresh, que el juego llama
  después de cada clic en 0x428370 y redibuja Hidden Map en 0x42862a).
- Todavía **no hace nada en el juego**. El pintado igual debe exigir `!(OPT & 0x10)`, por si una partida o un
  OPTIONS.* trae los dos bits.

**Falta:**
- Pintado de la noche (paso de 0x45a960), con las tablas calculadas al cargar la paleta (paso 2). Próximo paso.
- Fila «Day/Night» en el reporte View Game Options (diálogo 115; sus dos columnas ya tienen 8 filas).
- Prueba en el juego (va a TAREAS cuando haya pintado: probar solo la casilla no vale la instalación).
