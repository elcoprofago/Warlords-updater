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

Lo que faltaba (pintado y reporte) quedó en el paso 4.

## Paso 4 — el pintado de la noche y el reporte (26/10/2026, vista aliada 1.0.75.0; probado en emulación, no en el juego)

- **Cuándo:** opción puesta (SHOPT & 2), sin Hidden Map (OPT & 0x10) y vuelta par ([0x5032f8+0x30]). Falta confirmar
  en el juego que la primera vuelta sea la 1 (si no, la noche cae al revés: se invierte en `dn_pre`).
- **Tabla de noche:** calculada al compilar desde `C:\Warlords3\war3.pal` (`dn_table`): cada color al 78 % por nivel
  con tinte azulado, al índice más parecido de la paleta. No toca `war3.pal`.
- **Grilla de niveles** (`dn_pre`, desvío del prólogo 0x459790 del dibujo del mapa): la vista más un borde, en 0..4
  (DN_N). La luz baja el nivel según la distancia (máx + mín/2 − radio): ciudades radio 1; ruinas, sitios y puentes
  en pie radio 0; ejércitos de quien mira radio 1. Caminos, puentes derribados y ejércitos ajenos no alumbran.
  Solo se marcan sucias las celdas cuyo 3x3 cambió desde el dibujo anterior (`dn_old`).
- **Pintado** (`dn_post`, desvío del epílogo 0x45aa6e): en cada celda sucia, una pasada de 0x4ee3c0 por nivel, con
  la máscara de vecinas tan oscuras o más y el borde de 0x4fbfc8 (las mismas formas que la niebla, así el halo sale
  suave).
- **Reporte View Game Options** (diálogo 115): fila «Day/Night» en la columna izquierda (filas a 19 px).
- **Prueba:** `parchesista-aliada\prueba_dianoche.py` (unicorn, mapa de juguete): niveles, celdas sucias y cada
  llamada al recoloreo contra el mismo cálculo en Python; sin cambios no pinta; mover un ejército ensucia solo su
  entorno; de día, con Hidden Map o sin la opción no pinta.

**Prueba en el juego (tarea 46):** bien; la primera vuelta es la 1 (impares de día, pares de noche).

## Paso 5 — ajustes pedidos tras la prueba (26/10/2026, vista aliada 1.0.76.0; prueba en el juego: tarea 48)

- La luz también se oscurece: nivel mínimo DN_MIN = 1 (82 % de brillo), y desde ahí el degradé.
- 6 niveles (DN_N = 6, factor 0,82 por nivel: el más oscuro ~30 %).
- Halo redondo en ejércitos, ruinas, sitios y puentes: distancia euclídea redondeada (`dn_stamp`, ch = 1); las
  ciudades siguen con máx + mín / 2 (cuadrado).

## Paso 6 — 8 niveles y el minimapa (26/10/2026, vista aliada 1.0.77.0; prueba en el juego: tarea 49)

- 8 niveles (DN_N = 8, factor 0,82: el más oscuro ~20 %).
- Minimapa: el del juego es [0x57276c] (clase 0x4f5028); 0x4114d0 copia la imagen base (hoja 0x2d) a la hoja 0x28,
  dibuja los íconos encima ([vtabla+0x10]) y la 0x28 va a pantalla (0x4dd4f0 en 0x4111b0). `dn_mini` (en 0x4114ef,
  entre la copia y los íconos) arma una grilla del mapa entero (`dn_m`, 256 por fila) con `dn_lights` (las luces,
  separadas de `dn_pre`; `dn_stamp` ahora escribe en [DN_BASE] con [DN_STR] por fila) y recolorea cada tramo de
  igual nivel de cada fila de píxeles con 0x4ede30 y la tabla compuesta del nivel (`dn_mt`). Píxel -> casilla como
  0x411370. `dn_pre` pone [minimapa+0xc] = 1 cuando cambia entre día y noche, para que se rearme.
- Prueba en emulación (`prueba_dianoche.py`, casos 6 y 7): tramos y tablas contra Python, la vista intacta, de día
  nada, y la marca de rearmado.
- Sin verificar en el juego: que la marca [+0xc] alcance para que el minimapa se rearme justo al cambiar de vuelta.
  El otro minimapa (0x5020e0, clase 0x4f5060, hoja 0x6a) no se tocó.

## Paso 7 — luz de los ejércitos al 50 % y bono «camo» (26/10/2026, vista aliada 1.0.78.0; tareas 50 y 51)

- Luz de los ejércitos: `dn_stamp` toma el nivel mínimo de cada luz en los bits 16..23 de ecx (0 = DN_MIN). Los
  ejércitos usan DN_AMIN = 4 (0,82^4 ~45 %; el 3 daría ~55 %): pedido «al 50 % en su punto más alto». Ciudades y
  sitios siguen en DN_MIN. Vale también para el minimapa (usa `dn_lights`).
- Camuflaje: bono de movimiento **camo** (`TERRAIN\SUBTYPE\camo.STT`, fuera de la lista de Combat Bonus del editor;
  los nombres de bono tienen 8 letras como máximo, por eso no «camouflage»). De noche (DN_ON), `cam_blit` reemplaza
  la copia final de `crdraw` (0x459d0d, ejército quieto; se engancha con el puntero CRBLIT): copia como siempre y, si
  todas las unidades del bando de la celda en esa casilla tienen «camo» (`cam_stack`; un héroe lo impide), recolorea
  con 0x4ee3c0 y los mismos argumentos (el mismo dibujo hace de máscara: solo cambian sus píxeles, banderín de color
  incluido) con `cam_tab` (40 % del color + 60 % de gris medio). Elegido el gris porque «del color del terreno»
  exigiría mezclar con el fondo de cada píxel, que la rutina de tablas del juego no hace.
- No cubre el grupo mientras se anima su paso (0x459e15, 0x459eea): se ve normal hasta que se para.
- Prueba: `prueba_camuflaje.py` (todo camo, mixto, héroe, enemigo, mayúsculas; de día, sin opción y con Hidden Map
  nada; la tabla contra Python). `prueba_dianoche.py` con AMIN.

**Falta:**
- Lo no explorado más oscuro de noche: sin Hidden Map el revelado (0x441b30) no corre, así que no hay registro de
  qué está explorado; haría falta llevarlo aparte. Para más adelante.

## Paso 8 — camuflaje al 30 % y Army Report (26/10/2026, vista aliada 1.0.79.0; tarea 52)

- Pedido tras la tarea 51: el globito seguía del color del equipo; camuflado al 30 %; el Army Report no tiene que
  revelar la posición de los camuflados de noche.
- `cam_blit_src(n, reg)` arma `cam_blit` (2ª pasada, celda en esi) y `cam_blit3` (3ª pasada, celda en edi; sitios
  `CAM_SITES`: figura 0x45a14f/0x45a18e, globito 0x45a267, barra 0x45a2ac, iconos 0x45a2cc/0x45a34a/0x45a3a5). Si el
  grupo está camuflado ya no copia el dibujo: solo 0x4ee3c0 con `cam_tab` = 70 % del fondo + 30 % de gris (silueta).
- Army Report: el mapita es el minimapa 0x414d50 (modo 0x10), que dibuja los ejércitos de todos. `cam_rep` en
  0x414e1a salta a 0x414e2b (no dibuja) si es de noche, el dueño no es quien mira ni un aliado mutuo con vista
  aliada (`fogally`), y `cam_stack` da camuflado. La barra de conteo del informe no cambia (no revela posición).
- Prueba: `prueba_camuflaje.py` (2ª y 3ª pasada, Army Report visto por cada bando, de día todos).

## Paso 9 — silueta más clara (26/10/2026, vista aliada 1.0.80.0; tarea 53)

- Tarea 52: el globito ya sale gris, pero el camuflado de noche no se veía (fondo oscuro + gris oscuro 32 al 30 %).
  `cam_tab` pasa a 55 % del fondo + 45 % de gris claro 160: silueta gris clara visible.

## Paso 10 — figura en gris apagado (26/10/2026, vista aliada 1.0.81.0; tarea 54)

- Tarea 53: la silueta clara salía como una mancha blanca. Ahora el camuflado vuelve a copiar el dibujo y lo
  recolorea con `cam_tab` = gris por luminancia (0,3 R + 0,59 G + 0,11 B) al 60 %: se conserva la figura, en gris
  oscuro, globito incluido (cam_blit3 sigue en la 3ª pasada).

## Paso 11 — camuflaje verdoso (26/10/2026, vista aliada 1.0.82.0; tarea 55)

- Tarea 54: el gris oscuro se notaba. `cam_tab` = oliva (95, 110, 60) × (0,8 + 0,4 · luminancia/255): poco contraste
  y del tono del pasto. La paleta es de 256 colores sin transparencia real; si hiciera falta más, el próximo paso es
  tramar (copiar solo parte de los píxeles).

## Paso 12 — escala de la paleta (26/10/2026, vista aliada 1.0.83.0; tarea 56)

- Tarea 55: mancha blanca otra vez. Causa: `war3.pal` va de 0 a 63 por canal y las fórmulas de 1.0.80.0 y 1.0.82.0
  usaban 0..255, así que todo caía en el color más claro. Ahora oliva (24, 28, 15) y luminancia /63: sale en los
  índices 19, 20, 215, 217 (grises ~20) y 165..167 (oliva ~31, 31, 8).

## Paso 13 — más verdoso (26/10/2026, vista aliada 1.0.84.0; tarea 57)

- Tarea 56: bien de tono y opacidad; pedido: más verdoso. La paleta no tiene grises verdosos (solo grises, oliva
  162..167 y verdes saturados 48..53). `cam_tab`: los índices impares se buscan entre 48..53, los pares como en el
  1.0.83.0; la mezcla de tonos de cada figura da el gris verdoso. Si queda moteado, volver a 1.0.83.0.

## Paso 14 — camo en ciudades y Día/Noche con Hidden Map (26/10/2026, vista aliada 1.0.85.0; tarea 58)

- Tarea 57: perfecto. Pedido para cerrar: (1) en una ciudad el camo no tiene efecto (está iluminada): `cam_stack`
  devuelve 0 si la casilla (`br_tile`) es de ciudad (byte +3 & 7 = 3); vale para el dibujo y el Army Report.
- (2) ¿Día/Noche con Hidden Map? Sí. Análisis:
  - Lo no explorado es una copia opaca negra (bit 8 de la celda) y la noche recolorea encima: negro sigue negro. No
    se neutralizan: la noche actúa sobre lo explorado, el negro sobre lo demás.
  - La única contradicción: una luz (ciudad, ruina, sitio, puente) bajo el negro estamparía su halo en las casillas
    exploradas vecinas y delataría su lugar. Con Hidden Map, `dn_lights` solo toma las luces de casillas
    exploradas por quien mira (0x1000 = byte +3 & 0x10, la copia de trabajo de lo explorado). Los ejércitos de quien
    mira siempre están en lo explorado.
  - El «no explorado más oscuro» del pedido original queda resuelto por el propio negro del Hidden Map.
  - Se quitó la exclusión del diálogo (`ck_dn`, `refresh`), la condición en `dn_pre` y `dn_mini`, y «(not with Hidden
    Map)» del texto de la casilla.
- Pruebas: `prueba_dianoche.py` 8) (Hidden Map de noche, el sitio sin explorar no alumbra, minimapa);
  `prueba_camuflaje.py` 1c) ciudad y 2b) Hidden Map. El diálogo no se emula: tarea 58.

## Paso 15 — «camo» pasa a llamarse «camouflg» (26/10/2026, vista aliada 1.0.88.0; tarea 61)

- Pedido: más intuitivo en el editor y el comparador. `CAMO = b'camouflg'` (8 letras, cabe en el campo de 9 con el 0),
  `TERRAIN\SUBTYPE\camouflg.STT`, `COMB_NO` del editor y `prueba_camuflaje.py` (TODO OK sobre el exe nuevo).
- El actualizador no borra archivos: el `camo.STT` viejo queda en las instalaciones (sin efecto); tarea 61 paso 4.
