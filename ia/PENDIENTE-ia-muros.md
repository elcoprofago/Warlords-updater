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
   - **.ARM del ranking (`C:\Warlords\ARMY`, 380):** llevan «build» `archers.ARM` (Archers: solo build),
     `Dwarfsap.ARM` (Dwarf Sappers: hills + build) y `red_scav.ARM` (Red Scavens: desert + build).
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
3. **Dónde.** Propuesta: solo en la capital y en las ciudades amenazadas (pila enemiga en guerra a pocas casillas),
   tapando primero los accesos por tierra (la tanda 183 mostró que lo que deja abierta la costa no la cierra).
4. **Cómo.** El constructor tiene que ir a la casilla y construir con la misma función que el humano (BD_PW con
   OB_MURO y su dirección), cobrando con 0x43fd60. Mover al constructor es lo nuevo: `ai_wrep` no mueve a nadie.
   Una primera etapa más simple: construir solo donde el constructor ya está (junto a una ciudad propia), sin
   moverlo, como `ai_wrep`.

## Esquema de trabajo (el mismo de los demás pasos)
Registrar (evento nuevo: bloque construido por la IA, x, y, n = ciudad que protege) → prueba emulada con controles
(humano, sin artificer/engineer, sin «build», sin oro, casilla ocupada, tope lleno, ciudad sin amenaza) → tanda A/B con las guardadas `_BD`
(IA de prueba construye, original no) → PV, ciudades perdidas y pérdidas. Si mejora, pasa al ranking (CLAUDE.md).

## Próximo paso
Punto 1 cerrado (19/11/2026). Punto 2 (oro mínimo): medir el oro de cada color a mitad de partida en las tandas ya corridas (evento 30), sin cambiar código.

Frase para retomar: «Seguimos con ia\PENDIENTE-ia-muros.md, punto 2».
