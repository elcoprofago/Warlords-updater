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
