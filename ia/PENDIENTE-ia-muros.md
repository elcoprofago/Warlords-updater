# PENDIENTE — La IA construye murallas (pedido del usuario, 19/11/2026)

Vocabulario (usuario, 19/11/2026; ver CLAUDE.md): **MURALLA** = lo que se construye (pasan terrestres aliados y
voladores); **MURO** = terreno «Walls» del escenario (no pasa nadie, como las montañas altas). En las citas textuales
anteriores a esa fecha, «muro» quiere decir muralla.

Pedido textual: *«Que la IA sepa construir muros sería muy importante, incluso más que construir caminos. Vamos por
ese tema.»* Viene de ia\PENDIENTE-ia-innovaciones.md (paso 5.5 cerrado: «que la IA construya muros, paso aparte»).

## Por qué importa (lo medido)
- Tanda 183 (TAREAS 249, Tanda_hex_MU_control): con un anillo de 12 bloques alrededor de tres capitales, la IA casi
  no ataca la muralla (1 ataque), insiste contra la ciudad por la costa y pierde mucho. **La muralla protege.**
- Tanda 187: abrir brecha en un bloque (24 Longbows virtuales) le costó a la IA 65 ejércitos sin tirar ninguno.
- Hoy la IA solo repara murallas que ya tiene (`ai_wrep`, 1.0.222.0); no construye ninguno.

## Lo que hay hoy en el código (build.py, revisado 19/11/2026)
- Muralla (muro de piedra en el código) = obra OB_MURO (tipo 7) de la tabla `ob_*`. Lo construye un **grupo con un ejército con «build»**
  (BD_HASB, bono de movimiento), en la **casilla del líder**: tierra sin camino, ciudad, ruina, sitio, edificio ni
  otra obra. Dirección 1..8 en el byte +5 (une el bloque con sus vecinos, `ob_wmask`). Precio OB_FRAC = 10
  veinteavos = 50 % de fundar una ciudad, por bloque. Puerta (camino encima) OB_MCAM = 5 veinteavos.
- La muralla es **intransitable por tierra para todos, también para el dueño**, salvo por una puerta (dueño y
  aliados, `po_pf`). Los voladores la pasan.
- **Tope: OB_MAX = 512 obras en toda la partida** (era 64; subido en vista-aliada 1.0.263.0 a pedido del usuario),
  sumando las de todos los bandos (torres, faros, murallas). Los .SAV viejos ('OBRA', 64) se siguen cargando.
- **Las puertas vienen con la muralla:** el constructor nunca queda encerrado (corrección del usuario, 19/11/2026; así
  es desde 1.0.175.0/1.0.177.0). La nota anterior («la IA se encierra sola») venía de un registro viejo de 1.0.151.
- Hoy ningún bando de las guardadas del banco tiene unidades con «build» (relevamiento del paso 5).

## Cuándo construye la IA (condiciones del usuario, 19/11/2026)
Pedido textual: *«una condición de levantar murallas sería tener activado "artificer" o al menos "engineer" al
principio de la partida; otra, contar con un mínimo de oro. Es una estrategia defensiva, pero una más entre tantas.
No toda IA debe construir muros, solo debe saber hacerlo, y decidir cuándo es mejor, en base a las condiciones
predeterminadas.»*
- El bando tiene **artificer** o **engineer** activos al empezar la partida (bits de personalidad 18/19, bytes
  +0xc0..0xc2 del registro del jugador). Sin eso, no construye murallas nunca.
- Tiene **un mínimo de oro** (a medir: oro de cada color a mitad de partida, evento 30) y no gasta lo que necesita
  para sus tropas (como AW_DIV = 2 de `ai_wrep`).
- Aun cumpliendo eso, decide si conviene (ciudad amenazada, accesos por tierra): es una estrategia más, no obligatoria.

## Lo que hay que resolver (en este orden: enumerar antes de programar)
1. **Constructores.** Sin «build» la IA no puede construir. Ver qué unidades lo llevan en los .ARM del ranking
   (`C:\Warlords\ARMY`) y en las guardadas del banco. Si ninguna lo tiene, armar guardadas `_BD` (como `balsa.py`:
   «build» en una ranura de los 8 bandos) para la tanda, con artificer/engineer en los colores que deben construir.
   **Medido (19/11/2026):**
   - **.ARM con «build»: 10**, los mismos en `E:\Warlords-TEST\Warlords3\ARMY` y en `C:\Warlords\ARMY` (medido de
     nuevo el 19/11/2026): Archers, Blade Runners, Dark Dwarves (FU_darkd), Drow Infantry (drowinf; la otra copia,
     MC_DrowI, no lo tiene), Dwarf Sappers, Elven Sappers (FU_elfi), Gnomes sappers (FU_gnome), Royal Sappers
     (FU_rgrd), Scavens (MC_Scav) y Red Scavens. Una medición anterior de la misma sesión leyó en C: solo 3; la
     relectura da 10, con las fechas de los archivos sin cambiar (6 y 9/11). No se averiguó por qué difirió.
   - **Guardadas:** la guardada lleva su propia copia de cada unidad, no el .ARM. En las 28 de `C:\Warlords\SAVES`
     ninguna unidad tiene «build». En el banco (44) solo las de prueba de caminos y obras (`build_01/02`, `roads01/02`,
     `agua04`: Blade Runners y Red Scavens con build); ninguna de las `Tanda_*`. En `Tanda_hex_MU` los Red Scavens
     tienen desert + dungeon (copia anterior al .ARM actual) y los Zapadores tienen «road», que no es «build».
   - **Personalidades:** en `Tanda_hex_MU` y sus controles (`_MU_control`, `_control`, `_espejo_control`,
     `_lugar_control`) los 6 colores que juegan (0, 1, 3, 4, 5, 7) tienen **Artificer**: todos cumplirían la
     condición. En `Tanda_hex_perfiles` y `Tanda_juguete`, el 4 tiene Engineer y el 7 Artificer; los demás, ninguno.
   - **Conclusión:** para la tanda hay que armar guardadas `_BD` (como `balsa.py`): «build» en una ranura de cada
     bando. Base propuesta: `Tanda_hex_perfiles` (solo 4 y 7 cumplen la condición: los demás son el control natural
     dentro de la misma partida) o `Tanda_hex_MU` sin murallas, quitando Artificer a la mitad de los colores.
2. **El oro mínimo.** 12 bloques = 6 ciudades fundadas. Medir en el banco el oro de cada color a mitad de partida.
   **Medido (19/11/2026):**
   - **Precio de un bloque** (OB_FRAC = 10 veinteavos de fundar una ciudad, `BuildCity=800` en Default.rul): 400.
     Verificado en el exe (0x4057a0, el ajuste que usa `bd_price`): suma la ingeniería del mejor héroe del bando
     (habilidad 12) y le agrega **+6 con Artificer** (bit 0x80000 de +0xc0 del jugador) o **+2 con Engineer** (bit
     0x40000), tope 9; el precio baja un 10 % por punto. Sin héroes ingenieros: **Engineer 320, Artificer 160**.
     Las dos personalidades de la condición del usuario son justamente las que abaratan la muralla.
     Detalle del exe (0x4057a0), confirmado por el usuario el 19/11/2026: por cada héroe vivo del bando suma su
     ingeniería propia (0x43feb0, habilidad 12: el Warmason la gana con misiones) más dos aportes que dependen de su
     casilla (0x409e40 y 0x409fb0, también con 12; según el usuario, ítems con ingeniería). Toma el **mejor héroe**
     (no suma héroes entre sí), le agrega la personalidad y corta en **9** (90 % de descuento). Vale para todas las
     construcciones, trampas incluidas; se pierde si muere ese héroe.
     Sin identificar: `bd_price` además divide a la mitad si el campo +0xe2 del jugador (0x536c12) no vale -1; no
     se averiguó qué es.
   - **Oro de la computadora** (tabla `turno` de datos.db, tandas 169-188, colores vivos, 100.466 turnos-color):
     mediana 168 (turnos 1-10), 189 (11-20), 170 (21-30); p90 362 / 412 / 410. Turnos con al menos 160: 55,6 %;
     320: 16,9 %; 400: 10,0 %; 640: 3,7 %; 800: 2,6 %.
   - **Propuesta de mínimo:** como `ai_wrep` (AW_DIV = 2), construir un bloque solo si el oro es al menos **el doble
     de su precio**: Artificer 320 (se da en el 16,9 % de los turnos), Engineer 640 (3,7 %). Así el Artificer
     construye seguido y el Engineer pocas veces, y ninguno se queda sin oro para sus tropas. Un anillo de 12 bloques
     cuesta 1.920 con Artificer y 3.840 con Engineer: se arma de a un bloque por turno, empezando por el acceso más
     amenazado.
3. **Dónde (criterio del usuario, 19/11/2026).**
   - **Anillos alrededor de una ciudad: descartados** (*«lleva mucho trabajo, tiempo en turnos, costo y es solo para
     defender esa ciudad. Lo descarto de plano.»*). Única excepción: el bando en decadencia (pocas ciudades, a punto
     de ser eliminado) y con reservas suficientes, que se juega todo a atrincherarse.
   - **Lo que importa: pasos clave.** Detectar los pasos estrechos (un camino entre montañas o costa) y cerrarlos con
     un tramo corto de muralla: más efectivo y más barato.
   - **Con visión de conjunto y anticipación** (3-4 jugadas, como en ajedrez): pensar como el enemigo. Por dónde se
     acercaría a nuestras ciudades con sus propias capacidades, aprovechando nuestras debilidades. Distinguir el
     enemigo más peligroso en potencia (también el que está en paz), no solo el declarado.
   - **Mirar qué tiene cada enemigo:** barcos con «landing» o «raft» (la muralla no frena un desembarco: alta
     vulnerabilidad), unidades voladoras (la muralla tampoco las frena), mucho oro, etc. Si el enemigo puede rodear
     el paso por agua o por aire, cerrarlo vale menos.
   - **Qué ve la IA (revisado en el código, 19/11/2026):** la IA del parche lee directamente la tabla de ejércitos
     del juego (posición, tipo, bonos, dueño) y el oro de cada bando; no pasa por los reportes del jugador ni por la
     niebla (al_thr no consulta la visibilidad). O sea, puede saber todo lo anterior. **Sin verificar:** si la IA
     original del juego respeta el mapa oculto (anotado como pendiente en PENDIENTE-entrenamiento-ia.md).
   - **Orden propuesto, de a uno y midiendo:**
     a. Detectar pasos clave en los mapas del banco con un script (sin tocar el juego): casillas de tierra transitable
        cuyo cierre con 1-3 bloques corta todos los caminos por tierra entre dos zonas con ciudades. Mostrarlos al
        usuario sobre el mapa para confirmar que son los que él reconoce.
        **Hecho (19/11/2026): `ia\pasos.py`.** Tierra transitable = todo salvo agua (clase 1) y montaña (clase 4) sin
        camino, la regla del constructor. Busca tramos rectos de 1-3 casillas donde se puede poner muralla que, cerrados,
        dejan de un lado y del otro al menos una ciudad (y 12 casillas). Tramos que separan las mismas ciudades son un
        solo paso (queda el más corto, mejor si cierra un camino). Dibujos y listas en `ia\pasos\`:
        - Borderlands: 10 pasos (cabeceras de puente, caminos de montaña; p. ej. 10: 3 bloques en (57,44-46) aíslan
          7 ciudades del noroeste; 7: 3 bloques aíslan las 6 de los goblins del sudeste).
        - Scarpart: 6 (los de un bloque en caminos: 4 y 6 aíslan 2 y 4 ciudades; 1, 2, 3 y 5 en islas del sur/norte).
        - Kor: 1 (3 bloques aíslan Erdarc y Bethem). El resto del mapa es abierto: no tiene pasos de 1-3 casillas.
        - Hexagon: 12. Seis, uno por sector de color (11 ciudades), de 2-3 bloques junto al centro; y seis de 2
          bloques en la abertura de cada núcleo rodeado de muro (3 ciudades cada uno).
        Corrección del usuario (19/11/2026): también son intransitables el bosque profundo («Forest», clase 4: ya
        estaba incluido, ahora se dibuja aparte en verde oscuro) y el muro del escenario («Walls», clase 5: en
        Hexagon rodean los núcleos y el borde del mapa; ni por aire). Los mapas al azar no los tienen; los
        escenarios editados, quizás: la regla vale para cualquier mapa.
        Para 3.b, `pasos.vuelo()`: dónde entra un volador. Desde la reforma de otra sesión (build.py, «Montañas altas:
        tampoco por aire», 19/11/2026) ni el muro del escenario (clase 5) ni la montaña («Mountains», clase 4) se
        sobrevuelan; el bosque profundo sí. Con camino o puente, las dos se pasan: una casilla de muro
        con camino no es muro, es camino (usuario, 19/11/2026; así lo hace el juego, 0x4a4f90). Medido: Kor,
        2712 casillas cerradas al vuelo (todas sus montañas); Hexagon, 5162 (su muro). Así, un paso entre montañas
        frena también a los voladores, salvo que lo rodeen por otro lado.
        Falta que el usuario confirme que son los que él reconoce (TAREAS 267). No mira barcos, voladores ni grupos
        que cruzan montañas (eso es 3.b). Tarda ~5 min por mapa.
     b. Por cada paso: qué enemigos llegan por él a ciudades propias, y en cuántos turnos; y si pueden rodearlo
        (barcos con landing/raft, voladores).
        **Hecho en parte (19/11/2026): `ia\amenaza.py`** (lee la guardada y `ia\pasos\<mapa>.json`, que ahora deja
        `pasos.py`). Por paso y por lado: ciudades, dueños, costa y puertos; por cada bando con ciudades de un lado,
        los enemigos con ciudades del otro (todo color fuera de su equipo, también los que están en paz: el criterio
        del usuario de pensar en el enemigo potencial más peligroso), a cuántas casillas por tierra, y si rodean el
        paso:
        - Por agua, según el barco del bando (ranura 15, build.py): común, de puerto a puerto (puerto = casilla de
          agua con el bit 0x4000; el grafo 0x4a4f90 une agua y tierra solo ahí); «Landing», de un puerto de su lado a
          cualquier costa del nuestro, en el mismo mar; «Raft», de costa a costa sin alejarse más de 1 casilla de tierra.
        - Por aire: la MURALLA no frena a los voladores. Cuenta si el bando puede producir voladores (tipo +0xe0 == 4,
          el criterio de isfly) o ya los tiene, y si llegan volando (`pasos.vuelo`) a las ciudades del otro lado.
        Resultados con las guardadas del banco (al empezar la partida: casi todas las ciudades son neutrales, así que
        la mayoría de los pasos todavía no tiene enemigo de ningún lado; dentro del juego se mira con los dueños del
        momento):
        - Borderlands (sin voladores, barco común): el 4 encierra la capital de 7 sola, a 4 casillas del paso, sin
          puertos: una MURALLA de 2 bloques la cierra por tierra a los otros 7 bandos y nadie la rodea. Es el mejor
          caso de los cuatro mapas. El 3 y el 6 encierran la capital de 6 y la de 4, pero tienen puerto: se rodean de
          puerto a puerto. El 10 (7 ciudades del noroeste, una de 6), igual. Los otros 6 encierran solo neutrales.
        - Kor: el único paso encierra la capital de 7; se rodea de puerto a puerto (y en Tanda_Kor_RF, en balsa).
          La MURALLA ahí solo demora.
        - Scarpart (sin voladores): los 6 pasos encierran solo neutrales; el más cercano a una capital es el 5, a 3
          casillas de la de 3. Sirven cuando alguien conquiste esas ciudades.
        - Hexagon (equipos 01457 contra 3; todos pueden producir Descenders', voladores): los 6 pasos de sector se
          rodean por agua y por aire. Los 6 de los núcleos (3 ciudades neutrales, rodeados de MURO, sin costa) solo
          se entran por la abertura: una MURALLA ahí frena a todo terrestre; los voladores entran igual, porque
          cruzan la abertura por encima.
        **Falta:** los turnos. La distancia es en casillas; el costo de movimiento de cada terreno y los pasos de cada
        unidad todavía no se ubicaron (el +0xdd de la copia del .ARM en la guardada no es el movimiento: casi siempre
        0). Tampoco mira héroes que vuelan ni el oro de cada bando. Tarda ~1 min por mapa.
     c. Recién ahí la regla de decisión dentro del juego.
4. **Cómo.** El constructor tiene que ir a la casilla y construir con la misma función que el humano (BD_PW con
   OB_MURO y su dirección), cobrando con 0x43fd60. Mover al constructor es lo nuevo: `ai_wrep` no mueve a nadie.
   Una primera etapa más simple: construir solo donde el constructor ya está (junto a una ciudad propia), sin
   moverlo, como `ai_wrep`.

## Esquema de trabajo (el mismo de los demás pasos)
Registrar (evento nuevo: bloque construido por la IA, x, y, n = ciudad que protege) → prueba emulada con controles
(humano, sin artificer/engineer, sin «build», sin oro, casilla ocupada, tope lleno, ciudad sin amenaza) → tanda A/B con las guardadas `_BD`
(IA de prueba construye, original no) → PV, ciudades perdidas y pérdidas. Si mejora, pasa al ranking (CLAUDE.md).

## Próximo paso
Puntos 1 y 2 cerrados; criterio del punto 3 definido por el usuario (19/11/2026). 3.a hecho (ia\pasos.py); falta la confirmación del usuario (TAREAS 267). 3.b hecho en parte (ia\amenaza.py: enemigos, distancia en casillas, rodeo por agua y por aire). Siguiente: los turnos del 3.b (ubicar el costo de movimiento por terreno y los pasos de cada unidad) y después 3.c.

Frase para retomar: «Seguimos con ia\PENDIENTE-ia-muros.md, punto 3.b (turnos)».
