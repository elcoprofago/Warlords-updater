# IA de los bandos — alianzas, primera versión

## Objective
Etapa 3, paso 3 de ia/PENDIENTE-entrenamiento-ia.md. Que los colores con la IA de prueba (ia_mode = prueba en
DATA\IA.INI) usen las alianzas como un buen jugador: refugiar sus pilas en la ciudad compartida de un aliado cuando
corren peligro, y sumar fuerzas a la defensa de una ciudad aliada amenazada. El control de la etapa 3 (tandas 19 a
21, 16 partidas válidas en Tanda_Border_Alianzas) mostró que la IA original no hace ninguna de las dos cosas: 0
refugios y 0 batallas con defensores de más de un color.

El éxito se mide en lo táctico, batalla por batalla, en tandas A/B (un equipo de 4 con la IA de prueba contra uno de
4 con la original, equipos alternados en pares complementarios): las pilas amenazadas de la IA de prueba sobreviven
más, y las ciudades aliadas que defiende resisten más, que las de la IA original y que en el control. Qué alianza
gana la partida se registra como dato secundario, a tomar con pinzas (depende de la suerte de la ubicación, los
premios y las decisiones de rumbo, que esta destreza no toca).

## Requirements

### Refugio
1. Una pila de un color con IA de prueba busca refugio en una ciudad compartida de un aliado (la regla de ciudades
   compartidas de vista-aliada, `partners`/`member`) cuando se da alguna de estas condiciones:
   a. una pila enemiga más fuerte que ella puede alcanzarla en su próximo turno;
   b. quedó débil después de una batalla (perdió la mayor parte de su fuerza o le quedan pocas unidades);
   c. un héroe enemigo tiene como misión matar unidades de su color o a su héroe, y viene hacia ella.
2. Solo se refugia en una ciudad compartida que pueda alcanzar este turno, y prefiere la que deja a la pila más
   lejos de la amenaza (o más defendida). Si no alcanza ninguna, sigue con la decisión de la IA original.
3. Una pila refugiada sale cuando se cumple alguna de estas condiciones:
   a. el enemigo se alejó y el dueño de la ciudad ya juntó fuerzas nuevas en ella;
   b. se recuperó o se reforzó.
4. Si está muy débil y su color no tiene oro ni refuerzos cerca, se queda en la ciudad hasta el final de la partida
   (un héroe vivo suma PV).
5. Si el enemigo ataca o amenaza la ciudad donde está refugiada, se queda a defenderla con el aliado.

### Refuerzo de una ciudad aliada
6. Una pila de un color con IA de prueba va a reforzar una ciudad compartida de un aliado amenazada por el enemigo
   (al alcance de una pila enemiga en su próximo turno) cuando:
   a. llega antes de que el enemigo pueda atacarla; o
   b. no llega a tiempo, pero la ciudad es importante (req. 7) y con su pila sumada la defensa vencería al atacante
      previsto. En este caso va aunque deje sin defensa alguna ciudad propia.
7. Una ciudad aliada es importante si cumple alguna de estas condiciones:
   a. está entre el enemigo y las ciudades propias, o cerca de recursos (muchas ruinas sin explorar, muchas ciudades
      neutrales);
   b. produce unidades fuertes, o un sitio cercano le da una ventaja (un turno menos de producción, maná);
   c. es la capital del aliado;
   d. es un paso difícil, fácil de defender por el terreno (por ejemplo, rodeada de montañas intransitables);
   e. forma parte de una condición de victoria del escenario (Rey de la colina, Mantener bandera).

### Información y alcance
8. La IA de prueba usa todo lo que el juego sabe, aunque la partida tenga mapa oculto (la misma ventaja que tiene
   hoy la IA original).
9. Solo cambian las decisiones de los colores con ia_mode = prueba. Los colores con la IA original, y todos los
   colores cuando no hay DATA\IA.INI, juegan exactamente como hoy.

### Registro y medición
10. Cada decisión nueva se anota en DATA\IA_EVT.CSV (tabla `evento`) con tipos nuevos: refugio decidido (con el
    motivo a, b o c del req. 1), salida del refugio (con el motivo del req. 3), quedarse hasta el final (req. 4) y
    refuerzo de ciudad aliada (con el motivo a o b del req. 6, y el criterio de importancia del req. 7).
11. Se registra en la base de datos, por pila amenazada (condición 1a), si sobrevivió al turno siguiente, para las
    dos IA, de modo que se pueda comparar la de prueba con la original y con el control.
12. El informe de una tanda A/B muestra, por IA:
    a. pilas amenazadas y cuántas sobrevivieron al turno siguiente;
    b. refugios (evento 5 y los nuevos) y salidas;
    c. batallas en ciudad aliada con defensores de más de un color, y cuántas ganó la defensa;
    d. ciudades compartidas atacadas y cuántas resistieron;
    e. héroes vivos al final de la partida;
    f. como dato secundario, qué equipo ganó la partida (PV por equipo).
13. Los PATRONES de tanda.py reparten la IA por equipo (los 4 colores de una alianza con la misma IA) y alternan
    qué equipo tiene la IA de prueba en pares complementarios.

## Constraints
- Se programa como parche de Darklord.exe en parches\vista-aliada\build.py (keystone/capstone), como las demás
  destrezas y registros; publica una versión nueva de vista-aliada con tools\publicar-parche.ps1.
- Se apoya en lo que ya existe: ciudades compartidas (`partners`, `member`, 1.0.34.0 también con mapa visible),
  registro de la IA (IA.CSV, IA_BAT.CSV con `colores_d`, IA_DIP.CSV, IA_EVT.CSV), ia_fin/ia_vic, tanda.py,
  informe.py y el Monitor de IA.
- Cada pieza se prueba primero emulada (unicorn, con partidas guardadas reales, como prueba_iaregistro.py y
  prueba_compartidas.py) y después en vivo con una tanda.
- Partidas: Tanda_Border_Alianzas (equipos 0135 | 2467, compartidas y diplomacia), la misma del control.
- El juego corre en C:\Warlords3; commits desde el Windows 10.

## Out of scope
- Limitar la visión de la IA a lo que vería un humano (mapa oculto, reportes): queda para más adelante, cuando la IA
  de prueba se equipare a un humano.
- Proponer, aceptar o romper alianzas (la diplomacia sigue como la decide la IA original).
- Las destrezas de ia-destrezas-v1 (objetivo claro, no desangrarse, combinar armas).
- Mejorar el resultado global de la partida (rumbo, misiones, compras): no se mide como objetivo.
- Modalidades como Crusade.

## Edge cases to handle
- **No hay ninguna ciudad compartida al alcance** → la pila sigue la decisión de la IA original.
- **La ciudad compartida está llena (máximo de pilas o ejércitos de la casilla)** → no la elige; prueba otra o sigue
  con la decisión original.
- **El aliado pierde la ciudad, o la alianza se rompe, mientras la pila está refugiada** → la pila deja de
  considerarse refugiada y vuelve a decidir con las reglas normales (si sigue en la ciudad, pelea por ella).
- **El dueño de la ciudad es eliminado** → igual que el anterior.
- **Varias pilas propias quieren el mismo refugio o la misma ciudad a reforzar** → solo van las necesarias para que
  la defensa aguante; el resto sigue con su objetivo.
- **Una ciudad propia y una aliada amenazadas a la vez** → la aliada solo gana si es importante (req. 7) y la propia
  no lo es más; si no, se defiende la propia como hoy.
- **Partida sin alianzas o sin ciudades compartidas activadas** → la destreza no hace nada; la IA de prueba juega
  igual que la original.
- **Sin DATA\IA.INI** → nada cambia en ningún color (req. 9).
- **Héroe cazador que no se ve (mapa oculto)** → se usa lo que el juego sabe (req. 8).

## Definition of done
- [x] Prueba emulada, con partidas guardadas de alianzas: una pila de prueba amenazada por una más fuerte, con una
      ciudad compartida al alcance, se mueve a ella y anota el evento; el mismo caso con IA original no cambia nada.
- [x] Prueba emulada de cada motivo del req. 1 (a, b, c), de las salidas del req. 3, del req. 4 y del req. 5.
- [ ] Prueba emulada del refuerzo: casos 6a y 6b, cada criterio del req. 7 con un caso que lo cumple y uno que no.
      (Hechos 6a, 6b y el criterio 7a; 7b-7e no están construidos, ver «Construcción».)
- [x] Prueba emulada de control: sin IA.INI y con todos los colores en original, las decisiones son idénticas
      byte a byte a las de vista-aliada 1.0.35.0.
- [x] Prueba emulada de los casos límite (ciudad llena, sin ciudad al alcance, alianza rota).
- [x] tanda.py reparte la IA por equipo (req. 13), probado en juguete.
- [x] El informe de una tanda muestra los puntos a-f del req. 12, también para las tandas de control 19-21 (las que
      no tengan el dato, en blanco).
- [ ] Tanda A/B en vivo de 16 partidas válidas (8 pares) en Tanda_Border_Alianzas: hay refugios y defensas con más
      de un color en los equipos con IA de prueba, y el informe compara las métricas a-e con la IA original y con el
      control.
- [ ] vista-aliada publicado, PENDIENTE-entrenamiento-ia.md y TAREAS.md al día.

## Open questions
- Cómo lee el juego la misión de un héroe (matar unidades de un color o a un héroe) y su destino: hay que ubicarlo
  en el exe para el req. 1c.
- Cómo se ubican en el exe la condición de victoria del escenario (Rey de la colina, Mantener bandera, req. 7e) y la
  ventaja de producción o maná que da un sitio cercano (req. 7b).
- Qué medida de "fuerza" de una pila usar para "más fuerte" (req. 1a) y "aguanta" (req. 6b): la del propio
  cálculo de la IA original si existe en el exe, o una propia calibrada contra IA_BAT.
- Los umbrales de "débil" (req. 1b), "muchas ruinas o ciudades neutrales" (req. 7a) y "unidades fuertes" (req. 7b) se
  fijan durante la construcción con datos de las tandas de control, y quedan escritos en el spec.

## Construcción (vista-aliada 1.0.36.0, 18/10/2026)
Lo construido (build.py, bloque «IA: destreza de alianzas»; prueba_iaalianzas.py, 36 casos TODO OK):
- Gancho: ai_ally reemplaza el call 0x40c990(pila, 0) de 0x40edf1 (la decisión de cada pila de la IA en su turno).
  Sin IA.INI salta directo a 0x40c990. Con IA.INI anota para todo color de la computadora el evento 11 (pila
  amenazada, condición 1a) y al turno siguiente el 12 (sobrevivió 1 / 0, desde ia_turn). Solo con ia_mode = prueba
  decide además refugio o refuerzo; si no decide nada, sigue la decisión original.
- Fuerza de una pila: suma de fuerza base × vida (bits 9-12 y 13-15 de la palabra +0xe, como 0x467240).
- Amenaza a una casilla: suma de la fuerza de los ejércitos en guerra (DIPLO 2) a no más de movimiento / 2 + 1
  casillas (distancia de rey; aproximado, no mira el terreno).
- Alcance propio: costo del mapa de caminos del juego (0x497750 / 0x4a65d0) <= movimiento que le queda al grupo,
  o la pila ya está en la ciudad. Lugar: ejércitos en la ciudad + los de la pila <= 32.
- 1a: amenaza > fuerza de la pila. 1b: fuerza × 2 < la fuerza de la decisión del turno anterior. 1c (aproximado):
  un héroe enemigo al alcance con destino a 2 casillas o menos de la pila (no se ubicó en el exe la misión del héroe).
- 2: elige la ciudad compartida alcanzable que queda más lejos del enemigo más cercano.
- 3a: la fuerza del dueño en la ciudad supera la que tenía al entrar la pila. 3b: la pila tiene la fuerza de entrada
  + max(2, la mitad). Ciudad perdida, alianza rota o dueño eliminado: sale (evento 8, n = 3) y decide de nuevo.
- 4: fuerza <= 6, oro < 100 y ningún ejército propio fuera de la pila a 8 casillas o menos. Después ya no sale.
- 5: si la ciudad está amenazada, se queda (evento 13, una vez por amenaza) aunque se cumpla una salida.
- 6a: la alcanza este turno y la amenaza supera a los defensores más lo ya mandado ese turno; si una ciudad propia
  está amenazada, solo va si la aliada es importante. 6b: no llega este turno, el mapa de caminos la alcanza, es
  importante y defensores + ya mandado + la pila > amenaza. «Ya mandado» evita que vayan más pilas de las necesarias.
- 7a: ruinas sin explorar + ciudades neutrales cerca (la cuenta de la IA original, 0x41d640 / 0x41ec20) >= 3, o una
  ciudad propia a 6 casillas o menos.
- Eventos nuevos en IA_EVT.CSV: 7 refugio (n = motivo), 8 salida (1 = 3a, 2 = 3b, 3 = ciudad o alianza perdida),
  9 hasta el final, 10 refuerzo (n = 10 × motivo + criterio), 11 pila amenazada (n = líder), 12 su resultado,
  13 se queda a defender.
- Control (req. 9): sin IA.INI nada cambia y con la IA original el estado del juego queda igual byte a byte (prueba
  emulada). Comparado con el exe de 1.0.35.0, fuera de las cuevas del parche solo cambian el gancho de 0x40edf1 y
  ocho llamadas a las rutinas del registro, que se corrieron de lugar.

No construido (queda para una versión siguiente):
- Criterios 7b (producción fuerte o ventaja de un sitio), 7c (capital del aliado), 7d (paso difícil) y 7e
  (condición de victoria del escenario): no se ubicaron en el exe. Hoy una ciudad es importante solo por 7a.
- La tabla de refugios no se guarda con la partida: al cargar una guardada, las pilas deciden desde cero.
- Los umbrales (6 de fuerza, 100 de oro, 8 y 6 casillas, 3 sitios) son de diseño; se revisan con la tanda A/B.

## Observaciones del usuario durante la tanda 22 (18/10/2026)
- No se ven defensas de una ciudad con más de un color. Coincide con lo construido: el refuerzo solo dispara con
  ciudades «importantes» por 7a (7b-7e no están), así que puede no darse nunca. Se confirma o descarta con el
  evento 10 del informe A/B.
- Los barcos con bono «cabotaje» y «landing» se comportan bien.
- La IA de prueba no destruye puentes ni puertos con fin estratégico. No está en este spec (nada lo construye).
  Definición dada por el usuario para una versión siguiente: el único fin que justifica destruir un lugar que
  permite salir de una isla o cruzar a otro territorio es **defensivo**, impedir un ataque inminente por ese paso.

## Tanda 22 (primera de la A/B, 6 válidas de 16, 18/10/2026)
- Equipo ganador: 2467 gana 5 de 6, con cualquier IA: el mapa favorece a ese equipo. Por IA: prueba 2 de 6,
  original 4 de 6 (PV por color 6,2 contra 7,4; ciudades 4,9 contra 5,8). Con 6 partidas no se separa del mapa.
- Alianzas, prueba: 15 refugios, 2 salidas, 7 se quedan a defender, 41 refuerzos mandados. Pero 0 batallas con
  defensores de más de un color, igual que la original: los refuerzos salen y no llegan a defender juntos. Confirma
  lo que vio el usuario. Pilas amenazadas que sobreviven: prueba 90 de 121 (74 %), original 99 de 124 (80 %).
- «Desangradas»: 6 en prueba, 0 en original.
- Faltan 10 válidas (5 pares) para el criterio del spec.

## Corrección: el refuerzo se queda (vista-aliada 1.0.37.0, 18/10/2026)
- Causa de las 0 defensas de más de un color en la tanda 22, confirmada en el emulador: la pila que llegaba a la
  ciudad aliada no tenía estado de refuerzo. Al turno siguiente sus defensores ya la incluían, la ciudad dejaba de
  «necesitar» refuerzo y la decisión volvía a la IA original, que la sacaba aunque la amenaza siguiera.
- Ahora (ai_ally, al_reinf): una pila de la IA de prueba que está en una ciudad compartida de un aliado con amenaza
  se queda y anota el evento 14 (n = amenaza), cada turno que se queda. Sin amenaza sigue la decisión original.
- prueba_iaalianzas.py: 2 casos nuevos (se queda / con la amenaza pasada sigue la original), 38 TODO OK; el caso
  nuevo falla con el exe de 1.0.36.0. informe.py: columna «ref.qda».
- La tanda 22 queda como referencia de 1.0.36.0; la A/B de 16 válidas se arma de nuevo con 1.0.37.0.

## Tandas 23 y 24 (A/B con 1.0.37.0, 15 válidas, 19/10/2026)
- 15 válidas de 16 (la 4 de la tanda 24 se colgó al cargar, 0 turnos). Gana el equipo de la IA original 12 de 15.
  PV por color: prueba 3,5 / 3,7 contra original 10,9 / 10,4 (en la tanda 22, con 1.0.36.0: 6,2 contra 7,4).
- Evento 14 (refuerzo que se queda): 0 en vivo. De los 94 refuerzos, solo 3 dejan rastro de la pila en la ciudad
  en los 4 turnos siguientes (evento 7, 11 o 13 en sus casillas): las pilas casi nunca llegan.
- 80 de los 94 refuerzos son 6b (no llega este turno). 6b solo pide que el mapa de caminos alcance la ciudad, sin
  límite de distancia, y se decide de nuevo cada turno: las pilas cruzan el mapa detrás de amenazas que se van
  antes de que lleguen, y dejan de jugar su propio frente. Es la explicación más probable de la caída de la IA de
  prueba (menos ciudades, menos ataques, menos héroes vivos).
- Próximo paso: 6b con límite (la ciudad a no más de 2 turnos de movimiento, y la amenaza tiene que seguir al
  llegar), y el refuerzo guardado en AL_TAB como el refugio, para que la pila siga el mismo destino y no decida de
  nuevo cada turno. Después, otra A/B.

## Refuerzo quitado (vista-aliada 1.0.38.0, 19/10/2026)
- Pedido del usuario: los req. 6 y 7 (refuerzo de ciudades aliadas) se quitan. Mandar refuerzos es una decisión
  estratégica (los fines de la contienda, según el criterio de victoria), no táctica (ganar cada batalla).
- build.py: fuera al_reinf (6a/6b, evento 14) y al_imp (7a); la pila que no se refugia sigue la decisión original.
  prueba_iaalianzas.py: los casos 6/6b pasan a un solo control (ciudad aliada amenazada al alcance: sin evento 10
  ni 14, sigue la original); 33 TODO OK.
- Lo que sigue: clasificar todas las instrucciones pendientes en tácticas o estratégicas (ver
  ia/PENDIENTE-entrenamiento-ia.md, «Clasificación táctica / estratégica») antes de otra A/B.

## Regla del héroe y defensa de ciudades aliadas (vista-aliada 1.0.39.0, 19/10/2026)
Las dos reglas tácticas que el usuario confirmó en la revisión táctica / estratégica.
- **Héroe perseguido** (reemplaza al 1c aproximado y al req. 4 «quedarse hasta el final», que se quita): un héroe
  débil se refugia en una ciudad aliada mientras a) la ciudad ya esté bien defendida por el aliado, b) un héroe
  enemigo lo persiga para asesinarlo y cumplir una misión, y c) el perseguidor esté cerca. Cómo lo mide la IA:
  - b) un jugador en guerra tiene la misión activa 11 «Assassinating an Enemy» con objetivo en la pila. La misión
    activa está en 0x55edc4 + jugador * 16: +0 activa, +2 su héroe, +4 tipo, +6 el ejército objetivo, según el
    generador 0x45ec40. Los nombres de los tipos 1..12 están en Sagetext.tex: el 10 es «Destroying an Enemy Site»
    y el 11 «Assassinating an Enemy».
  - c) el perseguidor alcanza al objetivo en su próximo turno (movimiento / 2 + 1 casillas, como la amenaza).
  - débil: los ejércitos del perseguidor en su casilla suman más fuerza que la pila.
  - a) el dueño de la ciudad tiene en ella más fuerza que la amenaza a esa ciudad.
  - Se mira antes que los motivos 1 y 2 (evento 7, n = 3); si ninguna ciudad cumple a), siguen ellos. Se queda
    mientras se cumplan las cuatro y sale cuando alguna falla (evento 8, n = 4). Si la ciudad está amenazada,
    manda el req. 5.
- **Defensa de ciudades aliadas** (regla del usuario: «siempre defender una ciudad aliada en riesgo inminente de
  ataque de un enemigo común, salvo que eso descuide una ciudad propia también en riesgo»). Para la pila que no se
  refugia, si ninguna ciudad propia tiene amenaza mayor que sus defensores:
  - si ya está en una ciudad aliada con amenaza, se queda (evento 16, cada turno);
  - si no, va (evento 15) a la ciudad aliada que alcanza este turno, con lugar, cuya amenaza supera a sus
    defensores más lo ya mandado este turno por otras pilas. Entre varias, va a la que le falta más defensa.
  - Pasada la amenaza, decide la original. No hay criterio de «importancia» de la ciudad.
  - Aproximación: la amenaza son los enemigos del que manda; se supone que también son enemigos del aliado, como
    en las partidas por equipos.
- prueba_iaalianzas.py: 44 TODO OK. Casos nuevos con controles: misión de otro objetivo o inactiva, perseguidor
  lejos o más débil, ciudad sin defensa, no llega este turno, ya cubierta, ciudad propia en riesgo, y permanencia
  y salida en las dos reglas. Contra 1.0.38.0 fallan los 5 casos nuevos que la distinguen.
- informe.py: columnas ref.hér (evento 7 con n = 3), def.ali (15) y def.qda (16).
- Próximo paso: A/B de 16 partidas con 1.0.39.0 (TAREAS 21).

## Órdenes del humano a un aliado de la computadora (vista-aliada 1.0.40.0, 19/10/2026)
Primera parte de los mensajes entre aliados (ia/PENDIENTE-entrenamiento-ia.md): la IA ya sabe cumplir una orden;
todavía no hay forma de dársela desde el juego (falta el paquete 0x2a2 y la barra «#n»), así que en partida no
cambia nada.
- Decisiones del usuario: **la orden va primero**, antes del refugio, de la defensa de ciudades aliadas y de la IA
  original («quien comanda es el humano; si toma malas decisiones, es a su costo y riesgo»). La cumplen **las pilas
  que llegan en 2 turnos o menos**, y la orden **caduca a los 2 turnos** de emitida.
- Entrada en el exe: 0x40c990(pila, arg) con arg != 0 saltea el planificador: meta = arg / 1000, objetivo =
  arg % 1000. ai_ord (gancho de 0x40edf1, antes de ai_ally, con o sin IA.INI) pasa:
  - «atacá CIUDAD» (tipo 1): 7000 + ciudad. Si la ciudad ya es del bando o de un aliado, la orden queda cumplida.
  - «atacá a COLOR» (tipo 2): 7000 + la ciudad de ese color más barata de alcanzar.
  - «mandame refuerzos» (tipo 3): 1000 + la ciudad del que la dio más barata de alcanzar (o en la que ya está).
- «Llega en 2 turnos» = costo del mapa de caminos <= 2 * movimiento del grupo; para atacar, a una de las 12
  casillas que rodean la ciudad (or_ring), porque las de una ciudad enemiga no tienen costo de paso. Aproximación:
  el movimiento del turno siguiente se supone igual al de este.
- Vencimiento: OR_TAB +1 = turnos que quedan + 1; quien recibe la orden pone 3 e ia_turn lo baja al empezar cada
  turno del bando: vale en sus 2 turnos siguientes, juegue antes o después del humano en la ronda.
- Evento 17 (x, y = ciudad, n = tipo) cuando una pila cumple la orden, si hay IA.INI.
- prueba_iaalianzas.py: TODO OK, con 13 casos nuevos (cada tipo, sin IA.INI, no llega, cumplida, vencida, contra
  el propio color, ya en la ciudad, y la cuenta de turnos en ia_turn con control de otro bando).
- No publicado: se publica junto con el paquete 0x2a2 y la barra «#n» (1.0.41.0, abajo).

## Dar la orden desde el juego: barra «#n» y paquete 0x2a2 (vista-aliada 1.0.41.0, 19/10/2026)
- El humano escribe en la barra de chat «#n ORDEN», con n = número del bando aliado de la computadora (1 a 8):
  «#n ataca CIUDAD» (nombre exacto), «#n ataca a BANDO» (número o nombre exacto) y «#n mandame refuerzos». Sin
  distinguir mayúsculas; el verbo vale por sus 4 primeras letras («atacá» = «ataca»).
- La barra original (0x409170) descartaba «#n» a un bando no humano (0x4091ea); ahí entra ch_ai. La PC del humano
  interpreta la orden y la difunde como paquete 0x2a2 (bando que la da, bando que la recibe, tipo, objetivo), que un
  Warlords sin parche descarta. El humano ve su propio texto; si no son aliados o la orden no se entiende, ve una
  respuesta con el color del bando n («No somos aliados» o la lista de órdenes) solo en su pantalla.
- Recepción (or_recv, en todas las PC): valida que quien la da sea humano de la máquina que mandó el paquete, que
  el destino sea de la computadora, que sean aliados y el objetivo; llena OR_TAB con 3. La PC que corre ese bando
  contesta con el chat nativo (0x1ac del bando de la computadora, solo a la máquina del humano): «Ok, ataco
  CIUDAD», «Ok, ataco a BANDO», «Ok, te mando refuerzos». Ningún enemigo ve la orden ni la respuesta.
- Todavía no hay «no puedo: MOTIVO»: si ninguna pila llega en 2 turnos, la IA sigue con lo suyo sin avisar.
- prueba_chatordenes.py: 24 casos TODO OK (barra real 0x409170 con cada orden, errores y controles; recepción
  válida en la PC del bando y en otra, siete rechazos y otro paquete que sigue a tl_recv).
