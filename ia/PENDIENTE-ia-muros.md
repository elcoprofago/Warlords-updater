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
- **Tope: OB_MAX = 64 obras en toda la partida**, sumando las de todos los bandos (torres, faros, muros).
- Hoy ningún bando de las guardadas del banco tiene unidades con «build» (relevamiento del paso 5).

## Lo que hay que resolver (en este orden: enumerar antes de programar)
1. **Constructores.** Sin «build» la IA no puede construir. Ver qué unidades lo llevan en los .ARM del ranking
   (`C:\Warlords\ARMY`) y en las guardadas del banco. Si ninguna lo tiene, armar guardadas `_BD` (como `balsa.py`:
   «build» en una ranura de los 8 bandos) para la tanda.
2. **El tope de 64.** Un anillo son 12 bloques: con 8 bandos se llena enseguida y deja sin obras a los humanos.
   Proponer al usuario un cupo para la IA (p. ej., N bloques por bando) o subir OB_MAX (cambia el .SAV y la red:
   medir antes cuánto ocupa).
3. **El precio.** 12 bloques = 6 ciudades fundadas. Conviene que la IA no gaste lo que necesita para sus tropas
   (como AW_DIV = 2 de `ai_wrep`): medir en el banco el oro de cada color a mitad de partida (evento 30).
4. **Dónde.** Propuesta: solo en la capital y en las ciudades amenazadas (pila enemiga en guerra a pocas casillas),
   tapando primero los accesos por tierra (la tanda 183 mostró que lo que deja abierta la costa no la cierra), y
   **siempre con una puerta propia**, o la IA se encierra sola (el muro también le cierra el paso a ella).
5. **Cómo.** El constructor tiene que ir a la casilla y construir con la misma función que el humano (BD_PW con
   OB_MURO y su dirección), cobrando con 0x43fd60. Mover al constructor es lo nuevo: `ai_wrep` no mueve a nadie.
   Una primera etapa más simple: construir solo donde el constructor ya está (junto a una ciudad propia), sin
   moverlo, como `ai_wrep`.

## Esquema de trabajo (el mismo de los demás pasos)
Registrar (evento nuevo: bloque construido por la IA, x, y, n = ciudad que protege) → prueba emulada con controles
(humano, sin «build», sin oro, casilla ocupada, tope lleno, ciudad sin amenaza) → tanda A/B con las guardadas `_BD`
(IA de prueba construye, original no) → PV, ciudades perdidas y pérdidas. Si mejora, pasa al ranking (CLAUDE.md).

## Próximo paso
Punto 1 (constructores) y punto 2 (el tope): solo leer y medir, sin cambiar código.

Frase para retomar: «Seguimos con ia\PENDIENTE-ia-muros.md, punto 1».
