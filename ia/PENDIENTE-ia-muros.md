# PENDIENTE — La IA construye muros (pedido del usuario, 19/11/2026)

Pedido textual: *«Que la IA sepa construir muros sería muy importante, incluso más que construir caminos. Vamos por
ese tema.»* Viene de ia\PENDIENTE-ia-innovaciones.md (paso 5.5 cerrado: «que la IA construya muros, paso aparte»).

## Por qué importa (lo medido)
- Tanda 183 (TAREAS 249, Tanda_hex_MU_control): con un anillo de 12 bloques alrededor de tres capitales, la IA casi
  no ataca el muro (1 ataque), insiste contra la ciudad por la costa y pierde mucho. **El muro protege.**
- Tanda 187: abrir brecha en un bloque (24 Longbows virtuales) le costó a la IA 65 ejércitos sin tirar ninguno.
- Hoy la IA solo repara muros que ya tiene (`ai_wrep`, 1.0.222.0); no construye ninguno.

## Lo que hay hoy en el código (build.py, revisado 19/11/2026)
- Muro de piedra = obra OB_MURO (tipo 7) de la tabla `ob_*`. Lo construye un **grupo con un ejército con «build»**
  (BD_HASB, bono de movimiento), en la **casilla del líder**: tierra sin camino, ciudad, ruina, sitio, edificio ni
  otra obra. Dirección 1..8 en el byte +5 (une el bloque con sus vecinos, `ob_wmask`). Precio OB_FRAC = 10
  veinteavos = 50 % de fundar una ciudad, por bloque. Puerta (camino encima) OB_MCAM = 5 veinteavos.
- El muro es **intransitable para todos, también para el dueño**, salvo por una puerta (dueño y aliados, `po_pf`).
- **Tope: OB_MAX = 512 obras en toda la partida** (era 64; subido en vista-aliada 1.0.263.0 a pedido del usuario),
  sumando las de todos los bandos (torres, faros, muros). Los .SAV viejos ('OBRA', 64) se siguen cargando.
- **Las puertas vienen con el muro:** el constructor nunca queda encerrado (corrección del usuario, 19/11/2026; así
  es desde 1.0.175.0/1.0.177.0). La nota anterior («la IA se encierra sola») venía de un registro viejo de 1.0.151.
- Hoy ningún bando de las guardadas del banco tiene unidades con «build» (relevamiento del paso 5).

## Cuándo construye la IA (condiciones del usuario, 19/11/2026)
Pedido textual: *«una condición de levantar murallas sería tener activado "artificer" o al menos "engineer" al
principio de la partida; otra, contar con un mínimo de oro. Es una estrategia defensiva, pero una más entre tantas.
No toda IA debe construir muros, solo debe saber hacerlo, y decidir cuándo es mejor, en base a las condiciones
predeterminadas.»*
- El bando tiene **artificer** o **engineer** activos al empezar la partida (bits de personalidad 18/19, bytes
  +0xc0..0xc2 del registro del jugador). Sin eso, no construye muros nunca.
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
     dentro de la misma partida) o `Tanda_hex_MU` sin muros, quitando Artificer a la mitad de los colores.
2. **El oro mínimo.** 12 bloques = 6 ciudades fundadas. Medir en el banco el oro de cada color a mitad de partida.
   **Medido (19/11/2026):**
   - **Precio de un bloque** (OB_FRAC = 10 veinteavos de fundar una ciudad, `BuildCity=800` en Default.rul): 400.
     Verificado en el exe (0x4057a0, el ajuste que usa `bd_price`): suma la ingeniería del mejor héroe del bando
     (habilidad 12) y le agrega **+6 con Artificer** (bit 0x80000 de +0xc0 del jugador) o **+2 con Engineer** (bit
     0x40000), tope 9; el precio baja un 10 % por punto. Sin héroes ingenieros: **Engineer 320, Artificer 160**.
     Las dos personalidades de la condición del usuario son justamente las que abaratan el muro.
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
     un tramo corto de muro: más efectivo y más barato.
   - **Con visión de conjunto y anticipación** (3-4 jugadas, como en ajedrez): pensar como el enemigo. Por dónde se
     acercaría a nuestras ciudades con sus propias capacidades, aprovechando nuestras debilidades. Distinguir el
     enemigo más peligroso en potencia (también el que está en paz), no solo el declarado.
   - **Mirar qué tiene cada enemigo:** barcos con «landing» o «raft» (el muro no frena un desembarco: alta
     vulnerabilidad), unidades voladoras (el muro tampoco las frena), mucho oro, etc. Si el enemigo puede rodear
     el paso por agua o por aire, cerrarlo vale menos.
   - **Qué ve la IA (revisado en el código, 19/11/2026):** la IA del parche lee directamente la tabla de ejércitos
     del juego (posición, tipo, bonos, dueño) y el oro de cada bando; no pasa por los reportes del jugador ni por la
     niebla (al_thr no consulta la visibilidad). O sea, puede saber todo lo anterior. **Sin verificar:** si la IA
     original del juego respeta el mapa oculto (anotado como pendiente en PENDIENTE-entrenamiento-ia.md).
   - **Orden propuesto, de a uno y midiendo:**
     a. Detectar pasos clave en los mapas del banco con un script (sin tocar el juego): casillas de tierra transitable
        cuyo cierre con 1-3 bloques corta todos los caminos por tierra entre dos zonas con ciudades. Mostrarlos al
        usuario sobre el mapa para confirmar que son los que él reconoce.
     b. Por cada paso: qué enemigos llegan por él a ciudades propias, y en cuántos turnos; y si pueden rodearlo
        (barcos con landing/raft, voladores).
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
Puntos 1 y 2 cerrados; criterio del punto 3 definido por el usuario (19/11/2026). Siguiente: 3.a, detectar pasos clave en los mapas del banco con un script y mostrarlos al usuario.

Frase para retomar: «Seguimos con ia\PENDIENTE-ia-muros.md, punto 3.a».
