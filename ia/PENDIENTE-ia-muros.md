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
     **La computadora paga la mitad** (identificado el 19/11/2026, punto 3.c): `bd_price` divide la base a la mitad
     si el campo +0xe2 del jugador (0x536c12) no vale -1, y -1 es el humano. Para la IA, sin héroes ingenieros: **sin
     personalidad 200, Engineer 160, Artificer 80** por bloque.
   - **Oro de la computadora** (tabla `turno` de datos.db, tandas 169-188, colores vivos, 100.466 turnos-color):
     mediana 168 (turnos 1-10), 189 (11-20), 170 (21-30); p90 362 / 412 / 410. Turnos con al menos 160: 55,6 %;
     320: 16,9 %; 400: 10,0 %; 640: 3,7 %; 800: 2,6 %.
   - **Propuesta de mínimo:** como `ai_wrep` (AW_DIV = 2), construir un bloque solo si el oro es al menos **el doble
     de su precio**. Con el precio de la computadora (la mitad): **Artificer 160** (se da en el 55,6 % de los turnos),
     **Engineer 320** (16,9 %). Así el Artificer construye seguido y el Engineer menos, y ninguno se queda sin oro
     para sus tropas. (La primera versión de esta propuesta usaba el precio del humano, el doble: 320 y 640.) Un
     tramo de 3 bloques cuesta 240 con Artificer y 480 con Engineer; se arma de a un bloque por turno.
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
        **Hecho (19/11/2026): `ia\amenaza.py`** (lee la guardada y `ia\pasos\<mapa>.json`, que ahora deja
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
        - Borderlands (sin voladores, barco común): el 4 encierra una sola ciudad, de 7 (las otras 3 de 7 quedan del otro lado), a 4
          casillas del paso, sin puertos: una MURALLA de 2 bloques la cierra por tierra a los otros 7 bandos y nadie la rodea. Es el mejor
          caso de los cuatro mapas. El 3 y el 6 encierran una ciudad de 6 y dos de 4, pero tienen puerto: se rodean de
          puerto a puerto. El 10 (7 ciudades del noroeste, una de 6), igual. Los otros 6 encierran solo neutrales.
        - Kor: el único paso encierra una ciudad de 7 y una neutral; se rodea de puerto a puerto (y en Tanda_Kor_RF, en balsa).
          La MURALLA ahí solo demora.
        - Scarpart (sin voladores): los 6 pasos encierran solo neutrales; el más cercano a una capital es el 5, a 3
          casillas de la de 3. Sirven cuando alguien conquiste esas ciudades.
        - Hexagon (equipos 01457 contra 3; todos pueden producir Descenders', voladores): los 6 pasos de sector se
          rodean por agua y por aire. Los 6 de los núcleos (3 ciudades neutrales, rodeados de MURO, sin costa) solo
          se entran por la abertura: una MURALLA ahí frena a todo terrestre; los voladores entran igual, porque
          cruzan la abertura por encima.
        **Turnos, hechos (19/11/2026): `ia\movimiento.py`**, verificado contra el código del juego con
        `ia\prueba_movimiento.py` (corre DarklordAV.exe en el emulador de simcombate: TODO OK en los cuatro mapas).
        - Costo de cada casilla (0x4a4f90): palabra +0x34 del registro de terreno (llanura 2, colinas 4-5, pantano 5,
          desierto 3, lava 9); +1 con la capa de bosque; 1 en camino y en ciudad. La réplica coincide byte a byte con
          la grilla del juego (65.960 casillas); el control (sin el +1 del bosque) falla en todas las casillas con
          bosque, como debe.
        - Costo de un paso (0x4a6490): con bono de terreno, las casillas de su clase que cuestan más de 2 bajan a 2.
          Bit 1 del bono = segundo terreno del mapa (pantano en Hexagon y Borderlands, bosque en Kor y Scarpart),
          bit 2 = colinas. El bono lo arma 0x486ab0: basta una unidad del grupo que lo tenga. 90.804 llamadas, 0
          diferencias.
        - El paso se da solo si queda movimiento para pagarlo, y lo que sobra se pierde (0x4a6290; leído del código,
          probado en un caso de juguete con control, no emulado).
        - Movimiento de cada unidad: +0x9b de su registro en la guardada; coincide con el del ejército en el mapa
          (+0x10 de 0x54fe52) en los 83 ejércitos comunes de las guardadas de prueba.
        `amenaza.py` ahora dice, por enemigo, en qué turno llega al paso y a la ciudad más cercana del defensor,
        saliendo de sus ciudades del otro lado con la unidad no voladora más rápida que puede producir (una por bono
        de terreno; se queda con la que llega antes). Resultados (inicio de partida):
        - Borderlands (Gnoll Cavalry, mov 24, por caminos): todo enemigo con ciudad junto a un paso lo cruza en el
          turno 1; el 4 (el mejor caso) deja a la ciudad de 7 a 2 turnos de cinco bandos. Una MURALLA ahí tiene que
          estar antes del turno 2.
        - Kor (Orcs Ram, mov 22, bono colinas): el de 7 llega al paso en el turno 2 y a la ciudad de 0 en el 4; 0
          llega a la de 7 en el 3.
        - Hexagon (Blade Runners, mov 24-30, bono colinas): los pasos de sector se alcanzan en los turnos 4 a 7 y las
          capitales del otro lado recién en el 9 a 12. Hay tiempo para cerrarlos, pero se rodean por agua y por aire.
        No cuenta héroes, objetos, el oro del enemigo ni las MURALLAS ya construidas: es el peor caso de un ejército
        recién producido. Tarda unos segundos por mapa.
     c. Recién ahí la regla de decisión dentro del juego.
        **Decidido y prototipado (19/11/2026): `ia\cerrar_paso.py`** (la regla v1 en Python, con los datos que el
        juego tiene a mano; lee una guardada y, con `partida turno`, los dueños, el oro y la diplomacia de ese turno
        en datos.db; `--control` compara las simplificaciones con lo exacto).
        - **Se calcula en el juego, no precalculado por mapa.** Así sirve en los mapas al azar, en los 9 escenarios
          de ESCEN y en las campañas, y con las MURALLAS y los dueños del momento. El costo alcanza: `pasos.py` ahora
          separa los lados con un recorrido alternado (el lado más chico se agota primero) en vez de la ventana de
          7 casillas, con los mismos pasos y los mismos lados en los cuatro mapas (medido contra los JSON del commit
          anterior). Medido: 1,1 millones de visitas de casilla en Borderlands y 3,0 en Hexagon para todos los tramos
          juntos; 24 mil como máximo para un tramo. Se recalcula cuando cambia el mapa (obras, dueños), no cada turno.
        - **La regla v1:**
          1. Condiciones del bando: Artificer o Engineer; oro ≥ 2 × precio del bloque (160 / 320); y alguna unidad con
             «build» que pueda producir.
          2. Por cada paso no cerrado y cada lado D con ciudades propias: **amenaza** = por cada bando no aliado (en
             guerra o en paz) con ciudades del otro lado y ninguna en D, sus ciudades de ese lado que **llegan al
             paso en 4 turnos o menos** («3-4 jugadas»), × 2 si no puede rodear el paso, × 1 si puede (por agua o por
             aire: vale menos, no nada).
          3. Se descarta el paso si la ciudad propia más cercana está a más de 20 casillas (el constructor tendría
             que cruzar medio mapa) o si no tiene amenaza.
          4. Elige la mayor amenaza; a igualdad, la ciudad propia más cercana y después el tramo más corto.
        - **Simplificaciones para el juego, medidas contra lo exacto de 3.b (`--control`):**
          - Agua: barco común si los dos lados tienen puerto; «Landing», puerto de su lado y costa del nuestro;
            «Raft», costa de los dos (sin mirar si es el mismo mar). En los cuatro mapas da lo mismo que amenaza.py.
          - Turnos al paso: un solo recorrido hacia atrás desde el tramo con el costo de cada casilla (la grilla del
            juego), uno por bono de terreno; turnos = techo(costo / movimiento). Contra `movimiento.turnos` (que pierde
            lo que sobra de cada turno): igual en 352 de 358 ciudades enemigas, 1 turno de más en 6; cambia «dentro o
            fuera de 4 turnos» en 3 (Borderlands al empezar y en la partida 1477, turno 15). Se equivoca siempre
            hacia el lado prudente: cuenta como amenaza a alguien que tarda un turno más.
          - Lava: el juego la marca como agua (clase 1); se distingue por el nombre del terreno («Lava», en
            0x535f12 + terreno × 0x58), como hace amenaza.py.
        - **Resultados:**
          - En las guardadas del banco nadie construiría hoy: ningún bando tiene unidades con «build» (punto 1), y en
            Borderlands, Kor y Scarpart ninguno tiene Artificer ni Engineer. Hacen falta las guardadas `_BD`.
          - Borderlands, partida 1477, turno 15 (mirando solo la amenaza): el 7 tiene el paso 4 (amenaza 62, nadie lo
            rodea, su ciudad a 4 casillas); el 3, el paso 8 (52, a 13); el 0, el 7 y el 5 (25-29, se rodean por agua);
            el 6, el 10 y el 3. Con la caballería gnoll (24 de movimiento por camino) casi todo enemigo llega en 4
            turnos: en un mapa chico y rápido el horizonte apenas recorta (68 → 62 en el paso 4 del 7).
          - Hexagon: todo se rodea por aire (Descenders'); los pasos de sector quedan a 44-48 casillas de las
            capitales (más de 20: lejos).
          - Kor: amenaza 1-6, se rodea por agua.
          5. Con la tabla de obras, mirando todos los tramos que cortan las mismas ciudades (`pasos.detectar(d,
             todos=True)`; el paso 8 de Borderlands tiene 2, otros hasta 61):
             - un paso con algún tramo cerrado entero por MURALLA del bando o de un aliado **no se elige**;
             - uno a medio cerrar (MURALLA propia o aliada en un tramo) **va primero**: terminar lo empezado, en ese
               mismo tramo;
             - **uno con MURALLA ajena (de un bando no aliado) va después de los empezados y antes que el resto**:
               *«un paso con una muralla ajena le sirve solo al enemigo, con mayor razón, esa sería una señal de que
               el paso en sí es importante»* (usuario, 19/11/2026; la primera versión de esta regla lo descartaba).
             - Sobre una obra no se construye (MURALLA ajena, torre, faro): se cierra en otro tramo del mismo paso sin
               obras ajenas, prefiriendo el que ya tiene bloques propios, después el que queda del lado propio. Si todos
               los tramos tienen una obra ajena (el paso 6 de Borderlands: sus dos tramos comparten (13,83) y (13,84)),
               no se puede cerrar y no se elige.
             Probado con `ia\prueba_cerrar_paso.py` (obras puestas en memoria en Borderlands, partida 1477, turno 15:
             empezado, cerrado, torre, MURALLA ajena en un paso con tramo libre y en uno sin tramo libre; control: las
             opciones de un bando sin obras en sus pasos no cambian; y la lectura de la tabla de obras de Tanda_hex_MU):
             TODO OK.
        - **Cómo quedó en el juego (build.py), escrito en vista-aliada 1.0.271.0** (diseño, 19/11/2026):
          - `mp_scan`, una vez por estado del mapa (se recalcula si cambian OB_N, los dueños o los tamaños de las
            ciudades; no cada turno). Igual en todas las PC: sin azar, mismo orden de recorrido.
            1. Grilla de un byte por casilla (OB_MAPSZ): tierra transitable (clase fuera de 1, 4 y 5, o camino),
               candidata (`ob_okt(OB_MURO)` acepta, o ya hay una MURALLA; nunca casilla de ciudad), costa y puerto
               (vecina de agua que no es lava: nombre del terreno en 0x535f12 + terreno × 0x58; puerto = byte +1 &
               0x40). Componentes de tierra numerados.
            2. Tramos: x por fuera, y por dentro; largo 1 a 3; horizontal y después vertical (el de largo 1, una sola
               vez), como `pasos.tramos`.
            3. Separación como `pasos.separa`: un grupo por vecina del tramo, cada uno con su cola; se expande siempre
               el grupo más chico (a igualdad, el de menor número); dos grupos que se tocan se unen (unión de a lo
               sumo 8 etiquetas). Termina cuando un grupo se agota (ese es el lado chico) o queda uno solo (no separa).
               Memoria: las colas en un bloque pedido con malloc al empezar (8 × OB_MAPSZ palabras), no en el .exe.
               Antes de escribirlo, medir en Python que la cola FIFO por grupo da los mismos pasos que hoy.
            4. Lado chico y lado grande (= componente − chico − tramo): las dos con ≥ MIN_LADO casillas y ≥ 1
               ciudad. Máscara de ciudades de cada lado (80 bits), costa y puerto de cada lado. Pasos con las mismas
               máscaras: son un solo paso; el tramo principal es el más corto, mejor si tiene camino, a igualdad el
               primero, pero **se guardan todos sus tramos** (la regla 5 elige uno sin obras ajenas).
            5. Por paso y lado: distancia en casillas desde el tramo (para MP_DIST) y, por bono de terreno (0-3), el
               costo hacia atrás desde el tramo con la grilla 0x57d158 del juego. Como los costos van de 1 a 9, alcanza
               una cola por cubos (Dial) en lugar de un montículo. Se guarda el mínimo por ciudad, no la grilla.
          - `mp_pick(p)` en `ia_turn`, después de `ai_wobs`, solo para la computadora (+0xe2 != -1): condiciones
            (personalidad, oro ≥ AW_DIV × `bd_price`, constructor en sus 16 ranuras), amenaza de cada paso con los
            dueños y la diplomacia del momento (DIPLO, wl_war/fogally), barco (ranura 15: común, «landing», «raft»)
            y voladores (isfly), regla 5 con OB_TAB, y elección. Deja el objetivo del bando (`mp_obj[p]`: paso y
            lado) para el punto 4, y el evento 51 («paso que la IA decide cerrar»: x, y del primer bloque del tramo,
            n = amenaza × 100 + bloques), que hay que sumar a EVENTOS en `ia\tanda.py`.
          - Verificación: emulador (simcombate\motor.py, como `ia\prueba_movimiento.py`): mismos pasos y lados que
            `pasos.py` en los cuatro mapas, y misma elección que `cerrar_paso.py` en guardadas con MURALLAS y dueños
            distintos, con los controles del «Esquema de trabajo».
          - **Hecho (19/11/2026, vista-aliada 1.0.271.0).** Diferencias con el diseño: las colas y las tablas no van
            con malloc sino en una zona sin datos de la sección .avis (`MP_BSS_OFF`, el cargador la llena con ceros);
            el caché compara la grilla entera (tierra, candidatas, costa/puerto, caminos, ciudades en pie y costos de movimiento), no
            OB_N: una MURALLA no cambia los pasos y no hace recalcular. `mp_pick` corre para la computadora con o sin
            IA.INI, pero solo decide: deja `mp_obj[p]` (paso | lado << 8 | tramo << 16, −1 si nada) y el evento 51;
            la partida no cambia hasta el punto 4. Modelo en Python del recorrido del juego: `ia\mp_modelo.py`
            (mismos pasos que `pasos.py` en 20 guardadas del banco).
            **Prueba: `ia\prueba_mp_scan.py` → TODO OK** en Tanda_hex_perfiles, Borderlands, Kor, Scarpart, build_01,
            roads02 y agua04, y en una variante «forzada» de cada una (Artificer, 5000 de oro y «build» en todos los
            colores, para que haya quien elija): pasos, tramos, lados, costa/puerto, distancia y costo por bono de
            cada ciudad iguales a Python; la elección de cada color igual a `cerrar_paso.py` (Borderlands forzada: 4,
            6 y 7 eligen; Kor forzada: 0 y 7, uno por cada lado). Controles: sin Artificer/Engineer, sin oro, sin
            «build» y tabla de obras llena → no elige; MURALLA propia en todo el tramo → ese paso no; MURALLA ajena o
            un bloque propio (empezado) en otro paso con tramo libre → ese paso pasa adelante; caché: sin cambios no
            recalcula. Lo del humano (+0xe2 = −1) está en `ia_turn` y no se emuló.
            De paso, `cerrar_paso.py` ahora ignora las ciudades arrasadas (tamaño 0), como `pasos.py` y el juego.
4. **Cómo.** El constructor tiene que ir a la casilla y construir con la misma función que el humano (BD_PW con
   OB_MURO y su dirección), cobrando con 0x43fd60. Mover al constructor es lo nuevo: `ai_wrep` no mueve a nadie.
   Una primera etapa más simple: construir solo donde el constructor ya está (junto a una ciudad propia), sin
   moverlo, como `ai_wrep`.

## Esquema de trabajo (el mismo de los demás pasos)
Registrar (evento nuevo: bloque construido por la IA, x, y, n = ciudad que protege) → prueba emulada con controles
(humano, sin artificer/engineer, sin «build», sin oro, casilla ocupada, tope lleno, ciudad sin amenaza) → tanda A/B con las guardadas `_BD`
(IA de prueba construye, original no) → PV, ciudades perdidas y pérdidas. Si mejora, pasa al ranking (CLAUDE.md).

## Próximo paso
Puntos 1 y 2 cerrados; criterio del punto 3 definido por el usuario (19/11/2026). 3.a hecho (ia\pasos.py); falta la confirmación del usuario (TAREAS 267). 3.b hecho (ia\amenaza.py). 3.c hecho en el juego (vista-aliada 1.0.271.0: `mp_scan` / `mp_pick`, evento 51; verificado con ia\prueba_mp_scan.py contra cerrar_paso.py). 4 hecho en el juego, solo para los colores en prueba de una tanda (vista-aliada 1.0.274.0): por la meta 9, como los puentes. `mw_ev` (desde `ai_brrebev`) propone «ir a levantar MURALLA» (código 0x7000) a una pila con «build» si el bando es de prueba (IA.INI, IA_MODE = 1), hay bloque libre en el tramo de `mp_obj[p]`, el oro alcanza para AW_DIV × precio y el bloque está a 30 o menos; `mw_go` (desde `ai_brreb`) la lleva al primer bloque libre (`mw_tile`) y, parada ahí, manda BD_PKT con 0x4000 | dirección << 8 | OB_MURO (tramo horizontal: E; vertical: N). `bd_recv` ahora acepta de la computadora solo la MURALLA. Eventos 52 (bloque levantado: x, y, n = paso) y 53 (no pudo: n = 1 sin «build», 2 sin oro). Verificado con ia\prueba_mw.py (emulado): `mw_tile` da el primer bloque del tramo en los colores que eligen; `mw_ev` propone con la distancia justa y da −1 en los controles (sin tanda, color original, sin oro, casilla sin pila con «build», tramo entero con MURALLA); con MURALLA en el primer bloque, `mw_tile` da el segundo. No se emuló `mw_go` (mover y mandar el paquete): se ve en la tanda.
Guardadas `_BD` armadas (19/11/2026) con `ia\constructores.py`: «build» en el primer bono libre de las 16 unidades de cada bando (no pisa ninguno). Bases: `Tanda_hex_control` (los 6 colores con Artificer, sin murallas) y `Tanda_hex_perfiles` (solo 4 Engineer y 7 Artificer: los demás son control dentro de la partida). Tanda lanzada: `python ia	anda.py nueva --partidas 32 --guardadas Tanda_hex_control_BD,Tanda_hex_perfiles_BD` (parche 1.0.275.0).
Antes: armar las guardadas `_BD` (como `balsa.py`: «build» en una ranura de cada bando, ninguna de las del banco tiene Artificer/Engineer) y correr la tanda A/B (prueba construye, original no); mirar eventos 52/53, PV, ciudades perdidas y pérdidas. Si mejora, pasa al ranking (CLAUDE.md).

Frase para retomar: «Seguimos con ia\PENDIENTE-ia-muros.md, tanda del punto 4».
